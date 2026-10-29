"""
AGROMATCH - Hastalıkların bulaş kaynağı
========================================
Projenin ikinci ve üçüncü kısmının sınırı burada çizilir: ikinci kısım
TOPRAKTAN gelen sorunlarla, üçüncü kısım BÖCEKTEN gelenlerle ilgilenir.
Bir hastalığı hangi kısma koyacağımız, onu neyin taşıdığına bağlı.

Dört kaynak ayırıyoruz:

    toprak   patojen toprakta, anızda ya da yumruda kışlar; kök veya kök
             boğazından girer. Ekim nöbeti, drenaj ve toprak işleme
             doğrudan etkiler — yani TOPRAK ANALİZİ bu gruba konuşur.
    tohum    patojen tohumun içinde ya da üstünde taşınır. Çözüm tohum
             ilaçlaması ve sertifikalı tohum; toprak analizi bir şey
             söylemez.
    hava     spor rüzgârla gelir. Kaynak çoğu zaman komşu tarla ya da
             anız. Çözüm dayanıklı çeşit ve zamanında yaprak ilacı.
    bocek    patojeni bir böcek taşır (vektör). Böceği durdurmadan
             hastalığı durduramazsınız — bu yüzden ÜÇÜNCÜ KISMA aittir.

Bir hastalığın birden çok yolu olabilir; ``ikincil`` alanı bunu tutar.
Birincil kaynak, Muş koşullarında hangi yolun yönetim kararını belirlediği
düşünülerek seçilmiştir.

UYARI: Buradaki atamalar fitopatoloji literatürüne dayanır, Bakanlık
belgelerinden tek tek DOĞRULANMAMIŞTIR. Danışman hocanın gözden
geçirmesi gereken bir listedir.
"""

from __future__ import annotations

from typing import Any

import mus_hastalik_profil as hp

KAYNAKLAR = ("toprak", "tohum", "hava", "bocek")

KAYNAK_ACIKLAMA = {
    "toprak": "toprakta, anızda ya da yumruda kışlar; kökten girer",
    "tohum": "tohumun içinde ya da üstünde taşınır",
    "hava": "spor rüzgârla gelir",
    "bocek": "bir böcek taşır (vektör)",
}

