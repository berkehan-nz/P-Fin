"""run_daily._refresh_price_derived — fiyat degisince carpanlar dogru mu?"""

import pytest

from src import cards, run_daily
from tests import fixtures


def base_card():
    return cards.build(fixtures.dbx(), source="test")


class TestPriceRefresh:
    def test_card_stores_ttm_and_shares(self):
        c = base_card()
        assert c["shares_outstanding_m"] == pytest.approx(300.0)
        assert c["ttm"]["ebit_musd"] == pytest.approx(640.0)
        assert c["net_debt_musd"] == pytest.approx(808.0)   # 1980 - 1172

    def test_doubling_price_doubles_market_cap(self):
        c = base_card()
        quote = {"price": 57.34, "history": [], "high_52w": 60.0}
        run_daily._refresh_price_derived(c, quote, [])
        assert c["market_cap_musd"] == pytest.approx(17202.0, abs=1)
        # EV = mcap + net borc
        assert c["enterprise_value_musd"] == pytest.approx(18010.0, abs=1)

    def test_multiples_recomputed_not_scaled(self):
        c = base_card()
        run_daily._refresh_price_derived(
            c, {"price": 28.67, "history": [], "high_52w": 32.0}, [])
        # ayni fiyat -> ayni carpan (sapma yok)
        assert c["metrics"]["ev_ebit"]["value"] == pytest.approx(14.702, abs=0.01)
        assert c["metrics"]["fcf_yield_ev"]["value"] == pytest.approx(9.098, abs=0.01)

    def test_repeated_refresh_does_not_drift(self):
        """Ayni fiyatla 10 kez tazelemek carpani kaydirmamali."""
        c = base_card()
        quote = {"price": 28.67, "history": [], "high_52w": 32.0}
        for _ in range(10):
            run_daily._refresh_price_derived(c, quote, [])
        assert c["metrics"]["ev_ebit"]["value"] == pytest.approx(14.702, abs=0.001)

    def test_cheaper_price_lifts_fcf_yield(self):
        c = base_card()
        run_daily._refresh_price_derived(
            c, {"price": 14.34, "history": [], "high_52w": 32.0}, [])
        assert c["metrics"]["fcf_yield_ev"]["value"] > 9.098
        assert c["metrics"]["ev_ebit"]["value"] < 14.702

    def test_colors_follow_new_values(self):
        c = base_card()
        run_daily._refresh_price_derived(
            c, {"price": 5.0, "history": [], "high_52w": 32.0}, [])
        # cok ucuz -> EV/EBIT yesil
        assert c["metrics"]["ev_ebit"]["color"] == "green"

    def test_negative_ebit_keeps_multiple_none(self):
        c = cards.build(fixtures.kvyo(), source="test")
        run_daily._refresh_price_derived(
            c, {"price": 25.0, "history": [], "high_52w": 30.0}, [])
        assert c["metrics"]["ev_ebit"]["value"] is None
        assert c["metrics"]["ev_gross_profit"]["value"] is not None

    def test_missing_price_data_does_not_crash(self):
        c = base_card()
        run_daily._refresh_price_derived(c, {"price": None, "history": []}, [])
        assert c["ticker"] == "DBX"

    def test_off_52w_high(self):
        c = base_card()
        run_daily._refresh_price_derived(
            c, {"price": 25.0, "history": [], "high_52w": 50.0}, [])
        assert c["metrics"]["pct_off_52w_high"]["value"] == pytest.approx(50.0)
