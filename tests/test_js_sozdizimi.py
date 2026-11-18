"""Panel JavaScript'i sözdizimi açısından geçerli mi.

NEDEN VAR: Bu proje üç kez aynı hatayı yaşadı — panelin JS'ine bir
sözdizimi ya da yazım hatası girdi, Python testlerinin hepsi geçti,
panel kuruldu, dosya boyutu normaldi ve HATA ANCAK TARAYICIDA AÇINCA
GÖRÜLDÜ. Bir keresinde tek bir eksik parantez bütün paneli boş
bıraktı: on beş sekmenin hiçbiri çizilmedi.

Python tarafında 240 test vardı, JavaScript tarafında sıfır. Bu dosya
o boşluğun en ucuz kapatması: her JS dosyası `node --check` ile
ayrıştırılır. Çalıştırmaz, yalnızca ayrıştırır — saniyenin altında
sürer ve sözdizimi hatasının panele ulaşmasını imkânsız kılar.

node kurulu değilse testler atlanır; node bir ÖNKOŞUL değil.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

PANEL = Path(__file__).resolve().parent.parent / "src" / "panel"
JS = sorted((PANEL / "js").glob("*.js"))

node_yok = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node kurulu değil; sözdizimi denetimi atlandı")


def test_js_dosyalari_bulundu():
    assert JS, "src/panel/js altında .js dosyası yok"


@node_yok
@pytest.mark.parametrize("yol", JS, ids=lambda p: p.name)
def test_js_sozdizimi_gecerli(yol: Path):
    s = subprocess.run(["node", "--check", str(yol)],
                       capture_output=True, text=True, timeout=30)
    assert s.returncode == 0, f"{yol.name} ayrıştırılamadı:\n{s.stderr}"


@node_yok
def test_birlestirilmis_betik_de_gecerli(tmp_path: Path):
    """Dosyalar tek tek geçerli olsa da birleşince bozulabilir.

    Panel bütün JS'i tek bir <script> içinde birleştirdiği için asıl
    denetlenmesi gereken birleşmiş hâlidir: bir dosyanın sonundaki
    eksik parantez bir sonrakinin başını yutabilir.
    """
    birlesik = "\n".join(y.read_text(encoding="utf-8") for y in JS)
    # Veri yer tutucuları henüz JSON ile dolmadığı için geçerli birer
    # değişmez hâline getiriliyor; amaç sözdizimi, değer değil.
    for ad in ("MUS", "HASTALIK", "CERCO", "BELIRSIZ", "IZ", "DEPO",
               "BOCEK", "UYARI", "KARLILIK", "OLCUM", "ETKI", "COLLESME"):
        birlesik = birlesik.replace(f"__{ad}_JSON__", "null")
    yol = tmp_path / "birlesik.js"
    yol.write_text(birlesik, encoding="utf-8")
    s = subprocess.run(["node", "--check", str(yol)],
                       capture_output=True, text=True, timeout=30)
    assert s.returncode == 0, f"birleşik betik ayrıştırılamadı:\n{s.stderr}"


@node_yok
def test_uretilmis_panelin_betigi_gecerli(tmp_path: Path):
    """Üretilmiş mus_panel.html içindeki betik de ayrıştırılabilmeli.

    Bu, zincirin son halkası: yer tutucular JSON ile doldurulurken de
    bir şey bozulabilir (örneğin veride kaçırılmamış bir </script>).
    """
    import re
    panel = PANEL.parent.parent / "mus_panel.html"
    if not panel.exists():
        pytest.skip("mus_panel.html üretilmemiş")
    html = panel.read_text(encoding="utf-8")
    betikler = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    assert betikler, "panelde <script> bulunamadı"
    for i, b in enumerate(betikler):
        yol = tmp_path / f"panel{i}.js"
        yol.write_text(b, encoding="utf-8")
        s = subprocess.run(["node", "--check", str(yol)],
                           capture_output=True, text=True, timeout=30)
        assert s.returncode == 0, f"panel betiği {i} ayrıştırılamadı:\n{s.stderr}"
