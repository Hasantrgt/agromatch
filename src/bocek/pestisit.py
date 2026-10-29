"""
AGROMATCH - Pestisit yükü ve kalıntısız yol
============================================
Üçüncü kısmın karar katmanı. İki soruyu cevaplar:

    1. Bir zararlıya karşı kullanılan ilaç grubu, zararlının yanında
       BAŞKA NEYİ öldürüyor?
    2. O gruba başvurmadan önce denenebilecek ne var?

NE YAPMAZ — ve bu bilerek böyledir
-----------------------------------
Bu modül ÜRÜN ADI VERMEZ, DOZ VERMEZ, REÇETE YAZMAZ. Türkiye'de bitki
koruma ürünü tavsiyesi reçete yazma yetkisi olan kişilerin işidir ve
ruhsatlı ürün listesi Bakanlık'ın BKÜ kayıtlarından gelir, bir yazılımın
belleğinden değil. Burada tutulan şey ETKİ MEKANİZMASI GRUBUDUR: bir
grubun neye etki ettiği, neye zarar verdiği ve direnç açısından ne anlama
geldiği. Bu bilgi tavsiye değil, karşılaştırma ölçütüdür.

Pratikte fark şu: "şu ilacı at" demek yerine "bu gruba girersen arıyı ve
sünenin parazitoitini de vurursun, önce şunları dene" demek.

PESTİSİT YÜKÜ
-------------
Tek bir sayı değil, üç ayrı eksende ölçülür ve öyle gösterilir:

    canliya_zarar   kaç faydalı türü vuruyor
    kalinti         hasat öncesi bekleme süresi (gün)
    direnc          o grupta direnç gelişme riski

Üçünü tek puana indirmiyoruz; çünkü hangisinin daha önemli olduğu
üreticinin durumuna göre değişir (ihracat yapan için kalıntı, arıcılık da
yapan için canlıya zarar belirleyicidir).
"""

from __future__ import annotations

from typing import Any

SEVIYE = {"yüksek": 3, "orta": 2, "düşük": 1, "yok": 0}

