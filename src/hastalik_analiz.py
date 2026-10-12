"""
AGROMATCH - Hastalık risk analizi ve görüntü işleme hattı
=========================================================
İki ayrı iş yapar:

  1. İKLİME DAYALI RİSK (bugün çalışıyor)
     Her il-ürün-hastalık üçlüsü için, ilin sıcaklık ve yağış profili hastalığın
     gelişme koşullarına ne kadar uyuyor? Çıktı: 0-100 risk skoru, risk sınıfı ve
     ilaçlama penceresi. Bu, panelde doğrudan gösterilebilen kural tabanlı katmandır.

  2. GÖRÜNTÜDEN TESPİT (eğitilecek model)
     Hangi hastalık yaprak görüntüsünden tanınabilir, hangisi tanınamaz (toprak
     kaynaklı solgunluklar ve tohum hastalıkları görüntüden tespit edilemez).
     PlantVillage sınıf eşleşmesi burada tutulur; model eğitildiğinde metrikler
     bu dosyanın çıktısına eklenir.

Çıktı: outputs/hastalik.json
"""

import json
import math
from pathlib import Path

from bolge_profil import DESEN, ILLER
from hastalik_profil import HASTALIKLAR, PV_ONCELIK, SICAKLIK
from kaynak_profil import YAGIS

CIKTI = Path(__file__).resolve().parent.parent / "outputs"

AY_ADI = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


# Yıllık sıcaklık genliği: karasal iklimde yaz-kış farkı büyüktür.
# Temmuz en sıcak, ocak en soğuk ay kabul edilir.
GENLIK = {"Doğu Anadolu": 13.0, "Güneydoğu Anadolu": 12.0}


def ay_sicakligi(yillik_ortalama, bolge, ay):
    """Ayın ortalama sıcaklığını basit bir mevsim eğrisiyle tahmin eder.

    Yıllık ortalamayı doğrudan kullanmak yaz hastalıklarının riskini sistematik
    olarak düşürür (Muş'un yıllık ortalaması 9,8 °C'dir ama temmuz ortalaması
    bunun çok üstündedir). Gerçek aylık veri Open-Meteo'dan çekildiğinde bu
    tahmin yerine ölçüm kullanılacaktır.
    """
    return yillik_ortalama + GENLIK[bolge] * math.cos(2 * math.pi * (ay - 7) / 12)


def sicaklik_uygunlugu(yillik_ortalama, bolge, kritik_aylar, aralik):
    """Hastalığın kritik aylarındaki sıcaklık, optimum aralığına ne kadar yakın?"""
    alt, ust = aralik
    puanlar = []
    for ay in kritik_aylar:
        t = ay_sicakligi(yillik_ortalama, bolge, ay)
        if alt <= t <= ust:
            puanlar.append(1.0)
        else:
            uzaklik = alt - t if t < alt else t - ust
            puanlar.append(max(0.0, 1 - uzaklik / 8.0))
    return sum(puanlar) / len(puanlar) if puanlar else 0.0


def nem_uygunlugu(il_yagis, esik):
    return max(0.15, min(1.0, il_yagis / esik))


