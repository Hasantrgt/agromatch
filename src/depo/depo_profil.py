"""
AGROMATCH - Depolanmış buğday: zararlılar ve mücadele seçenekleri
==================================================================
Tarla modülleri hasada kadar olanı hesaplar. Bu modül hasattan SONRASINI
kapsar: ambardaki buğdaya ne oluyor.

NEDEN AYRI BİR KATMAN
Buğday biti (Sitophilus granarius) tarlada değil depoda zarar verir ve
üstelik uçamaz — bulaşma tarladan değil, ambarda kalan eski üründen ve
bulaşık çuvaldan gelir. Yani mücadelesi de tarla mücadelesinden bambaşka:
ekim nöbeti, çeşit seçimi, ilaçlama takvimi burada işe yaramaz; depo
temizliği, sıcaklık yönetimi ve tane koruması işe yarar.

İKİ KATALOG
    ZARARLILAR   buğdayın depo zararlıları, gelişme eşikleriyle
    MUCADELE     kullanılabilen yöntemler, kalıntı ve direnç profiliyle

SINIR — burası ilaç tavsiyesi vermez
MUCADELE kataloğu yöntemleri TANITIR; hangi ürünün hangi dozda
kullanılacağını söylemez. Türkiye'de bu karar reçete yazma yetkisi olan
kişilerindir. Ruhsatlı ürün ve doz bilgisi için Bakanlığın Bitki Koruma
Ürünleri Veri Tabanı (bku.tarimorman.gov.tr) kaynaktır.

Bu kataloğun amacı farklı: bir yöntemin KALINTI bırakıp bırakmadığını,
DİRENÇ geliştirip geliştirmediğini ve faydalı organizmaya ne yaptığını
yan yana koymak. "Pestisitten arındırılmış yol" ancak bu karşılaştırma
yapılabilirse çizilebilir.

KAYNAK DİSİPLİNİ
tarla tarafındaki hastalık kataloğuyla aynı: `kaynak` alanı "ZMTT" ise
Bakanlık belgesinden, "literatür" ise yayından alınmış ve DOĞRULANMAMIŞ
demektir. Gelişme eşikleri özellikle dikkat ister — literatürde tür ve
çalışmaya göre değişir, bu yüzden hepsi "literatür" ve danışman hocanın
düzeltmesine açık.

    python src/depo/depo_profil.py
"""

from typing import Any

# ---------------------------------------------------------------------------
# ZARARLILAR
#
# ic_besleyen: larva tanenin İÇİNDE gelişir. Bu ayrım iki yerde belirleyici:
#   - tespit: içeriden beslenen larva dışarıdan görünmez, numune kırılmadan
#     ya da görüntü/akustik yöntemle bakılmadan sayılamaz
#   - mücadele: temas yoluyla etki eden toz ve ilaçlar tanenin içine
#     ulaşamaz, yalnızca ergine etki eder
#
# taban_sicaklik: gelişmenin durduğu eşik (°C). LİTERATÜR DEĞERİ, tür ve
# çalışmaya göre değişir; Muş ambar modelinde doğrudan kullanıldığı için
# danışman hocanın teyit etmesi gereken ilk sayı budur.
# ---------------------------------------------------------------------------

