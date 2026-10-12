"""
AGROMATCH - Ürün bazlı belirsizlik ve ölçüm önceliği
=====================================================
Panel her ürün için bir denge oranı söylüyor. Bu sayıların hepsi ölçülmemiş
varsayımların üstünde duruyor. Bu modül iki soruyu HER ÜRÜN İÇİN AYRI sorar:

  1. Bu oran ne kadar belirsiz?
     Her varsayıma makul bir aralık verilir, aralıktan on binlerce kez örnek
     çekilir, denge yeniden hesaplanır. Çıktı tek sayı değil, dağılımdır.

  2. Bu belirsizlik hangi bilinmeyenden geliyor ve ölçülürse ne kazanırız?
     Birinci mertebe duyarlılık indisi (Sobol S1) ile varyans ayrıştırılır,
     her bilinmeyene bir ölçüm yolu eşlenir, ÖLÇÜM ÖNCELİK SIRASI çıkar.

HER ÜRÜN KENDİ ÖLÇEĞİNDE SORULUR
---------------------------------
"Muş kendi ihtiyacını karşılıyor mu?" sorusu buğday için anlamsızdır: Muş
368 bin ton buğday üretir, kendi nüfusu 98 bin ton tüketir, fazlası ülkeye
gider. Bu ilin işlevidir, sorunu değil.

Aynı soru kaba yem için tam yerindedir: yonca ve silaj hacimli ve ucuzdur,
uzaktan getirmek ekonomik değildir, denge il içinde kurulmak zorundadır.

Pancarda soru büsbütün başkadır: belirleyici olan ne ilin tüketimi ne
ülkenin ihtiyacıdır — fabrikanın işleyebileceği miktardır.

Ölçekler mus_profil.DENGE_OLCEGI'nde tanımlıdır ve ürünün taşınabilirliğinden
türetilir. Kaba yem ürünleri birbirinin yerine geçtiği için tek grup sayılır.

Çıktı: outputs/mus_belirsizlik.json

    python src/mus_belirsizlik.py
"""

import json
from pathlib import Path

import numpy as np

import mus_profil as mp

CIKTI = Path(__file__).resolve().parent.parent / "outputs"
ORNEK = 40000
TOHUM = 20261008

