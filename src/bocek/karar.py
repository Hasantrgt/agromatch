"""
AGROMATCH - Böcek karar sistemi
================================
Projede zararlı, ilaç grubu ve faydalı böcek KATALOGLARI vardı ama bunları
birleştiren bir karar akışı yoktu. Çiftçinin sorusu "17 zararlının listesi
nedir" değil: "tarlamda şu böcek var, ne yapayım".

Bu modül o soruyu dört adımda cevaplıyor ve ADIMLARIN SIRASI RASTGELE
DEĞİL. Sıra, hangi cevabın hangisinden önce gelmesi gerektiğini anlatır:

    1. İLAÇLAMALI MI?        Çoğu ilaçlama gereksizdir. Eşiğin altında
                             zararlı varlığı zarar demek değildir ve
                             ilaçlamak faydalıyı öldürüp sorunu büyütür.
    2. İLAÇSIZ ÇÖZÜLÜR MÜ?   Kalıntı bırakmayan yol varsa önce o denenir.
    3. İLAÇ GEREKİYORSA       Gruplar faydalıya verdikleri yüke göre
       HANGİSİ?               sıralanır; en az vuran önce gelir.
    4. FAYDALIYI NASIL        Seçilen grup kimi vuruyor, o zararlıyı
       KORURUZ?               zaten kim avlıyor, ne yapılmalı.

NEDEN BU SIRA: "hangi ilaç" sorusuyla başlamak, cevabı baştan ilaçlamaya
sabitler. Oysa karar ağacının ilk düğümü eşiktir. Panel de bu sırayı
gösterir; kullanıcı 3. adımı görmeden 1. ve 2. adımı okumak zorunda kalır.

NE YAPMAZ — bilerek:
  - Ticari ürün adı vermez. Ruhsatlı ürün listesi Bakanlık'ındır ve
    değişir; burada tutmak yanlış tavsiyeye yol açar.
  - Doz vermez. Doz ürüne ve ruhsata bağlıdır.
  - Bekleme süresi vermez. Bir zamanlar veriyordu ve UYDURMAYDI;
    kaldırıldı (bkz. pestisit.py "BEKLEME SÜRESİ NEDEN YOK").

Bu üçü eksiklik değil, sınır. Karar sistemi "hangi ETKİ GRUBU" sorusuna
kadar götürür; oradan sonrası reçetedir ve ziraat mühendisinin işidir.
"""

from __future__ import annotations

from typing import Any

from . import faydali as fa
from . import pestisit as pe
from . import tarla_zararli as tz

# Eşik ölçülmeden ilaçlama kararı verilemeyen zararlılar için, ölçümün
# nasıl yapılacağı zararlının kendi "esik" alanında yazılı.
ADIM_ADI = ("İlaçlamalı mı", "İlaçsız çözülür mü",
            "İlaç gerekiyorsa hangisi", "Faydalıyı nasıl koruruz")


def _zararli(ad: str) -> dict[str, Any] | None:
    for z in tz.ZARARLILAR:
        if z["ad"] == ad:
            return z
    return None


