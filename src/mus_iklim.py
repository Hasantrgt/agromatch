"""
AGROMATCH - Muş iklim uygunluğu
===============================
Toprak analizi tek başına yanıltıcıdır. Varto'nun toprağı ilin en iyisidir
(volkanik, drenajı iyi, organik maddesi yüksek, kireci düşük) ama 1620
metrede şeker pancarı yetişmez. Toprak "yetişebilir mi" sorusunun yarısını
cevaplar; diğer yarısı iklimdir.

Bu modül iki şeyi hesaplar:

  1. Etkili sıcaklık toplamı (GDD)  -- ürünün olgunlaşmaya yetecek sıcaklığı
                                       bulup bulamadığı
  2. Donsuz dönem                   -- dona hassas ürünün güvenli penceresi

Aylık sıcaklık, yıllık ortalamadan kosinüs mevsim eğrisiyle türetilir.
Karasal Doğu Anadolu için genlik 14 °C alınmıştır: Muş Merkez'de bu,
temmuz ~24 °C ve ocak ~-4 °C demektir ve MGM uzun yıllar ortalamasına
yakındır. Gerçek istasyon verisi geldiğinde AYLIK_SICAKLIK doğrudan
doldurulacak, eğri devre dışı kalacaktır.

    python src/mus_iklim.py
"""

import math

import mus_profil as mp

GENLIK = 14.0          # yıllık sıcaklık salınımı (°C), karasal iklim
ZIRVE_AY = 7.3         # en sıcak nokta: temmuz sonu
GUNLUK_FARK = 8.0      # gündüz-gece farkının yarısı; don riski için

AY_GUN = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
AY_AD = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
         "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

# Gerçek istasyon verisi geldiğinde buraya ilçe: [12 aylık ortalama] yazılacak.
AYLIK_SICAKLIK = {}

# ürün: (taban sıcaklık °C, gerekli GDD, don hassasiyeti 1-5,
#        serin sever mi, hedef ekim ayı)
IKLIM_ISTEK = {
    "Şeker pancarı":  (5,  1800, 3, False, 4),
    "Buğday":         (0,  1400, 1, False, 10),
    "Arpa":           (0,  1250, 1, False, 10),
    "Yonca":          (5,  1600, 2, False, 4),
    "Korunga":        (5,  1200, 1, False, 4),
    "Silajlık mısır": (10, 1350, 5, False, 5),
    "Fiğ":            (3,  1000, 2, False, 10),
    "Patates":        (7,  1050, 4, True,  5),
    "Kuru fasulye":   (10, 1100, 5, False, 5),
}


def aylik_sicaklik(ilce):
    """İlçenin 12 aylık ortalama sıcaklığı."""
    if ilce in AYLIK_SICAKLIK:
        return list(AYLIK_SICAKLIK[ilce])
    ort = mp.IKLIM[ilce][0]
    return [round(ort + GENLIK * math.cos(2 * math.pi * (ay - ZIRVE_AY) / 12), 1)
            for ay in range(1, 13)]


def gdd(ilce, taban):
    """Etkili sıcaklık toplamı: yıl boyunca tabanın üstünde geçen derece-gün."""
    return round(sum(max(0.0, t - taban) * g
                     for t, g in zip(aylik_sicaklik(ilce), AY_GUN)))


def donsuz_gun(ilce):
    """Gece minimumunun 0 °C üstünde kaldığı gün sayısı (yaklaşık).

    Gece minimumu, aylık ortalamadan GUNLUK_FARK kadar düşük varsayılır.
    Bir ay, ortalaması GUNLUK_FARK'ın üstündeyse donsuz sayılır; sınırdaki
    aylar oransal olarak hesaba katılır.
    """
    toplam = 0.0
    for t, g in zip(aylik_sicaklik(ilce), AY_GUN):
        min_sic = t - GUNLUK_FARK
        if min_sic >= 2:
            toplam += g
        elif min_sic > -2:
            toplam += g * (min_sic + 2) / 4       # geçiş ayı
    return round(toplam)


