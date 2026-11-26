"""
AGROMATCH - Muş il profili (ilçe çözünürlüğünde)
================================================
Projenin tek veri omurgası. Analiz dosyaları hesap yapar, veri tutmaz.

ÜÇ TÜR SAYI VAR — KARIŞTIRILMAMALI
-----------------------------------
  ÖLÇÜM    : Resmî kaynakta yayımlanmış sayı. İl geneli. (OLCUM sözlüğü)
  VARSAYIM : Literatürden alınan katsayı; ölçülmedi. (VERIM, KATSAYI)
  DAĞITIM  : İl toplamının ilçelere bölünmesi. Tamamen tahmin. (PAY)

Resmî belgelerde Muş için İLÇE KIRILIMI YOK. İl toplamları gerçek, ilçelere
dağıtım tahmindir. Panel bu ayrımı her sayıda gösterir.

ANA KAYNAK
----------
T.C. Tarım ve Orman Bakanlığı — Muş Tarımsal Yatırım Rehberi 2025
(TÜİK 2024 verilerine dayanır)
https://mus.tarimorman.gov.tr/Belgeler/DUYURULAR/Muş Tarımsal Yatırım Rehberi-2025.pdf

BELGENİN KENDİ İÇİNDEKİ ÇELİŞKİLER (bilerek kayıt altına alındı)
----------------------------------------------------------------
  - Buğday: Tablo 3'te 368.297 ton, Bölüm 2.2'de "115 bin ha'da ~244 bin ton".
    Tablo 3 esas alındı; 115 bin ha ile tutarlı verim 0,32 ton/da çıkıyor.
  - Yem bitkileri: Bölüm 2.1'de 494.853 ton, Bölüm 2.2'de 1.515.000 ton.
    Tablo 3'teki ürün bazlı sayılar esas alındı.
  - Tarım alanı: Tablo 1'de 324.112 ha, Bölüm 2.1'de 357.342 ha "potansiyel".
  - Nadas 22.535 da olarak veriliyor; Doğu Anadolu pratiği için düşük görünüyor.

    python src/mus_profil.py     # veri tutarlılığını denetler ve kaynakları listeler
"""

from typing import Any

# --------------------------------------------------------------- tip takma adları
# Bu takma adlar veri yapılarının şeklini belgelendiriyor. Yorum satırı
# eskiyebilir; tip takma adı eskidiğinde mypy söyler.
Olcum = tuple[float, str, str]                 # (değer, birim, kaynak)
Uretim = tuple[float, str]                     # (ton, kaynak)
UrunKunye = tuple[str, float, float, float, float, float, float, float, float, bool]
Pay = tuple[int, float, float, float, float, float]
Toprak = tuple[float, float, float, float, int, int, int,
               float, float, str, int, int]
Iklim = tuple[float, int, int]                 # (ortalama °C, yağış mm, don ayı)
Konum = tuple[float, float]                    # (enlem, boylam)
Desen = dict[str, tuple[int, float]]           # ürün -> (alan dekar, verim)
KunyeSatiri = tuple[str, str, str, str, str, str]


# ======================================================================
#  1. ÖLÇÜM — resmî kaynakta yayımlanmış il geneli sayılar
# ======================================================================
OLCUM: dict[str, Olcum] = {
    "nufus":            (392301,  "kişi",  "TÜİK 2024"),
    "toplam_tarim_da":  (3241124, "dekar", "TÜİK 2024"),
    "mera_da":          (3716350, "dekar", "TÜİK 2024"),
    "nadas_da":         (22535,   "dekar", "TÜİK 2024"),
    "buyukbas":         (242277,  "baş",   "TÜİK 2024 (sığır 235.125 + manda 7.152)"),
    "kucukbas":         (1158210, "baş",   "TÜİK 2024 (koyun 895.621 + keçi 262.589)"),
}

# İl geneli ÜRETİM (ton) — TÜİK 2024, Bakanlık rehberi Tablo 3
URETIM: dict[str, Uretim] = {
    "Şeker pancarı":  (665032, "TÜİK 2024"),
    "Buğday":         (368297, "TÜİK 2024"),
    "Arpa":            (98938, "TÜİK 2024"),
    "Yonca":          (434922, "TÜİK 2024 — yeşil ot"),
    "Korunga":          (8389, "TÜİK 2024 — yeşil ot"),
    "Silajlık mısır":  (49703, "TÜİK 2024"),
    # Bu üçü 2025 faaliyet raporuyla DÜZELDİ. Eski değerler projenin
    # kendi notlarında zaten "tahmin" ya da "güncel yıl yok" diye
    # işaretliydi; rapor o boşlukları kapattı.
    #   patates       4.087 (TÜİK 2021)  -> 5.826
    #   fiğ          25.000 (TAHMİNDİ)   -> 1.839
    #   kuru fasulye  1.200 (TAHMİNDİ)   ->   396
    # UYARI: fiğ ve kuru fasulyede 2023'ten 2024'e sert düşüş var
    # (fiğ 41.648 -> 1.839 ton, fasulye ~5.617 -> 396). Tek yılın
    # rakamı bu ürünler için kırılgan; eğilim için birkaç yıl gerekir.
    "Patates":          (5826, "Muş İl Tarım 2025 faaliyet raporu — 2024"),
    "Fiğ":              (1839, "Muş İl Tarım 2025 faaliyet raporu — 2024"),
    "Kuru fasulye":      (396, "Muş İl Tarım 2025 faaliyet raporu — 2024"),
}

