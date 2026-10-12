"""
AGROMATCH - Panel üretici
=========================
outputs/bolge.json ve outputs/sonuclar.json içeriğini panel şablonuna gömer
ve tek dosyalık panel.html üretir. Analiz yeniden çalıştırıldığında paneli
elle güncellemek gerekmez:

    python src/bolge_analiz.py && python src/analiz.py && python src/panel_uret.py
"""

import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "outputs"


def main():
    bolge = json.loads((CIKTI / "bolge.json").read_text(encoding="utf-8"))
    ant = json.loads((CIKTI / "sonuclar.json").read_text(encoding="utf-8"))

    # Panelin ihtiyacı olan Antalya verisini sadeleştir
    denge = [r for r in ant["denge"] if r["urun"] == "Biber"]
    denge.sort(key=lambda r: r["yil"])
    fiyat = sorted([r for r in ant["fiyat"] if r["urun"] == "Biber"], key=lambda r: r["yil"])
    ilk_alan = denge[0]["ekim_alani_dekar"]

    antalya = dict(
        yil=[r["yil"] for r in denge],
        alan_endeks=[round(r["ekim_alani_dekar"] / ilk_alan * 100, 1) for r in denge],
        fiyat_endeks=[round(r["reel_fiyat_endeksi"], 1) for r in fiyat],
        dongu=sorted(ant["dongu"], key=lambda r: -r["tepki_katsayisi"]),
        dagitim=ant["dagitim"],
    )

    senaryo_veri = json.loads((CIKTI / "senaryo.json").read_text(encoding="utf-8"))
    sablon = (Path(__file__).parent / "panel_sablon.html").read_text(encoding="utf-8")
    html = (sablon
            .replace("__KUNYE_JSON__", json.dumps(senaryo_veri["kunye"], ensure_ascii=False))
            .replace("__BOLGE_JSON__", json.dumps(bolge, ensure_ascii=False))
            .replace("__ANTALYA_JSON__", json.dumps(antalya, ensure_ascii=False)))
    (KOK / "panel.html").write_text(html, encoding="utf-8")
    print(f"panel.html yazıldı ({len(html) // 1024} KB)")

    # --- Ürün paneli
    urun = json.loads((CIKTI / "urun.json").read_text(encoding="utf-8"))
    sablon2 = (Path(__file__).parent / "urun_panel_sablon.html").read_text(encoding="utf-8")
    html2 = sablon2.replace("__URUN_JSON__", json.dumps(urun, ensure_ascii=False))
    (KOK / "urun_panel.html").write_text(html2, encoding="utf-8")
    print(f"urun_panel.html yazıldı ({len(html2) // 1024} KB)")

    # --- İl karnesi paneli
    karne = json.loads((CIKTI / "karne.json").read_text(encoding="utf-8"))
    sablon3 = (Path(__file__).parent / "karne_sablon.html").read_text(encoding="utf-8")
    html3 = sablon3.replace("__KARNE_JSON__", json.dumps(karne, ensure_ascii=False))
    (KOK / "il_karne.html").write_text(html3, encoding="utf-8")
    print(f"il_karne.html yazıldı ({len(html3) // 1024} KB)")

    # --- Senaryo simülatörü
    senaryo = json.loads((CIKTI / "senaryo.json").read_text(encoding="utf-8"))
    sablon4 = (Path(__file__).parent / "senaryo_sablon.html").read_text(encoding="utf-8")
    html4 = sablon4.replace("__SENARYO_JSON__", json.dumps(senaryo, ensure_ascii=False))
    (KOK / "simulator.html").write_text(html4, encoding="utf-8")
    print(f"simulator.html yazıldı ({len(html4) // 1024} KB)")

    harita_json = json.dumps(senaryo["harita"], ensure_ascii=False)

    # --- Toprak paneli
    toprak = json.loads((CIKTI / "toprak.json").read_text(encoding="utf-8"))
    sablon5 = (Path(__file__).parent / "toprak_sablon.html").read_text(encoding="utf-8")
    html5 = (sablon5.replace("__TOPRAK_JSON__", json.dumps(toprak, ensure_ascii=False))
                    .replace("__HARITA_JSON__", harita_json))
    (KOK / "toprak_panel.html").write_text(html5, encoding="utf-8")
    print(f"toprak_panel.html yazıldı ({len(html5) // 1024} KB)")

    # --- Hastalık paneli
    hastalik = json.loads((CIKTI / "hastalik.json").read_text(encoding="utf-8"))
    sablon6 = (Path(__file__).parent / "hastalik_sablon.html").read_text(encoding="utf-8")
    cerco_yol = CIKTI / "cercospora.json"
    cerco = (cerco_yol.read_text(encoding="utf-8") if cerco_yol.exists()
             else '{"asamalar":[],"siddet_olcegi":[],"siddet_ornek":[],'
                  '"dogrulama":{"satirlar":[],"kesinlik":0,"duyarlilik":0,"f1":0,'
                  '"ortalama_mutlak_sapma":0},"parametre_taramasi":[],'
                  '"parametreler":{"min_alan":0},"ornek":{"leke_sayisi":0,'
                  '"enfekte_alan_yuzdesi":0,"ortalama_cap_piksel":0,'
                  '"siddet":{"ad":"-","karar":"-","seviye":0}}}')
    html6 = (sablon6.replace("__HASTALIK_JSON__", json.dumps(hastalik, ensure_ascii=False))
                    .replace("__CERCOSPORA_JSON__", cerco)
                    .replace("__HARITA_JSON__", harita_json))
    (KOK / "hastalik_panel.html").write_text(html6, encoding="utf-8")
    print(f"hastalik_panel.html yazıldı ({len(html6) // 1024} KB)")


if __name__ == "__main__":
    main()