def ekim_penceresi(ilce, taban):
    """Toprağın ekim sıcaklığına ulaştığı ve düştüğü ay (ondalık)."""
    ort = mp.IKLIM[ilce][0]
    if ort + GENLIK <= taban:
        return None
    oran = (taban - ort) / GENLIK
    oran = max(-1.0, min(1.0, oran))
    acik = math.acos(oran) * 12 / (2 * math.pi)
    return round(ZIRVE_AY - acik, 1), round(ZIRVE_AY + acik, 1)


def uygunluk(ilce, urun):
    taban, gerekli, don_hassas, serin, ekim_ay = IKLIM_ISTEK[urun]
    mevcut = gdd(ilce, taban)
    pay = mevcut / gerekli if gerekli else 1.0

    # Sıcaklık yeterliliği: %135 marjda tam puan, %85'in altında sıfır
    isi_puan = max(0.0, min(100.0, (pay - 0.85) / 0.50 * 100))

    # Dona hassas ürün kısa donsuz dönemde cezalanır
    donsuz = donsuz_gun(ilce)
    gerekli_donsuz = 90 + don_hassas * 22          # hassasiyet 5 -> 200 gün
    don_puan = max(0.0, min(100.0, (donsuz - gerekli_donsuz * 0.72)
                            / (gerekli_donsuz * 0.38) * 100))

    # Serin seven ürün (patates) yaz sıcağında kalite kaybeder
    temmuz = aylik_sicaklik(ilce)[6]
    sicak_puan = 100.0
    if serin and temmuz > 22:
        sicak_puan = max(40.0, 100 - (temmuz - 22) * 18)

    puan = 0.50 * isi_puan + 0.35 * don_puan + 0.15 * sicak_puan
    pencere = ekim_penceresi(ilce, taban)

    if pay < 0.90:
        kisit = "sıcaklık toplamı yetersiz"
    elif don_puan < 60:
        kisit = "donsuz dönem kısa"
    elif sicak_puan < 80:
        kisit = "yaz sıcağı kaliteyi düşürür"
    else:
        kisit = "-"

    return dict(
        puan=round(puan, 1), gdd=mevcut, gerekli_gdd=gerekli,
        gdd_payi=round(pay, 2), donsuz_gun=donsuz,
        gerekli_donsuz=gerekli_donsuz, temmuz=temmuz,
        isi_puan=round(isi_puan, 1), don_puan=round(don_puan, 1),
        sicak_puan=round(sicak_puan, 1),
        ekim_baslangic=pencere[0] if pencere else None,
        kisit=kisit,
        sinif=("çok uygun" if puan >= 80 else "uygun" if puan >= 65
               else "sınırlı" if puan >= 50 else "uygun değil"),
    )


def ozet():
    return [dict(ilce=i, rakim=mp.ILCE[i][0], ortalama=mp.IKLIM[i][0],
                 yagis=mp.IKLIM[i][1], donsuz_gun=donsuz_gun(i),
                 aylik=aylik_sicaklik(i),
                 gdd5=gdd(i, 5), gdd10=gdd(i, 10))
            for i in mp.ILCE]


if __name__ == "__main__":
    print(f"{'İLÇE':<11}{'Rakım':>7}{'Ort.':>7}{'Donsuz':>8}{'GDD5':>7}{'GDD10':>7}")
    for r in ozet():
        print(f"{r['ilce']:<11}{r['rakim']:>7}{r['ortalama']:>7.1f}"
              f"{r['donsuz_gun']:>8}{r['gdd5']:>7}{r['gdd10']:>7}")

    print(f"\n{'ÜRÜN':<16}" + "".join(f"{i[:6]:>9}" for i in mp.ILCE))
    for urun in IKLIM_ISTEK:
        satir = "".join(f"{uygunluk(i, urun)['puan']:>9.0f}" for i in mp.ILCE)
        print(f"{urun:<16}{satir}")

    print("\nKısıtlar:")
    for urun in IKLIM_ISTEK:
        for ilce in mp.ILCE:
            u = uygunluk(ilce, urun)
            if u["puan"] < 65:
                print(f"  {ilce:<10} {urun:<16} {u['puan']:>5.0f}  {u['kisit']}")
