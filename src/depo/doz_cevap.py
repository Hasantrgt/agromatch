"""
AGROMATCH - Doz–cevap analizi (probit)
=======================================
Bir mücadele denemesinin ham sayımlarından öldürücü doz ve süreyi kestirir.

GİRDİ — denemenin ham hâli, ortalaması değil
Her satır bir kaptaki bir tekrardır:

    doz      uygulanan miktar (ppm, g/kg, ne kullanılıyorsa)
    sure     maruz kalma süresi (gün)
    denenen  kaba konan birey sayısı
    olen     süre sonunda ölü sayılan birey
    (sicaklik, nem, tekrar — isteğe bağlı, kayıt için)

Ortalama yüzdelerle çalışmak bilgi kaybettirir: 10 bireyin 9'u ile 100
bireyin 90'ı aynı yüzdedir ama ikincisinin belirsizliği çok daha dardır.
Probit modeli bunu kendiliğinden hesaba katar.

ÇIKTI
    LC50 / LC90   belirtilen sürede %50 ve %90 ölüm veren doz
    LT50 / LT90   belirtilen dozda %50 ve %90 ölüm veren süre
    eğim          doz iki katına çıkınca ölüm kaç kat artıyor
    güven aralığı Fieller yöntemiyle

NEDEN PROBİT
Ölüm oranı doza doğrusal bağlı değildir; S eğrisi çizer. Probit, bu eğriyi
log-doz ekseninde doğruya çeviren standart dönüşümdür ve toksikolojinin
ortak dilidir — hocanın literatürde okuduğu LC50 değerleri bu yöntemle
üretilmiştir. Lojistik de kullanılabilir (neredeyse aynı sonucu verir);
karşılaştırma için ikisi de hesaplanır.

ABBOTT DÜZELTMESİ
Kontrol grubunda da ölüm olur (taşıma, yaşlanma). Uygulamanın kendi etkisini
görmek için ölüm oranı kontrole göre düzeltilir:

    düzeltilmiş = (uygulama − kontrol) / (1 − kontrol)

Kontrol ölümü %20'yi aşarsa deneme şüphelidir; kod uyarır.

SINIR — bu bir ilaç tavsiyesi değildir
Bu modül bir denemenin sonucunu ÖZETLER. Hangi ürünün hangi dozda
kullanılacağı reçete yazma yetkisi olan kişilerin kararıdır. Çıktılar
araştırma ve planlama içindir.

Kullanım:
    python src/depo/doz_cevap.py --ornek      # sentetik veriyle gösterim
    python src/depo/doz_cevap.py --veri deneme.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import warnings
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import statsmodels.api as sm
from scipy import stats

KOK = Path(__file__).resolve().parent.parent.parent

# Kontrol ölümü bu oranı aşarsa deneme güvenilmez sayılır (Abbott geleneği)
KONTROL_UYARI = 0.20


@dataclass
class Gozlem:
    """Tek bir kaptaki tek bir tekrar."""
    doz: float
    sure: float
    denenen: int
    olen: int
    sicaklik: float | None = None
    nem: float | None = None
    tekrar: str = ""

    @property
    def oran(self) -> float:
        return self.olen / self.denenen if self.denenen else 0.0


@dataclass
class Uyum:
    """Bir doz–cevap uyumunun sonucu."""
    baglanti: str                 # "probit" ya da "lojistik"
    kesim: float                  # a
    egim: float                   # b  (log10 doz başına)
    n_gozlem: int
    n_birey: int
    kontrol_olumu: float
    # Her LC kaydı ya {'deger', 'alt', 'ust'} sayılarını ya da
    # {'kestirilemedi': sebep} metnini taşır; bu yüzden değer tipi Any.
    lc: dict[str, dict[str, Any]] = field(default_factory=dict)
    uyari: list[str] = field(default_factory=list)

    @property
    def iki_kat_etkisi(self) -> float:
        """Doz iki katına çıkınca ölüm BAHİS ORANI (odds) kaç kat artıyor.

        Literatürde bu sayıyla karşılaştırma yapılır (örn. SilicoSec için
        2,77 bildirilmiştir). Anlamı "ölüm oranı 2,77 katına çıkar" DEĞİL:
        ölüm oranı eğrinin neresinde olduğuna bağlıdır, %95'ten 2,77 katına
        çıkamaz. Katlanan şey bahis oranıdır, p/(1-p).

        x ekseni log10 olduğu için dozu ikiye katlamak x'e log10(2)=0,301
        ekler; lojistik modelde bahis oranı bu kadar artar.
        """
        return float(math.exp(self.egim * math.log10(2.0)))


def _bag(baglanti: str) -> tuple[Any, Any]:
    """Bağlantı fonksiyonu ve tersi."""
    if baglanti == "probit":
        return stats.norm.cdf, stats.norm.ppf
    if baglanti == "lojistik":
        return (lambda z: 1 / (1 + np.exp(-z)),
                lambda p: np.log(p / (1 - p)))
    raise ValueError(f"bilinmeyen bağlantı: {baglanti}")


def abbott(oran: float, kontrol: float) -> float:
    """Kontrol ölümüne göre düzeltilmiş ölüm oranı."""
    if kontrol >= 1.0:
        return 0.0
    return max(0.0, min(1.0, (oran - kontrol) / (1.0 - kontrol)))


def _lc_araligi(a: float, b: float, hedef_z: float, kov: np.ndarray,
                guven: float = 0.95, cekilis: int = 20000,
                tohum: int = 7) -> tuple[float, float] | None:
    """LC için güven aralığı — parametrik önyükleme.

    log10(LC) = (z − a) / b, yani iki kestirimin ORANI. Oranın güven aralığı
    tek tek aralıklardan türetilemez. Klasik çözüm Fieller teoremidir; burada
    daha sağlam ve doğrulaması kolay olan parametrik önyükleme kullanılıyor:
    (a, b) ikilisi asimptotik normalinden binlerce kez çekilir, her çekilişte
    LC hesaplanır, yüzdelikler alınır.

    Önyüklemenin iki üstünlüğü var: aralık nokta tahminini kapsamak zorunda
    (yüzdelik olduğu için), ve oranın çarpık dağılımını olduğu gibi taşır.
    Fieller'ın kapalı formunda işaret hatası yapmak kolaydır ve hata sessizce
    geçer — nitekim ilk uygulamada tam bu oldu.

    Eğimi pozitif olmayan çekilişler atılır: doz arttıkça ölüm artmıyorsa
    öldürücü doz tanımsızdır. Çekilişlerin %5'inden azı sağlıklıysa None
    döner — bu bir hata değil, "bu veriyle kestirilemez" demektir.
    """
    rng = np.random.default_rng(tohum)
    try:
        ornek = rng.multivariate_normal([a, b], kov, size=cekilis)
    except (np.linalg.LinAlgError, ValueError):          # pragma: no cover
        return None
    aa, bb = ornek[:, 0], ornek[:, 1]
    gecerli = bb > 0
    if gecerli.sum() < cekilis * 0.05:
        return None
    m = (hedef_z - aa[gecerli]) / bb[gecerli]
    alt_y, ust_y = (1 - guven) / 2 * 100, (1 + guven) / 2 * 100
    alt, ust = np.percentile(m, [alt_y, ust_y])
    # Üs sınırlanıyor: ıraksamış çekilişlerde 10**büyük_sayı taşar.
    if not (math.isfinite(alt) and math.isfinite(ust)) or max(abs(alt), abs(ust)) > 30:
        return None
    return float(10 ** alt), float(10 ** ust)


def uydur(gozlemler: Sequence[Gozlem], eksen: str = "doz",
          baglanti: str = "probit",
          hedefler: Sequence[float] = (0.5, 0.9, 0.95)) -> Uyum:
    """Doz–cevap eğrisini uydurur.

    eksen="doz"  -> LC (öldürücü doz),  sabit süre verisi beklenir
    eksen="sure" -> LT (öldürücü süre), sabit doz verisi beklenir
    """
    cdf, ppf = _bag(baglanti)
    uyari: list[str] = []

    kontroller = [g for g in gozlemler if getattr(g, eksen) <= 0]
    uygulanan = [g for g in gozlemler if getattr(g, eksen) > 0]
    if not uygulanan:
        raise ValueError("uygulama grubu yok (hepsi kontrol)")

    k_denenen = sum(g.denenen for g in kontroller)
    k_olen = sum(g.olen for g in kontroller)
    kontrol = k_olen / k_denenen if k_denenen else 0.0
    if kontrol > KONTROL_UYARI:
        uyari.append(
            f"kontrol ölümü %{kontrol * 100:.0f} — %{KONTROL_UYARI * 100:.0f} "
            f"üzerinde; deneme koşulları sorgulanmalı")
    if not kontroller:
        uyari.append("kontrol grubu yok; Abbott düzeltmesi uygulanamadı")

    x = np.array([math.log10(getattr(g, eksen)) for g in uygulanan])
    denenen = np.array([g.denenen for g in uygulanan], dtype=float)
    # Abbott düzeltmesi oran üzerinde yapılır, sonra tam sayıya döndürülür
    olen = np.array([abbott(g.oran, kontrol) * g.denenen for g in uygulanan])

    if denenen.sum() == 0:
        raise ValueError("denenen birey sayısı sıfır")
    if len(set(x.tolist())) < 2:
        raise ValueError(f"tek bir {eksen} düzeyi var; eğri uydurulamaz")

    # Uyum statsmodels GLM ile yapılıyor: binom ailesi + probit/logit bağlantısı.
    # Elle yazılmış bir en-çok-olabilirlik araması da aynı katsayıları bulur ama
    # kovaryans matrisini güvenilir vermez (BFGS'in hess_inv'i bir yaklaşımdır
    # ve güven aralıkları ona dayanıyor). GLM gözlenen bilgi matrisini verir.
    bag = sm.families.links.Probit() if baglanti == "probit" else sm.families.links.Logit()
    tasarim = sm.add_constant(x.reshape(-1, 1), has_constant="add")
    yanit = np.column_stack([olen, denenen - olen])
    model = sm.GLM(yanit, tasarim, family=sm.families.Binomial(link=bag))
    with warnings.catch_warnings(record=True) as yakalanan:
        warnings.simplefilter("always")
        uyum = model.fit()
    if any("eparation" in str(w.message) for w in yakalanan):
        uyari.append(
            "mükemmel ayrışma: bir doz düzeyinde ölümün tamamı ya da hiçbiri "
            "gerçekleşmiş. Katsayılar güvenilir değil; ara dozlar eklenmeli")

    a, b = float(uyum.params[0]), float(uyum.params[1])
    kov = np.asarray(uyum.cov_params(), dtype=float)

    if b <= 0:
        uyari.append("eğim pozitif değil: doz arttıkça ölüm artmıyor")

    # Denenen aralığın ÇOK dışına düşen bir LC bildirilmez.
    # İki sebeple: sayı taşabilir (mükemmel ayrışmada eğim sonsuza gider ve
    # 10**(...) patlar), ve bildirilse bile anlamsızdır — 400 ppm'e kadar
    # denenmiş bir denemeden "LC90 = 90.000 ppm" çıkarmak veriyi aşan bir
    # iddiadır. Bir kademe dışarı (×10) hoş görülür, ötesi "kestirilemez".
    alt_sinir = min(getattr(g, eksen) for g in uygulanan) / 10.0
    ust_sinir = max(getattr(g, eksen) for g in uygulanan) * 10.0

    lc: dict[str, dict[str, Any]] = {}
    for hedef in hedefler:
        ad_lc = f"{'LC' if eksen == 'doz' else 'LT'}{int(hedef * 100)}"
        z = float(ppf(hedef))
        if b <= 0:
            lc[ad_lc] = {"kestirilemedi": "eğim pozitif değil"}
            continue
        us = (z - a) / b
        if not math.isfinite(us) or abs(us) > 30:
            lc[ad_lc] = {"kestirilemedi": "katsayılar ıraksadı"}
            continue
        deger = float(10 ** us)
        if not (alt_sinir <= deger <= ust_sinir):
            lc[ad_lc] = {"kestirilemedi":
                         f"denenen aralığın dışında (~{deger:.3g})"}
            continue
        kayit: dict[str, Any] = {"deger": deger}
        aralik = _lc_araligi(a, b, z, kov)
        if aralik:
            kayit["alt"], kayit["ust"] = aralik
        lc[ad_lc] = kayit

    return Uyum(baglanti=baglanti, kesim=a, egim=b,
                n_gozlem=len(uygulanan), n_birey=int(denenen.sum()),
                kontrol_olumu=kontrol, lc=lc, uyari=uyari)


def oku(yol: Path) -> list[Gozlem]:
    """Deneme CSV'sini okur. Ayraç virgül ya da noktalı virgül olabilir."""
    metin = yol.read_text(encoding="utf-8-sig")
    ayrac = ";" if metin.split("\n")[0].count(";") > metin.split("\n")[0].count(",") else ","
    gozlemler = []
    for i, s in enumerate(csv.DictReader(metin.splitlines(), delimiter=ayrac), start=2):
        try:
            gozlemler.append(Gozlem(
                doz=float(s["doz"]), sure=float(s["sure"]),
                denenen=int(s["denenen"]), olen=int(s["olen"]),
                sicaklik=float(s["sicaklik"]) if s.get("sicaklik") else None,
                nem=float(s["nem"]) if s.get("nem") else None,
                tekrar=s.get("tekrar", "")))
        except (KeyError, ValueError) as e:
            raise SystemExit(
                f"{yol} satır {i}: {e}\n"
                f"Beklenen sütunlar: doz, sure, denenen, olen "
                f"(isteğe bağlı: sicaklik, nem, tekrar)") from e
    if not gozlemler:
        raise SystemExit(f"{yol} boş")
    return gozlemler


