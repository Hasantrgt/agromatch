"""
AGROMATCH - Görüntüleme kutusu yapım föyü ve kalibrasyon kartı
==============================================================
İki PDF üretir:

  AGROMATCH_Kutu_Foyu.pdf          Yapım ölçüleri, kurulum adımları, çekim protokolü
  AGROMATCH_Kalibrasyon_Karti.pdf  A4, %100 ölçekte yazdırılacak referans kart

Kalibrasyon kartı neden şart: fotoğraftaki bir lekenin kaç milimetre olduğunu
ancak görüntüde bilinen boyutta bir nesne varsa bilebilirsin. Kart ayrıca gri
basamaklarıyla pozlamanın ve beyaz dengesinin her çekimde aynı kalıp kalmadığını
gösterir.

Kullanım:
    python src/kutu_foyu.py
    node pdf_foy.mjs        (HTML'leri PDF'e çevirir)
"""

from pathlib import Path

KOK = Path(__file__).resolve().parent.parent

ORTAK_STIL = """
  @page { size: A4; margin: 0; }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: Carlito, "Liberation Sans", Arial, sans-serif;
         font-size: 9.6pt; line-height: 1.4; color: #16281F; }
  .serif { font-family: Lora, Georgia, serif; }
  .sayfa { width: 210mm; min-height: 297mm; padding: 0; position: relative;
           page-break-after: always; }
  .sayfa:last-child { page-break-after: auto; }
  header { background: #16281F; color: #F7F5EE; padding: 8mm 14mm 6mm;
           display: flex; justify-content: space-between; align-items: flex-end; gap: 8mm; }
  .marka { font-family: Lora, Georgia, serif; font-size: 20pt; font-weight: 600; line-height: 1; }
  .alt { font-size: 10pt; color: #CBD4C6; margin-top: 2mm; }
  .kim { text-align: right; font-size: 8.2pt; color: #AEB9AB; }
  .serit { height: 2mm; background: #B4761A; }
  main { padding: 7mm 14mm; }
  h2 { font-family: Lora, Georgia, serif; font-size: 12pt; color: #1F4733; margin: 0 0 3mm;
       padding-bottom: 1.2mm; border-bottom: 0.7pt solid #DCD9CC; }
  h3 { font-size: 9.8pt; margin: 4mm 0 1.5mm; }
  p { margin: 0 0 2.5mm; }
  .soluk { color: #5F6A5E; font-size: 8.6pt; }
  table { width: 100%; border-collapse: collapse; font-size: 8.8pt; }
  th, td { text-align: left; padding: 1.35mm 2mm; border-bottom: 0.5pt solid #E2E0D6; }
  thead th { font-size: 7.6pt; text-transform: uppercase; letter-spacing: 0.4pt; color: #5F6A5E; }
  ol, ul { margin: 0 0 3mm; padding-left: 5mm; }
  li { margin-bottom: 1.6mm; }
  .kutu { background: #FAF8F2; border-left: 2pt solid #B4761A; padding: 3mm 4mm; margin-bottom: 3mm; }
  .ikili { display: flex; gap: 7mm; }
  .ikili > div { flex: 1; }
  footer { position: absolute; bottom: 7mm; left: 14mm; right: 14mm; display: flex;
           justify-content: space-between; font-size: 7.6pt; color: #5F6A5E;
           border-top: 0.6pt solid #DCD9CC; padding-top: 2mm; }
"""


def foy_html():
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>AGROMATCH Kutu Föyü</title><style>{ORTAK_STIL}</style></head><body>

