"""
AGROMATCH - Ürün bazlı belirsizlik ve ölçüm önceliği
=====================================================
Her denge sorusu için iki şeyi hesaplar:

  1. Bu oran ne kadar belirsiz?
     Her varsayıma makul bir aralık verilir, aralıktan on binlerce kez örnek
     çekilir, denge yeniden hesaplanır. Çıktı tek sayı değil, dağılımdır.

  2. Bu belirsizlik hangi bilinmeyenden geliyor ve ölçülürse ne kazanırız?
     Birinci mertebe duyarlılık indisi (Sobol S1) ile varyans ayrıştırılır,
     her bilinmeyene bir ölçüm yolu eşlenir, ÖLÇÜM ÖNCELİK SIRASI çıkar.

DENGE FORMÜLLERİ BURADA DEĞİL
------------------------------
Bu modül bir zamanlar denge formüllerinin kendi kopyasını tutuyordu. İki
kopya demek, bir formül değiştiğinde birinin unutulması demektir. Formüller
artık yalnızca mus_iz.denge_grafigi() içinde, hesap grafiği olarak tanımlı.
Bu modül oradan beslenir ve üstüne karar katmanını kurar:

    mus_iz (ne hesaplanıyor)  ->  mus_belirsizlik (ne anlama geliyor)

Örnekleme, duyarlılık ve uç köşe hesabı da iz.py'nin işi; burada yok.

HER ÜRÜN KENDİ ÖLÇEĞİNDE SORULUR
---------------------------------
"Muş kendi ihtiyacını karşılıyor mu?" sorusu buğday için anlamsızdır: Muş
368 bin ton buğday üretir, kendi nüfusu 98 bin ton tüketir, fazlası ülkeye
gider. Aynı soru kaba yem için tam yerindedir: hacimli ve ucuzdur, uzaktan
getirmek ekonomik değildir. Pancarda belirleyici olan ne ilin tüketimi ne
ülkenin ihtiyacıdır — fabrikanın işleyebileceği miktardır.

Ölçekler mus_iz.denge_grafigi() içinde her dengenin yanında tanımlıdır.

Çıktı: outputs/mus_belirsizlik.json

    python src/mus_belirsizlik.py
"""

import json
from pathlib import Path

import numpy as np

import mus_iz
import mus_profil as mp
from iz import Calisma, bol, fark

CIKTI = Path(__file__).resolve().parent.parent / "outputs"
ORNEK = 40000
TOHUM = 20261008


