"""
Doz–cevap motorunun testleri.

Bu modülün çıktısı bir akademisyene gösterilecek ve literatürdeki LC50
değerleriyle karşılaştırılacak. Yanlış bir güven aralığı sessizce geçerse
proje güven kaybeder — nitekim ilk uygulamada Fieller formülündeki bir
işaret hatası, nokta tahminini KAPSAMAYAN bir aralık üretti ve bu ancak
çıktıya gözle bakınca fark edildi. Aşağıdaki testler o hatanın geri
gelmesini engeller.

Sınama yöntemi: bilinen bir eğriden veri üret, aracın o eğriyi geri bulup
bulmadığına bak. Sentetik verinin buradaki amacı budur.
"""

import math

import pytest
from scipy import stats

from depo.doz_cevap import Gozlem, abbott, ornek_veri, uydur

# ornek_veri() bu parametrelerle üretiliyor
GERCEK_A, GERCEK_B = -6.4, 2.6
GERCEK_LC50 = 10 ** ((stats.norm.ppf(0.5) - GERCEK_A) / GERCEK_B)


@pytest.fixture(scope="module")
def uyum():
    return uydur(ornek_veri(), eksen="doz", baglanti="probit")


# ------------------------------------------------------------ doğruluk
def test_bilinen_lc50_geri_bulunuyor(uyum):
    """Araç, veriyi üreten eğrinin LC50'sini %15 içinde bulmalı."""
    bulunan = uyum.lc["LC50"]["deger"]
    sapma = abs(bulunan - GERCEK_LC50) / GERCEK_LC50
    assert sapma < 0.15, f"LC50 sapması %{sapma * 100:.1f} (bulunan {bulunan:.1f}, gerçek {GERCEK_LC50:.1f})"


def test_bilinen_egim_geri_bulunuyor(uyum):
    assert abs(uyum.egim - GERCEK_B) < 0.8, f"eğim {uyum.egim:.2f}, beklenen ~{GERCEK_B}"


# -------------------------------------------------- güven aralığı sağlığı
def test_guven_araligi_nokta_tahmini_kapsiyor(uyum):
    """En temel sağlık kontrolü: aralık kendi merkezini içermeli.

    Fieller uygulamasındaki işaret hatası tam burada patlıyordu.
    """
    for ad, k in uyum.lc.items():
        if "alt" not in k:
            continue
        assert k["alt"] <= k["deger"] <= k["ust"], (
            f"{ad}: {k['deger']:.1f} aralığın dışında "
            f"[{k['alt']:.1f}, {k['ust']:.1f}]")


def test_guven_araligi_gercek_degeri_kapsiyor(uyum):
    k = uyum.lc["LC50"]
    assert k["alt"] <= GERCEK_LC50 <= k["ust"], (
        f"gerçek LC50 {GERCEK_LC50:.1f} aralıkta değil "
        f"[{k['alt']:.1f}, {k['ust']:.1f}]")


def test_lc90_lc50den_buyuk(uyum):
    assert uyum.lc["LC90"]["deger"] > uyum.lc["LC50"]["deger"]
    assert uyum.lc["LC95"]["deger"] > uyum.lc["LC90"]["deger"]


def test_daha_cok_veri_araligi_daraltir():
    """Tekrar sayısı artınca güven aralığı daralmalı — temel istatistik."""
    az = uydur([g for g in ornek_veri() if g.tekrar in ("k1", "t1")])
    cok = uydur(ornek_veri())
    genislik = lambda u: u.lc["LC50"]["ust"] - u.lc["LC50"]["alt"]  # noqa: E731
    assert genislik(cok) < genislik(az), "daha çok veri aralığı daraltmadı"


# ------------------------------------------------------------- Abbott
def test_abbott_kontrol_olumunu_cikarir():
    assert abbott(0.5, 0.0) == pytest.approx(0.5)
    assert abbott(0.6, 0.2) == pytest.approx(0.5)      # (0.6-0.2)/0.8
    assert abbott(0.1, 0.2) == 0.0                     # negatife düşmez
    assert abbott(1.0, 0.2) == pytest.approx(1.0)


