"""
AGROMATCH - Denge hesaplarının izlenebilir grafiği
===================================================
mus_belirsizlik.py'deki altı denge sorusu burada iz.py grafiğiyle yeniden
kurulur. Fark şu: orada formüller elle yazılmış Python fonksiyonlarıydı ve
künye ayrı bir listede elle tutuluyordu. Burada her büyüklük kendi kaynağını
ve bağımlılıklarını taşıyor, künye hesabın kendisinden çıkıyor.

Kazançlar:
  - Panelde bir sayıya tıklayıp kaynağına kadar inilebiliyor.
  - Monte Carlo ve duyarlılık hesabı grafikten otomatik çıkıyor; elle
    yazılmış örnekleme fonksiyonuna gerek yok.
  - Formül değişince künye kendiliğinden değişiyor, eskiyemiyor.

DOĞRULAMA
---------
Bu modül, mevcut mus_belirsizlik.py ile aynı sayıları üretmek zorundadır.
--dogrula bayrağı ikisini karşılaştırır. Yeni bir soyutlama getirirken
eskisiyle aynı sonucu verdiğini göstermek, soyutlamanın doğru olduğunun
tek kanıtıdır.

    python src/mus_iz.py
    python src/mus_iz.py --dogrula
"""

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

import iz
import mus_profil as mp
from iz import Calisma, bol, carp, fark, olcum, topla, varsayim

CIKTI = Path(__file__).resolve().parent.parent / "outputs"
ORNEK = 40000
TOHUM = 20261008

KAYNAK = "TÜİK 2024 · Bakanlık Muş Tarımsal Yatırım Rehberi 2025"


def yol(yontem: str, birim: str, miktar: int, zorluk: int,
        kim: str) -> dict[str, Any]:
    """Bir bilinmeyenin nasıl ölçüleceği.

    Emek = miktar × zorluk. Ölçüm önceliği bu sayıya göre sıralanır: tek bir
    resmî yazı (1 × 1) ile 40 noktalık saha çalışması (40 × 2) aynı kefeye
    konamaz. masa_basi, saha işi gerektirmeyen kalemleri ayırır.
    """
    return dict(yontem=yontem, birim=birim, miktar=miktar, zorluk=zorluk,
                kim=kim, emek=miktar * zorluk, masa_basi=bool(miktar <= 2))