# ======================================================================
#  Belirsiz girdiler
# ======================================================================
# anahtar: (etiket, en düşük, en olası, en yüksek, tür, gerekçe)
GIRDI = {
    # --- hayvan ve mera tarafı
    "mera_verim": (
        "Mera verimi (ton KM/da)", 0.05, 0.10, 0.18, "varsayım",
        "Doğu Anadolu'da bozulmuş mera 0,04–0,08; iyi durumdaki mera 0,15–0,25 "
        "ton kuru madde/dekar verir. Muş'ta ölçüm yok. 3,7 milyon dekarda bu "
        "katsayı yem arzının en büyük kalemini tek başına belirliyor."),
    "mera_otlatilabilir": (
        "Otlatılabilir mera oranı", 0.70, 0.88, 1.00, "varsayım",
        "Kadastral mera alanının tamamı otlatılamaz: kayalık, çok dik, "
        "erişilemeyen kısımlar vardır. Oran bilinmiyor."),
    "aniz_verim": (
        "Anız verimi (ton KM/da)", 0.02, 0.05, 0.09, "varsayım",
        "Hasat sonrası tarlada kalan ve hayvanın yiyebildiği sap. Biçerdöver "
        "ayarına ve sapın toplanıp toplanmadığına göre değişir."),
    "yem_buyukbas": (
        "Büyükbaş yıllık kaba yem ihtiyacı (ton KM)", 2.20, 2.60, 3.10, "varsayım",
        "Canlı ağırlığa, süt verimine ve barınma süresine bağlı. Muş'ta "
        "ağırlıklı olarak melez sığır var; ihtiyaç kültür ırkından düşük."),
    "yem_kucukbas": (
        "Küçükbaş yıllık kaba yem ihtiyacı (ton KM)", 0.35, 0.45, 0.58, "varsayım",
        "Koyun ve keçi arasında fark var; 1,16 milyon başta küçük bir sapma "
        "büyük tonaja dönüşüyor."),
    "kesif_buyukbas": (
        "Büyükbaş yıllık kesif yem ihtiyacı (ton)", 0.55, 0.80, 1.15, "varsayım",
        "Süt veren hayvanda yoğun yem tüketimi çok değişken; besi ve süt "
        "işletmeleri arasında iki kat fark olabilir."),
    "kesif_kucukbas": (
        "Küçükbaş yıllık kesif yem ihtiyacı (ton)", 0.025, 0.06, 0.10, "varsayım",
        "Meraya dayalı küçükbaşta kesif yem az; ağıl döneminde artar."),
    "hayvan_sayisi": (
        "Hayvan sayısı çarpanı", 0.95, 1.00, 1.05, "ölçüm",
        "TÜİK 2024 kaydı var; belirsizlik kayıt dışı hayvan ve yıl içi "
        "dalgalanmadan geliyor. Diğerlerine göre çok dar."),

    # --- üretim tarafı
    "km_yesil_ot": (
        "Yeşil otta kuru madde oranı", 0.21, 0.25, 0.30, "varsayım",
        "TÜİK yonca ve korungayı yeşil ot olarak kaydediyor. Kuru maddeye "
        "çevrim oranı biçim zamanına ve kurutma koşullarına göre değişir."),
    "uretim_yem": (
        "Yem bitkisi üretimi çarpanı", 0.85, 1.00, 1.15, "ölçüm",
        "TÜİK kaydı var ama belgenin kendi içinde çelişkisi var "
        "(Bölüm 2.1: 494.853 ton · Bölüm 2.2: 1.515.000 ton)."),
    "uretim_bugday": (
        "Buğday üretimi (ton)", 244000, 368297, 380000, "ölçüm",
        "KAYNAK KENDİSİYLE ÇELİŞİYOR: Tablo 3'te 368.297 ton, Bölüm 2.2'de "
        "'115 bin ha'da ~244 bin ton'. Ölçülmüş bir sayının bile belirsiz "
        "olabileceğinin örneği."),
    "uretim_tahmini": (
        "Kayıtsız ürün üretimi çarpanı", 0.60, 1.00, 1.50, "varsayım",
        "Fiğ ve kuru fasulye resmî tabloda ayrı kalem değil; üretimleri "
        "tamamen tahmin."),

    # --- tüketim tarafı
    "kisi_basi_bugday": (
        "Kişi başı yıllık buğday (ton)", 0.195, 0.250, 0.300, "varsayım",
        "Un, bulgur, makarna eşdeğeri. Türkiye ortalaması 200–250 kg; kırsalda "
        "ev ekmeği nedeniyle daha yüksek olabilir."),
    "kisi_basi_patates": (
        "Kişi başı yıllık patates (ton)", 0.055, 0.085, 0.120, "varsayım",
        "Türkiye ortalaması mertebesi; bölgesel ölçüm yok."),
    "kisi_basi_fasulye": (
        "Kişi başı yıllık kuru fasulye (ton)", 0.005, 0.009, 0.014, "varsayım",
        "Kuru baklagil tüketimi; bölgesel kayıt yok."),
    "tohumluk_oran": (
        "Tohumluk ve fire payı", 0.04, 0.08, 0.14, "varsayım",
        "Üretimin tohumluk ayrılan ve depoda kaybolan payı. Sertifikalı tohum "
        "kullanım oranına göre değişir."),

    # --- fabrika
    "fabrika_kapasite": (
        "Fabrika günlük kapasitesi (ton)", 5000, 7500, 9500, "varsayım",
        "TEYİT EDİLMEDİ. Resmî kaynakta bulunamadı. Tek bir telefon görüşmesi "
        "ya da resmî yazı bu belirsizliği tamamen kaldırır."),
    "fabrika_gun": (
        "Kampanya süresi (gün)", 75, 95, 115, "varsayım",
        "Pancarın geliş hızına ve hava koşullarına göre değişir. "
        "Fabrika kayıtlarında var."),
    "pancar_uretim": (
        "Pancar üretimi çarpanı", 0.95, 1.00, 1.05, "ölçüm",
        "TÜİK 2024 kaydı; fabrika alım kayıtlarıyla çapraz doğrulanabilir."),
}

