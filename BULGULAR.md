# AGROMATCH — Bulgular

Bu belge, projenin **ne öğrendiğini** bir arada tutar. `README.md` yöntemi ve
dizin yapısını anlatır; bulgular orada dağınıktı — kod açıklamalarında, commit
mesajlarında ve panelde. Burada tek yerde ve her biri kaynağıyla birlikte.

**Bu belge ne değildir:** tavsiye listesi değil. Buradaki her madde, projenin
kendi verisine sorduğu bir sorunun cevabıdır ve çoğunun yanında bir **sınır**
yazılıdır. Sınırı olmayan bulgu yoktur; sınırı yazılmamış bulgu ise yayımlanmaz.

Her sayı, bu depodaki kodun bugünkü çıktısıdır. Yeniden üretmek için:

```
python src/mus_panel_uret.py --hepsi
```

---

## Projenin sorusu

Muş'ta ne ekileceğine bugün alışkanlık ve geçen yılın fiyatı karar veriyor.
AGROMATCH şunu sorar: **ilin ve ilçenin gerçek ihtiyacı neyse, desen ona göre
nasıl değişmeli?**

Danışman hocanın çizdiği üç kısım:

1. **Planlama** — hangi ürün nerede yetişir, ne kadar gerekir
2. **Toprak** — topraktan hangi hastalık gelir
3. **Böcek** — tarlada ve depoda hangi zararlı, hangi ilaç, kalıntısız yol var mı

Dördüncüsü sonradan eklendi: **çatı** — bu üç kısmın birbirini denetlediği yer.

## Kapsam

| | |
|---|---|
| İlçe | 6 (Merkez, Bulanık, Malazgirt, Varto, Hasköy, Korkut) |
| Ürün | 9 |
| Ekili alan | 2.239.459 dekar |
| Hastalık kaydı | 59 |
| Tarla zararlısı / faydalı / ilaç grubu | 17 / 8 / 8 (4'ü kalıntısız) |
| Depo zararlısı | 8 |
| Laboratuvar satırı | 2.622 (2011–2015), ilçeye bağlanabilen 1.223 |
| Belirsizlik modeli | 6 soru, 76 düğüm, 40.000 Monte Carlo örneği |

---

# Bulgular

## 1 · İlde uygulanan münavebe, kök çürüklüğü baskısını kırmıyor

**Soru.** Planlama kısmı, ürün deseni dar olan ilçeye *"risk dağılır, münavebe
hastalık baskısını kırar"* diyordu. Bu cümle hastalık kısmına hiç sorulmamıştı.

**Bulgu.** Soruldu. İki ürün topraktan bulaşan aynı etkeni paylaşıyorsa
aralarındaki münavebe o baskıyı kırmaz. 9 ürün 36 çift yapıyor:

| karar | çift | anlamı |
|---|---|---|
| kırar | **1** | şeker pancarı – arpa |
| kırmaz | 17 | ortak etken tür düzeyinde kayıtlı |
| belirsiz | 18 | katalog yalnız cins yazıyor, karar verilemez |

Ve toprağa bakınca: **Muş'ta ekili alanın %83,5'i buğday ile arpa arasında
dönüyor** — bu iki ürün *Bipolaris sorokiniana*'yı paylaşıyor. Yani ilde fiilen
uygulanan münavebe, kırmayan münavebedir.

**Sınır.** "Aynı tür kayıtlı" tarlada aynı suşun geçtiğini kanıtlamaz:
*Rhizoctonia solani*'nin anastomoz grupları konakçıya göre ayrışır (patateste
AG-3, pancarda AG-2-2) ve katalog AG kaydetmiyor. Bu boşluk masa başından
kapanmaz, izolat teşhisi gerektirir.

**Nerede.** `src/cati.py` · `tests/test_cati.py`

## 2 · Kıran tek münavebenin tavanını agronomi değil fabrika kotası koyuyor

**Bulgu.** Baskıyı kıran tek çift pancarlı. Pancar alanı ise Muş Şeker
Fabrikası kotasıyla sınırlı: bugün 112.188 dekar, tavan 120.194 dekar
(boşluk 8.006). Tavan, il ekili alanının **%5,4'ü**.

Yani bu münavebe en iyi durumda ilin topraklarının yirmide birinde
uygulanabilir. Geri kalan alan için projenin elinde *"münavebe baskıyı kırar"*
diyecek bir dayanak yok — oradaki kaldıraç **drenaj ve tohum/çeşittir**.

Bu bir çelişki değil, iki kısmın **birlikte** okunmasının sonucu: ayrı
sekmelerde dururken görünmüyordu.

Aynı öneri bir de toprak katmanına soruldu. 1. kısım kotada boşluk
görünce "sözleşmeli alan **güvenle** büyütülebilir" diyordu; oysa altı
ilçenin altısında da pancar uygunluğu **tavanlanmış** durumda. Merkez ve
Bulanık'ta tavanı koyan kısıt **drenaj** — ve drenaj aynı zamanda pancarın
Rhizoctonia kök çürüklüğüne uygun koşuldur (katalogda önem 3). "Güvenle"
kelimesi tam orada eksikti; şimdi kısıtı adıyla söylüyor. Bu pancarı
büyütmeye karşı bir uyarı değil — sıranın drenajda olduğunun söylenmesi.

**Nerede.** `cati.pancar_tavani()`, `cati.pancar_buyutme_uyarisi()` · `tests/test_cati.py::test_pancar_tavani_celiskiyi_yakaliyor`

