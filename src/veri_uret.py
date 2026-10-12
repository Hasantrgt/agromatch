"""
AGROMATCH - Örnek veri üretici
==============================
DİKKAT: Bu script GERÇEK VERİ DEĞİL, gerçek veriyle aynı şemaya sahip
SİMÜLASYON verisi üretir. Amaç, analiz motorunu gerçek veri gelmeden
geliştirip test edebilmektir.

Üretilen veri, literatürdeki "domuz döngüsü" (cobweb / sürü etkisi)
davranışını bilinçli olarak içerir. Böylece analiz motorunun bu döngüyü
gerçekten yakalayıp yakalamadığı sınanabilir (bir tür birim test).

Gerçek veri geldiğinde bu script devre dışı kalır; data/ klasöründeki
CSV'ler aynı sütun isimleriyle gerçek veriyle değiştirilir.
Kaynaklar için bkz. README.md
"""

import numpy as np
import pandas as pd
from pathlib import Path

RASTGELE_TOHUM = 42
YILLAR = list(range(2015, 2026))
VERI_KLASORU = Path(__file__).resolve().parent.parent / "data"

# Ürün başlangıç parametreleri (Türkiye geneli, yaklaşık büyüklükler)
URUNLER = {
    "Domates": dict(alan_da=1_750_000, verim=7.2, kisi_basi_kg=88, ihracat_ton=600_000,
                    ithalat_ton=5_000, sanayi_orani=0.35, fire=0.12, esneklik=1.15),
    "Biber":   dict(alan_da=850_000,  verim=3.6, kisi_basi_kg=27, ihracat_ton=120_000,
                    ithalat_ton=2_000, sanayi_orani=0.15, fire=0.12, esneklik=1.35),
    "Patlıcan":dict(alan_da=270_000,  verim=3.2, kisi_basi_kg=10, ihracat_ton=35_000,
                    ithalat_ton=500,   sanayi_orani=0.08, fire=0.12, esneklik=1.5),
    "Salatalık":dict(alan_da=430_000, verim=4.4, kisi_basi_kg=22, ihracat_ton=90_000,
                    ithalat_ton=1_000, sanayi_orani=0.10, fire=0.12, esneklik=1.25),
    "Kabak":   dict(alan_da=180_000,  verim=2.8, kisi_basi_kg=6,  ihracat_ton=15_000,
                    ithalat_ton=200,   sanayi_orani=0.05, fire=0.12, esneklik=1.6),
}

# Başlangıçtaki yapısal denge durumu (1.00 = arz talebe eşit)
# Domates ve salatalıkta yapısal fazla, biberde açık varsayılmıştır.
BASLANGIC_DENGE = {"Domates": 1.22, "Biber": 0.88, "Patlıcan": 1.05,
                   "Salatalık": 1.12, "Kabak": 0.96}

# Pilot ilin (Antalya) ülke üretimindeki yaklaşık payı
PILOT_IL = "Antalya"
PILOT_PAY = {"Domates": 0.22, "Biber": 0.19, "Patlıcan": 0.17, "Salatalık": 0.28, "Kabak": 0.12}

NUFUS_BASLANGIC = 78_700_000
NUFUS_ARTIS = 0.008


def uret():
    rng = np.random.default_rng(RASTGELE_TOHUM)
    uretim_kayitlari, fiyat_kayitlari, talep_kayitlari = [], [], []

    for urun, p in URUNLER.items():
        # Başlangıç ekim alanı, ilk yılın ihtiyacına göre kalibre edilir
        # (denge oranı ~1.0'dan başlasın, döngü oradan salınsın)
        ilk_gida = NUFUS_BASLANGIC * p["kisi_basi_kg"] / 1000
        ilk_ihtiyac = ((ilk_gida * (1 + p["sanayi_orani"])) * (1 + p["fire"])
                       + p["ihracat_ton"] - p["ithalat_ton"])
        alan = ilk_ihtiyac / p["verim"] * BASLANGIC_DENGE[urun]

        reel_fiyat = 100.0          # 2015 = 100 reel fiyat endeksi
        onceki_fiyat_degisimi = 0.0

        for i, yil in enumerate(YILLAR):
            nufus = int(NUFUS_BASLANGIC * (1 + NUFUS_ARTIS) ** i)

            # --- SÜRÜ ETKİSİ: çiftçi GEÇEN yılın fiyatına bakarak bu yılın alanını belirler
            alan *= (1 + p["esneklik"] * onceki_fiyat_degisimi + rng.normal(0, 0.02))

            verim = p["verim"] * (1 + rng.normal(0, 0.06))       # hava/iklim dalgalanması
            uretim = alan * verim

            # --- Talep (analiz motoruyla aynı formül)
            kisi_basi = p["kisi_basi_kg"] * (1 + rng.normal(0, 0.015))
            gida = nufus * kisi_basi / 1000
            sanayi = gida * p["sanayi_orani"]
            fire = (gida + sanayi) * p["fire"]
            ihracat = p["ihracat_ton"] * (1 + 0.03 * i + rng.normal(0, 0.05))
            ithalat = p["ithalat_ton"]
            ihtiyac = gida + sanayi + fire + ihracat - ithalat

            # --- Fiyat: arz fazlası fiyatı düşürür (ters ilişki)
            denge = uretim / ihtiyac
            yeni_fiyat = reel_fiyat * (1 + (-0.9 * (denge - 1)) + rng.normal(0, 0.03))
            yeni_fiyat = float(np.clip(yeni_fiyat, 50, 200))
            onceki_fiyat_degisimi = (yeni_fiyat - reel_fiyat) / reel_fiyat
            reel_fiyat = yeni_fiyat

            uretim_kayitlari.append(dict(
                yil=yil, urun=urun, kapsam="Türkiye",
                ekim_alani_dekar=round(alan), verim_ton_dekar=round(verim, 3),
                uretim_ton=round(uretim)))
            uretim_kayitlari.append(dict(
                yil=yil, urun=urun, kapsam=PILOT_IL,
                ekim_alani_dekar=round(alan * PILOT_PAY[urun]),
                verim_ton_dekar=round(verim * 1.15, 3),        # sera ağırlıklı, verim daha yüksek
                uretim_ton=round(alan * PILOT_PAY[urun] * verim * 1.15)))
            fiyat_kayitlari.append(dict(
                yil=yil, urun=urun, reel_fiyat_endeksi=round(reel_fiyat, 2)))
            talep_kayitlari.append(dict(
                yil=yil, urun=urun, nufus=nufus,
                kisi_basi_tuketim_kg=round(kisi_basi, 2),
                ihracat_ton=round(ihracat), ithalat_ton=ithalat,
                sanayi_isleme_orani=p["sanayi_orani"], fire_orani=p["fire"]))

    VERI_KLASORU.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(uretim_kayitlari).to_csv(VERI_KLASORU / "uretim.csv", index=False)
    pd.DataFrame(fiyat_kayitlari).to_csv(VERI_KLASORU / "fiyat.csv", index=False)
    pd.DataFrame(talep_kayitlari).to_csv(VERI_KLASORU / "talep.csv", index=False)
    print(f"Örnek veri yazıldı -> {VERI_KLASORU}")


if __name__ == "__main__":
    uret()