# Ölçüm yolu: (yöntem, birim, miktar, zorluk 1-5, kim yapar)
OLCUM_YOLU = {
    "mera_verim": ("Kadran biçimi + Sentinel-2 NDVI kalibrasyonu",
                   "saha noktası", 40, 2, "Öğrenci ekibi + Tarla Bitkileri"),
    "mera_otlatilabilir": ("Uydu görüntüsünden eğim ve arazi örtüsü maskesi",
                           "ilçe", 6, 1, "Öğrenci ekibi (ücretsiz veri)"),
    "aniz_verim": ("Hasat sonrası kadran biçimi", "tarla", 20, 2, "Öğrenci ekibi"),
    "yem_buyukbas": ("Literatür + İl Müdürlüğü ırk dağılımı", "resmî yazı", 1, 1,
                     "Danışman hoca"),
    "yem_kucukbas": ("Sürü kompozisyonu anketi", "işletme", 30, 3,
                     "Öğrenci ekibi + Zootekni"),
    "kesif_buyukbas": ("Yem bayisi satış kaydı + işletme anketi", "işletme", 25, 3,
                       "Öğrenci ekibi"),
    "kesif_kucukbas": ("İşletme anketi", "işletme", 25, 3, "Öğrenci ekibi"),
    "hayvan_sayisi": ("TÜRKVET kaydı", "resmî yazı", 1, 1, "Danışman hoca"),
    "km_yesil_ot": ("Etüv kurutma (laboratuvar)", "örnek", 24, 2,
                    "Üniversite laboratuvarı"),
    "uretim_yem": ("İl Müdürlüğü üretim kaydı", "resmî yazı", 1, 1, "Danışman hoca"),
    "uretim_bugday": ("İl Müdürlüğü ve TMO alım kaydı karşılaştırması",
                      "resmî yazı", 1, 1, "Danışman hoca"),
    "uretim_tahmini": ("İl Müdürlüğü ürün bazlı üretim kaydı", "resmî yazı", 1, 1,
                       "Danışman hoca"),
    "kisi_basi_bugday": ("TÜİK hanehalkı tüketim anketi + bölgesel düzeltme",
                         "masa başı", 1, 2, "Öğrenci ekibi"),
    "kisi_basi_patates": ("TÜİK hanehalkı tüketim anketi", "masa başı", 1, 2,
                          "Öğrenci ekibi"),
    "kisi_basi_fasulye": ("TÜİK hanehalkı tüketim anketi", "masa başı", 1, 2,
                          "Öğrenci ekibi"),
    "tohumluk_oran": ("İl Müdürlüğü sertifikalı tohum dağıtım kaydı",
                      "resmî yazı", 1, 1, "Danışman hoca"),
    "fabrika_kapasite": ("Fabrika müdürlüğünden teyit", "resmî yazı", 1, 1,
                         "Danışman hoca"),
    "fabrika_gun": ("Fabrika kampanya kaydı", "resmî yazı", 1, 1, "Danışman hoca"),
    "pancar_uretim": ("Fabrika alım kaydı", "resmî yazı", 1, 1, "Danışman hoca"),
}


# ======================================================================
#  Denge soruları — her biri kendi ölçeğinde
# ======================================================================
def _nufus():
    return mp.OLCUM["nufus"][0]


def _hayvan(x):
    return (mp.OLCUM["buyukbas"][0] * x["hayvan_sayisi"],
            mp.OLCUM["kucukbas"][0] * x["hayvan_sayisi"])


def denge_pancar(x):
    """Ölçek: fabrika havzası. Tavanı fabrika koyar, tüketim değil."""
    arz = mp.URETIM["Şeker pancarı"][0] * x["pancar_uretim"]
    ihtiyac = x["fabrika_kapasite"] * x["fabrika_gun"]
    return arz, ihtiyac


def denge_bugday(x):
    """Ölçek: ulusal. İl içi tüketim sadece referans; fazla sorun değil."""
    arz = x["uretim_bugday"]
    tohumluk = arz * x["tohumluk_oran"]
    ihtiyac = _nufus() * x["kisi_basi_bugday"] + tohumluk
    return arz, ihtiyac


def denge_arpa(x):
    """Ölçek: il ve çevre il. Arpa ağırlıklı olarak kesif yem."""
    bb, kb = _hayvan(x)
    arz = mp.URETIM["Arpa"][0]
    tohumluk = arz * x["tohumluk_oran"]
    ihtiyac = bb * x["kesif_buyukbas"] + kb * x["kesif_kucukbas"] + tohumluk
    return arz, ihtiyac


def denge_kaba_yem(x):
    """Ölçek: ilçe. Grup olarak sorulur — ürünler birbirinin yerine geçer.

    Arz = mera + anız + yem bitkileri (hepsi kuru madde).
    Mera ve anız da arz tarafındadır; hayvan onları da yer.
    """
    bb, kb = _hayvan(x)
    ihtiyac = bb * x["yem_buyukbas"] + kb * x["yem_kucukbas"]

    mera = mp.OLCUM["mera_da"][0] * x["mera_otlatilabilir"] * x["mera_verim"]
    tahil_alan = sum(mp.il_alani(u) for u in ("Buğday", "Arpa"))
    aniz = tahil_alan * x["aniz_verim"]

    yesil = mp.URETIM["Yonca"][0] + mp.URETIM["Korunga"][0]
    fig = mp.URETIM["Fiğ"][0] * x["uretim_tahmini"]
    silaj = mp.URETIM["Silajlık mısır"][0] * mp.KURU_MADDE["Silajlık mısır"]
    yem_bitkisi = ((yesil + fig) * x["km_yesil_ot"] + silaj) * x["uretim_yem"]

    return mera + aniz + yem_bitkisi, ihtiyac


