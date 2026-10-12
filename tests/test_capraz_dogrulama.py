"""
Çapraz doğrulama ve uçtan uca testler.

Buradaki testler yavaştır (Monte Carlo, panel üretimi) ve `yavas` işaretiyle
ayrılmıştır. Hızlı geri bildirim için atlanabilirler:

    pytest -m "not yavas"       # sadece hızlı testler
    pytest                      # hepsi
"""

import json
from pathlib import Path

import pytest

import mus_analiz
import mus_belirsizlik
import mus_iz
import mus_profil as mp
import mus_toprak

KOK = Path(__file__).resolve().parent.parent


# =====================================================================
#  Tek kaynak: denge formülleri yalnızca grafikte
# =====================================================================
# Bir zamanlar mus_belirsizlik ve mus_iz aynı altı dengeyi ayrı ayrı
# hesaplıyordu ve bu test ikisini karşılaştırıyordu. İki kopya tutmak
# bakım borcuydu: formül değişince biri unutulurdu. Refactor'da formüller
# tek yere, mus_iz.denge_grafigi()'ne taşındı.
#
# Karşılaştıracak ikinci bir yol kalmadığı için koruma görevi artık
# tests/test_altin.py'de: refactor öncesi çıktı altın dosya olarak
# kaydedildi ve sayıların değişmediği orada doğrulanıyor.
#
# Burada kalan test, iki modülün AYNI grafiği kullandığını doğrular.

@pytest.mark.yavas
def test_iki_modul_ayni_grafigi_kullanir():
    grafik = mus_iz.denge_grafigi()
    belirsiz = mus_belirsizlik.analiz(n=20000)

    assert set(grafik) == {q["anahtar"] for q in belirsiz["sorular"]}

    for anahtar, kayit in grafik.items():
        q = next(x for x in belirsiz["sorular"] if x["anahtar"] == anahtar)
        assert q["baslik"] == kayit["baslik"]
        assert q["olcek"] == kayit["olcek"]
        assert q["urunler"] == kayit["urunler"]
        # Noktasal değerler grafikten geliyor mu
        assert q["arz_medyan"] == pytest.approx(kayit["arz"].deger(), rel=0.15)


@pytest.mark.yavas
def test_dogrula_komutu_calisir():
    """python src/mus_iz.py --dogrula komutunun kullandığı fonksiyon."""
    assert mus_iz.dogrula() is True


# =====================================================================
#  Belirsizlik analizinin iç tutarlılığı
# =====================================================================
@pytest.mark.yavas
def test_yuzdelikler_sirali():
    s = mus_belirsizlik.analiz(n=20000)
    for q in s["sorular"]:
        o = q["oran"]
        assert o["alt90"] <= o["medyan"] <= o["ust90"], q["baslik"]


@pytest.mark.yavas
def test_duyarlilik_paylari_bir_asmaz():
    """Birinci mertebe indislerin toplamı 1'i aşamaz; fark etkileşimdir."""
    s = mus_belirsizlik.analiz(n=20000)
    for q in s["sorular"]:
        toplam = sum(d["s1"] for d in q["duyarlilik"])
        assert 0 <= toplam <= 1.05, f"{q['baslik']}: S1 toplamı {toplam}"


@pytest.mark.yavas
def test_olcum_plani_belirsizligi_azaltir():
    """Plandaki her adım, kalan belirsizliği azaltmalı — artıramaz."""
    s = mus_belirsizlik.analiz(n=20000)
    for q in s["sorular"]:
        sapmalar = [p["sapma_yp"] for p in q["plan"]]
        assert sapmalar == sorted(sapmalar, reverse=True), (
            f"{q['baslik']}: ölçüm planı belirsizliği azaltmıyor {sapmalar}")


@pytest.mark.yavas
def test_her_denge_kendi_olceginde():
    s = mus_belirsizlik.analiz(n=5000)
    olcekler = {q["baslik"]: q["olcek"] for q in s["sorular"]}
    assert olcekler["Kaba yem"] == "ilçe"
    assert olcekler["Şeker pancarı"] == "fabrika havzası"
    assert olcekler["Buğday"] == "ulusal"


