"""
AGROMATCH - Ham veriyi veri setine çeviren araç
===============================================
TÜİK'ten indirilen Excel dosyaları her seferinde farklı sütun adlarıyla gelir
("İl Adı", "İller", "Province", "Yıl", "Ekilen alan (dekar)"...). Bu araç
elindeki ham dosyayı inceler, sütunları kanonik şemaya eşler, doğrular ve
data/ klasörüne temiz CSV yazar.

ÜÇ ADIM

  1) İNCELE — dosyada ne var?
     python src/veri_al.py incele data/ham/tuik_uretim.xlsx

  2) DÖNÜŞTÜR — sütunları eşle ve yaz
     python src/veri_al.py donustur data/ham/tuik_uretim.xlsx --tip uretim \\
         --esle "yil=Yıl,kapsam=İl Adı,urun=Ürün Adı,
                 ekim_alani_dekar=Ekilen Alan(dekar),uretim_ton=Üretim(ton)"

  3) DOĞRULA — veri seti tutarlı mı?
     python src/veri_al.py dogrula

Kanonik şema (analiz kodunun beklediği hâl):

  uretim.csv : yil, urun, kapsam, ekim_alani_dekar, verim_ton_dekar, uretim_ton
  talep.csv  : yil, urun, nufus, kisi_basi_tuketim_kg, ihracat_ton, ithalat_ton,
               sanayi_isleme_orani, fire_orani
  fiyat.csv  : yil, urun, reel_fiyat_endeksi
  hayvan.csv : yil, il, buyukbas, kucukbas

Not: verim sütunu yoksa üretim/alan oranından hesaplanır; üretim yoksa
alan x verim ile tamamlanır. İkisi birden eksikse satır reddedilir.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
VERI = KOK / "data"

SEMA = {
    "uretim": dict(
        dosya="uretim.csv",
        zorunlu=["yil", "urun", "kapsam"],
        sayisal=["ekim_alani_dekar", "verim_ton_dekar", "uretim_ton"],
        aralik={"ekim_alani_dekar": (0, 50_000_000),
                "verim_ton_dekar": (0, 25),
                "uretim_ton": (0, 50_000_000)},
        anahtar=["yil", "urun", "kapsam"]),
    "talep": dict(
        dosya="talep.csv",
        zorunlu=["yil", "urun"],
        sayisal=["nufus", "kisi_basi_tuketim_kg", "ihracat_ton", "ithalat_ton",
                 "sanayi_isleme_orani", "fire_orani"],
        aralik={"kisi_basi_tuketim_kg": (0, 400), "sanayi_isleme_orani": (0, 1),
                "fire_orani": (0, 1)},
        anahtar=["yil", "urun"]),
    "fiyat": dict(
        dosya="fiyat.csv",
        zorunlu=["yil", "urun"],
        sayisal=["reel_fiyat_endeksi"],
        aralik={"reel_fiyat_endeksi": (0, 2000)},
        anahtar=["yil", "urun"]),
    "hayvan": dict(
        dosya="hayvan.csv",
        zorunlu=["yil", "il"],
        sayisal=["buyukbas", "kucukbas"],
        aralik={"buyukbas": (0, 5_000_000), "kucukbas": (0, 20_000_000)},
        anahtar=["yil", "il"]),
}

# Sık karşılaşılan sütun adları — otomatik eşleme denemesi için
TAHMIN = {
    "yil": ["yil", "yıl", "year", "donem", "dönem"],
    "kapsam": ["il", "iladi", "ilad", "iller", "province", "sehir", "şehir", "kapsam"],
    "il": ["il", "iladi", "iller", "province"],
    "urun": ["urun", "ürün", "urunadi", "ürünadı", "crop", "mahsul"],
    "ekim_alani_dekar": ["ekilenalan", "ekimalani", "alan", "area", "ekilisalani"],
    "uretim_ton": ["uretim", "üretim", "production", "uretimmiktari"],
    "verim_ton_dekar": ["verim", "yield"],
    "buyukbas": ["buyukbas", "büyükbaş", "sigir", "sığır"],
    "kucukbas": ["kucukbas", "küçükbaş", "koyun", "keci", "keçi"],
    "nufus": ["nufus", "nüfus", "population"],
    "reel_fiyat_endeksi": ["fiyat", "price", "endeks"],
}


def _sadelestir(s):
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if c.isalnum())


def tr_sayi(deger):
    """Türkçe biçimli sayıyı güvenle çözer.

    TUZAK: pandas "853.169" değerini ondalık sayı sanıp 853,169 olarak okur —
    oysa bu 853 bin 169'dur. Bu yüzden dosyalar METİN olarak okunur ve sayılar
    burada çözülür. Kural: noktadan sonra tam üç rakam varsa nokta binlik
    ayracıdır; virgül her zaman ondalık ayracıdır.
    """
    if deger is None:
        return None
    m = str(deger).strip()
    if not m or m.lower() in ("nan", "none", "-", "—", ".."):
        return None
    m = re.sub(r"[^\d,.\-]", "", m)
    if not m or m in ("-", ".", ","):
        return None
    if "," in m:                                   # virgül varsa: ondalık virgül
        m = m.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", m):  # 853.169 ya da 1.234.567
        m = m.replace(".", "")
    try:
        return float(m)
    except ValueError:
        return None


def dosya_oku(yol, sayfa=None):
    """Her şeyi METİN olarak okur — sayı çözümü tr_sayi'ye bırakılır."""
    yol = Path(yol)
    if not yol.is_absolute():
        yol = KOK / yol
    if yol.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(yol, sheet_name=sayfa or 0, dtype=str)
    for ayrac in (";", ",", "\t"):
        try:
            df = pd.read_csv(yol, sep=ayrac, encoding="utf-8-sig", dtype=str)
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    return pd.read_csv(yol, dtype=str)


