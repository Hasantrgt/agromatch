"""
AGROMATCH - Çatı: kısımların birbirini denetlediği yer
=======================================================
Panelin "Çatı" sekmesi üç kısmı YAN YANA gösteriyordu ve kendi metninde
bunu açıkça söylüyordu: "bu sayfanın amacı yeni bilgi vermek değil".
Doğruydu — ama çatının işi bu değil. Üç parçayı aynı sayfaya koymak
onları birbiriyle KONUŞTURMAZ.

Bu modül o konuşmayı kuruyor ve ilk yaptığı şey 1. kısmı denetlemek.

DENETLENEN SÖZ
1. kısım (mus_analiz.oneriler) ürün deseni dar olan ilçeye şöyle diyordu:

    "Risk dağılır, münavebe hastalık baskısını kırar."

Panelin çatı sekmesi de aynı sözü veriyordu: "toprak kaynaklı bir kök
çürüklüğüne ilaçlama değil ekim nöbeti çare olur."

İkisi de 2. kısma sorulmadan yazılmıştı. 2. kısımda ise her hastalığın
patojeni ve bulaş kaynağı kayıtlı. Soru hesaplanabilir: iki ürün
TOPRAKTAN bulaşan aynı etkeni paylaşıyorsa, o ikisi arasındaki münavebe
o etkenin baskısını kırmaz — toprakta aynı patojeni beslemeye devam eder.

HESABIN SONUCU
Muş'un 9 ürünü 36 çift yapıyor. Bu çiftlerden yalnızca BİRİ topraktan
bulaşan ortak etken taşımıyor: şeker pancarı – arpa. 17 çiftte ortak
etken tür düzeyinde kayıtlı, 18 çiftte katalog yalnızca cins yazdığı
için karar verilemiyor.

Yani "münavebe hastalık baskısını kırar" cümlesi Muş için genel bir
doğru değil; bir çift için doğru. Söz bu yüzden daraltıldı.

İKİ EK BULGU — çift saymak yerine toprağa bakınca
1) Muş'ta ekili alanın %83'ü BUĞDAY ile ARPA arasında dönüyor ve bu iki
   ürün Bipolaris sorokiniana'yı paylaşıyor. İlde fiilen uygulanan
   münavebe, kök çürüklüğü baskısını kırmayan münavebedir.
2) Baskıyı kıran tek çift pancara dayanıyor; pancar alanı ise agronomiyle
   değil Muş Şeker Fabrikası kotasıyla sınırlı. Tavan 120.194 dekar =
   il ekili alanının %5,4'ü. Yani bu münavebe en iyi durumda ilin
   topraklarının yirmide birinde uygulanabilir.

   Bu, 1. ve 2. kısmın çelişmesi değil, BİRLİKTE okunmasının sonucudur:
   iki kısım ayrı sekmelerde dururken görünmüyordu. pancar_tavani()
   bunu hesaplar.

Geri kalan alan için doğru cümle şudur: kök çürüklüğünde kaldıraç
münavebe değil, DRENAJ ve tohum/çeşittir. 1. kısım drenajı zaten
"her şeyin önünde" diye öneriyordu; çatı o önerinin neden birinci
sırada olduğunu gösteriyor.

CİNS / TÜR AYRIMI — bu modülün en önemli kuralı
Katalog patojeni bazen tür düzeyinde yazar (Rhizoctonia solani), bazen
cins düzeyinde (Fusarium spp.). İkisi aynı şey değildir ve karıştırmak
bulguyu şişirir:

    tür aynı    -> aynı patojen iki üründe kayıtlı. Münavebe o etkeni
                   KIRMAZ sayılır.
    yalnız cins -> aynı cins iki üründe geçiyor ama TÜR bilinmiyor.
                   Fusarium cinsinde buğdayı tutan tür ile fasulyeyi
                   tutan tür farklı olabilir. Burada "kırmaz" demek
                   kataloğun söylemediğini söylemektir. Cevap BELİRSİZ.

forma specialis (f.sp.) ayrıca ele alınır: f.sp. eki patojenin konakçıya
ÖZELLEŞTİĞİNİ söyler. Fusarium oxysporum f.sp. betae pancarı tutar,
buğdayı tutmaz. Bu yüzden f.sp. yazan bir kayıt cins benzerliğine
sayılmaz — eldeki en kesin bilgi konakçı özelliğidir.

SINIR — bilerek açık bırakıldı
"Tür aynı" bile kesin bir kırılmazlık kanıtı değildir. Rhizoctonia
solani'nin anastomoz grupları (AG) konakçıya göre ayrışır: patateste
AG-3, pancarda AG-2-2, fasulyede AG-4 baskındır. Katalog AG kaydetmiyor.
Dolayısıyla bu modül "aynı tür kayıtlı" der, "aynı suş tarlada geçiyor"
demez. Fark bosluklar() içinde yazılı ve kapatılması izolat teşhisi
gerektirir — masa başından kapatılamaz.

Çatı yeni veri üretmez. Eldeki iki kısmı birbirine sorarak 1. kısmın
veremeyeceği bir sözü geri alır. Bir karar sisteminin çatısı budur.
"""

