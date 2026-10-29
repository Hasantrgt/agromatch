"""
AGROMATCH - Yayınlanmış doz–cevap verisi (Sitophilus granarius × diyatomit)
===========================================================================
Buradaki her sayı BASILI BİR YAYINDAN alınmıştır; hiçbiri üretilmemiştir.
Yayınlar yüzde olarak ölüm bildiriyor, bizim araç tam sayı (ölen/denenen)
istiyor. Çevirim ``olen = round(yuzde/100 * denenen)`` ile yapılıyor ve
yuvarlama hatası birey başına ±0,5'tir — bu, kaydın kendi alanında yazılı.

NEDEN ÖNEMLİ
------------
Projenin doz–cevap aracı şimdiye kadar sentetik veriyle gösteriliyordu.
Sentetik veri aracın çalıştığını kanıtlar ama hiçbir şey öğretmez. Bu iki
yayın aynı türü, aynı etken maddeyi, hatta bir tanesinde aynı ticari ürünü
farklı sıcaklık ve nemde ölçmüş. Yan yana konduklarında ortaya Muş için
doğrudan sonuç veren bir karşıtlık çıkıyor (bkz. ``sicaklik_karsitligi``).

LİSANS
------
İki yayın da MDPI/Insects dergisinde açık erişim ve CC BY 4.0 lisanslı;
veri, kaynak gösterilerek kullanılabilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from depo.doz_cevap import Gozlem

# ---------------------------------------------------------------- yayınlar


@dataclass(frozen=True)
class Calisma:
    kod: str
    yazarlar: str
    yil: int
    baslik: str
    dergi: str
    doi: str
    sicaklik: float          # °C
    nem: float               # % bağıl nem
    urun: str
    birey_basina_kap: int
    tekrar: int
    kontrol_notu: str
    abbott: bool             # yayın Abbott düzeltmesi uygulamış mı
    not_: str

    @property
    def n_hucre(self) -> int:
        """Bir doz × süre hücresindeki toplam birey."""
        return self.birey_basina_kap * self.tekrar


CALISMALAR: dict[str, Calisma] = {
    "agrafioti2023": Calisma(
        kod="agrafioti2023",
        yazarlar=("Agrafioti, P.; Vrontaki, M.; Rigopoulou, M.; Lampiri, E.; "
                  "Grigoriadou, K.; Ioannidis, P.M.; Rumbos, C.I.; "
                  "Athanassiou, C.G."),
        yil=2023,
        baslik=("Insecticidal Effect of Diatomaceous Earth Formulations for "
                "the Control of a Wide Range of Stored-Product Beetle Species"),
        dergi="Insects 14(7), 656",
        doi="10.3390/insects14070656",
        sicaklik=26.0, nem=55.0, urun="yumuşak buğday",
        birey_basina_kap=20, tekrar=9,
        kontrol_notu="kontrol ölümü her durumda %2'nin altında kalmış",
        abbott=False,
        not_=("Aynı kaplar 3, 7, 14 ve 21. günlerde tekrar sayılmış "
              "(tekrarlı ölçüm). Bu yüzden süreler BAĞIMSIZ örnek değildir; "
              "her süre AYRI uyduruluyor, hiçbir zaman birleştirilmiyor."),
    ),
    "ogreten2025": Calisma(
        kod="ogreten2025",
        yazarlar=("Öğreten, A.; Eren, S.; Mutlu, Ç.; Ayaz, T.; Saeed, A.; "
                  "Bingham, G.V.; Morrison, W.R."),
        yil=2025,
        baslik=("Insecticidal Effects of Native Raw and Commercial "
                "Diatomaceous Earth Against Lesser Grain Borer and Granary "
                "Weevil Under Different Environmental Conditions"),
        dergi="Insects 16(6), 549",
        doi="10.3390/insects16060549",
        sicaklik=30.0, nem=40.0, urun="Pehlivan ekmeklik buğday",
        birey_basina_kap=30, tekrar=10,
        kontrol_notu="ölümler Abbott formülüyle düzeltilmiş",
        abbott=True,
        not_=("TAGEM BS-13/12-01/01-01 projesi; Diyarbakır Zirai Mücadele "
              "Araştırma Enstitüsü. Aydın ve Ankara YERLİ diyatomitleri. "
              "Yayın metninde yalnızca 1000 ppm'in sayıları açık yazılı; "
              "ara dozlar yalnızca şekilde verildiği için buraya ALINMADI."),
    ),
}

# ------------------------------------------------------------- ölçümler
# (calisma, formulasyon, doz_ppm, sure_gun, olum_yuzdesi)
# Agrafioti 2023 — Çizelge 5, Sitophilus granarius, 26 °C / %55 nem
# Öğreten  2025 — Şekil 4 anlatımı, 30 °C / %40 nem, yalnızca 1000 ppm

OLCUMLER: tuple[tuple[str, str, float, float, float], ...] = (
    # --- Agrafioti 2023 · Silicid (>%99 SiO2)
    ("agrafioti2023", "Silicid", 100, 3, 2.7),
    ("agrafioti2023", "Silicid", 300, 3, 10.0),
    ("agrafioti2023", "Silicid", 500, 3, 12.2),
    ("agrafioti2023", "Silicid", 1000, 3, 23.8),
    ("agrafioti2023", "Silicid", 100, 7, 3.9),
    ("agrafioti2023", "Silicid", 300, 7, 9.4),
    ("agrafioti2023", "Silicid", 500, 7, 12.7),
    ("agrafioti2023", "Silicid", 1000, 7, 42.7),
    ("agrafioti2023", "Silicid", 100, 14, 4.4),
    ("agrafioti2023", "Silicid", 300, 14, 10.5),
    ("agrafioti2023", "Silicid", 500, 14, 26.1),
    ("agrafioti2023", "Silicid", 1000, 14, 93.9),
    ("agrafioti2023", "Silicid", 100, 21, 5.0),
    ("agrafioti2023", "Silicid", 300, 21, 16.6),
    ("agrafioti2023", "Silicid", 500, 21, 78.3),
    ("agrafioti2023", "Silicid", 1000, 21, 100.0),
    # --- Agrafioti 2023 · Celatom MN-23 (%83,7 SiO2)
    ("agrafioti2023", "Celatom MN-23", 100, 3, 2.2),
    ("agrafioti2023", "Celatom MN-23", 300, 3, 1.6),
    ("agrafioti2023", "Celatom MN-23", 500, 3, 2.7),
    ("agrafioti2023", "Celatom MN-23", 1000, 3, 5.0),
    ("agrafioti2023", "Celatom MN-23", 100, 7, 2.7),
    ("agrafioti2023", "Celatom MN-23", 300, 7, 2.7),
    ("agrafioti2023", "Celatom MN-23", 500, 7, 3.9),
    ("agrafioti2023", "Celatom MN-23", 1000, 7, 6.1),
    ("agrafioti2023", "Celatom MN-23", 100, 14, 3.3),
    ("agrafioti2023", "Celatom MN-23", 300, 14, 3.9),
    ("agrafioti2023", "Celatom MN-23", 500, 14, 6.1),
    ("agrafioti2023", "Celatom MN-23", 1000, 14, 14.4),
    ("agrafioti2023", "Celatom MN-23", 100, 21, 2.7),
    ("agrafioti2023", "Celatom MN-23", 300, 21, 5.0),
    ("agrafioti2023", "Celatom MN-23", 500, 21, 13.9),
    ("agrafioti2023", "Celatom MN-23", 1000, 21, 73.3),
    # --- Agrafioti 2023 · SilicoSec (%90 SiO2)
    ("agrafioti2023", "SilicoSec", 100, 3, 1.1),
    ("agrafioti2023", "SilicoSec", 300, 3, 2.7),
    ("agrafioti2023", "SilicoSec", 500, 3, 1.6),
    ("agrafioti2023", "SilicoSec", 1000, 3, 0.6),
    ("agrafioti2023", "SilicoSec", 100, 7, 1.6),
    ("agrafioti2023", "SilicoSec", 300, 7, 3.3),
    ("agrafioti2023", "SilicoSec", 500, 7, 2.2),
    ("agrafioti2023", "SilicoSec", 1000, 7, 2.2),
    ("agrafioti2023", "SilicoSec", 100, 14, 2.7),
    ("agrafioti2023", "SilicoSec", 300, 14, 6.1),
    ("agrafioti2023", "SilicoSec", 500, 14, 22.2),
    ("agrafioti2023", "SilicoSec", 1000, 14, 64.4),
    ("agrafioti2023", "SilicoSec", 100, 21, 2.7),
    ("agrafioti2023", "SilicoSec", 300, 21, 10.5),
    ("agrafioti2023", "SilicoSec", 500, 21, 63.3),
    ("agrafioti2023", "SilicoSec", 1000, 21, 99.4),
    # --- Öğreten 2025 · yalnızca 1000 ppm, 30 °C / %40 nem
    ("ogreten2025", "Ankara (yerli)", 1000, 7, 70.0),
    ("ogreten2025", "Ankara (yerli)", 1000, 14, 74.0),
    ("ogreten2025", "Ankara (yerli)", 1000, 21, 100.0),
    ("ogreten2025", "Aydın (yerli)", 1000, 7, 86.0),
    ("ogreten2025", "Aydın (yerli)", 1000, 14, 91.0),
    ("ogreten2025", "Aydın (yerli)", 1000, 21, 100.0),
    ("ogreten2025", "SilicoSec", 1000, 7, 83.0),
    ("ogreten2025", "SilicoSec", 1000, 14, 88.0),
    ("ogreten2025", "SilicoSec", 1000, 21, 100.0),
)


def gozlemler(calisma: str, formulasyon: str, sure: float) -> list[Gozlem]:
    """Bir yayın × ürün × süre için doz serisini Gozlem listesine çevirir.

    Yayın yüzde veriyor; tam sayıya çeviriyoruz. Tek bir "tekrar" olarak
    veriliyor çünkü yayın tekrar tekrar ayrışmış sayıları yayımlamamış —
    elimizdeki, dokuz (ya da on) kabın ortalaması.
    """
    c = CALISMALAR[calisma]
    n = c.n_hucre
    return [Gozlem(doz=doz, sure=sure, denenen=n,
                   olen=round(yuzde / 100 * n),
                   sicaklik=c.sicaklik, nem=c.nem,
                   tekrar=f"{calisma}:{formulasyon}")
            for k, f, doz, s, yuzde in OLCUMLER
            if k == calisma and f == formulasyon and s == sure]


def seriler() -> list[tuple[str, str, float, int]]:
    """Hangi yayın × ürün × süre kombinasyonunda kaç doz var."""
    sayac: dict[tuple[str, str, float], int] = {}
    for k, f, _doz, s, _y in OLCUMLER:
        sayac[(k, f, s)] = sayac.get((k, f, s), 0) + 1
    return [(k, f, s, n) for (k, f, s), n in sorted(sayac.items())]


def sicaklik_karsitligi() -> dict[str, Any]:
    """İki yayının ÇAKIŞTIĞI tek noktayı bulur ve farkı döndürür.

    SilicoSec, Sitophilus granarius, 1000 ppm, 7 gün — her iki yayında da
    var. Tek değişen sıcaklık ve nem. Aradaki fark, diyatomitin ortam
    koşullarına ne kadar bağlı olduğunun en temiz kanıtı ve bu projenin
    Muş'a dair çıkarımının dayanağı.
    """
    def bul(calisma: str) -> float:
        for k, f, doz, s, y in OLCUMLER:
            if k == calisma and f == "SilicoSec" and doz == 1000 and s == 7:
                return y
        raise LookupError(f"{calisma} içinde SilicoSec 1000 ppm / 7 gün yok")

    soguk, sicak = bul("agrafioti2023"), bul("ogreten2025")
    a, o = CALISMALAR["agrafioti2023"], CALISMALAR["ogreten2025"]
    return {
        "urun": "SilicoSec", "doz": 1000, "sure": 7,
        "dusuk": {"olum": soguk, "sicaklik": a.sicaklik, "nem": a.nem,
                  "kaynak": a.kod},
        "yuksek": {"olum": sicak, "sicaklik": o.sicaklik, "nem": o.nem,
                   "kaynak": o.kod},
        "kat": round(sicak / soguk, 1) if soguk else None,
    }


def ozet() -> dict[str, Any]:
    return {
        "yayin": len(CALISMALAR),
        "olcum": len(OLCUMLER),
        "birey": sum(CALISMALAR[k].n_hucre for k, *_ in OLCUMLER),
        "seri": len(seriler()),
        "doz_serisi": sum(1 for *_, n in seriler() if n >= 3),
    }


if __name__ == "__main__":
    o = ozet()
    print(f"{o['yayin']} yayın · {o['olcum']} ölçüm · {o['birey']:,} birey")
    print(f"{o['seri']} seri, bunların {o['doz_serisi']} tanesi uydurulabilir "
          f"(>=3 doz)")
    k = sicaklik_karsitligi()
    print(f"\nSıcaklık karşıtlığı — {k['urun']} {k['doz']} ppm, {k['sure']} gün:")
    print(f"  {k['dusuk']['sicaklik']} °C / %{k['dusuk']['nem']} nem "
          f"-> %{k['dusuk']['olum']} ölüm")
    print(f"  {k['yuksek']['sicaklik']} °C / %{k['yuksek']['nem']} nem "
          f"-> %{k['yuksek']['olum']} ölüm   ({k['kat']} kat)")
