// Doğrulama sekmesinin çizim ve yorum yardımcıları.
// 45_sekme_dogrulama.js 260 satır sınırını aştığı için ayrıldı;
// dosyalar ad sırasına göre yüklendiği için bu önce gelir.

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

// Üç testin birlikte söylediği şeyi tek cümleye indirger.
function dogrulamaSonuc(a) {
  if (!a.ayirt_edici && a.ayni_yon) {
    return "Sabit bir kayma var, ilçe ayrımı ise ölçüm gürültüsünden "
      + "küçük. Mutlak değer için laboratuvar esas alınmalı.";
  }
  if (!a.ayirt_edici) {
    return "İlçeler arası fark, ilçe içi yayılımdan küçük — bu ölçümle "
      + "ilçeler birbirinden ayrılamaz.";
  }
  if (a.ayni_yon) {
    return "Sistematik kayma var ama ilçe ayrımı ölçülebilir durumda.";
  }
  return a.siralama_uyumu != null && a.siralama_uyumu < 0
    ? "İki kaynak ilçeleri TERS sıralıyor: gerçek bir anlaşmazlık, "
      + "basit bir kayma değil. En çok incelenmesi gereken alan bu."
    : "Yön karışık; sapma sistematik değil.";
}

// Kil anlaşmazlığının tavsiyeye etkisi — doğrulamanın "ee, ne olmuş?"
// sorusuna cevabı. İstatistiksel bir fark, karar değiştirmiyorsa
// akademik kalır; değiştiriyorsa acildir.
function kilEtkisiBolumu() {
  if (!KIL || !KIL.var) return null;
  const o = KIL.ozet;
  const labSg = KIL.karsilastirmalar.find(k => k.ad === "laboratuvar -> SoilGrids");
  const varLab = KIL.karsilastirmalar.find(k => k.ad === "varsayım -> laboratuvar");

  const esikMetni = KIL.esikler
    .map(e => `kil ≥ ${n0(e.kil_en_az)} → ${e.sinif}`).join(" · ");

  return el("div", {},
    el("div", { class: "kutu" },
      el("strong", { text: "Kil puana doğrudan girmiyor." }),
      el("p", { text: "Önce bünye sınıfına çevriliyor (" + esikMetni
        + "), sonra o sınıf puanlanıyor. Yani bir kil farkı ancak SINIF "
        + "SINIRINI geçerse tavsiyeyi değiştirir. 26 ile 30 arasındaki "
        + "fark hiçbir şey değiştirmez; 34 ile 36 arasındaki fark her "
        + "şeyi değiştirir." })),
    el("div", { class: "tiles" },
      ...[["Varsayım yanlış çıkan ilçe",
            n0(o.sinifi_ayrisan_ilce) + " / " + n0(o.toplam_ilce),
            "bünye sınıfı kaynaklar arasında ayrışıyor"],
          ["Varsayım → laboratuvar", n0(varLab.sinif_degisen) + " tavsiye",
            "ölçüm bağlanınca değişen ilçe × ürün sınıfı"],
          ["Laboratuvar → SoilGrids", n0(labSg.sinif_degisen) + " tavsiye",
            "anlaşmazlığın tavsiyeye fiilen yansıması"],
          ["İki ölçüm aynı sınıfta",
            n0(o.lab_sg_ayni_sinif) + " / " + n0(o.toplam_ilce),
            "sayılar farklı olsa da sınıf aynı"]]
        .map(([b, d, a]) => el("div", { class: "tile" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))),
    el("div", { class: "kaydir" },
      tablo([{ ad: "ilçe" }, { ad: "varsayım" }, { ad: "laboratuvar" },
             { ad: "SoilGrids" }, { ad: "" }],
        KIL.ilceler.map(r => [
          el("strong", { text: r.ilce }),
          el("span", {}, el("span", { class: "mono",
              style: "color:var(--warn-ink)", text: n1(r.varsayim_kil) }),
            el("div", { style: "font-size:11px;color:var(--muted)",
              text: r.varsayim_bunye })),
          el("span", {}, el("span", { class: "mono",
              style: "font-weight:600", text: n1(r.lab_kil) }),
            el("div", { style: "font-size:11px;color:var(--muted)",
              text: r.lab_olcum_var ? r.lab_bunye
                : r.lab_bunye + " (ölçüm yok)" })),
          el("span", {}, el("span", { class: "mono",
              style: "color:var(--s1);font-weight:600", text: n1(r.sg_kil) }),
            el("div", { style: "font-size:11px;color:var(--muted)",
              text: r.sg_bunye })),
          !r.lab_olcum_var
            ? rozet("laboratuvar ölçümü yok", "r-kotu")
            : r.lab_sg_ayni_sinif
              ? rozet("iki ölçüm aynı sınıfta", "r-iyi")
              : rozet("ölçümler ayrı sınıfta", "r-orta"),
        ]))),
    labSg.sinif_degisenler.length
      ? el("div", {},
          el("h3", { class: "cati-baslik",
            text: "Anlaşmazlığın değiştirdiği tavsiyeler" }),
          el("div", { class: "kaydir" },
            tablo([{ ad: "ilçe" }, { ad: "ürün" }, { ad: "laboratuvarla" },
                   { ad: "SoilGrids ile" }, { ad: "fark", num: true }],
              labSg.sinif_degisenler.map(s => [
                el("strong", { text: s.ilce }), s.urun,
                el("span", { style: "color:var(--muted)",
                  text: `${n1(s.once_puan)} ${s.once_sinif}` }),
                el("span", { style: "font-weight:600",
                  text: `${n1(s.sonra_puan)} ${s.sonra_sinif}` }),
                el("span", { class: "mono",
                  text: (s.fark > 0 ? "+" : "") + n1(s.fark) }),
              ]))))
      : el("p", { class: "note", text: "Anlaşmazlık hiçbir tavsiyeyi "
          + "değiştirmiyor." }),
    KIL.lab_olcumu_olmayan.length
      ? el("p", { class: "uyari", text: "Asıl boşluk burada: "
          + KIL.lab_olcumu_olmayan.join(", ")
          + " için güvenilir laboratuvar kili yok, model orada hâlâ "
          + "varsayımla çalışıyor — ve varsayım, kontrol edilebilen beş "
          + "ilçenin beşinde de yanlış çıktı. Numune toplanacaksa "
          + "önceliği burası almalı." })
      : null);
}
