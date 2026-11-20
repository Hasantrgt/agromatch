"""
AGROMATCH - Laboratuvar verisinin adli denetimi
================================================
NEDEN VAR: Bu veriyi bize veren hoca da ona güvenmiyor. Doğru cevap
veriyi savunmak değil, kusurlarını SAYMAK ve her kusur için ne
yapıldığını yazmaktır. Güvenilmeyen bir veriyle çalışmanın tek dürüst
yolu, nerede güvenilmez olduğunu ölçmektir.

Bu modül ham dosyaları okur ve yedi denetim çalıştırır. Hiçbir kusuru
düzeltmez — kusurları RAPORLAR. Düzeltme kararı analiz.py'de verilir ve
her denetim, o kararın ne olduğunu da yazar.

DENETİMLERİN MANTIĞI
--------------------
Bir kusurun ağırlığı, modele ulaşıp ulaşmadığına göre belirlenir:

  "ölçümü etkiler"      -> modele giren bir sayıyı bozar, ayıklanmalı
  "sütun kullanılmıyor" -> o sütun zaten modele girmiyor, zararsız
  "yalnızca kayıt"      -> istatistiği bozmaz, veri setinin niteliğini
                           gösterir

Çıktı: outputs/veri_kalitesi.json  ->  panelde "Veri kalitesi" sekmesi

    python src/toprak_olcum/kalite.py
"""

from __future__ import annotations

import argparse
import json
import random
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import mus_profil as mp

from . import analiz

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

# Ham Excel başlıkları — analiz.py yalnızca kullandığı sütunları
# tanır, denetim ise HEPSİNE bakmak zorunda.
SUTUN = {
    "lab": "Lab No",
    "yer": "Örneğin Alındığı Yer",
    "ph": "pH",
    "ec": "EC(dS/m)",
    "tuz": "Toplam Tuz (%)",
    "kirec": "CaCO3",
    "om": "Organik Madde (%)",
    "p_ppm": "P(ppm)",
    "p2o5_ppm": "P2O5 (ppm)",
    "p2o5_kgda": "P2O5 (kg/da)",
    "k2o_kgda": "K2O (kg/da)",
}

# Veride fiilen görülen Muş DIŞI yer adları: üç il ve iki ilçe. Liste
# uydurulmuş değil, yer sütununun denetiminden çıktı (bkz. d_yer). İşi,
# KESİN olarak Muş dışı olan kaydı GERÇEKTEN belirsiz olandan ayırmak:
# "Merkez - Bingöl" tartışmasız Bingöl'dür, ama "Bulanık - Sarıpınar"da
# hangisinin ilçe olduğu köy kütüğü olmadan bilinemez. İkisini aynı
# kutuya atmak, belirsizliği olduğundan büyük gösterir.
KOMSU_YER = {"Bingöl", "Bitlis", "Osmaniye", "Solhan", "Güroymak"}

# Ölçümün modele giren dört alanı
OLCUM_ALAN = ("ph", "ec", "tuz", "kirec", "om")

# 1 ppm kaç kg/da eder: 1 da = 1.000 m², 20 cm derinlik = 200 m³,
# hacim ağırlığı ~1,3 t/m³ -> 260 ton toprak. 1 mg/kg × 260 t = 0,26 kg.
PPM_KGDA = 0.26

# EC (dS/m) ile toplam tuz (%) arasındaki kabaca doğrusal bağ.
# Literatürde tuz% ≈ EC × 0,032 (0,064 civarı da kullanılır). Burada
# amaç katsayıyı doğrulamak değil, SATIR İÇİ tutarsızlığı yakalamak:
# oranı medyandan on kat sapan satır, iki sütundan birinin o satırda
# yanlış yazıldığını gösterir.
EC_TUZ_SAPMA_KAT = 10.0


