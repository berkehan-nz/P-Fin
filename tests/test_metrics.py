"""metrics.py dogrulamasi — sartnamedeki uc referans sirket."""

import pytest

from src import metrics
from src.config import STAGE3
from tests import fixtures


def approx(value, target, tol):
    assert value is not None, "deger hesaplanamadi (None)"
    assert abs(value - target) <= tol, f"{value} != {target} (+-{tol})"


# --------------------------------------------------------------------- DBX
@pytest.fixture(scope="module")
def dbx_r():
    return metrics.compute(fixtures.dbx())


@pytest.fixture(scope="module")
def lscc_r():
    return metrics.compute(fixtures.lscc())


@pytest.fixture(scope="module")
def kvyo_r():
    return metrics.compute(fixtures.kvyo())


class TestDBX:
    @pytest.fixture(autouse=True)
    def _bind(self, dbx_r):
        self.r = dbx_r

    def test_ev_ebit(self):
        r = self.r
        approx(r["metrics"]["ev_ebit"], 14.7, 0.15)

    def test_fcf_yield(self):
        r = self.r
        approx(r["metrics"]["fcf_yield_ev"], 9.1, 0.15)

    def test_negative_equity_forces_roic_method_b(self):
        r = self.r
        # Ozkaynak negatif -> (a) yontemi anlamsiz
        assert r["meta"]["roic_method"] == "b"

    def test_z_unreliable_flag(self):
        r = self.r
        assert r["flags"]["z_unreliable"] is True

    def test_enterprise_value_excludes_leases(self):
        r = self.r
        # 8601 mcap + 1980 borc - 1172 nakit = 9409; kiralama (385) DAHIL DEGIL
        approx(r["meta"]["enterprise_value_musd"], 9409, 1.0)
        approx(r["metrics"]["lease_liabilities"], 385, 0.01)

    def test_track_a(self):
        r = self.r
        assert metrics.track_for(r["metrics"], STAGE3["track_b_operating_margin_pct"]) == "A"

    def test_buybacks_show_as_negative_share_change(self):
        r = self.r
        assert r["metrics"]["share_count_change_1y"] < 0


# -------------------------------------------------------------------- LSCC
class TestLSCC:
    @pytest.fixture(autouse=True)
    def _bind(self, lscc_r):
        self.r = lscc_r

    def test_ev_sales(self):
        r = self.r
        approx(r["metrics"]["ev_sales"], 30.0, 0.3)

    def test_fcf_yield(self):
        r = self.r
        approx(r["metrics"]["fcf_yield_ev"], 0.8, 0.05)

    def test_roic_uses_method_a(self):
        r = self.r
        # Ozkaynak pozitif -> standart yontem
        assert r["meta"]["roic_method"] == "a"

    def test_net_cash_balance_sheet(self):
        r = self.r
        assert r["metrics"]["net_debt"] < 0


# -------------------------------------------------------------------- KVYO
class TestKVYO:
    @pytest.fixture(autouse=True)
    def _bind(self, kvyo_r):
        self.r = kvyo_r

    def test_ebit_negative(self):
        r = self.r
        assert r["meta"]["ebit_ttm_musd"] < 0

    def test_track_b(self):
        r = self.r
        assert metrics.track_for(r["metrics"], STAGE3["track_b_operating_margin_pct"]) == "B"

    def test_ev_gross_profit(self):
        r = self.r
        approx(r["metrics"]["ev_gross_profit"], 5.0, 0.1)

    def test_rule_of_40(self):
        r = self.r
        approx(r["metrics"]["rule_of_40"], 48.5, 0.5)

    def test_ev_ebit_is_none_when_ebit_negative(self):
        r = self.r
        # Negatif EBIT'te carpan anlamsiz — sayi uretmek yerine None
        assert r["metrics"]["ev_ebit"] is None
        assert r["metrics"]["pe"] is None

    def test_rule_of_40_gap_is_sbc_driven(self):
        r = self.r
        # EBITDA varyanti FCF varyantindan yuksek olmali (SBC farki)
        assert r["metrics"]["rule_of_40_gap"] is not None


