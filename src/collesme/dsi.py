"""
AGROMATCH - Muş çölleşme duyarlılığı (DSI)
===========================================
Muş'un altı ilçesi için çölleşmeye duyarlılık endeksi hesaplar.

BU RESMÎ HARİTA DEĞİLDİR — önce bunu yazmak gerekiyor
------------------------------------------------------
Türkiye'nin resmî Çölleşme Hassasiyet Haritası Çölleşme ve Erozyonla
Mücadele Genel Müdürlüğü tarafından üretildi; 7 kriter ve 48 gösterge
kullanıyor, üç sınıfa ayırıyor (zayıf / orta / yüksek) ve e-Devlet'ten
sorgulanabiliyor. Ülke genelinde dağılım: %18 zayıf, %50,9 orta,
%22,5 yüksek. Tarım arazilerinde yüksek duyarlılık payı %26,25,
meralarda %34,56.

**Muş'un resmî sınıfı o haritadan okunmalıdır ve burada YOKTUR.**

Burada yapılan şey ayrı: yayımlanmış MEDALUS türevi DSI yöntemini
projenin kendi ölçtüğü veriye uygulamak. Değeri şurada: 2.622 gerçek
toprak analizinden hesaplanmış bir çölleşme endeksi Muş için daha önce
üretilmedi. Resmî haritanın yerini tutmaz, onu ilçe ölçeğinde
tamamlar — ve ikisi çelişirse bu, sorulacak iyi bir sorudur.

YÖNTEM
------
Kaynak: Desertification Assessment Using MEDALUS Model,
ISPRS Archives XLIII-B3-2020, s. 1257.

    SQI = (ST × SD × DR × EC × OM)^(1/5)      toprak kalitesi
    CQI = yağış sınıf ağırlığı                 iklim kalitesi
    VQI = (FR × EP × DD)^(1/3)                 bitki örtüsü kalitesi
    HQI = (LU × SE)^(1/2)                      insan etkisi
    DSI = (SQI × CQI × VQI × HQI)^(1/4)

Sınıflar: 1,00–1,22 düşük · 1,23–1,37 orta · 1,38–1,53 yüksek ·
1,54–2,00 çok yüksek.

KAYNAKTAN AYRILDIĞIMIZ İKİ YER — ikisi de bilerek
--------------------------------------------------
1. **Eğim (slope) çıkarıldı.** Yayında SQI'nin altı parametresi var ama
   üssü 1/5 yazılmış; yayının kendi içinde bir tutarsızlık. Bizde ilçe
   bazında eğim verisi olmadığı için eğimi hiç almadık ve kalan BEŞ
   parametrenin geometrik ortalamasını aldık — böylece üs 1/5 ile
   tutarlı hâle geldi. Eğim verisi gelirse altıya çıkar.
2. **Yağış erozivitesi çıkarıldı.** CQI yayında (RF × RE)^(1/2); bizde
   erozivite ölçümü yok, yalnızca yağış var. Tek parametre kaldığı için
   karekök alınmadı. Bu CQI'yi hafif İYİMSER yapar; panelde yazıyor.

Çıktı: outputs/collesme.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mus_profil as mp
import mus_toprak as mt

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

KAYNAK = ("Desertification Assessment Using MEDALUS Model, "
          "ISPRS Archives XLIII-B3-2020, s. 1257")

# --- DSI sınıf sınırları (yayından)
SINIFLAR = ((1.22, "düşük"), (1.37, "orta"), (1.53, "yüksek"),
            (99.0, "çok yüksek"))

# --- SQI parametre ağırlıkları (yayından, birebir)
# Laboratuvarın bünye sınıfı -> yayındaki doku sınıfı ağırlığı
BUNYE_AGIRLIK = {
    "Tınlı": 1.0,          # L — iyi
    "Killi-Tınlı": 1.0,    # CL — iyi
    "Killi": 1.6,          # C — zayıf
    "Ağır Killi": 1.6,     # C — zayıf
    "Kumlu": 2.0,          # S — çok zayıf
}
DRENAJ_AGIRLIK = {"iyi": 1.0, "orta": 1.2, "zayıf": 2.0}
EROZYON_AGIRLIK = {1: 1.0, 2: 1.2, 3: 1.5, 4: 1.7, 5: 2.0}


def derinlik_agirligi(cm: float) -> float:
    if cm > 75:
        return 1.0
    if cm >= 30:
        return 1.2
    if cm >= 15:
        return 1.6
    return 2.0


def ec_agirligi(ds_m: float) -> float:
    if ds_m < 4:
        return 1.0
    if ds_m < 8:
        return 1.2
    if ds_m < 16:
        return 1.4
    if ds_m < 32:
        return 1.6
    if ds_m < 64:
        return 1.8
    return 2.0


def om_agirligi(yuzde: float) -> float:
    if yuzde > 3:
        return 1.0
    if yuzde >= 2:
        return 1.2
    if yuzde >= 1:
        return 1.5
    if yuzde >= 0.5:
        return 1.7
    return 2.0


def yagis_agirligi(mm: float) -> float:
    if mm < 280:
        return 2.0
    if mm < 650:
        return 1.8
    if mm <= 1000:
        return 1.5
    return 1.0


# --- VQI: arazi örtüsüne göre (yayından)
# Muş'ta iki örtü var: yıllık tarım (tahıl ağırlıklı) ve mera.
ORTU = {
    "tarim":  {"yangin": 1.5, "erozyon_korumasi": 1.6, "kuraklik": 1.6},
    "mera":   {"yangin": 1.5, "erozyon_korumasi": 1.3, "kuraklik": 1.3},
}
# HQI arazi kullanımı: tek sezonluk kuru tarım yayında 1,8
ARAZI_KULLANIM = 1.8


def _gm(degerler: list[float]) -> float:
    carpim = 1.0
    for d in degerler:
        carpim *= d
    return carpim ** (1 / len(degerler))


def sinif(dsi: float) -> str:
    for ust, ad in SINIFLAR:
        if dsi <= ust:
            return ad
    return "çok yüksek"


def bunye_agirligi(ilce: str) -> tuple[float, str]:
    """Ölçülen bünye dağılımından ağırlıklı doku puanı."""
    try:
        from toprak_olcum import analiz
        veri = analiz.uret()
        dagilim = veri["ilce"].get(ilce, {}).get("bunye", []) if veri.get("var") else []
    except Exception:
        dagilim = []
    gecerli = [b for b in dagilim if b["sinif"] in BUNYE_AGIRLIK]
    if gecerli:
        toplam = sum(b["n"] for b in gecerli)
        return (sum(BUNYE_AGIRLIK[b["sinif"]] * b["n"] for b in gecerli) / toplam,
                "ölçüm")
    # Ölçüm yoksa kil oranından kabaca
    kil = mt.ilce_toprak(ilce)["kil"]
    return (1.6 if kil >= 40 else 1.0), "varsayım"


def ilce_dsi(ilce: str) -> dict[str, Any]:
    t = mt.ilce_toprak(ilce)
    kaynak = t.get("_kaynak", {})

    doku, doku_kaynak = bunye_agirligi(ilce)
    sqi_parca = {
        "doku": {"deger": round(doku, 2), "kaynak": doku_kaynak},
        "derinlik": {"deger": derinlik_agirligi(float(t["derinlik"])),
                     "kaynak": kaynak.get("derinlik", "varsayım")},
        "drenaj": {"deger": DRENAJ_AGIRLIK.get(str(t["drenaj"]), 1.2),
                   "kaynak": kaynak.get("drenaj", "varsayım")},
        "tuzluluk": {"deger": ec_agirligi(float(t["ec"])),
                     "kaynak": kaynak.get("ec", "varsayım")},
        "organik_madde": {"deger": om_agirligi(float(t["om"])),
                          "kaynak": kaynak.get("om", "varsayım")},
    }
    sqi = _gm([p["deger"] for p in sqi_parca.values()])

    yagis = mp.IKLIM[ilce][1]
    cqi = yagis_agirligi(float(yagis))

    # Arazi örtüsü payı: ekili alan ve mera
    ekili = sum(a for a, _v in mp.DESEN[ilce].values())
    mera = float(mp.ILCE[ilce][4]) if isinstance(mp.ILCE, dict) else 0.0
    toplam = ekili + mera
    pay_tarim = ekili / toplam if toplam else 1.0
    pay_mera = 1.0 - pay_tarim
    vqi_parca = {}
    for alan in ("yangin", "erozyon_korumasi", "kuraklik"):
        vqi_parca[alan] = round(
            ORTU["tarim"][alan] * pay_tarim + ORTU["mera"][alan] * pay_mera, 3)
    vqi = _gm(list(vqi_parca.values()))

    erozyon = EROZYON_AGIRLIK.get(int(t["erozyon"]), 1.5)
    hqi = _gm([ARAZI_KULLANIM, erozyon])

    dsi = _gm([sqi, cqi, vqi, hqi])
    return {
        "ilce": ilce,
        "sqi": round(sqi, 3), "cqi": round(cqi, 3),
        "vqi": round(vqi, 3), "hqi": round(hqi, 3),
        "dsi": round(dsi, 3), "sinif": sinif(dsi),
        "sqi_parca": sqi_parca,
        "vqi_parca": vqi_parca,
        "hqi_parca": {"arazi_kullanim": ARAZI_KULLANIM,
                      "su_erozyonu": erozyon},
        "yagis_mm": yagis,
        "tarim_payi": round(pay_tarim, 3),
        "mera_payi": round(pay_mera, 3),
        "olculen_girdi": sum(1 for p in sqi_parca.values()
                             if p["kaynak"] in ("ölçüm", "türetildi")),
        "girdi_sayisi": len(sqi_parca),
    }


# ------------------------------------------------------------- kaldıraçlar
# Bir endeksin değeri, nereye müdahale edileceğini söylemesindedir.
# Burada her kaldıraç için "o parametre bir sınıf iyileşirse DSI ne olur"
# hesaplanıyor. Senaryo, tahmin değil: "şunu yaparsanız endeks şuraya
# iner" demektir.
KALDIRACLAR = {
    "organik_madde": {
        "ad": "Organik maddeyi bir sınıf yükseltmek",
        "nasil": "Anız yakmayı bırakmak, ahır gübresi, yeşil gübre, "
                 "münavebeye baklagil sokmak",
        "yeni": 1.2,     # %2-3 sınıfı
        "sure": "3–5 yıl",
    },
    "su_erozyonu": {
        "ad": "Su erozyonunu bir sınıf düşürmek",
        "nasil": "Eğime dik sürüm, teraslama, anız örtüsü bırakmak, "
                 "mera otlatma planı",
        "yeni": None,    # mevcut ağırlıktan bir basamak iyi
        "sure": "2–4 yıl",
    },
    "drenaj": {
        "ad": "Drenajı iyileştirmek",
        "nasil": "Tahliye kanalı, drenaj borusu, taban suyu kontrolü",
        "yeni": 1.0,
        "sure": "1–2 yıl",
    },
}

_EROZYON_BASAMAK = [1.0, 1.2, 1.5, 1.7, 2.0]


def senaryo(ilce: str) -> list[dict[str, Any]]:
    """Her kaldıraç için DSI'nin nereye ineceği."""
    temel = ilce_dsi(ilce)
    cikti = []
    for anahtar, k in KALDIRACLAR.items():
        sqi_parca = {a: p["deger"] for a, p in temel["sqi_parca"].items()}
        erozyon = temel["hqi_parca"]["su_erozyonu"]

        if anahtar == "organik_madde":
            if sqi_parca["organik_madde"] <= k["yeni"]:
                continue          # zaten iyi, kaldıraç yok
            sqi_parca["organik_madde"] = k["yeni"]
        elif anahtar == "drenaj":
            if sqi_parca["drenaj"] <= k["yeni"]:
                continue
            sqi_parca["drenaj"] = k["yeni"]
        elif anahtar == "su_erozyonu":
            i = _EROZYON_BASAMAK.index(erozyon) if erozyon in _EROZYON_BASAMAK else None
            if not i:
                continue          # zaten en iyi basamakta
            erozyon = _EROZYON_BASAMAK[i - 1]

        yeni_sqi = _gm(list(sqi_parca.values()))
        yeni_hqi = _gm([ARAZI_KULLANIM, erozyon])
        yeni_dsi = _gm([yeni_sqi, temel["cqi"], temel["vqi"], yeni_hqi])
        cikti.append({
            "kaldirac": anahtar, "ad": k["ad"], "nasil": k["nasil"],
            "sure": k["sure"],
            "dsi_once": temel["dsi"], "dsi_sonra": round(yeni_dsi, 3),
            "kazanc": round(temel["dsi"] - yeni_dsi, 3),
            "sinif_once": temel["sinif"], "sinif_sonra": sinif(yeni_dsi),
            "sinif_degisti": temel["sinif"] != sinif(yeni_dsi),
        })
    return sorted(cikti, key=lambda s: -s["kazanc"])



