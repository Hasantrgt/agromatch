// Toprak ve iklim sekmesi: ilçe profili, ürün uygunluğu.

function sekmeToprak() {
  const kutu = el("div", {});
  const secim = el("div", { class: "ilce-sec" });
  let aktif = TOPRAK.ilceler[0].ilce;

  function ciz() {
    const r = TOPRAK.ilceler.find(i => i.ilce === aktif);
    const t = r.toprak, ik = r.iklim;

    const alanlar = [
      ["pH", t.ph, ""], ["Organik madde", t.om, "%"], ["Kireç", t.kirec, "%"],
      ["Tuzluluk", t.ec, "dS/m"], ["Derinlik", t.derinlik, "cm"],
      ["Rakım", ik.rakim, "m"], ["Donsuz dönem", ik.donsuz_gun, "gün"],
      ["Yağış", ik.yagis, "mm"],
    ];
    const kutular = el("div", { class: "tiles" },
      alanlar.map(([ad, v, br]) => el("div", { class: "tile" },
        el("span", { class: "k", text: ad }),
        el("span", { class: "v mono", text: typeof v === "number" ? n1(v) : v }),
        el("span", { class: "u", text: br }))),
      el("div", { class: "tile" }, el("span", { class: "k", text: "Bünye" }),
        el("span", { class: "v mono", style: "font-size:17px", text: r.bunye }),
        el("span", { class: "u", text: "drenaj: " + t.drenaj })),
      el("div", { class: "tile " + (r.saglik.harf === "A" ? "iyi" : "") },
        el("span", { class: "k", text: "Toprak sağlığı" }),
        el("span", { class: "v mono", text: r.saglik.harf + " · " + r.saglik.puan }),
        el("span", { class: "u", text: "zayıf halka: " + r.saglik.zayif_halka })));

    const uygunluk = tablo(
      [{ ad: "Ürün" }, { ad: "Toprak", num: true }, { ad: "İklim", num: true },
       { ad: "Birleşik", num: true }, { ad: "" }, { ad: "Darboğaz" },
       { ad: "Kısıtlayıcı etken" }, { ad: "Ekili" }],
      r.urunler.map(u => [
        u.urun, n1(u.puan), n1(u.iklim.puan),
        el("strong", { class: "mono", text: n1(u.birlesik) }),
        cubuk(u.birlesik, 100, puanRenk(u.birlesik)),
        u.darbogaz === "iklim" ? rozet("iklim", "r-kotu")
          : u.darbogaz === "toprak" ? rozet("toprak", "r-orta") : rozet("dengeli", "r-notr"),
        u.iklim.kisit !== "-" ? u.iklim.kisit : (u.tavanlandi ? u.tavan_sebebi : u.kisitlayici),
        u.ekili ? rozet(n0(u.alan) + " da", "r-iyi") : rozet("ekilmiyor", "r-notr")]));

    const sicakliklar = ik.aylik;
    const maksS = Math.max(...sicakliklar), minS = Math.min(...sicakliklar);
    const serit = el("div", { class: "takvim" },
      sicakliklar.map((s, i) => el("div", { class: "ay" },
        el("span", { class: "ad", text: ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"][i] }),
        el("span", { class: "sic", text: n1(s) + "°" }),
        el("div", { class: "h", style:
          `background:${s < 0 ? "var(--s1)" : s < 10 ? "var(--s3)" : s < 20 ? "var(--s4)" : "var(--s2)"};`
          + `height:${6 + (s - minS) / ((maksS - minS) || 1) * 16}px` }))));

    kutu.replaceChildren(
      el("p", { class: "note", text: r.not_ }),
      kutular,
      el("h3", { text: "Aylık ortalama sıcaklık", style: "margin-top:16px" }),
      serit,
      el("h3", { text: "Ürün uygunluğu", style: "margin-top:16px" }),
      el("p", { class: "note", text: "Birleşik puan, toprak ve iklim puanının geometrik "
        + "ortalamasıdır. Darboğaz sütunu hangisinin sınırladığını söyler: toprağı "
        + "iyileştirebilirsin, iklimi iyileştiremezsin." }),
      uygunluk);
  }

  for (const i of TOPRAK.ilceler) {
    secim.append(el("button", { type: "button", text: i.ilce,
      "aria-pressed": String(i.ilce === aktif),
      onclick: () => { aktif = i.ilce;
        [...secim.children].forEach(c => c.setAttribute("aria-pressed", String(c.textContent === aktif)));
        ciz(); } }));
  }
  ciz();

  const karsilastirma = tablo(
    [{ ad: "Ürün" }, ...TOPRAK.ilceler.map(i => ({ ad: i.ilce, num: true })),
     { ad: "En iyi" }, { ad: "Makas", num: true }],
    TOPRAK.urun_karsilastirma.map(u => {
      const sira = Object.fromEntries(u.ilceler.map(d => [d.ilce, d.puan]));
      return [u.urun,
        ...TOPRAK.ilceler.map(i => el("span", { class: "mono",
          style: `color:${puanRenk(sira[i.ilce])};font-weight:600`, text: n1(sira[i.ilce]) })),
        u.en_iyi, n1(u.makas)];
    }));

  return [
    bolum("01", "İlçe profili",
      "Her ilçenin toprağı, iklimi ve dokuz ürünün buradaki uygunluğu.",
      secim, kutu),
    bolum("02", "Aynı ürün hangi ilçede daha rahat yetişir",
      "Birleşik uygunluk puanları. Makas sütunu en iyi ve en zor ilçe arasındaki farktır: "
      + "makas büyükse ürünün yerini seçmek önemlidir.",
      karsilastirma),
    bolum("03", "Yöntem notu", null,
      el("div", { class: "uyari", html:
        "<strong>Neden geometrik ortalama?</strong> Toprağı 98, iklimi 46 olan bir ilçe "
        + "aritmetik ortalamada 72 alır ve 'uygun' görünür. Geometrik ortalamada 67'ye "
        + "düşer, çünkü iki koşuldan biri diğerinin yerini tutmaz.<br><br>"
        + "<strong>Neden tavan var?</strong> Drenaj, tuzluluk ve toprak derinliği telafi "
        + "edilemeyen özelliklerdir (Liebig'in minimum yasası). Kök 120 cm'e inmesi "
        + "gereken bir ürün 65 cm'lik toprakta, diğer bütün özellikler mükemmel olsa bile "
        + "sınırlıdır. Bu yüzden bu üçünün en düşüğü toplam puana bir tavan koyar." })),
  ];
}
