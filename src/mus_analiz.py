"""
AGROMATCH - Muş analiz motoru
=============================
mus_profil.py'deki veriyi alır, altı ilçe için şunları hesaplar:

  1. Arz / ihtiyaç dengesi  — hangi üründe fazla, hangisinde açık var
  2. Yem bilançosu          — mera + anız + yem bitkileri vs hayvan ihtiyacı
  3. Su ve enerji           — sulama suyu m3, pompa elektriği, mazot, karbon
  4. Fabrika kotası         — şeker pancarı alanının üst sınırı ve dağıtımı
  5. İlçe karnesi           — yem, su, çeşitlilik, toprak uyumu puanları
  6. Ekim önerisi           — gelecek sezon için alan kaydırma önerisi

Çıktı: outputs/mus.json

    python src/mus_analiz.py
"""

import json
import math
from pathlib import Path

import mus_profil as mp

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "outputs"

ESIK_FAZLA = 1.10      # arz/ihtiyaç bunun üstündeyse "fazla"
ESIK_ACIK = 0.95       # bunun altındaysa "açık"


def sayi(x, basamak=0):
    """Türkçe binlik ayracı: 570000 -> 570.000"""
    return f"{x:,.{basamak}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------- 1. denge
def ihtiyac_hesapla(ilce):
    """Bir ilçenin ürün bazında yıllık ihtiyacını ton cinsinden döndürür."""
    rakim, nufus, bb, kb, mera, sul = mp.ILCE[ilce]
    ihtiyac = {}

    # Gıda: kişi başı tüketim
    for urun, kisi_basi in mp.GIDA_IHTIYAC.items():
        ihtiyac[urun] = nufus * kisi_basi

    # Tohumluk ve fire payı: ekilen alanın kendi tohumu
    for urun, (alan, verim) in mp.DESEN[ilce].items():
        if mp.URUN[urun][0] in ("gıda", "kesif"):
            ihtiyac[urun] = ihtiyac.get(urun, 0) + alan * verim * 0.08

    # Kaba yem: hayvan ihtiyacından mera, anız ve kesif yem düşüldükten sonra
    # kalanı yem bitkileri karşılamak zorunda. Hesap kuru madde (KM) üzerinden
    # yapılır; yoksa 0,32 KM'li silaj ile 0,88 KM'li kuru ot toplanamaz.
    yem = yem_bilancosu(ilce)
    kalan = max(0.0, yem["ihtiyac_ton"] - yem["mera_ton"]
                - yem["aniz_ton"] - yem["kesif_ton"])
    kaba_urunler = [u for u in mp.DESEN[ilce] if mp.URUN[u][0] == "kaba"]
    kaba_uretim = sum(mp.DESEN[ilce][u][0] * mp.DESEN[ilce][u][1] * kuru_madde(u)
                      for u in kaba_urunler)
    for u in kaba_urunler:
        pay = (mp.DESEN[ilce][u][0] * mp.DESEN[ilce][u][1] * kuru_madde(u)
               / kaba_uretim) if kaba_uretim else 1 / len(kaba_urunler)
        ihtiyac[u] = kalan * pay      # KM cinsinden

    # Kesif yem: arpa — hayvan başına yoğun yem
    ihtiyac["Arpa"] = ihtiyac.get("Arpa", 0) + bb * 0.75 + kb * 0.06

    # Sanayi: şeker pancarı fabrika kotasıyla belirlenir, ilçe tüketimi yok
    ihtiyac["Şeker pancarı"] = kota_dagitimi().get(ilce, 0.0)
    return ihtiyac


def kuru_madde(urun):
    """Kuru madde oranı; tek tanım mus_profil'de durur."""
    return mp.kuru_madde(urun)


