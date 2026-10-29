"""
AGROMATCH - Ambar sıcaklığı ve depo zararlısının gelişme penceresi
===================================================================
SORU
Isıtılmamış bir Muş ambarında buğday biti yılın kaç ayı gelişebiliyor?

Bu soru Muş için özellikle anlamlı: il soğuk, ve depo zararlılarının hepsinin
bir gelişme eşiği var. Eşik yeterince uzun süre aşılmıyorsa, soğuk tek başına
bir mücadele aracıdır — kalıntısız, dirençsiz, bedava.

NAİF HATA
"Muş soğuk, o hâlde depoda sorun olmaz" demek yanlıştır. Tahıl yığını büyük
bir ısı deposudur: dışarısı -8 °C'ye inerken yığının ortası haftalarca
ılık kalır. Yığın dış havayı GECİKMELİ ve ZAYIFLAYARAK takip eder. Bu modülün
yaptığı iş, o gecikmeyi ve zayıflamayı hesaba katmaktır.

MODEL
Aylık yığın sıcaklığı, dış hava sıcaklığının üstel yumuşatmasıdır:

    T_yığın[ay] = α · T_hava[ay] + (1 − α) · T_yığın[ay−1]

α küçüldükçe yığın daha çok direnir (daha büyük kütle, daha iyi yalıtım).
Döngü yıl boyunca tekrarlandığı için denge durumuna kadar yinelenir.

α BİR VARSAYIMDIR. Yığın yüksekliğine, depo yalıtımına ve havalandırmaya
göre değişir; ölçülmeden kesinleşmez. Varsayılan 0,35 orta büyüklükte,
havalandırmasız bir ambar içindir. Ambara bir veri kaydedici (data logger)
konursa bu katsayı ölçümle yerine oturur — ve bu, hocaya önerilebilecek
en ucuz deneylerden biridir.

NESİL SAYISI BİLEREK HESAPLANMIYOR
Bir neslin tamamlanması için gereken derece-gün literatürde vardır ama
türe ve çalışmaya göre değişir. Uydurulmuş bir sayıyla nesil hesaplamak
yerine, modül derece-günü verir ve nesil sayısını ancak danışman hocadan
gelen değerle hesaplar (`nesil_sayisi`). Bilinmeyen bir sayıyı doldurmak
yerine boş bırakmak, bu projenin baştan beri tuttuğu çizgi.

    python src/depo/ambar_sicaklik.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import mus_iklim
import mus_profil as mp
from depo.depo_profil import ZARARLILAR

KOK = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK / "outputs"

# Yığının dış havayı ne kadar hızlı takip ettiği. VARSAYIM — bkz. modül başlığı.
SONUMLEME = 0.35

AY_GUN = mus_iklim.AY_GUN
AY_AD = mus_iklim.AY_AD


def ambar_sicakligi(ilce: str, alfa: float = SONUMLEME) -> list[float]:
    """Aylık yığın sıcaklığı (°C), dış havadan türetilir.

    Denge durumuna yakınsaması için yıl birkaç kez yinelenir; böylece
    ocak ayının değeri bir önceki aralıktan etkilenmiş olur (gerçekte de
    öyledir — yığın yıl başında sıfırlanmaz).
    """
    hava = mus_iklim.aylik_sicaklik(ilce)
    yigin = list(hava)
    for _ in range(6):                      # yaklaşık denge için yeterli
        for i in range(12):
            onceki = yigin[(i - 1) % 12]
            yigin[i] = alfa * hava[i] + (1 - alfa) * onceki
    return [round(t, 1) for t in yigin]


def gelisme_penceresi(ilce: str, taban: float,
                      alfa: float = SONUMLEME) -> dict[str, Any]:
    """Bir eşiğin üstünde geçen süre ve biriken derece-gün."""
    yigin = ambar_sicakligi(ilce, alfa)
    aylar = [i for i, t in enumerate(yigin) if t > taban]
    derece_gun = sum((yigin[i] - taban) * AY_GUN[i] for i in aylar)
    return dict(
        ilce=ilce, taban=taban,
        aylik_yigin=yigin,
        elverisli_aylar=[AY_AD[i] for i in aylar],
        elverisli_ay_sayisi=len(aylar),
        derece_gun=round(derece_gun),
        en_sicak_ay=AY_AD[max(range(12), key=lambda i: yigin[i])],
        en_sicak=max(yigin), en_soguk=min(yigin),
    )


def nesil_sayisi(derece_gun: float, derece_gun_nesil: float) -> float:
    """Yılda kaç nesil.

    derece_gun_nesil danışman hocadan gelmelidir: bir neslin tamamlanması
    için gereken birikimli derece-gün. Bu sayı modülde SAKLI DEĞİL çünkü
    literatürde tek bir değeri yok; varsayılan koymak, kaynağı olmayan bir
    sayıyı gerçek gibi göstermek olurdu.
    """
    if derece_gun_nesil <= 0:
        raise ValueError("derece_gun_nesil pozitif olmalı")
    return round(derece_gun / derece_gun_nesil, 2)


def analiz(alfa: float = SONUMLEME) -> dict[str, Any]:
    """Altı ilçe × sekiz zararlı için gelişme penceresi."""
    satirlar = []
    for ilce in mp.ILCE:
        for z in ZARARLILAR:
            p = gelisme_penceresi(ilce, float(z["taban_sicaklik"]), alfa)
            satirlar.append(dict(
                ilce=ilce, zararli=z["ad"], tur=z["tur"],
                taban_sicaklik=z["taban_sicaklik"],
                elverisli_ay=p["elverisli_ay_sayisi"],
                aylar=p["elverisli_aylar"],
                derece_gun=p["derece_gun"],
                ic_besleyen=z["ic_besleyen"],
                karantina=z["karantina"],
                onem=z["onem"]))

    ornek = {ilce: ambar_sicakligi(ilce, alfa) for ilce in mp.ILCE}
    return dict(sonumleme=alfa, satirlar=satirlar, aylik_yigin=ornek,
                dis_hava={i: mus_iklim.aylik_sicaklik(i) for i in mp.ILCE},
                not_=("sonumleme bir VARSAYIMDIR; ambara veri kaydedici "
                      "konarak ölçülmelidir. elverisli_ay ve derece_gun "
                      "ona duyarlıdır."))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sonumleme", type=float, default=SONUMLEME,
                    help="yığının dış havayı takip hızı (0–1)")
    ap.add_argument("--derece-gun-nesil", type=float, default=None,
                    help="bir nesil için gereken derece-gün (hocadan gelecek)")
    a = ap.parse_args()

    sonuc = analiz(a.sonumleme)

    print(f"AMBAR SICAKLIĞI — sönümleme {a.sonumleme}\n")
    print(f"{'ilçe':<12}" + "".join(f"{ad:>6}" for ad in AY_AD))
    for ilce in mp.ILCE:
        dis = sonuc["dis_hava"][ilce]
        yig = sonuc["aylik_yigin"][ilce]
        print(f"{ilce + ' (dış)':<12}" + "".join(f"{t:>6.1f}" for t in dis))
        print(f"{'  yığın':<12}" + "".join(f"{t:>6.1f}" for t in yig))
    print()

    bugday_biti = next(z for z in ZARARLILAR if z["tur"] == "Sitophilus granarius")
    taban = float(bugday_biti["taban_sicaklik"])
    print(f"BUĞDAY BİTİ — gelişme eşiği {taban} °C\n")
    print(f"{'ilçe':<12}{'elverişli ay':>14}{'derece-gün':>12}  aylar")
    for ilce in mp.ILCE:
        p = gelisme_penceresi(ilce, taban, a.sonumleme)
        print(f"{ilce:<12}{p['elverisli_ay_sayisi']:>14}{p['derece_gun']:>12}"
              f"  {', '.join(p['elverisli_aylar'])}")

    if a.derece_gun_nesil:
        print(f"\nNesil sayısı (nesil başına {a.derece_gun_nesil} derece-gün):")
        for ilce in mp.ILCE:
            p = gelisme_penceresi(ilce, taban, a.sonumleme)
            n = nesil_sayisi(p["derece_gun"], a.derece_gun_nesil)
            print(f"  {ilce:<12} {n:>5.2f} nesil/yıl")
    else:
        print("\n  Nesil sayısı hesaplanmadı: nesil başına derece-gün bilinmiyor.")
        print("  Danışman hocadan bu sayı gelince --derece-gun-nesil ile verilir.")

    print("\nTÜRLERE GÖRE ELVERİŞLİ AY (Merkez)")
    for z in sorted(ZARARLILAR, key=lambda z: z["taban_sicaklik"]):
        p = gelisme_penceresi("Merkez", float(z["taban_sicaklik"]), a.sonumleme)
        isaret = " ← KARANTİNA" if z["karantina"] else ""
        print(f"  {z['ad']:<22} eşik {z['taban_sicaklik']:>4.1f} °C  "
              f"{p['elverisli_ay_sayisi']:>2} ay  "
              f"{p['derece_gun']:>5} derece-gün{isaret}")

    CIKTI.mkdir(exist_ok=True)
    (CIKTI / "depo_ambar.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{CIKTI / 'depo_ambar.json'} yazıldı")


if __name__ == "__main__":
    main()
