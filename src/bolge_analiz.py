"""
AGROMATCH - Doğu ve Güneydoğu Anadolu il il denge analizi
=========================================================
Her il için ürün bazında arz ve ihtiyaç karşılaştırılır. İhtiyaç, ürünün
tipine göre farklı kuralla hesaplanır:

  gıda        -> il nüfusu x kişi başı tüketim
  kaba yem    -> büyükbaş x 2.6 ton + küçükbaş x 0.32 ton (kuru ot eşdeğeri)
  kesif yem   -> büyükbaş x 0.75 ton + küçükbaş x 0.09 ton
  sanayi      -> fabrika kotası / sözleşmeli alım miktarı
  pazar       -> yurt içi pazar payı + ihracat talebi

Yorumlama kuralı (ÖNEMLİ):
  Bir ilin kendi tüketiminden fazla üretmesi tek başına "gereksiz ekim" değildir;
  ürün ülke arzına gidiyor olabilir. Bu yüzden her ürün, Türkiye'nin o üründeki
  net durumu (ithalatçı / dengede / ihracatçı) ile birlikte değerlendirilir.
  Gerçek israf, ülke düzeyinde de fazla olan üründe yapılan ekimdir.

Çıktı: outputs/bolge.json
"""

import json
from pathlib import Path

from bolge_profil import (
    ANIZ_VERIM,
    DESEN,
    ILLER,
    KABA_YEM_BUYUKBAS,
    KABA_YEM_KUCUKBAS,
    KESIF_YEM_BUYUKBAS,
    KESIF_YEM_KUCUKBAS,
    KISI_BASI_KG,
    MERA,
    MERA_VERIM,
    TIP_GIDA,
    TIP_KABA_YEM,
    TIP_KESIF_YEM,
    TIP_PAZAR,
    TIP_SANAYI,
    URUN_TIPI,
)

CIKTI = Path(__file__).resolve().parent.parent / "outputs"

# Türkiye'nin ürün bazında net dış ticaret durumu (doğrulanacak varsayım)
TR_DURUM = {
    "Buğday": "ithalatçı", "Arpa": "ithalatçı", "Mısır (dane)": "ithalatçı",
    "Mercimek": "ithalatçı", "Pamuk": "ithalatçı", "Yem bitkileri": "ithalatçı",
    "Şeker pancarı": "kotalı", "Patates": "dengede", "Tütün": "ihracatçı",
    "Antep fıstığı": "ihracatçı", "Kayısı": "ihracatçı", "Üzüm": "ihracatçı",
    "Zeytin": "ihracatçı", "Elma": "ihracatçı", "Karpuz": "dengede",
    "Yer fıstığı": "dengede",
}

ESIK_FAZLA, ESIK_ACIK = 1.10, 0.95


def il_ihtiyaci(il, urun, pazar_talebi):
    _, nufus, buyukbas, kucukbas = ILLER[il]
    tip = URUN_TIPI[urun]
    if tip == TIP_GIDA:
        return nufus * KISI_BASI_KG[urun] / 1000
    if tip == TIP_KABA_YEM:
        return buyukbas * KABA_YEM_BUYUKBAS + kucukbas * KABA_YEM_KUCUKBAS
    if tip == TIP_KESIF_YEM:
        # Kesif yem ihtiyacı arpa ve mısır arasında paylaşılır
        desen_kesif = [u for u in DESEN[il] if URUN_TIPI[u] == TIP_KESIF_YEM]
        toplam = buyukbas * KESIF_YEM_BUYUKBAS + kucukbas * KESIF_YEM_KUCUKBAS
        return toplam / max(len(desen_kesif), 1)
    if tip in (TIP_SANAYI, TIP_PAZAR):
        return float(pazar_talebi)
    raise ValueError(urun)


