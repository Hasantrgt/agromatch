// Ortak yardımcılar: sayı biçimi, DOM kurucu, rozet, çubuk, tablo.

const TR = new Intl.NumberFormat("tr-TR");
const n0 = v => TR.format(Math.round(v));
const n1 = v => TR.format(Math.round(v * 10) / 10);
const yuzde = v => (v == null ? "—" : "%" + Math.round(v * 100));
const n2 = v => (v == null ? "—"
  : new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 2,
      maximumFractionDigits: 2 }).format(v));
const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") e.className = v;
    else if (k === "html") e.innerHTML = v;
    else if (k === "text") e.textContent = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return e;
};
const puanRenk = p => p >= 80 ? "var(--good)" : p >= 65 ? "var(--s3)"
  : p >= 50 ? "var(--warning)" : "var(--critical)";
const riskRenk = r => r >= 60 ? "var(--critical)" : r >= 35 ? "var(--warning)" : "var(--s3)";
const rozet = (metin, sinif) => el("span", { class: "rozet " + sinif, text: metin });
const KAYNAK_AD = { o: "ölçüm", v: "varsayım", d: "dağıtım" };
const kaynakEtiket = tur => el("span",
  { class: "kaynak k-" + { o: "olcum", v: "varsayim", d: "dagitim" }[tur],
    text: KAYNAK_AD[tur] });
const turRozet = t => t === "ölçüm" ? rozet("ölçüm", "r-olcum")
  : t === "varsayım" ? rozet("varsayım", "r-varsayim") : rozet("dağıtım", "r-dagitim");

function cubuk(deger, maks, renk, hedef) {
  const d = el("div", { class: "cubuk" });
  d.append(el("i", { style: `width:${Math.max(2, Math.min(100, deger / maks * 100))}%;background:${renk}` }));
  if (hedef != null) d.append(el("div", { class: "hedef", style: `left:${Math.min(99, hedef / maks * 100)}%` }));
  return d;
}

function tablo(basliklar, satirlar) {
  const thead = el("thead", {}, el("tr", {}, basliklar.map(b =>
    el("th", { class: b.num ? "num" : null, text: b.ad }))));
  const tbody = el("tbody", {}, satirlar.map(s => el("tr", {}, s.map((h, i) =>
    el("td", { class: basliklar[i].num ? "num" : null },
      h && h.nodeType ? h : document.createTextNode(h == null ? "—" : String(h)))))));
  return el("div", { class: "cizelge" }, el("table", {}, thead, tbody));
}

function bolum(no, baslik, aciklama, ...govde) {
  return el("section", {},
    el("div", { class: "sec-head" },
      el("span", { class: "sec-num", text: no }), el("h2", { text: baslik })),
    aciklama ? el("p", { class: "note", text: aciklama }) : null,
    ...govde);
}
