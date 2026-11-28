"""Üçüncü kısım: tarla zararlıları, faydalılar, pestisit yükü.

Bu dosyanın asıl işi üç katalog arasındaki BAĞLARI korumak. Üç ayrı
dosyada yaşayan listeler birbirine adla bağlanıyor; bir ad değiştiğinde
bağ sessizce kopar ve panel boş hücre gösterir. Buradaki çapraz
denetimler o kopmayı yakalar.
"""

from __future__ import annotations

import pytest

import bulas_kaynagi as bk
import mus_hastalik_profil as hp
from bocek import faydali as fy
from bocek import pestisit as ps
from bocek import tarla_zararli as tz

ZARARLI_ADLARI = {z["ad"] for z in tz.ZARARLILAR}
HASTALIK_ADLARI = {h["ad"] for h in hp.HASTALIKLAR}
MUS_URUNLERI = {"Buğday", "Arpa", "Şeker pancarı", "Patates", "Kuru fasulye",
                "Silajlık mısır", "Yonca", "Korunga", "Fiğ"}


# ------------------------------------------------- iç tutarlılık


def test_kataloglar_kendi_denetiminden_geciyor():
    assert tz.denetle() == []
    assert fy.denetle(ZARARLI_ADLARI) == []
    assert ps.denetle(ZARARLI_ADLARI) == []
    assert bk.denetle() == []


def test_her_zararli_mus_urunune_bagli():
    for z in tz.ZARARLILAR:
        assert set(z["urunler"]) <= MUS_URUNLERI, z["ad"]


def test_dokuz_urunun_hepsinde_en_az_bir_zararli_var():
    kapsanan = {u for z in tz.ZARARLILAR for u in z["urunler"]}
    assert kapsanan == MUS_URUNLERI, MUS_URUNLERI - kapsanan


# --------------------------------------------- kısımlar arası bağ


def test_vektor_zararlilari_gercek_hastaliklara_isaret_ediyor():
    """Üçüncü kısımdan ikinci kısma giden köprü kopmasın."""
    for zararli, hastalik in tz.vektorler():
        assert hastalik in HASTALIK_ADLARI, f"{zararli} -> {hastalik}"


def test_bocekle_tasinan_hastaliklarin_vektoru_katalogda_var():
    """Sınıflamada 'böcek' denen her hastalığın bir taşıyıcısı olmalı."""
    tasinan = {h["ad"] for h in bk.zenginlestir() if h["bulas"] == "bocek"}
    vektorlenen = {h for _z, h in tz.vektorler()}
    assert tasinan <= vektorlenen, tasinan - vektorlenen


def test_bulas_sinifi_hastaligi_dogru_kisma_koyuyor():
    z = bk.zenginlestir()
    assert all(h["kisim"] == 3 for h in z if h["bulas"] == "bocek")
    assert all(h["kisim"] == 2 for h in z if h["bulas"] != "bocek")
    assert len(z) == len(hp.HASTALIKLAR)


def test_rizomani_toprak_kisminda_kaliyor():
    """Vektörü Polymyxa betae — bir böcek değil. Üçüncü kısma kaymamalı."""
    assert bk.kaynak("Şeker pancarı", "Rizomani") == "toprak"


def test_depo_koprusu_iki_katalogda_da_var():
    """Tarlada başlayıp ambarda süren zararlılar işaretli olmalı."""
    assert set(tz.depo_koprusu()) == {"Patates güvesi", "Fasulye tohum böceği"}


# ------------------------------------------------- pestisit yükü


def test_kalintisiz_gruplar_kalinti_birakmiyor():
    for g in ps.ETKI_GRUPLARI:
        assert g["kalinti"] == (g["grup"] not in ps.KALINTISIZ), g["grup"]


def test_bekleme_suresi_alani_HIC_OLMAMALI():
    """İlk sürümde her grup için uydurma gün aralıkları vardı.

    O sayılar kaldırıldı: Türkiye'de son uygulama ile hasat arasındaki
    süre ürün etiketinde, etkili madde ve kültür bitkisi bazında yazar.
    Grup düzeyinde bir sayı vermek yanlıştır ve yanlış bir bekleme
    süresi hiç vermemekten tehlikelidir. Geri gelmesin.
    """
    for g in ps.ETKI_GRUPLARI:
        assert "kalinti_suresi_gun" not in g, g["grup"]
        assert "bekleme" not in g, g["grup"]


def test_irac_kodlari_dogrulanmis_degerlerde():
    """IRAC Mode of Action brochure (Ed. 6) ile karşılaştırıldı."""
    beklenen = {"piretroit": "3A", "neonikotinoid": "4A",
                "organik_fosforlu": "1B", "diamid": "28", "bt": "11A"}
    for grup, kod in beklenen.items():
        assert ps.grup(grup)["irac"] == kod, grup


