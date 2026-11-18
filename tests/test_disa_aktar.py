"""Veri paketi: her veri seti üretiliyor mu, künye eksiksiz mi.

Bu dosyanın sebebi: paket danışman hocaya gidiyor ve eksik bir veri seti
sessizce düşerse kimse fark etmez. Buradaki testler paketin kapsamını
sabitliyor — yeni veri seti eklemek serbest, çıkarmak testi kırar.
"""

from __future__ import annotations

import csv

import pytest

import disa_aktar as da

# Paketin bugünkü kapsamı. Yeni veri seti eklerken bu listeye de ekle;
# bir şey çıkarılıyorsa bilerek çıkarıldığı buradan görünsün.
BEKLENEN = {
    "00_veri_kunyesi", "hastalik_katalogu", "hastalik_risk",
    "hastalik_ilce_ozeti", "hastalik_aylik_takvim",
    "goruntuden_tespit_onceligi",
    "tarla_zararlilari", "faydalilar", "etki_gruplari", "zararli_takvimi",
    "depo_zararlilari", "depo_mucadele",
    "literatur_doz_cevap", "doz_cevap_kestirim", "yayin_kunyeleri",
    "deneme_sablonu",
    "ambar_sicakligi", "gelisme_penceresi", "erken_uyari_takvimi",
    "karlilik", "piyasa_girdileri",
    "urun_denge", "ilce_profili", "il_uretim", "alan_olcumleri",
    "yem_dengesi", "su_ve_karbon", "ilce_karnesi", "ilce_onerileri",
    "seker_kotasi",
    "toprak_uygunluk_modeli", "ilce_toprak_profili", "urun_toprak_istegi",
    "puan_agirliklari", "olcum_duyarliligi",
    "olcum_oncelikleri", "denge_karari", "hesap_izi_belirsiz_girdiler",
    "toprak_uygunluk", "cercospora_lezyon",
    # Kasım 2026 — laboratuvar ölçümleri ve çölleşme katmanı
    "toprak_olcum_ilce", "toprak_bunye_dagilimi", "olcum_etkisi",
    "collesme_dsi", "collesme_kaldiraclari",
}


def test_kapsam_daralmadi():
    """Veri seti çıkarılmışsa test kırılsın; eklemek serbest."""
    var = {ad for ad, *_ in da.KAYIT}
    assert var >= BEKLENEN, f"paketten düşen veri seti: {BEKLENEN - var}"


def test_her_veri_setinin_turu_tanimli():
    for ad, _aciklama, tur, _f in da.KAYIT:
        assert tur in da.TUR_ACIKLAMA, f"{ad}: bilinmeyen tür {tur}"


def test_her_veri_setinin_aciklamasi_var():
    for ad, aciklama, _tur, _f in da.KAYIT:
        assert len(aciklama) > 20, f"{ad}: açıklama çok kısa"


def test_ad_yinelenmiyor():
    adlar = [ad for ad, *_ in da.KAYIT]
    assert len(adlar) == len(set(adlar))


def test_sentetik_olanlar_isaretli():
    """Sentetik veri gerçek sanılırsa en büyük zarar burada olur."""
    sentetik = {ad for ad, _a, tur, _f in da.KAYIT if tur == "sentetik"}
    assert sentetik == {"toprak_uygunluk", "cercospora_lezyon"}
    assert "GERÇEK VERİ DEĞİLDİR" in da.TUR_ACIKLAMA["sentetik"]


def test_pestisit_veri_seti_urun_adi_icermiyor():
    """Reçete yetkisi olmayan bir yazılım ilaç adı yayımlamaz."""
    satir = next(a for a in da.KAYIT if a[0] == "etki_gruplari")
    assert "ÜRÜN ADI VE DOZ İÇERMEZ" in satir[1]


@pytest.fixture(scope="module")
def paket(tmp_path_factory, monkeypatch_session=None):
    """Paketi geçici bir dizine üretir; depoyu kirletmez."""
    gecici = tmp_path_factory.mktemp("veri")
    eski = da.HEDEF
    da.HEDEF = gecici
    try:
        sayilar = {ad: f() for ad, _a, _t, f in da.KAYIT}
        da._yaz("00_KUNYE",
                ["veri_seti", "satir", "tur", "tur_ne_demek", "aciklama"],
                da.kunye(sayilar))
        yield gecici, sayilar
    finally:
        da.HEDEF = eski


def test_her_veri_seti_iki_bicimde_de_yaziliyor(paket):
    gecici, _ = paket
    for ad, *_ in da.KAYIT:
        assert (gecici / "csv" / f"{ad}.csv").exists(), ad
        assert (gecici / "csv_excel" / f"{ad}_excel.csv").exists(), ad


def test_excel_surumu_noktali_virgul_ve_bom(paket):
    """Düz CSV Excel'de açılırsa Türkçe bozulur; ikisi ayrı olmalı."""
    gecici, _ = paket
    ham = (gecici / "csv_excel" / "hastalik_katalogu_excel.csv").read_bytes()
    assert ham.startswith(b"\xef\xbb\xbf"), "BOM yok"
    ilk = ham.decode("utf-8-sig").splitlines()[0]
    assert ilk.count(";") > ilk.count(","), "ayraç noktalı virgül değil"

    duz = (gecici / "csv" / "hastalik_katalogu.csv").read_bytes()
    assert not duz.startswith(b"\xef\xbb\xbf"), "düz sürümde BOM olmamalı"


def test_bos_veri_seti_yok(paket):
    _gecici, sayilar = paket
    bos = [ad for ad, n in sayilar.items() if n == 0]
    assert not bos, f"boş veri seti: {bos}"


def test_kunye_butun_veri_setlerini_listeliyor(paket):
    gecici, sayilar = paket
    with open(gecici / "csv" / "00_KUNYE.csv", encoding="utf-8") as f:
        satir = list(csv.DictReader(f))
    assert {s["veri_seti"] for s in satir} == {ad for ad, *_ in da.KAYIT}
    for s in satir:
        assert int(s["satir"]) == sayilar[s["veri_seti"]]


def test_doz_cevap_verisi_yayin_kunyesini_tasiyor(paket):
    """Hocanın en çok kullanacağı dosya; DOI'siz satır olmamalı."""
    gecici, _ = paket
    with open(gecici / "csv" / "literatur_doz_cevap.csv", encoding="utf-8") as f:
        satir = list(csv.DictReader(f))
    assert satir
    for s in satir:
        assert s["doi"].startswith("10."), s
        assert int(s["denenen"]) > 0 and int(s["olen"]) >= 0
        assert 0 <= float(s["olum_yuzde"]) <= 100