ETKI_GRUPLARI: tuple[dict[str, Any], ...] = (
    {
        "grup": "piretroit", "ad": "Piretroitler", "irac": "3A",
        "etki_sekli": "sinir sisteminde sodyum kanalını açık bırakır",
        "sistemik": False, "genis_etkili": True,
        "ariya_toksik": "yüksek", "parazitoite_toksik": "yüksek",
        "direnc_riski": "yüksek", "kalinti_suresi_gun": (7, 21),
        "hedef": ("Süne", "Kımıl", "Patates böceği", "Pancar piresi",
                  "Yonca hortumlu böceği", "Bozkurt"),
        "kaynak": "literatür",
        "not_": ("Hızlı ve ucuz olduğu için en çok kullanılan grup. Geniş "
                 "etkili olması tam da sorunudur: hedefi de, doğal "
                 "düşmanı da aynı anda vurur."),
    },
    {
        "grup": "neonikotinoid", "ad": "Neonikotinoidler", "irac": "4A",
        "etki_sekli": "sinir hücresindeki nikotinik reseptöre bağlanır",
        "sistemik": True, "genis_etkili": True,
        "ariya_toksik": "yüksek", "parazitoite_toksik": "orta",
        "direnc_riski": "yüksek", "kalinti_suresi_gun": (14, 28),
        "hedef": ("Yeşil şeftali yaprak biti", "Bakla yaprak biti",
                  "Hububat yaprak bitleri", "Yonca yaprak biti",
                  "Patates böceği"),
        "kaynak": "literatür",
        "not_": ("Sistemik olduğu için bitkinin içine geçer ve poleni ile "
                 "nektarına da ulaşır — arı açısından kritik grup. "
                 "Avrupa'da birkaç etkili maddesi açık alanda yasaklandı; "
                 "Türkiye'deki güncel durum Bakanlık BKÜ kayıtlarından "
                 "TEYİT EDİLMELİDİR."),
    },
    {
        "grup": "organik_fosforlu", "ad": "Organik fosforlular", "irac": "1B",
        "etki_sekli": "asetilkolinesteraz enzimini bloke eder",
        "sistemik": False, "genis_etkili": True,
        "ariya_toksik": "yüksek", "parazitoite_toksik": "yüksek",
        "direnc_riski": "yüksek", "kalinti_suresi_gun": (14, 30),
        "hedef": ("Süne", "Kımıl", "Pancar sineği", "Mısır kurdu",
                  "Ekin kambur böceği"),
        "kaynak": "literatür",
        "not_": ("Memeli toksisitesi de yüksek olan eski bir grup; birçok "
                 "etkili maddesi kullanımdan kalktı. Uygulayıcı güvenliği "
                 "ayrı bir konudur."),
    },
    {
        "grup": "diamid", "ad": "Diamidler", "irac": "28",
        "etki_sekli": "kas hücresinde kalsiyum salınımını bozar",
        "sistemik": True, "genis_etkili": False,
        "ariya_toksik": "düşük", "parazitoite_toksik": "düşük",
        "direnc_riski": "orta", "kalinti_suresi_gun": (3, 14),
        "hedef": ("Mısır kurdu", "Patates güvesi"),
        "kaynak": "literatür",
        "not_": ("Kelebek larvalarına seçici; arı ve parazitoite nispeten "
                 "güvenli. Seçici grupların örneği — 'ilaç = kötü' değil, "
                 "'geniş etkili ilaç = pahalı' demek daha doğru."),
    },
    {
        "grup": "bt", "ad": "Bacillus thuringiensis", "irac": "11A",
        "etki_sekli": "larvanın bağırsak çeperini delen protein kristali",
        "sistemik": False, "genis_etkili": False,
        "ariya_toksik": "yok", "parazitoite_toksik": "düşük",
        "direnc_riski": "orta", "kalinti_suresi_gun": (0, 3),
        "hedef": ("Mısır kurdu", "Patates böceği", "Patates güvesi"),
        "kaynak": "literatür",
        "not_": ("Biyolojik kökenli, organik üretimde kullanılabilir. "
                 "Yalnızca YUTAN larvaya etkilidir; zamanlama kritiktir, "
                 "larva sapa girdikten sonra işe yaramaz."),
    },
    {
        "grup": "mineral", "ad": "İnert tozlar (diyatomlu toprak)", "irac": "—",
        "etki_sekli": "kütikuladaki mum tabakasını aşındırır, böcek kurur",
        "sistemik": False, "genis_etkili": False,
        "ariya_toksik": "düşük", "parazitoite_toksik": "düşük",
        "direnc_riski": "yok", "kalinti_suresi_gun": (0, 0),
        "hedef": ("Fasulye tohum böceği", "Patates güvesi"),
        "kaynak": "literatür",
        "not_": ("Zehirleme yok, fiziksel etki var — bu yüzden DİRENÇ "
                 "GELİŞMEZ. Depo kısmının merkezindeki yöntem. Tarlada "
                 "yağmurla yıkandığı için asıl yeri kapalı ortamdır; "
                 "etkisi sıcaklık ve neme bağlıdır (bkz. Depo sekmesi)."),
    },
    {
        "grup": "kulturel", "ad": "Kültürel ve fiziksel yöntemler", "irac": "—",
        "etki_sekli": "zararlının barınma, üreme ya da beslenme koşulunu bozar",
        "sistemik": False, "genis_etkili": False,
        "ariya_toksik": "yok", "parazitoite_toksik": "yok",
        "direnc_riski": "yok", "kalinti_suresi_gun": (0, 0),
        "hedef": ("Ekin sap arısı", "Ekin kambur böceği", "Mısır kurdu",
                  "Bozkurt", "Yonca hortumlu böceği", "Baklagil tohum "
                  "hortumluları", "Fasulye tohum böceği"),
        "kaynak": "literatür",
        "not_": ("Ekim nöbeti, anız parçalama, erken biçim, ekim zamanı "
                 "kaydırma, tuzakla izleme. Kalıntısı ve direnci olmayan "
                 "tek grup; bedeli işgücü ve planlamadır."),
    },
    {
        "grup": "biyolojik", "ad": "Biyolojik mücadele (salım)", "irac": "—",
        "etki_sekli": "doğal düşmanı çoğaltıp tarlaya bırakma",
        "sistemik": False, "genis_etkili": False,
        "ariya_toksik": "yok", "parazitoite_toksik": "yok",
        "direnc_riski": "yok", "kalinti_suresi_gun": (0, 0),
        "hedef": ("Mısır kurdu", "Süne", "Yonca hortumlu böceği"),
        "kaynak": "literatür",
        "not_": ("Trichogramma salımı mısır kurdunda uygulanan bir yöntem. "
                 "Maliyet ve tedarik sorunu var; ama ilaç kullanılan "
                 "tarlada işe yaramaz — ikisi birlikte olmaz. Yonca "
                 "hortumlu böceğinde entomopatojen mantar Beauveria "
                 "talimatta doğal düşman olarak adı geçen etmendir."),
    },
)

KIMYASAL = ("piretroit", "neonikotinoid", "organik_fosforlu", "diamid")
KALINTISIZ = ("kulturel", "biyolojik", "bt", "mineral")


def grup(ad: str) -> dict[str, Any]:
    for g in ETKI_GRUPLARI:
        if g["grup"] == ad:
            return g
    raise KeyError(ad)


