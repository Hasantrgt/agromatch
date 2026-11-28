"""
AGROMATCH - Muş tarla zararlıları
==================================
Projenin ÜÇÜNCÜ kısmının gövdesi. İkinci kısım topraktan gelen hastalıkla
ilgilenir; burası böcekle gelen zararla.

Bir ayrımı baştan koymak gerekiyor, çünkü proje boyunca karışıyor:

    hastalık   bir patojen (mantar, bakteri, virüs) bitkiyi hasta eder
    zararlı    bir böcek bitkiyi doğrudan yer, emer ya da deler

Muş'un dokuz ürününde ikisi de var ama ağırlık zararlıdadır: 57 hastalığın
yalnızca 3'ü böcekle taşınıyor, buna karşılık buğdayda süne tek başına
hastalıkların tamamından fazla ürün kaybettirebilir.

ALANLAR
-------
zarar_sekli     emgi | yaprak_yeme | kok_yeme | sap_ici | tohum_delme
hedef_organ     hangi organı vurduğu — ilaçlama zamanını belirler
vektor          taşıdığı hastalıklar; ikinci kısmın kataloğuna bağlanır
kritik_aylar    Muş'ta zararın görüldüğü aylar
dogal_dusman    o zararlıyı baskılayan faydalılar (bkz. faydali.py)
esik            ekonomik zarar eşiği; yoksa None (ölçülmemiş demektir)
depoda_da       ambar katalogunda da görünüyor mu (iki kısım arasındaki köprü)

KAYNAK DİSİPLİNİ
----------------
Buradaki kayıtların tamamı şimdilik "literatür" etiketli. Hastalık
kataloğunda ZMTT (Bakanlık Zirai Mücadele Teknik Talimatları) ile
doğrulanmış kayıtlar vardı; böcekler için o doğrulama HENÜZ YAPILMADI.
Danışman hoca entomolog olduğu için bu listenin gözden geçirilmesi
projenin en hızlı kazanacağı yer.
"""

from __future__ import annotations

from typing import Any

ZARAR_SEKLI = {
    "emgi": "bitki özsuyunu ya da dane içeriğini emer",
    "yaprak_yeme": "yaprak ayasını yer, yapraklanma alanını düşürür",
    "kok_yeme": "kökü ya da kök boğazını yer, bitki devrilir ya da kurur",
    "sap_ici": "sapın içinde galeri açar, başak beslenemez",
    "tohum_delme": "tohumu deler, çimlenme ve pazar değeri düşer",
}

