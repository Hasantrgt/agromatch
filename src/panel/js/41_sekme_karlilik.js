// Karlılık sekmesi: dekar başına net gelir, belirsizliğiyle birlikte.

function karlilikCubuk(s, enGenis) {
  // Güven aralığını yatay bir bant olarak çizer; sıfır çizgisi işaretli.
  const en = 260;
  const olcek = v => Math.round((v / enGenis) * (en / 2) + en / 2);
  const sol = Math.min(olcek(s.net_alt), olcek(s.net_ust));
  const genislik = Math.max(Math.abs(olcek(s.net_ust) - olcek(s.net_alt)), 2);
  return el("div", { style: `position:relative;width:${en}px;height:16px` },
    el("div", { style: `position:absolute;left:${en / 2}px;top:0;width:1px;`
      + "height:16px;background:var(--muted)" }),
    el("div", { style: `position:absolute;left:${sol}px;top:4px;`
      + `width:${genislik}px;height:8px;border-radius:4px;`
      + `background:${s.net_alt > 0 ? "var(--good)" : "var(--warning)"};`
      + "opacity:.5" }),
    el("div", { style: `position:absolute;left:${olcek(s.net_orta)}px;top:1px;`
      + "width:2px;height:14px;background:var(--ink)" }));
}

function sekmeKarlilik() {
  if (!KARLILIK.satirlar || !KARLILIK.satirlar.length) {
    return [bolum("01", "Karlılık verisi üretilmemiş",
      "Üretmek için: python src/piyasa/karlilik.py")];
  }

  const o = KARLILIK.ozet;
  const y = KARLILIK.veri_yasi;
  const p = KARLILIK.parametre;
  const hesapli = KARLILIK.satirlar.filter(s => s.hesaplanabilir);
  const enGenis = Math.max(...hesapli.map(s => Math.abs(s.net_ust)),
                           ...hesapli.map(s => Math.abs(s.net_alt)));

  // --- 01 veri durumu: en üstte, çünkü her şeyi belirliyor
  const durum = el("div", {},
    el("div", { class: "kutu" },
      el("strong", { text: y.bayat
        ? `FİYAT VERİSİ ${n0(y.gun)} GÜN ESKİ.`
        : `Fiyat verisi ${n0(y.gun)} günlük.` }),
      el("p", { text: `Bu tablodaki ${n0(o.dogrulanmis_fiyat)} fiyat ölçümle `
        + `doğrulanmıştır — yani hiçbiri. Hepsi varsayım ve Muş için `
        + `teyit edilmemiştir. Güncellemek için tek dosya var: `
        + `data/piyasa.csv. Her satır kendi kaynağını ve tarihini taşır.` })),
    el("div", { class: "tiles" },
      ...[["Hesaplanan", n0(o.hesaplanan) + " satır",
            `${n0(o.hesaplanamayan)} satır hesaplanamadı`],
          ["Doğrulanmış fiyat", n0(o.dogrulanmis_fiyat) + " / " + n0(KARLILIK.piyasa.length),
            "ölçümle teyit edilen ürün sayısı"],
          ["Sıralanabilen ilçe", n0(o.ayrisan_ilce) + " / " + n0(o.ilce_sayisi),
            "ilk iki ürünün ayrıştığı ilçe"]]
        .map(([b, d, a]) => el("div", { class: "tile vurgu" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))));

  // --- 02 net gelir tablosu
  const tabloEl = el("div", { class: "kaydir" },
    tablo([{ ad: "ilçe" }, { ad: "ürün" }, { ad: "verim", num: true },
           { ad: "net TL/dekar", num: true }, { ad: "%90 aralık" },
           { ad: "zarar olasılığı", num: true }],
      hesapli.sort((a, b) => a.ilce === b.ilce
        ? b.net_orta - a.net_orta : a.ilce.localeCompare(b.ilce, "tr"))
        .map(s => [
          el("span", { style: "font-size:12.5px", text: s.ilce }),
          el("strong", { text: s.urun }),
          el("span", { class: "mono", text: n2(s.verim) }),
          el("span", { class: "mono", style: "font-weight:600",
            text: n0(s.net_orta) }),
          el("span", {},
            karlilikCubuk(s, enGenis),
            el("span", { class: "mono", style: "font-size:11px;color:var(--muted)",
              text: `${n0(s.net_alt)} … ${n0(s.net_ust)}` })),
          el("span", { class: "mono",
            style: `color:${s.zarar_olasiligi > 0.2 ? "var(--critical)"
              : s.zarar_olasiligi > 0.05 ? "var(--warning)" : "var(--good)"}`,
            text: yuzde(s.zarar_olasiligi) }),
        ])));

  // --- 03 sıralanabilirlik: sekmenin asıl söylediği şey
  const ayirtEl = el("div", { class: "kaydir" },
    tablo([{ ad: "ilçe" }, { ad: "en kârlı görünen" }, { ad: "ikinci" },
           { ad: "sıralanabiliyor mu" }],
      KARLILIK.ayirt_edilebilirlik.map(a => [
        el("strong", { text: a.ilce }),
        el("span", {}, a.birinci, el("span", { class: "mono",
          style: "color:var(--muted)", text: ` ${n0(a.birinci_net)}` })),
        el("span", {}, a.ikinci, el("span", { class: "mono",
          style: "color:var(--muted)", text: ` ${n0(a.ikinci_net)}` })),
        a.ayrisiyor
          ? el("span", { style: "color:var(--good);font-weight:600", text: "evet" })
          : el("span", { style: "color:var(--critical);font-weight:600",
              text: "HAYIR — aralıklar örtüşüyor" }),
      ])));

  // --- 04 hesaplanamayanlar ve eksik veri
  const eksik = KARLILIK.satirlar.filter(s => !s.hesaplanabilir);
  const eksikUrun = [...new Set(eksik.map(s => s.urun))];
  const kaynakEl = el("div", { class: "kaydir" },
    tablo([{ ad: "ürün" }, { ad: "fiyat TL/ton", num: true },
           { ad: "maliyet TL/dekar", num: true }, { ad: "destek", num: true },
           { ad: "tür" }, { ad: "nereden gelmeli" }],
      KARLILIK.piyasa.map(k => [
        el("strong", { text: k.urun }),
        el("span", { class: "mono", text: k.fiyat ? n0(k.fiyat) : "—" }),
        el("span", { class: "mono", text: k.maliyet ? n0(k.maliyet) : "—" }),
        el("span", { class: "mono", text: k.destek ? n0(k.destek) : "—" }),
        rozet(k.tur, k.tur === "ölçüm" ? "r-olcum" : "r-varsayim"),
        el("span", { style: "font-size:12.5px", text: k.kaynak }),
      ])));

  return [
    bolum("01", "Veri durumu: her şey buna bağlı",
      "Karlılık hesabının tamamı fiyat verisinin doğruluğuna bağlıdır. "
      + "Bu yüzden veri durumu en üstte duruyor, sonuçların altında değil.",
      durum),
    bolum("02", "Dekar başına net gelir: tek sayı değil, aralık",
      `net = verim × fiyat − maliyet + destek. Üç girdi de oynak olduğu için `
      + `tek sayı vermiyoruz: ${n0(p.cekilis)} çekilişlik Monte Carlo ile `
      + `dağılım üretiliyor (fiyat ±%${n0(p.fiyat_oynaklik * 100)}, verim `
      + `±%${n0(p.verim_oynaklik * 100)}, maliyet ±%${n0(p.maliyet_oynaklik * 100)} — `
      + "bu paylar da varsayımdır). Çubuk %90 aralığı, dikey çizgi ortancayı, "
      + "ince çizgi sıfırı gösterir.",
      tabloEl),
    bolum("03", "Asıl soru: ürünleri sıralayabiliyor muyuz?",
      "Bir ürünün ortanca geliri diğerinden yüksek görünebilir ama güven "
      + "aralıkları örtüşüyorsa \"bu daha kârlı\" denemez. Panelin bu "
      + "bölümde yaptığı şey, kârlılık sıralaması vermek değil, sıralamanın "
      + "mümkün olup olmadığını söylemek.",
      ayirtEl,
      el("p", { class: "note", text: o.ayrisan_ilce === 0
        ? "Hiçbir ilçede sıralama yapılamıyor. Bu bir başarısızlık değil "
          + "bulgudur: varsaydığımız belirsizlikle bu soru cevaplanamıyor. "
          + "Cevaplanması için gereken şey daha iyi model değil, GERÇEK "
          + "FİYAT VERİSİ ve o fiyatın gerçek oynaklığı."
        : `${n0(o.ayrisan_ilce)} ilçede sıralama yapılabiliyor.` })),
    bolum("04", "Fiyat tablosu ve eksikler",
      `${n0(eksikUrun.length)} ürün hesaplanamıyor: `
      + eksikUrun.join(", ") + ". Yem bitkileri Muş'ta satılmıyor, hayvana "
      + "veriliyor; karlılıkları satış fiyatıyla değil İKAME DEĞERİYLE "
      + "hesaplanır — o yemi satın alsaydınız ne öderdiniz. O veri yok. "
      + "Uydurma bir fiyat koymak bu ürünleri kârsız gösterip yanlış karar "
      + "ürettirirdi.",
      kaynakEl),
  ];
}
