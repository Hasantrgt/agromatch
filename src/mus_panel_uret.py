"""
AGROMATCH - Muş paneli üretici
==============================
Panelin kaynağı src/panel/ altında parçalara ayrılmıştır:

    panel/bas.html      <title>, yazı tipi bağlantıları
    panel/stil.css      bütün biçimlendirme
    panel/govde.html    sayfa iskeleti
    panel/js/*.js       sıra numarasına göre birleştirilen betikler

Bu betik hepsini birleştirip TEK DOSYALIK mus_panel.html üretir. Tek dosya
olması bilinçli: panelin dış bağlantı olmadan, bir USB bellekten ya da
e-posta ekinden açılabilmesi gerekiyor. Kaynağın parçalı olması ise
ayrı bir ihtiyaç — 1.100 satırlık tek bir betiğe birden fazla kişi
dokunamaz.

Panel elle düzenlenmez; veri değişince bu betik yeniden çalıştırılır:

    python src/mus_profil.py        # veri tutarlılığını denetle
    python src/mus_toprak.py        # toprak + iklim
    python src/mus_hastalik.py      # hastalık riski
    python src/mus_analiz.py        # denge, yem, kota, karne
    python src/mus_panel_uret.py    # paneli üret

ya da kısaca:  python src/mus_panel_uret.py --hepsi
"""

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "outputs"

BOS_DEPO: dict = {"zararlilar": [], "mucadele": [], "kaynaklar": {},
                  "ozet": {}, "ambar": {"ilceler": [], "aylar": [], "yigin": {},
                                        "dis_hava": {}, "pencere": [], "sonumleme": 0},
                  "doz_cevap": {"lc": {}, "noktalar": [], "egri": [], "sentetik": True}}

BOS_BOCEK: dict = {"zararlilar": [], "faydalilar": [], "gruplar": [],
                   "takvim": [], "ay_yogunlugu": [], "aylar": [],
                   "koprular": {"vektor_hastalik": [], "depo_koprusu": [],
                                "katalogda_olmayan": []},
                   "bosluklar": {"esiksiz": [], "kalintisiz_yolu_yok": [],
                                 "dogal_dusmani_yazilmamis": [],
                                 "dogrulanmamis_kayit": 0},
                   "ozet": {}}

BOS_UYARI: dict = {"uyarilar": {}, "ilceler": [], "aylar": [], "turler": [],
                   "aylik_sayi": {}, "gunluk_veri": False, "cozunurluk": "ay",
                   "ozet": {}}

BOS_KARLILIK: dict = {"satirlar": [], "piyasa": [], "ayirt_edilebilirlik": [],
                      "parametre": {}, "veri_yasi": {}, "ozet": {}}

BOS_CATI: dict = {"var": False}
BOS_YENI: dict = {"var": False}
BOS_OLCUM: dict = {"var": False}
BOS_KALITE: dict = {"var": False}
BOS_DOGRULAMA: dict = {"var": False}
BOS_KIL: dict = {"var": False}
BOS_ETKI: dict = {"satirlar": [], "ozet": {}, "sinif_degisenler": []}
BOS_COLLESME: dict = {"satirlar": [], "siniflar": [], "ozet": {}, "resmi": {},
                      "ayrim": []}

BOS_CERCO = {
    "asamalar": [], "siddet_olcegi": [], "siddet_ornek": [],
    "dogrulama": None, "parametre_taramasi": [], "parametreler": {},
}


