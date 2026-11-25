// Doğrulama sekmesi: laboratuvar ölçümü bağımsız bir kaynakla karşılaştırılır.
// Üç sayı yan yana: varsayım, laboratuvar, SoilGrids.

const UYUM_ROZET = { "tutuyor": "r-iyi", "ayrışıyor": "r-kotu",
                     "ölçüm yok": "r-notr" };

// Üç kaynağı tek bir ölçek üzerinde gösterir: SoilGrids çeyrek bandı,
// laboratuvar çeyrek bandı ve varsayım işareti.
function ucluOlcek(s, alt, ust) {
  const en = 220;
  const px = v => Math.round((v - alt) / (ust - alt) * en);
  const kap = el("div", { style: `position:relative;width:${en}px;height:26px` });

  const band = (q1, q3, ustten, renk, baslik) => {
    const sol = Math.max(px(q1), 0);
    const gen = Math.max(px(q3) - px(q1), 2);
    return el("div", { title: baslik,
      style: `position:absolute;left:${sol}px;top:${ustten}px;`
        + `width:${gen}px;height:7px;border-radius:3px;background:${renk};`
        + "opacity:.5" });
  };
  const cizgi = (v, ustten, yuk, renk, baslik) =>
    el("div", { title: baslik,
      style: `position:absolute;left:${Math.max(0, Math.min(en - 2, px(v)))}px;`
        + `top:${ustten}px;width:2px;height:${yuk}px;background:${renk}` });

  const sg = s.soilgrids;
  kap.append(band(sg.q1, sg.q3, 3, "var(--s1)", "SoilGrids çeyrek aralığı"));
  kap.append(cizgi(sg.medyan, 1, 11, "var(--s1)", "SoilGrids medyanı " + n2(sg.medyan)));

  if (s.laboratuvar) {
    const l = s.laboratuvar;
    if (!s.lab_turetildi) {
      kap.append(band(l.q1, l.q3, 15, "var(--s3)", "laboratuvar çeyrek aralığı"));
    }
    kap.append(cizgi(l.medyan, 13, 11,
      s.lab_turetildi ? "var(--muted)" : "var(--ink)",
      (s.lab_turetildi ? "türetilmiş laboratuvar değeri " : "laboratuvar medyanı ")
      + n2(l.medyan)));
  }
  kap.append(cizgi(s.varsayim, 0, 26, "var(--warning)",
    "varsayım " + n2(s.varsayim)));
  return kap;
}

function dogrulamaEfsane() {
  const oge = (renk, metin) => el("span",
    { style: "display:flex;align-items:center;gap:6px" },
    el("span", { style: `width:12px;height:5px;border-radius:2px;background:${renk}` }),
    el("span", { text: metin }));
  return el("div", { style: "display:flex;flex-wrap:wrap;gap:4px 18px;"
    + "font-size:12px;color:var(--muted);margin-bottom:10px" },
    oge("var(--s1)", "SoilGrids (bağımsız tahmin)"),
    oge("var(--ink)", "laboratuvar ölçümü"),
    oge("var(--warning)", "projenin varsayımı"));
}

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
          ["Tutan", o.tutma_orani == null ? "—" : "%" + n1(o.tutma_orani),
            `${n0(o.tutan)} / ${n0(o.olcumlu)} · SoilGrids medyanı `
            + "laboratuvarın çeyrek aralığında"]]
        .map(([b, d, a]) => el("div", { class: "tile" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))));

  // --- 02 alan özeti
  const alanBolum = el("div", { class: "kaydir" },
    tablo([{ ad: "ölçüm" }, { ad: "ilçe", num: true },
           { ad: "tutan", num: true }, { ad: "ort. mutlak fark", num: true },
           { ad: "" }],
      DOGRULAMA.alan_ozeti.map(a => [
        el("span", {}, el("strong", { text: a.alan_ad }),
          a.sg_turetildi
            ? el("div", { style: "font-size:11px;color:var(--muted)",
                text: "SoilGrids karbondan türetildi (× "
                  + n2(DOGRULAMA.om_katsayi) + ")" })
            : null),
        el("span", { class: "mono",
          text: a.lab_turetildi ? n0(a.turetilmis_ilce) : n0(a.olcumlu_ilce) }),
        a.lab_turetildi
          ? el("span", { style: "color:var(--muted)", text: "—" })
          : el("span", { class: "mono",
              style: `font-weight:700;color:${a.tutan_ilce === a.olcumlu_ilce
                ? "var(--good)" : a.tutan_ilce === 0
                ? "var(--critical)" : "var(--warning)"}`,
              text: n0(a.tutan_ilce) }),
        el("span", { class: "mono", text: n2(a.lab_turetildi
          ? a.turetilmis_ortalama_fark : a.ortalama_mutlak_fark) }),
        a.lab_turetildi
          ? rozet("laboratuvar değeri türetilmiş", "r-orta")
          : rozet("doğrudan ölçümle karşılaştırıldı", "r-olcum"),
      ])));

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
    bolum("02", "Hangi ölçüm ne kadar tuttu",
      "Tutma ölçütü: SoilGrids'in ilçe medyanı, laboratuvarın çeyrek "
      + "aralığına düşüyor mu. Laboratuvar değeri türetilmişse bu test "
      + "uygulanamaz — o satırlar ayrı sayılır, orana katılmaz.",
      alanBolum),
    bolum("03", "İlçe ilçe: üç sayı yan yana",
      "Üçünün birbirini tuttuğu yerde o değere güvenilebilir. Ayrıştığı "
      + "yerde hangisinin yanlış olduğunu bu tablo söylemez; nereye "
      + "bakılacağını söyler.",
      ayrintiBolum),
    bolum("04", "Doğrulanamayanlar — ve neden önemli",
      "Bir doğrulamanın en dürüst kısmı, neyi doğrulayamadığını "
      + "yazdığı yerdir.",
      eksikBolum),
  ];
}
