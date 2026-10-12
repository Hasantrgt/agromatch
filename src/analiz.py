"""
AGROMATCH - Analiz ve Planlama Motoru v1
========================================
Dört modül:
  1) Denge Analizi      : Arz / İhtiyaç oranı (ürün x yıl)
  2) Sürü Etkisi Testi  : Geçen yılın fiyatı bu yılın ekim alanını ne kadar belirliyor?
  3) Sezon Risk Skoru   : Gelecek sezon hangi ürün riskli, hangisi fırsat?
  4) Kota Motoru        : İhtiyaca göre hedef ekim alanı, il kotası ve çiftçi dağıtımı

Çıktı: outputs/sonuclar.json + ekrana özet tablo
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parent.parent
VERI = KOK / "data"
CIKTI = KOK / "outputs"

PILOT_IL = "Antalya"

# Denge oranı eşikleri
ESIK_FAZLA = 1.10     # bunun üstü: gereksiz ekim / fiyat çökme riski
ESIK_ACIK = 0.95      # bunun altı: arz açığı / ithalat baskısı


# ----------------------------------------------------------------------------
# 1) DENGE ANALİZİ
# ----------------------------------------------------------------------------
def denge_analizi(uretim: pd.DataFrame, talep: pd.DataFrame) -> pd.DataFrame:
    """Her ürün-yıl için ulusal arz ve ihtiyacı hesaplar.

    İhtiyaç = yurt içi gıda tüketimi + sanayi (salça vb.) + fire
              + ihracat - ithalat
    """
    tr = uretim[uretim["kapsam"] == "Türkiye"].merge(talep, on=["yil", "urun"])

    tr["yurtici_gida_ton"] = tr["nufus"] * tr["kisi_basi_tuketim_kg"] / 1000
    tr["sanayi_ton"] = tr["yurtici_gida_ton"] * tr["sanayi_isleme_orani"]
    tr["fire_ton"] = (tr["yurtici_gida_ton"] + tr["sanayi_ton"]) * tr["fire_orani"]
    tr["ihtiyac_ton"] = (tr["yurtici_gida_ton"] + tr["sanayi_ton"] + tr["fire_ton"]
                         + tr["ihracat_ton"] - tr["ithalat_ton"])

    tr["denge_orani"] = tr["uretim_ton"] / tr["ihtiyac_ton"]
    tr["fazla_ton"] = tr["uretim_ton"] - tr["ihtiyac_ton"]
    tr["durum"] = np.select(
        [tr["denge_orani"] > ESIK_FAZLA, tr["denge_orani"] < ESIK_ACIK],
        ["FAZLA EKİM", "ARZ AÇIĞI"], default="DENGEDE")

    return tr[["yil", "urun", "ekim_alani_dekar", "verim_ton_dekar", "uretim_ton",
               "ihtiyac_ton", "denge_orani", "fazla_ton", "durum"]]


# ----------------------------------------------------------------------------
# 2) SÜRÜ ETKİSİ (DOMUZ DÖNGÜSÜ) TESTİ
# ----------------------------------------------------------------------------
def suru_etkisi(uretim: pd.DataFrame, fiyat: pd.DataFrame) -> pd.DataFrame:
    """Hipotez: Çiftçi GEÇEN yılın fiyatına bakarak BU yılın ekim alanını belirler.
    Bu doğruysa, bir yıl gecikmeli fiyat değişimi ile alan değişimi pozitif
    korelasyon gösterir; aynı yılın alanı ile fiyatı ise negatif korelasyon verir.
    """
    tr = uretim[uretim["kapsam"] == "Türkiye"].merge(fiyat, on=["yil", "urun"])
    satirlar = []

    for urun, g in tr.groupby("urun"):
        g = g.sort_values("yil").copy()
        g["alan_degisim"] = g["ekim_alani_dekar"].pct_change()
        g["fiyat_degisim"] = g["reel_fiyat_endeksi"].pct_change()
        g["onceki_yil_fiyat_degisim"] = g["fiyat_degisim"].shift(1)
        g = g.dropna()

        # Geçen yılın fiyat değişimi -> bu yılın alan değişimi
        r_gecikmeli = g["onceki_yil_fiyat_degisim"].corr(g["alan_degisim"])
        # Aynı yıl: alan arttıkça fiyat düşüyor mu?
        r_esanli = g["alan_degisim"].corr(g["fiyat_degisim"])
        # Basit tepki katsayısı (esneklik): %1 fiyat artışı alanı % kaç artırıyor?
        egim = np.polyfit(g["onceki_yil_fiyat_degisim"], g["alan_degisim"], 1)[0]

        satirlar.append(dict(
            urun=urun,
            gecikmeli_korelasyon=round(float(r_gecikmeli), 3),
            esanli_korelasyon=round(float(r_esanli), 3),
            tepki_katsayisi=round(float(egim), 3),
            dongu_var=bool(r_gecikmeli > 0.35 and r_esanli < -0.25),
        ))

    return pd.DataFrame(satirlar)


# ----------------------------------------------------------------------------
# 3) SEZON RİSK SKORU
# ----------------------------------------------------------------------------
def sezon_riski(denge: pd.DataFrame, fiyat: pd.DataFrame, dongu: pd.DataFrame) -> pd.DataFrame:
    """Gelecek sezon için ürün bazında risk skoru ve öneri üretir.

    Risk iki sinyalin birleşimidir:
      A) Mevcut denge oranı zaten 1'in üstünde mi? (yapısal fazla)
      B) Geçen yıl fiyat sıçradı mı? (sürü etkisini tetikleyen sinyal)
    """
    son_yil = denge["yil"].max()
    d = denge[denge["yil"] == son_yil].set_index("urun")

    f = fiyat.sort_values("yil").groupby("urun")["reel_fiyat_endeksi"]
    fiyat_degisim = f.apply(lambda s: s.iloc[-1] / s.iloc[-2] - 1)

    dg = dongu.set_index("urun")
    satirlar = []

    for urun in d.index:
        denge_orani = float(d.loc[urun, "denge_orani"])
        fd = float(fiyat_degisim[urun])
        tepki = float(dg.loc[urun, "tepki_katsayisi"])

        # Beklenen alan artışı = geçen yılın fiyat değişimi x tepki katsayısı
        beklenen_alan_degisim = fd * tepki
        # Bu artış gerçekleşirse gelecek sezonun denge oranı
        tahmini_denge = denge_orani * (1 + beklenen_alan_degisim)

        risk = float(np.clip((tahmini_denge - 1) / 0.35, -1, 1))  # -1 açık ... +1 fazla

        if risk > 0.25:
            oneri = "EKİMİ SINIRLA - fiyat çökme riski yüksek"
        elif risk < -0.25:
            oneri = "EKİMİ ARTIR - arz açığı ve ithalat riski"
        else:
            oneri = "MEVCUT PLANI KORU"

        satirlar.append(dict(
            urun=urun,
            son_denge_orani=round(denge_orani, 3),
            gecen_yil_fiyat_degisimi=round(fd, 3),
            beklenen_alan_degisimi=round(beklenen_alan_degisim, 3),
            tahmini_gelecek_denge=round(tahmini_denge, 3),
            risk_skoru=round(risk, 3),
            oneri=oneri,
        ))

    return pd.DataFrame(satirlar).sort_values("risk_skoru", ascending=False)


# ----------------------------------------------------------------------------
# 4) KOTA / PLANLAMA MOTORU
# ----------------------------------------------------------------------------
def kota_hesapla(denge: pd.DataFrame, uretim: pd.DataFrame, il: str = PILOT_IL) -> pd.DataFrame:
    """İhtiyaca göre olması gereken ekim alanını ve pilot ilin kotasını hesaplar."""
    son_yil = denge["yil"].max()
    d = denge[denge["yil"] == son_yil]
    il_df = uretim[(uretim["kapsam"] == il) & (uretim["yil"] == son_yil)]
    tr_df = uretim[(uretim["kapsam"] == "Türkiye") & (uretim["yil"] == son_yil)]

    satirlar = []
    for _, r in d.iterrows():
        il_r = il_df[il_df["urun"] == r["urun"]].iloc[0]
        tr_r = tr_df[tr_df["urun"] == r["urun"]].iloc[0]

        # İlin ülke üretimindeki payı kadar ihtiyaç ona düşer;
        # hedef alan, İLİN kendi verimiyle hesaplanır (sera verimi farklıdır).
        pay = il_r["uretim_ton"] / tr_r["uretim_ton"]
        ihtiyac_il_ton = r["ihtiyac_ton"] * pay
        hedef_alan_il = ihtiyac_il_ton / il_r["verim_ton_dekar"]
        mevcut_alan_il = il_r["ekim_alani_dekar"]

        satirlar.append(dict(
            urun=r["urun"],
            il_payi=round(float(pay), 3),
            ihtiyac_il_ton=int(ihtiyac_il_ton),
            mevcut_alan_dekar=int(mevcut_alan_il),
            hedef_alan_dekar=int(hedef_alan_il),
            kalan_kota_dekar=int(hedef_alan_il - mevcut_alan_il),
            kota_doluluk=round(float(mevcut_alan_il / hedef_alan_il), 3),
        ))

    return pd.DataFrame(satirlar)


def ciftci_dagit(kota: pd.DataFrame, ciftciler: list[dict]) -> list[dict]:
    """Kotayı çiftçilere dağıtır; kota dolunca yeni öneriyi durdurur ve
    açık olan bir ürüne yönlendirir. (Sürü etkisine karşı koruma)
    """
    kalan = {r.urun: r.kalan_kota_dekar for r in kota.itertuples()}

    sonuc = []
    for c in ciftciler:
        istek, urun = c["arazi_dekar"], c["talep_ettigi_urun"]
        # Kotası en çok açık olan ürün = alternatif öneri (her başvuruda güncellenir)
        alternatif = max(kalan, key=kalan.get)
        if kalan.get(urun, 0) >= istek:
            kalan[urun] -= istek
            sonuc.append({**c, "onay": "ONAYLANDI", "atanan_urun": urun,
                          "atanan_dekar": istek,
                          "gerekce": "Kota içinde, alım güvenceli"})
        elif kalan.get(urun, 0) > 0:
            verilen = kalan[urun]
            kalan[urun] = 0
            sonuc.append({**c, "onay": "KISMİ", "atanan_urun": urun,
                          "atanan_dekar": int(verilen),
                          "gerekce": f"Kota doldu; kalan {istek - verilen:.0f} dekar için "
                                     f"{alternatif} öneriliyor"})
        else:
            alternatif = max(kalan, key=kalan.get)
            verilen = min(istek, max(kalan[alternatif], 0))
            kalan[alternatif] -= verilen
            sonuc.append({**c, "onay": "YÖNLENDİRİLDİ", "atanan_urun": alternatif,
                          "atanan_dekar": int(verilen),
                          "gerekce": f"{urun} kotası dolu (fiyat çökme riski); "
                                     f"{alternatif} arz açığında"})
    return sonuc


# ----------------------------------------------------------------------------
def main():
    uretim = pd.read_csv(VERI / "uretim.csv")
    fiyat = pd.read_csv(VERI / "fiyat.csv")
    talep = pd.read_csv(VERI / "talep.csv")

    denge = denge_analizi(uretim, talep)
    dongu = suru_etkisi(uretim, fiyat)
    risk = sezon_riski(denge, fiyat, dongu)
    kota = kota_hesapla(denge, uretim)

    # --- Çiftçi dağıtımı demosu: il kotasının tamamı değil, tek bir kooperatife
    # düşen dilim kullanılır (il kotasının binde 5'i ~ bir köy/kooperatif ölçeği).
    KOOP_PAYI = 0.005
    kota_koop = kota.copy()
    kota_koop["kalan_kota_dekar"] = (kota_koop["kalan_kota_dekar"] * KOOP_PAYI).round().astype(int)

    ciftciler = [
        dict(ciftci="Mehmet A.", ilce="Kumluca", arazi_dekar=25, talep_ettigi_urun="Domates"),
        dict(ciftci="Ayşe K.",   ilce="Serik",   arazi_dekar=40, talep_ettigi_urun="Domates"),
        dict(ciftci="Hasan T.",  ilce="Demre",   arazi_dekar=18, talep_ettigi_urun="Domates"),
        dict(ciftci="Fatma Y.",  ilce="Finike",  arazi_dekar=30, talep_ettigi_urun="Biber"),
        dict(ciftci="Ali D.",    ilce="Kumluca", arazi_dekar=22, talep_ettigi_urun="Salatalık"),
    ]
    dagitim = ciftci_dagit(kota_koop, ciftciler)

    CIKTI.mkdir(parents=True, exist_ok=True)
    denge.to_csv(CIKTI / "denge_analizi.csv", index=False)
    risk.to_csv(CIKTI / "sezon_riski.csv", index=False)
    kota.to_csv(CIKTI / "kota.csv", index=False)

    sonuc = dict(
        pilot_il=PILOT_IL,
        son_yil=int(denge["yil"].max()),
        denge=json.loads(denge.to_json(orient="records")),
        dongu=json.loads(dongu.to_json(orient="records")),
        risk=json.loads(risk.to_json(orient="records")),
        kota=json.loads(kota.to_json(orient="records")),
        dagitim=dagitim,
        fiyat=json.loads(fiyat.to_json(orient="records")),
    )
    (CIKTI / "sonuclar.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                                         encoding="utf-8")

    pd.set_option("display.width", 140)
    print("\n=== 1) DENGE ANALİZİ (son yıl) ===")
    print(denge[denge["yil"] == denge["yil"].max()].to_string(index=False))
    print("\n=== 2) SÜRÜ ETKİSİ TESTİ ===")
    print(dongu.to_string(index=False))
    print("\n=== 3) GELECEK SEZON RİSKİ ===")
    print(risk.to_string(index=False))
    print("\n=== 4) PİLOT İL KOTASI ===")
    print(kota.to_string(index=False))
    print("\n=== 5) ÇİFTÇİ DAĞITIMI ===")
    for d in dagitim:
        print(f" {d['ciftci']:<10} {d['ilce']:<9} {d['talep_ettigi_urun']:<10} "
              f"-> {d['onay']:<14} {d['atanan_urun']:<10} {d['atanan_dekar']:>4} da | {d['gerekce']}")


if __name__ == "__main__":
    main()