ZARARLILAR: tuple[dict[str, Any], ...] = (
    # ----------------------------------------------------- Buğday / Arpa
    {
        "ad": "Süne", "latince": "Eurygaster integriceps",
        "urunler": ("Buğday", "Arpa"), "onem": 3,
        "zarar_sekli": "emgi", "hedef_organ": "başak ve dane",
        "vektor": (), "kritik_aylar": (4, 5, 6),
        "dogal_dusman": ("Trissolcus yumurta parazitoitleri",),
        "esik": ("kışlamış ergin m²'de ortalama 0,8 ve üzerindeyse yumurta "
                 "parazitlenme sürveyine geçilir; ilaçlama kararı ERGİN "
                 "YOĞUNLUĞU ile PARAZİTLENME ORANI birlikte değerlendirilerek "
                 "verilir (bkz. sune_karari)"),
        "esik_kaynak": "ZMTT",
        "karar_kurali": "sune_karari",
        "depoda_da": False, "kaynak": "ZMTT",
        "belirti": ("Emgi yapılan danede şeffaf leke ve nokta; unda gluten "
                    "çöker, ekmeklik değer düşer. Zarar tartıda değil, "
                    "SÜNELİ DANE ORANINDA ölçülür."),
        "not_": ("Türkiye'de süne mücadelesinin belkemiği yumurta "
                 "parazitoitleridir. Teknik talimat tek bir sayıya değil, "
                 "parazitlenme oranına bağlı bir KARAR TABLOSUNA dayanır: "
                 "parazitlenme yeterliyse ilaçlama yapılmaz. Projenin savı "
                 "olan 'faydalı, kararı değiştirir' ilkesinin resmî karşılığı "
                 "budur."),
    },
    {
        "ad": "Kımıl", "latince": "Aelia spp.",
        "urunler": ("Buğday", "Arpa"), "onem": 2,
        "zarar_sekli": "emgi", "hedef_organ": "başak ve dane",
        "vektor": (), "kritik_aylar": (4, 5, 6),
        "dogal_dusman": ("yumurta parazitoitleri",),
        "esik": None,
        "esik_kaynak": None,
        "depoda_da": False, "kaynak": "literatür",
        "belirti": "Süneye benzer emgi; genellikle süneyle birlikte bulunur.",
        "not_": "Süne ile birlikte sayılır; ayrı eşik verisi Muş için yok.",
    },
    {
        "ad": "Ekin kambur böceği", "latince": "Zabrus tenebrioides",
        "urunler": ("Buğday", "Arpa"), "onem": 2,
        "zarar_sekli": "yaprak_yeme", "hedef_organ": "fide yaprağı",
        "vektor": (), "kritik_aylar": (10, 11, 3, 4),
        "dogal_dusman": (),
        "esik": ("sonbahardan nisan ortasına: m²'de 1 ve üzeri canlı larva "
                 "ILE 5 ve üzeri zararlı görmüş bitki → tohum ilaçlama "
                 "programı. Erken ilkbaharda m²'de 3 ve üzeri canlı larva "
                 "YA DA 15 ve üzeri zararlı görmüş bitki → yüzey ilaçlaması"),
        "esik_kaynak": "ZMTT",
        "depoda_da": False, "kaynak": "ZMTT",
        "belirti": ("Larva geceleri fideyi yer, yaprak lif lif ayrılır ve "
                    "deliğe çekilir. Tarlada ocak ocak boşluk görülür."),
        "not_": ("Sayım 1/4 m²'lik çerçeveyle, toprak 15 cm derinliğe "
                 "kazılarak yapılır. Ekim nöbeti talimatta ilk sırada: "
                 "buğdayın buğdayı izlediği tarlalarda bulaşma artıyor. "
                 "Derin sürüm larva ve pupayı kırar; hasadı geciktirmemek "
                 "tarlaya dökülen daneyi ergine yem olmaktan çıkarır."),
    },
    {
        "ad": "Ekin sap arısı", "latince": "Cephus pygmaeus",
        "urunler": ("Buğday",), "onem": 2,
        "zarar_sekli": "sap_ici", "hedef_organ": "sap",
        "vektor": (), "kritik_aylar": (5, 6),
        "dogal_dusman": ("parazitoit arılar",),
        "esik": None,
        "esik_kaynak": None,
        "depoda_da": False, "kaynak": "literatür",
        "belirti": ("Larva sapın içinde aşağı iner, hasada yakın sapı "
                    "keser; başak devrilir ve hasatta toplanamaz."),
        "not_": ("Larva sapın içinde olduğu için temas etkili ilaç "
                 "ulaşmaz — anız yönetimi ana araçtır."),
    },
    {
        "ad": "Hububat yaprak bitleri",
        "latince": "Rhopalosiphum padi, Sitobion avenae",
        "urunler": ("Buğday", "Arpa"), "onem": 2,
        "zarar_sekli": "emgi", "hedef_organ": "yaprak ve başak",
        "vektor": ("Arpa sarı cücelik virüsü (BYDV)",),
        "kritik_aylar": (4, 5, 6),
        "dogal_dusman": ("gelin böceği", "altın gözlü böcek", "Aphidius spp."),
        "esik": None,
        "esik_kaynak": None,
        "depoda_da": False, "kaynak": "literatür",
        "belirti": "Emgi ile zayıflama; ayrıca virüs taşır.",
        "not_": ("Taşıdığı BYDV artık hastalık kataloğunda (buğday ve arpa "
                 "kayıtları). Sonbahar bulaşması ilkbahardan çok daha "
                 "zararlı; bu yüzden erken ekimden kaçınmak ilaçtan önce "
                 "gelir."),
    },
    # -------------------------------------------------------- Patates
    {
        "ad": "Patates böceği", "latince": "Leptinotarsa decemlineata",
        "urunler": ("Patates",), "onem": 3,
        "zarar_sekli": "yaprak_yeme", "hedef_organ": "yaprak",
        "vektor": (), "kritik_aylar": (5, 6, 7, 8),
        "dogal_dusman": ("avcı tahtakuruları",),
        "esik": ("kimyasal mücadelede EŞİK YOKTUR. Bitki %20 yaprak zararını "
                 "verim kaybı olmadan kaldırır; fenolojik döneme göre bu "
                 "tolerans %40'a çıkabilir. İlaçlama 1. dölde ilk 4. dönem "
                 "larvalar görüldüğünde yapılır"),
        "esik_kaynak": "ZMTT",
        "depoda_da": False, "kaynak": "ZMTT",
        "belirti": ("Ergin ve larva yaprağı tamamen yer; ağır bulaşmada "
                    "bitki sapa iner. Yumru iriliği doğrudan düşer."),
        "not_": ("İnsektisit direnci dünyada en hızlı gelişen türlerden; "
                 "aynı etki grubunun üst üste kullanılmaması kritik. Sürvey "
                 "günlük ortalama sıcaklık 14–15 °C'yi bulunca haftalık "
                 "başlar. İkinci dölde ilaçlama çoğu zaman gereksizdir."),
    },
    {
        "ad": "Yeşil şeftali yaprak biti", "latince": "Myzus persicae",
        "urunler": ("Patates", "Şeker pancarı"), "onem": 3,
        "zarar_sekli": "emgi", "hedef_organ": "yaprak",
        "vektor": ("Patates Y virüsü (PVY)",
                   "Patates yaprak kıvrılma virüsü (PLRV)"),
        "kritik_aylar": (5, 6, 7, 8),
        "dogal_dusman": ("gelin böceği", "altın gözlü böcek", "Aphidius spp."),
        "esik": ("Patateste iki ayrı durum: YEMEKLİK patateste talimat "
                 "\"mücadele eşiğine ulaşılmadığı için kimyasal mücadele "
                 "önerilmemektedir\" diyor. TOHUMLUK patateste virüs "
                 "yayılımını önlemek için gerekebilir; bitki çıkışından "
                 "itibaren tarlaya köşegen girilerek rasgele 50 yaprakta "
                 "sayım yapılır ve yaprak biti VARLIĞI belirlendiğinde "
                 "mücadele yapılır. Şeker pancarı için ayrı eşik "
                 "bulunamadı."),
        "esik_kaynak": "ZMTT",
        "depoda_da": False, "kaynak": "ZMTT",
        "belirti": ("Emgi zararı küçüktür; asıl zarar TAŞIDIĞI VİRÜSTÜR. "
                    "Tohumluk patateste belirleyici zararlıdır."),
        "not_": ("Hastalık kataloğundaki iki virüsün vektörü budur — "
                 "ikinci kısımla üçüncü kısmın birleştiği yer. Eşik de bu "
                 "ayrımı yapıyor: VERİM için ilaçlama önerilmiyor, VİRÜS "
                 "için tohumlukta öneriliyor. Yani kararı belirleyen "
                 "zararlının yoğunluğu değil, ürünün ne için yetiştirildiği."),
    },
    {
        "ad": "Patates güvesi", "latince": "Phthorimaea operculella",
        "urunler": ("Patates",), "onem": 2,
        "zarar_sekli": "sap_ici", "hedef_organ": "yaprak ve yumru",
        "vektor": (), "kritik_aylar": (7, 8, 9, 10),
        "dogal_dusman": ("parazitoit arılar",),
        "esik": ("Yeşil aksamda eşeysel çekici tuzakta 1 ergin "
                 "yakalandığında mücadele kararı verilir. Depoda yumru "
                 "gözle incelenir; depo sıcaklığı 10 °C'nin altındayken "
                 "zararlı gelişemediği için zarar yapamaz."),
        "esik_kaynak": "ZMTT",
        "depoda_da": True, "kaynak": "ZMTT",
        "belirti": ("Larva yaprakta galeri açar, yumruda ise içeri girer. "
                    "Depoda zarar sürer."),
        "not_": ("Tarlada başlayıp DEPODA devam eden tek zararlı — tarla "
                 "ile ambar kısmını birbirine bağlar. Talimatın 10 °C "
                 "sınırı bu bağın sayısal karşılığıdır: depo sıcaklığı "
                 "kararı tarladaki kadar belirliyor."),
    },
    # -------------------------------------------------- Şeker pancarı
    {
        "ad": "Pancar sineği", "latince": "Pegomya betae",
        "urunler": ("Şeker pancarı",), "onem": 3,
        "zarar_sekli": "yaprak_yeme", "hedef_organ": "yaprak",
        "vektor": (), "kritik_aylar": (5, 6, 7),
        "dogal_dusman": ("parazitoit arılar",),
        "esik": "fide döneminde bitki başına 2–3 larva",
        "esik_kaynak": "literatür",
        "depoda_da": False, "kaynak": "literatür",
        "belirti": ("Larva yaprağın iki zarı arasında galeri açar; yaprak "
                    "kabarır ve kurur. Fide döneminde ölümcül."),
        "not_": "Erken dönem zararı şeker veriminde kalıcı kayıp bırakır.",
    },
    {
        "ad": "Pancar piresi", "latince": "Chaetocnema tibialis",
        "urunler": ("Şeker pancarı",), "onem": 2,
        "zarar_sekli": "yaprak_yeme", "hedef_organ": "fide yaprağı",
        "vektor": (), "kritik_aylar": (4, 5),
        "dogal_dusman": (),
        "esik": None,
        "esik_kaynak": None,
        "depoda_da": False, "kaynak": "literatür",
        "belirti": "Yaprakta kalbur gibi küçük delikler; fide dönemi kritik.",
        "not_": "Çıkıştan sonraki ilk iki hafta belirleyicidir.",
    },
    {
        "ad": "Bozkurt", "latince": "Agrotis spp.",
        "urunler": ("Şeker pancarı", "Patates", "Silajlık mısır"), "onem": 2,
        "zarar_sekli": "kok_yeme", "hedef_organ": "kök boğazı",
        "vektor": (), "kritik_aylar": (4, 5, 6),
        "dogal_dusman": ("yer böcekleri (Carabidae)",),
        "esik": ("Ürüne göre ayrı: MISIRDA m²'de ya da 3 m'lik sıra "
                 "üzerinde en az 2 yenik veya kesik bitki görüldüğünde "
                 "yüzey ilaçlaması. PATATESTE dikim anında m²'de 2-3 larva, "
                 "dikimden sonra %1-3 larva veya kesik bitki. Örnekleme "
                 "fide döneminde, serpme ekimde 1/4 m²'lik çerçeveyle, "
                 "sıraya ekimde 3 m sıra üzerinde, en az 10 ayrı noktada."),
        "esik_kaynak": "ZMTT",
        "depoda_da": False, "kaynak": "ZMTT",
        "belirti": ("Larva geceleri fideyi kök boğazından keser; sabah "
                    "devrilmiş bitkiler görülür. Zarar ocak ocaktır."),
        "not_": ("Toprak işleme ve yabancı ot temizliği popülasyonu "
                 "düşürür. Şeker pancarı için talimatta ayrı bir eşik "
                 "bulunamadı; yukarıdaki iki değer mısır ve patates "
                 "içindir."),
    },
    # -------------------------------------------------- Silajlık mısır
    {
        "ad": "Mısır kurdu", "latince": "Ostrinia nubilalis",
        "urunler": ("Silajlık mısır",), "onem": 3,
        "zarar_sekli": "sap_ici", "hedef_organ": "sap ve koçan",
        "vektor": (), "kritik_aylar": (6, 7, 8),
        "dogal_dusman": ("Trichogramma yumurta parazitoitleri",),
        "esik": ("1. üründe %5 bulaşma, 2. üründe 1 yumurta paketi. Bitki "
                 "boyu 40-50 cm'e ulaştığında başlanır; 100 bitkide yumurta "
                 "paketi aranır (yaprağın alt yüzü). Işık tuzağında 10-15 "
                 "ergin/hafta yakalanması ve ilk yumurta paketinin görülmesi "
                 "birlikte değerlendirilir."),
        "esik_kaynak": "ZMTT",
        "depoda_da": False, "kaynak": "ZMTT",
        "belirti": ("Larva sapın içinde galeri açar; sap kırılır, koçan "
                    "beslenemez. Açtığı yara Fusarium'a kapı olur."),
        "not_": ("Sap içine girdikten sonra ilaç ulaşmaz; zamanlama "
                 "yumurta açılımına göre yapılır. Anız parçalama kışlayan "
                 "larvayı düşürür. EŞİĞİN İKİ KOLU VAR ve hangisinin "
                 "geçerli olduğu ekimin birinci mi ikinci ürün mü olduğuna "
                 "bağlıdır: talimat 1. üründe (Karadeniz Bölgesi hariç) "
                 "genellikle ilaçlamaya gerek olmadığını söylüyor. Muş'ta "
                 "silajlık mısırın hangi kola girdiği ekim zamanıyla "
                 "belirlenir; proje bunu kaydetmiyor."),
    },
    # ---------------------------------------------------- Kuru fasulye
    {
        "ad": "Fasulye tohum böceği", "latince": "Acanthoscelides obtectus",
        "urunler": ("Kuru fasulye",), "onem": 3,
        "zarar_sekli": "tohum_delme", "hedef_organ": "tohum",
        "vektor": (), "kritik_aylar": (8, 9, 10, 11, 12),
        "dogal_dusman": (),
        "esik": None,
        "esik_kaynak": None,
        "depoda_da": True, "kaynak": "literatür",
        "belirti": ("Larva tohumun içini yer, çıkış deliği bırakır. "
                    "Çimlenme ve pazar değeri biter."),
        "not_": ("Tarlada bulaşır, DEPODA çoğalır. Muş'ta kuru fasulye "
                 "ambar şartlarında tutulduğu için depo tarafı belirleyici."),
    },
    {
        "ad": "Bakla yaprak biti", "latince": "Aphis fabae",
        "urunler": ("Kuru fasulye", "Şeker pancarı"), "onem": 2,
        "zarar_sekli": "emgi", "hedef_organ": "sürgün ve yaprak",
        "vektor": ("Fasulye sarı mozaik virüsü",),
        "kritik_aylar": (5, 6, 7),
        "dogal_dusman": ("gelin böceği", "altın gözlü böcek", "Aphidius spp."),
        "esik": None,
        "esik_kaynak": None,
        "depoda_da": False, "kaynak": "literatür",
        "belirti": "Sürgün uçlarında koloni; emgi ve virüs taşıma.",
        "not_": "Hastalık kataloğundaki fasulye sarı mozaiğinin vektörü.",
    },
    # ------------------------------------------- Yonca / Korunga / Fiğ
    {
        "ad": "Yonca hortumlu böceği", "latince": "Hypera variabilis",
        "urunler": ("Yonca", "Fiğ"), "onem": 3,
        "zarar_sekli": "yaprak_yeme", "hedef_organ": "yaprak ve sürgün ucu",
        "vektor": (), "kritik_aylar": (3, 4, 5),
        "dogal_dusman": ("Bathyplectes parazitoitleri", "gelin böceği",
                         "Beauveria (entomopatojen mantar)"),
        "esik": ("ilk biçimden 10–20 gün önce m²'de 25 larva veya ergin; "
                 "uygulama genellikle nisan başı ile 15 Mayıs arasına, bitki "
                 "15–30 cm boydayken denk gelir"),
        "esik_kaynak": "ZMTT",
        "depoda_da": False, "kaynak": "ZMTT",
        "belirti": ("Larva sürgün ucundaki yaprakları kemirir; tarla "
                    "uzaktan ağarmış görünür. Birinci biçim en çok etkilenir."),
        "not_": ("Talimat Türkiye'de türü Hypera variabilis olarak veriyor; "
                 "literatürde H. postica ile yakın/eşanlamlı kullanılır. "
                 "Yılda tek döl. Kalıntısız paketin tamamı resmî: biçimi "
                 "10–15 gün erkene almak, biçimden bir hafta önce sulamak "
                 "(larva gelişimi yavaşlar), biçimden sonra 7–10 gün su "
                 "vermemek (toprağa düşen larva güneşte ölür) ve biçilen "
                 "yoncayı tarlada bırakmayıp başka yerde kurutmak."),
    },
    {
        "ad": "Yonca yaprak biti", "latince": "Acyrthosiphon pisum",
        "urunler": ("Yonca", "Fiğ"), "onem": 2,
        "zarar_sekli": "emgi", "hedef_organ": "sürgün ve yaprak",
        "vektor": (), "kritik_aylar": (5, 6, 7),
        "dogal_dusman": ("gelin böceği", "altın gözlü böcek"),
        "esik": None,
        "esik_kaynak": None,
        "depoda_da": False, "kaynak": "literatür",
        "belirti": "Sürgünde koloni, bitki zayıflar, kaba yem kalitesi düşer.",
        "not_": "Doğal düşman baskısı çoğu yıl ilaç gerektirmeden yeterlidir.",
    },
    {
        "ad": "Baklagil tohum hortumluları", "latince": "Apion spp.",
        "urunler": ("Korunga", "Fiğ", "Yonca"), "onem": 2,
        "zarar_sekli": "tohum_delme", "hedef_organ": "tohum",
        "vektor": (), "kritik_aylar": (5, 6, 7),
        "dogal_dusman": ("parazitoit arılar",),
        "esik": None,
        "esik_kaynak": None,
        "depoda_da": False, "kaynak": "literatür",
        "belirti": ("Larva tohum taslağını yer; tohumluk üretiminde verim "
                    "düşer. Kaba yem amaçlı üretimde zarar önemsizdir."),
        "not_": ("Muş'ta korunga ve fiğ ağırlıkla KABA YEM için üretiliyor; "
                 "bu yüzden ekonomik zarar yalnızca tohumluk tarlalarında."),
    },
)