# ======================================================================
#  2. VARSAYIM — literatür katsayıları, Muş'ta ölçülmedi
# ======================================================================
# Ekim alanı = üretim / verim olarak TÜRETİLİR. Verim değişirse alan değişir.
VERIM: dict[str, float] = {                       # ton / dekar
    "Şeker pancarı":  6.00,     # Muş ovası sulu koşul
    # 368.297 t / 0,32 = 115.093 ha -> belgedeki "115 bin ha" ifadesiyle tutarlı
    "Buğday":         0.32,
    "Arpa":           0.26,
    "Yonca":          3.80,     # yeşil ot, çok biçimli
    "Korunga":        1.50,     # yeşil ot
    "Silajlık mısır": 4.00,     # yeşil
    "Fiğ":            1.60,     # yeşil
    "Patates":        2.80,
    "Kuru fasulye":   0.20,
}

# Yeşil/yaş üründen kuru maddeye çevrim
KURU_MADDE: dict[str, float] = {
    "Yonca": 0.25, "Korunga": 0.25, "Fiğ": 0.25, "Silajlık mısır": 0.32,
}

# ------------------------------------------------- ölçülen verim (2024)
# Muş İl Tarım ve Orman Müdürlüğü 2025 faaliyet raporu. Rapor hem ALAN
# hem ÜRETİM veriyor, dolayısıyla verim ikisinin oranı olarak ÖLÇÜLÜYOR —
# bizim gibi varsayılmıyor. Projenin üretim rakamları dokuz üründen
# altısında raporla birebir aynı, yani aynı kaynaktan besleniyoruz;
# ayrışan tek şey verim.
#
# RAPOR KENDİ İÇİNDE ÇELİŞİYOR — bilerek kayda geçiyor. Sayfa 22'deki
# Tablo 8 korungayı 1.066,2 da, sayfa 47 ise 10.662 da yazıyor. Hangisinin
# doğru olduğu belli: Tablo 8'in değeriyle verim 7,87 ton/da çıkıyor ki
# korunga için imkânsız; sayfa 47'ninkiyle 0,79 — normal. Aynı on kat
# hatası patates (26,5 ton/da), mısır silaj (52,7) ve fiğde de var.
# Raporun kendi "Toplam" satırı yanlış değerlerden hesaplanmış, yani hata
# toplama da taşınmış. Burada SAYFA 47 değerleri kullanılıyor.
#
# durum alanı, verimin neden uygulandığını ya da uygulanmadığını söyler:
#   "temiz"   üretim tutuyor, alan güvenilir, varsayımın dayanağı yok
#             -> ölçüm uygulanır
#   "çelişki" iki resmî belge farklı alan veriyor -> uygulanmaz
#   "üretim"  üretim rakamı bile tutmuyor -> uygulanmaz
VERIM_OLCUM: dict[str, tuple[float, int, int, str]] = {
    # ürün:            (verim, alan_da, üretim_ton, durum)
    "Yonca":           (1.933, 225033, 434922, "temiz"),
    "Korunga":         (0.787,  10662,   8389, "temiz"),
    "Silajlık mısır":  (5.270,   9432,  49703, "temiz"),
    # Buğday ve arpa bir süre "çelişki" olarak bekletildi: projenin
    # verimi bağımsız bir varsayım değil, başka bir resmî belgenin
    # "115 bin ha" ifadesinden geriye hesaplanmıştı. Çelişki şöyle
    # çözüldü: o ifade NE 2023'ü (141.467 ha) NE 2024'ü (135.197 ha)
    # tutuyor, yani hiçbir yılla uyuşmuyor. Faaliyet raporu ise alanı
    # ve üretimi AYNI yıl ve AYNI kayıttan veriyor, üstelik ima ettiği
    # verim (0,272 susuz buğday) agronomik olarak 0,320'den makul.
    # İçsel tutarlılığı olan kaynak tercih edildi.
    "Buğday":          (0.272, 1351970, 368297, "temiz"),
    "Arpa":            (0.209,  472885,  98938, "temiz"),
    # Bu üçü de "üretim tutmuyor" diye bekletiliyordu. Tutmamasının
    # sebebi raporda değil bizdeydi: projenin kendi notları fiğ ve
    # kuru fasulyeyi "TAHMİN", patatesi "TÜİK 2021" diye işaretliyordu.
    # Üretim raporun 2024 değerine çekilince verim de uygulanabilir
    # oldu. Kontrol: üretim ÷ verim, raporun alanını %1 içinde yeniden
    # üretiyor (fiğ 3.065/3.067, patates 2.198/2.198, fasulye
    # 1.951/1.948).
    "Fiğ":             (0.600,    3067,   1839, "temiz"),
    "Patates":         (2.651,    2198,   5826, "temiz"),
    "Kuru fasulye":    (0.203,    1948,    396, "temiz"),
    # Fark ihmal edilebilir (%2); uygulamaya değmez ama kayda değer.
    "Şeker pancarı":   (5.895,  112820, 665032, "temiz"),
}
VERIM_KAYNAK = ("Muş İl Tarım ve Orman Müdürlüğü, 2025 yılı faaliyet "
                "raporu, Tablo 8 ve Bölüm 7.1")
