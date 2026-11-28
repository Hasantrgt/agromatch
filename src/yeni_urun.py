"""
AGROMATCH - "Muş'ta şu ürün yetişir mi?"
=========================================
Proje bugüne kadar EKİLEN dokuz ürün arasında karar veriyordu: hangisini
büyüt, hangisini kıs. Çiftçinin ve hocanın sorduğu bir soru daha var ve
model aslında onu cevaplayabilecek durumdaydı:

    "Muş'ta hiç ekilmemiş bir ürün yetişir mi?"

Cevaplayabilir, çünkü iklim tarafı TABLO DEĞİL, MEKANİK: etkili sıcaklık
toplamı (GDD), donsuz gün ve kış minimumu üzerinden çalışıyor. Yeni bir
ürün için gereken şey Muş'a dair veri değil, O ÜRÜNE dair istek.

MODELDE BULUNAN AÇIK
Bu soru sorulunca bir eksik ortaya çıktı: mus_iklim.uygunluk() kış
minimumuna HİÇ bakmıyordu. Dokuz ürünün dokuzu da yıllık olduğu için
bu bugüne kadar sorun değildi — kışlık tahıl kar altında geçirir,
diğerleri ilkbaharda ekilir. Ama çok yıllık bir tür sorulduğunda model
zeytini yazın GDD'yi tutturduğu için kabul ederdi. Kış dayanımı bu
modülde ele alınıyor ve mus_iklim'in sıcaklık serisi yeniden
hesaplanmıyor, OKUNUYOR (formül tek yerde kalsın).

YÖNTEM — ve neden bu sırayla
    1. KIŞ        Çok yıllık tür kışı tarlada geçirir. Kış minimumu
                  türün dayanımının altındaysa cevap HAYIR'dır ve
                  toprağın ne dediğinin önemi yoktur.
    2. SICAKLIK   GDD ve donsuz gün yeterli mi (mus_iklim).
    3. TOPRAK     İsteği kayıtlıysa toprak uygunluğu.
Sıra, projenin geometrik ortalama ilkesinin aynısı: bir koşul diğerinin
yerini tutmaz. Toprağı sulayabilirsin, kışı değiştiremezsin.

NE SÖYLEMEZ — bilerek
Bu modül "yetişir" dese bile VERİM, KÂRLILIK ve PAZAR hakkında hiçbir
şey söylemez. Cevap "iklim ve toprak izin veriyor mu, vermiyorsa
darboğaz ne" ile sınırlıdır. Bir ürünün yetişebilir olması, ekilmesi
gerektiği anlamına gelmez.

DOĞRULAMA — ayırt edicilik testi
Bu projede "yüzde kaç doğruluk" diye bir sayı yoktur ve uydurulmayacak:
doğru ekim kararının etiketli gerçeği yok. Ama ölçülebilir bir şey var:
model, cevabını ÖNCEDEN BİLDİĞİMİZ vakaları ayırabiliyor mu?

    pozitif kontrol  Muş'ta FİİLEN yetişen meyveler (İl Tarım 2025
                     faaliyet raporu, Tablo 9) — model "olur" demeli
    negatif kontrol  Muş'ta yetişmeyen ve kışı atlatamayacak türler —
                     model "olmaz" demeli

Sonuç ayirt_edicilik() ile hesaplanır ve testle kilitlidir.

SINIR — kış minimumu ORTALAMA, uç değer değil
Kullanılan sayı, en soğuk ayın gece ortalamasıdır (mus_iklim'in sinüs
modeli). Muş'un kaydedilmiş MUTLAK minimumu bundan çok daha düşüktür.
Yani test GEVŞEK taraftadır: modelin reddettiği bir tür marjla
reddedilmiştir, ama sınıra yakın kabul ettiği bir tür güvende demek
değildir. Mutlak minimum istasyon verisi geldiğinde bu eşik sertleşir.
"""

from __future__ import annotations

from typing import Any

import mus_iklim
import mus_profil as mp

