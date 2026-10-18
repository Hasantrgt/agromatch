"""
AGROMATCH - Toprak analizi veri toplama föyü
=============================================
Tek sayfalık A4 föy üretir: laboratuvara / İl Müdürlüğü'ne giderken
yanında götürülür, dönerken dolu gelir.

Föyün varlık sebebi: modelin kullandığı 12 değer belli. Elde ne varsa
onu almak yerine, NEYİN gerektiğini bilerek gitmek gerekir. Eksik bir
alanla dönmek ikinci bir ziyaret demektir.

Föy her hücrede mevcut VARSAYIMI soluk gri yazar. Böylece ölçüm geldiği
anda sapma görülür: laboratuvar pH 8,4 diyorsa ve biz 7,6 varsaymışsak,
o ilçenin bütün uygunluk puanları değişecek demektir.

    python src/toprak_foyu.py
    node pdf_foy.mjs
"""

from pathlib import Path

import mus_profil as mp

KOK = Path(__file__).resolve().parent.parent

# (alan, etiket, birim, laboratuvar verir mi, TOPRAK demetindeki sıra)
ALANLAR = [
    ("ph",       "pH",                    "1:2,5 su",      True,   0),
    ("om",       "Organik madde",         "%",             True,   1),
    ("kirec",    "Kireç (CaCO₃)",         "%",             True,   2),
    ("ec",       "Tuzluluk (EC)",         "dS/m",          True,   3),
    ("kil",      "Kil",                   "%",             True,   4),
    ("kum",      "Kum",                   "%",             True,   5),
    ("silt",     "Silt",                  "%",             True,   6),
    ("p2o5",     "Fosfor (P₂O₅)",         "kg/da",         True,   7),
    ("k2o",      "Potasyum (K₂O)",        "kg/da",         True,   8),
    ("drenaj",   "Drenaj",                "zayıf/orta/iyi", False, 9),
    ("erozyon",  "Erozyon derecesi",      "1–5",           False, 10),
    ("derinlik", "Toprak derinliği",      "cm",            False, 11),
]

STIL = """
  @page { size: A4; margin: 0; }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: Carlito, "Liberation Sans", Arial, sans-serif;
         font-size: 9.4pt; line-height: 1.38; color: #16281F; }
  .sayfa { width: 210mm; min-height: 297mm; position: relative; }
  header { background: #16281F; color: #F7F5EE; padding: 8mm 14mm 6mm;
           display: flex; justify-content: space-between; align-items: flex-end; gap: 8mm; }
  .marka { font-family: Lora, Georgia, serif; font-size: 20pt; font-weight: 600; line-height: 1; }
  .alt { font-size: 9.6pt; color: #CBD4C6; margin-top: 2mm; }
  .kim { text-align: right; font-size: 8pt; color: #AEB9AB; }
  .serit { height: 2mm; background: #B4761A; }
  main { padding: 6mm 14mm; }
  h2 { font-family: Lora, Georgia, serif; font-size: 11.5pt; color: #1F4733;
       margin: 0 0 2.5mm; padding-bottom: 1.2mm; border-bottom: 0.7pt solid #DCD9CC; }
  p { margin: 0 0 2.5mm; }
  .soluk { color: #5F6A5E; font-size: 8.4pt; }
  .kutu { background: #FAF8F2; border-left: 2pt solid #B4761A;
          padding: 2.8mm 4mm; margin: 0 0 4mm; font-size: 8.8pt; }
  .kutu b { color: #8A5A12; }

  table.veri { width: 100%; border-collapse: collapse; font-size: 8.4pt; }
  table.veri th, table.veri td { border: 0.5pt solid #D8D5C8; padding: 0; }
  table.veri thead th { background: #1F4733; color: #F7F5EE; font-size: 7.4pt;
       text-transform: uppercase; letter-spacing: 0.3pt; padding: 1.6mm 1mm;
       font-weight: 600; text-align: center; }
  table.veri thead th.sol { text-align: left; padding-left: 2mm; }
  td.ad { padding: 0 2mm; font-size: 8.4pt; white-space: nowrap; }
  td.birim { padding: 0 1.5mm; font-size: 7.4pt; color: #5F6A5E; white-space: nowrap; }
  td.hucre { height: 7.6mm; text-align: center; vertical-align: top; padding-top: 0.8mm; }
  .varsayim { font-size: 6.6pt; color: #B9B5A6; display: block; }
  /* Laboratuvarın VERMEYECEĞİ üç satır. Föy metni "koyu zeminle işaretlendi"
     diyor; ayrım göz tarafından bir bakışta seçilmezse o cümle boşa gider. */
  tr.saha td { background: #E6E2D2; }
  tr.saha td.ad { font-weight: 600; }
  tr.saha td.ad::before { content: "▸ "; color: #B4761A; }
  tr.saha + tr.saha td { border-top-color: #CFCBB8; }
  .bayrak { display: inline-block; width: 3mm; }

  table.kimlik { width: 100%; border-collapse: collapse; font-size: 8.6pt; margin-top: 1mm; }
  table.kimlik td { border: 0.5pt solid #D8D5C8; padding: 1.6mm 2mm; height: 8mm; }
  table.kimlik td.etiket { background: #FAF8F2; width: 32mm; font-size: 8pt; color: #3C4A3E; }
  footer { position: absolute; bottom: 7mm; left: 14mm; right: 14mm; display: flex;
           justify-content: space-between; font-size: 7.4pt; color: #5F6A5E;
           border-top: 0.6pt solid #DCD9CC; padding-top: 2mm; }
"""


