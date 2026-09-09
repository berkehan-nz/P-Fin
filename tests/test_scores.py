"""scores.py dogrulamasi — Piotroski, Altman, Beneish, Sloan, ters DCF."""

import pytest

from src import metrics, scores
from tests import fixtures


class TestPiotroski:
    def test_dbx_is_6(self):
        f = fixtures.dbx()
        r = scores.piotroski_f(f.ttm_period(), f.ttm_period(offset=4))
        assert r["score"] == 6, r["tests"]

    def test_lscc_is_5(self):
        f = fixtures.lscc()
        r = scores.piotroski_f(f.ttm_period(), f.ttm_period(offset=4))
        assert r["score"] == 5, r["tests"]

    def test_kvyo_is_4(self):
        f = fixtures.kvyo()
        r = scores.piotroski_f(f.ttm_period(), f.ttm_period(offset=4))
        assert r["score"] == 4, r["tests"]

    def test_missing_data_is_none_not_zero(self):
        """Eksik veri 0 puan degil, 'bilinmiyor' olarak raporlanmali."""
        from src.fundamentals import Period
        r = scores.piotroski_f(Period(period_end="2025-12-31"), Period(period_end="2024-12-31"))
        assert r["score"] is None
        assert r["max_possible"] == 0


class TestAltman:
    def test_lscc_z(self):
        f = fixtures.lscc()
        r = scores.altman_z(f.ttm_period())
        assert r["z"] == pytest.approx(10.4, abs=0.15)
        assert r["unreliable"] is False

    def test_dbx_negative_equity_is_unreliable(self):
        f = fixtures.dbx()
        r = scores.altman_z(f.ttm_period())
        assert r["unreliable"] is True
        # Yerine bakilacak yedek olculer uretilmeli
        fb = scores.solvency_fallback(f.ttm_period())
        assert fb["interest_coverage"] is not None
        assert fb["fcf_to_total_debt"] is not None


class TestBeneish:
    def test_dbx_m(self):
        f = fixtures.dbx()
        r = scores.beneish_m(f.ttm_period(), f.ttm_period(offset=4))
        assert r["m"] == pytest.approx(-3.1, abs=0.15)
        assert r["missing"] == []

    def test_components_present(self):
        f = fixtures.lscc()
        r = scores.beneish_m(f.ttm_period(), f.ttm_period(offset=4))
        assert set(r["components"]) == {"DSRI", "GMI", "AQI", "SGI", "DEPI",
                                        "SGAI", "TATA", "LVGI"}


class TestSloan:
    def test_dbx_accruals_negative(self):
        # CFO net kardan cok yuksek -> tahakkuk negatif (saglikli)
        f = fixtures.dbx()
        assert scores.sloan_accruals(f.ttm_period()) < 0

    def test_formula(self):
        from src.fundamentals import Period
        p = Period(period_end="2025-12-31", net_income=100, cfo=80, cfi=-30, assets=1000)
        # (100 - 80 - (-30)) / 1000 = 0.05
        assert scores.sloan_accruals(p) == pytest.approx(0.05)


class TestReverseDCF:
    def test_round_trip(self):
        """dcf_value ile implied_growth birbirinin tersi olmali."""
        fcf0, g = 100.0, 0.08
        ev = scores.dcf_value(fcf0, g)
        assert scores.implied_growth(fcf0, ev) == pytest.approx(8.0, abs=0.05)

    def test_negative_fcf_returns_none(self):
        assert scores.implied_growth(-50, 1000) is None
        assert scores.implied_growth(0, 1000) is None

    def test_expensive_company_implies_high_growth(self):
        f = fixtures.lscc()
        r = metrics.compute(f)
        s = scores.compute(f, r)
        # EV/Hasilat 30 -> fiyat cok yuksek buyume varsayiyor
        assert s["metrics"]["implied_growth"] > 25

    def test_cheap_company_implies_low_growth(self):
        f = fixtures.dbx()
        r = metrics.compute(f)
        s = scores.compute(f, r)
        assert s["metrics"]["implied_growth"] < 10


class TestScoresIntegration:
    @pytest.mark.parametrize("name", ["DBX", "LSCC", "KVYO"])
    def test_compute_produces_all_keys(self, name):
        f = fixtures.ALL[name]()
        r = metrics.compute(f)
        s = scores.compute(f, r)
        for key in ("piotroski_f", "altman_z", "beneish_m", "sloan_accruals",
                    "implied_growth", "implied_vs_actual_growth"):
            assert key in s["metrics"]

    def test_empty_company_does_not_crash(self):
        from src.fundamentals import Fundamentals
        f = Fundamentals(ticker="ZZZZ")
        r = metrics.compute(f)
        s = scores.compute(f, r)
        assert s["metrics"]["piotroski_f"] is None


class TestImpliedGrowthRatio:
    """Ima edilen/gerceklesen orani yalnizca ikisi de pozitifken anlamlidir.

    DOCU'da gorulen: fiyat %-1,0 buyume varsayiyordu, sirket %8,6 buyuyordu.
    Oran -0,12 cikiyor ve "gerceklesenin -0,12 katini varsayiyor" gibi
    yorumlanamaz bir cumleye donusuyordu.
    """

    def _res(self, implied, actual):
        f = fixtures.dbx()
        r = metrics.compute(f)
        r["metrics"]["rev_cagr_3y"] = actual
        r["meta"]["fcf_ttm_musd"] = 100.0
        r["meta"]["enterprise_value_musd"] = 1000.0
        s = scores.compute(f, r)
        s["metrics"]["implied_growth"] = implied
        # orani yeniden hesaplat
        return scores.compute(f, r)

    def test_negative_implied_growth_gives_no_ratio(self):
        f = fixtures.dbx()
        r = metrics.compute(f)
        r["metrics"]["rev_cagr_3y"] = 8.6
        # cok ucuz -> ima edilen buyume negatif
        r["meta"]["fcf_ttm_musd"] = 500.0
        r["meta"]["enterprise_value_musd"] = 3000.0
        s = scores.compute(f, r)
        if s["metrics"]["implied_growth"] is not None and s["metrics"]["implied_growth"] <= 0:
            assert s["metrics"]["implied_vs_actual_growth"] is None

    def test_both_positive_gives_ratio(self):
        f = fixtures.lscc()
        r = metrics.compute(f)
        s = scores.compute(f, r)
        if (s["metrics"]["implied_growth"] or 0) > 0 and (r["metrics"]["rev_cagr_3y"] or 0) > 0:
            assert s["metrics"]["implied_vs_actual_growth"] is not None
            assert s["metrics"]["implied_vs_actual_growth"] > 0

    def test_negative_actual_growth_gives_no_ratio(self):
        f = fixtures.dbx()      # hasilati daraliyor
        r = metrics.compute(f)
        s = scores.compute(f, r)
        assert r["metrics"]["rev_cagr_3y"] < 0
        assert s["metrics"]["implied_vs_actual_growth"] is None
