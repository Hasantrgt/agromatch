// Sekme yönlendirmesi ve açılış.

const SEKMELER = [
  ["cati", "Çatı", sekmeCati],
  ["olcum", "Toprak ölçümü", sekmeOlcum],
  ["collesme", "Çölleşme", sekmeCollesme],
  ["uyari", "Erken uyarı", sekmeUyari],
  ["karlilik", "Karlılık", sekmeKarlilik],
  ["genel", "Genel bakış", sekmeGenel],
  ["denge", "Denge & yem", sekmeDenge],
  ["toprak", "Toprak & iklim", sekmeToprak],
  ["hastalik", "Hastalık", sekmeHastalik],
  ["belirsizlik", "Belirsizlik", sekmeBelirsizlik],
  ["iz", "Hesap izi", sekmeIz],
  ["depo", "Depo", sekmeDepo],
  ["bocek", "Böcek & ilaç", sekmeBocek],
  ["karne", "İlçe karnesi", sekmeKarne],
  ["kunye", "Veri künyesi", sekmeKunye],
];

const navKutu = document.getElementById("sekmeler");
const icerik = document.getElementById("icerik");

function goster(anahtar) {
  const bulunan = SEKMELER.find(s => s[0] === anahtar) || SEKMELER[0];
  [...navKutu.children].forEach(b =>
    b.setAttribute("aria-pressed", String(b.dataset.k === bulunan[0])));
  icerik.replaceChildren(...bulunan[2]());
  try { history.replaceState(null, "", "#" + bulunan[0]); } catch (e) { /* yok say */ }
  window.scrollTo({ top: 0, behavior: "instant" });
}

for (const [k, ad] of SEKMELER) {
  navKutu.append(el("button", { type: "button", role: "tab", text: ad, "data-k": k,
    "aria-pressed": "false", onclick: () => goster(k) }));
}

// Üst etiketler
const etiket = document.getElementById("ustEtiket");
const olcumSayisi = MUS.kunye.filter(k => k.tur === "ölçüm").length;
const tahminSayisi = MUS.kunye.length - olcumSayisi;
etiket.append(
  el("span", { class: "tag", text: "6 ilçe" }),
  el("span", { class: "tag", text: "9 ürün" }),
  el("span", { class: "tag", text: HASTALIK.istatistik.hastalik_sayisi + " hastalık" }),
  el("span", { class: "tag", text: "il verisi: TÜİK 2024" }),
  el("span", { class: "tag warn",
    text: `${olcumSayisi} alan ölçüm · ${tahminSayisi} alan tahmin` }));

const basla = (location.hash || "").replace("#", "");
// Varsayılan sekme Çatı: panel açılınca önce projenin üç kısmı
// görünsün, ayrıntı sonra gelsin.
goster(SEKMELER.some(s => s[0] === basla) ? basla : "cati");