VERIM_OLCUM_KULLAN = True

# Varsayılan hâli saklanıyor ki ölçümün NE DEĞİŞTİRDİĞİ ölçülebilsin.
VERIM_VARSAYIM: dict[str, float] = dict(VERIM)


def verim_uygula() -> None:
    """Ölçülen verimleri VERIM'e bindirir; yalnızca "temiz" olanları."""
    VERIM.update(VERIM_VARSAYIM)
    if not VERIM_OLCUM_KULLAN:
        return
    for urun, (v, _a, _u, durum) in VERIM_OLCUM.items():
        if durum == "temiz" and urun in VERIM:
            VERIM[urun] = v


verim_uygula()


# ad: (tip, su ihtiyacı mm, mazot L/da, N kg/da, P kg/da, K kg/da,
#      fiyat TL/ton, maliyet TL/da, destek TL/da, kışlık mı)
URUN: dict[str, UrunKunye] = {
    "Şeker pancarı":   ("sanayi",  750, 24.0, 18, 10,  8,  2450,  9800, 1050, False),
    "Buğday":          ("gıda",    420, 13.5, 12,  7,  0,  9500,  3100,  520, True),
    "Arpa":            ("kesif",   370, 12.5, 10,  6,  0,  8800,  2700,  480, True),
    "Yonca":           ("kaba",    900, 15.0,  5, 12, 10,  1800,  4600,  620, False),
    "Korunga":         ("kaba",    520,  9.5,  3,  8,  6,  1500,  2400,  560, False),
    "Silajlık mısır":  ("kaba",    680, 20.0, 20, 10,  8,  1350,  6400,  720, False),
    "Fiğ":             ("kaba",    390,  9.0,  3,  7,  5,  1700,  2200,  540, True),
    "Patates":         ("gıda",    560, 26.0, 16, 12, 18,  9200, 14500,  380, False),
    "Kuru fasulye":    ("gıda",    480, 14.0,  4, 10,  6, 32000,  7300,  640, False),
}

# ----------------------------------------------------------- denge ölçeği
# Bir ürünün "yeterli mi" sorusu, her ürün için aynı ölçekte sorulamaz.
# Belirleyici olan TAŞINABİLİRLİK: ürünün değer yoğunluğu ve hacmi.
#
#   Kaba yem   -> hacimli, ucuz, uzağa taşımak ekonomik değil. Denge İL içinde
#                 kurulmak zorunda. Açık varsa gerçek bir açıktır.
#   Sanayi     -> alıcısı tek bir tesis. Denge FABRİKA HAVZASI ölçeğinde. İlin
#                 tüketimi de ülkenin ihtiyacı da belirleyici değil.
#   Kesif yem  -> taşınabilir ama nakliye hissedilir. İL ve çevre il ölçeği.
#   Gıda tahıl -> ucuz taşınır, ulusal piyasası var. İl fazlası SORUN DEĞİLDİR;
#                 ilin ülkeye katkısıdır. Doğru soru ULUSAL ölçekte sorulur ve
#                 bu projenin birinci fazının kapsamı dışındadır.
#
# ürün: (ölçek, taşınabilirlik 1-5, il fazlası sorun mu, açıklama)
DENGE_OLCEGI: dict[str, tuple[str, int, bool, str]] = {
    "Şeker pancarı":  ("fabrika havzası", 2, True,
                       "Alıcısı tek tesis. Tavanı fabrika kapasitesi belirler; "
                       "aşan miktar sökülse bile işlenemez."),
    "Buğday":         ("ulusal", 5, False,
                       "Ucuz taşınır, TMO alım yapar. Muş'un fazlası ülkeye gider; "
                       "il ölçeğinde fazlalık uyarı konusu değildir."),
    "Arpa":           ("il ve çevre il", 4, False,
                       "Taşınabilir ama yem olarak ağırlıklı yerinde tüketilir."),
    "Yonca":          ("ilçe", 1, True,
                       "Hacimli ve ucuz; 100 km ötesinden getirmek ekonomik değil."),
    "Korunga":        ("ilçe", 1, True, "Yonca ile aynı; birbirinin yerine geçer."),
    "Silajlık mısır": ("ilçe", 1, True,
                       "En taşınmaz ürün: %68'i su. Silaj çukurunun yanında yetişir."),
    "Fiğ":            ("ilçe", 2, True, "Kaba yem grubunun parçası."),
    "Patates":        ("ulusal", 4, False,
                       "Ulusal piyasası var; il fazlası sorun değil."),
    "Kuru fasulye":   ("ulusal", 5, False,
                       "Dayanıklı ve değerli; ulusal piyasada satılır."),
}

