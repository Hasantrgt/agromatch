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


# ------------------------------------------- pancar büyütme vaadi
def test_guvenle_sozu_geri_gelmedi():
    """1. kısım "sözleşmeli alan GÜVENLE büyütülebilir" diyordu.

    Toprak katmanına sorulmamıştı; altı ilçenin altısında da pancar
    uygunluğu tavanlanmış durumda. Söz daraltıldı, geri gelmemeli.
    """
    for o in ma.oneriler():
        for m in o["maddeler"]:
            butun = f"{m['metin']} {m['kazanc']}".lower()
            assert "güvenle büyütülebilir" not in butun, (
                f"{o['ilce']}: daraltılmamış pancar sözü geri gelmiş")


def test_her_ilcede_pancar_uygunlugu_tavanli():
    """Bulgu kilidi: tavan kalkarsa uyarı metni de gözden geçirilmeli."""
    for ilce in mp.ILCE:
        d = cati.pancar_buyutme_uyarisi(ilce)
        assert d["tavanlandi"] is True, f"{ilce}: pancar tavanı kalkmış"
        assert d["kisitlayici"], f"{ilce}: kısıtlayıcı adı yok"


def test_drenaj_kisitli_ilcede_kok_curuklugu_aniliyor():
    """Drenaj hem tavanı koyan kısıt hem de Rhizoctonia'nın koşulu.

    O ilçede uyarı bu bağı kurmuyorsa, çatı iki kısmı yine ayrı
    okuyor demektir.
    """
    drenajli = [i for i in mp.ILCE
                if cati.pancar_buyutme_uyarisi(i)["drenaj_kisiti"]]
    assert drenajli, "drenaj kısıtlı ilçe kalmamış — bulgu değişti"
    for ilce in drenajli:
        c = cati.pancar_buyutme_uyarisi(ilce)["cumle"]
        assert "DRENAJ" in c and "Rhizoctonia" in c, ilce


# ----------------------------------------------- arazi bütçesi
def test_arazi_butcesi_toplami_tutuyor():
    for ilce in mp.ILCE:
        b = cati.arazi_butcesi(ilce)
        assert b["toplam_dekar"] == pytest.approx(
            sum(t["dekar"] for t in b["talepler"]))
        assert b["toplam_pay"] == pytest.approx(
            b["toplam_dekar"] / b["ekili_alan_dekar"])
        assert b["durum"] in cati.ARAZI_DURUM


def test_merkez_onerileri_ilceye_sigmiyor():
    """Bulgu 6'nın arazi tarafındaki karşılığı."""
    assert cati.arazi_butcesi("Merkez")["durum"] == "sığmıyor"


def test_bulanik_yaridan_fazlasini_istiyor():
    """EN KRİTİK TEST (bu bulgu için).

    Bulanık aritmetik olarak sığdığı için eski uygunluk testinden
    geçiyordu. Durum değişirse bulgu değişti demektir.
    """
    b = cati.arazi_butcesi("Bulanık")
    assert b["durum"] == "yarıdan fazlası", (
        "Bulanık artık yarıdan fazlasını istemiyorsa bulgu 14 gözden "
        "geçirilmeli")
    assert 0.5 < b["toplam_pay"] < 1.0


def test_yem_onerisi_istedigi_payi_soyluyor():
    """Alan payı söylenmeden 'kapanır' demek, ölçeği gizlemektir."""
    bulundu = 0
    for o in ma.oneriler():
        for m in o["maddeler"]:
            if m["baslik"] != "Kaba yem açığını kapat":
                continue
            bulundu += 1
            assert "ekili alanı" in m["metin"] or "ekili alanın" in m["metin"], (
                f"{o['ilce']}: yem önerisi istediği alan payını söylemiyor")
    assert bulundu >= 5


def test_arazi_sinirlari_agronomik_iddia_etmiyor():
    """Sınırlar aritmetik; proje bilmediği bir eşiği uydurmuyor."""
    n = cati.arazi_butcesi("Bulanık")["sinir_notu"]
    assert "aritmetik" in n and "bilmiyor" in n


# --------------------------------------------- toprak girdisi / kireç
def test_oneriler_olcum_katmanindan_okuyor():
    """Öneri metinleri ham varsayımı değil ölçüm katmanını okumalı.

    Eskiden mp.TOPRAK tuple'ı doğrudan okunuyordu; aynı projenin toprak
    katmanı ölçülmüş değeri üretirken öneri varsayımla konuşuyordu.
    """
    olculu = [i for i in mp.ILCE
              if cati.toprak_girdisi(i)["kaynak"].get("kirec") == "ölçüm"]
    assert len(olculu) >= 5, "kireç ölçümü uygulanmıyor"
    for ilce in olculu:
        ham = float(mp.TOPRAK[ilce][2])
        olcum = float(cati.toprak_girdisi(ilce)["degerler"]["kirec"])
        assert olcum != ham, f"{ilce}: ölçüm uygulanmamış görünüyor"


def test_kirec_varsayimlari_olcumlerin_belirgin_ustunde():
    """Bulgu kilidi: beş ilçede de varsayım ölçümün çok üstünde.

    Yön değişirse (ölçüm varsayımı aşarsa) bulgu 15 gözden geçirilmeli.
    """
    for ilce in mp.ILCE:
        g = cati.toprak_girdisi(ilce)
        if g["kaynak"].get("kirec") != "ölçüm":
            continue
        assert float(g["degerler"]["kirec"]) < float(mp.TOPRAK[ilce][2]), ilce


def test_kirec_onerisi_dayanagini_soyluyor():
    """Doğrulanmamış bir sayıya dayanan öneri bunu yazmak zorunda."""
    bulundu = 0
    for o in ma.oneriler():
        for m in o["maddeler"]:
            if m["baslik"] != "Fosforu kireç bağlıyor":
                continue
            bulundu += 1
            metin = m["metin"]
            assert "varsayım" in metin, f"{o['ilce']}: kaynak yazılmamış"
            assert "doğrulayamadı" in metin, (
                f"{o['ilce']}: doğrulanamadığı söylenmiyor")
            assert "ölçülmeli" in m["kazanc"], f"{o['ilce']}: kazanç kayıtsız"
    assert bulundu >= 1, "fosfor önerisi hiçbir ilçede çıkmıyor"


def test_drenaj_onerisi_dogrulandi():
    """'Drenaj her şeyin önünde' iddiası veriyle tutuyor mu.

    Bu bir yakalama değil, ONAY: öneri çıkan ilçelerde drenaj ürünlerin
    çoğunun tavanını koyuyor. Tarama yalnızca yanlışları raporlarsa
    yanlı olur.
    """
    import mus_toprak as mt
    for ilce in mp.ILCE:
        if cati.toprak_girdisi(ilce)["degerler"]["drenaj"] != "zayıf":
            continue
        drenajli = sum(1 for u in mp.URUN
                       if mt.uygunluk(ilce, u).get("kisitlayici") == "drenaj")
        assert drenajli >= 6, (
            f"{ilce}: drenaj artık ürünlerin çoğunu tavanlamıyor "
            f"({drenajli}/9) — 'her şeyin önünde' iddiası gözden geçirilmeli")