ZARARLILAR: list[dict[str, Any]] = [
    dict(ad="Buğday biti", tur="Sitophilus granarius", sinif="kın kanatlı",
         ic_besleyen=True, ucabilir=False, karantina=False, onem=3,
         taban_sicaklik=11.0, optimum_sicaklik=(26, 30), optimum_nem=(65, 75),
         en_dusuk_tane_nemi=9.5,
         belirti="Tanede yuvarlak çıkış delikleri; tane sağlam görünür ama "
                 "içi boşalmıştır. Yığında ısınma ve küflenme eşlik eder",
         zarar="Ağırlık kaybı, çimlenme gücünün düşmesi, un kalitesinin bozulması",
         not_="Uçamaz: bulaşma tarladan değil, ambarda kalan eski üründen, "
              "çuvaldan ve makineden gelir. Depo temizliği bu yüzden en etkili "
              "önlemdir",
         kaynak="literatür"),
    dict(ad="Küçük tahıl kurdu", tur="Rhyzopertha dominica", sinif="kın kanatlı",
         ic_besleyen=True, ucabilir=True, karantina=False, onem=3,
         taban_sicaklik=18.0, optimum_sicaklik=(32, 35), optimum_nem=(50, 70),
         en_dusuk_tane_nemi=8.0,
         belirti="Tanede düzensiz delikler ve bol un tozu; kendine has keskin koku",
         zarar="Hem larva hem ergin beslenir; kuru tanede bile ilerleyebilir",
         not_="Uçabildiği için yeni depoya dışarıdan girer. Buğday bitinden "
              "daha sıcak sever, Muş koşullarında daha sınırlı kalması beklenir",
         kaynak="literatür"),
    dict(ad="Un biti", tur="Tribolium castaneum", sinif="kın kanatlı",
         ic_besleyen=False, ucabilir=True, karantina=False, onem=2,
         taban_sicaklik=20.0, optimum_sicaklik=(32, 35), optimum_nem=(60, 75),
         en_dusuk_tane_nemi=10.0,
         belirti="Kırık tane ve unda yoğunlaşır; ürüne küf ve keskin koku verir",
         zarar="İkincil zararlı: sağlam taneyi delemez, önce başkası delmelidir",
         not_="Varlığı tek başına değil, birincil zararlıyla birlikte okunmalı — "
              "bu böcek görülüyorsa yığında zaten delinmiş tane var demektir. "
              "AD DÜZELTİLDİ: kayıt önce 'Kırma biti' diyordu, oysa ZMTT "
              "Cilt I'de Kırma biti Tribolium CONFUSUM'dur; T. castaneum'un "
              "resmî Türkçe adı Un biti. Tür verisi (optimum 32-35 °C) "
              "castaneum'a uyuyordu, bu yüzden tür korundu ve ad düzeltildi",
         kaynak="literatür"),
    dict(ad="Testereli böcek", tur="Oryzaephilus surinamensis", sinif="kın kanatlı",
         ic_besleyen=False, ucabilir=False, karantina=False, onem=2,
         taban_sicaklik=18.0, optimum_sicaklik=(30, 33), optimum_nem=(70, 80),
         en_dusuk_tane_nemi=10.5,
         belirti="Göğsünün kenarındaki testere dişleriyle tanınır; kırık tanede çoğalır",
         zarar="İkincil zararlı; nem ve küflenmeyi artırır",
         not_="Yassı gövdesiyle çuval dikişinden ve ambalaj aralığından geçer",
         kaynak="literatür"),
    dict(ad="Khapra böceği", tur="Trogoderma granarium", sinif="kın kanatlı",
         ic_besleyen=False, ucabilir=False, karantina=True, onem=3,
         taban_sicaklik=21.0, optimum_sicaklik=(33, 37), optimum_nem=(25, 50),
         en_dusuk_tane_nemi=6.0,
         belirti="Larva kılları ve gömlekleri ürüne karışır; ergin nadir görülür",
         zarar="Kuraklığa ve açlığa olağanüstü dayanıklı; larva yıllarca "
               "beklemeye (diyapoz) girebilir",
         not_="KARANTİNA. Fumigasyona diğer türlerden daha dayanıklıdır. "
              "Şüphe hâlinde İl Tarım ve Orman Müdürlüğü'ne bildirim zorunludur",
         kaynak="literatür"),
    dict(ad="Arpa güvesi", tur="Sitotroga cerealella", sinif="kelebek",
         ic_besleyen=True, ucabilir=True, karantina=False, onem=2,
         taban_sicaklik=16.0, optimum_sicaklik=(26, 30), optimum_nem=(60, 80),
         en_dusuk_tane_nemi=10.0,
         belirti="Tanede ince zarla kapalı çıkış deliği; yığın yüzeyinde uçuşan "
                 "küçük açık kahve kelebekler",
         zarar="Yüzeydeki ilk santimetrelerde yoğunlaşır, derine inmez",
         not_="Yüzeyde kaldığı için yüzey uygulaması etkili olabilir",
         kaynak="literatür"),
    dict(ad="Değirmen güvesi", tur="Ephestia kuehniella", sinif="kelebek",
         ic_besleyen=False, ucabilir=True, karantina=False, onem=2,
         taban_sicaklik=12.0, optimum_sicaklik=(24, 28), optimum_nem=(60, 75),
         en_dusuk_tane_nemi=11.0,
         belirti="Larvanın ördüğü ipek ağlar; un ve elekler topaklanır",
         zarar="Değirmende elek tıkar, üretimi durdurur",
         not_="Un fabrikası ve değirmen için ambardan daha önemli",
         kaynak="literatür"),
    dict(ad="Un akarı", tur="Acarus siro", sinif="akar",
         ic_besleyen=False, ucabilir=False, karantina=False, onem=1,
         taban_sicaklik=7.0, optimum_sicaklik=(21, 25), optimum_nem=(80, 90),
         en_dusuk_tane_nemi=13.0,
         belirti="Tatlımsı-küflü koku; yüzeyde toz görünümlü hareketli kütle",
         zarar="Yüksek nemde patlama yapar; alerjen",
         not_="Nem göstergesidir: un akarı varsa tane nemi %13'ün üzerindedir. "
              "Çözümü ilaç değil kurutmadır",
         kaynak="literatür"),
]


