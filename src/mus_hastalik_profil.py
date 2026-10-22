"""
AGROMATCH - Muş hastalık kataloğu (tek tanım)
==============================================
Muş'ta ekilen DOKUZ ürünün ekonomik önemi olan hastalıkları. Bu dosya Muş
kataloğunun TEK kaynağıdır.

NEDEN AYRI BİR DOSYA
Önceden Muş'un hastalık listesi üç parçadan toplanıyordu: bölgesel katalog
(hastalik_profil.HASTALIKLAR), Muş'a özel ek liste (mus_hastalik.EK_HASTALIK)
ve ürün adlarını eşleyen bir sözlük. Üçü birden okunmadan "Muş'ta kuru
fasulyenin kaç hastalığı var" sorusu cevaplanamıyordu — nitekim bir kez
yanlış cevaplandı. Tek dosya, tek liste.

Bölgesel katalog (hastalik_profil.py) duruyor; onu bölge ölçeğindeki eski
analizler kullanıyor. Muş analizine artık karışmıyor.

KAYNAK DİSİPLİNİ
Her kayıtta `kaynak` alanı var ve iki değer alır:

    "ZMTT"      T.C. Tarım ve Orman Bakanlığı üretici belgeleri /
                Zirai Mücadele Teknik Talimatları'ndan doğrulandı
    "literatür" Fitopatoloji literatüründen; Bakanlık belgesinden
                DOĞRULANMADI, saha gözlemiyle kesinleştirilmeli

Projenin ölçüm/varsayım ayrımının kaynaklara uygulanmış hâli. "literatür"
etiketli bir kayıt yanlış demek değil; DOĞRULANMAMIŞ demek.

Şeker pancarı ve yem bitkileri kayıtları "literatür" çünkü Bakanlığın
"Endüstri ve Süs Bitkileri Hastalıkları" belgesi indirilemedi ve yem
bitkileri için Bakanlık üretici belgesi serisinde karşılık yok. Bu ikisi
Türkşeker Enstitüsü ve Bitki Koruma bölümüyle teyit edilmelidir.

EŞİKLER VARSAYIMDIR
sicaklik_opt ve nem_esik değerleri risk modelinin girdileridir. Kaynak
belgede sayı verildiyse o kullanıldı (örn. patates mildiyösü 19–22 °C,
fasulye antraknozu 17–23 °C); verilmediyse literatürden yaklaşık değer
konuldu. Panel ilaçlama kararı değil ÖNCELİK SIRASI üretir.

KRİTİK AYLAR — Muş takvimine göre
  kışlık tahıl  ekim eylül–ekim, hasat temmuz–ağustos
  şeker pancarı ekim nisan, hasat eylül–kasım
  patates       dikim nisan–mayıs, hasat eylül–ekim
  kuru fasulye  ekim mayıs, hasat eylül
  yem bitkileri biçim mayıs–eylül

EŞİKLER DEĞİŞTİRİLMEDİ — bilerek
Bu dosya kataloğu 22 kayıttan 57'ye çıkarır. Önceden var olan kayıtların
sicaklik_opt / nem_esik / kritik_aylar değerleri AYNEN KORUNDU; yalnızca
yeni hastalıklara yeni değer verildi.

Sebebi: bu üç alan risk modelinin kalibrasyonudur. Katalog genişletirken
yanlarından geçerken değiştirmek, panelin bütün risk sayılarını sessizce
kaydırır. İlk denemede tam bu oldu — on yedi kaydın eşiği farkında olmadan
değişti ve tests/test_regresyon.py bunu yakaladı (Cercospora riski bir
ilçede 31'in altına düştü). Değerler geri alındı.

Resmî belgeler bazı hastalıklar için farklı sayı veriyor; bunlar ilgili
kaydın yanında yorum olarak duruyor. Eşikleri o sayılara göre yeniden
kalibre etmek AYRI ve BİLİNÇLİ bir karardır — ayrı bir commit'te, altın
dosya gerekçesiyle birlikte yapılmalıdır.

Alanlar:
  urun, ad, patojen, tip                 kimlik
  sicaklik_opt, nem_esik, kritik_aylar   risk modelinin girdileri
  belirti, yonetim                       üreticiye gösterilen metin
  pv_sinif, goruntuden                   görüntü işleme hattı için
  kaynak, karantina, onem                köken ve ağırlık
"""

from typing import Any

# onem: 3 = ilde yaygın ve ekonomik kayıp büyük
#       2 = görülüyor, koşullar uygunsa kayıp yapar
#       1 = sporadik ya da henüz Muş'ta kayda geçmemiş

