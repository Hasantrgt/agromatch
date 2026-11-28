"""
AGROMATCH - Depo karar sistemi
===============================
Tarla karar sisteminin depodaki karşılığı. Soru aynı: "ambarımda şu
böcek var, ne yapayım". Ama depo, tarladan iki temel noktada ayrılıyor
ve karar akışı bu iki farkın üzerine kuruluyor.

FARK 1 — BÖCEK TANENİN İÇİNDE OLABİLİR
Buğday biti, küçük tahıl kurdu ve arpa güvesi larvaları taneyi İÇERİDEN
yer. Tane dışarıdan sağlam görünür. Yüzeye uygulanan hiçbir şey —
diyatomlu toprak dahil — o larvaya ulaşamaz. Bu yüzden karar akışının
İLK sorusu "hangi ilaç" değil, "böcek nerede".

Bunu atlamak, projenin verebileceği en pahalı yanlış tavsiyedir:
çiftçi diyatomlu toprağı doğru uygular, erginleri öldürür, içerideki
larvalar gelişmeye devam eder ve ürün yine kaybedilir — üstelik
"kalıntısız yol işe yaramıyor" kanaatiyle.

FARK 2 — KALINTISIZ YOLUN ETKİSİ KOŞULA BAĞLI
Diyatomlu toprak zehir değil, aşındırıcıdır: böceğin mum tabakasını
yıpratır ve böcek su kaybından ölür. Dolayısıyla etkisi nemle ve
sıcaklıkla değişir. Projenin literatür katmanı bunu ölçmüş: AYNI ürün,
AYNI doz, AYNI süre —

    26 °C / %55 nem  ->  %2,2 ölüm
    30 °C / %40 nem  ->  %83 ölüm

Otuz yedi kat fark. Koşulu söylemeden "diyatomlu toprak kullan" demek,
tavsiye değil kura çekmektir. Bu yüzden koşul uyarısı kararın ayrı bir
adımı, dipnot değil.

ADIMLAR
    1. Böcek nerede?        iç besleyen mi, yüzeyde mi
    2. Hangi yollar ULAŞIR? kalıntısız seçenekler, larvaya ulaşıp
                            ulaşmadıklarına göre ayrılmış
    3. Koşul tutuyor mu?    kalıntısız yol seçildiyse neyin sağlanması
                            gerektiği, ölçülmüş sayılarla
    4. Son çare             fumigasyon ve bedeli

Çıktı: panelde "Depo" sekmesi.
"""

from __future__ import annotations

from typing import Any

from . import depo_profil as dp
from . import literatur as lt

ADIM_ADI = ("Böcek nerede", "Hangi yollar ulaşır", "Koşul tutuyor mu",
            "Son çare ve bedeli")

# Taneyi içeriden yiyen zararlıda yüzey uygulaması larvaya ULAŞMAZ.
# Bu, mücadele kaydındaki gucu["ic_larva"] alanıyla eşleşir.
YUZEY_YETMEZ = ("Yüzeye uygulanan yöntem taneyi içeriden yiyen larvaya "
                "ulaşmaz. Erginleri öldürür, içerideki nesli öldürmez.")


def _sayi(d: float) -> str:
    """Türkçe ondalık, tam sayıysa ondalık gösterme.

    Panelde aynı sayının metinde "38 kat", kutucukta "37,7 kat"
    görünmesi okuyanı tereddüde düşürür; ikisi tek kaynaktan gelmeli.
    """
    return (f"{d:.0f}" if abs(d - round(d)) < 0.05
            else f"{d:.1f}".replace(".", ","))


def _zararli(ad: str) -> dict[str, Any] | None:
    for z in dp.ZARARLILAR:
        if z["ad"] == ad:
            return z
    return None


def _nerede_adimi(z: dict[str, Any]) -> dict[str, Any]:
    """1. adım: böcek tanenin içinde mi, yüzeyinde mi."""
    ic = bool(z["ic_besleyen"])
    return {
        "adim": 1, "ad": ADIM_ADI[0],
        "durum": "tane içinde" if ic else "tane yüzeyinde",
        "aciklama": (
            (f"{z['ad']} larvası taneyi İÇERİDEN yer. " + YUZEY_YETMEZ
             + " Belirti aldatıcıdır: " + z["belirti"].split(";")[0].strip()
             + ".")
            if ic else
            f"{z['ad']} tanenin dışında beslenir; yüzeye uygulanan "
            "yöntemler ona ulaşır. Bu, kalıntısız yolun gerçekten "
            "yeterli olabileceği durumdur."),
        "ic_besleyen": ic,
        "belirti": z["belirti"],
        "optimum_sicaklik": z["optimum_sicaklik"],
        "en_dusuk_tane_nemi": z["en_dusuk_tane_nemi"],
    }


