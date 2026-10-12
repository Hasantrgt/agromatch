"""
AGROMATCH - Mobil uygulama devir paketi
=======================================
Mobil uygulamayı yazan arkadaşın BEKLEMESİNE GEREK YOK. İhtiyacı olan şey
hastalık veri seti değil, üç şey: hastalık kataloğu, tespit algoritmasının
tarifi ve uygulamanın tutacağı kayıt şeması. Üçü de bugün hazır.

Bu script onları tek klasöre yazar:

    mobil_paket/
      hastalik_katalog.json   24 hastalık: ürün, patojen, belirti, mücadele, kritik aylar
      siddet_olcegi.json      enfekte alan yüzdesi -> seviye, ad, karar
      veri_semasi.json        uygulamanın tutacağı ve göndereceği kayıt şekilleri
      ALGORITMA.md            tespit hattının adım adım tarifi (Dart'a port için)
      OKUBENI.md              paketin ne olduğu ve ilk adımlar

Kullanım:
    python src/mobil_paket.py
"""

import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "outputs"
PAKET = KOK / "mobil_paket"

ALGORITMA = """# Cercospora tespit hattı — Dart'a port tarifi

Bu, `src/goruntu/cercospora.py` dosyasının mobil karşılığıdır. Python kodunu
okumadan da uygulayabilmen için her adım sayı sayı yazıldı. OpenCV'yi mobile
gömmene gerek yok; adımların hepsi piksel üzerinde basit işlem.

## Girdi
Kameradan gelen RGB görüntü. Genişlik 900 pikselden büyükse 900'e ölçekle
(en-boy oranını koru) — hız için.

## Adım 1 — Yaprak maskesi
Her pikseli HSV'ye çevir. Şu aralıktakiler yaprak sayılır:

    H: 22–95   (OpenCV ölçeği 0–179; Dart'ta 0–360 kullanıyorsan 44–190)
    S: 35–255
    V: 35–255

Sonra:
1. Kapama (closing) 9×9 — yaprak içindeki küçük boşlukları kapat
2. Açma (opening) 5×5 — arka plandaki serpintileri at
3. En büyük bağlı bileşeni tut, gerisini sil
4. Delikleri doldur (lekeler maskede delik olarak görünür, dolmalı)
5. Kenarı 7×7 aşındır (erode) — kenar kuruması analize girmesin

## Adım 2 — Yeşillik kanalı
Her piksel için:

    yesillik = G - (R + B) / 2

Sağlıklı doku ve damarlar yüksek değer alır, lekeler düşük. Azot sarılığı da
yüksek kalır — bu yüzden hastalıkla karışmaz. (Ölçülen tipik değerler:
sağlıklı doku 53, damar 45, sarılık 46, leke halkası −27, leke merkezi 7.)

## Adım 3 — Otsu eşikleme
Yaprak maskesi içindeki yeşillik değerlerini al. Yüzde 1 ve yüzde 99'luk
dilimlere göre 0–255 aralığına ölçekle, sonra Otsu yöntemiyle eşik bul.
Eşiğin ALTINDA kalan ve yaprak içindeki pikseller aday lekedir.

Otsu kısaca: 0–255 histogramını kur; her olası eşik için iki sınıfın
ağırlıklı varyansını hesapla; varyansı en küçük yapan eşiği seç.

## Adım 4 — Morfoloji
1. Açma 3×3 — toz zerrelerini at
2. Kapama 5×5 — leke içindeki boşlukları doldur

## Adım 5 — Bileşen analizi ve filtre
Bağlı bileşenleri bul. Her biri için:

    alan        = piksel sayısı
    cevre       = kontur uzunluğu
    dairesellik = 4 * pi * alan / (cevre * cevre)
    cap         = 2 * sqrt(alan / pi)

Kabul kuralları (parametre taramasıyla seçildi):

    alan 34 ile 1800 piksel arasında olmalı
    dairesellik en az 0.45 olmalı     (damar gölgesi gibi çizgisel izleri eler)

## Adım 6 — Sonuç
    leke_sayisi          = kabul edilen bileşen sayısı
    lezyon_alani         = kabul edilenlerin toplam piksel alanı
    enfekte_alan_yuzdesi = 100 * lezyon_alani / yaprak_alani
    ortalama_cap         = kabul edilenlerin çap ortalaması

Şiddet sınıfı için `siddet_olcegi.json` dosyasına bak: enfekte alan yüzdesini
eşiklerle karşılaştır, seviye ve karar metnini oradan al.

## Milimetre ölçümü (opsiyonel ama değerli)
Fotoğrafta bilinen boyutta bir nesne varsa (cetvel çizgisi ya da kalibrasyon
kartındaki daire), mm başına piksel hesaplanır ve çap milimetre cinsinden
raporlanır. Cercospora lekesi tipik olarak 3–5 mm'dir; bu, tespitin doğruluk
kontrolü olarak da kullanılabilir.

## Doğrulama
Masaüstü sürümü, lekelerin yeri önceden bilinen 12 sentetik görüntüde
kesinlik %100, duyarlılık %91, F1 0,953 verdi. Dart portunu aynı görüntülerle
test et: `data/sentetik/` klasöründeki dosyalar ve `gercek_degerler.json`
pakette değil ama depoda var, oradan al. Sonuç bu değerlere yakın çıkmalı.

## Sırada ne var
Bu hat yalnızca yuvarlak lekeleri sayar, hastalık AYRIMI yapmaz. Hastalığı
tanımak için CNN gerekir (TFLite). Önce bu hattı çalıştır — CNN'i Kasım'da
ekleyeceğiz.
"""