# ------------------------------------------------------- genel dayaniklilik
class TestRobustness:
    def test_empty_fundamentals_does_not_crash(self):
        from src.fundamentals import Fundamentals
        r = metrics.compute(Fundamentals(ticker="ZZZZ"))
        assert r["metrics"]["ev_ebit"] is None
        assert r["meta"]["market_cap_musd"] is None

    def test_missing_price_yields_no_valuation(self):
        f = fixtures.dbx()
        f.price = None
        r = metrics.compute(f)
        assert r["metrics"]["ev_ebit"] is None
        # ama isletme metrikleri hala hesaplanmali
        assert r["metrics"]["gross_margin"] is not None

    def test_market_cap_is_price_times_shares(self):
        f = fixtures.dbx()
        assert f.market_cap() == pytest.approx(28.67 * 300.0)

    def test_one_off_earnings_detected(self):
        # LYFT tipi: net kar EBIT'in 2 katindan fazla (vergi varligi kaydi)
        f = fixtures.dbx()
        f.annuals[-1].net_income = 1500      # EBIT 640
        f.annuals[-1].pretax_income = 300
        f.annuals[-1].tax_expense = -1200    # negatif vergi
        r = metrics.compute(f)
        assert r["flags"]["one_off_earnings"] is True

    def test_organic_growth_suspect_on_large_cap_fast_growth(self):
        # CPAY/GPN/NTAP tipi: bu olcekte %20+ buyume organik olamaz
        f = fixtures.kvyo()
        f.price = 60.0            # mcap 16.8B > 10B esigi
        r = metrics.compute(f)
        assert r["flags"]["rev_growth_organic_suspect"] is True

    def test_goodwill_jump_flags_acquisition(self):
        f = fixtures.lscc()
        f.annuals[-1].goodwill = 400     # 285 -> 400, %40 artis
        r = metrics.compute(f)
        assert r["flags"]["rev_growth_organic_suspect"] is True


class TestNetDebtConsistency:
    """EV ve net borc ayni kurali izlemeli.

    MNTN'de gorulen: borc etiketi yokken EV hesaplandi (borc 0 sayildi) ama
    net_debt None dondu; kartta EV dolu, net borc bos gorunuyordu.
    """

    def test_missing_debt_with_known_cash_is_treated_as_zero(self):
        f = fixtures.lscc()
        p = f.annuals[-1]
        p.long_term_debt = None
        p.short_term_debt = None
        r = metrics.compute(f)
        # nakit 130, borc yok -> net borc -130
        assert r["metrics"]["net_debt"] == pytest.approx(-130.0)

    def test_net_debt_matches_ev_minus_market_cap(self):
        f = fixtures.dbx()
        r = metrics.compute(f)
        ev = r["meta"]["enterprise_value_musd"]
        mcap = r["meta"]["market_cap_musd"]
        assert r["metrics"]["net_debt"] == pytest.approx(ev - mcap, abs=0.01)

    def test_no_balance_sheet_data_gives_none(self):
        from src.fundamentals import Fundamentals
        r = metrics.compute(Fundamentals(ticker="ZZZZ"))
        assert r["metrics"]["net_debt"] is None


class TestCashFlowGroupCoherence:
    """Nakit akis kalemleri TEK PARCA karar vermeli.

    SONO'da gorulen: CFO ceyreklerden toplaniyor, yatirim harcamasi yillik
    tablodan geliyordu; FCF iki farkli tabanin farki oldugu icin ceyrek
    toplami (130,4) ile TTM (147,1) uyusmuyordu.
    """

    def _quarters_with_gap(self):
        from src.fundamentals import Fundamentals, Period
        f = Fundamentals(ticker="MIX")
        # 4 ceyrek: CFO hepsinde var, capex son ceyrekte YOK
        for i, (cfo, capex) in enumerate([(100, 10), (110, 12), (120, 11), (130, None)]):
            f.quarters.append(Period(period_end=f"2025-{(i + 1) * 3:02d}-30",
                                     period_type="Q", revenue=1000,
                                     cfo=cfo, capex=capex))
        f.annuals.append(Period(period_end="2025-12-31", period_type="FY",
                                revenue=4000, cfo=460, capex=45))
        return f

    def test_whole_group_falls_back_together(self):
        p = self._quarters_with_gap().ttm_period()
        # capex eksik -> CFO da yillik tabloya dusmeli
        assert p.cfo == 460
        assert p.capex == 45
        assert p.fcf == 415

    def test_fcf_is_never_mixed_basis(self):
        p = self._quarters_with_gap().ttm_period()
        # 460-45=415 tutarli; 460(ceyrek toplami) - 45(yillik) = 415 olsaydi
        # rastlanti olurdu. Asil kontrol: cfo ve capex ayni kaynaktan.
        assert p.cfo == 460 and p.capex == 45

    def test_complete_quarters_still_summed(self):
        from src.fundamentals import Fundamentals, Period
        f = Fundamentals(ticker="OK")
        for i, (cfo, capex) in enumerate([(100, 10), (110, 12), (120, 11), (130, 13)]):
            f.quarters.append(Period(period_end=f"2025-{(i + 1) * 3:02d}-30",
                                     period_type="Q", revenue=1000,
                                     cfo=cfo, capex=capex))
        p = f.ttm_period()
        assert p.cfo == 460 and p.capex == 46 and p.fcf == 414

    def test_field_missing_everywhere_does_not_force_fallback(self):
        """Hic yatirim harcamasi raporlamayan sirkette CFO ceyreklerden gelmeli."""
        from src.fundamentals import Fundamentals, Period
        f = Fundamentals(ticker="NOCAPEX")
        for i, cfo in enumerate([100, 110, 120, 130]):
            f.quarters.append(Period(period_end=f"2025-{(i + 1) * 3:02d}-30",
                                     period_type="Q", revenue=1000, cfo=cfo))
        f.annuals.append(Period(period_end="2025-12-31", period_type="FY",
                                revenue=4000, cfo=999))
        p = f.ttm_period()
        assert p.cfo == 460          # yillik 999'a DUSMEMELI


