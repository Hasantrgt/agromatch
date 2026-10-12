"""
AGROMATCH - Muş toprak analizi (ilçe çözünürlüğünde)
====================================================
Üç soruyu ilçe bazında cevaplar:

  1. Bu ilçenin toprağı ne durumda?   -> toprak sağlığı karnesi
  2. Bu ürün bu ilçeye uyar mı?       -> uygunluk puanı ve kısıtlayıcı faktör
  3. Ne kadar gübre gerekir?          -> hedef verime göre N-P-K

Puanlayıcılar (ph_puan, tuz_puan, drenaj_puan ...) toprak_analiz.py'den
olduğu gibi alınır; burada sadece Muş'un ürün seti ve ilçe verisi vardır.
Böylece tek bir puanlama mantığı var, iki yerde bakım yapılmıyor.

Çıktı: outputs/mus_toprak.json

    python src/mus_toprak.py
"""

import json
import math
from pathlib import Path
from typing import Any

import mus_iklim
import mus_profil as mp
from toprak_analiz import (
    AGIRLIK,
    bunye_puan,
    derinlik_puan,
    drenaj_puan,
    kirec_puan,
    ph_puan,
    tuz_puan,
)
from toprak_profil import DRENAJ_PUAN, bunye_sinifi
from toprak_profil import URUN_ISTEK as ORTAK_ISTEK

CIKTI = Path(__file__).resolve().parent.parent / "outputs"

# Muş'a özgü ürünlerin toprak istekleri.
# N / P / K değerleri ÜRÜNÜN BİR TONU için kaldırdığı saf besin (kg).
EK_ISTEK: dict[str, dict[str, Any]] = {
    "Yonca": dict(
        ph_opt=(6.5, 8.0), ph_sinir=(6.0, 8.5), ec_esik=2.0, kirec_tol="yüksek",
        bunye="tınlı", om_hedef=2.0, N=28, P=6, K=25, azot_baglar=True,
        drenaj_hassas=5.0, kok_derinlik=200),
    "Korunga": dict(
        ph_opt=(6.5, 8.2), ph_sinir=(6.0, 8.6), ec_esik=3.0, kirec_tol="yüksek",
        bunye="kumlu-tın", om_hedef=1.5, N=24, P=5, K=18, azot_baglar=True,
        drenaj_hassas=4.5, kok_derinlik=150),
    "Silajlık mısır": dict(
        ph_opt=(5.8, 7.5), ph_sinir=(5.5, 8.0), ec_esik=1.7, kirec_tol="orta",
        bunye="tınlı", om_hedef=2.5, N=4.5, P=1.8, K=4.0, azot_baglar=False,
        drenaj_hassas=3.5, kok_derinlik=100),
    "Fiğ": dict(
        ph_opt=(6.0, 7.5), ph_sinir=(5.5, 8.2), ec_esik=3.0, kirec_tol="orta",
        bunye="tınlı", om_hedef=1.8, N=22, P=6, K=14, azot_baglar=True,
        drenaj_hassas=3.5, kok_derinlik=80),
    "Kuru fasulye": dict(
        ph_opt=(6.0, 7.5), ph_sinir=(5.5, 7.8), ec_esik=1.0, kirec_tol="düşük",
        bunye="kumlu-tın", om_hedef=2.2, N=45, P=9, K=20, azot_baglar=True,
        drenaj_hassas=5.0, kok_derinlik=60),
}

# Muş'ta yetişen dokuz ürünün tamamı
URUN_ISTEK: dict[str, dict[str, Any]] = {
    u: dict(ORTAK_ISTEK[u]) if u in ORTAK_ISTEK else EK_ISTEK[u]
    for u in mp.URUN}


def ilce_toprak(ilce: str) -> dict[str, Any]:
    ph, om, kirec, ec, kil, kum, silt, p, k, drenaj, erozyon, derinlik = mp.TOPRAK[ilce]
    return dict(ph=ph, om=om, kirec=kirec, ec=ec, kil=kil, kum=kum, silt=silt,
                p2o5=p, k2o=k, drenaj=drenaj, erozyon=erozyon, derinlik=derinlik)


