"""Yayınlanmış doz–cevap verisi ve ondan çıkarılan kestirimler.

Bu dosyanın iki işi var. Birincisi veriyi korumak: sayılar elle
yazıldığı için bir harf hatası sessizce geçebilir, buradaki tutarlılık
denetimleri onu yakalar. İkincisi ve daha önemlisi, aracın GERÇEK veride
doğru davrandığını sabitlemek — özellikle KESTİRİM YAPMAYI REDDETTİĞİ
durumları. Bir araç yanlış cevabı değil, cevabı olmadığını söyleyemediği
için tehlikelidir.
"""

from __future__ import annotations

import pytest

from depo import doz_cevap as dc
from depo import literatur as lit

AGRAFIOTI_URUN = ("Silicid", "Celatom MN-23", "SilicoSec")
AGRAFIOTI_DOZ = (100, 300, 500, 1000)
AGRAFIOTI_SURE = (3, 7, 14, 21)


# --------------------------------------------------------------- veri


def test_her_olcum_bilinen_bir_yayina_bagli():
    for calisma, *_ in lit.OLCUMLER:
        assert calisma in lit.CALISMALAR


def test_yuzdeler_gecerli_aralikta():
    for calisma, urun, doz, sure, yuzde in lit.OLCUMLER:
        assert 0.0 <= yuzde <= 100.0, f"{calisma}/{urun}/{doz}/{sure}"
        assert doz > 0 and sure > 0


def test_agrafioti_izgarasi_eksiksiz():
    """3 ürün × 4 doz × 4 süre = 48 hücre, hiçbiri boş değil."""
    var = {(u, d, s) for c, u, d, s, _ in lit.OLCUMLER if c == "agrafioti2023"}
    beklenen = {(u, d, s) for u in AGRAFIOTI_URUN
                for d in AGRAFIOTI_DOZ for s in AGRAFIOTI_SURE}
    assert var == beklenen
    assert len(var) == 48


def test_hucre_basina_birey_sayilari():
    assert lit.CALISMALAR["agrafioti2023"].n_hucre == 180   # 20 birey × 9 tekrar
    assert lit.CALISMALAR["ogreten2025"].n_hucre == 300     # 30 birey × 10 tekrar


def test_her_yayinin_doi_ve_kosullari_yazili():
    for c in lit.CALISMALAR.values():
        assert c.doi.startswith("10.")
        assert c.sicaklik > 0 and 0 < c.nem < 100
        assert c.kontrol_notu and c.not_


def test_gozlem_cevrimi_yuzdeyi_koruyor():
    """olen/denenen, yayındaki yüzdeye bir bireyden fazla sapmamalı."""
    for calisma, urun, doz, sure, yuzde in lit.OLCUMLER:
        for g in lit.gozlemler(calisma, urun, sure):
            if g.doz != doz:
                continue
            assert abs(g.oran * 100 - yuzde) <= 100 / g.denenen / 2 + 1e-9
            assert 0 <= g.olen <= g.denenen


def test_sure_uzadikca_olum_artiyor():
    """Aynı kaplar tekrar sayıldığı için ölüm geri gidemez.

    Yüzdeler ortalama olduğu ve yayın yuvarladığı için küçük geri
    gidişler olabilir; iki puandan fazlası veri hatasıdır.
    """
    kayit = {(c, u, d, s): y for c, u, d, s, y in lit.OLCUMLER}
    for (c, u, d, s), y in kayit.items():
        if c != "agrafioti2023":
            continue
        for sonraki in (x for x in AGRAFIOTI_SURE if x > s):
            assert kayit[(c, u, d, sonraki)] >= y - 2.0, (c, u, d, s, sonraki)


def test_karsitlik_iki_yayinin_cakistigi_noktayi_buluyor():
    k = lit.sicaklik_karsitligi()
    assert k["urun"] == "SilicoSec" and k["doz"] == 1000 and k["sure"] == 7
    assert k["dusuk"]["sicaklik"] < k["yuksek"]["sicaklik"]
    assert k["yuksek"]["olum"] > k["dusuk"]["olum"]
    assert k["kat"] > 10          # fark küçük değil, onlarca kat


