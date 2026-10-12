// Denge ve yem sekmesi: yem bilançosu, fabrika kotası, ilçe dengesi.

function sekmeDenge() {
  const k = MUS.kota;

  const yemTablo = tablo(
    [{ ad: "İlçe" }, { ad: "Hayvan", num: true }, { ad: "İhtiyaç (ton KM)", num: true },
     { ad: "Mera", num: true }, { ad: "Anız", num: true }, { ad: "Yem bitkisi", num: true },
     { ad: "Kesif", num: true }, { ad: "Karşılama", num: true }, { ad: "Açık", num: true },
     { ad: "Gereken ek yonca (da)", num: true }],
    MUS.yem.map(y => [
      y.ilce, n0(y.buyukbas + y.kucukbas), n0(y.ihtiyac_ton),
      n0(y.mera_ton), n0(y.aniz_ton), n0(y.kaba_ton), n0(y.kesif_ton),
      el("span", {}, rozet("%" + Math.round(y.karsilama * 100),
        y.karsilama >= 0.65 ? "r-orta" : "r-kotu")),
      n0(y.acik_ton), n0(y.ek_yonca_dekar)]));

  const kotaTablo = tablo(
    [{ ad: "İlçe" }, { ad: "Pancar alanı (da)", num: true }, { ad: "Üretim (ton)", num: true },
     { ad: "Fabrika payı (ton)", num: true }, { ad: "Durum" }],
    k.ilce.map(d => [d.ilce, n0(d.alan), n0(d.uretim), n0(d.kota),
      d.kota >= d.uretim - 1 ? rozet("tamamı alınır", "r-iyi") : rozet("kota kısıntısı", "r-kotu")]));

  // İlçe seçimli denge tablosu
  const durumRozet = d => d === "fazla" ? rozet("fazla", "r-orta")
    : d === "açık" ? rozet("açık", "r-kotu")
    : d === "dengeli" ? rozet("dengeli", "r-iyi") : rozet("—", "r-notr");

  const kutu = el("div", { class: "cizelge" });
  const secim = el("div", { class: "ilce-sec" });
  let aktif = MUS.ilceler[0].ad;

  function ciz() {
    const satirlar = MUS.denge.filter(d => d.ilce === aktif)
      .sort((a, b) => b.alan_dekar - a.alan_dekar);
    const maks = Math.max(...satirlar.map(s => Math.max(s.uretim_ton, s.ihtiyac_ton)));
    kutu.replaceChildren(el("table", {},
      el("thead", {}, el("tr", {},
        ["Ürün", "Tip", "Alan (da)", "Üretim", "İhtiyaç", "Birim", "Arz / ihtiyaç", "",
         "Hedef alan (da)", "Durum"]
          .map((b, i) => el("th", { class: [2, 3, 4, 6, 8].includes(i) ? "num" : null, text: b })))),
      el("tbody", {}, satirlar.map(s => el("tr", {},
        el("td", { text: s.urun }),
        el("td", {}, rozet(s.tip, "r-notr")),
        el("td", { class: "num", text: n0(s.alan_dekar) }),
        el("td", { class: "num", text: n0(s.uretim_ton) }),
        el("td", { class: "num", text: s.ihtiyac_ton ? n0(s.ihtiyac_ton) : "—" }),
        el("td", { style: "font-size:12px;color:var(--muted)", text: s.birim }),
        el("td", { class: "num", text: s.oran == null ? "—" : "×" + n1(s.oran) }),
        el("td", { style: "width:104px" },
          cubuk(s.uretim_ton, maks, s.durum === "açık" ? "var(--critical)"
            : s.durum === "fazla" ? "var(--warning)" : "var(--s3)",
            s.ihtiyac_ton || null)),
        el("td", { class: "num mono",
          style: s.hedef_alan && s.hedef_alan > s.alan_dekar * 1.1
            ? "color:var(--critical);font-weight:600" : null,
          text: s.hedef_alan ? n0(s.hedef_alan) : "—" }),
        el("td", {}, durumRozet(s.durum)))))));
  }
  for (const i of MUS.ilceler) {
    const b = el("button", { type: "button", text: i.ad,
      "aria-pressed": String(i.ad === aktif),
      onclick: () => { aktif = i.ad;
        [...secim.children].forEach(c => c.setAttribute("aria-pressed", String(c.textContent === aktif)));
        ciz(); } });
    secim.append(b);
  }
  ciz();

  return [
    bolum("01", "Yem bilançosu",
      "Mera ve anız dahil edildi; dahil edilmeseydi açık gerçekte olduğundan çok daha "
      + "büyük görünürdü. Kesif yem, arpa danesinin hayvana giden payıdır. "
      + "Hepsi kuru madde (KM) cinsinden.",
      yemTablo,
      el("div", { class: "uyari", html: "<strong>Okuma notu:</strong> Karşılama oranı "
        + "hiçbir ilçede %70'e ulaşmıyor. Bu, hayvan sayısının azalması gerektiği "
        + "anlamına gelmez; yem bitkisi alanının artması gerektiği anlamına gelir. "
        + "Tablonun son sütunu açığı kapatacak yonca alanını veriyor." })),
    bolum("02", "Şeker pancarı ve fabrika kotası",
      `Fabrikanın işleyebileceği pancar bir tavan koyuyor: günde `
      + `${n0(k.gunluk_kapasite_ton || 6000)} ton × ${n0(k.kampanya_gun || 95)} gün = `
      + `${n0(k.tavan_ton)} ton. Ortalama verim ${n1(k.ortalama_verim)} ton/dekar ile `
      + `bu ${n0(k.tavan_alan_dekar)} dekara denk geliyor.`,
      kotaTablo),
    bolum("03", "İlçe bazında arz-ihtiyaç dengesi",
      "Çubuktaki dikey çizgi ihtiyacı, dolu kısım üretimi gösterir. Kaba yem "
      + "ürünlerinde her iki taraf da kuru madde (KM) cinsindendir; yoksa %32 kuru "
      + "maddeli silaj ile %88 kuru maddeli yonca toplanamaz. Şeker pancarının "
      + "'ihtiyacı' fabrika kotasıdır, tüketim değil. Son sütun, bugünkü verimle "
      + "ihtiyacı karşılayacak ekim alanıdır.",
      secim, kutu),
  ];
}
