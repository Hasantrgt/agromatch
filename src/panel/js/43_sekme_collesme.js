// Çölleşme sekmesi: Muş'un çölleşmeye duyarlılığı (DSI).

const DSI_RENK = { "düşük": "#2f7d4f", "orta": "#d9a441",
                   "yüksek": "#eb6834", "çok yüksek": "#c0392b" };

function dsiOlcek(deger) {
  // 1,00–2,00 arasını dört sınıfa bölen yatay ölçek
  const en = 280, alt = 1.0, ust = 2.0;
  const px = v => Math.round((v - alt) / (ust - alt) * en);
  const kap = el("div", { style: `position:relative;width:${en}px;height:20px` });
  let onceki = alt;
  for (const s of COLLESME.siniflar) {
    const sag = Math.min(s.ust, ust);
    kap.append(el("div", { title: s.ad,
      style: `position:absolute;left:${px(onceki)}px;top:6px;`
        + `width:${Math.max(px(sag) - px(onceki), 1)}px;height:8px;`
        + `background:${DSI_RENK[s.ad]};opacity:.35` }));
    onceki = sag;
  }
  kap.append(el("div", { style: `position:absolute;left:${px(deger)}px;top:0;`
    + "width:3px;height:20px;background:var(--ink);border-radius:2px" }));
  return kap;
}

