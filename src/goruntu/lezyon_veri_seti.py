"""
AGROMATCH - Lezyon öznitelik veri seti (veri madenciliği için)
==============================================================
NE ÜRETİR
Sentetik yaprak görüntülerinden, SEGMENTASYONUN BULDUĞU HER BİLEŞEN için bir
satır çıkarır ve her satırı "gerçek Cercospora lekesi mi, değil mi" diye
etiketler. Çıktı tek bir CSV'dir; satır sayısı yaprak sayısının onlarca katıdır.

NEDEN BU VERİ SETİ
cercospora.py hattı, bir bileşenin leke olup olmadığına ELLE AYARLANMIŞ üç
eşikle karar verir:

    MIN_ALAN = 34 piksel      MAKS_ALAN = 1800 piksel      MIN_DAIRESELLIK = 0.45

Bu eşikler parametre taramasıyla seçildi; işe yarıyorlar ama NEDEN o değerler
olduğunu kimse veriden türetmedi. Bu veri seti o soruyu öğrenilebilir hâle
getirir: aynı kararı veriden öğrenen bir model kurulabilir mi, ve öğrendiği
kural elle konan eşiklerle örtüşür mü?

Karar ağacı bu karşılaştırma için özellikle uygundur: öğrendiği eşikleri
açıkça yazar. Ağaç kökte "alan > 31.5" diyorsa, elle konan 34 değeri veriyle
doğrulanmış olur. Başka bir şey diyorsa, elle konan eşik sorgulanmalıdır.

ETİKETLEME
Sentetik üretici her lekenin merkezini ve yarıçapını bildiği için etiket
tahmin değil, bilinen gerçektir. Bir bileşen, merkezi herhangi bir gerçek
lekenin (yarıçap + TOLERANS) mesafesi içindeyse 1, değilse 0 etiketlenir.

Negatif örnekler uydurma değildir; üreticinin bilerek koyduğu yanıltıcılardır:
ana damar ve yan damarlar, azot eksikliği sarılığı, toz zerreleri, yaprak
kenarı kuruması. Yani veri seti "kolay negatif" içermez.

BİLİNEN SINIRLAR (rapora yazılmalı)
  - Sentetik görüntü gerçek yaprağın dokusunu, ışığını ve gölgesini taşımaz.
    Burada ölçülen başarı, saha başarısının üst sınırıdır.
  - Birleşen iki leke tek bileşen olarak çıkabilir; bu durumda bir pozitif
    satır iki lekeyi temsil eder.
  - Segmentasyonun hiç bulamadığı lekeler veri setinde yer almaz. Bu yüzden
    künyeye "kaçırılan leke oranı" yazılır: modelin erişebileceği en yüksek
    duyarlılık bununla sınırlıdır.

Kullanım:
    python src/goruntu/lezyon_veri_seti.py --yaprak 300
    python src/goruntu/lezyon_veri_seti.py --yaprak 50 --cikti data/deneme
"""

import argparse
import csv
import json
import math
from pathlib import Path

import cv2
import numpy as np
from cercospora import yaprak_maskesi, yesillik
from sentetik_yaprak import yaprak_uret

KOK = Path(__file__).resolve().parent.parent.parent

# Bir bileşenin merkezi, gerçek lekenin yarıçapı + bu kadar piksel içindeyse
# o lekeye ait sayılır. Lekenin kenarı bulanıklaştığı için sıfır tolerans
# gereğinden katı olur.
TOLERANS = 4.0

# Gürültü eşiği: 2 pikselden küçük bileşenlerin çevresi ve daireselliği
# anlamsız çıkar. Eşiği olabildiğince düşük tutuyoruz; elemeyi model öğrensin.
EN_KUCUK_BILESEN = 2

# Yaprak başına leke sayısının dağılımı: (oran, alt, üst)
# Tarlada taranan yaprakların çoğu erken evrededir. Veri setini ağır enfekte
# yapraklarla doldurmak hem gerçeği yansıtmaz hem de pozitif sınıfı şişirir.
SIDDET_DAGILIMI = [
    (0.25, 0, 2),     # temiz — ilaçlama kararının "hayır" tarafı
    (0.35, 3, 12),    # ilk lekeler ve eşik civarı
    (0.25, 13, 28),   # yerleşmiş enfeksiyon
    (0.15, 29, 50),   # ağır
]

OZNITELIKLER = [
    "alan", "cevre", "dairesellik", "esdeger_cap", "doluluk", "dolgunluk",
    "uzama", "en_boy_orani", "ort_h", "ort_s", "ort_v", "std_v",
    "ort_yesillik", "halka_farki", "kirmizilik", "merkez_parlaklik_farki",
    "kenar_uzakligi",
]
# Modele GİRMEYECEK sütunlar: kimlik ve konum bilgisi. Bunlar veri setinde
# hata ayıklamak ve bir satırı görüntüde bulmak için durur.
KIMLIK = ["yaprak", "bilesen", "x", "y"]