## 3 · Cins, tür değildir — ve bu ayrım bulgunun yarısını belirler

**Bulgu.** *Fusarium spp.* dokuz üründen sekizinde kayıtlı. Bunu "aynı patojen"
saymak, 18 "belirsiz" çifti sessizce "kırmaz"a çevirir ve kataloğun
söylemediğini söyler: aynı cinsin farklı türleri farklı konakçı tutar.

Bu yüzden tür düzeyinde eşleşme *kırmaz*, yalnız cins eşleşmesi *belirsiz*
verir. *forma specialis* (f.sp.) eki konakçıya özelleşmeyi gösterdiği için
ortaklığa hiç sayılmaz — *Fusarium oxysporum* f.sp. *betae* pancarı tutar,
buğdayı tutmaz.

**Belirsiz bir cevaptır, eksiklik değil.**

**Nerede.** `cati.munavebe()` · `tests/test_cati.py::test_yalniz_cins_ortakligi_kirmaz_demiyor`

## 4 · Kişi başı tüketim varsayımlarının üçü de yüksekmiş

**Soru.** Belirsizlik modeli "sıradaki en değerli ölçüm" olarak tüketim
parametrelerini gösterdi — ve bu masa başından kapatılabilirdi.

**Bulgu.** TEPGE (Bakanlık araştırma enstitüsü) ürün raporlarından:

| | varsayım (ton/kişi) | ölçüm | kaynak yılı |
|---|---|---|---|
| Buğday | 0,250 | **0,1733** | 2024/25 |
| Patates | 0,085 | **0,058** | 2023/24 |
| Kuru fasulye | 0,009 | **0,0031** | 2023/24 |

Kuru fasulyedeki üç kat fark bir **tanım hatasıydı**: kuru *baklagil* toplamı
(fasulye 3,1 + nohut 4,9 + mercimek ≈5,3 ≈ 13 kg) kuru *fasulye* sanılmıştı.
Proje yalnızca kuru fasulye üretiyor ve dengesini onun üzerinden kuruyor.

Talep yüksek varsayıldığı için il, kendi ihtiyacını olduğundan **az**
karşılıyor görünüyormuş.

**Ama eylem tablosu değişmedi.** Bu bir dayanıklılık işaretidir: model bu
büyüklükte bir girdi değişimine rağmen aynı şeyi öneriyorsa, öneriler o girdiye
aşırı duyarlı değildir. Düzeltme kararı değil, kararın dayandığı sayıyı
düzeltti.

**Nerede.** `src/mus_profil.py` (`GIDA_IHTIYAC`, `GIDA_KAYNAK`) · commit `f617d06`

## 5 · İl kendi buğdayını fazlasıyla üretiyor, baklagil ve patatesi üretmiyor

**Bulgu.** Karşılama oranları (medyan ve %90 aralığı, 40.000 örnek):

| soru | ölçek | karşılama | %90 aralığı |
|---|---|---|---|
| Buğday | ulusal | **3,44** | 2,98 – 3,98 |
| Şeker pancarı | fabrika havzası | 0,96 | 0,76 – 1,27 |
| Kaba yem | ilçe | 0,49 | 0,36 – 0,65 |
| Arpa (kesif yem) | il ve çevre | 0,35 | 0,29 – 0,44 |
| Kuru fasulye | ulusal | 0,31 | 0,27 – 0,36 |
| Patates | ulusal | 0,25 | 0,22 – 0,28 |

Her ürün kendi ölçeğinde dengelenir: kaba yem taşınamadığı için ilçe, pancar
fabrika havzası, buğday ulusal ölçekte.

**Nerede.** `src/mus_iz.py` · `outputs/mus_iz.json`

## 6 · Merkez'in yem açığı ekim yaparak kapatılamaz

**Bulgu.** Merkez'de kaba yem açığı 310.443 ton kuru madde; karşılama 0,276.
Kapatmak için gereken ek yonca alanı **730.008 dekar** — ilçenin **bütün ekili
alanı 554.279 dekar**. Oran 1,32.

Yani bu açık ekimle kapanmaz. Diğer beş ilçede kapanır (oranlar 0,00 – 0,51).
Merkez için doğru hedef açığı **küçültmek**, sıfırlamak değil: mera ıslahı,
hayvan dağılımı ve il dışı yem alımı birlikte düşünülmeli.

Öneri metni bu yüzden "kapatılamaz" diyor — önce "şu kadar dekar ekin" diyordu.

**Nerede.** `mus_analiz.yem_bilancosu()` · `tests/test_mus_profil.py`

## 7 · Veri kusurlu, ve her kusurun nereye dokunduğu biliniyor

Laboratuvar defteri (2.622 satır, 2011–2015) yedi denetimden geçti; altısında
kusur çıktı.

| denetim | bulgu | ne yapıldı |
|---|---|---|
| Yer sütunu | 1.399 / 2.622 sorunlu (%53,4): 1.182 boş, 211 Muş dışı | Muş dışı elenir; 1.223 satır ilçeye bağlandı |
| İmkânsız değer | 12 satırda pH < 3,5 (en düşüğü 2,06) | Ayıklandı |
| Yinelenen satır | 176 satır, beş ölçümün beşi de aynı | **Ayıklanmadı** — hangisinin kopya olduğu bilinemez |
| Kopyala-yapıştır izi | 1 satırda P₂O₅ = K₂O | Sütunlar zaten kullanılmıyor |
| EC – tuz tutarlılığı | 8 satır medyandan on kat sapıyor | Modele EC giriyor, tuz girmiyor |
| P / K birimi | 1.109 karşılaştırılabilir satırın **1.090'ı** (%98,3) beklenen orandan sapıyor | **Bu iki sütun modele hiç sokulmuyor** |
| Boş ölçüm | tamamen boş satır yok | Her alanın n'si ayrı |

