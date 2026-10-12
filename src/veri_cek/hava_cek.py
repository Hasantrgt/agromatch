"""
AGROMATCH - Hava durumu verisi çekici (Open-Meteo arşiv API)
============================================================
23 il için geçmiş yıllara ait yağış ve sıcaklık verisini indirir.
Open-Meteo ücretsizdir ve API anahtarı istemez; akademik kullanımda serbesttir.

Çıktı: data/hava.csv
    il, yil, yillik_yagis_mm, kislik_yagis_mm, yazlik_yagis_mm,
    ortalama_sicaklik_c, don_gunu_sayisi

Neden önemli: verim tahmini ve fazla üretim sınıflandırması için en güçlü
açıklayıcı değişkenler yağış ve sıcaklıktır. Ayrıca don günü sayısı, risk
modülünün gerçek veriyle çalışmasını sağlar.

Kullanım:
    pip install requests pandas
    python src/veri_cek/hava_cek.py --baslangic 2010 --bitis 2024

Not: Her il için bir istek atılır ve istekler arasında bekleme konur.
API'nin günlük ücretsiz kotası vardır; 23 il x 15 yıl tek seferde rahat çeker.
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.append(str(Path(__file__).resolve().parent.parent))
from senaryo import KOORDINAT  # il -> (enlem, boylam)

API = "https://archive-api.open-meteo.com/v1/archive"
VERI = Path(__file__).resolve().parent.parent.parent / "data"

# Kışlık ürünler (buğday, arpa, mercimek) ekim-hasat dönemi: Ekim–Haziran
KISLIK_AYLAR = [10, 11, 12, 1, 2, 3, 4, 5, 6]
YAZLIK_AYLAR = [4, 5, 6, 7, 8, 9]


def il_cek(il, enlem, boylam, baslangic, bitis):
    p = dict(latitude=enlem, longitude=boylam,
             start_date=f"{baslangic}-01-01", end_date=f"{bitis}-12-31",
             daily="precipitation_sum,temperature_2m_mean,temperature_2m_min",
             timezone="Europe/Istanbul")
    r = requests.get(API, params=p, timeout=60)
    r.raise_for_status()
    g = r.json()["daily"]
    df = pd.DataFrame(g)
    df["time"] = pd.to_datetime(df["time"])
    df["yil"], df["ay"] = df["time"].dt.year, df["time"].dt.month
    df["il"] = il
    return df


def ozetle(df):
    satirlar = []
    for (il, yil), g in df.groupby(["il", "yil"]):
        kislik = g[g["ay"].isin(KISLIK_AYLAR)]["precipitation_sum"].sum()
        yazlik = g[g["ay"].isin(YAZLIK_AYLAR)]["precipitation_sum"].sum()
        satirlar.append(dict(
            il=il, yil=int(yil),
            yillik_yagis_mm=round(g["precipitation_sum"].sum(), 1),
            kislik_yagis_mm=round(kislik, 1),
            yazlik_yagis_mm=round(yazlik, 1),
            ortalama_sicaklik_c=round(g["temperature_2m_mean"].mean(), 2),
            don_gunu_sayisi=int((g["temperature_2m_min"] < 0).sum())))
    return pd.DataFrame(satirlar).sort_values(["il", "yil"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baslangic", type=int, default=2010)
    ap.add_argument("--bitis", type=int, default=2024)
    ap.add_argument("--bekleme", type=float, default=1.5, help="istekler arası saniye")
    a = ap.parse_args()

    parcalar = []
    for i, (il, (enlem, boylam)) in enumerate(KOORDINAT.items(), 1):
        try:
            parcalar.append(il_cek(il, enlem, boylam, a.baslangic, a.bitis))
            print(f"[{i:>2}/{len(KOORDINAT)}] {il} indirildi")
        except Exception as e:
            print(f"[{i:>2}/{len(KOORDINAT)}] {il} HATA: {e}")
        time.sleep(a.bekleme)

    if not parcalar:
        print("Hiç veri indirilemedi. İnternet bağlantısını kontrol et.")
        return
    ozet = ozetle(pd.concat(parcalar, ignore_index=True))
    VERI.mkdir(exist_ok=True)
    ozet.to_csv(VERI / "hava.csv", index=False)
    print(f"\n{len(ozet)} satır yazıldı -> {VERI / 'hava.csv'}")
    print(ozet.head(8).to_string(index=False))


if __name__ == "__main__":
    main()