# (ürün, hastalık) -> (birincil kaynak, ikincil kaynaklar)
ATAMA: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = {
    # ------------------------------------------------------------ Buğday
    ("Buğday", "Sarı pas"): ("hava", ()),
    ("Buğday", "Kahverengi pas"): ("hava", ()),
    ("Buğday", "Kara pas"): ("hava", ()),
    ("Buğday", "Septoria yaprak lekesi"): ("hava", ("toprak",)),
    ("Buğday", "Sürme"): ("tohum", ("toprak",)),
    ("Buğday", "Açık rastık"): ("tohum", ()),
    ("Buğday", "Kök ve kökboğazı çürüklüğü"): ("toprak", ("tohum",)),
    ("Buğday", "Külleme"): ("hava", ()),
    ("Buğday", "Kar küfü"): ("toprak", ("tohum",)),
    ("Buğday", "Arpa sarı cücelik virüsü (BYDV)"): ("bocek", ()),
    # -------------------------------------------------------------- Arpa
    ("Arpa", "Arpa yaprak lekesi (kav)"): ("hava", ("tohum", "toprak")),
    ("Arpa", "Ağ lekesi"): ("hava", ("tohum", "toprak")),
    ("Arpa", "Külleme"): ("hava", ()),
    ("Arpa", "Kapalı rastık"): ("tohum", ()),
    ("Arpa", "Yarı açık rastık"): ("tohum", ()),
    ("Arpa", "Kök ve kökboğazı çürüklüğü"): ("toprak", ("tohum",)),
    ("Arpa", "Arpa sarı cücelik virüsü (BYDV)"): ("bocek", ()),
    # ----------------------------------------------------- Şeker pancarı
    ("Şeker pancarı", "Cercospora yaprak lekesi"): ("hava", ("toprak",)),
    # Rizomani'nin vektörü Polymyxa betae; bir BÖCEK değil, toprakta
    # yaşayan bir organizma. Bu yüzden ikinci kısma ait.
    ("Şeker pancarı", "Rizomani"): ("toprak", ()),
    ("Şeker pancarı", "Kök çürüklüğü (Rhizoctonia)"): ("toprak", ()),
    ("Şeker pancarı", "Fide çökerten"): ("toprak", ()),
    ("Şeker pancarı", "Külleme"): ("hava", ()),
    ("Şeker pancarı", "Pancar pası"): ("hava", ()),
    ("Şeker pancarı", "Fusarium sarılığı ve kök çürüklüğü"): ("toprak", ()),
    # ----------------------------------------------------------- Patates
    ("Patates", "Mildiyö (geç yanıklık)"): ("hava", ("toprak",)),
    ("Patates", "Erken yanıklık"): ("hava", ("toprak",)),
    ("Patates", "Siyah siğil (kökboğazı nekrozu)"): ("toprak", ("tohum",)),
    ("Patates", "Kuru çürüklük"): ("toprak", ("tohum",)),
    ("Patates", "Adi uyuz"): ("toprak", ()),
    ("Patates", "Bakteriyel yumuşak çürüklük (karabacak)"): ("toprak", ("tohum",)),
    ("Patates", "Patates halka çürüklüğü"): ("tohum", ()),
    ("Patates", "Bakteriyel solgunluk (kahverengi çürüklük)"): ("toprak", ("tohum",)),
    ("Patates", "Patates siğili"): ("toprak", ()),
    ("Patates", "Patates Y virüsü (PVY)"): ("bocek", ("tohum",)),
    ("Patates", "Patates yaprak kıvrılma virüsü (PLRV)"): ("bocek", ("tohum",)),
    # ------------------------------------------------------ Kuru fasulye
    ("Kuru fasulye", "Fasulye antraknozu"): ("tohum", ("hava",)),
    ("Kuru fasulye", "Fasulye adi yaprak yanıklığı"): ("tohum", ("hava",)),
    ("Kuru fasulye", "Fasulye hale yanıklığı"): ("tohum", ("hava",)),
    ("Kuru fasulye", "Fasulye kök çürüklüğü"): ("toprak", ()),
    ("Kuru fasulye", "Fasulye pası"): ("hava", ()),
    ("Kuru fasulye", "Fasulye adi mozaik virüsü"): ("tohum", ("bocek",)),
    ("Kuru fasulye", "Fasulye sarı mozaik virüsü"): ("bocek", ()),
    # ---------------------------------------------------- Silajlık mısır
    ("Silajlık mısır", "Mısır yaprak yanıklığı"): ("hava", ("toprak",)),
    ("Silajlık mısır", "Mısır rastığı"): ("toprak", ("hava",)),
    ("Silajlık mısır", "Mısır pası"): ("hava", ()),
    ("Silajlık mısır", "Kök ve kökboğazı çürüklüğü"): ("toprak", ()),
    # ------------------------------------------------------------ Yonca
    ("Yonca", "Yonca yaprak lekesi"): ("hava", ("toprak",)),
    ("Yonca", "Yonca pası"): ("hava", ()),
    ("Yonca", "Yonca külleme"): ("hava", ()),
    ("Yonca", "Kök ve kök boğazı çürüklüğü"): ("toprak", ()),
    ("Yonca", "Phytophthora kök çürüklüğü"): ("toprak", ()),
    ("Yonca", "Sclerotinia kök boğazı çürüklüğü"): ("toprak", ()),
    # ---------------------------------------------------------- Korunga
    ("Korunga", "Korunga külleme"): ("hava", ()),
    ("Korunga", "Korunga pası"): ("hava", ()),
    ("Korunga", "Kök ve kök boğazı çürüklüğü"): ("toprak", ()),
    # -------------------------------------------------------------- Fiğ
    ("Fiğ", "Fiğ askokitası"): ("tohum", ("hava", "toprak")),
    ("Fiğ", "Fiğ pası"): ("hava", ()),
    ("Fiğ", "Fiğ küllemesi"): ("hava", ()),
    ("Fiğ", "Kök çürüklüğü"): ("toprak", ()),
}

