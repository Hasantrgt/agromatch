# AGROMATCH — Muş Tarım Planlama Motoru

[![Testler](https://github.com/Hasantrgt/agromatch/actions/workflows/test.yml/badge.svg)](https://github.com/Hasantrgt/agromatch/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Lisans: MIT](https://img.shields.io/badge/lisans-MIT-green)](LICENSE)

Talep odaklı ekim planlaması için analiz motoru ve rapor paneli.
**Pilot il: Muş** · 6 ilçe · 9 ürün

Proje üç soruyu birlikte cevaplar:

1. **Ne var?** Hangi üründen ne kadar ekiliyor, ne kadarına ihtiyaç var?
2. **Ne olabilir?** Toprak ve iklim neye izin veriyor, hangi hastalık tehdit ediyor?
3. **Ne kadar eminiz?** Bu sayılar nereden geldi, belirsizliği azaltmak için neyi ölçmek gerekir?

Üçüncüsü projenin ayırt edici yanıdır. Tarımsal karar destek sistemleri genellikle
bir sayı verir; bu motor sayının **belirsizlik aralığını**, **türeyişini** ve
**hangi ölçümün o belirsizliği en çok azaltacağını** birlikte üretir.

> **[BULGULAR.md](BULGULAR.md) — projenin ne öğrendiği.** Bu dosya yöntemi ve
> dizin yapısını anlatır; bulgular orada, her biri kaynağı ve sınırıyla
> birlikte. Belgedeki sayılar `tests/test_bulgular.py` ile koda bağlıdır:
> kod değişip belge güncellenmezse test kırılır.

---

## Hızlı başlangıç

```bash
git clone https://github.com/Hasantrgt/agromatch.git
cd agromatch

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python src/mus_panel_uret.py --hepsi
```

Son komut bütün analizleri çalıştırır ve `mus_panel.html` dosyasını üretir.
Tarayıcıda açmanız yeterlidir; dış bağlantı gerektirmez.

Panelin kaynağı `src/panel/` altında parçalıdır, çıktısı tek dosyadır. İkisi
ayrı ihtiyaç: tek dosya çıktısı panelin USB bellekten ya da e-posta ekinden
açılabilmesi için; parçalı kaynak ise 1.100 satırlık tek bir betiğe birden
fazla kişinin dokunabilmesi için.

**Depoda üretilen hiçbir dosya durmaz.** `outputs/`, paneller ve föyler
`.gitignore` içindedir ve yukarıdaki tek komutla yeniden üretilir.

### Cercospora görüntü bölümü

Hastalık sekmesindeki görüntü işleme bölümü ayrı bir adım ister, çünkü
opencv ve pillow gerektirir:

```bash
pip install -r requirements-goruntu.txt
python src/goruntu/sentetik_yaprak.py          # sentetik yaprak kümesi
python src/goruntu/cercospora_panel_veri.py    # hat aşamaları + doğrulama
python src/mus_panel_uret.py                   # paneli yeniden üret
```

Bu adım atlanırsa panel çalışır, yalnızca o bölüm boş kalır ve üretici
bunu söyler.

---

## Dizin yapısı

```
src/
  mus_profil.py        Tek veri omurgası. Bütün ölçüm, varsayım ve dağıtımlar burada.
  mus_iklim.py         Aylık sıcaklık, GDD, donsuz dönem
  mus_toprak.py        Toprak × iklim uygunluğu, gübre önerisi
  mus_hastalik.py      Hastalık risk modeli ve ilaçlama takvimi
  mus_analiz.py        Arz-ihtiyaç dengesi, yem bilançosu, fabrika kotası, ilçe karnesi
  mus_belirsizlik.py   Monte Carlo belirsizlik yayılımı ve ölçüm önceliği
  iz.py                İzlenebilir hesap grafiği (alan bağımsız kütüphane)
  mus_iz.py            Denge hesaplarının iz.py ile kurulmuş hâli
  mus_panel_uret.py    Her şeyi çalıştırır ve paneli üretir
  panel/               Panel kaynağı (parçalı)
    bas.html             başlık ve yazı tipi bağlantıları
    stil.css             bütün biçimlendirme
    govde.html           sayfa iskeleti
    js/                  sıra numarasına göre birleştirilen betikler
  goruntu/             Cercospora görüntü işleme hattı
  veri_cek/            Dış veri kaynağı araçları
tests/                 Test takımı
data/                  Girdi verisi
outputs/               Üretilen çıktılar (git'e girmez)
```

### Bağımlılık yönü

```
mus_profil  ←  mus_iklim ← mus_toprak ← mus_hastalik
            ←  mus_analiz, mus_belirsizlik, mus_iz
iz          ←  mus_iz
```

Tek yön. Analiz dosyaları hesap yapar, **veri tutmaz**. Gerçek veri geldiğinde
değişecek tek dosya `mus_profil.py`'dir; hesaplar ve panel olduğu gibi çalışır.

---

## Veri durumu — önemli

Paneldeki sayılar üç türdür ve karıştırılmamalıdır:

| Tür | Anlamı | Örnek |
|---|---|---|
| **ölçüm** | Resmî kaynakta yayımlanmış | Nüfus, hayvan varlığı, üretim, **verim**, **ekim alanı**, toprak analizleri |
| **varsayım** | Literatürden alınan katsayı | Mera verimi, hastalık eşikleri, fiyat-maliyet |
| **dağıtım** | İl toplamının ilçelere bölünmesi | İlçe nüfusu, mera alanı, ürün deseni |

**Bu tablo sabit değil; proje ilerledikçe satırlar varsayımdan ölçüme geçiyor.**
Verim bir zamanlar varsayımdı: Muş İl Tarım ve Orman Müdürlüğü'nün 2025
faaliyet raporu hem alanı hem üretimi verdiği için artık ikisinin oranı
olarak ölçülüyor. Aynı rapor ilçe hayvan dağılımını da ölçüme çevirdi.
Künyenin doğru kalmasını `tests/test_kunye_dogru.py` denetliyor — etiketler
veriyle birlikte güncellenmezse test kırılır.

**İlçe kırılımı hâlâ kısmen eksiktir.** Hayvan varlığı ilçe bazında
yayımlanıyor, ama ürün ekim alanı yalnızca il genelinde. Panel bu ayrımı
her sayıda gösterir.

Ana kaynak: T.C. Tarım ve Orman Bakanlığı — *Muş Tarımsal Yatırım Rehberi 2025*
(TÜİK 2024 verileri).

---

## Ekip çalışması

Dal açma, commit biçimi, test yazma ve neyi değiştirmeden önce sorman
gerektiği [CONTRIBUTING.md](CONTRIBUTING.md) içinde.

## Testler

```bash
pytest                    # tüm testler
pytest -v                 # ayrıntılı
pytest tests/test_iz.py   # tek dosya
```

Test takımı dört şeyi korur:

- **Saf fonksiyonlar** — puanlayıcılar, dönüşümler, sınır değerleri
- **Veri tutarlılığı** — paylar 1'e toplanıyor mu, il üretim toplamı korunuyor mu
- **Regresyon** — geliştirme sırasında bulunan hatalar bir daha geri gelmesin
- **Altın dosya** — refactor'lar çıktıyı değiştirmesin

---

## Doğrulama komutları

```bash
ruff check src tests                # biçim ve statik denetim
mypy                                # tip denetimi (çekirdek 8 modül)
pytest                              # 121 test

python src/mus_profil.py            # veri tutarlılığını denetler
python src/mus_iz.py --dogrula      # noktasal değer ile dağılım merkezi tutarlı mı
python src/mus_belirsizlik.py       # belirsizlik ve ölçüm önceliği
```

### Denge formülleri tek yerde

Altı denge sorusunun formülleri yalnızca `mus_iz.denge_grafigi()` içinde,
hesap grafiği olarak tanımlıdır. `mus_belirsizlik` oradan beslenir ve üstüne
karar katmanını kurar:

```
mus_iz (ne hesaplanıyor)  ->  mus_belirsizlik (ne anlama geliyor)
```

Bu ayrım bir refactor'la kuruldu; öncesinde iki modül aynı formülleri ayrı
ayrı tutuyordu. `tests/test_altin.py`, refactor'ın çıktıyı değiştirmediğini
kaydedilmiş bir altın dosyayla doğrular.

---

## Veri madenciliği veri seti

Görüntü hattı, bir bileşenin leke olup olmadığına elle ayarlanmış üç eşikle
karar verir (`alan`, `dairesellik`). `lezyon_veri_seti.py` aynı kararı
**öğrenilebilir** hâle getirir: segmentasyonun bulduğu her bileşen için 17
öznitelik çıkarır ve sentetik üreticinin bildiği gerçek konumlarla etiketler.

```bash
pip install -r requirements-goruntu.txt
pip install scikit-learn pandas

python src/goruntu/lezyon_veri_seti.py --yaprak 300   # data/madencilik/lezyonlar.csv
python src/goruntu/taban_model.py                     # taban modeller + kural karşılaştırması
```

Veri seti kurulurken öğrenilen şey, veri setinin kendisinden önemliydi:

**İlk sürüm %100 doğruluk verdi.** Sebebi, sentetik üreticinin lekeleri sabit
bir renkle çizmesiydi; `kırmızılık > 4.78` tek başına %99,9 doğruluk alıyordu.
Model Cercospora'yı değil, koddaki renk sabitini öğrenmişti. Üreticiye leke
rengi değişkenliği, yaprak başına ışık kaymasi ve lekeyle **aynı renkteki**
yanıltıcılar (kenar kuruması, toprak sıçraması, odunlaşmış damar) eklendi.
Bunlar `cesitlilik` parametresiyle açılır; panel hattı eski sabit üretimi
kullanmaya devam eder, böylece doğrulama sayıları sürümler arası
karşılaştırılabilir kalır.

Düzeltmeden sonra tablo anlamlı hâle geldi:

| | doğruluk | F1 |
|---|---:|---:|
| Her zaman çoğunluk | 0,49 | 0,00 |
| Elle ayarlanmış kural | 0,86 | 0,88 |
| Karar ağacı (derinlik 3) | 0,99 | 0,99 |
| Rastgele orman | 0,99 | 0,99 |

Eğitim/test ayrımı **yaprağa göre** yapılır, satıra göre değil: aynı yaprağın
bileşenleri aynı ışığı ve aynı eşiği paylaşır, satıra göre bölmek başarıyı
olduğundan yüksek gösterir.

### Toprak uygunluk veri seti

İkinci veri seti aynı mantıkla kurulur, ama farklı bir soruyu sorar.

```bash
pip install -r requirements-madencilik.txt
python src/toprak_veri_seti.py --numune 400    # data/madencilik/toprak.csv
python src/toprak_taban_model.py               # üç hedef, taban modeller
python src/toprak_gurultu_deneyi.py            # gürültü taraması + grafik
```

Her satır bir (toprak numunesi, ürün) çiftidir. Öznitelikler bir laboratuvar
raporunda yazacak **ölçülen** değerler, hedefler ise numunenin **gerçek**
değerlerinden hesaplanan uygunluk sonucudur. Arada iki katman hata vardır:
mekânsal değişkenlik (tarlanın bir noktası, kararsa bütün tarla için) ve
laboratuvar tekrarlanabilirliği.

Bu ayrım şart: öznitelik ile hedef aynı sayılardan hesaplansaydı model kuralı
ezberler ve hiçbir şey öğretmezdi. Hata katmanı sayesinde sorulabilen soru
projenin kendi sorusuyla örtüşüyor — **laboratuvar hatası ekim kararını ne
kadar bozuyor?**

Cevap: varsayılan hata düzeyinde uygunluk sınıfı satırların **%12,6**'sında,
kısıtlayıcı faktör **%16,5**'inde değişiyor.

**Burada makine öğrenmesi uzman kuralını yenemiyor** — ve bu beklenen bir
sonuçtur: etiketler zaten o kuralla üretiliyor, model onu yalnızca yaklaşık
öğrenebilir. Modelin tek üstünlüğü gürültüyü ortalayabilmesidir. İki etki ters
yönde çalışır ve `toprak_gurultu_deneyi.py` kesişimi ölçer:

| laboratuvar hatası | kuralı ölçüme uygula | rastgele orman |
|---|---:|---:|
| ×0,5 | **%90,8** | %81,6 |
| ×1,0 | **%83,4** | %78,3 |
| ×1,5 | %74,5 | **%76,4** |
| ×3,0 | %56,7 | **%67,1** |

Kesişim **×1,37**. Laboratuvar bundan iyiyse formüle güven; kötüyse öğrenmeye
geç. İki veri seti böylece zıt iki ders veriyor:

| | elle konan kural | öğrenilen model |
|---|---:|---:|
| Cercospora lezyon filtresi | %84 | **%99** |
| Toprak uygunluk (×1 hata) | **%83** | %78 |

Fark, kuralın nereden geldiğidir. Lezyon filtresindeki üç eşik denemeyle
bulunmuş tahminlerdi; toprak kuralı ise literatürden kurulmuş bir uzman
modelidir. Makine öğrenmesi, **iyi bir kuralın olmadığı yerde** kazanıyor.

---

## Yöntem notları

**Toprak × iklim geometrik ortalamayla birleşir.** Aritmetik ortalamada toprağı 98,
iklimi 46 olan bir yer 72 alıp "uygun" görünür. Geometrik ortalamada 67'ye düşer:
iki koşuldan biri diğerinin yerini tutmaz.

**Kritik toprak özellikleri tavan koyar.** Drenaj, tuzluluk ve toprak derinliği
telafi edilemez (Liebig'in minimum yasası). Kökü 120 cm'e inmesi gereken bir ürün
65 cm'lik toprakta sınırlıdır.

**Her ürün kendi ölçeğinde dengelenir.** Ürünün taşınabilirliği, dengenin hangi
coğrafyada kurulacağını belirler: kaba yem ilçe, şeker pancarı fabrika havzası,
buğday ulusal ölçekte.

**Belirsizlik üçgen dağılımla modellenir.** Sınırların dışına çıkmaz — bir verim
ya da oran negatif olamaz.

---

## Lisans ve emek

Hasan Turgut · Muş Alparslan Üniversitesi, Yazılım Mühendisliği

Kod ve çözümlemeler Claude (Anthropic) ile birlikte geliştirilmiştir; commit
geçmişinde ortak yazarlık olarak belirtilmiştir.
