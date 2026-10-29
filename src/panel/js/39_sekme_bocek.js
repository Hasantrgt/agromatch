// Böcek & ilaç sekmesi — projenin ÜÇÜNCÜ kısmı.
// Tarla zararlıları, faydalılar, ilaç gruplarının pestisit yükü,
// kalıntısız yol ve ikinci kısma giden köprüler.

const BOCEK_RENK = { agir: "#c0392b", orta: "#eb6834", hafif: "#2a78d6",
                     temiz: "#2f7d4f" };

// Önem 3 = kırmızı, 2 = turuncu, 1 = mavi
function onemRenk(n) {
  return n >= 3 ? BOCEK_RENK.agir : n === 2 ? BOCEK_RENK.orta : BOCEK_RENK.hafif;
}

// Üç eksenli pestisit yükünü tek bir satırda üç küçük çubukla gösterir.
// Tek puana indirmiyoruz; hangisinin ağır bastığı üreticiye göre değişir.
function yukCubugu(deger, enCok, renk, baslik) {
  return el("div", { style: "display:flex;align-items:center;gap:6px",
    title: baslik },
    el("div", { style: "width:40px;height:8px;background:var(--cizgi);"
      + "border-radius:3px;overflow:hidden" },
      el("div", { style: `width:${Math.round(deger / enCok * 100)}%;`
        + `height:100%;background:${renk}` })),
    el("span", { class: "mono", style: "font-size:11px;color:var(--muted)",
      text: baslik }));
}