# ------------------------------------------------------- süne karar kuralı
# Zirai Mücadele Teknik Talimatı süne için TEK BİR SAYI vermiyor. Karar,
# kışlamış ergin yoğunluğu ile yumurta parazitlenme oranının birlikte
# okunmasıyla veriliyor. Tablo: (kışlamış ergin/m², o yoğunlukta erken
# ilaçlamadan vazgeçmek için gereken en düşük parazitlenme oranı %).
SUNE_PARAZITLENME: tuple[tuple[float, float], ...] = (
    (0.8, 40.0),
    (1.0, 50.0),
    (1.5, 70.0),
)

# Bu yoğunluğun üstünde, parazitlenme yüksek olsa bile 1.-3. dönem nimfe
# ilaçlama öngörülüyor: ergin çok olduğunda iyi parazitlenme bile geriye
# zarar verecek kadar nimf bırakıyor.
SUNE_ERKEN_ILAC_ERGIN = 2.0
SUNE_ERKEN_ILAC_PARAZIT = 70.0

# Sürveyin başladığı eşik
SUNE_SURVEY_ERGIN = 0.8


def gereken_parazitlenme(ergin_m2: float) -> float | None:
    """Bu ergin yoğunluğunda erken ilaçlamadan vazgeçmek için gereken oran."""
    gerek = None
    for yogunluk, oran in SUNE_PARAZITLENME:
        if ergin_m2 >= yogunluk:
            gerek = oran
    return gerek


