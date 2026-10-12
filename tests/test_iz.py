"""
iz.py — hesap grafiği kütüphanesinin testleri.

Bu dosya kütüphanenin SÖZLEŞMESİNİ test eder: düğümler nasıl değer üretir,
örnekler nasıl önbelleklenir, duyarlılık nasıl hesaplanır. Tarımla ilgisi
yoktur; kütüphane alan bağımsızdır ve testleri de öyle olmalıdır.
"""

import numpy as np
import pytest

import iz
from iz import Calisma, bol, carp, fark, olcum, topla, varsayim


# ----------------------------------------------------------- temel değer
def test_olcum_degeri_aynen_doner():
    n = olcum("Nüfus", 392301, "kişi", kaynak="TÜİK 2024")
    assert n.deger() == 392301
    assert n.tur == iz.OLCUM
    assert n.birim == "kişi"


def test_varsayim_en_olasi_degeri_kullanir():
    v = varsayim("Verim", 0.25, "ton/da", aralik=(0.1, 0.4))
    assert v.deger() == 0.25
    assert v.tur == iz.VARSAYIM
    # aralık (en düşük, en olası, en yüksek) olarak saklanır
    assert v.aralik == (0.1, 0.25, 0.4)


def test_aralikli_olcum_varsayima_doner():
    """Kaynak kendisiyle çelişiyorsa ölçüm de belirsizdir.

    Muş buğday üretiminde gerçekten böyle: aynı belgede 368.297 ton ve
    '115 bin ha'da ~244 bin ton' yazıyor.
    """
    u = olcum("Buğday üretimi", 368297, "ton", aralik=(244000, 368297, 380000))
    assert u.tur == iz.VARSAYIM
    assert u.deger() == 368297


def test_turetilmis_dugum_hesaplar():
    a = olcum("a", 10)
    b = olcum("b", 4)
    assert topla("toplam", a, b).deger() == 14
    assert carp("çarpım", a, b).deger() == 40
    assert bol("bölüm", a, b).deger() == 2.5
    assert fark("fark", a, b).deger() == 6


def test_fark_en_az_sifir():
    """Açık hesabında negatif değer anlamsızdır: arz ihtiyaçtan fazlaysa açık sıfırdır."""
    az = olcum("az", 3)
    cok = olcum("çok", 10)
    assert fark("açık", az, cok, en_az_sifir=True).deger() == 0
    assert fark("açık", az, cok, en_az_sifir=False).deger() == -7


def test_bol_sifira_bolmede_patlamaz():
    assert bol("bölüm", olcum("a", 5), olcum("b", 0)).deger() == 0.0


# ------------------------------------------------------------- yapı
def test_yapraklar_tekrarsiz_doner():
    """Aynı yaprak iki dalda geçse bile bir kez listelenir."""
    nufus = olcum("Nüfus", 100)
    k1 = varsayim("k1", 2.0)
    k2 = varsayim("k2", 3.0)
    dal1 = carp("dal1", nufus, k1)
    dal2 = carp("dal2", nufus, k2)
    kok = topla("kök", dal1, dal2)

    yapraklar = kok.yapraklar()
    assert len(yapraklar) == 3
    assert sum(1 for y in yapraklar if y.ad == "Nüfus") == 1


def test_belirsiz_yapraklar_sadece_araligi_olanlar():
    kok = topla("kök",
                olcum("kesin", 10),
                varsayim("belirsiz", 5, aralik=(1, 9)),
                varsayim("sabit varsayım", 3))     # aralık yok -> belirsiz değil
    belirsiz = kok.belirsiz_yapraklar()
    assert [y.ad for y in belirsiz] == ["belirsiz"]


def test_derinlik_ve_dugum_sayisi():
    a = olcum("a", 1)
    b = carp("b", a, varsayim("k", 2))
    c = topla("c", b, olcum("d", 3))
    assert c.derinlik() == 3
    assert c.dugum_sayisi() == 5


# -------------------------------------------------------- örnekleme
def test_olcum_ornegi_sabit():
    c = Calisma(n=500, tohum=1)
    x = olcum("sabit", 7).ornek(c)
    assert x.shape == (500,)
    assert np.allclose(x, 7)


