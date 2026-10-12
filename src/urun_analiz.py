"""
AGROMATCH - Ürün bazlı tam analiz
=================================
Her ürün için üç soruyu birlikte cevaplar:

  1. NEREDE ÜRETİLİYOR?  -> il il üretim, alan, verim
  2. NEREYE GİDİYOR?     -> bölge içi tüketim / ülke içi diğer illere sevk / ihracat
  3. NEYE MAL OLUYOR?    -> su, sulama elektriği, mazot, gübre ve karbon

Üçüncü soru projenin ayırt edici tarafıdır: aynı ürünün farklı illerde farklı
kaynak maliyeti vardır. Bir ton buğday, yağışın bol olduğu bir ilde neredeyse
sulamasız üretilirken, kurak bir ilde yüz metrelerce derinlikten çekilen suyla
üretilir. "Bilinçli ekim" kararı bu farkı görmeden verilemez.

Çıktı: outputs/urun.json
"""

import json
from pathlib import Path

from bolge_profil import DESEN, ILLER, KISI_BASI_KG, TIP_GIDA, URUN_TIPI
from bolge_analiz import TR_DURUM, il_ihtiyaci
from kaynak_profil import (CAZIBE_ILLERI, ETKIN_YAGIS_KISLIK, ETKIN_YAGIS_YAZLIK,
                           KARBON_ELEKTRIK, KARBON_GUBRE, KARBON_MAZOT, KAYNAK,
                           POMPA_CAZIBE, POMPA_VARSAYILAN, YAGIS)

CIKTI = Path(__file__).resolve().parent.parent / "outputs"


def il_kaynak(il, urun, alan_dekar, uretim_ton):
    """Bir ilin bir üründe harcadığı kaynakları hesaplar."""
    su_ihtiyaci, mazot_da, gubre_da, sulama_orani, kislik, _ = KAYNAK[urun]

    etkin_pay = ETKIN_YAGIS_KISLIK if kislik else ETKIN_YAGIS_YAZLIK
    yesil_su_mm = min(su_ihtiyaci, YAGIS[il] * etkin_pay)       # yağıştan gelen
    acik_mm = max(0.0, su_ihtiyaci - yesil_su_mm)               # sulamayla kapatılması gereken
    mavi_su_mm = acik_mm * sulama_orani                          # fiilen sulanan alanda verilen

    sulanan_alan = alan_dekar * sulama_orani
    mavi_su_m3 = mavi_su_mm * alan_dekar          # mm = m³/dekar
    yesil_su_m3 = yesil_su_mm * alan_dekar
    pompa = POMPA_CAZIBE if il in CAZIBE_ILLERI else POMPA_VARSAYILAN
    elektrik_kwh = mavi_su_m3 * pompa

    # Sulanan alanda mekanizasyon ve gübre kullanımı daha yüksektir
    mazot_lt = alan_dekar * mazot_da * (1 + 0.25 * sulama_orani)
    gubre_kg = alan_dekar * gubre_da

    karbon_kg = (mazot_lt * KARBON_MAZOT + elektrik_kwh * KARBON_ELEKTRIK
                 + gubre_kg * KARBON_GUBRE)

    t = max(uretim_ton, 1)
    return dict(
        sulanan_alan_dekar=round(sulanan_alan),
        yesil_su_m3=round(yesil_su_m3), mavi_su_m3=round(mavi_su_m3),
        toplam_su_m3=round(yesil_su_m3 + mavi_su_m3),
        elektrik_kwh=round(elektrik_kwh), mazot_lt=round(mazot_lt),
        gubre_kg=round(gubre_kg), karbon_kg=round(karbon_kg),
        su_ton_basi=round((yesil_su_m3 + mavi_su_m3) / t),
        mavi_su_ton_basi=round(mavi_su_m3 / t),
        elektrik_ton_basi=round(elektrik_kwh / t, 1),
        mazot_ton_basi=round(mazot_lt / t, 1),
        karbon_ton_basi=round(karbon_kg / t),
        pompa_katsayisi=pompa,
        yagis_mm=YAGIS[il],
    )


