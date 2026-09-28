#!/usr/bin/env bash
# VERI COMMIT'I — es zamanli kosulara dayanikli.
#
# Onceki kalip:  git pull --rebase --autostash ... || true ; git push
# Cakismada rebase yarim kaliyor, "|| true" hatayi yutuyor, push detached
# HEAD'de patliyordu. 17 Eylul'de 103 kartin yeniden hesaplanmasi bu yuzden
# kayboldu: hesaplama surerken bir tarama partisi candidates.json'a yazdi.
#
# Simdi:
#   * cakisan parcalarda BU KOSUNUN verisi tutulur (-X theirs; rebase
#     sirasinda "theirs" = yeniden oynatilan yerel commit),
#   * candidates.json kartlardan TURETILMIS bir dosya; birlestirme sonrasi
#     diskteki kartlardan yeniden kurulur ki baska kosunun ekledigi kart da
#     ozete girsin,
#   * 4 deneme, artan bekleme; hala olmazsa is akisi HATA verir (sessizce
#     gecmez).
#
# Kullanim: scripts/commit_data.sh "commit mesaji" [yol ...]   (varsayilan: data/)
set -uo pipefail

msg="$1"; shift
paths=("$@")
[ ${#paths[@]} -eq 0 ] && paths=(data/)
branch="${GITHUB_REF_NAME:-main}"

git config user.name  "berkehan-bot"
git config user.email "actions@github.com"

git add "${paths[@]}"
if git diff --staged --quiet; then
  echo "Degisiklik yok."
  exit 0
fi
git commit -q -m "$msg"

for attempt in 1 2 3 4; do
  if git pull -q --rebase -X theirs origin "$branch"; then
    if printf '%s\n' "${paths[@]}" | grep -q '^data/$\|candidates.json'; then
      python -c "from src import pipeline; pipeline.refresh_candidates_from_disk()" \
        && git add data/candidates.json \
        && { git diff --staged --quiet || git commit -q -m "veri: aday ozeti birlestirme sonrasi yenilendi"; }
    fi
    if git push -q origin "HEAD:$branch"; then
      echo "Gonderildi (deneme $attempt)."
      exit 0
    fi
  else
    git rebase --abort 2>/dev/null || true
  fi
  echo "Gonderilemedi (deneme $attempt), tekrar deneniyor..."
  sleep $((attempt * 8))
done

echo "::error::Veri commit'i 4 denemede gonderilemedi"
exit 1
