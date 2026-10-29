"""
AGROMATCH - Faydalı böcekler
=============================
Üçüncü kısmın en çok atlanan yarısı. Bir tarlada böcek demek zararlı
demek değildir: tozlaşmayı yapan da, zararlıyı baskılayan da böcektir.
"Pestisitten arındırılmış yol" lafının somut karşılığı buradadır —
çünkü o yolu yürüyen şey, ilaç değil, bu canlılardır.

Projeye kattığı şey şu: bir ilaç seçimi yalnızca zararlıyı öldürüp
öldürmediğiyle değil, BUNLARI öldürüp öldürmediğiyle de
değerlendirilmelidir. Süneye karşı atılan geniş etkili bir ilaç
Trissolcus'u da öldürürse, ertesi yıl süne daha çok olur.

ALANLAR
-------
rol          tozlayici | parazitoit | avci
hedef        baskıladığı zararlılar (tarla_zararli.py ile eşleşir)
hassasiyet   hangi etki gruplarına karşı hassas (pestisit.py ile eşleşir)
mevsim       etkin olduğu aylar
"""

from __future__ import annotations

from typing import Any

ROLLER = {
    "tozlayici": "çiçeği döller; tohum bağlamayı doğrudan belirler",
    "parazitoit": "yumurtasını zararlının içine/üstüne bırakır, larva onu yer",
    "avci": "zararlıyı doğrudan avlar ve yer",
}

FAYDALILAR: tuple[dict[str, Any], ...] = (
    {
        "ad": "Trissolcus yumurta parazitoitleri",
        "latince": "Trissolcus spp.",
        "rol": "parazitoit", "onem": 3,
        "hedef": ("Süne", "Kımıl"),
        "hassasiyet": ("piretroit", "organik_fosforlu", "neonikotinoid"),
        "mevsim": (4, 5, 6),
        "kaynak": "literatür",
        "ne_yapar": ("Sünenin yumurtasına kendi yumurtasını bırakır; "
                     "süne larvası hiç çıkmaz. Doğal parazitlenme oranı "
                     "yüksek yıllarda ilaçlamaya gerek kalmayabilir."),
        "korumak_icin": ("İlaçlama kararını yumurta parazitlenme oranına "
                         "bakarak ver; parazitlenme yüksekse ilaç zarar."),
    },
    {
        "ad": "Bal arısı", "latince": "Apis mellifera",
        "rol": "tozlayici", "onem": 3,
        "hedef": (),
        "hassasiyet": ("neonikotinoid", "piretroit", "organik_fosforlu"),
        "mevsim": (4, 5, 6, 7, 8, 9),
        "kaynak": "literatür",
        "ne_yapar": ("Korunga, fiğ ve yoncada tohum bağlamayı belirler. "
                     "Muş'ta arıcılık ayrıca başlı başına bir gelir "
                     "kalemidir — yani zarar iki yönlü."),
        "korumak_icin": ("Çiçeklenme döneminde ilaç atma; mecbursan "
                         "akşam serinliğinde ve arıya toksik olmayan "
                         "gruptan seç, arıcıyı önceden haberdar et."),
    },
    {
        "ad": "Gelin böceği", "latince": "Coccinella septempunctata",
        "rol": "avci", "onem": 2,
        "hedef": ("Hububat yaprak bitleri", "Yeşil şeftali yaprak biti",
                  "Bakla yaprak biti", "Yonca yaprak biti"),
        "hassasiyet": ("piretroit", "organik_fosforlu"),
        "mevsim": (4, 5, 6, 7, 8),
        "kaynak": "literatür",
        "ne_yapar": ("Ergin ve larvası yaprak biti yer; bir larva "
                     "gelişimi boyunca yüzlerce bit tüketir."),
        "korumak_icin": ("Yaprak bitine karşı erken ilaçlama çoğu zaman "
                         "gereksizdir; önce doğal düşman sayımı yap."),
    },
    {
        "ad": "Altın gözlü böcek", "latince": "Chrysoperla carnea",
        "rol": "avci", "onem": 2,
        "hedef": ("Hububat yaprak bitleri", "Yeşil şeftali yaprak biti",
                  "Bakla yaprak biti", "Yonca yaprak biti"),
        "hassasiyet": ("piretroit", "organik_fosforlu"),
        "mevsim": (5, 6, 7, 8),
        "kaynak": "literatür",
        "ne_yapar": "Larvası yaprak biti, tripsi ve yumurtaları avlar.",
        "korumak_icin": "Seçici ilaç ve ilaçsız şerit bırakmak popülasyonu tutar.",
    },
    {
        "ad": "Aphidius parazitoitleri", "latince": "Aphidius spp.",
        "rol": "parazitoit", "onem": 2,
        "hedef": ("Hububat yaprak bitleri", "Yeşil şeftali yaprak biti",
                  "Bakla yaprak biti", "Yonca yaprak biti"),
        "hassasiyet": ("piretroit", "organik_fosforlu", "neonikotinoid"),
        "mevsim": (5, 6, 7),
        "kaynak": "literatür",
        "ne_yapar": ("Yaprak bitinin içine yumurta bırakır; bit "
                     "şişip mumyalaşır. Mumya sayısı baskının göstergesidir."),
        "korumak_icin": "Mumyalı bit görülüyorsa ilaçlamayı ertele.",
    },
    {
        "ad": "Trichogramma yumurta parazitoitleri",
        "latince": "Trichogramma spp.",
        "rol": "parazitoit", "onem": 2,
        "hedef": ("Mısır kurdu",),
        "hassasiyet": ("piretroit", "organik_fosforlu"),
        "mevsim": (6, 7, 8),
        "kaynak": "literatür",
        "ne_yapar": ("Mısır kurdunun yumurtasını parazitler; larva sapa "
                     "hiç giremez. Salım yoluyla da kullanılır."),
        "korumak_icin": ("Yumurta döneminde geniş etkili ilaç atmak "
                         "parazitoiti de bitirir."),
    },
    {
        "ad": "Bathyplectes parazitoitleri", "latince": "Bathyplectes spp.",
        "rol": "parazitoit", "onem": 2,
        "hedef": ("Yonca hortumlu böceği",),
        "hassasiyet": ("piretroit", "organik_fosforlu"),
        "mevsim": (4, 5, 6),
        "kaynak": "literatür",
        "ne_yapar": "Yonca hortumlu böceği larvasını parazitler.",
        "korumak_icin": ("Erken biçim hem zararlıyı kırar hem parazitoiti "
                         "korur; ilaca göre açık ara üstün."),
    },
    {
        "ad": "Yer böcekleri", "latince": "Carabidae",
        "rol": "avci", "onem": 2,
        "hedef": ("Bozkurt", "Ekin kambur böceği"),
        "hassasiyet": ("organik_fosforlu", "piretroit"),
        "mevsim": (4, 5, 6, 7, 8, 9),
        "kaynak": "literatür",
        "ne_yapar": ("Toprak yüzeyinde gezer, larva ve yumurta yer. "
                     "Toprak işlemenin azaldığı tarlalarda artar."),
        "korumak_icin": "Toprağa uygulanan geniş etkili ilaçlardan kaçın.",
    },
)


