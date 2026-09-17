"""TUM KARTLARI YENIDEN HESAPLA — kaynaklarini koruyarak.

Veri cikarma veya puanlama mantigi degistiginde mevcut kartlar ESKI kodla
hesaplanmis olarak kalir. Tohum kosusu yalnizca tohum etiketiyle calisir,
tarama ise yalnizca EKSIK kartlari uretir; mevcut kartlari yeni kurallarla
yeniden hesaplayan bir yol yoktu. Sonuc: kural 10 Eylul'de degisti, tohum
kartlari 17 Eylul'de hala eski teshisi (would_fail_at, kill_reason)
gosteriyordu.

Her kartin kaynagi (tohum / huni / elle) ve yazili bolumleri (analiz,
karar) korunur; yalnizca hesaplanan kisim yenilenir.

Yuzdelik havuzu: yeniden hesaplanan kartlar + tarama hayatta kalanlari.
Yalnizca 100 kartlik havuz, huni kartlarini 250 sirketlik havuzdan
hesaplandiklari duruma gore farkli yuzdeliklere iterdi.

    python -m src.run_rebuild
    python -m src.run_rebuild --tickers COLL,CPAY,BELFA
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict

from . import funnel, percentiles, pipeline, scan, watchlist
from .config import CARDS_DIR, SEED_SOURCE_TAG
from .util import read_json


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mevcut kartlari yeniden hesapla")
    ap.add_argument("--tickers", help="Virgulle alt kume (bos = tum kartlar)")
    ap.add_argument("--no-news", action="store_true")
    args = ap.parse_args(argv)

    existing = {}
    for path in sorted(CARDS_DIR.glob("*.json")):
        card = read_json(path)
        if isinstance(card, dict) and card.get("ticker"):
            existing[card["ticker"]] = card

    wanted = ([t.strip().upper() for t in args.tickers.split(",")]
              if args.tickers else sorted(existing))
    manual = set(watchlist.tickers())
    print(f"[yeniden] {len(wanted)} kart yeniden hesaplanacak")

    bench = pipeline.benchmarks().get("QQQ", [])
    ctx = pipeline.context(wanted)

    rows, missing = [], []
    for i, ticker in enumerate(wanted, 1):
        print(f"[{i:3}/{len(wanted)}] {ticker}")
        f = pipeline.load_company(ticker)
        if f is None:
            missing.append(ticker)
            continue
        row = funnel.evaluate(f, benchmark=bench)
        row["is_manual"] = ticker in manual
        row["extra_warnings"] = []
        rows.append(row)

    fresh = {r["ticker"] for r in rows}
    pool = (rows
            + [scan.from_snapshot(s) for s in scan.load_survivors()
               if s.get("ticker") not in fresh]
            + pipeline.sector_rows_from_cards(exclude=fresh))
    sector_table = percentiles.build_sector_table(pool)
    print(f"[yeniden] yuzdelik havuzu: {len(pool)} sirket")

    by_source: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        old = existing.get(row["ticker"]) or {}
        source = ("manual" if row["is_manual"]
                  else old.get("source") or SEED_SOURCE_TAG)
        by_source[source].append(row)

    built = 0
    for source, group in by_source.items():
        built += len(pipeline.build_cards(group, source=source, sector_table=sector_table,
                                          ctx=ctx, bench=bench,
                                          with_news=not args.no_news))

    pipeline.write_thresholds()
    pipeline.refresh_candidates_from_disk()
    print(f"[yeniden] {built} kart yeniden hesaplandi"
          + (f"; yuklenemeyen: {', '.join(missing)}" if missing else ""))
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