OKUBENI = """# Mobil uygulama devir paketi

Bu paket, uygulamayı yazmaya BUGÜN başlaman için yeterlidir. Veri setinin
toplanmasını bekleme.

## İçindekiler

| Dosya | Ne işe yarar |
|---|---|
| `hastalik_katalog.json` | 24 hastalık: patojen, belirti, mücadele, kritik aylar |
| `siddet_olcegi.json` | Enfekte alan yüzdesinden şiddet seviyesi ve çiftçiye verilecek karar |
| `veri_semasi.json` | Uygulamanın tutacağı ve sunucuya göndereceği kayıt şekilleri |
| `ALGORITMA.md` | Tespit hattının adım adım tarifi — Dart'a port etmek için |

## İlk sürümde ne olmalı (v0)

İnternetsiz, girişsiz, sunucusuz çalışan bir uygulama:

1. Kamera ekranı — fotoğraf çek
2. `ALGORITMA.md`'deki hattı çalıştır — leke sayısı ve enfekte alan yüzdesi
3. `siddet_olcegi.json` ile şiddet ve kararı göster
4. Kaydı telefonda sakla (`veri_semasi.json` içindeki `tespit` şekli)

Sunucu, giriş ve senkronizasyon SONRA gelecek. Şemaya uygun kaydettiğin
sürece sonradan bağlamak kolay olacak.

## Önemli kurallar

- **Model telefonda çalışacak.** Tarlada internet yok; fotoğrafı sunucuya
  gönderip sonuç bekleyen bir tasarım sahada işe yaramaz.
- **Şemayı değiştirme.** Aynı şemaya cihaz ve paneller de yazıyor. Değişiklik
  gerekiyorsa Hasan'a söyle, şemayı o yönetiyor.
- **Kimlikler uygulamada üretilir** (UUID). Sunucu daha sonra bunları olduğu
  gibi kabul edecek.

## Takıldığın yer olursa

`ALGORITMA.md` adım adım yazıldı ama Python karşılığını görmek istersen
depodaki `src/goruntu/cercospora.py` dosyasına bak — aynı sıra, aynı sabitler.
"""


def veri_semasi():
    return {
        "aciklama": "Uygulamanın tuttuğu ve sunucuya göndereceği kayıt şekilleri. "
                    "Alan adları değiştirilmemelidir: cihaz ve paneller de aynı şemayı kullanır.",
        "surum": 1,
        "parsel": {
            "id": "uuid, uygulamada üretilir",
            "ad": "çiftçinin verdiği ad, örn. 'Kumluca alt tarla'",
            "il": "metin",
            "ilce": "metin",
            "enlem": "ondalık, GPS'ten",
            "boylam": "ondalık, GPS'ten",
            "alan_dekar": "ondalık",
            "urun": "hastalik_katalog.json içindeki ürün adlarından biri",
            "ekim_tarihi": "ISO 8601 tarih, örn. 2027-04-18",
        },
        "tespit": {
            "id": "uuid",
            "parsel_id": "uuid, parsel.id",
            "zaman": "ISO 8601 tarih-saat, cihaz saati",
            "fotograf_yolu": "telefon içi dosya yolu; sunucuya ayrı yüklenir",
            "leke_sayisi": "tam sayı",
            "enfekte_alan_yuzdesi": "ondalık, 0–100",
            "ortalama_cap_piksel": "ondalık",
            "ortalama_cap_mm": "ondalık, kalibrasyon varsa; yoksa null",
            "siddet_seviyesi": "tam sayı 0–5, siddet_olcegi.json",
            "hastalik_kodu": "metin, hastalik_katalog.json içindeki kod; "
                             "v0'da sabit 'cercospora_seker_pancari'",
            "yontem": "'klasik' | 'cnn' — hangi yöntemle bulundu",
            "gonderildi": "mantıksal, sunucuya iletildi mi",
        },
        "toprak_analizi": {
            "id": "uuid",
            "parsel_id": "uuid",
            "tarih": "ISO 8601 tarih",
            "ph": "ondalık",
            "organik_madde_yuzde": "ondalık",
            "kirec_yuzde": "ondalık",
            "tuzluluk_ds_m": "ondalık",
            "fosfor_kg_da": "ondalık",
            "potasyum_kg_da": "ondalık",
            "kaynak": "'laboratuvar' | 'elle giris' | 'rapor fotografi'",
        },
        "senkronizasyon": {
            "yontem": "Uygulama çevrimdışı çalışır; internet geldiğinde "
                      "gönderilmemiş kayıtları sırayla iletir.",
            "uc_nokta": {
                "POST /parsel": "parsel kaydı",
                "POST /tespit": "tespit kaydı (fotoğraf ayrı: POST /tespit/{id}/foto)",
                "POST /toprak": "toprak analizi kaydı",
            },
            "not": "Sunucu Kasım'da yazılacak. O zamana kadar kayıtlar telefonda "
                   "birikir; şema aynı kaldığı sürece geçiş sorunsuz olur.",
        },
    }