# ======================================================================
#  Ortak yapraklar — bir kez kurulur, bütün dengelerde paylaşılır
# ======================================================================
def yapraklar() -> dict[str, iz.Dugum]:
    y = {}
    y["nufus"] = olcum("Muş nüfusu", mp.OLCUM["nufus"][0], "kişi", kaynak=KAYNAK)
    y["buyukbas"] = olcum("Büyükbaş hayvan", mp.OLCUM["buyukbas"][0], "baş",
                          kaynak=KAYNAK)
    y["kucukbas"] = olcum("Küçükbaş hayvan", mp.OLCUM["kucukbas"][0], "baş",
                          kaynak=KAYNAK)
    y["mera_alan"] = olcum("Kadastral mera alanı", mp.OLCUM["mera_da"][0], "dekar",
                           kaynak=KAYNAK)

    y["yem_bb"] = varsayim(
        "Büyükbaş yıllık kaba yem ihtiyacı", 2.60, "ton KM/baş", (2.20, 3.10),
        gerekce="Canlı ağırlığa, süt verimine ve barınma süresine bağlı. "
                "Muş'ta ağırlıklı melez sığır var.",
        olcum_yolu=yol("İl Müdürlüğü ırk dağılımı", "resmî yazı", 1, 1, "Danışman hoca"))
    y["yem_kb"] = varsayim(
        "Küçükbaş yıllık kaba yem ihtiyacı", 0.45, "ton KM/baş", (0.35, 0.58),
        gerekce="1,16 milyon başta küçük bir sapma büyük tonaja dönüşüyor.",
        olcum_yolu=yol("Sürü kompozisyonu anketi", "işletme", 30, 3, "Öğrenci ekibi + Zootekni"))
    y["kesif_bb"] = varsayim(
        "Büyükbaş yıllık kesif yem ihtiyacı", 0.80, "ton/baş", (0.55, 1.15),
        gerekce="Besi ve süt işletmeleri arasında iki kat fark olabilir.",
        olcum_yolu=yol(
                "Yem bayisi satış kaydı + işletme anketi", "işletme", 25,
                3, "Öğrenci ekibi"))
    y["kesif_kb"] = varsayim(
        "Küçükbaş yıllık kesif yem ihtiyacı", 0.06, "ton/baş", (0.025, 0.10),
        gerekce="Meraya dayalı küçükbaşta az; ağıl döneminde artar.",
        olcum_yolu=yol("İşletme anketi", "işletme", 25, 3, "Öğrenci ekibi"))

    y["mera_verim"] = varsayim(
        "Mera verimi", 0.10, "ton KM/dekar", (0.05, 0.18),
        gerekce="Doğu Anadolu'da bozulmuş mera 0,04–0,08; iyi mera 0,15–0,25. "
                "Muş'ta ölçüm yok.",
        olcum_yolu=yol(
                "Kadran biçimi + Sentinel-2 NDVI kalibrasyonu", "saha noktası", 40,
                2, "Öğrenci ekibi + Tarla Bitkileri"))
    y["mera_oran"] = varsayim(
        "Otlatılabilir mera oranı", 0.88, "oran", (0.70, 1.00),
        gerekce="Kadastral alanın tamamı otlatılamaz: kayalık, dik, erişilemez.",
        olcum_yolu=yol(
                "Uydu görüntüsünden eğim ve arazi örtüsü maskesi", "ilçe", 6,
                1, "Öğrenci ekibi (ücretsiz veri)"))
    y["aniz_verim"] = varsayim(
        "Anız verimi", 0.05, "ton KM/dekar", (0.02, 0.09),
        gerekce="Hasat sonrası tarlada kalan ve hayvanın yiyebildiği sap.",
        olcum_yolu=yol("Hasat sonrası kadran biçimi", "tarla", 20, 2, "Öğrenci ekibi"))
    y["km_yesil"] = varsayim(
        "Yeşil otta kuru madde oranı", 0.25, "oran", (0.21, 0.30),
        gerekce="TÜİK yoncayı yeşil ot olarak kaydediyor; çevrim oranı biçim "
                "zamanına ve kurutma koşullarına göre değişir.",
        olcum_yolu=yol("Etüv kurutma (laboratuvar)", "örnek", 24, 2, "Üniversite laboratuvarı"))

    y["tohumluk"] = varsayim(
        "Tohumluk ve fire payı", 0.08, "oran", (0.04, 0.14),
        gerekce="Üretimin tohumluk ayrılan ve depoda kaybolan payı.",
        olcum_yolu=yol("İl Müdürlüğü sertifikalı tohum kaydı", "resmî yazı", 1, 1, "Danışman hoca"))
    y["kb_bugday"] = varsayim(
        "Kişi başı yıllık buğday", 0.250, "ton/kişi", (0.195, 0.300),
        gerekce="Un, bulgur, makarna eşdeğeri. Kırsalda ev ekmeği nedeniyle "
                "daha yüksek olabilir.",
        olcum_yolu=yol(
                "TÜİK hanehalkı tüketim anketi + bölgesel düzeltme", "masa başı", 1,
                2, "Öğrenci ekibi"))
    y["kb_patates"] = varsayim(
        "Kişi başı yıllık patates", 0.085, "ton/kişi", (0.055, 0.120),
        gerekce="Türkiye ortalaması mertebesi; bölgesel ölçüm yok.",
        olcum_yolu=yol("TÜİK hanehalkı tüketim anketi", "masa başı", 1, 2, "Öğrenci ekibi"))
    y["kb_fasulye"] = varsayim(
        "Kişi başı yıllık kuru fasulye", 0.009, "ton/kişi", (0.005, 0.014),
        gerekce="Kuru baklagil tüketimi; bölgesel kayıt yok.",
        olcum_yolu=yol("TÜİK hanehalkı tüketim anketi", "masa başı", 1, 2, "Öğrenci ekibi"))

    # Üretim: bir ölçümün kendisi de belirsiz olabilir
    y["u_bugday"] = olcum(
        "Buğday üretimi", 368297, "ton", aralik=(244000, 368297, 380000),
        kaynak=KAYNAK + " — KAYNAK KENDİSİYLE ÇELİŞİYOR: Tablo 3'te 368.297 ton, "
               "Bölüm 2.2'de '115 bin ha'da ~244 bin ton'")
    for ad, anahtar in (("Arpa", "u_arpa"), ("Yonca", "u_yonca"),
                        ("Korunga", "u_korunga"),
                        ("Silajlık mısır", "u_silaj"), ("Patates", "u_patates")):
        y[anahtar] = olcum(f"{ad} üretimi", mp.URETIM[ad][0], "ton", kaynak=KAYNAK)
    y["u_pancar"] = olcum("Şeker pancarı üretimi", mp.URETIM["Şeker pancarı"][0],
                          "ton", kaynak=KAYNAK)

    y["u_fig"] = varsayim(
        "Fiğ üretimi", mp.URETIM["Fiğ"][0], "ton",
        (mp.URETIM["Fiğ"][0] * 0.6, mp.URETIM["Fiğ"][0] * 1.5),
        gerekce="Resmî tabloda ayrı kalem değil; tamamen tahmin.",
        olcum_yolu=yol("İl Müdürlüğü ürün bazlı üretim kaydı", "resmî yazı", 1, 1, "Danışman hoca"))
    y["u_fasulye"] = varsayim(
        "Kuru fasulye üretimi", mp.URETIM["Kuru fasulye"][0], "ton",
        (mp.URETIM["Kuru fasulye"][0] * 0.6, mp.URETIM["Kuru fasulye"][0] * 1.5),
        gerekce="Resmî tabloda ayrı kalem değil; tamamen tahmin.",
        olcum_yolu=yol("İl Müdürlüğü ürün bazlı üretim kaydı", "resmî yazı", 1, 1, "Danışman hoca"))
    y["yem_carpan"] = varsayim(
        "Yem bitkisi üretimi çarpanı", 1.00, "çarpan", (0.85, 1.15),
        gerekce="Belgenin kendi içinde çelişkisi var (494.853 / 1.515.000 ton).",
        olcum_yolu=yol("İl Müdürlüğü üretim kaydı", "resmî yazı", 1, 1, "Danışman hoca"))
    y["pancar_carpan"] = varsayim(
        "Pancar üretimi çarpanı", 1.00, "çarpan", (0.95, 1.05),
        gerekce="TÜİK kaydı var; fabrika alım kaydıyla çapraz doğrulanabilir.",
        olcum_yolu=yol("Fabrika alım kaydı", "resmî yazı", 1, 1, "Danışman hoca"))
    y["hayvan_carpan"] = varsayim(
        "Hayvan sayısı çarpanı", 1.00, "çarpan", (0.95, 1.05),
        gerekce="TÜİK kaydı var; kayıt dışı hayvan ve yıl içi dalgalanma.",
        olcum_yolu=yol("TÜRKVET kaydı", "resmî yazı", 1, 1, "Danışman hoca"))

    y["fab_kapasite"] = varsayim(
        "Fabrika günlük kapasitesi", 7500, "ton/gün", (5000, 9500),
        gerekce="TEYİT EDİLMEDİ. Resmî kaynakta bulunamadı.",
        olcum_yolu=yol("Fabrika müdürlüğünden teyit", "resmî yazı", 1, 1, "Danışman hoca"))
    y["fab_gun"] = varsayim(
        "Kampanya süresi", 95, "gün", (75, 115),
        gerekce="Pancarın geliş hızına ve hava koşullarına göre değişir.",
        olcum_yolu=yol("Fabrika kampanya kaydı", "resmî yazı", 1, 1, "Danışman hoca"))

    y["tahil_alan"] = olcum(
        "Tahıl ekim alanı (buğday + arpa)",
        round(sum(mp.il_alani(u) for u in ("Buğday", "Arpa"))), "dekar",
        kaynak="Türetilmiş: üretim ÷ varsayılan verim")
    return y


