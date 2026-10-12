"""
AGROMATCH - İl karnesi
======================
Her il için dört göstergeden oluşan bir karne üretir. Amaç, bir ilin tarımsal
ekim deseninin "ne kadar bilinçli" olduğunu tek ekranda görünür kılmaktır.

  1. Yem yeterliliği   : İlin hayvanının kaba yemini kendi toprağından karşılama oranı
  2. Su verimliliği    : Her üründe, o ürünün bölge ortalamasına göre performans
                         (ürün karması yanlılığını ortadan kaldırmak için ürün bazlı
                         karşılaştırma, üretim payıyla ağırlıklandırılır)
  3. Ürün çeşitliliği  : Shannon çeşitlilik indeksinin etkin ürün sayısı karşılığı
                         (tek ürüne bağımlılık, fiyat ve hastalık riskini büyütür)
  4. Talep uyumu       : Ürünlerin denge oranlarının 1'e ne kadar yakın olduğu

Girdi: outputs/bolge.json (denge analizi) + outputs/urun.json (kaynak analizi)
Çıktı: outputs/karne.json

Not: Karne notu bir "başarı sıralaması" değil, planlama motorunun hangi ilde
neye öncelik vereceğini gösteren bir yön levhasıdır.
"""

import json
import math
from pathlib import Path

CIKTI = Path(__file__).resolve().parent.parent / "outputs"

AGIRLIK = dict(yem=0.30, su=0.25, cesitlilik=0.20, uyum=0.25)
HEDEF_URUN_CESIDI = 4       # etkin ürün sayısı bu değere ulaşınca çeşitlilik tam puan


def harf(puan):
    return "A" if puan >= 80 else "B" if puan >= 65 else "C" if puan >= 50 else "D"