class TestCouplingIsNarrow:
    """Baglanti kumesi DAR olmali.

    Ilk denemede tum nakit akis tablosunu (temettu, hisse ihraci,
    amortisman...) birbirine bagladim. Cogu sirket bunlarin bir kismini
    ceyreklik raporlamadigi icin 36 kartin HEPSI yillik tabloya dustu ve
    "mixed" oldu — ceyreklik veri varken bile kullanilmadi.
    """

    def _f(self, **quarter_overrides):
        from src.fundamentals import Fundamentals, Period
        f = Fundamentals(ticker="C")
        for i in range(4):
            p = Period(period_end=f"2025-{(i + 1) * 3:02d}-30", period_type="Q",
                       revenue=1000, cfo=100, capex=10, net_income=50)
            for k, vals in quarter_overrides.items():
                setattr(p, k, vals[i])
            f.quarters.append(p)
        f.annuals.append(Period(period_end="2025-12-31", period_type="FY",
                                revenue=4000, cfo=999, capex=99, net_income=200,
                                dividends_paid=40, sbc=80, cfi=-50))
        return f

    def test_missing_dividends_does_not_drag_down_cfo(self):
        """Temettu ceyreklik yoksa CFO yine ceyreklerden gelmeli."""
        p = self._f().ttm_period()
        assert p.cfo == 400          # yillik 999'a DUSMEMELI
        assert p.capex == 40

    def test_missing_capex_still_couples_cfo(self):
        """Ama FCF ciftinde eksik varsa ikisi birlikte duser."""
        p = self._f(capex=[10, 10, 10, None]).ttm_period()
        assert p.cfo == 999
        assert p.capex == 99

    def test_data_basis_not_mixed_when_only_uncoupled_missing(self):
        from src import metrics
        f = self._f()
        r = metrics.compute(f)
        assert r["meta"]["data_basis"] == "quarterly_ttm"


class TestQuarterlyFcfSeries:
    """Ceyreklik FCF serisi TTM ile ayni sayiyi anlatmali."""

    def _f(self, capex_vals):
        from src.fundamentals import Fundamentals, Period
        f = Fundamentals(ticker="S")
        for i in range(4):
            f.quarters.append(Period(
                period_end=f"2025-{(i + 1) * 3:02d}-30", period_type="Q",
                revenue=1000, cfo=100, capex=capex_vals[i]))
        return f

    def test_missing_capex_gives_none_not_inflated_fcf(self):
        from src import cards
        s = cards._build_series(self._f([10, 10, 10, None]))
        assert s["fcf"] == [90, 90, 90, None]      # son ceyrek 100 OLMAMALI

    def test_company_without_capex_uses_cfo(self):
        from src import cards
        s = cards._build_series(self._f([None, None, None, None]))
        assert s["fcf"] == [100, 100, 100, 100]

    def test_series_sum_matches_ttm_when_complete(self):
        from src import cards
        f = self._f([10, 12, 11, 13])
        s = cards._build_series(f)
        assert sum(s["fcf"]) == f.ttm_period().fcf