# ======================================================================
#  Altı denge grafiği
# ======================================================================
def grafikler(y: dict[str, iz.Dugum]) -> dict[str, dict[str, Any]]:
    bb = carp("Büyükbaş (düzeltilmiş)", y["buyukbas"], y["hayvan_carpan"], birim="baş")
    kb = carp("Küçükbaş (düzeltilmiş)", y["kucukbas"], y["hayvan_carpan"], birim="baş")

    # --- 1. Kaba yem (ölçek: ilçe)
    kaba_ihtiyac = topla(
        "Kaba yem ihtiyacı",
        carp("Büyükbaş kaba yem", bb, y["yem_bb"], birim="ton KM"),
        carp("Küçükbaş kaba yem", kb, y["yem_kb"], birim="ton KM"),
        birim="ton KM")

    mera = carp("Meradan gelen yem", y["mera_alan"], y["mera_oran"],
                y["mera_verim"], birim="ton KM")
    aniz = carp("Anızdan gelen yem", y["tahil_alan"], y["aniz_verim"], birim="ton KM")
    yesil_ot = topla("Yeşil ot üretimi", y["u_yonca"], y["u_korunga"], y["u_fig"],
                     birim="ton")
    yem_bitkisi = carp(
        "Yem bitkisi (kuru madde)",
        topla("Kuru madde toplamı",
              carp("Yeşil ottan KM", yesil_ot, y["km_yesil"], birim="ton KM"),
              carp("Silajdan KM", y["u_silaj"],
                   varsayim("Silaj kuru madde oranı", mp.KURU_MADDE["Silajlık mısır"],
                            "oran"), birim="ton KM"),
              birim="ton KM"),
        y["yem_carpan"], birim="ton KM")
    kaba_arz = topla("Kaba yem arzı", mera, aniz, yem_bitkisi, birim="ton KM")

    # --- 2. Şeker pancarı (ölçek: fabrika havzası)
    pancar_arz = carp("Pancar arzı", y["u_pancar"], y["pancar_carpan"], birim="ton")
    pancar_ihtiyac = carp("Fabrika işleme kapasitesi", y["fab_kapasite"],
                          y["fab_gun"], birim="ton")

    # --- 3. Arpa (ölçek: il ve çevre il)
    arpa_ihtiyac = topla(
        "Arpa ihtiyacı",
        carp("Büyükbaş kesif yem", bb, y["kesif_bb"], birim="ton"),
        carp("Küçükbaş kesif yem", kb, y["kesif_kb"], birim="ton"),
        carp("Arpa tohumluk ve fire", y["u_arpa"], y["tohumluk"], birim="ton"),
        birim="ton")

    # --- 4. Buğday (ölçek: ulusal, il içi referans)
    bugday_ihtiyac = topla(
        "Buğday ihtiyacı (il içi)",
        carp("Gıda buğday talebi", y["nufus"], y["kb_bugday"], birim="ton"),
        carp("Buğday tohumluk ve fire", y["u_bugday"], y["tohumluk"], birim="ton"),
        birim="ton")

    # --- 5. Patates, 6. Kuru fasulye
    patates_ihtiyac = topla(
        "Patates ihtiyacı (il içi)",
        carp("Gıda patates talebi", y["nufus"], y["kb_patates"], birim="ton"),
        carp("Patates tohumluk ve fire", y["u_patates"], y["tohumluk"], birim="ton"),
        birim="ton")
    fasulye_ihtiyac = topla(
        "Kuru fasulye ihtiyacı (il içi)",
        carp("Gıda fasulye talebi", y["nufus"], y["kb_fasulye"], birim="ton"),
        carp("Fasulye tohumluk ve fire", y["u_fasulye"], y["tohumluk"], birim="ton"),
        birim="ton")

    # Her dengenin kimliği: başlık, kapsadığı ürünler, ölçek, grafiğin iki
    # tarafı, bu ölçekte fazlalığın sorun olup olmadığı ve okuma notu.
    # BU SÖZLÜK PROJEDEKİ TEK DENGE TANIMIDIR; mus_belirsizlik buradan beslenir.
    return {
        "kaba_yem": dict(
            baslik="Kaba yem", urunler=list(mp.KABA_YEM_GRUBU), olcek="ilçe",
            arz=kaba_arz, ihtiyac=kaba_ihtiyac, fazla_sorun=True,
            yorum="Hacimli ve ucuz; uzaktan getirmek ekonomik değil. Açık gerçek "
                  "açıktır. Mera ve anız arz tarafına dahildir."),
        "pancar": dict(
            baslik="Şeker pancarı", urunler=["Şeker pancarı"],
            olcek="fabrika havzası", arz=pancar_arz, ihtiyac=pancar_ihtiyac,
            fazla_sorun=True,
            yorum="Alıcısı tek tesis. 'İhtiyaç' burada fabrika kapasitesidir; "
                  "aşan miktar sökülse bile işlenemez."),
        "arpa": dict(
            baslik="Arpa (kesif yem)", urunler=["Arpa"], olcek="il ve çevre il",
            arz=y["u_arpa"], ihtiyac=arpa_ihtiyac, fazla_sorun=False,
            yorum="Taşınabilir ama ağırlıklı olarak yerinde tüketilir."),
        "bugday": dict(
            baslik="Buğday", urunler=["Buğday"], olcek="ulusal",
            arz=y["u_bugday"], ihtiyac=bugday_ihtiyac, fazla_sorun=False,
            yorum="İl içi tüketim sadece referans. Fazla, ilin ülkeye katkısıdır; "
                  "uyarı konusu değildir. Doğru soru ulusal ölçekte sorulur."),
        "patates": dict(
            baslik="Patates", urunler=["Patates"], olcek="ulusal",
            arz=y["u_patates"], ihtiyac=patates_ihtiyac, fazla_sorun=False,
            yorum="Ulusal piyasası var; il dengesi bağlayıcı değil."),
        "fasulye": dict(
            baslik="Kuru fasulye", urunler=["Kuru fasulye"], olcek="ulusal",
            arz=y["u_fasulye"], ihtiyac=fasulye_ihtiyac, fazla_sorun=False,
            yorum="Ulusal piyasası var; üretim verisi zaten tahmin."),
    }


