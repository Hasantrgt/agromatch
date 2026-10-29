// Depo sekmesi: hasat sonrası. Yayınlanmış doz–cevap verisinden
// LC50 kestirimi, Muş sıcaklık uyarısı, ambar sıcaklığı,
// gelişme penceresi ve mücadele karşılaştırması.
// Çizim işleri 11_depo_grafik.js içinde.

function sekmeDepo() {
  // Depo katmanı scipy/statsmodels olmadan üretilemiyor; o durumda panel
  // yine kurulur, bu sekme sebebini söyler.
  if (!DEPO.zararlilar.length) {
    return [bolum("01", "Depo verisi üretilmemiş",
      "Bu sekme depo katmanından besleniyor ve o katman scipy ile "
      + "statsmodels ister. Üretmek için: pip install -r requirements-depo.txt "
      + "ve ardından python src/mus_panel_uret.py --hepsi")];
  }

  const dc = DEPO.doz_cevap;
  const amb = DEPO.ambar;
  const o = dc.ozet;

  // --- 01 doz–cevap -------------------------------------------------
  const kestirilen = dc.seriler.filter(s => s.lc.LC50 && s.lc.LC50.deger);
  const enIyi = kestirilen.reduce((a, b) =>
    (!a || b.lc.LC50.deger < a.lc.LC50.deger) ? b : a, null);

  const lcHucre = (s, ad) => {
    const k = s.lc[ad];
    if (!k || !k.deger) {
      return el("span", { style: "color:var(--muted)",
        text: k && k.kestirilemedi ? k.kestirilemedi : "—" });
    }
    return el("span", {},
      el("span", { class: "mono", style: "font-weight:600", text: n0(k.deger) }),
      el("span", { class: "mono", style: "color:var(--muted)",
        text: k.alt ? ` [${n0(k.alt)}–${n0(k.ust)}]` : "" }),
      k.disinda ? rozet("aralık dışı", "r-varsayim") : null);
  };

  const seriTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "ürün" }, { ad: "süre", num: true }, { ad: "eğim", num: true },
           { ad: "LC50 ppm [%95]" }, { ad: "LC90 ppm [%95]" }, { ad: "yayın" }],
      dc.seriler.map(s => [
        el("strong", { text: s.etiket }),
        el("span", { class: "mono", text: n0(s.sure) + " g" }),
        el("span", { class: "mono", text: s.egim > 0 ? n2(s.egim) : "—" }),
        lcHucre(s, "LC50"),
        lcHucre(s, "LC90"),
        el("span", { style: "font-size:12px;color:var(--muted)", text: s.kaynak }),
      ])));

  const kaynakKart = el("div", { class: "bulgu" },
    Object.entries(dc.calismalar).map(([kod, c]) => el("div", { class: "kart" },
      el("div", { class: "ust", style: "justify-content:space-between" },
        el("h3", { text: kod }),
        rozet(`${n0(c.sicaklik)} °C · %${n0(c.nem)}`, "r-olcum")),
      el("p", { style: "font-size:12.5px", text: `${c.yazarlar} (${c.yil}). ${c.dergi}.` }),
      el("p", { class: "mono", style: "font-size:12px;color:var(--muted)",
        text: "doi:" + c.doi }),
      el("p", { style: "font-size:12.5px",
        text: `${c.urun} · hücre başına ${n0(c.n_hucre)} birey · ${c.kontrol_notu}` }),
      el("p", { style: "font-size:12.5px;color:var(--muted)", text: c.not_ }))));

  const dozBolum = el("div", {},
    el("div", { class: "cerceve" }, dozCevapGrafik(dc.vitrin.seriler)),
    el("p", { class: "note", style: "margin-top:4px",
      text: `Grafik ${dc.vitrin.urun} ürününü gösteriyor: dört maruz kalma süresi `
        + "aynı eksende. Halkalar LC50'nin yerini işaretler — süre uzadıkça eğri "
        + "sola kayıyor, yani aynı ölümü daha az dozla elde ediyorsunuz. Ölçülen "
        + "doz aralığının dışına düşen LC50'ler grafikte gösterilmez." }),
    el("div", { class: "tiles" },
      ...[["Veri", n0(o.olcum) + " ölçüm", `${n0(o.yayin)} yayın · ${n0(o.birey)} birey`],
          ["Uydurulan", n0(dc.seriler.length) + " seri",
            `${n0(kestirilen.length)} tanesinde LC50 kestirilebildi`],
          ["En düşük LC50", enIyi ? n0(enIyi.lc.LC50.deger) + " ppm" : "—",
            enIyi ? `${enIyi.etiket} · ${n0(enIyi.sure)} gün` : ""]]
        .map(([b, d, a]) => el("div", { class: "tile" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))),
    seriTablo,
    el("p", { class: "note" , text:
      "Yayınlar LC50 vermiyor; yalnızca yüzde ölüm çizelgeleri yayımlamışlar. "
      + "Buradaki LC50 ve LC90 değerleri o çizelgelerden BU ARAÇLA kestirildi. "
      + `${n0(dc.seriler.length - kestirilen.length)} seride araç kestirim yapmayı `
      + "reddetti: kısa maruziyetlerde doz ile ölüm arasında ilişki yok, "
      + "dolayısıyla uydurulacak eğri de yok. "
      + "İki kademe var: denenen dozların onda biri ile on katı arasını aşan "
      + "kestirimler hiç yazılmaz; bu aralıkta kalıp da denenen dozların (100–1000 "
      + "ppm) dışına düşenler yazılır ama 'aralık dışı' diye işaretlenir — model "
      + "orada ölçüm görmemiştir, yalnızca uzatılmıştır." }),
    kaynakKart);

  // --- 02 Muş uyarısı ------------------------------------------------
  const k = dc.karsitlik;
  const acik = DEPO.acik;
  const karsitlikBolum = el("div", {},
    karsitlikGrafik(k),
    el("p", { class: "note", style: "margin-top:4px",
      text: `Aynı ürün (${k.urun}), aynı tür, aynı doz (${n0(k.doz)} ppm), aynı süre `
        + `(${n0(k.sure)} gün). Değişen tek şey ortam. Ölüm %${n1(k.dusuk.olum)}'den `
        + `%${n1(k.yuksek.olum)}'e çıkıyor — ${n1(k.kat)} kat. Nem de değiştiği için `
        + "farkın tamamı sıcaklığa yazılamaz, ama yönü tartışmasız." }),
    el("div", { class: "tiles" },
      ...[["Denemeler", acik.deneme_sicakliklari.map(t => n0(t)).join(" ve ") + " °C",
            "literatürdeki koşullar"],
          ["Muş'ta yığın", n1(acik.yigin_en_sicak) + " °C",
            "en sıcak ayda, en sıcak ilçede"],
          ["Fark", n1(acik.fark) + " °C", "kestirimin taşınamadığı aralık"]]
        .map(([b, d, a]) => el("div", { class: "tile vurgu" },
          el("div", { class: "k", text: b }),
          el("div", { class: "v", text: d }),
          el("div", { class: "u", text: a })))));

  // --- 03 ambar sıcaklığı
  // -0,04 bir ondalığa yuvarlanınca "-0" yazılıyor; sıfıra yapıştır.
  const derece = t => n1(Math.abs(t) < 0.05 ? 0 : t);
  const sicaklikTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "ilçe" }, ...amb.aylar.map(a => ({ ad: a, num: true }))],
      amb.ilceler.flatMap(i => [
        [el("span", { text: i + " (dış)" }),
          ...amb.dis_hava[i].map(t => el("span", { class: "mono", style: "color:var(--muted)", text: derece(t) }))],
        [el("strong", { text: "  yığın" }),
          ...amb.yigin[i].map(t => el("span", { class: "mono", text: derece(t) }))],
      ])));

  // --- 04 gelişme penceresi: ilçe × zararlı ızgarası
  const turler = DEPO.zararlilar.map(z => z.ad);
  const bul = (ilce, zararli) =>
    amb.pencere.find(p => p.ilce === ilce && p.zararli === zararli);
  const pencereTablo = el("div", { class: "kaydir" },
    tablo([{ ad: "zararlı" }, { ad: "eşik °C", num: true },
           ...amb.ilceler.map(i => ({ ad: i, num: true }))],
      turler.map(t => {
        const z = DEPO.zararlilar.find(x => x.ad === t);
        return [
          el("span", {}, el("strong", { text: t }),
            z.karantina ? rozet("karantina", "r-dagitim") : null,
            z.ic_besleyen ? el("span", { class: "mono", style: "font-size:11px;color:var(--muted)", text: " iç besleyen" }) : null),
          el("span", { class: "mono", text: n1(z.taban_sicaklik) }),
          ...amb.ilceler.map(i => {
            const p = bul(i, t);
            const ay = p ? p.elverisli_ay : 0;
            const renk = ay === 0 ? "var(--good)" : ay <= 3 ? "var(--s3)"
              : ay <= 6 ? "var(--warning)" : "var(--critical)";
            return el("span", { class: "mono", style: `color:${renk};font-weight:600`,
              text: ay === 0 ? "—" : ay + " ay" });
          })];
      })));

  // --- 05 mücadele karşılaştırması
  const evetHayir = (v, iyiEvet) => el("span", {
    style: `color:${v === iyiEvet ? "var(--good)" : "var(--critical)"};font-weight:600`,
    text: v ? "evet" : "hayır" });
  const riskRozet = r => rozet(r, r === "YÜKSEK" ? "r-dagitim"
    : r === "yok" ? "r-olcum" : "r-varsayim");

  const mucadeleTablo = el("div", { class: "kaydir" },
    tablo(["yöntem", "tip", "kalıntı", "direnç riski", "faydalıya", "iç larvaya",
           "organik"].map(a => ({ ad: a })),
      DEPO.mucadele.map(m => [
        el("strong", { text: m.ad }),
        m.tip,
        evetHayir(m.kalinti, false),
        riskRozet(m.direnc_riski),
        m.faydaliya,
        evetHayir(m.gucu.ic_larva, true),
        evetHayir(m.organik, true),
      ])));

  const kalintisiz = DEPO.mucadele.filter(m => !m.kalinti);
  const yolKart = el("div", { class: "bulgu" }, kalintisiz.map(m => el("div", { class: "kart" },
    el("div", { class: "ust", style: "justify-content:space-between" },
      el("h3", { text: m.ad }),
      rozet(m.tip, "r-olcum")),
    el("p", { text: m.mekanizma }),
    el("p", { class: "kazanc", text: m.gucu.ic_larva
      ? "Tanenin içindeki larvaya da ulaşır" : "Yalnızca ergine etkili" }),
    el("p", { style: "font-size:12.5px;color:var(--muted)", text: "Bedeli: " + m.bedel }))));

  return [
    bolum("01", "Doz–cevap: yayınlanmış denemelerden LC50 kestirimi",
      "Buradaki sayıların hiçbiri üretilmemiştir. İki açık erişimli yayından alınan "
      + `${n0(o.olcum)} ölçüm (toplam ${n0(o.birey)} birey) probit modele uyduruldu ve `
      + "öldürücü doz kestirildi. Kaynaklar bölümün altında künyeleriyle duruyor.",
      dozBolum),
    bolum("02", "Bu kestirimler Muş'a doğrudan taşınmaz",
      "Diyatomlu toprak böceği zehirlemez, kurutur. Bu yüzden etkisi sıcaklığa ve "
      + "neme bağlıdır — ve iki yayın bunu aynı ürün üzerinde ölçmüş. Aşağıdaki "
      + "karşıtlık, bu projenin depo için verebileceği en dürüst cevabın neden "
      + "'önce ölçün' olduğunu gösteriyor.",
      karsitlikBolum),
    bolum("03", "Ambar sıcaklığı: yığın dışarıyı gecikmeli takip eder",
      `Tahıl yığını büyük bir ısı deposudur. Dış hava −5 °C'ye inerken yığının içi `
      + `haftalarca ılık kalır; bu yüzden "Muş soğuk, depoda sorun olmaz" sanısı `
      + `yanlıştır. Model, aylık yığın sıcaklığını dış havanın sönümlenmiş hâli olarak `
      + `hesaplar (sönümleme ${amb.sonumleme} — bir VARSAYIMDIR, ambara veri kaydedici `
      + `konarak ölçülmelidir).`,
      sicaklikTablo),
    bolum("04", "Gelişme penceresi: hangi zararlı kaç ay gelişebiliyor",
      "Her türün bir gelişme eşiği var. Isıtılmamış ambarda yığın sıcaklığı o eşiği "
      + "kaç ay aşıyorsa zararlı o kadar süre üreyebilir. Sıfır ay demek, soğuk tek "
      + "başına o türü durduruyor demektir — kalıntısız, dirençsiz, bedava. "
      + "Eşik değerleri literatürden alınmıştır ve danışman hocanın teyidini bekler.",
      pencereTablo),
    bolum("05", "Mücadele seçenekleri: kalıntı, direnç ve faydalıya etki",
      "Bu tablo ilaç TAVSİYE ETMEZ — ürün ve doz seçimi reçete yazma yetkisi olan "
      + "kişilerin kararıdır. Yaptığı iş yöntemleri aynı ölçütlerle yan yana koymak. "
      + "'İç larvaya' sütunu kritik: buğday biti larvası tanenin içinde geliştiği için "
      + "yalnızca ergine etkili bir yöntem gizli bulaşmayı temizlemez.",
      mucadeleTablo),
    bolum("06", "Kalıntı bırakmayan yol",
      `Sekiz yöntemin ${kalintisiz.length} tanesi üründe ölçülebilir kalıntı bırakmıyor. `
      + "\"Pestisitten arındırılmış yol\" bu seçeneklerin birleşiminden çıkar; hiçbiri "
      + "tek başına yeterli değildir.",
      yolKart),
  ];
}