def soru_analizi(anahtar, kayit, c):
    """Bir denge sorusunun belirsizlik çözümlemesi.

    Formüller burada değil: kayit, mus_iz.denge_grafigi()'nden gelen hesap
    grafiğinin bir dalıdır. Burada yapılan iş, o daldan çıkan dağılımı karar
    diline çevirmektir.
    """
    arz_d, ihtiyac_d = kayit["arz"], kayit["ihtiyac"]
    oran_d = bol("Arz / ihtiyaç", arz_d, ihtiyac_d, birim="oran")

    oran = oran_d.ornek(c)
    p = {q: float(np.percentile(oran, q)) for q in (5, 25, 50, 75, 95)}
    sapma = float(oran.std())

    # Duyarlılık hesabı iz.py'de; burada sadece karar katmanı eklenir.
    duyarlilik = []
    for d in oran_d.duyarlilik(c):
        if d["s1"] < 0.002:
            continue                      # bu dengeye girmiyor
        y = d["olcum_yolu"] or {}
        kalan_oran = float(np.sqrt(max(0.0, 1 - d["s1"])))
        duyarlilik.append(dict(
            anahtar=d["kimlik"], etiket=d["ad"], tur="varsayım",
            gerekce=d["gerekce"], aralik=[d["aralik"][0], d["aralik"][2]],
            en_olasi=d["aralik"][1], s1=d["s1"], varyans_payi=d["varyans_payi"],
            kazanc_yp=round((sapma - sapma * kalan_oran) * 100, 2),
            yontem=y.get("yontem", "—"), birim=y.get("birim", "—"),
            miktar=y.get("miktar", 1), zorluk=y.get("zorluk", 1),
            kim=y.get("kim", "—"), emek=y.get("emek", 1),
            masa_basi=bool(y.get("masa_basi", True))))

    # Ölçüm planı: masa başı işler önce toplu, saha ölçümleri etkiye göre
    masa = [r for r in duyarlilik if r["masa_basi"]]
    saha = [r for r in duyarlilik if not r["masa_basi"]]
    plan, kalan = [], 1.0
    if masa:
        kalan = max(0.0, kalan - sum(r["s1"] for r in masa))
        plan.append(dict(adim=1, asama="masa başı",
                         etiket=f"{len(masa)} kalem resmî yazı / kayıt sorgusu",
                         kalemler=[r["etiket"] for r in masa],
                         yontem="İl Müdürlüğü, TÜRKVET, fabrika yazışması",
                         kim="Danışman hoca",
                         emek=sum(r["emek"] for r in masa),
                         sapma_yp=round(sapma * float(np.sqrt(kalan)) * 100, 2),
                         aciklanan=round((1 - kalan) * 100, 1)))
    for r in saha:
        kalan = max(0.0, kalan - r["s1"])
        plan.append(dict(adim=len(plan) + 1, asama="saha / laboratuvar",
                         etiket=r["etiket"], kalemler=None, yontem=r["yontem"],
                         kim=r["kim"], emek=r["emek"],
                         sapma_yp=round(sapma * float(np.sqrt(kalan)) * 100, 2),
                         aciklanan=round((1 - kalan) * 100, 1)))

    # Karar netliği: %90 aralık 1,0 eşiğini kesiyor mu?
    # Kesmiyorsa yön bellidir (açık ya da fazla), ölçüm kararı değiştirmez.
    kesiyor = p[5] < 1.0 < p[95]
    if kesiyor:
        karar = "belirsiz"
        karar_notu = ("%90 aralık yeterlilik eşiğini (1,0) kesiyor: bugünkü "
                      "veriyle açık mı fazla mı olduğunu söyleyemeyiz.")
    elif p[95] < 1.0:
        karar = "açık"
        karar_notu = ("En iyimser uçta bile arz ihtiyacın altında. Açığın "
                      "varlığı kesin; büyüklüğü belirsiz.")
    else:
        karar = "fazla"
        karar_notu = ("En kötümser uçta bile arz ihtiyacın üstünde. "
                      + ("Fazlalık bu ölçekte sorundur." if kayit["fazla_sorun"]
                         else "Bu ölçekte fazlalık sorun değildir."))

    acik_d = fark("Açık", ihtiyac_d, arz_d, birim=ihtiyac_d.birim, en_az_sifir=True)

    return dict(
        anahtar=anahtar, baslik=kayit["baslik"], urunler=kayit["urunler"],
        olcek=kayit["olcek"], fazla_sorun=kayit["fazla_sorun"],
        yorum=kayit["yorum"],
        oran=dict(medyan=round(p[50], 3), alt90=round(p[5], 3),
                  ust90=round(p[95], 3), alt50=round(p[25], 3),
                  ust50=round(p[75], 3), sapma=round(sapma, 4),
                  sapma_yp=round(sapma * 100, 1)),
        arz_medyan=round(float(np.percentile(arz_d.ornek(c), 50))),
        ihtiyac_medyan=round(float(np.percentile(ihtiyac_d.ornek(c), 50))),
        acik_medyan=round(float(np.percentile(acik_d.ornek(c), 50))),
        karar=karar, karar_notu=karar_notu,
        esigi_kesiyor=bool(kesiyor),
        en_iyimser=round(oran_d.kose(en_buyuk=True), 3),
        en_kotumser=round(oran_d.kose(en_buyuk=False), 3),
        baskin=duyarlilik[0] if duyarlilik else None,
        duyarlilik=duyarlilik, plan=plan,
        dugum_sayisi=oran_d.dugum_sayisi(), derinlik=oran_d.derinlik(),
        toplam_s1=round(sum(r["s1"] for r in duyarlilik), 3),
        histogram=_histogram(oran),
    )