def analiz():
    iller = []
    for il, (bolge, nufus, buyukbas, kucukbas) in ILLER.items():
        urunler = []
        for urun, (alan, verim, talep) in DESEN[il].items():
            uretim = alan * verim
            ihtiyac = il_ihtiyaci(il, urun, talep)
            oran = uretim / ihtiyac if ihtiyac > 0 else float("nan")
            durum = ("FAZLA" if oran > ESIK_FAZLA else
                     "AÇIK" if oran < ESIK_ACIK else "DENGEDE")
            urunler.append(dict(
                urun=urun, tip=URUN_TIPI[urun], tr_durum=TR_DURUM[urun],
                alan_dekar=alan, verim=verim,
                uretim_ton=round(uretim), ihtiyac_ton=round(ihtiyac),
                oran=round(oran, 2), fark_ton=round(uretim - ihtiyac),
                durum=durum))

        # --- Bölgeye özgü kritik gösterge: kaba yem dengesi
        # Arz = ekilen yem bitkileri + çayır-mera otlatması
        yem = next((u for u in urunler if u["tip"] == TIP_KABA_YEM), None)
        mera_ton = MERA.get(il, 0) * MERA_VERIM
        # Anız ve nadas otlatması: tahıl/baklagil alanlarının hasat sonrası kaba yem katkısı
        aniz_alani = sum(u["alan_dekar"] for u in urunler
                         if u["urun"] in ("Buğday", "Arpa", "Mercimek", "Mısır (dane)"))
        aniz_ton = aniz_alani * ANIZ_VERIM
        yem_ihtiyac = buyukbas * KABA_YEM_BUYUKBAS + kucukbas * KABA_YEM_KUCUKBAS
        yem_arz = (yem["uretim_ton"] if yem else 0) + mera_ton + aniz_ton
        yem_orani = yem_arz / yem_ihtiyac if yem_ihtiyac else None
        yem_acigi = max(0, yem_ihtiyac - yem_arz)

        # --- Öneri motoru: yem açığını, ülke düzeyinde de fazla olmayan ama
        # ilde aşırı yayılmış tahıl alanından kaydırarak kapatmayı önerir.
        oneri = None
        if yem and yem_acigi > 0:
            gereken_dekar = yem_acigi / yem["verim"]
            # Kaynak: öz yeterliliği 2 katın üstünde olan tahıl alanı
            kaynaklar = [u for u in urunler
                         if u["tip"] in (TIP_GIDA, TIP_KESIF_YEM) and u["oran"] > 1.5]
            kaynaklar.sort(key=lambda u: u["oran"], reverse=True)
            if kaynaklar:
                k = kaynaklar[0]
                serbest_dekar = k["alan_dekar"] * (1 - 1.5 / k["oran"])
                aktarilacak = int(min(gereken_dekar, serbest_dekar))
                kapanan = aktarilacak * yem["verim"]
                oneri = dict(
                    kaynak_urun=k["urun"], hedef_urun=yem["urun"],
                    aktarilacak_dekar=aktarilacak,
                    kapanan_acik_ton=round(kapanan),
                    kapanma_orani=round(kapanan / yem_acigi, 2) if yem_acigi else 0,
                    metin=(f"{k['urun']} alanının {aktarilacak:,} dekarı yem bitkisine "
                           f"kaydırılırsa kaba yem açığının %"
                           f"{min(100, round(kapanan / yem_acigi * 100))}'i kapanır")
                    .replace(",", "."))

        iller.append(dict(
            il=il, bolge=bolge, nufus=nufus, buyukbas=buyukbas, kucukbas=kucukbas,
            hayvan_birimi=round(buyukbas + kucukbas * 0.15),
            toplam_alan_dekar=sum(a for a, _, _ in DESEN[il].values()),
            urunler=urunler,
            mera_dekar=MERA.get(il, 0),
            aniz_ton=round(aniz_ton),
            kaba_yem_arz_ton=round(yem_arz),
            kaba_yem_ihtiyac_ton=round(yem_ihtiyac),
            kaba_yem_orani=round(yem_orani, 2) if yem_orani else None,
            kaba_yem_acigi_ton=round(yem_acigi),
            oneri=oneri))

    iller.sort(key=lambda x: (x["bolge"], x["il"]))

    # --- Bölge özeti
    def ozet(bolge_adi):
        grup = [i for i in iller if i["bolge"] == bolge_adi] if bolge_adi else iller
        yem_acik_il = [i for i in grup if i["kaba_yem_orani"] is not None
                       and i["kaba_yem_orani"] < ESIK_ACIK]
        return dict(
            bolge=bolge_adi or "Toplam",
            il_sayisi=len(grup),
            yem_acigi_olan_il=len(yem_acik_il),
            toplam_yem_acigi_ton=sum(i["kaba_yem_acigi_ton"] for i in grup),
            toplam_ekim_alani_dekar=sum(i["toplam_alan_dekar"] for i in grup),
            hayvan_birimi=sum(i["hayvan_birimi"] for i in grup))

    sonuc = dict(
        iller=iller,
        ozet=[ozet("Doğu Anadolu"), ozet("Güneydoğu Anadolu"), ozet(None)],
        esikler=dict(fazla=ESIK_FAZLA, acik=ESIK_ACIK),
    )
    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "bolge.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    return sonuc


if __name__ == "__main__":
    s = analiz()
    for o in s["ozet"]:
        print(f"{o['bolge']:<20} {o['il_sayisi']:>2} il | yem açığı olan il: "
              f"{o['yem_acigi_olan_il']:>2} | toplam açık: {o['toplam_yem_acigi_ton']:>12,} ton")
    print()
    for i in s["iller"]:
        yem = f"{i['kaba_yem_orani']:.2f}" if i["kaba_yem_orani"] else "  - "
        print(f"{i['il']:<11} {i['bolge']:<17} yem oranı {yem} | "
              + ", ".join(f"{u['urun']}:{u['oran']:.2f}" for u in i["urunler"]))
        if i["oneri"]:
            print(f"            -> {i['oneri']['metin']}")