def aday_maske(bgr, yaprak):
    """Otsu eşiğiyle ham aday maskesi — MORFOLOJİ YOK.

    cercospora.lezyon_maskesi burada bir açma (opening) uygular ve toz
    zerrelerini bileşen hâline gelmeden siler. Veri seti için bunu bilerek
    yapmıyoruz: toz, damar parçası ve kenar artığı ELENMESİ GEREKEN ADAYLAR
    olarak veriye girmelidir.

    Aksi hâlde veri setindeki negatiflerin çoğu zaten temizlenmiş olur, sınıf
    dağılımı %85 pozitife kayar ve "her adaya leke de" diyen bir model yüksek
    doğruluk alır. Öğrenilecek karar kalmaz.

    Kapama (closing) korunur: o bir eleme adımı değil, tek lekenin iki parçaya
    bölünmesini engelleyen bir birleştirme adımıdır.
    """
    kanal = yesillik(bgr)
    icerik = kanal[yaprak > 0]
    if icerik.size == 0:
        return np.zeros(yaprak.shape, np.uint8)

    alt, ust = np.percentile(icerik, [1, 99])
    olcekli = np.clip((kanal - alt) / max(ust - alt, 1e-6), 0, 1) * 255
    olcekli = olcekli.astype(np.uint8)
    olcekli[yaprak == 0] = 255
    esik, _ = cv2.threshold(olcekli[yaprak > 0], 0, 255,
                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    maske = ((olcekli < esik) & (yaprak > 0)).astype(np.uint8) * 255
    return cv2.morphologyEx(maske, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))


def _momentten_uzama(parca):
    """Bileşenin uzunluk/genişlik oranı — ikinci derece momentlerden.

    Momentlerden türetilen eşdeğer elipsin eksen uzunlukları özdeğerlerin
    kareköküyle orantılıdır. Tek piksel genişliğindeki bir bileşende küçük
    özdeğer sıfıra gider; bu yüzden yarım pikselden küçük olmasına izin
    verilmiyor. Sonuç makul bir üst sınırla (en fazla 50) kırpılır — bundan
    büyük değerler bilgi taşımaz, yalnızca uç değer üretir.
    """
    m = cv2.moments(parca, binaryImage=True)
    if m["m00"] <= 0:
        return 1.0
    mu20 = m["mu20"] / m["m00"]
    mu02 = m["mu02"] / m["m00"]
    mu11 = m["mu11"] / m["m00"]
    ortak = math.sqrt(max((mu20 - mu02) ** 2 + 4 * mu11 ** 2, 0.0))
    lam1 = (mu20 + mu02 + ortak) / 2.0
    lam2 = (mu20 + mu02 - ortak) / 2.0
    buyuk = math.sqrt(max(lam1, 0.0))
    kucuk = max(math.sqrt(max(lam2, 0.0)), 0.5)
    return min(buyuk / kucuk, 50.0)


