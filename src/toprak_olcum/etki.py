"""
AGROMATCH - Ölçüm gelince ne değişti
=====================================
Toprak modelini iki kez çalıştırır — bir kez eski VARSAYIMLARLA, bir kez
laboratuvar ÖLÇÜMLERİYLE — ve farkı ölçer.

Bu dosya projenin en önemli sorusuna cevap veriyor: **varsayımla
çalışmak bize ne kaybettirdi?** Fark küçükse model sağlamdır ve
varsayımlar iyi seçilmişti. Fark büyükse, varsayımla verilen her tavsiye
yeniden değerlendirilmelidir.

Cevabı önceden bilmiyoruz; ikisi de projenin lehine bir sonuç değil.
Önemli olan sayıyı görmek.

Çıktı: outputs/olcum_etkisi.json

    python src/toprak_olcum/etki.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mus_profil as mp
import mus_toprak as mt

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

# Uygunluk sınıfı sınırları (mus_toprak ile aynı mantık)
SINIF = ((85, "çok uygun"), (70, "uygun"), (55, "sınırlı"), (0, "uygun değil"))


def sinif(puan: float) -> str:
    for esik, ad in SINIF:
        if puan >= esik:
            return ad
    return "uygun değil"


def _tablo() -> list[dict[str, Any]]:
    """Her ilçe × ürün için toprak uygunluk puanı ve darboğazı."""
    satir = []
    for ilce in mp.ILCE:
        for urun in mp.URUN:
            u = mt.uygunluk(ilce, urun)
            satir.append({
                "ilce": ilce, "urun": urun,
                "puan": round(u["puan"], 1),
                "kisit": u.get("kisit"),
                "sinif": sinif(u["puan"]),
            })
    return satir


def karsilastir() -> dict[str, Any]:
    mt.OLCUM_KULLAN = False
    once = {(s["ilce"], s["urun"]): s for s in _tablo()}
    mt.OLCUM_KULLAN = True
    sonra = {(s["ilce"], s["urun"]): s for s in _tablo()}

    satirlar = []
    for anahtar, o in once.items():
        s = sonra[anahtar]
        satirlar.append({
            "ilce": anahtar[0], "urun": anahtar[1],
            "varsayim_puan": o["puan"], "olcum_puan": s["puan"],
            "fark": round(s["puan"] - o["puan"], 1),
            "varsayim_sinif": o["sinif"], "olcum_sinif": s["sinif"],
            "sinif_degisti": o["sinif"] != s["sinif"],
            "varsayim_kisit": o["kisit"], "olcum_kisit": s["kisit"],
            "kisit_degisti": o["kisit"] != s["kisit"],
        })

    # Hangi ilçede ölçüm var, hangisinde yok — farkın sıfır çıkması
    # ölçümün etkisiz olduğu anlamına gelmez, ölçüm OLMADIĞI anlamına
    # gelebilir. İkisini ayırmak gerekiyor.
    olculen = set(mt.olcum_katmani())
    etkilenen = [s for s in satirlar if s["ilce"] in olculen]

    farklar = [abs(s["fark"]) for s in etkilenen]
    return {
        "satirlar": satirlar,
        "olculen_ilceler": sorted(olculen),
        "olcumsuz_ilceler": sorted(set(mp.ILCE) - olculen),
        "ozet": {
            "toplam_satir": len(satirlar),
            "olcumlu_satir": len(etkilenen),
            "ortalama_mutlak_fark": (round(sum(farklar) / len(farklar), 2)
                                     if farklar else 0.0),
            "en_buyuk_fark": max(farklar) if farklar else 0.0,
            "sinif_degisen": sum(1 for s in etkilenen if s["sinif_degisti"]),
            "kisit_degisen": sum(1 for s in etkilenen if s["kisit_degisti"]),
            "iyilesen": sum(1 for s in etkilenen if s["fark"] > 0),
            "kotulesen": sum(1 for s in etkilenen if s["fark"] < 0),
        },
        "en_cok_degisen": sorted(etkilenen, key=lambda s: -abs(s["fark"]))[:12],
        "sinif_degisenler": [s for s in etkilenen if s["sinif_degisti"]],
    }


def main() -> None:
    veri = karsilastir()
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "olcum_etkisi.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    o = veri["ozet"]
    print(f"{yol} yazıldı\n")
    print(f"Ölçüm bulunan ilçeler : {', '.join(veri['olculen_ilceler'])}")
    print(f"Ölçümsüz kalan        : {', '.join(veri['olcumsuz_ilceler']) or '—'}")
    print(f"\nÖlçümlü {o['olcumlu_satir']} ilçe×ürün satırında:")
    print(f"  ortalama mutlak fark : {o['ortalama_mutlak_fark']} puan")
    print(f"  en büyük fark        : {o['en_buyuk_fark']} puan")
    print(f"  uygunluk SINIFI değişen : {o['sinif_degisen']} satır")
    print(f"  darboğazı değişen       : {o['kisit_degisen']} satır")
    print(f"  puanı yükselen {o['iyilesen']} · düşen {o['kotulesen']}")
    if veri["sinif_degisenler"]:
        print("\nSınıfı değişenler:")
        for s in veri["sinif_degisenler"]:
            print(f"  {s['ilce']:11s} {s['urun']:15s} "
                  f"{s['varsayim_puan']:>5.1f} {s['varsayim_sinif']:12s} → "
                  f"{s['olcum_puan']:>5.1f} {s['olcum_sinif']}")
    print("\nEn çok değişen altı satır:")
    for s in veri["en_cok_degisen"][:6]:
        print(f"  {s['ilce']:11s} {s['urun']:15s} "
              f"{s['varsayim_puan']:>5.1f} → {s['olcum_puan']:>5.1f} "
              f"({s['fark']:+.1f})")


if __name__ == "__main__":
    main()