def test_genis_etkili_gruplar_daha_cok_faydaliyi_vuruyor():
    """Tasarımın savunduğu şeyin sayıyla doğrulanması."""
    genis = [ps.yuk(g["grup"], fy.FAYDALILAR)["canliya_zarar"]
             for g in ps.ETKI_GRUPLARI if g["genis_etkili"]]
    dar = [ps.yuk(g["grup"], fy.FAYDALILAR)["canliya_zarar"]
           for g in ps.ETKI_GRUPLARI if not g["genis_etkili"]]
    assert min(genis) > max(dar)


def test_diyatomlu_toprakta_direnc_riski_yok():
    """Fiziksel etki — projenin depo kısmındaki temel sav."""
    g = ps.grup("mineral")
    assert g["direnc_riski"] == "yok"
    assert g["kalinti"] is False


def test_siralama_yuku_hafiften_agira_veriyor():
    gruplar = ps.zararliya_gore("Patates böceği")
    assert gruplar, "patates böceği için grup bulunamadı"
    yukler = [ps.SEVIYE[g["ariya_toksik"]] + ps.SEVIYE[g["parazitoite_toksik"]]
              for g in gruplar]
    assert yukler == sorted(yukler)


@pytest.mark.parametrize("zararli", sorted(ZARARLI_ADLARI))
def test_her_zararli_en_az_bir_grubun_hedefinde(zararli):
    assert ps.zararliya_gore(zararli), zararli


def test_kalintisiz_yolu_olmayanlar_bilinen_liste():
    """Bu liste bir EKSİK değil, bir BULGUDUR: yedi zararlı için
    elimizde kalıntı bırakmayan bir seçenek yok. Liste değişirse
    bilerek değişsin."""
    yok = {z["ad"] for z in tz.ZARARLILAR if not ps.kalintisiz_yol(z["ad"])}
    assert yok == {
        "Kımıl", "Hububat yaprak bitleri", "Yeşil şeftali yaprak biti",
        "Pancar sineği", "Pancar piresi", "Bakla yaprak biti",
        "Yonca yaprak biti"}


# --------------------------------------------------- faydalılar


def test_her_faydalinin_hassasiyeti_gercek_gruba_isaret_ediyor():
    gruplar = {g["grup"] for g in ps.ETKI_GRUPLARI}
    for f in fy.FAYDALILAR:
        assert set(f["hassasiyet"]) <= gruplar, f["ad"]


def test_sunenin_parazitoiti_katalogda():
    """Türkiye'de süne mücadelesinin dayandığı canlı; kaybolmasın."""
    assert fy.hedefe_gore("Süne"), "sünenin doğal düşmanı yazılmamış"


def test_tozlayici_hicbir_zararliyi_hedeflemiyor():
    for f in fy.FAYDALILAR:
        if f["rol"] == "tozlayici":
            assert f["hedef"] == ()


def test_kaynak_disiplini_korunuyor():
    """Yalnızca Bakanlık belgesinden DOĞRULANMIŞ kayıtlar ZMTT olabilir.

    Doğrulama taramasında dört kayıt belgeye bağlandı. Üçünde yazdığım
    eşik YANLIŞ çıktı (süne, patates böceği, yonca hortumlu böceği),
    birinde eşik hiç yazılmamıştı ve belgede vardı (ekin kambur böceği).
    Listeye yeni bir ZMTT eklenecekse gerçekten belgeden gelmiş olmalı.

    GÜNCELLEME (28 Kasım 2026): dört kayıt daha eklendi. Kaynakları
    Bakanlık TAGEM Entegre Mücadele Teknik Talimatlarıdır ve belgeler
    okunarak işlendi:
      Mısır Entegre Mücadele Teknik Talimatı, EK-1 çizelgesi
        - Mısır kurdu   (1. üründe %5 bulaşma / 2. üründe 1 yumurta paketi)
        - Bozkurt       (mısırda m² veya 3 m sırada >=2 yenik/kesik bitki)
      Patates Entegre Mücadele Teknik Talimatı, EK-1 çizelgesi ve 7.1.4
        - Bozkurt       (patateste dikimde m²'de 2-3 larva)
        - Patates güvesi (eşeysel çekici tuzakta 1 ergin)
        - Yeşil şeftali yaprak biti (yemeklikte önerilmiyor; tohumlukta
          50 yaprakta varlık)
    Belgede bulunmayan eşik UYDURULMADI; sekiz zararlı hâlâ eşiksiz.
    """
    dogrulanmis = {z["ad"] for z in tz.ZARARLILAR if z["kaynak"] == "ZMTT"}
    assert dogrulanmis == {"Süne", "Patates böceği", "Yonca hortumlu böceği",
                           "Ekin kambur böceği", "Mısır kurdu", "Bozkurt",
                           "Patates güvesi", "Yeşil şeftali yaprak biti"}
    for kayit in (*fy.FAYDALILAR, *ps.ETKI_GRUPLARI):
        assert kayit["kaynak"] == "literatür", kayit.get("ad", kayit.get("grup"))