İki nokta önemli:

**Yinelenen satırlar gerçekten yineleme mi, yoksa şans mı?** Permütasyon
sınaması yapıldı: her sütun ayrı ayrı karıştırılıp şans beklentisi hesaplandı.
2011'de gözlenen 120, şans beklentisi 0,01. Tekrar gerçek — ama silmek veri
uydurmak olurdu, bu yüzden kayda geçti ve laboratuvara sorulacaklar listesine
girdi.

**Projenin kendi hatası da bu denetimde çıktı:** eski sürüm 130 kaydı yanlış
ilçeye yazıyordu. Düzeltildi.

> Bu veri kusurludur. Kullanılabilir olmasının sebebi kusursuz olması değil,
> **her kusurun nereye dokunduğunun bilinmesidir.**

**Nerede.** `src/toprak_olcum/kalite.py` · `tests/test_kalite.py`

## 8 · "Tutuyor mu" yanlış soruydu

**Soru.** Laboratuvar ölçümleri bağımsız bir kaynakla doğrulanabilir mi?
ISRIC SoilGrids 2.0'dan 6 ilçe için 1.176 nokta sorgulandı.

**İlk sonuç yanıltıcıydı:** 18 karşılaştırmanın yalnızca 2'si tuttu (%20). Bu
rakam yayımlanmadı, çünkü yanlış soruyu cevaplıyor — SoilGrids de bir **tahmin**
ürünüdür, Muş'u özel olarak bilmez. Onu doğru kabul edip laboratuvarı
yargılamak, bilinmeyeni bilinenin hakemi yapmaktır.

**Üç ayrı soru soruldu:**

1. **Mutlak değerler tutuyor mu?** pH'ta ortalama fark 0,53; organik maddede 4,09.
2. **Sapma sistematik mi?** pH'ta kayma −0,53 ve **her ilçede aynı yönde**;
   organik maddede +4,09, yine aynı yönde. Aynı yönlü sapma, küresel modelin bu
   bölgedeki **yanlılığına** işaret eder — laboratuvarın yanlış olduğunun kanıtı
   değildir.
3. **İki kaynak ilçeleri aynı sırada mı diziyor?** Asıl soru bu, çünkü model
   ilçeleri birbirine göre kıyaslıyor. pH ve organik maddede ilçeler arası fark,
   ilçe içi yayılımdan küçük: **bu iki alan ilçeleri ayırt etmeye yetmiyor.**

**En kritik eksik:** kireç ve tuzluluk **hiç doğrulanamadı** — SoilGrids
karbonat ve elektriksel iletkenlik yayımlamıyor. Varsayımın en çok şaştığı alan
kireçti; yani en çok doğrulanması gereken alan doğrulanamadı.

**Nerede.** `src/toprak_dogrulama/` · `tests/test_dogrulama.py`

## 9 · İstatistiksel olarak gerçek bir anlaşmazlık, tavsiyede 1 satır ediyor

**Soru.** Kil ölçümünde laboratuvar ile SoilGrids anlaşmıyor. Bu, çiftçiye
verilen öneriyi ne kadar değiştirir?

**Bulgu.** Kil puana doğrudan girmiyor; önce **bünye sınıfına** çevriliyor
(≥%45 killi, ≥%35 killi-tın). Bu yüzden bir kil farkı ancak **sınıf sınırını
geçtiğinde** tavsiyeyi değiştirir.

| karşılaştırma | değişen satır | sınıf değişen |
|---|---|---|
| varsayım → laboratuvar | 12 | 6 |
| laboratuvar → SoilGrids | 6 | **1** |
| varsayım → SoilGrids | 17 | 7 |

Yani iki kaynak arasındaki anlaşmazlık gerçek, ama tavsiyeye **tek bir satır**
olarak yansıyor. Anlaşmazlığın büyüklüğü değil, **sınıf sınırını geçip
geçmediği** önemli.

**Nerede.** `src/toprak_dogrulama/kil_etkisi.py` · `tests/test_kil_etkisi.py`

## 10 · Ölçüm bir iyileştirmedir, önkoşul değil

**Bulgu.** Laboratuvar katmanı açılıp kapatılabilir (`OLCUM_KULLAN`). Açıldığında
54 uygunluk satırının 45'i ölçümle hesaplanıyor:

- ortalama mutlak fark **1,6 puan**, en büyük fark 15,8
- 6 satırda sınıf değişti, **0 satırda kritik kısıt değişti**
- 9 satır iyileşti, 3 satır kötüleşti

Ölçüm kararı iyileştiriyor ama hiçbirinin **kısıtını** değiştirmiyor: drenaj,
tuzluluk ve derinlik tavanları yerinde kalıyor. Bu, modelin ölçüm olmadan da
çalışabilmesinin sebebi.

**Nerede.** `src/toprak_olcum/etki.py` · `tests/test_regresyon.py`