def _bilesen_oznitelikleri(parca, bgr, hsv, kanal, yaprak_uzaklik):
    """Tek bir bağlı bileşenden öznitelik vektörü çıkarır.

    parca: bileşeni gösteren 0/1 maske (uint8)
    """
    alan = float(parca.sum())
    kontur, _ = cv2.findContours(parca, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not kontur:
        return None
    c = max(kontur, key=cv2.contourArea)
    cevre = float(cv2.arcLength(c, True))
    if cevre <= 0:
        return None

    # Dairesellik tanımı gereği (0, 1] aralığındadır; 1 tam dairedir.
    # Küçük bileşenlerde poligon çevresi gerçek çevreyi OLDUĞUNDAN KISA
    # ölçtüğü için formül 1'i aşan değerler üretebilir. Fiziksel aralığa
    # sıkıştırıyoruz. cercospora.py'nin 0.45 eşiğiyle karşılaştırma bundan
    # etkilenmez; eşik zaten 1'in altındadır.
    dairesellik = min(4 * math.pi * alan / (cevre ** 2), 1.0)
    esdeger_cap = 2 * math.sqrt(alan / math.pi)

    # Doluluk (solidity): bileşen, kendi dışbükey kabuğunun ne kadarını
    # dolduruyor? Pay ve payda AYNI yöntemle ölçülmeli — piksel sayısını
    # poligon alanına bölmek küçük bileşenlerde 1'i aşan değerler üretir
    # (12 pikselik bir lekenin poligon alanı ~5 çıkar).
    kontur_alan = float(cv2.contourArea(c))
    kabuk_alan = float(cv2.contourArea(cv2.convexHull(c)))
    doluluk = min(kontur_alan / kabuk_alan, 1.0) if kabuk_alan > 0 else 0.0

    x, y, w, h = cv2.boundingRect(c)
    dolgunluk = alan / float(w * h) if w * h > 0 else 0.0
    en_boy = w / float(h) if h > 0 else 0.0

    # Uzama, ikinci derece merkezsel momentlerden hesaplanır.
    # cv2.fitEllipse kullanılmıyor: noktalar neredeyse doğrusal olduğunda
    # NaN ya da on binlere varan saçma eksen uzunlukları döndürüyor, bu da
    # ölçeklemeye duyarlı modelleri (k-NN, lojistik regresyon) bozuyor.
    # Momentler her bileşen için tanımlıdır ve sınırlı değer üretir.
    uzama = _momentten_uzama(parca)

    ic = parca > 0
    ort_h = float(hsv[..., 0][ic].mean())
    ort_s = float(hsv[..., 1][ic].mean())
    ort_v = float(hsv[..., 2][ic].mean())
    std_v = float(hsv[..., 2][ic].std())
    ort_yesillik = float(kanal[ic].mean())

    # Kırmızılık (R - G): Cercospora halkası kırmızı-kahve, yaprak yeşildir.
    g = bgr[..., 1].astype(np.float32)
    r = bgr[..., 2].astype(np.float32)
    kirmizilik = float((r[ic] - g[ic]).mean())

    # Halka farkı: Cercospora lekesinin çevresi, lekenin kendisinden koyudur.
    # Bileşeni genişletip orijinalini çıkararak bir halka elde ediyoruz.
    genis = cv2.dilate(parca, np.ones((5, 5), np.uint8), iterations=1)
    halka = (genis > 0) & (~ic)
    halka_farki = float(hsv[..., 2][halka].mean() - ort_v) if halka.sum() > 0 else 0.0

    # Merkez parlaklık farkı: lekenin gri merkezi, lekenin tamamından açıktır.
    kucuk_maske = cv2.erode(parca, np.ones((3, 3), np.uint8), iterations=1) > 0
    merkez_farki = (float(hsv[..., 2][kucuk_maske].mean() - ort_v)
                    if kucuk_maske.sum() > 0 else 0.0)

    # Yaprak kenarına uzaklık: kenar kuruması kenarda olur, leke içeride.
    kenar_uzakligi = float(yaprak_uzaklik[ic].mean())

    return dict(
        alan=round(alan, 1), cevre=round(cevre, 2),
        dairesellik=round(dairesellik, 4), esdeger_cap=round(esdeger_cap, 2),
        doluluk=round(doluluk, 4), dolgunluk=round(dolgunluk, 4),
        uzama=round(uzama, 4), en_boy_orani=round(en_boy, 4),
        ort_h=round(ort_h, 2), ort_s=round(ort_s, 2), ort_v=round(ort_v, 2),
        std_v=round(std_v, 2), ort_yesillik=round(ort_yesillik, 2),
        halka_farki=round(halka_farki, 2), kirmizilik=round(kirmizilik, 2),
        merkez_parlaklik_farki=round(merkez_farki, 2),
        kenar_uzakligi=round(kenar_uzakligi, 2),
    )


def _leke_sayisi_sec(rng):
    """SIDDET_DAGILIMI'na göre bir yaprak için leke sayısı seçer."""
    p = float(rng.random())
    birikimli = 0.0
    for oran, alt, ust in SIDDET_DAGILIMI:
        birikimli += oran
        if p <= birikimli:
            return int(rng.integers(alt, ust + 1))
    return int(rng.integers(*SIDDET_DAGILIMI[-1][1:]))


def yapraktan_satirlar(gorsel, gercek, ad):
    """Bir yaprak görüntüsünden etiketli satırları üretir.

    Döner: (satirlar, bulunan_leke_sayisi, toplam_leke_sayisi)
    """
    rgb = np.array(gorsel.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    yaprak = yaprak_maskesi(bgr)
    maske = aday_maske(bgr, yaprak)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    kanal = yesillik(bgr)

    # Her pikselin yaprak kenarına uzaklığı.
    # Işık kaydırılmış bazı görüntülerde HSV filtresi tüm kareyi yaprak sayıyor;
    # o durumda maskede hiç arka plan pikseli kalmıyor ve distanceTransform
    # sonsuz üretiyor. Sonsuz tek bir satırda bile sklearn'ü durdurur, bu yüzden
    # görüntü köşegeniyle sınırlıyoruz: hiçbir uzaklık ondan büyük olamaz.
    kosegen = float(math.hypot(*yaprak.shape))
    yaprak_uzaklik = cv2.distanceTransform((yaprak > 0).astype(np.uint8), cv2.DIST_L2, 5)
    yaprak_uzaklik = np.nan_to_num(yaprak_uzaklik, nan=0.0,
                                   posinf=kosegen, neginf=0.0)
    yaprak_uzaklik = np.clip(yaprak_uzaklik, 0.0, kosegen)

    sayi, etiket, istat, merkez = cv2.connectedComponentsWithStats(maske, 8)
    satirlar = []
    eslesen_lekeler = set()

    for i in range(1, sayi):
        if int(istat[i, cv2.CC_STAT_AREA]) < EN_KUCUK_BILESEN:
            continue
        parca = (etiket == i).astype(np.uint8)
        oz = _bilesen_oznitelikleri(parca, bgr, hsv, kanal, yaprak_uzaklik)
        if oz is None:
            continue

        mx, my = float(merkez[i][0]), float(merkez[i][1])
        etiket_degeri, en_yakin = 0, None
        for j, lk in enumerate(gercek):
            d = math.hypot(mx - lk["x"], my - lk["y"])
            if d <= lk["r"] + TOLERANS:
                etiket_degeri = 1
                en_yakin = j
                break
        if en_yakin is not None:
            eslesen_lekeler.add(en_yakin)

        satirlar.append(dict(yaprak=ad, bilesen=i, x=round(mx, 1), y=round(my, 1),
                             **oz, lezyon=etiket_degeri))

    return satirlar, len(eslesen_lekeler), len(gercek)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--yaprak", type=int, default=300, help="üretilecek yaprak sayısı")
    ap.add_argument("--cikti", default="data/madencilik")
    ap.add_argument("--tohum", type=int, default=20261018)
    ap.add_argument("--cesitlilik", type=float, default=1.0,
                    help="0 = sabit renk (panel modu), 1 = gerçekçi değişkenlik")
    a = ap.parse_args()

    hedef = KOK / a.cikti
    hedef.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.tohum)

    satirlar, bulunan, toplam = [], 0, 0
    for i in range(a.yaprak):
        adet = _leke_sayisi_sec(rng)
        tohum = int(a.tohum + i)
        gorsel, gercek = yaprak_uret(tohum, adet, cesitlilik=a.cesitlilik)
        ad = f"yaprak_{i:04d}"
        s, b, t = yapraktan_satirlar(gorsel, gercek, ad)
        satirlar.extend(s)
        bulunan += b
        toplam += t
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{a.yaprak} yaprak · {len(satirlar)} satır")

    if not satirlar:
        raise SystemExit("Hiç bileşen bulunamadı; segmentasyon bozuk olabilir.")

    basliklar = KIMLIK + OZNITELIKLER + ["lezyon"]
    csv_yol = hedef / "lezyonlar.csv"
    with csv_yol.open("w", encoding="utf-8", newline="") as f:
        y = csv.DictWriter(f, fieldnames=basliklar)
        y.writeheader()
        y.writerows(satirlar)

    pozitif = sum(r["lezyon"] for r in satirlar)
    negatif = len(satirlar) - pozitif
    kacirilan = 1 - (bulunan / toplam) if toplam else 0.0

    kunye = {
        "satir_sayisi": len(satirlar),
        "yaprak_sayisi": a.yaprak,
        "pozitif": pozitif,
        "negatif": negatif,
        "pozitif_orani": round(pozitif / len(satirlar), 4),
        "oznitelikler": OZNITELIKLER,
        "kimlik_sutunlari": KIMLIK,
        "hedef": "lezyon",
        "tohum": a.tohum,
        "tolerans_piksel": TOLERANS,
        "gercek_leke_toplami": toplam,
        "segmentasyonun_buldugu_leke": bulunan,
        "kacirilan_leke_orani": round(kacirilan, 4),
        "duyarlilik_tavani": round(1 - kacirilan, 4),
        "not": ("kacirilan_leke_orani, segmentasyonun hiç bileşen üretmediği "
                "lekelerin oranıdır. Hiçbir sınıflandırıcı bu lekeleri "
                "yakalayamaz; duyarlilik_tavani bu yüzden 1.0 değildir."),
    }
    (hedef / "kunye.json").write_text(
        json.dumps(kunye, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{csv_yol} yazıldı")
    print(f"  satır       : {len(satirlar)}")
    print(f"  pozitif     : {pozitif} ({pozitif / len(satirlar):.1%})")
    print(f"  negatif     : {negatif}")
    print(f"  öznitelik   : {len(OZNITELIKLER)}")
    print(f"  duyarlılık tavanı : {1 - kacirilan:.1%} "
          f"(segmentasyon {toplam} lekenin {bulunan} tanesini gördü)")


if __name__ == "__main__":
    main()