def denge_patates(x):
    arz = mp.URETIM["Patates"][0]
    ihtiyac = _nufus() * x["kisi_basi_patates"] + arz * x["tohumluk_oran"]
    return arz, ihtiyac


def denge_fasulye(x):
    arz = mp.URETIM["Kuru fasulye"][0] * x["uretim_tahmini"]
    ihtiyac = _nufus() * x["kisi_basi_fasulye"] + arz * x["tohumluk_oran"]
    return arz, ihtiyac


# anahtar: (başlık, ürünler, ölçek, fonksiyon, "fazla sorun mu", yorum)
SORU = {
    "kaba_yem": (
        "Kaba yem", list(mp.KABA_YEM_GRUBU), "ilçe", denge_kaba_yem, True,
        "Hacimli ve ucuz; uzaktan getirmek ekonomik değil. Açık gerçek açıktır. "
        "Mera ve anız arz tarafına dahildir."),
    "pancar": (
        "Şeker pancarı", ["Şeker pancarı"], "fabrika havzası", denge_pancar, True,
        "Alıcısı tek tesis. 'İhtiyaç' burada fabrika kapasitesidir; aşan miktar "
        "sökülse bile işlenemez."),
    "arpa": (
        "Arpa (kesif yem)", ["Arpa"], "il ve çevre il", denge_arpa, False,
        "Taşınabilir ama ağırlıklı olarak yerinde tüketilir."),
    "bugday": (
        "Buğday", ["Buğday"], "ulusal", denge_bugday, False,
        "İl içi tüketim sadece referans. Fazla, ilin ülkeye katkısıdır; "
        "uyarı konusu değildir. Doğru soru ulusal ölçekte sorulur."),
    "patates": (
        "Patates", ["Patates"], "ulusal", denge_patates, False,
        "Ulusal piyasası var; il dengesi bağlayıcı değil."),
    "fasulye": (
        "Kuru fasulye", ["Kuru fasulye"], "ulusal", denge_fasulye, False,
        "Ulusal piyasası var; üretim verisi zaten tahmin."),
}


# ======================================================================
#  Motor
# ======================================================================
def ornekle(n=ORNEK, tohum=TOHUM):
    """Üçgen dağılım: en düşük, en olası ve en yüksek bilindiğinde kullanılan
    standart seçim. Sınırların dışına çıkmaz — mera verimi negatif olamaz."""
    rng = np.random.default_rng(tohum)
    return {ad: rng.triangular(d, m, y, n)
            for ad, (_e, d, m, y, _t, _g) in GIRDI.items()}


def s1_indisi(girdi, cikti, kutu=28):
    """Birinci mertebe duyarlılık: Var(E[Y|X]) / Var(Y).

    Örnekler girdiye göre eşit büyüklükte kutulara ayrılır, her kutunun çıktı
    ortalaması alınır, bu ortalamaların varyansı toplam varyansa bölünür.
    Girdi çıktıyı etkilemiyorsa kutu ortalamaları eşitlenir, indis sıfıra iner.
    """
    if np.allclose(girdi, girdi[0]):
        return 0.0
    y = cikti[np.argsort(girdi)]
    parcalar = np.array_split(y, kutu)
    ort = np.array([p.mean() for p in parcalar])
    ag = np.array([len(p) for p in parcalar], dtype=float)
    ag /= ag.sum()
    genel = (ort * ag).sum()
    toplam = cikti.var()
    if toplam <= 0:
        return 0.0
    return float(max(0.0, min(1.0, (ag * (ort - genel) ** 2).sum() / toplam)))