def analiz():
    iller = []
    hastalik_ozet = {h["ad"] + " · " + h["urun"]: dict(
        ad=h["ad"], urun=h["urun"], patojen=h["patojen"], tip=h["tip"],
        goruntuden=h["goruntuden"], pv_sinif=h["pv_sinif"],
        yuksek_riskli_il=[], ortalama_risk=[]) for h in HASTALIKLAR}

    for il, (bolge, *_rest) in ILLER.items():
        sicaklik, yagis = SICAKLIK[il], YAGIS[il]
        ekili = set(DESEN[il].keys())
        toplam_alan = sum(a for a, _v, _t in DESEN[il].values()) or 1
        kayitlar = []

        for h in HASTALIKLAR:
            if h["urun"] not in ekili:
                continue
            s = sicaklik_uygunlugu(sicaklik, bolge, h["kritik_aylar"], h["sicaklik_opt"])
            n = nem_uygunlugu(yagis, h["nem_esik"])
            # Ekim yoğunluğu: aynı ürün ne kadar geniş alanda ekilirse hastalık
            # baskısı (inokulum kaynağı ve yayılma hızı) o kadar artar.
            pay = DESEN[il][h["urun"]][0] / toplam_alan
            yogunluk = min(1.0, pay / 0.40)
            risk = round(100 * s * n * (0.65 + 0.35 * yogunluk))
            sinif = "yüksek" if risk >= 65 else "orta" if risk >= 40 else "düşük"
            kayitlar.append(dict(
                urun=h["urun"], ad=h["ad"], patojen=h["patojen"], tip=h["tip"],
                risk=risk, sinif=sinif,
                sicaklik_uyum=round(s, 2), nem_uyum=round(n, 2),
                kritik_ay_sicakligi=round(sum(ay_sicakligi(sicaklik, bolge, a)
                                              for a in h["kritik_aylar"])
                                          / len(h["kritik_aylar"]), 1),
                ekim_yogunlugu=round(yogunluk, 2),
                kritik_aylar=h["kritik_aylar"],
                ilaclama_penceresi=" – ".join(AY_ADI[a] for a in
                                              (h["kritik_aylar"][0], h["kritik_aylar"][-1])),
                belirti=h["belirti"], yonetim=h["yonetim"],
                goruntuden=h["goruntuden"], pv_sinif=h["pv_sinif"]))

            anahtar = h["ad"] + " · " + h["urun"]
            hastalik_ozet[anahtar]["ortalama_risk"].append(risk)
            if sinif == "yüksek":
                hastalik_ozet[anahtar]["yuksek_riskli_il"].append(il)

        kayitlar.sort(key=lambda r: -r["risk"])
        yuksek = [k for k in kayitlar if k["sinif"] == "yüksek"]

        # Aylık risk takvimi: her ay için o ayda kritik olan hastalıkların en yüksek riski
        takvim = []
        for ay in range(1, 13):
            o_ay = [k["risk"] for k in kayitlar if ay in k["kritik_aylar"]]
            takvim.append(dict(ay=ay, ad=AY_ADI[ay],
                               risk=max(o_ay) if o_ay else 0,
                               hastalik_sayisi=len(o_ay)))

        iller.append(dict(
            il=il, bolge=bolge, sicaklik=sicaklik, yagis=yagis,
            hastaliklar=kayitlar, takvim=takvim,
            yuksek_risk_sayisi=len(yuksek),
            en_riskli=kayitlar[0] if kayitlar else None,
            ortalama_risk=round(sum(k["risk"] for k in kayitlar) / max(len(kayitlar), 1)),
        ))

    iller.sort(key=lambda r: (r["bolge"], r["il"]))

    for v in hastalik_ozet.values():
        v["ortalama_risk"] = (round(sum(v["ortalama_risk"]) / len(v["ortalama_risk"]))
                              if v["ortalama_risk"] else 0)

    ozet_liste = sorted(hastalik_ozet.values(), key=lambda v: -v["ortalama_risk"])
    goruntuden = [h for h in HASTALIKLAR if h["goruntuden"]]
    pv_var = [h for h in HASTALIKLAR if h["pv_sinif"]]

    sonuc = dict(
        iller=iller,
        hastalik_ozet=ozet_liste,
        goruntu_hatti=dict(
            toplam_hastalik=len(HASTALIKLAR),
            goruntuden_tespit=len(goruntuden),
            veri_seti_karsiligi=len(pv_var),
            oncelikli_siniflar=PV_ONCELIK,
            adimlar=[
                dict(ad="Veri seti", aciklama="PlantVillage'dan bölge ürünlerine ait sınıflar "
                     "seçilir; sınıf dengesizliği envanterle ölçülür.",
                     cikti="data/goruntu_bolunmus/"),
                dict(ad="Ön işleme", aciklama="224×224 yeniden boyutlandırma, normalizasyon; "
                     "döndürme, yatay çevirme ve parlaklık değişimiyle veri artırma.",
                     cikti="tf.data / torch DataLoader"),
                dict(ad="Model", aciklama="Transfer öğrenme: ImageNet ağırlıklı MobileNetV2 "
                     "ya da ResNet50; son katman sınıf sayısına göre yeniden eğitilir.",
                     cikti="model.keras / model.pt"),
                dict(ad="Değerlendirme", aciklama="Doğruluk, kesinlik, duyarlılık, F1 ve "
                     "karmaşıklık matrisi; sınıf bazında hata analizi.",
                     cikti="outputs/model_metrik.json"),
                dict(ad="Açıklanabilirlik", aciklama="Grad-CAM ısı haritasıyla modelin yaprağın "
                     "neresine baktığı gösterilir — ziraat mühendisi için güven unsuru.",
                     cikti="ısı haritası görselleri"),
                dict(ad="Entegrasyon", aciklama="Model çıktısı, ilin iklime dayalı risk skoruyla "
                     "birleştirilir: görüntü teyidi + bölgesel risk = erken uyarı.",
                     cikti="panel"),
            ],
            hedef_metrikler=dict(dogruluk="≥ %92", f1="≥ 0.90",
                                 not_="PlantVillage laboratuvar koşullarında çekilmiş "
                                      "görüntülerden oluşur; saha fotoğraflarında başarı düşer. "
                                      "Raporda bu sınırlılık mutlaka tartışılmalıdır."),
        ),
        ozet=dict(
            il_sayisi=len(iller),
            izlenen_hastalik=len(HASTALIKLAR),
            yuksek_riskli_cift=sum(r["yuksek_risk_sayisi"] for r in iller),
            en_riskli_hastalik=ozet_liste[0]["ad"] if ozet_liste else None,
        ),
    )
    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "hastalik.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    return sonuc


if __name__ == "__main__":
    s = analiz()
    o = s["ozet"]
    print(f"{o['izlenen_hastalik']} hastalık, {o['il_sayisi']} il, "
          f"{o['yuksek_riskli_cift']} yüksek riskli il-hastalık çifti\n")
    print(f"{'HASTALIK':<26}{'ÜRÜN':<15}{'ORT. RİSK':>10}{'YÜKSEK RİSKLİ İL':>18}  GÖRÜNTÜDEN")
    for h in s["hastalik_ozet"][:12]:
        print(f"{h['ad']:<26}{h['urun']:<15}{h['ortalama_risk']:>10}"
              f"{len(h['yuksek_riskli_il']):>18}  {'evet' if h['goruntuden'] else 'hayır'}")
    print(f"\n{'İL':<12}{'ORT. RİSK':>10}{'YÜKSEK':>8}  EN RİSKLİ")
    for r in s["iller"][:8]:
        e = r["en_riskli"]
        print(f"{r['il']:<12}{r['ortalama_risk']:>10}{r['yuksek_risk_sayisi']:>8}  "
              f"{e['ad']} ({e['urun']}, {e['risk']})" if e else "-")
