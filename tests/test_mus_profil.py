"""
Veri omurgasının tutarlılık testleri.

mus_profil.py projenin tek veri kaynağıdır. Buradaki bir tutarsızlık bütün
analizlere sessizce yayılır: paylar 1'e toplanmazsa il toplamı kaybolur,
bir ürün künyede tanımsızsa panel yarım çizilir.

Bu testler, mus_profil.denetle() fonksiyonunun yaptığını otomatikleştirir ve
üstüne birkaç şey ekler. denetle() elle çalıştırılır; bunlar her zaman çalışır.
"""

import pytest

import mus_profil as mp


# ------------------------------------------------------- bütünlük
def test_denetle_hatasiz():
    """Projenin kendi denetim fonksiyonu temiz geçmeli."""
    assert mp.denetle() == []


@pytest.mark.parametrize("sozluk_adi", [
    "DESEN", "TOPRAK", "IKLIM", "KOORDINAT", "VERIM_DUZELTME", "ILCE_NOTU",
])
def test_her_ilce_her_sozlukte_var(sozluk_adi):
    sozluk = getattr(mp, sozluk_adi)
    eksik = [i for i in mp.ILCE if i not in sozluk]
    assert not eksik, f"{sozluk_adi} içinde eksik ilçe: {eksik}"


def test_her_urun_tanimli():
    for urun in mp.URUN:
        assert urun in mp.URETIM, f"{urun} için üretim yok"
        assert urun in mp.VERIM, f"{urun} için verim yok"
        assert urun in mp.DENGE_OLCEGI, f"{urun} için denge ölçeği yok"


def test_kaba_yem_grubu_urun_listesinde():
    for u in mp.KABA_YEM_GRUBU:
        assert u in mp.URUN
        assert mp.URUN[u][0] == "kaba", f"{u} kaba yem grubunda ama tipi 'kaba' değil"


# ------------------------------------------------------------ paylar
@pytest.mark.parametrize("ad,indeks", [
    ("nüfus", 1), ("tarım", 2), ("mera", 3), ("hayvan", 4),
])
def test_ilce_paylari_bire_toplanir(ad, indeks):
    toplam = sum(v[indeks] for v in mp.PAY.values())
    assert toplam == pytest.approx(1.0, abs=0.005), f"{ad} payları toplamı {toplam}"


def test_urun_paylari_bire_toplanir():
    for urun, paylar in mp.URUN_PAYI.items():
        toplam = sum(paylar.values())
        assert toplam == pytest.approx(1.0, abs=0.005), f"{urun}: {toplam}"
        eksik = set(mp.ILCE) - set(paylar)
        assert not eksik, f"{urun} payında eksik ilçe: {eksik}"


# ------------------------------------------------- dağıtım toplamı korur
def test_ilce_dagitimi_il_uretimini_korur():
    """İlçelere bölmek il toplamını değiştirmemeli.

    Bu, dağıtım mantığındaki en kolay hatadır: ilçe verimleri il ortalamasından
    farklı olduğu için alan hesabı kayarsa üretim toplamı tutmaz.
    """
    for urun in mp.URUN:
        _, uretim = mp.il_toplami(urun)
        resmi = mp.URETIM[urun][0]
        assert uretim == pytest.approx(resmi, rel=0.02), (
            f"{urun}: dağıtım sonrası {uretim:,.0f}, resmî {resmi:,.0f}")


def test_ilce_nufus_toplami_il_nufusuna_esit():
    toplam = sum(v[1] for v in mp.ILCE.values())
    assert toplam == pytest.approx(mp.OLCUM["nufus"][0], rel=0.01)


def test_ilce_mera_toplami_il_merasina_esit():
    toplam = sum(v[4] for v in mp.ILCE.values())
    assert toplam == pytest.approx(mp.OLCUM["mera_da"][0], rel=0.01)