# Hangi kısma ait: toprak/tohum/hava ikinci kısım, böcek üçüncü kısım
KISIM = {"toprak": 2, "tohum": 2, "hava": 2, "bocek": 3}


def kaynak(urun: str, ad: str) -> str:
    return ATAMA[(urun, ad)][0]


def ikincil(urun: str, ad: str) -> tuple[str, ...]:
    return ATAMA[(urun, ad)][1]


def zenginlestir() -> list[dict[str, Any]]:
    """Hastalık kataloğunu bulaş kaynağı alanlarıyla birlikte döndürür.

    Katalog dosyasına DOKUNMUYORUZ. O dosyadaki eşikler kalibre edilmiş
    durumda ve daha önce bir kez farkında olmadan kaymıştı; bu yüzden
    sınıflama ayrı dosyada duruyor ve katalogla yalnızca okuma yoluyla
    birleşiyor.
    """
    cikti = []
    for h in hp.HASTALIKLAR:
        k = kaynak(h["urun"], h["ad"])
        cikti.append({**h, "bulas": k,
                      "bulas_ikincil": list(ikincil(h["urun"], h["ad"])),
                      "kisim": KISIM[k]})
    return cikti


def ozet() -> dict[str, Any]:
    from collections import Counter
    z = zenginlestir()
    sayac = Counter(h["bulas"] for h in z)
    urun_kaynak: dict[str, dict[str, int]] = {}
    for h in z:
        urun_kaynak.setdefault(h["urun"], dict.fromkeys(KAYNAKLAR, 0))
        urun_kaynak[h["urun"]][h["bulas"]] += 1
    return {
        "toplam": len(z),
        "kaynak": {k: sayac.get(k, 0) for k in KAYNAKLAR},
        "kisim": {2: sum(1 for h in z if h["kisim"] == 2),
                  3: sum(1 for h in z if h["kisim"] == 3)},
        "urun_kaynak": urun_kaynak,
        "ikincil_bocek": [f'{h["urun"]} · {h["ad"]}' for h in z
                          if "bocek" in h["bulas_ikincil"]],
    }


def denetle() -> list[str]:
    """Sınıflama ile katalog birbirini tutuyor mu."""
    hata = []
    katalog = {(h["urun"], h["ad"]) for h in hp.HASTALIKLAR}
    for anahtar in katalog - set(ATAMA):
        hata.append(f"sınıflanmamış hastalık: {anahtar[0]} · {anahtar[1]}")
    for anahtar in set(ATAMA) - katalog:
        hata.append(f"katalogda olmayan atama: {anahtar[0]} · {anahtar[1]}")
    for (urun, ad), (birincil, ikincil_) in ATAMA.items():
        if birincil not in KAYNAKLAR:
            hata.append(f"{urun} · {ad}: bilinmeyen kaynak {birincil}")
        if birincil in ikincil_:
            hata.append(f"{urun} · {ad}: birincil kaynak ikincilde tekrar ediyor")
        for i in ikincil_:
            if i not in KAYNAKLAR:
                hata.append(f"{urun} · {ad}: bilinmeyen ikincil kaynak {i}")
    return hata


if __name__ == "__main__":
    for h in denetle():
        print("HATA:", h)
    o = ozet()
    print(f"{o['toplam']} hastalık")
    for k, n in o["kaynak"].items():
        print(f"  {k:8s} {n:>3}   {KAYNAK_ACIKLAMA[k]}")
    print(f"\n2. kısım (toprak/tohum/hava): {o['kisim'][2]}")
    print(f"3. kısım (böcek taşıyan)     : {o['kisim'][3]}")
    print("\nİkincil yolu böcek olanlar (üçüncü kısım da ilgilenmeli):")
    for a in o["ikincil_bocek"]:
        print("  " + a)