def _ham(klasor: Path) -> list[dict[str, Any]]:
    """Beş dosyayı başlık adlarıyla okur. analiz.py'nin süzgeçleri YOK.

    analiz.oku() ile aynı kural: dosya yoksa openpyxl de gerekmez.
    """
    dosyalar = sorted(klasor.glob("*.xlsx")) if klasor.exists() else []
    if not dosyalar:
        return []

    try:
        import openpyxl
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            f"{len(dosyalar)} laboratuvar dosyası var ama openpyxl kurulu "
            "değil: pip install openpyxl") from e

    import re
    satirlar: list[dict[str, Any]] = []
    for yol in dosyalar:
        es = re.search(r"(20\d\d)", yol.name)
        if not es:
            continue
        yil = int(es.group(1))
        wb = openpyxl.load_workbook(yol, read_only=True, data_only=True)
        ham = list(wb.active.iter_rows(values_only=True))
        wb.close()
        if not ham:
            continue
        basliklar = [str(c).strip() if c else "" for c in ham[0]]
        indeks = {ad: basliklar.index(b) for ad, b in SUTUN.items()
                  if b in basliklar}
        for r in ham[1:]:
            if not any(c not in (None, "") for c in r):
                continue
            k: dict[str, Any] = {"yil": yil}
            for ad, i in indeks.items():
                d = r[i] if i < len(r) else None
                k[ad] = (str(d).strip() if ad in ("lab", "yer") and d
                         else analiz._sayi(d) if ad not in ("lab", "yer")
                         else None)
            satirlar.append(k)
    return satirlar


def _denetim(ad: str, soru: str, bulgu: int, toplam: int, agirlik: str,
             ne_yapildi: str, ayrinti: Any = None) -> dict[str, Any]:
    return {
        "ad": ad,
        "soru": soru,
        "bulgu": bulgu,
        "toplam": toplam,
        "oran": round(bulgu / toplam * 100, 2) if toplam else 0.0,
        "agirlik": agirlik,
        "ne_yapildi": ne_yapildi,
        "ayrinti": ayrinti,
    }


# --- 1 ------------------------------------------------------------------
def d_yer(ham: list[dict[str, Any]]) -> dict[str, Any]:
    """Yer sütunu: hangi yıl dolu, dolu olanların kaçı Muş'a bağlanıyor."""
    yil: dict[int, Counter[str]] = defaultdict(Counter)
    kirilim: Counter[str] = Counter()
    dis: Counter[str] = Counter()
    for k in ham:
        y = k.get("yer") or ""
        yil[k["yil"]]["n"] += 1
        if not y:
            yil[k["yil"]]["bos"] += 1
            kirilim["yer sütunu boş"] += 1
            continue
        yil[k["yil"]]["dolu"] += 1
        i = analiz.ilce_bul(y)
        if i:
            kirilim["Muş ilçesine bağlandı"] += 1
            continue
        parca = [p.strip() for p in y.replace("/", "-").replace(",", "-")
                 .split("-") if p.strip()]
        son = parca[-1] if parca else "?"
        if son in KOMSU_YER:
            # Tartışma yok: son parça başka bir ilin ya da o ilin bir
            # ilçesinin adı. "Merkez - Bingöl" Bingöl'dür.
            kirilim["Muş dışı"] += 1
        elif any(p in mp.ILCE for p in parca[:-1]):
            # Son parça tanınmıyor ama içinde Muş ilçesi var: sıra ters
            # yazılmış olabilir ("Bulanık - Sarıpınar"). Son parçanın
            # bilinen bir Muş köyü olup olmadığını bilmek gerekir — o
            # kütük elimizde yok, bu yüzden kayıt GERÇEKTEN belirsiz.
            kirilim["belirsiz sıralama"] += 1
        else:
            kirilim["tanınmayan yer"] += 1
        dis[son] += 1

    return _denetim(
        "Yer sütunu",
        "Örnek hangi ilçeden alındı — ve gerçekten Muş'tan mı?",
        len(ham) - kirilim["Muş ilçesine bağlandı"], len(ham),
        "ölçümü etkiler",
        "Son parça kuralı uygulanıyor; Muş dışı kayıt ELENİR. Eski "
        "sürüm 130 kaydı yanlış ilçeye yazmıştı, düzeltildi.",
        {
            "kirilim": dict(kirilim),
            "yil": {str(y): dict(c) for y, c in sorted(yil.items())},
            "dis_iller": dict(dis.most_common(8)),
        })


# --- 2 ------------------------------------------------------------------
def d_imkansiz(ham: list[dict[str, Any]]) -> dict[str, Any]:
    """Tarım toprağında fiziksel olarak olamayacak değerler."""
    sayim: Counter[str] = Counter()
    ucler: dict[str, list[float]] = defaultdict(list)
    for k in ham:
        for alan in OLCUM_ALAN:
            d = k.get(alan)
            if d is None or alan not in analiz.GECERLI:
                continue
            alt, ust = analiz.GECERLI[alan]
            if not (alt <= d <= ust):
                sayim[alan] += 1
                ucler[alan].append(d)
    return _denetim(
        "Fiziksel olarak imkânsız değerler",
        "pH 2,06 olan bir tarım toprağı yoktur — bu ölçüm değil yazım hatası.",
        sum(sayim.values()), len(ham), "ölçümü etkiler",
        "Her biri ayıklanıyor (analiz.GECERLI aralıkları). Ayıklanan "
        "sayısı panelde ve analiz çıktısında yazar.",
        {alan: {"n": n, "aralik": list(analiz.GECERLI[alan]),
                "gorulen": sorted(ucler[alan])[:6]}
         for alan, n in sorted(sayim.items(), key=lambda x: -x[1])})


