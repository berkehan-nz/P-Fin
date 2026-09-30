"""run_portfolio — saatlik portfoy kosusu TAZE fiyat kullanmali.

30 Eylul'de pano bir gun eski fiyat gosterdi: fiyatlar yalnizca gunluk
kosuda (ABD piyasasi acilmadan) ve 12 saatlik onbellekle cekiliyordu.
Saatlik kosu onbellekten okursa "guncelleme" eski fiyati yeniden yazar.
"""

from src import config, pipeline, run_portfolio
from src.sources import finnhub_api, prices


def test_hourly_run_bypasses_price_cache(monkeypatch):
    seen = {"quote": [], "write": None}

    def fake_quote(ticker, **kw):
        seen["quote"].append((ticker, kw.get("max_age_hours")))
        return {"ticker": ticker, "price": 100.0, "change_1d_pct": 0.1, "as_of": "2026-09-30"}

    def fake_write(quotes, bench, ctx, *, max_age_hours=12):
        seen["write"] = (sorted(quotes), max_age_hours)
        return True

    monkeypatch.setattr(run_portfolio.portfolio, "ensure_file", lambda: None)
    monkeypatch.setattr(run_portfolio.portfolio, "tickers", lambda: ["QQQM", "SGOV"])
    monkeypatch.setattr(prices, "quote", fake_quote)
    monkeypatch.setattr(pipeline, "benchmarks", lambda: {})
    monkeypatch.setattr(pipeline, "write_portfolio_state", fake_write)
    monkeypatch.setattr(finnhub_api, "cached_earnings_calendar", lambda **kw: {})

    assert run_portfolio.main([]) == 0
    fresh = config.PORTFOLIO_REFRESH["max_age_hours"]
    assert fresh < 1
    assert seen["quote"] == [("QQQM", fresh), ("SGOV", fresh)]
    assert seen["write"] == (["QQQM", "SGOV"], fresh)


def test_state_writer_passes_freshness_to_price_series(monkeypatch, tmp_path):
    calls = []

    def fake_history(ticker, **kw):
        calls.append((ticker, kw.get("max_age_hours")))
        return []

    monkeypatch.setattr(pipeline, "CARDS_DIR", tmp_path)
    monkeypatch.setattr(pipeline.portfolio, "load", lambda: {"positions": [], "cash_usd": 0})
    monkeypatch.setattr(pipeline.portfolio, "tickers", lambda: ["SGOV"])
    monkeypatch.setattr(prices, "history", fake_history)
    monkeypatch.setattr(prices, "fx_rate", lambda *a, **k: {})
    monkeypatch.setattr(prices, "dividends", lambda *a, **k: [])
    monkeypatch.setattr(pipeline, "write_json", lambda *a, **k: True)
    from src import history
    monkeypatch.setattr(history, "load", lambda: [])
    monkeypatch.setattr(history, "write", lambda rows: True)

    pipeline.write_portfolio_state({}, {}, {"earnings": {}}, max_age_hours=0.25)
    assert calls and all(h == 0.25 for _, h in calls)