# ---------------------------------------------------------------------------
# MÜCADELE SEÇENEKLERİ
#
# kalinti: üründe ölçülebilir kalıntı bırakır mı (MRL konusu olur mu)
# direnc_riski: zararlının zamanla bağışıklık kazanma riski
# faydaliya: depo faydalılarına (parazitoit arılar, predatör akarlar) etkisi
# organik: organik tarım sertifikasında kullanılabilir mi
# ---------------------------------------------------------------------------

MUCADELE: list[dict[str, Any]] = [
    dict(ad="Diyatomlu toprak (DE)", tip="fiziksel", etken="amorf silis",
         mekanizma="Böceğin kütikülasındaki mum tabakasını aşındırır; "
                   "böcek su kaybından ölür. Zehirleme yoktur",
         kalinti=False, direnc_riski="yok", faydaliya="düşük", organik=True,
         etki_suresi="uzun (kuru kaldığı sürece aylarca)",
         gucu=dict(ergin=True, ic_larva=False),
         kosul="Etkisi düşük nemde artar, yüksek nemde düşer. Sıcaklık arttıkça "
               "böcek daha hareketli olur ve toza daha çok temas eder",
         bedel="Tanenin akıcılığını ve hektolitre ağırlığını düşürür; toz yapar",
         onem=3, kaynak="literatür"),
    dict(ad="Soğuk depolama / havalandırma", tip="fiziksel", etken="sıcaklık",
         mekanizma="Yığın sıcaklığı türün gelişme eşiğinin altına indirilir; "
                   "üreme durur, uzun sürede ölüm görülür",
         kalinti=False, direnc_riski="yok", faydaliya="yok", organik=True,
         etki_suresi="soğuk sürdüğü sürece",
         gucu=dict(ergin=True, ic_larva=True),
         kosul="Soğuk hava gerektirir. Muş'un kışı bu yöntem için elverişlidir; "
               "asıl soru yığının ne kadar hızlı soğuduğudur",
         bedel="Havalandırma fanı ve elektrik; yoğuşmaya dikkat",
         onem=3, kaynak="literatür"),
    dict(ad="Kontrollü atmosfer (CO₂ / N₂)", tip="fiziksel", etken="gaz bileşimi",
         mekanizma="Oksijen düşürülür ya da CO₂ yükseltilir; böcek boğulur",
         kalinti=False, direnc_riski="düşük", faydaliya="yok", organik=True,
         etki_suresi="uygulama süresince",
         gucu=dict(ergin=True, ic_larva=True),
         kosul="Sızdırmaz depo şart; sızdıran ambarda işe yaramaz",
         bedel="Sızdırmazlık yatırımı ve gaz maliyeti",
         onem=2, kaynak="literatür"),
    dict(ad="Isıl işlem", tip="fiziksel", etken="sıcaklık",
         mekanizma="Ortam 50–60 °C'ye çıkarılır; böcek kısa sürede ölür",
         kalinti=False, direnc_riski="yok", faydaliya="yok", organik=True,
         etki_suresi="uygulama anlık, kalıcı koruma yok",
         gucu=dict(ergin=True, ic_larva=True),
         kosul="Daha çok değirmen ve boş depo için; tanenin çimlenme gücü "
               "yüksek sıcaklıkta zarar görebilir",
         bedel="Enerji; tohumluk üründe çimlenme riski",
         onem=1, kaynak="literatür"),
    dict(ad="Fosfin fumigasyonu", tip="kimyasal", etken="alüminyum fosfit",
         mekanizma="Nemle tepkiyerek fosfin gazı açığa çıkarır; solunum "
                   "zinciri engellenir",
         kalinti=True, direnc_riski="YÜKSEK", faydaliya="yüksek", organik=False,
         etki_suresi="uygulama süresince, kalıcı koruma yok",
         gucu=dict(ergin=True, ic_larva=True),
         kosul="Sızdırmaz ortam ve yetkili uygulayıcı zorunlu. Dünya genelinde "
               "yaygın direnç bildirilmiştir; eksik doz direnci hızlandırır",
         bedel="İnsan için yüksek tehlike; uygulama yetkisi gerektirir",
         onem=3, kaynak="literatür"),
    dict(ad="Temas etkili tane koruyucu", tip="kimyasal",
         etken="ruhsatlı etkili maddeler (BKU veri tabanına bakılır)",
         mekanizma="Tane yüzeyine uygulanır, temas eden ergini öldürür",
         kalinti=True, direnc_riski="orta", faydaliya="yüksek", organik=False,
         etki_suresi="haftalar–aylar",
         gucu=dict(ergin=True, ic_larva=False),
         kosul="Ürün ve doz seçimi REÇETE YETKİLİSİNİN kararıdır. Hasat/kullanım "
               "aralığına ve MRL'ye uyulması zorunludur",
         bedel="Kalıntı riski; ihracatta MRL aşımı ürünü geri çevirtir",
         onem=2, kaynak="ZMTT"),
    dict(ad="Depo temizliği ve hijyen", tip="kültürel", etken="—",
         mekanizma="Eski ürün artığı, çuval, elek ve makine temizlenir; "
                   "bulaşma kaynağı ortadan kalkar",
         kalinti=False, direnc_riski="yok", faydaliya="yok", organik=True,
         etki_suresi="kalıcı (tekrarlandığı sürece)",
         gucu=dict(ergin=True, ic_larva=True),
         kosul="Buğday biti uçamadığı için bulaşma neredeyse tamamen bu yolla "
               "olur; bu yüzden tek başına en yüksek getirili önlemdir",
         bedel="İşgücü",
         onem=3, kaynak="ZMTT"),
    dict(ad="Feromon tuzakla izleme", tip="izleme", etken="—",
         mekanizma="Popülasyonu öldürmez, VARLIĞINI ve yoğunluğunu ölçer",
         kalinti=False, direnc_riski="yok", faydaliya="yok", organik=True,
         etki_suresi="—",
         gucu=dict(ergin=True, ic_larva=False),
         kosul="Mücadele değil karar aracıdır: eşik aşıldı mı sorusunu "
               "cevaplar. Gereksiz uygulamayı önleyen asıl yöntem budur",
         bedel="Tuzak ve düzenli sayım",
         onem=3, kaynak="literatür"),
]


