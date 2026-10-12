"""
AGROMATCH - Bitki hastalıkları kataloğu ve iklim koşulları
==========================================================
Bölgede ekonomik önemi olan hastalıklar, bunların gelişmesi için gereken iklim
koşulları ve görüntü işleme ile tespit edilip edilemeyecekleri.

DİKKAT: Hastalıkların iklim eşikleri fitopatoloji literatüründen alınan
YAKLAŞIK değerlerdir. Kesinleştirmek için Zirai Mücadele Teknik Talimatları,
Tarım ve Orman Bakanlığı tahmin-uyarı sistemleri ve ziraat fakültesi
bitki koruma bölümünün saha gözlemleri kullanılacaktır.

Alanlar:
  sicaklik_opt : hastalığın hızlı geliştiği ortalama sıcaklık aralığı (°C)
  nem_esik     : enfeksiyon için gereken yıllık yağış eşiği (mm) — nem vekili
  kritik_aylar : enfeksiyon ve ilaçlama penceresi
  pv_sinif     : PlantVillage veri setindeki karşılığı (görüntü işleme projesi için)
  goruntuden   : yaprak/meyve görüntüsünden tespit edilebilir mi
"""

# İl yıllık ortalama sıcaklık (°C) — yaklaşık değerler, MGM ile doğrulanacak
SICAKLIK = {
    "Ağrı": 6.5, "Ardahan": 4.2, "Bingöl": 12.0, "Bitlis": 9.5, "Elazığ": 13.0,
    "Erzincan": 11.0, "Erzurum": 5.5, "Hakkari": 10.0, "Iğdır": 12.0, "Kars": 4.8,
    "Malatya": 13.8, "Muş": 9.8, "Tunceli": 12.5, "Van": 9.0,
    "Adıyaman": 17.0, "Batman": 16.3, "Diyarbakır": 15.9, "Gaziantep": 15.0,
    "Kilis": 16.5, "Mardin": 16.5, "Siirt": 16.0, "Şanlıurfa": 18.5, "Şırnak": 16.5,
}