# Kaba yem ürünleri birbirinin yerine geçer: "yonca yeterli mi" sorusu tek
# başına anlamsızdır, hayvan yoncayı da korungayı da silajı da yer. Bu yüzden
# denge sorusu grup olarak sorulur.
KABA_YEM_GRUBU = ("Yonca", "Korunga", "Silajlık mısır", "Fiğ")

# Hayvan başına yıllık kuru madde ihtiyacı (ton) — NRC/TÜRKVET mertebeleri
YEM_IHTIYAC: dict[str, float] = {"buyukbas": 2.60, "kucukbas": 0.45}
# Kişi başına yıllık gıda tüketimi (ton). ARTIK VARSAYIM DEĞİL:
# TEPGE (Tarım ve Orman Bakanlığı Tarımsal Ekonomi ve Politika Geliştirme
# Enstitüsü) ürün raporlarından, TÜİK denge tablolarına dayanıyor.
#
# Üç varsayımın üçü de YÜKSEKTİ ve üçü de aynı yönde şaşmıştı:
#       buğday         0,250 -> 0,1733   (TEPGE Buğday raporu, 2024/25)
#       patates        0,085 -> 0,058    (TEPGE Patates raporu, 2023/24)
#       kuru fasulye   0,009 -> 0,0031   (TEPGE Kuru Baklagil raporu, 2023/24)
#
# Kuru fasulyedeki üç kat fark muhtemelen bir tanım hatasıydı: kuru
# BAKLAGİL toplamı (fasulye 3,1 + nohut 4,9 + mercimek 5,3 ≈ 13 kg) kuru
# FASULYE sanılmış. Proje yalnızca kuru fasulye üretiyor ve dengesini
# kuru fasulye üzerinden kuruyor.
#
# Talep yüksek varsayıldığı için il kendi ihtiyacını olduğundan daha az
# karşılıyor görünüyordu. Düzeltme üç oranı da yukarı taşıyor.
GIDA_IHTIYAC: dict[str, float] = {
    "Buğday": 0.1733, "Patates": 0.058, "Kuru fasulye": 0.0031}
GIDA_KAYNAK = ("TEPGE ürün raporları (TÜİK denge tabloları): buğday "
               "2024/25 173,3 kg; patates 2023/24 58,0 kg; kuru fasulye "
               "2023/24 3,1 kg")

MERA_VERIM = 0.10      # ton kuru madde / dekar / yıl — zayıf step merası
ANIZ_VERIM = 0.05      # tahıl anızından ton KM / dekar

POMPA_KWH_M3 = 0.33
MAZOT_KG_CO2 = 2.68
ELEKTRIK_KG_CO2 = 0.42
AZOT_KG_CO2 = 5.50

# Muş Şeker Fabrikası — KAPASİTE TEYİT EDİLMEDİ
# Resmî belgede kapasite yok. Aşağıdaki değer varsayımdır ve fabrika
# müdürlüğünden teyit alınana kadar öyle kalacaktır.
FABRIKA: dict[str, Any] = {
    "ad": "Muş Şeker Fabrikası",
    "gunluk_kapasite_ton": 7500,
    "kampanya_gun": 95,
    "min_sekerorani": 16.0,
    "teyit": False,
    "not": "Kapasite varsayımdır; resmî kaynakta bulunamadı. Fabrika "
           "müdürlüğünden teyit alınacak.",
}

# ======================================================================
#  3. DAĞITIM — il toplamının ilçelere bölünmesi (TAHMİN)
# ======================================================================
# Resmî belgede ilçe kırılımı yok. Paylar ova yüzölçümü, rakım ve yerleşim
# yoğunluğu gözetilerek verildi. Belgedeki iki somut dayanak:
#   Bulanık Ovası 52.250 ha, Malazgirt Ovası 45.000 ha
# ilçe: (rakım m, nüfus payı, tarım payı, mera payı, hayvan payı, sulanabilir oran)
PAY: dict[str, Pay] = {
    "Merkez":    (1350, 0.430, 0.255, 0.126, 0.260, 0.42),
    "Bulanık":   (1450, 0.205, 0.270, 0.200, 0.235, 0.34),
    "Malazgirt": (1540, 0.145, 0.235, 0.200, 0.215, 0.26),
    "Varto":     (1620, 0.085, 0.090, 0.262, 0.145, 0.14),
    "Hasköy":    (1400, 0.075, 0.080, 0.106, 0.080, 0.38),
    "Korkut":    (1500, 0.060, 0.070, 0.106, 0.065, 0.30),
}

# Ürünün ilçelere dağılımı, genel tarım payından farklıysa burada ezilir.
# Pancar sulanan ovada yoğunlaşır; Varto'da neredeyse yok.
URUN_PAYI: dict[str, dict[str, float]] = {
    "Şeker pancarı": {"Merkez": 0.40, "Bulanık": 0.30, "Malazgirt": 0.15,
                      "Varto": 0.02, "Hasköy": 0.08, "Korkut": 0.05},
    "Silajlık mısır": {"Merkez": 0.35, "Bulanık": 0.28, "Malazgirt": 0.18,
                       "Varto": 0.05, "Hasköy": 0.09, "Korkut": 0.05},
    "Patates": {"Merkez": 0.30, "Bulanık": 0.20, "Malazgirt": 0.12,
                "Varto": 0.25, "Hasköy": 0.08, "Korkut": 0.05},
}