def uret() -> dict[str, Any]:
    satirlar = [ilce_dsi(i) for i in mp.ILCE]
    sayim: dict[str, int] = {}
    for s in satirlar:
        sayim[s["sinif"]] = sayim.get(s["sinif"], 0) + 1
    en_yuksek = max(satirlar, key=lambda s: s["dsi"])
    en_dusuk = min(satirlar, key=lambda s: s["dsi"])
    return {
        "satirlar": satirlar,
        "siniflar": [{"ad": a, "ust": u} for u, a in SINIFLAR],
        "kaynak": KAYNAK,
        "resmi": {
            "ad": "Türkiye Çölleşme Hassasiyet Haritası",
            "kurum": "Çölleşme ve Erozyonla Mücadele Genel Müdürlüğü",
            "yontem": "7 kriter, 48 gösterge, CBS tabanlı",
            "siniflar": ["zayıf", "orta", "yüksek"],
            "ulke_dagilimi": {"zayıf": 18.0, "orta": 50.9, "yüksek": 22.5},
            "tarim_arazisi": {"yüksek": 26.25, "orta": 64.77, "düşük": 8.98},
            "mera": {"yüksek": 34.56, "orta": 52.45, "düşük": 12.99},
            "not_": "Muş'un resmî sınıfı bu haritadan okunmalıdır; "
                    "burada hesaplanan DSI onun yerini tutmaz.",
        },
        "ozet": {
            "sinif_dagilimi": sayim,
            "en_duyarli": en_yuksek["ilce"],
            "en_duyarli_dsi": en_yuksek["dsi"],
            "en_az_duyarli": en_dusuk["ilce"],
            "en_az_duyarli_dsi": en_dusuk["dsi"],
            "ortalama_dsi": round(sum(s["dsi"] for s in satirlar) / len(satirlar), 3),
            "olculen_girdi_payi": round(
                sum(s["olculen_girdi"] for s in satirlar)
                / sum(s["girdi_sayisi"] for s in satirlar), 3),
        },
        "senaryo": {i: senaryo(i) for i in mp.ILCE},
        "ayrim": [
            "Eğim parametresi çıkarıldı: ilçe bazında eğim verisi yok. "
            "Yayındaki 1/5 üssü kalan beş parametreyle tutarlı hâle geldi.",
            "Yağış erozivitesi çıkarıldı: ölçümü yok. CQI tek parametreye "
            "indiği için hafif İYİMSER.",
            "Bitki örtüsü kalitesi arazi örtüsü payından türetildi; "
            "uydu görüntüsünden bitki örtüsü yoğunluğu ölçülmedi.",
        ],
    }


def main() -> None:
    veri = uret()
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "collesme.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"{yol} yazıldı\n")
    print(f"{'ilçe':11s} {'SQI':>6} {'CQI':>6} {'VQI':>6} {'HQI':>6} "
          f"{'DSI':>6}  sınıf       ölçülen girdi")
    for s in veri["satirlar"]:
        print(f"{s['ilce']:11s} {s['sqi']:>6.3f} {s['cqi']:>6.3f} "
              f"{s['vqi']:>6.3f} {s['hqi']:>6.3f} {s['dsi']:>6.3f}  "
              f"{s['sinif']:11s} {s['olculen_girdi']}/{s['girdi_sayisi']}")
    o = veri["ozet"]
    print(f"\nortalama DSI {o['ortalama_dsi']} · "
          f"en duyarlı {o['en_duyarli']} ({o['en_duyarli_dsi']}) · "
          f"en az {o['en_az_duyarli']} ({o['en_az_duyarli_dsi']})")
    print(f"sınıf dağılımı: {o['sinif_dagilimi']}")
    print(f"SQI girdilerinin %{o['olculen_girdi_payi'] * 100:.0f}'i ölçüme dayanıyor")


if __name__ == "__main__":
    main()
