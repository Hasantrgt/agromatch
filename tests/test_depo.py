"""
Depo modüllerinin testleri.

İki şeyi korurlar: katalogların tutarlılığı ve ambar modelinin fiziksel
olarak anlamlı davranması. İkincisi önemli — sönümleme modeli sessizce
ters çalışsa (yığın dışarıdan daha soğuk çıksa) kimse fark etmez ama
bütün gelişme penceresi yanlış olur.
"""

import pytest

import mus_iklim
import mus_profil as mp
from depo import ambar_sicaklik as amb
from depo import depo_profil as dp


# ------------------------------------------------------------- kataloglar
def test_katalog_tutarli():
    hatalar = dp.denetle()
    assert hatalar == [], "katalog tutarsız: " + "; ".join(hatalar)


def test_bugday_biti_ucamaz_ve_ic_besleyendir():
    """İki özellik de mücadele stratejisini belirliyor; yanlışsa her şey yanlış."""
    z = next(z for z in dp.ZARARLILAR if z["tur"] == "Sitophilus granarius")
    assert z["ic_besleyen"] is True, "larva tanenin içinde gelişir"
    assert z["ucabilir"] is False, "buğday biti uçamaz; bulaşma depodan gelir"


def test_karantina_turu_isaretli():
    karantina = [z for z in dp.ZARARLILAR if z["karantina"]]
    assert len(karantina) == 1
    assert karantina[0]["tur"] == "Trogoderma granarium"


def test_kalintisiz_secenekler_kimyasal_icermez():
    for m in dp.kalintisiz_secenekler():
        assert not m["kalinti"]
    adlar = [m["ad"] for m in dp.kalintisiz_secenekler()]
    assert "Fosfin fumigasyonu" not in adlar
    assert "Diyatomlu toprak (DE)" in adlar


def test_de_yalnizca_ergine_etkili():
    """DE temas yoluyla etki eder; tanenin içindeki larvaya ulaşamaz.

    Bu, 'DE tek başına yeter mi' sorusunun cevabını belirliyor: yetmez,
    ergin çıkışı sürdükçe koruma devam etmelidir.
    """
    de = next(m for m in dp.MUCADELE if m["ad"].startswith("Diyatomlu"))
    assert de["gucu"]["ergin"] is True
    assert de["gucu"]["ic_larva"] is False
    assert de["direnc_riski"] == "yok"
    assert de["kalinti"] is False


def test_fosfin_yuksek_direnc_riski_tasiyor():
    f = next(m for m in dp.MUCADELE if m["ad"] == "Fosfin fumigasyonu")
    assert f["direnc_riski"] == "YÜKSEK"
    assert f["kalinti"] is True


# ----------------------------------------------------- ambar sıcaklık modeli
@pytest.fixture(scope="module")
def merkez():
    return dict(dis=mus_iklim.aylik_sicaklik("Merkez"),
                yigin=amb.ambar_sicakligi("Merkez"))


def test_yigin_kisin_disaridan_ilik_yazin_daha_serin(merkez):
    """Yığının ısı ataleti: kışın dışarıdan sıcak, yazın dışarıdan serin.

    Model ters çalışırsa bu test kırılır. 'Muş soğuk, depoda sorun olmaz'
    sanısının neden yanlış olduğunu da bu gösteriyor.
    """
    ocak = 0
    temmuz = 6
    assert merkez["yigin"][ocak] > merkez["dis"][ocak], "kışın yığın daha soğuk çıktı"
    assert merkez["yigin"][temmuz] < merkez["dis"][temmuz], "yazın yığın daha sıcak çıktı"


def test_yigin_zirvesi_dis_havadan_gec(merkez):
    """Isı ataleti gecikme yaratır: yığın en sıcak ayına sonra ulaşır."""
    dis_zirve = max(range(12), key=lambda i: merkez["dis"][i])
    yigin_zirve = max(range(12), key=lambda i: merkez["yigin"][i])
    assert yigin_zirve > dis_zirve, (
        f"yığın zirvesi ({yigin_zirve}) dış hava zirvesinden ({dis_zirve}) geç olmalı")


def test_yigin_salinimi_dis_havadan_dar(merkez):
    dis_genlik = max(merkez["dis"]) - min(merkez["dis"])
    yigin_genlik = max(merkez["yigin"]) - min(merkez["yigin"])
    assert yigin_genlik < dis_genlik, "yığın salınımı sönümlenmemiş"


def test_sonumleme_bire_yaklasinca_yigin_dis_havaya_yaklasir():
    """alfa=1 demek ısı ataleti yok demek; yığın dış havayı aynen izlemeli."""
    dis = mus_iklim.aylik_sicaklik("Merkez")
    yigin = amb.ambar_sicakligi("Merkez", alfa=1.0)
    for a, b in zip(dis, yigin):
        assert abs(a - b) < 0.2


# ------------------------------------------------------ gelişme penceresi
def test_yuksek_esikli_tur_daha_az_ay_bulur():
    """Eşik yükseldikçe elverişli ay sayısı azalmalı — monotonluk."""
    onceki = 13
    for taban in (7.0, 11.0, 16.0, 20.0, 25.0):
        p = amb.gelisme_penceresi("Merkez", taban)
        assert p["elverisli_ay_sayisi"] <= onceki
        onceki = p["elverisli_ay_sayisi"]


def test_sicak_seven_turler_isitilmamis_ambarda_gelisemiyor():
    """Un biti ve khapra böceği Muş'un ısıtılmamış ambarında eşiği aşamaz.

    Bu bir model çıktısı, kesin bir iddia değil; sönümleme varsayımına
    bağlı. Ama varsayım değişmediği sürece sonuç sabit kalmalı.
    """
    for tur in ("Tribolium castaneum", "Trogoderma granarium"):
        z = next(z for z in dp.ZARARLILAR if z["tur"] == tur)
        p = amb.gelisme_penceresi("Merkez", float(z["taban_sicaklik"]))
        assert p["elverisli_ay_sayisi"] == 0, f"{tur} beklenmedik şekilde gelişiyor"


def test_varto_merkezden_dar_pencere_veriyor():
    """Varto en yüksek ve en soğuk ilçe; buğday biti için penceresi dar olmalı."""
    taban = 11.0
    merkez = amb.gelisme_penceresi("Merkez", taban)
    varto = amb.gelisme_penceresi("Varto", taban)
    assert varto["derece_gun"] < merkez["derece_gun"]
    assert varto["elverisli_ay_sayisi"] <= merkez["elverisli_ay_sayisi"]


def test_butun_ilceler_analize_giriyor():
    sonuc = amb.analiz()
    ilceler = {s["ilce"] for s in sonuc["satirlar"]}
    assert ilceler == set(mp.ILCE)
    assert len(sonuc["satirlar"]) == len(mp.ILCE) * len(dp.ZARARLILAR)


# ------------------------------------------------------------ nesil sayısı
def test_nesil_sayisi_pozitif_derece_gun_ister():
    with pytest.raises(ValueError):
        amb.nesil_sayisi(800, 0)
    with pytest.raises(ValueError):
        amb.nesil_sayisi(800, -5)


def test_nesil_sayisi_bolme_yapiyor():
    assert amb.nesil_sayisi(800, 400) == pytest.approx(2.0)
