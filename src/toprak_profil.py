"""
AGROMATCH - Toprak profilleri ve ürün toprak istekleri
======================================================
DİKKAT — VERİ DURUMU:
İl toprak değerleri ÖN TAHMİNDİR. Bölgenin bilinen toprak yapısına dayanır
(kireçli ve organik maddesi düşük Güneydoğu toprakları, Harran Ovası'nda sulama
kaynaklı tuzlanma, Iğdır'ın tuzlu-sodyumlu toprakları, Muş Ovası'nın ağır bünyeli
ve drenaj sorunlu alüvyal toprakları, Doğu Anadolu'da yüksek erozyon riski).

Gerçek veri kaynakları (doğrulanacak):
  - İl Tarım ve Orman Müdürlüğü toprak analiz laboratuvarları (çiftçi analiz kayıtları)
  - Toprak, Gübre ve Su Kaynakları Merkez Araştırma Enstitüsü
  - ISRIC SoilGrids (250 m küresel toprak haritası, ücretsiz API — bkz. src/veri_cek/toprak_cek.py)
  - FAO Harmonized World Soil Database

Birimler:
  ph          : 1:2.5 toprak-su süspansiyonu
  om          : organik madde, %
  kirec       : CaCO3, %
  ec          : tuzluluk, dS/m (saturasyon ekstraktı)
  kil/kum/silt: bünye bileşenleri, %
  p2o5, k2o   : alınabilir fosfor ve potasyum, kg/dekar
  derinlik    : etkili toprak derinliği, cm
  erozyon     : 1 (çok az) – 5 (çok şiddetli)
"""

DRENAJ_PUAN = {"iyi": 100, "orta": 70, "zayıf": 40}

# il: pH, OM%, kireç%, EC, kil%, kum%, silt%, P2O5, K2O, drenaj, erozyon, derinlik
TOPRAK = {
    "Ağrı":      (7.8, 1.8,  8, 0.5, 32, 38, 30, 4.5,  95, "orta",  4, 60),
    "Ardahan":   (6.9, 3.2,  3, 0.3, 30, 35, 35, 5.0, 110, "iyi",   3, 70),
    "Bingöl":    (7.4, 2.0,  7, 0.4, 35, 30, 35, 4.0, 100, "orta",  5, 50),
    "Bitlis":    (7.3, 2.2,  6, 0.4, 33, 32, 35, 4.2, 105, "orta",  5, 50),
    "Elazığ":    (7.7, 1.5, 12, 0.6, 38, 30, 32, 3.8,  90, "orta",  4, 60),
    "Erzincan":  (7.9, 1.6, 14, 0.7, 30, 40, 30, 5.5, 115, "iyi",   3, 80),
    "Erzurum":   (7.5, 2.4,  6, 0.5, 34, 33, 33, 4.0, 100, "orta",  4, 60),
    "Hakkari":   (7.6, 1.9, 10, 0.4, 30, 40, 30, 3.5,  95, "zayıf", 5, 35),
    "Iğdır":     (8.1, 1.3, 16, 1.6, 36, 30, 34, 4.5, 120, "zayıf", 2, 90),
    "Kars":      (6.9, 3.0,  4, 0.3, 32, 33, 35, 4.8, 105, "orta",  3, 70),
    "Malatya":   (7.9, 1.4, 15, 0.6, 33, 35, 32, 4.2,  95, "iyi",   4, 70),
    "Muş":       (7.5, 2.1,  9, 0.5, 40, 25, 35, 4.6, 110, "zayıf", 3, 90),
    "Tunceli":   (7.2, 2.3,  8, 0.4, 32, 35, 33, 4.0, 100, "orta",  5, 45),
    "Van":       (7.9, 1.7, 11, 0.9, 33, 34, 33, 4.0, 100, "orta",  4, 60),
    "Adıyaman":  (7.8, 1.2, 18, 0.5, 40, 25, 35, 3.5,  90, "iyi",   3, 80),
    "Batman":    (7.9, 1.0, 20, 0.6, 42, 24, 34, 3.2,  95, "iyi",   3, 75),
    "Diyarbakır":(7.8, 1.1, 17, 0.7, 45, 22, 33, 3.4, 100, "orta",  3, 85),
    "Gaziantep": (7.7, 1.3, 22, 0.4, 38, 28, 34, 3.6,  95, "iyi",   3, 60),
    "Kilis":     (7.8, 1.2, 24, 0.5, 36, 30, 34, 3.4,  92, "iyi",   2, 65),
    "Mardin":    (7.9, 1.0, 21, 0.6, 44, 22, 34, 3.0,  90, "iyi",   3, 70),
    "Siirt":     (7.8, 1.2, 19, 0.5, 40, 26, 34, 3.3,  95, "orta",  4, 60),
    "Şanlıurfa": (7.9, 0.9, 23, 2.4, 48, 20, 32, 3.0, 105, "zayıf", 2, 100),
    "Şırnak":    (7.8, 1.1, 18, 0.6, 40, 26, 34, 3.1,  92, "orta",  4, 55),
}

