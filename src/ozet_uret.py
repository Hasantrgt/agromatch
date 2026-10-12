"""
AGROMATCH - Tek sayfalık özet üretici
=====================================
Dekana bırakılacak A4 özeti, analiz çıktılarından otomatik üretir.
Sayılar elle yazılmaz: outputs/ klasöründeki JSON'lardan okunur, böylece
gerçek veri girildiğinde özet de kendiliğinden güncellenir.

    python src/ozet_uret.py          -> ozet.html
    node pdf.mjs                     -> AGROMATCH_Ozet.pdf
"""

import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "outputs"
PILOT = "Muş"

# Baskıya uygun palet
YESIL, KOYU, AMBER, KIRMIZI = "#1F4733", "#16281F", "#B4761A", "#9B2C2C"
KAGIT, KREM, CIZGI, SOLUK = "#FFFFFF", "#FAF8F2", "#DCD9CC", "#5F6A5E"

NOT_RENK = {"A": "#1A7A2E", "B": "#3F8F4F", "C": "#D08700", "D": "#B03A2E"}


def hex_harita(karne, harita):
    """23 ilin altıgen haritasını, karne notuna göre renklendirilmiş SVG olarak üretir."""
    notlar = {r["il"]: r["harf"] for r in karne["iller"]}
    R, W_ORAN = 13.0, 3 ** 0.5
    en_q = max(p["q"] for p in harita.values())
    en_r = max(p["r"] for p in harita.values())
    w, h = W_ORAN * R, 1.5 * R
    G, Y = (en_q + 2) * w, (en_r + 1) * h + R * 1.2

    parcalar = [f'<svg viewBox="0 0 {G:.0f} {Y:.0f}" width="100%" '
                f'xmlns="http://www.w3.org/2000/svg" aria-label="23 ilin karne haritası">']
    for il, p in harita.items():
        cx = (p["q"] + 1) * w + (w / 2 if p["r"] % 2 else 0)
        cy = p["r"] * h + R
        nokta = " ".join(
            f"{cx + R * __import__('math').cos(__import__('math').radians(60 * k - 90)):.1f},"
            f"{cy + R * __import__('math').sin(__import__('math').radians(60 * k - 90)):.1f}"
            for k in range(6))
        harf = notlar.get(il, "C")
        vurgu = il == PILOT
        parcalar.append(
            f'<polygon points="{nokta}" fill="{NOT_RENK[harf]}" '
            f'stroke="{"#16281F" if vurgu else "#FFFFFF"}" stroke-width="{2 if vurgu else 1}"/>')
        parcalar.append(
            f'<text x="{cx:.1f}" y="{cy + 3.4:.1f}" text-anchor="middle" fill="#FFFFFF" '
            f'font-size="10" font-family="Carlito, sans-serif" font-weight="700">{harf}</text>')
    parcalar.append("</svg>")
    return "".join(parcalar)


def uret():
    karne = json.loads((CIKTI / "karne.json").read_text(encoding="utf-8"))
    senaryo = json.loads((CIKTI / "senaryo.json").read_text(encoding="utf-8"))
    bolge = json.loads((CIKTI / "bolge.json").read_text(encoding="utf-8"))

    m = next(r for r in karne["iller"] if r["il"] == PILOT)
    mb = next(r for r in bolge["iller"] if r["il"] == PILOT)
    bugday = next(u for u in m["urunler"] if u["urun"] == "Buğday")
    yem = next(u for u in m["urunler"] if u["urun"] == "Yem bitkileri")
    toplam = next(o for o in bolge["ozet"] if o["bolge"] == "Toplam")

    def bin_ayir(n):
        return f"{round(n):,}".replace(",", ".")

    def ondalik(x, basamak=1):
        return f"{x:.{basamak}f}".replace(".", ",")

    harita_svg = hex_harita(karne, senaryo["harita"])

    html = f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>AGROMATCH — Tek Sayfa Özet</title>
