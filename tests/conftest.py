"""
Ortak test hazırlıkları.

TEMİZ KLON SORUNU
-----------------
outputs/ klasörü .gitignore içindedir: üretilen hiçbir dosya depoda durmaz.
Yeni klonlanmış bir depoda o klasör boştur.

Bazı testler üretilmiş çıktıya bakar (panel gerçekten yazılıyor mu, JSON'lar
geçerli mi). Bu testler önce analizlerin çalışmış olmasını gerektirir. Hazırlık
yapılmazsa "benim makinemde geçiyordu" durumu oluşur: geliştiricide outputs/
dolu olduğu için testler geçer, temiz klonda kırılır.

Aşağıdaki fixture bunu önler: çıktıya ihtiyaç duyan testler bunu ister,
analizler oturum başına bir kez çalışır.
"""

from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "outputs"

GEREKLI = ("mus.json", "mus_toprak.json", "mus_hastalik.json",
           "mus_belirsizlik.json", "mus_iz.json")


@pytest.fixture(scope="session")
def ciktilar():
    """Analiz çıktılarının var olduğunu garanti eder; yoksa üretir."""
    eksik = [a for a in GEREKLI if not (CIKTI / a).exists()]
    if eksik:
        import mus_panel_uret
        mus_panel_uret.hepsini_calistir()

    hala_eksik = [a for a in GEREKLI if not (CIKTI / a).exists()]
    assert not hala_eksik, f"analizler çalıştı ama çıktı yok: {hala_eksik}"
    return CIKTI


@pytest.fixture(scope="session")
def panel(ciktilar):
    """Panelin üretilmiş olduğunu garanti eder."""
    import mus_panel_uret
    mus_panel_uret.main()
    hedef = KOK / "mus_panel.html"
    assert hedef.exists(), "panel üretilmedi"
    return hedef