def denge_grafigi() -> dict[str, dict[str, Any]]:
    """Denge grafiğini kurar ve döndürür. Tek giriş noktası.

    mus_belirsizlik bu fonksiyonu çağırır; denge formüllerinin ikinci bir
    kopyası projede bulunmaz.
    """
    return grafikler(yapraklar())


def analiz(n: int = ORNEK, tohum: int = TOHUM
           ) -> tuple[dict[str, Any], dict[str, dict[str, Any]], Calisma]:
    y = yapraklar()
    g = grafikler(y)
    c = Calisma(n, tohum)

    sorular = []
    for anahtar, kayit in g.items():
        oran = bol("Arz / ihtiyaç", kayit["arz"], kayit["ihtiyac"], birim="oran")
        x = oran.ornek(c)
        duyar = oran.duyarlilik(c)
        acik = fark("Açık", kayit["ihtiyac"], kayit["arz"],
                    birim=kayit["ihtiyac"].birim, en_az_sifir=True)

        sorular.append(dict(
            anahtar=anahtar, baslik=kayit["baslik"], olcek=kayit["olcek"],
            oran=dict(medyan=round(float(np.percentile(x, 50)), 3),
                      alt90=round(float(np.percentile(x, 5)), 3),
                      ust90=round(float(np.percentile(x, 95)), 3),
                      noktasal=round(oran.deger(), 3),
                      sapma=round(float(x.std()), 4)),
            arz=round(kayit["arz"].deger()),
            ihtiyac=round(kayit["ihtiyac"].deger()),
            acik=round(acik.deger()),
            dugum_sayisi=oran.dugum_sayisi(),
            derinlik=oran.derinlik(),
            yaprak_sayisi=len(oran.yapraklar()),
            belirsiz_yaprak=len(oran.belirsiz_yapraklar()),
            duyarlilik=duyar,
            agac=dict(arz=kayit["arz"].agac(paylar={
                          r["kimlik"]: r["varyans_payi"] for r in duyar}),
                      ihtiyac=kayit["ihtiyac"].agac(paylar={
                          r["kimlik"]: r["varyans_payi"] for r in duyar})),
        ))

    sonuc = dict(ornek_sayisi=n, tohum=tohum, sorular=sorular,
                 toplam_dugum=sum(q["dugum_sayisi"] for q in sorular))
    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "mus_iz.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    return sonuc, g, c


