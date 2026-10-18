"""
AGROMATCH - Ölçüm hatası ne zaman makine öğrenmesini haklı çıkarır?
===================================================================
toprak_taban_model.py şaşırtıcı bir sonuç verdi: uzman kuralını doğrudan
laboratuvar raporuna uygulamak, öğrenilen her modeli yendi.

Bu beklenen bir sonuç aslında. Veri setindeki etiketler ZATEN o kuralla
üretiliyor; hiçbir model kendisini üreten kuralı geçemez. Modelin tek
kazanma yolu, kuralın yapamadığı bir şeyi yapmaktır: ÖLÇÜM GÜRÜLTÜSÜNÜ
ORTALAMAK.

Kural, raporu olduğu gibi alır ve hatayı sonuca aynen geçirir. Öğrenilen
model ise eğitimde binlerce (hatalı ölçüm → gerçek sonuç) çifti gördüğü için
hatanın yapısını öğrenir ve bir kısmını telafi edebilir.

Bu telafinin bir bedeli var: model kuralı yalnızca YAKLAŞIK öğrenir. Yani iki
etki ters yönde çalışıyor:

    yaklaşıklık kaybı   (model kuralı tam bilmiyor)      -> kural lehine
    gürültü telafisi    (model hatayı ortalayabiliyor)   -> model lehine

Gürültü küçükken birincisi, büyükken ikincisi baskın. Arada bir KESİŞİM
noktası olmalı. Bu betik onu ölçer: laboratuvar hatasını kademeli büyütüp
her kademede iki yaklaşımı karşılaştırır.

Pratik karşılığı doğrudan projeyle ilgili: laboratuvarımız ne kadar iyiyse
formüle güvenmek o kadar doğru; hata belli bir eşiği aşıyorsa öğrenmeye
geçmek gerekir.

Kullanım:
    pip install -r requirements-madencilik.txt
    python src/toprak_gurultu_deneyi.py
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GroupShuffleSplit

import mus_profil as mp
import mus_toprak as mt
import toprak_veri_seti as tvs

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "outputs"
BELGE = KOK / "belgeler"

CARPANLAR = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0)
NUMUNE = 400

SAYISAL = tvs.SAYISAL
KATEGORIK = tvs.KATEGORIK


def veri_uret(carpan: float, tohum: int) -> pd.DataFrame:
    """Belirli bir hata çarpanıyla veri seti üretir (dosyaya yazmadan)."""
    asil = dict(tvs.LAB_HATASI)
    try:
        for k in tvs.LAB_HATASI:
            tvs.LAB_HATASI[k] = asil[k] * carpan
        rng = np.random.default_rng(tohum)
        satirlar = []
        for i in range(NUMUNE):
            ilce = str(rng.choice(list(mp.ILCE)))
            gercek = tvs.numune_uret(rng, ilce, bool(rng.random() < 0.25))
            olculen = tvs.olc(rng, gercek)
            for urun in mp.URUN:
                s = mt.topraktan_uygunluk(gercek, urun)
                satir: dict[str, Any] = dict(numune=f"n{i:04d}", urun=urun,
                                             kisitlayici=s["kisitlayici"])
                for a in SAYISAL:
                    satir[f"olculen_{a}"] = float(olculen[a])
                for a in KATEGORIK:
                    satir[f"olculen_{a}"] = olculen[a]
                satirlar.append(satir)
        return pd.DataFrame(satirlar)
    finally:
        tvs.LAB_HATASI.update(asil)       # genel durumu bozmadan geri al


def oznitelikler(df: pd.DataFrame) -> pd.DataFrame:
    X = pd.DataFrame(index=df.index)
    for a in SAYISAL:
        X[a] = df[f"olculen_{a}"]
    X["erozyon"] = df["olculen_erozyon"]
    X["drenaj"] = df["olculen_drenaj"].map({"zayıf": 0, "orta": 1, "iyi": 2})
    for u in sorted(df["urun"].unique()):
        X[f"urun_{u}"] = (df["urun"] == u).astype(int)
    return X


def kural_dogrulugu(test: pd.DataFrame) -> float:
    tahmin = []
    for _, s in test.iterrows():
        t: dict[str, Any] = {a: float(s[f"olculen_{a}"]) for a in SAYISAL}
        t["drenaj"] = s["olculen_drenaj"]
        t["erozyon"] = int(s["olculen_erozyon"])
        tahmin.append(mt.topraktan_uygunluk(t, s["urun"])["kisitlayici"])
    return float(accuracy_score(test["kisitlayici"], tahmin))


def main() -> None:
    sonuc = []
    print(f"{'hata':>6}  {'kural':>7}  {'orman':>7}  {'fark':>7}")
    print("-" * 32)
    for carpan in CARPANLAR:
        df = veri_uret(carpan, tohum=20261018)
        X = oznitelikler(df)
        b = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
        ei, ti = next(b.split(X, groups=df["numune"]))
        test = df.iloc[ti]

        k = kural_dogrulugu(test)
        m = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
        m.fit(X.iloc[ei].to_numpy(), df.iloc[ei]["kisitlayici"].to_numpy())
        o = float(accuracy_score(test["kisitlayici"], m.predict(X.iloc[ti].to_numpy())))

        sonuc.append(dict(carpan=carpan, kural=round(k, 4), orman=round(o, 4),
                          fark=round(o - k, 4)))
        print(f"  x{carpan:<4} {k:7.3f}  {o:7.3f}  {o - k:+7.3f}")

    kesisim = None
    for a, b_ in zip(sonuc, sonuc[1:]):
        if a["fark"] < 0 <= b_["fark"]:
            # iki nokta arasında doğrusal ara değer
            oran = -a["fark"] / (b_["fark"] - a["fark"])
            kesisim = round(a["carpan"] + oran * (b_["carpan"] - a["carpan"]), 2)
            break

    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "toprak_gurultu_deneyi.json").write_text(json.dumps(
        dict(numune=NUMUNE, hedef="kisitlayici", sonuc=sonuc, kesisim=kesisim,
             not_=("kesisim, laboratuvar hatasının kaç katında öğrenilen modelin "
                   "kuralı geçtiğidir. 1.0 = toprak_veri_seti.py'deki varsayılan "
                   "hata düzeyi.")),
        ensure_ascii=False, indent=2), encoding="utf-8")

    BELGE.mkdir(exist_ok=True)
    (BELGE / "toprak_gurultu.svg").write_text(grafik(sonuc, kesisim),
                                              encoding="utf-8")
    print(f"\nkesişim: hata × {kesisim}")
    print(f"{CIKTI / 'toprak_gurultu_deneyi.json'}")
    print(f"{BELGE / 'toprak_gurultu.svg'}")


def grafik(sonuc: list[dict[str, Any]], kesisim: float | None) -> str:
    """İki seriyi tek eksende çizer. Dış bağımlılık yok — elle SVG.

    Panel de haritalarını böyle çiziyor; tek dosya ve kütüphanesiz kalmak
    bilinçli bir tercih. İki seri olduğu için hem gösterge hem doğrudan
    etiket var: kimlik yalnızca renge bırakılmıyor.
    """
    G, Y = 760, 430
    sol, sag, ust, alt = 72, 150, 78, 64
    gw, gh = G - sol - sag, Y - ust - alt
    xs = [s["carpan"] for s in sonuc]
    x0, x1 = min(xs), max(xs)
    y0, y1 = 0.45, 0.95

    def px(v): return sol + (v - x0) / (x1 - x0) * gw
    def py(v): return ust + (1 - (v - y0) / (y1 - y0)) * gh

    p = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {G} {Y}" '
         f'width="{G}" height="{Y}" font-family="Carlito, Arial, sans-serif">',
         f'<rect width="{G}" height="{Y}" fill="#fcfcfb"/>',
         f'<text x="{sol}" y="26" font-size="15" font-weight="600" fill="#16281f">'
         'Ölçüm hatası büyüdükçe kural zayıflar, öğrenilen model dayanır</text>',
         f'<text x="{sol}" y="44" font-size="11" fill="#5f6a5e">'
         'Kısıtlayıcı faktörü doğru bilme oranı · 400 numune × 9 ürün · '
         'numuneye göre bölme</text>']

    # Gösterge. Çizgi uçlarındaki doğrudan etiketler zaten kimliği taşıyor;
    # gösterge, grafiğin bir kısmı kırpılarak alıntılandığında da kimliğin
    # kaybolmaması için duruyor.
    gx = sol
    for renk, ad, genislik in (("#2a78d6", "Kuralı ölçüme uygula", 148),
                               ("#eb6834", "Rastgele orman", 0)):
        p.append(f'<rect x="{gx}" y="61" width="18" height="3" rx="1.5" '
                 f'fill="{renk}"/>')
        p.append(f'<text x="{gx + 24}" y="66" font-size="10.5" '
                 f'fill="#3c4a3e">{ad}</text>')
        gx += genislik

    for i in range(6):                                   # ızgara, geri planda
        v = y0 + (y1 - y0) * i / 5
        p.append(f'<line x1="{sol}" y1="{py(v):.1f}" x2="{sol + gw}" '
                 f'y2="{py(v):.1f}" stroke="#e6e4da" stroke-width="1"/>')
        p.append(f'<text x="{sol - 10}" y="{py(v) + 4:.1f}" font-size="10" '
                 f'fill="#7a7466" text-anchor="end">%{v * 100:.0f}</text>')
    for s in sonuc:
        p.append(f'<text x="{px(s["carpan"]):.1f}" y="{ust + gh + 20}" '
                 f'font-size="10" fill="#7a7466" text-anchor="middle">'
                 f'×{s["carpan"]:g}</text>')
    p.append(f'<text x="{sol + gw / 2:.0f}" y="{ust + gh + 44}" font-size="11" '
             f'fill="#5f6a5e" text-anchor="middle">'
             'laboratuvar hatasının katı (×1 = varsayılan düzey)</text>')

    if kesisim is not None and x0 <= kesisim <= x1:
        p.append(f'<line x1="{px(kesisim):.1f}" y1="{ust}" x2="{px(kesisim):.1f}" '
                 f'y2="{ust + gh}" stroke="#b4761a" stroke-width="1.5" '
                 'stroke-dasharray="5 4"/>')
        p.append(f'<text x="{px(kesisim) + 7:.1f}" y="{ust + 16}" font-size="10.5" '
                 f'fill="#8a5a12">kesişim ×{kesisim:g}</text>')

    for anahtar, renk, ad in (("kural", "#2a78d6", "Kuralı ölçüme uygula"),
                              ("orman", "#eb6834", "Rastgele orman")):
        d = " ".join(f'{"M" if i == 0 else "L"}{px(s["carpan"]):.1f},'
                     f'{py(s[anahtar]):.1f}' for i, s in enumerate(sonuc))
        p.append(f'<path d="{d}" fill="none" stroke="{renk}" stroke-width="2" '
                 'stroke-linejoin="round" stroke-linecap="round"/>')
        for s in sonuc:
            p.append(f'<circle cx="{px(s["carpan"]):.1f}" cy="{py(s[anahtar]):.1f}" '
                     f'r="4.5" fill="{renk}" stroke="#fcfcfb" stroke-width="2"/>')
        son = sonuc[-1]
        p.append(f'<text x="{px(son["carpan"]) + 12:.1f}" y="{py(son[anahtar]) + 4:.1f}" '
                 f'font-size="11" fill="#3c4a3e">{ad}</text>')
        p.append(f'<circle cx="{px(son["carpan"]) + 5:.1f}" '
                 f'cy="{py(son[anahtar]):.1f}" r="3.5" fill="{renk}"/>')

    p.append('</svg>')
    return "\n".join(p)


if __name__ == "__main__":
    main()