# İlçe verim düzeltmesi: rakım ve sulama erişimine göre il ortalamasına oran
VERIM_DUZELTME: dict[str, float] = {
    "Merkez": 1.04, "Bulanık": 1.03, "Malazgirt": 0.93,
    "Varto": 0.83, "Hasköy": 1.00, "Korkut": 0.94,
}

KOORDINAT: dict[str, Konum] = {
    "Merkez":    (38.73, 41.49), "Bulanık":   (39.09, 42.27),
    "Malazgirt": (39.14, 42.54), "Varto":     (39.17, 41.45),
    "Hasköy":    (38.69, 41.69), "Korkut":    (38.73, 41.80),
}

# ---------------------------------------------------------- türetilen veri
def il_alani(urun: str) -> float:
    """Ekim alanı ölçülmedi; üretim / verim olarak türetilir."""
    return URETIM[urun][0] / VERIM[urun]


def _desen() -> dict[str, Desen]:
    """ilçe -> {ürün: (alan dekar, verim ton/da)} — tamamen türetilmiş."""
    d: dict[str, Desen] = {}
    for ilce, (rakim, n_pay, t_pay, m_pay, h_pay, sul) in PAY.items():
        d[ilce] = {}
        for urun in URUN:
            pay = URUN_PAYI.get(urun, {}).get(ilce, t_pay)
            verim = VERIM[urun] * VERIM_DUZELTME[ilce]
            # Alanı, ilçe payı × il üretimi ÷ ilçe verimi olarak kur ki
            # il üretim toplamı korunsun
            uretim = URETIM[urun][0] * pay
            d[ilce][urun] = (round(uretim / verim), round(verim, 3))
    return d


DESEN = _desen()

# --------------------------------------------- ilçe hayvan varlığı (ÖLÇÜM)
# Muş İl Tarım ve Orman Müdürlüğü 2025 yılı faaliyet raporu, Bölüm 3.1.1.
# Kurumun KENDİ YAYIMLADIĞI belgeden alındı — ziyarette veri verilmedi,
# ama yayımlanmış rapor kamuya açık. Dört sütunun da (büyükbaş, küçükbaş,
# kovan, işletme) toplamı raporun yazdığı toplamı birebir tutuyor; bu,
# aktarımın doğru olduğunun kontrolüdür.
#
# NEDEN ÖNEMLİ: Bu tablo gelene kadar proje, büyükbaş ile küçükbaşın
# ilçelere AYNI oranda dağıldığını varsayıyordu (tek bir h_pay). Gerçek
# dağılım bunu desteklemiyor:
#
#       ilçe        varsayılan   gerçek büyükbaş   gerçek küçükbaş
#       Merkez          %26,0            %26,3             %50,5
#       Bulanık         %23,5            %31,6             %14,7
#       Malazgirt       %21,5            %22,0              %5,6
#       Varto           %14,5             %7,2             %19,2
#
# Merkez il küçükbaşının yarısını barındırıyor, Malazgirt ise sığırın
# beşte birine sahipken küçükbaşın yalnızca %5,6'sına sahip. Kaba yem
# dengesi doğrudan bu sayılara bağlı olduğu için varsayım, projenin en
# büyük bulgusunu çarpıtıyordu.
HAYVAN_ILCE: dict[str, tuple[int, int, int, int]] = {
    # ilçe:      (büyükbaş, küçükbaş, kovan, işletme)
    "Merkez":    (72384, 697116, 30961, 6628),
    "Bulanık":   (87044, 202122,  2455, 5260),
    "Malazgirt": (60541,  77731,  3280, 3460),
    "Varto":     (19743, 265200, 12696, 2033),
    "Hasköy":    (18766,  48805,  1994, 1758),
    "Korkut":    (16977,  88298,  6545, 2179),
}
HAYVAN_KAYNAK = ("Muş İl Tarım ve Orman Müdürlüğü, 2025 yılı faaliyet "
                 "raporu, Bölüm 3.1.1")

# İl toplamı TÜİK 2024'te kalıyor, yalnızca İLÇE DAĞILIMI ölçümden geliyor.
#
# Bakanlık raporunun il toplamı TÜİK'ten farklı (büyükbaş 275.455'e karşı
# 242.277; küçükbaş 1.379.272'ye karşı 1.158.210) çünkü biri TÜRKVET
# kayıtlarından, diğeri TÜİK anketinden geliyor. Projenin arz tarafı
# (mera, yem üretimi) baştan sona TÜİK 2024 ile kurulu; yalnızca hayvan
# toplamını başka bir kayıttan almak, dengenin iki yakasını farklı
# kaynaklardan beslemek olurdu. Bu yüzden ölçümden alınan şey PAY,
# toplam değil. Toplam farkı ayrıca raporlanıyor.
HAYVAN_OLCUM_KULLAN = True


