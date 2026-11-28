// "Muş'ta şu ürün yetişir mi?" — projenin ekilmeyen ürüne bakabildiği yer.
// Karar rozetleri bilerek üç renkli: yetişmez (kötü), söylenemez (nötr),
// yetişir/sınırda (iyi/orta). "Söylenemez" bir eksiklik değil, cevaptır.

const YENI_ROZET = {
  "yetişmez": "r-kotu",
  "söylenemez": "r-notr",
  "sınırda": "r-orta",
  "yetişir": "r-iyi",
  "iklim uygun, toprak bilinmiyor": "r-orta",
};

function yeniUrunTablosu(ilce) {
  const satirlar = (YENI.urunler || []).slice().sort(
    (a, b) => b.dayanim - a.dayanim);
  return el("div", { class: "kaydir" },
    tablo([{ ad: "tür" }, { ad: "kış dayanımı (°C)", num: true },
           { ad: "Muş'ta var mı" }, { ad: "karar" }, { ad: "gerekçe" }],
      satirlar.map(u => {
        const k = (u.ilceler || {})[ilce] || {};
        return [
          el("strong", { text: u.urun }),
          el("span", { class: "mono", text: n1(u.dayanim) }),
          u.musta
            ? el("span", { style: "font-size:12px", text: u.musta })
            : el("span", { style: "color:var(--muted);font-size:12px",
                text: "kayıtlı üretim yok" }),
          rozet(k.karar || "—", YENI_ROZET[k.karar] || "r-notr"),
          el("span", { style: "white-space:normal;font-size:12px;"
            + "color:var(--ink-2)", text: k.gerekce || "" }),
        ];
      })));
}

function yeniUrunSinav() {
  const a = YENI.ayirt_edicilik || {};
  return el("div", {},
    el("div", { style: "display:flex;gap:8px;flex-wrap:wrap;"
      + "align-items:center;margin-bottom:8px" },
      rozet(`${(a.dogru_ret || []).length} doğru ret`, "r-iyi"),
      rozet(`${(a.yanlis_elenen || []).length} yanlış eleme`, "r-iyi"),
      rozet(`${(a.cekimser || []).length} çekimser`, "r-orta")),
    el("p", { style: "white-space:normal;font-size:12.5px;color:var(--ink-2)",
      text: a.yorum || "" }),
    el("p", { class: "note", style: "white-space:normal;margin-top:8px",
      text: "Kaynaklar — kış dayanımı: " + (a.kaynak_kis || "")
        + " · Muş'ta varlık: " + (a.kaynak_varlik || "") }));
}

function sekmeYeniUrun() {
  if (!YENI || !YENI.var) {
    return [bolum("01", "Bu sekme üretilmemiş",
      "Üretmek için: python src/yeni_urun.py")];
  }

  const ilceler = Object.keys(YENI.kis_minimum || {});
  const govde = el("div", {});
  const dugmeler = el("div", { class: "cati-secim" });
  const sec = ad => {
    [...dugmeler.children].forEach(d =>
      d.setAttribute("aria-pressed", String(d.dataset.ilce === ad)));
    govde.replaceChildren(
      el("p", { class: "note", style: "margin:0 0 8px",
        text: `${ad} — en soğuk ayın gece ortalaması `
          + `${n1(YENI.kis_minimum[ad])} °C` }),
      yeniUrunTablosu(ad));
  };
  for (const ad of ilceler) {
    dugmeler.append(el("button", { type: "button", text: ad, "data-ilce": ad,
      "aria-pressed": "false", onclick: () => sec(ad) }));
  }
  sec(ilceler[0]);

  return [
    bolum("01", "Hiç ekilmemiş bir ürün sorulabilir",
      "Proje bugüne kadar EKİLEN dokuz ürün arasında karar veriyordu. "
      + "İklim tarafı tablo değil mekanik olduğu için — etkili sıcaklık "
      + "toplamı, donsuz gün, kış minimumu — hiç ekilmemiş bir ürün de "
      + "sorulabilir. Gereken şey Muş'a dair veri değil, o ürüne dair "
      + "istek. Üç kapı sırayla: KIŞ, sıcaklık toplamı, toprak. İlk kapı "
      + "kapandıysa diğerlerine bakılmaz; toprağı sulayabilirsin, kışı "
      + "değiştiremezsin.",
      dugmeler, govde),
    bolum("02", "Model ayırt edebiliyor mu",
      "Bu projede “yüzde kaç doğruluk” diye bir sayı yok ve "
      + "uydurulmayacak: doğru ekim kararının etiketli gerçeği yok. Ama "
      + "ölçülebilen bir şey var — model, cevabını ÖNCEDEN bildiğimiz "
      + "vakaları ayırabiliyor mu? Pozitif kontrol İl Müdürlüğü'nün kendi "
      + "meyve tablosundan, kış dayanımları akademik bir kaynaktan geliyor.",
      yeniUrunSinav()),
    bolum("03", "Bu sekme ne söylemez",
      "Model “yetişir” dese bile VERİM, KÂRLILIK ve PAZAR "
      + "hakkında hiçbir şey söylemez. Bir ürünün yetişebilir olması, "
      + "ekilmesi gerektiği anlamına gelmez.",
      el("p", { class: "uyari", style: "white-space:normal",
        text: YENI.sinir || "" })),
  ];
}
