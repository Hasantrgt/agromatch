"""
Panel üretiminin testleri.

Panelin kaynağı src/panel/ altında parçalı, çıktısı tek dosya. Bu testler
birleştirmenin doğru çalıştığını ve parçalı yapının bozulmadığını korur.

Tek dosya çıktısı bilinçli bir karar: panelin dış bağlantı olmadan, bir USB
bellekten ya da e-posta ekinden açılabilmesi gerekiyor. Kaynağın parçalı
olması ayrı bir ihtiyaç — 1.100 satırlık tek bir betiğe birden fazla kişi
dokunamaz.
"""

import re
from pathlib import Path

import pytest

import mus_panel_uret

PANEL = Path(__file__).resolve().parent.parent / "src" / "panel"


# --------------------------------------------------------- kaynak yapısı
def test_panel_kaynagi_parcali():
    for ad in ("bas.html", "stil.css", "govde.html"):
        assert (PANEL / ad).exists(), f"{ad} yok"
    assert (PANEL / "js").is_dir()


def test_js_dosyalari_sira_numarali():
    """Yükleme sırası önemli: yardımcılar sekmelerden, sekmeler
    yönlendirmeden önce gelmeli. Sıra ad sıralamasıyla sağlanıyor."""
    dosyalar = sorted(d.name for d in (PANEL / "js").glob("*.js"))
    assert dosyalar, "betik dosyası yok"
    for ad in dosyalar:
        assert re.match(r"^\d{2}_", ad), f"{ad}: sıra numarası yok"

    assert dosyalar[0].startswith("00_"), "veri dosyası ilk sırada olmalı"
    assert dosyalar[-1].startswith("90_"), "yönlendirme son sırada olmalı"
    # Yardımcılar bütün sekmelerden önce
    ortak = next(i for i, a in enumerate(dosyalar) if "ortak" in a)
    ilk_sekme = next(i for i, a in enumerate(dosyalar) if "sekme" in a)
    assert ortak < ilk_sekme


def test_hicbir_js_dosyasi_asiri_uzun():
    """Parçalamanın amacı buydu; bir dosya yeniden şişerse bölünmeli."""
    for d in (PANEL / "js").glob("*.js"):
        satir = len(d.read_text(encoding="utf-8").splitlines())
        assert satir < 260, f"{d.name}: {satir} satır — bölünmeli"


def test_eski_tek_dosya_sablon_kaldirildi():
    assert not (PANEL.parent / "mus_sablon.html").exists(), (
        "eski tek dosyalık şablon geri gelmiş; iki kaynak olur")


# ------------------------------------------------------------ birleştirme
@pytest.fixture(scope="module")
def sablon():
    return mus_panel_uret.sablonu_birlestir()


def test_sablon_butun_parcalari_icerir(sablon):
    assert "<style>" in sablon and "</style>" in sablon
    assert "<script>" in sablon and "</script>" in sablon
    assert "<title>" in sablon
    # Her betik dosyası çıktıda bir ayraçla görünmeli
    for d in (PANEL / "js").glob("*.js"):
        assert f"===== {d.name}" in sablon, f"{d.name} birleştirmeye girmemiş"


def test_sablon_yer_tutuculari_tasir(sablon):
    for yer in ("__MUS_JSON__", "__TOPRAK_JSON__", "__HASTALIK_JSON__",
                "__CERCOSPORA_JSON__", "__BELIRSIZLIK_JSON__", "__IZ_JSON__"):
        assert yer in sablon, f"{yer} şablonda yok"


def test_butun_sekme_fonksiyonlari_tanimli(sablon):
    """Yönlendirme listesindeki her fonksiyonun tanımı birleşik çıktıda olmalı.

    Parçalı kaynakta bir dosya unutulursa burada yakalanır: sekme listesi
    90_uygulama.js'te, tanımlar başka dosyalarda.
    """
    liste = re.search(r"const SEKMELER = \[(.*?)\];", sablon, re.S)
    assert liste, "SEKMELER listesi bulunamadı"
    cagrilan = re.findall(r"(sekme\w+)\]", liste.group(1))
    assert len(cagrilan) >= 8, f"beklenenden az sekme: {cagrilan}"
    for fn in cagrilan:
        assert f"function {fn}(" in sablon, f"{fn} tanımı yok"


def test_tema_belirtecleri_tam(sablon):
    """Üç tema durumu da tanımlı olmalı: açık, koyu (sistem), koyu (seçim)."""
    assert ":root {" in sablon
    assert "@media (prefers-color-scheme: dark)" in sablon
    assert ':root[data-theme="dark"]' in sablon


# ------------------------------------------------------------- çıktı
@pytest.mark.yavas
def test_panel_uretiliyor(panel):
    html = panel.read_text(encoding="utf-8")
    assert len(html) > 100_000
    for yer in ("__MUS_JSON__", "__TOPRAK_JSON__", "__HASTALIK_JSON__",
                "__BELIRSIZLIK_JSON__", "__IZ_JSON__"):
        assert yer not in html, f"doldurulmamış yer tutucu: {yer}"


@pytest.mark.yavas
def test_panel_dis_baglanti_kullanmiyor(panel):
    """Panel tek dosya olmalı: yazı tipi dışında dış kaynak yüklememeli.

    Bir USB bellekten ya da e-posta ekinden açıldığında çalışması gerekiyor.
    """
    html = panel.read_text(encoding="utf-8")
    kaynaklar = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    izinli = ("fonts.googleapis.com", "fonts.gstatic.com")
    disarida = [k for k in kaynaklar if not any(i in k for i in izinli)]
    assert not disarida, f"panel dışarıdan kaynak yüklüyor: {disarida}"
