// Çatı sekmesi: üç kısmın tek sayfada buluştuğu yer.
// Bir ilçe seçiliyor ve o ilçe için üç soru arka arkaya cevaplanıyor:
//   ne yetişiyor · topraktan ne geliyor · böcekten ne geliyor

const CATI_KISIM = [
  { no: 1, ad: "Planlama", soru: "Ne ekilmeli, ne kadar, hangi ilçede?",
    sekme: "denge" },
  { no: 2, ad: "Toprak", soru: "Topraktan hangi hastalık geliyor?",
    sekme: "hastalik" },
  { no: 3, ad: "Böcek", soru: "Hangi böcek, hangi ilaç, kalıntısız yol var mı?",
    sekme: "bocek" },
];

function catiKisimKart() {
  const h = (BOCEK.hastalik_bulas) || {};
  const toprakSayi = Object.values(h).filter(v => v === "toprak").length;
  const bocekSayi = Object.values(h).filter(v => v === "bocek").length;
  const sayilar = {
    1: `${n0(MUS.ilceler.length)} ilçe · ${n0(MUS.urunler.length)} ürün`,
    2: `${n0(toprakSayi)} toprak kaynaklı hastalık`,
    3: `${n0((BOCEK.zararlilar || []).length)} zararlı · ${n0(bocekSayi)} virüs`,
  };
  return el("div", { class: "bulgu" }, CATI_KISIM.map(k => el("div", { class: "kart" },
    el("div", { class: "ust", style: "justify-content:space-between" },
      el("h3", { text: `${k.no}. ${k.ad}` }),
      rozet(sayilar[k.no], "r-olcum")),
    el("p", { text: k.soru }),
    el("p", { style: "font-size:12.5px;color:var(--muted)",
      text: "Ayrıntı için ilgili sekmeye bak." }))));
}