def _esik_adimi(z: dict[str, Any], ergin_m2: float | None,
                parazitlenme: float | None) -> dict[str, Any]:
    """1. adım: ilaçlama kararı için eşik ne diyor.

    Bu adımın cevabı çoğu zaman "ÖLÇÜLMEDEN KARAR VERİLEMEZ" olur ve bu
    bir eksiklik değil, doğru cevaptır. Eşiği bilinmeyen bir zararlıya
    ilaçlama önermek, projenin yapmayacağı tek şeydir.
    """
    esik = z.get("esik")
    kaynak = z.get("esik_kaynak")

    # Sünenin eşiği iki ölçüme birden bağlı; projede kendi kararı var.
    if z["ad"] == "Süne" and ergin_m2 is not None:
        k = tz.sune_karari(ergin_m2, parazitlenme)
        return {"adim": 1, "ad": ADIM_ADI[0], "durum": k.get("karar", "?"),
                "aciklama": k.get("gerekce", ""), "ayrinti": k,
                "esik": esik, "esik_kaynak": kaynak}

    # ÜÇ AYRI CEVAP, ikisi kolayca karıştırılır:
    #   "eşik bilinmiyor"   bizde kayıt yok — ilaçlama önerilmez
    #   "resmî eşik yok"    TALİMAT eşik vermiyor ve bunu açıkça söylüyor;
    #                       karar sayıma değil başka bir ölçüte bağlı
    #   "eşik var"          sayıma bağlı karar
    # İkincisini birincisiyle birleştirmek, Bakanlığın verdiği kararı
    # "bilinmiyor" diye göstermek olurdu. Tersi daha kötü: eşik vermeyen
    # bir zararlıda "ölçüm gerekli" demek, olmayan sayıyı aratır.
    if z.get("esik_turu") == "yok":
        return {
            "adim": 1, "ad": ADIM_ADI[0], "durum": "resmî eşik yok",
            "aciklama": ("Talimat bu zararlı için ekonomik zarar eşiği "
                         "VERMİYOR ve bunu açıkça yazıyor. Bu, eşiği "
                         "bilmediğimiz anlamına gelmez: karar sayıma "
                         "değil, aşağıdaki ölçüte bağlanmıştır."),
            "esik": esik, "esik_kaynak": kaynak}

    if not esik:
        return {
            "adim": 1, "ad": ADIM_ADI[0], "durum": "eşik bilinmiyor",
            "aciklama": "Bu zararlı için ekonomik zarar eşiği elimizde "
                        "yok. Eşiksiz ilaçlama önerisi verilmez: zararlının "
                        "varlığı tek başına zarar demek değildir. Zirai "
                        "Mücadele Teknik Talimatı'ndaki eşik bulunana kadar "
                        "karar, tarlayı gören ziraat mühendisinindir.",
            "esik": None, "esik_kaynak": None}

    return {
        "adim": 1, "ad": ADIM_ADI[0], "durum": "eşik var — ölçüm gerekli",
        "aciklama": "İlaçlama kararı sayıma bağlıdır. Eşiğin altındaysa "
                    "ilaçlama yapılmaz; yapılırsa faydalı böcekler ölür ve "
                    "sorun bir sonraki yıl büyür.",
        "esik": esik, "esik_kaynak": kaynak}


def _ilacsiz_adimi(ad: str) -> dict[str, Any]:
    """2. adım: kalıntı bırakmayan yollar."""
    yollar = pe.kalintisiz_yol(ad)
    return {
        "adim": 2, "ad": ADIM_ADI[1],
        "durum": "var" if yollar else "yok",
        "aciklama": ("Önce bunlar denenir; kalıntı bırakmaz, faydalıyı "
                     "vurmaz ve dirence yol açmaz."
                     if yollar else
                     "Bu zararlı için elimizde kalıntısız bir yol YOK. Bu "
                     "bir eksiklik değil, bilinen bir boşluk: öyle "
                     "yazılıyor, uydurulmuyor."),
        "secenekler": [{"grup": g["grup"], "ad": g["ad"],
                        "etki_sekli": g["etki_sekli"],
                        "not_": g.get("not_", "")} for g in yollar]}


def _ilac_adimi(ad: str) -> dict[str, Any]:
    """3. adım: ilaç gerekiyorsa hangi ETKİ GRUBU.

    Gruplar faydalıya verdikleri yüke göre sıralanır — en az vuran önce.
    Sıralama ölçütü ürün tercihi değil, ekolojik maliyettir.
    """
    faydalilar = tuple(fa.FAYDALILAR)
    gruplar = [g for g in pe.zararliya_gore(ad) if g["grup"] in pe.KIMYASAL]
    yukler = [pe.yuk(g["grup"], faydalilar) for g in gruplar]
    yukler.sort(key=lambda y: (y["canliya_zarar"],
                               {"yok": 0, "düşük": 1, "orta": 2,
                                "yüksek": 3}.get(y["direnc"], 9)))
    return {
        "adim": 3, "ad": ADIM_ADI[2],
        "durum": "seçenek var" if yukler else "kimyasal seçenek yok",
        "aciklama": ("Gruplar faydalıya verdikleri yüke göre sıralı; en az "
                     "vuran önce. Aynı grubu üst üste kullanmak direnç "
                     "doğurur — yıldan yıla IRAC grubu değiştirilmeli. "
                     "Ticari ürün adı ve doz BURADA YOK: o reçetedir ve "
                     "ziraat mühendisinin işidir."
                     if yukler else
                     "Bu zararlı için kayıtlı bir kimyasal grup yok."),
        "secenekler": yukler}