## 11 · Depoda koşulu söylemeden ilaç önermek kura çekmektir

**Bulgu.** Diyatomlu toprak zehir değil **aşındırıcıdır**: böceğin mum
tabakasını yıpratır, böcek su kaybından ölür. Etkisi bu yüzden sıcaklık ve nemle
değişir — ve değişim küçük değil. Literatürde **aynı ürün, aynı doz (1000 ppm),
aynı süre (7 gün)**:

| koşul | ölüm |
|---|---|
| 26 °C / %55 nem | %2,2 |
| 30 °C / %40 nem | %83,0 |

**37,7 kat fark.** Bu yüzden koşul uyarısı kararın ayrı bir adımıdır, dipnot
değil.

**Nerede.** `src/depo/literatur.py`, `src/depo/karar.py` · `tests/test_depo_karar.py`

## 12 · Depoda ilk soru "hangi ilaç" değil, "böcek nerede"

**Bulgu.** 8 depo zararlısının **3'ü taneyi içeriden yiyor** (buğday biti, küçük
tahıl kurdu, arpa güvesi). Tane dışarıdan sağlam görünür ve yüzeye uygulanan
hiçbir şey — diyatomlu toprak dahil — o larvaya ulaşmaz.

Bunu atlamak projenin verebileceği **en pahalı yanlış tavsiyedir**: çiftçi
diyatomu doğru uygular, erginleri öldürür, içerideki larvalar gelişmeye devam
eder, ürün yine kaybedilir — üstelik "kalıntısız yol işe yaramıyor" kanaatiyle.

**Nerede.** `src/depo/karar.py` · `tests/test_depo_karar.py::test_ic_besleyende_yuzey_yontemi_ulasan_listesine_girmiyor`

## 13 · Tarlada 17 zararlının 12'sinde eşik yok — ve bu yazılıyor

**Bulgu.** Karar akışının ilk düğümü eşiktir, ilaç değil. Çünkü zararlının
**varlığı** tek başına zarar demek değildir ve eşiğin altında ilaçlamak faydalıyı
öldürüp sorunu büyütür.

| | |
|---|---|
| Sayısal eşiği olan | 11 / 17 |
| Talimatın eşik vermediği | 4 / 17 |
| Eşiği bilinmeyen | 2 / 17 |
| Kalıntısız yolu olmayan | 7 / 17 |
| Hiçbir seçeneği olmayan | 0 |

Eşiği bilinmeyen zararlıya **ilaçlama önerilmiyor** — "eşik yok" diye yazılıyor
ve karar tarlayı gören ziraat mühendisine bırakılıyor.

**ZMTT taraması (28 Kasım 2026).** Bakanlık TAGEM Entegre Mücadele Teknik
Altı resmî belge okundu ve **eşiği bilinmeyen zararlı 12'den 2'ye indi.**
Dokuz kayda eşik işlendi, dördünde talimatın eşik VERMEDİĞİ tespit
edildi. Belgede bulunmayan eşik uydurulmadı.

Kalan iki zararlı — yonca yaprak biti ve baklagil tohum hortumluları —
ZMTT'nin altı ciltlik setinde **hiç yok**; bu, Cilt VI'nın I–VI genel
indeksi taranarak doğrulandı. Yani oradaki eksik, arama yetersizliği
değil, kaynakta bulunmama.

Beş belge okundu, üçü işe yaradı. Okunup **hiçbir şey vermeyen** ikisi de
kayda değer: "Hububat Zararlıları ZMTT" kımıl, ekin sap arısı ve hububat
yaprak bitlerini içermiyor (mısır ve çim zararlıları için bir ek cilt),
"ZMTT Cilt 6" ise nematod ve yabancı ot cildi. Belgenin adı içeriğini
garanti etmiyor.

Bunlardan dördü karar sisteminin cevabını değiştiriyor:

- **Yeşil şeftali yaprak biti** — talimat yemeklik patateste *"mücadele
  eşiğine ulaşılmadığı için kimyasal mücadele önerilmemektedir"* diyor.
  Tohumluk patateste ise virüs yayılımı için gerekebilir ve orada eşik
  bir yoğunluk değil **varlık**: 50 yaprakta tek bir yaprak biti bulunması
  yeter. Yani kararı zararlının yoğunluğu değil, ürünün ne için
  yetiştirildiği belirliyor.
- **Patates güvesi** — depo sıcaklığı **10 °C'nin altındayken zararlı
  gelişemiyor**. Tarlada başlayıp depoda süren tek zararlının kararı, böylece
  3. kısmın depo tarafına bağlanıyor.
- **Ekin sap arısı** — talimat **kimyasal mücadeleyi hiç önermiyor**;
  yalnızca kültürel önlem sayıyor. Üstelik bir uyarısı doğrudan bu projeye
  bakıyor: parazitoitlerin ergin çıkışı zararlınınkiyle aynı güne denk
  geldiği için, o günlerde **başka** hububat zararlısına yapılacak
  ilaçlamada yan etkisi az ürün seçilmeli. Bu zararlıya hiç ilaç atılmasa
  bile komşu kararı onu etkiliyor.
- **Hububat yaprak bitleri** — sayısal eşik yok; sürveyde zararlıyla
  **birlikte yararlı da sayılıyor** ve karar araştırma enstitüleri ile İl
  Müdürlüğü işbirliğiyle veriliyor. Talimat ayrıca resmen önerilen bir
  kimyasal preparat **bulunmadığını** yazıyor — bizim katalog ise bu
  zararlı için bir etki grubu gösteriyordu. Grup kaldırılmadı (etki grubu
  ruhsat tavsiyesi değildir) ama karar akışının 3. adımı artık bu uyarıyı
  taşıyor.
