// Depo sekmesinin çizim yardımcıları: SVG kurucu, doz–cevap
// eğrisi ve sıcaklık karşıtlığı grafiği. Sekmenin kendisi
// 38_sekme_depo.js içinde; burada yalnızca çizim var.
// Ayrılma sebebi: tek dosya 260 satır sınırını aştı
// (tests/test_panel.py), ve çizim zaten ayrı bir iş.

const DEPO_RENK = { nokta: "#eb6834", yigin: "#eb6834", dis: "#2a78d6" };
// Maruz kalma süresi arttıkça koyulaşan bir dizi; eğrinin sola kayışı
// renkten de okunsun diye.
const SURE_RENK = ["#a9c9e8", "#6aa3da", "#2a78d6", "#143f78"];

// --- küçük bir SVG çizim yardımcısı (panelin başka yerinde kullanılmıyor)
function svgEl(tag, attrs = {}) {
  const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  return e;
}

// Birden çok süreyi aynı eksende çizer. Tek bir eğri yerine dördünü üst
// üste koymanın sebebi: LC50'nin süreyle sola kayışı bu sekmenin anlattığı
// asıl şey ve tek grafikte görünüyor.
function dozCevapGrafik(seriler) {
  const G = 680, Y = 330, sol = 54, sag = 86, ust = 14, alt = 46;
  const gw = G - sol - sag, gh = Y - ust - alt;
  const hepsi = seriler.flatMap(s => (s.egri || []).map(p => p.doz));
  const x0 = Math.log10(Math.min(...hepsi)), x1 = Math.log10(Math.max(...hepsi));
  const px = d => sol + (Math.log10(d) - x0) / (x1 - x0) * gw;
  const py = o => ust + (1 - o) * gh;

  const svg = svgEl("svg", {
    viewBox: `0 0 ${G} ${Y}`, width: "100%", role: "img",
    "aria-label": "Doz–cevap eğrileri, maruz kalma süresine göre",
  });

  for (let i = 0; i <= 4; i++) {
    const o = i / 4;
    svg.appendChild(svgEl("line", {
      x1: sol, y1: py(o), x2: sol + gw, y2: py(o),
      stroke: "var(--cizgi)", "stroke-width": o === 0.5 ? 1.4 : 1,
      "stroke-dasharray": o === 0.5 ? "5 4" : null }));
    const t = svgEl("text", {
      x: sol - 8, y: py(o) + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--muted)" });
    t.textContent = "%" + Math.round(o * 100);
    svg.appendChild(t);
  }
  for (const d of [100, 200, 400, 800, 1600]) {
    if (Math.log10(d) < x0 || Math.log10(d) > x1) continue;
    const t = svgEl("text", {
      x: px(d), y: ust + gh + 18, "text-anchor": "middle",
      "font-size": 11, fill: "var(--muted)" });
    t.textContent = String(d);
    svg.appendChild(t);
  }
  const eksenAd = svgEl("text", {
    x: sol + gw / 2, y: ust + gh + 38, "text-anchor": "middle",
    "font-size": 11.5, fill: "var(--muted)" });
  eksenAd.textContent = "doz (ppm, logaritmik eksen)";
  svg.appendChild(eksenAd);

  seriler.forEach((s, i) => {
    const renk = SURE_RENK[i % SURE_RENK.length];
    if (s.egri) {
      svg.appendChild(svgEl("path", {
        d: s.egri.map((p, j) => `${j ? "L" : "M"}${px(p.doz).toFixed(1)},${py(p.olum).toFixed(1)}`).join(" "),
        fill: "none", stroke: renk, "stroke-width": 2, "stroke-linejoin": "round" }));
    }
    for (const p of s.noktalar) {
      svg.appendChild(svgEl("circle", {
        cx: px(p.doz), cy: py(p.olum), r: 4,
        fill: renk, stroke: "var(--yuzey)", "stroke-width": 1.5 }));
    }
    // LC50 yalnızca ÖLÇÜLEN doz aralığına düşüyorsa işaretleniyor.
    // Dışarı düşenler çizelgede ayrıca belirtiliyor; grafikte göstermek,
    // ölçülmemiş bir yeri ölçülmüş gibi sunmak olurdu.
    const k = s.lc && s.lc.LC50;
    if (k && k.deger && !k.disinda) {
      svg.appendChild(svgEl("line", {
        x1: px(k.deger), y1: py(0.5), x2: px(k.deger), y2: ust + gh,
        stroke: renk, "stroke-width": 1, "stroke-dasharray": "3 3", opacity: 0.8 }));
      svg.appendChild(svgEl("circle", {
        cx: px(k.deger), cy: py(0.5), r: 3.5, fill: "var(--yuzey)",
        stroke: renk, "stroke-width": 2 }));
    }
    // sağ kenarda süre etiketi, eğrinin bittiği yükseklikte
    const son = s.egri ? s.egri[s.egri.length - 1] : null;
    if (son) {
      const t = svgEl("text", {
        x: sol + gw + 8, y: py(son.olum) + 4, "font-size": 11.5,
        fill: renk, "font-weight": 600 });
      t.textContent = `${n0(s.sure)} gün`;
      svg.appendChild(t);
    }
  });
  return svg;
}

// İki yayının çakıştığı tek noktayı iki çubukla gösterir.
function karsitlikGrafik(k) {
  const satir = (y, renk) => el("div", {
    style: "display:flex;align-items:center;gap:12px;margin:8px 0" },
    el("div", { style: "min-width:150px;font-size:12.5px",
      text: `${n0(y.sicaklik)} °C · %${n0(y.nem)} nem` }),
    el("div", { style: "flex:1;background:var(--cizgi);height:22px;border-radius:4px;overflow:hidden" },
      el("div", { style: `width:${y.olum}%;height:100%;background:${renk}` })),
    el("div", { class: "mono", style: "min-width:54px;text-align:right;font-weight:600",
      text: "%" + n1(y.olum) }));
  // Mavi = serin koşul, turuncu = sıcak koşul. Yeşil/kırmızı kullanılmıyor:
  // düşük ölüm çiftçi için iyi haber değil, mücadelenin işlememesi demek.
  return el("div", { class: "cerceve" },
    satir(k.dusuk, DEPO_RENK.dis),
    satir(k.yuksek, DEPO_RENK.nokta));
}

