"""
iz — izlenebilir hesap grafiği
==============================
Bir sayının doğru olup olmadığı kadar, NEREDEN GELDİĞİ de önemlidir. Bu
kütüphane her büyüklüğü bir düğüm olarak tutar: değerini, birimini, kaynağını
ve hangi başka büyüklüklerden türediğini bilir.

Kazanç şudur: künye artık elle yazılan bir belge değil, hesabın kendisinden
çıkan bir şeydir. Formül değişirse iz de değişir, eskiyemez.

Üç düğüm türü vardır:

    olcum(...)   Resmî kaynakta yayımlanmış sayı. Kaynağı ve yılı vardır.
    varsayim(...) Literatürden alınan katsayı. Aralığı ve gerekçesi vardır.
    turet(...)   Başka düğümlerden hesaplanır. Kendi değeri yoktur.

Kullanım:

    nufus = olcum("Muş nüfusu", 392301, "kişi", kaynak="TÜİK 2024")
    kisi_basi = varsayim("Kişi başı buğday", 0.25, "ton/kişi",
                         aralik=(0.195, 0.30), gerekce="...")
    talep = turet("Gıda buğday talebi", lambda n, k: n * k, nufus, kisi_basi,
                  birim="ton")

    talep.deger()                  -> 98.075
    talep.agac()                   -> türeyiş ağacı (panelde çizilir)
    c = Calisma(40000); talep.ornek(c)   -> dağılım
    talep.duyarlilik(c)            -> hangi yaprak belirsizliğin kaçını üretiyor

NEDEN ÖRNEKLER ÖNBELLEKLENİR
-----------------------------
Aynı yaprak grafiğin birden çok dalında geçebilir (nüfus hem gıda talebinde
hem tohumlukta kullanılır). Her geçişte yeniden örneklenirse aralarındaki
bağ kopar ve belirsizlik olduğundan büyük çıkar. Bu yüzden örnekler Calisma
nesnesinde düğüm kimliğine göre önbelleklenir: bir yaprak bir çalışmada bir
kez örneklenir.
"""

import itertools
import math
from collections.abc import Callable, Iterator, Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

Dizi = NDArray[np.float64]
Aralik = tuple[float, float, float]

_SAYAC = itertools.count(1)

OLCUM = "ölçüm"
VARSAYIM = "varsayım"
TURETILMIS = "türetilmiş"