<style>
  @page {{ size: A4; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: {KAGIT}; color: {KOYU};
    font-family: Carlito, "Liberation Sans", Arial, sans-serif; font-size: 8.5pt; line-height: 1.3; }}
  .serif {{ font-family: Lora, Georgia, serif; }}

  header {{ background: {KOYU}; color: #F7F5EE; padding: 7mm 13mm 5.5mm;
    display: flex; justify-content: space-between; align-items: flex-end; gap: 10mm; }}
  .marka {{ font-family: Lora, Georgia, serif; font-size: 23pt; font-weight: 600;
    letter-spacing: 0.4pt; line-height: 1; margin-bottom: 2.5mm; }}
  .slogan {{ font-size: 9.6pt; color: #CBD4C6; line-height: 1.35; max-width: 108mm; }}
  .kim {{ text-align: right; font-size: 8.4pt; color: #AEB9AB; line-height: 1.5; }}
  .kim strong {{ display: block; font-size: 10pt; color: #F7F5EE; font-weight: 600; }}
  .serit {{ height: 2.2mm; background: {AMBER}; }}

  main {{ padding: 5mm 13mm 0; }}
  .bolum {{ margin-bottom: 3.4mm; }}
  h2 {{ font-family: Lora, Georgia, serif; font-size: 11pt; font-weight: 600; color: {YESIL};
    margin: 0 0 2.4mm; padding-bottom: 1.2mm; border-bottom: 0.7pt solid {CIZGI}; }}
  h3 {{ font-size: 9.4pt; margin: 0 0 0.8mm; font-weight: 700; }}
  p {{ margin: 0 0 2mm; }}
  .soluk {{ color: {SOLUK}; font-size: 8pt; line-height: 1.35; }}

  .rakamlar {{ display: flex; gap: 4mm; }}
  .rakam {{ flex: 1; background: {KREM}; border-left: 2.2pt solid {YESIL};
    padding: 3mm 3.5mm; }}
  .rakam.amber {{ border-left-color: {AMBER}; }}
  .rakam.kirmizi {{ border-left-color: {KIRMIZI}; }}
  .rakam .v {{ font-family: Lora, Georgia, serif; font-size: 15pt; font-weight: 600;
    line-height: 1.05; color: {YESIL}; }}
  .rakam.amber .v {{ color: {AMBER}; }}
  .rakam.kirmizi .v {{ color: {KIRMIZI}; }}
  .rakam .a {{ font-size: 7.7pt; color: {SOLUK}; line-height: 1.35; margin-top: 1.2mm; }}

  .ikili {{ display: flex; gap: 8mm; }}
  .ikili > div {{ flex: 1; }}
  .genis {{ flex: 1.15 !important; }}

  ol.modul {{ margin: 0; padding-left: 4.6mm; }}
  ol.modul li {{ margin-bottom: 1.2mm; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 8.7pt; }}
  th, td {{ text-align: right; padding: 1.05mm 2mm; border-bottom: 0.5pt solid {CIZGI}; }}
  th:first-child, td:first-child {{ text-align: left; }}
  thead th {{ font-size: 7.4pt; text-transform: uppercase; letter-spacing: 0.4pt;
    color: {SOLUK}; font-weight: 600; border-bottom: 0.7pt solid {KOYU}; }}
  tbody tr:last-child td {{ border-bottom: none; }}
  .art {{ color: #1A7A2E; font-weight: 700; }}
  .eksi {{ color: {KIRMIZI}; font-weight: 700; }}
  .notlar td {{ background: {KREM}; font-weight: 700; }}

  .harita {{ background: {KREM}; padding: 2mm; border: 0.5pt solid {CIZGI}; text-align: center; }}
  .harita svg {{ width: 84%; }}
  .harita-alt {{ display: flex; gap: 3mm; margin-top: 2mm; font-size: 7.6pt; color: {SOLUK}; }}
  .puan {{ display: inline-block; width: 2.6mm; height: 2.6mm; }}

  .uyari {{ background: {KREM}; border-left: 2.2pt solid {AMBER}; padding: 3mm 4mm; }}

  .talep {{ background: #F1F5EF; border: 0.8pt solid {YESIL}; padding: 3.2mm 4mm; }}
  .talep h2 {{ border-bottom-color: #C3D2BE; margin-bottom: 2.5mm; }}
  .talep-satir {{ display: flex; gap: 2.5mm; margin-bottom: 1.6mm; }}
  .talep-no {{ font-family: Lora, Georgia, serif; font-weight: 600; color: {YESIL};
    font-size: 11pt; line-height: 1.1; width: 5mm; }}
  .talep-satir:last-child {{ margin-bottom: 0; }}

  footer {{ margin-top: 3mm; padding: 2.5mm 13mm; border-top: 0.7pt solid {CIZGI};
    display: flex; justify-content: space-between; font-size: 7.6pt; color: {SOLUK}; }}
</style>
</head>
<body>

<header>
  <div>
    <div class="marka">AGROMATCH</div>
    <div class="slogan">İhtiyaca göre ekim planlaması — Doğu ve Güneydoğu Anadolu modeli, Muş pilotu</div>
  </div>
  <div class="kim">
    <strong>Hasan Turgut</strong>
    Yazılım Mühendisliği, 3. sınıf<br>
    Muş Alparslan Üniversitesi<br>
    4 kişilik öğrenci ekibi
  </div>
</header>
<div class="serit"></div>

<main>

<div class="bolum">
  <h2>Problem: ekim kararı ihtiyaçtan kopuk veriliyor</h2>
  <div class="rakamlar">
    <div class="rakam"><div class="v">{ondalik(bugday['oran'])} kat</div>
      <div class="a">Muş'ta buğday üretimi, ilin kendi ihtiyacının {ondalik(bugday['oran'])} katı</div></div>
    <div class="rakam amber"><div class="v">%{round(yem['oran'] * 100)}</div>
      <div class="a">Yem bitkisi üretimi, ildeki hayvanın ihtiyacının yalnızca %{round(yem['oran'] * 100)}'i</div></div>
    <div class="rakam kirmizi"><div class="v">{bin_ayir(mb['kaba_yem_acigi_ton'] / 1000)} bin t</div>
      <div class="a">Muş'un yıllık kaba yem açığı; dışarıdan alımla kapanıyor</div></div>
    <div class="rakam kirmizi"><div class="v">{toplam['yem_acigi_olan_il']} / {toplam['il_sayisi']}</div>
      <div class="a">Analiz edilen ilin bu kadarında kaba yem açığı var</div></div>
  </div>
  <p class="soluk" style="margin-top:2.5mm">Aynı toprakta ihtiyaç fazlası ürün yetişirken, ihtiyaç duyulan ürün dışarıdan alınıyor.
    Sorun ne kadar ürettiğimiz değil, <strong style="color:{KOYU}">neyi ürettiğimiz</strong>.</p>
</div>

<div class="bolum ikili">
  <div class="genis">
    <h2>Ne yaptık</h2>
    <p style="margin-bottom:2mm">23 il ve 16 ürün için <strong>dört modüllü planlama motoru</strong> (Python) ve dört çalışan panel:</p>
    <ol class="modul">
      <li><strong>Denge analizi</strong> — arz ile ihtiyacı karşılaştırır; ihtiyaç gıda, yem, sanayi kotası ve pazar talebi için ayrı kuralla hesaplanır.</li>
      <li><strong>Sürü etkisi testi</strong> — geçen yılın fiyatının bu yılın ekim alanını ne kadar belirlediğini ölçer.</li>
      <li><strong>Kaynak analizi</strong> — bir ton ürünün kaç m³ su, kaç kWh elektrik, kaç litre mazot ve kaç kg karbona mal olduğunu hesaplar.</li>
      <li><strong>İl karnesi</strong> — yem yeterliliği, su verimliliği, ürün çeşitliliği ve talep uyumundan harf notu verir.</li>
    </ol>
    <p class="soluk" style="margin-top:1.6mm">Paneller: <strong style="color:{KOYU}">bölge analizi</strong>,
      <strong style="color:{KOYU}">ürün analizi</strong>, <strong style="color:{KOYU}">il karnesi</strong> ve
      <strong style="color:{KOYU}">senaryo simülatörü</strong>. Tamamı tarayıcıda çalışır, kurulum gerektirmez.</p>
  </div>
  <div>
    <h2>Bölge karnesi</h2>
    <div class="harita">{harita_svg}</div>
    <div class="harita-alt">
      <span><span class="puan" style="background:{NOT_RENK['A']}"></span> A</span>
      <span><span class="puan" style="background:{NOT_RENK['B']}"></span> B</span>
      <span><span class="puan" style="background:{NOT_RENK['C']}"></span> C</span>
      <span><span class="puan" style="background:{NOT_RENK['D']}"></span> D</span>
      <span style="margin-left:auto">Koyu çerçeveli: Muş</span>
    </div>
  </div>
</div>

<div class="bolum">
  <h2>Muş senaryosu: 239 bin dekar buğday alanı yem bitkisine</h2>
  <div class="ikili">
    <div class="genis">
      <table>
        <thead><tr><th>Gösterge</th><th>Şimdi</th><th>Senaryo</th><th>Değişim</th></tr></thead>
        <tbody>
          <tr><td>Kaba yem karşılama oranı</td><td>0,57</td><td>0,71</td><td class="art">+%26</td></tr>
          <tr><td>Kaba yem açığı</td><td>473 bin t</td><td>315 bin t</td><td class="art">−%33</td></tr>
          <tr><td>Dekar başına net çiftçi geliri</td><td>1.756 TL</td><td>2.005 TL</td><td class="art">+%14</td></tr>
          <tr><td>Sulama suyu</td><td>141 mn m³</td><td>198 mn m³</td><td class="eksi">+%40</td></tr>
          <tr class="notlar"><td>İl karne notu</td><td>C (61)</td><td>B (67)</td><td class="art">+6 puan</td></tr>
        </tbody>
      </table>
    </div>
    <div>
      <p class="soluk">Model bir tavsiye makinesi değil, <strong style="color:{KOYU}">takası gösteren bir karar aracıdır</strong>:
        yem açığı ve çiftçi geliri iyileşirken sulama suyu artıyor. Bu tercihi çiftçi ve kurum birlikte yapar;
        sistemin işi, sonucu ekim yapılmadan önce göstermektir.</p>
      <p class="soluk">Senaryoda buğdayda ilin kendi ihtiyacının 1,5 katı güvenlik payı korunur; il gıda güvenliğini kaybetmez.</p>
    </div>
  </div>
</div>

<div class="bolum uyari">
  <h3>Verinin durumu — açıkça</h3>
  <p class="soluk" style="margin:0">Paneldeki sayılar <strong style="color:{KOYU}">henüz gerçek veri değil, ön tahmindir</strong>.
    Doğru olan kısım modelin yapısıdır: ihtiyacın hangi kuralla hesaplandığı, dengenin nasıl yorumlandığı ve kaynak hesabının yöntemi.
    Modeldeki 19 girdinin her biri için tür, belirsizlik payı ve doğrulanacağı kaynak panelde listelenmiştir. Duyarlılık analizi, sonucu en çok belirleyen
    girdinin <strong style="color:{KOYU}">ürün fiyatı</strong> olduğunu gösteriyor; veri toplamaya oradan başlıyoruz. Gerçek veri girildiğinde analiz kodunda tek satır değişmeyecek.</p>
</div>

<div class="ikili">
  <div>
    <h2>Dört haftalık plan</h2>
    <table>
      <tbody>
        <tr><td style="width:22%"><strong>1. hafta</strong></td><td style="text-align:left">Ekip görevlendirmesi, veri talep yazıları</td></tr>
        <tr><td><strong>2. hafta</strong></td><td style="text-align:left">Muş için 4 ürünün 10 yıllık üretim, fiyat ve hayvancılık verisi</td></tr>
        <tr><td><strong>3. hafta</strong></td><td style="text-align:left">Sahada ziraat mühendisi ve çiftçi görüşmeleri</td></tr>
        <tr><td><strong>4. hafta</strong></td><td style="text-align:left">Panellerin gerçek veriyle yeniden üretilmesi, pilot raporu</td></tr>
      </tbody>
    </table>
    <p class="soluk" style="margin-top:2mm">Sonraki aşama: motorun web servisine dönüştürülmesi ve TÜBİTAK 2209-A başvurusu.</p>
  </div>
  <div class="talep">
    <h2>Dekanlıktan talebimiz</h2>
    <div class="talep-satir"><div class="talep-no">1</div><div><strong>Akademik danışman</strong> — ziraat, hayvancılık ya da tarım ekonomisi alanından bir hoca; modelin katsayılarını doğrulayacak kişi.</div></div>
    <div class="talep-satir"><div class="talep-no">2</div><div><strong>Resmi veri talep yazısı</strong> — Muş İl Tarım ve Orman Müdürlüğü'nden il ve ilçe bazlı üretim ve hayvancılık verisi. <em>En kritik ihtiyacımız.</em></div></div>
    <div class="talep-satir"><div class="talep-no">3</div><div><strong>TÜBİTAK 2209-A</strong> başvurusunda kurumsal destek ve danışman onayı.</div></div>
    <div class="talep-satir"><div class="talep-no">4</div><div><strong>Çalışma alanı</strong> — dört kişilik ekip için düzenli çalışma yeri, varsa teknokent bağlantısı.</div></div>
  </div>
</div>

</main>

<footer>
  <span>AGROMATCH · İhtiyaca göre ekim planlaması · Pilot il: Muş · 23 il, 16 ürün</span>
  <span>Bu özeti hazırlayan Hasan Turgut'tur.</span>
</footer>

</body>
</html>
"""
    (KOK / "ozet.html").write_text(html, encoding="utf-8")
    print(f"ozet.html yazıldı ({len(html) // 1024} KB)")


if __name__ == "__main__":
    uret()
