"""
AGROMATCH - Cercospora örneğinin panel verisini üretir
======================================================
Aşama görsellerini, şiddet örneklerini, doğrulama sonuçlarını ve parametre
taramasını tek bir JSON'a toplar. Görseller base64 olarak gömülür, böylece
panel tek dosya hâlinde çalışır (internet ya da yan dosya gerekmez).

Kullanım:
    python src/goruntu/sentetik_yaprak.py --adet 12
    python src/goruntu/cercospora_panel_veri.py
"""

import base64
import json
import sys
from pathlib import Path

import cv2

sys.path.append(str(Path(__file__).resolve().parent))
import cercospora as C

KOK = Path(__file__).resolve().parent.parent.parent
VERI = KOK / "data" / "sentetik"
CIKTI = KOK / "outputs"
GENISLIK = 440


def _b64(bgr, png=False):
    olcek = GENISLIK / bgr.shape[1]
    kucuk = cv2.resize(bgr, None, fx=olcek, fy=olcek, interpolation=cv2.INTER_AREA)
    if png:
        ok, tampon = cv2.imencode(".png", kucuk)
        tur = "png"
    else:
        ok, tampon = cv2.imencode(".jpg", kucuk, [cv2.IMWRITE_JPEG_QUALITY, 82])
        tur = "jpeg"
    if not ok:
        raise RuntimeError("görüntü kodlanamadı")
    return f"data:image/{tur};base64," + base64.b64encode(tampon).decode()


def parametre_taramasi():
    satirlar = []
    asil_alan, asil_dai = C.MIN_ALAN, C.MIN_DAIRESELLIK
    for alan in (22, 28, 34, 40, 48):
        C.MIN_ALAN = alan
        d = C.dogrula(VERI)
        satirlar.append(dict(min_alan=alan, kesinlik=d["kesinlik"],
                             duyarlilik=d["duyarlilik"], f1=d["f1"],
                             temiz_yaprak_yanlis_pozitif=d["satirlar"][0]["fp"]))
    C.MIN_ALAN, C.MIN_DAIRESELLIK = asil_alan, asil_dai
    return satirlar


def main():
    if not VERI.exists():
        print("Önce sentetik görüntüleri üret: python src/goruntu/sentetik_yaprak.py --adet 12")
        return

    # --- Aşama görselleri (orta şiddette bir yaprak)
    ornek = VERI / "yaprak_07.png"
    sonuc, ara = C.analiz_et(ornek)
    gorseller = C.asama_gorselleri(ara, sonuc["lezyonlar"])

    asamalar = [
        dict(no=1, ad="Girdi görüntüsü",
             aciklama="Tarladan çekilen yaprak fotoğrafı. Zemin, damarlar, azot sarılığı ve toz "
                      "zerreleri bilinçli olarak bırakıldı — algoritma bunları elemeyi başarmalı.",
             gorsel=_b64(gorseller["orijinal"])),
        dict(no=2, ad="Yaprak segmentasyonu",
             aciklama="HSV renk uzayında yeşil-sarı ton aralığı seçilir, en büyük bağlı bileşen "
                      "yaprak kabul edilir, delikler doldurulur ve kenar aşındırılır.",
             gorsel=_b64(gorseller["yaprak"], png=True)),
        dict(no=3, ad="Yeşillik kanalı",
             aciklama="G − (R+B)/2. Sağlıklı doku ve damarlar yüksek, lekeler düşük değer alır. "
                      "Azot sarılığı da yüksek kalır, böylece hastalıkla karışmaz.",
             gorsel=_b64(gorseller["kanal"])),
        dict(no=4, ad="Otsu eşikleme ve morfoloji",
             aciklama="Yaprak içindeki iki tepeli dağılımdan eşik bulunur; açma işlemi toz "
                      "zerrelerini, kapama işlemi leke içindeki boşlukları temizler.",
             gorsel=_b64(gorseller["maske"], png=True)),
        dict(no=5, ad="Bileşen analizi ve karar",
             aciklama="Her bileşenin alanı, eşdeğer çapı ve daireselliği ölçülür. Dairesellik "
                      "filtresi damar gölgesi gibi çizgisel izleri eler; "
                      "kalanlar Cercospora lekesidir.",
             gorsel=_b64(gorseller["kaplama"])),
    ]

    # --- Şiddet basamakları
    siddet_ornek = []
    for dosya in ("yaprak_01.png", "yaprak_06.png", "yaprak_11.png"):
        s, a = C.analiz_et(VERI / dosya)
        g = C.asama_gorselleri(a, s["lezyonlar"])
        siddet_ornek.append(dict(
            dosya=dosya, leke_sayisi=s["leke_sayisi"],
            enfekte=s["enfekte_alan_yuzdesi"], siddet=s["siddet"],
            ortalama_cap=s["ortalama_cap_piksel"],
            gorsel=_b64(g["kaplama"])))

    dogrulama = C.dogrula(VERI)

    sonuc_json = dict(
        ornek={k: v for k, v in sonuc.items() if k != "lezyonlar"},
        asamalar=asamalar,
        siddet_olcegi=[dict(ust_sinir=u, seviye=s, ad=a, karar=k) for u, s, a, k in C.SIDDET],
        siddet_ornek=siddet_ornek,
        dogrulama=dogrulama,
        parametre_taramasi=parametre_taramasi(),
        parametreler=dict(min_alan=C.MIN_ALAN, maks_alan=C.MAKS_ALAN,
                          min_dairesellik=C.MIN_DAIRESELLIK),
    )
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "cercospora.json"
    yol.write_text(json.dumps(sonuc_json, ensure_ascii=False), encoding="utf-8")
    print(f"cercospora.json yazıldı ({yol.stat().st_size // 1024} KB)")
    print(f"Kesinlik {dogrulama['kesinlik']} · Duyarlılık {dogrulama['duyarlilik']} · "
          f"F1 {dogrulama['f1']}")


if __name__ == "__main__":
    main()