HASTALIKLAR = [
    # --- Buğday
    dict(urun="Buğday", ad="Sarı pas", patojen="Puccinia striiformis", tip="mantar",
         sicaklik_opt=(8, 15), nem_esik=450, kritik_aylar=[3, 4, 5],
         belirti="Yaprak damarları boyunca sıralı sarı püstüller",
         yonetim="Dayanıklı çeşit, erken uyarıya göre fungisit",
         pv_sinif="Wheat___Yellow_Rust (ek veri seti)", goruntuden=True),
    dict(urun="Buğday", ad="Kahverengi pas", patojen="Puccinia triticina", tip="mantar",
         sicaklik_opt=(15, 22), nem_esik=400, kritik_aylar=[4, 5, 6],
         belirti="Dağınık kahverengi püstüller",
         yonetim="Dayanıklı çeşit, fungisit", pv_sinif="Wheat___Brown_Rust (ek veri seti)",
         goruntuden=True),
    dict(urun="Buğday", ad="Septoria yaprak lekesi", patojen="Zymoseptoria tritici",
         tip="mantar", sicaklik_opt=(12, 20), nem_esik=550, kritik_aylar=[3, 4, 5],
         belirti="Açık kahverengi, siyah noktalı uzun lekeler",
         yonetim="Ekim nöbeti, anız yönetimi, fungisit", pv_sinif=None, goruntuden=True),
    dict(urun="Buğday", ad="Sürme", patojen="Tilletia spp.", tip="mantar",
         sicaklik_opt=(5, 15), nem_esik=300, kritik_aylar=[10, 11],
         belirti="Başakta balık kokulu siyah kitle",
         yonetim="Sertifikalı ve ilaçlı tohum", pv_sinif=None, goruntuden=False),

    # --- Arpa
    dict(urun="Arpa", ad="Arpa yaprak lekesi", patojen="Rhynchosporium commune",
         tip="mantar", sicaklik_opt=(10, 18), nem_esik=500, kritik_aylar=[3, 4, 5],
         belirti="Gri-yeşil, kahverengi kenarlı lekeler",
         yonetim="Ekim nöbeti, dayanıklı çeşit", pv_sinif=None, goruntuden=True),
    dict(urun="Arpa", ad="Külleme", patojen="Blumeria graminis", tip="mantar",
         sicaklik_opt=(15, 22), nem_esik=350, kritik_aylar=[4, 5],
         belirti="Yaprak yüzeyinde beyaz unlu tabaka",
         yonetim="Dengeli azot, fungisit", pv_sinif=None, goruntuden=True),

    # --- Mercimek
    dict(urun="Mercimek", ad="Antraknoz", patojen="Ascochyta lentis", tip="mantar",
         sicaklik_opt=(15, 22), nem_esik=450, kritik_aylar=[4, 5],
         belirti="Yaprak ve sapta koyu kenarlı açık lekeler",
         yonetim="Temiz tohum, ekim nöbeti", pv_sinif=None, goruntuden=True),
    dict(urun="Mercimek", ad="Fusarium solgunluğu", patojen="Fusarium oxysporum",
         tip="mantar", sicaklik_opt=(20, 28), nem_esik=250, kritik_aylar=[5, 6],
         belirti="Bitkide ani solma, kök boğazında renk değişimi",
         yonetim="Dayanıklı çeşit, uzun ekim nöbeti", pv_sinif=None, goruntuden=False),

    # --- Mısır
    dict(urun="Mısır (dane)", ad="Yaprak yanıklığı", patojen="Exserohilum turcicum",
         tip="mantar", sicaklik_opt=(18, 27), nem_esik=400, kritik_aylar=[6, 7, 8],
         belirti="Uzun, puro biçimli gri-kahve lekeler",
         yonetim="Dayanıklı çeşit, fungisit",
         pv_sinif="Corn___Northern_Leaf_Blight", goruntuden=True),
    dict(urun="Mısır (dane)", ad="Mısır pası", patojen="Puccinia sorghi", tip="mantar",
         sicaklik_opt=(16, 25), nem_esik=450, kritik_aylar=[6, 7],
         belirti="Yaprakta kırmızı-kahve püstüller",
         yonetim="Dayanıklı çeşit", pv_sinif="Corn___Common_rust", goruntuden=True),

    # --- Pamuk
    dict(urun="Pamuk", ad="Verticillium solgunluğu", patojen="Verticillium dahliae",
         tip="mantar", sicaklik_opt=(20, 27), nem_esik=300, kritik_aylar=[6, 7, 8],
         belirti="Yapraklarda damar arası sararma, erken dökülme",
         yonetim="Ekim nöbeti, dayanıklı çeşit, dengeli sulama",
         pv_sinif=None, goruntuden=True),
    dict(urun="Pamuk", ad="Kök çürüklüğü", patojen="Rhizoctonia solani", tip="mantar",
         sicaklik_opt=(18, 25), nem_esik=350, kritik_aylar=[4, 5],
         belirti="Fide döneminde kök boğazında çökme",
         yonetim="Tohum ilaçlama, iyi drenaj", pv_sinif=None, goruntuden=False),

    # --- Şeker pancarı
    dict(urun="Şeker pancarı", ad="Cercospora yaprak lekesi", patojen="Cercospora beticola",
         tip="mantar", sicaklik_opt=(20, 28), nem_esik=400, kritik_aylar=[6, 7, 8],
         belirti="Gri merkezli, kırmızı-kahve halkalı yuvarlak lekeler",
         yonetim="Ekim nöbeti, zamanında fungisit", pv_sinif=None, goruntuden=True),
    dict(urun="Şeker pancarı", ad="Rizomani", patojen="BNYVV (virüs)", tip="virüs",
         sicaklik_opt=(18, 26), nem_esik=300, kritik_aylar=[5, 6, 7],
         belirti="Sakallı kök, bitkide bodurlaşma ve sararma",
         yonetim="Dayanıklı çeşit, bulaşık tarlada ekim nöbeti",
         pv_sinif=None, goruntuden=False),

    # --- Patates
    dict(urun="Patates", ad="Mildiyö", patojen="Phytophthora infestans", tip="mantar",
         sicaklik_opt=(12, 20), nem_esik=500, kritik_aylar=[6, 7, 8],
         belirti="Yaprak kenarında su yeşili lekeler, alt yüzde beyaz kül",
         yonetim="Tahmin-uyarı sistemine göre koruyucu ilaçlama",
         pv_sinif="Potato___Late_blight", goruntuden=True),
    dict(urun="Patates", ad="Erken yanıklık", patojen="Alternaria solani", tip="mantar",
         sicaklik_opt=(20, 28), nem_esik=300, kritik_aylar=[6, 7],
         belirti="İç içe halkalı koyu kahve lekeler",
         yonetim="Dengeli besleme, fungisit",
         pv_sinif="Potato___Early_blight", goruntuden=True),

    # --- Yem bitkileri
    dict(urun="Yem bitkileri", ad="Yonca yaprak lekesi", patojen="Pseudopeziza medicaginis",
         tip="mantar", sicaklik_opt=(15, 22), nem_esik=450, kritik_aylar=[5, 6, 9],
         belirti="Yaprakta küçük koyu kahverengi lekeler, erken dökülme",
         yonetim="Erken biçim, dayanıklı çeşit", pv_sinif=None, goruntuden=True),

    # --- Antep fıstığı
    dict(urun="Antep fıstığı", ad="Karazenk", patojen="Septoria pistaciarum", tip="mantar",
         sicaklik_opt=(18, 26), nem_esik=450, kritik_aylar=[5, 6, 7],
         belirti="Yaprakta siyah noktacıklar, erken yaprak dökümü",
         yonetim="Hastalıklı yaprakların imhası, fungisit", pv_sinif=None, goruntuden=True),

    # --- Kayısı
    dict(urun="Kayısı", ad="Monilya", patojen="Monilinia laxa", tip="mantar",
         sicaklik_opt=(12, 20), nem_esik=400, kritik_aylar=[3, 4],
         belirti="Çiçek ve sürgünlerde ani kuruma, zamk akıntısı",
         yonetim="Çiçeklenmede koruyucu ilaçlama, kuru dal budama",
         pv_sinif="Peach___Bacterial_spot (benzer tür)", goruntuden=True),

    # --- Elma
    dict(urun="Elma", ad="Kara leke", patojen="Venturia inaequalis", tip="mantar",
         sicaklik_opt=(12, 22), nem_esik=500, kritik_aylar=[4, 5, 6],
         belirti="Yaprak ve meyvede zeytin yeşili-siyah kadifemsi lekeler",
         yonetim="Mills çizelgesine göre ilaçlama, yaprak imhası",
         pv_sinif="Apple___Apple_scab", goruntuden=True),
    dict(urun="Elma", ad="Elma küllemesi", patojen="Podosphaera leucotricha", tip="mantar",
         sicaklik_opt=(18, 24), nem_esik=300, kritik_aylar=[4, 5, 6],
         belirti="Sürgün ve yapraklarda beyaz unlu örtü",
         yonetim="Bulaşık sürgün budama, fungisit", pv_sinif=None, goruntuden=True),

    # --- Üzüm
    dict(urun="Üzüm", ad="Mildiyö", patojen="Plasmopara viticola", tip="mantar",
         sicaklik_opt=(15, 25), nem_esik=450, kritik_aylar=[5, 6, 7],
         belirti="Yaprakta yağ lekesi, alt yüzde beyaz kül",
         yonetim="3-10 kuralına göre ilaçlama",
         pv_sinif="Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", goruntuden=True),
    dict(urun="Üzüm", ad="Küllemesi", patojen="Erysiphe necator", tip="mantar",
         sicaklik_opt=(20, 27), nem_esik=250, kritik_aylar=[5, 6, 7],
         belirti="Tanelerde kül rengi örtü ve çatlama",
         yonetim="Kükürt uygulaması", pv_sinif="Grape___Esca_(Black_Measles)",
         goruntuden=True),

    # --- Zeytin
    dict(urun="Zeytin", ad="Halkalı leke", patojen="Spilocaea oleagina", tip="mantar",
         sicaklik_opt=(14, 22), nem_esik=400, kritik_aylar=[3, 4, 11],
         belirti="Yaprakta sarı halkalı koyu lekeler, yaprak dökümü",
         yonetim="Bakırlı ilaçlama, taç içi havalandırma", pv_sinif=None, goruntuden=True),
]

# Görüntü işleme projesi için öncelikli PlantVillage sınıfları
PV_ONCELIK = [
    "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
    "Corn___Common_rust", "Corn___Northern_Leaf_Blight", "Corn___healthy",
    "Apple___Apple_scab", "Apple___Black_rot", "Apple___healthy",
    "Grape___Esca_(Black_Measles)", "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___healthy",
]