def _histogram(oran, kutu=32):
    alt, ust = float(np.percentile(oran, 0.3)), float(np.percentile(oran, 99.7))
    sayim, kenar = np.histogram(np.clip(oran, alt, ust), bins=kutu, range=(alt, ust))
    return dict(sayim=sayim.tolist(), kenar=[round(float(k), 4) for k in kenar])


def karar_tablosu(sorular, toprak):
    """Dengeyi uygunlukla çaprazlar ve her ürün için EYLEM üretir.

    "Açık var, ürün de uyuyor, o halde ekelim" yetmez: ARAZİ SINIRLIDIR.
    Dokuz ürünün hepsi birden artamaz. Bu yüzden eylem, dengenin yanında
    iki şeye daha bakar:

      - ÖLÇEK: açık hangi ölçekte? Ulusal piyasası olan bir üründe il açığı
        zorunluluk değil, olsa olsa fırsattır. Kaba yemde ise zorunluluktur.
      - GÖRELİ UYGUNLUK: ürün, o ilçede ekilebilecek diğer ürünlere göre
        kaçıncı sırada? Mutlak puan ayırt etmiyor (Muş'ta her şey 78-96
        arasında); sıralama ayırt ediyor.
    """
    if not toprak:
        return []
    uygunluk, sirala = {}, {}
    for u in toprak.get("urun_karsilastirma", []):
        puanlar = [d["puan"] for d in u["ilceler"]]
        uygunluk[u["urun"]] = dict(
            en_iyi_ilce=u["en_iyi"], en_iyi_puan=u["ilceler"][0]["puan"],
            ortalama=round(sum(puanlar) / len(puanlar), 1),
            makas=u["makas"], darbogaz=u["ilceler"][0]["darbogaz"])
    # Her ilçede ürünlerin kendi içindeki sırası
    for r in toprak.get("ilceler", []):
        for i, u in enumerate(r["urunler"], 1):
            sirala.setdefault(u["urun"], {})[r["ilce"]] = i

    cikti = []
    for q in sorular:
        for urun in q["urunler"]:
            uy = uygunluk.get(urun)
            if not uy:
                continue
            oran = q["oran"]["medyan"]
            yerel = q["olcek"] in ("ilçe", "fabrika havzası", "il ve çevre il")
            sira = sirala.get(urun, {}).get(uy["en_iyi_ilce"], 99)
            # İki ayrı sinyal. Sıra: ürün o ilçede rakiplerine göre iyi mi?
            # Makas: ürünün ilçeler arası farkı büyük mü — yani YERİ önemli mi?
            # Makas küçükse ürün her yerde aynı yetişir, planlamanın katkısı yok.
            # Makas büyükse doğru ilçeye koymak tek başına verim kazandırır.
            yeri_onemli = uy["makas"] >= 12
            one_cikan = sira <= 3 or yeri_onemli

            if q["olcek"] == "fabrika havzası":
                if q["karar"] == "belirsiz":
                    eylem, oncelik = "önce ölç", 1
                    gerekce = ("Tavana yakın ama tavanın nerede olduğu bilinmiyor. "
                               "Fabrika kapasitesi teyit edilmeden alan kararı "
                               "verilmemeli: aşarsan sökülen pancar işlenemez.")
                elif oran < 1:
                    eylem, oncelik = "sınırlı artır", 2
                    gerekce = "Fabrika tavanına kadar alan büyütülebilir."
                else:
                    eylem, oncelik = "azalt", 1
                    gerekce = "Üretim fabrika kapasitesinin üstünde."
            elif yerel and oran < 1:
                eylem, oncelik = "artır", 1
                gerekce = (f"Açık yerinde kapanmak zorunda ({q['olcek']} ölçeği). "
                           f"{uy['en_iyi_ilce']} bu ürün için en uygun yer "
                           f"({uy['en_iyi_puan']} puan).")
            elif not yerel and oran < 1 and one_cikan:
                eylem, oncelik = "fırsat", 3
                if yeri_onemli:
                    gerekce = (f"İl kendi tüketiminin %{round(oran * 100)}'ini "
                               f"üretiyor. Zorunluluk değil ama bu ürünün ilçeler "
                               f"arası farkı {uy['makas']} puan — ilin en "
                               f"yüksekleri arasında. {uy['en_iyi_ilce']} belirgin "
                               f"şekilde doğru yer; yer seçimi tek başına kazanç "
                               f"getirir.")
                else:
                    gerekce = (f"İl kendi tüketiminin %{round(oran * 100)}'ini "
                               f"üretiyor. Zorunluluk değil ama "
                               f"{uy['en_iyi_ilce']}'da bu ürün {sira}. sırada.")
            elif not yerel and oran < 1:
                eylem, oncelik = "gerek yok", 4
                gerekce = ("Açık var ama ulusal piyasadan karşılanıyor ve ürün "
                           "ilin öncelikli ürünlerinden değil.")
            elif not yerel:
                eylem, oncelik = "koru", 4
                gerekce = (f"Fazla, bu ölçekte sorun değil: ilin ulusal arza "
                           f"katkısı. Oran {oran:.2f}.")
            else:
                eylem, oncelik = "koru", 4
                gerekce = "Denge yerinde."

            cikti.append(dict(
                urun=urun, soru=q["baslik"], olcek=q["olcek"],
                oran=round(oran, 3), karar=q["karar"],
                belirsiz=q["esigi_kesiyor"],
                uygunluk=uy["ortalama"], en_iyi_ilce=uy["en_iyi_ilce"],
                en_iyi_puan=uy["en_iyi_puan"], ilce_sirasi=sira,
                makas=uy["makas"], yeri_onemli=bool(yeri_onemli),
                darbogaz=uy["darbogaz"], eylem=eylem, oncelik=oncelik,
                gerekce=gerekce))
    cikti.sort(key=lambda r: (r["oncelik"], -r["en_iyi_puan"]))
    return cikti


