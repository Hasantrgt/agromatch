"""
AGROMATCH - Doğu ve Güneydoğu Anadolu il profilleri
===================================================
DİKKAT — VERİ DURUMU:
Buradaki nüfus, hayvan varlığı, ekim alanı ve verim değerleri
ÖN TAHMİNDİR (bölgenin bilinen ürün desenine dayanan yaklaşık büyüklükler).
GERÇEK VERİ DEĞİLDİR ve TÜİK ile doğrulanmadan hiçbir yerde
"veri" olarak sunulmamalıdır.

Doğru olan kısım MODELİN YAPISIDIR: hangi ilde hangi ürün deseni var,
ihtiyaç hangi kuralla hesaplanır, denge nasıl yorumlanır.
Ekip TÜİK verisini girdiğinde bu dosyadaki sayılar değişir, kod değişmez.

Ürün deseni kaynakları (doğrulanacak):
  TÜİK Bitkisel Üretim İstatistikleri (il bazında ekim alanı/verim/üretim)
  TÜİK Hayvansal Üretim İstatistikleri (il bazında büyükbaş/küçükbaş)
  TÜİK ADNKS (il nüfusu)
"""

DOGU = "Doğu Anadolu"
GUNEYDOGU = "Güneydoğu Anadolu"

# il: (bölge, nüfus, büyükbaş, küçükbaş)
ILLER = {
    "Ağrı":      (DOGU, 511_000, 380_000, 1_150_000),
    "Ardahan":   (DOGU,  92_000, 245_000,   120_000),
    "Bingöl":    (DOGU, 282_000, 170_000,   420_000),
    "Bitlis":    (DOGU, 353_000, 150_000,   560_000),
    "Elazığ":    (DOGU, 604_000, 210_000,   630_000),
    "Erzincan":  (DOGU, 237_000, 175_000,   430_000),
    "Erzurum":   (DOGU, 749_000, 660_000,   800_000),
    "Hakkari":   (DOGU, 287_000,  55_000,   680_000),
    "Iğdır":     (DOGU, 203_000, 110_000,   380_000),
    "Kars":      (DOGU, 279_000, 480_000,   290_000),
    "Malatya":   (DOGU, 812_000, 145_000,   480_000),
    "Muş":       (DOGU, 407_000, 330_000,   720_000),
    "Tunceli":   (DOGU,  84_000,  45_000,   130_000),
    "Van":       (DOGU, 1_128_000, 260_000, 1_900_000),
    "Adıyaman":  (GUNEYDOGU, 635_000,  95_000, 520_000),
    "Batman":    (GUNEYDOGU, 634_000,  60_000, 420_000),
    "Diyarbakır":(GUNEYDOGU, 1_805_000, 270_000, 1_250_000),
    "Gaziantep": (GUNEYDOGU, 2_164_000, 105_000, 780_000),
    "Kilis":     (GUNEYDOGU, 155_000,  25_000, 190_000),
    "Mardin":    (GUNEYDOGU, 875_000,  85_000, 700_000),
    "Siirt":     (GUNEYDOGU, 331_000,  55_000, 480_000),
    "Şanlıurfa": (GUNEYDOGU, 2_213_000, 320_000, 2_400_000),
    "Şırnak":    (GUNEYDOGU, 557_000,  60_000, 830_000),
}

# Ürün tipleri, ihtiyacın hangi kuralla hesaplanacağını belirler
TIP_GIDA = "gıda"            # nüfus x kişi başı tüketim
TIP_KABA_YEM = "kaba yem"    # hayvan varlığı x yıllık kaba yem ihtiyacı
TIP_KESIF_YEM = "kesif yem"  # hayvan varlığı x yıllık kesif yem ihtiyacı
TIP_SANAYI = "sanayi"        # fabrika kotası / sözleşmeli alım
TIP_PAZAR = "pazar"          # yurt içi pazar payı + ihracat talebi

