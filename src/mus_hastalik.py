"""
AGROMATCH - Muş hastalık risk analizi (ilçe çözünürlüğünde)
===========================================================
Muş'ta ekilen dokuz ürünün ekonomik önemi olan hastalıkları, her ilçenin
aylık sıcaklık ve nem koşullarına göre puanlanır.

Risk üç çarpandan oluşur:

    risk = sıcaklık uygunluğu × nem uygunluğu × ekim yoğunluğu

  - sıcaklık: hastalığın KRİTİK AYLARINDAKİ ortalama sıcaklık, patojenin
    optimum aralığına ne kadar yakın. Yıllık ortalama kullanılsaydı bütün
    yaz hastalıkları sıfırlanırdı (Muş'un yıllık ortalaması 9,8 °C'dir ama
    temmuzu 23,6 °C'dir). Aylık sıcaklık mus_iklim'den gelir.
  - nem: yağış vekil değişken olarak kullanılır. Sulanan tarlada yaprak
    ıslaklığı yağıştan bağımsız da oluşur; bu yüzden sulanan oran risk
    tabanını yükseltir.
  - yoğunluk: aynı ürün ilçe ekim alanının büyük kısmını kaplıyorsa inokulum
    birikir ve epidemi hızlanır (monokültür etkisi).

DİKKAT: Eşikler fitopatoloji literatüründen alınan YAKLAŞIK değerlerdir.
Zirai Mücadele Teknik Talimatları ve Bitki Koruma bölümünün saha gözlemiyle
kesinleştirilecektir. Bu panel ilaçlama kararı değil, ÖNCELİK SIRASI üretir.

Çıktı: outputs/mus_hastalik.json

    python src/mus_hastalik.py
"""

import json
from pathlib import Path

import mus_iklim
import mus_profil as mp
from hastalik_profil import HASTALIKLAR as ORTAK

CIKTI = Path(__file__).resolve().parent.parent / "outputs"

# Ortak katalogdaki ürün adlarını Muş'un ürün setine eşle
ESLEME = {"Mısır (dane)": "Silajlık mısır", "Yem bitkileri": "Yonca"}

# Muş'un ürün setinde olup ortak katalogda bulunmayan hastalıklar
EK_HASTALIK = [
    # --- Yonca
    dict(urun="Yonca", ad="Yonca pası", patojen="Uromyces striatus", tip="mantar",
         sicaklik_opt=(18, 25), nem_esik=400, kritik_aylar=[6, 7, 8],
         belirti="Yaprak alt yüzünde kahverengi toz püstüller",
         yonetim="Erken biçim, dayanıklı çeşit", pv_sinif=None, goruntuden=True),
    dict(urun="Yonca", ad="Kök ve kök boğazı çürüklüğü", patojen="Fusarium spp.",
         tip="mantar", sicaklik_opt=(15, 25), nem_esik=350, kritik_aylar=[5, 6, 9],
         belirti="Bitkide solgunluk, kök kesitinde kahverengileşme",
         yonetim="Drenaj, tarla yaşını uzatmama, ekim nöbeti",
         pv_sinif=None, goruntuden=False),

    # --- Korunga
    dict(urun="Korunga", ad="Korunga külleme", patojen="Erysiphe trifolii",
         tip="mantar", sicaklik_opt=(16, 24), nem_esik=300, kritik_aylar=[5, 6, 7],
         belirti="Yaprak yüzeyinde beyaz unlu örtü",
         yonetim="Erken biçim, sık ekimden kaçınma", pv_sinif=None, goruntuden=True),

    # --- Fiğ
    dict(urun="Fiğ", ad="Fiğ antraknozu", patojen="Ascochyta spp.", tip="mantar",
         sicaklik_opt=(14, 22), nem_esik=420, kritik_aylar=[4, 5, 6],
         belirti="Gövde ve yaprakta koyu kenarlı çökük lekeler",
         yonetim="Temiz tohum, ekim nöbeti", pv_sinif=None, goruntuden=True),

    # --- Kuru fasulye
    dict(urun="Kuru fasulye", ad="Fasulye antraknozu",
         patojen="Colletotrichum lindemuthianum", tip="mantar",
         sicaklik_opt=(15, 22), nem_esik=400, kritik_aylar=[6, 7],
         belirti="Yaprak damarlarında ve baklada koyu çökük yaralar",
         yonetim="Sertifikalı tohum, ıslakken tarlaya girmeme",
         pv_sinif=None, goruntuden=True),
    dict(urun="Kuru fasulye", ad="Bakteriyel yanıklık",
         patojen="Xanthomonas axonopodis", tip="bakteri",
         sicaklik_opt=(20, 30), nem_esik=300, kritik_aylar=[6, 7, 8],
         belirti="Yaprakta sarı haleli kahverengi lekeler",
         yonetim="Temiz tohum, bakır uygulaması", pv_sinif=None, goruntuden=True),

    # --- Şeker pancarı (Muş için kritik ek)
    dict(urun="Şeker pancarı", ad="Kök çürüklüğü (Rhizoctonia)",
         patojen="Rhizoctonia solani", tip="mantar",
         sicaklik_opt=(20, 28), nem_esik=250, kritik_aylar=[6, 7, 8],
         belirti="Kökte siyah-kahverengi çürük, bitkide ani solma",
         yonetim="DRENAJ, ekim nöbeti, dayanıklı çeşit",
         pv_sinif=None, goruntuden=False),
    dict(urun="Şeker pancarı", ad="Külleme", patojen="Erysiphe betae",
         tip="mantar", sicaklik_opt=(20, 30), nem_esik=200, kritik_aylar=[7, 8],
         belirti="Yaprak yüzeyinde beyaz unlu tabaka",
         yonetim="Zamanında kükürt/fungisit", pv_sinif=None, goruntuden=True),

    # --- Buğday (Muş rakımında önemli)
    dict(urun="Buğday", ad="Kar küfü", patojen="Microdochium nivale", tip="mantar",
         sicaklik_opt=(0, 8), nem_esik=500, kritik_aylar=[2, 3],
         belirti="Kar eridikten sonra yatık, pembe-gri küflü yamalar",
         yonetim="Erken ekimden kaçınma, dengeli azot",
         pv_sinif=None, goruntuden=True),
]