KAYNAKLAR = {
    "ZMTT": ("T.C. Tarım ve Orman Bakanlığı belgeleri ve Zirai Mücadele "
             "Teknik Talimatları"),
    "literatür": ("Depo zararlıları literatürü. Gelişme eşikleri tür ve "
                  "çalışmaya göre değişir; danışman hocanın teyidi gerekir."),
}


def denetle() -> list[str]:
    """Katalog tutarlılığını denetler. Boş liste = sorun yok."""
    hatalar: list[str] = []
    for z in ZARARLILAR:
        alt, ust = z["optimum_sicaklik"]
        if not alt < ust:
            hatalar.append(f"{z['ad']}: optimum sıcaklık aralığı ters")
        if not z["taban_sicaklik"] < alt:
            hatalar.append(
                f"{z['ad']}: taban sıcaklık ({z['taban_sicaklik']}) optimumun "
                f"altında olmalı")
        n_alt, n_ust = z["optimum_nem"]
        if not 0 <= n_alt < n_ust <= 100:
            hatalar.append(f"{z['ad']}: nem aralığı geçersiz")
        if z["kaynak"] not in KAYNAKLAR:
            hatalar.append(f"{z['ad']}: bilinmeyen kaynak")
    adlar = [z["ad"] for z in ZARARLILAR]
    if len(adlar) != len(set(adlar)):
        hatalar.append("yinelenen zararlı adı var")

    for m in MUCADELE:
        if m["kaynak"] not in KAYNAKLAR:
            hatalar.append(f"{m['ad']}: bilinmeyen kaynak")
        if m["direnc_riski"] not in ("yok", "düşük", "orta", "YÜKSEK"):
            hatalar.append(f"{m['ad']}: direnç riski değeri tanımsız")
        if m["faydaliya"] not in ("yok", "düşük", "orta", "yüksek"):
            hatalar.append(f"{m['ad']}: faydalıya etki değeri tanımsız")
        if set(m["gucu"]) != {"ergin", "ic_larva"}:
            hatalar.append(f"{m['ad']}: gucu alanı eksik")
        # Kalıntı bırakmayan bir yöntemin direnç riski yüksek olamaz
        if not m["kalinti"] and m["direnc_riski"] == "YÜKSEK":
            hatalar.append(f"{m['ad']}: kalıntısız ama yüksek direnç riski?")
    return hatalar