- **Bakla yaprak biti** — eşik yaprak başına 10–20 birey; ama talimat
  yanına şunu koyuyor: *ilaçlamaya karar vermeden önce parazitoit ve
  predatörlerin etkinliği dikkate alınmalı.* Sünede olduğu gibi faydalı,
  kararın parçası. Projenin "faydalı kararı değiştirir" savının ikinci
  resmî dayanağı.
- **Pancar piresi** — eşik bir böcek sayısı değil, **yaklaşık yaprak alanı kaybı**:
  asimilasyon alanının %20'si. Üstelik talimat üç ayrı gerekçeyle ilaçlamaya
  karşı duruyor: tohum ilacı çıkıştan sonra 35–40 gün koruyor, sonraki
  döllerin zararını bitki telafi ediyor, larvaların köke zararı önemsiz.
  Yani eşik aşılsa bile sıra önce tohum ilacında.

**Kalan beşin nerede olduğu da doğrulandı.** ZMTT setinin Cilt VI'sı
I–VI ciltlerinin genel indeksini taşıyor; o indeks tarandı:

| zararlı | nerede |
| --- | --- |
| Kımıl (*Aelia* spp.) | Cilt I |
| Ekin sap arıları (*Cephus pygmaeus*) | Cilt I |
| Hububat yaprak bitleri (*Rhopalosiphum padi*, *Sitobion avenae*) | Cilt I |
| Yonca yaprak biti (*Acyrthosiphon pisum*) | **sette yok** |
| Baklagil tohum hortumluları (*Apion* spp.) | **sette yok** |

Son ikisi için eşik eksikliği **arama yetersizliği değil**: indekste ne
*Acyrthosiphon* ne de "bezelye yaprakbiti" kaydı var, *Apion* ise yalnızca
mercimekte ve farklı bir türle (*A. arrogans*, Cilt III) geçiyor. Yem
bitkisi zararlılarından sette sadece yonca hortumlu böceği ve korungada
çadır tırtılı bulunuyor. Bu artık kaynağıyla birlikte söylenebilen bir
boşluk.

Bir de tarama sırasında kendi hatamı yakaladım: patates yaprak biti eşiği
önce yanlışlıkla **hububat yaprak bitleri** kaydına yazıldı — iki kaydın
doğal düşman listeleri birebir aynıydı ve yama ilk eşleşmeye tutundu.
`bosluklar()` bunu hemen gösterdi. Artık bir test, eşik metninin zararlının
ürünleri arasında olmayan bir ürünü anmasını yakalıyor.

Karar sistemi bilerek **etki grubuna** kadar götürür; ticari ürün adı, doz ve
bekleme süresi vermez. Bunlar reçetedir. (Proje bir zamanlar bekleme süresi
veriyordu ve **uydurmaydı**; kaldırıldı ve testle geri gelmesi engellendi.)

**Nerede.** `src/bocek/karar.py` · `tests/test_bocek_karar.py`

## 14 · Öneriler aynı toprağı istiyor ve kimse toplamıyordu

**Soru.** Bir ilçeye verilen öneriler tek tek doğru. Peki hepsi birlikte
o ilçenin toprağına sığıyor mu?

**Bulgu.** Yem açığı önerisinin tek uygunluk testi "gereken alan ilçeye
sığıyor mu" idi — çok zayıf bir eşik. Bulanık'ta gereken ek yonca
297.242 dekar; ilçenin bütün ekili alanı 577.970 dekar. Yani öneri tek
başına ilçenin **%51,4'ünü** istiyor ve test onu "kapanır" diye
geçiriyordu. Pancar payıyla birlikte öneriler **%51,8**.

| İlçe | öneriler toplamı | ekili alan payı | durum |
| --- | --- | --- | --- |
| Merkez | 733.104 dekar | %132,3 | sığmıyor |
| Bulanık | 299.587 dekar | %51,8 | yarıdan fazlası |
| Varto | 51.620 dekar | %22,6 | sığıyor |
| Korkut | 31.463 dekar | %19,6 | sığıyor |
| Malazgirt | 65.385 dekar | %12,0 | sığıyor |
| Hasköy | 644 dekar | %0,4 | sığıyor |

Merkez zaten "kapatılamaz" diye işaretliydi (bulgu 6). Yakalanan yeni
şey Bulanık: aritmetik olarak sığdığı için geçiyordu, oysa ilçenin
yarısını başka ürüne çevirmek tavsiye değil **dönüşümdür**. Öneri artık
istediği payı söylüyor.

**Sınır.** Burada agronomik eşik uydurulmadı. Sınırlar yalnızca
aritmetik: toplam ekili alanı aşıyorsa "sığmıyor", yarısını aşıyorsa
"yarıdan fazlası". Hangi oranın gerçekten uygulanabilir olduğu
agronomik bir sorudur ve bu proje onu bilmiyor — bildiği ve söylemesi
gereken şey, önerinin ne kadar toprak istediğidir.

**Nerede.** `cati.arazi_butcesi()`, `cati.arazi_cumlesi()` · `tests/test_cati.py`

## 15 · Öneri metinleri ölçümü hiç okumuyordu