# Liebig'in minimum yasası: bu üç özellik telafi edilemez.
# Toprak ne kadar iyi olursa olsun, kök bedrock'a çarpıyorsa ya da tarla
# su tutuyorsa ürün sınırlıdır. Ortalama bunu gizler, tavan gizlemez.
KRITIK = ("drenaj", "tuzluluk", "derinlik")


def uygunluk(ilce: str, urun: str) -> dict[str, Any]:
    t = ilce_toprak(ilce)
    istek = URUN_ISTEK[urun]
    sinif = bunye_sinifi(t["kil"], t["kum"], t["silt"])

    bilesen = dict(
        ph=round(ph_puan(t["ph"], istek), 1),
        tuzluluk=round(tuz_puan(t["ec"], istek["ec_esik"]), 1),
        kirec=round(kirec_puan(t["kirec"], istek["kirec_tol"]), 1),
        bunye=round(bunye_puan(sinif, istek["bunye"]), 1),
        drenaj=round(drenaj_puan(t["drenaj"], istek["drenaj_hassas"]), 1),
        organik=round(min(100.0, t["om"] / istek["om_hedef"] * 100), 1),
        derinlik=round(derinlik_puan(t["derinlik"], istek["kok_derinlik"]), 1),
    )
    ham = sum(bilesen[k] * AGIRLIK[k] for k in AGIRLIK)

    # Kritik bileşenlerin en düşüğü bir tavan koyar
    en_dusuk_kritik = min(bilesen[k] for k in KRITIK)
    tavan = 55 + 0.45 * en_dusuk_kritik
    puan = min(ham, tavan)
    tavanlandi = puan < ham - 0.05

    kisit = min(bilesen, key=lambda k: bilesen[k])
    etiket = ("çok uygun" if puan >= 80 else "uygun" if puan >= 65
              else "sınırlı" if puan >= 50 else "uygun değil")
    return dict(puan=round(puan, 1), ham_puan=round(ham, 1), sinif=etiket,
                bilesen=bilesen, kisitlayici=kisit, kisit_puani=bilesen[kisit],
                tavanlandi=tavanlandi,
                tavan_sebebi=(min(KRITIK, key=lambda k: bilesen[k])
                              if tavanlandi else None))


def gubre_onerisi(ilce: str, urun: str, verim: float) -> dict[str, Any]:
    t = ilce_toprak(ilce)
    istek = URUN_ISTEK[urun]
    ihtiyac_n = verim * istek["N"]
    ihtiyac_p = verim * istek["P"]
    ihtiyac_k = verim * istek["K"]

    # Soğuk ve kısa vejetasyonlu Muş'ta mineralizasyon yavaş: %1 OM ~ 1,2 kg N/da
    topraktan_n = t["om"] * 1.2
    if istek["azot_baglar"]:
        ihtiyac_n *= 0.3

    etkinlik_n, etkinlik_p, etkinlik_k = 0.65, 0.45, 0.75
    if t["kirec"] > 15:
        etkinlik_p = 0.35

    return dict(
        azot=round(max(0.0, ihtiyac_n - topraktan_n) / etkinlik_n, 1),
        fosfor=round(max(0.0, ihtiyac_p - t["p2o5"] * 0.5) / etkinlik_p, 1),
        potasyum=round(max(0.0, ihtiyac_k - t["k2o"] * 0.25) / etkinlik_k, 1),
        fosfor_etkinligi=etkinlik_p,
        topraktan_gelen_azot=round(topraktan_n, 1),
        organik_gubre_gerekli=bool(t["om"] < istek["om_hedef"] * 0.8),
    )


def toprak_sagligi(ilce: str) -> dict[str, Any]:
    t = ilce_toprak(ilce)
    b = dict(
        organik=round(min(100.0, t["om"] / 3.0 * 100), 1),
        tuzluluk=round(max(0.0, min(100.0, (4.0 - t["ec"]) / 3.5 * 100)), 1),
        erozyon=round((5 - t["erozyon"]) / 4 * 100, 1),
        drenaj=float(DRENAJ_PUAN[t["drenaj"]]),
        derinlik=round(min(100.0, t["derinlik"] / 90 * 100), 1),
        kirec=round(max(20.0, 100 - max(0, t["kirec"] - 10) * 3), 1),
    )
    ag = dict(organik=0.28, tuzluluk=0.22, erozyon=0.18, drenaj=0.14,
              derinlik=0.10, kirec=0.08)
    puan = sum(b[k] * ag[k] for k in ag)
    harf = "A" if puan >= 80 else "B" if puan >= 65 else "C" if puan >= 50 else "D"
    return dict(puan=round(puan), harf=harf, bilesen=b,
                zayif_halka=min(b, key=lambda k: b[k]))