def analiz():
    urunler = {}

    for il in ILLER:
        for urun, (alan, verim, talep) in DESEN[il].items():
            uretim = alan * verim
            k = il_kaynak(il, urun, alan, uretim)
            kayit = urunler.setdefault(urun, dict(
                urun=urun, tip=URUN_TIPI[urun], tr_durum=TR_DURUM[urun],
                ihracat_payi=KAYNAK[urun][5], su_ihtiyaci_mm=KAYNAK[urun][0],
                sulama_orani=KAYNAK[urun][3], iller=[]))
            kayit["iller"].append(dict(
                il=il, bolge=ILLER[il][0], alan_dekar=alan, verim=verim,
                uretim_ton=round(uretim),
                ihtiyac_ton=round(il_ihtiyaci(il, urun, talep)), **k))

    for urun, k in urunler.items():
        iller = sorted(k["iller"], key=lambda r: -r["uretim_ton"])
        k["iller"] = iller
        toplam_uretim = sum(r["uretim_ton"] for r in iller)
        toplam_ihtiyac = sum(r["ihtiyac_ton"] for r in iller)

        # --- Dağılım: ürün nereye gidiyor?
        bolge_tuketim = min(toplam_uretim, toplam_ihtiyac)
        artan = max(0, toplam_uretim - bolge_tuketim)
        ihracat = artan * k["ihracat_payi"]
        ulke_ici = artan - ihracat

        t = max(toplam_uretim, 1)
        k.update(
            il_sayisi=len(iller),
            toplam_alan_dekar=sum(r["alan_dekar"] for r in iller),
            toplam_uretim_ton=toplam_uretim,
            bolge_ihtiyaci_ton=round(toplam_ihtiyac),
            ortalama_verim=round(toplam_uretim / max(sum(r["alan_dekar"] for r in iller), 1), 3),
            dagitim=dict(bolge_tuketim_ton=round(bolge_tuketim),
                         ulke_ici_sevk_ton=round(ulke_ici),
                         ihracat_ton=round(ihracat)),
            toplam=dict(
                su_m3=sum(r["toplam_su_m3"] for r in iller),
                mavi_su_m3=sum(r["mavi_su_m3"] for r in iller),
                elektrik_kwh=sum(r["elektrik_kwh"] for r in iller),
                mazot_lt=sum(r["mazot_lt"] for r in iller),
                gubre_kg=sum(r["gubre_kg"] for r in iller),
                karbon_kg=sum(r["karbon_kg"] for r in iller)),
        )
        k["birim"] = dict(
            su=round(k["toplam"]["su_m3"] / t),
            mavi_su=round(k["toplam"]["mavi_su_m3"] / t),
            elektrik=round(k["toplam"]["elektrik_kwh"] / t, 1),
            mazot=round(k["toplam"]["mazot_lt"] / t, 1),
            gubre=round(k["toplam"]["gubre_kg"] / t, 1),
            karbon=round(k["toplam"]["karbon_kg"] / t))

        # --- En verimli ve en pahalı il (ton başına toplam su)
        sirali = sorted(iller, key=lambda r: r["su_ton_basi"])
        k["en_verimli_il"] = dict(il=sirali[0]["il"], su_ton_basi=sirali[0]["su_ton_basi"])
        k["en_maliyetli_il"] = dict(il=sirali[-1]["il"], su_ton_basi=sirali[-1]["su_ton_basi"])
        k["makas"] = (round(sirali[-1]["su_ton_basi"] / max(sirali[0]["su_ton_basi"], 1), 1)
                      if len(sirali) > 1 else 1.0)

    sirali_urunler = sorted(urunler.values(), key=lambda k: -k["toplam_uretim_ton"])
    sonuc = dict(urunler=sirali_urunler)
    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "urun.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    return sonuc


if __name__ == "__main__":
    s = analiz()
    print(f"{'ÜRÜN':<15}{'ÜRETİM ton':>12}{'SU m³/ton':>11}{'MAVİ SU':>9}"
          f"{'ELEKTRİK kWh/t':>15}{'MAZOT lt/t':>11}{'CO2 kg/t':>10}  MAKAS")
    for k in s["urunler"]:
        print(f"{k['urun']:<15}{k['toplam_uretim_ton']:>12,}{k['birim']['su']:>11,}"
              f"{k['birim']['mavi_su']:>9,}{k['birim']['elektrik']:>15}"
              f"{k['birim']['mazot']:>11}{k['birim']['karbon']:>10,}"
              f"  {k['makas']}x ({k['en_verimli_il']['il']} → {k['en_maliyetli_il']['il']})")