def main():
    hastalik_yolu = CIKTI / "hastalik.json"
    cerco_yolu = CIKTI / "cercospora.json"
    if not hastalik_yolu.exists():
        print("Önce çalıştır: python src/hastalik_analiz.py")
        return

    hastalik = json.loads(hastalik_yolu.read_text(encoding="utf-8"))

    # Katalog: panelden bağımsız, sade ve uygulamaya uygun
    katalog = []
    for h in hastalik["hastalik_ozet"]:
        kod = (h["ad"] + "_" + h["urun"]).lower()
        for a, b in (("ı", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"), ("ö", "o"),
                     ("ç", "c"), (" ", "_"), ("(", ""), (")", ""), ("ü", "u")):
            kod = kod.replace(a, b)
        katalog.append(dict(kod=kod, ad=h["ad"], urun=h["urun"], patojen=h["patojen"],
                            tip=h["tip"], goruntuden_tespit=h["goruntuden"],
                            veri_seti_sinifi=h["pv_sinif"],
                            bolge_ortalama_riski=h["ortalama_risk"]))

    # Belirti ve mücadele bilgisi il kayıtlarında duruyor; ilk bulduğunu al
    detay = {}
    for il in hastalik["iller"]:
        for h in il["hastaliklar"]:
            anahtar = h["ad"] + "|" + h["urun"]
            detay.setdefault(anahtar, dict(belirti=h["belirti"], yonetim=h["yonetim"],
                                           kritik_aylar=h["kritik_aylar"]))
    for k in katalog:
        d = detay.get(k["ad"] + "|" + k["urun"], {})
        k.update(belirti=d.get("belirti", ""), mucadele=d.get("yonetim", ""),
                 kritik_aylar=d.get("kritik_aylar", []))

    PAKET.mkdir(exist_ok=True)
    (PAKET / "hastalik_katalog.json").write_text(
        json.dumps(dict(surum=1, hastalik_sayisi=len(katalog), hastaliklar=katalog),
                   ensure_ascii=False, indent=2), encoding="utf-8")

    if cerco_yolu.exists():
        cerco = json.loads(cerco_yolu.read_text(encoding="utf-8"))
        olcek = cerco["siddet_olcegi"]
        parametreler = cerco["parametreler"]
    else:
        olcek, parametreler = [], {}
    (PAKET / "siddet_olcegi.json").write_text(
        json.dumps(dict(surum=1, aciklama="Enfekte yaprak alanı yüzdesine göre şiddet.",
                        olcek=olcek, tespit_parametreleri=parametreler),
                   ensure_ascii=False, indent=2), encoding="utf-8")

    (PAKET / "veri_semasi.json").write_text(
        json.dumps(veri_semasi(), ensure_ascii=False, indent=2), encoding="utf-8")
    (PAKET / "ALGORITMA.md").write_text(ALGORITMA, encoding="utf-8")
    (PAKET / "OKUBENI.md").write_text(OKUBENI, encoding="utf-8")

    print(f"Paket hazır -> {PAKET}")
    for f in sorted(PAKET.iterdir()):
        print(f"  {f.name:<26}{f.stat().st_size // 1024 or 1:>4} KB")
    print(f"\n{len(katalog)} hastalık, {sum(1 for k in katalog if k['goruntuden_tespit'])} "
          f"tanesi görüntüden tespit edilebilir.")


if __name__ == "__main__":
    main()
