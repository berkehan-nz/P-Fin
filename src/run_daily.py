"""GUNLUK KOSU — hafta ici 07:00 TSI.

Yaptiklari: fiyat, momentum, haber, kazanc takvimi, portfoy degerleri
guncellenir; ``merge_story()`` her kart icin cagrilir; makro tazelenir.
Huni CALISMAZ (o haftalik). Degisiklik yoksa hicbir dosyaya dokunulmaz.

    python -m src.run_daily
"""

from __future__ import annotations

import argparse
import sys

from . import cards, config, pipeline, portfolio, validate, watchlist
from .config import CARDS_DIR
from .sources import analyst as analyst_src, finnhub_api, prices
from .util import read_json, try_fetch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gunluk guncelleme")
    parser.add_argument("--no-news", action="store_true")
    args = parser.parse_args(argv)

    portfolio.ensure_file()
    watchlist.ensure_file()

    card_paths = sorted(CARDS_DIR.glob("*.json"))
    tickers = sorted({p.stem.upper() for p in card_paths}
                     | set(watchlist.tickers()) | set(portfolio.tickers()))
    if not tickers:
        print("[gunluk] Kart yok. Once `python -m src.run_seed` calistir.")
        return 1

    print(f"[gunluk] {len(tickers)} sembol guncelleniyor")

    bench_map = pipeline.benchmarks()
    ctx = pipeline.context(tickers)

    quotes: dict[str, dict] = {}
    changed = 0

    for i, ticker in enumerate(tickers, 1):
        quote = try_fetch(prices.quote, ticker, label=f"fiyat {ticker}")
        if quote:
            quotes[ticker] = quote

        card = read_json(CARDS_DIR / f"{ticker}.json")
        if not isinstance(card, dict):
            continue

        # --- fiyata bagli alanlari tazele ---
        if quote and quote.get("price"):
            card["price"] = round(quote["price"], 2)
            card["change_1d_pct"] = (round(quote["change_1d_pct"], 2)
                                     if quote.get("change_1d_pct") is not None else None)
            card["series"]["price_sparkline"] = prices.sparkline(quote["history"])
            _refresh_price_derived(card, quote, bench_map.get("QQQ", []))
            card["data_sources"]["price"] = quote.get("source")

        # --- haber ve takvim ---
        if not args.no_news and finnhub_api.enabled():
            news = try_fetch(finnhub_api.news, ticker, label=f"haber {ticker}")
            if news:
                card["news"] = news
        card["calendar"] = {"next_earnings": ctx["earnings"].get(ticker)}

        analyst = try_fetch(analyst_src.consensus, ticker, card.get("price"),
                            label=f"analist {ticker}")
        if analyst:
            card["analyst"] = analyst

        # Fiyat degisince carpanlar yeniden hesaplandi; denetimi tekrarla
        validate.check(card)
        card["as_of"] = pipeline.today_iso()
        # merge_story() HER KOSUDA cagrilir — Claude'un yazdigi kartlara isler
        if cards.save(card):
            changed += 1

    pipeline.write_thresholds()
    pipeline.refresh_candidates_from_disk()
    pipeline.write_portfolio_state(quotes, bench_map, ctx)
    pipeline.write_overview(ctx, quotes)
    pipeline.write_macro()

    print(f"[gunluk] {changed} kart degisti, {len(quotes)} fiyat guncellendi")
    return 0


def _refresh_price_derived(card: dict, quote: dict, benchmark: list) -> None:
    """Fiyat degisince degerleme carpanlarini ve momentumu yeniden hesapla.

    Temel veri (EDGAR) gun icinde degismez, o yuzden tam yeniden uretim
    gereksiz. EV hisse sayisi ve net borctan, carpanlar da kartta saklanan
    TTM buyukluklerinden YENIDEN kurulur — dunku carpani oranla olceklemek
    her gun biraz daha sapan bir sayi birakirdi. Tam yeniden uretim
    haftalik kosuda yapilir.
    """
    from .metrics import return_over
    from .util import div, num

    price = num(quote.get("price"))
    shares = num(card.get("shares_outstanding_m"))
    net_debt = num(card.get("net_debt_musd"))
    ttm = card.get("ttm") or {}
    cells = card.setdefault("metrics", {})

    if price is not None and shares is not None:
        mcap = price * shares
        ev = mcap + (net_debt or 0.0)
        card["market_cap_musd"] = round(mcap, 1)
        card["enterprise_value_musd"] = round(ev, 1)

        ebit = num(ttm.get("ebit_musd"))
        ebitda = num(ttm.get("ebitda_musd"))
        gross_profit = num(ttm.get("gross_profit_musd"))
        revenue = num(ttm.get("revenue_musd"))
        net_income = num(ttm.get("net_income_musd"))
        fcf = num(ttm.get("fcf_musd"))

        # Negatif paydada carpan anlamsiz — None birak, sahte sayi uretme
        _set(cells, "ev_ebit", div(ev, ebit) if (ebit or 0) > 0 else None)
        _set(cells, "ev_ebitda", div(ev, ebitda) if (ebitda or 0) > 0 else None)
        _set(cells, "ev_gross_profit",
             div(ev, gross_profit) if (gross_profit or 0) > 0 else None)
        _set(cells, "ev_sales", div(ev, revenue) if (revenue or 0) > 0 else None)
        _set(cells, "pe", div(mcap, net_income) if (net_income or 0) > 0 else None)
        _set(cells, "earnings_yield",
             (ebit / ev * 100) if (ebit is not None and ev > 0) else None)
        _set(cells, "fcf_yield_ev",
             (fcf / ev * 100) if (fcf is not None and ev > 0) else None)
        _set(cells, "fcf_yield_mcap",
             (fcf / mcap * 100) if (fcf is not None and mcap > 0) else None)

        card["reverse_dcf"] = {**(card.get("reverse_dcf") or {}),
                               "enterprise_value_musd": round(ev, 1)}

    # --- momentum ---
    history = quote.get("history") or []
    p = config.METRIC_PARAMS
    r6 = return_over(history, p["window_6m_days"])
    r12 = return_over(history, p["window_12m_days"])
    b6 = return_over(benchmark, p["window_6m_days"])
    b12 = return_over(benchmark, p["window_12m_days"])
    high = num(quote.get("high_52w"))
    off_high = ((1 - price / high) * 100) if (high and price and high > 0) else None

    for key, value in (
        ("return_6m", r6),
        ("return_12m", r12),
        ("rel_strength_6m", (r6 - b6) if (r6 is not None and b6 is not None) else None),
        ("rel_strength_12m", (r12 - b12) if (r12 is not None and b12 is not None) else None),
        ("pct_off_52w_high", off_high),
    ):
        _set(cells, key, value)


def _set(cells: dict, key: str, value) -> None:
    """Bir metrik hucresini gunceller; yuzdelikler haftalik kosuda yenilenir."""
    from .config import color_for
    from .util import num
    v = num(value)
    cell = cells.setdefault(key, {"sector_pct": None, "own_5y_pct": None,
                                  "pct_basis": "none"})
    cell["value"] = round(v, 3) if v is not None else None
    cell["color"] = color_for(key, v)


if __name__ == "__main__":
    sys.exit(main())