def _hayvan_payi(tur: int) -> dict[str, float]:
    """Ölçülen ilçe dağılımını paya çevirir. tur: 0 büyükbaş, 1 küçükbaş."""
    toplam = sum(v[tur] for v in HAYVAN_ILCE.values())
    return {i: v[tur] / toplam for i, v in HAYVAN_ILCE.items()}


def _ilce_hayvan(ilce: str, h_pay: float) -> tuple[int, int]:
    """İlçenin büyükbaş ve küçükbaş sayısı.

    Ölçüm kapalıysa ya da ilçe ölçümde yoksa eski varsayıma (h_pay)
    düşer: ölçüm bir İYİLEŞTİRMEDİR, önkoşul değil.
    """
    if not HAYVAN_OLCUM_KULLAN or ilce not in HAYVAN_ILCE:
        return (round(OLCUM["buyukbas"][0] * h_pay),
                round(OLCUM["kucukbas"][0] * h_pay))
    return (round(OLCUM["buyukbas"][0] * _hayvan_payi(0)[ilce]),
            round(OLCUM["kucukbas"][0] * _hayvan_payi(1)[ilce]))


ILCE = {
    ilce: (rakim,
           round(OLCUM["nufus"][0] * n_pay),
           *_ilce_hayvan(ilce, h_pay),
           round(OLCUM["mera_da"][0] * m_pay),
           sul)
    for ilce, (rakim, n_pay, t_pay, m_pay, h_pay, sul) in PAY.items()
}

# -------------------------------------------------------------- ilçe toprak
# (pH, organik madde %, kireç %, EC dS/m, kil %, kum %, silt %,
#  P ppm, K ppm, drenaj, erozyon 1-5, toprak derinliği cm)
# TAMAMI TAHMİN — üniversite laboratuvarı analizleriyle değiştirilecek.
TOPRAK: dict[str, Toprak] = {
    "Merkez":    (7.6, 2.0, 10, 0.6, 46, 20, 34, 4.2, 105, "zayıf", 2,  95),
    "Bulanık":   (7.5, 2.2,  9, 0.5, 42, 24, 34, 4.6, 112, "zayıf", 2, 100),
    "Malazgirt": (7.8, 1.7, 13, 0.6, 36, 30, 34, 3.8,  98, "orta",  4,  80),
    "Varto":     (6.9, 2.8,  4, 0.3, 30, 38, 32, 5.4, 135, "iyi",   5,  65),
    "Hasköy":    (7.5, 2.1,  9, 0.5, 41, 26, 33, 4.5, 108, "orta",  3,  90),
    "Korkut":    (7.7, 1.9, 11, 0.5, 38, 28, 34, 4.1, 102, "orta",  4,  80),
}

ILCE_NOTU: dict[str, str] = {
    "Merkez": "Muş Ovası'nın kalbi. Ağır killi bünye ve yüksek taban suyu; "
              "drenaj açılmadan erken ilkbahar ekimi riskli, kök hastalıkları artıyor.",
    "Bulanık": "Murat vadisi tabanı; belgede ovası 52.250 ha olarak geçiyor. "
               "İlin en verimli tahıl alanı, taban suyu yüksek.",
    "Malazgirt": "Geniş step platosu, belgede ovası 45.000 ha. Kireç yüksek, "
                 "organik madde düşük; fosfor kireçle bağlanıyor.",
    "Varto": "Volkanik, eğimli ve serin. Drenaj iyi ama erozyon riski en yüksek, "
             "toprak sığ. Mera ve kaba yem ilçesi; pancara uygun değil.",
    "Hasköy": "Ova kenarı, orta bünye. Sulama erişimi iyi, drenaj Merkez'den rahat.",
    "Korkut": "Ova–yamaç geçişi. Toprak sığ ve kireçli; kuru tarım ağırlıklı.",
}

# --------------------------------------------------------------- iklim
# (yıllık ortalama sıcaklık °C, yıllık yağış mm, don riskli son ay)
# İl ortalaması MGM mertebesi; ilçeler rakım farkıyla türetildi.
IKLIM: dict[str, Iklim] = {
    "Merkez":    (9.8,  780, 4), "Bulanık":   (9.2,  800, 5),
    "Malazgirt": (8.7,  700, 5), "Varto":     (8.2,  950, 5),
    "Hasköy":    (9.5,  790, 4), "Korkut":    (8.9,  760, 5),
}