URUN_TIPI = {
    "Buğday": TIP_GIDA, "Mercimek": TIP_GIDA, "Patates": TIP_GIDA,
    "Arpa": TIP_KESIF_YEM, "Mısır (dane)": TIP_KESIF_YEM,
    "Yem bitkileri": TIP_KABA_YEM,
    "Şeker pancarı": TIP_SANAYI, "Pamuk": TIP_SANAYI, "Tütün": TIP_SANAYI,
    "Antep fıstığı": TIP_PAZAR, "Kayısı": TIP_PAZAR, "Elma": TIP_PAZAR,
    "Üzüm": TIP_PAZAR, "Zeytin": TIP_PAZAR, "Karpuz": TIP_PAZAR,
    "Yer fıstığı": TIP_PAZAR,
}

# Kişi başı yıllık tüketim (kg) - gıda ürünleri
KISI_BASI_KG = {"Buğday": 205, "Mercimek": 8.5, "Patates": 62}

# Hayvan başına yıllık yem ihtiyacı (ton, kuru ot / kesif yem eşdeğeri)
KABA_YEM_BUYUKBAS, KABA_YEM_KUCUKBAS = 2.6, 0.32
KESIF_YEM_BUYUKBAS, KESIF_YEM_KUCUKBAS = 0.75, 0.09


# Çayır-mera alanı (dekar) ve mera kuru ot verimi (ton/dekar).
# Kaba yem arzının büyük kısmı meradan gelir; aşırı otlatma nedeniyle verim düşüktür.
MERA_VERIM = 0.10
# Anız ve nadas otlatmasının kaba yem katkısı (ton/dekar, tahıl ve baklagil alanı)
ANIZ_VERIM = 0.05
MERA = {
    "Ağrı": 4_500_000, "Ardahan": 1_600_000, "Bingöl": 1_700_000, "Bitlis": 1_900_000,
    "Elazığ": 1_500_000, "Erzincan": 1_700_000, "Erzurum": 8_000_000, "Hakkari": 2_600_000,
    "Iğdır": 700_000, "Kars": 4_000_000, "Malatya": 1_200_000, "Muş": 2_600_000,
    "Tunceli": 1_000_000, "Van": 5_500_000,
    "Adıyaman": 700_000, "Batman": 500_000, "Diyarbakır": 1_300_000, "Gaziantep": 500_000,
    "Kilis": 150_000, "Mardin": 900_000, "Siirt": 900_000, "Şanlıurfa": 1_500_000,
    "Şırnak": 1_100_000,
}