def incele(yol, sayfa=None):
    yol_tam = KOK / yol if not Path(yol).is_absolute() else Path(yol)
    if yol_tam.suffix.lower() in (".xlsx", ".xls"):
        sayfalar = pd.ExcelFile(yol_tam).sheet_names
        print(f"Sayfalar: {', '.join(sayfalar)}\n")
    df = dosya_oku(yol, sayfa)
    print(f"{len(df):,} satır, {df.shape[1]} sütun\n".replace(",", "."))
    print(f"{'SÜTUN':<38}{'TİP':<10}{'DOLU':>8}{'TEKİL':>8}  ÖRNEK DEĞER")
    for s in df.columns:
        ornek = df[s].dropna().iloc[0] if df[s].notna().any() else "-"
        print(f"{str(s)[:36]:<38}{str(df[s].dtype):<10}{df[s].notna().sum():>8}"
              f"{df[s].nunique():>8}  {str(ornek)[:28]}")

    print("\nOtomatik eşleme önerisi:")
    duz = {_sadelestir(s): s for s in df.columns}
    oneri = []
    for hedef, adaylar in TAHMIN.items():
        for a in adaylar:
            eslesen = next((asil for temiz, asil in duz.items() if a in temiz), None)
            if eslesen:
                oneri.append(f"{hedef}={eslesen}")
                break
    print("  --esle \"" + ",".join(oneri) + "\"" if oneri else "  (eşleşme bulunamadı)")


def donustur(yol, tip, esle, sayfa=None, uzun_format=None):
    if tip not in SEMA:
        sys.exit(f"Bilinmeyen tip: {tip}. Seçenekler: {', '.join(SEMA)}")
    sema = SEMA[tip]
    df = dosya_oku(yol, sayfa)

    eslesme = {}
    for parca in esle.split(","):
        if "=" not in parca:
            continue
        hedef, kaynak = parca.split("=", 1)
        eslesme[hedef.strip()] = kaynak.strip()

    eksik = [k for k in eslesme.values() if k not in df.columns]
    if eksik:
        sys.exit(f"Dosyada bulunmayan sütunlar: {', '.join(eksik)}\n"
                 f"Mevcut sütunlar: {', '.join(map(str, df.columns))}")

    yeni = pd.DataFrame({hedef: df[kaynak] for hedef, kaynak in eslesme.items()})

    # Sayısal temizlik (binlik ayracı ve ondalık virgül dahil)
    for s in sema["sayisal"]:
        if s in yeni.columns:
            yeni[s] = yeni[s].map(tr_sayi)

    if "yil" in yeni.columns:
        yeni["yil"] = yeni["yil"].map(tr_sayi).astype("Int64")

    # Üretim / alan / verim üçlüsünü tamamla
    if tip == "uretim":
        a, v, u = "ekim_alani_dekar", "verim_ton_dekar", "uretim_ton"
        for s in (a, v, u):
            if s not in yeni.columns:
                yeni[s] = pd.Series([float("nan")] * len(yeni), dtype="float64")
            else:
                yeni[s] = yeni[s].astype("float64")
        bos_v = yeni[v].isna() & yeni[a].notna() & yeni[u].notna() & (yeni[a] > 0)
        if bos_v.any():
            yeni.loc[bos_v, v] = (yeni.loc[bos_v, u] / yeni.loc[bos_v, a]).round(4)
        bos_u = yeni[u].isna() & yeni[a].notna() & yeni[v].notna()
        if bos_u.any():
            yeni.loc[bos_u, u] = (yeni.loc[bos_u, a] * yeni.loc[bos_u, v]).round()
        if "kapsam" not in yeni.columns and "il" in yeni.columns:
            yeni = yeni.rename(columns={"il": "kapsam"})

    # Metin alanlarını düzelt
    for s in ("urun", "kapsam", "il"):
        if s in yeni.columns:
            yeni[s] = yeni[s].astype(str).str.strip()

    once = len(yeni)
    yeni = yeni.dropna(subset=[k for k in sema["zorunlu"] if k in yeni.columns])
    yeni = yeni.drop_duplicates(subset=[k for k in sema["anahtar"] if k in yeni.columns],
                                keep="last")

    VERI.mkdir(exist_ok=True)
    hedef = VERI / sema["dosya"]
    yeni.to_csv(hedef, index=False)
    print(f"{len(yeni):,} satır yazıldı -> {hedef}".replace(",", "."))
    if once != len(yeni):
        print(f"  ({once - len(yeni)} satır eksik zorunlu alan ya da tekrar nedeniyle atıldı)")
    print()
    raporla(tip, yeni)


