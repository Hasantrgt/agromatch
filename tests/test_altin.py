"""
Altın dosya testi — refactor sırasında sayılar değişmedi mi?

tests/altin/belirsizlik.json, iki hesap yolunu teke indirme refactor'ından
ÖNCE kaydedildi. O refactor'da mus_belirsizlik.py kendi denge formüllerini
bırakıp mus_iz.denge_grafigi()'nden beslenmeye başladı.

Böyle bir değişiklikte tek güvence, çıktının aynı kalmasıdır. Kod tamamen
değişti ama sayılar değişmemeli — değiştiyse refactor sırasında bir şey
bozulmuş demektir.

ALTIN DOSYA NE ZAMAN GÜNCELLENİR
--------------------------------
Yalnızca bir MODEL değişikliği bilerek yapıldığında ve yeni sayının neden
doğru olduğu gerekçelendirildiğinde. Test kırıldı diye altın dosyayı
yenilemek, testin varlık sebebini ortadan kaldırır.

GÜNCELLEME KAYDI
----------------
Kasım 2026 — laboratuvar ölçümlerinin bağlanması. Muş İl Tarım ve Orman
Müdürlüğü'nün 2011-2015 analiz kayıtları (2.622 örnek) modele bağlandı ve
ilçe toprak değerleri varsayım olmaktan çıktı. Dört sayı değişti:

    Patates      eylem        fırsat   -> gerek yok
    Patates      yeri_onemli  True     -> False
    Patates      makas        16,9     -> 11,3
    Kuru fasulye makas        15,0     -> 17,1

NEDEN DOĞRU: makas, en iyi ilçe ile ikincisi arasındaki uygunluk farkıdır
ve "nerede ektiğin önemli mi" sorusunu o belirler. Ölçülen Muş toprakları
varsaydığımızdan daha TEKDÜZE çıktı (özellikle kireç: varsayım %9-13,
ölçüm %1,3-2,7). Toprak ilçeler arasında daha az ayrım yapınca patatesin
Varto'daki üstünlüğü 16,9 puandan 11,3'e indi ve eşiğin altına düştü.
Sistem artık "patates için yer seçimi fırsatı var" demiyor.

Bu bir bozulma değil, DÜZELTMEDİR: eski tavsiye varsayılmış bir toprak
farkına dayanıyordu.

Kasım 2026 (dördüncü güncelleme) — BELİRSİZLİK MODELİ ÖLÇÜMLERİ TAKİP
ETMEMİŞ. Proje üç kalemi ölçtü ama belirsizlik modeli onları hâlâ
belirsiz sayıyordu, dolayısıyla "önce neyi ölçmeli" sıralaması yanlış
şeyleri gösteriyordu:

  Buğday üretimi: alt sınırı 244.000 tondu ve gerekçesi belgenin
      "115 bin ha" ifadesiydi. O ifade çürütüldü (hiçbir yılı tutmuyor),
      dolayısıyla alt sınırın dayanağı kalmadı. Aralık ±%5'e indi.
  Fiğ ve kuru fasulye üretimi: "resmî tabloda ayrı kalem değil, tamamen
      tahmin" deniyordu. Artık ayrı kalem. Kalan pay ölçüm payı değil,
      yıllar arası oynaklık — fiğ 2023'te 41.648, 2024'te 1.839 ton.
  Yem bitkisi çarpanı: belgenin kendi çelişkisine dayanıyordu; rapor
      yoncayı, korungayı ve silajı ayrı verince çelişki daraldı.

ANLAMLI SONUÇ: buğdayın baskın bilinmeyeni DEĞİŞTİ.

    "Buğday üretimi"  ->  "Kişi başı yıllık buğday"

Üretim netleşince darboğaz tüketime kaydı. Bir belirsizlik analizinin
işi tam olarak budur: ölçüm yapıldıkça sıranın değişmesi gerekir. Eski
sıra donmuş kalsaydı, proje zaten bildiği bir şeyi ölçmeye çalışırdı.

Bu güncelleme SAHA ÇALIŞMASI YAPILAMAYACAĞI netleştiği için ayrıca
önemli: kalan en yüksek kazançlı dört iş de masa başı (TÜİK tüketim
tabloları ve fabrika telefonu). Masa başı kazanç 28,8, saha kazancı 7,6.


Kasım 2026 (üçüncü güncelleme) — ÜÇ TAHMİNİN VE BİR ÇELİŞKİNİN KAPANMASI.
Aynı faaliyet raporu, projenin kendi notlarında zaten eksik işaretlediği
kalemleri kapattı:

    patates       4.087 ton (TÜİK 2021, "güncel yıl belgede yok") -> 5.826
    fiğ          25.000 ton ("TAHMİN — belgede ayrı kalem yok")   -> 1.839
    kuru fasulye  1.200 ton ("TAHMİN")                            ->   396

Bunlar uyuşmazlık değildi; projenin kendi kabul ettiği boşluklardı.

Buğday/arpa çelişkisi de çözüldü. Projenin buğday verimi (0,32) bağımsız
bir varsayım değil, başka bir belgenin "115 bin ha" ifadesinden geriye
hesaplanmıştı. O ifade NE 2023'ü (141.467 ha) NE 2024'ü (135.197 ha)
tutuyor. Faaliyet raporu ise alanı ve üretimi aynı yıl, aynı kayıttan
veriyor ve ima ettiği verim (0,272) susuz Muş buğdayı için 0,320'den
makul. İçsel tutarlılığı olan kaynak seçildi.

DOĞRULAMA: artık dokuz ürünün dokuzunda da "üretim ÷ verim", raporun
ÖLÇÜLMÜŞ alanını %1 içinde yeniden üretiyor. Proje ekim alanlarını
varsayımdan değil ölçümden türetiyor.

Değişen sayılar:

    Kaba yem oranı         0,48   ->  0,489
    Patates oranı          0,12   ->  0,17    (eski üretim 2021'di)
    Kuru fasulye oranı     0,329  ->  0,111   (eski üretim tahmindi)
    acik_ton             607.772  -> 597.915
    sadece_ekimle_dekar  1.257.676 -> 1.237.279
    bugday_payi            109,3  ->  91,4
    kat                      4,8  ->    5,0
    masa_basi_kazanc        33,0  ->   30,2

bugday_payi'nin düşmesi iyileşme DEĞİL: buğday alanı 1.151.000'den
1.354.000 dekara çıktığı için aynı gereksinim daha küçük bir paya denk
geliyor. Açık hâlâ buğday alanının %91'i kadar yem alanı istiyor.

YAN BULGU: Hasköy'ün yem karşılama oranı 1,008'e çıktı — ilçe artık
kendi ihtiyacından fazla üretiyor. "Her ilçede açık vardır" varsayan
regresyon testi bu yüzden güncellendi; varsayım veriyle çürütüldü.


Kasım 2026 (ikinci güncelleme) — yem bitkisi veriminin ÖLÇÜLMESİ. Muş
İl Tarım ve Orman Müdürlüğü'nün 2025 faaliyet raporu hem alan hem üretim
veriyor, dolayısıyla verim ikisinin oranı olarak ölçülebiliyor. Projenin
yonca verimi 3,80 ton/da VARSAYIMDI; ölçülen 1,933. Korunga 1,50 -> 0,787,
silajlık mısır 4,00 -> 5,27. Üretim rakamlarımız raporla birebir aynı,
yani ayrışan tek şey verim.

Değişen dört sayı:

    acik_ton             609.828  ->   607.772
    sadece_ekimle_dekar  641.924  -> 1.257.676
    bugday_payi             55,8  ->     109,3
    kat                      4,3  ->       4,8
    masa_basi_kazanc        33,8  ->      33,0

NEDEN DOĞRU: Yonca verimi yarıya inince, aynı açığı kapatmak için gereken
alan ikiye katlanıyor. Bu bir bozulma değil, varsayımın şişirdiği bir
sayının gerçek değerine inmesidir.

NE ANLAMA GELİYOR: bugday_payi'nin 100'ü aşması, açığı YALNIZCA ekimle
kapatmanın il genelinde buğday alanının TAMAMINDAN fazlasını gerektirdiğini
söylüyor. İlçe düzeyinde de aynı: Merkez için gereken 735.062 dekar, oysa
ilçenin bütün ekili alanı 485.571 dekar. Yani "şu kadar yonca ekin"
tavsiyesi Merkez'de fiziksel olarak imkânsız. Panel artık bunu sayıyla
geçiştirmiyor, açıkça yazıyor.

Bu, projenin verdiği tavsiyeyi değiştiren bir düzeltmedir: açık ekimle
kapatılamıyorsa hedef onu küçültmek olmalı, sıfırlamak değil.
 Değişikliğin tamamı src/toprak_olcum/etki.py ile
ölçülebilir; ilçe×ürün puanlarında ortalama mutlak fark 1,63 puan, ama 45
satırın 7'sinde uygunluk SINIFI değişti.
"""

