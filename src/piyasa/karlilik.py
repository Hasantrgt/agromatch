"""
AGROMATCH - Karlılık simülasyonu
=================================
Dekar başına net geliri hesaplar ve BELİRSİZLİĞİYLE BİRLİKTE verir.

    net = verim × fiyat − maliyet + destek        (TL/dekar)

Tek bir sayı vermiyoruz. Fiyat ve verim ikisi de oynak; tek sayı vermek
"buğday ektir" demekle aynı kapıya çıkar ve o cümleyi kurmak için
elimizde veri yok. Bunun yerine Monte Carlo ile dağılım üretiliyor ve
panelde asıl şu soru cevaplanıyor: **bu belirsizlikle ürünleri
sıralayabiliyor muyuz, sıralayamıyor muyuz?**

Çoğu zaman cevap "sıralayamıyoruz" oluyor ve bu bir başarısızlık değil,
bulgudur: ölçüm gerekiyor demektir.

NEDEN "CANLI" DEĞİL
-------------------
Türkiye'de bu ürünler için ücretsiz canlı fiyat servisi yok. Buğday ve
arpada TMO hasat döneminde alım fiyatı açıklıyor; şeker pancarında
fabrika sözleşme fiyatı veriyor; destekler Resmî Gazete'de yayımlanıyor;
üretim maliyetlerini Ziraat Odaları hesaplıyor. Hiçbiri API değil.

Bu yüzden fiyatlar TEK BİR DOSYADAN okunuyor: ``data/piyasa.csv``.
Dosyanın her satırı kendi tarihini ve kaynağını taşıyor; panel verinin
kaç gün eski olduğunu büyük harflerle yazıyor. "Canlı" değil,
"güncellenebilir ve ne kadar eski olduğu görünen".

YEM BİTKİLERİ NEDEN HESAPLANMIYOR
---------------------------------
Yonca, korunga, fiğ ve silajlık mısır Muş'ta satılmıyor; hayvana
veriliyor. Bunların karlılığı satış fiyatıyla değil İKAME DEĞERİYLE
hesaplanır: o yemi satın alsaydınız ne öderdiniz. O veri elimizde yok,
bu yüzden hesaplanmıyor ve panelde sebebi yazıyor. Uydurma bir fiyat
koymak, bu ürünleri kârsız göstererek yanlış karar ürettirirdi.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

import numpy as np

import mus_profil as mp

KOK = Path(__file__).resolve().parent.parent.parent
VERI = KOK / "data" / "piyasa.csv"
CIKTI = KOK / "outputs"

# Monte Carlo çekiliş sayısı ve tohum (yeniden üretilebilirlik için sabit)
CEKILIS = 20_000
TOHUM = 20261029

# Belirsizlik payları. Fiyat payı yüksek çünkü fiyat sezon içinde
# ikiye katlanabiliyor; verim payı iklim ve bakım kaynaklı.
# İkisi de VARSAYIM; ölçümle daraltılacak alanlar bunlar.
FIYAT_OYNAKLIK = 0.30      # ±%30
VERIM_OYNAKLIK = 0.20      # ±%20
MALIYET_OYNAKLIK = 0.15    # ±%15

# Veri bu kadar günden eskiyse panel uyarı verir
BAYATLAMA_GUN = 90


def _sayi(s: str) -> float | None:
    s = (s or "").strip()
    if not s:
        return None
    return float(s.replace(",", "."))


def oku(yol: Path = VERI) -> list[dict[str, Any]]:
    metin = yol.read_text(encoding="utf-8-sig")
    ayrac = ";" if metin.splitlines()[0].count(";") else ","
    satir = []
    for s in csv.DictReader(metin.splitlines(), delimiter=ayrac):
        satir.append({
            "urun": s["urun"].strip(),
            "fiyat": _sayi(s["fiyat_tl_ton"]),
            "maliyet": _sayi(s["maliyet_tl_dekar"]),
            "destek": _sayi(s["destek_tl_dekar"]),
            "satiliyor": s["satiliyor"].strip().lower() == "evet",
            "tur": s["tur"].strip(),
            "kaynak": s["kaynak"].strip(),
            "tarih": s["tarih"].strip() or None,
        })
    return satir


def yas(tarih: str | None, bugun: dt.date | None = None) -> int | None:
    if not tarih:
        return None
    bugun = bugun or dt.date.today()
    return (bugun - dt.date.fromisoformat(tarih)).days


def hesaplanabilir(k: dict[str, Any]) -> bool:
    """Bu ürün için net gelir hesaplanabilir mi."""
    return (k["satiliyor"] and k["fiyat"] is not None
            and k["maliyet"] is not None)


def dagilim(verim: float, k: dict[str, Any],
            rng: np.random.Generator) -> np.ndarray:
    """Dekar başına net gelir dağılımı (TL/dekar).

    Üç girdi de bağımsız normal dağılımdan çekiliyor. Bağımsızlık bir
    VARSAYIMDIR: gerçekte kötü hava hem verimi düşürüp hem fiyatı
    yükseltebilir, yani ters yönde ilişkili olabilirler. Bu ilişki
    ölçülmeden modele konmaz.
    """
    fiyat = rng.normal(k["fiyat"], k["fiyat"] * FIYAT_OYNAKLIK, CEKILIS)
    v = rng.normal(verim, verim * VERIM_OYNAKLIK, CEKILIS)
    maliyet = rng.normal(k["maliyet"], k["maliyet"] * MALIYET_OYNAKLIK, CEKILIS)
    return np.maximum(v, 0) * np.maximum(fiyat, 0) - maliyet + (k["destek"] or 0)


def urun_kaydi(ilce: str, urun: str, verim: float,
               k: dict[str, Any], rng: np.random.Generator) -> dict[str, Any]:
    temel = {
        "ilce": ilce, "urun": urun, "verim": verim,
        "satiliyor": k["satiliyor"], "tur": k["tur"],
        "kaynak": k["kaynak"], "tarih": k["tarih"], "yas_gun": yas(k["tarih"]),
    }
    if not hesaplanabilir(k):
        temel.update({
            "hesaplanabilir": False,
            "sebep": ("yem bitkisi — satılmıyor, ikame değeri gerekiyor"
                      if not k["satiliyor"] else "fiyat ya da maliyet verisi yok"),
        })
        return temel
    d = dagilim(verim, k, rng)
    alt, orta, ust = np.percentile(d, [5, 50, 95])
    temel.update({
        "hesaplanabilir": True,
        "fiyat": k["fiyat"], "maliyet": k["maliyet"], "destek": k["destek"],
        "net_orta": round(float(orta)),
        "net_alt": round(float(alt)), "net_ust": round(float(ust)),
        "zarar_olasiligi": round(float((d < 0).mean()), 3),
        "ortalama": round(float(d.mean())),
    })
    return temel


def siralanabilir_mi(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """İki ürünün güven aralıkları ayrışıyor mu.

    Ayrışmıyorsa "A, B'den kârlı" denemez. Panelin asıl söylediği şey bu.
    """
    return a["net_alt"] > b["net_ust"] or b["net_alt"] > a["net_ust"]


def uret() -> dict[str, Any]:
    piyasa = {k["urun"]: k for k in oku()}
    rng = np.random.default_rng(TOHUM)
    satirlar: list[dict[str, Any]] = []
    for ilce, desen in mp.DESEN.items():
        for urun, (_alan, verim) in desen.items():
            k = piyasa.get(urun)
            if k is None:
                continue
            satirlar.append(urun_kaydi(ilce, urun, verim, k, rng))

    hesapli = [s for s in satirlar if s["hesaplanabilir"]]
    # İlçe bazında sıralanabilirlik: en kârlı ikiliyi ayırabiliyor muyuz
    ayirt: list[dict[str, Any]] = []
    for ilce in mp.DESEN:
        ilcenin = sorted((s for s in hesapli if s["ilce"] == ilce),
                         key=lambda s: -s["net_orta"])
        if len(ilcenin) < 2:
            continue
        birinci, ikinci = ilcenin[0], ilcenin[1]
        ayirt.append({
            "ilce": ilce, "birinci": birinci["urun"], "ikinci": ikinci["urun"],
            "birinci_net": birinci["net_orta"], "ikinci_net": ikinci["net_orta"],
            "ayrisiyor": siralanabilir_mi(birinci, ikinci),
        })

    tarihler = [k["tarih"] for k in piyasa.values() if k["tarih"]]
    en_eski = min(tarihler) if tarihler else None
    return {
        "satirlar": satirlar,
        "ayirt_edilebilirlik": ayirt,
        "piyasa": list(piyasa.values()),
        "parametre": {
            "cekilis": CEKILIS,
            "fiyat_oynaklik": FIYAT_OYNAKLIK,
            "verim_oynaklik": VERIM_OYNAKLIK,
            "maliyet_oynaklik": MALIYET_OYNAKLIK,
        },
        "veri_yasi": {
            "en_eski_tarih": en_eski,
            "gun": yas(en_eski),
            "bayat": (yas(en_eski) or 0) > BAYATLAMA_GUN,
            "esik_gun": BAYATLAMA_GUN,
        },
        "ozet": {
            "toplam": len(satirlar),
            "hesaplanan": len(hesapli),
            "hesaplanamayan": len(satirlar) - len(hesapli),
            "dogrulanmis_fiyat": sum(1 for k in piyasa.values()
                                     if k["tur"] == "ölçüm"),
            "ayrisan_ilce": sum(1 for a in ayirt if a["ayrisiyor"]),
            "ilce_sayisi": len(ayirt),
        },
    }


def main() -> None:
    veri = uret()
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "karlilik.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    o, y = veri["ozet"], veri["veri_yasi"]
    print(f"{yol} yazıldı")
    print(f"  {o['hesaplanan']} satır hesaplandı, {o['hesaplanamayan']} "
          f"hesaplanamadı (fiyat yok ya da yem bitkisi)")
    print(f"  doğrulanmış fiyat: {o['dogrulanmis_fiyat']} / "
          f"{len(veri['piyasa'])} ürün")
    print(f"  veri yaşı: {y['gun']} gün"
          + ("  BAYAT" if y["bayat"] else ""))
    print(f"  ürün sıralaması {o['ayrisan_ilce']}/{o['ilce_sayisi']} ilçede "
          f"ayrışıyor")
    for a in veri["ayirt_edilebilirlik"]:
        isaret = "ayrışıyor" if a["ayrisiyor"] else "AYRIŞMIYOR — sıralanamaz"
        print(f"    {a['ilce']:11s} {a['birinci']} ({a['birinci_net']:>6}) vs "
              f"{a['ikinci']} ({a['ikinci_net']:>6})  {isaret}")


if __name__ == "__main__":
    main()