def ornek_veri(tohum: int = 20261029) -> list[Gozlem]:
    """SENTETİK deneme verisi — aracın çalıştığını göstermek için.

    GERÇEK VERİ DEĞİLDİR. Bilinen bir probit eğrisinden üretilir; aracın
    o eğriyi geri bulup bulamadığı böylece sınanabilir. Hocanın ham
    sayıları geldiğinde bu fonksiyon devre dışı kalır.

    Üretim parametreleri gerçekçi seçildi: diyatomlu toprak için tipik
    çalışma aralığı 100–1500 ppm, 7–21 gün maruz kalma.
    """
    rng = np.random.default_rng(tohum)
    gercek_a, gercek_b = -6.4, 2.6          # log10(LC50) ≈ 2.46 -> ~290 ppm
    gozlemler = [Gozlem(doz=0, sure=14, denenen=50,
                        olen=int(rng.binomial(50, 0.04)), tekrar=f"k{t}")
                 for t in range(1, 4)]
    for doz in (100, 200, 400, 800, 1500):
        for tekrar in range(1, 4):
            p = stats.norm.cdf(gercek_a + gercek_b * math.log10(doz))
            gozlemler.append(Gozlem(
                doz=doz, sure=14, denenen=50,
                olen=int(rng.binomial(50, min(p + 0.04, 0.999))),
                sicaklik=26.0, nem=65.0, tekrar=f"t{tekrar}"))
    return gozlemler