def hastalik_listesi():
    """Muş'ta ekilen ürünlere ait hastalıkların tamamı."""
    urunler = set(mp.URUN)
    liste = []
    for h in ORTAK:
        urun = ESLEME.get(h["urun"], h["urun"])
        if urun in urunler:
            kayit = dict(h)
            kayit["urun"] = urun
            kayit["kaynak_urun"] = h["urun"]
            liste.append(kayit)
    liste.extend(dict(h, kaynak_urun=h["urun"]) for h in EK_HASTALIK)
    return liste


def sicaklik_uygunlugu(ilce, kritik_aylar, aralik):
    alt, ust = aralik
    aylik = mus_iklim.aylik_sicaklik(ilce)
    puanlar = []
    for ay in kritik_aylar:
        t = aylik[ay - 1]
        if alt <= t <= ust:
            puanlar.append(1.0)
        else:
            uzaklik = alt - t if t < alt else t - ust
            puanlar.append(max(0.0, 1 - uzaklik / 8.0))
    return sum(puanlar) / len(puanlar) if puanlar else 0.0


def nem_uygunlugu(ilce, esik, urun):
    """Yağış vekil değişken; sulanan üründe yaprak ıslaklığı tabanı yükseltir."""
    yagis = mp.IKLIM[ilce][1]
    taban = max(0.15, min(1.0, yagis / esik))
    kislik = mp.URUN[urun][9]
    sulama = mp.ILCE[ilce][5] * (0.35 if kislik else 1.0)
    return min(1.0, taban + sulama * 0.25)


