"""NABIZ KOSUSU — genel bakis sayfasini canli tutan HAFIF kosu.

Gunluk kosu her karti yeniden isler ve dakikalar surer; saatte bir
calistirilamaz. Bu kosu yalnizca DEGISEN seyi ceker:

* kuresel piyasa goruntusu (yfinance, anahtarsiz)
* portfoy + izleme + en yuksek puanli adaylarin haberleri (Finnhub)
* kritik tarihler takvimi (FRED yayin tarihleri + bilanco + SEC olaylari)

Kartlara DOKUNMAZ. Tek ciktisi ``data/pulse.json``; boylece nabiz kosusu
ile veri hatti ayni dosyalar uzerinde carpismaz.

    python -m src.run_pulse
    python -m src.run_pulse --no-calendar     # yalnizca piyasa + haber

GERCEKCI BEKLENTI: is akisi saatlik kurulu ama GitHub zamanlanmis
kosulari en iyi cabayla calistirir; pratikte birkac saatte bir doner.
Pano ``generated_at`` damgasini gosterir ki tazelik tahmin edilmesin.
"""

from __future__ import annotations

import argparse
import sys

from . import config, pipeline, portfolio, watchlist
from .config import DATA_DIR
from .sources import calendar_src, finnhub_api, market
from .util import read_json, try_fetch, utc_now_iso, write_json


def tracked_tickers(limit: int | None = None) -> tuple[set[str], dict[str, int]]:
    """Ilgi alanimizdaki semboller + CIK haritasi.

    Portfoy ve izleme listesi HER ZAMAN girer. Adaylardan yalnizca en
    yuksek puanlilar girer: 157 sirketin haberini saatte bir cekmek
    Finnhub kotasini anlamsizca yakar.
    """
    limit = config.PULSE["top_candidates"] if limit is None else limit
    tickers = set(watchlist.tickers()) | set(portfolio.tickers())

    cand = read_json(DATA_DIR / "candidates.json", {}) or {}
    rows = [*(cand.get("seed") or []), *(cand.get("candidates") or []),
            *(cand.get("manual") or [])]
    rows.sort(key=lambda r: (r.get("scores") or {}).get("total") or -1, reverse=True)
    for row in rows[:limit]:
        if row.get("ticker"):
            tickers.add(str(row["ticker"]).upper())

    cik_by_ticker: dict[str, int] = {}
    for path in config.CARDS_DIR.glob("*.json"):
        card = read_json(path)
        if isinstance(card, dict) and card.get("ticker") in tickers and card.get("cik"):
            cik_by_ticker[card["ticker"]] = card["cik"]

    return tickers, cik_by_ticker


def collect_news(tickers: set[str]) -> list[dict]:
    """Takip edilen sirketlerin son haberleri, tarihe gore sirali."""
    if not finnhub_api.enabled():
        print("[nabiz] FINNHUB_API_KEY yok — haber atlandi.")
        return []

    p = config.PULSE
    items: list[dict] = []
    for ticker in sorted(tickers):
        for item in (try_fetch(finnhub_api.news, ticker,
                               days=p["news_days"], limit=p["news_per_ticker"],
                               label=f"haber {ticker}") or []):
            items.append({**item, "ticker": ticker})

    # Ayni haber birden fazla sirkete bagli gelebiliyor; basliga gore tekille.
    seen: set[str] = set()
    unique = []
    for item in sorted(items, key=lambda n: n.get("date", ""), reverse=True):
        key = (item.get("headline") or "").strip().lower()
        if key and key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:p["max_news"]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Genel bakis nabiz kosusu")
    ap.add_argument("--no-calendar", action="store_true")
    ap.add_argument("--no-news", action="store_true")
    ap.add_argument("--limit", type=int, help="Kac adayi takip et")
    args = ap.parse_args(argv)

    tickers, cik_by_ticker = tracked_tickers(args.limit)
    print(f"[nabiz] {len(tickers)} sembol takip ediliyor")

    rows = try_fetch(market.snapshot, label="piyasa goruntusu") or []
    print(f"[nabiz] {len(rows)} enstruman guncellendi")

    news = [] if args.no_news else collect_news(tickers)
    print(f"[nabiz] {len(news)} haber")

    calendar: dict = {"upcoming": [], "recent": [], "source": "atlandi"}
    if not args.no_calendar:
        earnings = try_fetch(finnhub_api.cached_earnings_calendar,
                             label="kazanc takvimi") or {}
        calendar = try_fetch(calendar_src.build, earnings=earnings,
                             tickers=tickers, cik_by_ticker=cik_by_ticker,
                             label="takvim") or calendar
        print(f"[nabiz] takvim: {len(calendar['upcoming'])} yaklasan, "
              f"{len(calendar['recent'])} gecmis olay")

    ok = write_json(DATA_DIR / "pulse.json", {
        "market": rows,
        "risk_note": market.risk_note(rows),
        "news": news,
        "calendar": calendar,
        "tracked_count": len(tickers),
        "generated_at": utc_now_iso(),
        "source": "yfinance+finnhub+fred+sec",
    })

    # Portfoy K/Z'si fiyata bagli; nabiz kosusunda tazelenirse genel bakis
    # kutulari da canli olur. Kart YAZILMAZ — yalnizca ozet dosyasi.
    pipeline.write_macro()

    print("[nabiz] pulse.json yazildi" if ok else "[nabiz] degisiklik yok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