def yazdir(u: Uyum, eksen: str, birim: str) -> None:
    ad = "doz" if eksen == "doz" else "süre"
    print(f"  bağlantı        : {u.baglanti}")
    print(f"  gözlem / birey  : {u.n_gozlem} kap, {u.n_birey} birey")
    print(f"  kontrol ölümü   : %{u.kontrol_olumu * 100:.1f}")
    print(f"  eğim            : {u.egim:.3f}  "
          f"({ad} iki katına çıkınca ölüm bahsi ×{u.iki_kat_etkisi:.2f})")
    print()
    for ad_lc, k in u.lc.items():
        if "kestirilemedi" in k:
            print(f"  {ad_lc:<6} {'—':>9}        kestirilemedi: {k['kestirilemedi']}")
        elif "alt" in k:
            print(f"  {ad_lc:<6} {k['deger']:9.1f} {birim}   "
                  f"(%95 GA: {k['alt']:.1f} – {k['ust']:.1f})")
        else:
            print(f"  {ad_lc:<6} {k['deger']:9.1f} {birim}   (GA hesaplanamadı)")
    for m in u.uyari:
        print(f"  UYARI: {m}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Doz–cevap (probit) analizi")
    ap.add_argument("--veri", type=Path, help="deneme CSV'si")
    ap.add_argument("--ornek", action="store_true",
                    help="sentetik veriyle gösterim")
    ap.add_argument("--eksen", choices=("doz", "sure"), default="doz")
    ap.add_argument("--birim", default="ppm")
    ap.add_argument("--json", type=Path, help="sonucu JSON olarak yaz")
    a = ap.parse_args()

    if a.ornek:
        gozlemler = ornek_veri()
        print("SENTETİK VERİ — aracın çalıştığını göstermek için üretildi.")
        print("Gerçek deneme verisi değildir.\n")
    elif a.veri:
        gozlemler = oku(a.veri)
    else:
        raise SystemExit("--veri ya da --ornek verin")

    print(f"=== {'LC (öldürücü doz)' if a.eksen == 'doz' else 'LT (öldürücü süre)'} ===")
    probit = uydur(gozlemler, eksen=a.eksen, baglanti="probit")
    yazdir(probit, a.eksen, a.birim)
    print()
    print("  — karşılaştırma için lojistik —")
    lojistik = uydur(gozlemler, eksen=a.eksen, baglanti="lojistik")
    for ad_lc, k in lojistik.lc.items():
        if "deger" in k:
            print(f"  {ad_lc:<6} {k['deger']:9.1f} {a.birim}")

    if a.ornek:
        hedef = 10 ** ((stats.norm.ppf(0.5) - (-6.4)) / 2.6)
        bulunan = probit.lc["LC50"]["deger"]
        print(f"\n  DOĞRULAMA: veri üretilirken kullanılan gerçek LC50 "
              f"{hedef:.1f} {a.birim}")
        print(f"             araç {bulunan:.1f} {a.birim} buldu "
              f"(sapma %{abs(bulunan - hedef) / hedef * 100:.1f})")

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"probit": _sozluk(probit), "lojistik": _sozluk(lojistik),
             "eksen": a.eksen, "birim": a.birim},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n{a.json} yazıldı")


def _sozluk(u: Uyum) -> dict[str, Any]:
    return dict(baglanti=u.baglanti, kesim=u.kesim, egim=u.egim,
                iki_kat_etkisi=u.iki_kat_etkisi, n_gozlem=u.n_gozlem,
                n_birey=u.n_birey, kontrol_olumu=u.kontrol_olumu,
                lc=u.lc, uyari=u.uyari)


if __name__ == "__main__":
    main()