def test_varsayim_ornegi_aralikta_kalir():
    """Üçgen dağılım sınırların dışına çıkmaz. Bir verim negatif olamaz."""
    c = Calisma(n=5000, tohum=1)
    x = varsayim("mera verimi", 0.10, aralik=(0.05, 0.18)).ornek(c)
    assert x.min() >= 0.05
    assert x.max() <= 0.18
    assert 0.09 < x.mean() < 0.13      # üçgen dağılımın ortalaması (a+m+b)/3


def test_araligi_olmayan_varsayim_sabit_orneklenir():
    c = Calisma(n=100, tohum=1)
    x = varsayim("sabit", 0.32).ornek(c)
    assert np.allclose(x, 0.32)


def test_ayni_yaprak_bir_kez_orneklenir():
    """Kütüphanenin en kritik davranışı.

    Nüfus hem gıda talebinde hem tohumlukta geçiyor. Her geçişte yeniden
    örneklenseydi aralarındaki bağ kopar ve belirsizlik olduğundan büyük
    çıkardı. Burada test ettiğimiz şey şu: x - x her zaman tam olarak
    sıfır olmalı, çünkü iki dal da AYNI örneği görmeli.
    """
    ortak = varsayim("ortak", 10, aralik=(1, 20))
    c = Calisma(n=1000, tohum=1)
    sifir = fark("kendisiyle farkı", ortak, ortak).ornek(c)
    assert np.allclose(sifir, 0.0), "aynı yaprak iki kez örneklenmiş"


def test_onbellek_sifirlanabilir():
    v = varsayim("v", 5, aralik=(1, 9))
    c = Calisma(n=100, tohum=1)
    ilk = v.ornek(c).copy()
    assert np.allclose(v.ornek(c), ilk)      # önbellekten geliyor
    c.sifirla()
    # Aynı rng akışı devam ettiği için yeni örnek farklı olmalı
    assert not np.allclose(v.ornek(c), ilk)


def test_ayni_tohum_ayni_sonuc():
    v = varsayim("v", 5, aralik=(1, 9))
    a = v.ornek(Calisma(n=200, tohum=42))
    b = v.ornek(Calisma(n=200, tohum=42))
    assert np.allclose(a, b)


# -------------------------------------------------------- duyarlılık
def test_etkisiz_girdi_sifir_duyarlilik():
    """Çıktıyı etkilemeyen bir yaprağın varyans payı sıfıra yakın olmalı."""
    etkili = varsayim("etkili", 10, aralik=(1, 100))
    etkisiz = varsayim("etkisiz", 5, aralik=(4.99, 5.01))
    kok = topla("kök", etkili, etkisiz)

    c = Calisma(n=20000, tohum=7)
    paylar = {r["ad"]: r["s1"] for r in kok.duyarlilik(c)}
    assert paylar["etkili"] > 0.9
    assert paylar["etkisiz"] < 0.05


def test_tek_belirsiz_girdi_tum_varyansi_aciklar():
    kok = carp("kök", olcum("sabit", 100), varsayim("tek", 2, aralik=(1, 3)))
    c = Calisma(n=20000, tohum=7)
    d = kok.duyarlilik(c)
    assert len(d) == 1
    assert d[0]["s1"] > 0.95


def test_duyarlilik_azalan_sirada():
    kok = topla("kök",
                varsayim("büyük", 50, aralik=(0, 100)),
                varsayim("orta", 10, aralik=(5, 15)),
                varsayim("küçük", 1, aralik=(0.9, 1.1)))
    c = Calisma(n=20000, tohum=7)
    paylar = [r["s1"] for r in kok.duyarlilik(c)]
    assert paylar == sorted(paylar, reverse=True)


def test_s1_toplami_biri_asmaz():
    kok = carp("kök",
               varsayim("a", 2, aralik=(1, 3)),
               varsayim("b", 5, aralik=(2, 8)))
    c = Calisma(n=20000, tohum=7)
    toplam = sum(r["s1"] for r in kok.duyarlilik(c))
    assert 0 <= toplam <= 1.05      # etkileşim payı nedeniyle 1'in biraz altında


