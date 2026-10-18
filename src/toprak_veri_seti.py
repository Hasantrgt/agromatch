"""
AGROMATCH - Toprak uygunluk veri seti (veri madenciliği için)
=============================================================
NE ÜRETİR
Her satır bir (toprak numunesi, ürün) çiftidir. Öznitelikler bir laboratuvar
raporunda yazacak olan ÖLÇÜLEN değerlerdir; hedefler ise numunenin GERÇEK
değerlerinden hesaplanan uygunluk sonucudur.

NEDEN ARADA ÖLÇÜM HATASI VAR — bu dosyanın can alıcı noktası
Uygunluk puanı mus_toprak'taki kuralın deterministik çıktısıdır. Eğer
öznitelikler ile hedef aynı sayılardan hesaplansaydı, herhangi bir model
kuralı neredeyse hatasız ezberler ve %100 doğruluk verirdi. Böyle bir sonuç
hiçbir şey öğretmez: modelin yaptığı tek şey formülü yeniden keşfetmek olur.
(Cercospora veri setinde tam olarak bu tuzağa düşüp geri döndük.)

Gerçekte böyle değildir. Toprak raporundaki pH 7,6 değeri tarlanın pH'ı
DEĞİLDİR; tarlanın pH'ının bir ölçümüdür ve iki katman hata taşır:

  1. Mekânsal hata — numune tarlanın bir noktasından alınır, karar bütün
     tarla için verilir. Aynı parselin iki ucu farklı çıkar.
  2. Laboratuvar hatası — aynı numune iki kez ölçülse iki farklı sonuç verir.
     Cihaz, yöntem ve operatör farkı.

Bu veri seti o farkı modelliyor. Böylece sorulabilecek soru anlamlı hâle
geliyor ve projenin kendi sorusuyla birebir örtüşüyor:

    LABORATUVAR HATASI EKİM KARARINI NE KADAR BOZUYOR,
    VE HANGİ ÖLÇÜMDE HASSASİYET GERÇEKTEN ÖNEMLİ?

Cevabı tarlada ölçemezsin, çünkü gerçeği bilmiyorsun. Sentetikte
ölçebilirsin. Sentetik veri burada bir eksiklik değil, yöntemin kendisidir.

NE KANITLAMAZ (rapora yazılmalı)
  - Muş topraklarının gerçek dağılımını kanıtlamaz. Profiller altı ilçenin
    TAHMİNİ değerleri etrafında üretildi; ilçe verisi henüz ölçüm değil.
  - Uygunluk kuralının doğruluğunu kanıtlamaz. Kural literatürden kurulmuş
    bir uzman sistemidir; veri seti onu veri saymaz, SINANACAK varsayım sayar.
  - Yüksek bir model başarısı "ekim kararı güvenilir" demek değildir;
    yalnızca "kural, ölçüm hatasına rağmen tutarlı uygulanabiliyor" demektir.

Kullanım:
    python src/toprak_veri_seti.py --numune 400
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

import mus_profil as mp
import mus_toprak as mt

KOK = Path(__file__).resolve().parent.parent

DRENAJ_SIRASI = ("zayıf", "orta", "iyi")

# ---------------------------------------------------------------------------
# MEKÂNSAL DEĞİŞKENLİK — aynı ilçe içinde tarladan tarlaya fark.
# Hepsi VARSAYIMDIR: Doğu Anadolu toprak etüt çalışmalarındaki tipik
# parsel içi değişim aralıklarından alındı, Muş için ölçülmedi.
# Gerçek ilçe verisi geldiğinde buradaki değerler ölçülen saçılımla
# değiştirilmelidir.
# ---------------------------------------------------------------------------
MEKANSAL = dict(
    ph=0.26, om=0.34, kirec=2.6, ec=0.14,
    doku=4.0,          # kil/kum/silt yüzdelerine eklenen sapma (toplam 100'e normalize)
    p2o5=1.3, k2o=19.0, derinlik=13.0,
)

# ---------------------------------------------------------------------------
# LABORATUVAR ÖLÇÜM HATASI — aynı numune iki kez ölçülse çıkacak fark.
# "oran" ile biten alanlar bağıl hatadır (değerin yüzdesi), diğerleri mutlak.
# Bunlar da VARSAYIMDIR; akredite laboratuvarların tekrarlanabilirlik
# beyanlarındaki tipik büyüklükler esas alındı.
# ---------------------------------------------------------------------------
LAB_HATASI = dict(
    ph=0.15,           # mutlak, pH birimi
    om_oran=0.12,      # bağıl — Walkley-Black yönteminin tekrarlanabilirliği
    kirec=1.5,         # mutlak, % CaCO3
    ec_oran=0.08,      # bağıl
    doku=3.0,          # mutlak, hidrometre yönteminde fraksiyon başına
    p2o5_oran=0.18,    # bağıl — ekstraksiyona en duyarlı ölçüm
    k2o_oran=0.12,     # bağıl
    derinlik=8.0,      # mutlak cm — burgu ile tahmin, kesin değil
    erozyon_yanlis=0.20,   # bir sınıf şaşma olasılığı (gözleme dayalı)
    drenaj_yanlis=0.15,    # bir sınıf şaşma olasılığı (gözleme dayalı)
)

SAYISAL = ["ph", "om", "kirec", "ec", "kil", "kum", "silt", "p2o5", "k2o", "derinlik"]
KATEGORIK = ["drenaj", "erozyon"]
OZNITELIKLER = [f"olculen_{a}" for a in SAYISAL + KATEGORIK] + ["urun"]
# Modele GİRMEYECEK sütunlar: numunenin kimliği ve gerçek değerleri.
# Gerçek değerler veri setinde duruyor çünkü "ölçüm ne kadar saptı" sorusu
# ancak onlarla cevaplanır — ama öznitelik olarak kullanılırlarsa hedef
# sızar ve bütün sonuçlar anlamsızlaşır.
KIMLIK = (["numune", "ilce", "sorunlu_alan"]
          + [f"gercek_{a}" for a in SAYISAL + KATEGORIK])
HEDEFLER = ["uygunluk_puani", "uygunluk_sinifi", "kisitlayici", "tavanlandi"]


def _dokuyu_duzelt(kil: float, kum: float, silt: float) -> tuple[float, float, float]:
    """Üç fraksiyonu pozitif tutup toplamı 100'e normalize eder."""
    k, u, s = max(kil, 1.0), max(kum, 1.0), max(silt, 1.0)
    t = k + u + s
    return k / t * 100, u / t * 100, s / t * 100