# --------------------------------------------------------------- kaynaklar
KAYNAK_KIS = ("Ankara Üniversitesi açık ders materyali — meyve türlerinin "
              "kış donlarına dayanımı")
KAYNAK_VARLIK = ("Muş İl Tarım ve Orman Müdürlüğü 2025 faaliyet raporu, "
                 "Tablo 9 (meyve) ve Tablo 8 (tarla bitkileri), 2024 yılı")

# Tür: (dinlenme dönemi dayanım sıcaklığı °C, kaynaktaki ifade)
# Sayılar yukarıdaki açık ders materyalinden alındı; BİRİ BİLE
# uydurulmadı. Kaynakta geçmeyen tür bu listeye girmez.
KIS_DAYANIMI: dict[str, tuple[float, str]] = {
    "Elma":     (-35.0, "gövde ve ana dallar -35 ile -40 °C; bir yaşlı "
                        "dallar -20 °C"),
    "Armut":    (-25.0, "gövde ve yaşlı dallar -25 ile -30 °C"),
    "Ceviz":    (-25.0, "-25 °C'ye kadar"),
    "Üzüm":     (-16.0, "subtropikte -16 °C'de zarar; serin bölgede "
                        "-24 °C'ye dayanan çeşitler var"),
    "Kayısı":   (-20.0, "gövde -20 ile -25 °C"),
    "Badem":    (-18.0, "kışın -18 °C'de tomurcuklarda zarar"),
    "Nar":      (-10.0, "yıllık dallar -10 °C; iki ve daha yaşlı dallar "
                        "-15 °C"),
    "İncir":     (-9.0, "-9 °C'nin altı ekonomik üretimi engeller; "
                        "-13 ile -14 °C'de toprak üstü organlar donar"),
    "Zeytin":    (-7.0, "kış donlarına -7 °C'ye kadar dayanıklı; -4 ile "
                        "-5 °C'nin altına sık düşen yerde riskli"),
    "Portakal":  (-5.0, "-5 °C'de zarar görür"),
    "Limon":     (-3.5, "-3,5 °C'de zarar görür"),
    "Muz":        (0.0, "0 °C'de zarar başlar; -1,5 ile -2 °C'de toprak "
                        "üstü donar"),
}

# Muş'ta FİİLEN yetişenler — İl Müdürlüğü'nün kendi kaydı.
# Bu küme testin pozitif kontrolüdür ve modele sorulmadan bilinir.
MUSTA_YETISEN: dict[str, str] = {
    "Üzüm": "5.600 dekar, 6.040 ton (2024)",
    "Ceviz": "4.860 dekar, 860 ton (2024)",
    "Elma": "4.511 dekar, 1.624 ton (2024)",
    "Armut": "1.441 dekar, 679 ton (2024)",
}


def kis_minimum(ilce: str) -> float:
    """En soğuk ayın gece ortalaması (°C).

    mus_iklim'in sıcaklık serisi OKUNUR, yeniden hesaplanmaz: aynı
    formülün ikinci kopyası bakım borcudur ve projede bir kez bu yüzden
    iki modül birbirinden ayrı düşmüştü.
    """
    return round(min(mus_iklim.aylik_sicaklik(ilce)) - mus_iklim.GUNLUK_FARK, 1)


def _toprak_bakisi(urun: str, ilce: str) -> dict[str, Any] | None:
    """Toprak isteği kayıtlıysa toprak uygunluğu; değilse None.

    Kayıt yoksa TAHMİN ÜRETİLMEZ; cevapta "toprak isteği kayıtlı değil"
    yazar. Eksik veriyi doldurmak, cevabı uydurmaktır.
    """
    import mus_toprak as mt
    import toprak_profil as tpf

    istek = tpf.URUN_ISTEK.get(urun)
    if istek is None:
        return None
    return mt.topraktan_uygunluk(mt.ilce_toprak(ilce), urun, istek)


