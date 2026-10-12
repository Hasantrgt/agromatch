// Veri künyesi sekmesi: hangi sayı ölçüm, hangisi varsayım.

function sekmeKunye() {
  const guvenRozet = g => g === "yüksek" ? rozet("yüksek", "r-iyi")
    : g === "orta" ? rozet("orta", "r-orta") : rozet("düşük", "r-kotu");

  const sayim = { "ölçüm": 0, "varsayım": 0, "dağıtım": 0 };
  for (const k of MUS.kunye) sayim[k.tur] = (sayim[k.tur] || 0) + 1;

  const kunyeTablo = tablo(
    [{ ad: "Alan" }, { ad: "Tür" }, { ad: "Kaynak" }, { ad: "Yıl" },
     { ad: "Güven" }, { ad: "Not" }],
    MUS.kunye.map(k => [k.alan, turRozet(k.tur), k.kaynak, k.yil, guvenRozet(k.guven),
      el("span", { style: "white-space:normal;display:inline-block;max-width:46ch",
        text: k.not_ })]));

  const olcumTablo = tablo(
    [{ ad: "Gösterge" }, { ad: "Değer", num: true }, { ad: "Birim" }, { ad: "Kaynak" }],
    (MUS.olcum || []).map(o => [
      ({ nufus: "İl nüfusu", toplam_tarim_da: "Toplam tarım alanı",
         mera_da: "Çayır-mera alanı", nadas_da: "Nadas alanı",
         buyukbas: "Büyükbaş hayvan", kucukbas: "Küçükbaş hayvan" })[o.ad] || o.ad,
      el("strong", { class: "mono", text: n0(o.deger) }), o.birim, o.kaynak]));

  const uretimTablo = tablo(
    [{ ad: "Ürün" }, { ad: "Üretim (ton)", num: true }, { ad: "Kaynak" },
     { ad: "Varsayılan verim (t/da)", num: true }, { ad: "Türetilen alan (da)", num: true }],
    (MUS.uretim || []).map(u => [
      u.urun, el("strong", { class: "mono", text: n0(u.ton) }),
      u.kaynak.startsWith("TAHMİN") ? rozet("tahmin", "r-kotu")
        : el("span", { style: "font-size:12.5px", text: u.kaynak }),
      TR.format(u.verim), n0(u.alan)]));

  const celiskiler = [
    ["Buğday üretimi", "Tablo 3: 368.297 ton · Bölüm 2.2: \u201c115 bin ha'da ~244 bin ton\u201d",
     "Tablo 3 esas alındı. İlginç olan şu: 368.297 tonu 115 bin hektara böldüğünde "
     + "0,32 ton/dekar çıkıyor — yani iki ifade, verim 0,32 kabul edilirse uyuşuyor. "
     + "Panelde buğday verimi bu yüzden 0,32 alındı."],
    ["Yem bitkisi üretimi", "Bölüm 2.1: 494.853 ton · Bölüm 2.2: 1.515.000 ton",
     "Üç kat fark var. Tablo 3'teki ürün bazlı sayılar (yonca, korunga, silajlık mısır) "
     + "esas alındı; toplamları ikisine de tam oturmuyor."],
    ["Tarım alanı", "Tablo 1: 324.112 ha · Bölüm 2.1: 357.342 ha \u201cpotansiyel\u201d",
     "Tablo 1 esas alındı. \u201cPotansiyel\u201d muhtemelen sulanabilir hale "
     + "getirilebilecek alanı kastediyor."],
    ["Nadas alanı", "22.535 dekar",
     "Doğu Anadolu'nun nöbetleşe kuru tarım pratiği için çok düşük görünüyor. "
     + "Bu sayıyı modelde kullanmadım."],
  ];

  const kaynakListesi = el("div", { class: "liste" },
    (MUS.kaynaklar || []).map(k => el("div", { class: "madde" },
      el("span", { class: "sira mono", text: "↗" }),
      el("div", { class: "govde" },
        el("a", { href: k.baglanti, target: "_blank", rel: "noopener", text: k.ad })))));

  return [
    bolum("01", "Bu paneldeki sayılar gerçek mi?",
      null,
      el("div", { class: "uyari", html:
        "<strong>Bir kısmı.</strong> Üç tür sayı var ve karıştırılmamaları gerekiyor."
        + "<br><br>"
        + "<span class='kaynak k-olcum'>ÖLÇÜM</span> — resmî kaynakta yayımlanmış, il geneli. "
        + "Nüfus, hayvan varlığı, mera alanı ve ürün üretim miktarları böyledir; "
        + "kaynağı Tarım ve Orman Bakanlığı'nın Muş Tarımsal Yatırım Rehberi 2025 "
        + "(TÜİK 2024 verileri)."
        + "<br><br>"
        + "<span class='kaynak k-varsayim'>VARSAYIM</span> — literatürden alınan katsayı. "
        + "Verim, su ihtiyacı, toprak parametreleri, hastalık eşikleri, fabrika "
        + "kapasitesi. Ekim alanları ölçülmedi; üretim ÷ verim olarak türetildi."
        + "<br><br>"
        + "<span class='kaynak k-dagitim'>DAĞITIM</span> — il toplamının ilçelere bölünmesi. "
        + "<strong>Resmî belgede Muş için ilçe kırılımı yok.</strong> İlçe sayılarının "
        + "tamamı tahmindir; il toplamları korunur." }),
      el("div", { class: "tiles" },
        el("div", { class: "tile" }, el("span", { class: "k", text: "Ölçüme dayalı" }),
          el("span", { class: "v mono", text: String(sayim["ölçüm"]) }),
          el("span", { class: "u", text: "veri alanı" })),
        el("div", { class: "tile" }, el("span", { class: "k", text: "Varsayım" }),
          el("span", { class: "v mono", text: String(sayim["varsayım"]) }),
          el("span", { class: "u", text: "veri alanı" })),
        el("div", { class: "tile" }, el("span", { class: "k", text: "İlçeye dağıtım" }),
          el("span", { class: "v mono", text: String(sayim["dağıtım"]) }),
          el("span", { class: "u", text: "veri alanı" })))),

    bolum("02", "Resmî sayılar", "Doğrudan kaynaktan alınan, il geneli göstergeler.",
      olcumTablo),

    bolum("03", "Üretim ve türetilen ekim alanı",
      "Üretim miktarı resmî; ekim alanı değil. Alan, üretimi varsayılan verime bölerek "
      + "bulunur. Verim değişirse alan değişir — bu yüzden verim sütunu tabloda duruyor.",
      uretimTablo),

    bolum("04", "Kaynağın kendi içindeki çelişkiler",
      "Resmî belge birkaç yerde kendisiyle çelişiyor. Hangi sayıyı neden seçtiğimi "
      + "gizlemek yerine buraya yazdım; veriyle çalışmanın gerçek hali bu.",
      el("div", { class: "liste" }, celiskiler.map(([a, b, c], i) =>
        el("div", { class: "madde" },
          el("span", { class: "sira mono", text: String(i + 1) }),
          el("div", { class: "govde" },
            el("strong", { text: a }),
            el("p", { class: "mono", style: "font-size:12.5px", text: b }),
            el("p", { text: c })))))),

    bolum("05", "Alan alan künye", null, kunyeTablo),

    bolum("06", "Sıradaki veri",
      "Öncelik sırasına göre, hangi veri geldiğinde panelin hangi kısmı gerçekleşir.",
      el("div", { class: "liste" }, [
        ["TÜİK Bitkisel Üretim — Muş ilçe tabloları",
         "İlçe dağıtımı tahmin olmaktan çıkar. Şu an panelin en zayıf halkası bu: "
         + "il toplamları gerçek ama altı ilçeye bölünüşü değil."],
        ["Üniversite laboratuvarı toprak analizleri",
         "Toprak paneli tahmin olmaktan çıkar. Hocanın destek verdiği kısım burası; "
         + "ilçe başına 5–10 parsel örneği bile ilk gerçek katmanı verir."],
        ["İl Müdürlüğü verim kayıtları",
         "Ekim alanları türetilmiş olmaktan çıkar, ölçülmüş olur."],
        ["Muş Şeker Fabrikası kampanya verisi",
         "Kota tavanı şu an tamamen varsayım. Teyit edilince pancar planlaması "
         + "gerçek bir karar aracı olur."],
        ["MGM ilçe iklim verisi",
         "Kosinüs eğrisi yerine ölçülmüş aylık sıcaklık kullanılır; hastalık takvimi keskinleşir."],
        ["Saha yaprak fotoğrafları (kutu + kalibrasyon kartı)",
         "Cercospora tespiti sentetik veriden gerçek yaprağa geçer."],
      ].map(([a, b], i) => el("div", { class: "madde" },
        el("span", { class: "sira mono", text: String(i + 1) }),
        el("div", { class: "govde" }, el("strong", { text: a }), el("p", { text: b })))))),

    bolum("07", "Kaynaklar", null, kaynakListesi),
  ];
}