ALANLAR = ("ph", "om", "kirec", "ec", "kil", "kum", "silt", "p2o5", "k2o",
           "drenaj", "erozyon", "derinlik")

# İl toprak notlarında öne çıkan, bölgede bilinen sorunlar
IL_NOTU = {
    "Şanlıurfa": "Harran Ovası'nda sulama kaynaklı tuzlanma ve drenaj sorunu; "
                 "yıkama suyu ve drenaj şebekesi olmadan tuz yüzeyde birikir.",
    "Iğdır": "Tuzlu-sodyumlu topraklar yaygın; jips uygulaması ve yıkama gerektirir.",
    "Muş": "Muş Ovası ağır bünyeli ve taban suyu yüksek; drenaj yapılmadan "
           "erken ilkbahar ekimi zorlaşır, kök hastalıkları artar.",
    "Hakkari": "Eğimli ve sığ topraklar; tarla tarımı yerine mera ve meyvecilik uygundur.",
    "Kars": "Organik maddesi görece yüksek çayır-mera toprakları; yem bitkisi için elverişli.",
    "Ardahan": "Bölgenin en yüksek organik maddeli toprakları; asitliğe yakın pH.",
    "Diyarbakır": "Karacadağ bazaltik killi topraklar; su tutar ama ıslak işlemede sıkışır.",
    "Gaziantep": "Yüksek kireç; demir klorozuna duyarlı türlerde yaprak sararması görülür.",
}

