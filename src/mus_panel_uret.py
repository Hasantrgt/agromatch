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
    print("Analizler yeniden çalıştı.")


def oku(ad, varsayilan=None):
    yol = CIKTI / ad
    if not yol.exists():
        if varsayilan is None:
            raise SystemExit(f"{ad} yok. Önce analizleri çalıştır: "
                             f"python src/mus_panel_uret.py --hepsi")
        return varsayilan
    return json.loads(yol.read_text(encoding="utf-8"))


def sablonu_birlestir():
    """src/panel/ altındaki parçaları tek bir HTML şablonuna birleştirir.

    JS dosyaları ad sırasına göre yüklenir; sıra numaraları (00_, 10_, 90_)
    bunun içindir. Yükleme sırası önemlidir: yardımcılar sekme fonksiyonlarından,
    sekme fonksiyonları da yönlendirmeden önce gelmelidir.
    """
    kaynak = Path(__file__).parent / "panel"
    js_dosyalari = sorted((kaynak / "js").glob("*.js"))
    if not js_dosyalari:
        raise SystemExit(f"{kaynak / 'js'} içinde betik yok")

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

    sablon = sablonu_birlestir()
    html = (sablon
            .replace("__MUS_JSON__", json.dumps(mus, ensure_ascii=False))
            .replace("__TOPRAK_JSON__", json.dumps(toprak, ensure_ascii=False))
            .replace("__HASTALIK_JSON__", json.dumps(hastalik, ensure_ascii=False))
            .replace("__CERCOSPORA_JSON__", json.dumps(cerco, ensure_ascii=False))
            .replace("__BELIRSIZLIK_JSON__", json.dumps(belirsiz, ensure_ascii=False))
            .replace("__IZ_JSON__", json.dumps(izveri, ensure_ascii=False)))

    hedef = KOK / "mus_panel.html"
    hedef.write_text(html, encoding="utf-8")
    print(f"mus_panel.html yazıldı ({len(html.encode('utf-8')) // 1024} KB)")

    # Hızlı tutarlılık kontrolü: yer tutucu kalmadı mı
    kalan = [p for p in ("__MUS_JSON__", "__TOPRAK_JSON__", "__HASTALIK_JSON__",
                         "__CERCOSPORA_JSON__", "__BELIRSIZLIK_JSON__",
                         "__IZ_JSON__") if p in html]
    if kalan:
        print("UYARI — doldurulmamış yer tutucu:", ", ".join(kalan))


if __name__ == "__main__":
    main()