def kaldirac_analizi(sorular):
    """Yem açığı nasıl kapanır? Arazi bütçesiyle birlikte.

    Açığı sadece yem bitkisi ekerek kapatmak mümkün mü diye bakar. Gereken
    alanı hesaplar ve bunu mevcut buğday alanıyla karşılaştırır. Mera
    ıslahını ayrı bir kaldıraç olarak ele alır: ARAZİ REKABETİ YOKTUR, çünkü
    mera zaten oradadır, sadece daha az ot vermektedir.
    """
    kaba = next((q for q in sorular if q["anahtar"] == "kaba_yem"), None)
    if not kaba:
        return None
    acik = max(0.0, kaba["ihtiyac_medyan"] - kaba["arz_medyan"])

    # Yonca ile kapatmanın arazi maliyeti
    yonca_km = mp.VERIM["Yonca"] * mp.KURU_MADDE["Yonca"]      # ton KM / dekar
    gereken_da = acik / yonca_km if yonca_km else 0
    bugday_alan = mp.il_alani("Buğday")
    mevcut_yem = sum(mp.il_alani(u) for u in mp.KABA_YEM_GRUBU)

    mera_da = mp.OLCUM["mera_da"][0]
    kaldiraclar = [
        dict(ad="Mera ıslahı (+0,03 ton KM/da)",
             tur="arazi rekabeti yok", kazanc=round(mera_da * 0.03),
             arazi=0,
             not_="Otlatma planı, dinlendirme ve gübreleme ile mera verimini "
                  "0,10'dan 0,13'e çıkarmak. Tek bir dekar tarla alanı "
                  "gerektirmez — mera zaten orada."),
        dict(ad="Mera ıslahı (+0,05 ton KM/da)",
             tur="arazi rekabeti yok", kazanc=round(mera_da * 0.05),
             arazi=0,
             not_="Daha iddialı ıslah hedefi. Çok yıllık bir programdır."),
        dict(ad="Nadas alanının yem bitkisine dönmesi",
             tur="arazi var", kazanc=round(mp.OLCUM["nadas_da"][0] * yonca_km),
             arazi=mp.OLCUM["nadas_da"][0],
             not_="Resmî nadas alanı 22.535 dekar; küçük ama bedava."),
        dict(ad="Yem bitkisi alanını iki katına çıkarmak",
             tur="arazi gerek", kazanc=round(mevcut_yem * yonca_km),
             arazi=round(mevcut_yem),
             not_=f"Mevcut {round(mevcut_yem):,} dekara eşit kadar yeni alan. "
                  f"Tahıl alanından gelir.".replace(",", ".")),
    ]
    for k in kaldiraclar:
        k["acik_payi"] = round(k["kazanc"] / acik * 100, 1) if acik else 0
        k["bugday_payi"] = (round(k["arazi"] / bugday_alan * 100, 1)
                            if bugday_alan else 0)

    return dict(
        acik_ton=round(acik),
        sadece_ekimle_dekar=round(gereken_da),
        mevcut_yem_alani=round(mevcut_yem),
        bugday_alani=round(bugday_alan),
        bugday_payi=round(gereken_da / bugday_alan * 100, 1) if bugday_alan else 0,
        kat=round(gereken_da / mevcut_yem, 1) if mevcut_yem else 0,
        kaldiraclar=kaldiraclar,
        sonuc=("Açığı yalnızca yem bitkisi ekerek kapatmak, mevcut yem "
               "alanının katlanmasını ve tahıl alanının önemli bir kısmının "
               "dönüşmesini gerektirir. Tek başına gerçekçi değildir. "
               "Mera ıslahı arazi rekabeti olmayan tek kaldıraçtır ve en "
               "büyük tek katkıyı verir — aynı zamanda en belirsiz "
               "bildiğimiz şeydir. Ölçüm önceliği ile eylem önceliği "
               "burada çakışıyor."),
    )


