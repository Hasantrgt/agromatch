// Belirsizlik sekmesi: eylem tablosu, dağılımlar, ölçüm önceliği.

const EYLEM_ROZET = {
  "artır": "r-iyi", "fırsat": "r-iyi", "sınırlı artır": "r-orta",
  "önce ölç": "r-kotu", "azalt": "r-kotu", "koru": "r-notr", "gerek yok": "r-notr",
};

function dagilimCizimi(q) {
  const h = q.histogram, say = h.sayim, kenar = h.kenar;
  const G = 560, Y = 150, sol = 36, sag = 12, ust = 22, alt = 28;
  const maks = Math.max(...say, 1);
  const xMin = Math.min(kenar[0], 0.95), xMaks = Math.max(kenar[kenar.length - 1], 1.05);
  const px = v => sol + (v - xMin) / (xMaks - xMin) * (G - sol - sag);
  const py = v => Y - alt - v / maks * (Y - ust - alt);

  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${G} ${Y}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label",
    `${q.baslik}: arz/ihtiyaç ${n2(q.oran.medyan)}, %90 aralık `
    + `${n2(q.oran.alt90)} – ${n2(q.oran.ust90)}`);
  const mk = (t, a) => { const n = document.createElementNS(ns, t);
    for (const [k, v] of Object.entries(a)) n.setAttribute(k, v); return n; };

  svg.append(mk("rect", { x: px(q.oran.alt90), y: ust,
    width: Math.max(1, px(q.oran.ust90) - px(q.oran.alt90)),
    height: Y - ust - alt, fill: "var(--hl)" }));

  for (let i = 0; i < say.length; i++) {
    const x1 = px(kenar[i]), x2 = px(kenar[i + 1]);
    const orta = (kenar[i] + kenar[i + 1]) / 2;
    svg.append(mk("rect", { x: x1 + 0.4, y: py(say[i]),
      width: Math.max(0.8, x2 - x1 - 0.8), height: Y - alt - py(say[i]),
      fill: orta < 1 ? "var(--s2)" : "var(--s3)", "fill-opacity": 0.9 }));
  }

  // Yeterlilik eşiği
  if (xMin < 1 && xMaks > 1) {
    svg.append(mk("line", { x1: px(1), y1: ust - 6, x2: px(1), y2: Y - alt,
      stroke: "var(--ink)", "stroke-width": 1.6, "stroke-dasharray": "4 3" }));
    const e = mk("text", { x: px(1), y: ust - 9, "text-anchor": "middle",
      "font-size": 10.5, "font-family": "IBM Plex Mono, monospace",
      fill: "var(--ink-2)" });
    e.textContent = "yeterlilik";
    svg.append(e);
  }

  svg.append(mk("line", { x1: sol, y1: Y - alt, x2: G - sag, y2: Y - alt,
    stroke: "var(--axis)", "stroke-width": 1 }));
  const adim = (xMaks - xMin) > 2 ? 0.5 : (xMaks - xMin) > 0.8 ? 0.2 : 0.1;
  for (let v = Math.ceil(xMin / adim) * adim; v <= xMaks + 1e-9; v += adim) {
    const t = mk("text", { x: px(v), y: Y - alt + 14, "text-anchor": "middle",
      "font-size": 10, "font-family": "IBM Plex Mono, monospace",
      fill: "var(--muted)" });
    t.textContent = TR.format(Math.round(v * 100) / 100);
    svg.append(t);
  }
  return svg;
}

