"""
AGROMATCH - Hastalık sınıflandırma modeli (transfer öğrenme)
============================================================
Yaprak görüntüsünden hastalık şiddetini / türünü sınıflandıran CNN'i eğitir,
ölçer ve açıklanabilirlik görseli üretir.

NEDEN TRANSFER ÖĞRENME
Sıfırdan CNN eğitmek için on binlerce görüntü ve saatlerce GPU gerekir.
ImageNet üzerinde eğitilmiş bir ağın ilk katmanları kenar, doku ve renk
geçişlerini zaten öğrenmiştir; biz yalnızca son katmanı kendi sınıflarımıza
göre yeniden eğitiriz. Birkaç yüz görüntüyle ve CPU'yla bile sonuç alınır.

BEKLENEN KLASÖR YAPISI (goruntu_hazirla.py --bol bunu üretir)
    <veri>/egitim/<sınıf>/*.jpg
    <veri>/dogrulama/<sınıf>/*.jpg
    <veri>/test/<sınıf>/*.jpg

ÇIKTILAR
    outputs/model/<ad>.pt              eğitilmiş ağırlıklar
    outputs/model_metrik.json          doğruluk, sınıf bazında kesinlik/duyarlılık/F1
    outputs/model_karmasiklik.png      karmaşıklık matrisi
    outputs/gradcam/*.png              modelin yaprağın neresine baktığı

Kullanım:
    python src/goruntu/egitim.py --veri data/goruntu_bolunmus --epok 8
    python src/goruntu/egitim.py --veri data/goruntu_bolunmus --model resnet18 --onegitimli 0

Not: --onegitimli 0, ImageNet ağırlıklarını indirmeden (internetsiz ortamda)
rastgele başlangıçla eğitir. Gerçek çalışmada 1 kullanılmalıdır.
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"
ORTALAMA = [0.485, 0.456, 0.406]
SAPMA = [0.229, 0.224, 0.225]


def donusumler(boyut):
    egitim = transforms.Compose([
        transforms.RandomResizedCrop(boyut, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.25, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(ORTALAMA, SAPMA),
    ])
    olcme = transforms.Compose([
        transforms.Resize(int(boyut * 1.15)),
        transforms.CenterCrop(boyut),
        transforms.ToTensor(),
        transforms.Normalize(ORTALAMA, SAPMA),
    ])
    return egitim, olcme


def model_kur(ad, sinif_sayisi, onegitimli):
    if ad == "mobilenet_v3_small":
        m = models.mobilenet_v3_small(weights="DEFAULT" if onegitimli else None)
        m.classifier[3] = nn.Linear(m.classifier[3].in_features, sinif_sayisi)
        hedef_katman = m.features[-1]
    elif ad == "resnet18":
        m = models.resnet18(weights="DEFAULT" if onegitimli else None)
        m.fc = nn.Linear(m.fc.in_features, sinif_sayisi)
        hedef_katman = m.layer4[-1]
    else:
        raise ValueError(f"bilinmeyen model: {ad}")

    # Sıfırdan eğitimde toplu normalleştirme (BatchNorm) tuzağı:
    # torchvision'ın MobileNetV3'ü BN momentumunu 0,01 gibi çok küçük bir değere ayarlar.
    # Önceden eğitilmiş ağırlıklarla sorun değildir (istatistikler hazır gelir), ama
    # sıfırdan eğitimde koşan ortalama/varyans güncellenemez: model eğitimde öğrenir,
    # değerlendirme kipinde (model.eval) rastgele tahmin yapar — doğrulama doğruluğu
    # 1/sınıf sayısına çakılır. Momentumu normal değerine çekiyoruz.
    if not onegitimli:
        for katman in m.modules():
            if isinstance(katman, nn.BatchNorm2d):
                katman.momentum = 0.1
    return m, hedef_katman


def dongu(model, yukleyici, kayip_f, cihaz, eniyileyici=None):
    egitim_mi = eniyileyici is not None
    model.train(egitim_mi)
    toplam_kayip, dogru, adet = 0.0, 0, 0
    tahminler, gercekler = [], []
    with torch.set_grad_enabled(egitim_mi):
        for x, y in yukleyici:
            x, y = x.to(cihaz), y.to(cihaz)
            cikti = model(x)
            kayip = kayip_f(cikti, y)
            if egitim_mi:
                eniyileyici.zero_grad(); kayip.backward(); eniyileyici.step()
            toplam_kayip += kayip.item() * x.size(0)
            t = cikti.argmax(1)
            dogru += (t == y).sum().item(); adet += x.size(0)
            tahminler += t.cpu().tolist(); gercekler += y.cpu().tolist()
    return toplam_kayip / adet, dogru / adet, tahminler, gercekler


def karmasiklik_ciz(matris, siniflar, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(1.6 + 0.9 * len(siniflar), 1.4 + 0.8 * len(siniflar)))
    ax.imshow(matris, cmap="Blues")
    ax.set_xticks(range(len(siniflar)), siniflar, rotation=30, ha="right")
    ax.set_yticks(range(len(siniflar)), siniflar)
    ax.set_xlabel("Model tahmini"); ax.set_ylabel("Gerçek sınıf")
    enb = matris.max() if matris.size else 1
    for i in range(len(siniflar)):
        for j in range(len(siniflar)):
            ax.text(j, i, int(matris[i, j]), ha="center", va="center",
                    color="white" if matris[i, j] > enb * 0.55 else "#16281F", fontsize=11)
    ax.set_title("Karmaşıklık matrisi")
    fig.tight_layout(); fig.savefig(yol, dpi=140); plt.close(fig)


def gradcam(model, hedef_katman, veri_kumesi, cihaz, siniflar, kac=6):
    """Modelin kararını hangi bölgeye dayandırdığını gösterir (Grad-CAM)."""
    import cv2
    aktivasyon, gradyan = {}, {}

    def ileri(_m, _g, cikti): aktivasyon["v"] = cikti.detach()
    def geri(_m, _gi, go): gradyan["v"] = go[0].detach()

    t1 = hedef_katman.register_forward_hook(ileri)
    t2 = hedef_katman.register_full_backward_hook(geri)

    hedef = CIKTI / "gradcam"; hedef.mkdir(parents=True, exist_ok=True)
    model.eval()
    secilen = np.linspace(0, len(veri_kumesi) - 1, min(kac, len(veri_kumesi))).astype(int)
    kayitlar = []
    for n in secilen:
        x, y = veri_kumesi[int(n)]
        girdi = x.unsqueeze(0).to(cihaz).requires_grad_(True)
        cikti = model(girdi)
        sinif = int(cikti.argmax(1).item())
        model.zero_grad(); cikti[0, sinif].backward()

        a, g = aktivasyon["v"][0], gradyan["v"][0]
        agirlik = g.mean(dim=(1, 2), keepdim=True)
        isi = torch.relu((agirlik * a).sum(0)).cpu().numpy()
        isi = isi / (isi.max() + 1e-8)
        isi = cv2.resize(isi, (x.shape[2], x.shape[1]))

        goruntu = (x.cpu().numpy().transpose(1, 2, 0) * np.array(SAPMA) + np.array(ORTALAMA))
        goruntu = np.clip(goruntu * 255, 0, 255).astype(np.uint8)[:, :, ::-1]
        renkli = cv2.applyColorMap((isi * 255).astype(np.uint8), cv2.COLORMAP_JET)
        kaplama = cv2.addWeighted(goruntu, 0.6, renkli, 0.4, 0)
        ad = f"gradcam_{n:03d}_gercek-{siniflar[y]}_tahmin-{siniflar[sinif]}.png"
        cv2.imwrite(str(hedef / ad), kaplama)
        kayitlar.append(dict(dosya=ad, gercek=siniflar[y], tahmin=siniflar[sinif]))

    t1.remove(); t2.remove()
    return kayitlar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--veri", default="data/goruntu_bolunmus")
    ap.add_argument("--model", default="mobilenet_v3_small",
                    choices=["mobilenet_v3_small", "resnet18"])
    ap.add_argument("--epok", type=int, default=8)
    ap.add_argument("--boyut", type=int, default=160)
    ap.add_argument("--parti", type=int, default=32)
    ap.add_argument("--ogrenme-hizi", type=float, default=None,
                    help="boş bırakılırsa eniyileyiciye göre seçilir")
    ap.add_argument("--eniyileyici", default="sgd", choices=["sgd", "adamw"],
                    help="sıfırdan eğitimde sgd, önceden eğitilmiş ağırlıkta adamw daha iyi sonuç verir")
    ap.add_argument("--onegitimli", type=int, default=1)
    a = ap.parse_args()

    kok = KOK / a.veri if not Path(a.veri).is_absolute() else Path(a.veri)
    if not (kok / "egitim").exists():
        print(f"Veri bulunamadı: {kok}\nÖnce goruntu_hazirla.py --bol çalıştır.")
        return

    cihaz = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    e_don, o_don = donusumler(a.boyut)
    kumeler = {k: datasets.ImageFolder(kok / k, e_don if k == "egitim" else o_don)
               for k in ("egitim", "dogrulama", "test")}
    siniflar = kumeler["egitim"].classes
    yukleyiciler = {k: DataLoader(v, batch_size=a.parti, shuffle=(k == "egitim"),
                                  num_workers=2)
                    for k, v in kumeler.items()}
    print(f"Cihaz: {cihaz} · Sınıflar: {siniflar}")
    for k, v in kumeler.items():
        print(f"  {k:<10} {len(v):>5} görüntü")

    model, hedef_katman = model_kur(a.model, len(siniflar), bool(a.onegitimli))
    model.to(cihaz)
    kayip_f = nn.CrossEntropyLoss()
    # Eniyileyici seçimi önemli: sıfırdan eğitimde AdamW'nin küçük öğrenme hızı
    # ağı yeterince hareket ettirmiyor ve model tek sınıfa çakılıyor. Momentumlu SGD
    # + kosinüs azalan öğrenme hızı, bu veri büyüklüğünde belirgin şekilde daha iyi.
    if a.eniyileyici == "sgd":
        lr = a.ogrenme_hizi or 0.01
        eniyileyici = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9,
                                      weight_decay=1e-4)
    else:
        lr = a.ogrenme_hizi or 3e-4
        eniyileyici = torch.optim.AdamW(model.parameters(), lr=lr)
    plan = torch.optim.lr_scheduler.CosineAnnealingLR(eniyileyici, T_max=a.epok)

    gecmis, en_iyi, en_iyi_durum = [], 0.0, None
    baslangic = time.time()
    for epok in range(1, a.epok + 1):
        ek, ed, _, _ = dongu(model, yukleyiciler["egitim"], kayip_f, cihaz, eniyileyici)
        dk, dd, _, _ = dongu(model, yukleyiciler["dogrulama"], kayip_f, cihaz)
        gecmis.append(dict(epok=epok, egitim_kayip=round(ek, 4), egitim_dogruluk=round(ed, 4),
                           dogrulama_kayip=round(dk, 4), dogrulama_dogruluk=round(dd, 4)))
        print(f"epok {epok:>2}/{a.epok}  eğitim {ed:.3f}  doğrulama {dd:.3f}  "
              f"(kayıp {dk:.3f})")
        plan.step()
        if dd > en_iyi:
            en_iyi = dd
            en_iyi_durum = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if en_iyi_durum:
        model.load_state_dict(en_iyi_durum)

    _, test_dogruluk, tahmin, gercek = dongu(model, yukleyiciler["test"], kayip_f, cihaz)
    from sklearn.metrics import classification_report, confusion_matrix
    rapor = classification_report(gercek, tahmin, target_names=siniflar,
                                  output_dict=True, zero_division=0)
    matris = confusion_matrix(gercek, tahmin, labels=list(range(len(siniflar))))

    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "model").mkdir(exist_ok=True)
    torch.save(model.state_dict(), CIKTI / "model" / f"{a.model}.pt")
    karmasiklik_ciz(matris, siniflar, CIKTI / "model_karmasiklik.png")
    gradcam_kayit = gradcam(model, hedef_katman, kumeler["test"], cihaz, siniflar)

    metrik = dict(
        model=a.model, onegitimli=bool(a.onegitimli), epok=a.epok, boyut=a.boyut,
        eniyileyici=a.eniyileyici, ogrenme_hizi=lr,
        en_iyi_dogrulama=round(en_iyi, 4),
        siniflar=siniflar,
        veri=dict(egitim=len(kumeler["egitim"]), dogrulama=len(kumeler["dogrulama"]),
                  test=len(kumeler["test"])),
        test_dogruluk=round(test_dogruluk, 4),
        makro_f1=round(rapor["macro avg"]["f1-score"], 4),
        sinif_metrikleri={s: dict(kesinlik=round(rapor[s]["precision"], 3),
                                  duyarlilik=round(rapor[s]["recall"], 3),
                                  f1=round(rapor[s]["f1-score"], 3),
                                  adet=int(rapor[s]["support"])) for s in siniflar},
        karmasiklik_matrisi=matris.tolist(),
        gecmis=gecmis, gradcam=gradcam_kayit,
        sure_saniye=round(time.time() - baslangic, 1),
    )
    (CIKTI / "model_metrik.json").write_text(json.dumps(metrik, ensure_ascii=False, indent=2),
                                             encoding="utf-8")

    print(f"\nTest doğruluğu {test_dogruluk:.3f} · makro F1 {metrik['makro_f1']:.3f} "
          f"· süre {metrik['sure_saniye']} sn")
    for s in siniflar:
        m = metrik["sinif_metrikleri"][s]
        print(f"  {s:<8} kesinlik {m['kesinlik']:.2f}  duyarlılık {m['duyarlilik']:.2f}  "
              f"F1 {m['f1']:.2f}  ({m['adet']} görüntü)")
    print(f"\nÇıktılar: outputs/model_metrik.json · model_karmasiklik.png · gradcam/")


if __name__ == "__main__":
    main()