import json
from pathlib import Path

import pytest

import mus_belirsizlik

ALTIN = json.loads(
    (Path(__file__).parent / "altin" / "belirsizlik.json").read_text(encoding="utf-8"))

# Monte Carlo gürültüsü: aynı tohumla aynı örnek çekilse de grafik üzerinden
# hesaplanan dallar farklı sırada örneklendiği için küçük sapma olabilir.
TOLERANS = 0.02


@pytest.fixture(scope="module")
def sonuc():
    return mus_belirsizlik.analiz(n=20000)


def test_ayni_denge_sorulari(sonuc):
    assert [q["anahtar"] for q in sonuc["sorular"]] == \
           [q["anahtar"] for q in ALTIN["sorular"]]


@pytest.mark.parametrize("anahtar", [q["anahtar"] for q in ALTIN["sorular"]])
def test_denge_oranlari_degismedi(sonuc, anahtar):
    yeni = next(q for q in sonuc["sorular"] if q["anahtar"] == anahtar)
    eski = next(q for q in ALTIN["sorular"] if q["anahtar"] == anahtar)

    for alan in ("medyan", "alt90", "ust90"):
        assert yeni["oran"][alan] == pytest.approx(eski["oran"][alan], rel=TOLERANS), (
            f"{anahtar}.{alan}: {yeni['oran'][alan]} != {eski['oran'][alan]}")

    assert yeni["karar"] == eski["karar"]
    assert yeni["esigi_kesiyor"] == eski["esigi_kesiyor"]
    assert yeni["olcek"] == eski["olcek"]