def test_ozet_sayilari_tutarli():
    o = lit.ozet()
    assert o["olcum"] == len(lit.OLCUMLER)
    assert o["yayin"] == len(lit.CALISMALAR)
    assert o["birey"] == sum(lit.CALISMALAR[c].n_hucre for c, *_ in lit.OLCUMLER)
    assert o["doz_serisi"] == 12   # üç ürün × dört süre


# ------------------------------------------------------- kestirimler


def uy(urun: str, sure: float) -> dc.Uyum:
    return dc.uydur(lit.gozlemler("agrafioti2023", urun, sure),
                    eksen="doz", baglanti="probit")


def test_silicid_lc50_sure_uzadikca_dusuyor():
    """Aracın ürettiği asıl bulgu: aynı ölüm daha az dozla elde ediliyor."""
    lc = [uy("Silicid", s).lc["LC50"]["deger"] for s in AGRAFIOTI_SURE]
    assert lc == sorted(lc, reverse=True), lc
    assert lc[0] / lc[-1] > 5      # 3 günden 21 güne en az beş kat


def test_silicid_21_gun_yayinla_uyumlu():
    """Yayın 21. günde 500 ppm'de %78, 1000 ppm'de %100 bildiriyor;
    LC50 bu ikisinin arasında, 500'e yakın ama altında olmalı."""
    k = uy("Silicid", 21).lc["LC50"]
    assert 300 < k["deger"] < 500
    assert k["alt"] < k["deger"] < k["ust"]


def test_21_gunde_siralama_yayinin_sonucuyla_ayni():
    """Yayın 'Silicid en etkili' diyor ama sayı vermiyor; araç sıralıyor."""
    lc = {u: uy(u, 21).lc["LC50"]["deger"] for u in AGRAFIOTI_URUN}
    assert lc["Silicid"] < lc["SilicoSec"] < lc["Celatom MN-23"]


def test_silicosec_uc_gunde_kestirim_reddediliyor():
    """Üç günde doz ile ölüm arasında ilişki yok (1,1 / 2,7 / 1,6 / 0,6).

    Araç bu durumda eğri uydurmamalı. Reddetmek doğru cevaptır.
    """
    u = uy("SilicoSec", 3)
    assert u.egim <= 0
    assert "kestirilemedi" in u.lc["LC50"]


def test_celatom_erken_surelerde_kestirim_reddediliyor():
    for s in (3, 7, 14):
        assert "kestirilemedi" in uy("Celatom MN-23", s).lc["LC50"]
    assert "deger" in uy("Celatom MN-23", 21).lc["LC50"]


@pytest.mark.parametrize("urun", AGRAFIOTI_URUN)
def test_21_gun_kestirimi_denenen_aralikta(urun):
    """21. günde üçünün de LC50'si 100–1000 ppm arasına düşmeli;
    yani uzatma değil, ölçülmüş bölgede bir kestirim."""
    k = uy(urun, 21).lc["LC50"]
    assert 100 <= k["deger"] <= 1000


def test_guven_araligi_nokta_tahminini_kapsiyor():
    """Fieller hatasının nöbetçisi — gerçek veride de geçerli."""
    for urun in AGRAFIOTI_URUN:
        for s in AGRAFIOTI_SURE:
            for k in uy(urun, s).lc.values():
                if "deger" in k and k.get("alt") is not None:
                    assert k["alt"] <= k["deger"] <= k["ust"]


def test_kontrol_grubu_olmadigi_uyarisi_veriliyor():
    """Yayın kontrol ölümünü sayıyla vermiyor (yalnızca '%2'nin altında'),
    bu yüzden Abbott uygulanmıyor. Araç bunu söylemek zorunda."""
    u = uy("Silicid", 21)
    assert any("kontrol" in x.lower() for x in u.uyari), u.uyari