def denge_analizi():
    satirlar = []
    for ilce in mp.ILCE:
        ihtiyac = ihtiyac_hesapla(ilce)
        for urun, (alan, verim) in mp.DESEN[ilce].items():
            kaba = mp.URUN[urun][0] == "kaba"
            # Kaba yemde her iki taraf da kuru madde; diğerlerinde ürün ağırlığı
            uretim = alan * verim * (kuru_madde(urun) if kaba else 1.0)
            ihty = ihtiyac.get(urun, 0.0)
            oran = uretim / ihty if ihty > 0 else None
            if oran is None:
                durum = "ihtiyaç tanımsız"
            elif oran > ESIK_FAZLA:
                durum = "fazla"
            elif oran < ESIK_ACIK:
                durum = "açık"
            else:
                durum = "dengeli"
            # Hedef alan, ihtiyacı bugünkü verimle karşılayacak ekim alanı
            etkin_verim = verim * (kuru_madde(urun) if kaba else 1.0)
            satirlar.append(dict(
                ilce=ilce, urun=urun, tip=mp.URUN[urun][0],
                alan_dekar=alan, verim=verim, birim="ton KM" if kaba else "ton",
                uretim_ton=round(uretim, 1), ihtiyac_ton=round(ihty, 1),
                oran=round(oran, 3) if oran else None, durum=durum,
                hedef_alan=(round(ihty / etkin_verim)
                            if ihty > 0 and etkin_verim > 0 else None),
            ))
    return satirlar


# -------------------------------------------------------- 2. yem bilançosu
def yem_bilancosu(ilce):
    rakim, nufus, bb, kb, mera, sul = mp.ILCE[ilce]
    ihtiyac = bb * mp.YEM_IHTIYAC["buyukbas"] + kb * mp.YEM_IHTIYAC["kucukbas"]

    mera_ton = mera * mp.MERA_VERIM
    tahil_alan = sum(mp.DESEN[ilce].get(u, (0, 0))[0] for u in ("Buğday", "Arpa"))
    aniz_ton = tahil_alan * mp.ANIZ_VERIM

    kaba_ton = sum(a * v * kuru_madde(u)
                   for u, (a, v) in mp.DESEN[ilce].items()
                   if mp.URUN[u][0] == "kaba")
    # Arpa danesinin yem olarak kullanılan payı (dane KM ~%87)
    arpa_a, arpa_v = mp.DESEN[ilce].get("Arpa", (0, 0))
    kesif_ton = arpa_a * arpa_v * 0.87 * 0.70

    arz = mera_ton + aniz_ton + kaba_ton + kesif_ton
    return dict(
        ilce=ilce, buyukbas=bb, kucukbas=kb,
        ihtiyac_ton=round(ihtiyac), mera_ton=round(mera_ton),
        aniz_ton=round(aniz_ton), kaba_ton=round(kaba_ton),
        kesif_ton=round(kesif_ton), arz_ton=round(arz),
        acik_ton=round(max(0.0, ihtiyac - arz)),
        karsilama=round(arz / ihtiyac, 3) if ihtiyac else None,
        # Açığı kapatmak için gereken ek yonca alanı
        ek_yonca_dekar=round(max(0.0, ihtiyac - arz) / (0.95 * 0.88)) if ihtiyac else 0,
    )


# ---------------------------------------------------------- 3. su ve enerji
def kaynak_analizi():
    satirlar = []
    for ilce in mp.ILCE:
        rakim, nufus, bb, kb, mera, sul_oran = mp.ILCE[ilce]
        sicaklik, yagis, don = mp.IKLIM[ilce]
        for urun, (alan, verim) in mp.DESEN[ilce].items():
            tip, su_mm, mazot, n, p, k, fiyat, maliyet, destek, kislik = mp.URUN[urun]

            # Yeşil su: kışlık ürün yağışın daha büyük payını kullanır
            etkin_yagis = yagis * (0.70 if kislik else 0.42)
            net_mm = max(0.0, su_mm - etkin_yagis)
            sulanan = alan * (sul_oran if not kislik else sul_oran * 0.35)
            mavi_m3 = sulanan * net_mm          # 1 mm = 1 m3/dekar
            yesil_m3 = alan * min(su_mm, etkin_yagis)

            elektrik = mavi_m3 * mp.POMPA_KWH_M3
            mazot_l = alan * mazot
            uretim = alan * verim

            karbon = (mazot_l * mp.MAZOT_KG_CO2
                      + elektrik * mp.ELEKTRIK_KG_CO2
                      + alan * n * mp.AZOT_KG_CO2) / 1000  # ton CO2e

            satirlar.append(dict(
                ilce=ilce, urun=urun, alan_dekar=alan,
                uretim_ton=round(uretim, 1),
                mavi_su_m3=round(mavi_m3), yesil_su_m3=round(yesil_m3),
                su_ton_basina=round(mavi_m3 / uretim, 1) if uretim else None,
                elektrik_kwh=round(elektrik), mazot_litre=round(mazot_l),
                karbon_ton=round(karbon, 1),
                karbon_ton_basina=round(karbon * 1000 / uretim, 1) if uretim else None,
            ))
    return satirlar