def hepsini_calistir():
    import mus_analiz
    import mus_belirsizlik
    import mus_hastalik
    import mus_iz
    import mus_profil
    import mus_toprak

    hatalar = mus_profil.denetle()
    if hatalar:
        print("VERİ TUTARSIZ — panel üretilmedi:")
        for h in hatalar:
            print("  -", h)
        sys.exit(1)

    toprak = mus_toprak.analiz()
    mus_hastalik.analiz()
    mus_belirsizlik.analiz()
    mus_iz.analiz()
    puanlar = mus_toprak.ilce_puanlari(toprak)

    veri = mus_analiz.calistir(puanlar)
    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "mus.json").write_text(
        json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    # Depo katmanı scipy/statsmodels ister. Kurulu değilse panelin tamamı
    # çökmesin: görüntü hattındaki gibi o sekme boş kalsın, sebebi yazılsın.
    try:
        import depo.depo_panel_veri as dpv
    except ImportError as e:
        print(f"NOT: Depo katmanı atlandı ({e.name} kurulu değil).")
        print("     Kurmak için: pip install -r requirements-depo.txt")
    else:
        (CIKTI / "depo.json").write_text(
            json.dumps(dpv.uret(), ensure_ascii=False, indent=1),
            encoding="utf-8")
    # Çatı: 1. ve 2. kısmı birbirine soran katman. Dış veri istemez, bu
    # yüzden koşulsuz üretilir.
    import cati
    cati.uret()  # outputs/cati.json'u kendisi yazar
    import yeni_urun
    yeni_urun.uret()  # outputs/yeni_urun.json
    import collesme.dsi as cds
    import toprak_olcum.analiz as tol
    import toprak_olcum.etki as tet
    (CIKTI / "toprak_olcum.json").write_text(
        json.dumps(tol.uret(), ensure_ascii=False, indent=1), encoding="utf-8")
    (CIKTI / "olcum_etkisi.json").write_text(
        json.dumps(tet.karsilastir(), ensure_ascii=False, indent=1),
        encoding="utf-8")
    (CIKTI / "collesme.json").write_text(
        json.dumps(cds.uret(), ensure_ascii=False, indent=1), encoding="utf-8")
    # Kalite raporu YALNIZCA ham dosyalardan üretilebilir; özetten
    # yeniden kurulamaz. Ham veri yoksa depodaki rapor OLDUĞU GİBİ
    # bırakılır — boş bir raporla üzerine yazmak, yayındaki panelde
    # denetimin tamamını silerdi.
    import toprak_olcum.kalite as tkl
    kalite_raporu = tkl.rapor()
    if kalite_raporu.get("var"):
        (CIKTI / "veri_kalitesi.json").write_text(
            json.dumps(kalite_raporu, ensure_ascii=False, indent=1),
            encoding="utf-8")
    else:
        print("NOT: Ham laboratuvar dosyası yok; depodaki veri kalitesi "
              "raporu korundu.")
    # Bağımsız kaynakla doğrulama. SoilGrids çıktısı depoda durmaz ve
    # internet ister, bu yüzden kalite raporuyla aynı kural: üretilemiyorsa
    # depodaki sonuç OLDUĞU GİBİ bırakılır.
    import toprak_dogrulama.karsilastir as tdk
    dogrulama = tdk.uret()
    if dogrulama.get("var"):
        (CIKTI / "toprak_dogrulama.json").write_text(
            json.dumps(dogrulama, ensure_ascii=False, indent=1),
            encoding="utf-8")
    else:
        print("NOT: SoilGrids verisi yok; depodaki doğrulama sonucu korundu.")
        print("     Üretmek için: python src/toprak_dogrulama/soilgrids_cek.py")
    import toprak_dogrulama.kil_etkisi as tke
    kil_etkisi = tke.uret()
    if kil_etkisi.get("var"):
        (CIKTI / "kil_etkisi.json").write_text(
            json.dumps(kil_etkisi, ensure_ascii=False, indent=1),
            encoding="utf-8")
    # Toprak ölçüm hatasının ürün kararını ne kadar bozduğu. Panelde
    # doğrudan görünmüyor ama dışa aktarma paketine giriyor; zincirde
    # olmazsa temiz klonda o veri seti boş kalır.
    import toprak_urun_duyarlilik as tud
    tud.main([])
    import piyasa.karlilik as pkr
    (CIKTI / "karlilik.json").write_text(
        json.dumps(pkr.uret(), ensure_ascii=False, indent=1), encoding="utf-8")
    import uyari.takvim as utk
    (CIKTI / "uyari.json").write_text(
        json.dumps(utk.uret(), ensure_ascii=False, indent=1), encoding="utf-8")
    import bocek.bocek_panel_veri as bpv
    (CIKTI / "bocek.json").write_text(
        json.dumps(bpv.uret(), ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("Analizler yeniden çalıştı.")


def oku(ad, varsayilan=None):
    """Üretilmiş bir JSON çıktısını okur.

    Üç ayrı başarısızlık var ve üçü farklı şey söyler:
      dosya yok     -> analizler hiç çalışmamış
      JSON bozuk    -> yazma işlemi yarıda kesilmiş (disk dolu, Ctrl+C)
      içerik boş    -> analiz çalıştı ama sonuç üretmedi

    Hepsini aynı yığın izine bırakmak, hatayı okuyana "bir şeyler bozuk"
    demekten başka bir şey söylemez.
    """
    yol = CIKTI / ad
    if not yol.exists():
        if varsayilan is None:
            raise SystemExit(
                f"{ad} bulunamadı ({yol}).\n"
                f"Analizler henüz çalışmamış. Şunu çalıştır:\n"
                f"  python src/mus_panel_uret.py --hepsi")
        return varsayilan

    try:
        metin = yol.read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"{ad} okunamadı: {e}") from e

    try:
        veri = json.loads(metin)
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"{ad} bozuk JSON (satır {e.lineno}, sütun {e.colno}): {e.msg}\n"
            f"Yazma işlemi yarıda kesilmiş olabilir. Dosyayı silip "
            f"analizleri yeniden çalıştır:\n"
            f"  rm {yol}\n"
            f"  python src/mus_panel_uret.py --hepsi") from e

    if not veri:
        raise SystemExit(
            f"{ad} boş. Analiz çalıştı ama sonuç üretmedi; "
            f"veri tutarlılığını denetle:\n"
            f"  python src/mus_profil.py")
    return veri


def sablonu_birlestir():
    """src/panel/ altındaki parçaları tek bir HTML şablonuna birleştirir.

    JS dosyaları ad sırasına göre yüklenir; sıra numaraları (00_, 10_, 90_)
    bunun içindir. Yükleme sırası önemlidir: yardımcılar sekme fonksiyonlarından,
    sekme fonksiyonları da yönlendirmeden önce gelmelidir.
    """
    kaynak = Path(__file__).parent / "panel"
    if not kaynak.is_dir():
        raise SystemExit(f"Panel kaynağı yok: {kaynak}")

    for ad in ("bas.html", "stil.css", "govde.html"):
        if not (kaynak / ad).exists():
            raise SystemExit(f"Panel parçası eksik: {kaynak / ad}")

    js_dosyalari = sorted((kaynak / "js").glob("*.js"))
    if not js_dosyalari:
        raise SystemExit(
            f"{kaynak / 'js'} içinde betik yok.\n"
            f"Panel kaynağı parçalı; en az 00_veri.js ve 90_uygulama.js olmalı.")

    numarasiz = [d.name for d in js_dosyalari if not d.name[:2].isdigit()]
    if numarasiz:
        raise SystemExit(
            f"Sıra numarası olmayan betik: {', '.join(numarasiz)}\n"
            f"Yükleme sırası ada göre belirlenir; her dosya iki haneli bir "
            f"numarayla başlamalı (00_, 10_, 90_).")

    betik = "\n\n".join(
        f"// ===== {d.name} " + "=" * max(0, 60 - len(d.name))
        + "\n" + d.read_text(encoding="utf-8").strip()
        for d in js_dosyalari)

    return (
        kaynak.joinpath("bas.html").read_text(encoding="utf-8").rstrip()
        + "\n<style>\n"
        + kaynak.joinpath("stil.css").read_text(encoding="utf-8").rstrip()
        + "\n</style>\n\n"
        + kaynak.joinpath("govde.html").read_text(encoding="utf-8").strip()
        + "\n\n<script>\n" + betik + "\n</script>\n")


def main():
    if "--hepsi" in sys.argv:
        hepsini_calistir()

    mus = oku("mus.json")
    toprak = oku("mus_toprak.json")
    hastalik = oku("mus_hastalik.json")
    cerco = oku("cercospora.json", BOS_CERCO)
    if not cerco.get("asamalar"):
        print("NOT: Cercospora görüntü verisi yok, panelde o bölüm boş kalacak.")
        print("     Üretmek için (opencv ve pillow gerekir):")
        print("       pip install -r requirements-goruntu.txt")
        print("       python src/goruntu/sentetik_yaprak.py")
        print("       python src/goruntu/cercospora_panel_veri.py")
    belirsiz = oku("mus_belirsizlik.json")
    izveri = oku("mus_iz.json", {"sorular": []})
    depo = oku("depo.json", BOS_DEPO)
    if not depo.get("zararlilar"):
        print("NOT: Depo verisi yok, o sekme boş kalacak.")
        print("     Üretmek için: python src/depo/depo_panel_veri.py")

    bocek = oku("bocek.json", BOS_BOCEK)
    if not bocek.get("zararlilar"):
        print("NOT: Böcek verisi yok, o sekme boş kalacak.")
        print("     Üretmek için: python src/bocek/bocek_panel_veri.py")

    uyari = oku("uyari.json", BOS_UYARI)
    if not uyari.get("ilceler"):
        print("NOT: Uyarı verisi yok, o sekme boş kalacak.")
        print("     Üretmek için: python src/uyari/takvim.py")

    karlilik = oku("karlilik.json", BOS_KARLILIK)
    if not karlilik.get("satirlar"):
        print("NOT: Karlılık verisi yok, o sekme boş kalacak.")
        print("     Üretmek için: python src/piyasa/karlilik.py")

    yeniveri = oku("yeni_urun.json", BOS_YENI)
    cativeri = oku("cati.json", BOS_CATI)
    if not cativeri.get("var"):
        print("NOT: Çatı verisi yok, o sekmenin denetim bölümü boş kalacak.")
        print("     Üretmek için: python src/cati.py")

    olcum = oku("toprak_olcum.json", BOS_OLCUM)
    etki = oku("olcum_etkisi.json", BOS_ETKI)
    collesme = oku("collesme.json", BOS_COLLESME)
    kalite = oku("veri_kalitesi.json", BOS_KALITE)
    dogrulama = oku("toprak_dogrulama.json", BOS_DOGRULAMA)
    kil = oku("kil_etkisi.json", BOS_KIL)
    if not olcum.get("var"):
        print("NOT: Toprak ölçüm verisi yok, o sekme boş kalacak.")
        print("     Üretmek için: python src/toprak_olcum/analiz.py")

    sablon = sablonu_birlestir()
    html = (sablon
            .replace("__MUS_JSON__", json.dumps(mus, ensure_ascii=False))
            .replace("__TOPRAK_JSON__", json.dumps(toprak, ensure_ascii=False))
            .replace("__HASTALIK_JSON__", json.dumps(hastalik, ensure_ascii=False))
            .replace("__CERCOSPORA_JSON__", json.dumps(cerco, ensure_ascii=False))
            .replace("__BELIRSIZLIK_JSON__", json.dumps(belirsiz, ensure_ascii=False))
            .replace("__IZ_JSON__", json.dumps(izveri, ensure_ascii=False))
            .replace("__DEPO_JSON__", json.dumps(depo, ensure_ascii=False))
            .replace("__BOCEK_JSON__", json.dumps(bocek, ensure_ascii=False))
            .replace("__UYARI_JSON__", json.dumps(uyari, ensure_ascii=False))
            .replace("__KARLILIK_JSON__", json.dumps(karlilik, ensure_ascii=False))
            .replace("__OLCUM_JSON__", json.dumps(olcum, ensure_ascii=False))
            .replace("__ETKI_JSON__", json.dumps(etki, ensure_ascii=False))
            .replace("__COLLESME_JSON__", json.dumps(collesme, ensure_ascii=False))
            .replace("__KALITE_JSON__", json.dumps(kalite, ensure_ascii=False))
            .replace("__DOGRULAMA_JSON__",
                     json.dumps(dogrulama, ensure_ascii=False))
            .replace("__KIL_JSON__", json.dumps(kil, ensure_ascii=False))
            .replace("__CATI_JSON__",
                     json.dumps(cativeri, ensure_ascii=False))
            .replace("__YENI_JSON__",
                     json.dumps(yeniveri, ensure_ascii=False)))

    hedef = KOK / "mus_panel.html"
    hedef.write_text(html, encoding="utf-8")
    print(f"mus_panel.html yazıldı ({len(html.encode('utf-8')) // 1024} KB)")

    # Hızlı tutarlılık kontrolü: yer tutucu kalmadı mı
    kalan = [p for p in ("__MUS_JSON__", "__TOPRAK_JSON__", "__HASTALIK_JSON__",
                         "__CERCOSPORA_JSON__", "__BELIRSIZLIK_JSON__",
                         "__IZ_JSON__", "__DEPO_JSON__",
                         "__BOCEK_JSON__", "__UYARI_JSON__", "__KARLILIK_JSON__", "__OLCUM_JSON__",
                         "__ETKI_JSON__", "__COLLESME_JSON__",
                         "__KALITE_JSON__", "__DOGRULAMA_JSON__",
                         "__KIL_JSON__", "__CATI_JSON__",
                         "__YENI_JSON__") if p in html]
    if kalan:
        print("UYARI — doldurulmamış yer tutucu:", ", ".join(kalan))


if __name__ == "__main__":
    main()