def uret():
    bolge = json.loads((CIKTI / "bolge.json").read_text(encoding="utf-8"))
    urun_veri = json.loads((CIKTI / "urun.json").read_text(encoding="utf-8"))

    # (il, ürün) -> kaynak kaydı
    kaynak = {}
    for u in urun_veri["urunler"]:
        for r in u["iller"]:
            kaynak[(r["il"], u["urun"])] = dict(r, tr_durum=u["tr_durum"])

    iller = []
    for i in bolge["iller"]:
        urunler = []
        for p in i["urunler"]:
            k = kaynak.get((i["il"], p["urun"]), {})
            urunler.append(dict(p, **{a: k.get(a) for a in (
                "su_ton_basi", "mavi_su_ton_basi", "elektrik_ton_basi", "mazot_ton_basi",
                "karbon_ton_basi", "toplam_su_m3", "mavi_su_m3", "elektrik_kwh",
                "mazot_lt", "gubre_kg", "karbon_kg", "sulanan_alan_dekar", "yagis_mm")}))

        toplam_uretim = sum(u["uretim_ton"] for u in urunler) or 1
        toplam = dict(
            su_m3=sum(u["toplam_su_m3"] or 0 for u in urunler),
            mavi_su_m3=sum(u["mavi_su_m3"] or 0 for u in urunler),
            elektrik_kwh=sum(u["elektrik_kwh"] or 0 for u in urunler),
            mazot_lt=sum(u["mazot_lt"] or 0 for u in urunler),
            gubre_kg=sum(u["gubre_kg"] or 0 for u in urunler),
            karbon_kg=sum(u["karbon_kg"] or 0 for u in urunler),
            uretim_ton=toplam_uretim,
            sulanan_alan_dekar=sum(u["sulanan_alan_dekar"] or 0 for u in urunler))

        # --- Gösterge 3: ürün çeşitliliği (Shannon -> etkin ürün sayısı)
        paylar = [u["uretim_ton"] / toplam_uretim for u in urunler if u["uretim_ton"] > 0]
        shannon = -sum(p * math.log(p) for p in paylar) if paylar else 0
        etkin_urun = math.exp(shannon) if shannon else 1
        cesitlilik_puan = min(100, etkin_urun / HEDEF_URUN_CESIDI * 100)

        # --- Gösterge 4: talep uyumu (denge oranlarının 1'e yakınlığı)
        sapmalar = [min(abs(math.log(max(u["oran"], 0.05))), 1.5) for u in urunler]
        uyum_puan = max(0, 100 * (1 - (sum(sapmalar) / len(sapmalar)) / 1.5)) if sapmalar else 0

        # --- Gösterge 1: yem yeterliliği
        yem_puan = min(100, (i["kaba_yem_orani"] or 0) * 100)

        iller.append(dict(
            il=i["il"], bolge=i["bolge"], nufus=i["nufus"],
            buyukbas=i["buyukbas"], kucukbas=i["kucukbas"], hayvan_birimi=i["hayvan_birimi"],
            toplam_alan_dekar=i["toplam_alan_dekar"], mera_dekar=i.get("mera_dekar", 0),
            kaba_yem_orani=i["kaba_yem_orani"], kaba_yem_arz_ton=i["kaba_yem_arz_ton"],
            kaba_yem_ihtiyac_ton=i["kaba_yem_ihtiyac_ton"],
            kaba_yem_acigi_ton=i["kaba_yem_acigi_ton"],
            oneri=i["oneri"], urunler=urunler, toplam=toplam,
            mavi_su_ton_basi=round(toplam["mavi_su_m3"] / toplam_uretim),
            karbon_ton_basi=round(toplam["karbon_kg"] / toplam_uretim),
            etkin_urun_sayisi=round(etkin_urun, 2),
            puan=dict(yem=round(yem_puan), cesitlilik=round(cesitlilik_puan),
                      uyum=round(uyum_puan))))

    # --- Gösterge 2: su verimliliği
    # Ürün karması yanlılığını önlemek için her il, ÜRÜN BAZINDA bölge ortalamasıyla
    # karşılaştırılır. Şeker pancarı gibi verimi yüksek bir ürün, ton başına suyu
    # kendiliğinden düşürdüğü için ham "m³/ton" karşılaştırması adil değildir.
    urun_ort = {}
    for r in iller:
        for u in r["urunler"]:
            urun_ort.setdefault(u["urun"], []).append(u["mavi_su_ton_basi"] or 0)
    urun_ort = {k: (sum(v) / len(v)) for k, v in urun_ort.items()}

    for r in iller:
        toplam_uretim = max(r["toplam"]["uretim_ton"], 1)
        endeks, agirlik_top = 0.0, 0.0
        for u in r["urunler"]:
            ort = urun_ort[u["urun"]]
            deger = u["mavi_su_ton_basi"] or 0
            if ort <= 0:
                oran = 1.0                      # bu üründe hiçbir ilde sulama yok
            elif deger <= 0:
                oran = 2.0                      # sulamasız üretiyor: en iyi durum
            else:
                oran = min(2.0, ort / deger)    # ortalamadan iyiyse 1'in üstünde
            agirlik = u["uretim_ton"] / toplam_uretim
            endeks += oran * agirlik
            agirlik_top += agirlik
        endeks = endeks / agirlik_top if agirlik_top else 1.0
        r["su_endeksi"] = round(endeks, 2)
        r["puan"]["su"] = round(max(0, min(100, endeks * 50)))

    for sira, r in enumerate(sorted(iller, key=lambda x: -x["puan"]["su"])):
        r["su_sirasi"] = sira + 1

    # --- Toplam not
    for r in iller:
        p = r["puan"]
        genel = sum(p[k] * AGIRLIK[k] for k in AGIRLIK)
        r["genel_puan"] = round(genel)
        r["harf"] = harf(genel)

    # --- Bölge sıralamaları
    for anahtar, ters in (("genel_puan", True), ("toplam_alan_dekar", True),
                          ("kaba_yem_orani", True)):
        s = sorted(iller, key=lambda r: (r[anahtar] is None, r[anahtar]), reverse=ters)
        for sira, r in enumerate(s):
            r.setdefault("siralar", {})[anahtar] = sira + 1

    iller.sort(key=lambda r: -r["genel_puan"])
    sonuc = dict(iller=iller, agirlik=AGIRLIK, il_sayisi=len(iller))
    (CIKTI / "karne.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    return sonuc


if __name__ == "__main__":
    s = uret()
    print(f"{'İL':<12}{'NOT':>4}{'GENEL':>7}{'YEM':>6}{'SU':>5}{'ÇEŞİT':>7}{'UYUM':>6}"
          f"{'MAVİ SU m³/t':>14}{'ETKİN ÜRÜN':>12}")
    for r in s["iller"]:
        p = r["puan"]
        print(f"{r['il']:<12}{r['harf']:>4}{r['genel_puan']:>7}{p['yem']:>6}{p['su']:>5}"
              f"{p['cesitlilik']:>7}{p['uyum']:>6}{r['mavi_su_ton_basi']:>14,}"
              f"{r['etkin_urun_sayisi']:>12}")
