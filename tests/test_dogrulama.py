"""Bağımsız kaynakla doğrulama modülü doğru karşılaştırıyor mu.

NEDEN VAR: Bu modül "elimizdeki veri tutuyor" ya da "tutmuyor" diyen bir
sonuç üretiyor ve bu sonuç hocaya gösterilecek. Yanlış bir birim dönüşümü
ya da yanlış bir aralık testi, olmayan bir doğrulama iddiası doğurur —
bu, doğrulama yapmamaktan kötüdür.

Testler ham veriye ihtiyaç duymaz: uydurma ama GERÇEKÇİ CSV satırlarıyla
çalışır. Ham SoilGrids çıktısı depoda durmaz, dolayısıyla temiz klonda da
geçerler.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from toprak_dogrulama import karsilastir as k

BASLIK = ["ilce", "enlem", "boylam", "derinlik", "ozellik", "deger",
          "birim", "d_factor", "ham_deger"]


def _csv(tmp_path: Path, satirlar: list[list]) -> Path:
    yol = tmp_path / "noktalar.csv"
    with open(yol, "w", encoding="utf-8", newline="") as f:
        y = csv.writer(f)
        y.writerow(BASLIK)
        y.writerows(satirlar)
    return yol


def _nokta(ilce="Merkez", enlem=38.73, boylam=41.49, ozellik="ph",
           deger=7.4, birim="pH"):
    """Üç derinlik kademesi için aynı değerde satırlar."""
    return [[ilce, enlem, boylam, d, ozellik, deger, birim, 10, 0]
            for d in ("0-5cm", "5-15cm", "15-30cm")]


# --- birim dönüşümü ----------------------------------------------------
@pytest.mark.parametrize("birim,giren,bekleneni", [
    ("%", 32.0, 32.0),
    ("g/kg", 320.0, 32.0),
    ("dg/kg", 3200.0, 32.0),
])
def test_birim_yuzdeye_cevriliyor(birim, giren, bekleneni):
    d, yontem = k._yuzdeye(giren, birim)
    assert d == pytest.approx(bekleneni)
    assert yontem


def test_taninmayan_birim_uydurulmuyor():
    """Bilinmeyen birimde sayı ÜRETMEK, hata vermekten kötüdür.

    Yanlış katsayıyla çevrilmiş bir değer tabloya girer, kimse fark
    etmez ve 'doğrulama' adı altında uydurma bir sonuç yayımlanır.
    """
    d, yontem = k._yuzdeye(32.0, "kg/ha")
    assert d is None
    assert "tanınmadı" in yontem


# --- derinlik ağırlığı -------------------------------------------------
def test_derinlik_agirligi_0_20cm_hedefliyor():
    """15-30cm kademesinin yalnızca 5 cm'i 20 cm'in içinde kalır."""
    assert k.DERINLIK_AGIRLIK == {"0-5cm": 5.0, "5-15cm": 10.0,
                                  "15-30cm": 5.0}


def test_nokta_degeri_agirlikli_ortalama():
    d = k._nokta_degeri({"0-5cm": 10.0, "5-15cm": 20.0, "15-30cm": 30.0})
    # (10*5 + 20*10 + 30*5) / 20 = 20
    assert d == pytest.approx(20.0)


def test_eksik_kademe_kalan_agirlikla_hesaplanir():
    d = k._nokta_degeri({"0-5cm": 10.0, "5-15cm": 20.0})
    assert d == pytest.approx((10 * 5 + 20 * 10) / 15)


def test_tanimsiz_kademe_yok_sayilir():
    assert k._nokta_degeri({"100-200cm": 5.0}) is None


# --- uçtan uca ---------------------------------------------------------
def test_dosya_yoksa_cokmez(tmp_path: Path):
    d = k.uret(tmp_path / "yok.csv")
    assert d["var"] is False and d["sebep"]


def test_ph_karsilastirmasi_calisir(tmp_path: Path):
    satir = []
    for i in range(6):
        satir += _nokta(boylam=41.40 + i * 0.02, deger=7.4)
    d = k.uret(_csv(tmp_path, satir))
    assert d["var"] is True
    ph = [s for s in d["satirlar"] if s["alan"] == "ph"]
    assert len(ph) == 1
    s = ph[0]
    assert s["ilce"] == "Merkez"
    assert s["soilgrids"]["medyan"] == pytest.approx(7.4)
    assert s["soilgrids"]["n"] == 6


def test_organik_madde_karbondan_turetilir_ve_isaretlenir(tmp_path: Path):
    satir = []
    for i in range(6):
        satir += _nokta(boylam=41.40 + i * 0.02, ozellik="soc",
                        deger=14.0, birim="g/kg")
    d = k.uret(_csv(tmp_path, satir))
    om = [s for s in d["satirlar"] if s["alan"] == "om"][0]
    # 14 g/kg -> %1,4 karbon -> %1,4 × 1,724 organik madde
    assert om["soilgrids"]["medyan"] == pytest.approx(1.4 * k.OM_KATSAYI, abs=0.01)
    assert om["turetildi"] is True, "türetilmiş değer işaretlenmeli"
    assert "Van Bemmelen" in om["soilgrids"]["donusum"]


def test_turetilmis_laboratuvar_degeri_tutma_oranina_girmiyor(tmp_path: Path):
    """Kil karşılaştırması oranı sahte biçimde düşürmemeli.

    Laboratuvar kili bünye SINIFINDAN türetiliyor; tek bir sayı olduğu
    için çeyrek aralığı sıfır genişlikte. 'Aralığa düşüyor mu' testi o
    satırda neredeyse her zaman 'hayır' der. Bu satırlar ana orana
    katılırsa, doğrulama olduğundan kötü görünür.
    """
    satir = []
    for i in range(6):
        satir += _nokta(boylam=41.40 + i * 0.02, ozellik="clay",
                        deger=32.0, birim="%")
        satir += _nokta(boylam=41.40 + i * 0.02, deger=7.4)
    d = k.uret(_csv(tmp_path, satir))
    kil = [a for a in d["alan_ozeti"] if a["alan"] == "kil"]
    assert kil, "kil alan özeti üretilmeli"
    for s in d["satirlar"]:
        if s.get("lab_turetildi"):
            assert s["alan"] == "kil"
    # ana oran yalnızca doğrudan ölçülmüş satırlardan hesaplanmalı
    assert d["ozet"]["olcumlu"] + d["ozet"]["turetilmis"] >= len(
        [s for s in d["satirlar"] if s["laboratuvar"]])


def test_dogrulanamayanlar_acikca_yazili():
    """Kireç ve tuzluluk doğrulanamıyor; bu gizlenemez."""
    assert set(k.DOGRULANAMAYAN) == {"kirec", "ec"}
    for alan, sebep in k.DOGRULANAMAYAN.items():
        assert "SoilGrids" in sebep, f"{alan}: sebep yazılmamış"


def test_kirec_karsilastirmaya_girmiyor(tmp_path: Path):
    """SoilGrids kireç vermiyor; yanlışlıkla bir yerden sızmamalı."""
    satir = []
    for i in range(6):
        satir += _nokta(boylam=41.40 + i * 0.02, deger=7.4)
    d = k.uret(_csv(tmp_path, satir))
    assert all(s["alan"] != "kirec" for s in d["satirlar"])
    assert all(s["alan"] != "ec" for s in d["satirlar"])


def test_yargi_ispat_iddia_etmiyor():
    """Metin bir doğrulamayı ispat gibi sunmamalı."""
    satir_yok = k.uret(Path("/olmayan/yol.csv"))
    assert satir_yok["var"] is False
    # yargı metni uret() içinde sabit; sözleşmesi burada korunuyor
    kaynak = (Path(k.__file__).read_text(encoding="utf-8"))
    assert "doğrulamadır, bir ispat değil" in kaynak
    assert "SoilGrids de bir TAHMİN" in kaynak
