"""
AGROMATCH - Sentetik sınıflandırma veri seti
============================================
Eğitim hattını saha fotoğrafları gelmeden sınamak için, şiddet sınıflarına
ayrılmış bir görüntü kümesi üretir.

    temiz  : 0–2 leke    (hastalık yok ya da ilk belirti)
    hafif  : 4–14 leke   (ilaçlama eşiği civarı)
    agir   : 25–60 leke  (gecikmiş / ağır enfeksiyon)

Bu veri seti modelin GERÇEK başarısını ölçmez — sentetik görüntüler gerçek
yaprağın dokusunu, ışığını ve gölgesini taşımaz. Ölçtüğü şey şudur:
eğitim döngüsü, veri yükleyici, metrikler ve Grad-CAM uçtan uca çalışıyor mu?
Saha fotoğrafları geldiğinde aynı komut, aynı klasör yapısıyla çalışacak.

Kullanım:
    python src/goruntu/veri_seti_uret.py --sinif-basina 100
    python src/goruntu/goruntu_hazirla.py --kok data/goruntu_sentetik --bol
"""

import argparse
from pathlib import Path

from sentetik_yaprak import yaprak_uret

KOK = Path(__file__).resolve().parent.parent.parent
SINIFLAR = {"temiz": (0, 2), "hafif": (4, 14), "agir": (25, 60)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sinif-basina", type=int, default=100)
    ap.add_argument("--cikti", default="data/goruntu_sentetik")
    a = ap.parse_args()

    import numpy as np
    rng = np.random.default_rng(7)
    hedef = KOK / a.cikti
    for sinif, (alt, ust) in SINIFLAR.items():
        klasor = hedef / sinif
        klasor.mkdir(parents=True, exist_ok=True)
        for i in range(a.sinif_basina):
            adet = int(rng.integers(alt, ust + 1))
            gorsel, _ = yaprak_uret(tohum=hash((sinif, i)) % 10_000_000, leke_sayisi=adet)
            gorsel.save(klasor / f"{sinif}_{i:03d}.jpg", quality=88)
        print(f"{sinif:<7} {a.sinif_basina} görüntü ({alt}–{ust} leke)")
    print(f"\nToplam {a.sinif_basina * len(SINIFLAR)} görüntü -> {hedef}")


if __name__ == "__main__":
    main()