def yetisir_mi(urun: str, ilce: str) -> dict[str, Any]:
    """Bir ürün bu ilçede yetişir mi — ve yetişmiyorsa darboğaz ne.

    Üç kapı sırayla: kış, sıcaklık toplamı, toprak. İlk kapı kapandıysa
    diğerlerine bakılmaz, çünkü biri diğerinin yerini tutmaz.
    """
    if ilce not in mp.ILCE:
        return {"var": False, "sebep": f"'{ilce}' Muş ilçesi değil"}

    kis = kis_minimum(ilce)
    dayanim = KIS_DAYANIMI.get(urun)
    iklim = mus_iklim.uygunluk(ilce, urun) if urun in mus_iklim.IKLIM_ISTEK \
        else None
    toprak = _toprak_bakisi(urun, ilce)

    # 1. KAPI — kış
    if dayanim is not None and dayanim[0] > kis:
        return {
            "var": True, "urun": urun, "ilce": ilce, "karar": "yetişmez",
            "darbogaz": "kış soğuğu",
            "gerekce": (f"{urun} dinlenme döneminde {_c(dayanim[0])} °C'ye "
                        f"kadar dayanıyor ({dayanim[1]}). {ilce}'de en soğuk "
                        f"ayın gece ortalaması {_c(kis)} °C — türün sınırının "
                        "altında. Kışı atlatamayan bir ağaç için toprağın ne "
                        "dediğinin önemi yok."),
            "kis_minimum": kis, "kis_dayanimi": dayanim[0],
            "iklim": iklim, "toprak": toprak,
            "sinir": SINIR_KIS,
        }

    # 2. KAPI — sıcaklık toplamı ve donsuz dönem
    if iklim is None:
        return {
            "var": True, "urun": urun, "ilce": ilce, "karar": "söylenemez",
            "darbogaz": "iklim isteği kayıtlı değil",
            "gerekce": (f"{urun} kışı {ilce}'de atlatır" if dayanim else
                        f"{urun} için kış dayanımı kaydı yok") +
                       ", ama sıcaklık toplamı ve donsuz gün isteği "
                       "kayıtlı olmadığı için yetişip yetişmeyeceği "
                       "SÖYLENEMEZ. Eksik olan Muş verisi değil, ürünün "
                       "kendi isteği.",
            "kis_minimum": kis,
            "kis_dayanimi": dayanim[0] if dayanim else None,
            "iklim": None, "toprak": toprak, "sinir": SINIR_KIS,
        }

    if iklim["puan"] < 50:
        return {
            "var": True, "urun": urun, "ilce": ilce, "karar": "yetişmez",
            "darbogaz": "sıcaklık", "gerekce":
                (f"{ilce}'de iklim puanı {iklim['puan']} ({iklim['sinif']}); "
                 f"kısıt: {iklim['kisit']}. Gerekli GDD {iklim['gerekli_gdd']}, "
                 f"mevcut {iklim['gdd']}."),
            "kis_minimum": kis,
            "kis_dayanimi": dayanim[0] if dayanim else None,
            "iklim": iklim, "toprak": toprak, "sinir": SINIR_KIS,
        }

    # 3. KAPI — toprak
    if toprak is None:
        karar, darbogaz = "iklim uygun, toprak bilinmiyor", "toprak isteği yok"
        gerekce = (f"İklim izin veriyor (puan {iklim['puan']}). Toprak "
                   "isteği kayıtlı olmadığı için toprak tarafı "
                   "değerlendirilmedi.")
    else:
        bir = mus_toprak_birlesik(toprak["puan"], iklim["puan"])
        karar = ("yetişir" if bir >= 65 else
                 "sınırda" if bir >= 50 else "yetişmez")
        darbogaz = ("iklim" if iklim["puan"] < toprak["puan"] - 5 else
                    "toprak" if toprak["puan"] < iklim["puan"] - 5 else
                    "dengeli")
        gerekce = (f"Toprak {toprak['puan']}, iklim {iklim['puan']}; "
                   f"geometrik ortalama {bir}. Darboğaz: {darbogaz}"
                   + (f" ({toprak['kisitlayici']})"
                      if darbogaz == "toprak" and toprak.get("kisitlayici")
                      else f" ({iklim['kisit']})"
                      if darbogaz == "iklim" else "") + ".")
        return {
            "var": True, "urun": urun, "ilce": ilce, "karar": karar,
            "darbogaz": darbogaz, "gerekce": gerekce, "birlesik": bir,
            "kis_minimum": kis,
            "kis_dayanimi": dayanim[0] if dayanim else None,
            "iklim": iklim, "toprak": toprak, "sinir": SINIR_KIS,
        }

    return {
        "var": True, "urun": urun, "ilce": ilce, "karar": karar,
        "darbogaz": darbogaz, "gerekce": gerekce,
        "kis_minimum": kis,
        "kis_dayanimi": dayanim[0] if dayanim else None,
        "iklim": iklim, "toprak": toprak, "sinir": SINIR_KIS,
    }