@pytest.mark.parametrize("anahtar", [q["anahtar"] for q in ALTIN["sorular"]])
def test_arz_ve_ihtiyac_degismedi(sonuc, anahtar):
    yeni = next(q for q in sonuc["sorular"] if q["anahtar"] == anahtar)
    eski = next(q for q in ALTIN["sorular"] if q["anahtar"] == anahtar)
    assert yeni["arz_medyan"] == pytest.approx(eski["arz_medyan"], rel=TOLERANS)
    assert yeni["ihtiyac_medyan"] == pytest.approx(eski["ihtiyac_medyan"], rel=TOLERANS)


@pytest.mark.parametrize("anahtar", [q["anahtar"] for q in ALTIN["sorular"]])
def test_baskin_bilinmeyen_ayni(sonuc, anahtar):
    """Baskın bilinmeyen değişmemeli.

    Etiketlerde bilinçli bir fark var: refactor'da birim, etiketin içinden
    çıkıp kendi alanına taşındı ("Mera verimi (ton KM/da)" -> "Mera verimi"
    + birim="ton KM/dekar"). Kimliğin korunduğunu, eski etiketin yenisiyle
    başlamasına bakarak doğruluyoruz.
    """
    yeni = next(q for q in sonuc["sorular"] if q["anahtar"] == anahtar)
    eski = next(q for q in ALTIN["sorular"] if q["anahtar"] == anahtar)

    if eski["baskin"] is None:
        assert yeni["baskin"] is None
        return

    assert eski["baskin"].startswith(yeni["baskin"]["etiket"]), (
        f"{anahtar}: baskın bilinmeyen değişmiş — "
        f"eski '{eski['baskin']}', yeni '{yeni['baskin']['etiket']}'")
    assert yeni["baskin"]["varyans_payi"] == pytest.approx(
        eski["baskin_pay"], abs=3.0)


def test_belirsiz_kalan_karar_ayni(sonuc):
    assert sonuc["belirsiz_karar"] == ALTIN["belirsiz_karar"]


def test_eylem_tablosu_degismedi(sonuc):
    yeni = {r["urun"]: r for r in sonuc["karar"]}
    for eski in ALTIN["karar"]:
        y = yeni[eski["urun"]]
        assert y["eylem"] == eski["eylem"], f"{eski['urun']}: eylem değişmiş"
        assert y["olcek"] == eski["olcek"]
        assert y["oran"] == pytest.approx(eski["oran"], rel=TOLERANS)
        assert y["en_iyi_ilce"] == eski["en_iyi_ilce"]
        assert y["makas"] == pytest.approx(eski["makas"], abs=0.5)
        assert y["yeri_onemli"] == eski["yeri_onemli"]


def test_kaldirac_degismedi(sonuc):
    for alan, deger in ALTIN["kaldirac"].items():
        assert sonuc["kaldirac"][alan] == pytest.approx(deger, rel=TOLERANS), alan


def test_olcum_kazanclari_degismedi(sonuc):
    assert sonuc["masa_basi_kazanc"] == pytest.approx(
        ALTIN["masa_basi_kazanc"], rel=0.10)
    assert sonuc["saha_kazanc"] == pytest.approx(ALTIN["saha_kazanc"], rel=0.10)


# ---------------------------------------------------------------------
#  Refactor'ın asıl kazancı: tek tanım
# ---------------------------------------------------------------------
def test_denge_formulleri_tek_yerde():
    """mus_belirsizlik artık kendi denge formüllerini tutmamalı.

    Bu test bir sayıyı değil, bir MİMARİ KARARI korur: formüllerin ikinci
    bir kopyası geri gelirse kırılır.
    """
    kaynak = (Path(__file__).parent.parent / "src" / "mus_belirsizlik.py"
              ).read_text(encoding="utf-8")
    for yasak in ("def denge_kaba_yem", "def denge_pancar", "def denge_bugday",
                  "def ornekle(", "def s1_indisi(", "GIRDI = {", "SORU = {"):
        assert yasak not in kaynak, (
            f"denge formülü / örnekleme kopyası geri gelmiş: {yasak}")


def test_belirsizlik_grafikten_besleniyor():
    kaynak = (Path(__file__).parent.parent / "src" / "mus_belirsizlik.py"
              ).read_text(encoding="utf-8")
    assert "mus_iz.denge_grafigi()" in kaynak