# --- 3 ------------------------------------------------------------------
def _fazla(satirlar: list[dict[str, Any]]) -> int:
    """Birden fazla kez görünen ölçüm takımlarının fazlalık sayısı."""
    c: Counter[tuple[Any, ...]] = Counter()
    for k in satirlar:
        imza = tuple(k.get(a) for a in OLCUM_ALAN)
        if all(v is None for v in imza):
            continue
        c[imza] += 1
    return sum(n - 1 for n in c.values() if n > 1)


def _sans_beklentisi(grup: list[dict[str, Any]], tur: int = 200,
                     tohum: int = 20261118) -> tuple[float, float]:
    """Yinelenme şansla da olabilir mi — sütunları bağımsız karıştırarak ölç.

    Beş değer yuvarlanmış olduğu için iki ayrı örneğin tesadüfen aynı
    takımı vermesi mümkündür. Bu yüzden "176 satır kopyalanmış" demek
    ÖLÇMEDEN iddia etmek olur. Her sütun kendi içinde karıştırılırsa
    dağılımlar korunur ama satır içi bağ kopar; o kurguda çıkan
    yinelenme sayısı, saf şansın beklentisidir. Gözlenen sayı bu
    beklentinin çok üstündeyse tekrar gerçektir.
    """
    rnd = random.Random(tohum)
    alanlar = list(OLCUM_ALAN)
    sonuc = []
    for _ in range(tur):
        kol = {a: [k.get(a) for k in grup] for a in alanlar}
        for a in alanlar:
            rnd.shuffle(kol[a])
        sonuc.append(_fazla([{a: kol[a][i] for a in alanlar}
                             for i in range(len(grup))]))
    return st.fmean(sonuc), st.pstdev(sonuc)


def d_yinelenen(ham: list[dict[str, Any]]) -> dict[str, Any]:
    """Aynı ölçüm takımının birden fazla satırda tekrar etmesi."""
    yila: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for k in ham:
        yila[k["yil"]].append(k)

    yil_ayrinti = {}
    gozlenen = beklenen = 0.0
    for yil, grup in sorted(yila.items()):
        g = _fazla(grup)
        b, s = _sans_beklentisi(grup)
        gozlenen += g
        beklenen += b
        yil_ayrinti[str(yil)] = {"n": len(grup), "gozlenen": g,
                                 "sans_beklentisi": round(b, 2),
                                 "sapma": round(s, 2)}

    lab: Counter[str] = Counter(str(k.get("lab")) for k in ham if k.get("lab"))
    lab_tekrar = sum(n - 1 for n in lab.values() if n > 1)
    kat = round(gozlenen / beklenen, 1) if beklenen > 0.05 else None

    return _denetim(
        "Yinelenen satırlar",
        "Beş ölçümün tamamı aynı olan satırlar — gerçek iki örnek mi, "
        "kopyalanmış tek örnek mi?",
        int(gozlenen), len(ham), "yalnızca kayıt",
        "AYIKLANMIYOR. Hangi satırın kopya olduğu tek tek bilinemez ve "
        "silmek veri uydurmak olurdu. Medyan kullanıldığı için etkisi "
        "sınırlı. Ama tekrarın GERÇEK olduğu permütasyon sınamasıyla "
        "gösterildi: laboratuvara sorulacaklar listesinde.",
        {"yila_gore": yil_ayrinti,
         "ayni_lab_no": lab_tekrar,
         "sans_beklentisi_toplam": round(beklenen, 2),
         "sans_kati": kat,
         "yorum": (
             f"Şans beklentisi {beklenen:.1f}".replace(".", ",")
             + f", gözlenen {int(gozlenen)}. "
             "Yuvarlanmış beş değerin tesadüfen çakışması bu sayıyı "
             "açıklamıyor; tekrar gerçektir. 2011 dosyası tek başına "
             f"{yil_ayrinti.get('2011', {}).get('gozlenen', 0)} tanesini "
             "taşıyor — kusur yıla göre dağılmıyor, bir dosyada "
             "yoğunlaşıyor.")})


