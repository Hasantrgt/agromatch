"""
AGROMATCH - Sentetik şeker pancarı yaprağı üretici
==================================================
NEDEN SENTETİK GÖRÜNTÜ?
Saha fotoğrafları toplanana kadar görüntü işleme hattının doğru çalıştığını
kanıtlamanın tek yolu, lekelerin yerini ve boyutunu ÖNCEDEN bildiğimiz
görüntüler üretmektir. Böylece algoritmanın bulduğu lekeler gerçek lekelerle
karşılaştırılabilir (duyarlılık / kesinlik ölçülebilir).

Üretilen yaprak bilinçli olarak zorlaştırılmıştır:
  - toprak zemin (yaprağın arka plandan ayrılması gerekir)
  - ana damar ve yan damarlar (lekeyle karıştırılabilir)
  - azot eksikliği sarılığı (geniş, soluk lekeler — hastalık DEĞİL)
  - toz ve toprak zerreleri (küçük koyu noktalar — hastalık DEĞİL)
Algoritma bunları elemeyi başarmalıdır.

Cercospora beticola lekesinin gerçek görünümü:
  3–5 mm çapında yuvarlak leke, açık gri merkez, kırmızı-kahverengi halka,
  merkezde iğne ucu kadar siyah noktacıklar (konidi yatakları).

Kullanım:
    python src/goruntu/sentetik_yaprak.py --adet 12 --cikti data/sentetik
"""

import argparse
import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

KOK = Path(__file__).resolve().parent.parent.parent
GEN, YUK = 640, 480


def _zemin(rng):
    """Toprak zemin: kahverengi, gürültülü."""
    taban = np.zeros((YUK, GEN, 3), np.float32)
    taban[..., 0] = 96; taban[..., 1] = 78; taban[..., 2] = 60
    gurultu = rng.normal(0, 14, (YUK, GEN, 1))
    taban += gurultu
    return np.clip(taban, 0, 255)


def _yaprak_maskesi():
    """Dalgalı kenarlı, geniş pancar yaprağı silueti."""
    y, x = np.mgrid[0:YUK, 0:GEN]
    cx, cy = GEN / 2, YUK / 2
    dx, dy = (x - cx) / 262.0, (y - cy) / 196.0
    aci = np.arctan2(dy, dx)
    yaricap = np.sqrt(dx ** 2 + dy ** 2)
    dalga = 1 + 0.065 * np.sin(7 * aci) + 0.032 * np.sin(13 * aci + 1.1)
    return yaricap <= dalga


def _yaprak_dokusu(rng, maske):
    """Yeşil gövde, damarlar ve azot sarılığı."""
    kat = np.zeros((YUK, GEN, 3), np.float32)
    y, x = np.mgrid[0:YUK, 0:GEN]
    # taban yeşil + dikey gradyan
    kat[..., 0] = 66 + (y / YUK) * 18
    kat[..., 1] = 112 + (y / YUK) * 22
    kat[..., 2] = 48 + (y / YUK) * 10
    kat += rng.normal(0, 6, (YUK, GEN, 1))

    gorsel = Image.fromarray(np.clip(kat, 0, 255).astype(np.uint8))
    ciz = ImageDraw.Draw(gorsel)
    cx, cy = GEN / 2, YUK / 2
    # ana damar
    ciz.line([(cx - 250, cy + 6), (cx + 250, cy - 4)], fill=(150, 175, 110), width=9)
    # yan damarlar
    for k in range(-5, 6):
        if k == 0:
            continue
        bas = (cx + k * 42, cy + (6 if k < 0 else -4))
        son = (cx + k * 52, cy + math.copysign(150, k % 2 - 0.5) * (1 - abs(k) / 9))
        ciz.line([bas, son], fill=(138, 163, 102), width=4)
    gorsel = gorsel.filter(ImageFilter.GaussianBlur(1.1))
    kat = np.asarray(gorsel).astype(np.float32)

    # azot eksikliği sarılığı: geniş, soluk, kenarsız (hastalık değil)
    for _ in range(2):
        sx, sy = rng.integers(140, GEN - 140), rng.integers(110, YUK - 110)
        r = rng.integers(55, 95)
        d2 = (x - sx) ** 2 + (y - sy) ** 2
        g = np.exp(-d2 / (2 * (r / 1.6) ** 2))[..., None]
        kat = kat * (1 - 0.45 * g) + np.array([188, 186, 92], np.float32) * (0.45 * g)
    return kat


