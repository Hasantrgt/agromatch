// Genel bakış sekmesi: kutular, üç temel bulgu, ilçe haritası.

function sekmeGenel() {
  const k = MUS.kota;
  const toplamIhtiyac = MUS.yem.reduce((a, y) => a + y.ihtiyac_ton, 0);
  const toplamAcik = MUS.yem.reduce((a, y) => a + y.acik_ton, 0);
  const toplamAlan = MUS.denge.reduce((a, d) => a + d.alan_dekar, 0);
  const olc = Object.fromEntries((MUS.olcum || []).map(o => [o.ad, o.deger]));
  const bb = olc.buyukbas ?? MUS.ilceler.reduce((a, i) => a + i.buyukbas, 0);
  const kb = olc.kucukbas ?? MUS.ilceler.reduce((a, i) => a + i.kucukbas, 0);
  const nufus = olc.nufus ?? MUS.ilceler.reduce((a, i) => a + i.nufus, 0);
  const acikPay = toplamAcik / toplamIhtiyac;

  // Yuvarlanmış gösterim: ölçülmemiş sayı virgülüne kadar yazılmaz
  const kaba = v => v >= 100000 ? Math.round(v / 1000) * 1000
    : v >= 1000 ? Math.round(v / 100) * 100 : Math.round(v / 10) * 10;

  const kutu = (etiket, deger, alt, tur, sinif) => el("div",
    { class: "tile" + (sinif ? " " + sinif : "") },
    el("span", { class: "k", text: etiket }),
    el("span", { class: "v mono", text: deger }),
    el("span", { class: "u", text: alt }),
    kaynakEtiket(tur));

  const kutular = el("div", { class: "tiles" },
    kutu("İlçe", "6", n0(nufus) + " kişi", "o"),
    kutu("Ekilen alan", "~" + n0(Math.round(toplamAlan / 1000)),
      "bin dekar · 9 ürün", "v"),
    kutu("Hayvan varlığı", n0(Math.round((bb + kb) / 1000)),
      `bin baş · ${n0(Math.round(bb / 1000))} bin büyükbaş`, "o"),
    kutu("Kaba yem açığı", "~%" + Math.round(acikPay * 100),
      "yaklaşık " + n0(kaba(toplamAcik)) + " ton kuru madde", "v", "vurgu"),
    kutu("Fabrika doluluğu", "~" + yuzde(k.doluluk),
      "~" + n0(kaba(k.bos_alan_dekar)) + " da boşluk", "v"),
    kutu("Yüksek riskli hastalık", String(HASTALIK.istatistik.yuksek_riskli_kayit),
      HASTALIK.istatistik.goruntuden_tespit + " tanesi görüntüden", "v"));

  const olcumSerit = el("div", { class: "uyari", html:
    "<strong>Kutulardaki etiketler ne anlama geliyor?</strong> "
    + "<span class='kaynak k-olcum'>ölçüm</span> resmî kaynakta yayımlanmış sayıdır. "
    + "<span class='kaynak k-varsayim'>varsayım</span> literatür katsayısıyla "
    + "türetilmiştir. <span class='kaynak k-dagitim'>dağıtım</span> il toplamının "
    + "ilçelere tahmini bölünmesidir. "
    + "Türetilmiş sayılar bilerek yuvarlanarak yazılır: ölçülmemiş bir değeri "
    + "virgülüne kadar yazmak, ölçülmüş izlenimi verir." });

  const enKotu = [...MUS.yem].sort((a, b) => a.karsilama - b.karsilama)[0];
  const enIyiPancar = TOPRAK.urun_karsilastirma.find(u => u.urun === "Şeker pancarı");
  const mısır = TOPRAK.urun_karsilastirma.find(u => u.urun === "Silajlık mısır");

  const bulgular = el("div", { class: "bulgu" },
    el("div", { class: "kart" },
      el("div", { class: "ust" },
        el("span", { class: "nokta", style: "background:var(--critical)" }),
        el("h3", { text: "Hayvancılık ili kendi yemini üretemiyor" })),
      el("p", { text: `Muş'ta ${n0(bb + kb)} baş hayvan var ama mera, anız ve yem `
        + `bitkilerinin tamamı ihtiyacın ancak %${Math.round((1 - acikPay) * 100)}'ini `
        + `karşılıyor. Açık ${n0(toplamAcik)} ton kuru madde. En zorlanan ilçe `
        + `${enKotu.ilce} (%${Math.round(enKotu.karsilama * 100)}).` }),
      el("p", { class: "note", text: "Bu açık her yıl il dışından yem alımıyla kapanıyor; "
        + "besi maliyetinin doğrudan içine giriyor." })),
    el("div", { class: "kart" },
      el("div", { class: "ust" },
        el("span", { class: "nokta", style: "background:var(--s4)" }),
        el("h3", { text: "Pancarın tavanı fabrikada" })),
      el("p", { text: `${k.fabrika} kampanyası ${n0(k.kampanya_gun || 95)} gün sürüyor ve `
        + `en çok ${n0(k.tavan_ton)} ton pancar işleyebiliyor. Bugünkü üretim `
        + `${n0(k.uretim_ton)} ton: tavanın %${Math.round(k.doluluk * 100)}'i. `
        + `Yani ${n0(k.bos_alan_dekar)} dekar daha ekilebilir, fazlası sökülüp kalır.` }),
      el("p", { class: "note", text: "Pancarda doğru soru 'ne kadar ekebilirim' değil, "
        + "'fabrika ne kadarını alabilir' sorusudur." })),
    el("div", { class: "kart" },
      el("div", { class: "ust" },
        el("span", { class: "nokta", style: "background:var(--s1)" }),
        el("h3", { text: "İyi toprak her zaman doğru yer değil" })),
      el("p", { text: `Varto ilin en iyi toprağına sahip (volkanik, drenajlı, organik `
        + `maddesi yüksek) ama 1620 metrede. Şeker pancarında ${enIyiPancar.en_iyi} `
        + `${n1(enIyiPancar.ilceler[0].puan)} puanla önde, Varto ${n1(enIyiPancar.ilceler.at(-1).puan)} `
        + `ile sonuncu. Silajlık mısırda Varto ${n1(mısır.ilceler.at(-1).puan)}: `
        + `sıcaklık toplamı olgunlaşmaya yetmiyor.` }),
      el("p", { class: "note", text: "Panel toprakla iklimi geometrik ortalamayla "
        + "birleştirir: biri kötüyse diğeri onu telafi edemez." })));

  return [
    bolum("01", "Muş bir bakışta", null, kutular, olcumSerit),
    bolum("02", "Üç temel bulgu",
      "Paneldeki bütün hesapların işaret ettiği üç sonuç.", bulgular),
    bolum("03", "İlçeler",
      "Daire büyüklüğü nüfusu, renk yem karşılama oranını gösterir.",
      harita(ad => {
        const y = MUS.yem.find(v => v.ilce === ad);
        return { renk: y.karsilama >= 0.65 ? "var(--s3)" : y.karsilama >= 0.55
          ? "var(--warning)" : "var(--critical)",
          metin: "%" + Math.round(y.karsilama * 100) };
      }, ad => MUS.ilceler.find(i => i.ad === ad).rakim + " m", "Muş ilçeleri yem karşılama haritası"),
      el("div", { class: "olcek" },
        el("span", {}, el("i", { style: "background:var(--s3)" }), "yem karşılama ≥ %65"),
        el("span", {}, el("i", { style: "background:var(--warning)" }), "%55–65"),
        el("span", {}, el("i", { style: "background:var(--critical)" }), "< %55"))),
  ];
}
