"""Çatı modülünün testleri.

NEDEN VAR: Bu modülün tek işi, 1. kısmın 2. kısma sormadan verdiği bir
sözü geri almak. O sözün sessizce geri gelmesi, çatıyı anlamsızlaştırır.
Buradaki testlerin çoğu tek bir şeyi kovalıyor: "münavebe hastalık
baskısını kırar" cümlesi, hesaplanmadan bir daha yazılmasın.

İkinci kovaladıkları şey CİNS/TÜR ayrımı. Fusarium spp. sekiz üründe
geçiyor; bunu "aynı patojen" saymak bulguyu şişirir ve kataloğun
söylemediğini söyler. Ayrım bozulursa 18 "belirsiz" çift sessizce
"kırmaz"a döner ve proje elinde olmayan bir kesinlik iddia eder.
"""

from __future__ import annotations

import itertools

import pytest

import cati
import mus_analiz as ma
import mus_profil as mp


def test_denetle_temiz():
    assert cati.denetle() == []


# ------------------------------------------------- geri alınan söz
def test_daraltilmamis_munavebe_sozu_geri_gelmedi():
    """EN KRİTİK TEST.

    Eskiden her öneri kaydında şu yazıyordu: "Risk dağılır, münavebe
    hastalık baskısını kırar." 36 çiftin 35'i için bu doğru değil.
    """
    yasak = "münavebe hastalık baskısını kırar"
    for o in ma.oneriler():
        for m in o["maddeler"]:
            butun = f"{m['baslik']} {m['metin']} {m['kazanc']}".lower()
            assert yasak not in butun, (
                f"{o['ilce']}: daraltılmamış münavebe sözü geri gelmiş")


def test_desen_onerisi_hesaplanmis_cumle_tasiyor():
    """Söz silinmekle kalmadı, yerine hesap kondu."""
    bulundu = 0
    for o in ma.oneriler():
        for m in o["maddeler"]:
            if m["baslik"] != "Ürün deseni dar":
                continue
            bulundu += 1
            assert "ürün çiftinden" in m["metin"] or "hiçbiri" in m["metin"], (
                f"{o['ilce']}: münavebe cümlesi hesaplanmamış")
    assert bulundu, "hiçbir ilçede 'Ürün deseni dar' önerisi çıkmadı"


# ------------------------------------------------- cins / tür ayrımı
def test_yalniz_cins_ortakligi_kirmaz_demiyor():
    """Cins ortaklığı 'kırmaz' kanıtı değildir; cevap belirsiz olmalı."""
    for m in cati.matris():
        if not m["tur_ortak"] and m["cins_ortak"]:
            assert m["durum"] == "belirsiz", (
                f"{m['urunler']}: yalnız cins ortak ama durum {m['durum']}")


def test_kirmaz_karari_hep_tur_ortakligina_dayaniyor():
    for m in cati.matris():
        if m["durum"] == "kırmaz":
            assert m["tur_ortak"], f"{m['urunler']}: kırmaz ama ortak tür yok"


def test_kirar_karari_hic_ortaklik_istemiyor():
    for m in cati.matris():
        if m["durum"] == "kırar":
            assert not m["tur_ortak"] and not m["cins_ortak"], m["urunler"]


def test_fusarium_cins_duzeyinde_kaliyor():
    """Fusarium spp. sekiz üründe geçiyor ama TÜR yazılı değil.

    Bu test, bir gün biri cins/tür ayrımını kaldırırsa 18 belirsiz çiftin
    sessizce 'kırmaz'a dönmesini engeller.
    """
    t = cati.topraktan_etkenler()
    fusariumlu = [u for u in mp.URUN if "Fusarium" in t[u]["cins"]]
    assert len(fusariumlu) >= 7, "Fusarium cins kaydı kaybolmuş"
    for u in fusariumlu:
        assert not any(e.startswith("Fusarium") for e in t[u]["tur"]), (
            f"{u}: Fusarium tür düzeyinde sayılmış — katalog tür yazmıyor")


def test_forma_specialis_ortaklik_saymiyor():
    """f.sp. konakçıya özelleşmeyi söyler; cins benzerliğine sayılmaz.

    Fusarium oxysporum f.sp. betae pancarı tutar, buğdayı tutmaz.
    """
    assert cati._konakci_ozel("Fusarium oxysporum f.sp. betae") is True
    assert cati._konakci_ozel("Fusarium spp.") is False
    t = cati.topraktan_etkenler()
    assert "Fusarium" not in t["Şeker pancarı"]["cins"], (
        "pancarın konakçıya özel Fusarium'u genel Fusarium sayılmış")


