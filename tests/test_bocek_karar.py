"""Böcek karar sisteminin testleri.

NEDEN VAR: Bu modülün çıktısı doğrudan "tarlaya ne uygulanmalı"
sorusunu cevaplıyor. Burada bir hata, kataloglardaki hatadan farklı:
yanlış bir liste okunup geçilir, yanlış bir KARAR uygulanır.

En kritik iki kural sınanıyor:
  - Eşiği bilinmeyen zararlıya ilaçlama önerilmemeli.
  - Adımların SIRASI değişmemeli; "hangi ilaç" sorusu eşikten ve
    kalıntısız yoldan sonra gelmeli. Sıra bozulursa cevap baştan
    ilaçlamaya sabitlenir.
"""

from __future__ import annotations

import pytest

from bocek import karar as kr
from bocek import pestisit as pe
from bocek import tarla_zararli as tz


def test_bilinmeyen_zararli_cokmez():
    d = kr.karar("Olmayan Böcek")
    assert d["var"] is False and d["sebep"]


@pytest.mark.parametrize("ad", [z["ad"] for z in tz.ZARARLILAR])
def test_her_zararli_icin_dort_adim(ad: str):
    d = kr.karar(ad)
    assert d["var"] is True
    assert [a["adim"] for a in d["adimlar"]] == [1, 2, 3, 4], (
        f"{ad}: adım sırası bozulmuş")
    for a in d["adimlar"]:
        assert a["durum"], f"{ad} adım {a['adim']}: durum boş"
        assert a["aciklama"], f"{ad} adım {a['adim']}: açıklama boş"


def test_adim_sirasi_esikle_basliyor():
    """İlk düğüm eşik olmalı, ilaç değil."""
    d = kr.karar("Süne")
    assert d["adimlar"][0]["ad"] == "İlaçlamalı mı"
    assert d["adimlar"][1]["ad"] == "İlaçsız çözülür mü"
    assert d["adimlar"][2]["ad"] == "İlaç gerekiyorsa hangisi"


@pytest.mark.parametrize("ad", [z["ad"] for z in tz.ZARARLILAR])
def test_esigi_bilinmeyen_zararliya_ilaclama_onerilmiyor(ad: str):
    """Eşik yoksa 1. adım bunu açıkça söylemeli.

    Eşiksiz ilaçlama önerisi, projenin yapmayacağı tek şeydir: zararlının
    varlığı tek başına zarar demek değildir.
    """
    d = kr.karar(ad)
    esik_adimi = d["adimlar"][0]
    z = next(x for x in tz.ZARARLILAR if x["ad"] == ad)
    if not z.get("esik"):
        assert esik_adimi["durum"] == "eşik bilinmiyor", ad
        assert "önerilmez" in esik_adimi["aciklama"] \
            or "verilmez" in esik_adimi["aciklama"], ad


@pytest.mark.parametrize("ad", [z["ad"] for z in tz.ZARARLILAR])
def test_urun_adi_ve_doz_sizmiyor(ad: str):
    """Karar sistemi etki grubuna kadar götürür; reçete yazmaz.

    Ticari ad, doz ve bekleme süresi bilerek yok. Biri sonradan
    eklerse bu test yakalar.
    """
    import json
    metin = json.dumps(kr.karar(ad), ensure_ascii=False).lower()
    for yasak in ("ml/da", "gr/da", "g/da", "cc/da", "bekleme süresi",
                  "hasat öncesi gün"):
        assert yasak not in metin, f"{ad}: '{yasak}' sızmış — doz/reçete"


def test_ilac_secenekleri_faydali_yukune_gore_sirali():
    """En az faydalı vuran grup önce gelmeli."""
    for z in tz.ZARARLILAR:
        s = kr.karar(z["ad"])["adimlar"][2]["secenekler"]
        zarar = [x["canliya_zarar"] for x in s]
        assert zarar == sorted(zarar), f"{z['ad']}: yük sıralaması bozuk"


def test_yalnizca_kimyasal_gruplar_ucuncu_adimda():
    """Kalıntısız yollar 2. adımda; 3. adıma karışmamalı."""
    for z in tz.ZARARLILAR:
        for s in kr.karar(z["ad"])["adimlar"][2]["secenekler"]:
            assert s["grup"] in pe.KIMYASAL, (
                f"{z['ad']}: {s['grup']} kimyasal değil ama 3. adımda")


def test_kalintisiz_yol_yoksa_oyle_yaziliyor():
    """Boş liste bir cevaptır, eksiklik değil."""
    for z in tz.ZARARLILAR:
        a = kr.karar(z["ad"])["adimlar"][1]
        if not a["secenekler"]:
            assert a["durum"] == "yok"
            assert "YOK" in a["aciklama"] or "yok" in a["aciklama"]


def test_sune_olcumle_karar_veriyor():
    """Ölçüm verilince 1. adım gerçek karara dönüşmeli."""
    olcumsuz = kr.karar("Süne")["adimlar"][0]
    olculu = kr.karar("Süne", ergin_m2=2.5, parazitlenme=20.0)["adimlar"][0]
    assert olcumsuz["durum"] != olculu["durum"], (
        "ölçüm verilmesi kararı değiştirmedi")
    assert olculu.get("ayrinti"), "süne kararının ayrıntısı taşınmamış"


def test_bosluklar_durust():
    b = kr.bosluklar()
    for alan in ("esigi_bilinmeyen", "kalintisiz_yolu_olmayan",
                 "hicbir_secenegi_olmayan"):
        assert alan in b
        assert isinstance(b[alan], list)
    adlar = {z["ad"] for z in tz.ZARARLILAR}
    for alan in ("esigi_bilinmeyen", "kalintisiz_yolu_olmayan"):
        assert set(b[alan]) <= adlar, f"{alan}: kayıtlı olmayan zararlı var"


def test_ozet_cumlesi_her_zararli_icin_uretiliyor():
    for z in tz.ZARARLILAR:
        o = kr.karar(z["ad"])["ozet"]
        assert o and z["ad"] in o, f"{z['ad']}: özet cümlesi eksik"
