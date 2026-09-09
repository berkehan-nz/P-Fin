"""data/ klasorunu gecerli ama BOS semalarla kurar.

Dashboard ilk acilista 404 almasin diye. Gercek veri GitHub Actions'taki
``bootstrap.yml`` / ``weekly.yml`` kosularinda doldurulur — bu ortamda
sec.gov, stooq ve finnhub'a cikis yok.

UYDURMA VERI YAZILMAZ. Bos sema, sahte sayidan iyidir.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config, portfolio, watchlist  # noqa: E402
from src.util import write_json  # noqa: E402

D = config.DATA_DIR


def main() -> int:
    written = []

    if write_json(D / "thresholds.json",
                  {**config.thresholds_payload(), "source": "config.py"}):
        written.append("thresholds.json")

    if write_json(D / "candidates.json", {
        "candidates": [], "seed": [], "manual": [],
        "counts": {"funnel": 0, "seed": 0, "manual": 0},
        "seed_date": config.SEED_DATE,
        "source": "bos — veri hatti henuz calismadi",
    }):
        written.append("candidates.json")

    if write_json(D / "universe.json", {
        "total_evaluated": 0, "log": {"stages": [], "kill_reasons": {}},
        "sectors": {}, "source": "bos",
    }):
        written.append("universe.json")

    if write_json(D / "funnel_log.json", {"runs": [], "source": "bos"}):
        written.append("funnel_log.json")

    if write_json(D / "macro.json", {"series": {}, "source": "bos"}):
        written.append("macro.json")

    if write_json(D / "overview.json", {
        "movers": [], "news": [], "watched_count": 0, "source": "bos",
    }):
        written.append("overview.json")

    if write_json(D / "portfolio_state.json", {
        "positions": [], "closed": [], "warnings": [],
        "summary": {"position_count": 0, "cost_usd": 0.0,
                    "equity_value_usd": 0.0, "cash_usd": 0.0,
                    "portfolio_value_usd": 0.0, "pnl_usd": 0.0,
                    "pnl_pct": None, "sector_mix_pct": {},
                    "largest_position_pct": None,
                    "vs_benchmark": {"nasdaq100": None, "sp500": None}},
        "source": "bos",
    }):
        written.append("portfolio_state.json")

    if watchlist.ensure_file():
        written.append("watchlist.json")
    if portfolio.ensure_file():
        written.append("portfolio.json")

    if write_json(D / "scan_state.json", {
        **__import__("src.scan", fromlist=["scan"]).empty_state(),
    }):
        written.append("scan_state.json")

    survivors = D / "survivors"
    survivors.mkdir(parents=True, exist_ok=True)
    keep = survivors / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")
        written.append("survivors/.gitkeep")

    gitkeep = config.CARDS_DIR / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
        written.append("cards/.gitkeep")

    print(f"[init] {len(written)} dosya yazildi: {', '.join(written) or 'degisiklik yok'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
