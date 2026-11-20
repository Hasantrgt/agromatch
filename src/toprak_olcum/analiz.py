"""
AGROMATCH - Muş toprak analizi ölçümleri (2011-2015)
=====================================================
Projenin ilk GERÇEK ölçüm katmanı. Bugüne kadar ilçe toprak değerleri
``mus_profil.TOPRAK`` içinde VARSAYIM olarak duruyordu; burası onları
Muş İl Tarım ve Orman Müdürlüğü laboratuvar kayıtlarıyla karşılaştırır.

KAYNAK
------
Beş yıllık laboratuvar defteri, 2.622 örnek. Dosyalar danışman hoca
aracılığıyla alındı ve ``data/toprak_analizi/`` altında durur. **Ham
kayıtlar depoya gönderilmez** (.gitignore): başkasının laboratuvar
verisi, yayımlama izni sorulmadan kamuya açık bir depoya konmaz. Depoya
giren şey yalnızca buradan çıkan ÖZET istatistiklerdir.

VERİNİN SINIRLARI — panelde de yazar
------------------------------------
1. **İlçe bilgisi yalnızca 2011 ve 2012'de var.** 2013-2015'teki 1.181
   örneğin "Örneğin Alındığı Yer" sütunu tamamen boş. O örnekler il
   geneli istatistiğe girer, ilçe karşılaştırmasına giremez.
2. **Fosfor ve potasyum birimleri tutarsız.** 2011-2012'de P(ppm),
   2013-2015'te P2O5(ppm) var; ikisinin medyanı 0,12 ve 0,16 ki
   bitkiye yarayışlı fosfor için anlamsız derecede düşük. K2O sütunu
   "kg/da" etiketli ama medyanı 242 — bu değer ppm'e benziyor. Birim
   laboratuvara sorulmadan BU İKİ SÜTUN KULLANILMIYOR.
3. **Örnekler tarlaya göre seçilmiş, rastgele değil.** Çiftçi analiz
   yaptırdığı için gelen örnekler sorunlu ya da yatırım yapılan
   tarlalardır. İlçe medyanı, o ilçenin ortalama toprağı değil,
   ANALİZ YAPTIRILAN tarlalarının medyanıdır.
4. Malazgirt ve Bulanık örnek sayısı düşük; o ilçelerde karşılaştırma
   gösterilir ama güvenilir sayılmaz.

Çıktı: outputs/toprak_olcum.json

    python src/toprak_olcum/analiz.py
    python src/toprak_olcum/analiz.py --klasor /baska/yol
"""

from __future__ import annotations

import argparse
import json
import re
import statistics as st
from collections import Counter
from pathlib import Path
from typing import Any

import mus_profil as mp

KOK = Path(__file__).resolve().parent.parent.parent
VARSAYILAN_KLASOR = KOK / "data" / "toprak_analizi"
CIKTI = KOK / "outputs"

# Güvenilir karşılaştırma için en az bu kadar örnek gerekir
GUVEN_ESIGI = 30

# Tarım toprağında fiziksel olarak mümkün aralıklar. Dışına düşen
# kayıtlar ÖLÇÜM DEĞİL YAZIM HATASI sayılır ve ayıklanır; kaç tanesinin
# ayıklandığı çıktıda yazar.
GECERLI = {
    "ph": (3.5, 10.0),
    "ec": (0.0, 20.0),
    "tuz": (0.0, 5.0),
    "kirec": (0.0, 60.0),
    "om": (0.0, 15.0),
}

# Excel başlığı -> iç alan adı. Fosfor ve potasyum bilerek yok (bkz. 2).
BASLIK = {
    "pH": "ph",
    "EC(dS/m)": "ec",
    "Toplam Tuz (%)": "tuz",
    "CaCO3": "kirec",
    "Organik Madde (%)": "om",
}

# mus_profil.TOPRAK sırası: ph, om, kirec, ec, kil, kum, silt,
#                           p2o5, k2o, drenaj, erozyon, derinlik
VARSAYIM_SIRA = {"ph": 0, "om": 1, "kirec": 2, "ec": 3}

# Yer adının son parçası bunlardan biriyse il Muş'tur
IL_ADI = {"Muş", "Mus", "MUŞ"}

