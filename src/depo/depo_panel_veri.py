"""
AGROMATCH - Depo sekmesinin verisini üretir
============================================
Dört kaynağı tek JSON'da toplar:

    literatur        yayınlanmış doz–ölüm ölçümleri (GERÇEK veri)
    doz_cevap        bu ölçümlere uydurulan probit modeller
    depo_profil      zararlı ve mücadele katalogları
    ambar_sicaklik   ilçe bazında yığın sıcaklığı ve gelişme penceresi

Doz–cevap bölümü artık SENTETİK DEĞİL. İki açık erişimli yayından alınan
57 ölçüm (toplam 11.340 birey) kullanılıyor. Araç bu ölçümlerden LC50 ve
LC90 kestiriyor — yayınların KENDİSİ bu sayıları vermiyor, yalnızca yüzde
ölüm çizelgeleri veriyor. Yani burada üretilen şey literatürün tekrarı
değil, literatürden çıkarılan yeni bir sayı.

Danışman hocanın ham sayımları geldiğinde ``--veri`` ile aynı hat o veriyi
işler ve grafikte yayınların yanına yerleşir.

Çıktı: outputs/depo.json

    python src/depo/depo_panel_veri.py
    python src/depo/depo_panel_veri.py --veri data/deneme.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import mus_profil as mp
from depo import ambar_sicaklik as amb
from depo import depo_profil as dp
from depo import doz_cevap as dc
from depo import literatur as lit

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

# Eğrinin çizileceği doz noktası sayısı (log aralıklı)
EGRI_NOKTA = 48

# Büyük grafikte gösterilecek seri: en çok dozda ve en çok sürede ölçülmüş
# olan ürün. Dört süresi de aynı eksende çizilince LC50'nin sola kayışı
# görünüyor — bu sekmenin anlatmak istediği tek şey o.
VITRIN_URUN = "Silicid"
VITRIN_CALISMA = "agrafioti2023"


def egri(uyum: dc.Uyum, alt: float, ust: float) -> list[dict[str, float]]:
    """Uydurulan eğriyi çizim için noktalara açar."""
    cdf, _ = dc._bag(uyum.baglanti)
    xs = np.logspace(np.log10(max(alt, 1e-6)), np.log10(ust), EGRI_NOKTA)
    return [dict(doz=float(x),
                 olum=float(cdf(uyum.kesim + uyum.egim * np.log10(x))))
            for x in xs]


def seri_kaydi(gozlemler: list[dc.Gozlem], etiket: str, sure: float,
               kaynak: str, cizilsin: bool) -> dict[str, Any]:
    """Bir doz serisini uydurur ve panelin okuyacağı kaydı döndürür.

    Uyum başarısız olabilir ve bu bir hata değildir: üç günlük maruziyette
    doz ile ölüm arasında ilişki yoksa araç LC50 uydurmaz, 'kestirilemedi'
    der. Panelde bu satırlar da gösteriliyor — aracın ne zaman konuşmayı
    reddettiği, ne söylediği kadar önemli.
    """
    uyum = dc.uydur(gozlemler, eksen="doz", baglanti="probit")
    dozlar = [g.doz for g in gozlemler if g.doz > 0]
    en_az, en_cok = min(dozlar), max(dozlar)

    # Araç, denenen dozun onda biri ile on katı arasını kabul ediyor. Ama
    # denenen dozların DIŞINA düşen bir LC50, modelin ölçülmemiş bölgeye
    # uzatılmasıdır; panelde ayrı işaretlenmesi gerekir. Yayının kendisi de
    # o bölgede ne olduğunu bilmiyor.
    for k in uyum.lc.values():
        if "deger" in k:
            k["disinda"] = not (en_az <= k["deger"] <= en_cok)

    kayit: dict[str, Any] = dict(
        etiket=etiket, sure=sure, kaynak=kaynak,
        egim=round(uyum.egim, 3),
        n_birey=uyum.n_birey, n_gozlem=uyum.n_gozlem,
        doz_araligi=[en_az, en_cok],
        lc=uyum.lc, uyari=uyum.uyari,
        noktalar=[dict(doz=g.doz, olum=g.oran) for g in gozlemler if g.doz > 0],
        cizilsin=cizilsin,
    )
    if cizilsin and uyum.egim > 0:
        kayit["egri"] = egri(uyum, min(dozlar) * 0.7, max(dozlar) * 1.4)
    return kayit


def doz_cevap_bolumu(ek: list[dc.Gozlem] | None, ek_ad: str) -> dict[str, Any]:
    """Bütün yayınlanmış serileri uydurur, varsa hocanın verisini ekler."""
    seriler: list[dict[str, Any]] = []
    for calisma, formulasyon, sure, n_doz in lit.seriler():
        if n_doz < 3:
            continue          # üç dozun altında eğri uydurulmaz
        g = lit.gozlemler(calisma, formulasyon, sure)
        seriler.append(seri_kaydi(
            g, formulasyon, sure, calisma,
            cizilsin=(calisma == VITRIN_CALISMA
                      and formulasyon == VITRIN_URUN)))

    if ek:
        seriler.append(seri_kaydi(ek, ek_ad, ek[0].sure, "saha", cizilsin=True))

    # Vitrin eğrileri süreye göre sıralı dursun ki grafik soldan sağa okunsun
    cizilen = sorted((s for s in seriler if s.get("cizilsin")),
                     key=lambda s: s["sure"])
    ozet = lit.ozet()
    return dict(
        kaynak="saha" if ek else "literatur",
        vitrin=dict(urun=VITRIN_URUN,
                    calisma=VITRIN_CALISMA if not ek else "saha",
                    seriler=cizilen),
        seriler=sorted(seriler, key=lambda s: (s["kaynak"], s["etiket"], s["sure"])),
        calismalar={k: dict(yazarlar=c.yazarlar, yil=c.yil, dergi=c.dergi,
                            doi=c.doi, sicaklik=c.sicaklik, nem=c.nem,
                            urun=c.urun, n_hucre=c.n_hucre,
                            kontrol_notu=c.kontrol_notu, abbott=c.abbott,
                            not_=c.not_)
                    for k, c in lit.CALISMALAR.items()},
        ozet=ozet,
        karsitlik=lit.sicaklik_karsitligi(),
    )


def uret(veri: Path | None = None) -> dict[str, Any]:
    ek = dc.oku(veri) if veri else None
    ambar = amb.analiz()
    zararlilar = sorted(dp.ZARARLILAR,
                        key=lambda z: (-z["onem"], z["taban_sicaklik"]))
    dcb = doz_cevap_bolumu(ek, veri.stem if veri else "")

    # Literatürdeki koşullar ile Muş'un ambar sıcaklığını yan yana koy.
    # Bu kıyas, sekmenin iki yarısını birbirine bağlayan tek cümledir.
    en_sicak_yigin = max(max(v) for v in ambar["aylik_yigin"].values())
    kosullar = sorted({c["sicaklik"] for c in dcb["calismalar"].values()})
    return dict(
        zararlilar=[dict(z) for z in zararlilar],
        mucadele=list(dp.MUCADELE),
        kaynaklar=dp.KAYNAKLAR,
        ozet=dp.ozet(),
        ambar=dict(
            sonumleme=ambar["sonumleme"],
            ilceler=list(mp.ILCE),
            aylar=amb.AY_AD,
            yigin=ambar["aylik_yigin"],
            dis_hava=ambar["dis_hava"],
            pencere=ambar["satirlar"],
            not_=ambar["not_"],
        ),
        doz_cevap=dcb,
        acik=dict(
            yigin_en_sicak=round(en_sicak_yigin, 1),
            deneme_sicakliklari=kosullar,
            fark=round(min(kosullar) - en_sicak_yigin, 1),
        ),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--veri", type=Path,
                    help="hocanın ham deneme CSV'si (yayınların yanına eklenir)")
    a = ap.parse_args()

    veri = uret(a.veri)
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "depo.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    d, o = veri["doz_cevap"], veri["doz_cevap"]["ozet"]
    kestirilen = sum(1 for s in d["seriler"] if "deger" in s["lc"].get("LC50", {}))
    print(f"{yol} yazıldı")
    print(f"  zararlı {veri['ozet']['zararli']} · mücadele "
          f"{veri['ozet']['mucadele']} · kalıntısız {veri['ozet']['kalintisiz']}")
    print(f"  ambar penceresi {len(veri['ambar']['pencere'])} satır")
    print(f"  doz–cevap: {o['yayin']} yayın · {o['olcum']} ölçüm · "
          f"{o['birey']:,} birey")
    print(f"    {len(d['seriler'])} seri uyduruldu, {kestirilen} tanesinde "
          f"LC50 kestirilebildi")
    for s in d["seriler"]:
        lc = s["lc"].get("LC50", {})
        if "deger" in lc:
            print(f"    {s['etiket']:16s} {s['sure']:>3.0f}g  "
                  f"LC50 {lc['deger']:6.0f} ppm [{lc['alt']:.0f}–{lc['ust']:.0f}]")
        else:
            print(f"    {s['etiket']:16s} {s['sure']:>3.0f}g  "
                  f"LC50 kestirilemedi — {lc.get('kestirilemedi', '')}")
    k = veri["acik"]
    print(f"  Muş'ta yığının en sıcak ayı {k['yigin_en_sicak']} °C; "
          f"denemeler {k['deneme_sicakliklari']} °C'de yapılmış "
          f"({k['fark']} °C fark)")


if __name__ == "__main__":
    main()
