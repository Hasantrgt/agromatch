// İlçe karnesi sekmesi: dört başlıkta puanlama ve öneriler.

function sekmeKarne() {
  const kartlar = el("div", { class: "bulgu" }, MUS.karne.map(r => {
    const p = r.puan;
    const bar = (ad, v) => el("div", { style: "display:flex;align-items:center;gap:8px" },
      el("span", { style: "font-size:12px;color:var(--muted);width:76px;flex:none", text: ad }),
      cubuk(v, 100, puanRenk(v)),
      el("span", { class: "mono", style: "font-size:12px;width:26px;text-align:right", text: String(v) }));
    return el("div", { class: "kart" },
      el("div", { class: "ust", style: "justify-content:space-between" },
        el("h3", { text: `${r.sira}. ${r.ilce}` }),
        el("span", { class: "mono", style: `font-size:20px;font-weight:600;color:${puanRenk(r.toplam)}`,
          text: n1(r.toplam) })),
      bar("Yem", p.yem), bar("Su etkinliği", p.su),
      bar("Çeşitlilik", p.cesitlilik), bar("Toprak+iklim", p.toprak),
      el("p", { style: "font-size:12.5px;color:var(--muted);margin-top:4px",
        text: `Etkin ürün sayısı ${n1(r.etkin_urun)} · yem açığı ${n0(r.yem_acik_ton)} ton` }),
      el("p", { text: r.not_ }));
  }));

  const oneriler = el("div", { class: "bulgu" }, MUS.oneri.map(o => el("div", { class: "kart" },
    el("h3", { text: o.ilce }),
    el("div", { class: "liste" }, o.maddeler.map((m, i) => el("div", { class: "madde" },
      el("span", { class: "sira mono", text: String(i + 1) }),
      el("div", { class: "govde" },
        el("strong", { text: m.baslik }),
        el("p", { text: m.metin }),
        el("p", { class: "kazanc", text: m.kazanc }))))))));

  return [
    bolum("01", "İlçe karnesi",
      "Dört başlık ağırlıklandırılır: yem %32, su etkinliği %24, toprak+iklim uyumu %26, "
      + "ürün çeşitliliği %18. Su puanı ürün karmasından arındırılmıştır — pancar ektiği "
      + "için bir ilçe otomatik olarak kötü görünmez, aynı ürünü il ortalamasından daha "
      + "verimli sulayan ilçe puan alır.",
      kartlar),
    bolum("02", "İlçe bazında öneriler",
      "Sıralama önem sırasına göredir; birinci madde diğerlerinin önkoşuludur.",
      oneriler),
  ];
}