# ---------------------------------------------------------------------------
# Ürün toprak istekleri
#   ph_opt      : optimum pH aralığı
#   ph_sinir    : bu aralığın dışında ürün ciddi zorlanır
#   ec_esik     : verim düşüşünün başladığı tuzluluk (dS/m, FAO yaklaşık değerleri)
#   kirec_tol   : "yüksek" / "orta" / "düşük" kireç toleransı
#   bunye       : tercih edilen bünye
#   om_hedef    : istenen en az organik madde, %
#   N, P, K     : bir ton ürün için topraktan kaldırılan besin, kg
#   drenaj_hassas : taban suyuna / ıslaklığa duyarlılık, 1 (toleranslı) – 5 (çok hassas)
#   kok_derinlik  : ürünün rahat gelişmesi için istediği etkili toprak derinliği, cm
#   azot_baglar : baklagil ise True (azot ihtiyacının çoğunu havadan karşılar)
# ---------------------------------------------------------------------------
URUN_ISTEK = {
    "Buğday":        dict(ph_opt=(6.0, 7.5), ph_sinir=(5.5, 8.3), ec_esik=6.0,
                          kirec_tol="yüksek", bunye="tınlı", om_hedef=2.0,
                          N=25, P=10, K=18, azot_baglar=False, drenaj_hassas=3, kok_derinlik=90),
    "Arpa":          dict(ph_opt=(6.5, 7.8), ph_sinir=(5.8, 8.5), ec_esik=8.0,
                          kirec_tol="yüksek", bunye="tınlı", om_hedef=1.8,
                          N=22, P=9, K=16, azot_baglar=False, drenaj_hassas=3.5, kok_derinlik=80),
    "Mercimek":      dict(ph_opt=(6.0, 7.5), ph_sinir=(5.5, 8.2), ec_esik=1.5,
                          kirec_tol="orta", bunye="tınlı", om_hedef=1.5,
                          N=10, P=12, K=25, azot_baglar=True, drenaj_hassas=5, kok_derinlik=60),
    "Mısır (dane)":  dict(ph_opt=(5.8, 7.2), ph_sinir=(5.0, 8.0), ec_esik=1.7,
                          kirec_tol="orta", bunye="tınlı", om_hedef=2.5,
                          N=22, P=9, K=20, azot_baglar=False, drenaj_hassas=3.5, kok_derinlik=100),
    "Pamuk":         dict(ph_opt=(6.5, 8.0), ph_sinir=(5.8, 8.5), ec_esik=7.7,
                          kirec_tol="yüksek", bunye="killi", om_hedef=1.5,
                          N=45, P=18, K=45, azot_baglar=False, drenaj_hassas=4, kok_derinlik=120),
    "Şeker pancarı": dict(ph_opt=(6.5, 8.0), ph_sinir=(6.0, 8.3), ec_esik=7.0,
                          kirec_tol="yüksek", bunye="tınlı", om_hedef=2.5,
                          N=4, P=1.5, K=6, azot_baglar=False, drenaj_hassas=3.5, kok_derinlik=120),
    "Patates":       dict(ph_opt=(5.5, 6.8), ph_sinir=(5.0, 7.5), ec_esik=1.7,
                          kirec_tol="düşük", bunye="kumlu", om_hedef=2.5,
                          N=5, P=2, K=8, azot_baglar=False, drenaj_hassas=5, kok_derinlik=60),
    "Yem bitkileri": dict(ph_opt=(6.5, 7.8), ph_sinir=(5.8, 8.3), ec_esik=2.0,
                          kirec_tol="orta", bunye="tınlı", om_hedef=2.0,
                          N=8, P=6, K=25, azot_baglar=True, drenaj_hassas=4, kok_derinlik=150),
    "Antep fıstığı": dict(ph_opt=(7.0, 8.2), ph_sinir=(6.5, 8.6), ec_esik=3.0,
                          kirec_tol="yüksek", bunye="tınlı", om_hedef=1.0,
                          N=35, P=12, K=30, azot_baglar=False, drenaj_hassas=5, kok_derinlik=150),
    "Kayısı":        dict(ph_opt=(6.5, 7.8), ph_sinir=(6.0, 8.2), ec_esik=1.6,
                          kirec_tol="orta", bunye="tınlı", om_hedef=2.0,
                          N=6, P=2, K=8, azot_baglar=False, drenaj_hassas=5, kok_derinlik=150),
    "Üzüm":          dict(ph_opt=(6.0, 7.8), ph_sinir=(5.5, 8.3), ec_esik=1.5,
                          kirec_tol="orta", bunye="tınlı", om_hedef=1.5,
                          N=6, P=2, K=9, azot_baglar=False, drenaj_hassas=4, kok_derinlik=150),
    "Zeytin":        dict(ph_opt=(6.5, 8.2), ph_sinir=(6.0, 8.5), ec_esik=2.7,
                          kirec_tol="yüksek", bunye="tınlı", om_hedef=1.0,
                          N=10, P=3, K=12, azot_baglar=False, drenaj_hassas=4, kok_derinlik=120),
    "Elma":          dict(ph_opt=(5.8, 7.0), ph_sinir=(5.3, 7.8), ec_esik=1.7,
                          kirec_tol="düşük", bunye="tınlı", om_hedef=2.5,
                          N=3, P=1, K=4, azot_baglar=False, drenaj_hassas=4, kok_derinlik=120),
    "Karpuz":        dict(ph_opt=(6.0, 7.5), ph_sinir=(5.5, 8.0), ec_esik=2.5,
                          kirec_tol="orta", bunye="kumlu", om_hedef=2.0,
                          N=2.5, P=1, K=4, azot_baglar=False, drenaj_hassas=4, kok_derinlik=90),
    "Yer fıstığı":   dict(ph_opt=(5.8, 7.0), ph_sinir=(5.3, 7.8), ec_esik=3.2,
                          kirec_tol="düşük", bunye="kumlu", om_hedef=1.5,
                          N=12, P=8, K=25, azot_baglar=True, drenaj_hassas=4, kok_derinlik=60),
    "Tütün":         dict(ph_opt=(5.5, 6.8), ph_sinir=(5.0, 7.5), ec_esik=0.8,
                          kirec_tol="düşük", bunye="kumlu", om_hedef=1.5,
                          N=35, P=12, K=50, azot_baglar=False, drenaj_hassas=3, kok_derinlik=70),
}

KIREC_ESIK = {"yüksek": 30, "orta": 18, "düşük": 10}   # bu değerin üstü sorun


def bunye_sinifi(kil, kum, silt):
    if kil >= 45:
        return "killi"
    if kil >= 35:
        return "killi-tın"
    if kum >= 50:
        return "kumlu-tın"
    return "tınlı"


def il_toprak(il):
    return dict(zip(ALANLAR, TOPRAK[il]))