def _leke_ciz(gorsel, x, y, r, rng):
    """Tek bir Cercospora lekesi: gri merkez, kırmızı-kahve halka, siyah noktacıklar."""
    ciz = ImageDraw.Draw(gorsel, "RGBA")
    ciz.ellipse([x - r, y - r, x + r, y + r], fill=(132, 62, 46, 235))          # halka
    ic = max(1.5, r * 0.62)
    ciz.ellipse([x - ic, y - ic, x + ic, y + ic], fill=(176, 170, 150, 240))    # gri merkez
    for _ in range(int(rng.integers(2, 6))):                                     # konidi yatakları
        nx = x + rng.uniform(-ic * 0.6, ic * 0.6)
        ny = y + rng.uniform(-ic * 0.6, ic * 0.6)
        ciz.ellipse([nx - 1, ny - 1, nx + 1, ny + 1], fill=(52, 46, 42, 255))


def yaprak_uret(tohum, leke_sayisi=None):
    rng = np.random.default_rng(tohum)
    maske = _yaprak_maskesi()
    zemin = _zemin(rng)
    doku = _yaprak_dokusu(rng, maske)
    birlesik = np.where(maske[..., None], doku, zemin)
    gorsel = Image.fromarray(np.clip(birlesik, 0, 255).astype(np.uint8))

    # Lekeleri yaprağın iç kısmına yerleştir (kenardan uzak)
    ic_maske = _yaprak_maskesi()
    adet = int(leke_sayisi if leke_sayisi is not None else rng.integers(6, 26))
    gercek = []
    deneme = 0
    while len(gercek) < adet and deneme < adet * 60:
        deneme += 1
        x = int(rng.integers(70, GEN - 70)); y = int(rng.integers(60, YUK - 60))
        r = float(rng.uniform(4.5, 11.0))
        if not ic_maske[y, x]:
            continue
        if any((x - gx) ** 2 + (y - gy) ** 2 < (r + gr + 6) ** 2 for gx, gy, gr in gercek):
            continue
        _leke_ciz(gorsel, x, y, r, rng)
        gercek.append((x, y, r))

    # Yanıltıcılar: toz zerreleri (küçük ve koyu, leke değil)
    ciz = ImageDraw.Draw(gorsel)
    for _ in range(int(rng.integers(5, 12))):
        x, y = int(rng.integers(60, GEN - 60)), int(rng.integers(50, YUK - 50))
        if not ic_maske[y, x]:
            continue
        rr = rng.uniform(1.2, 2.4)
        ciz.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(58, 50, 44))

    gorsel = gorsel.filter(ImageFilter.GaussianBlur(0.6))
    return gorsel, [dict(x=g[0], y=g[1], r=round(g[2], 2)) for g in gercek]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adet", type=int, default=12)
    ap.add_argument("--cikti", default="data/sentetik")
    a = ap.parse_args()

    hedef = KOK / a.cikti
    hedef.mkdir(parents=True, exist_ok=True)
    kayit = []
    for i in range(a.adet):
        # şiddet basamakları: temizden ağıra
        sayi = [0, 3, 6, 10, 14, 18, 22, 27, 32, 38, 44, 52][i % 12]
        gorsel, gercek = yaprak_uret(1000 + i, sayi)
        ad = f"yaprak_{i:02d}.png"
        gorsel.save(hedef / ad)
        kayit.append(dict(dosya=ad, leke_sayisi=len(gercek), lekeler=gercek))
        print(f"{ad}: {len(gercek)} leke")
    (hedef / "gercek_degerler.json").write_text(
        json.dumps(kayit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{a.adet} görüntü ve gerçek değerler yazıldı -> {hedef}")


if __name__ == "__main__":
    main()
