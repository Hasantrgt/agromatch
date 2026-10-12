"""
AGROMATCH - Görüntü veri seti envanteri ve bölme (görüntü işleme projesi)
========================================================================
PlantVillage benzeri bir klasör yapısını (her sınıf bir klasör) tarar,
envanterini çıkarır ve eğitim/doğrulama/test kümelerine böler.

Veri setini indirmek için (Kaggle hesabı ve API anahtarı gerekir):
    pip install kaggle
    # kaggle.json dosyasını ~/.kaggle/ içine koy (Kaggle > Settings > Create New Token)
    kaggle datasets download -d vipoooool/new-plant-diseases-dataset
    unzip new-plant-diseases-dataset.zip -d data/goruntu

Kullanım:
    python src/veri_cek/goruntu_hazirla.py --kok data/goruntu --bol
    python src/veri_cek/goruntu_hazirla.py --kok data/goruntu --sinif-filtre domates biber

Çıktı:
    outputs/goruntu_envanter.csv   sınıf başına görüntü sayısı, ortalama boyut
    data/goruntu_bolunmus/{egitim,dogrulama,test}/<sınıf>/...  (--bol verilirse)

Not: Ders raporunda sınıf dengesizliği mutlaka tartışılmalıdır. Envanter tablosu
bunu gösterir; dengesizlik varsa ağırlıklandırma ya da veri artırma (augmentation)
gerekçesi buradan yazılır.
"""

import argparse
import random
import shutil
from collections import Counter
from pathlib import Path

import pandas as pd

UZANTILAR = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
KOK = Path(__file__).resolve().parent.parent.parent


def envanter(kok: Path, filtre):
    satirlar = []
    for sinif_dizin in sorted(p for p in kok.rglob("*") if p.is_dir()):
        dosyalar = [f for f in sinif_dizin.iterdir()
                    if f.is_file() and f.suffix.lower() in UZANTILAR]
        if not dosyalar:
            continue
        ad = sinif_dizin.name
        if filtre and not any(f.lower() in ad.lower() for f in filtre):
            continue
        boyutlar = [f.stat().st_size for f in dosyalar]
        satirlar.append(dict(
            sinif=ad, yol=str(sinif_dizin.relative_to(kok)),
            goruntu_sayisi=len(dosyalar),
            ortalama_kb=round(sum(boyutlar) / len(boyutlar) / 1024, 1)))
    return pd.DataFrame(satirlar).sort_values("goruntu_sayisi", ascending=False)


def bol(kok: Path, df, oranlar=(0.7, 0.15, 0.15), tohum=42):
    rastgele = random.Random(tohum)
    hedef = KOK / "data" / "goruntu_bolunmus"
    for kume in ("egitim", "dogrulama", "test"):
        (hedef / kume).mkdir(parents=True, exist_ok=True)

    sayac = Counter()
    for _, r in df.iterrows():
        dizin = kok / r["yol"]
        dosyalar = [f for f in dizin.iterdir()
                    if f.is_file() and f.suffix.lower() in UZANTILAR]
        rastgele.shuffle(dosyalar)
        n = len(dosyalar)
        k1, k2 = int(n * oranlar[0]), int(n * (oranlar[0] + oranlar[1]))
        for kume, parca in (("egitim", dosyalar[:k1]), ("dogrulama", dosyalar[k1:k2]),
                            ("test", dosyalar[k2:])):
            hedef_dizin = hedef / kume / r["sinif"]
            hedef_dizin.mkdir(parents=True, exist_ok=True)
            for f in parca:
                shutil.copy2(f, hedef_dizin / f.name)
            sayac[kume] += len(parca)
    return hedef, sayac


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", default="data/goruntu")
    ap.add_argument("--sinif-filtre", nargs="*", default=None)
    ap.add_argument("--bol", action="store_true")
    a = ap.parse_args()

    kok = (KOK / a.kok) if not Path(a.kok).is_absolute() else Path(a.kok)
    if not kok.exists():
        print(f"Klasör bulunamadı: {kok}\nÖnce veri setini indirip buraya açman gerekiyor.")
        return

    df = envanter(kok, a.sinif_filtre)
    if df.empty:
        print("Görüntü bulunamadı. Klasör yapısı 'sınıf adı/görüntüler' şeklinde olmalı.")
        return

    (KOK / "outputs").mkdir(exist_ok=True)
    df.to_csv(KOK / "outputs" / "goruntu_envanter.csv", index=False)
    print(df.to_string(index=False))
    print(f"\nToplam {df['goruntu_sayisi'].sum():,} görüntü, {len(df)} sınıf"
          .replace(",", "."))
    az, cok = df["goruntu_sayisi"].min(), df["goruntu_sayisi"].max()
    print(f"Sınıf dengesizliği: en az {az}, en çok {cok} görüntü (oran {cok / max(az,1):.1f}x)")

    if a.bol:
        hedef, sayac = bol(kok, df)
        print(f"\nBölündü -> {hedef}")
        for k, v in sayac.items():
            print(f"  {k:<11} {v:,}".replace(",", "."))


if __name__ == "__main__":
    main()