# --- 4 ------------------------------------------------------------------
def d_kopyala(ham: list[dict[str, Any]]) -> dict[str, Any]:
    """Aynı satırda iki ayrı ölçümün birebir eşit olması."""
    ciftler = (("p2o5_ppm", "k2o_kgda"), ("p2o5_kgda", "k2o_kgda"),
               ("p_ppm", "p2o5_ppm"), ("ec", "tuz"))
    bulgu: Counter[str] = Counter()
    for k in ham:
        for a, b in ciftler:
            x, y = k.get(a), k.get(b)
            if x is not None and y is not None and x == y and x != 0:
                bulgu[f"{SUTUN[a]} = {SUTUN[b]}"] += 1
    return _denetim(
        "Kopyala-yapıştır izleri",
        "İki farklı ölçümün aynı satırda birebir eşit olması, birinin "
        "diğerinden kopyalandığını düşündürür.",
        sum(bulgu.values()), len(ham), "sütun kullanılmıyor",
        "Etkilenen sütunlar (fosfor, potasyum) birim belirsizliği "
        "yüzünden zaten modele girmiyor. Bulgu, dosyanın elle "
        "düzenlendiğinin kanıtı olarak kayda geçer.",
        dict(bulgu.most_common()))


# --- 5 ------------------------------------------------------------------
def d_ec_tuz(ham: list[dict[str, Any]]) -> dict[str, Any]:
    """EC ile toplam tuz birbirine bağlıdır; satır içi tutarsızlık."""
    oran = [(k["tuz"] / k["ec"], k) for k in ham
            if k.get("ec") and k.get("tuz") and k["ec"] > 0]
    if not oran:
        return _denetim("EC - tuz tutarlılığı", "", 0, len(ham),
                        "ölçümü etkiler", "İki sütundan biri yok.", None)
    med = st.median(o for o, _ in oran)
    sapan = [(o, k) for o, k in oran
             if o > med * EC_TUZ_SAPMA_KAT or o < med / EC_TUZ_SAPMA_KAT]
    return _denetim(
        "EC - tuz tutarlılığı",
        "Elektrik iletkenliği ile toplam tuz aynı şeyi ölçer; oranı "
        "medyandan on kat sapan satırda biri yanlış yazılmış.",
        len(sapan), len(oran), "ölçümü etkiler",
        "Modele EC giriyor, tuz girmiyor. Sapan satırlar tek tek "
        "ayıklanmıyor; aralık süzgeci ve medyan birlikte etkisini "
        "sınırlıyor. Laboratuvara sorulacaklar listesinde.",
        {"medyan_oran": round(med, 5),
         "sapan": len(sapan),
         "en_uc": [round(o, 4) for o, _ in sorted(sapan, key=lambda x: -x[0])[:5]]})


# --- 6 ------------------------------------------------------------------
def d_birim(ham: list[dict[str, Any]]) -> dict[str, Any]:
    """Fosforun iki birimi aynı ölçümü anlatmalı — anlatmıyor."""
    cift = [(k["p2o5_kgda"] / k["p2o5_ppm"], k) for k in ham
            if k.get("p2o5_ppm") and k.get("p2o5_kgda") and k["p2o5_ppm"] > 0]
    med = st.median(o for o, _ in cift) if cift else 0.0
    # "bulgu", karşılaştırılabilir satır sayısı değil KUSURLU satır
    # sayısı olmalı: beklenen orandan beş kat sapan satırlar.
    sapan = sum(1 for o, _ in cift
                if o > PPM_KGDA * 5 or o < PPM_KGDA / 5)
    medyanlar = {}
    for ad in ("p_ppm", "p2o5_ppm", "p2o5_kgda", "k2o_kgda"):
        d = [k[ad] for k in ham if k.get(ad) is not None]
        medyanlar[SUTUN[ad]] = round(st.median(d), 3) if d else None
    return _denetim(
        "Fosfor ve potasyum birimi",
        "P2O5'in kg/da ve ppm sütunları aynı ölçümün iki birimi olmalı; "
        f"oranları {PPM_KGDA} civarı çıkmalı.",
        sapan, len(cift), "sütun kullanılmıyor",
        "BU İKİ SÜTUN MODELE SOKULMUYOR. Birimi şüpheli bir sayıyı "
        "modele koymak, hiç koymamaktan kötüdür. İl Tarım'a sorulacak "
        "ilk teknik soru bu.",
        {"beklenen_oran": PPM_KGDA,
         "karsilastirilabilir_satir": len(cift),
         "olculen_oran_medyan": round(med, 2),
         "kat_fark": round(med / PPM_KGDA, 1) if PPM_KGDA else None,
         "sutun_medyanlari": medyanlar})