from __future__ import annotations

import itertools
import re
from typing import Any

import bulas_kaynagi as bk
import mus_hastalik as mh
import mus_profil as mp

# Bileşik patojen etiketini ayıran ayraçlar: "Fusarium spp. / Rhizoctonia
# solani" tek bir etken değil, iki etkendir. Birebir karşılaştırma bunu
# iki ayrı şey sanıp ortaklığı gözden kaçırıyordu.
AYRAC = re.compile(r"\s*(?:[/,+]|\sve\s)\s*")

# Cins düzeyinde kalan yazımlar: tür belirtilmemiş.
CINS_IZI = ("spp.", "sp.")

# Parantez içi ek bilgi taşır ("(vektör: Polymyxa betae)"); etkenin kimliği
# değildir ve cins çıkarırken karışır.
PARANTEZ = re.compile(r"\s*\([^)]*\)")

# Katalog bileşik etiketlerde cinsi kısaltıyor: "Tilletia caries / T. foetida".
# "T." bir cins değil; önündeki tam adın cinsidir.
KISALTMA = re.compile(r"^([A-ZÇĞİÖŞÜ])\.\s")

DURUM = ("kırar", "kırmaz", "belirsiz")


def _virus_mu(etken: str) -> bool:
    """Virüs adlarında cins soyutlaması yoktur.

    "Beet necrotic yellow vein virus" ilk sözcüğü cins sanılırsa başka bir
    "Beet ... virus" kaydıyla yanlışlıkla eşleşir. Virüs yalnızca kendi
    tam adıyla karşılaştırılır.
    """
    return "virus" in etken.lower() or "virüs" in etken.lower()


def _etkenler(etiket: str) -> list[str]:
    """Bileşik patojen etiketini tek tek etkenlere ayırır.

    Ayırmadan önce parantezli ekler atılır; ayırdıktan sonra kısaltılmış
    cins adı ("T. foetida") önündeki tam adın cinsiyle açılır — yoksa
    cins karşılaştırması anlamsız bir "T." üzerinden yapılır.
    """
    temiz = PARANTEZ.sub("", etiket)
    cikti: list[str] = []
    son_cins = ""
    for parca in AYRAC.split(temiz):
        p = parca.strip()
        if not p:
            continue
        m = KISALTMA.match(p)
        if m and son_cins and son_cins.startswith(m.group(1)):
            p = son_cins + " " + p[m.end():]
        cikti.append(p)
        ilk = p.split()[0] if p.split() else ""
        if len(ilk) > 2 and not ilk.endswith("."):
            son_cins = ilk
    return cikti


def _konakci_ozel(etken: str) -> bool:
    """forma specialis: patojen konakçıya özelleşmiş.

    f.sp. betae pancarı tutar, buğdayı tutmaz. Böyle bir kayıt cins
    benzerliğine sayılmaz; eldeki en kesin bilgi konakçı özelliğidir.
    """
    return "f.sp." in etken or "f. sp." in etken


def _cins_mi(etken: str) -> bool:
    """Tür belirtilmemiş mi (Fusarium spp. gibi)."""
    return any(iz in etken for iz in CINS_IZI) and not _konakci_ozel(etken)


