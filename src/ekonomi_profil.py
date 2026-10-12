"""
AGROMATCH - Ekonomi katsayıları ve veri künyesi
===============================================
İki şey içerir:
  1. Ürün fiyatları ve dekar başına üretim maliyetleri (çiftçi geliri hesabı için)
  2. VERİ KÜNYESİ: modeldeki her girdinin kaynağı, türü ve belirsizlik payı

Künye, panellerde açıkça gösterilir. Amaç, tahmin olan sayıyı gerçek veri gibi
sunmamaktır: hangi sayının nereden geldiği ve ne kadar oynayabileceği okuyucuya
baştan söylenir.
"""

# --- Ürün fiyatı (TL/ton), üretim maliyeti (TL/dekar), devlet desteği (TL/dekar)
# 2026 yılı yaklaşık değerleridir. Fiyatlar enflasyona ve sezona göre hızla değişir;
# destekleme ödemeleri (mazot-gübre desteği, yem bitkisi ve pamuk primi) hesaba dahildir.
# Panelde oynatılabilir varsayımlardır.
EKONOMI = {
    "Buğday":        ( 13_000,  2_800,   400),
    "Arpa":          ( 11_000,  2_500,   350),
    "Mercimek":      ( 30_000,  2_200,   400),
    "Mısır (dane)":  ( 11_000,  9_000,   500),
    "Pamuk":         ( 25_000, 11_000, 2_500),
    "Şeker pancarı": (  3_400, 12_000,   400),
    "Patates":       ( 15_000, 14_000,   300),
    "Yem bitkileri": (  8_000,  4_000,   900),
    "Antep fıstığı": (300_000,  7_000,   300),
    "Kayısı":        ( 70_000, 10_000,   300),
    "Üzüm":          ( 30_000,  9_000,   300),
    "Zeytin":        ( 45_000,  6_000,   300),
    "Elma":          ( 22_000, 13_000,   300),
    "Karpuz":        (  9_000,  8_000,   200),
    "Yer fıstığı":   ( 55_000, 12_000,   400),
    "Tütün":         (130_000,  9_000,   500),
}

# --- Veri künyesi
# (girdi, modeldeki yeri, tür, kaynak / doğrulanacağı yer, belirsizlik)
KUNYE = [
    ("Ürün deseni (hangi ilde ne yetişiyor)", "bolge_profil.DESEN", "yapısal bilgi",
     "Bölgenin bilinen tarım yapısı; TÜİK il bazlı üretim istatistikleriyle doğrulanacak", "düşük"),
    ("Ekim alanı (dekar)", "bolge_profil.DESEN", "tahmin",
     "TÜİK Bitkisel Üretim İstatistikleri (il bazında)", "±%30"),
    ("Verim (ton/dekar)", "bolge_profil.DESEN", "tahmin",
     "TÜİK Bitkisel Üretim İstatistikleri", "±%20"),
    ("İl nüfusu", "bolge_profil.ILLER", "tahmin",
     "TÜİK ADNKS", "±%5"),
    ("Büyükbaş / küçükbaş sayısı", "bolge_profil.ILLER", "tahmin",
     "TÜİK Hayvansal Üretim İstatistikleri", "±%25"),
    ("Çayır-mera alanı", "bolge_profil.MERA", "tahmin",
     "Tarım ve Orman Bakanlığı mera envanteri", "±%40"),
    ("Mera ot verimi (0,10 ton/da)", "kaynak_profil.MERA_VERIM", "literatür",
     "Mera ıslah çalışmaları; otlatma baskısına göre 0,05–0,20 arası değişir", "±%50"),
    ("Kişi başı tüketim (kg/yıl)", "bolge_profil.KISI_BASI_KG", "literatür",
     "TÜİK Bitkisel Ürün Denge Tabloları", "±%15"),
    ("Hayvan başına yem ihtiyacı", "bolge_profil.KABA_YEM_*", "literatür",
     "Hayvan besleme normları (canlı ağırlık ve süt verimine göre değişir)", "±%20"),
    ("Bitki su ihtiyacı (mm/sezon)", "kaynak_profil.KAYNAK", "literatür",
     "Tarım ve Orman Bakanlığı sulama rehberleri; bölgeye göre değişir", "±%20"),
    ("Yıllık yağış (mm)", "kaynak_profil.YAGIS", "tahmin",
     "MGM uzun yıllar il ortalamaları", "±%15"),
    ("Sulanan alan oranı", "kaynak_profil.KAYNAK", "tahmin",
     "DSİ sulama istatistikleri ve il tarım müdürlükleri", "±%30"),
    ("Pompa enerjisi (kWh/m³)", "kaynak_profil.POMPA_*", "literatür",
     "Kuyu derinliği ve pompa verimine bağlı; DSİ ve saha ölçümü", "±%35"),
    ("Mazot tüketimi (lt/dekar)", "kaynak_profil.KAYNAK", "literatür",
     "Tarımsal mekanizasyon çalışmaları", "±%25"),
    ("Karbon katsayıları", "kaynak_profil.KARBON_*", "literatür",
     "IPCC emisyon faktörleri; elektrik için Türkiye şebeke ortalaması", "±%20"),
    ("Ürün fiyatı (TL/ton)", "ekonomi_profil.EKONOMI", "tahmin",
     "TMO, borsa ve hal fiyatları; sezona göre çok oynak", "±%40"),
    ("Üretim maliyeti (TL/dekar)", "ekonomi_profil.EKONOMI", "tahmin",
     "Ziraat odaları maliyet cetvelleri", "±%35"),
    ("Destekleme ödemesi (TL/dekar)", "ekonomi_profil.EKONOMI", "tahmin",
     "Tarım ve Orman Bakanlığı destekleme tebliğleri", "±%25"),
    ("Türkiye net dış ticaret durumu", "bolge_analiz.TR_DURUM", "yapısal bilgi",
     "TÜİK dış ticaret istatistikleri", "düşük"),
]

# --- Duyarlılık analizinde oynatılacak katsayılar ve makul değişim aralığı
DUYARLILIK = [
    ("Verim", "verim", 0.20, "Verim %20 yanılırsa üretim, gelir ve ton başına kaynak değişir"),
    ("Bitki su ihtiyacı", "su", 0.20, "Su ihtiyacı katsayısı sulama suyunu doğrudan değiştirir"),
    ("Ürün fiyatı", "fiyat", 0.40, "Fiyat en oynak girdidir; net geliri doğrudan belirler"),
    ("Üretim maliyeti", "maliyet", 0.35, "Mazot ve gübre zamları maliyeti hızla değiştirir"),
    ("Hayvan sayısı", "hayvan", 0.25, "Yem ihtiyacı ve dolayısıyla açık buna bağlıdır"),
]
