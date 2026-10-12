"""
AGROMATCH - Senaryo verisi + harita konumları + veri künyesi
============================================================
Simülatör panelinin ihtiyaç duyduğu her şeyi tek dosyada toplar:

  * Her il için ürün bazında DEKAR BAŞINA katsayılar (su, elektrik, mazot, karbon,
    gelir). Alan aktarıldığında sonucu yeniden hesaplamak için gereken budur.
  * Kaba yem arzının bileşenleri (yem bitkileri + mera + anız), böylece tahıl alanı
    değiştiğinde anız katkısı da doğru şekilde güncellenir.
  * Karne puanının yeniden hesaplanması için ürün bazlı bölge ortalamaları ve ağırlıklar.
  * 23 ilin altıgen harita konumu (gerçek koordinatlardan üretilir).
  * Veri künyesi ve duyarlılık analizi tanımları.

Çıktı: outputs/senaryo.json
"""

import json
from pathlib import Path

from bolge_analiz import TR_DURUM, il_ihtiyaci
from bolge_profil import ANIZ_VERIM, DESEN, ILLER, MERA, MERA_VERIM, TIP_KABA_YEM, URUN_TIPI
from ekonomi_profil import DUYARLILIK, EKONOMI, KUNYE
from il_karne import AGIRLIK, HEDEF_URUN_CESIDI
from kaynak_profil import KAYNAK, YAGIS

CIKTI = Path(__file__).resolve().parent.parent / "outputs"

ANIZ_URUNLERI = ("Buğday", "Arpa", "Mercimek", "Mısır (dane)")

# İl merkezlerinin yaklaşık coğrafi koordinatları (enlem, boylam)
KOORDINAT = {
    "Ardahan": (41.11, 42.70), "Kars": (40.60, 43.10), "Iğdır": (39.92, 44.04),
    "Ağrı": (39.72, 43.05), "Erzurum": (39.90, 41.27), "Erzincan": (39.75, 39.49),
    "Tunceli": (39.11, 39.55), "Bingöl": (38.89, 40.50), "Muş": (38.75, 41.49),
    "Van": (38.49, 43.38), "Bitlis": (38.40, 42.11), "Hakkari": (37.58, 43.74),
    "Malatya": (38.36, 38.31), "Elazığ": (38.68, 39.22),
    "Adıyaman": (37.76, 38.28), "Şanlıurfa": (37.16, 38.80), "Gaziantep": (37.07, 37.38),
    "Kilis": (36.72, 37.12), "Diyarbakır": (37.91, 40.24), "Mardin": (37.31, 40.74),
    "Batman": (37.88, 41.13), "Siirt": (37.93, 41.94), "Şırnak": (37.52, 42.46),
}


def harita_konumlari():
    """Gerçek koordinatları çakışmasız bir altıgen ızgaraya yerleştirir.

    Gerçek il sınırları yerine altıgen kutucuk haritası kullanılır: sınır verisi
    gerektirmez ve küçük illerin görünmeme sorununu ortadan kaldırır.
    """
    ham = {il: (round((lon - 36.9) / 0.62), round((41.35 - lat) / 0.50))
           for il, (lat, lon) in KOORDINAT.items()}
    yerlesim, dolu = {}, set()
    # Kuzeyden güneye, batıdan doğuya sırayla yerleştir; çakışanı en yakın boş göze kaydır
    for il in sorted(ham, key=lambda k: (ham[k][1], ham[k][0])):
        q, r = ham[il]
        if (q, r) not in dolu:
            yerlesim[il] = (q, r); dolu.add((q, r)); continue
        for mesafe in range(1, 6):
            aday = [(q + dq, r + dr) for dq in range(-mesafe, mesafe + 1)
                    for dr in range(-mesafe, mesafe + 1)
                    if max(abs(dq), abs(dr)) == mesafe and (q + dq, r + dr) not in dolu]
            if aday:
                aday.sort(key=lambda p: (abs(p[1] - r), abs(p[0] - q)))
                yerlesim[il] = aday[0]; dolu.add(aday[0]); break
    q0 = min(q for q, _ in yerlesim.values())
    r0 = min(r for _, r in yerlesim.values())
    return {il: dict(q=q - q0, r=r - r0) for il, (q, r) in yerlesim.items()}


