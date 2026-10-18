"""
AGROMATCH - Toprak uygunluk: taban modeller ve "kuralı uygula" karşılaştırması
==============================================================================
toprak_veri_seti.py'nin ürettiği tabloyu okur ve üç hedefi modeller:

    uygunluk_puani   regresyon     (0–100)
    kisitlayici      7 sınıf       hangi toprak özelliği sınırlıyor
    tavanlandi       ikili         Liebig tavanı devreye girdi mi

ASIL SORU
Elimizde zaten kuralın kendisi var. O hâlde makine öğrenmesi niye?

Çünkü kuralı GERÇEK toprağa uygulamakla ÖLÇÜLEN toprağa uygulamak aynı şey
değildir. Tarlada gerçeğe erişimin yok; elinde yalnızca laboratuvar raporu
var ve o rapor hata taşıyor. Kuralı doğrudan rapora uygularsan, raporun
hatası sonuca olduğu gibi geçer.

Öğrenilen bir model bunu yapmak zorunda değildir. Eğitim sırasında binlerce
(hatalı ölçüm, gerçek sonuç) çiftini gördüğü için hatanın hangi yönde ve ne
büyüklükte olduğunu öğrenebilir; yani gürültüyü bir ölçüde ORTALAYABİLİR.

Tablodaki "Kuralı ölçülen değerlere uygula" satırı bu yüzden var: taban
çizgisi, formülün kendisidir. Öğrenilen model onu geçerse kazanılan şey yeni
bir formül değil, GÜRÜLTÜYE DAYANIKLILIKTIR.

NUMUNEYE GÖRE BÖLME
Bir numune dokuz satır üretir (dokuz ürün). Satıra göre bölersen aynı
toprağın bir ürünü eğitimde, bir başka ürünü testte olur ve model o toprağı
zaten görmüştür. Bölme numuneye göre yapılır.

Kullanım:
    python src/toprak_veri_seti.py --numune 400
    python src/toprak_taban_model.py
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

import mus_toprak as mt

KOK = Path(__file__).resolve().parent.parent
VERI = KOK / "data" / "madencilik"
CIKTI = KOK / "outputs"

SAYISAL = ["ph", "om", "kirec", "ec", "kil", "kum", "silt", "p2o5", "k2o", "derinlik"]
KATEGORIK = ["drenaj", "erozyon"]


def hazirla(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Öznitelik çerçevesini kurar: ölçülen değerler + ürün (sayısallaştırılmış).

    gercek_* sütunlarına DOKUNULMAZ — hedef onlardan hesaplandığı için
    öznitelik olarak verilirse sonuç anlamsız olur.
    """
    X = pd.DataFrame(index=df.index)
    for a in SAYISAL:
        X[a] = df[f"olculen_{a}"]
    X["erozyon"] = df["olculen_erozyon"]
    X["drenaj"] = df["olculen_drenaj"].map({"zayıf": 0, "orta": 1, "iyi": 2})
    for u in sorted(df["urun"].unique()):
        X[f"urun_{u}"] = (df["urun"] == u).astype(int)
    return X, list(X.columns)


def kurali_olcumlere_uygula(df: pd.DataFrame) -> pd.DataFrame:
    """Uzman kuralını, ölçülen (hatalı) değerlere uygular.

    Taban çizgisi budur: makine öğrenmesi olmadan, elimizdeki formülü
    laboratuvar raporuna doğrudan uygulayınca ne elde ediyoruz.
    """
    kayit = []
    for _, s in df.iterrows():
        toprak: dict[str, Any] = {a: float(s[f"olculen_{a}"]) for a in SAYISAL}
        toprak["drenaj"] = s["olculen_drenaj"]
        toprak["erozyon"] = int(s["olculen_erozyon"])
        o = mt.topraktan_uygunluk(toprak, s["urun"])
        kayit.append((o["puan"], o["kisitlayici"], int(o["tavanlandi"])))
    return pd.DataFrame(kayit, index=df.index,
                        columns=["puan", "kisitlayici", "tavanlandi"])


def siniflandir(ad: str, Xe, ye, Xt, yt, modeller) -> list[dict[str, Any]]:
    sonuc = []
    for mad, m in modeller.items():
        m.fit(Xe, ye)
        t = m.predict(Xt)
        sonuc.append(dict(hedef=ad, model=mad,
                          dogruluk=round(accuracy_score(yt, t), 4),
                          makro_f1=round(f1_score(yt, t, average="macro",
                                                  zero_division=0), 4)))
    return sonuc


