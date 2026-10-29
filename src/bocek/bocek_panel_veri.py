"""
AGROMATCH - Böcek sekmesinin verisini üretir
=============================================
Üçüncü kısmın üç kataloğunu tek JSON'da toplar ve aralarındaki bağları
hesaplar. Panelin göstereceği asıl şey listeler değil, BAĞLAR:

    zararlı -> taşıdığı hastalık      üçüncü kısımdan ikinciye köprü
    zararlı -> ilaç grubu -> faydalı  bir ilacın gerçekte neyi vurduğu
    zararlı -> kalıntısız yol         ya da böyle bir yolun olmadığı

Çıktı: outputs/bocek.json

    python src/bocek/bocek_panel_veri.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import bulas_kaynagi as bk
import mus_profil as mp
from bocek import faydali as fy
from bocek import pestisit as ps
from bocek import tarla_zararli as tz

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

AY_AD = ("Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem",
         "Ağu", "Eyl", "Eki", "Kas", "Ara")


def zararli_kaydi(z: dict[str, Any]) -> dict[str, Any]:
    """Bir zararlıyı, bağlarıyla birlikte panelin okuyacağı biçime getirir."""
    gruplar = ps.zararliya_gore(z["ad"])
    kalintisiz = ps.kalintisiz_yol(z["ad"])
    dusmanlar = fy.hedefe_gore(z["ad"])
    return {
        "ad": z["ad"], "latince": z["latince"],
        "urunler": list(z["urunler"]), "onem": z["onem"],
        "zarar_sekli": z["zarar_sekli"],
        "zarar_aciklama": tz.ZARAR_SEKLI[z["zarar_sekli"]],
        "hedef_organ": z["hedef_organ"],
        "kritik_aylar": list(z["kritik_aylar"]),
        "vektor": list(z["vektor"]),
        "esik": z["esik"],
        "depoda_da": z["depoda_da"],
        "belirti": z["belirti"], "not_": z["not_"],
        "kaynak": z["kaynak"],
        "dusman": [d["ad"] for d in dusmanlar],
        "grup": [g["grup"] for g in gruplar],
        "kalintisiz": [g["grup"] for g in kalintisiz],
        # Panelde en çok görülecek sayı: en hafif seçeneğin yükü
        "en_hafif": gruplar[0]["grup"] if gruplar else None,
    }


def grup_kaydi(g: dict[str, Any]) -> dict[str, Any]:
    y = ps.yuk(g["grup"], fy.FAYDALILAR)
    return {
        "grup": g["grup"], "ad": g["ad"], "irac": g["irac"],
        "etki_sekli": g["etki_sekli"],
        "sistemik": g["sistemik"], "genis_etkili": g["genis_etkili"],
        "ariya_toksik": g["ariya_toksik"],
        "parazitoite_toksik": g["parazitoite_toksik"],
        "direnc_riski": g["direnc_riski"],
        "kalinti_gun": list(g["kalinti_suresi_gun"]),
        "hedef": list(g["hedef"]),
        "vurulan": y["vurulan"],
        "canliya_zarar": y["canliya_zarar"],
        "kimyasal": y["kimyasal"],
        "not_": g["not_"], "kaynak": g["kaynak"],
    }


def takvim() -> list[dict[str, Any]]:
    """Ay × zararlı ızgarası: hangi ayda kaç zararlı etkin.

    Çiftçinin tarlaya ne zaman bakacağını söyleyen tek tablo bu.
    """
    satir = []
    for z in tz.ZARARLILAR:
        satir.append({
            "ad": z["ad"],
            "urunler": list(z["urunler"]),
            "onem": z["onem"],
            "aylar": [1 if a in z["kritik_aylar"] else 0
                      for a in range(1, 13)],
        })
    return satir


def ay_yogunlugu() -> list[int]:
    """Her ayda etkin zararlı sayısı — önem ağırlıklı."""
    return [sum(z["onem"] for z in tz.ZARARLILAR if a in z["kritik_aylar"])
            for a in range(1, 13)]


def koprular() -> dict[str, Any]:
    """İkinci ve üçüncü kısmın birbirine değdiği noktalar."""
    z = bk.zenginlestir()
    bocekle = [{"hastalik": h["ad"], "urun": h["urun"], "tip": h["tip"],
                "onem": h["onem"],
                "vektor": [zz for zz, hh in tz.vektorler() if hh == h["ad"]]}
               for h in z if h["bulas"] == "bocek"]
    return {
        "vektor_hastalik": bocekle,
        "depo_koprusu": [zararli_kaydi(z2) for z2 in tz.ZARARLILAR
                         if z2["depoda_da"]],
        "katalogda_olmayan": sorted({h for _z, h in tz.vektorler()
                                     if h not in {x["ad"] for x in
                                                  bk.hp.HASTALIKLAR}}),
    }


def bosluklar() -> dict[str, Any]:
    """Panelde açıkça gösterilecek eksikler.

    Bir eksiği göstermek, onu gizleyip tam görünmekten iyidir: hoca
    neyi vereceğini bu listeden görür.
    """
    return {
        "esiksiz": tz.esigi_olmayanlar(),
        "kalintisiz_yolu_yok": [z["ad"] for z in tz.ZARARLILAR
                                if not ps.kalintisiz_yol(z["ad"])],
        "dogal_dusmani_yazilmamis": [z["ad"] for z in tz.ZARARLILAR
                                     if not fy.hedefe_gore(z["ad"])],
        "dogrulanmamis_kayit": sum(
            1 for k in (*tz.ZARARLILAR, *fy.FAYDALILAR, *ps.ETKI_GRUPLARI)
            if k["kaynak"] == "literatür"),
    }


def uret() -> dict[str, Any]:
    bk_ozet = bk.ozet()
    return {
        "zararlilar": [zararli_kaydi(z) for z in tz.ZARARLILAR],
        "faydalilar": [{**{k: v for k, v in f.items()
                           if k not in ("hedef", "hassasiyet", "mevsim")},
                        "hedef": list(f["hedef"]),
                        "hassasiyet": list(f["hassasiyet"]),
                        "mevsim": list(f["mevsim"])}
                       for f in fy.FAYDALILAR],
        "gruplar": [grup_kaydi(g) for g in ps.ETKI_GRUPLARI],
        "roller": fy.ROLLER,
        "zarar_sekli": tz.ZARAR_SEKLI,
        "takvim": takvim(),
        "ay_yogunlugu": ay_yogunlugu(),
        "aylar": list(AY_AD),
        "urunler": list(mp.URUN) if hasattr(mp, "URUN") else [],
        "koprular": koprular(),
        "bosluklar": bosluklar(),
        "bulas": {"ozet": bk_ozet["kaynak"],
                  "aciklama": bk.KAYNAK_ACIKLAMA,
                  "kisim": {str(k): v for k, v in bk_ozet["kisim"].items()}},
        "ozet": {
            "zararli": len(tz.ZARARLILAR),
            "faydali": len(fy.FAYDALILAR),
            "grup": len(ps.ETKI_GRUPLARI),
            "kalintisiz_grup": len(ps.KALINTISIZ),
            "vektor": len(tz.vektorler()),
            **tz.ozet()["zarar_sekli"],
        },
    }


def main() -> None:
    veri = uret()
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "bocek.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    o, b = veri["ozet"], veri["bosluklar"]
    print(f"{yol} yazıldı")
    print(f"  {o['zararli']} tarla zararlısı · {o['faydali']} faydalı · "
          f"{o['grup']} etki grubu")
    print(f"  {o['vektor']} vektör bağı · "
          f"{len(veri['koprular']['depo_koprusu'])} tarla-ambar köprüsü")
    print(f"  eksik: {len(b['esiksiz'])} eşiksiz zararlı, "
          f"{len(b['kalintisiz_yolu_yok'])} tanesinin kalıntısız yolu yok")
    en_yogun = max(range(12), key=lambda i: veri["ay_yogunlugu"][i])
    print(f"  en yoğun ay: {AY_AD[en_yogun]} "
          f"(ağırlık {veri['ay_yogunlugu'][en_yogun]})")


if __name__ == "__main__":
    main()
