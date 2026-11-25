"""Ölçülen verim katmanının testleri.

NEDEN VAR: Bu değişiklik projenin VERDİĞİ TAVSİYEYİ değiştirdi. Yonca
verimi yarılanınca açığı kapatmak için gereken alan ikiye katlandı ve
Merkez'de ilçenin bütün ekili alanını aştı — yani tavsiye imkânsız hâle
geldi ve panel artık bunu söylüyor.

Böyle bir zincirde en tehlikeli hata, bir ucun değişip diğerinin eski
kalmasıdır: hiçbir yerde hata vermez, yalnızca yanlış tavsiye üretir.
Nitekim tam bu olmuştu — ek yonca hesabı 0,95'i çıplak sabit olarak
tutuyordu ve verime bağlı değildi.
"""

from __future__ import annotations

import pytest

import mus_analiz as ma
import mus_profil as mp


def test_ek_yonca_verime_bagli():
    """0,95 bir daha donup kalmasın.

    Eskiden ek yonca hesabı çıplak bir 0,95 kullanıyordu; bu sayı elle
    VERIM × KURU_MADDE'den hesaplanmıştı. Verim değiştiğinde sabit eski
    kaldı ve kimse fark etmedi. Bu test o bağı kilitliyor.
    """
    eski = mp.VERIM["Yonca"]
    try:
        mp.VERIM["Yonca"] = 2.0
        assert ma.yonca_km_da() == pytest.approx(2.0 * mp.KURU_MADDE["Yonca"])
        mp.VERIM["Yonca"] = 4.0
        assert ma.yonca_km_da() == pytest.approx(4.0 * mp.KURU_MADDE["Yonca"])
    finally:
        mp.VERIM["Yonca"] = eski


def test_sadece_temiz_urunlerde_olcum_uygulaniyor():
    """Çelişkili ya da üretimi tutmayan ürünlere dokunulmamalı."""
    for urun, (olculen, _a, _u, durum) in mp.VERIM_OLCUM.items():
        if urun not in mp.VERIM:
            continue
        if durum == "temiz":
            assert mp.VERIM[urun] == pytest.approx(olculen), urun
        else:
            assert mp.VERIM[urun] == pytest.approx(mp.VERIM_VARSAYIM[urun]), (
                f"{urun}: durumu '{durum}' olduğu hâlde ölçüm uygulanmış")


def test_durum_etiketleri_tanimli():
    gecerli = {"temiz", "çelişki", "üretim"}
    for urun, (_v, _a, _u, durum) in mp.VERIM_OLCUM.items():
        assert durum in gecerli, f"{urun}: bilinmeyen durum {durum!r}"


def test_olculen_verim_alan_ve_uretimle_tutarli():
    """Verim, raporun alan ve üretiminin oranı olmalı — elle girilmiş değil."""
    for urun, (verim, alan, uretim, _d) in mp.VERIM_OLCUM.items():
        assert verim == pytest.approx(uretim / alan, rel=0.01), (
            f"{urun}: {uretim}/{alan} = {uretim / alan:.3f}, "
            f"yazılan {verim}")


def test_olcum_kapatilabiliyor():
    eski = mp.VERIM_OLCUM_KULLAN
    try:
        mp.VERIM_OLCUM_KULLAN = False
        mp.verim_uygula()
        assert mp.VERIM["Yonca"] == pytest.approx(mp.VERIM_VARSAYIM["Yonca"])
    finally:
        mp.VERIM_OLCUM_KULLAN = eski
        mp.verim_uygula()
    assert mp.VERIM["Yonca"] == pytest.approx(mp.VERIM_OLCUM["Yonca"][0])


def test_yapilabilirlik_isaretleniyor():
    """Gereken alan ekili alandan büyükse bayrak düşmeli.

    Sayıyı yazıp susmak, okuyana yapılabilir bir şey öneriyormuş
    izlenimi verir. Bu testin koruduğu şey bir hesap değil, bir
    dürüstlük kuralı.
    """
    import mus_toprak as mt
    yem = {d["ilce"]: d for d in ma.calistir(mt.ilce_puanlari())["yem"]}
    for ilce, y in yem.items():
        assert "yonca_ile_kapanir" in y, ilce
        assert "ekili_alan_dekar" in y, ilce
        if y["ek_yonca_dekar"] > y["ekili_alan_dekar"]:
            assert y["yonca_ile_kapanir"] is False, (
                f"{ilce}: gereken alan ekili alandan büyük ama "
                "kapanır işaretlenmiş")


def test_kapanmayan_ilcede_oneri_imkansizligi_soyluyor():
    """Öneri metni 'bunu kapatır' demeye devam etmemeli."""
    import mus_toprak as mt
    v = ma.calistir(mt.ilce_puanlari())
    yem = {d["ilce"]: d for d in v["yem"]}
    kapanmaz = [i for i, y in yem.items() if y["yonca_ile_kapanir"] is False]
    if not kapanmaz:
        pytest.skip("bu veriyle her ilçede açık ekimle kapanıyor")
    for o in v["oneri"]:
        if o["ilce"] not in kapanmaz:
            continue
        metin = " ".join(m["metin"] for m in o["maddeler"]
                         if "yem" in m["baslik"].lower())
        if metin:
            assert "kapatılamaz" in metin, o["ilce"]


def test_kaynak_yazili():
    assert "2025" in mp.VERIM_KAYNAK and "faaliyet" in mp.VERIM_KAYNAK.lower()