def main() -> None:
    csv_yol = VERI / "toprak.csv"
    if not csv_yol.exists():
        raise SystemExit(f"{csv_yol} yok.\nÖnce üret:\n"
                         f"  python src/toprak_veri_seti.py --numune 400")
    df = pd.read_csv(csv_yol)
    X, sutunlar = hazirla(df)

    bolucu = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
    ei, ti = next(bolucu.split(X, groups=df["numune"]))
    Xe, Xt = X.iloc[ei].to_numpy(), X.iloc[ti].to_numpy()
    test_df = df.iloc[ti]

    print(f"Veri   : {len(df)} satır ({df['numune'].nunique()} numune × "
          f"{df['urun'].nunique()} ürün)")
    print(f"Bölme  : {df.iloc[ei]['numune'].nunique()} numune eğitim / "
          f"{test_df['numune'].nunique()} numune test (numuneye göre)")
    print(f"Öznitelik: {len(sutunlar)}\n")

    kural = kurali_olcumlere_uygula(test_df)
    tum: list[dict[str, Any]] = []

    # ---------------------------------------------------------- regresyon
    ye, yt = df.iloc[ei]["uygunluk_puani"].to_numpy(), test_df["uygunluk_puani"].to_numpy()
    print("=" * 74)
    print("HEDEF 1 — uygunluk puanı (regresyon, 0–100)")
    print("=" * 74)
    reg = {
        "Ortalamayı söyle (taban)": DummyRegressor(strategy="mean"),
        "Doğrusal regresyon": make_pipeline(StandardScaler(), LinearRegression()),
        "Karar ağacı (derinlik 6)": DecisionTreeRegressor(max_depth=6, random_state=42),
        "Rastgele orman": RandomForestRegressor(n_estimators=300, random_state=42,
                                                n_jobs=-1),
    }
    satirlar = [dict(model="Kuralı ölçülen değerlere uygula",
                     rmse=round(float(np.sqrt(mean_squared_error(yt, kural["puan"]))), 3),
                     mae=round(float(mean_absolute_error(yt, kural["puan"])), 3),
                     r2=round(float(r2_score(yt, kural["puan"])), 4))]
    for ad, m in reg.items():
        m.fit(Xe, ye)
        t = m.predict(Xt)
        satirlar.append(dict(model=ad,
                             rmse=round(float(np.sqrt(mean_squared_error(yt, t))), 3),
                             mae=round(float(mean_absolute_error(yt, t)), 3),
                             r2=round(float(r2_score(yt, t)), 4)))
    print(pd.DataFrame(satirlar).to_string(index=False))
    tum.extend([dict(hedef="uygunluk_puani", **s) for s in satirlar])

    # ----------------------------------------------- çok sınıflı: kısıtlayıcı
    print("\n" + "=" * 74)
    print("HEDEF 2 — kısıtlayıcı faktör (7 sınıf: hangi özellik sınırlıyor)")
    print("=" * 74)
    ye2 = df.iloc[ei]["kisitlayici"].to_numpy()
    yt2 = test_df["kisitlayici"].to_numpy()
    sinif_modelleri = {
        "En sık sınıfı söyle (taban)": DummyClassifier(strategy="most_frequent"),
        "Karar ağacı (derinlik 8)": DecisionTreeClassifier(max_depth=8, random_state=42),
        "Rastgele orman": RandomForestClassifier(n_estimators=300, random_state=42,
                                                 n_jobs=-1),
        "Lojistik regresyon": make_pipeline(StandardScaler(),
                                            LogisticRegression(max_iter=3000)),
    }
    s2 = [dict(model="Kuralı ölçülen değerlere uygula",
               dogruluk=round(accuracy_score(yt2, kural["kisitlayici"]), 4),
               makro_f1=round(f1_score(yt2, kural["kisitlayici"], average="macro",
                                       zero_division=0), 4))]
    for r in siniflandir("kisitlayici", Xe, ye2, Xt, yt2, sinif_modelleri):
        s2.append({k: v for k, v in r.items() if k != "hedef"})
    print(pd.DataFrame(s2).to_string(index=False))
    tum.extend([dict(hedef="kisitlayici", **s) for s in s2])

    # --------------------------------------------------- ikili: tavanlandi
    print("\n" + "=" * 74)
    print("HEDEF 3 — Liebig tavanı devreye girdi mi (ikili)")
    print("=" * 74)
    ye3 = df.iloc[ei]["tavanlandi"].to_numpy()
    yt3 = test_df["tavanlandi"].to_numpy()
    s3 = [dict(model="Kuralı ölçülen değerlere uygula",
               dogruluk=round(accuracy_score(yt3, kural["tavanlandi"]), 4),
               makro_f1=round(f1_score(yt3, kural["tavanlandi"], average="macro",
                                       zero_division=0), 4))]
    for r in siniflandir("tavanlandi", Xe, ye3, Xt, yt3, sinif_modelleri):
        s3.append({k: v for k, v in r.items() if k != "hedef"})
    print(pd.DataFrame(s3).to_string(index=False))
    tum.extend([dict(hedef="tavanlandi", **s) for s in s3])

    # ------------------------------------------------------ öznitelik önemi
    orman = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
    orman.fit(Xe, ye2)
    onem = pd.Series(orman.feature_importances_, index=sutunlar).sort_values(
        ascending=False)
    print("\n" + "=" * 74)
    print("ÖZNİTELİK ÖNEMİ — kısıtlayıcı faktörü ne belirliyor")
    print("=" * 74)
    for ad, d in onem.head(12).items():
        print(f"  {ad:<22} {d:.4f} {'█' * int(round(d * 70))}")

    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "toprak_madencilik.json").write_text(json.dumps(
        dict(sonuclar=tum,
             oznitelik_onemi={k: round(float(v), 5) for k, v in onem.items()},
             bolme="numuneye göre (GroupShuffleSplit, test_size=0.3)"),
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{CIKTI / 'toprak_madencilik.json'} yazıldı")


if __name__ == "__main__":
    main()
