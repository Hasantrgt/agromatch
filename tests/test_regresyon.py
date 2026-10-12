"""
Regresyon testleri — geliştirme sırasında gerçekten yapılmış hatalar.

Buradaki her test, bir zamanlar yanlış çalışmış bir şeyi korur. Hepsinin
hikâyesi var ve hikâye testin içinde yazılı. Bir test kırılırsa, o hata
geri gelmiş demektir.

Bu dosya projenin en değerli testlerini içerir: genel doğruluk testleri
tahmin edilerek yazılır, bunlar ise acıyla öğrenilmiştir.
"""

import pytest

import mus_analiz
import mus_hastalik
import mus_iklim
import mus_profil as mp
import mus_toprak

# =====================================================================
#  HATA 1 — Bütün toprak uygunluk puanları aynı çıkıyordu
# =====================================================================
# Puanlama eşik tabanlıydı: pH optimum aralığın İÇİNDEYSE 100, dışındaysa
# düşük. Muş'ta bütün ürünlerin pH aralığı toprağı kapsadığı için hepsi 100
# alıyordu ve tablo tamamen aynı sayılarla doluyordu. Sürekli (parabolik)
# puanlamaya geçildi.

def test_urun_puanlari_birbirinden_farkli():
    """Aynı ilçede dokuz ürün aynı puanı almamalı."""
    puanlar = [mus_toprak.uygunluk("Merkez", u)["puan"] for u in mus_toprak.URUN_ISTEK]
    assert len(set(puanlar)) > 3, f"puanlar fazla benzer: {sorted(set(puanlar))}"
    assert max(puanlar) - min(puanlar) > 10, "puan aralığı çok dar"


def test_ph_puani_aralik_icinde_de_degisir():
    """Optimum aralığın ortası kenarından daha iyi puan almalı."""
    istek = dict(ph_opt=(6.0, 8.0), ph_sinir=(5.5, 8.5))
    orta = mus_toprak.ph_puan(7.0, istek)
    kenar = mus_toprak.ph_puan(8.0, istek)
    assert orta > kenar, "aralık içinde konum fark etmiyor"
    assert orta == pytest.approx(100, abs=0.5)


# =====================================================================
#  HATA 2 — Drenaj puanı ürüne bağlı değildi
# =====================================================================
# Drenajı zayıf bir tarlada yonca da buğday da aynı cezayı alıyordu. Oysa
# yonca ıslaklığa çok hassastır (kök boğazı çürür), buğday daha toleranslıdır.
# Ürün bazlı hassasiyet katsayısı eklendi.

def test_drenaj_cezasi_urune_gore_degisir():
    hassas = mus_toprak.drenaj_puan("zayıf", hassasiyet=5.0)
    toleransli = mus_toprak.drenaj_puan("zayıf", hassasiyet=1.0)
    assert hassas < toleransli, "drenaj cezası ürüne göre değişmiyor"


def test_iyi_drenajda_ceza_yok():
    for h in (1.0, 3.0, 5.0):
        assert mus_toprak.drenaj_puan("iyi", h) == 100.0


# =====================================================================
#  HATA 3 — Hastalık riski yıllık ortalama sıcaklıkla hesaplanıyordu
# =====================================================================
# Muş'un yıllık ortalaması 9,8 °C. Cercospora 20–28 °C ister. Yıllık ortalama
# kullanıldığında bütün yaz hastalıklarının riski sıfırlanıyordu — oysa Muş'un
# temmuz ortalaması 23,6 °C. Kritik ayların sıcaklığına geçildi.

def test_yaz_hastaligi_sifir_risk_almiyor():
    sonuc = mus_hastalik.analiz()
    cerco = [r for r in sonuc["satirlar"] if r["hastalik"] == "Cercospora yaprak lekesi"]
    assert cerco, "Cercospora kaydı yok"
    assert all(r["risk"] > 30 for r in cerco), (
        f"yaz hastalığının riski düşük: {[r['risk'] for r in cerco]}")


def test_temmuz_yillik_ortalamadan_cok_sicak():
    """Mevsim eğrisi çalışıyor mu — yıllık ortalama ile temmuz arasında fark olmalı."""
    aylik = mus_iklim.aylik_sicaklik("Merkez")
    yillik = mp.IKLIM["Merkez"][0]
    assert aylik[6] > yillik + 10, "temmuz sıcaklığı yıllık ortalamaya çok yakın"
    assert aylik[0] < yillik - 10, "ocak sıcaklığı yıllık ortalamaya çok yakın"