def sune_karari(ergin_m2: float, parazitlenme: float | None = None) -> dict[str, Any]:
    """Süne için ilaçlama kararı — talimatın kendi mantığıyla.

    Projenin savı olan "faydalı, kararı değiştirir" ilkesinin resmî
    karşılığı budur: aynı ergin yoğunluğunda parazitlenme oranı yüksekse
    ilaçlama yapılmaz.

    parazitlenme None ise henüz sürvey yapılmamış demektir.
    """
    if ergin_m2 < 0:
        raise ValueError("ergin yoğunluğu negatif olamaz")
    if ergin_m2 < SUNE_SURVEY_ERGIN:
        return {"karar": "izle",
                "gerekce": (f"kışlamış ergin m²'de {ergin_m2:g}; sürvey eşiği "
                            f"{SUNE_SURVEY_ERGIN:g}'in altında"),
                "ilac": False, "gereken_parazitlenme": None}
    if parazitlenme is None:
        return {"karar": "parazitlenme sürveyi yap",
                "gerekce": ("ergin yoğunluğu sürvey eşiğini aştı; karar "
                            "parazitlenme ölçülmeden verilemez (7 gün içinde)"),
                "ilac": None,
                "gereken_parazitlenme": gereken_parazitlenme(ergin_m2)}
    if not 0 <= parazitlenme <= 100:
        raise ValueError("parazitlenme oranı yüzde olarak 0-100 arasında olmalı")

    gerek = gereken_parazitlenme(ergin_m2)
    if ergin_m2 >= SUNE_ERKEN_ILAC_ERGIN and parazitlenme >= SUNE_ERKEN_ILAC_PARAZIT:
        return {"karar": "1.-3. dönem nimfe ilaçlama",
                "gerekce": (f"ergin m²'de {ergin_m2:g} ({SUNE_ERKEN_ILAC_ERGIN:g} "
                            f"ve üzeri); parazitlenme yüksek olsa da geriye "
                            f"zarar verecek kadar nimf kalıyor. Zamanlama: "
                            f"2. dönem nimfler popülasyonun %40'ına ulaşınca"),
                "ilac": True, "gereken_parazitlenme": gerek}
    if gerek is not None and parazitlenme >= gerek:
        return {"karar": "erken ilaçlama yapma, izle",
                "gerekce": (f"parazitlenme %{parazitlenme:g}, bu yoğunluk için "
                            f"gereken %{gerek:g}'in üstünde; 1.-3. döneme "
                            f"ilaçlama yapılmaz, 4.-5. döneme göre izlenir"),
                "ilac": False, "gereken_parazitlenme": gerek}
    return {"karar": "ilaçlama düşünülmeli",
            "gerekce": (f"parazitlenme %{parazitlenme:g}, gereken "
                        f"%{gerek:g}'in altında"),
            "ilac": True, "gereken_parazitlenme": gerek}


