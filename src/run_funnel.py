"""TAM EVREN TARAMASI — Asama 0'dan 4'e.

SEC toplu verisini senkronize eder, evreni kurar, huniyi calistirir,
ilk 50 aday icin kart uretir.

    python -m src.run_funnel
    python -m src.run_funnel --limit 500     # hizli deneme
    python -m src.run_funnel --skip-sync     # onbellekten calis
"""

from __future__ import annotations

import argparse
import sys

from . import config, funnel, pipeline, watchlist
from .pipeline import universe_tickers
from .config import SEED_TICKERS
from .sources import edgar_bulk


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tam evren huni taramasi")
    parser.add_argument("--limit", type=int, help="Islenecek sirket sayisi ustu")
    parser.add_argument("--skip-sync", action="store_true",
                        help="SEC toplu verisini yeniden indirme")
    parser.add_argument("--quarters", type=int, default=None,
                        help="Kac ceyrek toplu veri yuklensin")
    args = parser.parse_args(argv)

    if not args.skip_sync:
        print("[huni] SEC toplu verisi senkronize ediliyor...")
        new = edgar_bulk.sync(args.quarters)
        print(f"[huni] Yeni ceyrek: {new or 'yok'}")
        edgar_bulk.prune()
    print(f"[huni] Onbellek: {edgar_bulk.cache_stats()}")

    tickers = universe_tickers(args.limit)
    print(f"[huni] Evren adayi: {len(tickers)} sembol")

    bench_map = pipeline.benchmarks()
    bench = bench_map.get("QQQ", [])
    ctx = pipeline.context(tickers)

    rows = []
    for i, ticker in enumerate(tickers, 1):
        if i % 50 == 0:
            print(f"[huni] {i}/{len(tickers)} islendi")
        f = pipeline.load_company(ticker)
        if f is None:
            continue
        rows.append(funnel.evaluate(f, benchmark=bench))

    print(f"[huni] {len(rows)} sirket degerlendirildi")
    result = funnel.run(rows)

    for stage in result["log"]["stages"]:
        print(f"   Asama {stage['stage']} {stage['name']:16} "
              f"{stage['input']:5} -> {stage['output']:5}")

    print("\n[huni] En sik eleme sebepleri:")
    for reason, count in list(result["log"]["kill_reasons"].items())[:10]:
        print(f"   {count:5}  {reason}")

    sector_table = result["sector_table"]
    seed_rows = [r for r in result["all_rows"] if r["ticker"] in SEED_TICKERS]
    manual_rows = [r for r in result["all_rows"]
                   if r["ticker"] in watchlist.tickers()]
    for r in manual_rows:
        r["is_manual"] = True

    funnel_cards = pipeline.build_cards(
        result["candidates"], source="funnel",
        sector_table=sector_table, ctx=ctx, bench=bench)
    seed_cards = pipeline.build_cards(
        seed_rows, source=config.SEED_SOURCE_TAG,
        sector_table=sector_table, ctx=ctx, bench=bench)
    manual_cards = pipeline.build_cards(
        manual_rows, source="manual",
        sector_table=sector_table, ctx=ctx, bench=bench)

    pipeline.write_thresholds()
    pipeline.write_universe(result["all_rows"], result["log"])
    pipeline.append_funnel_log(result["log"])
    pipeline.refresh_candidates_from_disk()
    pipeline.write_macro()

    print(f"\n[huni] {len(funnel_cards)} aday karti, {len(seed_cards)} tohum karti, "
          f"{len(manual_cards)} elle eklenen kart yazildi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
