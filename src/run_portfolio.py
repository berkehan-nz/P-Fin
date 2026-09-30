"""PORTFOY KOSUSU — saatlik, hafif: yalnizca eldeki varliklar + kur.

Gunluk kosu yuzlerce karti isler ve ABD piyasasi acilmadan (~10:30 UTC)
calisir; portfoyun "bugun nasil gitti" sorusuna yetmez. Bu kosu yalnizca:

* eldeki ETF/hisselerin fiyat serisi (TAZE — onbellek 15 dk),
* kiyas serileri (SGOV, QQQ) ve USD/TRY,

ceker; ``data/portfolio_state.json`` ve ``data/portfolio_history.json``
dosyalarini yeniden yazar. Piyasa acikken son satir gun ici fiyattir;
kapanistan sonraki kosu onu kapanis fiyatiyla degistirir (tarihce her
kosuda bastan kurulur, tam satir tam satirin yerine gecer).

Kartlara, aday listesine ve huniye DOKUNMAZ.

    python -m src.run_portfolio
"""

from __future__ import annotations

import sys

from . import config, pipeline, portfolio
from .sources import finnhub_api, prices
from .util import try_fetch


def main(argv: list[str] | None = None) -> int:
    portfolio.ensure_file()
    fresh = config.PORTFOLIO_REFRESH["max_age_hours"]
    held = portfolio.tickers()

    quotes: dict[str, dict] = {}
    for ticker in held:
        q = try_fetch(prices.quote, ticker, max_age_hours=fresh, label=f"fiyat {ticker}")
        if q and q.get("price") is not None:
            quotes[ticker] = q

    bench = pipeline.benchmarks()
    earnings = try_fetch(finnhub_api.cached_earnings_calendar, label="kazanc takvimi") or {}
    pipeline.write_portfolio_state(quotes, bench, {"earnings": earnings},
                                   max_age_hours=fresh)

    eksik = sorted(set(held) - set(quotes))
    print(f"[portfoy] {len(quotes)}/{len(held)} fiyat"
          + (f" — EKSIK: {', '.join(eksik)}" if eksik else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
