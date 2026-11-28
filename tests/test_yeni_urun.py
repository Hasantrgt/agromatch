"""'Muş'ta şu ürün yetişir mi?' sorgusunun testleri.

NEDEN VAR: Bu modül projenin en kolay abartılabilecek parçası. Bir
jüriye "modelimiz hangi ürünün yetişeceğini biliyor" demek cazip; oysa
ölçülen şey dar ve sınırları yazılı. Buradaki testler iki şeyi birden
koruyor: bulgunun kendisi (kış kapısı iki grubu ayırıyor) ve bulgunun
ABARTILMAMASI (yetişir denmeyen yere yetişir yazılmasın, verim ve
kârlılık iddiası girmesin).
"""

from __future__ import annotations

import pytest

import mus_iklim
import mus_profil as mp
import yeni_urun as yu


def test_kis_minimumu_mus_iklimden_okunuyor():
    """Sıcaklık formülünün ikinci kopyası olmamalı.

    Projede bir kez iki modül aynı dengeyi ayrı ayrı hesapladı ve
    biri unutulunca ayrı düştüler. Kış minimumu da mus_iklim'in
    serisinden türetilmeli, yeniden modellenmemeli.
    """
    for ilce in mp.ILCE:
        beklenen = round(min(mus_iklim.aylik_sicaklik(ilce))
                         - mus_iklim.GUNLUK_FARK, 1)
        assert yu.kis_minimum(ilce) == beklenen, ilce


# --------------------------------------------------- ayırt edicilik
def test_ayirt_edicilik_bulgusu_kilitli():
    """EN KRİTİK TEST. Bulgu değişirse BULGULAR.md de değişmeli."""
    a = yu.ayirt_edicilik()
    assert len(a["dogru_ret"]) == len(yu.MUSTA_YOK) == 6, (
        "kış kapısı artık altı türün hepsini elemiyor")
    assert a["yanlis_ret"] == [], "elenmesi gereken bir tür geçti"
    assert a["yanlis_elenen"] == [], (
        "Muş'ta fiilen yetişen bir meyve yanlışlıkla elendi — "
        "model artık doğru olanı reddediyor")
    assert len(a["gecen_pozitif"]) == len(yu.MUSTA_YETISEN) == 4


def test_zeytin_kis_yuzunden_eleniyor():
    """Somut vaka: zeytin Muş'ta yetişmez ve sebebi kıştır."""
    d = yu.yetisir_mi("Zeytin", "Merkez")
    assert d["karar"] == "yetişmez"
    assert d["darbogaz"] == "kış soğuğu"
    assert d["kis_dayanimi"] > d["kis_minimum"], "eleme gerekçesi tutmuyor"


@pytest.mark.parametrize("ilce", list(mp.ILCE))
def test_zeytin_her_ilcede_eleniyor(ilce: str):
    """Muş'un hiçbir ilçesi zeytin için yeterince ılık değil."""
    assert yu.yetisir_mi("Zeytin", ilce)["karar"] == "yetişmez"


@pytest.mark.parametrize("urun", list(yu.MUSTA_YETISEN))
def test_yetisen_meyveler_hicbir_ilcede_elenmiyor(urun: str):
    for ilce in mp.ILCE:
        assert yu.yetisir_mi(urun, ilce)["karar"] != "yetişmez", (
            f"{urun} {ilce}'de elendi ama İl Tarım raporuna göre "
            "Muş'ta yetişiyor")


# ------------------------------------------- abartma koruması
def test_sicaklik_istegi_yoksa_yetisir_denmiyor():
    """Kışı atlatmak 'yetişir' demek değildir.

    İklim isteği kayıtlı olmayan bir ürün için model 'söylenemez'
    demeli; 'yetişir' demek, elde olmayan veriyi varmış gibi sunmaktır.
    """
    for urun in list(yu.MUSTA_YETISEN) + list(yu.CICEK_DONU_ACIGI):
        if urun in mus_iklim.IKLIM_ISTEK:
            continue
        d = yu.yetisir_mi(urun, "Merkez")
        assert d["karar"] == "söylenemez", urun
        assert "kayıtlı" in d["gerekce"]


def test_cicek_donu_acigi_yazili():
    """Modelin reddedemediği iki tür ve sebebi açıkça kayıtlı.

    Kayısı ve badem kışı atlatıyor, Muş'ta yine de yetişmiyor. Model
    bunu göremiyor çünkü ilkbahar geç donu modelde yok. Bu eksiği
    saklamak, testi anlamsızlaştırır.
    """
    a = yu.ayirt_edicilik()
    assert {x["urun"] for x in a["cekimser"]} == set(yu.CICEK_DONU_ACIGI)
    assert "geç don" in a["yorum"].lower() or "GEÇ DON" in a["yorum"]


def test_dogruluk_orani_iddia_edilmiyor():
    """Bu modül bir doğruluk yüzdesi vermez ve vermediğini söyler."""
    a = yu.ayirt_edicilik()
    assert "DOĞRULUK ORANI DEĞİL" in a["yorum"]
    import json
    metin = json.dumps(a, ensure_ascii=False).lower()
    for yasak in ("% doğruluk", "doğruluk oranı:", "accuracy"):
        assert yasak not in metin


def test_verim_ve_karlilik_iddiasi_yok():
    """Model 'yetişir' dese bile verim ya da kâr söylemez."""
    import json
    for urun in yu.KIS_DAYANIMI:
        metin = json.dumps(yu.yetisir_mi(urun, "Merkez"),
                           ensure_ascii=False).lower()
        for yasak in ("ton/da", "verim ", "kâr", "gelir", "tl/"):
            assert yasak not in metin, f"{urun}: '{yasak}' sızmış"


def test_her_cevapta_sinir_yazili():
    for urun in yu.KIS_DAYANIMI:
        d = yu.yetisir_mi(urun, "Merkez")
        assert d["sinir"] and "ortalama" in d["sinir"].lower()


def test_kis_dayanimlari_kaynaktan_geliyor():
    """Her değerin yanında kaynaktaki ifadesi durmalı."""
    for urun, (deger, ifade) in yu.KIS_DAYANIMI.items():
        assert isinstance(deger, float), urun
        assert len(ifade) >= 14, f"{urun}: kaynak ifadesi yok"
        assert "°C" in ifade or "C'" in ifade, urun


def test_bilinmeyen_ilce_cokmuyor():
    d = yu.yetisir_mi("Elma", "Ankara")
    assert d["var"] is False and d["sebep"]
