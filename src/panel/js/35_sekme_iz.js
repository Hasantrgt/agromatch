// Hesap izi sekmesi: türeyiş ağaçları.

function izDugumu(d, derinlik) {
  const turRoz = d.tur === "ölçüm" ? rozet("ölçüm", "r-olcum")
    : d.tur === "varsayım" ? rozet("varsayım", "r-varsayim") : null;
  const pay = d.varyans_payi;
  const payEl = (pay != null && pay >= 0.5)
    ? el("span", { class: "payrozet" + (pay < 10 ? " az" : ""),
        title: "Bu bilinmeyen, sonucun belirsizliğinin %" + n1(pay) + "'ini üretiyor",
        text: "varyans %" + n1(pay) })
    : null;

  const satir = el("div", { class: "dugum-sat" },
    el("span", { class: "dugum-ad", text: d.ad }),
    el("span", { class: "dugum-deger", text: TR.format(d.deger) }),
    el("span", { class: "dugum-birim", text: d.birim }),
    turRoz, payEl);

  const detay = [];
  if (d.kaynak) detay.push(el("span", { class: "dugum-kaynak", text: d.kaynak }));
  if (d.aralik && d.aralik[2] > d.aralik[0]) {
    detay.push(el("span", { class: "dugum-kaynak mono",
      text: `aralık ${TR.format(d.aralik[0])} – ${TR.format(d.aralik[2])}` }));
  }
  if (d.gerekce) detay.push(el("span", { class: "dugum-kaynak", text: d.gerekce }));
  if (d.olcum_yolu) {
    // Ölçüm yolu yapılandırılmış: yöntem, miktar, birim ve kimin yapacağı.
    const y = d.olcum_yolu;
    const olcek = y.miktar > 1 ? ` · ${y.miktar} ${y.birim}` : "";
    detay.push(el("span", { class: "dugum-kaynak",
      html: `<strong>Nasıl ölçülür:</strong> ${y.yontem}${olcek}`
        + (y.kim ? ` — ${y.kim}` : "") }));
  }

  if (!d.cocuklar || !d.cocuklar.length) {
    satir.prepend(el("span", { class: "ok-bos" }));
    return el("div", { class: "dugum" }, satir, ...detay);
  }
  const ac = derinlik < 2;
  const det = el("details", ac ? { open: "" } : {},
    el("summary", {}, el("span", { class: "ok", text: "▸" }), satir),
    ...detay,
    el("div", { class: "dal" }, d.cocuklar.map(c => izDugumu(c, derinlik + 1))));
  return el("div", { class: "dugum" }, det);
}