def test_kis_hastaligi_yazin_dusuk_risk():
    """Kar küfü (0–8 °C, şubat-mart) yaz aylarında yüksek risk almamalı."""
    s = mus_hastalik.sicaklik_uygunlugu("Merkez", kritik_aylar=[7, 8], aralik=(0, 8))
    assert s < 0.2, f"soğuk hastalığı yaz aylarında uygun çıkıyor: {s}"


# =====================================================================
#  HATA 4 — Kaba yem dengesinde yaş ve kuru ağırlık karıştırılıyordu
# =====================================================================
# Üretim yaş ağırlıkla (silajın %68'i su), ihtiyaç kuru maddeyle
# karşılaştırılıyordu. Silaj yoncadan üç kat fazla görünüyordu. Her iki taraf
# da kuru maddeye çevrildi ve satıra birim sütunu eklendi.

def test_kaba_yem_satirlari_kuru_madde_cinsinden():
    satirlar = mus_analiz.denge_analizi()
    kaba = [r for r in satirlar if r["tip"] == "kaba"]
    assert kaba, "kaba yem satırı yok"
    assert all(r["birim"] == "ton KM" for r in kaba), "kaba yem birimi kuru madde değil"


def test_gida_satirlari_urun_agirliginda():
    satirlar = mus_analiz.denge_analizi()
    gida = [r for r in satirlar if r["tip"] == "gıda"]
    assert all(r["birim"] == "ton" for r in gida)


def test_silaj_uretimi_kuru_maddeye_cevriliyor():
    """Silajın kuru madde oranı 0,32; üretim bu oranla düşmeli."""
    satirlar = mus_analiz.denge_analizi()
    silaj = next(r for r in satirlar
                 if r["urun"] == "Silajlık mısır" and r["ilce"] == "Merkez")
    yas = silaj["alan_dekar"] * silaj["verim"]
    assert silaj["uretim_ton"] == pytest.approx(yas * 0.32, rel=0.01)


# =====================================================================
#  HATA 5 — Yem bilançosunda mera ve anız unutulmuştu
# =====================================================================
# Sadece yem bitkileri sayıldığında açık ihtiyacın %80'ini aşıyordu; bu
# Muş gibi 3,7 milyon dekar merası olan bir il için saçmaydı. Mera ve
# hasat sonrası anız arz tarafına eklendi.

def test_mera_ve_aniz_arz_tarafinda():
    y = mus_analiz.yem_bilancosu("Varto")
    assert y["mera_ton"] > 0, "mera arza dahil değil"
    assert y["aniz_ton"] > 0, "anız arza dahil değil"
    assert y["arz_ton"] >= y["mera_ton"] + y["aniz_ton"]


def test_mera_yem_arzinin_buyuk_kismi():
    """Muş'ta mera, yem arzının en büyük kalemi olmalı."""
    y = mus_analiz.yem_bilancosu("Varto")
    assert y["mera_ton"] > y["kaba_ton"], "merası bol bir ilçede mera küçük kalmış"


def test_yem_acigi_makul_aralikta():
    """Açık var ama ihtiyacın tamamı kadar değil."""
    for ilce in mp.ILCE:
        y = mus_analiz.yem_bilancosu(ilce)
        assert 0.2 < y["karsilama"] < 1.0, f"{ilce}: karşılama {y['karsilama']}"


# =====================================================================
#  HATA 6 — İklim katmanı yoktu, Varto her üründe birinci çıkıyordu
# =====================================================================
# Varto'nun toprağı ilin en iyisi (volkanik, drenajlı, organik maddesi
# yüksek). Toprak tek başına bakıldığında şeker pancarında bile birinci
# çıkıyordu — oysa 1620 metrede pancar yetişmez. GDD ve donsuz dönem
# hesabı eklendi, toprakla geometrik ortalamayla birleştirildi.

def test_pancar_vartoda_en_dusuk():
    sonuc = mus_toprak.analiz()
    pancar = next(u for u in sonuc["urun_karsilastirma"] if u["urun"] == "Şeker pancarı")
    assert pancar["en_kotu"] == "Varto", (
        f"pancarda en zor ilçe Varto değil: {pancar['en_kotu']}")


def test_patates_vartoda_en_iyi():
    """Serin yayla patatesi — modelin agronomiyle uyuştuğunun kontrolü."""
    sonuc = mus_toprak.analiz()
    patates = next(u for u in sonuc["urun_karsilastirma"] if u["urun"] == "Patates")
    assert patates["en_iyi"] == "Varto"