class Dugum:
    """Hesap grafiğinde tek bir büyüklük."""

    def __init__(self, ad: str, tur: str, birim: str = "",
                 deger: float | None = None, aralik: Aralik | None = None,
                 kaynak: str | None = None, gerekce: str | None = None,
                 fn: Callable[..., Any] | None = None,
                 girdiler: Sequence["Dugum"] = (),
                 bicim: int | None = None,
                 olcum_yolu: dict[str, Any] | None = None) -> None:
        self.kimlik = f"d{next(_SAYAC)}"
        self.ad = ad
        self.tur = tur
        self.birim = birim
        self._deger = deger
        self.aralik = aralik          # (en düşük, en olası, en yüksek)
        self.kaynak = kaynak
        self.gerekce = gerekce
        self.fn = fn
        self.girdiler = list(girdiler)
        self.bicim = bicim            # ondalık basamak sayısı
        self.olcum_yolu = olcum_yolu  # bu bilinmeyen nasıl ölçülür

    # ------------------------------------------------------------ değer
    def deger(self) -> float:
        """Noktasal değer. Varsayımlarda 'en olası' uç kullanılır."""
        if self.tur != TURETILMIS:
            assert self._deger is not None, f"{self.ad}: yaprak düğümün değeri yok"
            return float(self._deger)
        assert self.fn is not None, f"{self.ad}: türetilmiş düğümün işlevi yok"
        return float(self.fn(*[g.deger() for g in self.girdiler]))

    # --------------------------------------------------------- örnekleme
    def ornek(self, calisma: "Calisma") -> Dizi:
        """Bu düğümün dağılımı. Calisma içinde bir kez hesaplanır."""
        if self.kimlik in calisma.onbellek:
            return calisma.onbellek[self.kimlik]

        if self.tur == VARSAYIM and self.aralik:
            d, m, y = self.aralik
            # Üçgen dağılım: sınırların dışına çıkmaz. Bir verim ya da oran
            # negatif olamaz; normal dağılım bunu garanti etmez.
            x = (calisma.rng.triangular(d, m, y, calisma.n)
                 if y > d else np.full(calisma.n, float(m)))
        elif self.tur == OLCUM:
            assert self._deger is not None, f"{self.ad}: ölçümün değeri yok"
            x = np.full(calisma.n, float(self._deger))
        else:
            assert self.fn is not None, f"{self.ad}: türetilmiş düğümün işlevi yok"
            x = np.asarray(self.fn(*[g.ornek(calisma) for g in self.girdiler]),
                           dtype=float)
            if x.shape == ():
                x = np.full(calisma.n, float(x))

        calisma.onbellek[self.kimlik] = x
        return x

    # -------------------------------------------------------------- yapı
    def yapraklar(self) -> list["Dugum"]:
        """Grafiğin altındaki bütün girdi düğümleri (tekrarsız, sıralı)."""
        bulunan, sira = {}, []

        def gez(d: "Dugum") -> None:
            if d.tur == TURETILMIS:
                for g in d.girdiler:
                    gez(g)
            elif d.kimlik not in bulunan:
                bulunan[d.kimlik] = d
                sira.append(d)
        gez(self)
        return sira

    def belirsiz_yapraklar(self) -> list["Dugum"]:
        return [y for y in self.yapraklar()
                if y.aralik and y.aralik[2] > y.aralik[0]]

    def derinlik(self) -> int:
        if self.tur != TURETILMIS:
            return 1
        return 1 + max((g.derinlik() for g in self.girdiler), default=0)

    def dugum_sayisi(self) -> int:
        return len({d.kimlik for d in self._hepsi()})

    def _hepsi(self) -> Iterator["Dugum"]:
        yield self
        for g in self.girdiler:
            yield from g._hepsi()

    # -------------------------------------------------------- duyarlılık
    def duyarlilik(self, calisma: "Calisma", kutu: int = 28) -> list[dict[str, Any]]:
        """Her belirsiz yaprağın bu düğümün varyansına birinci mertebe katkısı.

        Var(E[Y|X]) / Var(Y). Örnekler yaprağa göre kutulara ayrılır, kutu
        ortalamalarının varyansı toplam varyansa bölünür. Yaprak sonucu
        etkilemiyorsa kutu ortalamaları eşitlenir ve indis sıfıra iner.
        """
        y = self.ornek(calisma)
        toplam = float(y.var())
        cikti: list[dict[str, Any]] = []
        for yaprak in self.belirsiz_yapraklar():
            x = yaprak.ornek(calisma)
            s1 = 0.0
            if toplam > 0 and not np.allclose(x, x[0]):
                sirali = y[np.argsort(x)]
                parcalar = np.array_split(sirali, kutu)
                ort = np.array([p.mean() for p in parcalar])
                ag = np.array([len(p) for p in parcalar], dtype=float)
                ag /= ag.sum()
                genel = float((ort * ag).sum())
                s1 = float((ag * (ort - genel) ** 2).sum() / toplam)
                s1 = max(0.0, min(1.0, s1))
            assert yaprak.aralik is not None   # belirsiz_yapraklar() güvencesi
            cikti.append(dict(kimlik=yaprak.kimlik, ad=yaprak.ad,
                              birim=yaprak.birim, aralik=list(yaprak.aralik),
                              gerekce=yaprak.gerekce,
                              olcum_yolu=yaprak.olcum_yolu,
                              s1=round(s1, 4), varyans_payi=round(s1 * 100, 1)))
        cikti.sort(key=lambda r: -float(r["s1"]))
        return cikti

    def ozet(self, calisma: "Calisma") -> dict[str, Any]:
        x = self.ornek(calisma)
        return dict(
            ad=self.ad, birim=self.birim,
            noktasal=self.deger(),
            medyan=float(np.percentile(x, 50)),
            alt90=float(np.percentile(x, 5)), ust90=float(np.percentile(x, 95)),
            sapma=float(x.std()))

    # ------------------------------------------------------------- uç köşe
    def kose(self, en_buyuk: bool = True) -> float:
        """Bütün belirsiz yapraklar aynı anda uçlarındayken değer.

        "Her şey ters giderse ne olur?" sorusunun cevabı. Monte Carlo bu
        köşeye pratikte hiç uğramaz (on bağımsız değişkenin aynı anda aynı
        uçta olma olasılığı sıfıra yakındır), ama sınırları görmek için
        gerekir.

        Hangi ucun sonucu büyüttüğü analitik olarak bilinemez: bir yaprak
        arz tarafındaysa yükseği, talep tarafındaysa düşüğü sonucu büyütür.
        Bu yüzden her yaprak için iki uç da denenir, diğerleri en olası
        değerinde tutularak hangisinin sonucu büyüttüğüne bakılır.
        """
        belirsiz = self.belirsiz_yapraklar()
        if not belirsiz:
            return self.deger()

        asil = {y.kimlik: y._deger for y in belirsiz}
        try:
            for y in belirsiz:
                assert y.aralik is not None   # belirsiz_yapraklar() güvencesi
                dusuk, _mod, yuksek = y.aralik
                denemeler: dict[str, float] = {}
                for uc, deger in (("dusuk", dusuk), ("yuksek", yuksek)):
                    y._deger = deger
                    denemeler[uc] = self.deger()
                    y._deger = asil[y.kimlik]
                buyuten = max(denemeler, key=lambda k: denemeler[k])
                secilen = buyuten if en_buyuk else (
                    "yuksek" if buyuten == "dusuk" else "dusuk")
                y._deger = dusuk if secilen == "dusuk" else yuksek
            return self.deger()
        finally:
            for y in belirsiz:
                y._deger = asil[y.kimlik]

    # --------------------------------------------------------- türeyiş ağacı
    def agac(self, calisma: "Calisma | None" = None,
             paylar: dict[str, float | None] | None = None,
             derinlik: int = 0, maks: int = 6) -> dict[str, Any]:
        """Panelde çizilecek türeyiş ağacı (iç içe sözlük)."""
        if paylar is None and calisma is not None:
            paylar = {r["kimlik"]: r["varyans_payi"]
                      for r in self.duyarlilik(calisma)}
        paylar = paylar or {}

        kayit = dict(
            kimlik=self.kimlik, ad=self.ad, tur=self.tur, birim=self.birim,
            deger=round(self.deger(), self.bicim if self.bicim is not None
                        else _basamak(self.deger())),
            kaynak=self.kaynak, gerekce=self.gerekce,
            olcum_yolu=self.olcum_yolu,
            aralik=(list(self.aralik) if self.aralik is not None else None),
            varyans_payi=paylar.get(self.kimlik),
            cocuklar=[])
        if self.tur == TURETILMIS and derinlik < maks:
            kayit["cocuklar"] = [g.agac(None, paylar, derinlik + 1, maks)
                                 for g in self.girdiler]
        return kayit