def hedefe_gore(zararli: str) -> list[dict[str, Any]]:
    return [f for f in FAYDALILAR if zararli in f["hedef"]]


def gruba_hassas(grup: str) -> list[str]:
    return [f["ad"] for f in FAYDALILAR if grup in f["hassasiyet"]]


def ozet() -> dict[str, Any]:
    from collections import Counter
    return {
        "toplam": len(FAYDALILAR),
        "rol": dict(Counter(f["rol"] for f in FAYDALILAR)),
        "korumasiz_zararli": [],   # tarla_zararli ile çapraz denetimde dolar
    }


def denetle(zararli_adlari: set[str] | None = None) -> list[str]:
    hata = []
    for f in FAYDALILAR:
        if f["rol"] not in ROLLER:
            hata.append(f'{f["ad"]}: bilinmeyen rol {f["rol"]}')
        if f["rol"] != "tozlayici" and not f["hedef"]:
            hata.append(f'{f["ad"]}: avcı/parazitoit ama hedefi yok')
        if not f["hassasiyet"]:
            hata.append(f'{f["ad"]}: hassasiyet listesi boş')
        if zararli_adlari is not None:
            for h in f["hedef"]:
                if h not in zararli_adlari:
                    hata.append(f'{f["ad"]}: katalogda olmayan hedef "{h}"')
    return hata


if __name__ == "__main__":
    import tarla_zararli as tz
    for h in denetle({z["ad"] for z in tz.ZARARLILAR}):
        print("HATA:", h)
    o = ozet()
    print(f"{o['toplam']} faydalı")
    for r, n in o["rol"].items():
        print(f"  {r:12s} {n}   {ROLLER[r]}")
    print("\nDoğal düşmanı YAZILMAMIŞ zararlılar:")
    for z in tz.ZARARLILAR:
        if not hedefe_gore(z["ad"]):
            print(f'  {z["ad"]} ({"/".join(z["urunler"])})')
