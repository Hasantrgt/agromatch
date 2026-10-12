"""
AGROMATCH - Kaynak kullanım katsayıları
=======================================
Bir ürünü yetiştirmek için harcanan su, elektrik, mazot, gübre ve bunların
karbon karşılığı burada tanımlanır.

DİKKAT: Katsayılar literatürden alınan YAKLAŞIK değerlerdir (bitki su tüketimi,
mekanizasyon yakıt tüketimi, gübre normları). Kesin değerler için Tarım ve Orman
Bakanlığı sulama rehberleri, DSİ verileri ve ziraat fakültesi çalışmaları esas
alınmalıdır. Modelin yapısı doğrudur; sayılar doğrulanacaktır.

Birim notu: 1 mm yağış = 1 m³ su / dekar (1 mm x 1.000 m²). Bu sayede su
hesabı doğrudan mm üzerinden yapılabilir.
"""

# --- Ürün bazlı katsayılar
# urun: (mevsimlik su ihtiyacı mm, mazot lt/dekar, azotlu gübre kg/dekar,
#        sulanan alan oranı, kışlık mı, ihracata giden pay)
KAYNAK = {
    "Buğday":        (450,  9, 12, 0.25, True,  0.08),
    "Arpa":          (400,  8,  9, 0.15, True,  0.02),
    "Mercimek":      (350,  7,  4, 0.05, True,  0.22),
    "Mısır (dane)":  (650, 14, 22, 1.00, False, 0.02),
    "Pamuk":         (800, 22, 20, 1.00, False, 0.08),
    "Şeker pancarı": (700, 26, 18, 0.95, False, 0.01),
    "Patates":       (550, 20, 16, 0.90, False, 0.05),
    "Yem bitkileri": (750, 12, 10, 0.50, False, 0.00),
    "Antep fıstığı": (450, 10,  8, 0.15, False, 0.35),
    "Kayısı":        (600, 12, 12, 0.60, False, 0.45),
    "Üzüm":          (500, 11, 10, 0.25, False, 0.30),
    "Zeytin":        (450,  9,  9, 0.20, False, 0.20),
    "Elma":          (700, 13, 14, 0.75, False, 0.25),
    "Karpuz":        (450, 12, 12, 0.85, False, 0.10),
    "Yer fıstığı":   (600, 14, 12, 0.90, False, 0.05),
    "Tütün":         (400, 10,  8, 0.10, False, 0.60),
}

# --- İl yıllık ortalama yağış (mm) - yaklaşık
YAGIS = {
    "Ağrı": 480, "Ardahan": 560, "Bingöl": 940, "Bitlis": 900, "Elazığ": 400,
    "Erzincan": 370, "Erzurum": 450, "Hakkari": 800, "Iğdır": 260, "Kars": 500,
    "Malatya": 380, "Muş": 780, "Tunceli": 900, "Van": 380,
    "Adıyaman": 720, "Batman": 480, "Diyarbakır": 490, "Gaziantep": 550,
    "Kilis": 450, "Mardin": 650, "Siirt": 700, "Şanlıurfa": 450, "Şırnak": 700,
}

# Yıllık yağışın bitkinin gerçekten kullanabildiği payı
# Kışlık ürünler yağışın büyük kısmından yararlanır; yazlık ürünler yaz kuraklığına denk gelir.
ETKIN_YAGIS_KISLIK = 0.65
ETKIN_YAGIS_YAZLIK = 0.35

# --- Sulama enerjisi: 1 m³ suyu tarlaya ulaştırmanın elektrik maliyeti (kWh/m³)
# Derin kuyu sulaması pahalıdır; GAP ana kanal sistemi cazibeyle çalıştığı için ucuzdur.
POMPA_VARSAYILAN = 0.35
POMPA_CAZIBE = 0.18
CAZIBE_ILLERI = {"Şanlıurfa", "Diyarbakır", "Mardin", "Batman"}

# --- Karbon katsayıları
KARBON_MAZOT = 2.68     # kg CO2e / litre dizel
KARBON_ELEKTRIK = 0.42  # kg CO2e / kWh (Türkiye şebeke ortalaması)
KARBON_GUBRE = 5.50     # kg CO2e / kg azot (üretim + tarla emisyonu)