# ------------------------------------------------------------- ağaç
def test_agac_yapisi():
    kok = carp("kök", olcum("a", 10, "kg", kaynak="TÜİK"),
               varsayim("b", 2, "oran", aralik=(1, 3), gerekce="açıklama",
                        olcum_yolu="anket"))
    agac = kok.agac()
    assert agac["ad"] == "kök"
    assert agac["tur"] == iz.TURETILMIS
    assert len(agac["cocuklar"]) == 2

    a, b = agac["cocuklar"]
    assert a["kaynak"] == "TÜİK"
    assert b["aralik"] == [1, 2, 3]
    assert b["gerekce"] == "açıklama"
    assert b["olcum_yolu"] == "anket"


def test_agac_derinlik_sinirlar():
    d = olcum("en alt", 1)
    for i in range(10):
        d = carp(f"kat {i}", d, olcum("bir", 1))
    agac = d.agac(maks=3)

    def derinlik(k):
        return 1 + max((derinlik(c) for c in k["cocuklar"]), default=0)
    assert derinlik(agac) <= 4


def test_agac_varyans_payini_tasir():
    kok = carp("kök", olcum("sabit", 10), varsayim("belirsiz", 2, aralik=(1, 3)))
    c = Calisma(n=5000, tohum=3)
    agac = kok.agac(calisma=c)
    belirsiz = next(x for x in agac["cocuklar"] if x["ad"] == "belirsiz")
    assert belirsiz["varyans_payi"] is not None
    assert belirsiz["varyans_payi"] > 50


# --------------------------------------------------------------- özet
def test_ozet_yuzdelikleri():
    v = varsayim("v", 10, aralik=(0, 20))
    c = Calisma(n=20000, tohum=5)
    o = v.ozet(c)
    assert o["alt90"] < o["medyan"] < o["ust90"]
    assert o["noktasal"] == 10
    assert o["sapma"] > 0


@pytest.mark.parametrize("deger,beklenen_basamak", [
    (12345.0, 0), (123.45, 1), (1.2345, 2), (0.012345, 4),
])
def test_basamak_secimi(deger, beklenen_basamak):
    """Büyük sayı ondalık istemez, küçük sayı ister."""
    assert iz._basamak(deger) == beklenen_basamak


# ------------------------------------------------------------- uç köşe
def test_kose_tek_yaprak():
    """Tek belirsiz yaprakta köşe, aralığın ucudur."""
    v = varsayim("v", 5, aralik=(1, 9))
    kok = carp("kök", olcum("sabit", 2), v)
    assert kok.kose(en_buyuk=True) == 18    # 2 × 9
    assert kok.kose(en_buyuk=False) == 2    # 2 × 1


def test_kose_yonu_yaprak_konumuna_gore_secer():
    """Payda tarafındaki yaprağın DÜŞÜĞÜ sonucu büyütür.

    Kütüphane bunu analitik olarak bilmez; iki ucu da deneyip bakar.
    """
    pay = varsayim("pay", 10, aralik=(5, 20))
    payda = varsayim("payda", 2, aralik=(1, 4))
    kok = bol("oran", pay, payda)
    assert kok.kose(en_buyuk=True) == pytest.approx(20)   # 20 / 1
    assert kok.kose(en_buyuk=False) == pytest.approx(1.25)  # 5 / 4


def test_kose_belirsizlik_yoksa_noktasal_deger():
    kok = carp("kök", olcum("a", 3), olcum("b", 4))
    assert kok.kose() == 12


def test_kose_dugum_degerlerini_bozmaz():
    """En kritik davranış: köşe hesabı yan etki bırakmamalı."""
    v = varsayim("v", 5, aralik=(1, 9))
    kok = carp("kök", olcum("sabit", 2), v)
    once = kok.deger()
    kok.kose(en_buyuk=True)
    kok.kose(en_buyuk=False)
    assert kok.deger() == once, "köşe hesabı düğüm değerlerini kalıcı değiştirmiş"
    assert v.deger() == 5


def test_kose_medyani_kapsar():
    """Köşeler arası aralık, örneklemenin tamamını içermeli."""
    kok = topla("kök",
                varsayim("a", 10, aralik=(5, 15)),
                varsayim("b", 20, aralik=(10, 30)))
    c = Calisma(n=10000, tohum=11)
    x = kok.ornek(c)
    assert kok.kose(en_buyuk=False) <= x.min()
    assert kok.kose(en_buyuk=True) >= x.max()