def analiz(n=ORNEK, toprak=None):
    if toprak is None:
        yol = CIKTI / "mus_toprak.json"
        toprak = (json.loads(yol.read_text(encoding="utf-8"))
                  if yol.exists() else None)
    # Denge formüllerinin tek tanımı burada çağrılıyor.
    grafik = mus_iz.denge_grafigi()
    c = Calisma(n, TOHUM)
    sorular = [soru_analizi(a, kayit, c) for a, kayit in grafik.items()]

    # Bütün sorular arasında en çok işe yarayan ölçümler
    birikim = {}
    for s in sorular:
        for d in s["duyarlilik"]:
            # Gruplama etikete göre: düğüm kimliği her grafik kurulumunda
            # yeniden üretilir, etiket sabittir.
            b = birikim.setdefault(d["etiket"], dict(
                anahtar=d["etiket"], etiket=d["etiket"], tur=d["tur"],
                yontem=d["yontem"], kim=d["kim"], masa_basi=d["masa_basi"],
                emek=d["emek"], gerekce=d["gerekce"],
                etkiledigi=[], toplam_kazanc=0.0, en_yuksek_pay=0.0))
            b["etkiledigi"].append(dict(soru=s["baslik"], pay=d["varyans_payi"],
                                        kazanc=d["kazanc_yp"]))
            b["toplam_kazanc"] += d["kazanc_yp"]
            b["en_yuksek_pay"] = max(b["en_yuksek_pay"], d["varyans_payi"])
    genel = sorted(birikim.values(), key=lambda b: -b["toplam_kazanc"])
    for b in genel:
        b["toplam_kazanc"] = round(b["toplam_kazanc"], 2)
        b["soru_sayisi"] = len(b["etkiledigi"])
        b["verim"] = round(b["toplam_kazanc"] / b["emek"], 4)

    sonuc = dict(
        ornek_sayisi=n, tohum=TOHUM,
        sorular=sorular,
        genel_oncelik=genel,
        karar=karar_tablosu(sorular, toprak),
        kaldirac=kaldirac_analizi(sorular),
        belirsiz_karar=[s["baslik"] for s in sorular if s["karar"] == "belirsiz"],
        net_karar=[s["baslik"] for s in sorular if s["karar"] != "belirsiz"],
        masa_basi_kazanc=round(sum(b["toplam_kazanc"] for b in genel
                                   if b["masa_basi"]), 1),
        saha_kazanc=round(sum(b["toplam_kazanc"] for b in genel
                              if not b["masa_basi"]), 1),
        olcek_notu={u: dict(olcek=o, tasinabilirlik=t, fazla_sorun=f, not_=n2)
                    for u, (o, t, f, n2) in mp.DENGE_OLCEGI.items()},
    )
    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "mus_belirsizlik.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    return sonuc