def birlesik_puan(toprak_puan: float, iklim_puan: float) -> float:
    """Toprak ve iklimin geometrik ortalaması.

    Aritmetik ortalama kullanılsaydı iklimi 46 olan bir ilçe, toprağı 98
    olduğu için 72 alırdı ve 'uygun' görünürdü. Geometrik ortalama bunu
    engeller: iki koşuldan biri kötüyse sonuç kötüdür, çünkü biri diğerinin
    yerini tutmaz. Toprağı sulayabilirsin, iklimi değiştiremezsin.
    """
    return round(math.sqrt(max(0.0, toprak_puan) * max(0.0, iklim_puan)), 1)


def analiz() -> dict[str, Any]:
    ilceler: list[dict[str, Any]] = []
    for ilce in mp.ILCE:
        t = ilce_toprak(ilce)
        ekili = {u: v for u, (a, v) in mp.DESEN[ilce].items() if a > 0}

        urunler: list[dict[str, Any]] = []
        for urun in URUN_ISTEK:
            u = uygunluk(ilce, urun)
            ik = mus_iklim.uygunluk(ilce, urun)
            verim = ekili.get(urun)
            bir = birlesik_puan(u["puan"], ik["puan"])
            urunler.append(dict(
                urun=urun, ekili=urun in ekili, verim=verim,
                alan=mp.DESEN[ilce].get(urun, (0, 0))[0],
                gubre=gubre_onerisi(ilce, urun, verim) if verim else None,
                iklim=ik, birlesik=bir,
                birlesik_sinif=("çok uygun" if bir >= 80 else "uygun" if bir >= 65
                                else "sınırlı" if bir >= 50 else "uygun değil"),
                darbogaz=("iklim" if ik["puan"] < u["puan"] - 5
                          else "toprak" if u["puan"] < ik["puan"] - 5 else "dengeli"),
                **u))

        ekili_urunler = [u for u in urunler if u["ekili"]]
        agirlikli = sum(u["birlesik"] * u["alan"] for u in ekili_urunler)
        toplam_alan = sum(u["alan"] for u in ekili_urunler)
        sirali = sorted(urunler, key=lambda u: -u["birlesik"])

        ilceler.append(dict(
            ilce=ilce, toprak=t,
            bunye=bunye_sinifi(t["kil"], t["kum"], t["silt"]),
            saglik=toprak_sagligi(ilce),
            iklim=dict(rakim=mp.ILCE[ilce][0], ortalama=mp.IKLIM[ilce][0],
                       yagis=mp.IKLIM[ilce][1],
                       donsuz_gun=mus_iklim.donsuz_gun(ilce),
                       aylik=mus_iklim.aylik_sicaklik(ilce),
                       gdd5=mus_iklim.gdd(ilce, 5), gdd10=mus_iklim.gdd(ilce, 10)),
            not_=mp.ILCE_NOTU[ilce],
            urunler=sirali,
            ekili_ortalama=round(agirlikli / toplam_alan, 1) if toplam_alan else 0,
            sorunlu_ekimler=[u["urun"] for u in ekili_urunler if u["birlesik"] < 65],
            en_uygun=[u["urun"] for u in sirali[:3]],
        ))

    # Ürün bazında ilçe karşılaştırması: aynı ürün nerede daha rahat yetişir
    urun_karsilastirma: list[dict[str, Any]] = []
    for urun in URUN_ISTEK:
        # urun varsayılan argümanla bağlanıyor: yoksa kapanış döngü
        # değişkenini yakalar ve döngü ilerleyince yanlış ürüne bakar.
        def al(r: dict[str, Any], anahtar: str, urun: str = urun) -> Any:
            return next(u[anahtar] for u in r["urunler"] if u["urun"] == urun)
        satir: list[dict[str, Any]] = [dict(ilce=r["ilce"], puan=al(r, "birlesik"),
                      toprak=al(r, "puan"), iklim=al(r, "iklim")["puan"],
                      darbogaz=al(r, "darbogaz"),
                      kisit=al(r, "kisitlayici"), alan=al(r, "alan"))
                 for r in ilceler]
        satir.sort(key=lambda s: -s["puan"])
        urun_karsilastirma.append(dict(urun=urun, ilceler=satir,
                                       en_iyi=satir[0]["ilce"], en_kotu=satir[-1]["ilce"],
                                       makas=round(satir[0]["puan"] - satir[-1]["puan"], 1)))

    sonuc = dict(
        il="Muş", ilceler=ilceler, agirlik=AGIRLIK,
        urun_karsilastirma=urun_karsilastirma,
        urun_istek={k: {kk: (list(vv) if isinstance(vv, tuple) else vv)
                        for kk, vv in v.items()} for k, v in URUN_ISTEK.items()},
        ozet=dict(
            ortalama_om=round(sum(r["toprak"]["om"] for r in ilceler) / len(ilceler), 2),
            drenaj_sorunlu=[r["ilce"] for r in ilceler if r["toprak"]["drenaj"] == "zayıf"],
            yuksek_erozyon=[r["ilce"] for r in ilceler if r["toprak"]["erozyon"] >= 4],
            yuksek_kirec=[r["ilce"] for r in ilceler if r["toprak"]["kirec"] >= 12],
            sorunlu_ekim_sayisi=sum(len(r["sorunlu_ekimler"]) for r in ilceler),
        ),
    )
    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "mus_toprak.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    return sonuc