# ---------------------------------------------------------------- künye
# (alan, tür, kaynak, yıl, güven, not)
KUNYE: list[KunyeSatiri] = [
    ("İl nüfusu", "ölçüm", "TÜİK — Bakanlık Muş Tarımsal Yatırım Rehberi 2025",
     "2024", "yüksek", "392.301 kişi."),
    ("İlçe nüfusları", "dağıtım", "İl toplamının tahmini dağıtımı", "—",
     "düşük", "Resmî belgede ilçe kırılımı yok. TÜİK ADNKS ilçe tablosu ile değişecek."),
    ("Hayvan varlığı", "ölçüm", "TÜİK — Bakanlık rehberi Tablo 6", "2024",
     "yüksek", "242.277 büyükbaş, 1.158.210 küçükbaş. İLÇE DAĞILIMI ARTIK ÖLÇÜM: "
         "Muş İl Tarım ve Orman Müdürlüğü 2025 faaliyet raporu "
         "Bölüm 3.1.1. İl toplamı TÜİK'te bırakıldı; bakanlık "
         "raporunun toplamı farklı (275.455 / 1.379.272) çünkü "
         "TÜRKVET kaydından geliyor, dengenin arz tarafı ise TÜİK."),
    ("Mera alanı", "ölçüm", "TÜİK — Bakanlık rehberi Tablo 1", "2024",
     "yüksek", "3.716.350 dekar. İlçe dağılımı tahmin."),
    ("Toplam tarım alanı", "ölçüm", "TÜİK — Bakanlık rehberi Tablo 1", "2024",
     "orta", "3.241.124 da. Belgenin 2.1 bölümü 357.342 ha 'potansiyel' diyor; çelişkili."),
    ("Ürün üretimi (ton)", "ölçüm",
     "Muş İl Tarım 2025 faaliyet raporu (TÜİK ile aynı kayıt)", "2024",
     "yüksek", "Dokuz ürünün dokuzu da resmî kayıttan. Fiğ ve kuru fasulye "
               "bir zamanlar TAHMİNDİ; faaliyet raporunda ayrı kalem olarak "
               "yer aldıkları için düzeltildi (fiğ 25.000 -> 1.839 ton, kuru "
               "fasulye 1.200 -> 396). Patates TÜİK 2021'den 2024'e çekildi."),
    ("Verim (ton/dekar)", "ölçüm",
     "Muş İl Tarım 2025 faaliyet raporu — alan ve üretimin oranı", "2024",
     "yüksek", "ARTIK VARSAYIM DEĞİL. Rapor hem alan hem üretim verdiği için "
               "verim ikisinin oranı olarak ölçülüyor. Eski buğday verimi "
               "(0,32) bağımsız bir varsayım da değildi: başka bir belgenin "
               "'115 bin ha' ifadesinden geriye hesaplanmıştı ve o ifade "
               "hiçbir yılı tutmuyor (2023: 141.467 ha, 2024: 135.197 ha). "
               "Ölçülen 0,272. Yonca 3,80 varsayımdan 1,933 ölçüme indi."),
    ("Ekim alanı", "ölçüm",
     "Üretim ÷ verim; ikisi de Muş İl Tarım 2025 raporundan", "2024",
     "yüksek", "Hâlâ türetiliyor ama girdilerinin ikisi de ölçüm olduğu için "
               "sonuç, raporun ÖLÇTÜĞÜ alanı %1 içinde yeniden üretiyor "
               "(yonca 224.998/225.033, buğday 1.354.033/1.351.970). "
               "Bağımsız bir alan ölçümü hâlâ yok; türetim doğrulanmış."),
    ("İlçe ürün dağılımı", "dağıtım", "Ova yüzölçümü ve sulama erişimi tahmini", "—",
     "düşük", "Dayanak: Bulanık Ovası 52.250 ha, Malazgirt Ovası 45.000 ha."),
    ("Toprak parametreleri", "ölçüm",
     "Muş İl Tarım laboratuvar kayıtları 2011-2015", "2011-2015",
     "orta", "KISMEN ÖLÇÜM. pH, organik madde, kireç ve EC için 1.223 örnek "
             "bağlı (beş ilçe; Malazgirt örnek sayısı güven eşiğinin "
             "altında). Kil bünye sınıfından türetiliyor. Kireç ve tuzluluk "
             "bağımsız kaynakla DOĞRULANAMADI — en kritik eksik budur."),
    ("Yağış / sıcaklık", "varsayım", "MGM uzun yıllar mertebesi, rakımla düzeltildi",
     "1991-2020", "orta", "Open-Meteo arşivinden ilçe bazında çekilebilir."),
    ("Fabrika kapasitesi", "varsayım", "Teyit edilmedi", "—",
     "düşük", "Resmî kaynakta bulunamadı. SIRADAKİ EN DEĞERLİ İŞ: Muş Şeker "
              "Fabrikası'na tek bir telefon, kapasite ve kampanya süresini "
              "birlikte kapatıyor ve belirsizlikte 9,19 kazanç sağlıyor — "
              "en büyük saha ölçümünün (mera verimi, 4,00) iki katından "
              "fazlası, 80 saat yerine 1 saatte."),
    ("Fiyat ve maliyet", "varsayım", "2025 sezonu mertebesi", "2025",
     "düşük", "TMO ve ziraat odası maliyet cetveliyle değişecek."),
    ("Kişi başı gıda tüketimi", "ölçüm",
     "TEPGE ürün raporları — TÜİK denge tabloları", "2023/24-2024/25",
     "yüksek", "Buğday 173,3 kg, patates 58,0 kg, kuru fasulye 3,1 kg. "
               "Üçü de varsayımdı ve üçü de yüksekti (250 / 85 / 9). Kuru "
               "fasulyedeki üç kat fark tanım hatasıydı: kuru BAKLAGİL "
               "toplamı kuru FASULYE sanılmış. Ulusal ortalama; Muş'ta "
               "kırsal tüketim daha yüksek olabilir."),
    ("Hastalık eşikleri", "varsayım", "Fitopatoloji literatürü", "—",
     "orta", "Muş'ta saha gözlemi yok. Zirai Mücadele Teknik Talimatları ile kesinleşecek."),
]

