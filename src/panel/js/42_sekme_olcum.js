// Toprak ölçümü sekmesi: laboratuvar verisi geldiğinde ne değişti.

const OLCUM_ALAN_AD = { ph: "pH", om: "organik madde (%)",
                        kirec: "kireç / CaCO₃ (%)", ec: "tuzluluk (dS/m)" };

// Ölçülen dağılımı kutu-çizgi gibi gösterir, varsayımı üstüne işaretler.
function olcumCubugu(o, enDusuk, enYuksek) {
  const en = 230;
  const px = v => Math.round((v - enDusuk) / (enYuksek - enDusuk) * en);
  const sol = px(o.q1), gen = Math.max(px(o.q3) - px(o.q1), 3);
  const vx = px(o.varsayim);
  return el("div", { style: `position:relative;width:${en}px;height:18px` },
    // ölçülen min–maks ince çizgi
    el("div", { style: `position:absolute;left:${px(o.min)}px;top:8px;`
      + `width:${Math.max(px(o.maks) - px(o.min), 1)}px;height:2px;`
      + "background:var(--cizgi)" }),
    // çeyrekler arası kutu
    el("div", { style: `position:absolute;left:${sol}px;top:4px;`
      + `width:${gen}px;height:10px;border-radius:3px;`
      + "background:var(--s3);opacity:.55" }),
    // ölçülen medyan
    el("div", { style: `position:absolute;left:${px(o.medyan)}px;top:2px;`
      + "width:2px;height:14px;background:var(--ink)" }),
    // varsayım — aralığın dışındaysa kırmızı
    el("div", { title: "varsayım " + n2(o.varsayim),
      style: `position:absolute;left:${Math.max(0, Math.min(en - 2, vx))}px;`
        + "top:0;width:2px;height:18px;"
        + `background:${o.aralikta ? "var(--good)" : "var(--critical)"}` }));
}