# ------------------------------------------------------- 4. fabrika kotası
def kota_dagitimi():
    """Fabrika kapasitesini ilçelere mevcut alan ve verim payına göre dağıtır."""
    tavan = mp.FABRIKA["gunluk_kapasite_ton"] * mp.FABRIKA["kampanya_gun"]
    uretimler = {ilce: mp.DESEN[ilce].get("Şeker pancarı", (0, 0))[0]
                 * mp.DESEN[ilce].get("Şeker pancarı", (0, 0))[1]
                 for ilce in mp.ILCE}
    toplam = sum(uretimler.values())
    if toplam <= tavan:
        return uretimler                      # kota bağlayıcı değil
    k = tavan / toplam
    return {ilce: u * k for ilce, u in uretimler.items()}


def kota_ozeti():
    tavan = mp.FABRIKA["gunluk_kapasite_ton"] * mp.FABRIKA["kampanya_gun"]
    uretim = sum(mp.DESEN[i].get("Şeker pancarı", (0, 0))[0]
                 * mp.DESEN[i].get("Şeker pancarı", (0, 0))[1] for i in mp.ILCE)
    alan = sum(mp.DESEN[i].get("Şeker pancarı", (0, 0))[0] for i in mp.ILCE)
    ort_verim = uretim / alan if alan else 0
    return dict(
        fabrika=mp.FABRIKA["ad"],
        tavan_ton=tavan, uretim_ton=round(uretim),
        doluluk=round(uretim / tavan, 3) if tavan else None,
        mevcut_alan_dekar=alan,
        tavan_alan_dekar=round(tavan / ort_verim) if ort_verim else None,
        bos_alan_dekar=round(tavan / ort_verim - alan) if ort_verim else None,
        ortalama_verim=round(ort_verim, 2),
        ilce=[dict(ilce=i,
                   alan=mp.DESEN[i].get("Şeker pancarı", (0, 0))[0],
                   uretim=round(mp.DESEN[i].get("Şeker pancarı", (0, 0))[0]
                               * mp.DESEN[i].get("Şeker pancarı", (0, 0))[1]),
                   kota=round(kota_dagitimi()[i]))
              for i in mp.ILCE],
    )


# ---------------------------------------------------------- 5. ilçe karnesi
AGIRLIK = dict(yem=0.32, su=0.24, cesitlilik=0.18, toprak=0.26)


def cesitlilik(ilce):
    """Shannon çeşitlilik -> etkin ürün sayısı."""
    alanlar = [a for a, v in mp.DESEN[ilce].values()]
    toplam = sum(alanlar)
    if not toplam:
        return 0.0
    h = -sum((a / toplam) * math.log(a / toplam) for a in alanlar if a > 0)
    return math.exp(h)


