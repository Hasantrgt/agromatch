"""
AGROMATCH - Cercospora yaprak lekesi tespiti (klasik görüntü işleme hattı)
=========================================================================
Şeker pancarında (Beta vulgaris) Cercospora beticola lekelerini bir yaprak
fotoğrafından sayar, kapladıkları alanı ölçer ve hastalık şiddetini sınıflar.

NEDEN DERİN ÖĞRENME DEĞİL (ya da: neden önce bu)?
Cercospora lekesinin tanımlayıcı özellikleri ölçülebilir: yuvarlak biçim,
gri merkez, kırmızı-kahve halka, 3–5 mm çap. Bu, klasik görüntü işlemenin tam
olarak çözdüğü problem tipidir ve üç avantajı vardır:
  1. Etiketli veri gerektirmez — hemen çalışır.
  2. Her adımı açıklanabilir; ziraat mühendisi neden o sonucun çıktığını görür.
  3. Yalnızca "hastalık var/yok" demez, ŞİDDET ölçer — ilaçlama kararı şiddete bağlıdır.
Derin öğrenme (CNN) ikinci aşamadır: farklı hastalıkları birbirinden ayırmak ve
saha koşullarındaki değişkenliği öğrenmek için gereklidir.

HAT (8 adım)
  1. Okuma ve ölçekleme
  2. Yaprak segmentasyonu     — HSV renk uzayında yeşil-sarı aralığı, en büyük bileşen
  3. Yeşillik kanalı          — G - (R+B)/2 ; lekeler bu kanalda çöker
  4. Otsu eşikleme            — yaprak içinde iki tepeli dağılımdan eşik
  5. Morfoloji                — açma (toz zerrelerini at), kapama, delik doldurma
  6. Bileşen analizi          — alan, eşdeğer çap, DAİRESELLİK (damar ve kenar kurumasını eler)
  7. Metrikler                — leke sayısı, enfekte alan oranı, ortalama çap
  8. Şiddet sınıfı ve karar   — ilaçlama eşiğiyle karşılaştırma

Kullanım:
    python src/goruntu/cercospora.py --gorsel data/sentetik/yaprak_07.png --asamalar
    python src/goruntu/cercospora.py --dogrula data/sentetik
"""

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

# Şiddet ölçeği: enfekte yaprak alanı yüzdesine göre
SIDDET = [
    (0.1, 0, "Temiz", "Leke yok. Haftalık tarla kontrolüne devam."),
    (1.0, 1, "İlk lekeler", "Enfeksiyon başlamış. Kontrol sıklığını 3 güne indir."),
    (5.0, 2, "İlaçlama eşiği", "Koruyucu fungisit uygulaması için doğru zaman."),
    (15.0, 3, "Gecikmiş", "Hastalık yayılıyor. Sistemik fungisit, 10–14 gün arayla tekrar."),
    (30.0, 4, "Ağır", "Şeker kaybı başladı. Yaprak yenilenmesi için bitki zorlanıyor."),
    (101.0, 5, "Epidemi", "Erken hasat ve gelecek sezon için ekim nöbeti değerlendirilmeli."),
]

MIN_ALAN, MAKS_ALAN = 34, 1800        # piksel (parametre taramasıyla seçildi)
MIN_DAIRESELLIK = 0.45


