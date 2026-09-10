"""INBOX BIRLESTIRME — claude_inbox/ icerigini kartlara isler.

AG GEREKTIRMEZ. Yalnizca repodaki dosyalari okur ve yazar; bu yuzden
saniyeler surer ve `claude_inbox/` klasorune her yazildiginda calisabilir.

Baska bir ajanin (sohbetteki Claude, GitHub baglantisiyla) yazdigi analiz
dosyalarini kartlara islemek icin tasarlandi. Ajan yalnizca inbox'a yazar;
sayisal alanlara dokunamaz.

    python -m src.run_merge
    python -m src.run_merge --check     # yalnizca dogrula, yazma
"""

from __future__ import annotations

import argparse
import sys

from . import cards, pipeline
from .config import CARDS_DIR, INBOX_DIR
from .inbox import validate_file
from .util import read_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="claude_inbox -> kartlar")
    parser.add_argument("--check", action="store_true",
                        help="Yalnizca dogrula; kartlara yazma")
    args = parser.parse_args(argv)

    files = sorted(p for p in INBOX_DIR.glob("*.json")
                   if not p.name.startswith("_"))
    if not files:
        print("[inbox] Islenecek dosya yok.")
        return 0

    errors: list[str] = []
    merged: list[str] = []
    skipped: list[str] = []

    for path in files:
        ticker = path.stem.upper()
        payload = read_json(path)
        problems = validate_file(payload, ticker)
        if problems:
            errors.extend(f"{path.name}: {p}" for p in problems)
            continue

        card_path = CARDS_DIR / f"{ticker}.json"
        if not card_path.exists():
            skipped.append(f"{ticker} (kart yok — once veri hatti calismali)")
            continue

        if args.check:
            merged.append(ticker)
            continue

        card = read_json(card_path)
        if not isinstance(card, dict):
            errors.append(f"{ticker}: kart okunamadi")
            continue
        card = cards.merge_story(card)
        card["story_age_days"] = cards._story_age(card)
        if cards.save(card, merge=False):
            merged.append(ticker)

    for e in errors:
        print(f"  [HATA] {e}")
    for s in skipped:
        print(f"  [atlandi] {s}")

    if args.check:
        print(f"[inbox] {len(merged)} dosya gecerli, {len(errors)} hatali")
        return 1 if errors else 0

    # Pano izgarasi kartlari DEGIL data/candidates.json'i okur. Tazelenmezse
    # birlestirme kartta gorunur ama panoda gorunmez — puan degistiginde
    # (kapsama carpani, katalizor) iki dosya birbiriyle celisir.
    # Kosulsuz: ``cards.save`` icerik degismediyse False doner, ama ozet dosyasi
    # yine de kartlarla ayni fikirde olmayabilir (baska bir kosu karti
    # guncelledi, birlestirme yeniden calisti). Yeniden kurmak ucuz.
    pipeline.refresh_candidates_from_disk()

    print(f"[inbox] {len(merged)} kart guncellendi"
          + (f": {', '.join(merged)}" if merged else ""))
    if errors:
        print(f"[inbox] {len(errors)} dosya hatali — duzeltilmeden islenmeyecek")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