function sekmeOlcum() {
  if (!OLCUM || !OLCUM.var) {
    return [bolum("01", "Ölçüm verisi bağlı değil",
      "Laboratuvar dosyaları data/toprak_analizi/ altına konup "
      + "python src/toprak_olcum/analiz.py çalıştırılmalı. Dosya yoksa "
      + "model varsayımla çalışmaya devam eder — ölçüm bir iyileştirmedir, "
      + "önkoşul değil.")];
  }

  const e = ETKI || {};
  const eo = e.ozet || {};

  // --- 01 veri künyesi
  const kunye = el("div", {},
    el("div", { class: "kutu" },
      el("strong", { text: `${n0(OLCUM.n_toplam)} laboratuvar örneği bağlandı.` }),
      el("p", { text: `${OLCUM.kaynak}, ${OLCUM.yillar[0]}–`
        + `${OLCUM.yillar[OLCUM.yillar.length - 1]}. Bu, projenin ilk gerçek `
        + "ölçüm katmanı: ilçe toprak değerleri artık varsayım değil." })),
    el("div", { class: "tiles" },
      ...[["Örnek", n0(OLCUM.n_toplam), `${n0(OLCUM.n_ilceli)} tanesinde ilçe bilgisi`],
          ["İlçeye bağlanabilen", "%" + n0(OLCUM.n_ilceli / OLCUM.n_toplam * 100),
            "geri kalanı yalnızca il geneline girer"],
          ["Model farkı", n2(eo.ortalama_mutlak_fark || 0) + " puan",
            "ilçe × ürün ortalama mutlak değişim"],
          ["Sınıfı değişen", n0(eo.sinif_degisen || 0) + " / " + n0(eo.olcumlu_satir || 0),
            "uygunluk sınıfı değişen satır"]]
        .map(([b, d, a]) => el("div", { class: "tile" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))),
    el("div", { class: "kaydir" },
      tablo([{ ad: "yıl" }, { ad: "örnek", num: true },
             { ad: "ilçesi belli", num: true }, { ad: "" }],
        OLCUM.yil_ozet.map(y => [
          el("strong", { text: String(y.yil) }),
          el("span", { class: "mono", text: n0(y.n) }),
          el("span", { class: "mono",
            style: y.ilceli ? "" : "color:var(--critical);font-weight:600",
            text: y.ilceli ? n0(y.ilceli) : "0" }),
          y.ilceli
            ? el("span", { style: "color:var(--good)", text: "ilçe karşılaştırmasına girer" })
            : el("span", { style: "color:var(--critical)",
                text: "yalnızca il geneli — yer sütunu boş" }),
        ]))),
    el("p", { class: "uyari", text: OLCUM.uyari.join("  ") }));

  // --- 02 varsayım ne kadar tuttu
  const sapmaTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "ölçüm" }, { ad: "ort. mutlak fark", num: true },
           { ad: "en büyük fark", num: true }, { ad: "nerede" },
           { ad: "varsayım ölçüm aralığında" }],
      OLCUM.sapma.map(s => [
        el("strong", { text: OLCUM_ALAN_AD[s.alan] || s.alan }),
        el("span", { class: "mono", text: n2(s.ortalama_mutlak_fark) }),
        el("span", { class: "mono", text: n2(s.en_buyuk_fark) }),
        s.en_buyuk_ilce,
        el("span", { style: `font-weight:600;color:${s.aralikta_kalan === 0
          ? "var(--critical)" : s.aralikta_kalan >= s.guvenilir_ilce / 2
          ? "var(--good)" : "var(--warning)"}`,
          text: `${n0(s.aralikta_kalan)} / ${n0(s.guvenilir_ilce)} ilçe` }),
      ])));

  const karsilastirma = el("div", {});
  for (const alan of Object.keys(OLCUM_ALAN_AD)) {
    const satir = Object.entries(OLCUM.ilce)
      .filter(([, v]) => v.alanlar[alan])
      .map(([i, v]) => [i, v.alanlar[alan]]);
    if (!satir.length) continue;
    const hepsi = satir.flatMap(([, o]) => [o.min, o.maks, o.varsayim]);
    const alt = Math.min(...hepsi), ust = Math.max(...hepsi);
    karsilastirma.append(
      el("h3", { class: "cati-baslik", text: OLCUM_ALAN_AD[alan] }),
      el("div", { class: "kaydir" },
        tablo([{ ad: "ilçe" }, { ad: "n", num: true },
               { ad: "ölçülen medyan", num: true }, { ad: "varsayım", num: true },
               { ad: "fark", num: true }, { ad: "dağılım" }],
          satir.map(([i, o]) => [
            el("span", {}, el("strong", { text: i }),
              o.guvenilir ? null : rozet("az örnek", "r-dagitim")),
            el("span", { class: "mono", text: n0(o.n) }),
            el("span", { class: "mono", style: "font-weight:600", text: n2(o.medyan) }),
            el("span", { class: "mono", style: "color:var(--muted)", text: n2(o.varsayim) }),
            el("span", { class: "mono",
              style: `font-weight:600;color:${o.aralikta ? "var(--good)" : "var(--critical)"}`,
              text: (o.fark > 0 ? "+" : "") + n2(o.fark) }),
            olcumCubugu(o, alt, ust),
          ]))));
  }

  // --- 03 modele etkisi
  const etkiBolum = el("div", {},
    el("p", { class: "note", text: "Yeşil çizgi: varsayım ölçülen çeyrekler "
      + "arası aralığın içinde. Kırmızı: dışında. Gri kutu çeyrekler arası, "
      + "siyah çizgi ölçülen medyan." }),
    (e.sinif_degisenler && e.sinif_degisenler.length)
      ? el("div", { class: "kaydir" },
          tablo([{ ad: "ilçe" }, { ad: "ürün" }, { ad: "varsayımla" },
                 { ad: "ölçümle" }, { ad: "fark", num: true }],
            e.sinif_degisenler.map(s => [
              s.ilce, el("strong", { text: s.urun }),
              el("span", { style: "color:var(--muted)",
                text: `${n1(s.varsayim_puan)} ${s.varsayim_sinif}` }),
              el("span", { style: "font-weight:600",
                text: `${n1(s.olcum_puan)} ${s.olcum_sinif}` }),
              el("span", { class: "mono",
                style: `color:${s.fark > 0 ? "var(--good)" : "var(--critical)"}`,
                text: (s.fark > 0 ? "+" : "") + n1(s.fark) }),
            ])))
      : el("p", { class: "note", text: "Uygunluk sınıfı değişen satır yok." }),
    el("p", { class: "note", text: "Ortalama değişim küçük olabilir ama "
      + "SINIF değişimi tavsiye değişimi demektir: 'burada sınırlı' diyen bir "
      + "satır 'uygun'a dönüyorsa, varsayımla verilmiş tavsiye yanlıştı." }));

  // --- 04 kullanılmayan sütunlar
  const eksikBolum = el("div", { class: "bulgu" },
    Object.entries(OLCUM.kullanilmayan_sutunlar).map(([ad, sebep]) =>
      el("div", { class: "kart" },
        el("div", { class: "ust", style: "justify-content:space-between" },
          el("h3", { text: ad }),
          rozet("kullanılmıyor", "r-dagitim")),
        el("p", { text: sebep }))));

  return [
    bolum("01", "Laboratuvar verisi: ne geldi, ne kadarı kullanılabilir",
      "Projenin en uzun süredir beklediği şey buydu. Ama gelen verinin "
      + "tamamı kullanılamıyor ve bunu gizlemek yerine yazmak gerekiyor.",
      kunye),
    bolum("02", "Varsayımlarımız ne kadar tuttu",
      "Bu sekmenin asıl sorusu. Model üç yıl boyunca varsayılmış toprak "
      + "değerleriyle çalıştı; ölçüm gelince hangi varsayımın isabetli, "
      + "hangisinin yanlış olduğu ortaya çıktı.",
      sapmaTablo, karsilastirma),
    bolum("03", "Ölçüm modeli ne kadar değiştirdi",
      `${n0(eo.olcumlu_satir || 0)} ilçe × ürün satırında ortalama mutlak `
      + `değişim ${n2(eo.ortalama_mutlak_fark || 0)} puan — model sağlam. `
      + `Ama ${n0(eo.sinif_degisen || 0)} satırda uygunluk SINIFI değişti.`,
      etkiBolum),
    bolum("04", "Gelen ama kullanılmayan sütunlar",
      "Bir sütunun dosyada olması kullanılabilir olduğu anlamına gelmiyor. "
      + "Birimi şüpheli bir sayıyı modele koymak, hiç koymamaktan kötüdür.",
      eksikBolum),
  ];
}