function sekmeIz() {
  if (!IZ || !IZ.sorular || !IZ.sorular.length) return [];
  const kutu = el("div", {});
  const secim = el("div", { class: "ilce-sec" });
  let aktif = IZ.sorular[0].anahtar;

  function ciz() {
    const q = IZ.sorular.find(x => x.anahtar === aktif);
    const olcumYaprak = q.yaprak_sayisi - q.belirsiz_yaprak;

    kutu.replaceChildren(
      el("div", { class: "tiles" },
        el("div", { class: "tile" }, el("span", { class: "k", text: "Arz / ihtiyaç" }),
          el("span", { class: "v mono", text: n2(q.oran.medyan) }),
          el("span", { class: "u",
            text: `%90 aralık ${n2(q.oran.alt90)} – ${n2(q.oran.ust90)}` })),
        el("div", { class: "tile" }, el("span", { class: "k", text: "Hesap düğümü" }),
          el("span", { class: "v mono", text: String(q.dugum_sayisi) }),
          el("span", { class: "u", text: q.derinlik + " kademe derinlik" })),
        el("div", { class: "tile" }, el("span", { class: "k", text: "Ölçüme dayalı girdi" }),
          el("span", { class: "v mono", text: String(olcumYaprak) }),
          el("span", { class: "u", text: "resmî kaynaktan" })),
        el("div", { class: "tile vurgu" },
          el("span", { class: "k", text: "Belirsiz girdi" }),
          el("span", { class: "v mono", text: String(q.belirsiz_yaprak) }),
          el("span", { class: "u", text: "aralıkla modellendi" }))),
      el("p", { class: "note", style: "margin-top:14px",
        text: `Ölçek: ${q.olcek}. Aşağıdaki ağaçlar bu dengenin iki tarafını `
          + `oluşturan büyüklükleri gösteriyor. Her satır bir hesap düğümü; `
          + `üçgene tıklayarak açılır.` }),
      el("h3", { text: "Arz tarafı", style: "margin-top:14px" }),
      el("div", { class: "agac" }, izDugumu(q.agac.arz, 0)),
      el("h3", { text: "İhtiyaç tarafı", style: "margin-top:14px" }),
      el("div", { class: "agac" }, izDugumu(q.agac.ihtiyac, 0)));
  }

  for (const q of IZ.sorular) {
    secim.append(el("button", { type: "button", text: q.baslik,
      "aria-pressed": String(q.anahtar === aktif),
      onclick: () => { aktif = q.anahtar;
        [...secim.children].forEach(c =>
          c.setAttribute("aria-pressed", String(c.textContent === q.baslik
            ? c.textContent === IZ.sorular.find(z => z.anahtar === aktif).baslik
            : false)));
        [...secim.children].forEach(c => c.setAttribute("aria-pressed",
          String(c.textContent === IZ.sorular.find(z => z.anahtar === aktif).baslik)));
        ciz(); } }));
  }
  ciz();

  return [
    bolum("01", "Her sayı kendi türeyişini taşır",
      `Paneldeki hiçbir sayı elle yazılmadı. Her büyüklük bir hesap grafiğinde `
      + `düğüm: değerini, birimini, kaynağını ve hangi başka büyüklüklerden `
      + `türediğini biliyor. Altı denge toplam ${IZ.toplam_dugum} düğümden `
      + `oluşuyor. Künye bu yüzden ayrı tutulan bir belge değil — hesabın `
      + `kendisinden çıkıyor ve formül değişince kendiliğinden değişiyor.`,
      secim, kutu),
    bolum("02", "Bu neden önemli", null,
      el("div", { class: "bulgu" },
        el("div", { class: "kart" },
          el("div", { class: "ust" },
            el("span", { class: "nokta", style: "background:var(--s1)" }),
            el("h3", { text: "Künye eskiyemez" })),
          el("p", { text: "Elle yazılan bir veri künyesi, formül değiştiğinde "
            + "sessizce yanlış hale gelir ve kimse fark etmez. Burada künye "
            + "hesabın kendisinden türetiliyor: formülü değiştirmek, izi de "
            + "değiştirir." })),
        el("div", { class: "kart" },
          el("div", { class: "ust" },
            el("span", { class: "nokta", style: "background:var(--s3)" }),
            el("h3", { text: "Belirsizlik otomatik yayılır" })),
          el("p", { text: "Grafik hangi yaprağın belirsiz olduğunu bildiği için "
            + "Monte Carlo ve duyarlılık hesabı kendiliğinden çıkıyor. Yeni bir "
            + "ürün ya da yeni bir kalem eklemek için ayrıca örnekleme "
            + "fonksiyonu yazmak gerekmiyor." })),
        el("div", { class: "kart" },
          el("div", { class: "ust" },
            el("span", { class: "nokta", style: "background:var(--s4)" }),
            el("h3", { text: "Aynı yaprak bir kez örneklenir" })),
          el("p", { text: "Nüfus hem gıda talebinde hem tohumlukta geçiyor. Her "
            + "geçişte yeniden örneklenseydi aralarındaki bağ kopar ve "
            + "belirsizlik olduğundan büyük çıkardı. Örnekler düğüm kimliğine "
            + "göre önbellekleniyor." })),
        el("div", { class: "kart" },
          el("div", { class: "ust" },
            el("span", { class: "nokta", style: "background:var(--s2)" }),
            el("h3", { text: "Alan bağımsız" })),
          el("p", { text: "Kütüphanenin tarımla ilgisi yok: ölçüm, varsayım ve "
            + "türetilmiş büyüklükler. Aynı yapı bir maliyet hesabına da, bir "
            + "enerji modeline de çalışır." })))),
    bolum("03", "Doğrulama", null,
      el("div", { class: "uyari", html:
        "<strong>Yeni bir soyutlama, eskisiyle aynı sonucu vermek zorundadır.</strong> "
        + "Bu grafik kurulmadan önce altı denge elle yazılmış fonksiyonlarla "
        + "hesaplanıyordu. İkisi birlikte çalıştırılıp karşılaştırılıyor: "
        + "<span class='mono'>python src/mus_iz.py --dogrula</span><br><br>"
        + "Altı dengenin tamamında fark %1'in altında — kalan fark Monte Carlo "
        + "örnekleme gürültüsü. Soyutlamanın doğru olduğunun kanıtı budur; "
        + "aksi halde elimizde yalnızca daha şık görünen, doğruluğu bilinmeyen "
        + "bir kod olurdu." })),
  ];
}
