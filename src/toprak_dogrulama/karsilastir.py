"""
AGROMATCH - Laboratuvar ölçümünü bağımsız bir kaynakla doğrulama
=================================================================
NEDEN VAR: Elimizdeki 2.622 laboratuvar kaydına veriyi veren hoca da
güvenmiyor, biz de güvenmiyoruz — kalite denetimi altı ayrı kusur buldu.
İl Tarım'dan ek veri istendi, verilmedi. Geriye tek dürüst yol kalıyor:
elimizdekini BAĞIMSIZ bir kaynakla karşılaştırmak.

ISRIC SoilGrids küresel, 250 m çözünürlüklü, hakemli yöntemle üretilmiş ve
CC-BY 4.0 lisanslı bir toprak tahmin ürünü. Muş'u özel olarak bilmiyor;
tam da bu yüzden bağımsız bir tanık.

ÜÇ SAYIYI YAN YANA KOYAR
------------------------
    varsayım      proje üç yıl boyunca bunu kullandı (literatür + uzman)
    laboratuvar   İl Tarım'ın 2011-2015 kayıtlarının ilçe medyanı
    SoilGrids     bağımsız küresel tahmin

Üçünün birbirini tuttuğu yerde o değere güvenilebilir. Ayrıştığı yerde
hangisinin yanlış olduğunu bu modül SÖYLEYEMEZ — ama nerede bakılması
gerektiğini söyler. Bir doğrulamanın işi budur.

NE DOĞRULANAMAZ — baştan yazılı
-------------------------------
SoilGrids kireç (CaCO3) ve tuzluluk (EC) vermiyor. İkisi de karşılaştırmaya
giremez. Üstelik varsayımımızın EN ÇOK ŞAŞTIĞI alan kireçti (ortalama 6,8
puan, beş ilçenin beşinde de ölçüm aralığının dışında). Yani bu doğrulama
en zayıf noktamızı kapatmıyor. Bunu yazmak, kapatıyormuş gibi yapmaktan
iyidir.

Organik madde de doğrudan yok: SoilGrids organik KARBON veriyor. Van
Bemmelen katsayısıyla çevriliyor (OM ≈ SOC × 1,724). Bu bir VARSAYIMDIR,
ölçüm değil; çıktıda ve panelde öyle işaretli.

Girdi : data/soilgrids/mus_noktalar.csv   (soilgrids_cek.py üretir)
Çıktı : outputs/toprak_dogrulama.json

    python src/toprak_dogrulama/karsilastir.py
"""

from __future__ import annotations

import csv
import json
import statistics as st
from collections import defaultdict
from pathlib import Path
from typing import Any

import mus_profil as mp

KOK = Path(__file__).resolve().parent.parent.parent
GIRDI = KOK / "data" / "soilgrids" / "mus_noktalar.csv"
CIKTI = KOK / "outputs"

# Tarla örneği genelde 0-20 cm'den alınır. SoilGrids kademelerinin bu
# aralığa düşen kalınlığı ağırlık olarak kullanılıyor: 15-30cm kademesinin
# yalnızca 5 cm'i 20 cm'in içinde kalır.
DERINLIK_AGIRLIK = {"0-5cm": 5.0, "5-15cm": 10.0, "15-30cm": 5.0}

# Van Bemmelen — organik karbondan organik maddeye geçiş katsayısı.
# Yaygın kullanılır ama toprak tipine göre değişir; bu yüzden türetilen
# her organik madde değeri "türetildi" olarak işaretlenir.
OM_KATSAYI = 1.724

# mus_profil.TOPRAK sırası: ph, om, kirec, ec, kil, kum, silt, ...
VARSAYIM_SIRA = {"ph": 0, "om": 1, "kirec": 2, "ec": 3, "kil": 4}

# Karşılaştırılabilir alanlar ve okunur adları
ALAN_AD = {"ph": "pH", "om": "organik madde (%)", "kil": "kil (%)"}

# SoilGrids'in vermediği, dolayısıyla doğrulanamayan alanlar
DOGRULANAMAYAN = {
    "kirec": "SoilGrids karbonat (CaCO3) içeriği yayımlamıyor. "
             "Varsayımın en çok şaştığı alan bu olduğu için en çok "
             "doğrulanması gereken de buydu; doğrulanamadı.",
    "ec": "SoilGrids tuzluluk (elektriksel iletkenlik) yayımlamıyor.",
}