# Laboratuvarın bünye sınıfları, kil oranına göre kabaca sıralı
BUNYE_SIRA = ("Kumlu", "Tınlı", "Killi-Tınlı", "Killi", "Ağır Killi")


def ilce_bul(yer: Any) -> str | None:
    """'Güneyik - Korkut' gibi bir yer adından Muş ilçesini çıkarır.

    DİKKAT — burada bir hata yapıldı ve düzeltildi. İlk sürüm, adın
    HERHANGİ bir parçasında Muş ilçesi arıyordu. Laboratuvar bölgeye
    hizmet verdiği için komşu illerden de örnek kabul ediyor ve
    "Merkez - Bingöl" kaydı Muş MERKEZ'e yazılıyordu. Eski kural 130
    kaydı yanlış yerleştirmişti:

        93  Muş dışı kayıt Muş'a girdi (89'u 'Merkez - Bingöl')
        34  gerçek Muş kaydı asıl ilçesinden alınıp Merkez'e yazıldı
            ('Merkez - Varto' 16, 'Merkez - Korkut' 9, 'Merkez - Hasköy' 6,
             'Merkez - Bulanık' 2, 'Merkez - Malazgirt' 1)

    Doğru kural: yer adının SON parçası ilçeyi belirler. Son parça bir
    Muş ilçesi ya da "Muş" değilse kayıt ELENİR; öncesindeki parçalara
    bakılmaz.

    YER SÜTUNUNUN SIRASI SABİT DEĞİL — bu bir varsayım değil, veride
    görülen bir durum. Baskın kalıp "köy - ilçe" ("Güneyik - Korkut"),
    ama üç kayıtta sıra ters: "Bulanık - Sarıpınar" (2) ve
    "Hasköy - Umurca" (1) ilçe-köy sırasında yazılmış. Köy kütüğü
    olmadan hangisinin köy hangisinin ilçe olduğu ayırt edilemez.

    Bu yüzden KATI kural seçildi ve bedeli yazıldı: 93 yabancı kayıt
    girmiyor, karşılığında 3 gerçek Muş kaydı düşüyor. İl Tarım'dan köy
    listesi gelirse o üç kayıt geri kazanılır. Düşenler sessizce
    kaybolmaz; kalite raporunda "belirsiz sıralama" başlığında sayılır.

    Yer sütunu dolu olan 1.440 kaydın dağılımı:
        1.223  Muş ilçesine bağlandı
          211  Muş dışı (Bingöl 133, Bitlis 67, Solhan 8, Güroymak 2,
                Osmaniye 1)
            3  ters sıralama — gerçek Muş, ayırt edilemediği için düştü
            3  yalnızca köy adı, ilçe eki yok
    """
    if not yer:
        return None
    parcalar = [p.strip() for p in re.split(r"[-/,]", str(yer)) if p.strip()]
    if not parcalar:
        return None
    son = parcalar[-1]

    # Son parça doğrudan bir Muş ilçesiyse iş bitti: "Güneyik - Korkut",
    # "Merkez - Varto".
    if son in mp.ILCE:
        return son

    # Son parça "Muş" ise il Muş'tur; ilçeyi bir önceki parça söyler.
    # "Merkez - Muş" -> Merkez. "Bağlar - Muş" -> köy adı, demek ki
    # il merkezi.
    if son in IL_ADI:
        if len(parcalar) >= 2 and parcalar[-2] in mp.ILCE:
            return parcalar[-2]
        return "Merkez"

    # Geriye kalan her şey Muş dışı ya da belirsiz: "Merkez - Bingöl",
    # "Güroymak - Bitlis", tek parçalı adlar.
    return None


