"""
AGROMATCH - Doğrulama kontrol listesi üretir
=============================================
Böcek katmanının hangi kayıtlarının doğrulanmadığını, danışman hocanın
tek oturumda işaretleyebileceği bir belgeye döker.

Neden böyle bir şey var: dört eşik iddiasından üçü yanlış çıktı (süne,
patates böceği, yonca hortumlu böceği). Kalan kayıtlarda da hata olma
ihtimali yüksek ve bunları tek tek belgeden doğrulamak yavaş. Entomolog
bir hoca aynı listeye bakıp dakikalar içinde "bu yanlış, bu eksik"
diyebilir.

Belge, kataloğun KENDİSİNDEN üretilir; katalog değişince yeniden
üretilir ve liste asla bayatlamaz.

    python src/bocek/dogrulama_listesi.py
"""

from __future__ import annotations

from pathlib import Path

from bocek import faydali as fy
from bocek import pestisit as ps
from bocek import tarla_zararli as tz

KOK = Path(__file__).resolve().parent.parent.parent
HEDEF = KOK / "belgeler" / "dogrulama_listesi.md"

AY = ("Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem",
      "Ağu", "Eyl", "Eki", "Kas", "Ara")


def aylar(nums: tuple[int, ...]) -> str:
    return " ".join(AY[a - 1] for a in nums)


def basliklar() -> list[str]:
    dogrulanmis = [z for z in tz.ZARARLILAR if z["kaynak"] == "ZMTT"]
    bekleyen = [z for z in tz.ZARARLILAR if z["kaynak"] != "ZMTT"]
    return [
        "# AGROMATCH — böcek katmanı doğrulama listesi",
        "",
        "> Bu belge koddan üretilir (`src/bocek/dogrulama_listesi.py`).",
        "> Elle düzenlemeyin; katalog değişince yeniden üretin.",
        "",
        "## Niçin",
        "",
        "Böcek katmanı hızlı yazıldı ve sonradan dört eşik iddiası resmî",
        "kaynakla karşılaştırıldı. **Üçü yanlış çıktı:**",
        "",
        "| zararlı | yazılan | resmî kaynak |",
        "|---|---|---|",
        "| Süne | 0,5 ergin/m² ya da 10 nimf/m² | eşik yok; parazitlenme "
        "oranına bağlı karar tablosu |",
        "| Patates böceği | 2 larva kümesi / %15 yaprak | \"eşik "
        "bulunmamaktadır\"; %20 (→%40) tolerans |",
        "| Yonca hortumlu böceği | sap başına 3 larva | m²'de 25 larva "
        "veya ergin |",
        "",
        "Dördüncüsünde (ekin kambur böceği) eşik hiç yazılmamıştı, "
        "belgede vardı.",
        "",
        f"Bugün **{len(dogrulanmis)} kayıt** belgeye bağlı, "
        f"**{len(bekleyen)} kayıt** bekliyor. Aşağıdaki listede her satır "
        "için sorulacak şey yazılı; cevaplar işaretlenince katalog "
        "güncellenecek.",
        "",
    ]


def zararli_bolumu() -> list[str]:
    s = ["## 1. Tarla zararlıları", ""]
    for z in tz.ZARARLILAR:
        dogru = z["kaynak"] == "ZMTT"
        isaret = "✅ doğrulandı" if dogru else "⬜ bekliyor"
        s += [f"### {z['ad']} — *{z['latince']}* · {isaret}", ""]
        s += [f"- **Ürün:** {', '.join(z['urunler'])}",
              f"- **Zarar:** {z['zarar_sekli'].replace('_', ' ')} · "
              f"{z['hedef_organ']}",
              f"- **Kritik aylar:** {aylar(tuple(z['kritik_aylar']))}",
              f"- **Eşik:** {z['esik'] or '— yazılmadı'}"
              + (f"  *(kaynak: {z['esik_kaynak']})*" if z["esik_kaynak"] else ""),
              f"- **Doğal düşman:** {', '.join(z['dogal_dusman']) or '— yazılmadı'}"]
        if z["vektor"]:
            s += [f"- **Taşıdığı hastalık:** {', '.join(z['vektor'])}"]
        if z["depoda_da"]:
            s += ["- **Depoda da görülür**"]
        if not dogru:
            sorular = ["Muş'ta ekonomik zarar yapıyor mu, yoksa listeden "
                       "çıkarılmalı mı?"]
            if not z["esik"]:
                sorular.append("Ekonomik zarar eşiği var mı? Varsa kaç, "
                               "hangi birimle?")
            else:
                sorular.append(f"Yazılan eşik doğru mu: *{z['esik']}*?")
            if not fy.hedefe_gore(z["ad"]):
                sorular.append("Bu türü baskılayan doğal düşman var mı?")
            sorular.append(f"Kritik aylar Muş için doğru mu "
                           f"({aylar(tuple(z['kritik_aylar']))})?")
            if not ps.kalintisiz_yol(z["ad"]):
                sorular.append("Kalıntı bırakmayan bir yöntem var mı? "
                               "(şu an 'yok' yazıyor)")
            s += ["", "**Sorulacak:**"]
            s += [f"{i}. {q}" for i, q in enumerate(sorular, 1)]
        s += [""]
    return s