def zararliya_gore(zararli: str) -> list[dict[str, Any]]:
    """Bir zararlıya karşı kullanılan grupları yükü hafiften ağıra sıralar."""
    uygun = [g for g in ETKI_GRUPLARI if zararli in g["hedef"]]
    return sorted(uygun, key=lambda g: (
        SEVIYE[g["ariya_toksik"]] + SEVIYE[g["parazitoite_toksik"]],
        g["kalinti_suresi_gun"][1], SEVIYE[g["direnc_riski"]]))


def yuk(grup_adi: str, faydalilar: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    """Bir grubun üç eksendeki yükü ve somut olarak neyi vurduğu."""
    g = grup(grup_adi)
    vurulan = [f["ad"] for f in faydalilar if grup_adi in f["hassasiyet"]]
    return {
        "grup": grup_adi, "ad": g["ad"], "irac": g["irac"],
        "canliya_zarar": len(vurulan),
        "vurulan": vurulan,
        "kalinti_gun": g["kalinti_suresi_gun"],
        "direnc": g["direnc_riski"],
        "kimyasal": grup_adi in KIMYASAL,
    }


def kalintisiz_yol(zararli: str) -> list[dict[str, Any]]:
    """O zararlı için kalıntı bırakmayan seçenekler.

    Boş dönerse bu bir cevaptır, eksiklik değil: o zararlı için elimizde
    kalıntısız bir yol YOK demektir ve panelde öyle yazılır.
    """
    return [g for g in ETKI_GRUPLARI
            if zararli in g["hedef"] and g["grup"] in KALINTISIZ]


def kapsanmayan(zararli_adlari: list[str]) -> list[str]:
    """Hiçbir grubun hedefinde görünmeyen zararlılar."""
    hedefli = {h for g in ETKI_GRUPLARI for h in g["hedef"]}
    return [z for z in zararli_adlari if z not in hedefli]


def ozet() -> dict[str, Any]:
    return {
        "grup": len(ETKI_GRUPLARI),
        "kimyasal": len(KIMYASAL),
        "kalintisiz": len(KALINTISIZ),
        "direnc_yok": [g["grup"] for g in ETKI_GRUPLARI
                       if g["direnc_riski"] == "yok"],
        "ariya_yuksek": [g["grup"] for g in ETKI_GRUPLARI
                         if g["ariya_toksik"] == "yüksek"],
    }


def denetle(zararli_adlari: set[str] | None = None) -> list[str]:
    hata = []
    adlar = [g["grup"] for g in ETKI_GRUPLARI]
    if len(adlar) != len(set(adlar)):
        hata.append("yinelenen grup adı var")
    for g in ETKI_GRUPLARI:
        for alan in ("ariya_toksik", "parazitoite_toksik", "direnc_riski"):
            if g[alan] not in SEVIYE:
                hata.append(f'{g["grup"]}: {alan} geçersiz ({g[alan]})')
        alt, ust = g["kalinti_suresi_gun"]
        if alt > ust or alt < 0:
            hata.append(f'{g["grup"]}: kalıntı süresi aralığı bozuk')
        if g["grup"] in KALINTISIZ and ust > 3:
            hata.append(f'{g["grup"]}: kalıntısız sayıldı ama bekleme {ust} gün')
        if not g["hedef"]:
            hata.append(f'{g["grup"]}: hedef listesi boş')
        if zararli_adlari is not None:
            for h in g["hedef"]:
                if h not in zararli_adlari:
                    hata.append(f'{g["grup"]}: katalogda olmayan hedef "{h}"')
    if set(KIMYASAL) & set(KALINTISIZ):
        hata.append("bir grup hem kimyasal hem kalıntısız sayılmış")
    return hata


if __name__ == "__main__":
    import faydali as fy
    import tarla_zararli as tz

    adlar = {z["ad"] for z in tz.ZARARLILAR}
    for h in denetle(adlar):
        print("HATA:", h)

    o = ozet()
    print(f"{o['grup']} etki grubu · {o['kimyasal']} kimyasal · "
          f"{o['kalintisiz']} kalıntısız")
    print(f"Direnç gelişmeyen: {', '.join(o['direnc_yok'])}")
    print(f"Arıya yüksek toksik: {', '.join(o['ariya_yuksek'])}")

    print("\nGrup başına pestisit yükü:")
    for g in ETKI_GRUPLARI:
        y = yuk(g["grup"], fy.FAYDALILAR)
        print(f"  {y['ad']:38s} faydalı vurulan {y['canliya_zarar']}  "
              f"bekleme {y['kalinti_gun'][0]}-{y['kalinti_gun'][1]} gün  "
              f"direnç {y['direnc']}")

    print("\nKalıntısız yolu OLMAYAN zararlılar:")
    for z in tz.ZARARLILAR:
        if not kalintisiz_yol(z["ad"]):
            print(f'  {z["ad"]} ({"/".join(z["urunler"])})')

    eksik = kapsanmayan([z["ad"] for z in tz.ZARARLILAR])
    if eksik:
        print(f"\nHiçbir grubun hedefinde olmayan: {', '.join(eksik)}")
