"""İlçe hayvan varlığı ölçümünün testleri.

NEDEN VAR: Bu veri, projenin en büyük bulgusunu — ilçe kaba yem açığını —
doğrudan belirliyor. Yanlış girilmiş tek bir rakam, bir ilçenin yem
açığını ikiye katlar ya da yarıya indirir ve bunu hiçbir şey fark etmez.

Veri, Muş İl Tarım ve Orman Müdürlüğü'nün yayımlanmış 2025 faaliyet
raporundan elle aktarıldı. Elle aktarmanın tek güvencesi, aktarılan
sayıların kendi toplamlarını tutmasıdır — raporun yazdığı toplamlar
burada sabit olarak duruyor ve testler her çalıştığında kontrol ediliyor.
"""

from __future__ import annotations

import pytest

import mus_profil as mp

# Raporun KENDİ yazdığı toplamlar. Aktarım doğruysa satırlar bunları
# tutar. Tutmuyorsa bir rakam yanlış girilmiş demektir.
RAPOR_TOPLAM = {"buyukbas": 275455, "kucukbas": 1379272,
                "kovan": 57931, "isletme": 21318}


@pytest.mark.parametrize("sutun,ad", list(enumerate(RAPOR_TOPLAM)))
def test_aktarilan_sayilar_raporun_toplamini_tutuyor(sutun: int, ad: str):
    toplam = sum(v[sutun] for v in mp.HAYVAN_ILCE.values())
    assert toplam == RAPOR_TOPLAM[ad], (
        f"{ad}: satırların toplamı {toplam:,}, raporun yazdığı "
        f"{RAPOR_TOPLAM[ad]:,}. Bir rakam yanlış aktarılmış.")


def test_butun_ilceler_var():
    assert set(mp.HAYVAN_ILCE) == set(mp.ILCE), "ilçe listesi tutmuyor"


def test_il_toplami_tuik_degerinde_kaliyor():
    """Ölçümden alınan PAY, toplam değil.

    Dengenin arz tarafı (mera, yem üretimi) baştan sona TÜİK 2024 ile
    kurulu. Yalnızca hayvan toplamını başka bir kayıttan almak,
    dengenin iki yakasını farklı kaynaklardan beslemek olurdu.
    """
    assert sum(v[2] for v in mp.ILCE.values()) == mp.OLCUM["buyukbas"][0]
    assert sum(v[3] for v in mp.ILCE.values()) == mp.OLCUM["kucukbas"][0]


def test_iki_tur_ayri_dagiliyor():
    """Projenin düzeltilen hatası: iki tür aynı oranda dağılmıyor.

    Bu test bir gerilemeyi önlüyor. Eski sürüm büyükbaş ile küçükbaşı
    TEK bir ilçe payıyla (h_pay) dağıtıyordu. Gerçek veri bunu
    desteklemiyor: Merkez il küçükbaşının yarısını barındırırken
    sığırın dörtte birine sahip.
    """
    bb = mp._hayvan_payi(0)
    kb = mp._hayvan_payi(1)
    assert bb != kb, "iki tür aynı payla dağıtılıyor — ölçüm bağlanmamış"
    assert kb["Merkez"] > 0.45, "Merkez küçükbaşın yarısına yakınını tutuyor"
    assert kb["Malazgirt"] < 0.10, "Malazgirt küçükbaşta küçük pay"
    assert bb["Malazgirt"] > 0.15, "ama büyükbaşta büyük pay"


def test_paylar_bire_tamamlaniyor():
    for tur in (0, 1):
        assert sum(mp._hayvan_payi(tur).values()) == pytest.approx(1.0)


def test_olcum_kapatilabiliyor():
    """Ölçüm bir iyileştirmedir, önkoşul değil.

    Kapatıldığında eski varsayıma dönebilmeli; dönemezse "ölçümün ne
    değiştirdiği" sorusu ölçülemez hâle gelir.
    """
    eski = mp.HAYVAN_OLCUM_KULLAN
    try:
        mp.HAYVAN_OLCUM_KULLAN = False
        h_pay = mp.PAY["Merkez"][4]
        bb, kb = mp._ilce_hayvan("Merkez", h_pay)
        assert bb == round(mp.OLCUM["buyukbas"][0] * h_pay)
        assert kb == round(mp.OLCUM["kucukbas"][0] * h_pay)
    finally:
        mp.HAYVAN_OLCUM_KULLAN = eski


def test_olcumde_olmayan_ilce_varsayima_duser():
    eski = dict(mp.HAYVAN_ILCE)
    try:
        mp.HAYVAN_ILCE.pop("Korkut")
        h_pay = mp.PAY["Korkut"][4]
        bb, kb = mp._ilce_hayvan("Korkut", h_pay)
        assert bb == round(mp.OLCUM["buyukbas"][0] * h_pay)
        assert kb == round(mp.OLCUM["kucukbas"][0] * h_pay)
    finally:
        mp.HAYVAN_ILCE.clear()
        mp.HAYVAN_ILCE.update(eski)


def test_kaynak_yazili():
    assert "faaliyet" in mp.HAYVAN_KAYNAK.lower()
    assert "2025" in mp.HAYVAN_KAYNAK


def test_kunye_ilce_dagiliminin_olcum_oldugunu_soyluyor():
    """Künye, ilçe dağılımının artık tahmin olmadığını yazmalı."""
    satir = [k for k in mp.KUNYE if k[0] == "Hayvan varlığı"]
    assert satir, "künyede hayvan varlığı satırı yok"
    not_ = satir[0][5]
    assert "ÖLÇÜM" in not_, "ilçe dağılımının ölçüm olduğu yazılmamış"
    assert "275.455" in not_, "bakanlık toplamıyla farkı yazılmamış"