SINIR_KIS = ("Kış minimumu, en soğuk ayın GECE ORTALAMASIDIR; Muş'un "
             "kaydedilmiş mutlak minimumu daha düşüktür. Test bu yüzden "
             "gevşek taraftadır: reddedilen tür marjla reddedilmiştir, "
             "sınıra yakın kabul edilen tür güvende demek değildir.")


def mus_toprak_birlesik(toprak_puan: float, iklim_puan: float) -> float:
    """Birleştirme formülü tek yerde: mus_toprak.birlesik_puan."""
    import mus_toprak as mt
    return mt.birlesik_puan(toprak_puan, iklim_puan)


def _c(x: float) -> str:
    """Türkçe ondalık."""
    return f"{x:.1f}".replace(".", ",").replace(",0", "")


# ------------------------------------------------- ayırt edicilik testi
# Muş'ta yetişmeyen ve kaynakta kış dayanımı bulunan türler. "Yetişmiyor"
# bilgisi İl Müdürlüğü raporunun meyve tablosunda YER ALMAMASINDAN
# geliyor; tablo Muş'un meyve üretiminin tamamını veriyor.
MUSTA_YOK: tuple[str, ...] = ("Zeytin", "İncir", "Nar", "Portakal",
                              "Limon", "Muz")

# Kışı atlatan ama Muş'ta yine de yetişmeyen türler. Model bunları
# REDDEDEMİYOR ve bu bir başarısızlık değil, BİLİNEN BİR AÇIK: ikisi de
# çok erken çiçeklenir ve Muş'ta asıl engel ilkbahar geç donudur —
# modelde çiçeklenme dönemi don riski YOK.
CICEK_DONU_ACIGI: tuple[str, ...] = ("Kayısı", "Badem")


