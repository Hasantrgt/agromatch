// Veri kalitesi sekmesinin çizim yardımcıları.
// 44_sekme_kalite.js 260 satır sınırını aştığı için ayrıldı;
// dosyalar ad sırasına göre yüklendiği için bu önce gelir.

// kalite.KOMSU_YER ile aynı küme — kesin Muş dışı olan yer adları
const KOMSU = new Set(["Bingöl", "Bitlis", "Osmaniye", "Solhan", "Güroymak"]);


// Yer sütunu kırılımı: hangi kutu iyi, hangisi kayıp
const KIRILIM_RENK = {
  "Muş ilçesine bağlandı": "var(--good)",
  "yer sütunu boş": "var(--warning)",
  "Muş dışı": "var(--critical)",
  "belirsiz sıralama": "var(--s5)",
  "tanınmayan yer": "var(--muted)",
};

// Kırılımı tek bir yatay şerit olarak çizer; genişlik = pay
function kirilimSeridi(kirilim, toplam) {
  const en = 560;
  const kap = el("div", {
    style: `display:flex;width:100%;max-width:${en}px;height:26px;`
      + "border-radius:5px;overflow:hidden;background:var(--grid)" });
  for (const [ad, n] of Object.entries(kirilim)) {
    if (!n) continue;
    const pay = n / toplam * 100;
    kap.append(el("div", {
      title: `${ad}: ${n0(n)} kayıt (%${n1(pay)})`,
      style: `width:${pay}%;background:${KIRILIM_RENK[ad] || "var(--s3)"};`
        + "display:flex;align-items:center;justify-content:center;"
        + "font-size:10.5px;font-weight:700;color:#fff;overflow:hidden",
      text: pay > 7 ? n0(n) : "" }));
  }
  return kap;
}

function kirilimEfsane(kirilim, toplam) {
  return el("div", { style: "display:flex;flex-wrap:wrap;gap:4px 18px;"
    + "margin-top:8px;font-size:12px" },
    ...Object.entries(kirilim).filter(([, n]) => n).map(([ad, n]) =>
      el("span", { style: "display:flex;align-items:center;gap:6px" },
        el("span", { style: "width:10px;height:10px;border-radius:2px;"
          + `background:${KIRILIM_RENK[ad] || "var(--s3)"}` }),
        el("span", { text: ad }),
        el("span", { class: "mono", style: "color:var(--muted)",
          text: `${n0(n)} · %${n1(n / toplam * 100)}` }))));
}

// Gözlenen ile şans beklentisini yan yana koyan iki çubuk
function sansCubugu(gozlenen, beklenen) {
  const en = 240, ust = Math.max(gozlenen, beklenen, 1);
  const bar = (v, renk, etiket) => el("div", {
    style: "display:flex;align-items:center;gap:8px;margin:3px 0" },
    el("span", { style: "width:112px;font-size:12px;color:var(--muted)",
      text: etiket }),
    el("div", { style: `width:${en}px;height:12px;background:var(--grid);`
      + "border-radius:3px;overflow:hidden" },
      el("div", { style: `width:${Math.max(v / ust * 100, v > 0 ? 1 : 0)}%;`
        + `height:100%;background:${renk}` })),
    el("span", { class: "mono", style: "font-weight:700",
      text: n1(v) }));
  return el("div", {},
    bar(gozlenen, "var(--critical)", "gözlenen"),
    bar(beklenen, "var(--s3)", "şans beklentisi"));
}