def _basamak(v: float) -> int:
    a = abs(v)
    if a >= 1000:
        return 0
    if a >= 10:
        return 1
    if a >= 1:
        return 2
    return 4


class Calisma:
    """Tek bir örnekleme turu. Yaprak örneklerini önbellekler."""

    def __init__(self, n: int = 40000, tohum: int = 20261008) -> None:
        self.n = n
        self.rng = np.random.default_rng(tohum)
        self.onbellek: dict[str, Dizi] = {}

    def sifirla(self) -> None:
        self.onbellek.clear()


# --------------------------------------------------------------- kurucular
def olcum(ad: str, deger: float, birim: str = "", kaynak: str | None = None,
          aralik: Aralik | None = None, bicim: int | None = None) -> Dugum:
    """Resmî kaynakta yayımlanmış sayı.

    aralik verilirse ölçümün kendisi de belirsiz sayılır — kaynak kendisiyle
    çelişiyorsa (Muş buğday üretiminde olduğu gibi) bu gerekir.
    """
    return Dugum(ad, VARSAYIM if aralik else OLCUM, birim, deger=deger,
                 aralik=aralik, kaynak=kaynak, bicim=bicim)


def varsayim(ad: str, en_olasi: float, birim: str = "",
             aralik: tuple[float, float] | Aralik | None = None,
             gerekce: str | None = None,
             olcum_yolu: dict[str, Any] | None = None,
             bicim: int | None = None) -> Dugum:
    """Literatürden alınan katsayı. aralik=(en düşük, en yüksek)."""
    if aralik and len(aralik) == 2:
        aralik = (aralik[0], en_olasi, aralik[1])
    elif aralik is None:
        aralik = (en_olasi, en_olasi, en_olasi)
    return Dugum(ad, VARSAYIM, birim, deger=en_olasi, aralik=aralik,
                 gerekce=gerekce, olcum_yolu=olcum_yolu, bicim=bicim)


