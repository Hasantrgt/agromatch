# Katkı kuralları

Bu depo dört kişilik bir ekip tarafından geliştiriliyor. Aşağıdakiler kural
olsun diye değil, **birbirimizin işini bozmayalım** diye yazıldı.

---

## Başlamadan önce

```bash
git clone https://github.com/<kullanıcı>/agromatch.git
cd agromatch
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest                              # 137 test geçmeli
python src/mus_panel_uret.py --hepsi
```

Testler geçmiyorsa kod yazmaya başlama; önce neden geçmediğini bul.

---

## Üç kural

### 1. Üretilen dosya depoya girmez

`outputs/`, `mus_panel.html`, föyler, sentetik görüntüler — hepsi `.gitignore`
içinde. Hepsi tek komutla yeniden üretilir.

Bunları depoya koymak iki soruna yol açar: her çalıştırmada devasa fark
(diff) çıkar, ve bir gün kaynakla çıktı birbirini tutmaz — hangisinin doğru
olduğu bilinmez.

Yeni bir üretilen dosya ekliyorsan `.gitignore`'a da ekle.

### 2. Veri tek yerde durur

`src/mus_profil.py` projenin tek veri omurgasıdır. Analiz dosyaları **hesap
yapar, veri tutmaz.**

Bir sayıyı başka yere yazma isteği gelirse dur ve düşün: o sayı `mus_profil`'e
ait. Gerçek veri geldiğinde değişecek tek dosya orası olmalı.

Aynı şey denge formülleri için geçerli: tek tanım `mus_iz.denge_grafigi()`
içinde. İkinci bir kopya çıkarsa `tests/test_altin.py` kırılır — bilerek.

### 3. Her sayının türü yazılı olur

Panele giren her veri üç kategoriden birine girer:

| Tür | Anlamı |
|---|---|
| **ölçüm** | Resmî kaynakta yayımlanmış |
| **varsayım** | Literatürden alınan katsayı |
| **dağıtım** | İl toplamının ilçelere bölünmesi |

Yeni bir sayı eklerken `KUNYE` listesine de ekle ve türünü yaz. Kaynağı
olmayan bir sayı panele giremez.

---

## Çalışma akışı

```bash
git checkout -b ozellik/mera-ndvi      # dal aç
# ... kod ...
pytest && ruff check src tests && mypy # üçü de temiz olmalı
git commit                              # aşağıdaki biçimde
git push -u origin ozellik/mera-ndvi
# GitHub'da pull request aç
```

`main` dalına doğrudan gönderim yapma. Dalın ömrü kısa olsun — bir hafta
süren dal, birleştirirken acı verir.

### Dal adları

| Önek | Ne için |
|---|---|
| `ozellik/` | yeni bir şey |
| `duzeltme/` | hata düzeltmesi |
| `veri/` | veri güncellemesi (TÜİK, laboratuvar sonucu) |
| `belge/` | yalnızca belge |

### Commit mesajları

İlk satır **ne yaptığını** söyler, gövde **neden** yaptığını:

```
Mera verimini laboratuvar ölçümüyle değiştir

Kadran biçimi 40 noktada yapıldı, ortalama 0,13 ton KM/dekar çıktı.
Önceki 0,10 varsayımdı ve yem açığı belirsizliğinin %73'ünü üretiyordu.
Ölçümle birlikte belirsizlik ±8,7'den ±4,0 yüzde puana iniyor.

Altın dosya bilerek güncellendi: bu bir model değişikliği, refactor değil.
```

Türkçe yaz. İlk satır 72 karakteri geçmesin, sonuna nokta koyma.

---

## Test yazma

Yeni bir hesap eklediysen testi de gelsin. İkisi aynı commit'te olur.

**Regresyon testi en değerlisidir.** Bir hata bulduysan, düzeltmeden önce o
hatayı yakalayan testi yaz. Hikâyesini de testin içine yaz:

```python
def test_sig_toprak_derin_koklu_urunu_sinirlar():
    """Varto'nun toprağı 65 cm. Derin köklü ürün burada tavanlanır, sığ
    köklü ürün tavanlanmaz — bu testi yazarken fark edildi."""
```

Altı ay sonra bu testi okuyan kişi (muhtemelen sen) neden var olduğunu
anlamalı.

### Altın dosya

`tests/altin/belirsizlik.json` refactor'ların çıktıyı değiştirmediğini
doğrular. **Test kırıldı diye altın dosyayı yenileme** — testin varlık
sebebini ortadan kaldırırsın.

Yalnızca bilerek bir model değişikliği yaptıysan ve yeni sayının neden doğru
olduğunu gerekçelendirebiliyorsan güncelle. Commit mesajında gerekçeyi yaz.

---

## Panel üzerinde çalışma

Panel kaynağı `src/panel/` altında parçalı:

```
bas.html      başlık, yazı tipi
stil.css      bütün biçimlendirme
govde.html    sayfa iskeleti
js/00_veri.js       veri yer tutucuları
js/10_ortak.js      yardımcılar
js/20_harita.js     ilçe haritası
js/3x_sekme_*.js    her sekme ayrı dosya
js/90_uygulama.js   yönlendirme
```

**Yükleme sırası ada göre belirlenir.** Yeni dosyaya iki haneli numara ver:
yardımcılar sekmelerden, sekmeler yönlendirmeden önce gelmeli.

`mus_panel.html` dosyasını **elle düzenleme** — üretilen dosya, bir sonraki
`python src/mus_panel_uret.py` çalıştırmasında kaybolur.

Bir dosya 260 satırı geçerse `tests/test_panel.py` kırılır. Bölmek gerekir.

---

## Neyi değiştirmeden önce sor

Bunlar başkalarının işini kırar:

- `src/mus_profil.py` içindeki sözlük **şekilleri** (değerler serbest)
- `mus_iz.denge_grafigi()` çıktısının anahtarları
- `outputs/*.json` alan adları — panel ve mobil uygulama bunlara bakıyor
- `mobil_paket/veri_semasi.json` — mobil uygulama ile sunucu arasındaki
  sözleşme

Değerleri güncellemek serbest ve beklenen şeydir; **şekli** değiştirmek
konuşulması gereken bir karardır.

---

## Sürekli tümleştirme

Her gönderimde GitHub Actions çalışır:

- **test** — Python 3.10 ve 3.12'de testler, veri denetimi, panel üretimi
- **lint** — ruff ve mypy

İkisi de yeşil yanmadan pull request birleştirilmez. Kırmızı yanan bir CI'yı
görmezden gelmeye başlarsak CI'nın hiçbir faydası kalmaz.

---

## Soru

Bir şeyin neden öyle yapıldığını anlamıyorsan önce kodun yorumuna bak —
yorumlar "ne" değil "neden" anlatacak şekilde yazıldı. Orada da yoksa sor;
cevabı yorum olarak eklememiz gerekiyordur.