def uret():
    urun_veri = json.loads((CIKTI / "urun.json").read_text(encoding="utf-8"))
    karne = json.loads((CIKTI / "karne.json").read_text(encoding="utf-8"))

    kaynak = {(r["il"], u["urun"]): r for u in urun_veri["urunler"] for r in u["iller"]}
    karne_il = {r["il"]: r for r in karne["iller"]}

    # Ürün bazlı bölge ortalaması (su endeksinin yeniden hesabı için)
    urun_ort = {}
    for u in urun_veri["urunler"]:
        d = [r["mavi_su_ton_basi"] for r in u["iller"]]
        urun_ort[u["urun"]] = round(sum(d) / len(d), 1)

    iller = []
    for il, (bolge, nufus, buyukbas, kucukbas) in ILLER.items():
        urunler = []
        for urun, (alan, verim, talep) in DESEN[il].items():
            k = kaynak[(il, urun)]
            fiyat, maliyet, destek = EKONOMI[urun]
            a = max(alan, 1)
            urunler.append(dict(
                urun=urun, tip=URUN_TIPI[urun], tr_durum=TR_DURUM[urun],
                alan_dekar=alan, verim=verim,
                ihtiyac_ton=round(il_ihtiyaci(il, urun, talep)),
                fiyat_tl_ton=fiyat, maliyet_tl_dekar=maliyet, destek_tl_dekar=destek,
                gelir_tl_dekar=round(verim * fiyat - maliyet + destek),
                # dekar başına kaynak katsayıları
                mavi_su_da=round(k["mavi_su_m3"] / a, 2),
                yesil_su_da=round(k["yesil_su_m3"] / a, 2),
                elektrik_da=round(k["elektrik_kwh"] / a, 2),
                mazot_da=round(k["mazot_lt"] / a, 2),
                gubre_da=round(k["gubre_kg"] / a, 2),
                karbon_da=round(k["karbon_kg"] / a, 2),
                mavi_su_ton_basi=k["mavi_su_ton_basi"],
                sulama_orani=KAYNAK[urun][3],
                aniz=urun in ANIZ_URUNLERI))

        yem = next((u for u in urunler if u["tip"] == TIP_KABA_YEM), None)
        iller.append(dict(
            il=il, bolge=bolge, nufus=nufus, buyukbas=buyukbas, kucukbas=kucukbas,
            hayvan_birimi=karne_il[il]["hayvan_birimi"],
            yem_ihtiyac_ton=karne_il[il]["kaba_yem_ihtiyac_ton"],
            mera_ton=round(MERA.get(il, 0) * MERA_VERIM),
            aniz_verim=ANIZ_VERIM,
            yem_urunu=yem["urun"] if yem else None,
            yem_verim=yem["verim"] if yem else 0.65,
            yem_mavi_su_da=yem["mavi_su_da"] if yem else 0,
            yem_elektrik_da=yem["elektrik_da"] if yem else 0,
            yem_mazot_da=yem["mazot_da"] if yem else 0,
            yem_karbon_da=yem["karbon_da"] if yem else 0,
            yem_gelir_da=yem["gelir_tl_dekar"] if yem else 0,
            yagis_mm=YAGIS[il],
            urunler=urunler,
            mevcut=dict(harf=karne_il[il]["harf"], genel_puan=karne_il[il]["genel_puan"],
                        puan=karne_il[il]["puan"], su_endeksi=karne_il[il]["su_endeksi"],
                        etkin_urun=karne_il[il]["etkin_urun_sayisi"],
                        kaba_yem_orani=karne_il[il]["kaba_yem_orani"],
                        mavi_su_ton_basi=karne_il[il]["mavi_su_ton_basi"]),
        ))

    sonuc = dict(
        iller=iller,
        urun_ort_mavi_su=urun_ort,
        agirlik=AGIRLIK,
        hedef_urun_cesidi=HEDEF_URUN_CESIDI,
        harita=harita_konumlari(),
        kunye=[dict(girdi=a, yer=b, tur=c, kaynak=d, belirsizlik=e) for a, b, c, d, e in KUNYE],
        duyarlilik=[dict(ad=a, anahtar=b, oran=c, aciklama=d) for a, b, c, d in DUYARLILIK],
    )
    (CIKTI / "senaryo.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    return sonuc


if __name__ == "__main__":
    s = uret()
    print(f"{len(s['iller'])} il, {len(s['kunye'])} künye satırı, "
          f"{len(s['duyarlilik'])} duyarlılık katsayısı")
    en = max(v["q"] for v in s["harita"].values()) + 1
    boy = max(v["r"] for v in s["harita"].values()) + 1
    print(f"Harita ızgarası: {en} sütun x {boy} satır")
    for il, p in sorted(s["harita"].items(), key=lambda x: (x[1]["r"], x[1]["q"])):
        print(f"  {il:<11} q={p['q']:>2} r={p['r']:>2}")
    m = next(i for i in s["iller"] if i["il"] == "Muş")
    print("\nMuş ürün ekonomisi (TL/dekar net gelir):")
    for u in m["urunler"]:
        print(f"  {u['urun']:<15}{u['gelir_tl_dekar']:>8,} TL/da   "
              f"mavi su {u['mavi_su_da']:>7} m³/da   karbon {u['karbon_da']:>6} kg/da")