# il -> {ürün: (ekim alanı dekar, verim ton/dekar, pazar-sanayi talebi ton)}
# Üçüncü değer yalnızca sanayi ve pazar ürünlerinde kullanılır (kota / talep).
DESEN = {
    "Ağrı":      {"Yem bitkileri": (620_000, 0.62, 0), "Buğday": (480_000, 0.22, 0),
                  "Arpa": (210_000, 0.24, 0), "Patates": (18_000, 2.10, 0)},
    "Ardahan":   {"Yem bitkileri": (430_000, 0.70, 0), "Arpa": (95_000, 0.23, 0),
                  "Buğday": (70_000, 0.20, 0), "Patates": (12_000, 1.90, 0)},
    "Bingöl":    {"Yem bitkileri": (210_000, 0.66, 0), "Buğday": (150_000, 0.21, 0),
                  "Arpa": (85_000, 0.23, 0)},
    "Bitlis":    {"Yem bitkileri": (185_000, 0.60, 0), "Buğday": (230_000, 0.22, 0),
                  "Patates": (22_000, 2.30, 0), "Tütün": (9_000, 0.11, 950)},
    "Elazığ":    {"Buğday": (620_000, 0.26, 0), "Arpa": (240_000, 0.26, 0),
                  "Yem bitkileri": (260_000, 0.72, 0), "Üzüm": (85_000, 0.55, 40_000)},
    "Erzincan":  {"Yem bitkileri": (330_000, 0.78, 0), "Buğday": (270_000, 0.27, 0),
                  "Şeker pancarı": (48_000, 5.10, 230_000), "Üzüm": (18_000, 0.60, 9_000)},
    "Erzurum":   {"Yem bitkileri": (1_150_000, 0.68, 0), "Buğday": (420_000, 0.21, 0),
                  "Arpa": (330_000, 0.24, 0), "Patates": (26_000, 2.00, 0),
                  "Şeker pancarı": (55_000, 4.80, 250_000)},
    "Hakkari":   {"Yem bitkileri": (95_000, 0.55, 0), "Buğday": (55_000, 0.18, 0)},
    "Iğdır":     {"Pamuk": (95_000, 0.42, 42_000), "Buğday": (180_000, 0.30, 0),
                  "Yem bitkileri": (140_000, 0.85, 0), "Kayısı": (28_000, 0.90, 26_000)},
    "Kars":      {"Yem bitkileri": (880_000, 0.72, 0), "Arpa": (160_000, 0.24, 0),
                  "Buğday": (140_000, 0.22, 0), "Patates": (14_000, 1.95, 0)},
    "Malatya":   {"Kayısı": (780_000, 0.34, 240_000), "Buğday": (520_000, 0.25, 0),
                  "Yem bitkileri": (210_000, 0.74, 0), "Elma": (95_000, 1.60, 140_000)},
    "Muş":       {"Şeker pancarı": (95_000, 5.40, 430_000), "Buğday": (720_000, 0.26, 0),
                  "Yem bitkileri": (430_000, 0.71, 0), "Arpa": (290_000, 0.27, 0)},
    "Tunceli":   {"Yem bitkileri": (95_000, 0.64, 0), "Buğday": (60_000, 0.20, 0)},
    "Van":       {"Yem bitkileri": (760_000, 0.61, 0), "Buğday": (620_000, 0.20, 0),
                  "Elma": (52_000, 1.45, 60_000), "Patates": (16_000, 2.05, 0)},
    "Adıyaman":  {"Buğday": (1_150_000, 0.30, 0), "Pamuk": (210_000, 0.45, 95_000),
                  "Mercimek": (380_000, 0.13, 0), "Yer fıstığı": (95_000, 0.42, 42_000)},
    "Batman":    {"Buğday": (980_000, 0.28, 0), "Mercimek": (420_000, 0.12, 0),
                  "Pamuk": (135_000, 0.44, 60_000), "Arpa": (210_000, 0.26, 0)},
    "Diyarbakır":{"Buğday": (2_650_000, 0.31, 0), "Mercimek": (620_000, 0.13, 0),
                  "Arpa": (720_000, 0.27, 0), "Pamuk": (330_000, 0.46, 150_000),
                  "Karpuz": (85_000, 4.20, 320_000)},
    "Gaziantep": {"Antep fıstığı": (1_450_000, 0.09, 105_000), "Zeytin": (310_000, 0.38, 110_000),
                  "Üzüm": (280_000, 0.62, 160_000), "Buğday": (720_000, 0.28, 0)},
    "Kilis":     {"Zeytin": (260_000, 0.40, 95_000), "Üzüm": (95_000, 0.58, 52_000),
                  "Buğday": (320_000, 0.27, 0), "Antep fıstığı": (140_000, 0.08, 10_000)},
    "Mardin":    {"Buğday": (1_850_000, 0.29, 0), "Mercimek": (720_000, 0.13, 0),
                  "Arpa": (480_000, 0.26, 0), "Pamuk": (180_000, 0.45, 80_000)},
    "Siirt":     {"Buğday": (480_000, 0.27, 0), "Antep fıstığı": (240_000, 0.07, 14_000),
                  "Mercimek": (190_000, 0.12, 0), "Pamuk": (55_000, 0.43, 24_000)},
    "Şanlıurfa": {"Buğday": (4_200_000, 0.34, 0), "Pamuk": (2_100_000, 0.48, 850_000),
                  "Mercimek": (1_350_000, 0.14, 0), "Mısır (dane)": (620_000, 1.05, 0),
                  "Antep fıstığı": (380_000, 0.08, 26_000)},
    "Şırnak":    {"Buğday": (620_000, 0.26, 0), "Mercimek": (240_000, 0.12, 0),
                  "Arpa": (280_000, 0.25, 0), "Antep fıstığı": (95_000, 0.07, 6_000)},
}
