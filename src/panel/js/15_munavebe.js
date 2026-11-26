// Münavebe denetimi: 1. kısmın sözünü 2. kısma sorduran bölüm.
// Üç karar ve üçü farklı şey söyler — rozet renkleri bunu taşımalı:
//   kırar    ortak topraktan etken kaydı yok            (iyi)
//   kırmaz   aynı TÜR iki üründe kayıtlı                (kötü)
//   belirsiz yalnız cins ortak; katalog tür yazmıyor    (nötr, eksik değil)

const MUN_ROZET = { "kırar": "r-iyi", "kırmaz": "r-kotu", "belirsiz": "r-notr" };

// NOT: burada .bulgu sınıfı kullanılmıyor. O sınıf üç sütunlu bir ızgara
// ve rozet satırını sütun yüksekliğine kadar gerip boş kutu gibi gösteriyordu.
function munavebeOzet() {
  const o = CATI.ozet || {};
  const s = o.durum_sayilari || {};
  return el("div", { style: "margin-bottom:12px" },
    el("p", { class: "kazanc", style: "white-space:normal;margin:0 0 8px",
      text: CATI.baskin_bulgu || "" }),
    el("div", { style: "display:flex;gap:8px;flex-wrap:wrap;"
      + "align-items:center;margin-bottom:8px" },
      rozet(`${n0(s["kırar"] || 0)} çift kırıyor`, "r-iyi"),
      rozet(`${n0(s["kırmaz"] || 0)} çift kırmıyor`, "r-kotu"),
      rozet(`${n0(s["belirsiz"] || 0)} çiftte söylenemiyor`, "r-notr")),
    el("p", { style: "white-space:normal;font-size:12.5px;color:var(--ink-2);"
      + "margin:0", text: o.bulgu || "" }));
}

// Alan olarak en büyük çiftler: karar çift SAYISINA değil toprağa bakar.
function munavebeBaskin() {
  return el("div", { class: "kaydir" },
    tablo([{ ad: "ürün çifti" }, { ad: "ekili alan payı", num: true },
           { ad: "münavebe" }, { ad: "ortak etken (tür)" }],
      (CATI.baskin || []).map(c => [
        el("strong", { text: c.urunler.join(" – ") }),
        el("span", { class: "mono", text: "%" + n1(100 * c.alan_payi) }),
        rozet(c.durum, MUN_ROZET[c.durum] || "r-notr"),
        el("span", { style: "white-space:normal;font-size:12.5px;font-style:italic",
          text: c.tur_ortak.length ? c.tur_ortak.join(", ") : "—" }),
      ])));
}

// Tam matris: 36 kayıt. Gerekçe ve sınır sütunları bilerek burada —
// gerekçesiz bir "kırmaz" rozeti, daralttığımız sözün yerine yeni bir
// slogan koymak olurdu.
function munavebeMatris() {
  const sira = { "kırmaz": 0, "belirsiz": 1, "kırar": 2 };
  const satirlar = (CATI.matris || []).slice()
    .sort((a, b) => (sira[a.durum] - sira[b.durum])
      || a.urunler[0].localeCompare(b.urunler[0], "tr"));
  return el("div", { class: "kaydir" },
    tablo([{ ad: "ürün çifti" }, { ad: "karar" }, { ad: "ortak etken" },
           { ad: "gerekçe" }],
      satirlar.map(m => [
        el("span", { style: "white-space:normal", text: m.urunler.join(" – ") }),
        rozet(m.durum, MUN_ROZET[m.durum] || "r-notr"),
        el("span", { style: "white-space:normal;font-size:12px;font-style:italic",
          text: (m.tur_ortak.length ? m.tur_ortak : m.cins_ortak).join(", ") || "—" }),
        el("span", { style: "white-space:normal;font-size:12px;color:var(--ink-2)",
          text: m.gerekce }),
      ])));
}

// Çatının yakaladığı çelişki: baskıyı kıran tek münavebe pancara dayanıyor,
// pancar alanı ise fabrika kotasıyla sınırlı.
function munavebeTavan() {
  const t = CATI.tavan || {};
  if (!t.aciklama) return null;
  return el("div", { class: "kart" },
    el("div", { class: "ust", style: "justify-content:space-between;flex-wrap:wrap;gap:6px" },
      el("h3", { text: "Kıran münavebenin tavanı" }),
      rozet(t.celiski ? "tek dayanak: pancar" : "birden çok dayanak",
        t.celiski ? "r-kotu" : "r-iyi")),
    el("p", { style: "white-space:normal", text: t.aciklama }),
    el("div", { style: "display:flex;gap:8px;flex-wrap:wrap;margin-top:8px" },
      rozet("pancar bugün " + n0(t.pancar_alan_dekar) + " dekar", "r-olcum"),
      rozet("tavan " + n0(t.pancar_tavan_dekar) + " dekar", "r-olcum"),
      rozet("boşluk " + n0(t.bos_alan_dekar) + " dekar", "r-orta")));
}

function munavebeBosluk() {
  return el("div", { class: "liste" },
    (CATI.bosluklar || []).map((b, i) => el("div", { class: "madde" },
      el("span", { class: "sira mono", text: String(i + 1) }),
      el("div", { class: "govde" },
        el("strong", { style: "white-space:normal", text: b["boşluk"] }),
        rozet(b.masa_basi ? "masa başı iş" : "masa başından kapanmaz",
          b.masa_basi ? "r-orta" : "r-kotu"),
        el("p", { style: "white-space:normal;font-size:12.5px;margin:3px 0 0",
          text: b.etki }),
        el("p", { class: "note", style: "white-space:normal;margin:2px 0 0",
          text: "Kapanması: " + b.kapanmasi })))));
}

// Arazi bütçesi: öneriler tek tek doğru ama hepsi aynı toprağı istiyor.
const ARAZI_ROZET = { "sığıyor": "r-iyi", "yarıdan fazlası": "r-orta",
                      "sığmıyor": "r-kotu" };

function munavebeArazi() {
  const satirlar = (CATI.arazi || []).slice()
    .sort((a, b) => b.toplam_pay - a.toplam_pay);
  return el("div", { class: "kaydir" },
    tablo([{ ad: "ilçe" }, { ad: "önerilerin istediği", num: true },
           { ad: "ilçenin ekili alanı", num: true },
           { ad: "pay", num: true }, { ad: "durum" }],
      satirlar.map(a => [
        el("strong", { text: a.ilce }),
        el("span", { class: "mono", text: n0(a.toplam_dekar) + " da" }),
        el("span", { class: "mono", text: n0(a.ekili_alan_dekar) + " da" }),
        el("span", { class: "mono", style: "font-weight:600",
          text: "%" + n1(100 * a.toplam_pay) }),
        rozet(a.durum, ARAZI_ROZET[a.durum] || "r-notr"),
      ])));
}