@pytest.mark.yavas
def test_bugday_ulusal_olcekte_fazla_sorun_degil():
    """Muş kendi tüketiminin kat kat fazlasını üretir; bu uyarı konusu değildir."""
    s = mus_belirsizlik.analiz(n=5000)
    bugday = next(q for q in s["sorular"] if q["anahtar"] == "bugday")
    assert bugday["oran"]["medyan"] > 2.0
    assert bugday["karar"] == "fazla"

    karar = next(k for k in s["karar"] if k["urun"] == "Buğday")
    assert karar["eylem"] == "koru", "ulusal ölçekte fazla, uyarı üretmemeli"


# =====================================================================
#  Uçtan uca: bütün hat çalışıyor ve panel üretiliyor
# =====================================================================
@pytest.mark.yavas
def test_tum_analizler_calisir_ve_panel_uretilir(panel):
    """En temel güvence: hat baştan sona kırılmadan çalışıyor mu?

    Bu test bir şeyin DOĞRU olduğunu kanıtlamaz, ÇALIŞTIĞINI kanıtlar.
    İkisi farklıdır ama ikincisi olmadan birincisi anlamsızdır.
    """
    import mus_hastalik

    assert mp.denetle() == []

    toprak = mus_toprak.analiz()
    hastalik = mus_hastalik.analiz()
    puanlar = mus_toprak.ilce_puanlari(toprak)
    veri = mus_analiz.calistir(puanlar)

    assert len(veri["ilceler"]) == 6
    assert len(veri["urunler"]) == 9
    assert len(veri["karne"]) == 6
    assert hastalik["istatistik"]["hastalik_sayisi"] > 15

    # Panel gerçekten yazılıyor mu (panel fixture'ı üretimi garanti eder)
    html = panel.read_text(encoding="utf-8")
    assert len(html) > 100_000
    for yer_tutucu in ("__MUS_JSON__", "__TOPRAK_JSON__", "__HASTALIK_JSON__",
                       "__BELIRSIZLIK_JSON__", "__IZ_JSON__"):
        assert yer_tutucu not in html, f"doldurulmamış yer tutucu: {yer_tutucu}"


@pytest.mark.yavas
def test_cikti_dosyalari_gecerli_json(ciktilar):
    """Üretilen JSON'lar panelde okunacak; bozuk olamazlar."""
    cikti = ciktilar
    beklenen = ["mus.json", "mus_toprak.json", "mus_hastalik.json",
                "mus_belirsizlik.json", "mus_iz.json"]
    for ad in beklenen:
        yol = cikti / ad
        assert yol.exists(), f"{ad} üretilmemiş"
        veri = json.loads(yol.read_text(encoding="utf-8"))
        assert veri, f"{ad} boş"


# =====================================================================
#  Karne ve öneriler
# =====================================================================
def test_karne_puanlari_sinirlarda():
    puanlar = mus_toprak.ilce_puanlari()
    veri = mus_analiz.calistir(puanlar)
    for r in veri["karne"]:
        assert 0 <= r["toplam"] <= 100, f"{r['ilce']}: {r['toplam']}"
        for ad, p in r["puan"].items():
            assert 0 <= p <= 100, f"{r['ilce']}.{ad}: {p}"


def test_karne_agirliklari_bire_toplanir():
    assert sum(mus_analiz.AGIRLIK.values()) == pytest.approx(1.0)


def test_karne_sirali():
    puanlar = mus_toprak.ilce_puanlari()
    veri = mus_analiz.calistir(puanlar)
    toplamlar = [r["toplam"] for r in veri["karne"]]
    assert toplamlar == sorted(toplamlar, reverse=True)
    assert [r["sira"] for r in veri["karne"]] == [1, 2, 3, 4, 5, 6]


def test_her_ilce_icin_oneri_var():
    oneriler = mus_analiz.oneriler()
    assert len(oneriler) == 6
    for o in oneriler:
        assert o["maddeler"], f"{o['ilce']} için öneri yok"
        oncelikler = [m["oncelik"] for m in o["maddeler"]]
        assert oncelikler == sorted(oncelikler), "öneriler önem sırasında değil"
