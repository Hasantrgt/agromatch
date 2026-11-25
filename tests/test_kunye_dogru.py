"""Künye, verinin gerçek durumunu söylüyor mu.

NEDEN VAR: Bu projenin bütün iddiası, her sayının kaynağının dürüstçe
etiketlenmesine dayanıyor. Panelin her yerinde ÖLÇÜM / VARSAYIM / DAĞITIM
rozetleri var ve okuyan kişi onlara güveniyor.

Bu etiketler SESSİZCE ÇÜRÜR. Bir ölçüm katmanı bağlanır, veri gerçek
olur, ama künye satırı "varsayım" demeye devam eder. Hiçbir test kırılmaz,
hiçbir hata çıkmaz — yalnızca panel yalan söylemeye başlar. Nitekim tam
bu oldu: laboratuvar verisi, ilçe hayvan sayıları ve ölçülen verim
bağlandıktan sonra künyede üç satır hâlâ "ölçülmedi" diyordu.

Aşağıdaki testler, ölçüm katmanı OLAN alanların künyede ölçüm olarak
işaretli kalmasını zorunlu kılıyor. Biri geri alınırsa test kırılır ve
düzeltme unutulamaz.
"""

from __future__ import annotations

import pytest

import mus_profil as mp

# künye alanı -> o alanın ölçüm olduğunu kanıtlayan şey
OLCUME_BAGLI = {
    "Hayvan varlığı": "HAYVAN_ILCE",
    "Verim (ton/dekar)": "VERIM_OLCUM",
    "Toprak parametreleri": None,   # ayrı modülde, aşağıda sınanıyor
    "Ekim alanı": "VERIM_OLCUM",
    "Ürün üretimi (ton)": None,
}

GECERLI_TUR = {"ölçüm", "varsayım", "dağıtım", "literatür", "sentetik"}


def _satir(ad: str):
    for k in mp.KUNYE:
        if k[0] == ad:
            return k
    raise AssertionError(f"künyede '{ad}' satırı yok")


@pytest.mark.parametrize("ad", list(OLCUME_BAGLI))
def test_olcum_baglanan_alan_kunyede_olcum(ad: str):
    """Ölçüm katmanı bağlıysa künye 'varsayım' diyemez."""
    assert _satir(ad)[1] == "ölçüm", (
        f"'{ad}' için ölçüm bağlı ama künye '{_satir(ad)[1]}' diyor. "
        "Künye çürümüş — etiket veriyle birlikte güncellenmeli.")


@pytest.mark.parametrize("ad,sabit", [(a, s) for a, s in OLCUME_BAGLI.items() if s])
def test_dayanak_gercekten_duruyor(ad: str, sabit: str):
    """Künyeyi 'ölçüm' yapan veri hâlâ yerinde mi.

    Etiketi doğru tutmak yetmez: etiketin dayandığı veri silinirse
    künye yine yalan söyler, bu sefer ters yönde.
    """
    veri = getattr(mp, sabit, None)
    assert veri, f"{sabit} boş ya da yok — '{ad}' artık ölçüm değil"


def test_toprak_olcumu_gercekten_bagli():
    """Toprak künyesi, laboratuvar katmanı bağlıysa ölçüm olmalı."""
    try:
        from toprak_olcum.analiz import olcum_katmani
    except ImportError:
        pytest.skip("toprak_olcum modülü yok")
    katman = olcum_katmani()
    if not katman:
        pytest.skip("laboratuvar verisi bağlı değil (temiz klon olabilir)")
    assert _satir("Toprak parametreleri")[1] == "ölçüm"


def test_her_satirin_turu_tanimli():
    for k in mp.KUNYE:
        assert k[1] in GECERLI_TUR, f"{k[0]}: bilinmeyen tür {k[1]!r}"


def test_varsayim_kalanlar_gerekcesini_yaziyor():
    """Hâlâ varsayım olan alan, neyle değişeceğini söylemeli.

    "Varsayım" demek yeterli değil; okuyanın bunun nasıl kapanacağını
    görmesi gerekir. Projenin baştan beri uyguladığı kural bu.
    """
    for k in mp.KUNYE:
        if k[1] != "varsayım":
            continue
        not_ = k[5]
        assert len(not_) > 20, f"{k[0]}: varsayım ama gerekçe yazılmamış"


def test_olcum_satirlari_kaynagini_adlandiriyor():
    for k in mp.KUNYE:
        if k[1] != "ölçüm":
            continue
        assert len(k[2]) > 10, f"{k[0]}: ölçüm ama kaynağı yazılmamış"


def test_eski_yanlis_ifadeler_geri_gelmedi():
    """Düzeltilen üç yanlış ifade bir daha künyeye girmesin.

    Bunlar bir zamanlar doğruydu ve veri değişince yanlış oldu. Geri
    dönerlerse yine yanlış olurlar.
    """
    tum = " ".join(k[5] for k in mp.KUNYE)
    for ifade in ("Ölçülmedi. Verim değişirse",
                  "Fiğ ve kuru fasulye belgede yok",
                  "üniversite laboratuvarı analizleriyle değiştirilecek"):
        assert ifade not in tum, f"künyeye eski yanlış ifade dönmüş: {ifade!r}"
