"""
AGROMATCH - Hal fiyatı çekici (belediye açık veri portalları, CKAN API)
======================================================================
İzmir ve Konya büyükşehir belediyeleri günlük sebze-meyve hal fiyatlarını
CKAN tabanlı açık veri portallarında yayımlar. Bu script, veri setinin
kaynaklarını (resources) listeler, CSV'leri indirir ve ürün-yıl bazında
ortalama fiyata indirger.

Neden bu kaynak: TÜİK fiyat serisi il bazında ve ücretsiz değildir; belediye
hal verisi günlük, uzun yıllara yayılan ve indirilebilir tek açık fiyat kaynağıdır.
Fiyatlar TÜFE ile reelleştirilerek endeks hâline getirilir (bkz. --tufe).

Kullanım:
    pip install requests pandas
    python src/veri_cek/hal_cek.py --kesif                 # hangi yıllar var, sütunlar ne?
    python src/veri_cek/hal_cek.py --yil 2015 2024         # indir ve özetle

Çıktı: data/hal_fiyat.csv
    kaynak, yil, urun, ortalama_fiyat_tl_kg, kayit_sayisi
"""

import argparse
import io
import re
import sys
from pathlib import Path

import pandas as pd
import requests

VERI = Path(__file__).resolve().parent.parent.parent / "data"

PORTALLAR = {
    "izmir": ("https://acikveri.bizizmir.com", "sebze-ve-meyve-hal-fiyatlari"),
    "konya": ("https://acikveri.konya.bel.tr", "meyve-sebze-hal-fiyatlari"),
}

# Portallar sütun adlarını farklı yazar; hepsini tek şemaya indiriyoruz
AD_ESLESME = {
    "urun": ["mal_adi", "maladi", "urun_adi", "urunadi", "mal", "urun", "cins"],
    "fiyat": ["ortalama_ucret", "ortalama_fiyat", "birim_fiyat", "fiyat",
              "asgari_ucret", "azami_ucret", "ort_fiyat"],
    "tarih": ["tarih", "kayit_tarihi", "date", "islem_tarihi"],
}


def kaynaklari_getir(taban, paket):
    r = requests.get(f"{taban}/api/3/action/package_show", params={"id": paket}, timeout=60)
    r.raise_for_status()
    return r.json()["result"]["resources"]


def sutun_bul(sutunlar, anahtar):
    duz = {re.sub(r"[^a-z0-9_]", "", s.lower().replace(" ", "_")): s for s in sutunlar}
    for aday in AD_ESLESME[anahtar]:
        if aday in duz:
            return duz[aday]
    for temiz, asil in duz.items():
        if any(a in temiz for a in AD_ESLESME[anahtar]):
            return asil
    return None


def csv_oku(url):
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    for ayrac in (";", ","):
        for kodlama in ("utf-8-sig", "cp1254", "latin-1"):
            try:
                df = pd.read_csv(io.BytesIO(r.content), sep=ayrac, encoding=kodlama,
                                 low_memory=False)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
    raise ValueError("CSV okunamadı: " + url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kesif", action="store_true", help="kaynakları ve sütunları listele")
    ap.add_argument("--yil", type=int, nargs=2, metavar=("BAS", "BIT"), default=[2015, 2024])
    a = ap.parse_args()

    satirlar = []
    for ad, (taban, paket) in PORTALLAR.items():
        try:
            kaynaklar = kaynaklari_getir(taban, paket)
        except Exception as e:
            print(f"{ad}: kaynak listesi alınamadı ({e})")
            continue

        print(f"\n=== {ad.upper()} — {len(kaynaklar)} kaynak ===")
        for k in kaynaklar:
            yil_eslesme = re.search(r"(19|20)\d{2}", k.get("name", "") + k.get("url", ""))
            yil = int(yil_eslesme.group()) if yil_eslesme else None
            print(f"  {k.get('format','?'):<6} {yil or '-':<6} {k.get('name','')[:60]}")
            if a.kesif or not yil or not (a.yil[0] <= yil <= a.yil[1]):
                continue
            if (k.get("format") or "").upper() not in ("CSV", "XLSX", "XLS"):
                continue
            try:
                df = csv_oku(k["url"])
            except Exception as e:
                print(f"       indirilemedi: {e}")
                continue

            s_urun = sutun_bul(df.columns, "urun")
            s_fiyat = sutun_bul(df.columns, "fiyat")
            if not s_urun or not s_fiyat:
                print(f"       sütun eşleşmedi -> {list(df.columns)[:8]}")
                continue
            df[s_fiyat] = pd.to_numeric(
                df[s_fiyat].astype(str).str.replace(",", ".").str.replace(r"[^\d.]", "", regex=True),
                errors="coerce")
            g = df.groupby(s_urun)[s_fiyat].agg(["mean", "count"]).reset_index()
            for _, r in g.iterrows():
                satirlar.append(dict(kaynak=ad, yil=yil, urun=str(r[s_urun]).strip(),
                                     ortalama_fiyat_tl_kg=round(float(r["mean"]), 3),
                                     kayit_sayisi=int(r["count"])))
            print(f"       {len(g)} ürün özetlendi")

    if a.kesif:
        print("\nKeşif modu: indirme yapılmadı. Yıl aralığı seçip tekrar çalıştır.")
        return
    if not satirlar:
        print("\nVeri toplanamadı. Portal sütun adları değişmiş olabilir: --kesif ile bak.")
        return
    df = pd.DataFrame(satirlar).sort_values(["kaynak", "urun", "yil"])
    VERI.mkdir(exist_ok=True)
    df.to_csv(VERI / "hal_fiyat.csv", index=False)
    print(f"\n{len(df)} satır yazıldı -> {VERI / 'hal_fiyat.csv'}")


if __name__ == "__main__":
    main()