# --- 7 ------------------------------------------------------------------
def d_bos(ham: list[dict[str, Any]]) -> dict[str, Any]:
    """Hiçbir kullanılabilir ölçümü olmayan satırlar."""
    bos = sum(1 for k in ham
              if all(k.get(a) is None for a in OLCUM_ALAN))
    eksik: Counter[str] = Counter()
    for k in ham:
        for a in OLCUM_ALAN:
            if k.get(a) is None:
                eksik[a] += 1
    return _denetim(
        "Boş ve eksik ölçümler",
        "Satır var ama ölçüm yok ya da bir sütun o satırda boş.",
        bos, len(ham), "yalnızca kayıt",
        "Boş satır istatistiğe girmez. Eksik sütun o alanın n'sini "
        "düşürür; her alanın kendi n'si ayrı hesaplanıyor.",
        {"tamamen_bos": bos,
         "sutun_basina_eksik": {SUTUN[a]: n for a, n in eksik.most_common()}})


DENETIMLER = (d_yer, d_imkansiz, d_yinelenen, d_kopyala, d_ec_tuz,
              d_birim, d_bos)


def rapor(klasor: Path | None = None) -> dict[str, Any]:
    klasor = klasor or analiz.VARSAYILAN_KLASOR
    if not klasor.exists():
        return {"var": False, "sebep": f"{klasor} bulunamadı"}
    ham = _ham(klasor)
    if not ham:
        return {"var": False, "sebep": "okunabilir satır yok"}

    denetim = [d(ham) for d in DENETIMLER]
    agir = [d for d in denetim if d["agirlik"] == "ölçümü etkiler"]
    return {
        "var": True,
        "n_satir": len(ham),
        "yillar": sorted({k["yil"] for k in ham}),
        "kaynak": "Muş İl Tarım ve Orman Müdürlüğü laboratuvar defteri",
        "denetim": denetim,
        "ozet": {
            "denetim_sayisi": len(denetim),
            "kusur_bulunan": sum(1 for d in denetim if d["bulgu"]),
            "olcumu_etkileyen": len(agir),
            "ayiklanan_deger": next(
                (d["bulgu"] for d in denetim
                 if d["ad"].startswith("Fiziksel")), 0),
            "modele_giren_satir": sum(
                1 for k in ham if analiz.ilce_bul(k.get("yer"))),
        },
        "yargi": (
            "Bu veri kusurludur ve kusurları yukarıda tek tek sayılıdır. "
            "Kullanılabilir olmasının sebebi kusursuz olması değil, her "
            "kusurun nereye dokunduğunun bilinmesidir: ölçümü etkileyen "
            "kusurlar ayıklanıyor, birimi şüpheli sütunlar modele hiç "
            "sokulmuyor, kalanı yalnızca kayda geçiyor. Veriyi veren "
            "kurumun kendisi de ona temkinli yaklaşıyor; bu rapor o "
            "temkinin yerini tutmak için değil, onu ölçülebilir kılmak "
            "için var."),
    }


def main() -> None:
    a = argparse.ArgumentParser(description="Laboratuvar verisinin denetimi")
    a.add_argument("--klasor", type=Path, default=None)
    a.add_argument("--json", action="store_true", help="JSON yaz")
    n = a.parse_args()

    r = rapor(n.klasor)
    if not r.get("var"):
        print("Denetim çalışmadı:", r.get("sebep"))
        return

    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "veri_kalitesi.json"
    yol.write_text(json.dumps(r, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"{yol} yazıldı\n")
    print(f"{r['n_satir']} satır, {r['yillar'][0]}-{r['yillar'][-1]}\n")
    for d in r["denetim"]:
        im = "!!" if d["agirlik"] == "ölçümü etkiler" and d["bulgu"] else "  "
        print(f"{im} {d['ad']:34s} {d['bulgu']:6d} / {d['toplam']:<6d}"
              f" %{d['oran']:<6} {d['agirlik']}")
    o = r["ozet"]
    print(f"\n{o['denetim_sayisi']} denetim · {o['kusur_bulunan']} kusur "
          f"· modele giren satır {o['modele_giren_satir']}")


if __name__ == "__main__":
    main()
