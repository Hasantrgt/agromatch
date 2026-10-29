// Depo sekmesi: hasat sonrası. Doz–cevap eğrisi, ambar sıcaklığı,
// gelişme penceresi ve mücadele karşılaştırması.

const DEPO_RENK = { egri: "#2a78d6", nokta: "#eb6834", yigin: "#eb6834", dis: "#2a78d6" };

// --- küçük bir SVG çizim yardımcısı (panelin başka yerinde kullanılmıyor)
function svgEl(tag, attrs = {}) {
  const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  return e;
}

function dozCevapGrafik(dc) {
  const G = 680, Y = 320, sol = 54, sag = 18, ust = 16, alt = 46;
  const gw = G - sol - sag, gh = Y - ust - alt;
  const dozlar = dc.egri.map(p => p.doz);
  const x0 = Math.log10(Math.min(...dozlar)), x1 = Math.log10(Math.max(...dozlar));
  const px = d => sol + (Math.log10(d) - x0) / (x1 - x0) * gw;
  const py = o => ust + (1 - o) * gh;

  const svg = svgEl("svg", {
    viewBox: `0 0 ${G} ${Y}`, width: "100%", role: "img",
    "aria-label": "Doz–cevap eğrisi",
  });

  // ızgara ve eksen etiketleri
  for (let i = 0; i <= 4; i++) {
    const o = i / 4;
    svg.appendChild(svgEl("line", {
      x1: sol, y1: py(o), x2: sol + gw, y2: py(o),
      stroke: "var(--cizgi)", "stroke-width": 1 }));
    const t = svgEl("text", {
      x: sol - 8, y: py(o) + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--muted)" });
    t.textContent = "%" + Math.round(o * 100);
    svg.appendChild(t);
  }
  const tikDoz = [100, 200, 400, 800, 1600].filter(d =>
    Math.log10(d) >= x0 && Math.log10(d) <= x1);
  for (const d of tikDoz) {
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

  // LC50 / LC90 kılavuz çizgileri
  for (const [ad, k] of Object.entries(dc.lc)) {
    if (!k.deger || !(Math.log10(k.deger) >= x0 && Math.log10(k.deger) <= x1)) continue;
    if (ad === "LC95") continue;
    const hedef = ad === "LC50" ? 0.5 : 0.9;
    if (k.alt && k.ust) {
      svg.appendChild(svgEl("rect", {
        x: px(k.alt), y: py(hedef) - 5, width: Math.max(px(k.ust) - px(k.alt), 1),
        height: 10, fill: DEPO_RENK.egri, opacity: 0.16 }));
    }
    svg.appendChild(svgEl("line", {
      x1: px(k.deger), y1: py(hedef), x2: px(k.deger), y2: ust + gh,
      stroke: "var(--muted)", "stroke-width": 1, "stroke-dasharray": "4 3" }));
    // Etiket normalde çizginin sağına yazılır; sağ kenara yakınsa sola
    // çevrilir, yoksa grafiğin dışına taşıp kırpılıyor.
    const yazi = `${ad} ${n0(k.deger)}`;
    const sagaSigar = px(k.deger) + yazi.length * 7 < sol + gw;
    // Etiket eğrinin üstüne denk gelebiliyor; zemin rengiyle ince bir
    // kontur çizip üstüne yazıyoruz ki eğri metni yutmasın.
    const t = svgEl("text", {
      x: px(k.deger) + (sagaSigar ? 6 : -6), y: py(hedef) - 9,
      "text-anchor": sagaSigar ? "start" : "end",
      "font-size": 11, fill: "var(--ink)", "font-weight": 600,
      stroke: "var(--yuzey)", "stroke-width": 3.5, "paint-order": "stroke" });
    t.textContent = yazi;
    svg.appendChild(t);
  }

  // uydurulan eğri
  svg.appendChild(svgEl("path", {
    d: dc.egri.map((p, i) => `${i ? "L" : "M"}${px(p.doz).toFixed(1)},${py(p.olum).toFixed(1)}`).join(" "),
    fill: "none", stroke: DEPO_RENK.egri, "stroke-width": 2, "stroke-linejoin": "round" }));

  // gözlenen noktalar
  for (const p of dc.noktalar) {
    svg.appendChild(svgEl("circle", {
      cx: px(p.doz), cy: py(p.olum), r: 4.5,
      fill: DEPO_RENK.nokta, stroke: "var(--yuzey)", "stroke-width": 1.6 }));
  }
  return svg;
}

function sekmeDepo() {
  // Depo katmanı scipy/statsmodels olmadan üretilemiyor; o durumda panel
  // yine kurulur, bu sekme sebebini söyler.
  if (!DEPO.zararlilar.length) {
    return [bolum("01", "Depo verisi üretilmemiş",
      "Bu sekme depo katmanından besleniyor ve o katman scipy ile "
      + "statsmodels ister. Üretmek için: pip install -r requirements-depo.txt "
      + "ve ardından python src/mus_panel_uret.py --hepsi")];
  }

  const dc = DEPO.doz_cevap;
  const amb = DEPO.ambar;

  // --- 01 doz–cevap
  const lcSatir = Object.entries(dc.lc).map(([ad, k]) => k.deger
    ? [ad, n0(k.deger) + " ppm", k.alt ? `${n0(k.alt)} – ${n0(k.ust)}` : "—"]
    : [ad, "—", k.kestirilemedi || "kestirilemedi"]);

  const uyariKutu = dc.sentetik ? el("div", { class: "kutu" },
    el("strong", { text: "Bu grafik SENTETİK veriyle çizildi." }),
    el("p", { text: "Aracın çalıştığını göstermek için bilinen bir eğriden üretilmiş "
      + `sayılar kullanıldı. Üretimde kullanılan gerçek LC50 ${n0(dc.gercek_lc50)} ppm; `
      + `araç ${n0(dc.lc.LC50.deger)} ppm buldu. Danışman hocanın ham sayımları `
      + "geldiğinde aynı grafik gerçek veriyle çizilecek." })) : null;

  const dozBolum = el("div", {},
    uyariKutu,
    el("div", { class: "cerceve" }, dozCevapGrafik(dc)),
    el("div", { class: "tiles" },
      ...[["Eğim", n2(dc.egim), "doz iki katına çıkınca ölüm bahsi ×" + dc.iki_kat_etkisi],
          ["Kontrol ölümü", yuzde(dc.kontrol_olumu), "Abbott ile düzeltildi"],
          ["Gözlem", n0(dc.n_gozlem) + " kap", n0(dc.n_birey) + " birey"]]
        .map(([b, d, a]) => el("div", { class: "tile" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))),
    tablo([{ ad: "" }, { ad: "kestirim" }, { ad: "%95 güven aralığı" }], lcSatir),
    ...(dc.uyari || []).map(u => el("p", { class: "uyari", text: "Uyarı: " + u })));

  // --- 02 ambar sıcaklığı
  // -0,04 bir ondalığa yuvarlanınca "-0" yazılıyor; sıfıra yapıştır.
  const derece = t => n1(Math.abs(t) < 0.05 ? 0 : t);
  const sicaklikTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "ilçe" }, ...amb.aylar.map(a => ({ ad: a, num: true }))],
      amb.ilceler.flatMap(i => [
        [el("span", { text: i + " (dış)" }),
          ...amb.dis_hava[i].map(t => el("span", { class: "mono", style: "color:var(--muted)", text: derece(t) }))],
        [el("strong", { text: "  yığın" }),
          ...amb.yigin[i].map(t => el("span", { class: "mono", text: derece(t) }))],
      ])));

  // --- 03 gelişme penceresi: ilçe × zararlı ızgarası
  const turler = DEPO.zararlilar.map(z => z.ad);
  const bul = (ilce, zararli) =>
    amb.pencere.find(p => p.ilce === ilce && p.zararli === zararli);
  const pencereTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "zararlı" }, { ad: "eşik °C", num: true },
           ...amb.ilceler.map(i => ({ ad: i, num: true }))],
      turler.map(t => {
        const z = DEPO.zararlilar.find(x => x.ad === t);
        return [
          el("span", {}, el("strong", { text: t }),
            z.karantina ? rozet("karantina", "r-dagitim") : null,
            z.ic_besleyen ? el("span", { class: "mono", style: "font-size:11px;color:var(--muted)", text: " iç besleyen" }) : null),
          el("span", { class: "mono", text: n1(z.taban_sicaklik) }),
          ...amb.ilceler.map(i => {
            const p = bul(i, t);
            const ay = p ? p.elverisli_ay : 0;
            const renk = ay === 0 ? "var(--good)" : ay <= 3 ? "var(--s3)"
              : ay <= 6 ? "var(--warning)" : "var(--critical)";
            return el("span", { class: "mono", style: `color:${renk};font-weight:600`,
              text: ay === 0 ? "—" : ay + " ay" });
          })];
      })));

  // --- 04 mücadele karşılaştırması
  const evetHayir = (v, iyiEvet) => el("span", {
    style: `color:${v === iyiEvet ? "var(--good)" : "var(--critical)"};font-weight:600`,
    text: v ? "evet" : "hayır" });
  const riskRozet = r => rozet(r, r === "YÜKSEK" ? "r-dagitim"
    : r === "yok" ? "r-olcum" : "r-varsayim");

  const mucadeleTablo = el("div", { class: "kaydir" },
    tablo(["yöntem", "tip", "kalıntı", "direnç riski", "faydalıya", "iç larvaya",
           "organik"].map(a => ({ ad: a })),
      DEPO.mucadele.map(m => [
        el("strong", { text: m.ad }),
        m.tip,
        evetHayir(m.kalinti, false),
        riskRozet(m.direnc_riski),
        m.faydaliya,
        evetHayir(m.gucu.ic_larva, true),
        evetHayir(m.organik, true),
      ])));

  const kalintisiz = DEPO.mucadele.filter(m => !m.kalinti);
  const yolKart = el("div", { class: "bulgu" }, kalintisiz.map(m => el("div", { class: "kart" },
    el("div", { class: "ust", style: "justify-content:space-between" },
      el("h3", { text: m.ad }),
      rozet(m.tip, "r-olcum")),
    el("p", { text: m.mekanizma }),
    el("p", { class: "kazanc", text: m.gucu.ic_larva
      ? "Tanenin içindeki larvaya da ulaşır" : "Yalnızca ergine etkili" }),
    el("p", { style: "font-size:12.5px;color:var(--muted)", text: "Bedeli: " + m.bedel }))));

  return [
    bolum("01", "Doz–cevap: öldürücü doz kestirimi",
      "Bir mücadele denemesinin ham sayımlarından LC50 ve LC90 kestirilir. Yöntem "
      + "probit — hocanın literatürde okuduğu LC50 değerleri bu yöntemle üretilmiştir. "
      + "Kontrol grubundaki ölüm Abbott formülüyle ayıklanır. Güven aralıkları "
      + "parametrik önyüklemeyle hesaplanır; turuncu noktalar gözlenen tekrarlar, "
      + "mavi eğri uydurulan model, açık mavi bant LC'nin güven aralığıdır.",
      dozBolum),
    bolum("02", "Ambar sıcaklığı: yığın dışarıyı gecikmeli takip eder",
      `Tahıl yığını büyük bir ısı deposudur. Dış hava −5 °C'ye inerken yığının içi `
      + `haftalarca ılık kalır; bu yüzden "Muş soğuk, depoda sorun olmaz" sanısı `
      + `yanlıştır. Model, aylık yığın sıcaklığını dış havanın sönümlenmiş hâli olarak `
      + `hesaplar (sönümleme ${amb.sonumleme} — bir VARSAYIMDIR, ambara veri kaydedici `
      + `konarak ölçülmelidir).`,
      sicaklikTablo),
    bolum("03", "Gelişme penceresi: hangi zararlı kaç ay gelişebiliyor",
      "Her türün bir gelişme eşiği var. Isıtılmamış ambarda yığın sıcaklığı o eşiği "
      + "kaç ay aşıyorsa zararlı o kadar süre üreyebilir. Sıfır ay demek, soğuk tek "
      + "başına o türü durduruyor demektir — kalıntısız, dirençsiz, bedava. "
      + "Eşik değerleri literatürden alınmıştır ve danışman hocanın teyidini bekler.",
      pencereTablo),
    bolum("04", "Mücadele seçenekleri: kalıntı, direnç ve faydalıya etki",
      "Bu tablo ilaç TAVSİYE ETMEZ — ürün ve doz seçimi reçete yazma yetkisi olan "
      + "kişilerin kararıdır. Yaptığı iş yöntemleri aynı ölçütlerle yan yana koymak. "
      + "'İç larvaya' sütunu kritik: buğday biti larvası tanenin içinde geliştiği için "
      + "yalnızca ergine etkili bir yöntem gizli bulaşmayı temizlemez.",
      mucadeleTablo),
    bolum("05", "Kalıntı bırakmayan yol",
      `Sekiz yöntemin ${kalintisiz.length} tanesi üründe ölçülebilir kalıntı bırakmıyor. `
      + "\"Pestisitten arındırılmış yol\" bu seçeneklerin birleşiminden çıkar; hiçbiri "
      + "tek başına yeterli değildir.",
      yolKart),
  ];
}
