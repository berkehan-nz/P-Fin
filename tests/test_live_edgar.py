"""CANLI EDGAR dogrulamasi — yalnizca ag erisimi olan ortamlarda calisir.

``tests/fixtures.py`` elle kurulmus rakamlar kullanir (hesap MOTORUNU
dogrulamak icin). Bu testler ise gercek SEC verisinin ayristirilabildigini
ve makul buyukluklerde degerler urettigini kontrol eder.

Calistirmak icin:
    python -m pytest tests/test_live_edgar.py -m network -v

Varsayilan kosuda ATLANIR (ag olmayan ortamda anlamsizca kirmizi yanmasin).
"""

import os

import pytest

pytestmark = pytest.mark.network

RUN = os.getenv("RUN_NETWORK_TESTS") == "1"
skip_reason = "Ag testleri kapali (RUN_NETWORK_TESTS=1 ile ac)"


@pytest.mark.skipif(not RUN, reason=skip_reason)
class TestEdgarLoad:
    def test_ticker_map_has_known_symbols(self):
        from src.sources import edgar_api
        tmap = edgar_api.ticker_map()
        assert len(tmap) > 5000
        assert tmap["AAPL"]["cik"] == 320193

    @pytest.mark.parametrize("ticker", ["DBX", "LSCC", "KVYO"])
    def test_company_loads_with_sane_values(self, ticker):
        from src import metrics
        from src.sources import edgar_api, prices

        f = edgar_api.load(ticker)
        assert f is not None, f"{ticker} yuklenemedi"
        assert f.cik, "CIK yok"
        assert f.sic, "SIC yok"
        assert len(f.quarters) >= 8, f"yalnizca {len(f.quarters)} ceyrek"

        prices.attach(f)
        assert f.price and f.price > 0, "fiyat alinamadi"
        assert f.shares_outstanding and f.shares_outstanding > 0, "hisse sayisi yok"

        r = metrics.compute(f)
        rev = r["meta"]["revenue_ttm_musd"]
        assert rev and rev > 0, "TTM hasilat hesaplanamadi"
        gm = r["metrics"]["gross_margin"]
        assert gm is not None and 0 < gm < 100, f"brut marj sacma: {gm}"
        mcap = r["meta"]["market_cap_musd"]
        assert mcap and mcap > 100, f"piyasa degeri sacma: {mcap}"

    def test_negative_equity_company_uses_roic_method_b(self):
        """DBX'in ozkaynagi negatif; canli veride de (b) yontemi secilmeli."""
        from src import metrics
        from src.sources import edgar_api, prices
        f = edgar_api.load("DBX")
        prices.attach(f)
        r = metrics.compute(f)
        if (f.ttm_period().equity or 0) <= 0:
            assert r["meta"]["roic_method"] == "b"
            assert r["flags"]["z_unreliable"] is True

    def test_q4_is_derived_not_missing(self):
        """Cogu sirket Q4'u ayri raporlamaz; turetilmis olmali."""
        from src.sources import edgar_api
        f = edgar_api.load("DBX")
        ends = {q.period_end[5:] for q in f.quarters}
        assert len(ends) >= 4, f"ceyrek sonlari eksik: {sorted(ends)}"


@pytest.mark.skipif(not RUN, reason=skip_reason)
class TestPrices:
    def test_stooq_or_yfinance_returns_history(self):
        from src.sources import prices
        q = prices.quote("AAPL")
        assert q["price"] and q["price"] > 0
        assert len(q["history"]) > 200
        assert q["high_52w"] >= q["price"] * 0.3

    def test_benchmark_available(self):
        from src.sources import prices
        assert len(prices.benchmark_history("QQQ")) > 200