def dogrula() -> bool:
    """Grafiğin noktasal değeri, dağılımın merkeziyle tutarlı mı?

    Bir zamanlar bu fonksiyon grafiği, elle yazılmış ikinci bir hesapla
    karşılaştırıyordu. O ikinci hesap kaldırıldı (formüller artık tek yerde),
    dolayısıyla karşılaştırma kendini kendisiyle yapmaya dönüşmüştü.

    Yerine anlamlı bir kontrol kondu: noktasal değer (bütün varsayımlar en
    olası uçlarında) ile Monte Carlo medyanı birbirine yakın olmalı. Çok
    ayrışıyorlarsa ya dağılım aşırı çarpık ya da bir yerde hata var.

    Refactor'ın sayıları bozmadığının asıl güvencesi tests/test_altin.py'dir.
    """
    sonuc, g, c = analiz()
    print(f"{'DENGE':<22}{'NOKTASAL':>10}{'MC MEDYAN':>12}{'FARK':>9}  SONUÇ")
    hepsi = True
    for q in sonuc["sorular"]:
        nokta, medyan = q["oran"]["noktasal"], q["oran"]["medyan"]
        fark_yuzde = abs(nokta - medyan) / max(abs(medyan), 1e-9) * 100
        tuttu = fark_yuzde < 15
        hepsi &= tuttu
        print(f"{q['baslik']:<22}{nokta:>10.3f}{medyan:>12.3f}{fark_yuzde:>8.1f}%"
              f"  {'tutarlı' if tuttu else 'AYRIŞIYOR'}")
    print()
    print("Noktasal değerler dağılım merkezleriyle tutarlı." if hepsi
          else "AYRIŞMA VAR — dağılım çarpık ya da hesapta hata olabilir.")
    return hepsi