def numune_uret(rng: np.random.Generator, ilce: str,
                sorunlu: bool = False) -> dict[str, Any]:
    """Bir ilçenin profili etrafında gerçekçi bir tarla numunesi üretir.

    sorunlu=True ise numune, ilçenin ortalamasında görünmeyen ama sahada
    bulunan problemli alanlardan alınmış gibi kaydırılır: taban suyu yüksek
    tuzlanmış nokta, anakayaya yakın sığ toprak, drenajı bozuk çukur.

    NEDEN BİLEREK ÖRNEKLİYORUZ
    Altı ilçenin profil ortalamaları makul topraklardır; yalnızca onların
    etrafında üretince veri setinde "uygun değil" sınıfı hiç çıkmıyor. Oysa
    bir karar destek sisteminde en pahalı hata odur: uygun olmayan bir yere
    "ek" demek. Modelin o sınırı hiç görmeden öğrenmesi beklenemez.

    BEDELİ: veri setindeki sınıf oranları Muş'un gerçek arazi oranlarını
    YANSITMAZ. Sorunlu alanlar bilerek fazla örneklenmiştir. Bu veri setinden
    "Muş'un %x'i uygun değil" gibi bir sonuç çıkarılamaz.
    """
    t = dict(mt.ilce_toprak(ilce))
    if sorunlu:
        secim = int(rng.integers(0, 3))
        if secim == 0:                                  # tuzlanmış taban suyu alanı
            t["ec"] = float(t["ec"] + rng.uniform(1.6, 4.5))
            t["drenaj"] = "zayıf"
        elif secim == 1:                                # anakayaya yakın sığ toprak
            t["derinlik"] = float(rng.uniform(22, 45))
            t["erozyon"] = int(np.clip(t["erozyon"] + 1, 1, 5))
        else:                                           # drenajı bozuk ağır çukur
            t["drenaj"] = "zayıf"
            t["kil"] = float(min(t["kil"] + rng.uniform(8, 18), 70))
            t["om"] = float(max(0.4, t["om"] - rng.uniform(0.3, 0.9)))
    kil, kum, silt = _dokuyu_duzelt(
        t["kil"] + rng.normal(0, MEKANSAL["doku"]),
        t["kum"] + rng.normal(0, MEKANSAL["doku"]),
        t["silt"] + rng.normal(0, MEKANSAL["doku"]))

    drenaj = t["drenaj"]
    if rng.random() < 0.18:                      # komşu parsel farklı drene olabilir
        i = DRENAJ_SIRASI.index(drenaj) + int(rng.choice([-1, 1]))
        drenaj = DRENAJ_SIRASI[int(np.clip(i, 0, 2))]

    return dict(
        ph=float(np.clip(t["ph"] + rng.normal(0, MEKANSAL["ph"]), 4.5, 9.5)),
        om=float(max(0.2, t["om"] + rng.normal(0, MEKANSAL["om"]))),
        kirec=float(max(0.0, t["kirec"] + rng.normal(0, MEKANSAL["kirec"]))),
        ec=float(max(0.05, t["ec"] + rng.normal(0, MEKANSAL["ec"]))),
        kil=kil, kum=kum, silt=silt,
        p2o5=float(max(0.3, t["p2o5"] + rng.normal(0, MEKANSAL["p2o5"]))),
        k2o=float(max(20.0, t["k2o"] + rng.normal(0, MEKANSAL["k2o"]))),
        drenaj=drenaj,
        erozyon=int(np.clip(t["erozyon"] + rng.integers(-1, 2), 1, 5)),
        derinlik=float(np.clip(t["derinlik"] + rng.normal(0, MEKANSAL["derinlik"]),
                               20.0, 180.0)),
    )