<div class="sayfa">
  <header>
    <div><div class="marka">Görüntüleme Kutusu</div>
      <div class="alt">Yaprak fotoğrafı için sabit ışık, sabit mesafe, sabit zemin</div></div>
    <div class="kim">AGROMATCH<br>Yapım föyü · s.1</div>
  </header>
  <div class="serit"></div>
  <main>
    <h2>Neden kutu?</h2>
    <p>Saha fotoğrafında modeli bozan şey yaprağın kendisi değil, <b>koşulların değişmesidir</b>:
      güneş açısı, gölge, bulut, mesafe. Aynı yaprağı iki farklı saatte çekersen iki farklı sonuç
      çıkar. Kutu üç şeyi sabitler — ışık, mesafe, zemin — ve ölçümü tekrarlanabilir hâle getirir.</p>
    <div class="kutu"><b>Kazanım:</b> kalibrasyon kartı sayesinde lekenin çapı milimetre cinsinden
      ölçülür. Cercospora lekesi tipik olarak 3–5 mm'dir; ölçüm bu aralığa düşüyorsa tespit
      doğrulanmış olur.</div>

    <h2>Malzeme</h2>
    <table>
      <thead><tr><th>Parça</th><th>Özellik</th><th>Not</th></tr></thead>
      <tbody>
        <tr><td>Gövde</td><td>MDF ya da kalın karton, iç ölçü 40 × 40 × 45 cm</td><td>v0 için karton kutu yeter</td></tr>
        <tr><td>İç yüzey</td><td>Mat beyaz (parlak olmayacak)</td><td>Mat beyaz kâğıt ya da boya</td></tr>
        <tr><td>Zemin</td><td>Mat <b>mavi</b> karton</td><td>Yeşil yaprak maviden kolay ayrılır</td></tr>
        <tr><td>Aydınlatma</td><td>LED şerit 5000K, yüksek renk doğruluğu + difüzör</td><td>En kritik parça</td></tr>
        <tr><td>Kamera</td><td>Telefon (v0) ya da Pi Camera Module 3</td><td>Üst merkezde, sabit</td></tr>
        <tr><td>Kalibrasyon kartı</td><td>A4, %100 ölçekte yazdırılmış</td><td>Bu föyle birlikte verildi</td></tr>
      </tbody>
    </table>

    <h2>Ölçüler</h2>
    <div class="ikili">
      <div>
        <table>
          <tbody>
            <tr><td>Kamera – zemin mesafesi</td><td><b>30 cm</b></td></tr>
            <tr><td>Görüş alanı (telefonla)</td><td>yaklaşık 20 × 15 cm</td></tr>
            <tr><td>LED konumu</td><td>üst kenarda, dört köşeye yakın</td></tr>
            <tr><td>LED – zemin mesafesi</td><td>35–40 cm</td></tr>
            <tr><td>Difüzör</td><td>LED'in 3–5 cm altında, yarı saydam</td></tr>
            <tr><td>Kapak</td><td>dışarıdan ışık sızdırmayacak</td></tr>
          </tbody>
        </table>
        <p class="soluk" style="margin-top:2mm">Mesafeyi bir kez ayarla ve <b>bir daha değiştirme</b>.
          Mesafe değişirse mm/piksel oranı değişir, önceki ölçümlerle karşılaştırılamaz.</p>
      </div>
      <div>
        <svg viewBox="0 0 220 230" style="height:58mm;width:auto;display:block;margin:0 auto"
             aria-label="Kutu kesit şeması">
          <rect x="18" y="14" width="184" height="196" fill="#FAF8F2" stroke="#16281F" stroke-width="2"/>
          <rect x="18" y="14" width="184" height="12" fill="#16281F"/>
          <circle cx="110" cy="38" r="9" fill="#1F4733"/>
          <text x="124" y="42" font-size="9" fill="#16281F">kamera</text>
          <rect x="34" y="28" width="26" height="6" rx="3" fill="#B4761A"/>
          <rect x="160" y="28" width="26" height="6" rx="3" fill="#B4761A"/>
          <text x="34" y="24" font-size="8" fill="#B4761A">LED</text>
          <line x1="34" y1="52" x2="186" y2="52" stroke="#C9C6B8" stroke-width="2" stroke-dasharray="4 3"/>
          <text x="60" y="49" font-size="7.5" fill="#5F6A5E">difüzör</text>
          <rect x="34" y="176" width="152" height="18" fill="#9EC4E0" stroke="#16281F" stroke-width="1"/>
          <text x="38" y="188" font-size="8" fill="#16281F">mavi zemin</text>
          <ellipse cx="100" cy="176" rx="34" ry="9" fill="#5E9B3F"/>
          <rect x="146" y="168" width="36" height="9" fill="#ffffff" stroke="#16281F" stroke-width="0.8"/>
          <text x="148" y="166" font-size="6.5" fill="#16281F">kart</text>
          <line x1="110" y1="47" x2="110" y2="172" stroke="#1F4733" stroke-width="1" stroke-dasharray="3 3"/>
          <text x="114" y="118" font-size="9" fill="#1F4733" font-weight="bold">30 cm</text>
        </svg>
      </div>
    </div>

    <h2>Kurulum — sekiz adım</h2>
    <ol>
      <li>Kutunun içini mat beyazla kapla; parlak yüzey kalmasın (yansıma ölçümü bozar).</li>
      <li>Zemine mat mavi kartonu yerleştir.</li>
      <li>LED şeridi üst kenara, dört köşeye yakın olacak şekilde yapıştır.</li>
      <li>Difüzörü LED'in 3–5 cm altına ger; ışık doğrudan yaprağa vurmasın.</li>
      <li>Kamerayı üst merkeze sabitle, zemine <b>tam 30 cm</b> olacak şekilde ayarla.</li>
      <li>Kalibrasyon kartını zemine koy, çek, kenar çizgisinin 150 mm olduğunu cetvelle doğrula.</li>
      <li>Telefonun pro/manuel modunda ISO ve pozlamayı sabitle, flaşı kapat, zamanlayıcı kullan.</li>
      <li>Boş zeminin bir fotoğrafını çek ve sakla — sonraki çekimlerde ışık değişmiş mi diye bakarsın.</li>
    </ol>
    <div class="kutu"><b>v0 kısayolu:</b> MDF beklemeden karton kutu, masa lambası ve telefon tutucuyla
      bu hafta sonu kurulabilir. Mantık aynı; sonra kalıcı gövdeye geçersin.</div>
  </main>
  <footer><span>AGROMATCH · Görüntüleme kutusu yapım föyü</span>
    <span>Bu föyü hazırlayan Hasan Turgut'tur.</span></footer>