def _yollar_adimi(z: dict[str, Any]) -> dict[str, Any]:
    """2. adım: kalıntısız seçenekler, ULAŞIP ulaşmadıklarına göre."""
    ic = bool(z["ic_besleyen"])
    ulasan, yetersiz = [], []
    for m in dp.MUCADELE:
        if m["kalinti"] or m["tip"] == "izleme":
            continue
        kayit = {"ad": m["ad"], "tip": m["tip"], "etken": m["etken"],
                 "mekanizma": m["mekanizma"], "kosul": m.get("kosul", ""),
                 "bedel": m.get("bedel", ""), "organik": m.get("organik"),
                 "ic_larvaya": bool(m["gucu"]["ic_larva"])}
        if ic and not m["gucu"]["ic_larva"]:
            yetersiz.append(kayit)
        else:
            ulasan.append(kayit)

    return {
        "adim": 2, "ad": ADIM_ADI[1],
        "durum": "ulaşan yol var" if ulasan else "ulaşan kalıntısız yol yok",
        "aciklama": (
            ("Aşağıdakiler bu zararlıya ULAŞIR. Yanlarındaki liste ise "
             "ulaşmayanlar: tek başına kullanılırsa erginleri öldürüp "
             "sorunu sürdürürler." if ic else
             "Zararlı yüzeyde beslendiği için kalıntısız yolların hepsi "
             "ona ulaşır.")
            if ulasan else
            "Bu zararlıya ulaşan kalıntısız bir yol yok."),
        "ulasan": ulasan,
        "ulasmayan": yetersiz,
    }


def _kosul_adimi(yollar: dict[str, Any],
                 z: dict[str, Any] | None = None) -> dict[str, Any]:
    """3. adım: kalıntısız yol koşula bağlıysa, hangi koşula.

    Diyatomlu toprak için bu adım kritik: projenin literatür katmanı
    aynı ürünün aynı dozda 37 kat farklı sonuç verdiğini ÖLÇTÜ.
    """
    k = lt.sicaklik_karsitligi()
    de_var = any("Diyatom" in y["ad"] for y in yollar["ulasan"]) \
        or any("Diyatom" in y["ad"] for y in yollar["ulasmayan"])

    # ÖLÇÜMÜN KAPSAMI: 37,7 kat farkı Sitophilus granarius üzerinde
    # ölçüldü. Diyatomitin etkisi türe göre belirgin değişir, bu yüzden
    # sayıyı başka bir türün kartında tür adı vermeden göstermek onu
    # o tür için ölçülmüş gibi okutur.
    bu_tur = (z or {}).get("tur", "?")
    ayni_tur = bu_tur == k["tur"]
    kapsam = (f"Bu sayılar {k['tur']} üzerinde ölçüldü"
              + (" — yani tam da bu zararlı."
                 if ayni_tur else
                 f", bu zararlı ({bu_tur}) üzerinde değil. Diyatomitin "
                 "etkisi türe göre değişir; buradaki sayı koşulun NE KADAR "
                 "belirleyici olduğunu gösterir, bu tür için beklenen "
                 "ölümü değil."))
    return {
        "adim": 3, "ad": ADIM_ADI[2],
        "durum": "koşula bağlı" if de_var else "koşul kritik değil",
        "aciklama": (
            "Diyatomlu toprak zehir değil aşındırıcıdır: böceğin mum "
            "tabakasını yıpratır ve böcek su kaybından ölür. Bu yüzden "
            "etkisi nemle ve sıcaklıkla değişir — ve değişim küçük "
            "değildir. Aynı ürün, aynı doz, aynı süre: "
            f"{k['dusuk']['sicaklik']:.0f} °C / %{k['dusuk']['nem']:.0f} "
            f"nemde %{_sayi(k['dusuk']['olum'])} ölüm; "
            f"{k['yuksek']['sicaklik']:.0f} °C / %{k['yuksek']['nem']:.0f} "
            f"nemde %{_sayi(k['yuksek']['olum'])}. "
            f"{_sayi(k['kat'])} kat fark. "
            "Koşulu söylemeden 'diyatomlu toprak kullan' demek tavsiye "
            "değil, kura çekmektir. " + kapsam
            if de_var else
            "Bu zararlı için önerilen yollar koşula diyatomlu toprak "
            "kadar duyarlı değil."),
        "olcum": k if de_var else None,
        "olcum_ayni_tur": ayni_tur if de_var else None,
    }


