// Veri kalitesi sekmesi: laboratuvar verisinin adli denetimi.
// Bu sekme veriyi SAVUNMAZ. Kusurlarını sayar ve her biri için ne
// yapıldığını yazar — veriyi veren kurum da ona temkinli yaklaşıyor.

const AGIRLIK_ROZET = {
  "ölçümü etkiler": "r-kotu",
  "sütun kullanılmıyor": "r-orta",
  "yalnızca kayıt": "r-notr",
};
function sekmeKalite() {
  if (!KALITE || !KALITE.var) {
    return [bolum("01", "Veri kalitesi raporu üretilmemiş",
      "Üretmek için: python src/toprak_olcum/kalite.py — ham laboratuvar "
      + "dosyaları data/toprak_analizi/ altında olmalı. Ham kayıtlar "
      + "depoda tutulmaz, bu yüzden klonlanmış bir kopyada bu sekme boş "
      + "kalır.")];
  }

  const o = KALITE.ozet;
  const denetim = KALITE.denetim;
  const yer = denetim.find(d => d.ad === "Yer sütunu");
  const yin = denetim.find(d => d.ad === "Yinelenen satırlar");
  const bir = denetim.find(d => d.ad.startsWith("Fosfor"));

  // --- 01 yargı: önce sonuç, sonra ayrıntı
  const yargiBolum = el("div", {},
    el("div", { class: "kutu" },
      el("strong", { text: "Bu veri kusurludur." }),
      el("p", { text: KALITE.yargi.split("Veriyi veren")[0].trim() })),
    el("div", { class: "tiles" },
      ...[["Denetim", n0(o.denetim_sayisi),
            `${n0(o.kusur_bulunan)} tanesinde kusur bulundu`],
          ["Ölçümü etkileyen", n0(o.olcumu_etkileyen),
            "modele giren bir sayıyı bozabilen kusur"],
          ["Ayıklanan değer", n0(o.ayiklanan_deger),
            "fiziksel olarak imkânsız, modele girmedi"],
          ["Modele giren satır", n0(o.modele_giren_satir),
            `${n0(KALITE.n_satir)} satırın ilçesi belirlenebilen kısmı`]]
        .map(([b, d, a]) => el("div", { class: "tile" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))));

  // --- 02 denetim tablosu
  const tabloBolum = el("div", { class: "kaydir" },
    tablo([{ ad: "denetim" }, { ad: "bulgu", num: true },
           { ad: "oran", num: true }, { ad: "ağırlık" },
           { ad: "ne yapıldı" }],
      denetim.map(d => [
        el("span", {}, el("strong", { text: d.ad }),
          el("div", { style: "font-size:11px;color:var(--muted);"
            + "max-width:330px;white-space:normal", text: d.soru })),
        el("span", { class: "mono", style: "font-weight:600",
          text: `${n0(d.bulgu)} / ${n0(d.toplam)}` }),
        el("span", { class: "mono",
          style: d.agirlik === "ölçümü etkiler" && d.bulgu
            ? "color:var(--critical);font-weight:700" : "color:var(--muted)",
          text: "%" + n1(d.oran) }),
        rozet(d.agirlik, AGIRLIK_ROZET[d.agirlik] || "r-notr"),
        el("span", { style: "font-size:12px;max-width:290px;display:block;"
          + "white-space:normal;line-height:1.45", text: d.ne_yapildi }),
      ])));

  // --- 03 yer sütunu: en ciddi bulgu ve itiraf
  const yerBolum = el("div", {},
    kirilimSeridi(yer.ayrinti.kirilim, KALITE.n_satir),
    kirilimEfsane(yer.ayrinti.kirilim, KALITE.n_satir),
    el("div", { class: "kutu", style: "margin-top:14px" },
      el("strong", { text: "Bu hata bizim hatamızdı." }),
      el("p", { text: "Laboratuvar bölgeye hizmet verdiği için komşu "
        + "illerden de örnek kabul ediyor. İlk ilçe eşleştirmemiz adın "
        + "herhangi bir parçasında Muş ilçesi arıyordu, bu yüzden "
        + "\"Merkez - Bingöl\" kaydı Muş MERKEZ'e yazıldı. Eski kural 130 "
        + "kaydı yanlış yerleştirmişti: 93'ü Muş dışıydı ve Muş "
        + "istatistiğine girmişti, 34'ü ise gerçek Muş kaydıyken asıl "
        + "ilçesinden alınıp Merkez'e yazılmıştı. Düzeltildi; artık yer "
        + "adının yalnızca SON parçası ilçeyi belirliyor ve bir gerileme "
        + "testi bunu koruyor." })),
    el("p", { class: "uyari", text: "Yer sütununun sırası sabit değil: "
      + "baskın kalıp \"köy - ilçe\" ama üç kayıtta ters yazılmış. Köy "
      + "kütüğü olmadan ayırt edilemediği için katı kural seçildi — 93 "
      + "yabancı kayıt girmiyor, karşılığında 3 gerçek Muş kaydı "
      + "düşüyor. Bu üç kayıt yukarıda \"belirsiz sıralama\" olarak "
      + "sayılı; sessizce kaybolmuyor." }),
    el("div", { class: "kaydir" },
      tablo([{ ad: "yıl" }, { ad: "satır", num: true },
             { ad: "yer sütunu dolu", num: true }, { ad: "" }],
        Object.entries(yer.ayrinti.yil).map(([y, v]) => [
          el("strong", { text: y }),
          el("span", { class: "mono", text: n0(v.n) }),
          el("span", { class: "mono",
            style: v.dolu ? "" : "color:var(--critical);font-weight:600",
            text: n0(v.dolu || 0) }),
          v.dolu
            ? el("span", { style: "color:var(--good)",
                text: "ilçe karşılaştırmasına girer" })
            : el("span", { style: "color:var(--critical)",
                text: "yer sütunu tamamen boş — yalnızca il geneli" }),
        ]))),
    el("h3", { class: "cati-baslik",
      text: "Reddedilen kayıtların yer adı neyle bitiyor" }),
    el("p", { class: "note", text: "Çoğu komşu il ya da o illerin bir "
      + "ilçesi. Listedeki birkaç tanesi ise yalnızca köy adı: ilçe eki "
      + "olmadığı için hangi ilçeye ait olduğu bilinemiyor." }),
    el("div", { class: "kaydir" },
      tablo([{ ad: "son parça" }, { ad: "ne olduğu" },
             { ad: "kayıt", num: true }],
        Object.entries(yer.ayrinti.dis_iller).map(([ad, n]) => [
          el("span", { class: "mono", text: ad }),
          KOMSU.has(ad)
            ? rozet("Muş dışı", "r-kotu")
            : rozet("ilçe eki yok", "r-notr"),
          el("span", { class: "mono", text: n0(n) }),
        ]))));

  // --- 04 yinelenme: iddia değil sınama
  const yinBolum = el("div", {},
    el("p", { class: "note", text: "\"176 satır kopyalanmış\" demek "
      + "ölçmeden iddia etmek olurdu: beş değer yuvarlanmış olduğu için "
      + "iki ayrı örneğin tesadüfen aynı takımı vermesi mümkündür. Her "
      + "sütun kendi içinde karıştırılırsa dağılımlar korunur ama satır "
      + "içi bağ kopar; o kurguda çıkan yinelenme sayısı saf şansın "
      + "beklentisidir." }),
    sansCubugu(yin.bulgu, yin.ayrinti.sans_beklentisi_toplam),
    el("p", { style: "font-size:12.5px;margin-top:10px" },
      el("strong", { text: "Sonuç: " }), yin.ayrinti.yorum),
    el("div", { class: "kaydir" },
      tablo([{ ad: "yıl" }, { ad: "satır", num: true },
             { ad: "yinelenen", num: true },
             { ad: "şans beklentisi", num: true }, { ad: "" }],
        Object.entries(yin.ayrinti.yila_gore).map(([y, v]) => [
          el("strong", { text: y }),
          el("span", { class: "mono", text: n0(v.n) }),
          el("span", { class: "mono", style: v.gozlenen
            ? "font-weight:700;color:var(--critical)" : "",
            text: n0(v.gozlenen) }),
          el("span", { class: "mono", style: "color:var(--muted)",
            text: n2(v.sans_beklentisi) }),
          v.gozlenen > v.sans_beklentisi + 3 * Math.max(v.sapma, 0.5)
            ? rozet("şansla açıklanmaz", "r-kotu")
            : rozet("şans olabilir", "r-notr"),
        ]))),
    el("p", { class: "uyari", text: yin.ne_yapildi }));

  // --- 05 birim: neden iki sütun hiç kullanılmıyor
  const birBolum = el("div", {},
    el("div", { class: "tiles" },
      ...[["Beklenen oran", n2(bir.ayrinti.beklenen_oran),
            "1 ppm ≈ 0,26 kg/da (20 cm, 1,3 t/m³)"],
          ["Ölçülen oran", n2(bir.ayrinti.olculen_oran_medyan),
            "aynı ölçümün iki birimi arasındaki medyan oran"],
          ["Kat fark", n1(bir.ayrinti.kat_fark) + "×",
            "bu bir ölçüm farkı değil, birim hatası"],
          ["Sapan satır", "%" + n1(bir.oran),
            `${n0(bir.bulgu)} / ${n0(bir.ayrinti.karsilastirilabilir_satir)} `
            + "karşılaştırılabilir satır"]]
        .map(([b, d, a]) => el("div", { class: "tile vurgu" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))),
    el("div", { class: "kaydir" },
      tablo([{ ad: "sütun" }, { ad: "medyan", num: true }, { ad: "sorun" }],
        Object.entries(bir.ayrinti.sutun_medyanlari).map(([ad, m]) => [
          el("span", { class: "mono", text: ad }),
          el("span", { class: "mono", style: "font-weight:600", text: n2(m) }),
          el("span", { style: "font-size:12px", text:
            ad.includes("ppm")
              ? "yarayışlı fosfor için anlamsız derecede düşük"
              : ad.startsWith("K2O")
                ? "\"kg/da\" etiketli ama değerler ppm'e benziyor"
                : "makul görünen tek sütun" }),
        ]))),
    el("p", { class: "uyari", text: bir.ne_yapildi }));

  return [
    bolum("01", "Yargı: bu veriye neden yine de dayanılabilir",
      "Veriyi bize veren kurum da ona temkinli yaklaşıyor. Güvenilmeyen "
      + "bir veriyle çalışmanın tek dürüst yolu, nerede güvenilmez "
      + "olduğunu ölçmektir. Yedi denetim bunun için var.",
      yargiBolum),
    bolum("02", "Yedi denetim, tek tek",
      "Bir kusurun ağırlığı modele ulaşıp ulaşmadığına göre belirlenir. "
      + "Ölçümü etkileyen kusur ayıklanır; birimi şüpheli sütun modele "
      + "hiç sokulmaz; kalanı kayda geçer.",
      tabloBolum),
    bolum("03", "En ciddi bulgu: örnek gerçekten Muş'tan mı",
      `${n0(KALITE.n_satir)} satırın yalnızca `
      + `${n0(yer.ayrinti.kirilim["Muş ilçesine bağlandı"])}'ü bir Muş `
      + "ilçesine bağlanabiliyor. Geri kalanın nereye gittiği aşağıda.",
      yerBolum),
    bolum("04", "Yinelenen satırlar: şans mı, kopyalama mı",
      "Bu bölüm, projenin kendi iddiasını sınadığı yer.",
      yinBolum),
    bolum("05", "Fosfor ve potasyum neden hiç kullanılmıyor",
      "Bir sütunun dosyada olması kullanılabilir olduğu anlamına "
      + "gelmiyor.",
      birBolum),
  ];
}