KAYNAK_BAGLANTI: list[tuple[str, str]] = [
    ("Muş Tarımsal Yatırım Rehberi 2025 (Tarım ve Orman Bakanlığı)",
     "https://mus.tarimorman.gov.tr/Belgeler/DUYURULAR/"
     "Mu%C5%9F%20Tar%C4%B1msal%20Yat%C4%B1r%C4%B1m%20Rehberi-2025.pdf"),
]


# ------------------------------------------------------------ yardımcılar
def kuru_madde(urun: str) -> float:
    return KURU_MADDE.get(urun, 1.0)


def ilce_listesi() -> list[str]:
    return list(ILCE)


def urunler() -> list[str]:
    return list(URUN)


def il_toplami(urun: str) -> tuple[float, float]:
    alan = sum(d.get(urun, (0, 0))[0] for d in DESEN.values())
    uretim = sum(a * v for a, v in (d.get(urun, (0, 0)) for d in DESEN.values()))
    return alan, uretim


def denetle() -> list[str]:
    hata: list[str] = []
    for ilce in ILCE:
        for sozluk, ad in ((DESEN, "DESEN"), (TOPRAK, "TOPRAK"),
                           (IKLIM, "IKLIM"), (KOORDINAT, "KOORDINAT"),
                           (VERIM_DUZELTME, "VERIM_DUZELTME")):
            if ilce not in sozluk:
                hata.append(f"{ad} içinde {ilce} yok")
    for urun in URUN:
        if urun not in URETIM:
            hata.append(f"{urun} için üretim yok")
        if urun not in VERIM:
            hata.append(f"{urun} için verim yok")
    # Paylar 1'e yakın mı
    for ad, indeks in (("nüfus", 1), ("tarım", 2), ("mera", 3), ("hayvan", 4)):
        t = sum(v[indeks] for v in PAY.values())
        if abs(t - 1.0) > 0.005:
            hata.append(f"{ad} payları toplamı {t:.3f}, 1,000 olmalı")
    for urun, paylar in URUN_PAYI.items():
        t = sum(paylar.values())
        if abs(t - 1.0) > 0.005:
            hata.append(f"{urun} ilçe payları toplamı {t:.3f}, 1,000 olmalı")
    # İl üretim toplamı korunuyor mu
    for urun in URUN:
        _, uretim = il_toplami(urun)
        resmi = URETIM[urun][0]
        if abs(uretim - resmi) / resmi > 0.02:
            hata.append(f"{urun}: dağıtım sonrası {uretim:,.0f} ton, "
                        f"resmî {resmi:,.0f} ton")
    return hata


if __name__ == "__main__":
    hatalar = denetle()
    if hatalar:
        print("TUTARSIZLIK:")
        for h in hatalar:
            print("  -", h)
        print()
    else:
        print("Veri tutarlı.\n")

    def sy(x: float, b: int = 0) -> str:
        return f"{x:,.{b}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    print("ÖLÇÜM — resmî kaynak (TÜİK 2024)")
    for ad, (deger, birim, kaynak) in OLCUM.items():
        print(f"  {ad:<18}{sy(deger):>12} {birim:<7} {kaynak}")

    print("\nTÜRETİLEN EKİM ALANI (üretim ÷ varsayılan verim)")
    print(f"  {'Ürün':<16}{'Üretim (ton)':>14}{'Verim':>8}{'Alan (da)':>12}  Kaynak")
    toplam = 0.0
    for u in URUN:
        a = il_alani(u)
        toplam += a
        print(f"  {u:<16}{sy(URETIM[u][0]):>14}{VERIM[u]:>8.2f}{sy(a):>12}  "
              f"{URETIM[u][1]}")
    print(f"  {'TOPLAM':<16}{'':>14}{'':>8}{sy(toplam):>12}")
    print(f"  Toplam tarım alanının %{toplam / OLCUM['toplam_tarim_da'][0] * 100:.0f}'i "
          f"(kalan: nadas, meyve, sebze, modellenmeyen ürünler)")

    print("\nİLÇE DAĞITIMI (tahmin)")
    print(f"  {'İlçe':<11}{'Rakım':>7}{'Nüfus':>10}{'Büyükbaş':>11}"
          f"{'Küçükbaş':>11}{'Mera (da)':>12}")
    for i, v in ILCE.items():
        print(f"  {i:<11}{v[0]:>7}{sy(v[1]):>10}{sy(v[2]):>11}{sy(v[3]):>11}{sy(v[4]):>12}")