**Soru.** Taramanın son üç vaadi: "drenaj her şeyin önünde", "fosforu
kireç bağlıyor", "erozyon riski yüksek". Bunlar neye dayanıyor?

**Bulgu.** Dayandıkları sayıları **ham varsayımdan** okuyorlardı. Aynı
projenin toprak katmanı o değerlerin ölçülmüş hâlini üretiyor; öneri
metni onu hiç çağırmıyordu. Yani 1. kısmın puanlaması ölçümle, öneri
metni varsayımla konuşuyordu — aynı toprak hakkında iki sayı.

Kireçte fark küçük değil:

| İlçe | varsayım | laboratuvar | ölçüm kullanıldı mı |
| --- | --- | --- | --- |
| Merkez | %10 | **%2,2** | evet |
| Bulanık | %9 | **%1,3** | evet |
| Korkut | %11 | **%2,6** | evet |
| Hasköy | %9 | **%1,4** | evet |
| Varto | %4 | **%1,4** | evet |
| Malazgirt | %13 | %2,7 | **hayır** — n=4, güven eşiği 30 |

Beş ilçenin beşinde de ölçüm varsayımın **3–7 kat altında**. Ve fosfor
önerisi tam olarak altıncı ilçede, Malazgirt'te çıkıyor: ölçümünün
reddedildiği ve varsayımın (%13) yerinde kaldığı tek ilçe. O ilçenin
kendi ince ölçümü de %2,7 diyor, yani diğer beşle aynı yönde.

Üstüne: **kireç, SoilGrids'in yayımlamadığı iki alandan biri** (bulgu 8)
— projenin bağımsız bir kaynakla hiç doğrulayamadığı değer. Yani bu
öneri projenin en az doğrulanmış sayısına dayanıyor ve bunu
söylemiyordu. Artık söylüyor.

**Öneri sayıları değişmedi.** Hiçbir madde ortaya çıkmadı ya da kayboldu;
değişen şey tavsiye değil, tavsiyenin dayanağının görünür olması.

**Onaylanan iki vaat.** Aynı taramada "drenaj her şeyin önünde" iddiası
veriyle TUTUYOR: öneri çıkan iki ilçede (Merkez, Bulanık) drenaj dokuz
üründen **sekizinin** tavanını koyuyor. "Erozyon riski yüksek" ise
korunga öneriyor ve yem açığı önerisi de "yonca ya da eşdeğeri korunga"
diyor — ikisi çelişmiyor. Yalnızca yanlışları raporlayan bir tarama
yanlı olurdu.

**Sınır.** Erozyon önerisi "yıllık tahıl bu araziyi yorar" diyor; aynı
ilçelerde pancar alanının büyütülmesi de öneriliyor ve pancar yıllık bir
çapa bitkisidir. Bunu değerlendirmek için projede **olmayan** bir alan
gerekir (ürünün toprak örtüsü / çok yıllık mı). Uydurulmadı; boşluk
olarak yazıldı.

**Nerede.** `cati.toprak_girdisi()`, `cati.kirec_uyarisi()` · `tests/test_cati.py`

## 16 · "Talimat eşik vermiyor", "eşiği bilmiyoruz" demek değil

**Soru.** ZMTT taramasında bir zararlının belgesinde eşik yerine başka bir
ölçüt bulundu. Karar sistemi bunu nasıl göstermeli?

**Bulgu.** Göstermiyordu — ve yanlış gösteriyordu. Karar akışının ilk adımı
yalnızca iki cevap biliyordu: *eşik var* ya da *eşik bilinmiyor*. Oysa üç
durum var:

| cevap | anlamı |
| --- | --- |
| eşik var | karar sayıma bağlı |
| **resmî eşik yok** | **talimat eşik VERMİYOR ve bunu açıkça yazıyor; karar başka bir ölçüte bağlı** |
| eşik bilinmiyor | bizde kayıt yok — ilaçlama önerilmez |

Bu ayrım yokken **patates böceği** kaydı kendi kendisiyle çelişiyordu: eşik
metni *"kimyasal mücadelede EŞİK YOKTUR"* diye başlıyor, ama karar akışı o
kaydı "eşik var — ölçüm gerekli" diye gösteriyordu. Yani olmayan bir sayıyı
saydırıyordu. **Fasulye tohum böceğinde** de aynısı olacaktı: talimat eşik
vermiyor, mücadeleyi fenolojik döneme bağlıyor (alt kapsüller kuru oluma
girince).

İkisini "eşiği bilinmeyen" kovasına atmak da yanlış olurdu: orada boşluk
bizde değil, Bakanlık eşik yerine başka bir ölçüt koymuş.

**Sınır.** Bu ayrımın hangi kayıtlara konacağı belge okunarak elle
belirleniyor; otomatik bir kural yok. Şimdilik iki kayıtta var.

**Nerede.** `bocek/karar.py` (`_esik_adimi`, `bosluklar`) · `tests/test_bocek_karar.py`

## 17 · Ölçüm kendi türünün dışına taşmıştı

**Soru.** Cilt I'in içinde depolanmış ürün zararlıları da varmış. Depo
kataloğunun sekiz kaydı da "literatür" etiketliydi; belgeye sorulunca ne
çıkar?

**İki şey çıktı, ikisi de kendi hatamız.**