def _cins(etken: str) -> str:
    """Etkenin cins adı — ilk sözcük. Virüste tam ad döner."""
    if _virus_mu(etken):
        return etken
    return etken.split()[0] if etken.split() else etken


def topraktan_etkenler() -> dict[str, dict[str, set[str]]]:
    """Ürün -> {"tur": {...}, "cins": {...}} topraktan bulaşan etkenler.

    Bir hastalık, birincil kaynağı toprak ise ya da ikincil kaynakları
    arasında toprak varsa sayılır: ikincil yol da toprakta patojen
    bırakır ve münavebe kararını etkiler.
    """
    tablo: dict[str, dict[str, set[str]]] = {
        u: {"tur": set(), "cins": set()} for u in mp.URUN}
    for h in mh.hastalik_listesi():
        urun = h["urun"]
        if urun not in tablo:
            continue
        kaynak = bk.kaynak(urun, h["ad"])
        ikincil = bk.ikincil(urun, h["ad"])
        if kaynak != "toprak" and "toprak" not in ikincil:
            continue
        for e in _etkenler(h["patojen"]):
            if _konakci_ozel(e):
                continue
            if _cins_mi(e):
                tablo[urun]["cins"].add(_cins(e))
            else:
                tablo[urun]["tur"].add(e)
                tablo[urun]["cins"].add(_cins(e))
    return tablo


def munavebe(a: str, b: str) -> dict[str, Any]:
    """İki ürün arasındaki münavebe topraktan bulaşan baskıyı kırar mı.

    Üç cevap verir ve üçüncüsü bir cevaptır, eksiklik değil:
        kırar     ortak topraktan etken kaydı yok
        kırmaz    aynı TÜR iki üründe de kayıtlı
        belirsiz  yalnız CİNS ortak; tür bilinmediği için söylenemez
    """
    t = topraktan_etkenler()
    if a not in t or b not in t:
        return {"var": False, "sebep": f"'{a}' ya da '{b}' kayıtlı ürün değil"}

    tur_ortak = sorted(t[a]["tur"] & t[b]["tur"])
    cins_ortak = sorted(c for c in (t[a]["cins"] & t[b]["cins"])
                        if c not in {_cins(x) for x in tur_ortak})

    if tur_ortak:
        durum = "kırmaz"
        gerekce = (f"{', '.join(tur_ortak)} iki üründe de topraktan bulaşan "
                   "etken olarak kayıtlı. Bu ikisini sırayla ekmek toprakta "
                   "aynı patojeni beslemeye devam eder.")
    elif cins_ortak:
        durum = "belirsiz"
        gerekce = (f"{', '.join(cins_ortak)} cinsi iki üründe de geçiyor ama "
                   "katalog TÜR yazmıyor. Aynı cinsin farklı türleri farklı "
                   "konakçı tutabilir; kırar da kırmaz da denemez.")
    else:
        durum = "kırar"
        gerekce = ("İki üründe ortak topraktan bulaşan etken kaydı yok; "
                   "münavebe toprak kaynaklı baskıyı kırar.")

    return {
        "var": True, "urunler": (a, b), "durum": durum,
        "tur_ortak": tur_ortak, "cins_ortak": cins_ortak,
        "gerekce": gerekce,
        "sinir": ("Aynı tür kaydı, tarlada aynı suşun geçtiğini kanıtlamaz: "
                  "Rhizoctonia solani'nin anastomoz grupları konakçıya göre "
                  "ayrışır ve katalog AG kaydetmiyor."
                  if tur_ortak else
                  "Kayıt yokluğu, tarlada yokluk demek değil — katalog 59 "
                  "hastalıkla sınırlı."),
    }


def matris() -> list[dict[str, Any]]:
    """Bütün ürün çiftleri için münavebe kararı."""
    return [munavebe(a, b) for a, b in itertools.combinations(mp.URUN, 2)]


def kiran_ciftler() -> list[tuple[str, str]]:
    """Topraktan bulaşan baskıyı gerçekten kıran ürün çiftleri."""
    return [m["urunler"] for m in matris() if m["durum"] == "kırar"]


