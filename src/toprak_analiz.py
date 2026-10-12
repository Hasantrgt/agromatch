"""
AGROMATCH - Toprak analizi ve ürün-toprak uygunluğu
===================================================
Üç soruyu cevaplar:

  1. İlin toprağı ne durumda?      -> toprak sağlığı karnesi (organik madde, tuzluluk,
                                      erozyon, drenaj, derinlik, kireç)
  2. Bu ürün bu toprağa uyar mı?   -> ürün-toprak uygunluk skoru ve kısıtlayıcı faktör
  3. Ne kadar gübre gerekir?       -> hedef verime göre N-P-K ihtiyacı, topraktaki
                                      mevcut besin düşülerek

Planlama motoruyla bağlantısı: denge analizi "hangi ürüne ihtiyaç var" sorusunu,
bu modül "o ürün burada yetişir mi" sorusunu cevaplar. Bir ürün ancak iki filtreden
de geçerse önerilir.

Çıktı: outputs/toprak.json
"""

import json
from pathlib import Path

from bolge_profil import DESEN, ILLER
from toprak_profil import (
    DRENAJ_PUAN,
    IL_NOTU,
    KIREC_ESIK,
    URUN_ISTEK,
    bunye_sinifi,
    il_toprak,
)

CIKTI = Path(__file__).resolve().parent.parent / "outputs"

AGIRLIK = dict(ph=0.20, tuzluluk=0.25, kirec=0.15, bunye=0.12,
               drenaj=0.13, organik=0.10, derinlik=0.05)

BUNYE_YAKINLIK = {
    ("killi", "killi-tın"): 85, ("killi-tın", "killi"): 85,
    ("killi-tın", "tınlı"): 85, ("tınlı", "killi-tın"): 85,
    ("tınlı", "kumlu-tın"): 85, ("kumlu-tın", "tınlı"): 85,
    ("killi", "tınlı"): 70, ("tınlı", "killi"): 70,
    ("kumlu", "kumlu-tın"): 90, ("kumlu-tın", "kumlu"): 90,
    ("kumlu", "tınlı"): 70, ("tınlı", "kumlu"): 70,
}


def ph_puan(ph, istek):
    """Optimum aralığın İÇİNDE de konum önemlidir.

    Önceki sürümde aralığın içindeki her değer 100 puan alıyordu; bu, aralığı
    geniş olan ürünle dar olan ürünü aynı gösteriyordu. Şimdi puan, aralığın
    ortasından uzaklaştıkça düşer (kenarda 88), aralık dışında hızla azalır.
    """
    a, b = istek["ph_opt"]
    alt, ust = istek["ph_sinir"]
    merkez, yari = (a + b) / 2, max((b - a) / 2, 0.1)
    if a <= ph <= b:
        return 100 - 12 * ((ph - merkez) / yari) ** 2
    if ph < a:
        return max(0.0, 88 - (a - ph) / max(a - alt, 0.1) * 68)
    return max(0.0, 88 - (ph - b) / max(ust - b, 0.1) * 68)


def tuz_puan(ec, esik):
    """Tuzluluk eşiğin altındayken bile sürekli bir baskıdır.

    Mercimek (eşik 1,5 dS/m) ile arpa (eşik 8,0 dS/m) aynı tarlada aynı puanı
    almamalıdır: tuza hassas ürün, düşük tuzlulukta bile daha fazla risk taşır.
    """
    oran = ec / esik
    if oran <= 1:
        return 100 - 30 * oran ** 2
    return max(0.0, 70 - (oran - 1) * 70)


def kirec_puan(kirec, tolerans):
    esik = KIREC_ESIK[tolerans]
    oran = kirec / esik
    if oran <= 1:
        return 100 - 25 * oran ** 2
    return max(10.0, 75 - (oran - 1) * 60)


def bunye_puan(topragin, istenen):
    if topragin == istenen:
        return 100.0
    return float(BUNYE_YAKINLIK.get((topragin, istenen), 55))


def drenaj_puan(drenaj, hassasiyet):
    """Drenaj ürüne göre değişir: mercimek ve patates ıslaklığa çok hassastır,
    buğday ve tütün daha toleranslıdır. Önceki sürümde bu puan ürüne bağlı
    değildi ve bütün ürünler aynı değeri alıyordu."""
    ceza = {"iyi": 0.0, "orta": 20.0, "zayıf": 45.0}[drenaj]
    katsayi = 0.6 + (hassasiyet - 1) * 0.2      # hassasiyet 1 -> 0,6 ; 5 -> 1,4
    return max(10.0, 100 - ceza * katsayi)


def derinlik_puan(derinlik, istenen):
    """Derin köklü ürün (yonca, antep fıstığı, pamuk) sığ toprakta zorlanır."""
    return max(20.0, min(100.0, derinlik / istenen * 100))


def uygunluk(il, urun):
    t = il_toprak(il)
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
    puan = sum(bilesen[k] * AGIRLIK[k] for k in AGIRLIK)
    kisit = min(bilesen, key=bilesen.get)
    etiket = ("çok uygun" if puan >= 80 else "uygun" if puan >= 65
              else "sınırlı" if puan >= 50 else "uygun değil")
    return dict(puan=round(puan, 1), sinif=etiket, bilesen=bilesen,
                kisitlayici=kisit, kisit_puani=bilesen[kisit])


