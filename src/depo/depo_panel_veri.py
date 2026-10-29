"""
AGROMATCH - Depo sekmesinin verisini üretir
============================================
Üç kaynağı tek JSON'da toplar:

    depo_profil      zararlı ve mücadele katalogları
    ambar_sicaklik   ilçe bazında yığın sıcaklığı ve gelişme penceresi
    doz_cevap        örnek bir doz–cevap uyumu (şimdilik SENTETİK)

Doz–cevap kısmı bilerek sentetik veriyle üretiliyor ve panelde böyle
etiketleniyor. Amaç aracın çalıştığını göstermek; danışman hocanın ham
sayımları geldiğinde `--veri` ile gerçek dosya verilir ve aynı grafik
gerçek veriyle çizilir. Sentetiği gerçek gibi göstermek, bu projenin
baştan beri kaçındığı tek şey.

Çıktı: outputs/depo.json

    python src/depo/depo_panel_veri.py
    python src/depo/depo_panel_veri.py --veri data/deneme.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

import mus_profil as mp
from depo import ambar_sicaklik as amb
from depo import depo_profil as dp
from depo import doz_cevap as dc

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

# Eğrinin çizileceği doz noktaları (log aralıklı)
EGRI_NOKTA = 60


def egri(uyum: dc.Uyum, alt: float, ust: float) -> list[dict[str, float]]:
    """Uydurulan eğriyi çizim için noktalara açar."""
    cdf, _ = dc._bag(uyum.baglanti)
    xs = np.logspace(np.log10(max(alt, 1e-6)), np.log10(ust), EGRI_NOKTA)
    return [dict(doz=float(x),
                 olum=float(cdf(uyum.kesim + uyum.egim * np.log10(x))))
            for x in xs]


def doz_cevap_bolumu(gozlemler: list[dc.Gozlem], sentetik: bool) -> dict[str, Any]:
    uyum = dc.uydur(gozlemler, eksen="doz", baglanti="probit")
    uygulanan = [g for g in gozlemler if g.doz > 0]
    kontrol = [g for g in gozlemler if g.doz <= 0]
    k_oran = (sum(g.olen for g in kontrol) / sum(g.denenen for g in kontrol)
              if kontrol else 0.0)

    # Gözlem noktaları: Abbott düzeltilmiş oranlarla, grafikte eğriyle
    # aynı eksende durabilsinler diye
    noktalar = [dict(doz=g.doz, olum=dc.abbott(g.oran, k_oran),
                     denenen=g.denenen, tekrar=g.tekrar)
                for g in uygulanan]
    dozlar = [g.doz for g in uygulanan]
    return dict(
        sentetik=sentetik,
        baglanti=uyum.baglanti,
        egim=round(uyum.egim, 3),
        iki_kat_etkisi=round(uyum.iki_kat_etkisi, 2),
        kontrol_olumu=round(uyum.kontrol_olumu, 4),
        n_gozlem=uyum.n_gozlem, n_birey=uyum.n_birey,
        lc=uyum.lc, uyari=uyum.uyari,
        noktalar=noktalar,
        egri=egri(uyum, min(dozlar) * 0.6, max(dozlar) * 1.6),
        gercek_lc50=(float(10 ** ((stats.norm.ppf(0.5) - (-6.4)) / 2.6))
                     if sentetik else None),
    )


def uret(veri: Path | None = None) -> dict[str, Any]:
    if veri:
        gozlemler, sentetik = dc.oku(veri), False
    else:
        gozlemler, sentetik = dc.ornek_veri(), True

    ambar = amb.analiz()
    # Panelde ilçe × zararlı ızgarası çizilecek; sıralama sabit olsun
    zararlilar = sorted(dp.ZARARLILAR, key=lambda z: (-z["onem"], z["taban_sicaklik"]))

    return dict(
        zararlilar=[{k: v for k, v in z.items()} for z in zararlilar],
        mucadele=list(dp.MUCADELE),
        kaynaklar=dp.KAYNAKLAR,
        ozet=dp.ozet(),
        ambar=dict(
            sonumleme=ambar["sonumleme"],
            ilceler=list(mp.ILCE),
            aylar=amb.AY_AD,
            yigin=ambar["aylik_yigin"],
            dis_hava=ambar["dis_hava"],
            pencere=ambar["satirlar"],
            not_=ambar["not_"],
        ),
        doz_cevap=doz_cevap_bolumu(gozlemler, sentetik),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--veri", type=Path,
                    help="gerçek deneme CSV'si (verilmezse sentetik gösterim)")
    a = ap.parse_args()

    veri = uret(a.veri)
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "depo.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")

    d = veri["doz_cevap"]
    print(f"{yol} yazıldı")
    print(f"  zararlı {veri['ozet']['zararli']} · mücadele {veri['ozet']['mucadele']} "
          f"· kalıntısız {veri['ozet']['kalintisiz']}")
    print(f"  ambar penceresi {len(veri['ambar']['pencere'])} satır")
    etiket = "SENTETİK" if d["sentetik"] else "gerçek veri"
    lc50 = d["lc"].get("LC50", {})
    if "deger" in lc50:
        print(f"  doz–cevap ({etiket}): LC50 {lc50['deger']:.1f} "
              f"[{lc50.get('alt', 0):.1f}–{lc50.get('ust', 0):.1f}]")
    else:
        print(f"  doz–cevap ({etiket}): LC50 kestirilemedi")


if __name__ == "__main__":
    main()