// Seçili ilçe için üç kısmı arka arkaya çizer.
function catiIlce(ilce) {
  const kap = el("div", {});

  // --- 1. kısım: ne yetişiyor
  const ekim = (MUS.denge || []).filter(d => d.ilce === ilce)
    .sort((a, b) => b.alan_dekar - a.alan_dekar);
  const urunler = ekim.map(d => d.urun);
  const durumRenk = d => d === "açık" ? "var(--critical)"
    : d === "fazla" ? "var(--warning)" : "var(--good)";

  kap.append(
    el("h3", { class: "cati-baslik", text: "1 · Ne yetişiyor" }),
    el("div", { class: "kaydir" },
      tablo([{ ad: "ürün" }, { ad: "alan (dekar)", num: true },
             { ad: "üretim" , num: true }, { ad: "denge" }],
        ekim.map(d => [
          el("strong", { text: d.urun }),
          el("span", { class: "mono", text: n0(d.alan_dekar) }),
          el("span", { class: "mono", text: n0(d.uretim_ton) + " " + d.birim }),
          el("span", { style: `color:${durumRenk(d.durum)};font-weight:600`,
            text: d.durum }),
        ]))));

  // --- 2. kısım: topraktan gelen hastalıklar
  const bulas = BOCEK.hastalik_bulas || {};
  const toprakRisk = (HASTALIK.satirlar || [])
    .filter(s => s.ilce === ilce && bulas[s.hastalik] === "toprak")
    .sort((a, b) => b.risk - a.risk).slice(0, 6);

  kap.append(
    el("h3", { class: "cati-baslik", text: "2 · Topraktan ne geliyor" }),
    toprakRisk.length
      ? el("div", { class: "kaydir" },
          tablo([{ ad: "hastalık" }, { ad: "ürün" }, { ad: "risk", num: true },
                 { ad: "kritik aylar" }, { ad: "ne yapılmalı" }],
            toprakRisk.map(s => [
              el("span", {},
                el("strong", { text: s.hastalik }),
                s.karantina ? rozet("karantina", "r-dagitim") : null),
              s.urun,
              el("span", { class: "mono",
                style: `font-weight:600;color:${s.seviye === "yüksek"
                  ? "var(--critical)" : s.seviye === "orta"
                  ? "var(--warning)" : "var(--muted)"}`, text: n0(s.risk) }),
              el("span", { class: "mono", style: "font-size:12px",
                text: (s.kritik_aylar || []).map(a => BOCEK.aylar[a - 1]).join(" ") }),
              el("span", { style: "font-size:12.5px", text: s.yonetim }),
            ])))
      : el("p", { class: "note", text: "Bu ilçe için toprak kaynaklı risk satırı yok." }),
    el("p", { class: "note", text: "Yalnızca TOPRAK kaynaklı hastalıklar "
      + "listeleniyor — bekleyen toprak analizi tam olarak bunlara konuşacak. "
      + "Havadan ve tohumdan gelenler Hastalık sekmesinde." }));

  // --- 3. kısım: böcekten ne geliyor
  const zararli = (BOCEK.zararlilar || [])
    .filter(z => z.urunler.some(u => urunler.includes(u)))
    .sort((a, b) => b.onem - a.onem);
  const ambar = ((DEPO.ambar && DEPO.ambar.pencere) || [])
    .filter(p => p.ilce === ilce && p.elverisli_ay > 0)
    .sort((a, b) => b.elverisli_ay - a.elverisli_ay);

  kap.append(
    el("h3", { class: "cati-baslik", text: "3 · Böcekten ne geliyor" }),
    el("div", { class: "kaydir" },
      tablo([{ ad: "zararlı" }, { ad: "ürün" }, { ad: "kritik aylar" },
             { ad: "kalıntısız yol" }],
        zararli.map(z => {
          const grupAd = k => ((BOCEK.gruplar || []).find(g => g.grup === k) || {}).ad || k;
          return [
            el("span", {},
              el("strong", { text: z.ad }),
              z.vektor.length ? rozet("virüs taşır", "r-varsayim") : null,
              z.esik_kaynak === "ZMTT" ? rozet("eşik: ZMTT", "r-olcum") : null),
            el("span", { style: "font-size:12.5px",
              text: z.urunler.filter(u => urunler.includes(u)).join(", ") }),
            el("span", { class: "mono", style: "font-size:12px",
              text: z.kritik_aylar.map(a => BOCEK.aylar[a - 1]).join(" ") }),
            z.kalintisiz.length
              ? el("span", { style: "color:var(--good);font-size:12.5px",
                  text: z.kalintisiz.map(grupAd).join(", ") })
              : el("span", { style: "color:var(--critical);font-weight:600",
                  text: "yok" }),
          ];
        }))),
    ambar.length
      ? el("p", { class: "note", text: `Depoda: ${ambar.slice(0, 3)
          .map(a => `${a.zararli} ${a.elverisli_ay} ay`).join(" · ")}`
          + " — ısıtılmamış ambarda yığın sıcaklığı bu türlerin gelişme "
          + "eşiğini bu kadar ay aşıyor." })
      : null);

  return kap;
}

