// Hastalık sekmesi: takvim, risk tablosu, Cercospora görüntü işleme.

function sekmeHastalik() {
  const t = HASTALIK.takvim;
  const takvim = el("div", { class: "takvim" }, t.map(a => el("div", { class: "ay" },
    el("span", { class: "ad", text: a.ad }),
    el("span", { class: "sic", text: n1(a.sicaklik) + "°" }),
    el("div", { class: "yuva" }, a.hastaliklar.slice(0, 6).map(h =>
      el("div", { class: "h", style: `background:${riskRenk(h.risk)}`,
        title: `${h.ad} · ${h.urun} · risk ${h.risk}` }))))));

  const ozetTablo = tablo(
    [{ ad: "Hastalık" }, { ad: "Ürün" }, { ad: "Patojen" }, { ad: "Tip" },
     { ad: "Ort. risk", num: true }, { ad: "" }, { ad: "Riskli alan (da)", num: true },
     { ad: "Kritik aylar" }, { ad: "Görüntüden" }],
    HASTALIK.ozet.map(o => [
      o.hastalik, o.urun, el("span", { style: "font-style:italic", text: o.patojen }), o.tip,
      n0(o.ortalama_risk), cubuk(o.ortalama_risk, 100, riskRenk(o.ortalama_risk)),
      n0(o.riskli_alan),
      o.kritik_aylar.map(a => ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"][a - 1]).join(" "),
      o.goruntuden ? rozet("evet", "r-iyi") : rozet("hayır", "r-notr")]));

  const ilceTablo = tablo(
    [{ ad: "İlçe" }, { ad: "Hastalık kaydı", num: true }, { ad: "Yüksek riskli", num: true },
     { ad: "Ort. risk", num: true }, { ad: "En riskli üçü" }],
    HASTALIK.ilce_ozet.map(i => [
      i.ilce, n0(i.hastalik_sayisi), n0(i.yuksek_riskli), n0(i.ortalama_risk),
      i.en_riskli.map(r => `${r.ad} (${r.risk})`).join(" · ")]));

  // Cercospora görüntü işleme
  const c = CERCO;
  const parcalar = [];
  if (c && c.asamalar && c.asamalar.length) {
    parcalar.push(
      el("div", { class: "asama" }, c.asamalar.map((a, i) => el("figure", {},
        el("img", { src: a.gorsel, alt: a.ad, loading: "lazy" }),
        el("figcaption", {},
          el("span", { class: "no mono", text: String(a.no ?? i + 1).padStart(2, "0") + " · " }),
          el("strong", { text: a.ad }),
          a.aciklama ? el("span", { text: " — " + a.aciklama }) : null)))));
    if (c.dogrulama) {
      const d = c.dogrulama;
      parcalar.push(el("div", { class: "tiles" },
        el("div", { class: "tile iyi" }, el("span", { class: "k", text: "Kesinlik" }),
          el("span", { class: "v mono", text: n1(d.kesinlik * 100) + "%" }),
          el("span", { class: "u", text: "bulunan lekelerin doğruluğu" })),
        el("div", { class: "tile" }, el("span", { class: "k", text: "Duyarlılık" }),
          el("span", { class: "v mono", text: n1(d.duyarlilik * 100) + "%" }),
          el("span", { class: "u", text: "gerçek lekelerin yakalanma oranı" })),
        el("div", { class: "tile" }, el("span", { class: "k", text: "F1" }),
          el("span", { class: "v mono", text: n1(d.f1 * 100) + "%" }),
          el("span", { class: "u", text: "dengeli başarı ölçüsü" })),
        el("div", { class: "tile" }, el("span", { class: "k", text: "Sayım sapması" }),
          el("span", { class: "v mono", text: n1(d.ortalama_mutlak_sapma) }),
          el("span", { class: "u", text: "leke / yaprak" }))));
    }
  }

  return [
    bolum("01", "Hastalık takvimi",
      "Her sütun bir ay; çubuklar o ay penceresi açık olan hastalıklar. "
      + "Renk riski gösterir. Sıcaklık, ilçe ortalamasıdır.",
      takvim,
      el("div", { class: "olcek" },
        el("span", {}, el("i", { style: "background:var(--critical)" }), "yüksek risk (≥60)"),
        el("span", {}, el("i", { style: "background:var(--warning)" }), "orta (35–59)"),
        el("span", {}, el("i", { style: "background:var(--s3)" }), "düşük (<35)"))),
    bolum("02", "Muş'ta ekonomik önemi olan hastalıklar",
      `${HASTALIK.istatistik.hastalik_sayisi} hastalık; `
      + `${HASTALIK.istatistik.goruntuden_tespit} tanesi yaprak görüntüsünden tespit `
      + `edilebilir. Risk = sıcaklık uygunluğu × nem × ekim yoğunluğu.`,
      ozetTablo,
      el("div", { class: "uyari", html: "<strong>Bu panel ilaçlama kararı vermez.</strong> "
        + "Öncelik sırası üretir: hangi hastalığa önce bakılacağını, hangi ayda tarlaya "
        + "çıkılacağını söyler. İlaçlama kararı tahmin-uyarı istasyonu ölçümü ve saha "
        + "gözlemiyle verilir." })),
    bolum("03", "İlçe karşılaştırması", null, ilceTablo),
    parcalar.length ? bolum("04", "Görüntü işleme: Cercospora yaprak lekesi",
      "Şeker pancarının Muş'taki en önemli yaprak hastalığı. Klasik görüntü işleme "
      + "hattı: yaprağı arka plandan ayır, yeşillik kanalını çıkar, eşikle, lekeleri "
      + "bağlı bileşen olarak say, daireselliğe göre ele. Aşağıdaki başarı ölçütleri "
      + "sentetik görüntülerde ölçülmüştür — gerçek tarla fotoğraflarıyla yeniden "
      + "ölçülecektir.",
      ...parcalar) : null,
  ].filter(Boolean);
}