def karne(toprak_puanlari=None):
    kaynak = kaynak_analizi()
    # Ürün bazında il ortalaması su yoğunluğu — ürün karmasından arındırmak için
    il_ort = {}
    for r in kaynak:
        if r["su_ton_basina"] is not None:
            il_ort.setdefault(r["urun"], []).append(r["su_ton_basina"])
    il_ort = {u: sum(v) / len(v) for u, v in il_ort.items()}

    satirlar = []
    for ilce in mp.ILCE:
        yem = yem_bilancosu(ilce)
        yem_puan = max(0, min(100, (yem["karsilama"] or 0) * 100))

        # Suyun ürün-göreli etkinliği: her üründe il ortalamasına kıyas
        agirlikli, toplam_alan = 0.0, 0
        for r in kaynak:
            if r["ilce"] != ilce or r["su_ton_basina"] is None:
                continue
            ort = il_ort.get(r["urun"], 0)
            deger = r["su_ton_basina"]
            oran = 1.0 if ort <= 0 else (2.0 if deger <= 0 else min(2.0, ort / deger))
            agirlikli += oran * r["alan_dekar"]
            toplam_alan += r["alan_dekar"]
        endeks = agirlikli / toplam_alan if toplam_alan else 1.0
        su_puan = max(0, min(100, endeks * 50))

        etkin = cesitlilik(ilce)
        ces_puan = max(0, min(100, (etkin - 1) / (len(mp.URUN) - 1) * 100))

        top_puan = (toprak_puanlari or {}).get(ilce, 60.0)

        toplam = (AGIRLIK["yem"] * yem_puan + AGIRLIK["su"] * su_puan
                  + AGIRLIK["cesitlilik"] * ces_puan + AGIRLIK["toprak"] * top_puan)

        satirlar.append(dict(
            ilce=ilce,
            puan=dict(yem=round(yem_puan), su=round(su_puan),
                      cesitlilik=round(ces_puan), toprak=round(top_puan)),
            toplam=round(toplam, 1),
            etkin_urun=round(etkin, 2),
            yem_acik_ton=yem["acik_ton"],
            not_=mp.ILCE_NOTU[ilce],
        ))
    satirlar.sort(key=lambda r: -r["toplam"])
    for i, r in enumerate(satirlar, 1):
        r["sira"] = i
    return satirlar


# ----------------------------------------------------------- 6. ekim önerisi
def oneriler():
    """Her ilçe için somut, sayısal ekim kaydırma önerisi."""
    cikti = []
    kota = kota_ozeti()
    pay = {d["ilce"]: d for d in kota["ilce"]}

    for ilce in mp.ILCE:
        yem = yem_bilancosu(ilce)
        madde = []

        if yem["acik_ton"] > 0:
            madde.append(dict(
                oncelik=1, baslik="Kaba yem açığını kapat",
                metin=(f"{sayi(yem['acik_ton'])} ton kuru madde açık var "
                       f"(ihtiyacın %{round((1 - (yem['karsilama'] or 0)) * 100)}'i). "
                       f"Yaklaşık {sayi(yem['ek_yonca_dekar'])} dekar ek yonca ya da "
                       f"eşdeğeri korunga bunu kapatır."),
                kazanc="Dışarıdan yem alımı azalır, besi maliyeti düşer."))

        bos = kota["bos_alan_dekar"] or 0
        if bos > 0 and mp.DESEN[ilce].get("Şeker pancarı", (0, 0))[0] > 0:
            ilce_pay = round(bos * pay[ilce]["alan"] / kota["mevcut_alan_dekar"])
            if ilce_pay >= 100:
                madde.append(dict(
                    oncelik=2, baslik="Pancar alanı için boşluk var",
                    metin=(f"Fabrika tavanına göre il genelinde {sayi(bos)} dekar "
                           f"boşluk kaldı; bu ilçenin payı yaklaşık "
                           f"{sayi(ilce_pay)} dekar. Tavan aşılırsa sökülen pancar "
                           f"fabrikaya giremez."),
                    kazanc="Sözleşmeli alan güvenle büyütülebilir."))

        tp = mp.TOPRAK[ilce]
        if tp[9] == "zayıf":
            madde.append(dict(
                oncelik=1, baslik="Drenaj her şeyin önünde",
                metin=("Toprak drenajı zayıf. Gübre ya da çeşit değişikliğinden önce "
                       "tahliye kanalı açılmadan verim artışı kalıcı olmaz; "
                       "kök çürüklüğü ve rizoktonia riski yüksek kalır."),
                kazanc="Diğer bütün yatırımların getirisi buna bağlı."))
        if tp[2] >= 12:
            madde.append(dict(
                oncelik=3, baslik="Fosforu kireç bağlıyor",
                metin=(f"Kireç %{tp[2]}. Normal fosforlu gübrenin önemli kısmı "
                       f"bitkiye geçmiyor; bant uygulaması ya da asitleyici "
                       f"formülasyon gerekiyor."),
                kazanc="Aynı gübreden daha çok fayda."))
        if tp[10] >= 4:
            madde.append(dict(
                oncelik=2, baslik="Erozyon riski yüksek",
                metin=("Eğim ve toprak sığlığı nedeniyle erozyon riski yüksek. "
                       "Çok yıllık kaba yem (korunga) toprağı bağlar; "
                       "yıllık tahıl bu araziyi hızla yorar."),
                kazanc="Toprak derinliği korunur, uzun vadede verim düşmez."))

        etkin = cesitlilik(ilce)
        if etkin < 3.0:
            madde.append(dict(
                oncelik=3, baslik="Ürün deseni dar",
                metin=(f"Etkin ürün sayısı {etkin:.1f}. Tek ürüne bağımlılık "
                       f"fiyat ve hastalık şokunu doğrudan çiftçiye yansıtır."),
                kazanc="Risk dağılır, münavebe hastalık baskısını kırar."))

        madde.sort(key=lambda m: m["oncelik"])
        cikti.append(dict(ilce=ilce, maddeler=madde))
    return cikti


