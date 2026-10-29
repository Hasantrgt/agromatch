// Erken uyarı sekmesi: dört katmandan gelen uyarılar, ilçe ve ay bazında.

const UYARI_RENK = { 3: "#c0392b", 2: "#eb6834", 1: "#2a78d6" };
const TUR_ROZET = {
  don: "r-dagitim", zararlı: "r-varsayim", hastalık: "r-varsayim",
  depo: "r-olcum", sürvey: "r-olcum",
};

function sekmeUyari() {
  if (!UYARI.uyarilar || !UYARI.ilceler || !UYARI.ilceler.length) {
    return [bolum("01", "Uyarı verisi üretilmemiş",
      "Üretmek için: python src/uyari/takvim.py")];
  }

  const o = UYARI.ozet;
  const canli = UYARI.gunluk_veri;

  // --- 01 ne olduğu ve ne OLMADIĞI
  const kunye = el("div", {},
    el("div", { class: "kutu" },
      el("strong", { text: canli
        ? "Bu uyarılar ölçüme dayanıyor."
        : "Bu bir TAHMİN değil, BEKLENEN TAKVİMDİR." }),
      el("p", { text: canli
        ? "Günlük istasyon verisi bağlı; uyarılar ölçülen sıcaklığa göre üretiliyor."
        : "Uyarılar günlük hava verisine değil, iklim normaline dayanıyor. "
          + "Yani \"önümüzdeki hafta süne çıkacak\" demez — diyemez. "
          + "Söylediği şey, uzun yıllar ortalamasına göre hangi ayda neyin "
          + "kapıyı çalacağıdır. Günlük istasyon verisi bağlanınca "
          + "çözünürlük güne iner ve bu kutu değişir." })),
    el("div", { class: "tiles" },
      ...[["Uyarı", n0(o.toplam), `ilçe başına ${n1(o.ilce_basina)}`],
          ["Çözünürlük", UYARI.cozunurluk, canli ? "ölçüm" : "iklim normali"],
          ["Resmî kaynaklı", n0(o.zmtt) + " uyarı",
            "ZMTT'den doğrulanmış kayda dayanıyor"],
          ["En yoğun ay", o.en_yogun_ay, "tarlaya en çok bakılacak ay"]]
        .map(([b, d, a]) => el("div", { class: "tile" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))));

  // --- ilçe × ay ısı ızgarası
  const enCok = Math.max(...UYARI.ilceler.flatMap(i => UYARI.aylik_sayi[i]));
  const izgara = el("div", { class: "kaydir" },
    tablo([{ ad: "ilçe" }, ...UYARI.aylar.map(a => ({ ad: a.slice(0, 3), num: true }))],
      UYARI.ilceler.map(i => [
        el("strong", { text: i }),
        ...UYARI.aylik_sayi[i].map(v => el("span", {
          class: "mono",
          style: v ? `display:inline-block;width:100%;border-radius:3px;`
            + `background:rgba(192,57,43,${(0.15 + 0.6 * v / enCok).toFixed(2)});`
            + `font-weight:600` : "color:var(--muted)",
          text: v ? String(v) : "—" })),
      ])));

  // --- 02 seçili ilçenin uyarıları
  const govde = el("div", {});
  const dugmeler = el("div", { class: "cati-secim" });

  const ciz = ilce => {
    const liste = UYARI.uyarilar[ilce] || [];
    const aylar = [...new Set(liste.map(u => u.ay))].sort((a, b) => a - b);
    govde.replaceChildren(...aylar.map(ay => el("div", {},
      el("h3", { class: "cati-baslik",
        text: `${UYARI.aylar[ay - 1]} — ${liste.filter(u => u.ay === ay).length} uyarı` }),
      el("div", { class: "liste" },
        liste.filter(u => u.ay === ay).map(u => el("div", { class: "madde" },
          el("span", { class: "sira mono",
            style: `color:${UYARI_RENK[u.siddet]};font-weight:700`,
            text: "!".repeat(u.siddet) }),
          el("div", { class: "govde" },
            el("div", { style: "display:flex;align-items:center;gap:8px;flex-wrap:wrap" },
              el("strong", { text: u.baslik }),
              rozet(u.tur, TUR_ROZET[u.tur] || "r-varsayim"),
              rozet(u.kaynak, u.kaynak === "ZMTT" ? "r-olcum" : "r-varsayim")),
            el("p", { text: u.gerekce }),
            el("p", { class: "kazanc", text: u.yapilacak })))))
    )));
  };
  for (const ad of UYARI.ilceler) {
    dugmeler.append(el("button", { type: "button", text: ad, "data-ilce": ad,
      "aria-pressed": "false",
      onclick: () => {
        [...dugmeler.children].forEach(d =>
          d.setAttribute("aria-pressed", String(d.dataset.ilce === ad)));
        ciz(ad);
      } }));
  }
  dugmeler.children[0].setAttribute("aria-pressed", "true");
  ciz(UYARI.ilceler[0]);

  // --- 03 modelin yeri
  const modelBolum = el("div", { class: "bulgu" },
    [["Takvim uyarıyı verir",
      "Kural tabanlıdır: hastalık kataloğunun kritik ayları, zararlıların "
      + "dönemleri, ambar yığın sıcaklığı, don hassasiyeti. Burada yapay "
      + "zekâ yoktur ve olduğu iddia edilmez."],
     ["Model uyarıyı doğrular",
      "Takvim \"Cercospora dönemi\" dediğinde üretici yaprak fotoğrafı "
      + "çeker; lezyon sınıflayıcı (eğitilmiş model, %99 doğruluk) lekenin "
      + "gerçekten o olup olmadığını söyler. Yapay zekânın hak ettiği yer "
      + "burasıdır: uyarıyı üretmek değil, doğrulamak."],
     ["Ölçüm kuralı değiştirir",
      "Süne uyarısı ilaçlama demez, SÜRVEY der. Teknik talimat kararı "
      + "parazitlenme oranına bağladığı için, ölçüm yapılmadan karar "
      + "verilemez. Sistem bunu dayatır."]]
      .map(([b, m]) => el("div", { class: "kart" },
        el("div", { class: "ust" }, el("h3", { text: b })),
        el("p", { text: m }))));

  return [
    bolum("01", "Erken uyarı: hangi ayda neye bakılacak",
      `Dört katman tek akışa dönüyor: hastalık kataloğu, tarla zararlıları, `
      + "ambar modeli ve iklim. Uyarı, kritik ayın kendisine değil BİR "
      + "ÖNCESİNE konur — zararlı göründükten sonra haber vermek uyarı "
      + "değil, tespittir.",
      kunye,
      el("h3", { class: "cati-baslik", text: "İlçe × ay yoğunluğu" }),
      izgara),
    bolum("02", "İlçe seçin: aylara göre uyarı listesi",
      "Her uyarı neye dayandığını yanında taşır: türü, kaynağı (ZMTT mi "
      + "literatür mü) ve şiddeti. Ünlem sayısı şiddettir.",
      dugmeler, govde),
    bolum("03", "Yapay zekâ bu sistemde nerede",
      "Bu soruya net cevap vermek, cevabı şişirmekten iyidir.",
      modelBolum),
  ];
}
