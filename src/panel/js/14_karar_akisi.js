// Böcek karar akışı — "tarlamda şu böcek var, ne yapayım" sorusunun cevabı.
// Dört adım ve SIRASI önemli: eşik, ilaçsız yol, ilaç, faydalı koruma.
// "Hangi ilaç" sorusuyla başlamak cevabı baştan ilaçlamaya sabitler.

const ADIM_ROZET = {
  // 1. adım
  "eşik bilinmiyor": "r-kotu",
  // "resmî eşik yok" boşluk DEĞİL: talimat eşik yerine başka bir ölçüt
  // koymuş. Kırmızı göstermek onu eksiklik gibi okutur.
  "resmî eşik yok": "r-notr",
  "eşik var — ölçüm gerekli": "r-orta",
  // 2. adım
  "var": "r-iyi",
  "yok": "r-kotu",
  // 3. adım
  "seçenek var": "r-notr",
  "kimyasal seçenek yok": "r-orta",
  // 4. adım
  "doğal düşman var": "r-iyi",
  "kayıtlı doğal düşman yok": "r-orta",
};

function adimKutusu(a) {
  const govde = el("div", { style: "flex:1;min-width:0" },
    el("div", { style: "display:flex;align-items:center;gap:8px;"
      + "flex-wrap:wrap;margin-bottom:4px" },
      el("strong", { text: a.ad }),
      rozet(a.durum, ADIM_ROZET[a.durum] || "r-notr")),
    el("p", { style: "font-size:12.5px;margin:0;color:var(--ink-2)",
      text: a.aciklama }));

  if (a.esik) {
    govde.append(el("p", { class: "note",
      style: "margin-top:6px;font-size:12px",
      text: "Eşik: " + a.esik
        + (a.esik_kaynak ? "  [" + a.esik_kaynak + "]" : "") }));
  }

  if (a.secenekler && a.secenekler.length) {
    govde.append(el("div", { style: "margin-top:8px;display:flex;"
      + "flex-wrap:wrap;gap:6px" },
      ...a.secenekler.map(s => el("span", {
        // Kalıntısız seçeneklerde faydalı yükü hesaplanmaz (alan yok).
        // Tanımsızı "en kötü" saymak, en iyi seçeneği kırmızı gösterirdi.
        class: "rozet " + (s.canliya_zarar == null || s.canliya_zarar === 0
          ? "r-iyi" : s.canliya_zarar <= 2 ? "r-orta" : "r-kotu"),
        title: s.vurulan && s.vurulan.length
          ? "vurduğu faydalılar: " + s.vurulan.join(", ")
          : (s.not_ || s.etki_sekli || ""),
        text: s.ad + (s.canliya_zarar != null
          ? ` · ${n0(s.canliya_zarar)} faydalı vurur` : "")
      }))));
  }

  if (a.avcilar && a.avcilar.length) {
    govde.append(el("div", { class: "liste", style: "margin-top:8px" },
      a.avcilar.map(f => el("div", { class: "madde" },
        el("span", { class: "sira mono", text: "→" }),
        el("div", { class: "govde" },
          el("strong", { text: f.ad }),
          el("span", { style: "color:var(--muted);font-size:12px",
            text: "  " + f.rol }),
          f.korumak_icin
            ? el("p", { style: "font-size:12px;margin:2px 0 0",
                text: f.korumak_icin })
            : null)))));
    if (a.o_grubun_vurdugu && a.o_grubun_vurdugu.length) {
      govde.append(el("p", { class: "uyari", style: "margin-top:8px",
        text: `Seçilen grup (${a.en_az_vuran_grup}) şunları vuruyor: `
          + a.o_grubun_vurdugu.join(", ")
          + ". En az vuran seçenek bile bedelsiz değil." }));
    }
  }

  return el("div", { style: "display:flex;gap:12px;padding:10px 0;"
    + "border-top:1px solid var(--grid)" },
    el("div", { class: "mono",
      style: "flex:none;width:26px;height:26px;border-radius:50%;"
        + "background:var(--brand-soft);color:var(--ink);display:flex;"
        + "align-items:center;justify-content:center;font-weight:700;"
        + "font-size:12px", text: String(a.adim) }),
    govde);
}

function kararKarti(k) {
  return el("div", { class: "kart", style: "margin-bottom:14px" },
    el("div", { class: "ust", style: "justify-content:space-between;"
      + "align-items:flex-start;flex-wrap:wrap;gap:6px" },
      el("div", {},
        el("h3", { text: k.zararli }),
        el("div", { style: "font-size:11.5px;color:var(--muted);"
          + "font-style:italic", text: k.latince })),
      el("div", { style: "text-align:right" },
        rozet(k.urunler.join(", "), "r-notr"),
        el("div", { style: "font-size:11px;color:var(--muted);margin-top:3px",
          text: "kritik ay: " + k.kritik_aylar.map(a => BOCEK_AY[a - 1]).join(", ") }))),
    el("p", { class: "kazanc", style: "margin:6px 0 2px", text: k.ozet }),
    ...k.adimlar.map(adimKutusu));
}

const BOCEK_AY = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
                  "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];


// Karar bölümünün tamamını kurar. 39_sekme_bocek.js 260 satır
// sınırını aştığı için buraya taşındı.
function kararBolumuKur() {
  if (!BOCEK || !BOCEK.karar || !BOCEK.karar.length) return null;
  // Karar akışı en başa konuyor: kullanıcının sorusu "listede ne var"
  // değil, "ne yapayım". Kataloglar o sorunun arkasında durmalı.
  return el("div", {},
        el("div", { class: "kutu" },
          el("strong", { text: "Sıra rastgele değil." }),
          el("p", { text: "Önce eşik sorulur, çünkü çoğu ilaçlama "
            + "gereksizdir: zararlının varlığı tek başına zarar demek "
            + "değildir ve eşiğin altında ilaçlamak faydalı böcekleri "
            + "öldürüp sorunu büyütür. Sonra kalıntısız yol, sonra ilaç, "
            + "en son faydalı koruma. \"Hangi ilaç\" sorusuyla başlamak "
            + "cevabı baştan ilaçlamaya sabitlerdi." })),
        el("div", { class: "tiles", style: "margin-top:12px" },
          ...[["Zararlı", n0(BOCEK.karar.length), "karar akışı üretilen tür"],
              ["Eşiği bilinmeyen",
                n0(BOCEK.karar_bosluklari.esigi_bilinmeyen.length),
                "bu türlerde ilaçlama ÖNERİLMİYOR"],
              ["Kalıntısız yolu olmayan",
                n0(BOCEK.karar_bosluklari.kalintisiz_yolu_olmayan.length),
                "bilinen boşluk, uydurulmuyor"],
              ["Hiçbir seçeneği olmayan",
                n0(BOCEK.karar_bosluklari.hicbir_secenegi_olmayan.length),
                "ne kalıntısız yol ne kimyasal grup"]]
            .map(([b, d, a]) => el("div", { class: "tile" },
              el("div", { class: "k", text: b }),
              el("div", { class: "v", text: d }),
              el("div", { class: "u", text: a })))),
        el("p", { class: "uyari", style: "margin-top:12px",
          text: "Bu sistem ETKİ GRUBUNA kadar götürür. Ticari ürün adı, "
            + "doz ve bekleme süresi bilerek YOK: onlar reçetedir, "
            + "ruhsata bağlıdır ve ziraat mühendisinin işidir." }),
        el("div", { style: "margin-top:14px" },
          ...BOCEK.karar.map(kararKarti)))
}