def turet(ad: str, fn: Callable[..., Any], *girdiler: Dugum, birim: str = "",
          gerekce: str | None = None, bicim: int | None = None) -> Dugum:
    """Başka düğümlerden hesaplanan büyüklük."""
    return Dugum(ad, TURETILMIS, birim, fn=fn, girdiler=girdiler,
                 gerekce=gerekce, bicim=bicim)


def topla(ad: str, *girdiler: Dugum, birim: str = "") -> Dugum:
    return turet(ad, lambda *v: sum(v), *girdiler, birim=birim)


def carp(ad: str, *girdiler: Dugum, birim: str = "") -> Dugum:
    return turet(ad, lambda *v: math.prod(v) if not _dizi(v)
                 else _carpim(v), *girdiler, birim=birim)


def _dizi(v: Sequence[Any]) -> bool:
    return any(isinstance(x, np.ndarray) for x in v)


def _carpim(v: Sequence[Any]) -> Dizi:
    sonuc = np.asarray(v[0], dtype=float)
    for x in v[1:]:
        sonuc = sonuc * np.asarray(x, dtype=float)
    return sonuc


def bol(ad: str, pay: Dugum, payda: Dugum, birim: str = "") -> Dugum:
    return turet(ad, lambda a, b: np.divide(a, b, out=np.zeros_like(
        np.asarray(a, dtype=float)), where=np.asarray(b) != 0)
        if _dizi((a, b)) else (a / b if b else 0.0), pay, payda, birim=birim)


def fark(ad: str, a: Dugum, b: Dugum, birim: str = "",
         en_az_sifir: bool = False) -> Dugum:
    if en_az_sifir:
        return turet(ad, lambda x, y: np.maximum(0.0, np.asarray(x) - np.asarray(y))
                     if _dizi((x, y)) else max(0.0, x - y), a, b, birim=birim)
    return turet(ad, lambda x, y: x - y, a, b, birim=birim)


# ------------------------------------------------------------------ yazdır
def agac_yazdir(dugum: Dugum, calisma: "Calisma | None" = None,
                girinti: int = 0, paylar: dict[str, float | None] | None = None) -> None:
    """Terminalde türeyiş ağacını gösterir."""
    if paylar is None and calisma is not None:
        paylar = {r["kimlik"]: r["varyans_payi"] for r in dugum.duyarlilik(calisma)}
    paylar = paylar or {}

    deger = dugum.deger()
    bas = "   " * girinti + ("└── " if girinti else "")
    etiket = {OLCUM: "[ÖLÇÜM]", VARSAYIM: "[VARSAYIM]", TURETILMIS: ""}[dugum.tur]
    pay = paylar.get(dugum.kimlik)
    ek = f"  · varyans %{pay}" if pay and pay >= 0.5 else ""
    kaynak = f"  {dugum.kaynak}" if dugum.kaynak else ""
    basamak = dugum.bicim if dugum.bicim is not None else _basamak(deger)
    sayi = (f"{deger:,.{basamak}f}"
            .replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"{bas}{dugum.ad} = {sayi} {dugum.birim} {etiket}{kaynak}{ek}")
    for g in dugum.girdiler:
        agac_yazdir(g, None, girinti + 1, paylar)