HASTALIKLAR: list[dict[str, Any]] = [

    # ----------------------------------------------------------------- BUĞDAY
    dict(urun="Buğday", ad="Sarı pas", patojen="Puccinia striiformis",
         tip="mantar", sicaklik_opt=(8, 15), nem_esik=450, kritik_aylar=[3, 4, 5],
         belirti="Yaprak damarları boyunca sıralı, limon sarısı püstüller",
         yonetim="Dayanıklı çeşit; sık ekimden ve fazla azottan kaçınma; "
                 "erken uyarıya göre fungisit",
         pv_sinif="Wheat___Yellow_Rust (ek veri seti)", goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Buğday", ad="Kahverengi pas", patojen="Puccinia recondita",
         tip="mantar", sicaklik_opt=(15, 22), nem_esik=400, kritik_aylar=[4, 5, 6],
         belirti="Büyük bir püstülün çevresinde halka oluşturan küçük püstüller",
         yonetim="Dayanıklı çeşit; sarı pastan sonra, kara pastan önce görülür",
         pv_sinif="Wheat___Brown_Rust (ek veri seti)", goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Buğday", ad="Kara pas", patojen="Puccinia graminis f.sp. tritici",
         tip="mantar", sicaklik_opt=(18, 27), nem_esik=420, kritik_aylar=[6, 7],
         belirti="Yaprak, sap ve başakta kenarları yırtık, kiremit kırmızısı "
                 "büyük püstüller",
         yonetim="Dayanıklı çeşit; ara konukçu (kadın tuzluğu) temizliği",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Buğday", ad="Septoria yaprak lekesi", patojen="Septoria tritici",
         tip="mantar", sicaklik_opt=(12, 20), nem_esik=550, kritik_aylar=[3, 4, 5],
         belirti="Damarlarla sınırlı düzensiz kızıl-kahve lekeler; merkezleri "
                 "griye döner, üzerinde küçük siyah noktalar belirir",
         yonetim="Dayanıklı çeşit, geç ekim, ekim nöbeti, derin sürüm; "
                 "fungisit yalnızca epidemi yılında bayrak yaprak döneminde",
         pv_sinif="Wheat___Septoria (ek veri seti)", goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Buğday", ad="Sürme", patojen="Tilletia caries / T. foetida",
         tip="mantar", sicaklik_opt=(5, 15), nem_esik=300, kritik_aylar=[10, 11],
         belirti="Başaklar mavimsi-yeşil ve dik kalır; taneler kirli gri 'kör "
                 "tane'ye döner, ezilince balık kokar",
         yonetim="Tohum ilaçlaması (tercihen selektörde), dayanıklı çeşit, "
                 "ekim zamanı ayarı",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Buğday", ad="Açık rastık", patojen="Ustilago nuda var. tritici",
         tip="mantar", sicaklik_opt=(12, 22), nem_esik=380, kritik_aylar=[5, 6],
         belirti="Çiçeklenmede başaklar simsiyah toz yığınına döner",
         yonetim="Dayanıklı çeşit, ekim zamanı ayarı, yüzlek ekim, "
                 "tohum ilaçlaması",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Buğday", ad="Kök ve kökboğazı çürüklüğü",
         patojen="Fusarium spp. / Bipolaris sorokiniana / Rhizoctonia spp.",
         tip="mantar", sicaklik_opt=(15, 25), nem_esik=350, kritik_aylar=[4, 5, 6],
         belirti="Kök ve kökboğazında kahverengi yaralar, alt yaprak kınlarında "
                 "bal rengi renklenme, cılızlık, boş veya buruşuk tane",
         yonetim="Uygun ekim derinliği, dengeli gübreleme, 2–3 yıl ekim nöbeti, "
                 "anız gömme, tohum ilaçlaması",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Buğday", ad="Külleme", patojen="Blumeria graminis",
         tip="mantar", sicaklik_opt=(15, 22), nem_esik=420, kritik_aylar=[4, 5],
         belirti="Beyaz-gri unlu püstüller; zamanla kahverengileşir, kına, sapa "
                 "ve başağa yayılır, yatmayı artırır",
         yonetim="Dayanıklı çeşit; sık ekimden ve fazla azottan kaçınma; "
                 "ilk belirtide ilaçlama",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Buğday", ad="Kar küfü", patojen="Microdochium nivale",
         tip="mantar", sicaklik_opt=(0, 8), nem_esik=500, kritik_aylar=[2, 3],
         belirti="Kar eridikten sonra yatık, pembe-gri küflü yamalar",
         yonetim="Erken ekimden kaçınma, dengeli azot",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=2),

    # ------------------------------------------------------------------- ARPA
    dict(urun="Arpa", ad="Arpa yaprak lekesi (kav)",
         patojen="Rhynchosporium secalis", tip="mantar",
         sicaklik_opt=(10, 18), nem_esik=500, kritik_aylar=[3, 4, 5],
         # ZMTT: enfeksiyon 4–25 °C aralığında, 30 °C üstünde gelişmiyor.
         # Model "elverişli aralık" istediği için kalibre değer 10–18 korundu.
         belirti="Yaprakta soluk merkezli, koyu kenarlı lekeler; kardeş sayısı "
                 "ve bin tane ağırlığı düşer, kayıp %30–40'a çıkabilir",
         yonetim="Sertifikalı dayanıklı çeşit, anız ve yabancı ot temizliği, "
                 "ağır bulaşık tarlada 2–3 yıl ekim nöbeti, ilk lekede ilaçlama",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Arpa", ad="Ağ lekesi", patojen="Pyrenophora teres",
         tip="mantar", sicaklik_opt=(10, 22), nem_esik=430, kritik_aylar=[4, 5],
         belirti="Yaprakta ağ görünümlü koyu kahve çizgilenme",
         yonetim="Dayanıklı çeşit, ekim nöbeti, anız gömme",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=2),
    dict(urun="Arpa", ad="Külleme", patojen="Blumeria graminis f.sp. hordei",
         tip="mantar", sicaklik_opt=(15, 22), nem_esik=350, kritik_aylar=[4, 5],
         belirti="Yaprak yüzeyinde beyaz unlu örtü",
         yonetim="Sık ekimden ve fazla azottan kaçınma, ilk belirtide ilaçlama",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Arpa", ad="Kapalı rastık", patojen="Ustilago hordei",
         tip="mantar", sicaklik_opt=(12, 22), nem_esik=360, kritik_aylar=[5, 6],
         belirti="Sarı olumda başaklar grimsi, sonra siyahımsı; çoğu zaman "
                 "bayrak yaprak kınından tam çıkamaz",
         yonetim="Dayanıklı çeşit, ekim zamanı ayarı, yüzlek ekim, "
                 "tohum ilaçlaması",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Arpa", ad="Yarı açık rastık", patojen="Ustilago nigra",
         tip="mantar", sicaklik_opt=(12, 22), nem_esik=360, kritik_aylar=[5, 6],
         belirti="Başaklar siyah toz yığınına döner",
         yonetim="Dayanıklı çeşit, ekim zamanı ayarı, tohum ilaçlaması",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Arpa", ad="Kök ve kökboğazı çürüklüğü",
         patojen="Fusarium spp. / Bipolaris sorokiniana", tip="mantar",
         sicaklik_opt=(15, 25), nem_esik=350, kritik_aylar=[4, 5, 6],
         belirti="Kökboğazında kahverengi yaralar, cılızlık, erken kuruma",
         yonetim="Ekim nöbeti (yulaf dahil), dengeli gübreleme, tohum ilaçlaması",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=False, onem=2),

    # ---------------------------------------------------------- ŞEKER PANCARI
    dict(urun="Şeker pancarı", ad="Cercospora yaprak lekesi",
         patojen="Cercospora beticola", tip="mantar",
         sicaklik_opt=(20, 28), nem_esik=400, kritik_aylar=[6, 7, 8],
         # Literatürde optimum 25–32 °C verilir; buradaki 20–28, modelin
         # "elverişli aralık" tanımına göre kalibre edilmiş değerdir.
         belirti="3–5 mm yuvarlak lekeler: açık gri merkez, kırmızı-kahve halka, "
                 "merkezde iğne ucu kadar siyah konidi yatakları",
         yonetim="Dayanıklı çeşit, ekim nöbeti, anız gömme; şiddet eşiğine göre "
                 "koruyucu fungisit (panelin görüntü hattı bu şiddeti ölçer)",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=3),
    dict(urun="Şeker pancarı", ad="Rizomani",
         patojen="Beet necrotic yellow vein virus (vektör: Polymyxa betae)",
         tip="virüs", sicaklik_opt=(18, 26), nem_esik=300, kritik_aylar=[5, 6, 7],
         belirti="Kökte aşırı yan kök (sakal kök), kök ucunda kararma, "
                 "yapraklarda sararma ve dikleşme; şeker oranı belirgin düşer",
         yonetim="Dayanıklı çeşit tek etkili yol; bulaşık tarlada uzun ekim "
                 "nöbeti, drenaj, alet-ekipman temizliği",
         pv_sinif=None, goruntuden=False,
         kaynak="literatür", karantina=False, onem=3),
    dict(urun="Şeker pancarı", ad="Kök çürüklüğü (Rhizoctonia)",
         patojen="Rhizoctonia solani", tip="mantar",
         sicaklik_opt=(20, 28), nem_esik=250, kritik_aylar=[6, 7, 8],
         belirti="Kök boğazında ve kökte kahverengi-siyah çürüme, ani solgunluk",
         yonetim="Drenaj, boğaz doldurmada toprağı yaprak üstüne atmama, "
                 "ekim nöbeti, dayanıklı çeşit",
         pv_sinif=None, goruntuden=False,
         kaynak="literatür", karantina=False, onem=3),
    dict(urun="Şeker pancarı", ad="Fide çökerten",
         patojen="Aphanomyces cochlioides / Pythium spp. / Rhizoctonia solani",
         tip="mantar", sicaklik_opt=(12, 22), nem_esik=450, kritik_aylar=[4, 5],
         belirti="Çıkıştan sonra fide kökboğazı incelip kararır, fide devrilir; "
                 "tarlada boşluklar oluşur",
         yonetim="Tohum ilaçlaması, iyi hazırlanmış tohum yatağı, drenaj, "
                 "soğuk-ıslak toprağa erken ekimden kaçınma",
         pv_sinif=None, goruntuden=False,
         kaynak="literatür", karantina=False, onem=2),
    dict(urun="Şeker pancarı", ad="Külleme", patojen="Erysiphe betae",
         tip="mantar", sicaklik_opt=(20, 30), nem_esik=200, kritik_aylar=[7, 8],
         belirti="Yaprak yüzeyinde beyaz unlu örtü; sıcak ve kurak dönemde hızlanır",
         yonetim="Dayanıklı çeşit; şiddetliyse kükürtlü ya da sistemik fungisit",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=2),
    dict(urun="Şeker pancarı", ad="Pancar pası", patojen="Uromyces betae",
         tip="mantar", sicaklik_opt=(15, 22), nem_esik=430, kritik_aylar=[6, 9],
         belirti="Yaprağın iki yüzünde küçük, sarı haleli kahverengi püstüller",
         yonetim="Dayanıklı çeşit, anız gömme; Cercospora ilaçlamasıyla birlikte "
                 "baskılanır",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=1),
    dict(urun="Şeker pancarı", ad="Fusarium sarılığı ve kök çürüklüğü",
         patojen="Fusarium oxysporum f.sp. betae", tip="mantar",
         sicaklik_opt=(22, 30), nem_esik=350, kritik_aylar=[7, 8],
         belirti="Yapraklarda tek yanlı sararma ve solgunluk, kök kesitinde "
                 "damar kararması",
         yonetim="Ekim nöbeti, dayanıklı çeşit, dengeli sulama",
         pv_sinif=None, goruntuden=False,
         kaynak="literatür", karantina=False, onem=1),

    # ---------------------------------------------------------------- PATATES
    dict(urun="Patates", ad="Mildiyö (geç yanıklık)",
         patojen="Phytophthora infestans", tip="mantar",
         sicaklik_opt=(12, 20), nem_esik=500, kritik_aylar=[6, 7, 8],
         # ZMTT: hızlı yayılım 19–22 °C ve ~%80 nemde. Kalibre değer korundu.
         belirti="Yaprakta soluk yeşil-sarımsı lekeler kahverengileşir, alt "
                 "yüzde beyaz kül; yumruda içe ilerleyen mor-siyah kuru çürüklük",
         yonetim="Sertifikalı temiz tohumluk, bulaşık artıkları uzaklaştırma, "
                 "güneşli ve drenajı iyi yer; günlük ortalama 16 °C ya da "
                 "minimum 10 °C'ye ulaşınca ilaçlamaya başlama",
         pv_sinif="Potato___Late_blight", goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Patates", ad="Erken yanıklık", patojen="Alternaria solani",
         tip="mantar", sicaklik_opt=(20, 28), nem_esik=300, kritik_aylar=[6, 7],
         # ZMTT optimumu 28–30 °C verir; kalibre değer 20–28 korundu.
         belirti="Yaşlı yapraklarda iç içe halkalı, 1–2 cm kahverengi lekeler; "
                 "şiddetlenince yaprak dökümü",
         yonetim="Temiz tohumluk, fazla sulamadan kaçınma, artık temizliği; "
                 "ilk belirtide başlayıp 7–10 gün arayla ilaçlama",
         pv_sinif="Potato___Early_blight", goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Patates", ad="Siyah siğil (kökboğazı nekrozu)",
         patojen="Rhizoctonia solani", tip="mantar",
         sicaklik_opt=(15, 24), nem_esik=420, kritik_aylar=[5, 6, 7],
         belirti="Sap ve kökboğazında kızıl-kahve çökük yaralar; yumruda "
                 "yıkamayla çıkmayan sert siyah siğiller",
         yonetim="Temiz sertifikalı tohumluk, ıslak toprağa dikimden kaçınma, "
                 "dikim öncesi belirtili yumruları ayıklama",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Patates", ad="Kuru çürüklük", patojen="Fusarium spp.",
         tip="mantar", sicaklik_opt=(10, 20), nem_esik=300, kritik_aylar=[9, 10, 11],
         belirti="Yumruda çökük koyu lekeler, iç dokuda kahve-siyah nekroz, "
                 "boşluk ve mumyalaşma; renkli küf tabakası",
         yonetim="Yaralı yumruyu depolamama, 7 °C altında hasat etmeme, "
                 "13–18 °C'de iki hafta kabuk bağlatma, depoda havalandırma",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Patates", ad="Adi uyuz", patojen="Streptomyces scabies",
         tip="bakteri", sicaklik_opt=(18, 26), nem_esik=280, kritik_aylar=[6, 7],
         belirti="Toprak üstünde belirti yok; yumru kabuğunda yüzeysel, kabarık "
                 "ya da derin uyuz yaraları, pazar değeri düşer",
         yonetim="Dayanıklı çeşit ve sertifikalı tohumluk, toprak pH'ını "
                 "yükseltmeme, en az 3 yıl tahılla ekim nöbeti, boğaz doldurmadan "
                 "15 gün sonra düzenli sulama",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Patates", ad="Bakteriyel yumuşak çürüklük (karabacak)",
         patojen="Pectobacterium (Erwinia) carotovorum", tip="bakteri",
         sicaklik_opt=(20, 28), nem_esik=450, kritik_aylar=[6, 7, 8],
         belirti="Sap dibinde kararma ve yumuşama, yaprakta kıvrılma ve sararma; "
                 "yumruda kötü kokulu sulu çürüklük",
         yonetim="Temiz tohumluk, yumruyu kesmeden dikme, ağır toprakta derin "
                 "dikimden kaçınma, kabuk bağladıktan sonra hasat, depo denetimi",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Patates", ad="Patates halka çürüklüğü",
         patojen="Clavibacter michiganensis subsp. sepedonicus", tip="bakteri",
         sicaklik_opt=(18, 24), nem_esik=350, kritik_aylar=[7, 8, 9],
         belirti="Geç dönemde alttan başlayan solgunluk; yumru kesitinde iletim "
                 "demetlerini saran camsı krem-sarı halka, sonra kahverengi ve "
                 "peynirimsi",
         yonetim="KARANTİNA. Sertifikalı temiz tohumluk, yumruyu kesmeme, alet "
                 "ve depoyu çamaşır suyuyla en az 10 dakika dezenfekte etme, "
                 "çuvalı tek kullanma, bulaşık tarlaya 3 yıl patates ekmeme",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=True, onem=3),
    dict(urun="Patates", ad="Bakteriyel solgunluk (kahverengi çürüklük)",
         patojen="Ralstonia solanacearum", tip="bakteri",
         sicaklik_opt=(24, 32), nem_esik=400, kritik_aylar=[7, 8],
         belirti="Sıcak günlerde uç yapraklarda solgunluk, gece toparlanmaz; "
                 "sap dibinde kahverengi çizgiler, kesitten beyaz sümüksü akıntı",
         yonetim="KARANTİNA. Etkili mücadelesi yoktur. Sertifikalı temiz "
                 "tohumluk, 5 yıl münavebe ya da 3 yıl nadas + 2 yıl tahıl, "
                 "yabancı ot ve kendi gelen bitki temizliği, ekipman dezenfeksiyonu",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=True, onem=3),
    dict(urun="Patates", ad="Patates siğili", patojen="Synchytrium endobioticum",
         tip="mantar", sicaklik_opt=(12, 20), nem_esik=500, kritik_aylar=[6, 7, 8],
         belirti="Stolon, yumru gözleri ve kökboğazında karnabahar görünümlü "
                 "yumuşak siğiller; ağır bulaşmada yumru tamamen gala döner",
         yonetim="KARANTİNA. Kimyasal mücadelesi yok. Sertifikalı tohumluk, "
                 "bulaşık tarlada yıllarca patates ekmeme, bulaşık yumruyu yakma "
                 "ya da 80 °C üzerinde kaynatma, aleti %5 çamaşır suyuyla "
                 "dezenfekte etme",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=True, onem=3),
    dict(urun="Patates", ad="Patates Y virüsü (PVY)",
         patojen="Potato Y potyvirus (vektör: yaprak bitleri)", tip="virüs",
         sicaklik_opt=(18, 26), nem_esik=300, kritik_aylar=[6, 7],
         belirti="Mozaik, koyu lekeler, üst yapraklarda kıvrılma; damarlarda "
                 "kararma ve nekroz, bitkide cılızlık, yumru sayısı düşer",
         yonetim="Virüssüz sertifikalı tohumluk, sık dikimden kaçınma, bıçak "
                 "dezenfeksiyonu, 4–5 yapraktan itibaren şüpheli bitkileri "
                 "sökme, yaprak biti mücadelesi",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Patates", ad="Patates yaprak kıvrılma virüsü (PLRV)",
         patojen="Potato leafroll luteovirus (vektör: yaprak bitleri)",
         tip="virüs", sicaklik_opt=(18, 26), nem_esik=300, kritik_aylar=[6, 7],
         belirti="Üst yapraklar sararıp yukarı kıvrılır, alt yapraklar pembeleşip "
                 "ölür; bitki cılız ve dik durur. İkincil bulaşmada yumru "
                 "veriminde %90'a varan kayıp",
         yonetim="Virüssüz sertifikalı tohumluk, dayanıklı/tolerant çeşit, "
                 "yumruyu kesmeden dikme, 4–5 yapraktan itibaren sökme, "
                 "vektörsüz alanda tohumluk üretimi",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),

    # ----------------------------------------------------------- KURU FASULYE
    dict(urun="Kuru fasulye", ad="Fasulye antraknozu",
         patojen="Colletotrichum lindemuthianum", tip="mantar",
         sicaklik_opt=(15, 22), nem_esik=400, kritik_aylar=[6, 7],
         # ZMTT: 17–23 °C, optimum 20–25 °C ve ~%95 nem. Kalibre değer korundu.
         belirti="Fide gövdesi ve kotiledonda çökük koyu kızıl-kahve yaralar; "
                 "yaprak damarlarında, gövde ve baklada kararan lezyonlar",
         yonetim="Sertifikalı temiz tohum, bitki ıslakken tarlaya girmeme, "
                 "ekim nöbeti, artık temizliği",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Kuru fasulye", ad="Fasulye adi yaprak yanıklığı",
         patojen="Xanthomonas axonopodis pv. phaseoli", tip="bakteri",
         sicaklik_opt=(20, 30), nem_esik=300, kritik_aylar=[6, 7, 8],
         belirti="Yaprakta sulu görünümlü küçük lekeler büyüyüp birleşerek koyu "
                 "kahveye döner; baklada yağımsı çökük lekeler, nemde sarı "
                 "bakteriyel akıntı",
         yonetim="Temiz tohum, bulaşık artıkları yok etme, yağmurlama sulamadan "
                 "kaçınma, ekim nöbeti",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Kuru fasulye", ad="Fasulye hale yanıklığı",
         patojen="Pseudomonas savastanoi pv. phaseolicola", tip="bakteri",
         sicaklik_opt=(16, 23), nem_esik=450, kritik_aylar=[6, 7],
         belirti="Yaprakta kahverengi merkezli, sarımsı-yeşil hale ile çevrili "
                 "köşeli lekeler; baklada koyu yeşil sulu lekeler",
         yonetim="Hastalıksız tarladan temiz tohum, bulaşık bitkileri sökme, "
                 "drenaj, yabancı ot kontrolü, ekim nöbeti, yağmurlamadan kaçınma",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Kuru fasulye", ad="Fasulye kök çürüklüğü",
         patojen="Fusarium spp. / Rhizoctonia solani / Macrophomina phaseolina",
         tip="mantar", sicaklik_opt=(18, 28), nem_esik=380, kritik_aylar=[5, 6, 7],
         belirti="Çıkışta boşluklar, bitkide cılızlık ve yaprak dökümü; gövde "
                 "içi boşalır ve kızıl-kahveye döner, kök gelişmez",
         yonetim="Hastalıksız tarladan tohum, baklagil dışı ürünle en az 2 yıl "
                 "ekim nöbeti, fazla azottan kaçınma, taban suyu yüksek yerden "
                 "kaçınma, sık ekim ve aşırı sulamadan kaçınma, tohum ilaçlaması",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Kuru fasulye", ad="Fasulye pası",
         patojen="Uromyces appendiculatus", tip="mantar",
         sicaklik_opt=(16, 24), nem_esik=400, kritik_aylar=[7, 8],
         belirti="Soluk sarı hale ile çevrili kahverengi pas püstülleri; "
                 "mevsim sonunda siyahımsı kahveye döner",
         yonetim="Hasat sonrası artıkları yakma ya da derine gömme, ekim nöbeti; "
                 "yakın bitkilerde pas görülünce haftalık aralıkla 3–5 ilaçlama",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Kuru fasulye", ad="Fasulye adi mozaik virüsü",
         patojen="Bean common mosaic necrosis potyvirus (BCMNV)", tip="virüs",
         sicaklik_opt=(20, 28), nem_esik=280, kritik_aylar=[6, 7],
         belirti="Parlak sarı-yeşil ve koyu yeşil mozaik, yaprakta buruşma, "
                 "kabarcıklanma ve aşağı kıvrılma; sistemik nekrozda bitki ölür",
         yonetim="Dayanıklı çeşit ve virüssüz tohum, şüpheli bitkileri "
                 "komşularıyla birlikte sökme, vektör mücadelesi",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Kuru fasulye", ad="Fasulye sarı mozaik virüsü",
         patojen="Bean yellow mosaic potyvirus (BYMV)", tip="virüs",
         sicaklik_opt=(20, 28), nem_esik=280, kritik_aylar=[6, 7],
         belirti="Özellikle yaşlı yapraklarda parlak sarı mozaik benekler; "
                 "yaprak sertleşip kâse gibi aşağı kıvrılır, erken bulaşmada "
                 "bitki cılız kalır",
         yonetim="Dayanıklı çeşit, virüssüz tohum, şüpheli bitkileri sökme, "
                 "vektör mücadelesi",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=1),

    # --------------------------------------------------------- SİLAJLIK MISIR
    dict(urun="Silajlık mısır", ad="Mısır yaprak yanıklığı",
         patojen="Exserohilum turcicum / Bipolaris maydis", tip="mantar",
         sicaklik_opt=(18, 27), nem_esik=400, kritik_aylar=[6, 7, 8],
         belirti="Baklava dilimi biçiminde lekeler büyüyerek yaprağı kaplar; "
                 "tepe püskülü döneminde şiddetlenirse kayıp %50'ye çıkabilir",
         yonetim="Dayanıklı çeşit, ekim nöbeti, toprak ve yaprak analizine göre "
                 "gübreleme, fazla azottan kaçınma, artık temizliği "
                 "(Türkiye'de kimyasal mücadele önerilmez)",
         pv_sinif="Corn___Northern_Leaf_Blight", goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=3),
    dict(urun="Silajlık mısır", ad="Mısır rastığı", patojen="Ustilago maydis",
         tip="mantar", sicaklik_opt=(18, 26), nem_esik=380, kritik_aylar=[6, 7, 8],
         belirti="Yaprak, sap, koçan ve püskülde urlar; genç urlar sert, parlak "
                 "ve gri-beyaz zarla kaplı",
         yonetim="Sertifikalı tohum, 3–4 yıl ekim nöbeti, urları olgunlaşmadan "
                 "kesip gömme ya da yakma (hayvana yedirmeme), yaralayan "
                 "böceklerle mücadele, fazla azottan kaçınma",
         pv_sinif=None, goruntuden=True,
         kaynak="ZMTT", karantina=False, onem=2),
    dict(urun="Silajlık mısır", ad="Mısır pası", patojen="Puccinia sorghi",
         tip="mantar", sicaklik_opt=(16, 25), nem_esik=450, kritik_aylar=[6, 7],
         belirti="Yaprağın iki yüzünde dağınık, kızıl-kahve püstüller",
         yonetim="Dayanıklı çeşit; silajlık ekimde ekonomik eşiğe nadiren ulaşır",
         pv_sinif="Corn___Common_rust", goruntuden=True,
         kaynak="literatür", karantina=False, onem=1),
    dict(urun="Silajlık mısır", ad="Kök ve kökboğazı çürüklüğü",
         patojen="Pythium spp. / Fusarium spp. / Macrophomina phaseolina",
         tip="mantar", sicaklik_opt=(18, 28), nem_esik=400, kritik_aylar=[6, 7, 8],
         belirti="Fide ölümü; ileri dönemde sap çürüklüğü, kökboğazı bükülüp "
                 "bitki devrilir. Uygun koşulda kayıp %20–30",
         yonetim="Sertifikalı tohum, ekim nöbeti, tarlayı tesviye ederek su "
                 "göllenmesini önleme, uygun derinlik ve sıklıkta ekim, "
                 "boğaz doldurma, tohum ilaçlaması",
         pv_sinif=None, goruntuden=False,
         kaynak="ZMTT", karantina=False, onem=2),

    # ------------------------------------------------------------------ YONCA
    dict(urun="Yonca", ad="Yonca yaprak lekesi",
         patojen="Pseudopeziza medicaginis", tip="mantar",
         sicaklik_opt=(15, 22), nem_esik=450, kritik_aylar=[5, 6, 9],
         belirti="Yaprakçıklarda küçük, koyu kahve, kenarları düzgün yuvarlak "
                 "lekeler; şiddetlenince yaprak dökümü ve kalite kaybı",
         yonetim="Erken biçim (lekeli yaprak dökülmeden), dayanıklı çeşit, "
                 "biçim sonrası artıkları tarlada bırakmama",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=3),
    dict(urun="Yonca", ad="Yonca pası", patojen="Uromyces striatus",
         tip="mantar", sicaklik_opt=(18, 25), nem_esik=400, kritik_aylar=[6, 7, 8],
         belirti="Yaprak alt yüzünde kahverengi toz püstüller",
         yonetim="Erken biçim, dayanıklı çeşit",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=2),
    dict(urun="Yonca", ad="Yonca külleme", patojen="Erysiphe pisi",
         tip="mantar", sicaklik_opt=(18, 26), nem_esik=300, kritik_aylar=[6, 7, 8],
         belirti="Yaprak yüzeyinde beyaz unlu örtü, sıcak-kurak dönemde yayılır",
         yonetim="Erken biçim, dayanıklı çeşit",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=1),
    dict(urun="Yonca", ad="Kök ve kök boğazı çürüklüğü",
         patojen="Fusarium spp. / Rhizoctonia solani", tip="mantar",
         sicaklik_opt=(15, 25), nem_esik=350, kritik_aylar=[5, 6, 9],
         belirti="Bitkide solgunluk, kök kesitinde kahverengileşme; tarla "
                 "yaşlandıkça boşluklar artar",
         yonetim="Drenaj, tarla yaşını uzatmama, ekim nöbeti, biçimde "
                 "kök boğazını yaralamama",
         pv_sinif=None, goruntuden=False,
         kaynak="literatür", karantina=False, onem=3),
    dict(urun="Yonca", ad="Phytophthora kök çürüklüğü",
         patojen="Phytophthora medicaginis", tip="mantar",
         sicaklik_opt=(15, 24), nem_esik=480, kritik_aylar=[5, 6],
         belirti="Yapraklarda kızarma, solgunluk ve çökme; kökte ve nodüllerde "
                 "çürüme. Drenajı bozuk, ıslak tarlalarda",
         yonetim="İyi drenaj, dikkatli tarla hazırlığı, dayanıklı çeşit, "
                 "tohum ilaçlaması",
         pv_sinif=None, goruntuden=False,
         kaynak="literatür", karantina=False, onem=2),
    dict(urun="Yonca", ad="Sclerotinia kök boğazı çürüklüğü",
         patojen="Sclerotinia trifoliorum", tip="mantar",
         sicaklik_opt=(5, 15), nem_esik=480, kritik_aylar=[3, 4, 10, 11],
         belirti="Kök boğazında yumuşak çürüklük ve beyaz pamuksu misel, "
                 "içinde siyah sert sklerotlar; kışı çıkamayan bitkiler",
         yonetim="Drenaj, sonbaharda aşırı gelişmeyi önleme, ekim nöbeti",
         pv_sinif=None, goruntuden=False,
         kaynak="literatür", karantina=False, onem=2),

    # ---------------------------------------------------------------- KORUNGA
    dict(urun="Korunga", ad="Korunga külleme", patojen="Erysiphe trifolii",
         tip="mantar", sicaklik_opt=(16, 24), nem_esik=300, kritik_aylar=[5, 6, 7],
         belirti="Yaprak yüzeyinde beyaz unlu örtü",
         yonetim="Erken biçim, sık ekimden kaçınma",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=2),
    dict(urun="Korunga", ad="Korunga pası", patojen="Uromyces onobrychidis",
         tip="mantar", sicaklik_opt=(18, 25), nem_esik=400, kritik_aylar=[6, 7],
         belirti="Yaprak alt yüzünde kahverengi püstüller, erken yaprak dökümü",
         yonetim="Erken biçim, dayanıklı popülasyon kullanımı",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=1),
    dict(urun="Korunga", ad="Kök ve kök boğazı çürüklüğü",
         patojen="Fusarium spp. / Rhizoctonia solani", tip="mantar",
         sicaklik_opt=(15, 25), nem_esik=350, kritik_aylar=[5, 6, 9],
         belirti="Solgunluk, kök kesitinde kahverengileşme, tarlada boşalma",
         yonetim="Drenaj, ekim nöbeti, tarla yaşını uzatmama",
         pv_sinif=None, goruntuden=False,
         kaynak="literatür", karantina=False, onem=2),

    # -------------------------------------------------------------------- FİĞ
    dict(urun="Fiğ", ad="Fiğ askokitası", patojen="Ascochyta viciae",
         tip="mantar", sicaklik_opt=(14, 22), nem_esik=420, kritik_aylar=[4, 5, 6],
         belirti="Gövde ve yaprakta koyu kenarlı çökük lekeler, baklada yaralar",
         yonetim="Temiz tohum, ekim nöbeti, artık temizliği",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=2),
    dict(urun="Fiğ", ad="Fiğ pası", patojen="Uromyces viciae-fabae",
         tip="mantar", sicaklik_opt=(16, 24), nem_esik=400, kritik_aylar=[5, 6],
         belirti="Yaprakta sarı haleli kahverengi püstüller, erken yaprak dökümü",
         yonetim="Erken biçim, dayanıklı çeşit, ekim nöbeti",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=2),
    dict(urun="Fiğ", ad="Fiğ küllemesi", patojen="Erysiphe pisi",
         tip="mantar", sicaklik_opt=(18, 26), nem_esik=300, kritik_aylar=[5, 6],
         belirti="Yaprak ve gövdede beyaz unlu örtü",
         yonetim="Erken biçim, sık ekimden kaçınma",
         pv_sinif=None, goruntuden=True,
         kaynak="literatür", karantina=False, onem=1),
    dict(urun="Fiğ", ad="Kök çürüklüğü",
         patojen="Fusarium spp. / Rhizoctonia solani", tip="mantar",
         sicaklik_opt=(15, 25), nem_esik=380, kritik_aylar=[4, 5, 6],
         belirti="Çıkış boşlukları, fide ölümü, kökte kahverengileşme",
         yonetim="Baklagil dışı ürünle ekim nöbeti, drenaj, tohum ilaçlaması",
         pv_sinif=None, goruntuden=False,
         kaynak="literatür", karantina=False, onem=2),
]