def ayirt_edicilik(ilce: str = "Merkez") -> dict[str, Any]:
    """Model, cevabını önceden bildiğimiz vakaları ayırabiliyor mu.

    Bu bir "doğruluk oranı" DEĞİLDİR ve öyle sunulmamalıdır: doğru ekim
    kararının etiketli gerçeği yok. Ölçülen şey dar ama gerçek — kış
    kapısı, Muş'ta yetişenle yetişmeyeni ayırıyor mu.
    """
    dogru_ret, yanlis_ret, cekimser = [], [], []

    for urun in MUSTA_YOK:
        d = yetisir_mi(urun, ilce)
        (dogru_ret if d["karar"] == "yetişmez" else yanlis_ret).append(
            {"urun": urun, "karar": d["karar"], "darbogaz": d["darbogaz"]})

    yanlis_elenen, gecen = [], []
    for urun in MUSTA_YETISEN:
        d = yetisir_mi(urun, ilce)
        (yanlis_elenen if d["karar"] == "yetişmez" else gecen).append(
            {"urun": urun, "karar": d["karar"], "kayit": MUSTA_YETISEN[urun]})

    for urun in CICEK_DONU_ACIGI:
        d = yetisir_mi(urun, ilce)
        cekimser.append({"urun": urun, "karar": d["karar"]})

    return {
        "ilce": ilce,
        "kis_minimum": kis_minimum(ilce),
        "dogru_ret": dogru_ret,
        "yanlis_ret": yanlis_ret,
        "gecen_pozitif": gecen,
        "yanlis_elenen": yanlis_elenen,
        "cekimser": cekimser,
        "sonuc": (f"{len(dogru_ret)}/{len(MUSTA_YOK)} doğru ret, "
                  f"{len(yanlis_elenen)}/{len(MUSTA_YETISEN)} yanlış eleme"),
        "yorum": (
            "Muş'ta yetişmeyen ve kaynakta kış dayanımı bulunan "
            f"{len(MUSTA_YOK)} türün {len(dogru_ret)} tanesi kış kapısında "
            f"elendi. Muş'ta fiilen yetişen {len(MUSTA_YETISEN)} meyvenin "
            f"{len(yanlis_elenen)} tanesi yanlışlıkla elendi. Yani kış "
            "kapısı iki grubu ayırıyor.\n"
            "AMA BU BİR DOĞRULUK ORANI DEĞİL. Ölçülen tek şey kış "
            "kapısıdır. Yetişen dört meyve için model 'yetişir' de "
            "DEMİYOR: sıcaklık toplamı istekleri kayıtlı olmadığı için "
            "'söylenemez' diyor. Uydurulmadı.\n"
            "AÇIK: kayısı ve badem kışı atlatıyor ve model onları "
            "reddedemiyor; oysa Muş'ta yetişmiyorlar. Sebep modelde "
            "bulunmayan bir mekanizma — ikisi de çok erken çiçeklenir ve "
            "asıl engel İLKBAHAR GEÇ DONUDUR. Bu testin bulduğu gerçek "
            "eksik budur."),
        "kaynak_kis": KAYNAK_KIS,
        "kaynak_varlik": KAYNAK_VARLIK,
        "sinir": SINIR_KIS,
    }


def panel_verisi() -> dict[str, Any]:
    """Panelin "Yeni ürün" sekmesinin okuduğu veri."""
    sorulabilir = sorted(set(KIS_DAYANIMI))
    return {
        "var": True,
        "kis_minimum": {i: kis_minimum(i) for i in mp.ILCE},
        "urunler": [
            {"urun": u, "dayanim": KIS_DAYANIMI[u][0],
             "ifade": KIS_DAYANIMI[u][1],
             "musta": MUSTA_YETISEN.get(u),
             "ilceler": {i: {k: v for k, v in yetisir_mi(u, i).items()
                             if k in ("karar", "darbogaz", "gerekce")}
                         for i in mp.ILCE}}
            for u in sorulabilir],
        "ayirt_edicilik": ayirt_edicilik(),
        "kaynaklar": {"kis": KAYNAK_KIS, "varlik": KAYNAK_VARLIK},
        "sinir": SINIR_KIS,
    }


def uret() -> dict[str, Any]:
    import json
    from pathlib import Path
    veri = panel_verisi()
    cikti = Path(__file__).resolve().parent.parent / "outputs"
    cikti.mkdir(exist_ok=True)
    (cikti / "yeni_urun.json").write_text(
        json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    return veri


def main() -> None:
    a = uret()["ayirt_edicilik"]
    print(f"Kış minimumu (Merkez): {a['kis_minimum']} °C\n")
    print("DOĞRU RET:", ", ".join(x["urun"] for x in a["dogru_ret"]))
    print("GEÇEN (Muş'ta yetişen):",
          ", ".join(f"{x['urun']} [{x['karar']}]" for x in a["gecen_pozitif"]))
    print("ÇEKİMSER:", ", ".join(f"{x['urun']} [{x['karar']}]"
                                 for x in a["cekimser"]))
    print("\n" + a["sonuc"] + "\n")
    print(a["yorum"])