def satir(alan, etiket, birim, laboratuvar, sira):
    hucreler = "".join(
        f'<td class="hucre"><span class="varsayim">{mp.TOPRAK[i][sira]}</span></td>'
        for i in mp.ILCE)
    sinif = "" if laboratuvar else ' class="saha"'
    return (f"<tr{sinif}><td class='ad'>{etiket}</td>"
            f"<td class='birim'>{birim}</td>{hucreler}</tr>")


def foy_html():
    basliklar = "".join(f"<th>{i}</th>" for i in mp.ILCE)
    satirlar = "".join(satir(*a) for a in ALANLAR)
    lab = sum(1 for a in ALANLAR if a[3])
    saha = len(ALANLAR) - lab

    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>AGROMATCH Toprak Föyü</title><style>{STIL}</style></head><body>
<div class="sayfa">
  <header>
    <div><div class="marka">Toprak Analizi Veri Föyü</div>
      <div class="alt">Muş · 6 ilçe · modelin ihtiyaç duyduğu {len(ALANLAR)} değer</div></div>
    <div class="kim">AGROMATCH<br>Saha föyü</div>
  </header>
  <div class="serit"></div>
  <main>

    <p>Panelde şu an <b>ilçe toprak değerlerinin tamamı tahmindir.</b> Aşağıdaki
    tablo dolduğunda bu değerler <b>ölçüme</b> döner ve panelin uygunluk puanları,
    gübre önerileri ve belirsizlik aralıkları gerçek veriyle yeniden hesaplanır.
    Her hücrede şu anki varsayım soluk gri yazılıdır — ölçüm ondan çok saparsa
    o ilçenin bütün sonuçları değişecek demektir.</p>

    <div class="kutu">
      <b>Dikkat — laboratuvar {lab} değeri verir, son {saha} değeri vermez.</b>
      Drenaj, erozyon ve toprak derinliği rutin analiz raporunda <u>çıkmaz</u>;
      bunlar arazi gözlemi ve toprak haritası bilgisidir. İl Tarım ve Orman
      Müdürlüğü'nün toprak etüt haritalarından ya da arazide gözlemle alınır.
      Bu üç satır tabloda <b>koyu zeminle</b> işaretlendi. Sadece laboratuvar
      raporuyla dönersen tablo eksik kalır.
    </div>

    <h2>Ölçüm tablosu</h2>
    <table class="veri">
      <thead><tr><th class="sol">Parametre</th><th class="sol">Birim</th>{basliklar}</tr></thead>
      <tbody>{satirlar}</tbody>
    </table>
    <p class="soluk" style="margin-top:2mm">
      Soluk gri sayılar mevcut varsayımdır, üzerine ölçülen değeri yaz.
      Koyu zeminli üç satır laboratuvardan değil arazi/harita kaydından gelir.</p>

    <h2 style="margin-top:5mm">Her numune için kaydedilecekler</h2>
    <p class="soluk" style="margin-bottom:2mm">Bunlar yazılmazsa veri kullanılamaz:
      hangi ilçeye ait olduğu bilinmeyen bir analiz, analiz değildir.</p>
    <table class="kimlik">
      <tr><td class="etiket">İlçe / köy</td><td></td>
          <td class="etiket">Numune tarihi</td><td></td></tr>
      <tr><td class="etiket">Koordinat (varsa)</td><td></td>
          <td class="etiket">Derinlik (0–30 cm?)</td><td></td></tr>
      <tr><td class="etiket">Arazi kullanımı</td><td></td>
          <td class="etiket">Sulu / kuru</td><td></td></tr>
      <tr><td class="etiket">Laboratuvar</td><td></td>
          <td class="etiket">Rapor no</td><td></td></tr>
    </table>

    <div class="kutu" style="margin-top:4mm">
      <b>Birim tuzağı.</b> Fosfor ve potasyum bazı raporlarda <b>ppm</b>, bazılarında
      <b>kg/da</b> yazılır; ikisi karışırsa gübre önerisi 10 kat şaşar. Raporda hangisi
      yazıyorsa <u>olduğu gibi</u> kaydet, çevirmeye çalışma — çevrimi model yapar.
      Kireç de aynı: <b>% CaCO₃</b> mi yoksa başka bir ölçek mi, not et.
    </div>

  </main>
  <footer><span>AGROMATCH · Muş Tarım Planlama Motoru</span>
    <span>hasantrgt.github.io/agromatch</span></footer>
</div>
</body></html>"""


def main():
    hedef = KOK / "foy"
    hedef.mkdir(exist_ok=True)
    yol = hedef / "toprak_foyu.html"
    yol.write_text(foy_html(), encoding="utf-8")
    print(f"{yol} yazıldı ({len(ALANLAR)} alan, {len(mp.ILCE)} ilçe)")


if __name__ == "__main__":
    main()