def olc(rng: np.random.Generator, gercek: dict[str, Any]) -> dict[str, Any]:
    """Gerçek numuneden, laboratuvarın RAPOR EDECEĞİ değerleri üretir."""
    h = LAB_HATASI
    kil, kum, silt = _dokuyu_duzelt(
        gercek["kil"] + rng.normal(0, h["doku"]),
        gercek["kum"] + rng.normal(0, h["doku"]),
        gercek["silt"] + rng.normal(0, h["doku"]))

    drenaj = gercek["drenaj"]
    if rng.random() < h["drenaj_yanlis"]:
        i = DRENAJ_SIRASI.index(drenaj) + int(rng.choice([-1, 1]))
        drenaj = DRENAJ_SIRASI[int(np.clip(i, 0, 2))]

    erozyon = gercek["erozyon"]
    if rng.random() < h["erozyon_yanlis"]:
        erozyon = int(np.clip(erozyon + int(rng.choice([-1, 1])), 1, 5))

    return dict(
        ph=float(np.clip(gercek["ph"] + rng.normal(0, h["ph"]), 4.0, 10.0)),
        om=float(max(0.1, gercek["om"] * (1 + rng.normal(0, h["om_oran"])))),
        kirec=float(max(0.0, gercek["kirec"] + rng.normal(0, h["kirec"]))),
        ec=float(max(0.02, gercek["ec"] * (1 + rng.normal(0, h["ec_oran"])))),
        kil=kil, kum=kum, silt=silt,
        p2o5=float(max(0.1, gercek["p2o5"] * (1 + rng.normal(0, h["p2o5_oran"])))),
        k2o=float(max(10.0, gercek["k2o"] * (1 + rng.normal(0, h["k2o_oran"])))),
        drenaj=drenaj, erozyon=erozyon,
        derinlik=float(np.clip(gercek["derinlik"] + rng.normal(0, h["derinlik"]),
                               15.0, 200.0)),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Toprak uygunluk veri seti üretir")
    ap.add_argument("--numune", type=int, default=400, help="toprak numunesi sayısı")
    ap.add_argument("--cikti", default="data/madencilik")
    ap.add_argument("--tohum", type=int, default=20261018)
    ap.add_argument("--sorunlu-oran", type=float, default=0.25,
                    help="bilerek problemli alandan alınan numune oranı")
    ap.add_argument("--hata-carpani", type=float, default=1.0,
                    help="laboratuvar hatasını bu katsayıyla ölçekler (deney için)")
    a = ap.parse_args()

    if a.hata_carpani != 1.0:
        # Deney modu: hatanın büyüklüğü değişince kararın ne kadar bozulduğunu
        # ölçmek için. Oransal ve mutlak alanların hepsi aynı katsayıyla ölçeklenir.
        for anahtar in list(LAB_HATASI):
            LAB_HATASI[anahtar] = LAB_HATASI[anahtar] * a.hata_carpani
    rng = np.random.default_rng(a.tohum)
    hedef = KOK / a.cikti
    hedef.mkdir(parents=True, exist_ok=True)

    satirlar: list[dict[str, Any]] = []
    for i in range(a.numune):
        ilce = str(rng.choice(list(mp.ILCE)))
        sorunlu = bool(rng.random() < a.sorunlu_oran)
        gercek = numune_uret(rng, ilce, sorunlu)
        olculen = olc(rng, gercek)
        for urun in mp.URUN:
            sonuc = mt.topraktan_uygunluk(gercek, urun)   # etiket GERÇEKTEN gelir
            satir: dict[str, Any] = dict(numune=f"n{i:04d}", ilce=ilce,
                                         sorunlu_alan=int(sorunlu), urun=urun)
            for alan in SAYISAL:
                satir[f"gercek_{alan}"] = round(float(gercek[alan]), 3)
                satir[f"olculen_{alan}"] = round(float(olculen[alan]), 3)
            for alan in KATEGORIK:
                satir[f"gercek_{alan}"] = gercek[alan]
                satir[f"olculen_{alan}"] = olculen[alan]
            satir.update(
                uygunluk_puani=sonuc["puan"],
                uygunluk_sinifi=sonuc["sinif"],
                kisitlayici=sonuc["kisitlayici"],
                tavanlandi=int(sonuc["tavanlandi"]),
            )
            satirlar.append(satir)
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{a.numune} numune · {len(satirlar)} satır")

    basliklar = KIMLIK + OZNITELIKLER + HEDEFLER
    # Sözlük anahtarlarının sırası başlıkla birebir aynı olmalı
    duzenli = [{k: s[k] for k in basliklar} for s in satirlar]

    csv_yol = hedef / "toprak.csv"
    with csv_yol.open("w", encoding="utf-8", newline="") as f:
        y = csv.DictWriter(f, fieldnames=basliklar)
        y.writeheader()
        y.writerows(duzenli)

    # Ölçüm hatasının kararı kaç satırda değiştirdiğini ölç: aynı kuralı bir de
    # ÖLÇÜLEN değerlerle çalıştırıp gerçekle karşılaştırıyoruz. Veri setinin
    # var oluş sebebi bu sayı.
    bozulan_sinif = bozulan_kisit = 0
    for ham in satirlar:
        olculen_toprak = {alan: ham[f"olculen_{alan}"] for alan in SAYISAL + KATEGORIK}
        o = mt.topraktan_uygunluk(olculen_toprak, ham["urun"])
        if o["sinif"] != ham["uygunluk_sinifi"]:
            bozulan_sinif += 1
        if o["kisitlayici"] != ham["kisitlayici"]:
            bozulan_kisit += 1

    sinif_dagilim: dict[str, int] = {}
    kisit_dagilim: dict[str, int] = {}
    for s in duzenli:
        sinif_dagilim[s["uygunluk_sinifi"]] = sinif_dagilim.get(s["uygunluk_sinifi"], 0) + 1
        kisit_dagilim[s["kisitlayici"]] = kisit_dagilim.get(s["kisitlayici"], 0) + 1

    kunye = {
        "satir_sayisi": len(duzenli),
        "numune_sayisi": a.numune,
        "urun_sayisi": len(mp.URUN),
        "oznitelikler": OZNITELIKLER,
        "kimlik_sutunlari": KIMLIK,
        "hedefler": HEDEFLER,
        "sinif_dagilimi": sinif_dagilim,
        "kisitlayici_dagilimi": kisit_dagilim,
        "olcum_hatasi_sinifi_bozdu": bozulan_sinif,
        "olcum_hatasi_sinifi_bozdu_oran": round(bozulan_sinif / len(duzenli), 4),
        "olcum_hatasi_kisiti_bozdu": bozulan_kisit,
        "olcum_hatasi_kisiti_bozdu_oran": round(bozulan_kisit / len(duzenli), 4),
        "mekansal_degiskenlik": MEKANSAL,
        "laboratuvar_hatasi": LAB_HATASI,
        "tohum": a.tohum,
        "hata_carpani": a.hata_carpani,
        "sorunlu_alan_orani": a.sorunlu_oran,
        "not": ("gercek_* sütunları ÖZNİTELİK DEĞİLDİR; hedef onlardan "
                "hesaplandığı için modele verilirse sonuç anlamsız olur. "
                "Veri setinde durmalarının sebebi, ölçümün ne kadar saptığını "
                "incelenebilir kılmaktır."),
    }
    (hedef / "toprak_kunye.json").write_text(
        json.dumps(kunye, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{csv_yol} yazıldı")
    print(f"  satır              : {len(duzenli)} ({a.numune} numune × {len(mp.URUN)} ürün)")
    print(f"  uygunluk sınıfları : {sinif_dagilim}")
    print(f"  kısıtlayıcı faktör : {len(kisit_dagilim)} farklı")
    print("\n  ÖLÇÜM HATASININ ETKİSİ (aynı kural, ölçülen değerlerle):")
    print(f"    uygunluk sınıfı değişen : {bozulan_sinif} satır "
          f"({bozulan_sinif / len(duzenli):.1%})")
    print(f"    kısıtlayıcı değişen     : {bozulan_kisit} satır "
          f"({bozulan_kisit / len(duzenli):.1%})")


if __name__ == "__main__":
    main()
