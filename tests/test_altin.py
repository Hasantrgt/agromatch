"""
Altın dosya testi — refactor sırasında sayılar değişmedi mi?

tests/altin/belirsizlik.json, iki hesap yolunu teke indirme refactor'ından
ÖNCE kaydedildi. O refactor'da mus_belirsizlik.py kendi denge formüllerini
bırakıp mus_iz.denge_grafigi()'nden beslenmeye başladı.

Böyle bir değişiklikte tek güvence, çıktının aynı kalmasıdır. Kod tamamen
değişti ama sayılar değişmemeli — değiştiyse refactor sırasında bir şey
bozulmuş demektir.

ALTIN DOSYA NE ZAMAN GÜNCELLENİR
--------------------------------
Yalnızca bir MODEL değişikliği bilerek yapıldığında ve yeni sayının neden
doğru olduğu gerekçelendirildiğinde. Test kırıldı diye altın dosyayı
yenilemek, testin varlık sebebini ortadan kaldırır.
"""

import json
from pathlib import Path

import pytest

import mus_belirsizlik

ALTIN = json.loads(
    (Path(__file__).parent / "altin" / "belirsizlik.json").read_text(encoding="utf-8"))

# Monte Carlo gürültüsü: aynı tohumla aynı örnek çekilse de grafik üzerinden
# hesaplanan dallar farklı sırada örneklendiği için küçük sapma olabilir.
TOLERANS = 0.02


@pytest.fixture(scope="module")
def sonuc():
    return mus_belirsizlik.analiz(n=20000)


def test_ayni_denge_sorulari(sonuc):
    assert [q["anahtar"] for q in sonuc["sorular"]] == \
           [q["anahtar"] for q in ALTIN["sorular"]]


@pytest.mark.parametrize("anahtar", [q["anahtar"] for q in ALTIN["sorular"]])
def test_denge_oranlari_degismedi(sonuc, anahtar):
    yeni = next(q for q in sonuc["sorular"] if q["anahtar"] == anahtar)
    eski = next(q for q in ALTIN["sorular"] if q["anahtar"] == anahtar)

    for alan in ("medyan", "alt90", "ust90"):
        assert yeni["oran"][alan] == pytest.approx(eski["oran"][alan], rel=TOLERANS), (
            f"{anahtar}.{alan}: {yeni['oran'][alan]} != {eski['oran'][alan]}")

    assert yeni["karar"] == eski["karar"]
    assert yeni["esigi_kesiyor"] == eski["esigi_kesiyor"]
    assert yeni["olcek"] == eski["olcek"]


@pytest.mark.parametrize("anahtar", [q["anahtar"] for q in ALTIN["sorular"]])
def test_arz_ve_ihtiyac_degismedi(sonuc, anahtar):
    yeni = next(q for q in sonuc["sorular"] if q["anahtar"] == anahtar)
    eski = next(q for q in ALTIN["sorular"] if q["anahtar"] == anahtar)
    assert yeni["arz_medyan"] == pytest.approx(eski["arz_medyan"], rel=TOLERANS)
    assert yeni["ihtiyac_medyan"] == pytest.approx(eski["ihtiyac_medyan"], rel=TOLERANS)


@pytest.mark.parametrize("anahtar", [q["anahtar"] for q in ALTIN["sorular"]])
def test_baskin_bilinmeyen_ayni(sonuc, anahtar):
    """Baskın bilinmeyen değişmemeli.

    Etiketlerde bilinçli bir fark var: refactor'da birim, etiketin içinden
    çıkıp kendi alanına taşındı ("Mera verimi (ton KM/da)" -> "Mera verimi"
    + birim="ton KM/dekar"). Kimliğin korunduğunu, eski etiketin yenisiyle
    başlamasına bakarak doğruluyoruz.
    """
    yeni = next(q for q in sonuc["sorular"] if q["anahtar"] == anahtar)
    eski = next(q for q in ALTIN["sorular"] if q["anahtar"] == anahtar)

    if eski["baskin"] is None:
        assert yeni["baskin"] is None
        return

    assert eski["baskin"].startswith(yeni["baskin"]["etiket"]), (
        f"{anahtar}: baskın bilinmeyen değişmiş — "
        f"eski '{eski['baskin']}', yeni '{yeni['baskin']['etiket']}'")
    assert yeni["baskin"]["varyans_payi"] == pytest.approx(
        eski["baskin_pay"], abs=3.0)


def test_belirsiz_kalan_karar_ayni(sonuc):
    assert sonuc["belirsiz_karar"] == ALTIN["belirsiz_karar"]


def test_eylem_tablosu_degismedi(sonuc):
    yeni = {r["urun"]: r for r in sonuc["karar"]}
    for eski in ALTIN["karar"]:
        y = yeni[eski["urun"]]
        assert y["eylem"] == eski["eylem"], f"{eski['urun']}: eylem değişmiş"
        assert y["olcek"] == eski["olcek"]
        assert y["oran"] == pytest.approx(eski["oran"], rel=TOLERANS)
        assert y["en_iyi_ilce"] == eski["en_iyi_ilce"]
        assert y["makas"] == pytest.approx(eski["makas"], abs=0.5)
        assert y["yeri_onemli"] == eski["yeri_onemli"]


def test_kaldirac_degismedi(sonuc):
    for alan, deger in ALTIN["kaldirac"].items():
        assert sonuc["kaldirac"][alan] == pytest.approx(deger, rel=TOLERANS), alan


def test_olcum_kazanclari_degismedi(sonuc):
    assert sonuc["masa_basi_kazanc"] == pytest.approx(
        ALTIN["masa_basi_kazanc"], rel=0.10)
    assert sonuc["saha_kazanc"] == pytest.approx(ALTIN["saha_kazanc"], rel=0.10)


# ---------------------------------------------------------------------
#  Refactor'ın asıl kazancı: tek tanım
# ---------------------------------------------------------------------
def test_denge_formulleri_tek_yerde():
    """mus_belirsizlik artık kendi denge formüllerini tutmamalı.

    Bu test bir sayıyı değil, bir MİMARİ KARARI korur: formüllerin ikinci
    bir kopyası geri gelirse kırılır.
    """
    kaynak = (Path(__file__).parent.parent / "src" / "mus_belirsizlik.py"
              ).read_text(encoding="utf-8")
    for yasak in ("def denge_kaba_yem", "def denge_pancar", "def denge_bugday",
                  "def ornekle(", "def s1_indisi(", "GIRDI = {", "SORU = {"):
        assert yasak not in kaynak, (
            f"denge formülü / örnekleme kopyası geri gelmiş: {yasak}")


def test_belirsizlik_grafikten_besleniyor():
    kaynak = (Path(__file__).parent.parent / "src" / "mus_belirsizlik.py"
              ).read_text(encoding="utf-8")
    assert "mus_iz.denge_grafigi()" in kaynak