def test_silajlik_misir_yuksek_rakimda_iklimle_sinirlanir():
    """Mısır sıcaklık toplamı ister; Varto'da yetişmez."""
    varto = mus_iklim.uygunluk("Varto", "Silajlık mısır")
    merkez = mus_iklim.uygunluk("Merkez", "Silajlık mısır")
    assert varto["puan"] < merkez["puan"] - 15
    assert varto["puan"] < 65, "yüksek rakımda mısır yeterince cezalanmıyor"


def test_birlesik_puan_geometrik_ortalama():
    """Aritmetik ortalama kullanılsaydı kötü iklim gizlenirdi."""
    assert mus_toprak.birlesik_puan(98, 46) == pytest.approx(67.2, abs=0.5)
    # aynı girdilerin aritmetik ortalaması 72 olurdu
    assert mus_toprak.birlesik_puan(98, 46) < 72


def test_birlesik_puan_tek_tarafli_iyilikle_kurtarilmaz():
    """Bir koşul çok kötüyse diğeri mükemmel olsa bile sonuç kötü kalmalı."""
    assert mus_toprak.birlesik_puan(100, 20) < 50


# =====================================================================
#  HATA 7 — Kritik toprak özellikleri ortalamada eriyordu
# =====================================================================
# Derinlik ağırlığı 0,05'ti. Kökü 120 cm'e inen pancar, 65 cm'lik Varto
# toprağında derinlikten 54 puan alıyor ama toplam puanı 97 çıkıyordu.
# Liebig'in minimum yasası: drenaj, tuzluluk ve derinlik telafi edilemez.

def test_kritik_bilesen_tavan_koyar():
    """Drenajı zayıf bir ilçede ham puan yüksek olsa bile tavan uygulanmalı."""
    u = mus_toprak.uygunluk("Merkez", "Şeker pancarı")   # Merkez drenajı zayıf
    assert u["tavanlandi"], "tavan uygulanmamış"
    assert u["puan"] < u["ham_puan"]
    assert u["tavan_sebebi"] in mus_toprak.KRITIK


def test_tavan_formulu():
    """Tavan = 55 + 0,45 × en düşük kritik bileşen."""
    u = mus_toprak.uygunluk("Merkez", "Şeker pancarı")
    en_dusuk = min(u["bilesen"][k] for k in mus_toprak.KRITIK)
    assert u["puan"] == pytest.approx(min(u["ham_puan"], 55 + 0.45 * en_dusuk), abs=0.1)


def test_kritik_bilesenleri_yuksekse_tavan_baglamaz():
    """Tavan her zaman devrede değil; sadece kritik bir bileşen düşükse bağlar.

    Varto'da kuru fasulye: drenaj iyi, tuz yok, kök 60 cm (toprak 65 cm yeter).
    Üç kritik bileşen de yüksek olduğu için tavan ham puanın üstünde kalır.
    """
    u = mus_toprak.uygunluk("Varto", "Kuru fasulye")
    assert not u["tavanlandi"]
    assert u["puan"] == u["ham_puan"]


def test_sig_toprak_derin_koklu_urunu_sinirlar():
    """Varto'nun toprağı 65 cm. Derin köklü ürün burada tavanlanır, sığ köklü
    ürün tavanlanmaz — bu testi yazarken fark edildi.

    Kök derinliği: arpa 80 cm (tavanlanır), patates 60 cm (tavanlanmaz).
    """
    assert mp.TOPRAK["Varto"][11] == 65

    derin = mus_toprak.uygunluk("Varto", "Arpa")
    sig = mus_toprak.uygunluk("Varto", "Patates")

    assert derin["tavanlandi"], "sığ toprakta derin köklü ürün tavanlanmıyor"
    assert derin["tavan_sebebi"] == "derinlik"
    assert not sig["tavanlandi"], "sığ köklü ürün gereksiz tavanlanmış"
    assert sig["bilesen"]["derinlik"] == 100.0


# =====================================================================
#  HATA 8 — Fabrika kotası il verimiyle değil, yanlış verimle hesaplanıyordu
# =====================================================================

def test_kota_ortalama_verimle_tutarli():
    k = mus_analiz.kota_ozeti()
    beklenen = k["uretim_ton"] / k["mevcut_alan_dekar"]
    assert k["ortalama_verim"] == pytest.approx(beklenen, rel=0.01)
    assert k["tavan_alan_dekar"] == pytest.approx(
        k["tavan_ton"] / k["ortalama_verim"], rel=0.01)


def test_kota_dagitimi_tavani_asmaz():
    k = mus_analiz.kota_ozeti()
    toplam_kota = sum(d["kota"] for d in k["ilce"])
    assert toplam_kota <= k["tavan_ton"] * 1.01