function sekmeCati() {
  if (!BOCEK.zararlilar || !BOCEK.zararlilar.length) {
    return [bolum("01", "Çatı kurulamadı",
      "Bu sekme üç kısmın verisini birden okur; böcek katmanı üretilmemiş.")];
  }

  const ilceler = MUS.ilceler.map(i => i.ad);
  const govde = el("div", {});
  const dugmeler = el("div", { class: "cati-secim" });

  const sec = ad => {
    [...dugmeler.children].forEach(d =>
      d.setAttribute("aria-pressed", String(d.dataset.ilce === ad)));
    govde.replaceChildren(catiIlce(ad));
  };
  for (const ad of ilceler) {
    dugmeler.append(el("button", { type: "button", text: ad, "data-ilce": ad,
      "aria-pressed": "false", onclick: () => sec(ad) }));
  }
  sec(ilceler[0]);

  return [
    bolum("01", "Proje üç kısımdan oluşur",
      "Ayrım SEBEBE göre yapılır, belirtiye göre değil: bir sorunun kaynağı "
      + "toprak mıdır, böcek midir? Cevap, hangi kısmın ilgilendiğini ve "
      + "hangi çözümün işe yarayacağını birlikte belirler. Böcekle taşınan "
      + "bir virüse dayanıklı çeşit değil vektör yönetimi çare olur. "
      + "Toprak kaynaklı kök çürüklüğünde ise ekim nöbeti ancak iki ürün "
      + "ortak etken TAŞIMIYORSA çare olur — ve bu, aşağıda görüleceği "
      + "gibi Muş'ta istisna.",
      catiKisimKart()),
    bolum("02", "İlçe seçin: üç kısım yan yana",
      "Aynı ilçe için üç soru arka arkaya cevaplanıyor. Bu bölüm yeni bilgi "
      + "vermez, üç kısmın aynı tarlada buluştuğunu gösterir — çiftçi "
      + "bunların üçünü ayrı ayrı değil birlikte yaşıyor. Yeni bilgi "
      + "aşağıda: iki kısmı yan yana koymak yetmiyor, birbirine sormak "
      + "gerekiyor.",
      dugmeler, govde),
    ...munavebeBolumu(),
  ];
}

// Çatının asıl işi: 1. kısmın 2. kısma sormadan verdiği sözü denetlemek.
function munavebeBolumu() {
  if (!CATI || !CATI.var) {
    return [bolum("03", "Münavebe denetimi üretilmemiş",
      "Bu bölüm çatı katmanının verisini okur. Üretmek için: "
      + "python src/cati.py")];
  }
  return [
    bolum("03", "1. kısmın sözü 2. kısma soruldu",
      "Planlama kısmı, ürün deseni dar olan ilçeye \u201crisk dağılır, "
      + "münavebe hastalık baskısını kırar\u201d diyordu. Bu cümle 2. kısma "
      + "sorulmadan yazılmıştı. 2. kısımda ise her hastalığın patojeni ve "
      + "bulaş kaynağı kayıtlı, yani soru hesaplanabilir: iki ürün "
      + "TOPRAKTAN bulaşan aynı etkeni paylaşıyorsa, aralarındaki münavebe "
      + "o etkenin baskısını kırmaz — toprakta aynı patojeni beslemeye "
      + "devam eder.",
      munavebeOzet(), munavebeBaskin()),
    bolum("04", "Kıran münavebe neye dayanıyor",
      "Baskıyı kıran tek çift pancarlı. Pancar alanı ise agronomiyle değil "
      + "Muş Şeker Fabrikası kotasıyla sınırlı. İki kısım ayrı sekmelerde "
      + "dururken bu görünmüyordu; birlikte okununca önerinin tavanı "
      + "ortaya çıkıyor.",
      munavebeTavan()),
    bolum("05", "Otuz altı çiftin tamamı ve gerekçeleri",
      "\u201cBelirsiz\u201d bir cevaptır, eksiklik değil: katalog o "
      + "etkeni yalnız cins düzeyinde yazıyor (Fusarium spp. gibi) ve aynı "
      + "cinsin farklı türleri farklı konakçı tutabilir. Orada \u201ckırmaz\u201d "
      + "demek, kataloğun söylemediğini söylemek olurdu.",
      munavebeMatris()),
    bolum("06", "Çatının cevap veremediği yerler",
      "Bir karar sisteminin en dürüst kısmı, nerede karar veremediğidir. "
      + "Bunlardan biri masa başından kapanmıyor: aynı tür kaydı, tarlada "
      + "aynı suşun geçtiğini kanıtlamaz.",
      munavebeBosluk()),
  ];
}
