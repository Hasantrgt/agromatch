"""
AGROMATCH - Hangi ürünün kararı ölçüm hatasına en duyarlı?
===========================================================
toprak_veri_seti.py her (numune, ürün) çifti için iki şey biliyor: toprağın
GERÇEK değerleri ve laboratuvarın RAPOR EDECEĞİ değerler. Bu betik aynı
uygunluk kuralını ikisine birden uygular ve kararın kaç kez değiştiğini
ÜRÜN ÜRÜN sayar.

NEDEN ÜRÜN BAZINDA
Dokuz ürünün toprak isteği farklı. Kuru fasulyenin tuz eşiği 1,0 dS/m,
korunganınki 3,0 — yani aynı ölçüm hatası birinde kararı değiştirirken
diğerinde değiştirmez. "Laboratuvar hatası kararı %12 bozuyor" cümlesi il
ortalamasıdır ve hangi ürüne dikkat etmek gerektiğini söylemez.

PRATİK KARŞILIĞI
Saha kampanyasında bütün numuneler aynı özenle ölçülemez. Bu tablo, hangi
ürünün kararı için hassasiyetin gerçekten önemli olduğunu söyler — yani
parayı ve zamanı nereye koyacağını.

Yalnızca numpy gerektirir; scikit-learn gerekmez.

Kullanım:
    python src/toprak_urun_duyarlilik.py --numune 600
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

import mus_profil as mp
import mus_toprak as mt
import toprak_veri_seti as tvs

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "outputs"


def main(argv: list[str] | None = None) -> None:
    """argv açıkça verilebilir.

    Varsayılan None komut satırından çalıştırmak içindir. Başka bir
    betikten çağrılırken MUTLAKA liste geçilmeli: parse_args() argüman
    almazsa sys.argv'ı okur ve çağıran programın (örneğin pytest'in)
    kendi argümanlarını ayrıştırmaya kalkar.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--numune", type=int, default=600)
    ap.add_argument("--tohum", type=int, default=20261022)
    a = ap.parse_args(argv)

    rng = np.random.default_rng(a.tohum)
    kayit: dict[str, dict[str, Any]] = {
        u: dict(adet=0, sinif_bozuldu=0, kisit_bozuldu=0, puan=0.0,
                kisitlar=Counter(), tavan=0) for u in mp.URUN}

    for _ in range(a.numune):
        ilce = str(rng.choice(list(mp.ILCE)))
        gercek = tvs.numune_uret(rng, ilce, bool(rng.random() < 0.25))
        olculen = tvs.olc(rng, gercek)
        for urun in mp.URUN:
            g = mt.topraktan_uygunluk(gercek, urun)
            o = mt.topraktan_uygunluk(olculen, urun)
            k = kayit[urun]
            k["adet"] += 1
            k["puan"] += g["puan"]
            k["kisitlar"][g["kisitlayici"]] += 1
            k["tavan"] += int(g["tavanlandi"])
            k["sinif_bozuldu"] += int(o["sinif"] != g["sinif"])
            k["kisit_bozuldu"] += int(o["kisitlayici"] != g["kisitlayici"])

    satirlar = []
    for urun, k in kayit.items():
        n = k["adet"]
        satirlar.append(dict(
            urun=urun,
            ort_puan=round(k["puan"] / n, 1),
            sinif_bozulma=round(k["sinif_bozuldu"] / n, 4),
            kisit_bozulma=round(k["kisit_bozuldu"] / n, 4),
            tavan_orani=round(k["tavan"] / n, 4),
            en_sik_kisit=k["kisitlar"].most_common(1)[0][0],
            en_sik_kisit_oran=round(k["kisitlar"].most_common(1)[0][1] / n, 3),
        ))
    satirlar.sort(key=lambda s: -s["sinif_bozulma"])

    print(f"{a.numune} numune × {len(mp.URUN)} ürün = {a.numune * len(mp.URUN)} karar\n")
    print(f"{'ürün':<16}{'ort puan':>9}{'sınıf bozulma':>15}{'kısıt bozulma':>15}"
          f"{'tavan':>8}  en sık kısıt")
    print("-" * 88)
    for s in satirlar:
        print(f"{s['urun']:<16}{s['ort_puan']:>9.1f}{s['sinif_bozulma']:>14.1%}"
              f"{s['kisit_bozulma']:>15.1%}{s['tavan_orani']:>8.0%}  "
              f"{s['en_sik_kisit']} (%{s['en_sik_kisit_oran'] * 100:.0f})")

    en = satirlar[0]
    az = satirlar[-1]
    print(f"\nEn duyarlı : {en['urun']} — ölçüm hatası kararı "
          f"%{en['sinif_bozulma'] * 100:.0f} oranında değiştiriyor")
    print(f"En dayanıklı: {az['urun']} — %{az['sinif_bozulma'] * 100:.0f}")
    print(f"Fark {en['sinif_bozulma'] / max(az['sinif_bozulma'], 1e-9):.1f} kat. "
          f"Laboratuvar hassasiyeti her ürün için aynı derecede önemli değil.")

    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "toprak_urun_duyarlilik.json").write_text(
        json.dumps(dict(numune=a.numune, tohum=a.tohum, urunler=satirlar),
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{CIKTI / 'toprak_urun_duyarlilik.json'} yazıldı")


if __name__ == "__main__":
    main()