**1. Ölçüm kapsamının dışında gösteriliyordu.** Bulgu 11'deki 37,7 kat
fark *Sitophilus granarius* üzerinde ölçüldü. Ama karar sistemi o sayıyı
diyatomlu toprak önerilen **her** zararlının kartında, tür adı vermeden
gösteriyordu — kırma bitinde de, un akarında da. Diyatomitin etkisi türe
göre belirgin değişir; sayıyı tür adı olmadan sunmak onu o tür için
ölçülmüş gibi okutur. Bu, projenin başka yerlerde özenle kaçındığı
hatanın ta kendisi: ölçümü kapsamının dışına taşımak.

Sayı kaldırılmadı — koşulun ne kadar belirleyici olduğunu göstermesi
hâlâ doğru. Ama kart artık türü söylüyor ve farklı türse şunu ekliyor:
*"buradaki sayı koşulun NE KADAR belirleyici olduğunu gösterir, bu tür
için beklenen ölümü değil."*

**2. Bir zararlının Türkçe adı yanlıştı.** Katalog *Tribolium castaneum*'a
**"Kırma biti"** diyordu. ZMTT Cilt I'e göre Kırma biti *T. confusum*'dur;
*T. castaneum*'un resmî adı **"Un biti"**. Kayıttaki sıcaklık verisi
(optimum 32–35 °C) *castaneum*'a uyduğu için tür korundu ve **ad
düzeltildi**. Yanlış Türkçe ad, okuyucuyu başka bir türe götürür.

**Doğrulanan.** Depo karar sisteminin bel kemiği olan "tane içinde
besleniyor mu" bayrağı iki kritik kayıtta belgeyle teyit edildi:
*Sitophilus granarius* için *"yumurta, larva ve pupa dönemi tane içinde
geçer"*, *Rhizopertha dominica* için *"delerek girdikleri hububat tanesi
içinde gelişir... pupa dönemi tane içinde geçer"*. Bu bayrak yanlış
olsaydı modülün kendi deyimiyle "projenin verebileceği en pahalı yanlış
tavsiye" üretilirdi.

**Sınır.** Kalan altı depo kaydı hâlâ "literatür": belgede okunup teyit
edilen yalnızca bu ikisi ve Tribolium adlandırması.

**Nerede.** `depo/literatur.py` (`OLCULEN_TUR`), `depo/karar.py` (`_kosul_adimi`) · `tests/test_depo_karar.py`

## 18 · "Yüzde kaç doğruluk" yerine: model ayırt edebiliyor mu

**Soru.** Bu bir karar destek sistemi. Peki ne kadar doğru?

**Önce cevaplanamayacak olanı söylemek gerekiyor.** Bu projede bir
**doğruluk oranı yoktur ve uydurulmayacaktır.** Doğruluk oranı
sınıflandırıcıların ölçüsüdür: etiketli doğru cevaplar gerekir. "Muş'ta
doğru ekim kararı" diye gözlemlenebilir bir gerçek yok — bilmek için aynı
tarlada hem öneriyi uygulayıp hem uygulamamak gerekirdi. Üstelik ilçe
katmanı künyede zaten *dağıtım, güven düşük* diye işaretli; ilçe
düzeyinde "doğruluk" ölçmek kendi varsayımımızı ölçmek olurdu.

**Ama ölçülebilen bir şey var:** model, cevabını **önceden bildiğimiz**
vakaları ayırabiliyor mu?

Proje bunu sorabilir hâle geldi çünkü iklim tarafı tablo değil
**mekanik**: etkili sıcaklık toplamı, donsuz gün, kış minimumu. Yeni bir
tür için gereken, Muş'a dair veri değil, o türe dair istek.

**Modelde bulunan açık.** Soru sorulunca ortaya çıktı: iklim uygunluğu
kış minimumuna **hiç bakmıyordu**. Dokuz ürünün dokuzu da yıllık olduğu
için bu bugüne kadar sorun değildi; ama çok yıllık bir tür sorulunca
model zeytini, yazın sıcaklık toplamını tutturduğu için kabul ederdi.
Kış kapısı eklendi.

**Deney.** Kış dayanımları tek bir akademik kaynaktan (Ankara
Üniversitesi açık ders materyali), Muş'ta varlık bilgisi İl
Müdürlüğü'nün kendi 2025 faaliyet raporundan (Tablo 9). Kiraz, kaynak
tabloda yer almadığı için deneye alınmadı.

| grup | türler | beklenen | sonuç |
| --- | --- | --- | --- |
| Muş'ta **yok** | zeytin (−7), incir (−9), nar (−10), portakal (−5), limon (−3,5), muz (0) | elenmeli | **6/6 elendi** |
| Muş'ta **var** | elma (−35), ceviz (−25), armut (−25), üzüm (−16) | elenmemeli | **0/4 elendi** |

Merkez'de en soğuk ayın gece ortalaması **−12 °C**. Kış kapısı iki grubu
tam olarak ayırıyor.

**Abartılmayacak yer.** Yetişen dört meyve için model "yetişir" de
**demiyor** — sıcaklık toplamı istekleri kayıtlı olmadığı için
"söylenemez" diyor. Ölçülen tek şey kış kapısıdır.

**Testin bulduğu gerçek eksik.** Kayısı (−20) ve badem (−18) kışı
atlatıyor, model onları reddedemiyor; oysa Muş'ta yetişmiyorlar. Sebep
modelde bulunmayan bir mekanizma: ikisi de çok erken çiçeklenir ve asıl
engel **ilkbahar geç donudur**. Bir doğrulama testinin en değerli çıktısı
budur — modelin nerede kör olduğunu söylemesi.

