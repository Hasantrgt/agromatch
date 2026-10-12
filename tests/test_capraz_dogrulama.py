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
#  Çapraz doğrulama: iki ayrı yoldan aynı sayı
# =====================================================================
# mus_belirsizlik.py dengeleri elle yazılmış fonksiyonlarla, mus_iz.py ise
# hesap grafiğiyle hesaplar. İkisi aynı sonucu vermek ZORUNDA. Bu, yeni
# soyutlamanın doğru olduğunun tek kanıtıdır — aksi halde elimizde sadece
# daha şık görünen, doğruluğu bilinmeyen bir kod olurdu.

@pytest.mark.yavas
def test_grafik_ve_elle_yazilan_hesap_ayni_sonucu_verir():
    yeni, _, _ = mus_iz.analiz(n=20000)
    eski = mus_belirsizlik.analiz(n=20000)
    eski_harita = {q["anahtar"]: q for q in eski["sorular"]}

    assert len(yeni["sorular"]) == len(eski["sorular"])

    for q in yeni["sorular"]:
        e = eski_harita[q["anahtar"]]
        a, b = q["oran"]["medyan"], e["oran"]["medyan"]
        # Fark yalnızca Monte Carlo gürültüsü kadar olabilir
        assert a == pytest.approx(b, rel=0.02), (
            f"{q['baslik']}: grafik {a:.3f}, elle yazılan {b:.3f}")


@pytest.mark.yavas
def test_dogrula_komutu_basarili():
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
def test_tum_analizler_calisir_ve_panel_uretilir(tmp_path, monkeypatch):
    """En temel güvence: hat baştan sona kırılmadan çalışıyor mu?

    Bu test bir şeyin DOĞRU olduğunu kanıtlamaz, ÇALIŞTIĞINI kanıtlar.
    İkisi farklıdır ama ikincisi olmadan birincisi anlamsızdır.
    """
    import mus_hastalik
    import mus_panel_uret

    assert mp.denetle() == []

    toprak = mus_toprak.analiz()
    hastalik = mus_hastalik.analiz()
    puanlar = mus_toprak.ilce_puanlari(toprak)
    veri = mus_analiz.calistir(puanlar)

    assert len(veri["ilceler"]) == 6
    assert len(veri["urunler"]) == 9
    assert len(veri["karne"]) == 6
    assert hastalik["istatistik"]["hastalik_sayisi"] > 15

    # Panel gerçekten yazılıyor mu
    hedef = KOK / "mus_panel.html"
    once = hedef.stat().st_mtime if hedef.exists() else 0
    mus_panel_uret.main()
    assert hedef.exists()
    assert hedef.stat().st_mtime >= once

    html = hedef.read_text(encoding="utf-8")
    assert len(html) > 100_000
    for yer_tutucu in ("__MUS_JSON__", "__TOPRAK_JSON__", "__HASTALIK_JSON__",
                       "__BELIRSIZLIK_JSON__", "__IZ_JSON__"):
        assert yer_tutucu not in html, f"doldurulmamış yer tutucu: {yer_tutucu}"


@pytest.mark.yavas
def test_cikti_dosyalari_gecerli_json():
    """Üretilen JSON'lar panelde okunacak; bozuk olamazlar."""
    cikti = KOK / "outputs"
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