def ilce_munavebe(ilce: str) -> dict[str, Any]:
    """Bir ilçede EKİLİ ürünler arasında hangi münavebe baskıyı kırıyor.

    1. kısım bu ilçeye "deseni genişlet" derken, genişletmenin hastalık
    tarafında işe yarayıp yaramadığını bu fonksiyon söyler.
    """
    ekili = [u for u in mp.URUN if mp.DESEN[ilce].get(u, (0, 0))[0] > 0]
    ciftler = [munavebe(a, b) for a, b in itertools.combinations(ekili, 2)]
    kiran = [m for m in ciftler if m["durum"] == "kırar"]
    return {
        "ilce": ilce, "ekili_urun": ekili,
        "cift": len(ciftler),
        "kiran": [m["urunler"] for m in kiran],
        "kirmayan": len([m for m in ciftler if m["durum"] == "kırmaz"]),
        "belirsiz": len([m for m in ciftler if m["durum"] == "belirsiz"]),
    }


def munavebe_cumlesi(ilce: str) -> str:
    """1. kısmın öneri metnine girecek, hesaplanmış cümle.

    Eskiden burada "münavebe hastalık baskısını kırar" yazıyordu. O cümle
    36 çiftin 34'ü için yanlıştı.
    """
    d = ilce_munavebe(ilce)
    if d["kiran"]:
        ciftler = "; ".join(f"{a} – {b}" for a, b in d["kiran"])
        return (f"Hastalık tarafında ise {d['cift']} ürün çiftinden yalnızca "
                f"şu topraktan bulaşan baskıyı kırıyor: {ciftler}. "
                f"{d['kirmayan']} çiftte ortak toprak patojeni kayıtlı, "
                f"{d['belirsiz']} çiftte katalog tür yazmadığı için "
                "kırdığı söylenemiyor.")
    return (f"Hastalık tarafında ise bu ilçenin {d['cift']} ürün çiftinin "
            "hiçbiri topraktan bulaşan baskıyı kırmıyor: desen genişletmek "
            "fiyat riskini dağıtır, toprak patojenini dağıtmaz. Kök "
            "çürüklüğü için kaldıraç drenaj ve tohum/çeşittir.")


def urun_yuku(urun: str) -> dict[str, Any]:
    """Bir ürünü ekmenin 2. ve 3. kısımdaki bedeli.

    "Bu ürünü ekersem ne ile karşılaşırım" sorusunun tek yerden cevabı.
    Böcek katmanı kurulu değilse o bölüm None döner — uydurulmaz.
    """
    hastaliklar = [h for h in mh.hastalik_listesi() if h["urun"] == urun]
    kaynak_sayisi: dict[str, int] = {k: 0 for k in bk.KAYNAKLAR}
    for h in hastaliklar:
        kaynak_sayisi[bk.kaynak(urun, h["ad"])] += 1

    bocek: dict[str, Any] | None = None
    try:
        from bocek import karar as kr
        from bocek import tarla_zararli as tz
        zararlilar = tz.urune_gore(urun)
        esiksiz, kalintisizsiz = [], []
        for z in zararlilar:
            k = kr.karar(z["ad"])
            adim = {a["adim"]: a for a in k["adimlar"]}
            if adim[1]["durum"] == "eşik bilinmiyor":
                esiksiz.append(z["ad"])
            if adim[2]["durum"] == "yok":
                kalintisizsiz.append(z["ad"])
        bocek = {
            "zararli": len(zararlilar),
            "esigi_bilinmeyen": esiksiz,
            "kalintisiz_yolu_olmayan": kalintisizsiz,
        }
    except ImportError:  # pragma: no cover - böcek katmanı yoksa
        bocek = None

    return {
        "urun": urun,
        "hastalik": len(hastaliklar),
        "kaynak_dagilimi": kaynak_sayisi,
        "topraktan_etken": {
            "tur": sorted(topraktan_etkenler()[urun]["tur"]),
            "cins": sorted(topraktan_etkenler()[urun]["cins"]),
        },
        "bocek": bocek,
    }


