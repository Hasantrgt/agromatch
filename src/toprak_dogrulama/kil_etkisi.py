"""
AGROMATCH - Kil kaynağı tavsiyeyi değiştiriyor mu
==================================================
NEDEN VAR: Doğrulama tek bir ölçülebilir alan bıraktı — kil — ve orada
iki bağımsız kaynak anlaşamadı (sıralama uyumu -0,50). Bir anlaşmazlığın
önemli olup olmadığı, TAVSİYEYİ değiştirip değiştirmediğine bakılarak
anlaşılır. Bu modül o soruyu sorar.

KİL MODELE NASIL GİRİYOR
------------------------
Puana doğrudan girmiyor; önce BÜNYE SINIFINA çevriliyor:

    kil >= 45          -> killi
    kil >= 35          -> killi-tın
    kum >= 50          -> kumlu-tın
    aksi hâlde         -> tınlı

Sonra o sınıf, ürünün bünye tercihiyle karşılaştırılıp puanlanıyor. Yani
kil değerindeki fark ancak bir SINIF SINIRINI geçerse tavsiyeyi
etkiliyor. 26 ile 30 arasındaki fark hiçbir şey değiştirmez; 34 ile 36
arasındaki fark her şeyi değiştirir.

Bu, anlaşmazlığı doğru ölçmek için önemli: "ortalama 4,2 puan fark var"
cümlesi tek başına ne anlama geldiğini söylemez.

ÜÇ SENARYO
----------
    varsayım      projenin üç yıl kullandığı değer (36-46)
    laboratuvar   bünye sınıfından türetilmiş ölçüm (24-30)
    SoilGrids     bağımsız küresel tahmin (26-37)

Üçü de aynı puanlayıcıdan geçiriliyor; aradaki tek fark kil.

Çıktı: outputs/kil_etkisi.json

    python src/toprak_dogrulama/kil_etkisi.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mus_profil as mp
import mus_toprak as mt
from toprak_profil import bunye_sinifi

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

SINIF_ESIK = ((45.0, "killi"), (35.0, "killi-tın"))


def sg_kil() -> dict[str, float]:
    """Doğrulama çıktısından ilçe başına SoilGrids kil medyanı."""
    yol = CIKTI / "toprak_dogrulama.json"
    if not yol.exists():
        return {}
    try:
        d = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not d.get("var"):
        return {}
    return {s["ilce"]: s["soilgrids"]["medyan"]
            for s in d["satirlar"] if s["alan"] == "kil"}


def _tablo() -> dict[tuple[str, str], dict[str, Any]]:
    """Geçerli ayarlarla ilçe × ürün puanı ve sınıfı."""
    from toprak_olcum.etki import sinif
    cikti = {}
    for ilce in mp.ILCE:
        for urun in mp.URUN:
            u = mt.uygunluk(ilce, urun)
            cikti[(ilce, urun)] = {"puan": round(u["puan"], 1),
                                   "sinif": sinif(u["puan"]),
                                   "kisit": u.get("kisit")}
    return cikti


def _toprak_ozeti() -> dict[str, dict[str, Any]]:
    """Geçerli ayarlarla ilçe toprağının kil ve bünyesi."""
    o = {}
    for ilce in mp.ILCE:
        t = mt.ilce_toprak(ilce)
        o[ilce] = {"kil": round(float(t["kil"]), 1),
                   "kum": round(float(t["kum"]), 1),
                   "silt": round(float(t["silt"]), 1),
                   "bunye": bunye_sinifi(t["kil"], t["kum"], t["silt"]),
                   "kaynak": t.get("_kaynak", {}).get("kil", "varsayım")}
    return o


def _senaryo(ad: str, kil_ustu: dict[str, float] | None,
             olcum: bool) -> dict[str, Any]:
    """Tek senaryoyu çalıştırır ve modülün durumunu geri bırakır.

    mus_toprak modül düzeyinde durum tutuyor (OLCUM_KULLAN, önbellek).
    Senaryolar arasında bu durum sızarsa karşılaştırma sessizce
    bozulur — bu yüzden her senaryo kendi temizliğini yapıyor.
    """
    eski_bayrak = mt.OLCUM_KULLAN
    eski_fn = mt.olcum_katmani
    try:
        mt.OLCUM_KULLAN = olcum
        if kil_ustu is not None:
            taban = eski_fn() if olcum else {}

            def yama() -> dict[str, dict[str, Any]]:
                katman = {i: dict(a) for i, a in taban.items()}
                for ilce, kil in kil_ustu.items():
                    katman.setdefault(ilce, {})["kil"] = {
                        "deger": kil, "tur": "soilgrids", "n": 0}
                return katman

            mt.olcum_katmani = yama
        return {"ad": ad, "toprak": _toprak_ozeti(), "tablo": _tablo()}
    finally:
        mt.OLCUM_KULLAN = eski_bayrak
        mt.olcum_katmani = eski_fn


def uret() -> dict[str, Any]:
    sg = sg_kil()
    if not sg:
        return {"var": False,
                "sebep": "outputs/toprak_dogrulama.json yok ya da boş — "
                         "önce karsilastir.py çalıştırılmalı"}

    senaryolar = [
        _senaryo("varsayım", None, False),
        _senaryo("laboratuvar", None, True),
        _senaryo("soilgrids", sg, True),
    ]
    s_varsayim, s_lab, s_sg = senaryolar

    # --- ilçe bazında bünye sınıfı: asıl mekanizma burada
    ilce_satir = []
    for ilce in mp.ILCE:
        v, lb, sgs = (s["toprak"][ilce] for s in senaryolar)
        siniflar = {v["bunye"], lb["bunye"], sgs["bunye"]}
        ilce_satir.append({
            "ilce": ilce,
            "varsayim_kil": v["kil"], "varsayim_bunye": v["bunye"],
            "lab_kil": lb["kil"], "lab_bunye": lb["bunye"],
            "lab_kaynak": lb["kaynak"],
            "sg_kil": sgs["kil"], "sg_bunye": sgs["bunye"],
            "sinif_ayrisiyor": len(siniflar) > 1,
            "lab_sg_ayni_sinif": lb["bunye"] == sgs["bunye"],
            "lab_olcum_var": lb["kaynak"] != "varsayım",
        })

    # --- ikili karşılaştırmalar
    def fark(a: dict[str, Any], b: dict[str, Any], ad: str) -> dict[str, Any]:
        degisen = []
        for anahtar, x in a["tablo"].items():
            y = b["tablo"][anahtar]
            if x["sinif"] != y["sinif"] or abs(x["puan"] - y["puan"]) > 0.05:
                degisen.append({
                    "ilce": anahtar[0], "urun": anahtar[1],
                    "once_puan": x["puan"], "sonra_puan": y["puan"],
                    "fark": round(y["puan"] - x["puan"], 1),
                    "once_sinif": x["sinif"], "sonra_sinif": y["sinif"],
                    "sinif_degisti": x["sinif"] != y["sinif"],
                })
        sinif_degisen = [d for d in degisen if d["sinif_degisti"]]
        farklar = [abs(d["fark"]) for d in degisen]
        return {
            "ad": ad, "degisen_satir": len(degisen),
            "sinif_degisen": len(sinif_degisen),
            "en_buyuk_fark": max(farklar) if farklar else 0.0,
            "ortalama_mutlak_fark": (round(sum(farklar) / len(farklar), 2)
                                     if farklar else 0.0),
            "sinif_degisenler": sorted(sinif_degisen,
                                       key=lambda d: -abs(d["fark"]))[:20],
        }

    karsilastirmalar = [
        fark(s_varsayim, s_lab, "varsayım -> laboratuvar"),
        fark(s_lab, s_sg, "laboratuvar -> SoilGrids"),
        fark(s_varsayim, s_sg, "varsayım -> SoilGrids"),
    ]

    # Laboratuvar ölçümü OLMAYAN ilçe, SoilGrids'in gerçekten
    # doldurabileceği boşluktur: orada model hâlâ varsayımla çalışıyor.
    bosluk = [r["ilce"] for r in ilce_satir if not r["lab_olcum_var"]]

    return {
        "var": True,
        "esikler": [{"kil_en_az": e, "sinif": a} for e, a in SINIF_ESIK],
        "ilceler": ilce_satir,
        "karsilastirmalar": karsilastirmalar,
        "lab_olcumu_olmayan": bosluk,
        "ozet": {
            "sinifi_ayrisan_ilce": sum(1 for r in ilce_satir
                                       if r["sinif_ayrisiyor"]),
            "lab_sg_ayni_sinif": sum(1 for r in ilce_satir
                                     if r["lab_sg_ayni_sinif"]),
            "toplam_ilce": len(ilce_satir),
            "lab_sg_sinif_degisen_satir":
                karsilastirmalar[1]["sinif_degisen"],
        },
        "yargi": (
            "Kil puana doğrudan girmiyor; önce bünye sınıfına çevriliyor. "
            "Bu yüzden bir kil farkı ancak SINIF SINIRINI geçtiğinde "
            "tavsiyeyi değiştirir. Doğrulamada çıkan anlaşmazlığın önemi "
            "de buradan ölçülür: iki kaynak farklı sayı söylüyor ama aynı "
            "sınıfa düşüyorsa, anlaşmazlık tavsiyeyi etkilemez ve "
            "akademik kalır. Farklı sınıfa düşüyorsa, hangi kaynağın "
            "kullanıldığı doğrudan çiftçiye verilen öneriyi değiştirir."),
    }


def main() -> None:
    d = uret()
    if not d.get("var"):
        print("Çalışmadı:", d.get("sebep"))
        return
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "kil_etkisi.json"
    yol.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"{yol} yazıldı\n")

    print(f"{'ilçe':11s} {'varsayım':>20s} {'laboratuvar':>22s} "
          f"{'SoilGrids':>20s}")
    for r in d["ilceler"]:
        isaret = "  <-- sınıf ayrışıyor" if r["sinif_ayrisiyor"] else ""
        print(f"{r['ilce']:11s} "
              f"{r['varsayim_kil']:7.1f} {r['varsayim_bunye']:<11s} "
              f"{r['lab_kil']:7.1f} {r['lab_bunye']:<13s} "
              f"{r['sg_kil']:7.1f} {r['sg_bunye']:<11s}{isaret}")

    print()
    for k in d["karsilastirmalar"]:
        print(f"{k['ad']:28s} değişen {k['degisen_satir']:3d} satır · "
              f"sınıf değişen {k['sinif_degisen']:2d} · "
              f"en büyük fark {k['en_buyuk_fark']:.1f}")

    o = d["ozet"]
    print(f"\nBünye sınıfı üç kaynak arasında ayrışan ilçe: "
          f"{o['sinifi_ayrisan_ilce']}/{o['toplam_ilce']}")
    print(f"Laboratuvar ile SoilGrids aynı sınıfta: "
          f"{o['lab_sg_ayni_sinif']}/{o['toplam_ilce']}")
    if d["lab_olcumu_olmayan"]:
        print(f"\nLaboratuvar kili olmayan ilçe: "
              f"{', '.join(d['lab_olcumu_olmayan'])}")
        print("  Burada model hâlâ varsayımla çalışıyor; SoilGrids bu "
              "boşluğu doldurabilecek tek kaynak.")


if __name__ == "__main__":
    main()
