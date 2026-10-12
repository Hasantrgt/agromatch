// İlçe haritası. Etiket çakışmaları aday yer denenerek çözülür.

function harita(degerFn, etiketFn, baslik) {
  const il = MUS.ilceler;
  const enlemler = il.map(i => i.enlem), boylamlar = il.map(i => i.boylam);
  const [eMin, eMaks] = [Math.min(...enlemler), Math.max(...enlemler)];
  const [bMin, bMaks] = [Math.min(...boylamlar), Math.max(...boylamlar)];
  // Enlem düzeltmesi: 39°K'de bir boylam derecesi bir enlem derecesinden kısadır
  const kosEnlem = Math.cos((eMin + eMaks) / 2 * Math.PI / 180);
  const genKm = (bMaks - bMin) * 111 * kosEnlem, yukKm = (eMaks - eMin) * 111;

  const G = 540, pad = 58;
  const Y = Math.round(Math.max(210, Math.min(300,
    (G - 2 * pad) * (yukKm / (genKm || 1)) + 2 * pad)));
  const x = b => pad + (b - bMin) / ((bMaks - bMin) || 1) * (G - 2 * pad);
  const y = e => Y - pad - (e - eMin) / ((eMaks - eMin) || 1) * (Y - 2 * pad);

  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${G} ${Y}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", baslik);
  const mk = (t, a) => { const n = document.createElementNS(ns, t);
    for (const [k, v] of Object.entries(a)) n.setAttribute(k, v); return n; };

  // Konumları hesapla, sonra etiketleri çakışmayacak şekilde yerleştir
  const dugum = il.map(i => ({
    ad: i.ad, d: degerFn(i.ad), alt: etiketFn ? etiketFn(i.ad) : null,
    cx: x(i.boylam), cy: y(i.enlem),
    r: 14 + Math.sqrt(i.nufus / 193000) * 11,
  }));
  // Etiket çakışmasını çöz: her etiket için bir kutu ayır, dolu olanı kaydır.
  // Aday yerler sırayla denenir — altta, üstte, sağda, solda.
  dugum.sort((a, b) => a.cx - b.cx);
  const ADAY = [
    { dx: 0, dy: 1, hiza: "middle" }, { dx: 0, dy: -1, hiza: "middle" },
    { dx: 1, dy: 0, hiza: "start" }, { dx: -1, dy: 0, hiza: "end" },
  ];
  const kutular = [];
  const cakisir = (a, b) => a.x1 < b.x2 && a.x2 > b.x1 && a.y1 < b.y2 && a.y2 > b.y1;

  for (const n of dugum) {
    const g = Math.max(52, n.ad.length * 7.2), y = n.alt ? 28 : 15;
    let secilen = null;
    for (const a of ADAY) {
      const mx = n.cx + a.dx * (n.r + g / 2 + 5);
      const my = n.cy + a.dy * (n.r + y / 2 + 5);
      const kutu = { x1: mx - g / 2, x2: mx + g / 2, y1: my - y / 2, y2: my + y / 2 };
      // Çizim alanının dışına taşmasın ve başka etiketle/daireyle çakışmasın
      const disarda = kutu.x1 < 4 || kutu.x2 > G - 4
        || kutu.y1 < 26 || kutu.y2 > Y - 6;
      const carpar = kutular.some(k => cakisir(kutu, k))
        || dugum.some(d => d !== n && cakisir(kutu, {
          x1: d.cx - d.r, x2: d.cx + d.r, y1: d.cy - d.r, y2: d.cy + d.r }));
      if (!disarda && !carpar) { secilen = { a, mx, my, kutu }; break; }
    }
    if (!secilen) {
      const mx = n.cx, my = n.cy + n.r + y / 2 + 5;
      secilen = { a: ADAY[0], mx, my,
        kutu: { x1: mx - g / 2, x2: mx + g / 2, y1: my - y / 2, y2: my + y / 2 } };
    }
    n.etiketX = secilen.a.hiza === "start" ? n.cx + n.r + 6
      : secilen.a.hiza === "end" ? n.cx - n.r - 6 : n.cx;
    n.etiketY = secilen.a.dy === 0 ? n.cy + (n.alt ? -1 : 4)
      : secilen.a.dy > 0 ? n.cy + n.r + 14 : n.cy - n.r - (n.alt ? 18 : 7);
    n.hiza = secilen.a.hiza;
    kutular.push(secilen.kutu);
  }

  for (const n of dugum) {
    svg.append(mk("circle", { cx: n.cx, cy: n.cy, r: n.r, fill: n.d.renk,
      "fill-opacity": 0.88, stroke: "var(--page)", "stroke-width": 2 }));
    const deger = mk("text", { x: n.cx, y: n.cy + 4.5, "text-anchor": "middle",
      "font-size": 12.5, "font-family": "IBM Plex Mono, monospace",
      "font-weight": 600, fill: "#fff" });
    deger.textContent = n.d.metin;
    svg.append(deger);

    const ad = mk("text", { x: n.etiketX, y: n.etiketY, "text-anchor": n.hiza,
      "font-size": 12, "font-family": "IBM Plex Sans, sans-serif",
      "font-weight": 500, fill: "var(--ink)" });
    ad.textContent = n.ad;
    svg.append(ad);
    if (n.alt) {
      const alt = mk("text", { x: n.etiketX, y: n.etiketY + 13, "text-anchor": n.hiza,
        "font-size": 10.5, "font-family": "IBM Plex Mono, monospace",
        fill: "var(--muted)" });
      alt.textContent = n.alt;
      svg.append(alt);
    }
  }

  const pusula = mk("text", { x: G - 12, y: 18, "text-anchor": "end", "font-size": 10.5,
    "font-family": "IBM Plex Mono, monospace", fill: "var(--muted)" });
  pusula.textContent = "↑ kuzey · daire = nüfus";
  svg.append(pusula);
  // Ölçek çubuğu — sol üstte, etiketlerden uzakta
  const km20 = (G - 2 * pad) * (20 / (genKm || 1));
  svg.append(mk("line", { x1: 12, y1: 16, x2: 12 + km20, y2: 16,
    stroke: "var(--axis)", "stroke-width": 2 }));
  for (const u of [12, 12 + km20]) {
    svg.append(mk("line", { x1: u, y1: 12, x2: u, y2: 20,
      stroke: "var(--axis)", "stroke-width": 2 }));
  }
  const ol = mk("text", { x: 12 + km20 + 7, y: 20, "font-size": 10,
    "font-family": "IBM Plex Mono, monospace", fill: "var(--muted)" });
  ol.textContent = "20 km";
  svg.append(ol);
  return el("div", { class: "harita" }, svg);
}