def _yuzdeye(deger: float, birim: str) -> tuple[float | None, str]:
    """Birimi okuyup yüzdeye çevirir; tanımadığı birimi UYDURMAZ.

    SoilGrids sürümleri arasında birim etiketi değişebiliyor. Katsayıyı
    koda gömmek yerine dosyadaki birim okunuyor; tanınmayan bir birim
    sessizce yanlış sayı üretmektense açıkça None döner.
    """
    b = (birim or "").strip().lower()
    if b in ("%", "percent", "pct"):
        return deger, "doğrudan"
    if b in ("g/kg", "g kg-1"):
        return deger / 10.0, "g/kg -> % (÷10)"
    if b in ("dg/kg", "dg kg-1"):
        return deger / 100.0, "dg/kg -> % (÷100)"
    return None, f"birim tanınmadı: {birim!r}"


def oku(yol: Path | None = None) -> dict[str, Any]:
    """CSV'yi ilçe × alan × nokta yapısına çevirir."""
    yol = yol or GIRDI
    if not yol.exists():
        return {}
    # ilce -> alan -> nokta(enlem,boylam) -> {derinlik: deger}
    ham: dict[str, dict[str, dict[tuple, dict[str, float]]]] = \
        defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    birimler: dict[str, str] = {}
    with open(yol, encoding="utf-8", newline="") as f:
        for s in csv.DictReader(f):
            try:
                d = float(s["deger"])
            except (TypeError, ValueError):
                continue
            nokta = (s["enlem"], s["boylam"])
            ham[s["ilce"]][s["ozellik"]][nokta][s["derinlik"]] = d
            birimler.setdefault(s["ozellik"], s.get("birim", ""))
    return {"ham": ham, "birimler": birimler}


def _nokta_degeri(kademeler: dict[str, float]) -> float | None:
    """Kademeleri 0-20 cm'e ağırlıklı ortalamayla indirger."""
    pay = agirlik = 0.0
    for kademe, d in kademeler.items():
        a = DERINLIK_AGIRLIK.get(kademe)
        if a:
            pay += d * a
            agirlik += a
    return pay / agirlik if agirlik else None


def _ozet(degerler: list[float]) -> dict[str, Any]:
    d = sorted(degerler)
    ceyrek = st.quantiles(d, n=4) if len(d) >= 4 else [d[0], st.median(d), d[-1]]
    return {"n": len(d), "medyan": round(st.median(d), 3),
            "q1": round(ceyrek[0], 3), "q3": round(ceyrek[2], 3),
            "min": round(d[0], 3), "maks": round(d[-1], 3)}