def raporla(tip, df):
    sema = SEMA[tip]
    print(f"{'ALAN':<26}{'DOLU %':>9}{'EN KÜÇÜK':>14}{'EN BÜYÜK':>14}  UYARI")
    for s in sema["sayisal"]:
        if s not in df.columns:
            print(f"{s:<26}{'YOK':>9}{'':>14}{'':>14}  sütun yok")
            continue
        dolu = 100 * df[s].notna().mean()
        uyari = ""
        if s in sema["aralik"] and df[s].notna().any():
            alt, ust = sema["aralik"][s]
            disari = ((df[s] < alt) | (df[s] > ust)).sum()
            if disari:
                uyari = f"{disari} değer beklenen aralık dışında ({alt}–{ust})"
        if dolu < 90 and not uyari:
            uyari = "eksik veri oranı yüksek"
        en_k = f"{df[s].min():,.2f}".replace(",", ".") if df[s].notna().any() else "-"
        en_b = f"{df[s].max():,.2f}".replace(",", ".") if df[s].notna().any() else "-"
        print(f"{s:<26}{dolu:>8.0f}%{en_k:>14}{en_b:>14}  {uyari}")

    if "yil" in df.columns and df["yil"].notna().any():
        print(f"\nYıl aralığı: {int(df['yil'].min())}–{int(df['yil'].max())} "
              f"({df['yil'].nunique()} yıl)")
    for s in ("kapsam", "il", "urun"):
        if s in df.columns:
            print(f"{s}: {df[s].nunique()} farklı değer "
                  f"({', '.join(sorted(df[s].astype(str).unique())[:6])}…)")


def dogrula():
    """Veri setinin bütünlüğünü kontrol eder: dosyalar var mı, yıllar örtüşüyor mu?"""
    print(f"{'DOSYA':<16}{'DURUM':<10}{'SATIR':>9}{'YIL ARALIĞI':>16}")
    tablolar = {}
    for tip, sema in SEMA.items():
        yol = VERI / sema["dosya"]
        if not yol.exists():
            print(f"{sema['dosya']:<16}{'eksik':<10}{'-':>9}{'-':>16}")
            continue
        df = pd.read_csv(yol)
        tablolar[tip] = df
        aralik = (f"{int(df['yil'].min())}–{int(df['yil'].max())}"
                  if "yil" in df.columns and df["yil"].notna().any() else "-")
        print(f"{sema['dosya']:<16}{'var':<10}{len(df):>9}{aralik:>16}")

    if "uretim" in tablolar and "fiyat" in tablolar:
        u, f = tablolar["uretim"], tablolar["fiyat"]
        ortak = set(u["urun"].unique()) & set(f["urun"].unique())
        sadece_u = set(u["urun"].unique()) - ortak
        print(f"\nÜretim ve fiyat tablolarında ortak ürün: {len(ortak)}")
        if sadece_u:
            print(f"  Fiyatı olmayan ürünler: {', '.join(sorted(sadece_u)[:10])}")
            print("  (sürü etkisi testi bu ürünlerde çalışmaz)")

    if "uretim" in tablolar:
        u = tablolar["uretim"]
        if "kapsam" in u.columns:
            iller = sorted(u["kapsam"].unique())
            print(f"\nKapsamdaki il/bölge sayısı: {len(iller)}")
        bos_verim = u["verim_ton_dekar"].isna().sum() if "verim_ton_dekar" in u else 0
        if bos_verim:
            print(f"UYARI: {bos_verim} satırda verim hesaplanamadı "
                  f"(alan ya da üretim eksik).")
    print("\nSonraki adım: python src/bolge_analiz.py && python src/panel_uret.py")


def main():
    ap = argparse.ArgumentParser(description="Ham veriyi AGROMATCH şemasına çevirir.")
    alt = ap.add_subparsers(dest="komut", required=True)

    a1 = alt.add_parser("incele", help="dosyadaki sütunları ve örnek değerleri göster")
    a1.add_argument("dosya"); a1.add_argument("--sayfa", default=None)

    a2 = alt.add_parser("donustur", help="sütunları eşle ve kanonik CSV yaz")
    a2.add_argument("dosya")
    a2.add_argument("--tip", required=True, choices=list(SEMA))
    a2.add_argument("--esle", required=True, help="hedef=kaynak,hedef=kaynak…")
    a2.add_argument("--sayfa", default=None)

    alt.add_parser("dogrula", help="veri setinin bütünlüğünü kontrol et")

    a = ap.parse_args()
    if a.komut == "incele":
        incele(a.dosya, a.sayfa)
    elif a.komut == "donustur":
        donustur(a.dosya, a.tip, a.esle, a.sayfa)
    else:
        dogrula()


if __name__ == "__main__":
    main()