KAYNAKLAR = {
    "ZMTT": ("T.C. Tarım ve Orman Bakanlığı, Üretici Bilgi Köşesi belgeleri ve "
             "Zirai Mücadele Teknik Talimatları (hububat, patates, mısır, "
             "yemeklik baklagil)"),
    "literatür": ("Fitopatoloji literatürü. Bakanlık belgesinden DOĞRULANMADI; "
                  "Türkşeker Enstitüsü ve Bitki Koruma bölümü saha gözlemiyle "
                  "kesinleştirilecek."),
}


def denetle() -> list[str]:
    """Katalog tutarlılığını denetler. Boş liste = sorun yok."""
    hatalar: list[str] = []
    gorulen: set[tuple[str, str]] = set()
    for h in HASTALIKLAR:
        anahtar = (str(h["urun"]), str(h["ad"]))
        if anahtar in gorulen:
            hatalar.append(f"yinelenen kayıt: {anahtar[0]} / {anahtar[1]}")
        gorulen.add(anahtar)

        if h["kaynak"] not in KAYNAKLAR:
            hatalar.append(f"{h['ad']}: bilinmeyen kaynak {h['kaynak']!r}")
        alt, ust = h["sicaklik_opt"]
        if alt >= ust:
            hatalar.append(f"{h['ad']}: sıcaklık aralığı ters ({alt}–{ust})")
        if not h["kritik_aylar"] or any(not 1 <= ay <= 12 for ay in h["kritik_aylar"]):
            hatalar.append(f"{h['ad']}: kritik ay listesi geçersiz")
        if h["onem"] not in (1, 2, 3):
            hatalar.append(f"{h['ad']}: önem 1–3 olmalı")
        for alan in ("belirti", "yonetim", "patojen"):
            if not str(h[alan]).strip():
                hatalar.append(f"{h['ad']}: {alan} boş")
    return hatalar


def ozet() -> dict[str, Any]:
    from collections import Counter
    return dict(
        toplam=len(HASTALIKLAR),
        urun_basina=dict(Counter(str(h["urun"]) for h in HASTALIKLAR)),
        kaynak=dict(Counter(str(h["kaynak"]) for h in HASTALIKLAR)),
        tip=dict(Counter(str(h["tip"]) for h in HASTALIKLAR)),
        karantina=sum(1 for h in HASTALIKLAR if h["karantina"]),
        goruntuden=sum(1 for h in HASTALIKLAR if h["goruntuden"]),
    )


if __name__ == "__main__":
    import json

    hatalar = denetle()
    if hatalar:
        print("KATALOG TUTARSIZ:")
        for h in hatalar:
            print("  -", h)
        raise SystemExit(1)
    print("Katalog tutarlı.\n")
    print(json.dumps(ozet(), ensure_ascii=False, indent=2))