function sekmeCollesme() {
  if (!COLLESME || !COLLESME.satirlar || !COLLESME.satirlar.length) {
    return [bolum("01", "Çölleşme verisi üretilmemiş",
      "Üretmek için: python src/collesme/dsi.py")];
  }
  const o = COLLESME.ozet;
  const r = COLLESME.resmi;

  // --- 01 resmî harita ne diyor
  const resmiBolum = el("div", {},
    el("div", { class: "kutu" },
      el("strong", { text: "Bu, resmî çölleşme haritası DEĞİLDİR." }),
      el("p", { text: `${r.ad}, ${r.kurum} tarafından üretildi (${r.yontem}) `
        + "ve e-Devlet'ten sorgulanabiliyor. Muş'un resmî sınıfı oradan "
        + "okunmalıdır. Aşağıdaki hesap, yayımlanmış bir yöntemi bu projenin "
        + "kendi ölçtüğü veriye uygulamaktan ibarettir — resmî haritanın "
        + "yerini tutmaz, onu ilçe ölçeğinde tamamlar." })),
    el("div", { class: "tiles" },
      ...[["Türkiye — yüksek", "%" + n1(r.ulke_dagilimi["yüksek"]),
            `orta %${n1(r.ulke_dagilimi.orta)} · zayıf %${n1(r.ulke_dagilimi["zayıf"])}`],
          ["Tarım arazisi — yüksek", "%" + n1(r.tarim_arazisi["yüksek"]),
            "ülke genelinde tarım arazilerinin payı"],
          ["Mera — yüksek", "%" + n1(r.mera["yüksek"]),
            "meralar tarım arazisinden daha riskli"]]
        .map(([b, d, a]) => el("div", { class: "tile" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))));

  // --- 02 ilçe DSI
  const dsiTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "ilçe" }, { ad: "SQI", num: true }, { ad: "CQI", num: true },
           { ad: "VQI", num: true }, { ad: "HQI", num: true },
           { ad: "DSI", num: true }, { ad: "sınıf" }, { ad: "ölçek" }],
      COLLESME.satirlar.sort((a, b) => b.dsi - a.dsi).map(s => [
        el("span", {}, el("strong", { text: s.ilce }),
          el("div", { style: "font-size:11px;color:var(--muted)",
            text: `SQI girdilerinin ${s.olculen_girdi}/${s.girdi_sayisi}'i ölçüm` })),
        el("span", { class: "mono", text: n2(s.sqi) }),
        el("span", { class: "mono", style: "color:var(--muted)", text: n2(s.cqi) }),
        el("span", { class: "mono", text: n2(s.vqi) }),
        el("span", { class: "mono", style: "font-weight:600", text: n2(s.hqi) }),
        el("span", { class: "mono", style: "font-weight:700", text: n2(s.dsi) }),
        rozet(s.sinif, s.sinif === "yüksek" || s.sinif === "çok yüksek"
          ? "r-dagitim" : "r-varsayim"),
        dsiOlcek(s.dsi),
      ])));

  // --- 03 asıl bulgu: ne sürüklüyor
  const sqi = COLLESME.satirlar.map(s => s.sqi);
  const hqi = COLLESME.satirlar.map(s => s.hqi);
  const yay = d => Math.round((Math.max(...d) - Math.min(...d)) * 1000) / 1000;
  const bulgu = el("div", {},
    el("div", { class: "tiles" },
      ...[["Toprak kalitesi (SQI)", n2(Math.min(...sqi)) + "–" + n2(Math.max(...sqi)),
            "1'e yakın = iyi. Muş'un toprağı sorun değil."],
          ["İnsan etkisi (HQI)", n2(Math.min(...hqi)) + "–" + n2(Math.max(...hqi)),
            "ilçeleri birbirinden ayıran asıl etken"],
          ["İklim (CQI)", n2(COLLESME.satirlar[0].cqi),
            "altı ilçede de aynı — ayrım yapmıyor"]]
        .map(([b, d, a]) => el("div", { class: "tile vurgu" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))),
    el("p", { class: "note", text: `SQI yayılımı ${n2(yay(sqi))}, HQI yayılımı `
      + `${n2(yay(hqi))}. Yani Muş'ta çölleşme riskini belirleyen şey toprağın `
      + "kendisi değil, EROZYON ve ARAZİ KULLANIMI. Bu iyi haber: toprak "
      + "kalitesi kolay değişmez ama arazi kullanımı değişir." }),
    el("div", { class: "bulgu" }, COLLESME.satirlar
      .sort((a, b) => b.hqi - a.hqi).slice(0, 3)
      .map(s => el("div", { class: "kart" },
        el("div", { class: "ust", style: "justify-content:space-between" },
          el("h3", { text: s.ilce }),
          rozet("DSI " + n2(s.dsi), "r-dagitim")),
        el("p", { text: `Su erozyonu ağırlığı ${n2(s.hqi_parca.su_erozyonu)} `
          + `(1 en iyi, 2 en kötü). Arazinin %${n0(s.tarim_payi * 100)}'i ekili, `
          + `%${n0(s.mera_payi * 100)}'i mera.` }),
        el("p", { class: "kazanc", text: "Erozyon kontrolü ve mera yönetimi "
          + "bu ilçede DSI'yi düşürecek tek kaldıraç." })))));

  // --- 04 yöntem ve ayrımlar
  const yontem = el("div", {},
    el("p", { style: "font-size:12.5px" },
      el("strong", { text: "Yöntem: " }), COLLESME.kaynak),
    el("p", { class: "mono", style: "font-size:12px;color:var(--muted)",
      text: "DSI = (SQI × CQI × VQI × HQI)^(1/4)" }),
    el("h3", { class: "cati-baslik", text: "Yayından bilerek ayrıldığımız yerler" }),
    el("div", { class: "liste" }, COLLESME.ayrim.map((a, i) =>
      el("div", { class: "madde" },
        el("span", { class: "sira mono", text: String(i + 1) }),
        el("div", { class: "govde" }, el("p", { text: a }))))),
    el("p", { class: "uyari", text: r.not_ }));

  // --- 04 kaldıraçlar: nereye müdahale edilirse ne olur
  const senaryoBolum = el("div", {});
  for (const s of COLLESME.satirlar) {
    const liste = (COLLESME.senaryo || {})[s.ilce] || [];
    if (!liste.length) continue;
    senaryoBolum.append(
      el("h3", { class: "cati-baslik",
        text: `${s.ilce} — şu an DSI ${n2(s.dsi)} (${s.sinif})` }),
      el("div", { class: "kaydir" },
        tablo([{ ad: "kaldıraç" }, { ad: "DSI", num: true },
               { ad: "kazanç", num: true }, { ad: "sınıf" }, { ad: "nasıl" },
               { ad: "süre" }],
          liste.map(k => [
            el("strong", { text: k.ad }),
            el("span", { class: "mono",
              text: `${n2(k.dsi_once)} → ${n2(k.dsi_sonra)}` }),
            el("span", { class: "mono", style: "font-weight:600;color:var(--good)",
              text: "−" + n2(k.kazanc) }),
            k.sinif_degisti
              ? el("span", { style: "color:var(--good);font-weight:600",
                  text: `${k.sinif_once} → ${k.sinif_sonra}` })
              : el("span", { style: "color:var(--muted)", text: "değişmez" }),
            el("span", { style: "font-size:12.5px", text: k.nasil }),
            el("span", { class: "mono", style: "font-size:12px", text: k.sure }),
          ]))));
  }

  return [
    bolum("01", "Türkiye'nin resmî haritası ne diyor",
      "Çölleşme, Muş gibi yarı kurak bir ovada soyut bir tehdit değil. "
      + "Önce resmî çerçeve, sonra bizim hesabımız.",
      resmiBolum),
    bolum("02", "Muş'un altı ilçesi için DSI",
      `Altı ilçenin tamamı "${o.sinif_dagilimi["yüksek"] === 6 ? "yüksek" : "karışık"}" `
      + `sınıfında; ortalama DSI ${n2(o.ortalama_dsi)}. En duyarlı `
      + `${o.en_duyarli} (${n2(o.en_duyarli_dsi)}), en az duyarlı `
      + `${o.en_az_duyarli} (${n2(o.en_az_duyarli_dsi)}). Aradaki fark küçük: `
      + "endeks il içinde ayrım yapmıyor, bunu da yazmak gerekiyor.",
      dsiTablo),
    bolum("03", "Riski ne sürüklüyor — ve nereye müdahale edilir",
      "Bir endeksin değeri, nereye bakılacağını söylemesindedir.",
      bulgu),
    bolum("04", "Kaldıraçlar: nereye müdahale edilirse ne olur",
      "Endeksi hesaplamak yarım iş. Asıl soru, hangi müdahalenin sayıyı "
      + "hareket ettireceği. Aşağıdaki her satır bir senaryodur: o "
      + "parametre bir sınıf iyileşirse DSI nereye iner. "
      + "DİKKAT: en büyük kaldıraç olan drenaj hâlâ VARSAYIM — ölçülmedi. "
      + "Yani ölçülmesi gereken ilk şey o.",
      senaryoBolum),
    bolum("05", "Yöntem ve sınırları",
      "Hesabın tamamı yayımlanmış sınıf ağırlıklarına dayanıyor; "
      + "uydurulmuş katsayı yok. Veri yetmediği için çıkarılan parametreler "
      + "aşağıda tek tek yazılı.",
      yontem),
  ];
}