def _faydali_adimi(ad: str, secilen: list[dict[str, Any]]) -> dict[str, Any]:
    """4. adım: bu zararlıyı zaten kim avlıyor, onları nasıl korunur."""
    avcilar = fa.hedefe_gore(ad)
    en_iyi = secilen[0]["grup"] if secilen else None
    vurulan = fa.gruba_hassas(en_iyi) if en_iyi else []
    return {
        "adim": 4, "ad": ADIM_ADI[3],
        "durum": "doğal düşman var" if avcilar else "kayıtlı doğal düşman yok",
        "aciklama": ("Bu zararlıyı zaten avlayan canlılar var. İlaçlama "
                     "kararı onları da hesaba katmalı: doğal düşmanı "
                     "öldüren bir uygulama, kısa vadede zararlıyı azaltıp "
                     "uzun vadede artırır."
                     if avcilar else
                     "Bu zararlı için kayıtlı doğal düşman yok; kalıntısız "
                     "yol ve kültürel önlemler daha da önemli hâle gelir."),
        "avcilar": [{"ad": f["ad"], "rol": f["rol"],
                     "korumak_icin": f.get("korumak_icin", "")}
                    for f in avcilar],
        "en_az_vuran_grup": en_iyi,
        "o_grubun_vurdugu": vurulan}


def karar(zararli: str, *, ergin_m2: float | None = None,
          parazitlenme: float | None = None) -> dict[str, Any]:
    """Tek bir zararlı için dört adımlık karar akışı."""
    z = _zararli(zararli)
    if z is None:
        return {"var": False, "sebep": f"'{zararli}' kayıtlı zararlı değil"}

    ilacsiz = _ilacsiz_adimi(zararli)
    ilac = _ilac_adimi(zararli)
    return {
        "var": True,
        "zararli": z["ad"], "latince": z["latince"],
        "urunler": z["urunler"], "kritik_aylar": z["kritik_aylar"],
        "zarar_sekli": z["zarar_sekli"], "onem": z["onem"],
        "adimlar": [
            _esik_adimi(z, ergin_m2, parazitlenme),
            ilacsiz,
            ilac,
            _faydali_adimi(zararli, ilac["secenekler"]),
        ],
        "ozet": _ozet_cumlesi(z, ilacsiz, ilac),
    }


def _ozet_cumlesi(z: dict[str, Any], ilacsiz: dict[str, Any],
                  ilac: dict[str, Any]) -> str:
    """Dört adımın birlikte söylediği şeyi tek cümlede."""
    if ilacsiz["durum"] == "var" and ilac["secenekler"]:
        return (f"{z['ad']} için önce kalıntısız yol var; yetmezse en az "
                f"faydalı vuran grup {ilac['secenekler'][0]['ad']}. Karar "
                "yine de eşik sayımına bağlı.")
    if ilacsiz["durum"] == "var":
        return (f"{z['ad']} için kalıntısız yol var ve kayıtlı kimyasal "
                "grup yok — mücadele kalıntısız yoldan yürür.")
    if ilac["secenekler"]:
        return (f"{z['ad']} için kalıntısız yol YOK. Kimyasal gerekirse en "
                f"az faydalı vuran grup {ilac['secenekler'][0]['ad']}; "
                "eşik sayımı olmadan uygulanmaz.")
    return (f"{z['ad']} için elimizde ne kalıntısız yol ne de kayıtlı "
            "kimyasal grup var. Bu bir boşluktur ve öyle yazılıdır.")


def hepsi() -> list[dict[str, Any]]:
    """Bütün zararlılar için karar akışı — panel bunu gömer."""
    return [karar(z["ad"]) for z in tz.ZARARLILAR]


def bosluklar() -> dict[str, Any]:
    """Karar sisteminin cevap VEREMEDİĞİ yerler.

    Bir karar sisteminin en dürüst kısmı, nerede karar veremediğidir.
    """
    esiksiz, kalintisiz_yok, caresiz = [], [], []
    resmi_esiksiz = []
    for k in hepsi():
        a = {x["adim"]: x for x in k["adimlar"]}
        if a[1]["durum"] == "eşik bilinmiyor":
            esiksiz.append(k["zararli"])
        if a[1]["durum"] == "resmî eşik yok":
            resmi_esiksiz.append(k["zararli"])
        if a[2]["durum"] == "yok":
            kalintisiz_yok.append(k["zararli"])
        if a[2]["durum"] == "yok" and not a[3]["secenekler"]:
            caresiz.append(k["zararli"])
    return {
        "esigi_bilinmeyen": esiksiz,
        "resmi_esigi_olmayan": resmi_esiksiz,
        "kalintisiz_yolu_olmayan": kalintisiz_yok,
        "hicbir_secenegi_olmayan": caresiz,
        "not_": "Eşiği bilinmeyen zararlıya ilaçlama önerilmez; kalıntısız "
                "yolu olmayan için o boşluk yazılır. Hiçbir seçeneği "
                "olmayan varsa, proje bunu gizlemek yerine listeler. "
                "'Resmî eşiği olmayan' bunlardan AYRI bir durumdur: orada "
                "boşluk bizde değil, talimat eşik yerine başka bir ölçüt "
                "koymuştur.",
    }
