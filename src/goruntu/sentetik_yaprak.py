"""
AGROMATCH - Sentetik şeker pancarı yaprağı üretici
==================================================
NEDEN SENTETİK GÖRÜNTÜ?
Saha fotoğrafları toplanana kadar görüntü işleme hattının doğru çalıştığını
kanıtlamanın tek yolu, lekelerin yerini ve boyutunu ÖNCEDEN bildiğimiz
görüntüler üretmektir. Böylece algoritmanın bulduğu lekeler gerçek lekelerle
karşılaştırılabilir (duyarlılık / kesinlik ölçülebilir).

Üretilen yaprak bilinçli olarak zorlaştırılmıştır:
  - toprak zemin (yaprağın arka plandan ayrılması gerekir)
  - ana damar ve yan damarlar (lekeyle karıştırılabilir)
  - azot eksikliği sarılığı (geniş, soluk lekeler — hastalık DEĞİL)
  - toz ve toprak zerreleri (küçük koyu noktalar — hastalık DEĞİL)
Algoritma bunları elemeyi başarmalıdır.

Cercospora beticola lekesinin gerçek görünümü:
  3–5 mm çapında yuvarlak leke, açık gri merkez, kırmızı-kahverengi halka,
  merkezde iğne ucu kadar siyah noktacıklar (konidi yatakları).

Kullanım:
    python src/goruntu/sentetik_yaprak.py --adet 12 --cikti data/sentetik
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

KOK = Path(__file__).resolve().parent.parent.parent
GEN, YUK = 640, 480


def _zemin(rng):
    """Toprak zemin: kahverengi, gürültülü."""
    taban = np.zeros((YUK, GEN, 3), np.float32)
    taban[..., 0] = 96; taban[..., 1] = 78; taban[..., 2] = 60
    gurultu = rng.normal(0, 14, (YUK, GEN, 1))
    taban += gurultu
    return np.clip(taban, 0, 255)


def _yaprak_maskesi():
    """Dalgalı kenarlı, geniş pancar yaprağı silueti."""
    y, x = np.mgrid[0:YUK, 0:GEN]
    cx, cy = GEN / 2, YUK / 2
    dx, dy = (x - cx) / 262.0, (y - cy) / 196.0
    aci = np.arctan2(dy, dx)
    yaricap = np.sqrt(dx ** 2 + dy ** 2)
    dalga = 1 + 0.065 * np.sin(7 * aci) + 0.032 * np.sin(13 * aci + 1.1)
    return yaricap <= dalga


def _yaprak_dokusu(rng, maske):
    """Yeşil gövde, damarlar ve azot sarılığı."""
    kat = np.zeros((YUK, GEN, 3), np.float32)
    y, x = np.mgrid[0:YUK, 0:GEN]
    # taban yeşil + dikey gradyan
    kat[..., 0] = 66 + (y / YUK) * 18
    kat[..., 1] = 112 + (y / YUK) * 22
    kat[..., 2] = 48 + (y / YUK) * 10
    kat += rng.normal(0, 6, (YUK, GEN, 1))

    gorsel = Image.fromarray(np.clip(kat, 0, 255).astype(np.uint8))
    ciz = ImageDraw.Draw(gorsel)
    cx, cy = GEN / 2, YUK / 2
    # ana damar
    ciz.line([(cx - 250, cy + 6), (cx + 250, cy - 4)], fill=(150, 175, 110), width=9)
    # yan damarlar
    for k in range(-5, 6):
        if k == 0:
            continue
        bas = (cx + k * 42, cy + (6 if k < 0 else -4))
        son = (cx + k * 52, cy + math.copysign(150, k % 2 - 0.5) * (1 - abs(k) / 9))
        ciz.line([bas, son], fill=(138, 163, 102), width=4)
    gorsel = gorsel.filter(ImageFilter.GaussianBlur(1.1))
    kat = np.asarray(gorsel).astype(np.float32)

    # azot eksikliği sarılığı: geniş, soluk, kenarsız (hastalık değil)
    for _ in range(2):
        sx, sy = rng.integers(140, GEN - 140), rng.integers(110, YUK - 110)
        r = rng.integers(55, 95)
        d2 = (x - sx) ** 2 + (y - sy) ** 2
        g = np.exp(-d2 / (2 * (r / 1.6) ** 2))[..., None]
        kat = kat * (1 - 0.45 * g) + np.array([188, 186, 92], np.float32) * (0.45 * g)
    return kat


def _sapir(rng, renk, miktar):
    """Bir RGB rengi, TON AİLESİNİ KORUYARAK rastgele kaydırır.

    Üç kanala bağımsız büyük gürültü eklemek rengi aileden çıkarıyor:
    kahverengi bir leke pembeye ya da mora dönüyor ve görüntü gerçekçiliğini
    kaybediyor. Bunun yerine ağırlıklı olarak ortak bir açıklık çarpanı
    uygulanıyor (lekenin yaşı, gölge, pozlama), üstüne kanal başına küçük bir
    sapma ekleniyor (çeşit farkı, beslenme durumu).
    """
    if miktar <= 0:
        return tuple(int(k) for k in renk)
    carpan = 1.0 + float(rng.normal(0, 0.13 * miktar))
    return tuple(int(np.clip(k * carpan + rng.normal(0, 6 * miktar), 0, 255))
                 for k in renk)


def _leke_ciz(gorsel, x, y, r, rng, cesitlilik=0.0):
    """Tek bir Cercospora lekesi: gri merkez, kırmızı-kahve halka, siyah noktacıklar.

    cesitlilik > 0 ise lekenin rengi her seferinde kaydırılır. Sabit renkli
    leke üretmek veri setini işe yaramaz hâle getiriyor: sınıflandırıcı
    lekeyi biçiminden değil, koddaki renk sabitinden tanıyor ve %100 doğruluk
    veriyor. Gerçek yaprakta lekenin rengi lekenin yaşına, çeşide, ışığa ve
    yaprağın beslenme durumuna göre değişir.
    """
    ciz = ImageDraw.Draw(gorsel, "RGBA")
    # Lekenin yaşı: genç leke koyu ve küçük merkezli, yaşlı leke soluk ve geniş
    yas = float(rng.uniform(0, 1)) if cesitlilik > 0 else 0.5
    halka = _sapir(rng, (132 + 26 * yas, 62 + 18 * yas, 46 + 14 * yas), cesitlilik)
    merkez = _sapir(rng, (176 - 30 * (1 - yas), 170 - 30 * (1 - yas), 150 - 26 * (1 - yas)),
                    cesitlilik)
    # DİKKAT: rastgele sayı yalnızca çeşitlilik açıkken çekilir. Koşulsuz
    # çekmek, cesitlilik=0 modunda da RNG akışını kaydırıyor ve panelin
    # doğrulama sayılarını sessizce değiştiriyordu (F1 0,953 -> 0,936).
    saydam = 235 if cesitlilik <= 0 else int(
        np.clip(235 - 40 * cesitlilik * rng.random(), 150, 255))

    ciz.ellipse([x - r, y - r, x + r, y + r], fill=(*halka, saydam))
    ic = max(1.5, r * (0.62 + 0.18 * yas * cesitlilik))
    ciz.ellipse([x - ic, y - ic, x + ic, y + ic], fill=(*merkez, 240))
    for _ in range(int(rng.integers(2, 6))):                                     # konidi yatakları
        nx = x + rng.uniform(-ic * 0.6, ic * 0.6)
        ny = y + rng.uniform(-ic * 0.6, ic * 0.6)
        ciz.ellipse([nx - 1, ny - 1, nx + 1, ny + 1], fill=(52, 46, 42, 255))


def _zor_yaniltici_ciz(gorsel, ic_maske, rng):
    """Lekeyle AYNI RENK AİLESİNDE olan, ama leke olmayan şeyler.

    Toz zerresi ve azot sarılığı yetmiyor: ikisi de lekeden renkçe ayrıldığı
    için sınıflandırıcı sorunu tek bir renk eşiğiyle çözüyor. Gerçek tarlada
    yaprağın üstünde lekeyle aynı kahverengiyi taşıyan başka şeyler var.
    Bunları eklemeden öğrenilen model sahada çöker.

    Üç tip:
      kenar kuruması  — kahverengi, düzensiz, yaprak kenarında (konum ayırır)
      toprak sıçraması — kahverengi, düzensiz, her yerde (biçim ayırır)
      odunlaşmış damar — kahverengimsi, çizgisel (uzama ayırır)
    """
    ciz = ImageDraw.Draw(gorsel, "RGBA")
    yuk, gen = ic_maske.shape

    # Kenar kuruması: yaprağın dış hattına yakın kahverengi düzensiz yamalar
    for _ in range(int(rng.integers(0, 4))):
        aci = rng.uniform(0, 2 * math.pi)
        px = int(gen / 2 + math.cos(aci) * rng.uniform(0.74, 0.92) * gen / 2)
        py = int(yuk / 2 + math.sin(aci) * rng.uniform(0.74, 0.92) * yuk / 2)
        if not (0 <= px < gen and 0 <= py < yuk) or not ic_maske[py, px]:
            continue
        renk = _sapir(rng, (138, 74, 52), 0.8)
        for _ in range(int(rng.integers(4, 9))):
            ox, oy = px + rng.integers(-16, 17), py + rng.integers(-12, 13)
            rr = rng.uniform(3, 9)
            ciz.ellipse([ox - rr, oy - rr * 0.6, ox + rr, oy + rr * 0.6],
                        fill=(*renk, 215))

    # Toprak sıçraması: düzensiz kahverengi lekecikler
    for _ in range(int(rng.integers(3, 11))):
        px, py = int(rng.integers(70, gen - 70)), int(rng.integers(60, yuk - 60))
        if not ic_maske[py, px]:
            continue
        renk = _sapir(rng, (120, 78, 54), 0.9)
        noktalar = [(px + rng.integers(-7, 8), py + rng.integers(-6, 7))
                    for _ in range(int(rng.integers(5, 9)))]
        ciz.polygon([tuple(int(v) for v in n) for n in noktalar], fill=(*renk, 225))

    # Odunlaşmış / kurumuş damar parçası: çizgisel kahverengi iz
    for _ in range(int(rng.integers(0, 3))):
        px, py = int(rng.integers(90, gen - 90)), int(rng.integers(70, yuk - 70))
        if not ic_maske[py, px]:
            continue
        uz = rng.uniform(30, 90)
        aci = rng.uniform(0, math.pi)
        renk = _sapir(rng, (126, 84, 58), 0.7)
        ciz.line([(px, py),
                  (px + math.cos(aci) * uz, py + math.sin(aci) * uz)],
                 fill=(*renk, 210), width=int(rng.integers(2, 5)))


def _isik_kaydir(gorsel, rng, miktar):
    """Yaprak başına ışık ve beyaz dengesi değişimi.

    Aynı tarlada çekilen iki fotoğraf bile aynı renk dengesine sahip değildir:
    bulut geçer, gölge düşer, telefonun beyaz dengesi kayar. Bu kaydırma
    olmadan model yaprakları mutlak renk değerlerinden tanır; sahada bu
    değerler tutmaz.
    """
    if miktar <= 0:
        return gorsel
    dizi = np.asarray(gorsel).astype(np.float32)
    kazanc = 1.0 + rng.normal(0, 0.09 * miktar, 3)
    parlaklik = rng.normal(0, 16 * miktar)
    dizi = dizi * kazanc + parlaklik
    return Image.fromarray(np.clip(dizi, 0, 255).astype(np.uint8))


def yaprak_uret(tohum, leke_sayisi=None, cesitlilik=0.0):
    """Sentetik yaprak üretir.

    cesitlilik (0–1): 0 varsayılan ve panel hattının kullandığı moddur —
    sabit renkler, yalnızca toz ve azot sarılığı yanıltıcıları. 1 ise leke
    renkleri, ışık ve beyaz dengesi her yaprakta değişir ve lekeyle aynı
    renkteki zor yanıltıcılar (kenar kuruması, toprak sıçraması, odunlaşmış
    damar) eklenir.

    Ayrım bilinçli: panelin doğrulama sayıları sabit bir üretime dayanır ve
    sürüm sürüm karşılaştırılabilir olmalıdır. Makine öğrenmesi veri setinin
    ise tam tersine zor olması gerekir.
    """
    rng = np.random.default_rng(tohum)
    maske = _yaprak_maskesi()
    zemin = _zemin(rng)
    doku = _yaprak_dokusu(rng, maske)
    birlesik = np.where(maske[..., None], doku, zemin)
    gorsel = Image.fromarray(np.clip(birlesik, 0, 255).astype(np.uint8))

    # Lekeleri yaprağın iç kısmına yerleştir (kenardan uzak)
    ic_maske = _yaprak_maskesi()
    adet = int(leke_sayisi if leke_sayisi is not None else rng.integers(6, 26))
    gercek = []
    deneme = 0
    while len(gercek) < adet and deneme < adet * 60:
        deneme += 1
        x = int(rng.integers(70, GEN - 70)); y = int(rng.integers(60, YUK - 60))
        r = float(rng.uniform(4.5, 11.0))
        if not ic_maske[y, x]:
            continue
        if any((x - gx) ** 2 + (y - gy) ** 2 < (r + gr + 6) ** 2 for gx, gy, gr in gercek):
            continue
        _leke_ciz(gorsel, x, y, r, rng, cesitlilik)
        gercek.append((x, y, r))

    if cesitlilik > 0:
        _zor_yaniltici_ciz(gorsel, ic_maske, rng)

    # Yanıltıcılar: toz zerreleri (küçük ve koyu, leke değil)
    ciz = ImageDraw.Draw(gorsel)
    for _ in range(int(rng.integers(5, 12))):
        x, y = int(rng.integers(60, GEN - 60)), int(rng.integers(50, YUK - 50))
        if not ic_maske[y, x]:
            continue
        rr = rng.uniform(1.2, 2.4)
        ciz.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(58, 50, 44))

    gorsel = gorsel.filter(ImageFilter.GaussianBlur(0.6))
    gorsel = _isik_kaydir(gorsel, rng, cesitlilik)
    return gorsel, [dict(x=g[0], y=g[1], r=round(g[2], 2)) for g in gercek]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adet", type=int, default=12)
    ap.add_argument("--cikti", default="data/sentetik")
    a = ap.parse_args()

    hedef = KOK / a.cikti
    hedef.mkdir(parents=True, exist_ok=True)
    kayit = []
    for i in range(a.adet):
        # şiddet basamakları: temizden ağıra
        sayi = [0, 3, 6, 10, 14, 18, 22, 27, 32, 38, 44, 52][i % 12]
        gorsel, gercek = yaprak_uret(1000 + i, sayi)
        ad = f"yaprak_{i:02d}.png"
        gorsel.save(hedef / ad)
        kayit.append(dict(dosya=ad, leke_sayisi=len(gercek), lekeler=gercek))
        print(f"{ad}: {len(gercek)} leke")
    (hedef / "gercek_degerler.json").write_text(
        json.dumps(kayit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{a.adet} görüntü ve gerçek değerler yazıldı -> {hedef}")


if __name__ == "__main__":
    main()