def test_yuksek_kontrol_olumu_uyari_verir():
    g = [Gozlem(doz=0, sure=14, denenen=50, olen=25)]          # %50 kontrol
    g += [Gozlem(doz=d, sure=14, denenen=50, olen=45) for d in (100, 400, 1500)]
    u = uydur(g)
    assert any("kontrol ölümü" in m for m in u.uyari)


def test_kontrolsuz_veri_uyari_verir():
    g = [Gozlem(doz=d, sure=14, denenen=50, olen=o)
         for d, o in ((100, 10), (400, 30), (1500, 46))]
    u = uydur(g)
    assert any("kontrol grubu yok" in m for m in u.uyari)
    assert u.kontrol_olumu == 0.0


# --------------------------------------------------- hata durumları
def test_tek_doz_duzeyi_reddedilir():
    g = [Gozlem(doz=0, sure=14, denenen=50, olen=2),
         Gozlem(doz=400, sure=14, denenen=50, olen=30),
         Gozlem(doz=400, sure=14, denenen=50, olen=28)]
    with pytest.raises(ValueError, match="tek bir doz"):
        uydur(g)


def test_sadece_kontrol_reddedilir():
    g = [Gozlem(doz=0, sure=14, denenen=50, olen=2)]
    with pytest.raises(ValueError, match="uygulama grubu yok"):
        uydur(g)


def test_etkisiz_doz_uyari_verir():
    """Doz arttıkça ölüm artmıyorsa araç bunu söylemeli, sayı uydurmamalı."""
    g = [Gozlem(doz=0, sure=14, denenen=60, olen=6)]
    g += [Gozlem(doz=d, sure=14, denenen=60, olen=o)
          for d, o in ((100, 8), (400, 7), (1500, 6))]
    u = uydur(g)
    assert u.egim <= 0.5, "etkisiz dozda eğim yüksek çıktı"
    if u.egim <= 0:
        assert any("eğim" in m for m in u.uyari)


# --------------------------------------------------------- LT ekseni
def test_lt_ekseni_calisiyor():
    """Sabit dozda süre uzadıkça ölüm artıyorsa LT kestirilebilmeli."""
    gercek_a, gercek_b = -1.6, 2.2
    g = [Gozlem(doz=500, sure=0, denenen=60, olen=3)]
    for sure in (3, 7, 14, 21, 28):
        p = stats.norm.cdf(gercek_a + gercek_b * math.log10(sure))
        g.append(Gozlem(doz=500, sure=sure, denenen=60, olen=int(round(60 * p))))
    u = uydur(g, eksen="sure")
    assert "LT50" in u.lc
    assert 3 < u.lc["LT50"]["deger"] < 28


# ------------------------------------------------- bahis oranı yorumu
def test_iki_kat_etkisi_dogru_hesaplaniyor(uyum):
    """Doz ikiye katlanınca bahis oranındaki artış exp(b·log10 2) olmalı.

    Yanlış hâli 2**b idi; o sayı literatürdeki değerlerle kıyaslanamaz.
    """
    beklenen = math.exp(uyum.egim * math.log10(2.0))
    assert uyum.iki_kat_etkisi == pytest.approx(beklenen)
    assert 1.0 < uyum.iki_kat_etkisi < 10.0


# ------------------------------------------------- probit ve lojistik
def test_probit_ve_lojistik_yakin_sonuc_verir():
    """İkisi farklı bağlantı fonksiyonu ama LC50 civarında örtüşmeli."""
    p = uydur(ornek_veri(), baglanti="probit")
    L = uydur(ornek_veri(), baglanti="lojistik")
    fark = abs(p.lc["LC50"]["deger"] - L.lc["LC50"]["deger"])
    assert fark / p.lc["LC50"]["deger"] < 0.10