def yaprak_maskesi(bgr):
    """Adım 2 — yaprağı arka plandan ayır."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # yeşil-sarı ton aralığı; toprak kahverengisi ve gölge dışarıda kalır
    maske = cv2.inRange(hsv, (22, 35, 35), (95, 255, 255))
    maske = cv2.morphologyEx(maske, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    # en büyük bağlı bileşen = yaprak
    sayi, etiket, istat, _ = cv2.connectedComponentsWithStats(maske, 8)
    if sayi > 1:
        en_buyuk = 1 + int(np.argmax(istat[1:, cv2.CC_STAT_AREA]))
        maske = np.where(etiket == en_buyuk, 255, 0).astype(np.uint8)

    # lekeler yaprağın içinde "delik" gibi görünür; doldur
    dolu = maske.copy()
    h, w = maske.shape
    tampon = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(dolu, tampon, (0, 0), 255)
    maske = maske | cv2.bitwise_not(dolu)
    # kenar kurumasını analiz dışında tut
    return cv2.erode(maske, np.ones((7, 7), np.uint8), iterations=1)


def yesillik(bgr):
    """Adım 3 — yeşillik kanalı: G - (R+B)/2.

    Sağlıklı doku ve damarlar pozitif, lekeler sıfıra yakın ya da negatiftir.
    Azot sarılığı da yüksek kalır, böylece hastalıkla karışmaz.
    """
    b, g, r = cv2.split(bgr.astype(np.float32))
    return g - (r + b) / 2.0


def lezyon_maskesi(bgr, yaprak):
    """Adım 4–5 — eşikleme ve morfoloji."""
    kanal = yesillik(bgr)
    icerik = kanal[yaprak > 0]
    if icerik.size == 0:
        return np.zeros(yaprak.shape, np.uint8), 0.0

    # Yaprak içindeki değerleri 0–255'e ölçekle, Otsu ile eşik bul
    alt, ust = np.percentile(icerik, [1, 99])
    olcekli = np.clip((kanal - alt) / max(ust - alt, 1e-6), 0, 1) * 255
    olcekli = olcekli.astype(np.uint8)
    olcekli[yaprak == 0] = 255                       # arka planı "sağlıklı" say
    esik, _ = cv2.threshold(olcekli[yaprak > 0], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    maske = ((olcekli < esik) & (yaprak > 0)).astype(np.uint8) * 255

    maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    maske = cv2.morphologyEx(maske, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return maske, float(esik)


def lezyonlari_coz(maske):
    """Adım 6 — bileşen analizi ve biçim filtresi."""
    sayi, etiket, istat, merkez = cv2.connectedComponentsWithStats(maske, 8)
    lezyonlar, kabul_maske = [], np.zeros(maske.shape, np.uint8)
    for i in range(1, sayi):
        alan = int(istat[i, cv2.CC_STAT_AREA])
        if not (MIN_ALAN <= alan <= MAKS_ALAN):
            continue
        parca = (etiket == i).astype(np.uint8)
        kontur, _ = cv2.findContours(parca, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not kontur:
            continue
        cevre = cv2.arcLength(kontur[0], True)
        if cevre <= 0:
            continue
        dairesellik = 4 * math.pi * alan / (cevre ** 2)
        if dairesellik < MIN_DAIRESELLIK:
            continue                                  # damar gölgesi, çizgisel iz
        cap = 2 * math.sqrt(alan / math.pi)
        lezyonlar.append(dict(x=float(merkez[i][0]), y=float(merkez[i][1]),
                              alan=alan, cap=round(cap, 2),
                              dairesellik=round(dairesellik, 3)))
        kabul_maske |= parca * 255
    return lezyonlar, kabul_maske


def siddet_sinifi(oran):
    for esik, seviye, ad, karar in SIDDET:
        if oran < esik:
            return dict(seviye=seviye, ad=ad, karar=karar)
    return dict(seviye=5, ad="Epidemi", karar=SIDDET[-1][3])


def analiz_et(yol, mm_basina_piksel=None):
    bgr = cv2.imread(str(yol))
    if bgr is None:
        raise FileNotFoundError(yol)
    olcek = 1.0                                          # Adım 1
    if bgr.shape[1] > 900:
        olcek = 900 / bgr.shape[1]
        bgr = cv2.resize(bgr, None, fx=olcek, fy=olcek, interpolation=cv2.INTER_AREA)

    yaprak = yaprak_maskesi(bgr)
    ham_maske, esik = lezyon_maskesi(bgr, yaprak)
    lezyonlar, maske = lezyonlari_coz(ham_maske)

    yaprak_alan = int((yaprak > 0).sum())
    lezyon_alan = int(sum(l["alan"] for l in lezyonlar))
    oran = 100 * lezyon_alan / max(yaprak_alan, 1)
    caplar = [l["cap"] for l in lezyonlar]

    sonuc = dict(
        dosya=Path(yol).name,
        olcek=round(olcek, 4),
        yaprak_alani_piksel=yaprak_alan,
        leke_sayisi=len(lezyonlar),
        lezyon_alani_piksel=lezyon_alan,
        enfekte_alan_yuzdesi=round(oran, 3),
        ortalama_cap_piksel=round(float(np.mean(caplar)), 2) if caplar else 0.0,
        otsu_esigi=round(esik, 1),
        siddet=siddet_sinifi(oran),
        lezyonlar=lezyonlar,
    )
    if mm_basina_piksel:
        sonuc["ortalama_cap_mm"] = round(sonuc["ortalama_cap_piksel"] / mm_basina_piksel, 2)
        sonuc["leke_yogunlugu_cm2"] = round(
            len(lezyonlar) / (yaprak_alan / (mm_basina_piksel ** 2) / 100), 2)
    return sonuc, dict(bgr=bgr, yaprak=yaprak, maske=maske, kanal=yesillik(bgr))


def asama_gorselleri(ara, lezyonlar):
    """Panelde gösterilecek adım görselleri."""
    bgr, yaprak, maske, kanal = ara["bgr"], ara["yaprak"], ara["maske"], ara["kanal"]

    yaprak_gorsel = cv2.cvtColor(yaprak, cv2.COLOR_GRAY2BGR)
    kanal_n = cv2.normalize(kanal, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    kanal_gorsel = cv2.applyColorMap(kanal_n, cv2.COLORMAP_VIRIDIS)
    kanal_gorsel[yaprak == 0] = (30, 30, 30)
    maske_gorsel = cv2.cvtColor(maske, cv2.COLOR_GRAY2BGR)

    kaplama = bgr.copy()
    for n, l in enumerate(lezyonlar, 1):
        r = max(6, int(l["cap"] / 2) + 4)
        cv2.circle(kaplama, (int(l["x"]), int(l["y"])), r, (60, 230, 255), 2)
    cv2.putText(kaplama, f"{len(lezyonlar)} leke", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (60, 230, 255), 2, cv2.LINE_AA)
    return dict(orijinal=bgr, yaprak=yaprak_gorsel, kanal=kanal_gorsel,
                maske=maske_gorsel, kaplama=kaplama)


def dogrula(klasor):
    """Sentetik görüntülerde doğruluk ölçümü: tespit edilen lekeler gerçeklerle eşleşiyor mu?"""
    klasor = Path(klasor) if Path(klasor).is_absolute() else KOK / klasor
    gercekler = json.loads((klasor / "gercek_degerler.json").read_text(encoding="utf-8"))
    satirlar, tp_t, fp_t, fn_t = [], 0, 0, 0

    for kayit in gercekler:
        sonuc, _ = analiz_et(klasor / kayit["dosya"])
        olcek = sonuc["olcek"]        # analizde yeniden boyutlandırma yapıldıysa ölçekle
        gercek = [(g["x"] * olcek, g["y"] * olcek, g["r"] * olcek) for g in kayit["lekeler"]]
        bulunan = [(l["x"], l["y"]) for l in sonuc["lezyonlar"]]

        eslesen = set()
        tp = 0
        for bx, by in bulunan:
            for i, (gx, gy, gr) in enumerate(gercek):
                if i in eslesen:
                    continue
                if (bx - gx) ** 2 + (by - gy) ** 2 <= (max(gr, 8) * 1.6) ** 2:
                    eslesen.add(i); tp += 1; break
        fp = len(bulunan) - tp
        fn = len(gercek) - tp
        tp_t += tp; fp_t += fp; fn_t += fn
        satirlar.append(dict(dosya=kayit["dosya"], gercek=len(gercek),
                             bulunan=len(bulunan), tp=tp, fp=fp, fn=fn,
                             enfekte_yuzde=sonuc["enfekte_alan_yuzdesi"],
                             siddet=sonuc["siddet"]["ad"]))

    kesinlik = tp_t / max(tp_t + fp_t, 1)
    duyarlilik = tp_t / max(tp_t + fn_t, 1)
    f1 = 2 * kesinlik * duyarlilik / max(kesinlik + duyarlilik, 1e-9)
    sapma = [abs(s["bulunan"] - s["gercek"]) for s in satirlar]
    return dict(satirlar=satirlar,
                kesinlik=round(kesinlik, 3), duyarlilik=round(duyarlilik, 3),
                f1=round(f1, 3), ortalama_mutlak_sapma=round(float(np.mean(sapma)), 2),
                toplam=dict(tp=tp_t, fp=fp_t, fn=fn_t))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gorsel")
    ap.add_argument("--dogrula")
    ap.add_argument("--asamalar", action="store_true")
    ap.add_argument("--mm-piksel", type=float, default=None,
                    help="1 mm kaç piksel (cetvelle çekilen fotoğrafta)")
    a = ap.parse_args()
    CIKTI.mkdir(exist_ok=True)

    if a.gorsel:
        sonuc, ara = analiz_et(a.gorsel, a.mm_piksel)
        print(json.dumps({k: v for k, v in sonuc.items() if k != "lezyonlar"},
                         ensure_ascii=False, indent=2))
        if a.asamalar:
            hedef = CIKTI / "cercospora_asama"
            hedef.mkdir(exist_ok=True)
            for ad, g in asama_gorselleri(ara, sonuc["lezyonlar"]).items():
                cv2.imwrite(str(hedef / f"{ad}.png"), g)
            print(f"\nAşama görselleri -> {hedef}")

    if a.dogrula:
        d = dogrula(a.dogrula)
        print(f"\n{'DOSYA':<16}{'GERÇEK':>7}{'BULUNAN':>9}{'TP':>5}{'FP':>4}{'FN':>4}"
              f"{'ENFEKTE %':>11}  ŞİDDET")
        for s in d["satirlar"]:
            print(f"{s['dosya']:<16}{s['gercek']:>7}{s['bulunan']:>9}{s['tp']:>5}"
                  f"{s['fp']:>4}{s['fn']:>4}{s['enfekte_yuzde']:>11}  {s['siddet']}")
        print(f"\nKesinlik {d['kesinlik']}  Duyarlılık {d['duyarlilik']}  "
              f"F1 {d['f1']}  Ortalama sayım sapması {d['ortalama_mutlak_sapma']}")


if __name__ == "__main__":
    main()
