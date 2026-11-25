"""
AGROMATCH - SoilGrids'ten Muş toprak verisi çekme
==================================================
BU BETİK SENİN BİLGİSAYARINDA ÇALIŞIR, projenin geri kalanı gibi
otomatik değil. Sebebi basit: Claude'un çalıştığı ortamın ağ erişimi
isric.org'a kapalı. Senin normal internetin kapalı değil.

NE YAPIYOR
----------
ISRIC SoilGrids (250 m çözünürlüklü, küresel, CC-BY 4.0) üzerinden Muş'un
altı ilçesi için toprak değerlerini çeker. Her ilçede TEK NOKTA değil, ilçe
merkezinin çevresine serpiştirilmiş bir nokta ızgarası sorgulanır: tek nokta
250 metrelik bir kareyi temsil eder, bir ilçeyi değil.

NEDEN GEREKLİ
-------------
Elimizdeki 2.622 laboratuvar kaydına ne biz ne de veriyi veren hoca tam
güveniyor. Bağımsız bir kaynakla karşılaştırmak, o veriyi savunulması
gereken bir yük olmaktan çıkarıp DOĞRULANMIŞ ya da DOĞRULANMAMIŞ hâle
getirir. İkisi de sonuçtur; belirsizlik sonuç değildir.

NE DOĞRULANAMAZ — baştan yazılı olsun
-------------------------------------
SoilGrids kireç (CaCO3) ve tuzluluk (EC) vermiyor. Bu ikisi karşılaştırmaya
giremez. Üstelik varsayımımızın en çok şaştığı alan kireçti (ortalama 6,8
puan). Yani bu doğrulama en zayıf noktamızı kapatmıyor; bunu gizlemek yerine
yazıyoruz.

Organik madde doğrudan yok: SoilGrids organik KARBON veriyor. Dönüşüm için
yaygın Van Bemmelen katsayısı kullanılıyor (OM ≈ SOC × 1,724) ve bu bir
VARSAYIMDIR, ölçüm değil — çıktıda öyle işaretleniyor.

KULLANIM
--------
    python src/toprak_dogrulama/soilgrids_cek.py

Kütüphane gerektirmez, yalnızca Python standart kütüphanesi. Yarıda
kesilirse aynı komutla devam eder: çekilmiş noktalar atlanır.

    --yaricap 0.10   ilçe merkezinden kaç derece uzağa kadar (varsayılan)
    --adim 5         ızgara kenarı (5 -> 25 nokta/ilçe)
    --bekle 1.5      istekler arası saniye (sunucuya kibar olmak için)

Çıktı: data/soilgrids/mus_noktalar.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI_KLASOR = KOK / "data" / "soilgrids"
CIKTI = CIKTI_KLASOR / "mus_noktalar.csv"

ADRES = "https://rest.isric.org/soilgrids/v2.0/properties/query"

# mus_profil.KOORDINAT ile aynı; burada tekrar yazılı çünkü bu betik
# projenin geri kalanından bağımsız çalışabilmeli (başka bir makinede,
# depo kurulmadan).
KOORDINAT = {
    "Merkez": (38.73, 41.49), "Bulanık": (39.09, 42.27),
    "Malazgirt": (39.14, 42.54), "Varto": (39.17, 41.45),
    "Hasköy": (38.69, 41.69), "Korkut": (38.73, 41.80),
}

# SoilGrids özellik adı -> bizim alan adımız
OZELLIK = {
    "phh2o": "ph",          # pH (H2O)
    "soc":   "soc",         # organik karbon
    "clay":  "kil",
    "sand":  "kum",
    "silt":  "silt",
    "cec":   "kdk",         # katyon değişim kapasitesi
    "bdod":  "hacim_agirligi",
    "nitrogen": "azot",
}

# Tarla toprağı örneği genelde 0-20 cm'den alınır; SoilGrids'in bu aralığı
# kapsayan üç kademesi kullanılır.
DERINLIK = ("0-5cm", "5-15cm", "15-30cm")

BASLIK = ["ilce", "enlem", "boylam", "derinlik", "ozellik", "deger",
          "birim", "d_factor", "ham_deger"]


def noktalar(enlem: float, boylam: float, yaricap: float,
             adim: int) -> list[tuple[float, float]]:
    """Merkez çevresinde adim x adim nokta ızgarası.

    Tek nokta sorgulamak yanıltıcı olurdu: SoilGrids 250 m çözünürlükte,
    ilçe ise onlarca kilometre. Izgara, ilçe çekirdeğinin dağılımını verir.
    """
    if adim < 2:
        return [(enlem, boylam)]
    basamak = (2 * yaricap) / (adim - 1)
    return [(round(enlem - yaricap + i * basamak, 5),
             round(boylam - yaricap + j * basamak, 5))
            for i in range(adim) for j in range(adim)]


def sorgula(enlem: float, boylam: float, deneme: int = 3) -> dict | None:
    """Tek nokta sorgusu. Başarısızsa artan bekleme ile tekrar dener."""
    sorgu = [f"lon={boylam}", f"lat={enlem}", "value=mean"]
    sorgu += [f"property={p}" for p in OZELLIK]
    sorgu += [f"depth={d}" for d in DERINLIK]
    url = f"{ADRES}?{'&'.join(sorgu)}"

    for n in range(deneme):
        try:
            istek = urllib.request.Request(
                url, headers={"User-Agent": "AGROMATCH/1.0 (ogrenci projesi)",
                              "Accept": "application/json"})
            with urllib.request.urlopen(istek, timeout=60) as c:
                return json.loads(c.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:           # çok hızlı gittik
                time.sleep(10 * (n + 1))
                continue
            print(f"    HTTP {e.code}: {e.reason}")
            if 400 <= e.code < 500:
                return None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"    bağlantı hatası: {e}")
        time.sleep(5 * (n + 1))
    return None


def ayikla(cevap: dict, ilce: str, enlem: float,
           boylam: float) -> list[list]:
    """SoilGrids cevabını düz satırlara çevirir.

    Değerler sunucuda tam sayı olarak saklanır ve gerçek değere bölmek
    için d_factor verilir (pH için 10, kil/kum/silt için 10, ...).
    Katsayıyı elle yazmak yerine cevabın kendi d_factor'ü kullanılıyor:
    ISRIC bir gün ölçeği değiştirirse bu kod yanlış sonuç üretmez.
    """
    satir: list[list] = []
    for katman in cevap.get("properties", {}).get("layers", []):
        ad = OZELLIK.get(katman.get("name"))
        if not ad:
            continue
        birim_bilgi = katman.get("unit_measure", {}) or {}
        d = birim_bilgi.get("d_factor") or 1
        birim = birim_bilgi.get("target_units") or birim_bilgi.get(
            "mapped_units") or ""
        for kademe in katman.get("depths", []):
            ham = (kademe.get("values") or {}).get("mean")
            if ham is None:
                continue
            satir.append([ilce, enlem, boylam, kademe.get("label"), ad,
                          round(ham / d, 4), birim, d, ham])
    return satir


def yazilmis() -> set[tuple[str, float, float]]:
    """Daha önce çekilmiş noktalar — betik yarıda kesilirse devam etsin."""
    if not CIKTI.exists():
        return set()
    with open(CIKTI, encoding="utf-8", newline="") as f:
        return {(s["ilce"], float(s["enlem"]), float(s["boylam"]))
                for s in csv.DictReader(f)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SoilGrids'ten Muş toprağı")
    ap.add_argument("--yaricap", type=float, default=0.10,
                    help="ilçe merkezinden derece cinsinden yarıçap")
    ap.add_argument("--adim", type=int, default=5,
                    help="ızgara kenarı; 5 -> ilçe başına 25 nokta")
    ap.add_argument("--bekle", type=float, default=1.5,
                    help="istekler arası saniye")
    a = ap.parse_args(argv)

    CIKTI_KLASOR.mkdir(parents=True, exist_ok=True)
    atla = yazilmis()
    if atla:
        print(f"{len(atla)} nokta zaten çekilmiş, atlanıyor.\n")

    yeni_dosya = not CIKTI.exists()
    toplam = sum(len(noktalar(e, b, a.yaricap, a.adim))
                 for e, b in KOORDINAT.values())
    sayac = basarisiz = 0

    with open(CIKTI, "a", encoding="utf-8", newline="") as f:
        yazici = csv.writer(f)
        if yeni_dosya:
            yazici.writerow(BASLIK)

        for ilce, (enlem, boylam) in KOORDINAT.items():
            izgara = noktalar(enlem, boylam, a.yaricap, a.adim)
            print(f"{ilce}: {len(izgara)} nokta")
            for e, b in izgara:
                sayac += 1
                if (ilce, e, b) in atla:
                    continue
                cevap = sorgula(e, b)
                if cevap is None:
                    basarisiz += 1
                    print(f"  [{sayac}/{toplam}] {e},{b} ALINAMADI")
                    continue
                satirlar = ayikla(cevap, ilce, e, b)
                if not satirlar:
                    basarisiz += 1
                    print(f"  [{sayac}/{toplam}] {e},{b} boş cevap")
                    continue
                yazici.writerows(satirlar)
                f.flush()
                print(f"  [{sayac}/{toplam}] {e},{b} tamam "
                      f"({len(satirlar)} değer)")
                time.sleep(a.bekle)

    print(f"\n{CIKTI} yazıldı")
    if basarisiz:
        print(f"UYARI: {basarisiz} nokta alınamadı. Aynı komutu tekrar "
              "çalıştırırsan yalnızca eksikler denenir.")
        if basarisiz == toplam:
            print("\nHİÇBİR NOKTA ALINAMADI. Muhtemel sebep: ISRIC'in REST\n"
                  "servisi geçici olarak kapalı olabiliyor. Birkaç saat\n"
                  "sonra tekrar dene; sorun sürerse söyle, veriyi başka\n"
                  "yoldan (WCS ya da hazır indirme) alırız.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