def kose_degeri(fn, acik_buyusun):
    """Bütün girdiler aynı anda en uç noktalarındayken oran.

    Hangi uç "kötü" olduğu girdinin arz mı talep mi tarafında olduğuna bağlı.
    Bunu analitik olarak bilmek yerine iki ucu da deneyip seçiyoruz: her girdi
    için tek tek hangi ucun oranı düşürdüğüne bakılır.
    """
    orta = {ad: np.array([m]) for ad, (_e, _d, m, _y, _t, _g) in GIRDI.items()}
    secim = {}
    for ad, (_e, dusuk, mod, yuksek, _t, _g) in GIRDI.items():
        denemeler = {}
        for uc, deger in (("dusuk", dusuk), ("yuksek", yuksek)):
            gecici = dict(orta)
            gecici[ad] = np.array([deger])
            arz, iht = fn(gecici)
            denemeler[uc] = float(np.asarray(arz / iht).ravel()[0])
        # Açığın büyümesi = oranın küçülmesi
        kotu = min(denemeler, key=denemeler.get)
        secilen = kotu if acik_buyusun else ("yuksek" if kotu == "dusuk" else "dusuk")
        secim[ad] = np.array([dusuk if secilen == "dusuk" else yuksek])
    arz, iht = fn(secim)
    return float(np.asarray(arz / iht).ravel()[0])


def soru_analizi(anahtar, x):
    baslik, urunler, olcek, fn, fazla_sorun, yorum = SORU[anahtar]
    arz, ihtiyac = fn(x)
    oran = np.asarray(arz / ihtiyac, dtype=float)

    p = {q: float(np.percentile(oran, q)) for q in (5, 25, 50, 75, 95)}
    sapma = float(oran.std())

    duyarlilik = []
    for ad, (etiket, d, m, y, tur, gerekce) in GIRDI.items():
        s1 = s1_indisi(x[ad], oran)
        if s1 < 0.002:
            continue                      # bu soruya girmiyor
        yontem, birim, miktar, zorluk, kim = OLCUM_YOLU[ad]
        duyarlilik.append(dict(
            anahtar=ad, etiket=etiket, tur=tur, gerekce=gerekce,
            aralik=[d, y], en_olasi=m, s1=round(s1, 4),
            varyans_payi=round(s1 * 100, 1),
            kazanc_yp=round((sapma - sapma * float(np.sqrt(max(0.0, 1 - s1)))) * 100, 2),
            yontem=yontem, birim=birim, miktar=miktar, zorluk=zorluk, kim=kim,
            masa_basi=bool(miktar <= 2)))
    duyarlilik.sort(key=lambda r: -r["s1"])

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
                         emek=sum(r["miktar"] * r["zorluk"] for r in masa),
                         sapma_yp=round(sapma * float(np.sqrt(kalan)) * 100, 2),
                         aciklanan=round((1 - kalan) * 100, 1)))
    for r in saha:
        kalan = max(0.0, kalan - r["s1"])
        plan.append(dict(adim=len(plan) + 1, asama="saha / laboratuvar",
                         etiket=r["etiket"], kalemler=None, yontem=r["yontem"],
                         kim=r["kim"], emek=r["miktar"] * r["zorluk"],
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
                      + ("Fazlalık bu ölçekte sorundur." if fazla_sorun
                         else "Bu ölçekte fazlalık sorun değildir."))

    sayisal = {k: dict(arz=round(float(np.percentile(np.asarray(arz, dtype=float)
                                                     * np.ones_like(oran), q))),
                       ihtiyac=round(float(np.percentile(
                           np.asarray(ihtiyac, dtype=float) * np.ones_like(oran), q))))
               for k, q in (("p50", 50),)}

    return dict(
        anahtar=anahtar, baslik=baslik, urunler=urunler, olcek=olcek,
        fazla_sorun=fazla_sorun, yorum=yorum,
        oran=dict(medyan=round(p[50], 3), alt90=round(p[5], 3),
                  ust90=round(p[95], 3), alt50=round(p[25], 3),
                  ust50=round(p[75], 3), sapma=round(sapma, 4),
                  sapma_yp=round(sapma * 100, 1)),
        arz_medyan=sayisal["p50"]["arz"], ihtiyac_medyan=sayisal["p50"]["ihtiyac"],
        karar=karar, karar_notu=karar_notu,
        esigi_kesiyor=bool(kesiyor),
        en_iyimser=round(kose_degeri(fn, False), 3),
        en_kotumser=round(kose_degeri(fn, True), 3),
        baskin=duyarlilik[0] if duyarlilik else None,
        duyarlilik=duyarlilik, plan=plan,
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
    x = ornekle(n)
    sorular = [soru_analizi(a, x) for a in SORU]

    # Bütün sorular arasında en çok işe yarayan ölçümler
    birikim = {}
    for s in sorular:
        for d in s["duyarlilik"]:
            b = birikim.setdefault(d["anahtar"], dict(
                anahtar=d["anahtar"], etiket=d["etiket"], tur=d["tur"],
                yontem=d["yontem"], kim=d["kim"], masa_basi=d["masa_basi"],
                emek=d["miktar"] * d["zorluk"], gerekce=d["gerekce"],
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
