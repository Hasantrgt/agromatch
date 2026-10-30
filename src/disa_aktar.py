"""
AGROMATCH - Bütün veri setlerini tek pakette dışa aktarır
==========================================================
Danışman hocaya ya da başka bir araştırmacıya verilecek paketi üretir.
Üç biçimde aynı veri:

    veri/AGROMATCH_Veri_Setleri.xlsx   sayfa başına bir veri seti
    veri/csv/*.csv                      Python/pandas için (virgül, UTF-8)
    veri/csv_excel/*_excel.csv          Excel için (noktalı virgül, BOM)

Düz CSV'yi Excel'de açarsan Türkçe harfler bozulur; bu yüzden iki sürüm
var ve adları birbirinden ayrı.

KÜNYE
-----
Pakette en önemli dosya veri setlerinin kendisi değil, KÜNYE sayfasıdır:
her veri setinin kaç satır olduğu, nereden geldiği ve DOĞRULANIP
DOĞRULANMADIĞI orada yazılı. Bir veri setini alıp kullanacak kişinin
önce bakması gereken yer orasıdır — hangi sayının ölçüm, hangisinin
literatür, hangisinin sentetik olduğunu başka türlü anlayamaz.

    python src/disa_aktar.py
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "outputs"
HEDEF = KOK / "veri"

# Veri türleri ve ne anlama geldikleri — künyede açıklanır
TUR_ACIKLAMA = {
    "ölçüm": "sahada ya da laboratuvarda ölçülmüş",
    "resmî": "Bakanlık/TÜİK belgesinden alınmış",
    "literatür": "bilimsel yayından alınmış, Bakanlık belgesiyle doğrulanmamış",
    "model": "projedeki bir modelin çıktısı, ölçüm değil",
    "sentetik": "bilgisayarda üretilmiş; GERÇEK VERİ DEĞİLDİR",
}


def _yaz(ad: str, basliklar: list[str], satirlar: list[list[Any]]) -> int:
    """Bir veri setini iki CSV biçiminde de yazar."""
    (HEDEF / "csv").mkdir(parents=True, exist_ok=True)
    (HEDEF / "csv_excel").mkdir(parents=True, exist_ok=True)

    with open(HEDEF / "csv" / f"{ad}.csv", "w", encoding="utf-8",
              newline="") as f:
        y = csv.writer(f)
        y.writerow(basliklar)
        y.writerows(satirlar)
    with open(HEDEF / "csv_excel" / f"{ad}_excel.csv", "w",
              encoding="utf-8-sig", newline="") as f:
        y = csv.writer(f, delimiter=";")
        y.writerow(basliklar)
        y.writerows(satirlar)
    return len(satirlar)


def _duzle(v: Any) -> Any:
    """Liste ve sözlükleri hücreye sığacak biçime indirger."""
    if isinstance(v, (list, tuple)):
        return " | ".join(str(x) for x in v)
    if isinstance(v, dict):
        return " | ".join(f"{k}={x}" for k, x in v.items())
    if isinstance(v, bool):
        return "evet" if v else "hayır"
    return "" if v is None else v


def _sozlukten(ad: str, kayitlar: list[dict[str, Any]],
               alanlar: list[str] | None = None) -> int:
    if not kayitlar:
        return _yaz(ad, ["(veri yok)"], [])
    basliklar = alanlar or list(kayitlar[0])
    return _yaz(ad, basliklar,
                [[_duzle(k.get(b)) for b in basliklar] for k in kayitlar])


def _json_oku(ad: str) -> dict[str, Any] | None:
    yol = CIKTI / ad
    if not yol.exists():
        return None
    return json.loads(yol.read_text(encoding="utf-8"))


# --------------------------------------------------------- veri setleri
# (dosya adı, açıklama, tür, üretici)
KAYIT: list[tuple[str, str, str, Callable[[], int]]] = []


def kaydet(ad: str, aciklama: str, tur: str):
    def sar(f: Callable[[], int]):
        KAYIT.append((ad, aciklama, tur, f))
        return f
    return sar


@kaydet("hastalik_katalogu", "Muş'un dokuz ürününde görülen hastalıklar; "
        "bulaş kaynağı sınıflamasıyla birlikte", "literatür")
def _hastalik() -> int:
    import bulas_kaynagi as bk
    kayit = []
    for h in bk.zenginlestir():
        alt, ust = h["sicaklik_opt"]
        kayit.append({
            "urun": h["urun"], "hastalik": h["ad"], "patojen": h["patojen"],
            "tip": h["tip"], "onem": h["onem"],
            "bulas_kaynagi": h["bulas"],
            "bulas_ikincil": h["bulas_ikincil"], "proje_kismi": h["kisim"],
            "karantina": h["karantina"], "kaynak": h["kaynak"],
            "goruntuden_tespit": h["goruntuden"],
            "sicaklik_alt": alt, "sicaklik_ust": ust,
            "nem_esik_mm": h["nem_esik"], "kritik_aylar": h["kritik_aylar"],
            "belirti": h["belirti"], "yonetim": h["yonetim"],
        })
    return _sozlukten("hastalik_katalogu", kayit)


@kaydet("hastalik_risk", "İlçe × ürün × hastalık risk satırları", "model")
def _risk() -> int:
    d = _json_oku("mus_hastalik.json")
    return _sozlukten("hastalik_risk", d["satirlar"] if d else [])


@kaydet("tarla_zararlilari", "Muş'ta ekonomik önemi olan tarla böcekleri",
        "literatür")
def _zararli() -> int:
    from bocek import tarla_zararli as tz
    return _sozlukten("tarla_zararlilari", [
        {"ad": z["ad"], "latince": z["latince"], "urunler": z["urunler"],
         "onem": z["onem"], "zarar_sekli": z["zarar_sekli"],
         "hedef_organ": z["hedef_organ"], "kritik_aylar": z["kritik_aylar"],
         "tasidigi_hastalik": z["vektor"], "ekonomik_esik": z["esik"],
         "esik_kaynagi": z["esik_kaynak"], "ambarda_da": z["depoda_da"],
         "dogal_dusman": z["dogal_dusman"], "kaynak": z["kaynak"],
         "belirti": z["belirti"], "not": z["not_"]}
        for z in tz.ZARARLILAR])


@kaydet("faydalilar", "Tozlayıcı, parazitoit ve avcı türler", "literatür")
def _faydali() -> int:
    from bocek import faydali as fy
    return _sozlukten("faydalilar", [
        {"ad": f["ad"], "latince": f["latince"], "rol": f["rol"],
         "onem": f["onem"], "baskiladigi": f["hedef"],
         "hassas_oldugu_gruplar": f["hassasiyet"], "etkin_aylar": f["mevsim"],
         "ne_yapar": f["ne_yapar"], "korumak_icin": f["korumak_icin"],
         "kaynak": f["kaynak"]}
        for f in fy.FAYDALILAR])


@kaydet("etki_gruplari", "İnsektisit etki mekanizması grupları ve pestisit "
        "yükü (ÜRÜN ADI VE DOZ İÇERMEZ)", "literatür")
def _grup() -> int:
    from bocek import faydali as fy
    from bocek import pestisit as ps
    return _sozlukten("etki_gruplari", [
        {"grup": g["grup"], "ad": g["ad"], "irac_kodu": g["irac"],
         "etki_sekli": g["etki_sekli"], "sistemik": g["sistemik"],
         "genis_etkili": g["genis_etkili"], "ariya_toksik": g["ariya_toksik"],
         "parazitoite_toksik": g["parazitoite_toksik"],
         "direnc_riski": g["direnc_riski"], "kalinti_birakir": g["kalinti"],
         "hedef_zararlilar": g["hedef"],
         "vurdugu_faydalilar": ps.yuk(g["grup"], fy.FAYDALILAR)["vurulan"],
         "not": g["not_"], "kaynak": g["kaynak"]}
        for g in ps.ETKI_GRUPLARI])


@kaydet("depo_zararlilari", "Depolanmış ürün zararlıları", "literatür")
def _depo_z() -> int:
    from depo import depo_profil as dp
    return _sozlukten("depo_zararlilari", list(dp.ZARARLILAR))


@kaydet("depo_mucadele", "Depoda kullanılan mücadele yöntemleri", "literatür")
def _depo_m() -> int:
    from depo import depo_profil as dp
    return _sozlukten("depo_mucadele", list(dp.MUCADELE))


@kaydet("literatur_doz_cevap",
        "Sitophilus granarius × diyatomlu toprak: iki yayından alınan "
        "doz–ölüm ölçümleri", "literatür")
def _lit() -> int:
    from depo import literatur as lit
    kayit = []
    for calisma, urun, doz, sure, yuzde in lit.OLCUMLER:
        c = lit.CALISMALAR[calisma]
        n = c.n_hucre
        kayit.append({
            "yayin": calisma, "urun": urun, "doz_ppm": doz, "sure_gun": sure,
            "olum_yuzde": yuzde, "denenen": n, "olen": round(yuzde / 100 * n),
            "sicaklik_c": c.sicaklik, "nem_yuzde": c.nem, "tahil": c.urun,
            "abbott_uygulandi": c.abbott, "kontrol_notu": c.kontrol_notu,
            "yazarlar": c.yazarlar, "yil": c.yil, "dergi": c.dergi,
            "doi": c.doi,
        })
    return _sozlukten("literatur_doz_cevap", kayit)


@kaydet("doz_cevap_kestirim",
        "Yukarıdaki ölçümlerden probit modelle kestirilen LC değerleri "
        "(yayınların KENDİSİ bu sayıları vermiyor)", "model")
def _lc() -> int:
    d = _json_oku("depo.json")
    if not d:
        return _yaz("doz_cevap_kestirim", ["(veri yok)"], [])
    kayit = []
    for s in d["doz_cevap"]["seriler"]:
        satir = {"yayin": s["kaynak"], "urun": s["etiket"],
                 "sure_gun": s["sure"], "egim": s["egim"],
                 "n_gozlem": s["n_gozlem"], "n_birey": s["n_birey"],
                 "denenen_doz_alt": s["doz_araligi"][0],
                 "denenen_doz_ust": s["doz_araligi"][1]}
        for ad in ("LC50", "LC90", "LC95"):
            k = s["lc"].get(ad, {})
            satir[f"{ad}_ppm"] = k.get("deger", "")
            satir[f"{ad}_alt"] = k.get("alt", "")
            satir[f"{ad}_ust"] = k.get("ust", "")
            satir[f"{ad}_durum"] = k.get("kestirilemedi",
                                         "aralık dışı" if k.get("disinda")
                                         else "kestirildi" if k.get("deger")
                                         else "")
        kayit.append(satir)
    return _sozlukten("doz_cevap_kestirim", kayit)


@kaydet("ambar_sicakligi", "İlçe × ay: dış hava ve tahıl yığını sıcaklığı",
        "model")
def _ambar() -> int:
    from depo import ambar_sicaklik as amb
    a = amb.analiz()
    kayit = []
    for ilce in a["aylik_yigin"]:
        for i, ay in enumerate(amb.AY_AD):
            kayit.append({"ilce": ilce, "ay": ay, "ay_no": i + 1,
                          "dis_hava_c": a["dis_hava"][ilce][i],
                          "yigin_c": a["aylik_yigin"][ilce][i],
                          "sonumleme": a["sonumleme"]})
    return _sozlukten("ambar_sicakligi", kayit)


@kaydet("gelisme_penceresi",
        "İlçe × depo zararlısı: yığın sıcaklığının gelişme eşiğini aştığı "
        "ay sayısı", "model")
def _pencere() -> int:
    from depo import ambar_sicaklik as amb
    return _sozlukten("gelisme_penceresi", amb.analiz()["satirlar"])


@kaydet("erken_uyari_takvimi", "İlçe × ay uyarı listesi", "model")
def _uyari() -> int:
    d = _json_oku("uyari.json")
    if not d:
        return _yaz("erken_uyari_takvimi", ["(veri yok)"], [])
    return _sozlukten("erken_uyari_takvimi",
                      [u for lst in d["uyarilar"].values() for u in lst])


@kaydet("karlilik", "İlçe × ürün net gelir simülasyonu", "model")
def _kar() -> int:
    d = _json_oku("karlilik.json")
    return _sozlukten("karlilik", d["satirlar"] if d else [])


@kaydet("piyasa_girdileri", "Karlılık hesabının fiyat/maliyet girdileri — "
        "HİÇBİRİ MUŞ İÇİN DOĞRULANMAMIŞTIR", "model")
def _piyasa() -> int:
    d = _json_oku("karlilik.json")
    return _sozlukten("piyasa_girdileri", d["piyasa"] if d else [])


@kaydet("urun_denge", "İlçe × ürün: alan, üretim, ihtiyaç, denge durumu",
        "resmî")
def _denge() -> int:
    d = _json_oku("mus.json")
    return _sozlukten("urun_denge", d["denge"] if d else [])


@kaydet("ilce_profili", "İlçe temel bilgileri: rakım, nüfus, "
        "hayvan varlığı, mera, iklim", "resmî")
def _ilce() -> int:
    d = _json_oku("mus.json")
    return _sozlukten("ilce_profili", d["ilceler"] if d else [])


@kaydet("toprak_uygunluk", "Toprak uygunluk veri seti (veri madenciliği)",
        "sentetik")
def _toprak() -> int:
    kaynak = KOK / "data" / "madencilik" / "toprak.csv"
    if not kaynak.exists():
        return _yaz("toprak_uygunluk", ["(üretilmemiş)"], [])
    with open(kaynak, encoding="utf-8") as f:
        r = list(csv.reader(f))
    return _yaz("toprak_uygunluk", r[0], r[1:])


@kaydet("cercospora_lezyon", "Cercospora lezyon öznitelikleri "
        "(veri madenciliği)", "sentetik")
def _lezyon() -> int:
    kaynak = KOK / "data" / "madencilik" / "lezyonlar.csv"
    if not kaynak.exists():
        return _yaz("cercospora_lezyon", ["(üretilmemiş)"], [])
    with open(kaynak, encoding="utf-8") as f:
        r = list(csv.reader(f))
    return _yaz("cercospora_lezyon", r[0], r[1:])


@kaydet("00_veri_kunyesi", "Projedeki her girdinin kaynağı, türü ve güven "
        "derecesi — paketin en önemli ikinci dosyası", "resmî")
def _proje_kunye() -> int:
    d = _json_oku("mus.json")
    return _sozlukten("00_veri_kunyesi", d["kunye"] if d else [])


@kaydet("toprak_uygunluk_modeli",
        "İlçe × ürün toprak+iklim uygunluk puanı, darboğaz ve kısıtla "
        "birlikte (GERÇEK model çıktısı; sentetik madencilik setiyle "
        "karıştırılmamalı)", "model")
def _toprak_model() -> int:
    d = _json_oku("mus_toprak.json")
    if not d:
        return _yaz("toprak_uygunluk_modeli", ["(veri yok)"], [])
    kayit = []
    for u in d["urun_karsilastirma"]:
        for i in u["ilceler"]:
            kayit.append({"urun": u["urun"], **i})
    return _sozlukten("toprak_uygunluk_modeli", kayit)


@kaydet("ilce_toprak_profili", "İlçe toprak analizi değerleri ve sağlık "
        "puanı", "model")
def _ilce_toprak() -> int:
    d = _json_oku("mus_toprak.json")
    if not d:
        return _yaz("ilce_toprak_profili", ["(veri yok)"], [])
    kayit = []
    for i in d["ilceler"]:
        s = {"ilce": i["ilce"], "bunye": i.get("bunye")}
        s.update({f"toprak_{k}": v for k, v in i["toprak"].items()})
        sag = i.get("saglik", {})
        s["saglik_puan"] = sag.get("puan")
        s["saglik_harf"] = sag.get("harf")
        kayit.append(s)
    return _sozlukten("ilce_toprak_profili", kayit)


@kaydet("olcum_oncelikleri",
        "Hangi ölçüm belirsizliği en çok azaltır — bilgi değeri sıralaması",
        "model")
def _oncelik() -> int:
    d = _json_oku("mus_belirsizlik.json")
    if not d:
        return _yaz("olcum_oncelikleri", ["(veri yok)"], [])
    return _sozlukten("olcum_oncelikleri", [
        {"girdi": o["etiket"], "tur": o["tur"], "yontem": o["yontem"],
         "kim": o["kim"], "masa_basi": o["masa_basi"], "emek": o["emek"],
         "toplam_kazanc": o["toplam_kazanc"],
         "en_yuksek_pay": o["en_yuksek_pay"],
         "etkiledigi_sorular": [e["soru"] for e in o["etkiledigi"]]}
        for o in d["genel_oncelik"]])


@kaydet("denge_karari", "Ürün × soru: fazla mı açık mı, karar belirsiz mi",
        "model")
def _karar() -> int:
    d = _json_oku("mus_belirsizlik.json")
    return _sozlukten("denge_karari", d["karar"] if d else [])


@kaydet("olcum_duyarliligi",
        "Laboratuvar hatasının ürün bazında uygunluk kararını ne kadar "
        "bozduğu", "model")
def _duyarlilik() -> int:
    d = _json_oku("toprak_urun_duyarlilik.json")
    return _sozlukten("olcum_duyarliligi", d["urunler"] if d else [])


@kaydet("yem_dengesi", "İlçe kaba yem arz-talep dengesi", "model")
def _yem() -> int:
    d = _json_oku("mus.json")
    return _sozlukten("yem_dengesi", d["yem"] if d else [])


@kaydet("su_ve_karbon", "İlçe × ürün su tüketimi, enerji ve karbon",
        "model")
def _su() -> int:
    d = _json_oku("mus.json")
    return _sozlukten("su_ve_karbon", d["kaynak"] if d else [])


@kaydet("ilce_karnesi", "Dört başlıkta ilçe puanlaması", "model")
def _karne() -> int:
    d = _json_oku("mus.json")
    if not d:
        return _yaz("ilce_karnesi", ["(veri yok)"], [])
    return _sozlukten("ilce_karnesi", [
        {"sira": r["sira"], "ilce": r["ilce"], "toplam": r["toplam"],
         **{f"puan_{k}": v for k, v in r["puan"].items()},
         "etkin_urun": r["etkin_urun"], "yem_acik_ton": r["yem_acik_ton"],
         "not": r["not_"]}
        for r in d["karne"]])


@kaydet("ilce_onerileri", "İlçe bazında öncelik sıralı öneriler", "model")
def _oneri() -> int:
    d = _json_oku("mus.json")
    if not d:
        return _yaz("ilce_onerileri", ["(veri yok)"], [])
    kayit = [{"ilce": o["ilce"], **m} for o in d["oneri"] for m in o["maddeler"]]
    return _sozlukten("ilce_onerileri", kayit)


@kaydet("il_uretim", "İl toplamı üretim, alan ve verim", "resmî")
def _uretim() -> int:
    d = _json_oku("mus.json")
    return _sozlukten("il_uretim", d["uretim"] if d else [])


@kaydet("alan_olcumleri", "İl düzeyinde ölçülmüş temel büyüklükler",
        "resmî")
def _olcum() -> int:
    d = _json_oku("mus.json")
    return _sozlukten("alan_olcumleri", d["olcum"] if d else [])


@kaydet("hastalik_ilce_ozeti", "İlçe başına hastalık sayısı ve en riskli "
        "üçlü", "model")
def _hast_ilce() -> int:
    d = _json_oku("mus_hastalik.json")
    if not d:
        return _yaz("hastalik_ilce_ozeti", ["(veri yok)"], [])
    return _sozlukten("hastalik_ilce_ozeti", [
        {"ilce": i["ilce"], "hastalik_sayisi": i["hastalik_sayisi"],
         "yuksek_riskli": i["yuksek_riskli"],
         "ortalama_risk": i["ortalama_risk"],
         "en_riskli": [f"{x['ad']} ({x['urun']}) {x['risk']}"
                       for x in i["en_riskli"]]}
        for i in d["ilce_ozet"]])


@kaydet("goruntuden_tespit_onceligi",
        "Görüntü işlemeyle tespit edilebilecek hastalıkların önceliği",
        "model")
def _goruntu() -> int:
    d = _json_oku("mus_hastalik.json")
    return _sozlukten("goruntuden_tespit_onceligi",
                      d["goruntu_oncelik"] if d else [])


@kaydet("zararli_takvimi", "Zararlı × ay ızgarası (1 = etkin)", "literatür")
def _z_takvim() -> int:
    d = _json_oku("bocek.json")
    if not d:
        return _yaz("zararli_takvimi", ["(veri yok)"], [])
    aylar = d["aylar"]
    return _sozlukten("zararli_takvimi", [
        {"zararli": t["ad"], "urunler": t["urunler"], "onem": t["onem"],
         **{aylar[i]: v for i, v in enumerate(t["aylar"])}}
        for t in d["takvim"]])


@kaydet("yayin_kunyeleri", "Doz–cevap verisinin alındığı yayınların tam "
        "künyeleri ve deneme koşulları", "literatür")
def _yayin() -> int:
    from depo import literatur as lit
    return _sozlukten("yayin_kunyeleri", [
        {"kod": c.kod, "yazarlar": c.yazarlar, "yil": c.yil,
         "baslik": c.baslik, "dergi": c.dergi, "doi": c.doi,
         "sicaklik_c": c.sicaklik, "nem_yuzde": c.nem, "tahil": c.urun,
         "birey_basina_kap": c.birey_basina_kap, "tekrar": c.tekrar,
         "hucre_basina_birey": c.n_hucre, "abbott": c.abbott,
         "kontrol_notu": c.kontrol_notu, "not": c.not_}
        for c in lit.CALISMALAR.values()])


@kaydet("deneme_sablonu", "Hocanın kendi ham sayımlarını girmesi için boş "
        "şablon — doldurulup --veri ile verilince aynı grafik gerçek "
        "veriyle çizilir", "ölçüm")
def _sablon() -> int:
    kaynak = KOK / "data" / "deneme_sablonu.csv"
    if not kaynak.exists():
        return _yaz("deneme_sablonu", ["(yok)"], [])
    metin = kaynak.read_text(encoding="utf-8-sig")
    ayrac = ";" if metin.splitlines()[0].count(";") else ","
    r = list(csv.reader(metin.splitlines(), delimiter=ayrac))
    return _yaz("deneme_sablonu", r[0], r[1:])



@kaydet("hesap_izi_belirsiz_girdiler",
        "Hesap ağacındaki belirsiz girdiler: aralıkları, gerekçeleri ve "
        "nasıl ölçüleceği", "model")
def _iz() -> int:
    d = _json_oku("mus_iz.json")
    if not d:
        return _yaz("hesap_izi_belirsiz_girdiler", ["(veri yok)"], [])
    kayit = []
    for s in d["sorular"]:
        for g in s.get("duyarlilik", []):
            y = g.get("olcum_yolu") or {}
            kayit.append({
                "soru": s["baslik"], "olcek": s["olcek"],
                "girdi": g["ad"], "birim": g.get("birim"),
                "alt": g["aralik"][0] if g.get("aralik") else None,
                "orta": g["aralik"][1] if len(g.get("aralik", [])) > 1 else None,
                "ust": g["aralik"][-1] if g.get("aralik") else None,
                "gerekce": g.get("gerekce"),
                "olcum_yontemi": y.get("yontem"),
                "olcum_miktari": y.get("miktar"),
                "olcum_birimi": y.get("birim"),
            })
    return _sozlukten("hesap_izi_belirsiz_girdiler", kayit)


@kaydet("urun_toprak_istegi", "Ürünlerin toprak istekleri (modelin "
        "kalibrasyon tablosu)", "literatür")
def _istek() -> int:
    d = _json_oku("mus_toprak.json")
    if not d:
        return _yaz("urun_toprak_istegi", ["(veri yok)"], [])
    return _sozlukten("urun_toprak_istegi",
                      [{"urun": u, **v} for u, v in d["urun_istek"].items()])


@kaydet("puan_agirliklari", "Toprak uygunluk puanının bileşen ağırlıkları",
        "model")
def _agirlik() -> int:
    d = _json_oku("mus_toprak.json")
    if not d:
        return _yaz("puan_agirliklari", ["(veri yok)"], [])
    return _sozlukten("puan_agirliklari",
                      [{"bilesen": k, "agirlik": v}
                       for k, v in d["agirlik"].items()])


@kaydet("hastalik_aylik_takvim", "Ay × sıcaklık × o ay kritik olan "
        "hastalıklar", "model")
def _h_takvim() -> int:
    d = _json_oku("mus_hastalik.json")
    if not d:
        return _yaz("hastalik_aylik_takvim", ["(veri yok)"], [])
    return _sozlukten("hastalik_aylik_takvim", [
        {"ay_no": a["ay"], "ay": a["ad"], "sicaklik_c": a["sicaklik"],
         "hastalik_sayisi": len(a["hastaliklar"]),
         "hastaliklar": [h if isinstance(h, str) else h.get("ad", "")
                         for h in a["hastaliklar"]]}
        for a in d["takvim"]])


@kaydet("seker_kotasi", "Muş Şeker Fabrikası kapasite ve doluluk "
        "(TEYİT EDİLMEDİ)", "model")
def _kota() -> int:
    d = _json_oku("mus.json")
    if not d:
        return _yaz("seker_kotasi", ["(veri yok)"], [])
    return _sozlukten("seker_kotasi", [d["kota"]])



# ----------------------------------------------------------------- paket


def kunye(sayilar: dict[str, int]) -> list[list[Any]]:
    return [[ad, sayilar.get(ad, 0), tur, TUR_ACIKLAMA[tur], aciklama]
            for ad, aciklama, tur, _f in KAYIT]


def excel(sayilar: dict[str, int]) -> Path | None:
    try:
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        return None

    KOYU, YAZI = "1F4733", "Arial"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "KUNYE"
    ws.append(["veri seti", "satır", "tür", "tür ne demek", "açıklama"])
    for h in ws[1]:
        h.font = Font(name=YAZI, bold=True, size=9, color="FFFFFF")
        h.fill = PatternFill("solid", fgColor=KOYU)
        h.alignment = Alignment(horizontal="center", vertical="center",
                                wrap_text=True)
    for s in kunye(sayilar):
        ws.append(s)
    for s in ws.iter_rows(min_row=2):
        for h in s:
            h.font = Font(name=YAZI, size=9)
            h.alignment = Alignment(vertical="top", wrap_text=True)
        if s[2].value == "sentetik":
            for h in s:
                h.fill = PatternFill("solid", fgColor="F6DDD8")
    for i, g in enumerate((26, 8, 11, 34, 54), start=1):
        ws.column_dimensions[get_column_letter(i)].width = g
    ws.freeze_panes = "A2"

    # Excel sayfa adı 31 karakterle sınırlı
    for ad, _acik, _tur, _f in KAYIT:
        yol = HEDEF / "csv" / f"{ad}.csv"
        if not yol.exists():
            continue
        with open(yol, encoding="utf-8") as f:
            satir = list(csv.reader(f))
        if len(satir) > 50_000:      # Excel'i şişirmemek için
            continue
        s = wb.create_sheet(ad[:31])
        for r in satir:
            s.append(r)
        for h in s[1]:
            h.font = Font(name=YAZI, bold=True, size=9, color="FFFFFF")
            h.fill = PatternFill("solid", fgColor=KOYU)
            h.alignment = Alignment(wrap_text=True, vertical="center")
        s.freeze_panes = "A2"
        s.auto_filter.ref = f"A1:{get_column_letter(len(satir[0]))}{len(satir)}"
        for i in range(1, len(satir[0]) + 1):
            s.column_dimensions[get_column_letter(i)].width = 18

    hedef = HEDEF / "AGROMATCH_Veri_Setleri.xlsx"
    wb.save(hedef)
    return hedef


def main() -> None:
    HEDEF.mkdir(exist_ok=True)
    sayilar: dict[str, int] = {}
    for ad, _aciklama, _tur, f in KAYIT:
        sayilar[ad] = f()
        print(f"  {ad:26s} {sayilar[ad]:>7} satır")

    _yaz("00_KUNYE", ["veri_seti", "satir", "tur", "tur_ne_demek", "aciklama"],
         kunye(sayilar))

    # Elle yazılan iki belge pakete kopyalanıyor; kaynakları belgeler/
    # altında ve sürüm takibinde. Pakette durmaları, paketi tek başına
    # anlaşılır kılmak için.
    import shutil
    for kaynak, ad in ((KOK / "belgeler" / "veri_paketi_beniokui.md", "BENIOKU.md"),
                       (KOK / "belgeler" / "dogrulama_listesi.md",
                        "dogrulama_listesi.md")):
        if kaynak.exists():
            shutil.copy2(kaynak, HEDEF / ad)

    x = excel(sayilar)
    toplam = sum(sayilar.values())
    print(f"\n{len(KAYIT)} veri seti · {toplam:,} satır")
    print(f"  CSV (Python)  : {HEDEF / 'csv'}")
    print(f"  CSV (Excel)   : {HEDEF / 'csv_excel'}")
    print(f"  Çalışma kitabı: {x if x else 'openpyxl yok, üretilmedi'}")


if __name__ == "__main__":
    main()