def gubre_onerisi(il, urun, verim):
    """Hedef verime göre kg/dekar N-P2O5-K2O önerisi."""
    t = il_toprak(il)
    istek = URUN_ISTEK[urun]
    ihtiyac_n = verim * istek["N"]
    ihtiyac_p = verim * istek["P"]
    ihtiyac_k = verim * istek["K"]

    # Organik maddeden yıllık mineralize olan azot.
    # Soğuk ve kurak bölgelerde mineralizasyon yavaştır: %1 OM ≈ 1,2 kg N/da.
    topraktan_n = t["om"] * 1.2
    if istek["azot_baglar"]:
        ihtiyac_n *= 0.3          # baklagil azotun çoğunu havadan bağlar

    # Gübre kullanım etkinliği: verilen gübrenin tamamı bitkiye geçmez.
    # Azotta yıkanma ve buharlaşma, fosforda kireçli toprakta fiksasyon kayıp yaratır.
    ETKINLIK_N, ETKINLIK_P, ETKINLIK_K = 0.65, 0.45, 0.75
    if t["kirec"] > 15:
        ETKINLIK_P = 0.35         # yüksek kireçte fosfor bağlanması artar

    return dict(
        azot=round(max(0.0, ihtiyac_n - topraktan_n) / ETKINLIK_N, 1),
        fosfor=round(max(0.0, ihtiyac_p - t["p2o5"] * 0.5) / ETKINLIK_P, 1),
        potasyum=round(max(0.0, ihtiyac_k - t["k2o"] * 0.25) / ETKINLIK_K, 1),
        fosfor_etkinligi=ETKINLIK_P,
        topraktan_gelen_azot=round(topraktan_n, 1),
        organik_gubre_gerekli=bool(t["om"] < istek["om_hedef"] * 0.8),
    )


def toprak_sagligi(il):
    t = il_toprak(il)
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
                zayif_halka=min(b, key=b.get))


def analiz():
    iller = []
    for il, (bolge, *_rest) in ILLER.items():
        t = il_toprak(il)
        ekili = {u: v for u, (a, v, _t) in DESEN[il].items()}

        urunler = []
        for urun in URUN_ISTEK:
            u = uygunluk(il, urun)
            verim = ekili.get(urun)
            urunler.append(dict(
                urun=urun, ekili=urun in ekili,
                verim=verim,
                gubre=gubre_onerisi(il, urun, verim) if verim else None,
                **u))

        ekili_urunler = [u for u in urunler if u["ekili"]]
        alternatifler = sorted([u for u in urunler if not u["ekili"]],
                               key=lambda u: -u["puan"])[:4]

        iller.append(dict(
            il=il, bolge=bolge, toprak=t,
            bunye=bunye_sinifi(t["kil"], t["kum"], t["silt"]),
            saglik=toprak_sagligi(il),
            not_=IL_NOTU.get(il),
            urunler=urunler,
            ekili_ortalama=round(sum(u["puan"] for u in ekili_urunler)
                                 / max(len(ekili_urunler), 1), 1),
            sorunlu_ekimler=[u["urun"] for u in ekili_urunler if u["puan"] < 65],
            alternatifler=[u["urun"] for u in alternatifler],
        ))

    iller.sort(key=lambda r: (r["bolge"], r["il"]))

    tuzlu = [r["il"] for r in iller if r["toprak"]["ec"] >= 1.0]
    dusuk_om = [r["il"] for r in iller if r["toprak"]["om"] < 1.5]
    erozyon = [r["il"] for r in iller if r["toprak"]["erozyon"] >= 4]

    sonuc = dict(
        iller=iller,
        agirlik=AGIRLIK,
        urun_istek={k: {kk: (list(vv) if isinstance(vv, tuple) else vv)
                        for kk, vv in v.items()} for k, v in URUN_ISTEK.items()},
        ozet=dict(
            il_sayisi=len(iller),
            ortalama_om=round(sum(r["toprak"]["om"] for r in iller) / len(iller), 2),
            tuzluluk_riski=tuzlu, dusuk_organik=dusuk_om, yuksek_erozyon=erozyon,
            sorunlu_ekim_sayisi=sum(len(r["sorunlu_ekimler"]) for r in iller),
        ),
    )
    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "toprak.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    return sonuc


if __name__ == "__main__":
    s = analiz()
    o = s["ozet"]
    print(f"Ortalama organik madde: %{o['ortalama_om']}")
    print(f"Tuzluluk riski: {', '.join(o['tuzluluk_riski'])}")
    print(f"Organik maddesi kritik (<%1,5): {len(o['dusuk_organik'])} il")
    print(f"Yüksek erozyon riski: {len(o['yuksek_erozyon'])} il")
    print(f"Toprağa uymayan mevcut ekim: {o['sorunlu_ekim_sayisi']} adet\n")
    print(f"{'İL':<12}{'NOT':>4}{'PUAN':>6}{'EKİLİ ORT.':>11}  ZAYIF HALKA   SORUNLU EKİMLER")
    for r in s["iller"]:
        print(f"{r['il']:<12}{r['saglik']['harf']:>4}{r['saglik']['puan']:>6}"
              f"{r['ekili_ortalama']:>11}  {r['saglik']['zayif_halka']:<13} "
              f"{', '.join(r['sorunlu_ekimler']) or '-'}")
