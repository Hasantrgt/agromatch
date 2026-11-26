"""BULGULAR.md içindeki sayılar koddan sapmasın.

NEDEN VAR: Bir bulgu belgesi, yazıldığı günün çıktısıyla doğrudur. Kod
değişince belge sessizce yanlışa döner ve en kötü yerde — hocaya ya da
jüriye gösterilen yerde — yanlış olur.

Bu test belgeyi okur ve içindeki yük taşıyan her sayıyı canlı modülden
hesaplanan değerle karşılaştırır. Sayı değişmişse test kırılır; o zaman
belge güncellenir ya da değişikliğin kendisi gözden geçirilir.

Belgedeki sayı biçimi Türkçedir (binlik nokta, ondalık virgül); karşılaştırma
da o biçimde yapılır.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import cati
import mus_analiz as ma
import mus_profil as mp
from bocek import karar as bkarar
from depo import karar as dkarar

KOK = Path(__file__).resolve().parent.parent
BELGE = KOK / "BULGULAR.md"
CIKTI = KOK / "outputs"


@pytest.fixture(scope="module")
def metin() -> str:
    assert BELGE.exists(), "BULGULAR.md yok"
    return BELGE.read_text(encoding="utf-8")


def tr(x: float, basamak: int = 0) -> str:
    """Belgedeki Türkçe sayı biçimi."""
    gov = f"{x:,.{basamak}f}"
    return gov.replace(",", " ").replace(".", ",").replace(" ", ".")


def _var(metin: str, parca: str, nicin: str) -> None:
    assert parca in metin, f"BULGULAR.md: '{parca}' yok — {nicin}"


def _cikti(ad: str) -> dict:
    yol = CIKTI / ad
    if not yol.exists():
        pytest.skip(f"{ad} üretilmemiş")
    return json.loads(yol.read_text(encoding="utf-8"))


# ------------------------------------------------------------- kapsam
def test_kapsam_sayilari(metin: str):
    alan = sum(v[0] for i in mp.ILCE for u, v in mp.DESEN[i].items() if u in mp.URUN)
    _var(metin, tr(alan), "il ekili alanı")
    _var(metin, f"{len(mp.ILCE)} (Merkez", "ilçe sayısı")


# --------------------------------------------------------------- çatı
def test_munavebe_sayilari(metin: str):
    o = cati.ozet()
    s = o["durum_sayilari"]
    _var(metin, f"| kırar | **{s['kırar']}** |", "kıran çift sayısı")
    _var(metin, f"| kırmaz | {s['kırmaz']} |", "kırmayan çift sayısı")
    _var(metin, f"| belirsiz | {s['belirsiz']} |", "belirsiz çift sayısı")
    _var(metin, f"{o['cift']} çift", "toplam çift sayısı")


def test_baskin_cift_sayilari(metin: str):
    en = cati.baskin_ciftler(1)[0]
    _var(metin, "%" + tr(100 * en["alan_payi"], 1), "buğday+arpa alan payı")
    for e in en["tur_ortak"]:
        _var(metin, e, "baskın çiftin ortak etkeni")


def test_pancar_tavani_sayilari(metin: str):
    t = cati.pancar_tavani()
    _var(metin, tr(t["pancar_alan_dekar"]), "pancar bugünkü alan")
    _var(metin, tr(t["pancar_tavan_dekar"]), "pancar tavanı")
    _var(metin, tr(t["bos_alan_dekar"]), "pancar boşluğu")
    _var(metin, "%" + tr(100 * t["tavandaki_pay"], 1), "tavanın il payı")


# ---------------------------------------------------------- tüketim
def test_tuketim_olcumleri(metin: str):
    for urun, deger in mp.GIDA_IHTIYAC.items():
        basamak = 4 if deger < 0.01 else (4 if deger < 0.2 else 3)
        _var(metin, tr(deger, basamak).rstrip("0").rstrip(","),
             f"{urun} kişi başı tüketim")


# ------------------------------------------------------------ denge
def test_karsilama_oranlari(metin: str):
    iz = _cikti("mus_iz.json")
    for s in iz["sorular"]:
        o = s["oran"]
        _var(metin, tr(o["medyan"], 2), f"{s['baslik']} karşılama medyanı")
        _var(metin, f"{tr(o['alt90'], 2)} – {tr(o['ust90'], 2)}",
             f"{s['baslik']} %90 aralığı")


def test_merkez_yem_acigi(metin: str):
    y = ma.yem_bilancosu("Merkez")
    assert not y["yonca_ile_kapanir"], "Merkez artık ekimle kapanıyorsa belge yanlış"
    _var(metin, tr(y["acik_ton"]), "Merkez yem açığı")
    _var(metin, tr(y["ek_yonca_dekar"]), "Merkez gereken ek yonca")
    _var(metin, tr(y["ekili_alan_dekar"]), "Merkez ekili alan")


# ----------------------------------------------------- veri kalitesi
def test_veri_kalitesi_sayilari(metin: str):
    k = _cikti("veri_kalitesi.json")
    _var(metin, tr(k["n_satir"]), "laboratuvar satır sayısı")
    _var(metin, tr(k["ozet"]["modele_giren_satir"]), "modele giren satır")
    bulgu = {d["ad"]: d for d in k["denetim"]}
    _var(metin, tr(bulgu["Yer sütunu"]["bulgu"]), "yer sütunu kusuru")
    _var(metin, tr(bulgu["Yinelenen satırlar"]["bulgu"]), "yinelenen satır")
    pk = bulgu["Fosfor ve potasyum birimi"]
    _var(metin, tr(pk["bulgu"]), "P/K sapan satır")
    _var(metin, tr(pk["toplam"]), "P/K karşılaştırılabilir satır")


# ------------------------------------------------------- doğrulama
def test_soilgrids_sayilari(metin: str):
    d = _cikti("toprak_dogrulama.json")
    _var(metin, tr(d["nokta_sorgusu"]), "SoilGrids nokta sorgusu")
    _var(metin, str(d["ozet"]["karsilastirma"]), "karşılaştırma sayısı")
    _var(metin, str(d["ozet"]["tutan"]), "tutan karşılaştırma")


def test_kil_sinif_sayilari(metin: str):
    k = _cikti("kil_etkisi.json")
    for c in k["karsilastirmalar"]:
        _var(metin, f"| {c['degisen_satir']} | {c['sinif_degisen']} |"
             if c["sinif_degisen"] != 1 else
             f"| {c['degisen_satir']} | **{c['sinif_degisen']}** |",
             f"{c['ad']} satır/sınıf sayıları")


def test_olcum_etkisi_sayilari(metin: str):
    e = _cikti("olcum_etkisi.json")["ozet"]
    _var(metin, f"{e['toplam_satir']} uygunluk satırının {e['olcumlu_satir']}",
         "uygunluk satır / ölçümlü satır")
    _var(metin, tr(e["ortalama_mutlak_fark"], 1), "ortalama mutlak fark")
    _var(metin, tr(e["en_buyuk_fark"], 1), "en büyük fark")
    _var(metin, f"**{e['kisit_degisen']} satırda kritik kısıt değişti**",
         "kısıt değişmedi ifadesi")


# ------------------------------------------------------ karar sistemleri
def test_depo_karsitligi(metin: str):
    d = _cikti("depo.json")["doz_cevap"]["karsitlik"]
    _var(metin, tr(d["kat"], 1), "diyatom koşul farkı (kat)")
    _var(metin, "%" + tr(d["dusuk"]["olum"], 1), "düşük koşul ölüm oranı")
    _var(metin, "%" + tr(d["yuksek"]["olum"], 1), "yüksek koşul ölüm oranı")


def test_karar_bosluklari(metin: str):
    b = bkarar.bosluklar()
    _var(metin, f"| {len(b['esigi_bilinmeyen'])} / 17 |", "eşiksiz zararlı")
    _var(metin, f"| {len(b['kalintisiz_yolu_olmayan'])} / 17 |",
         "kalıntısız yolu olmayan")
    assert not b["hicbir_secenegi_olmayan"], (
        "artık hiç seçeneği olmayan zararlı var — belge güncellenmeli")

    d = dkarar.ozet()
    _var(metin, f"**{d['yuzey_uygulamasi_yetmeyen']}'ü taneyi içeriden",
         "iç besleyen depo zararlısı")


# --------------------------------------------------------- bütünlük
def test_belgede_doldurulmamis_yer_yok(metin: str):
    for iz in ("TODO", "XXX", "???", "__"):
        assert iz not in metin, f"BULGULAR.md içinde '{iz}' kalmış"


def test_her_bulgunun_kaynagi_yazili(metin: str):
    """Her bulgu başlığının altında 'Nerede.' satırı olmalı."""
    basliklar = [s for s in metin.splitlines() if s.startswith("## ")
                 and s[3].isdigit()]
    assert len(basliklar) >= 13, "bulgu sayısı beklenenden az"
    assert metin.count("**Nerede.**") >= len(basliklar), (
        "bazı bulguların kaynak satırı yok")