**Sınır.** Kullanılan kış minimumu en soğuk ayın **gece ortalamasıdır**;
Muş'un kaydedilmiş mutlak minimumu daha düşüktür. Test bu yüzden gevşek
taraftadır: reddedilen tür marjla reddedilmiştir, sınıra yakın kabul
edilen tür güvende demek değildir.

**Ne söylemez.** Model "yetişir" dese bile verim, kârlılık ve pazar
hakkında hiçbir şey söylemez. Bir ürünün yetişebilir olması, ekilmesi
gerektiği anlamına gelmez.

**Nerede.** `src/yeni_urun.py` · `tests/test_yeni_urun.py` · panelde "Yeni ürün" sekmesi

---

# Projenin cevap veremediği yerler

Bir karar sisteminin en dürüst kısmı, nerede karar veremediğidir.

| boşluk | etki | masa başından kapanır mı |
|---|---|---|
| Anastomoz grubu (AG) kaydı yok | "Aynı tür" diyebiliyoruz, "aynı suş geçiyor" diyemiyoruz | **Hayır** — izolat teşhisi gerekir |
| Kireç ve tuzluluk doğrulanamadı | Varsayımın en çok şaştığı alan doğrulanamadı | Hayır — bağımsız ölçüm gerekir |
| Fabrika günlük kapasitesi + kampanya süresi | Pancar sorusunun belirsizliğinin **%97,5'i** bu ikisinde | **Evet** — bir telefon görüşmesi |
| P / K birimi | İki sütun modele hiç giremiyor | **Evet** — laboratuvara sorulacak ilk soru |
| Cins düzeyinde kalan etkenler | 18 ürün çiftinde münavebe kararı belirsiz | **Evet** — tür düzeyi kayıt aranabilir |
| Bulaş kaynağı atamaları | Topraktan/havadan ayrımı literatüre dayanıyor, Bakanlık belgesinden doğrulanmadı | Evet — danışman gözden geçirmesi |
| İlkbahar geç donu modelde yok | Erken çiçeklenen türler (kayısı, badem) elenemiyor | Evet — çiçeklenme dönemi don riski eklenebilir |
| Meyve türlerinin sıcaklık toplamı isteği kayıtlı değil | Kışı atlatan türler için "yetişir" denemiyor | Evet — literatürden kayıt |
| Malazgirt kireç ölçümü n=4 | Fosfor önerisi varsayıma dayanıyor | Evet — o ilçeden daha çok örnek |
| Ürünün toprak örtüsü / çok yıllıklık alanı yok | Erozyon önerisi ile pancar büyütme önerisi karşılaştırılamıyor | Evet — literatürden kayıt eklenebilir |

**Baskın bilinmeyenler** (duyarlılık analizi, varyans payı):

| soru | baskın bilinmeyen | pay |
|---|---|---|
| Patates | kişi başı tüketim | %99,1 |
| Şeker pancarı | fabrika kapasitesi + kampanya süresi | %67,5 + %30,0 |
| Arpa | büyükbaş kesif yem ihtiyacı | %69,7 |
| Kaba yem | mera verimi | %71,9 |
| Buğday | tohumluk ve fire payı | %65,5 |
| Kuru fasulye | üretim + tüketim | %51,1 + %47,5 |

---

# Yöntem ilkeleri

**Ölçüm bir iyileştirmedir, önkoşul değil.** Her ölçüm katmanı açılıp
kapatılabilir ve kapalıyken varsayıma düşer. Ölçüm beklemek yerine, ölçümün
kararı ne kadar değiştirdiği ölçülür (bkz. bulgu 10).

**Her kayıt kaynağını taşır.** `ölçüm` / `resmî` / `literatür` / `model` /
`sentetik` / `varsayım` / `dağıtım`. Eşikler ayrıca `ZMTT` ya da `literatür`
etiketlidir. "literatür" yanlış demek değil, **doğrulanmamış** demek.

**Sayılar sessizce değişemez.** Altın dosya (`tests/altin/`) refactor öncesi
çıktıyı tutar; değişecekse gerekçesi `tests/test_altin.py` içindeki
"GÜNCELLEME KAYDI" bölümüne yazılır. Bir kez katalog genişletilirken on yedi
kaydın eşiği farkında olmadan değişti ve regresyon testi yakaladı.

**Boş liste bir cevaptır.** "Bu zararlı için kalıntısız yol YOK" eksiklik değil,
bilinen bir boşluktur; öyle yazılır, uydurulmaz.

**Panelde yayımlanan her sayının bir testi vardır.** Bu belgedeki bulguların
tamamı `pytest` ile doğrulanır.

---

## Kaynaklar

- T.C. Tarım ve Orman Bakanlığı — Zirai Mücadele Teknik Talimatları (ZMTT)
- TEPGE ürün raporları — kişi başı tüketim
- TÜİK — üretim ve alan istatistikleri
- Muş İl Tarım ve Orman Müdürlüğü — laboratuvar kayıtları (2011–2015), faaliyet raporları
- ISRIC SoilGrids 2.0 (250 m, CC-BY 4.0)
- Depo literatürü: Agrafioti ve ark. 2023; Öğreten ve ark. 2025

---

Hasan Turgut · Muş Alparslan Üniversitesi, Yazılım Mühendisliği