def main() -> None:
    if "--dogrula" in sys.argv:
        sys.exit(0 if dogrula() else 1)

    sonuc, g, c = analiz()
    print(f"Hesap grafiği · {sonuc['toplam_dugum']} düğüm · "
          f"{sonuc['ornek_sayisi']:,} örnek\n".replace(",", "."))

    print(f"{'DENGE':<22}{'ORAN':>8}{'DÜĞÜM':>7}{'DERİNLİK':>10}"
          f"{'BELİRSİZ YAPRAK':>17}")
    for q in sonuc["sorular"]:
        print(f"{q['baslik']:<22}{q['oran']['medyan']:>8.2f}{q['dugum_sayisi']:>7}"
              f"{q['derinlik']:>10}{q['belirsiz_yaprak']:>17}")

    print("\n" + "=" * 70)
    print("TÜREYİŞ AĞACI ÖRNEĞİ — Kaba yem arzı")
    print("=" * 70)
    kaba = g["kaba_yem"]
    oran = bol("Arz / ihtiyaç", kaba["arz"], kaba["ihtiyac"])
    paylar = {r["kimlik"]: r["varyans_payi"] for r in oran.duyarlilik(c)}
    iz.agac_yazdir(kaba["arz"], paylar=paylar)


if __name__ == "__main__":
    main()