def ilce_puanlari(sonuc: dict[str, Any] | None = None) -> dict[str, float]:
    """mus_analiz.karne() için ilçe uyum puanı (ekili alana göre ağırlıklı)."""
    return {r["ilce"]: r["ekili_ortalama"] for r in (sonuc or analiz())["ilceler"]}


if __name__ == "__main__":
    s = analiz()
    o = s["ozet"]
    print(f"Ortalama organik madde: %{o['ortalama_om']}")
    print(f"Drenajı zayıf ilçeler: {', '.join(o['drenaj_sorunlu']) or '-'}")
    print(f"Yüksek erozyon: {', '.join(o['yuksek_erozyon']) or '-'}")
    print(f"Toprağa uymayan mevcut ekim: {o['sorunlu_ekim_sayisi']} adet\n")

    print(f"{'İLÇE':<11}{'NOT':>4}{'SAĞLIK':>8}{'EKİLİ ORT.':>11}  "
          f"{'ZAYIF HALKA':<12} SORUNLU EKİMLER")
    for r in s["ilceler"]:
        print(f"{r['ilce']:<11}{r['saglik']['harf']:>4}{r['saglik']['puan']:>8}"
              f"{r['ekili_ortalama']:>11}  {r['saglik']['zayif_halka']:<12} "
              f"{', '.join(r['sorunlu_ekimler']) or '-'}")

    print("\nBİRLEŞİK UYUM (toprak x iklim)")
    print(f"{'ÜRÜN':<16}" + "".join(f"{i[:6]:>9}" for i in mp.ILCE))
    for u in s["urun_karsilastirma"]:
        sira = {d["ilce"]: d["puan"] for d in u["ilceler"]}
        print(f"{u['urun']:<16}" + "".join(f"{sira[i]:>9.0f}" for i in mp.ILCE))

    print(f"\n{'ÜRÜN':<16}{'EN İYİ':<12}{'PUAN':>6}  {'EN ZOR':<12}{'PUAN':>6}  DARBOĞAZ")
    for u in sorted(s["urun_karsilastirma"], key=lambda x: -x["makas"]):
        print(f"{u['urun']:<16}{u['en_iyi']:<12}{u['ilceler'][0]['puan']:>6}  "
              f"{u['en_kotu']:<12}{u['ilceler'][-1]['puan']:>6}  "
              f"{u['ilceler'][-1]['darbogaz']}")