</div>

<div class="sayfa">
  <header>
    <div><div class="marka">Çekim Protokolü</div>
      <div class="alt">Her fotoğrafın aynı koşulda çekilmesi için</div></div>
    <div class="kim">AGROMATCH<br>Yapım föyü · s.2</div>
  </header>
  <div class="serit"></div>
  <main>
    <h2>Yaprak hazırlığı</h2>
    <ol>
      <li>Yaprağı saptan kes, <b>tozunu silme</b> — doğal hâli kalsın, sadece toprak bulaşığı varsa
        hafifçe temizle.</li>
      <li>Kıvrılmışsa düzleştir; gerekiyorsa kenarlarından şeffaf bir cam ya da asetatla bastır.</li>
      <li>Zeminin ortasına koy, kalibrasyon kartını yaprağın <b>yanına</b> yerleştir (üstüne değil).</li>
    </ol>

    <h2>Çekim</h2>
    <ol>
      <li>Kapağı kapat, zamanlayıcıyla çek (elle basmak titretir).</li>
      <li>Her yaprak için <b>üç kare</b>: üst yüz, alt yüz, ve üst yüzün 90° döndürülmüş hâli.</li>
      <li>Dosya adı: <b>parselKodu_tarih_yaprakNo_yuz.jpg</b> — örnek:
        <span class="serif">MUS01_20261010_007_ust.jpg</span></li>
    </ol>

    <h2>Her yaprak için not edilecekler</h2>
    <table>
      <thead><tr><th>Alan</th><th>Örnek</th><th>Neden</th></tr></thead>
      <tbody>
        <tr><td>Parsel kodu</td><td>MUS01</td><td>Tarlayla eşleştirme</td></tr>
        <tr><td>Tarih</td><td>2026-10-10</td><td>Zaman serisi</td></tr>
        <tr><td>Yaprak no</td><td>007</td><td>Tekrar bulabilmek için</td></tr>
        <tr><td>Gözle şiddet tahmini</td><td>orta</td><td>Algoritmanın sonucuyla karşılaştırılacak</td></tr>
        <tr><td>Elle leke sayımı</td><td>18</td><td><b>En değerli veri</b> — gerçek değer kümesi</td></tr>
        <tr><td>Yaprak konumu</td><td>dış taç / orta / genç</td><td>Hastalık önce yaşlı yapraklarda çıkar</td></tr>
      </tbody>
    </table>

    <h2>Kaç yaprak?</h2>
    <p>Tek parselden <b>20–30 yaprak</b>, tarlanın farklı noktalarından. Hepsi bir köşeden alınırsa
      örneklem yanlı olur. Köşegen üzerinde yürüyüp her on adımda bir yaprak almak iyi bir yöntemdir.</p>
    <div class="kutu"><b>Elle sayım neden şart:</b> algoritmanın sentetik görüntülerdeki başarısı
      kendi ürettiğimiz veriye karşı ölçüldü. Gerçek yapraklardaki başarıyı ancak elle saydığın bir
      referans kümeyle bilebilirsin. 30 yaprakta elle sayım, raporun en önemli tablosunu üretir.</div>

    <h2>Kalite kontrolü</h2>
    <ul>
      <li>Her 20 fotoğrafta bir, kalibrasyon kartının gri basamaklarına bak: parlaklık kaymışsa ışık
        ya da pozlama değişmiştir.</li>
      <li>Kart her karede görünür olmalı; görünmüyorsa o fotoğraf milimetre ölçümü için kullanılamaz.</li>
      <li>Gölge, parlama ya da bulanıklık varsa fotoğrafı sil ve yeniden çek — kötü görüntüyü veri
        setine koymak, az veriden daha zararlıdır.</li>
    </ul>

    <h2>Çekimden sonra</h2>
    <p>Fotoğrafları <span class="serif">data/saha/&lt;parsel&gt;/</span> klasörüne koy, notları aynı
      klasöre <span class="serif">kayit.csv</span> olarak yaz, sonra çalıştır:</p>
    <p class="serif" style="background:#F1EFE7;padding:2.5mm 3mm;border-radius:1.5mm">
      python src/goruntu/cercospora.py --gorsel data/saha/MUS01/MUS01_20261010_007_ust.jpg --asamalar</p>
  </main>
  <footer><span>AGROMATCH · Çekim protokolü</span>
    <span>Bu föyü hazırlayan Hasan Turgut'tur.</span></footer>
