#!/usr/bin/env bash
#
# AGROMATCH — GitHub'a ilk yükleme
#
# Kullanım:
#   ./scripts/github_yukle.sh <github-kullanıcı-adın>
#
# Yapmadan önce: GitHub'da BOŞ bir depo aç (agromatch adıyla).
# README, .gitignore ya da lisans EKLEME — hepsi bizde zaten var; eklersen
# çakışma çıkar ve ilk gönderim reddedilir.
#
# Betik bir şeyi bozmaz: önce kontrol eder, sorun varsa durur.

set -euo pipefail

KULLANICI="${1:-}"
DEPO="${2:-agromatch}"

renk() { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
bilgi() { renk "0;36" "→ $1"; }
tamam() { renk "0;32" "✓ $1"; }
hata()  { renk "0;31" "✗ $1" >&2; exit 1; }

if [[ -z "$KULLANICI" ]]; then
  hata "Kullanım: ./scripts/github_yukle.sh <github-kullanıcı-adın> [depo-adı]"
fi

cd "$(dirname "$0")/.."

# ---------------------------------------------------------------- kontroller
bilgi "Depo durumu kontrol ediliyor"

[[ -d .git ]] || hata "Burası bir git deposu değil."

if [[ -n "$(git status --porcelain)" ]]; then
  git status --short
  hata "Kaydedilmemiş değişiklik var. Önce commit et ya da geri al."
fi
tamam "çalışma alanı temiz"

DAL="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$DAL" != "main" ]]; then
  bilgi "Dal '$DAL' -> 'main' olarak yeniden adlandırılıyor"
  git branch -M main
fi
tamam "dal: main"

COMMIT="$(git rev-list --count HEAD)"
tamam "$COMMIT commit, $(git ls-files | wc -l | tr -d ' ') dosya"

# --------------------------------------------------------------- doğrulama
bilgi "Gönderim öncesi doğrulama (testler + denetimler)"

if ! python -m pytest -q >/tmp/agromatch_test.log 2>&1; then
  tail -20 /tmp/agromatch_test.log
  hata "Testler geçmiyor. Kırık kod gönderme."
fi
tamam "testler geçti"

if command -v ruff >/dev/null 2>&1; then
  ruff check src tests >/dev/null || hata "ruff uyarı veriyor."
  tamam "ruff temiz"
fi

if command -v mypy >/dev/null 2>&1; then
  python -m mypy >/dev/null || hata "mypy uyarı veriyor."
  tamam "mypy temiz"
fi

# ----------------------------------------------------------------- gönderim
UZAK="https://github.com/${KULLANICI}/${DEPO}.git"

if git remote get-url origin >/dev/null 2>&1; then
  MEVCUT="$(git remote get-url origin)"
  if [[ "$MEVCUT" != "$UZAK" ]]; then
    bilgi "origin güncelleniyor: $MEVCUT -> $UZAK"
    git remote set-url origin "$UZAK"
  fi
else
  bilgi "origin ekleniyor: $UZAK"
  git remote add origin "$UZAK"
fi
tamam "origin: $UZAK"

echo
bilgi "Gönderiliyor. Kimlik sorarsa parola DEĞİL, personal access token gir."
bilgi "Token: GitHub > Settings > Developer settings > Personal access tokens"
bilgi "       > Tokens (classic) > Generate new token > 'repo' yetkisi"
echo

git push -u origin main

echo
tamam "Gönderildi: https://github.com/${KULLANICI}/${DEPO}"
echo
bilgi "Şimdi şunlara bak:"
echo "   Actions sekmesi  — iki iş de yeşil yanmalı (test, lint)"
echo "   Settings > About — açıklama ve konu etiketleri ekle"
echo
bilgi "Sürüm etiketi göndermek istersen:"
echo "   git push origin v0.2.0"