# --------------------------------------------------------- alan ağırlığı
# Çift SAYMAK yanıltıcı olabilir: 36 çiftin hepsi aynı büyüklükte toprakta
# dönmüyor. Muş'ta buğday ekili alanın %62'si, arpa %22'si. Kararın
# değdiği yer, çiftin kaç tane olduğu değil ne kadar toprağı tuttuğu.
#
# Çiftler toprağı bölüştürmediği için payları TOPLANMAZ — toplamak aynı
# dekarı birkaç kez sayar. Bu yüzden burada toplam değil, çiftler alanına
# göre SIRALANIR ve kararları yanlarına yazılır.

def _tr(x: float, basamak: int = 0) -> str:
    """Türkçe sayı: binlik nokta, ondalık virgül.

    Metnin içine f-string ile basılan ham sayı binliği virgülle yazıyordu
    ve cümleyi düzeltmek için yapılan topluca virgül->nokta değişimi
    cümlenin kendi noktalamasını da bozdu. Biçimleme artık tek yerde.
    """
    gov = f"{x:,.{basamak}f}"
    return gov.replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")


def _alanlar() -> dict[str, float]:
    """Ürün -> il genelinde ekili dekar."""
    tablo: dict[str, float] = dict.fromkeys(mp.URUN, 0.0)
    for ilce in mp.ILCE:
        for urun, kayit in mp.DESEN[ilce].items():
            if urun in tablo:
                tablo[urun] += float(kayit[0])
    return tablo


def baskin_ciftler(adet: int = 5) -> list[dict[str, Any]]:
    """Alan olarak en büyük ürün çiftleri ve münavebe kararları."""
    alan = _alanlar()
    toplam = sum(alan.values()) or 1.0
    sirali = sorted(matris(),
                    key=lambda m: -(alan[m["urunler"][0]] + alan[m["urunler"][1]]))
    cikti = []
    for m in sirali[:adet]:
        a, b = m["urunler"]
        cikti.append({
            "urunler": (a, b), "durum": m["durum"],
            "tur_ortak": m["tur_ortak"],
            "alan_dekar": alan[a] + alan[b],
            "alan_payi": (alan[a] + alan[b]) / toplam,
        })
    return cikti


def pancar_tavani() -> dict[str, Any]:
    """Baskıyı kıran münavebe fabrika kotasıyla sınırlı mı.

    ÇATININ YAKALADIĞI ÇELİŞKİ: 2. kısım "pancarla münavebe yap" diyor,
    çünkü topraktan bulaşan baskıyı kıran tek çift pancarlı. 1. kısım ise
    pancar alanının Muş Şeker Fabrikası tavanıyla sınırlı olduğunu
    söylüyor. İkisi ayrı sekmelerde dururken çelişki görünmüyordu.

    mus_analiz buradan içe aktarılmıyor, fonksiyon içinde aktarılıyor:
    mus_analiz zaten bu modülü kullanıyor ve tepe seviyesinde karşılıklı
    aktarım döngü yapar.
    """
    import mus_analiz as ma  # döngüyü kırmak için fonksiyon içinde

    kota = ma.kota_ozeti()
    alan = _alanlar()
    toplam = sum(alan.values()) or 1.0
    kiran = kiran_ciftler()
    pancarli = [c for c in kiran if "Şeker pancarı" in c]
    tavan = float(kota["tavan_alan_dekar"])
    return {
        "kiran_cift": kiran,
        "kiran_cift_pancarli": pancarli,
        "pancar_alan_dekar": float(kota["mevcut_alan_dekar"]),
        "pancar_tavan_dekar": tavan,
        "bos_alan_dekar": float(kota["bos_alan_dekar"]),
        "il_ekili_dekar": toplam,
        "tavandaki_pay": tavan / toplam,
        "celiski": bool(pancarli) and len(kiran) == len(pancarli),
        "aciklama": (
            "Topraktan bulaşan baskıyı kıran münavebenin tamamı pancara "
            "dayanıyor. Pancar alanı ise agronomiyle değil fabrika "
            "kotasıyla sınırlı: tavan "
            f"{_tr(tavan)} dekar, yani il ekili alanının yalnızca "
            f"%{_tr(100 * tavan / toplam, 1)} kadarı. Dolayısıyla bu "
            "münavebe en iyi durumda ilin ekili alanının yirmide birinde "
            "uygulanabilir; geri kalan alan için projenin elinde "
            "'münavebe baskıyı kırar' diyecek bir dayanak yok."),
    }


