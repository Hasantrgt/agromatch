"""Veri kalitesi denetiminin kendisi doğru çalışıyor mu.

NEDEN VAR: Bu modül "veriye güvenme" diyen bir rapor üretiyor. Böyle bir
raporun kendisi yanlış sayarsa, güvensizliği yanlış yere yönlendirir ve
asıl kusur gizli kalır. Dolayısıyla denetim de denetlenmeli.

Testler iki şeyi ayırıyor:
  - MEKANİK doğruluk: uydurma satırlarla beslendiğinde doğru sayıyor mu
  - GERÇEK veri: ham dosyalar varsa beklenen kusurları buluyor mu
    (dosya yoksa atlanır; ham veri depoda tutulmaz)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from toprak_olcum import kalite

HAM_VAR = kalite.analiz.VARSAYILAN_KLASOR.exists()
ham_gerekir = pytest.mark.skipif(
    not HAM_VAR, reason="ham laboratuvar dosyaları yok (depoda tutulmaz)")


def _satir(**kw):
    """Tek bir ham satır; verilmeyen alanlar None."""
    s = {a: None for a in kalite.OLCUM_ALAN}
    s.update({"yil": 2011, "lab": None, "yer": None,
              "p_ppm": None, "p2o5_ppm": None,
              "p2o5_kgda": None, "k2o_kgda": None})
    s.update(kw)
    return s


# --- mekanik -----------------------------------------------------------
def test_imkansiz_deger_sayilir():
    ham = [_satir(ph=2.06), _satir(ph=7.4), _satir(ph=11.0), _satir(om=99.0)]
    d = kalite.d_imkansiz(ham)
    assert d["bulgu"] == 3, "iki pH ve bir OM aralık dışı"
    assert d["agirlik"] == "ölçümü etkiler"
    assert 2.06 in d["ayrinti"]["ph"]["gorulen"]


def test_gecerli_deger_kusur_sayilmaz():
    ham = [_satir(ph=7.4, om=2.0, kirec=12.0, ec=0.4, tuz=0.02)]
    assert kalite.d_imkansiz(ham)["bulgu"] == 0


def test_yinelenen_fazlalik_dogru_sayilir():
    ayni = dict(ph=7.4, om=2.0, kirec=12.0, ec=0.4, tuz=0.02)
    ham = [_satir(**ayni), _satir(**ayni), _satir(**ayni),
           _satir(ph=6.1, om=1.2, kirec=3.0, ec=0.2, tuz=0.01)]
    d = kalite.d_yinelenen(ham)
    assert d["bulgu"] == 2, "üç özdeş satır iki FAZLALIK demek"


def test_yinelenen_sans_beklentisi_tek_deger_icin_sifir_degil():
    """Tek bir değer tekrar ediyorsa karıştırma da aynı sonucu verir.

    Bu testin işi, şans beklentisinin körü körüne sıfır dönmediğini
    göstermek: aynı değerden oluşan bir sütunda yinelenme ŞANSTIR ve
    sınama bunu şans olarak işaretlemelidir.
    """
    ham = [_satir(ph=7.0, om=2.0, kirec=10.0, ec=0.3, tuz=0.01)
           for _ in range(5)]
    d = kalite.d_yinelenen(ham)
    bekl = d["ayrinti"]["sans_beklentisi_toplam"]
    assert bekl == pytest.approx(d["bulgu"], abs=0.5), (
        "tamamen özdeş veride tekrar şansla açıklanır; "
        f"gözlenen {d['bulgu']}, beklenen {bekl}")


def test_yinelenen_gercek_tekrari_sanstan_ayirir():
    """Dağılımı geniş, ama satırları kopyalanmış veri: şans açıklamaz."""
    ham = []
    for i in range(60):
        ham.append(_satir(ph=5.0 + i * 0.05, om=0.5 + i * 0.1,
                          kirec=1.0 + i * 0.3, ec=0.1 + i * 0.01,
                          tuz=0.005 + i * 0.001))
    ham += [dict(s) for s in ham[:20]]          # yirmi satır kopyalandı
    d = kalite.d_yinelenen(ham)
    assert d["bulgu"] == 20
    bekl = d["ayrinti"]["sans_beklentisi_toplam"]
    assert bekl < 1.0, f"şans beklentisi bu kadar yüksek olmamalı: {bekl}"
    # kat, beklenti ölçülemeyecek kadar küçükse None döner; bu daha da
    # güçlü bir kanıttır, zayıf değil.
    kat = d["ayrinti"]["sans_kati"]
    assert kat is None or kat > 20


def test_kopyala_yapistir_esitligi_yakalar():
    ham = [_satir(p2o5_kgda=48.5, k2o_kgda=48.5), _satir(p2o5_kgda=3.0,
                                                         k2o_kgda=242.0)]
    d = kalite.d_kopyala(ham)
    assert d["bulgu"] == 1
    assert d["agirlik"] == "sütun kullanılmıyor", (
        "fosfor ve potasyum modele girmiyor; bulgu kayıt değeri taşır")


def test_kopyala_sifir_esitligi_saymaz():
    """İki sütunun da sıfır olması kopyalama kanıtı değildir."""
    assert kalite.d_kopyala([_satir(p2o5_kgda=0.0, k2o_kgda=0.0)])["bulgu"] == 0


def test_birim_orani_beklenenden_sapanlari_sayar():
    ham = [_satir(p2o5_ppm=10.0, p2o5_kgda=2.6),      # tam beklenen oran
           _satir(p2o5_ppm=0.16, p2o5_kgda=3.0)]      # 18,75 kat sapma
    d = kalite.d_birim(ham)
    assert d["bulgu"] == 1
    assert d["ayrinti"]["karsilastirilabilir_satir"] == 2


def test_ec_tuz_satir_ici_tutarsizligi_yakalar():
    ham = [_satir(ec=1.0, tuz=0.032) for _ in range(20)]
    ham.append(_satir(ec=1.0, tuz=3.0))               # oran 90 kat sapık
    d = kalite.d_ec_tuz(ham)
    assert d["bulgu"] == 1


def test_bos_satir_sayilir():
    ham = [_satir(), _satir(ph=7.0)]
    assert kalite.d_bos(ham)["bulgu"] == 1


# --- yer sütunu: düzeltilen hatanın nöbetçisi --------------------------
@pytest.mark.parametrize("yer,beklenen", [
    ("Güneyik - Korkut", "Korkut"),
    ("Merkez - Varto", "Varto"),
    ("Merkez - Muş", "Merkez"),
    ("Bağlar - Muş", "Merkez"),
    ("Muş", "Merkez"),
    ("Merkez - Bingöl", None),
    ("Güroymak - Bitlis", None),
    ("Merkez - Güroymak - Bitlis", None),
    ("Merkez - Solhan - Bingöl", None),
])
def test_ilce_bul_son_parcaya_bakar(yer, beklenen):
    """Muş dışı kayıt Muş'a YAZILMAMALI.

    Bu test bir gerilemeyi önlüyor. Eski sürüm adın herhangi bir
    parçasında Muş ilçesi arıyor, "Merkez - Bingöl"ü Muş Merkez'e
    yazıyordu: 93 yabancı kayıt Muş istatistiğine girmişti.
    """
    assert kalite.analiz.ilce_bul(yer) == beklenen


def test_ilce_bul_bos_girdiye_dayanir():
    for bos in (None, "", "   ", "-", "//"):
        assert kalite.analiz.ilce_bul(bos) is None


# --- rapor bütünlüğü ---------------------------------------------------
def test_rapor_klasor_yoksa_cokmez(tmp_path: Path):
    r = kalite.rapor(tmp_path)
    assert r["var"] is False and r["sebep"]


def test_her_denetimin_agirligi_tanimli():
    ham = [_satir(ph=7.4, om=2.0, kirec=12.0, ec=0.4, tuz=0.02)]
    gecerli = {"ölçümü etkiler", "sütun kullanılmıyor", "yalnızca kayıt"}
    for d in kalite.DENETIMLER:
        s = d(ham)
        assert s["agirlik"] in gecerli, f"{s['ad']}: {s['agirlik']}"
        assert s["ne_yapildi"], f"{s['ad']}: ne yapıldığı yazılmamış"
        assert s["soru"], f"{s['ad']}: hangi soruyu sorduğu yazılmamış"


# --- gerçek veri -------------------------------------------------------
@ham_gerekir
def test_gercek_veride_bilinen_kusurlar_bulunur():
    r = kalite.rapor()
    assert r["var"] and r["n_satir"] > 2000
    ad = {d["ad"]: d for d in r["denetim"]}

    assert ad["Fiziksel olarak imkânsız değerler"]["bulgu"] > 0, (
        "pH 2,06 gibi değerler veride var; bulunmazsa süzgeç bozulmuş")
    assert ad["Yinelenen satırlar"]["ayrinti"]["sans_kati"] > 50, (
        "tekrar şansla açıklanamaz olmalı")
    assert ad["Fosfor ve potasyum birimi"]["oran"] > 90, (
        "fosfor birim tutarsızlığı satırların ezici çoğunluğunda")


@ham_gerekir
def test_mus_disi_kayitlar_modele_girmiyor():
    """216'ya yakın yabancı kayıt var; hiçbiri Muş ilçesine bağlanmamalı."""
    r = kalite.rapor()
    yer = next(d for d in r["denetim"] if d["ad"] == "Yer sütunu")
    k = yer["ayrinti"]["kirilim"]
    assert k["Muş ilçesine bağlandı"] == r["ozet"]["modele_giren_satir"]
    assert k["Muş dışı"] > 200, "Bingöl ve Bitlis kayıtları ayrı sayılmalı"
    assert k.get("belirsiz sıralama", 0) < 10, (
        "gerçekten belirsiz olan kayıt azdır; kesin Muş dışı olanlar "
        "buraya karışmamalı")
    assert "Bingöl" in yer["ayrinti"]["dis_iller"]