def soilgrids_ozeti(veri: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """İlçe -> alan -> özet. Birim dönüşümü burada ve kayıtlı yapılır."""
    sonuc: dict[str, dict[str, Any]] = {}
    for ilce, alanlar in veri["ham"].items():
        cikti: dict[str, Any] = {}

        for sg_ad, hedef in (("ph", "ph"), ("clay", "kil"), ("kil", "kil")):
            if sg_ad not in alanlar:
                continue
            d = [v for v in (_nokta_degeri(k)
                             for k in alanlar[sg_ad].values()) if v is not None]
            if not d:
                continue
            if hedef == "kil":
                birim = veri["birimler"].get(sg_ad, "")
                cevrilmis = []
                yontem = ""
                for x in d:
                    y, yontem = _yuzdeye(x, birim)
                    if y is not None:
                        cevrilmis.append(y)
                if not cevrilmis:
                    cikti[hedef] = {"hata": yontem}
                    continue
                cikti[hedef] = {**_ozet(cevrilmis), "donusum": yontem}
            else:
                cikti[hedef] = {**_ozet(d), "donusum": "doğrudan"}

        # organik madde: karbondan türetilir
        if "soc" in alanlar:
            d = [v for v in (_nokta_degeri(k)
                             for k in alanlar["soc"].values()) if v is not None]
            birim = veri["birimler"].get("soc", "")
            karbon = []
            yontem = ""
            for x in d:
                y, yontem = _yuzdeye(x, birim)
                if y is not None:
                    karbon.append(y)
            if karbon:
                cikti["om"] = {
                    **_ozet([k * OM_KATSAYI for k in karbon]),
                    "donusum": f"{yontem}, sonra × {OM_KATSAYI} "
                               "(Van Bemmelen) — TÜRETİLDİ",
                    "turetildi": True}
            elif yontem:
                cikti["om"] = {"hata": yontem}

        if cikti:
            sonuc[ilce] = cikti
    return sonuc


def _bunyeden_kil(ilce_kaydi: dict[str, Any]) -> dict[str, Any] | None:
    """Bünye sınıfı dağılımından kil oranı türetir.

    Laboratuvar kili sayı olarak ölçmemiş, bünye sınıfı yazmış. Projenin
    ölçüm katmanı bu sınıftan kil türetiyor (analiz.kil_kestirimi);
    burada da aynı fonksiyon kullanılıyor. Aynı veriden iki ayrı yöntemle
    iki ayrı sayı üretmek, karşılaştırmayı anlamsız kılardı.

    Tek bir sayı döndüğü için çeyrek aralığı yok; q1/q3 o sayıya eşitlenir
    ve satır "lab_turetildi" ile işaretlenir. Böyle bir karşılaştırmanın
    "aralıkta mı" sorusu zayıftır ve panelde öyle gösterilir.
    """
    bunye = ilce_kaydi.get("bunye")
    if not bunye or not ilce_kaydi.get("guvenilir"):
        return None
    try:
        from toprak_olcum.analiz import kil_kestirimi
    except ImportError:
        return None
    kil = kil_kestirimi(bunye)
    if kil is None:
        return None
    return {"n": sum(b["n"] for b in bunye), "medyan": kil,
            "q1": kil, "q3": kil, "guvenilir": True}


def uret(yol: Path | None = None) -> dict[str, Any]:
    veri = oku(yol)
    if not veri:
        return {"var": False,
                "sebep": f"{GIRDI} yok — önce soilgrids_cek.py çalıştırılmalı"}
    sg = soilgrids_ozeti(veri)
    if not sg:
        return {"var": False, "sebep": "CSV okundu ama kullanılabilir değer yok"}

    # laboratuvar özetini oku (varsa)
    lab_yol = CIKTI / "toprak_olcum.json"
    lab: dict[str, Any] = {}
    if lab_yol.exists():
        try:
            d = json.loads(lab_yol.read_text(encoding="utf-8"))
            if d.get("var"):
                lab = d.get("ilce", {})
        except (OSError, json.JSONDecodeError):
            lab = {}

    satirlar: list[dict[str, Any]] = []
    for ilce in mp.ILCE:
        if ilce not in sg:
            continue
        varsayimlar = mp.TOPRAK[ilce]
        for alan in ALAN_AD:
            o = sg[ilce].get(alan)
            if not o or "hata" in o:
                continue
            v = float(varsayimlar[VARSAYIM_SIRA[alan]])
            l_ozet = (lab.get(ilce, {}).get("alanlar", {}) or {}).get(alan)
            lab_turetildi = False
            if l_ozet is None and alan == "kil":
                # Laboratuvar kili SAYI olarak ölçmüyor, bünye SINIFI
                # kaydediyor ("Killi-Tınlı" gibi). Projenin ölçüm katmanı
                # o sınıftan kil oranı türetiyor; karşılaştırmada da aynı
                # türetme kullanılıyor ki iki taraf aynı şeyi konuşsun.
                # Türetilmiş olduğu satırda işaretli.
                l_ozet = _bunyeden_kil(lab.get(ilce, {}))
                lab_turetildi = l_ozet is not None

            satir: dict[str, Any] = {
                "ilce": ilce, "alan": alan, "alan_ad": ALAN_AD[alan],
                "soilgrids": o, "varsayim": v,
                "fark_varsayim": round(o["medyan"] - v, 3),
                "varsayim_sg_araliginda": o["q1"] <= v <= o["q3"],
                "turetildi": bool(o.get("turetildi")),
            }
            if l_ozet:
                satir["laboratuvar"] = {
                    k: l_ozet[k] for k in ("n", "medyan", "q1", "q3",
                                           "guvenilir") if k in l_ozet}
                satir["fark_lab"] = round(o["medyan"] - l_ozet["medyan"], 3)
                satir["lab_araliginda"] = (
                    l_ozet["q1"] <= o["medyan"] <= l_ozet["q3"])
                satir["uyum"] = ("tutuyor" if satir["lab_araliginda"]
                                 else "ayrışıyor")
                satir["lab_turetildi"] = lab_turetildi
            else:
                satir["laboratuvar"] = None
                satir["uyum"] = "ölçüm yok"
            satirlar.append(satir)

    # Alan bazında özet.
    #
    # ÖNEMLİ AYRIM: laboratuvar kili SAYI olarak ölçmedi, bünye sınıfından
    # TÜRETİLDİ. Türetilmiş değer tek bir sayıdır, çeyrek aralığı yoktur;
    # dolayısıyla "SoilGrids medyanı laboratuvarın çeyrek aralığına
    # düşüyor mu" testi o satırlarda anlamsızdır — aralık sıfır genişlikte
    # olduğu için neredeyse her zaman "ayrışıyor" çıkar. Bu satırları ana
    # tutma oranına katmak, oranı sahte biçimde düşürürdü. Ayrı sayılıyor
    # ve farkları yine raporlanıyor.
    def _olculu(s: dict[str, Any]) -> bool:
        return bool(s["laboratuvar"]) and bool(
            s["laboratuvar"].get("guvenilir")) and not s.get("lab_turetildi")

    def _turetilmis(s: dict[str, Any]) -> bool:
        return bool(s["laboratuvar"]) and bool(s.get("lab_turetildi"))

    alan_ozeti = []
    for alan, ad in ALAN_AD.items():
        ait = [s for s in satirlar if s["alan"] == alan]
        if not ait:
            continue
        olculu = [s for s in ait if _olculu(s)]
        turetilmis = [s for s in ait if _turetilmis(s)]
        farklar = [abs(s["fark_lab"]) for s in olculu]
        t_farklar = [abs(s["fark_lab"]) for s in turetilmis]
        alan_ozeti.append({
            "alan": alan, "alan_ad": ad,
            "karsilastirilan_ilce": len(ait),
            "olcumlu_ilce": len(olculu),
            "tutan_ilce": len([s for s in olculu if s["lab_araliginda"]]),
            "ortalama_mutlak_fark": round(st.fmean(farklar), 3) if farklar else None,
            "turetilmis_ilce": len(turetilmis),
            "turetilmis_ortalama_fark": (round(st.fmean(t_farklar), 3)
                                         if t_farklar else None),
            "lab_turetildi": bool(turetilmis),
            "sg_turetildi": any(s["turetildi"] for s in ait),
        })

    olculu_hepsi = [s for s in satirlar if _olculu(s)]
    tutan_hepsi = [s for s in olculu_hepsi if s["lab_araliginda"]]
    turetilmis_hepsi = [s for s in satirlar if _turetilmis(s)]
    nokta_sayisi = sum(len(a) for i in veri["ham"].values() for a in i.values())

    return {
        "var": True,
        "kaynak": "ISRIC SoilGrids 2.0 (250 m, CC-BY 4.0)",
        "kaynak_adres": "https://www.isric.org/explore/soilgrids",
        "nokta_sorgusu": nokta_sayisi,
        "ilce_sayisi": len(sg),
        "derinlik_agirlik": DERINLIK_AGIRLIK,
        "om_katsayi": OM_KATSAYI,
        "satirlar": satirlar,
        "alan_ozeti": alan_ozeti,
        "dogrulanamayan": [{"alan": a, "alan_ad": a, "sebep": s}
                           for a, s in DOGRULANAMAYAN.items()],
        "ozet": {
            "karsilastirma": len(satirlar),
            "olcumlu": len(olculu_hepsi),
            "tutan": len(tutan_hepsi),
            "tutma_orani": (round(len(tutan_hepsi) / len(olculu_hepsi) * 100, 1)
                            if olculu_hepsi else None),
            "turetilmis": len(turetilmis_hepsi),
        },
        "yargi": (
            "Bu bir doğrulamadır, bir ispat değil. SoilGrids de bir TAHMİN "
            "ürünüdür; Muş'u özel olarak bilmez. Üç sayının (varsayım, "
            "laboratuvar, SoilGrids) birbirini tuttuğu yerde o değere "
            "güvenilebilir. Ayrıştığı yerde hangisinin yanlış olduğunu bu "
            "karşılaştırma söyleyemez — nereye bakılması gerektiğini söyler. "
            "Kireç ve tuzluluk hiç doğrulanamadı; proje için en kritik "
            "eksik budur."),
    }


def main() -> None:
    d = uret()
    if not d.get("var"):
        print("Doğrulama çalışmadı:", d.get("sebep"))
        return
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "toprak_dogrulama.json"
    yol.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"{yol} yazıldı\n")
    print(f"{d['nokta_sorgusu']} nokta sorgusu · {d['ilce_sayisi']} ilçe\n")
    print(f"{'alan':20s} {'ilçe':>5s} {'ölçümlü':>8s} {'tutan':>6s} "
          f"{'ort|fark|':>10s}")
    for a in d["alan_ozeti"]:
        f = a["ortalama_mutlak_fark"]
        ek = (f"  (+{a['turetilmis_ilce']} türetilmiş, ort. fark "
              f"{a['turetilmis_ortalama_fark']})" if a["lab_turetildi"] else "")
        print(f"{a['alan_ad']:20s} {a['karsilastirilan_ilce']:5d} "
              f"{a['olcumlu_ilce']:8d} {a['tutan_ilce']:6d} "
              f"{(f'{f:.2f}' if f is not None else '—'):>10s}{ek}")
    o = d["ozet"]
    print(f"\nÖlçümle karşılaştırılabilen {o['olcumlu']} satırın "
          f"{o['tutan']}'i tutuyor"
          + (f" (%{o['tutma_orani']})" if o["tutma_orani"] is not None else ""))
    print("\nDoğrulanamayan:")
    for x in d["dogrulanamayan"]:
        print(f"  {x['alan']}: {x['sebep'].splitlines()[0]}")


if __name__ == "__main__":
    main()