def _son_care_adimi(z: dict[str, Any], yollar: dict[str, Any]) -> dict[str, Any]:
    """4. adım: fumigasyon ve bedeli."""
    kimyasal = [m for m in dp.MUCADELE
                if m["kalinti"] and m["gucu"]["ic_larva"]]
    gerekli = bool(z["ic_besleyen"]) and not yollar["ulasan"]
    return {
        "adim": 4, "ad": ADIM_ADI[3],
        "durum": "gerekebilir" if gerekli else "önce diğerleri",
        "aciklama": (
            "Taneyi içeriden yiyen larvaya ulaşan kalıntısız yol "
            "bulunamadı; fumigasyon gündeme gelir."
            if gerekli else
            "Kalıntısız yollar bu zararlıya ulaşıyor. Fumigasyon ilk "
            "seçenek değildir: kalıntı bırakır, direnç riski taşır ve "
            "deponun sızdırmaz olmasını gerektirir — sızdıran bir "
            "depoda hem işe yaramaz hem direnç üretir."),
        "secenekler": [{"ad": m["ad"], "etken": m["etken"],
                        "direnc_riski": m["direnc_riski"],
                        "kosul": m.get("kosul", ""),
                        "bedel": m.get("bedel", "")} for m in kimyasal],
    }


def karar(zararli: str) -> dict[str, Any]:
    """Tek bir depo zararlısı için dört adımlık karar akışı."""
    z = _zararli(zararli)
    if z is None:
        return {"var": False, "sebep": f"'{zararli}' kayıtlı depo zararlısı değil"}

    nerede = _nerede_adimi(z)
    yollar = _yollar_adimi(z)
    return {
        "var": True,
        "zararli": z["ad"], "tur": z["tur"], "sinif": z["sinif"],
        "onem": z["onem"], "karantina": bool(z.get("karantina")),
        "adimlar": [nerede, yollar, _kosul_adimi(yollar, z),
                    _son_care_adimi(z, yollar)],
        "ozet": _ozet(z, yollar),
    }


def _ozet(z: dict[str, Any], yollar: dict[str, Any]) -> str:
    if not z["ic_besleyen"]:
        return (f"{z['ad']} tanenin dışında beslenir: kalıntısız yollar "
                "ona ulaşır, koşul sağlanırsa fumigasyona gerek kalmaz.")
    if yollar["ulasan"]:
        adlar = ", ".join(y["ad"] for y in yollar["ulasan"][:2])
        return (f"{z['ad']} taneyi içeriden yer; yüzey uygulaması yetmez. "
                f"Ulaşan kalıntısız yollar: {adlar}.")
    return (f"{z['ad']} taneyi içeriden yer ve ulaşan kalıntısız yol yok — "
            "fumigasyon gündeme gelir.")


def hepsi() -> list[dict[str, Any]]:
    return [karar(z["ad"]) for z in dp.ZARARLILAR]


def ozet() -> dict[str, Any]:
    """Karar sisteminin topluca söyledikleri."""
    kararlar = hepsi()
    ic = [k["zararli"] for k in kararlar
          if k["adimlar"][0]["ic_besleyen"]]
    kalintisiz_yetmez = [k["zararli"] for k in kararlar
                         if k["adimlar"][1]["durum"].startswith("ulaşan kalıntısız yol yok")]
    return {
        "zararli": len(kararlar),
        "ic_besleyen": ic,
        "yuzey_uygulamasi_yetmeyen": len(ic),
        "kalintisiz_yolu_olmayan": kalintisiz_yetmez,
        "not_": "İç besleyen zararlıda yüzey uygulaması erginleri öldürür, "
                "içerideki nesli öldürmez. Bu ayrımı yapmayan bir tavsiye, "
                "kalıntısız yolun itibarını da yanlış yere harcar.",
    }