# ------------------------------------------------- etiket temizliği
def test_bilesik_etiket_ayriliyor():
    assert cati._etkenler("Fusarium spp. / Rhizoctonia solani") == [
        "Fusarium spp.", "Rhizoctonia solani"]


def test_kisaltilmis_cins_aciliyor():
    """'T. foetida' diye bir cins yok; önündeki tam addan açılmalı."""
    assert cati._etkenler("Tilletia caries / T. foetida") == [
        "Tilletia caries", "Tilletia foetida"]


def test_virus_adi_cinse_indirgenmiyor():
    """'Beet ... virus' ilk sözcüğü cins sanılırsa yanlış eşleşir."""
    ad = "Beet necrotic yellow vein virus"
    assert cati._cins(ad) == ad
    assert cati._etkenler(f"{ad} (vektör: Polymyxa betae)") == [ad]


# ------------------------------------------------- bulgular kilitli
def test_baskin_cift_bugday_arpa_ve_kirmiyor():
    """Alan olarak en büyük çift ilin fiilî münavebesidir.

    Bu çiftin kararı değişirse bulgunun kendisi değişti demektir;
    o zaman gerekçeyle birlikte bu test güncellenmeli.
    """
    en = cati.baskin_ciftler(1)[0]
    assert set(en["urunler"]) == {"Buğday", "Arpa"}
    assert en["durum"] == "kırmaz"
    assert "Bipolaris sorokiniana" in en["tur_ortak"]
    assert en["alan_payi"] > 0.7, "buğday+arpa payı %70'in altına düştü"


def test_alan_paylari_toplanmiyor():
    """Çiftler toprağı bölüştürmez; her payın kendisi 1'i geçmemeli."""
    for c in cati.baskin_ciftler(10):
        assert 0 < c["alan_payi"] <= 1.0, c["urunler"]


def test_pancar_tavani_celiskiyi_yakaliyor():
    t = cati.pancar_tavani()
    assert t["celiski"] is True, (
        "baskıyı kıran münavebe artık yalnız pancara dayanmıyorsa bu "
        "bulgu değişti — gerekçeyle güncellenmeli")
    assert t["tavandaki_pay"] < 0.10, "pancar tavanı ilin %10'unu geçmiş"
    assert "fabrika" in t["aciklama"] and "kota" in t["aciklama"]


def test_tavan_aciklamasinda_bozuk_noktalama_yok():
    """Binlik ayracı topluca değiştirilince cümlenin noktası bozulmuştu."""
    metin = cati.pancar_tavani()["aciklama"]
    assert " dekar. yani" not in metin
    assert "120.194" in metin


# ------------------------------------------------- sınırlar dürüst mü
def test_her_kararda_sinir_yazili():
    for m in cati.matris():
        assert m["sinir"], f"{m['urunler']}: sınır cümlesi yok"


def test_anastomoz_boslugu_masa_basi_degil_diye_yazili():
    """AG boşluğu izolat teşhisi gerektirir; masa başından kapanmaz.

    Bunu 'masa başı iş' diye işaretlemek, kapatılamayacak bir şeyi
    yapılacaklar listesine koymak olur.
    """
    ag = [b for b in cati.bosluklar() if "AG" in b["boşluk"]
          or "Anastomoz" in b["boşluk"]]
    assert ag, "anastomoz grubu boşluğu listede yok"
    assert ag[0]["masa_basi"] is False


def test_bosluklarin_hepsi_tam_kayit():
    for b in cati.bosluklar():
        for alan in ("boşluk", "etki", "kapanmasi", "masa_basi"):
            assert alan in b and b[alan] != "", b


# ------------------------------------------------- sağlamlık
def test_munavebe_simetrik():
    for a, b in itertools.combinations(mp.URUN, 2):
        assert cati.munavebe(a, b)["durum"] == cati.munavebe(b, a)["durum"]


def test_bilinmeyen_urun_cokmuyor():
    d = cati.munavebe("Kivi", "Buğday")
    assert d["var"] is False and d["sebep"]


@pytest.mark.parametrize("urun", list(mp.URUN))
def test_urun_yuku_her_urun_icin_uretiliyor(urun: str):
    y = cati.urun_yuku(urun)
    assert y["hastalik"] >= 0
    assert set(y["kaynak_dagilimi"]) == set(cati.__dict__["bk"].KAYNAKLAR)
    assert sum(y["kaynak_dagilimi"].values()) == y["hastalik"]


def test_ozet_sayilari_matrisle_tutuyor():
    o = cati.ozet()
    assert o["cift"] == len(cati.matris())
    assert sum(o["durum_sayilari"].values()) == o["cift"]
    assert o["durum_sayilari"]["kırar"] == len(cati.kiran_ciftler())