def faydali_bolumu() -> list[str]:
    s = ["## 2. Faydalılar", "",
         "Hiçbiri Bakanlık belgesiyle doğrulanmadı.", "",
         "| faydalı | rol | baskıladığı | hassas olduğu gruplar |",
         "|---|---|---|---|"]
    for f in fy.FAYDALILAR:
        s.append(f"| {f['ad']} | {f['rol']} | "
                 f"{', '.join(f['hedef']) or '—'} | "
                 f"{', '.join(f['hassasiyet'])} |")
    s += ["", "**Sorulacak:**",
          "1. Muş'ta bu türler gerçekten var mı, hangileri baskın?",
          "2. Listede olmayıp olması gereken var mı?",
          "3. Hassasiyet sütunu doğru mu — hangi grup hangisini vuruyor?",
          "4. Süne parazitlenme sürveyi Muş'ta yapılıyor mu, oranlar ne "
          "düzeyde?",
          ""]
    return s


def pestisit_bolumu() -> list[str]:
    s = ["## 3. Etki grupları", "",
         "IRAC grup kodları ve etki yeri tanımları **doğrulandı** "
         "(IRAC Mode of Action brochure Ed. 6). Toksisite değerleri "
         "genellemedir; etkili maddeye göre değişir.", "",
         "Hasat öncesi bekleme süresi bu tabloda **bilerek yok** — o süre "
         "ürün etiketinde, etkili madde ve kültür bitkisi bazında yazar.", "",
         "| grup | IRAC | arıya | parazitoite | direnç | kalıntı |",
         "|---|---|---|---|---|---|"]
    for g in ps.ETKI_GRUPLARI:
        s.append(f"| {g['ad']} | {g['irac']} | {g['ariya_toksik']} | "
                 f"{g['parazitoite_toksik']} | {g['direnc_riski']} | "
                 f"{'bırakır' if g['kalinti'] else 'bırakmaz'} |")
    s += ["", "**Sorulacak:**",
          "1. Arıya ve parazitoite toksisite sütunları grup düzeyinde "
          "savunulabilir mi, yoksa etkili madde düzeyine inmeli mi?",
          "2. Muş'ta fiilen hangi gruplar kullanılıyor?",
          "3. Direnç gözlenen bir zararlı var mı?",
          ""]
    return s


def uret() -> str:
    s = basliklar() + zararli_bolumu() + faydali_bolumu() + pestisit_bolumu()
    s += ["---", "",
          "## Cevaplar geldiğinde",
          "",
          "Her düzeltme için kataloğa yazılacak iki şey var: **değer** ve "
          "**kaynak**. Hocanın sözlü teyidi bir belge değildir — kayıt "
          "`kaynak=\"uzman görüşü\"` olarak işaretlenmeli ve hangi belgeye "
          "dayandığı sorulmalı. Proje bugüne kadar bu ayrımı koruduğu için "
          "ayakta.",
          ""]
    return "\n".join(s)


def main() -> None:
    HEDEF.parent.mkdir(exist_ok=True)
    metin = uret()
    HEDEF.write_text(metin, encoding="utf-8")
    bekleyen = sum(1 for z in tz.ZARARLILAR if z["kaynak"] != "ZMTT")
    print(f"{HEDEF} yazıldı ({len(metin.splitlines())} satır)")
    print(f"  {bekleyen} zararlı doğrulama bekliyor")


if __name__ == "__main__":
    main()