function sekmeBelirsizlik() {
  const B = BELIRSIZ;

  // ---------- 01 eylem tablosu
  const eylemTablo = tablo(
    [{ ad: "Ürün" }, { ad: "Eylem" }, { ad: "Denge ölçeği" },
     { ad: "Arz / ihtiyaç", num: true }, { ad: "En uygun ilçe" },
     { ad: "İlçeler arası makas", num: true }, { ad: "Gerekçe" }],
    (B.karar || []).map(k => [
      el("strong", { text: k.urun }),
      rozet(k.eylem, EYLEM_ROZET[k.eylem] || "r-notr"),
      el("span", { style: "font-size:12.5px", text: k.olcek }),
      el("span", { class: "mono",
        style: k.oran < 1 ? "color:var(--critical);font-weight:600"
          : "color:var(--good);font-weight:600",
        text: n2(k.oran) }),
      k.en_iyi_ilce + " (" + n1(k.en_iyi_puan) + ")",
      el("span", { class: "mono",
        style: k.yeri_onemli ? "font-weight:600;color:var(--s4)" : null,
        text: n1(k.makas) + (k.yeri_onemli ? " ◆" : "") }),
      el("span", { style: "white-space:normal;display:inline-block;max-width:46ch",
        text: k.gerekce })]));

  // ---------- 02 ürün bazlı dağılımlar
  const kartlar = el("div", { class: "bulgu" }, B.sorular.map(q => {
    const o = q.oran, b = q.baskin;
    const durumRenk = q.karar === "belirsiz" ? "var(--s4)"
      : q.karar === "açık" ? "var(--critical)" : "var(--good)";
    return el("div", { class: "kart", style: "gap:9px" },
      el("div", { class: "ust", style: "justify-content:space-between" },
        el("div", { class: "ust" },
          el("span", { class: "nokta", style: `background:${durumRenk}` }),
          el("h3", { text: q.baslik })),
        rozet(q.karar, q.karar === "belirsiz" ? "r-orta"
          : q.karar === "açık" ? "r-kotu" : "r-iyi")),
      el("p", { class: "mono", style: "font-size:13px",
        text: `arz/ihtiyaç ${n2(o.medyan)}  ·  %90 aralık `
          + `${n2(o.alt90)} – ${n2(o.ust90)}` }),
      el("p", { style: "font-size:12.5px;color:var(--muted)",
        text: `ölçek: ${q.olcek}` }),
      dagilimCizimi(q),
      el("p", { text: q.karar_notu }),
      b ? el("p", { class: "note", html:
        `<strong>Baskın bilinmeyen:</strong> ${b.etiket} — belirsizliğin `
        + `%${n1(b.varyans_payi)}'i. Ölçüm yolu: ${b.yontem} `
        + `(${b.masa_basi ? "masa başı" : "saha/laboratuvar"}).` }) : null,
      el("p", { class: "note", text: q.yorum }));
  }));

  // ---------- 03 kaldıraç
  const K = B.kaldirac;
  const kaldiracTablo = K ? tablo(
    [{ ad: "Kaldıraç" }, { ad: "Tür" }, { ad: "Kazanç (ton KM)", num: true },
     { ad: "Açığın", num: true }, { ad: "Gereken arazi (da)", num: true },
     { ad: "Not" }],
    K.kaldiraclar.map(x => [
      x.ad,
      x.arazi === 0 ? rozet("arazi gerekmez", "r-iyi") : rozet("arazi gerekir", "r-orta"),
      n0(x.kazanc),
      el("span", { class: "mono", style: "font-weight:600", text: "%" + n1(x.acik_payi) }),
      x.arazi ? n0(x.arazi) : "—",
      el("span", { style: "white-space:normal;display:inline-block;max-width:40ch",
        text: x.not_ })])) : null;

  // ---------- 04 ölçüm önceliği
  const oncelikTablo = tablo(
    [{ ad: "Ölçüm" }, { ad: "Tür" }, { ad: "Etkilediği denge" },
     { ad: "Toplam kazanç", num: true }, { ad: "Emek", num: true },
     { ad: "Kim yapar" }],
    B.genel_oncelik.slice(0, 12).map(b => [
      el("div", {}, el("span", { text: b.etiket }),
        el("span", { class: "gerekce", text: b.yontem })),
      b.masa_basi ? rozet("masa başı", "r-iyi") : rozet("saha", "r-orta"),
      b.etkiledigi.map(e => e.soru).join(" · "),
      el("span", { class: "mono", style: "font-weight:600",
        text: n1(b.toplam_kazanc) + " yp" }),
      String(b.emek), b.kim]));

  const belirsizSayisi = (B.belirsiz_karar || []).length;

  return [
    bolum("01", "Her ürün kendi ölçeğinde",
      "Projenin sorusu \u201cne ekilmeli\u201d. Bu soru her ürün için aynı "
      + "ölçekte sorulamaz: ürünün taşınabilirliği, dengenin hangi coğrafyada "
      + "kurulması gerektiğini belirler. Hacimli ve ucuz olan kaba yem il içinde "
      + "dengelenmek zorundadır; ucuz taşınan buğdayın dengesi ulusaldır ve il "
      + "fazlası sorun değildir; pancarın tavanını ne tüketim ne ihracat, "
      + "fabrikanın kapasitesi koyar.",
      eylemTablo,
      el("div", { class: "olcek" },
        el("span", {}, el("i", { style: "background:var(--s4)" }),
          "◆ makas ≥ 12 puan: yer seçimi tek başına kazanç getirir"),
        el("span", {}, el("i", { style: "background:var(--axis)" }),
          "makas küçük: ürün her ilçede benzer yetişir, planlamanın katkısı sınırlı")),
      el("div", { class: "uyari", html:
        "<strong>Kaba yem ürünleri tek denge paylaşır.</strong> Yonca, korunga, "
        + "fiğ ve silajlık mısır aynı oranı (0,48) gösteriyor çünkü hayvan "
        + "hepsini yer — birbirinin yerine geçerler. \u201cYonca yeterli mi\u201d "
        + "sorusu tek başına anlamsızdır; denge grup olarak kurulur. Aralarındaki "
        + "seçim toprak ve iklim uygunluğuna kalır." }),
      el("div", { class: "uyari", html:
        "<strong>Neden \u201cmakas\u201d sütunu var?</strong> Bir ürünün ilçeler "
        + "arasındaki uygunluk farkı küçükse, o ürün her yerde aynı yetişir ve "
        + "nereye ekileceğini planlamanın kazancı yoktur. Fark büyükse ürünün "
        + "doğru bir yeri vardır ve sadece oraya koymak verim kazandırır. "
        + "Planlamanın katkı sağladığı ürünler bunlardır." })),

    bolum("02", "Sayı değil, aralık",
      `Her denge oranı ölçülmemiş varsayımların üstünde duruyor. Her varsayıma `
      + `makul bir aralık verip ${n0(B.ornek_sayisi)} kez yeniden hesapladık. `
      + `Kesikli çizgi yeterlilik eşiği (1,0): dağılım bu çizgiyi kesiyorsa `
      + `açık mı fazla mı olduğunu bugünkü veriyle söyleyemeyiz.`,
      kartlar,
      el("div", { class: "uyari", html:
        belirsizSayisi
          ? `<strong>Altı denge sorusundan ${belirsizSayisi} tanesinin kararı `
            + `bugünkü veriyle verilemiyor: ${B.belirsiz_karar.join(", ")}.</strong> `
            + `Diğerlerinde yön kesin — belirsizlik sadece büyüklükte. `
            + `Bu ayrım önemli: yönü kesin olan bir sorunda ölçüm beklemeye `
            + `gerek yok, harekete geçilebilir.`
          : "<strong>Bütün dengelerde yön kesin.</strong> Belirsizlik "
            + "yalnızca büyüklüktedir." })),

    K ? bolum("03", "Yem açığı nasıl kapanır? Arazi bütçesi",
      `Açık ${n0(K.acik_ton)} ton kuru madde. Bunu yalnızca yem bitkisi ekerek `
      + `kapatmak ${n0(K.sadece_ekimle_dekar)} dekar gerektirir — mevcut yem `
      + `alanının ${TR.format(K.kat)} katı ve buğday alanının %${n1(K.bugday_payi)}'i. `
      + `Arazi sınırlı olduğu için bütün ürünler aynı anda artamaz; seçenekleri `
      + `arazi maliyetiyle birlikte görmek gerekir.`,
      kaldiracTablo,
      el("div", { class: "uyari", html:
        `<strong>${K.sonuc}</strong>` })) : null,

    bolum("04", "Hangi ölçüm yapılmaya değer?",
      `Bütün denge soruları birlikte ele alındığında ölçüm önceliği. Masa başı `
      + `işlerin toplam kazancı ${TR.format(B.masa_basi_kazanc)} yüzde puan, `
      + `saha ve laboratuvar işlerinin ${TR.format(B.saha_kazanc)} yüzde puan.`,
      oncelikTablo,
      el("div", { class: "uyari", html:
        "<strong>Sonuç:</strong> Muş'taki belirsizliğin büyük kısmı saha "
        + "çalışmasıyla değil, <strong>yazışmayla</strong> çözülüyor — fabrika "
        + "kapasitesi, İl Müdürlüğü üretim kaydı, tohumluk oranı. Bunlar bir "
        + "dönemlik öğrenci emeği değil, birkaç resmî yazıdır.<br><br>"
        + "Saha çalışması gerektiren tek büyük kalem <strong>mera verimi</strong>. "
        + "O da tesadüfen en büyük kaldıraç: mera ıslahı, arazi rekabeti olmayan "
        + "tek seçenek. <strong>Ölçüm önceliği ile eylem önceliği aynı yeri "
        + "gösteriyor.</strong>" })),

    bolum("05", "Yöntem", null,
      el("div", { class: "uyari", html:
        "<strong>Örnekleme.</strong> Her bilinmeyene üçgen dağılım verildi: en "
        + "düşük, en olası, en yüksek. Sınırların dışına çıkmaz — mera verimi "
        + "negatif olamaz.<br><br>"
        + "<strong>Duyarlılık.</strong> Birinci mertebe indis (Sobol S1), koşullu "
        + "beklentinin varyansıyla kestirildi: örnekler girdiye göre kutulara "
        + "ayrılır, kutu ortalamalarının varyansı toplam varyansa bölünür.<br><br>"
        + "<strong>Ölçüm kazancı.</strong> Bir girdi tam bilinseydi varyansın S1 "
        + "kadarı kalkardı; standart sapma √(1−S1) katına iner.<br><br>"
        + "<strong>Sınır.</strong> Aralıkların kendisi bir yargıdır; literatürden "
        + "ve bölgesel mertebelerden seçildi. Aralık yanlışsa belirsizlik tahmini "
        + "de yanlış olur. Her aralığın gerekçesi ürün kartlarında yazılı." })),
  ].filter(Boolean);
}