def test_ekim_alani_tarim_alanini_asmaz():
    """Türetilen ekim alanı toplamı, resmî tarım alanından büyük olamaz."""
    ekilen = sum(mp.il_alani(u) for u in mp.URUN)
    assert ekilen < mp.OLCUM["toplam_tarim_da"][0]


# --------------------------------------------------- makul aralıklar
def test_toprak_degerleri_makul():
    for ilce, t in mp.TOPRAK.items():
        ph, om, kirec, ec, kil, kum, silt, p, k, drenaj, erozyon, derinlik = t
        assert 3 <= ph <= 10, f"{ilce}: pH {ph}"
        assert 0 <= om <= 15, f"{ilce}: organik madde {om}"
        assert 0 <= kirec <= 60, f"{ilce}: kireç {kirec}"
        assert 0 <= ec <= 20, f"{ilce}: EC {ec}"
        assert kil + kum + silt == pytest.approx(100, abs=1), f"{ilce}: bünye toplamı"
        assert drenaj in ("iyi", "orta", "zayıf"), f"{ilce}: drenaj {drenaj}"
        assert 1 <= erozyon <= 5, f"{ilce}: erozyon {erozyon}"
        assert 10 <= derinlik <= 300, f"{ilce}: derinlik {derinlik}"


def test_iklim_degerleri_makul():
    for ilce, (sicaklik, yagis, don) in mp.IKLIM.items():
        assert -5 <= sicaklik <= 25, f"{ilce}: sıcaklık {sicaklik}"
        assert 150 <= yagis <= 2500, f"{ilce}: yağış {yagis}"
        assert 1 <= don <= 12, f"{ilce}: don ayı {don}"


def test_rakim_ile_sicaklik_ters_orantili():
    """Yükseldikçe soğur. Veri girilirken en kolay yapılan hata bunu bozmaktır."""
    sirali = sorted(mp.ILCE, key=lambda i: mp.ILCE[i][0])
    sicakliklar = [mp.IKLIM[i][0] for i in sirali]
    assert sicakliklar == sorted(sicakliklar, reverse=True), (
        "rakım artarken sıcaklık düşmüyor")


def test_koordinatlar_mus_sinirlarinda():
    """Muş yaklaşık 38,4–39,5 K ve 41,0–42,8 D arasında."""
    for ilce, (enlem, boylam) in mp.KOORDINAT.items():
        assert 38.0 <= enlem <= 39.6, f"{ilce} enlem {enlem}"
        assert 40.8 <= boylam <= 43.0, f"{ilce} boylam {boylam}"


def test_kuru_madde_oranlari_makul():
    for urun, oran in mp.KURU_MADDE.items():
        assert 0.1 <= oran <= 1.0, f"{urun}: kuru madde {oran}"
        assert urun in mp.URUN


def test_verim_pozitif():
    for urun, verim in mp.VERIM.items():
        assert verim > 0, f"{urun}: verim {verim}"


# --------------------------------------------------------------- künye
def test_kunye_turleri_gecerli():
    gecerli = {"ölçüm", "varsayım", "dağıtım"}
    for alan, tur, kaynak, yil, guven, not_ in mp.KUNYE:
        assert tur in gecerli, f"{alan}: bilinmeyen tür {tur}"
        assert guven in ("yüksek", "orta", "düşük"), f"{alan}: güven {guven}"
        assert kaynak, f"{alan}: kaynak boş"


def test_olcum_kayitlarinin_kaynagi_var():
    for ad, (deger, birim, kaynak) in mp.OLCUM.items():
        assert deger > 0, f"{ad}: değer {deger}"
        assert birim, f"{ad}: birim boş"
        assert kaynak, f"{ad}: kaynak boş"


def test_fabrika_kapasitesi_teyit_edilmedi_olarak_isaretli():
    """Teyit edilmemiş bir sayı, teyit edilmiş gibi görünmemeli."""
    assert mp.FABRIKA["teyit"] is False
    assert "teyit" in mp.FABRIKA["not"].lower()