def urune_gore(urun: str) -> list[dict[str, Any]]:
    return [z for z in ZARARLILAR if urun in z["urunler"]]


def vektorler() -> list[tuple[str, str]]:
    """(zararlı, taşıdığı hastalık) — ikinci kısma bağlanan köprü."""
    return [(z["ad"], h) for z in ZARARLILAR for h in z["vektor"]]


def depo_koprusu() -> list[str]:
    """Hem tarlada hem ambarda görülenler."""
    return [z["ad"] for z in ZARARLILAR if z["depoda_da"]]


def esigi_olmayanlar() -> list[str]:
    """Ekonomik zarar eşiği YAZILMAMIŞ olanlar.

    Eşiksiz bir zararlı için 'ne zaman ilaçlanmalı' sorusunun cevabı yok
    demektir. Bu liste, hocadan istenecek şeylerin listesidir.
    """
    return [f'{z["ad"]} ({"/".join(z["urunler"])})'
            for z in ZARARLILAR if not z["esik"]]


def ozet() -> dict[str, Any]:
    from collections import Counter
    urun = Counter(u for z in ZARARLILAR for u in z["urunler"])
    return {
        "toplam": len(ZARARLILAR),
        "urun_basina": dict(urun),
        "zarar_sekli": dict(Counter(z["zarar_sekli"] for z in ZARARLILAR)),
        "vektor": len(vektorler()),
        "depo_koprusu": depo_koprusu(),
        "esiksiz": len(esigi_olmayanlar()),
        "kaynak": dict(Counter(z["kaynak"] for z in ZARARLILAR)),
    }


