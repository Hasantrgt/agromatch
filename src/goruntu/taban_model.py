"""
AGROMATCH - Lezyon sınıflandırma: taban modeller ve kural karşılaştırması
=========================================================================
lezyon_veri_seti.py'nin ürettiği tabloyu okur, birkaç klasik sınıflandırıcıyı
eğitir ve hepsini ELLE AYARLANMIŞ KURALLA karşılaştırır.

SORULAN SORU
cercospora.py bir bileşenin leke olup olmadığına şu kuralla karar verir:

    34 <= alan <= 1800  ve  dairesellik >= 0.45

Bu kural parametre taramasıyla bulundu, veriden öğrenilmedi. Buradaki soru:
aynı kararı veriden öğrenen bir model daha mı iyi, ve öğrendiği eşikler elle
konanlarla örtüşüyor mu?

YAPRAĞA GÖRE BÖLME — DİKKAT
Eğitim/test ayrımı SATIRA göre değil YAPRAĞA göre yapılır. Aynı yaprağın
bileşenleri aynı ışığı, aynı dokuyu ve aynı segmentasyon eşiğini paylaşır;
satıra göre bölünürse modelin test başarısı olduğundan yüksek çıkar. Bu,
görüntüden türetilen tablolarda en sık yapılan sızıntı hatasıdır.

Kullanım:
    python src/goruntu/lezyon_veri_seti.py --yaprak 300
    python src/goruntu/taban_model.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

KOK = Path(__file__).resolve().parent.parent.parent
VERI = KOK / "data" / "madencilik"
CIKTI = KOK / "outputs"

# cercospora.py'deki elle ayarlanmış eşikler
EL_MIN_ALAN, EL_MAKS_ALAN, EL_MIN_DAIRESELLIK = 34, 1800, 0.45


def el_kurali(df):
    """cercospora.py'nin kullandığı kural, sınıflandırıcı gibi uygulanır."""
    return ((df["alan"] >= EL_MIN_ALAN)
            & (df["alan"] <= EL_MAKS_ALAN)
            & (df["dairesellik"] >= EL_MIN_DAIRESELLIK)).astype(int).to_numpy()


def olc(ad, y, tahmin, olasilik=None):
    return dict(
        model=ad,
        dogruluk=round(accuracy_score(y, tahmin), 4),
        kesinlik=round(precision_score(y, tahmin, zero_division=0), 4),
        duyarlilik=round(recall_score(y, tahmin, zero_division=0), 4),
        f1=round(f1_score(y, tahmin, zero_division=0), 4),
        auc=round(roc_auc_score(y, olasilik), 4) if olasilik is not None else None,
    )


def main():
    csv_yol = VERI / "lezyonlar.csv"
    if not csv_yol.exists():
        raise SystemExit(
            f"{csv_yol} yok.\nÖnce veri setini üret:\n"
            f"  python src/goruntu/lezyon_veri_seti.py --yaprak 300")

    df = pd.read_csv(csv_yol)
    kunye = json.loads((VERI / "kunye.json").read_text(encoding="utf-8"))
    oznitelikler = kunye["oznitelikler"]

    X = df[oznitelikler].to_numpy()
    y = df["lezyon"].to_numpy()
    gruplar = df["yaprak"].to_numpy()

    bolucu = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
    egitim_i, test_i = next(bolucu.split(X, y, gruplar))
    Xe, Xt, ye, yt = X[egitim_i], X[test_i], y[egitim_i], y[test_i]

    print(f"Veri      : {len(df)} satır, {len(oznitelikler)} öznitelik")
    print(f"Bölme     : {len(np.unique(gruplar[egitim_i]))} yaprak eğitim / "
          f"{len(np.unique(gruplar[test_i]))} yaprak test (yaprağa göre)")
    print(f"Eğitim    : {len(ye)} satır, %{100 * ye.mean():.1f} pozitif")
    print(f"Test      : {len(yt)} satır, %{100 * yt.mean():.1f} pozitif\n")

    sonuclar = []

    # Taban çizgileri: bunları geçemeyen bir model işe yaramıyordur
    sabit = DummyClassifier(strategy="most_frequent").fit(Xe, ye)
    sonuclar.append(olc("Her zaman çoğunluk (taban)", yt, sabit.predict(Xt)))
    sonuclar.append(olc("Elle ayarlanmış kural", yt, el_kurali(df.iloc[test_i])))

    modeller = {
        "Karar ağacı (derinlik 3)": DecisionTreeClassifier(
            max_depth=3, random_state=42),
        "Karar ağacı (budanmış)": DecisionTreeClassifier(
            max_depth=6, min_samples_leaf=20, random_state=42),
        "Rastgele orman": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1),
        "k-NN (k=9)": make_pipeline(
            StandardScaler(), KNeighborsClassifier(n_neighbors=9)),
        "Lojistik regresyon": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000)),
        "Naive Bayes": GaussianNB(),
    }
    for ad, m in modeller.items():
        m.fit(Xe, ye)
        olasilik = m.predict_proba(Xt)[:, 1] if hasattr(m, "predict_proba") else None
        sonuclar.append(olc(ad, yt, m.predict(Xt), olasilik))

    tablo = pd.DataFrame(sonuclar)
    print(tablo.to_string(index=False))

    # --- Öğrenilen kural, elle konan kuralla karşılaştırılsın
    agac = modeller["Karar ağacı (derinlik 3)"]
    print("\n" + "=" * 72)
    print("KARAR AĞACININ ÖĞRENDİĞİ KURAL")
    print("=" * 72)
    print(export_text(agac, feature_names=oznitelikler, decimals=2))
    print(f"Elle konan kural: {EL_MIN_ALAN} <= alan <= {EL_MAKS_ALAN} "
          f"ve dairesellik >= {EL_MIN_DAIRESELLIK}")
    print("Ağacın kökteki eşiği bu değerlere yakınsa, elle konan eşik veriyle")
    print("doğrulanmış demektir. Uzaksa, elle konan eşik sorgulanmalıdır.")

    # --- Hangi öznitelik işe yarıyor
    orman = modeller["Rastgele orman"]
    onem = (pd.Series(orman.feature_importances_, index=oznitelikler)
            .sort_values(ascending=False))
    print("\n" + "=" * 72)
    print("ÖZNİTELİK ÖNEMİ (rastgele orman)")
    print("=" * 72)
    for ad, deger in onem.items():
        cubuk = "█" * int(round(deger * 60))
        print(f"  {ad:<24} {deger:.4f} {cubuk}")

    print("\nKarmaşıklık matrisi — rastgele orman (satır: gerçek, sütun: tahmin)")
    km = confusion_matrix(yt, orman.predict(Xt))
    print("          tahmin:0  tahmin:1")
    print(f"  gerçek:0 {km[0, 0]:8d}  {km[0, 1]:8d}")
    print(f"  gerçek:1 {km[1, 0]:8d}  {km[1, 1]:8d}")

    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "madencilik_taban.json").write_text(json.dumps(
        dict(sonuclar=sonuclar,
             oznitelik_onemi={k: round(float(v), 5) for k, v in onem.items()},
             agac_kurali=export_text(agac, feature_names=oznitelikler, decimals=2),
             el_kurali=dict(min_alan=EL_MIN_ALAN, maks_alan=EL_MAKS_ALAN,
                            min_dairesellik=EL_MIN_DAIRESELLIK),
             bolme="yaprağa göre (GroupShuffleSplit, test_size=0.3)",
             duyarlilik_tavani=kunye["duyarlilik_tavani"]),
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{CIKTI / 'madencilik_taban.json'} yazıldı")


if __name__ == "__main__":
    main()
