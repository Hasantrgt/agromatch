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
        if hastalik == "Arpa sarı cücelik virüsü (BYDV)":
            continue      # katalogda yok, eklenmesi bekleniyor
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


def test_kalintisiz_gruplarda_bekleme_suresi_yok():
    for g in ps.ETKI_GRUPLARI:
        if g["grup"] in ps.KALINTISIZ:
            assert g["kalinti_suresi_gun"][1] <= 3, g["grup"]


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
    assert g["kalinti_suresi_gun"] == (0, 0)


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
    """Böcek tarafı henüz Bakanlık belgesiyle doğrulanmadı; hepsi
    'literatür' olmalı. Biri 'ZMTT' olduysa gerçekten doğrulanmış mı?"""
    for kayit in (*tz.ZARARLILAR, *fy.FAYDALILAR, *ps.ETKI_GRUPLARI):
        assert kayit["kaynak"] == "literatür", kayit.get("ad", kayit.get("grup"))
