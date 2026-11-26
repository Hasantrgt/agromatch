"""Depo karar sisteminin testleri.

NEDEN VAR: Bu modülün verebileceği en pahalı yanlış tavsiye şudur —
taneyi İÇERİDEN yiyen bir larvaya karşı yüzeye uygulanan bir yöntemi
(diyatomlu toprak gibi) yeterliymiş gibi sunmak. Çiftçi doğru uygular,
erginleri öldürür, içerideki larvalar gelişmeye devam eder, ürün yine
kaybedilir — üstelik "kalıntısız yol işe yaramıyor" kanaatiyle.

Bu testlerin çoğu o tek hatayı kovalıyor.
"""

from __future__ import annotations

import pytest

from depo import depo_profil as dp
from depo import karar as dk


def test_bilinmeyen_zararli_cokmez():
    d = dk.karar("Olmayan Böcek")
    assert d["var"] is False and d["sebep"]


@pytest.mark.parametrize("ad", [z["ad"] for z in dp.ZARARLILAR])
def test_her_zararli_icin_dort_adim(ad: str):
    d = dk.karar(ad)
    assert d["var"] is True
    assert [a["adim"] for a in d["adimlar"]] == [1, 2, 3, 4], f"{ad}: sıra bozuk"
    for a in d["adimlar"]:
        assert a["durum"] and a["aciklama"], f"{ad} adım {a['adim']}"


def test_ilk_adim_bocegin_yerini_soruyor():
    """Karar ağacının ilk düğümü 'hangi ilaç' değil, 'böcek nerede'."""
    d = dk.karar("Buğday biti")
    assert d["adimlar"][0]["ad"] == "Böcek nerede"


@pytest.mark.parametrize("ad", [z["ad"] for z in dp.ZARARLILAR
                                if z["ic_besleyen"]])
def test_ic_besleyende_yuzey_yontemi_ulasan_listesine_girmiyor(ad: str):
    """EN KRİTİK TEST.

    İç besleyen zararlıda, iç larvaya etki etmeyen hiçbir yöntem
    "ulaşan" sayılamaz. Diyatomlu toprak bu yüzden buğday bitinde
    ulaşmayanlar listesinde olmalı.
    """
    a = dk.karar(ad)["adimlar"][1]
    for y in a["ulasan"]:
        assert y["ic_larvaya"] is True, (
            f"{ad}: '{y['ad']}' iç larvaya etki etmiyor ama ULAŞAN "
            "listesinde — yanlış tavsiye üretir")


def test_bugday_bitinde_diyatom_ulasmayanlarda():
    """Somut vaka: projenin baştan beri konuştuğu diatom örneği."""
    a = dk.karar("Buğday biti")["adimlar"][1]
    ulasmayan = [y["ad"] for y in a["ulasmayan"]]
    assert any("Diyatom" in x for x in ulasmayan), (
        "Buğday biti taneyi içeriden yer; diyatomlu toprak ona ulaşmaz "
        "ve ulaşmayanlar listesinde olmalı")


@pytest.mark.parametrize("ad", [z["ad"] for z in dp.ZARARLILAR
                                if not z["ic_besleyen"]])
def test_yuzeyde_beslenende_kalintisiz_yollar_ulasiyor(ad: str):
    a = dk.karar(ad)["adimlar"][1]
    assert a["ulasan"], f"{ad}: yüzeyde besleniyor ama ulaşan yol yok"
    assert not a["ulasmayan"], (
        f"{ad}: yüzeyde beslenen zararlıda 'ulaşmayan' olmamalı")


@pytest.mark.parametrize("ad", [z["ad"] for z in dp.ZARARLILAR])
def test_kalintili_yontem_ikinci_adimda_yok(ad: str):
    """2. adım yalnızca kalıntısız yolları gösterir."""
    kalintili = {m["ad"] for m in dp.MUCADELE if m["kalinti"]}
    a = dk.karar(ad)["adimlar"][1]
    for y in a["ulasan"] + a["ulasmayan"]:
        assert y["ad"] not in kalintili, f"{ad}: {y['ad']} kalıntılı"


def test_kosul_adimi_olculmus_sayilari_tasiyor():
    """Diyatom önerilen yerde 37 kat farkın sayıları görünmeli.

    Koşulu söylemeden diyatom önermek tavsiye değil kura çekmektir;
    bu test o sayıların kaybolmamasını garanti ediyor.
    """
    a = dk.karar("Kırma biti")["adimlar"][2]
    assert a["durum"] == "koşula bağlı"
    o = a["olcum"]
    assert o and o["dusuk"]["olum"] < 10 and o["yuksek"]["olum"] > 50
    assert o["kat"] > 10
    for parca in (str(int(o["dusuk"]["olum"])), str(int(o["yuksek"]["olum"]))):
        assert parca in a["aciklama"], "ölçülmüş sayı açıklamada yok"


def test_fumigasyon_son_care_olarak_konumlanmis():
    """Kalıntısız yol varken fumigasyon ilk seçenek gibi sunulmamalı."""
    for z in dp.ZARARLILAR:
        d = dk.karar(z["ad"])
        a = d["adimlar"][3]
        if d["adimlar"][1]["ulasan"]:
            assert a["durum"] == "önce diğerleri", z["ad"]
            assert "ilk seçenek değildir" in a["aciklama"], z["ad"]


def test_doz_ve_urun_adi_sizmiyor():
    import json
    for z in dp.ZARARLILAR:
        metin = json.dumps(dk.karar(z["ad"]), ensure_ascii=False).lower()
        for yasak in ("gr/ton", "ml/ton", "bekleme süresi"):
            assert yasak not in metin, f"{z['ad']}: '{yasak}' sızmış"


def test_ozet_ic_besleyenleri_sayiyor():
    o = dk.ozet()
    gercek = {z["ad"] for z in dp.ZARARLILAR if z["ic_besleyen"]}
    assert set(o["ic_besleyen"]) == gercek
    assert o["yuzey_uygulamasi_yetmeyen"] == len(gercek)


def test_her_zararlinin_ozet_cumlesi_var():
    for z in dp.ZARARLILAR:
        o = dk.karar(z["ad"])["ozet"]
        assert o and z["ad"] in o
