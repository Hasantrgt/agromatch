"""Kil kaynağının tavsiyeye etkisini ölçen modülün testleri.

NEDEN VAR: Bu modül mus_toprak'ın MODÜL DÜZEYİNDEKİ durumunu geçici
olarak değiştirerek üç senaryo çalıştırıyor (OLCUM_KULLAN bayrağı ve
olcum_katmani fonksiyonu). Böyle bir kod, durumu geri bırakmazsa kendi
sonucunu bozmakla kalmaz — aynı oturumda çalışan DİĞER testleri ve
panel üretimini de sessizce yanlış sonuç üretir hâle getirir. Böyle bir
hata hiçbir yerde hata vermez, yalnızca yanlış sayı üretir.

Bu yüzden en kritik test, hesapların doğruluğu değil, modülün
ardında iz bırakmamasıdır.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import mus_toprak as mt
from toprak_dogrulama import kil_etkisi as ke
from toprak_profil import bunye_sinifi


def test_senaryo_modul_durumunu_geri_biraktigi():
    """En önemli test: senaryo çalıştıktan sonra hiçbir iz kalmamalı."""
    onceki_bayrak = mt.OLCUM_KULLAN
    onceki_fn = mt.olcum_katmani

    ke._senaryo("sınama", {"Merkez": 99.0}, True)

    assert mt.OLCUM_KULLAN is onceki_bayrak, "OLCUM_KULLAN geri alınmadı"
    assert mt.olcum_katmani is onceki_fn, "olcum_katmani geri alınmadı"


def test_senaryo_hata_atsa_bile_durumu_geri_birakir(monkeypatch):
    """Geri alma finally içinde olmalı, mutlu yolda değil."""
    onceki_bayrak = mt.OLCUM_KULLAN
    onceki_fn = mt.olcum_katmani

    def patla() -> dict:
        raise RuntimeError("bilerek")

    monkeypatch.setattr(ke, "_toprak_ozeti", patla)
    with pytest.raises(RuntimeError):
        ke._senaryo("sınama", None, True)

    assert mt.OLCUM_KULLAN is onceki_bayrak
    assert mt.olcum_katmani is onceki_fn


def test_senaryo_kil_ustu_gercekten_uygulaniyor():
    """Verilen kil değeri modele geçmeli, yoksa senaryo anlamsız olur."""
    s = ke._senaryo("sınama", {"Merkez": 52.0}, True)
    assert s["toprak"]["Merkez"]["kil"] == pytest.approx(52.0)
    # 52 >= 45 -> killi
    assert s["toprak"]["Merkez"]["bunye"] == "killi"


def test_esikler_bunye_sinifi_ile_tutarli():
    """Modül eşikleri belgeliyor; belge koddan sapmamalı.

    SINIF_ESIK yalnızca panelde gösterilen bir açıklama. Biri
    bunye_sinifi()'ni değiştirir de burayı unutursa, panel yanlış bir
    kural anlatır. Bu test ikisini birbirine bağlıyor.
    """
    for esik, beklenen in ke.SINIF_ESIK:
        # eşiğin hemen üstü o sınıfa düşmeli
        assert bunye_sinifi(esik, 25.0, 25.0) == beklenen
        # eşiğin hemen altı o sınıfa DÜŞMEMELİ
        assert bunye_sinifi(esik - 0.1, 25.0, 25.0) != beklenen


def test_dogrulama_ciktisi_yoksa_cokmez(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(ke, "CIKTI", tmp_path)
    d = ke.uret()
    assert d["var"] is False and d["sebep"]


def test_sg_kil_bozuk_dosyada_cokmez(monkeypatch, tmp_path: Path):
    (tmp_path / "toprak_dogrulama.json").write_text("{bozuk", encoding="utf-8")
    monkeypatch.setattr(ke, "CIKTI", tmp_path)
    assert ke.sg_kil() == {}