def denetle() -> list[str]:
    hata = []
    adlar = [z["ad"] for z in ZARARLILAR]
    if len(adlar) != len(set(adlar)):
        hata.append("yinelenen zararlı adı var")
    for z in ZARARLILAR:
        if z["zarar_sekli"] not in ZARAR_SEKLI:
            hata.append(f'{z["ad"]}: bilinmeyen zarar şekli {z["zarar_sekli"]}')
        if not 1 <= z["onem"] <= 3:
            hata.append(f'{z["ad"]}: önem 1-3 dışında')
        if not z["urunler"]:
            hata.append(f'{z["ad"]}: ürün listesi boş')
        for ay in z["kritik_aylar"]:
            if not 1 <= ay <= 12:
                hata.append(f'{z["ad"]}: geçersiz ay {ay}')
        if not z["belirti"] or not z["not_"]:
            hata.append(f'{z["ad"]}: belirti ya da not boş')
    return hata


if __name__ == "__main__":
    for h in denetle():
        print("HATA:", h)
    o = ozet()
    print(f"{o['toplam']} tarla zararlısı · {o['vektor']} vektör ilişkisi")
    print("\nÜrün başına:")
    for u, n in sorted(o["urun_basina"].items(), key=lambda x: -x[1]):
        print(f"  {u:16s} {n}")
    print("\nZarar şekli:")
    for s, n in sorted(o["zarar_sekli"].items(), key=lambda x: -x[1]):
        print(f"  {s:14s} {n}   {ZARAR_SEKLI[s]}")
    print(f"\nTarla-ambar köprüsü: {', '.join(o['depo_koprusu'])}")
    print(f"\nEkonomik eşiği YAZILMAMIŞ {o['esiksiz']} zararlı "
          f"(hocaya sorulacak liste):")
    for a in esigi_olmayanlar():
        print("  " + a)
