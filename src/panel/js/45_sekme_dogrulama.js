// Doğrulama sekmesi: laboratuvar ölçümü bağımsız bir kaynakla karşılaştırılır.
// Üç sayı yan yana: varsayım, laboratuvar, SoilGrids.

function sekmeDogrulama() {
  if (!DOGRULAMA || !DOGRULAMA.var) {
    return [bolum("01", "Doğrulama verisi üretilmemiş",
      "Bu sekme laboratuvar ölçümlerini bağımsız bir kaynakla (ISRIC "
      + "SoilGrids) karşılaştırır. Üretmek için önce veriyi çek: "
      + "python src/toprak_dogrulama/soilgrids_cek.py — internet ister ve "
      + "birkaç dakika sürer. Sonra: "
      + "python src/toprak_dogrulama/karsilastir.py")];
  }

  const o = DOGRULAMA.ozet;
  const satirlar = DOGRULAMA.satirlar;

  // --- 01 ne yapıldı, neye yaramaz
  const girisBolum = el("div", {},
    el("div", { class: "kutu" },
      el("strong", { text: "Bu bir doğrulamadır, ispat değil." }),
      el("p", { text: DOGRULAMA.yargi })),
    el("div", { class: "tiles" },
      ...[["Bağımsız kaynak", "SoilGrids", "250 m · küresel · CC-BY 4.0"],
          ["Nokta sorgusu", n0(DOGRULAMA.nokta_sorgusu),
            `${n0(DOGRULAMA.ilce_sayisi)} ilçe · ilçe merkezi çevresinde ızgara`],
          ["Karşılaştırma", n0(o.olcumlu),
            "ölçümle doğrudan karşılaştırılabilen ilçe × alan"],
          ["Sistematik kayma",
            n0(DOGRULAMA.alan_ozeti.filter(a => a.ayni_yon).length) + " / "
              + n0(DOGRULAMA.alan_ozeti.length),
            "her ilçede aynı yönde sapan ölçüm — model yanlılığı"]]
        .map(([b, d, a]) => el("div", { class: "tile" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))));

  // --- 02 üç ayrı test
  const testBolum = el("div", {},
    el("p", { class: "note", text: "Tek bir \"tutuyor mu\" sorusu yanıltır. "
      + "Üç ayrı soru var ve üçü ayrı cevaplanmalı: mutlak değerler "
      + "tutuyor mu, sapma sistematik mi, iki kaynak ilçeleri aynı sırada "
      + "mı diziyor." }),
    el("div", { class: "kaydir" },
      tablo([{ ad: "ölçüm" }, { ad: "ilçe", num: true },
             { ad: "sistematik kayma", num: true }, { ad: "sapma aynı yönde" },
             { ad: "ilçe ayrımı ölçülebilir mi" }, { ad: "sıralama uyumu" },
             { ad: "sonuç" }],
        DOGRULAMA.alan_ozeti.map(a => [
          el("span", {}, el("strong", { text: a.alan_ad }),
            a.sg_turetildi
              ? el("div", { style: "font-size:11px;color:var(--muted)",
                  text: "karbondan türetildi" })
              : null),
          el("span", { class: "mono", text: n0(a.kiyas_ilce) }),
          el("span", { class: "mono", style: "font-weight:700",
            text: (a.sistematik_kayma > 0 ? "+" : "") + n2(a.sistematik_kayma)
              + (a.kayma_yayilimi == null ? ""
                 : "  ±" + n2(a.kayma_yayilimi)) }),
          a.ayni_yon
            ? rozet("altı ilçede de aynı yön", "r-kotu")
            : rozet("yön karışık", "r-notr"),
          a.ayirt_edici
            ? rozet("ölçülebilir", "r-iyi")
            : el("span", {}, rozet("ölçülemez", "r-orta"),
                el("div", { style: "font-size:11px;color:var(--muted);"
                  + "white-space:normal;max-width:210px",
                  text: `ilçeler arası fark ${n2(a.ilceler_arasi_fark)}, `
                    + `ilçe içi yayılım ${n2(a.ic_yayilim)}` })),
          a.ayirt_edici && a.siralama_uyumu != null
            ? el("span", { class: "mono", style: "font-weight:600",
                text: "ρ = " + n2(a.siralama_uyumu) })
            : el("span", { style: "color:var(--muted)", text: "yorumlanamaz" }),
          el("span", { style: "font-size:12px;white-space:normal;"
            + "max-width:230px;display:block", text: dogrulamaSonuc(a) }),
        ]))),
    el("div", { class: "kutu", style: "margin-top:14px" },
      el("strong", { text: "Sistematik kayma ne demek, ne demek değil" }),
      el("p", { text: "Sapma altı ilçenin altısında da aynı yöndeyse bu "
        + "rastgele hata değildir: küresel modelin bu bölgedeki "
        + "yanlılığıdır. Laboratuvarın yanlış olduğunun kanıtı DEĞİLDİR. "
        + "pH'ta kayma −0,53 ve yayılımı yalnızca ±0,11 — yani sabit bir "
        + "fark çıkarıldığında iki kaynak neredeyse üst üste düşüyor. "
        + "Muş toprağı kireçli; kireçli topraklar pH 7,5 civarında "
        + "tamponlanır ve laboratuvarın 7,4-7,6 aralığı bununla "
        + "tutarlıdır." })));

  // --- 03 ilçe × alan ayrıntısı
  const ayrintiBolum = el("div", {}, dogrulamaEfsane());
  for (const a of DOGRULAMA.alan_ozeti) {
    const ait = satirlar.filter(s => s.alan === a.alan);
    if (!ait.length) continue;
    const hepsi = ait.flatMap(s => [s.soilgrids.q1, s.soilgrids.q3, s.varsayim]
      .concat(s.laboratuvar ? [s.laboratuvar.q1, s.laboratuvar.q3] : []));
    const alt = Math.min(...hepsi), ust = Math.max(...hepsi);
    ayrintiBolum.append(
      el("h3", { class: "cati-baslik", text: a.alan_ad }),
      el("div", { class: "kaydir" },
        tablo([{ ad: "ilçe" }, { ad: "varsayım", num: true },
               { ad: "laboratuvar", num: true }, { ad: "SoilGrids", num: true },
               { ad: "fark", num: true }, { ad: "üç kaynak yan yana" },
               { ad: "" }],
          ait.map(s => [
            el("strong", { text: s.ilce }),
            el("span", { class: "mono", style: "color:var(--warn-ink)",
              text: n2(s.varsayim) }),
            s.laboratuvar
              ? el("span", {}, el("span", { class: "mono",
                  style: "font-weight:600", text: n2(s.laboratuvar.medyan) }),
                  s.lab_turetildi
                    ? el("div", { style: "font-size:10.5px;color:var(--muted)",
                        text: "bünyeden türetildi" })
                    : el("div", { style: "font-size:10.5px;color:var(--muted)",
                        text: "n=" + n0(s.laboratuvar.n) }))
              : el("span", { style: "color:var(--muted)", text: "ölçüm yok" }),
            el("span", { class: "mono", style: "color:var(--s1);font-weight:600",
              text: n2(s.soilgrids.medyan) }),
            s.fark_lab == null
              ? el("span", { style: "color:var(--muted)", text: "—" })
              : el("span", { class: "mono",
                  style: "font-weight:600;color:"
                    + ((s.laboratuvar && !s.laboratuvar.guvenilir)
                       || s.lab_turetildi ? "var(--muted)"
                       : s.uyum === "tutuyor" ? "var(--good)"
                       : "var(--critical)"),
                  text: (s.fark_lab > 0 ? "+" : "") + n2(s.fark_lab) }),
            ucluOlcek(s, alt, ust),
            s.lab_turetildi
              ? rozet("türetilmiş", "r-orta")
              : (s.laboratuvar && !s.laboratuvar.guvenilir)
                // Az örnekli ilçede "ayrışıyor" demek haksız bir yargı:
                // ayrışan şey SoilGrids değil, dört örnekle kurulmuş bir
                // medyan olabilir. Bu satırlar orana da girmiyor.
                ? rozet("az örnek — karşılaştırılamaz", "r-orta")
                : rozet(s.uyum, UYUM_ROZET[s.uyum] || "r-notr"),
          ]))));
  }

  // --- 04 doğrulanamayanlar
  const eksikBolum = el("div", { class: "bulgu" },
    DOGRULAMA.dogrulanamayan.map(x =>
      el("div", { class: "kart" },
        el("div", { class: "ust", style: "justify-content:space-between" },
          el("h3", { text: x.alan === "kirec" ? "Kireç (CaCO₃)" : "Tuzluluk (EC)" }),
          rozet("doğrulanamadı", "r-kotu")),
        el("p", { text: x.sebep }))));

  return [
    bolum("01", "Elimizdeki veriyi bağımsız bir kaynakla sınamak",
      "İl Tarım'dan ek veri istendi, verilmedi. Elimizdeki laboratuvar "
      + "kayıtlarına ise ne biz ne de veriyi veren hoca tam güveniyor. "
      + "Geriye tek dürüst yol kalıyor: bağımsız bir kaynakla "
      + "karşılaştırmak.",
      girisBolum),
    bolum("02", "Üç ayrı soru, üç ayrı cevap",
      "Bir doğrulama tek sayıya indirgenirse yanıltır. Asıl belirleyici "
      + "olan, modelin kullandığı şeyin doğrulanıp doğrulanmadığıdır: "
      + "model ilçeleri BİRBİRİNE GÖRE kıyaslıyor.",
      testBolum),
    bolum("03", "İlçe ilçe: üç sayı yan yana",
      "Üçünün birbirini tuttuğu yerde o değere güvenilebilir. Ayrıştığı "
      + "yerde hangisinin yanlış olduğunu bu tablo söylemez; nereye "
      + "bakılacağını söyler.",
      ayrintiBolum),
    (KIL && KIL.var)
      ? bolum("04", "Peki bu anlaşmazlık tavsiyeyi değiştiriyor mu",
          "Bir doğrulamanın asıl sorusu budur. İstatistiksel bir fark, "
          + "karar değiştirmiyorsa akademik kalır; değiştiriyorsa acildir.",
          kilEtkisiBolumu())
      : null,
    bolum("05", "Doğrulanamayanlar — ve neden önemli",
      "Bir doğrulamanın en dürüst kısmı, neyi doğrulayamadığını "
      + "yazdığı yerdir.",
      eksikBolum),
  ].filter(Boolean);
}