def _sayi(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def oku(klasor: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Beş yılın defterini tek listeye çevirir, ayıklananları sayar.

    OKUNACAK DOSYA YOKSA openpyxl DE GEREKMEZ. Bu sıralama önemli:
    ham laboratuvar kayıtları depoda durmaz, dolayısıyla temiz bir
    klonda (ve GitHub Actions'ta) bu klasör boştur. Kütüphaneyi dosya
    var mı diye bakmadan istemek, ölçüm verisi olmayan her ortamda
    panelin tamamını çökertiyordu — nitekim çökertti: Pages'teki panel
    bu yüzden haftalarca eski sürümde kaldı.

    Ölçüm bir İYİLEŞTİRMEDİR, önkoşul değil. Kod da öyle davranmalı.
    """
    dosyalar = sorted(klasor.glob("*.xlsx")) if klasor.exists() else []
    if not dosyalar:
        return [], {}

    try:
        import openpyxl
    except ImportError as e:
        raise SystemExit(
            f"{len(dosyalar)} laboratuvar dosyası var ama openpyxl kurulu "
            "değil: pip install openpyxl") from e

    kayit: list[dict[str, Any]] = []
    ayiklanan: Counter[str] = Counter()
    for yol in dosyalar:
        eslesme = re.search(r"(20\d\d)", yol.name)
        if not eslesme:
            continue
        yil = int(eslesme.group(1))
        wb = openpyxl.load_workbook(yol, read_only=True, data_only=True)
        satirlar = list(wb.active.iter_rows(values_only=True))
        wb.close()
        if not satirlar:
            continue
        basliklar = [str(c).strip() if c else "" for c in satirlar[0]]
        indeks = {BASLIK[b]: i for i, b in enumerate(basliklar) if b in BASLIK}
        bunye_i = basliklar.index("Bünye") if "Bünye" in basliklar else None
        for r in satirlar[1:]:
            if not any(c not in (None, "") for c in r):
                continue
            k: dict[str, Any] = {
                "yil": yil,
                "ilce": ilce_bul(r[1] if len(r) > 1 else None),
                "bunye": (str(r[bunye_i]).strip()
                          if bunye_i is not None and len(r) > bunye_i
                          and r[bunye_i] else None),
                "ekilecek": (str(r[3]).strip() if len(r) > 3 and r[3] else None),
            }
            for ad, i in indeks.items():
                d = _sayi(r[i]) if i < len(r) else None
                if d is not None:
                    alt, ust = GECERLI[ad]
                    if not (alt <= d <= ust):
                        ayiklanan[ad] += 1
                        d = None
                k[ad] = d
            kayit.append(k)
    return kayit, dict(ayiklanan)


def _ozet(degerler: list[float]) -> dict[str, Any]:
    d = sorted(degerler)
    ceyrek = st.quantiles(d, n=4) if len(d) >= 4 else [d[0], st.median(d), d[-1]]
    return {
        "n": len(d),
        "medyan": round(st.median(d), 3),
        "ortalama": round(st.fmean(d), 3),
        "q1": round(ceyrek[0], 3),
        "q3": round(ceyrek[2], 3),
        "min": round(d[0], 3),
        "maks": round(d[-1], 3),
    }


def ilce_ozeti(kayit: list[dict[str, Any]]) -> dict[str, Any]:
    """İlçe × ölçüm özeti ve varsayımla karşılaştırma."""
    cikti: dict[str, Any] = {}
    for ilce in mp.ILCE:
        orneklem = [k for k in kayit if k["ilce"] == ilce]
        if not orneklem:
            continue
        alanlar: dict[str, Any] = {}
        for ad, sira in VARSAYIM_SIRA.items():
            d = [k[ad] for k in orneklem if k.get(ad) is not None]
            if not d:
                continue
            o = _ozet(d)
            varsayim = mp.TOPRAK[ilce][sira]
            o["varsayim"] = varsayim
            o["fark"] = round(o["medyan"] - varsayim, 3)
            o["oran"] = (round(o["medyan"] / varsayim, 2)
                         if varsayim else None)
            o["guvenilir"] = o["n"] >= GUVEN_ESIGI
            # Varsayım ölçülen dağılımın içinde mi kalıyor
            o["aralikta"] = o["q1"] <= varsayim <= o["q3"]
            alanlar[ad] = o
        bunyeler = [k["bunye"] for k in orneklem if k["bunye"]]
        cikti[ilce] = {
            "n_ornek": len(orneklem),
            "alanlar": alanlar,
            "bunye": [{"sinif": s, "n": n,
                       "pay": round(n / len(bunyeler), 3)}
                      for s, n in Counter(bunyeler).most_common()]
            if bunyeler else [],
            "guvenilir": len(orneklem) >= GUVEN_ESIGI,
        }
    return cikti


def il_ozeti(kayit: list[dict[str, Any]]) -> dict[str, Any]:
    """İlçesi belli olmayanlar dahil, il geneli."""
    alanlar = {}
    for ad in VARSAYIM_SIRA:
        d = [k[ad] for k in kayit if k.get(ad) is not None]
        if d:
            alanlar[ad] = _ozet(d)
    bunyeler = [k["bunye"] for k in kayit if k["bunye"]]
    return {
        "n_ornek": len(kayit),
        "alanlar": alanlar,
        "bunye": [{"sinif": s, "n": n, "pay": round(n / len(bunyeler), 3)}
                  for s, n in Counter(bunyeler).most_common()],
    }


def yayimlanmis_ozet() -> dict[str, Any] | None:
    """Ham dosyalar yokken depodaki özetten devam eder.

    NEDEN VAR: Ham laboratuvar kayıtları depoya konmuyor (başkasının
    verisi). Panel ise GitHub Pages'te her gönderimde TEMİZ bir klondan
    üretiliyor. Geri düşüş olmasaydı yayındaki panelde ölçüm ve veri
    kalitesi sekmeleri boş çıkardı — denetimin tamamı, paneli açan
    kişiye görünmez olurdu.

    Depoya giren özet bunun için yeterli: ilçe medyanları, çeyrekler,
    güvenilirlik bayrağı ve bünye dağılımı modelin ihtiyacı olan her
    şeyi taşıyor. Ham kayıt, Lab No ya da köy-ölçüm bağı içermiyor.

    Dönen sözlük ``yeniden_uretildi: False`` ile işaretlenir; panel ve
    çıktılar bunun ham veriden değil özetten geldiğini söyleyebilsin.
    """
    yol = CIKTI / "toprak_olcum.json"
    if not yol.exists():
        return None
    try:
        d = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not d.get("var") or not d.get("ilce"):
        return None
    d["yeniden_uretildi"] = False
    return d


def uret(klasor: Path = VARSAYILAN_KLASOR) -> dict[str, Any]:
    kayit, ayiklanan = oku(klasor)
    if not kayit:
        ozet = yayimlanmis_ozet()
        if ozet is not None:
            return ozet
        return {"var": False, "sebep": f"{klasor} içinde xlsx bulunamadı"}

    ilceli = [k for k in kayit if k["ilce"]]
    yillar = sorted({k["yil"] for k in kayit})
    yil_ozet = [{
        "yil": y,
        "n": sum(1 for k in kayit if k["yil"] == y),
        "ilceli": sum(1 for k in kayit if k["yil"] == y and k["ilce"]),
    } for y in yillar]

    ilce = ilce_ozeti(ilceli)
    # Hangi varsayım ne kadar şaşmış — panelin asıl göstereceği şey
    sapma = []
    for ad in VARSAYIM_SIRA:
        kayitlar = [(i, v["alanlar"][ad]) for i, v in ilce.items()
                    if ad in v["alanlar"] and v["alanlar"][ad]["guvenilir"]]
        if not kayitlar:
            continue
        farklar = [abs(o["fark"]) for _i, o in kayitlar]
        sapma.append({
            "alan": ad,
            "guvenilir_ilce": len(kayitlar),
            "ortalama_mutlak_fark": round(st.fmean(farklar), 3),
            "en_buyuk_fark": round(max(farklar), 3),
            "en_buyuk_ilce": max(kayitlar, key=lambda x: abs(x[1]["fark"]))[0],
            "aralikta_kalan": sum(1 for _i, o in kayitlar if o["aralikta"]),
        })

    return {
        "var": True,
        "yeniden_uretildi": True,
        "kaynak": "Muş İl Tarım ve Orman Müdürlüğü laboratuvar kayıtları",
        "yillar": yillar,
        "yil_ozet": yil_ozet,
        "n_toplam": len(kayit),
        "n_ilceli": len(ilceli),
        "ayiklanan": ayiklanan,
        "guven_esigi": GUVEN_ESIGI,
        "ilce": ilce,
        "il": il_ozeti(kayit),
        "sapma": sapma,
        "kullanilmayan_sutunlar": {
            "P / P2O5": "birim tutarsız (medyan 0,12–0,16 ppm); laboratuvara "
                        "sorulmadan kullanılmıyor",
            "K2O": "kg/da etiketli ama medyan 242; değerler ppm'e benziyor",
        },
        "kil_kestirimi": {i: kil_kestirimi(v["bunye"])
                          for i, v in ilce.items() if v["bunye"]},
        "uyari": [
            "İlçe bilgisi yalnızca 2011 ve 2012 kayıtlarında var.",
            "Örnekler rastgele değil: çiftçinin analiz yaptırdığı tarlalardan "
            "geliyor, dolayısıyla ilçenin ortalama toprağını temsil etmez.",
            "Ham kayıtlar depoda tutulmaz; yalnızca bu özet yayımlanır.",
        ],
    }


# --------------------------------------------------------- ölçüm katmanı
# Laboratuvarın bünye sınıfları için kil oranı orta değerleri (%).
# Bünye sınıfı ölçümdür ama kil YÜZDESİ ölçülmemiştir; bu eşleme
# literatürden gelen bir dönüşümdür ve çıktıda "türetildi" diye
# işaretlenir. Ölçümle aynı kefeye konmaz.
BUNYE_KIL = {
    "Kumlu": 8.0,
    "Tınlı": 18.0,
    "Killi-Tınlı": 33.0,
    "Killi": 50.0,
    "Ağır Killi": 60.0,
}


def kil_kestirimi(bunye_dagilimi: list[dict[str, Any]]) -> float | None:
    """Bünye sınıflarının payından ağırlıklı kil oranı."""
    toplam = sum(b["n"] for b in bunye_dagilimi if b["sinif"] in BUNYE_KIL)
    if not toplam:
        return None
    return round(sum(BUNYE_KIL[b["sinif"]] * b["n"]
                     for b in bunye_dagilimi if b["sinif"] in BUNYE_KIL)
                 / toplam, 1)


def olcum_katmani(veri: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Modele bindirilecek ölçülmüş değerler.

    Yalnızca GÜVENİLİR (n >= GUVEN_ESIGI) alanlar döner. Az örnekli
    ilçede varsayım yerinde kalır — üç örnekle bir ilçenin toprağı
    yeniden tanımlanmaz.

    Her değer kendi türünü taşır: "ölçüm" doğrudan laboratuvardan,
    "türetildi" ölçülen bünye sınıfından hesaplanmış demektir.
    """
    veri = veri or uret()
    if not veri.get("var"):
        return {}
    katman: dict[str, dict[str, Any]] = {}
    for ilce, v in veri["ilce"].items():
        alanlar: dict[str, Any] = {}
        for ad, o in v["alanlar"].items():
            if o["guvenilir"]:
                alanlar[ad] = {"deger": o["medyan"], "tur": "ölçüm",
                               "n": o["n"]}
        kil = kil_kestirimi(v["bunye"]) if v["guvenilir"] else None
        if kil is not None:
            alanlar["kil"] = {"deger": kil, "tur": "türetildi",
                              "n": sum(b["n"] for b in v["bunye"])}
        if alanlar:
            katman[ilce] = alanlar
    return katman



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--klasor", type=Path, default=VARSAYILAN_KLASOR)
    a = ap.parse_args()

    veri = uret(a.klasor)
    if not veri["var"]:
        print("NOT:", veri["sebep"])
        return
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "toprak_olcum.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    print(f"{yol} yazıldı")
    print(f"  {veri['n_toplam']} örnek · {veri['n_ilceli']} tanesinde ilçe "
          f"(%{veri['n_ilceli'] / veri['n_toplam'] * 100:.0f})")
    if veri["ayiklanan"]:
        print(f"  ayıklanan aykırı değer: {veri['ayiklanan']}")
    print("\n  Varsayım ne kadar şaşmış:")
    for s in veri["sapma"]:
        print(f"    {s['alan']:6s} ort.mutlak fark {s['ortalama_mutlak_fark']:>6.2f} · "
              f"en büyük {s['en_buyuk_fark']:>6.2f} ({s['en_buyuk_ilce']}) · "
              f"{s['aralikta_kalan']}/{s['guvenilir_ilce']} ilçede varsayım "
              f"ölçüm aralığında")
    print("\n  İlçe bazında örnek sayısı:")
    for i, v in veri["ilce"].items():
        isaret = "" if v["guvenilir"] else "  AZ ÖRNEK"
        print(f"    {i:11s} {v['n_ornek']:>4}{isaret}")


if __name__ == "__main__":
    main()