# --------------------------------------------------------------- toplayıcı
def calistir(toprak_puanlari=None):
    veri = dict(
        il="Muş",
        ilceler=[dict(ad=i, rakim=v[0], nufus=v[1], buyukbas=v[2],
                      kucukbas=v[3], mera_dekar=v[4], sulanabilir=v[5],
                      enlem=mp.KOORDINAT[i][0], boylam=mp.KOORDINAT[i][1],
                      sicaklik=mp.IKLIM[i][0], yagis=mp.IKLIM[i][1],
                      not_=mp.ILCE_NOTU[i])
                 for i, v in mp.ILCE.items()],
        urunler=[dict(ad=u, tip=d[0], su_mm=d[1], fiyat=d[6],
                      maliyet=d[7], destek=d[8], kislik=d[9])
                 for u, d in mp.URUN.items()],
        denge=denge_analizi(),
        yem=[yem_bilancosu(i) for i in mp.ILCE],
        kaynak=kaynak_analizi(),
        kota=kota_ozeti(),
        karne=karne(toprak_puanlari),
        oneri=oneriler(),
        kunye=[dict(alan=a, tur=t, kaynak=k, yil=y, guven=g, not_=n)
               for a, t, k, y, g, n in mp.KUNYE],
        olcum=[dict(ad=a, deger=d, birim=b, kaynak=k)
               for a, (d, b, k) in mp.OLCUM.items()],
        uretim=[dict(urun=u, ton=t, kaynak=k, verim=mp.VERIM[u],
                     alan=round(mp.il_alani(u)))
                for u, (t, k) in mp.URETIM.items()],
        kaynaklar=[dict(ad=a, baglanti=b) for a, b in mp.KAYNAK_BAGLANTI],
    )
    return veri


def main():
    CIKTI.mkdir(exist_ok=True)
    veri = calistir()
    (CIKTI / "mus.json").write_text(
        json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")

    print("Muş analizi tamam -> outputs/mus.json\n")

    k = veri["kota"]
    print(f"{k['fabrika']}: tavan {sayi(k['tavan_ton'])} ton, "
          f"üretim {sayi(k['uretim_ton'])} ton "
          f"(doluluk %{k['doluluk'] * 100:.0f})")
    print(f"  Pancar alanı {sayi(k['mevcut_alan_dekar'])} da, "
          f"tavan {sayi(k['tavan_alan_dekar'])} da -> "
          f"{sayi(k['bos_alan_dekar'])} da boşluk\n")

    print(f"{'İlçe':<11}{'Yem karş.':>11}{'Açık (ton)':>13}{'Etkin ürün':>12}{'Karne':>8}")
    for r in veri["karne"]:
        y = next(x for x in veri["yem"] if x["ilce"] == r["ilce"])
        print(f"{r['ilce']:<11}%{(y['karsilama'] or 0) * 100:>9.0f}"
              f"{sayi(y['acik_ton']):>13}{r['etkin_urun']:>12.2f}{r['toplam']:>8.1f}")

    toplam_acik = sum(x["acik_ton"] for x in veri["yem"])
    toplam_ihtiyac = sum(x["ihtiyac_ton"] for x in veri["yem"])
    print(f"\nİl geneli kaba yem açığı: {sayi(toplam_acik)} ton "
          f"(ihtiyacın %{toplam_acik / toplam_ihtiyac * 100:.0f}'i)")


if __name__ == "__main__":
    main()