</div>

</body></html>"""


def kart_html():
    """A4 kalibrasyon kartı. Ölçüler mm cinsinden, %100 ölçekte yazdırılmalı."""
    gri = "".join(
        f'<div style="width:24mm;height:18mm;background:{renk};border:0.3mm solid #000">'
        f'<span style="font-size:7pt;color:{"#000" if i < 3 else "#fff"};'
        f'display:block;padding:1mm">{etiket}</span></div>'
        for i, (renk, etiket) in enumerate(
            [("#ffffff", "%100"), ("#cccccc", "%75"), ("#999999", "%50"),
             ("#4d4d4d", "%25"), ("#1a1a1a", "%5")]))
    renkli = "".join(
        f'<div style="width:24mm;height:18mm;background:{renk};border:0.3mm solid #000"></div>'
        for renk in ("#c0392b", "#27ae60", "#2980b9", "#f1c40f"))
    daireler = "".join(
        f'<div style="text-align:center">'
        f'<div style="width:{c}mm;height:{c}mm;border-radius:50%;background:#000;'
        f'margin:0 auto"></div>'
        f'<div style="font-size:7.5pt;margin-top:1.5mm">{c} mm</div></div>'
        for c in (20, 10, 5, 3))
    def cetvel_parcasi(x):
        cizgi = (f'<div style="position:absolute;left:{x}mm;top:0;width:0.3mm;'
                 f'height:{6 if x % 10 == 0 else 3}mm;background:#000"></div>')
        if x % 10:
            return cizgi
        etiket = (f'<div style="position:absolute;left:{x - 2}mm;top:7mm;'
                  f'font-size:6.5pt">{x}</div>')
        return cizgi + etiket

    cetvel = "".join(cetvel_parcasi(x) for x in range(0, 101, 5))

    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>AGROMATCH Kalibrasyon Kartı</title>
<style>
  @page {{ size: A4; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: Carlito, Arial, sans-serif; color: #000; }}
  .kart {{ width: 210mm; height: 297mm; padding: 15mm; position: relative; }}
  .cerceve {{ width: 150mm; height: 150mm; border: 0.5mm solid #000; position: relative;
             margin: 0 auto; padding: 6mm; }}
  h1 {{ font-size: 13pt; margin: 0 0 1mm; }}
  .alt {{ font-size: 8.5pt; color: #333; margin-bottom: 4mm; }}
  .sira {{ display: flex; gap: 3mm; margin-bottom: 5mm; }}
  .baslik {{ font-size: 8pt; font-weight: bold; margin-bottom: 1.5mm; }}
  .daireler {{ display: flex; gap: 8mm; align-items: flex-end; margin-bottom: 5mm; }}
  .cetvel {{ position: relative; height: 14mm; width: 100mm; }}
  .uyari {{ margin-top: 6mm; font-size: 8.5pt; border-left: 1mm solid #000; padding-left: 3mm; }}
  .kose {{ position: absolute; width: 8mm; height: 8mm; border: 0.5mm solid #000; }}
</style></head><body>
<div class="kart">
  <h1>AGROMATCH — Kalibrasyon Kartı</h1>
  <div class="alt">A4, <b>%100 ölçekte</b> yazdırın. Yazıcı ayarında "sayfaya sığdır" KAPALI olmalı.
    Yazdırdıktan sonra aşağıdaki çerçevenin kenarını cetvelle ölçün: <b>tam 150 mm</b> olmalı.</div>

  <div class="cerceve">
    <div class="baslik">Bilinen çaplar — mm/piksel ölçeği buradan hesaplanır</div>
    <div class="daireler">{daireler}</div>

    <div class="baslik">Milimetre cetveli (100 mm)</div>
    <div class="cetvel">{cetvel}</div>

    <div class="baslik">Gri basamaklar — pozlama ve beyaz dengesi kontrolü</div>
    <div class="sira">{gri}</div>

    <div class="baslik">Renk referansı</div>
    <div class="sira">{renkli}</div>

    <div class="uyari">
      <b>Kullanım:</b> kartı yaprağın yanına koyun, her karede görünsün.
      5 mm ve 3 mm daireler Cercospora lekesinin tipik boyutudur — görüntüdeki lekeler bu
      dairelerle karşılaştırılarak gözle de doğrulanabilir.
    </div>
  </div>

  <div style="text-align:center;font-size:8pt;color:#333;margin-top:5mm">
    AGROMATCH · Görüntüleme kutusu kalibrasyon kartı · Hasan Turgut
  </div>
</div>
</body></html>"""


def main():
    (KOK / "foy").mkdir(exist_ok=True)
    (KOK / "foy" / "kutu_foyu.html").write_text(foy_html(), encoding="utf-8")
    (KOK / "foy" / "kalibrasyon_karti.html").write_text(kart_html(), encoding="utf-8")
    print("HTML'ler yazıldı -> foy/")
    print("PDF için: node pdf_foy.mjs")


if __name__ == "__main__":
    main()