if __name__ == "__main__":
    s = analiz()
    print(f"Monte Carlo · {s['ornek_sayisi']:,} örnek · {len(s['sorular'])} denge sorusu\n"
          .replace(",", "."))

    print(f"{'DENGE SORUSU':<22}{'ÖLÇEK':<18}{'ARZ/İHTİYAÇ':>24}{'KARAR':>11}")
    for q in s["sorular"]:
        o = q["oran"]
        aralik = f"{o['medyan']:.2f}  ({o['alt90']:.2f} – {o['ust90']:.2f})"
        print(f"{q['baslik']:<22}{q['olcek']:<18}{aralik:>24}{q['karar']:>11}")

    print("\nBASKIN BİLİNMEYEN")
    for q in s["sorular"]:
        b = q["baskin"]
        if b:
            print(f"  {q['baslik']:<22}%{b['varyans_payi']:>5.1f}  {b['etiket']}")

    print(f"\nKARARI BELİRSİZ OLANLAR: "
          f"{', '.join(s['belirsiz_karar']) if s['belirsiz_karar'] else 'yok'}")

    print("\nEYLEM TABLOSU (denge x ölçek x göreli uygunluk)")
    print(f"  {'Ürün':<16}{'Eylem':<16}{'Ölçek':<18}{'Oran':>6}"
          f"{'En uygun':>11}{'Sıra':>5}{'Makas':>7}")
    for f in s["karar"]:
        print(f"  {f['urun']:<16}{f['eylem']:<16}{f['olcek']:<18}"
              f"{f['oran']:>6.2f}{f['en_iyi_ilce']:>11}{f['ilce_sirasi']:>5}"
              f"{f['makas']:>7.1f}{'  <- yer önemli' if f['yeri_onemli'] else ''}")

    k = s["kaldirac"]
    if k:
        print(f"\nYEM AÇIĞI NASIL KAPANIR? (açık {k['acik_ton']:,} ton KM)"
              .replace(",", "."))
        print(f"  Sadece yem bitkisi ekerek: {k['sadece_ekimle_dekar']:,} dekar "
              f"gerekir".replace(",", "."))
        print(f"  Bu, mevcut yem alanının {k['kat']} katı ve buğday alanının "
              f"%{k['bugday_payi']}'i\n")
        print(f"  {'Kaldıraç':<42}{'Kazanç (ton)':>14}{'Açığın':>8}{'Arazi (da)':>12}")
        for x in k["kaldiraclar"]:
            print(f"  {x['ad']:<42}{x['kazanc']:>14,}{x['acik_payi']:>7.1f}%"
                  f"{x['arazi']:>12,}".replace(",", "."))

    print("\nGENEL ÖLÇÜM ÖNCELİĞİ")
    print(f"  Masa başı işlerin toplam kazancı: {s['masa_basi_kazanc']} yüzde puan")
    print(f"  Saha / laboratuvar kazancı:       {s['saha_kazanc']} yüzde puan")
    print(f"\n  {'Ölçüm':<42}{'Tür':<12}{'Soru':>5}{'Kazanç':>9}{'Emek':>6}")
    for b in s["genel_oncelik"][:9]:
        print(f"  {b['etiket'][:40]:<42}"
              f"{'masa başı' if b['masa_basi'] else 'saha':<12}"
              f"{b['soru_sayisi']:>5}{b['toplam_kazanc']:>8.1f}y{b['emek']:>6}")