def baskin_cift_bulgusu() -> str:
    """Alan olarak en büyük çiftin kararını tek cümlede."""
    en = baskin_ciftler(1)[0]
    a, b = en["urunler"]
    pay = _tr(100 * en["alan_payi"])
    if en["durum"] == "kırmaz":
        ortak = ", ".join(en["tur_ortak"])
        return (f"Muş'ta ekili alanın %{pay} kadarı {a} ve {b} arasında "
                "dönüyor — ve bu ikisi topraktan bulaşan aynı etkeni "
                f"paylaşıyor ({ortak}). Yani fiilen uygulanan münavebe, kök "
                "çürüklüğü baskısını kırmayan münavebedir.")
    return (f"Alan olarak en büyük çift {a} – {b} (%{pay} kadarı) ve "
            f"münavebe kararı: {en['durum']}.")


def ozet() -> dict[str, Any]:
    """Çatının topluca söylediği."""
    m = matris()
    sayac = {d: len([x for x in m if x["durum"] == d]) for d in DURUM}
    return {
        "urun": len(mp.URUN), "cift": len(m), "durum_sayilari": sayac,
        "kiran_ciftler": kiran_ciftler(),
        "bulgu": (f"{len(m)} ürün çiftinden yalnızca {sayac['kırar']} "
                  f"tanesi topraktan bulaşan baskıyı kırıyor; "
                  f"{sayac['kırmaz']} çiftte ortak etken kayıtlı, "
                  f"{sayac['belirsiz']} çiftte katalog tür yazmadığı için "
                  "söylenemiyor. 'Münavebe hastalık baskısını kırar' "
                  "cümlesi bu yüzden daraltıldı."),
    }


def bosluklar() -> list[dict[str, Any]]:
    """Çatının cevap VEREMEDİĞİ yerler — masa başından kapanmayanlar dahil."""
    cins_kalan = sorted({c for m in matris() for c in m["cins_ortak"]})
    return [
        {"boşluk": "Anastomoz grubu (AG) kaydı yok",
         "etki": "'Aynı tür kayıtlı' diyebiliyoruz, 'tarlada aynı suş "
                 "geçiyor' diyemiyoruz. Rhizoctonia solani'de AG konakçıya "
                 "göre ayrışır.",
         "kapanmasi": "İzolat teşhisi gerekir; masa başından kapanmaz.",
         "masa_basi": False},
        {"boşluk": f"Cins düzeyinde kalan etkenler: {', '.join(cins_kalan)}",
         "etki": "Bu cinslerin geçtiği çiftlerde münavebe kararı belirsiz "
                 "kalıyor; katalog tür yazmıyor.",
         "kapanmasi": "ZMTT ve fitopatoloji kaynaklarında tür düzeyi kayıt "
                      "aranabilir — masa başı iş.",
         "masa_basi": True},
        {"boşluk": "Bulaş kaynağı atamaları Bakanlık belgesinden "
                   "doğrulanmadı",
         "etki": "Topraktan/havadan ayrımı literatüre dayanıyor; yanlış bir "
                 "atama münavebe kararını da yanlışlar.",
         "kapanmasi": "Danışman hocanın gözden geçirmesi (bulas_kaynagi.py "
                      "kendi başlığında da bunu yazıyor).",
         "masa_basi": True},
    ]


def denetle() -> list[str]:
    """Veri tutarlılığı: çatı iki kısmı okuyor, ikisi de yerinde mi."""
    sorun: list[str] = []
    t = topraktan_etkenler()
    for urun in mp.URUN:
        if urun not in t:
            sorun.append(f"{urun}: topraktan etken tablosunda yok")
    for m in matris():
        if m["durum"] not in DURUM:
            sorun.append(f"{m['urunler']}: tanınmayan durum {m['durum']}")
        if m["durum"] == "kırmaz" and not m["tur_ortak"]:
            sorun.append(f"{m['urunler']}: kırmaz dendi ama ortak tür yok")
    return sorun