def kalintisiz_secenekler() -> list[dict[str, Any]]:
    """Kalıntı bırakmayan yöntemler — 'pestisitten arındırılmış yol'un adayları."""
    return [m for m in MUCADELE if not m["kalinti"]]


def ic_larvaya_etkili() -> list[dict[str, Any]]:
    """Tanenin içindeki larvaya ulaşabilen yöntemler.

    Bu ayrım kritik: buğday biti larvası tanenin içinde gelişir. Yalnızca
    ergine etkili bir yöntem, yığındaki gizli bulaşmayı temizlemez — ergin
    çıkışı sürdükçe uygulamanın tekrarı gerekir.
    """
    return [m for m in MUCADELE if m["gucu"]["ic_larva"]]


def ozet() -> dict[str, Any]:
    from collections import Counter
    return dict(
        zararli=len(ZARARLILAR),
        ic_besleyen=sum(1 for z in ZARARLILAR if z["ic_besleyen"]),
        karantina=sum(1 for z in ZARARLILAR if z["karantina"]),
        mucadele=len(MUCADELE),
        kalintisiz=len(kalintisiz_secenekler()),
        ic_larvaya_etkili=len(ic_larvaya_etkili()),
        tip=dict(Counter(m["tip"] for m in MUCADELE)),
        zararli_kaynak=dict(Counter(z["kaynak"] for z in ZARARLILAR)),
    )


if __name__ == "__main__":
    import json

    hatalar = denetle()
    if hatalar:
        print("KATALOG TUTARSIZ:")
        for h in hatalar:
            print("  -", h)
        raise SystemExit(1)
    print("Katalog tutarlı.\n")
    print(json.dumps(ozet(), ensure_ascii=False, indent=2))
    print("\nKalıntı bırakmayan seçenekler:")
    for m in kalintisiz_secenekler():
        ic = "iç larvaya da etkili" if m["gucu"]["ic_larva"] else "yalnızca ergine"
        print(f"  {m['ad']:<34} {m['tip']:<10} {ic}")
