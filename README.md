# AGROMATCH — Muş Tarım Planlama Motoru

<!-- Depoyu GitHub'a gönderdikten sonra <kullanıcı> yerine kendi adını yaz -->
[![Testler](https://github.com/KULLANICI/agromatch/actions/workflows/test.yml/badge.svg)](https://github.com/KULLANICI/agromatch/actions/workflows/test.yml)
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

---

## Hızlı başlangıç

```bash
git clone https://github.com/KULLANICI/agromatch.git
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
| **ölçüm** | Resmî kaynakta yayımlanmış | Nüfus, hayvan varlığı, ürün üretim miktarı |
| **varsayım** | Literatürden alınan katsayı | Verim, mera verimi, hastalık eşikleri |
| **dağıtım** | İl toplamının ilçelere bölünmesi | Bütün ilçe sayıları |

**Resmî kaynakta Muş için ilçe kırılımı yoktur.** İl toplamları gerçek, ilçe
dağılımı tahmindir. Panel bu ayrımı her sayıda gösterir.

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
