"""TOHUM LISTESI KOSUSU — sartnamedeki ILK IS.

9 Eylul 2026 Finviz on taramasindan cikan 36 sirket icin tam metrik seti ve
kart uretir. Huniden BAGIMSIZ calisir; ama her sirketin huninin hangi
asamasinda elenecegi de hesaplanip kartta gosterilir (ogrenme icin).

    python -m src.run_seed
    python -m src.run_seed --tickers DBX,LSCC     # alt kume
"""

from __future__ import annotations

import argparse
import sys

from . import config, funnel, percentiles, pipeline, validate
from .config import SEED_SOURCE_TAG, SEED_TICKERS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tohum listesi kartlarini uretir")
    parser.add_argument("--tickers", help="Virgulle ayrilmis alt kume")
    parser.add_argument("--no-news", action="store_true", help="Haber cekme")
    args = parser.parse_args(argv)

    tickers = ([t.strip().upper() for t in args.tickers.split(",")]
               if args.tickers else SEED_TICKERS)

    print(f"[tohum] {len(tickers)} sirket — {config.SEED_DATE} taramasi")
    print(f"[tohum] Kol A: {len(config.SEED_TRACK_A)}, Kol B: {len(config.SEED_TRACK_B)}, "
          f"her ikisi: {config.SEED_BOTH_TRACKS}")

    bench_map = pipeline.benchmarks()
    bench = bench_map.get("QQQ", [])
    ctx = pipeline.context(tickers)

    rows, missing = [], []
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i:2}/{len(tickers)}] {ticker}")
        f = pipeline.load_company(ticker)
        if f is None:
            missing.append(ticker)
            continue
        row = funnel.evaluate(f, benchmark=bench)
        row["extra_warnings"] = []
        rows.append(row)

    if not rows:
        print("[hata] Hicbir sirket yuklenemedi — SEC erisimi ve "
              "SEC_USER_AGENT ayarini kontrol et.")
        return 1

    # Sektor tablosu tohum evreni uzerinden kurulur. 36 sirketlik havuz
    # kucuk; pct_basis alani hangi referansin kullanildigini kaydeder.
    #
    # ALT KUME KOSUSU: --tickers ile tek sirket calistirildiginda havuz tek
    # satira duser ve butun yuzdelikler None olur. Kosuda olmayan sirketler
    # diskteki kartlardan tamamlanir.
    pool = rows + pipeline.sector_rows_from_cards(
        exclude={r["ticker"] for r in rows})
    if len(pool) > len(rows):
        print(f"[tohum] yuzdelik havuzu {len(rows)} taze + "
              f"{len(pool) - len(rows)} mevcut kart = {len(pool)} sirket")
    sector_table = percentiles.build_sector_table(pool)

    built = pipeline.build_cards(rows, source=SEED_SOURCE_TAG,
                                 sector_table=sector_table, ctx=ctx, bench=bench,
                                 with_news=not args.no_news)

    pipeline.write_thresholds()
    pipeline.refresh_candidates_from_disk()
    pipeline.write_macro()

    would_fail = {}
    for card in built:
        stage = (card.get("flags") or {}).get("would_fail_at")
        would_fail[stage] = would_fail.get(stage, 0) + 1

    print(f"\n[tohum] {len(built)} kart uretildi -> data/cards/")
    if missing:
        print(f"[tohum] Yuklenemeyen: {', '.join(missing)}")
    print("[tohum] Huni calissaydi eleme dagilimi:")
    for stage in sorted(would_fail, key=lambda s: (s is None, s)):
        label = "gecerdi" if stage is None else f"Asama {stage}"
        print(f"          {label}: {would_fail[stage]}")

    # VERI KALITESI — sessiz yanlis sayi, gorunur bosluktan tehlikelidir
    summary = validate.summarize(built)
    print(f"\n[tohum] Veri kalitesi: {summary['counts']}")
    if summary["top_issues"]:
        print("[tohum] En sik sorunlar:")
        for code, n in summary["top_issues"].items():
            print(f"          {n:3}  {code}")
    bad = [c["ticker"] for c in built
           if (c.get("data_quality") or {}).get("status") == "kotu"]
    if bad:
        print(f"[tohum] Guvenilmeyen kartlar ({len(bad)}): {', '.join(bad)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