def analiz():
    hastaliklar = hastalik_listesi()
    satirlar = []

    for ilce in mp.ILCE:
        desen = mp.DESEN[ilce]
        toplam_alan = sum(a for a, _ in desen.values())
        aylik = mus_iklim.aylik_sicaklik(ilce)

        for h in hastaliklar:
            urun = h["urun"]
            alan = desen.get(urun, (0, 0))[0]
            if alan <= 0:
                continue
            pay = alan / toplam_alan if toplam_alan else 0
            yogunluk = min(1.0, pay / 0.40)

            s = sicaklik_uygunlugu(ilce, h["kritik_aylar"], h["sicaklik_opt"])
            n = nem_uygunlugu(ilce, h["nem_esik"], urun)
            risk = round(100 * s * n * (0.65 + 0.35 * yogunluk))

            satirlar.append(dict(
                ilce=ilce, urun=urun, hastalik=h["ad"], patojen=h["patojen"],
                tip=h["tip"], risk=risk,
                sicaklik_uygunluk=round(s, 2), nem_uygunluk=round(n, 2),
                ekim_yogunlugu=round(yogunluk, 2),
                alan_dekar=alan, alan_payi=round(pay, 3),
                kritik_aylar=h["kritik_aylar"],
                kritik_ay_sicakligi=round(
                    sum(aylik[a - 1] for a in h["kritik_aylar"]) / len(h["kritik_aylar"]), 1),
                belirti=h["belirti"], yonetim=h["yonetim"],
                goruntuden=h["goruntuden"], pv_sinif=h.get("pv_sinif"),
                seviye=("yüksek" if risk >= 60 else "orta" if risk >= 35 else "düşük"),
            ))

    satirlar.sort(key=lambda r: -r["risk"])

    # Hastalık bazında il geneli özet: riskli alan ağırlıklı
    ozet = {}
    for r in satirlar:
        anahtar = f"{r['hastalik']} · {r['urun']}"
        o = ozet.setdefault(anahtar, dict(
            hastalik=r["hastalik"], urun=r["urun"], patojen=r["patojen"],
            tip=r["tip"], goruntuden=r["goruntuden"], pv_sinif=r["pv_sinif"],
            kritik_aylar=r["kritik_aylar"], belirti=r["belirti"],
            yonetim=r["yonetim"], ilce_sayisi=0, riskli_alan=0,
            toplam_alan=0, agirlikli=0.0))
        o["ilce_sayisi"] += 1
        o["toplam_alan"] += r["alan_dekar"]
        o["agirlikli"] += r["risk"] * r["alan_dekar"]
        if r["risk"] >= 60:
            o["riskli_alan"] += r["alan_dekar"]
    for o in ozet.values():
        o["ortalama_risk"] = round(o["agirlikli"] / o["toplam_alan"]) if o["toplam_alan"] else 0
        del o["agirlikli"]
    ozet = sorted(ozet.values(), key=lambda o: -(o["riskli_alan"] or o["ortalama_risk"]))

    # Aylık ilaçlama takvimi: hangi ayda hangi hastalık penceresi açık
    takvim = []
    for ay in range(1, 13):
        aktif = [o for o in ozet if ay in o["kritik_aylar"] and o["ortalama_risk"] >= 35]
        takvim.append(dict(
            ay=ay, ad=mus_iklim.AY_AD[ay - 1],
            sicaklik=round(sum(mus_iklim.aylik_sicaklik(i)[ay - 1]
                               for i in mp.ILCE) / len(mp.ILCE), 1),
            hastaliklar=[dict(ad=o["hastalik"], urun=o["urun"],
                              risk=o["ortalama_risk"], goruntuden=o["goruntuden"])
                         for o in sorted(aktif, key=lambda x: -x["ortalama_risk"])],
        ))

    # Görüntü işleme önceliği: riskli alanı büyük VE görüntüden tespit edilebilir
    goruntu_oncelik = [o for o in ozet if o["goruntuden"]][:8]

    # İlçe özeti
    ilce_ozet = []
    for ilce in mp.ILCE:
        kendi = [r for r in satirlar if r["ilce"] == ilce]
        yuksek = [r for r in kendi if r["risk"] >= 60]
        ilce_ozet.append(dict(
            ilce=ilce, hastalik_sayisi=len(kendi), yuksek_riskli=len(yuksek),
            en_riskli=[dict(ad=r["hastalik"], urun=r["urun"], risk=r["risk"])
                       for r in kendi[:3]],
            ortalama_risk=round(sum(r["risk"] for r in kendi) / len(kendi)) if kendi else 0,
        ))
    ilce_ozet.sort(key=lambda r: -r["ortalama_risk"])

    sonuc = dict(
        il="Muş", satirlar=satirlar, ozet=ozet, takvim=takvim,
        ilce_ozet=ilce_ozet, goruntu_oncelik=goruntu_oncelik,
        istatistik=dict(
            hastalik_sayisi=len(ozet),
            goruntuden_tespit=sum(1 for o in ozet if o["goruntuden"]),
            yuksek_riskli_kayit=sum(1 for r in satirlar if r["risk"] >= 60),
            en_riskli_ilce=ilce_ozet[0]["ilce"],
        ),
    )
    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "mus_hastalik.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    return sonuc


if __name__ == "__main__":
    s = analiz()
    i = s["istatistik"]
    print(f"{i['hastalik_sayisi']} hastalık · "
          f"{i['goruntuden_tespit']} tanesi görüntüden tespit edilebilir")
    print(f"Yüksek riskli ilçe-hastalık kaydı: {i['yuksek_riskli_kayit']}")
    print(f"En riskli ilçe: {i['en_riskli_ilce']}\n")

    print(f"{'HASTALIK':<30}{'ÜRÜN':<16}{'RİSK':>6}{'RİSKLİ ALAN':>13}  GÖRÜNTÜ")
    for o in s["ozet"][:12]:
        print(f"{o['hastalik']:<30}{o['urun']:<16}{o['ortalama_risk']:>6}"
              f"{o['riskli_alan']:>13,}  {'evet' if o['goruntuden'] else 'hayır'}"
              .replace(",", "."))

    print(f"\nİLAÇLAMA TAKVİMİ")
    for t in s["takvim"]:
        if t["hastaliklar"]:
            adlar = ", ".join(f"{h['ad']} ({h['risk']})" for h in t["hastaliklar"][:3])
            print(f"  {t['ad']}  {t['sicaklik']:>5.1f}°C  {adlar}")