def test_her_esigin_kaynagi_yazili():
    """Eşik varsa kaynağı da olmalı; yoksa kaynağı da olmamalı."""
    for z in tz.ZARARLILAR:
        if z["esik"]:
            assert z["esik_kaynak"] in ("ZMTT", "literatür"), z["ad"]
        else:
            assert z["esik_kaynak"] is None, z["ad"]


def test_zmtt_kayitlarin_esigi_de_zmtt():
    for z in tz.ZARARLILAR:
        if z["kaynak"] == "ZMTT":
            assert z["esik_kaynak"] == "ZMTT", z["ad"]


# ------------------------------------------- süne karar kuralı (ZMTT)


def test_sune_survey_esiginin_altinda_islem_yok():
    k = tz.sune_karari(0.5)
    assert k["ilac"] is False and k["karar"] == "izle"


def test_sune_survey_esigi_asilinca_parazitlenme_isteniyor():
    """Karar, parazitlenme ölçülmeden VERİLEMEZ — talimatın özü bu."""
    k = tz.sune_karari(1.0)
    assert k["ilac"] is None
    assert "sürvey" in k["karar"]


@pytest.mark.parametrize("ergin,oran", [(0.8, 40.0), (1.0, 50.0), (1.5, 70.0)])
def test_sune_tablosu_talimattaki_degerleri_veriyor(ergin, oran):
    assert tz.gereken_parazitlenme(ergin) == oran


def test_sune_parazitlenme_yeterliyse_ilaclama_yok():
    """Projenin savı: faydalı, kararı değiştirir."""
    az = tz.sune_karari(1.2, 45.0)
    cok = tz.sune_karari(1.2, 55.0)
    assert az["ilac"] is True and cok["ilac"] is False


def test_sune_cok_yuksek_erginde_parazitlenme_yetmiyor():
    """2 ergin/m² üstünde iyi parazitlenme bile erken ilaçlamayı
    engellemiyor — talimat böyle diyor, yumuşatmıyoruz."""
    k = tz.sune_karari(2.5, 85.0)
    assert k["ilac"] is True and "1.-3. dönem" in k["karar"]


def test_sune_gecersiz_girdi_reddediliyor():
    with pytest.raises(ValueError):
        tz.sune_karari(-1)
    with pytest.raises(ValueError):
        tz.sune_karari(1.0, 150.0)


def test_patates_bocegi_esigi_yok_diyor():
    """Resmî kaynak 'kimyasal mücadelede eşik bulunmamaktadır' diyor;
    uydurma bir sayı geri gelmesin."""
    z = next(x for x in tz.ZARARLILAR if x["ad"] == "Patates böceği")
    assert "EŞİK YOKTUR" in z["esik"]
    assert "%20" in z["esik"]


def test_yonca_hortumlu_esigi_resmi_degerde():
    """Yazdığım 'sap başına 3 larva' YANLIŞTI; talimat m²'de 25 diyor."""
    z = next(x for x in tz.ZARARLILAR if x["ad"] == "Yonca hortumlu böceği")
    assert "25 larva veya ergin" in z["esik"]
    assert "m²" in z["esik"]
    assert z["latince"] == "Hypera variabilis"


def test_ekin_kambur_esigi_iki_kademeli():
    """Talimat iki ayrı karar veriyor: tohum ilaçlama ve yüzey ilaçlaması."""
    z = next(x for x in tz.ZARARLILAR if x["ad"] == "Ekin kambur böceği")
    assert "tohum ilaçlama" in z["esik"] and "yüzey ilaçlaması" in z["esik"]
    assert z["esik_kaynak"] == "ZMTT"


def test_dogrulanan_esikler_sayi_iceriyor():
    """ZMTT etiketli her eşik ya somut bir sayı verir ya da eşik
    olmadığını açıkça söyler — ikisinin arası yok."""
    import re
    for z in tz.ZARARLILAR:
        if z["esik_kaynak"] == "ZMTT":
            assert re.search(r"\d", z["esik"]), z["ad"]