def pancar_buyutme_uyarisi(ilce: str) -> dict[str, Any]:
    """Pancar alanını büyütme önerisi toprak katmanına soruldu mu.

    1. kısım fabrika kotasında boşluk görünce "sözleşmeli alan GÜVENLE
    büyütülebilir" diyordu. Toprak katmanına sorulmamıştı: altı ilçenin
    altısında da pancar puanı TAVANLANMIŞ durumda ve tavanı koyan şey
    telafi edilemeyen bir kısıt (Liebig'in minimum yasası).

    Merkez ve Bulanık'ta o kısıt DRENAJ. Drenaj aynı zamanda pancarın
    Rhizoctonia kök çürüklüğünün sevdiği koşul ve o hastalık katalogda
    önem 3. Yani "güvenle" kelimesi tam olarak drenajın zayıf olduğu
    yerde eksik kalıyor.

    Bu, pancarı büyütmeye karşı bir uyarı değil: kıran tek münavebe
    pancarlı (bkz. pancar_tavani). Söylenen şey, sıranın drenajda
    olduğu.
    """
    import mus_toprak as mt  # tepe seviyede aktarılmıyor: mus_analiz'in
    # toprak katmanından bağımsız kalması bilerek korunuyor

    u = mt.uygunluk(ilce, "Şeker pancarı")
    kisit = u.get("kisitlayici")
    tavanli = bool(u.get("tavanlandi"))
    drenajli = kisit == "drenaj"
    return {
        "ilce": ilce, "puan": u.get("puan"), "sinif": u.get("sinif"),
        "tavanlandi": tavanli, "kisitlayici": kisit,
        "drenaj_kisiti": drenajli,
        "cumle": (
            "Sözleşmeli alan büyütülebilir, ama bu ilçede pancar "
            "uygunluğunun tavanını DRENAJ koyuyor ve drenaj aynı zamanda "
            "pancarın Rhizoctonia kök çürüklüğüne uygun koşuldur. Önce "
            "tahliye, sonra alan."
            if drenajli else
            f"Sözleşmeli alan büyütülebilir; bu ilçede uygunluğun tavanını "
            f"{kisit} koyuyor ve bu telafi edilemeyen bir kısıt."
            if tavanli else
            "Sözleşmeli alan büyütülebilir; toprak tarafında tavan koyan "
            "bir kısıt görünmüyor."),
    }


# ------------------------------------------------------------- panel verisi
def panel_verisi() -> dict[str, Any]:
    """Panelin "Çatı" sekmesinin okuduğu veri.

    Matris JSON'a tam hâliyle gömülüyor: 36 kayıt küçük, ve kararın
    gerekçesini panelde göstermek bu modülün bütün amacı. Gerekçesiz bir
    "kırmaz" rozeti, daralttığımız sözün yerine yeni bir slogan koymak
    olurdu.
    """
    return {
        "var": True,
        "ozet": ozet(),
        "matris": [{"urunler": list(m["urunler"]), "durum": m["durum"],
                    "tur_ortak": m["tur_ortak"], "cins_ortak": m["cins_ortak"],
                    "gerekce": m["gerekce"], "sinir": m["sinir"]}
                   for m in matris()],
        "baskin": [{"urunler": list(c["urunler"]), "durum": c["durum"],
                    "tur_ortak": c["tur_ortak"],
                    "alan_dekar": c["alan_dekar"], "alan_payi": c["alan_payi"]}
                   for c in baskin_ciftler(6)],
        "baskin_bulgu": baskin_cift_bulgusu(),
        "tavan": pancar_tavani(),
        "yuk": [urun_yuku(u) for u in mp.URUN],
        "bosluklar": bosluklar(),
    }


def uret() -> dict[str, Any]:
    """outputs/cati.json üretir."""
    import json
    from pathlib import Path

    veri = panel_verisi()
    cikti = Path(__file__).resolve().parent.parent / "outputs"
    cikti.mkdir(exist_ok=True)
    (cikti / "cati.json").write_text(
        json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    return veri


def main() -> None:
    veri = uret()
    o = veri["ozet"]
    print(o["bulgu"])
    print()
    print(veri["baskin_bulgu"])
    print()
    print(veri["tavan"]["aciklama"])
    sorun = denetle()
    if sorun:
        print("\nTUTARSIZLIK:")
        for x in sorun:
            print("  -", x)


if __name__ == "__main__":
    main()