function sekmeBocek() {
  if (!BOCEK.zararlilar || !BOCEK.zararlilar.length) {
    return [bolum("01", "Böcek verisi üretilmemiş",
      "Üretmek için: python src/bocek/bocek_panel_veri.py")];
  }

  const o = BOCEK.ozet;
  const bos = BOCEK.bosluklar;
  const kop = BOCEK.koprular;

  // --- 01 tarla zararlıları -----------------------------------------
  const zararliTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "zararlı" }, { ad: "ürün" }, { ad: "ne yapıyor" },
           { ad: "ekonomik eşik" }, { ad: "doğal düşman", num: true }],
      BOCEK.zararlilar.map(z => [
        el("span", {},
          el("strong", { style: `color:${onemRenk(z.onem)}`, text: z.ad }),
          el("div", { style: "font-size:11.5px;color:var(--muted);font-style:italic",
            text: z.latince }),
          z.depoda_da ? rozet("ambarda da", "r-dagitim") : null,
          z.vektor.length ? rozet("virüs taşır", "r-varsayim") : null),
        el("span", { style: "font-size:12.5px", text: z.urunler.join(", ") }),
        el("span", {},
          el("div", { style: "font-size:12.5px",
            text: z.zarar_sekli.replace(/_/g, " ") }),
          el("div", { style: "font-size:11.5px;color:var(--muted)",
            text: z.hedef_organ })),
        z.esik
          ? el("span", { style: "font-size:12.5px", text: z.esik })
          : el("span", { style: "color:var(--muted)", text: "— yazılmadı" }),
        el("span", { class: "mono", style: z.dusman.length ? "" : "color:var(--muted)",
          text: z.dusman.length ? String(z.dusman.length) : "—" }),
      ])));

  // ay × zararlı ızgarası
  const enYogun = Math.max(...BOCEK.ay_yogunlugu);
  const takvimTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "zararlı" }, ...BOCEK.aylar.map(a => ({ ad: a, num: true }))],
      [...BOCEK.takvim.map(t => [
        el("span", {}, el("strong", { text: t.ad })),
        ...t.aylar.map(v => el("span", {
          style: v ? `display:inline-block;width:100%;height:14px;`
            + `background:${onemRenk(t.onem)};opacity:.85;border-radius:3px` : "",
          text: v ? "" : "" })),
      ]),
      [el("strong", { text: "ay yükü" }),
        ...BOCEK.ay_yogunlugu.map(v => el("span", {
          class: "mono",
          style: `font-weight:600;color:${v === enYogun ? BOCEK_RENK.agir : "var(--muted)"}`,
          text: v ? String(v) : "—" }))]]));

  // --- 02 pestisit yükü ---------------------------------------------
  const enCokVurulan = Math.max(...BOCEK.gruplar.map(g => g.canliya_zarar));
  const enUzunBekleme = Math.max(...BOCEK.gruplar.map(g => g.kalinti_gun[1]));
  const dirence = { "yüksek": 3, "orta": 2, "düşük": 1, "yok": 0 };

  const grupTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "etki grubu" }, { ad: "IRAC" }, { ad: "nasıl etki eder" },
           { ad: "faydalıya zarar" }, { ad: "bekleme" }, { ad: "direnç" }],
      BOCEK.gruplar.map(g => [
        el("span", {},
          el("strong", { text: g.ad }),
          g.kimyasal ? null : rozet("kalıntısız", "r-olcum"),
          g.genis_etkili ? rozet("geniş etkili", "r-dagitim") : null),
        el("span", { class: "mono", style: "font-size:12px", text: g.irac }),
        el("span", { style: "font-size:12.5px", text: g.etki_sekli }),
        yukCubugu(g.canliya_zarar, enCokVurulan,
          g.canliya_zarar ? BOCEK_RENK.agir : BOCEK_RENK.temiz,
          g.canliya_zarar ? `${g.canliya_zarar} tür` : "yok"),
        yukCubugu(g.kalinti_gun[1], enUzunBekleme,
          g.kalinti_gun[1] ? BOCEK_RENK.orta : BOCEK_RENK.temiz,
          g.kalinti_gun[1] ? `${g.kalinti_gun[0]}–${g.kalinti_gun[1]} gün` : "yok"),
        yukCubugu(dirence[g.direnc_riski], 3,
          dirence[g.direnc_riski] ? BOCEK_RENK.agir : BOCEK_RENK.temiz,
          g.direnc_riski),
      ])));

  const vurulanKart = el("div", { class: "bulgu" },
    BOCEK.gruplar.filter(g => g.vurulan.length).map(g => el("div", { class: "kart" },
      el("div", { class: "ust", style: "justify-content:space-between" },
        el("h3", { text: g.ad }),
        rozet(g.vurulan.length + " faydalı", "r-dagitim")),
      el("p", { style: "font-size:12.5px", text: "Birlikte vurulanlar: "
        + g.vurulan.join(", ") }),
      el("p", { style: "font-size:12.5px;color:var(--muted)", text: g.not_ }))));

  // --- 03 faydalılar -------------------------------------------------
  const faydaliKart = el("div", { class: "bulgu" },
    BOCEK.faydalilar.map(f => el("div", { class: "kart" },
      el("div", { class: "ust", style: "justify-content:space-between" },
        el("h3", { text: f.ad }),
        rozet(f.rol, f.rol === "tozlayici" ? "r-olcum" : "r-varsayim")),
      el("p", { style: "font-size:11.5px;color:var(--muted);font-style:italic",
        text: f.latince }),
      el("p", { text: f.ne_yapar }),
      f.hedef.length
        ? el("p", { class: "kazanc", text: "Baskıladığı: " + f.hedef.join(", ") })
        : null,
      el("p", { style: "font-size:12.5px;color:var(--critical)",
        text: "Hassas olduğu gruplar: " + f.hassasiyet.join(", ") }),
      el("p", { style: "font-size:12.5px;color:var(--muted)",
        text: "Korumak için: " + f.korumak_icin }))));

  // --- 04 kalıntısız yol ---------------------------------------------
  const grupAdi = k => (BOCEK.gruplar.find(g => g.grup === k) || {}).ad || k;
  const yolVar = BOCEK.zararlilar.filter(z => z.kalintisiz.length);
  const yolYok = BOCEK.zararlilar.filter(z => !z.kalintisiz.length);

  const yolTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "zararlı" }, { ad: "kalıntı bırakmayan seçenek" }],
      [...yolVar.map(z => [
        el("strong", { text: z.ad }),
        el("span", { style: `color:${BOCEK_RENK.temiz};font-weight:600`,
          text: z.kalintisiz.map(grupAdi).join(", ") })]),
       ...yolYok.map(z => [
        el("strong", { style: `color:${BOCEK_RENK.agir}`, text: z.ad }),
        el("span", { style: "color:var(--critical)",
          text: "yok — yalnızca kimyasal seçenek var" })])]));

  // --- 05 köprüler ----------------------------------------------------
  const koprArea = el("div", {},
    el("h3", { style: "font-size:14px;margin-bottom:6px",
      text: "Böcekle taşınan hastalıklar (2. kısımdan gelir)" }),
    tablo([{ ad: "hastalık" }, { ad: "ürün" }, { ad: "taşıyan böcek" }],
      kop.vektor_hastalik.map(v => [
        el("strong", { text: v.hastalik }),
        v.urun,
        el("span", { style: `color:${BOCEK_RENK.orta};font-weight:600`,
          text: v.vektor.join(", ") || "— vektör yazılmadı" })])),
    el("h3", { style: "font-size:14px;margin:16px 0 6px",
      text: "Hem tarlada hem ambarda olanlar (Depo sekmesine bağlanır)" }),
    el("div", { class: "bulgu" }, kop.depo_koprusu.map(z => el("div", { class: "kart" },
      el("div", { class: "ust" }, el("h3", { text: z.ad })),
      el("p", { text: z.belirti }),
      el("p", { style: "font-size:12.5px;color:var(--muted)", text: z.not_ })))),
    kop.katalogda_olmayan.length
      ? el("p", { class: "uyari", text: "Hastalık kataloğunda bulunmayan ama "
        + "bir zararlının taşıdığı: " + kop.katalogda_olmayan.join(", ")
        + " — eklenmesi gerekiyor." })
      : null);

  // --- 06 eksikler ----------------------------------------------------
  const eksikBolum = el("div", {},
    el("div", { class: "tiles" },
      ...[["Eşiği yazılmamış", n0(bos.esiksiz.length) + " zararlı",
            "ne zaman ilaçlanacağı belirsiz"],
          ["Kalıntısız yolu yok", n0(bos.kalintisiz_yolu_yok.length) + " zararlı",
            "yalnızca kimyasal seçenek"],
          ["Doğrulanmamış", n0(bos.dogrulanmamis_kayit) + " kayıt",
            "hepsi literatür, ZMTT teyidi bekliyor"]]
        .map(([b, d, a]) => el("div", { class: "tile vurgu" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))),
    el("p", { class: "note", text: "Ekonomik zarar eşiği yazılmamış olanlar: "
      + bos.esiksiz.join(" · ") }),
    el("p", { class: "note", text: "Doğal düşmanı yazılmamış olanlar: "
      + bos.dogal_dusmani_yazilmamis.join(" · ") }));

  return [
    bolum("01", "Tarla zararlıları: böceğin kendi verdiği zarar",
      `Muş'un dokuz ürününde ekonomik önemi olan ${n0(o.zararli)} tür. `
      + "Bunlar hastalık değildir — böcek bitkiyi doğrudan yer, emer ya da "
      + "deler. Hastalık kataloğundaki 57 kaydın yalnızca 3'ü böcekle "
      + "taşınırken, süne tek başına buğdayda hastalıkların tamamından "
      + "fazla kaybettirebilir. Üçüncü kısmın gövdesi bu yüzden burasıdır.",
      zararliTablo,
      el("h3", { style: "font-size:14px;margin:18px 0 6px",
        text: "Hangi ay hangi zararlı: tarlaya ne zaman bakılacak" }),
      takvimTablo),
    bolum("02", "Pestisit yükü: bir ilaç grubu başka neyi öldürüyor",
      "Bu tablo ÜRÜN ADI VE DOZ VERMEZ — reçete yazma yetkisi olmayan bir "
      + "yazılım ilaç tavsiye edemez, ruhsatlı ürün listesi de Bakanlık'ın "
      + "BKÜ kayıtlarından gelir. Burada tutulan şey etki mekanizması "
      + "grubudur. Yük tek puana indirilmiyor: canlıya zarar, bekleme "
      + "süresi ve direnç riski ayrı duruyor, çünkü hangisinin ağır bastığı "
      + "üreticinin durumuna göre değişir.",
      grupTablo, vurulanKart),
    bolum("03", "Faydalılar: yolu asıl yürüyen canlılar",
      `${n0(o.faydali)} tür. Bir tarlada böcek demek zararlı demek değildir; `
      + "tozlaşmayı yapan da, zararlıyı baskılayan da böcektir. Süneye karşı "
      + "atılan geniş etkili bir ilaç Trissolcus'u da öldürürse ertesi yıl "
      + "süne daha çok olur — pestisitten arındırılmış yolun somut karşılığı "
      + "bu canlıları ayakta tutmaktır.",
      faydaliKart),
    bolum("04", "Kalıntısız yol: hangisinde var, hangisinde yok",
      `${n0(yolVar.length)} zararlı için kalıntı bırakmayan en az bir seçenek `
      + `var; ${n0(yolYok.length)} tanesi için YOK. Bu bir eksiklik değil, `
      + "bulgudur: o yedi tür için bugün elimizde yalnızca kimyasal seçenek "
      + "bulunuyor ve projenin dürüst cevabı bunu yazmaktır.",
      yolTablo),
    bolum("05", "İkinci kısımla birleştiği yerler",
      "Üçüncü kısım ikinci kısımdan kopuk değil. Üç hastalığı böcek taşıyor; "
      + "iki zararlı tarlada başlayıp ambarda devam ediyor. Bu satırlar "
      + "iki kısmın aynı sorunu iki ucundan tuttuğu yerler.",
      koprArea),
    bolum("06", "Bu kısımda neyin eksik olduğu",
      "Katalogdaki boşluklar gizlenmiyor, sayılıyor. Danışman hocadan "
      + "istenecek şeylerin listesi burası.",
      eksikBolum),
  ];
}
