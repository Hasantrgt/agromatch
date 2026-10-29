"""
AGROMATCH - Erken uyarı takvimi
================================
Projenin dört katmanını tek bir uyarı akışına çevirir: hangi ilçede,
hangi ayda, neye bakılacak ve neden.

    hastalık katalogu   kritik aylar ve yönetim önerisi
    tarla zararlıları   kritik aylar, eşik, kalıntısız yol
    ambar modeli        yığın sıcaklığının gelişme eşiğini aştığı aylar
    iklim modeli        don riski ve ekim penceresi

ÇÖZÜNÜRLÜK: AY
--------------
Uyarılar GÜN değil AY çözünürlüğündedir, çünkü altındaki verinin
çözünürlüğü budur: ilçe sıcaklıkları aylık ortalama, hastalık kritik
dönemleri ay olarak yazılı. Günlük çözünürlük ancak günlük istasyon
verisi bağlanınca mümkün olur; o zaman ``gunluk_veri`` bayrağı açılır ve
derece-gün birikimi gün gün hesaplanır. Bugün böyle bir veri YOK ve
panel bunu açıkça yazar.

Bu yüzden sistem bir TAHMİN değil, BEKLENEN TAKVİMDİR: iklim normaline
göre hangi ayda neyin kapıyı çalacağını söyler. "Önümüzdeki hafta süne
çıkacak" demez, diyemez.

YAPAY ZEKÂ NEREDE
-----------------
Burada değil. Derece-gün ve eşik kuralları yapay zekâ değildir ve öyle
sunulmaz. Projenin iki eğitilmiş modeli (Cercospora lezyon sınıflayıcı
ve toprak uygunluk modeli) bu takvimin DOĞRULAMA adımında devreye
girer: takvim "Cercospora dönemi" uyarısı verir, üretici yaprak
fotoğrafı çeker, sınıflayıcı lekeyi doğrular. Uyarıyı model üretmez,
modeli uyarı tetikler.

Çıktı: outputs/uyari.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mus_hastalik_profil as hp
import mus_iklim as mi
import mus_profil as mp
from bocek import pestisit as ps
from bocek import tarla_zararli as tz
from depo import ambar_sicaklik as amb
from depo import depo_profil as dp

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

AY_AD = ("Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık")

# Günlük istasyon verisi bağlandığında True olacak. Panel bu bayrağa
# bakarak "beklenen takvim" mi "ölçüme dayalı uyarı" mı olduğunu yazar.
GUNLUK_VERI = False

# Don hassasiyeti bu değerin üstündeki ürünler için don uyarısı üretilir
DON_HASSAS_ESIK = 4

# Uyarı türleri ve panelde hangi sırada gösterilecekleri
TURLER = ("don", "zararlı", "hastalık", "depo", "sürvey")


def _uyari(ay: int, ilce: str, tur: str, konu: str, baslik: str,
           gerekce: str, yapilacak: str, siddet: int,
           kaynak: str) -> dict[str, Any]:
    if tur not in TURLER:
        raise ValueError(f"bilinmeyen uyarı türü: {tur}")
    if not 1 <= ay <= 12:
        raise ValueError(f"geçersiz ay: {ay}")
    if not 1 <= siddet <= 3:
        raise ValueError(f"şiddet 1-3 olmalı: {siddet}")
    return {
        "ay": ay, "ay_ad": AY_AD[ay - 1], "ilce": ilce, "tur": tur,
        "konu": konu, "baslik": baslik, "gerekce": gerekce,
        "yapilacak": yapilacak, "siddet": siddet, "kaynak": kaynak,
        # Her uyarı, hangi veriye dayandığını kendisi taşır. Panelde
        # "iklim normali" yazan bir uyarı ile ölçüme dayanan bir uyarı
        # aynı görünmemeli.
        "veri": "ölçüm" if GUNLUK_VERI else "iklim normali",
    }


def oncu_aylar(aylar: list[int]) -> list[tuple[int, list[int]]]:
    """Kritik ay kümesini BİTİŞİK bloklara ayırır, her bloğun öncüsünü verir.

    Ekin kambur böceği gibi türlerin dönemi yıla iki yerden yayılır
    (Eki-Kas ve Mar-Nis). Yalnızca en küçük aya bakmak sonbahar dönemini
    kaybettiriyordu; her blok kendi uyarısını alır.

    Yıl döngüseldir: Aralık ile Ocak bitişiktir.
    """
    kalan = sorted(set(aylar))
    if not kalan:
        return []
    bloklar: list[list[int]] = []
    for ay in kalan:
        if bloklar and ay == bloklar[-1][-1] + 1:
            bloklar[-1].append(ay)
        else:
            bloklar.append([ay])
    # Aralık-Ocak sarması: ilk blok Ocak'la, son blok Aralık'la başlıyorsa birleştir
    if len(bloklar) > 1 and bloklar[0][0] == 1 and bloklar[-1][-1] == 12:
        bloklar[0] = bloklar[-1] + bloklar[0]
        bloklar.pop()
    return [(12 if b[0] == 1 else b[0] - 1, b) for b in bloklar]


def zararli_uyarilari(ilce: str, urunler: set[str]) -> list[dict[str, Any]]:
    """Tarla zararlılarının kritik aylarından uyarı üretir.

    Uyarı, kritik ayın KENDİSİNE değil BİR ÖNCESİNE konur: erken uyarı
    olmasının anlamı bu. Zararlı göründükten sonra haber vermek uyarı
    değil, tespittir.
    """
    cikti = []
    for z in tz.ZARARLILAR:
        if not set(z["urunler"]) & urunler or not z["kritik_aylar"]:
            continue
        kalintisiz = ps.kalintisiz_yol(z["ad"])
        for onceki, blok in oncu_aylar(list(z["kritik_aylar"])):
            yap = f"{AY_AD[blok[0] - 1]} ayında {z['hedef_organ']} kontrol edilmeli. "
            yap += (f"Eşik: {z['esik']}" if z["esik"]
                    else "Bu tür için yazılı ekonomik zarar eşiği YOK; "
                         "ilaçlama kararı gözleme dayanır.")
            if kalintisiz:
                yap += (" · Kalıntısız seçenek: "
                        + ", ".join(g["ad"] for g in kalintisiz))
            cikti.append(_uyari(
                onceki, ilce, "zararlı", z["ad"],
                f"{z['ad']} dönemi yaklaşıyor",
                f"{', '.join(sorted(set(z['urunler']) & urunler))} ekili; "
                f"bu dönem {' · '.join(AY_AD[a - 1] for a in blok)}"
                + (f" (yılın diğer dönemi: "
                   f"{' · '.join(AY_AD[a - 1] for a in z['kritik_aylar'] if a not in blok)})"
                   if len(blok) < len(z["kritik_aylar"]) else "")
                + f". {z['belirti']}",
                yap, z["onem"], z["esik_kaynak"] or z["kaynak"]))
    return cikti


def hastalik_uyarilari(ilce: str, urunler: set[str]) -> list[dict[str, Any]]:
    """Hastalık kataloğunun kritik aylarından uyarı üretir.

    Yalnızca önemi 3 olanlar alınır; yoksa altı ilçe × elli dokuz
    hastalık = okunamaz bir liste çıkar. Tamamı Hastalık sekmesinde.
    """
    cikti = []
    for h in hp.HASTALIKLAR:
        if h["urun"] not in urunler or h["onem"] < 3 or not h["kritik_aylar"]:
            continue
        for onceki, blok in oncu_aylar(list(h["kritik_aylar"])):
            cikti.append(_uyari(
                onceki, ilce, "hastalık", h["ad"],
                f"{h['urun']}: {h['ad']} dönemi yaklaşıyor",
                f"Kritik dönem {' · '.join(AY_AD[a - 1] for a in blok)}; "
                f"elverişli sıcaklık {h['sicaklik_opt'][0]}–{h['sicaklik_opt'][1]} °C. "
                f"{h['belirti']}",
                h["yonetim"] + ("  (Belirti görülürse yaprak fotoğrafı çekilip "
                                "lezyon sınıflayıcıya verilebilir.)"
                                if h["goruntuden"] else ""),
                3, h["kaynak"]))
    return cikti


def don_uyarilari(ilce: str, urunler: set[str]) -> list[dict[str, Any]]:
    """Dona hassas ürünlerin ekim penceresi için uyarı."""
    cikti = []
    sicaklik = mi.aylik_sicaklik(ilce)
    for urun in sorted(urunler):
        if urun not in mi.IKLIM_ISTEK:
            continue
        taban, _gerekli, don_hassas, _serin, ekim_ay = mi.IKLIM_ISTEK[urun]
        if don_hassas < DON_HASSAS_ESIK:
            continue
        onceki = 12 if ekim_ay == 1 else ekim_ay - 1
        gece = sicaklik[ekim_ay - 1] - mi.GUNLUK_FARK
        cikti.append(_uyari(
            onceki, ilce, "don", urun,
            f"{urun}: don riski, ekim zamanlaması",
            f"Hedef ekim ayı {AY_AD[ekim_ay - 1]}; o ayın ortalama gece "
            f"sıcaklığı yaklaşık {gece:.1f} °C. Bu ürünün don hassasiyeti "
            f"{don_hassas}/5.",
            "Ekimi toprak sıcaklığı ölçülerek yapın; geç don riski geçmeden "
            f"ekmeyin. Taban sıcaklık {taban} °C.",
            3 if don_hassas == 5 else 2, "literatür"))
    return cikti


def depo_uyarilari(ilce: str) -> list[dict[str, Any]]:
    """Ambar yığın sıcaklığının gelişme eşiğini aştığı dönem."""
    cikti = []
    yigin = amb.ambar_sicakligi(ilce)
    for z in dp.ZARARLILAR:
        asan = [a for a in range(1, 13) if yigin[a - 1] > z["taban_sicaklik"]]
        if not asan:
            continue
        ilk = min(asan)
        onceki = 12 if ilk == 1 else ilk - 1
        yontem = dp.kalintisiz_secenekler()
        cikti.append(_uyari(
            onceki, ilce, "depo", z["ad"],
            f"Depoda {z['ad']} gelişme dönemi başlıyor",
            f"Yığın sıcaklığı {AY_AD[ilk - 1]} ayından itibaren bu türün "
            f"gelişme eşiğini ({z['taban_sicaklik']} °C) aşıyor; "
            f"yılda {len(asan)} ay elverişli."
            + ("  Larva tanenin İÇİNDE geliştiği için yalnızca ergine "
               "etkili yöntem gizli bulaşmayı temizlemez."
               if z["ic_besleyen"] else ""),
            "Ambar sıcaklığını ölç (veri kaydedici), havalandırmayı planla, "
            "eski ürün artığını temizle. Kalıntısız seçenekler: "
            + ", ".join(m["ad"] for m in yontem[:3]),
            z["onem"], "literatür"))
    return cikti


def survey_uyarilari(ilce: str, urunler: set[str]) -> list[dict[str, Any]]:
    """Resmî karar kuralı olan zararlılar için sürvey hatırlatması.

    Şimdilik tek örnek süne; talimat kararı parazitlenme oranına
    bağladığı için ölçüm yapılmadan ilaçlama kararı verilemez.
    """
    if not {"Buğday", "Arpa"} & urunler:
        return []
    sune = next(z for z in tz.ZARARLILAR if z["ad"] == "Süne")
    ilk = min(sune["kritik_aylar"])
    tablo = " · ".join(f"{y:g} ergin → %{o:g}"
                       for y, o in tz.SUNE_PARAZITLENME)
    return [_uyari(
        12 if ilk == 1 else ilk - 1, ilce, "sürvey", "Süne",
        "Süne: kışlamış ergin sayımı ve parazitlenme sürveyi",
        f"Teknik talimat ilaçlama kararını tek bir eşiğe değil, ergin "
        f"yoğunluğu ile yumurta parazitlenme oranının birlikte "
        f"okunmasına bağlıyor. Sürvey eşiği m²'de "
        f"{tz.SUNE_SURVEY_ERGIN:g} kışlamış ergin.",
        f"Önce ergin sayımı yap. {tz.SUNE_SURVEY_ERGIN:g}/m² aşılırsa "
        f"7 gün içinde yumurta parazitlenme sürveyine geç. Karar tablosu: "
        f"{tablo}. Bu oranların üstünde 1.-3. döneme İLAÇLAMA YAPILMAZ.",
        3, "ZMTT")]


def ilce_uyarilari(ilce: str) -> list[dict[str, Any]]:
    # İlçede fiilen ekili ürünler; uyarı üretmenin ön koşulu bu.
    # Ekilmeyen ürün için uyarı üretmek listeyi okunmaz yapar.
    urunler = set(mp.DESEN.get(ilce, {}))
    hepsi = (zararli_uyarilari(ilce, urunler)
             + hastalik_uyarilari(ilce, urunler)
             + don_uyarilari(ilce, urunler)
             + depo_uyarilari(ilce)
             + survey_uyarilari(ilce, urunler))
    return sorted(hepsi, key=lambda u: (u["ay"], -u["siddet"],
                                        TURLER.index(u["tur"]), u["konu"]))


def uret() -> dict[str, Any]:
    ilceler = list(mp.ILCE)
    uyarilar = {i: ilce_uyarilari(i) for i in ilceler}
    aylik = {i: [sum(1 for u in uyarilar[i] if u["ay"] == a)
                 for a in range(1, 13)] for i in ilceler}
    tum = [u for lst in uyarilar.values() for u in lst]
    return {
        "gunluk_veri": GUNLUK_VERI,
        "cozunurluk": "ay",
        "ilceler": ilceler,
        "aylar": list(AY_AD),
        "turler": list(TURLER),
        "uyarilar": uyarilar,
        "aylik_sayi": aylik,
        "ozet": {
            "toplam": len(tum),
            "ilce_basina": round(len(tum) / len(ilceler), 1),
            "tur": {t: sum(1 for u in tum if u["tur"] == t) for t in TURLER},
            "zmtt": sum(1 for u in tum if u["kaynak"] == "ZMTT"),
            "en_yogun_ay": AY_AD[max(
                range(12), key=lambda a: sum(v[a] for v in aylik.values()))],
        },
    }


def main() -> None:
    veri = uret()
    CIKTI.mkdir(exist_ok=True)
    yol = CIKTI / "uyari.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    o = veri["ozet"]
    print(f"{yol} yazıldı")
    print(f"  {o['toplam']} uyarı · ilçe başına {o['ilce_basina']}")
    print("  tür:", " · ".join(f"{k} {v}" for k, v in o["tur"].items()))
    print(f"  en yoğun ay: {o['en_yogun_ay']}")
    print(f"  çözünürlük: {veri['cozunurluk']} "
          f"({'ölçüm' if veri['gunluk_veri'] else 'İKLİM NORMALİ — tahmin değil'})")


if __name__ == "__main__":
    main()
