"""
AGROMATCH - Muş paneli üretici
==============================
Analiz çıktılarını tek dosyalık mus_panel.html içine gömer. Panel elle
düzenlenmez; veri değişince bu betik yeniden çalıştırılır:

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


def main():
    if "--hepsi" in sys.argv:
        hepsini_calistir()

    mus = oku("mus.json")
    toprak = oku("mus_toprak.json")
    hastalik = oku("mus_hastalik.json")
    cerco = oku("cercospora.json", BOS_CERCO)
    belirsiz = oku("mus_belirsizlik.json")
    izveri = oku("mus_iz.json", {"sorular": []})

    sablon = (Path(__file__).parent / "mus_sablon.html").read_text(encoding="utf-8")
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
