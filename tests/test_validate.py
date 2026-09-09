"""validate.py — sessiz yanlis sayilari yakalayan guvenlik agi.

Bu testler gercek EDGAR verisinde YASANMIS hatalari kullaniyor
(LYFT kismi TTM, MNTN eksik hisse sayisi, WDAY brut kar yoklugu).
"""

from src import cards, validate
from src.fundamentals import Fundamentals, Period, build_annual_fundamentals
from tests import fixtures


def bare_card(**over):
    c = {
        "ticker": "TEST", "price": 10.0, "market_cap_musd": 1000.0,
        "enterprise_value_musd": 1100.0, "shares_outstanding_m": 100.0,
        "ttm": {"revenue_musd": 500.0, "ebit_musd": 50.0,
                "gross_profit_musd": 300.0},
        "metrics": {}, "series": {}, "flags": {},
        "data_sources": {"shares": "kapak_sayfasi"},
    }
    c.update(over)
    return c


def cell(v, color="green"):
    return {"value": v, "color": color, "sector_pct": None,
            "own_5y_pct": None, "pct_basis": "none"}


class TestImpossibleValues:
    def test_negative_gross_margin_is_flagged_not_deleted(self):
        """LYFT'te gorulen: satis maliyeti etiketi yanlis eslesince brut marj
        -%21 cikmisti. Ama negatif brut marj GERCEKTEN mumkun (maliyetin
        altina satan sirket), o yuzden silinmez — isaretlenir."""
        c = bare_card(metrics={"gross_margin": cell(-21.2)})
        dq = validate.check(c)
        assert c["metrics"]["gross_margin"]["value"] == -21.2
        assert any(i["code"] == "supheli_gross_margin" for i in dq["issues"])
        assert dq["status"] == "sinirli"

    def test_impossible_gross_margin_is_deleted(self):
        """%100 ustu brut marj satis maliyetinin negatif oldugunu ima eder."""
        c = bare_card(metrics={"gross_margin": cell(140.0)})
        dq = validate.check(c)
        assert c["metrics"]["gross_margin"]["value"] is None
        assert c["metrics"]["gross_margin"]["color"] == "gray"
        assert dq["status"] == "kotu"

    def test_valid_gross_margin_kept(self):
        c = bare_card(metrics={"gross_margin": cell(72.5)})
        dq = validate.check(c)
        assert c["metrics"]["gross_margin"]["value"] == 72.5
        assert dq["status"] == "iyi"

    def test_piotroski_out_of_range_deleted(self):
        c = bare_card(metrics={"piotroski_f": cell(14)})
        validate.check(c)
        assert c["metrics"]["piotroski_f"]["value"] is None

    def test_slightly_negative_gross_margin_kept(self):
        """Gercekten zarar eden sirketlerde -%5 brut marj mumkun."""
        c = bare_card(metrics={"gross_margin": cell(-5.0)})
        validate.check(c)
        assert c["metrics"]["gross_margin"]["value"] == -5.0


class TestShareCountProblems:
    def test_negative_ev_with_positive_ebit_is_flagged(self):
        """MNTN'de gorulen: hisse sayisi tek sinif yakalaninca piyasa degeri
        kucuk cikti, EV negatife dondu ama sirket kar ediyordu."""
        c = bare_card(enterprise_value_musd=-26.7,
                      ttm={"revenue_musd": 313.0, "ebit_musd": 44.7,
                           "gross_profit_musd": 253.0})
        dq = validate.check(c)
        assert dq["status"] == "kotu"
        issue = next(i for i in dq["issues"] if i["code"] == "ev_negatif")
        assert "cok sinifli" in issue["message"]

    def test_missing_share_count_is_high_severity(self):
        c = bare_card(shares_outstanding_m=None, market_cap_musd=None,
                      enterprise_value_musd=None)
        dq = validate.check(c)
        assert dq["status"] == "kotu"
        assert any(i["code"] == "hisse_sayisi_yok" for i in dq["issues"])

    def test_fallback_share_source_is_noted(self):
        """Dusuk onemli not: kart kullanilabilir, durum 'iyi' kalir."""
        c = bare_card(data_sources={"shares": "seyreltilmis_agirlikli_ortalama"})
        dq = validate.check(c)
        assert any(i["code"] == "hisse_sayisi_tahmini" for i in dq["issues"])
        assert dq["status"] == "iyi"

    def test_negative_ev_without_profit_is_not_flagged(self):
        """Zarar eden, nakit zengini sirkette negatif EV normaldir."""
        c = bare_card(enterprise_value_musd=-50.0,
                      ttm={"revenue_musd": 100.0, "ebit_musd": -20.0,
                           "gross_profit_musd": 60.0})
        dq = validate.check(c)
        assert not any(i["code"] == "ev_negatif" for i in dq["issues"])


class TestMissingFundamentals:
    def test_missing_revenue_with_ebit_flagged(self):
        """CPAY'de gorulen: FVOK var ama hasilat etiketi eslesmedi."""
        c = bare_card(ttm={"revenue_musd": None, "ebit_musd": 2110.9,
                           "gross_profit_musd": None})
        dq = validate.check(c)
        assert any(i["code"] == "hasilat_yok" for i in dq["issues"])
        assert dq["status"] == "kotu"

    def test_missing_gross_profit_warns_about_stage1(self):
        """WDAY'de gorulen: brut marj Asama 1'de sert filtre, eksikse
        sirket haksiz elenir."""
        c = bare_card(ttm={"revenue_musd": 10155.0, "ebit_musd": 1085.0,
                           "gross_profit_musd": None})
        dq = validate.check(c)
        issue = next(i for i in dq["issues"] if i["code"] == "brut_kar_yok")
        assert "Asama 1" in issue["message"]

    def test_quarterly_gap_flagged(self):
        """LYFT'te gorulen: son iki ceyrek bos."""
        c = bare_card(series={"revenue": [100, 110, None, None]})
        dq = validate.check(c)
        issue = next(i for i in dq["issues"] if i["code"] == "ceyrek_bosluklu")
        assert "2 tanesinde" in issue["message"]

    def test_complete_quarters_not_flagged(self):
        c = bare_card(series={"revenue": [100, 110, 120, 130]})
        dq = validate.check(c)
        assert not any(i["code"] == "ceyrek_bosluklu" for i in dq["issues"])


class TestSuspiciousButKept:
    def test_extreme_growth_flagged_not_deleted(self):
        c = bare_card(metrics={"rev_growth_ttm": cell(-75.0)})
        dq = validate.check(c)
        assert c["metrics"]["rev_growth_ttm"]["value"] == -75.0   # silinmez
        assert any(i["code"] == "supheli_rev_growth_ttm" for i in dq["issues"])

    def test_severe_but_real_decline_is_not_flagged(self):
        """-%46 hasilat dususu sert ama gercek olabilir; yanlis alarm verme."""
        c = bare_card(metrics={"rev_growth_ttm": cell(-46.5)})
        dq = validate.check(c)
        assert not any(i["code"] == "supheli_rev_growth_ttm" for i in dq["issues"])

    def test_normal_growth_not_flagged(self):
        c = bare_card(metrics={"rev_growth_ttm": cell(24.0)})
        dq = validate.check(c)
        assert dq["status"] == "iyi"


class TestWarningsPropagate:
    def test_high_issues_reach_card_warnings(self):
        c = bare_card(shares_outstanding_m=None, market_cap_musd=None)
        validate.check(c)
        assert any("VERI KALITESI" in w for w in c["flags"]["warnings"])

    def test_low_issues_do_not_spam_warnings(self):
        c = bare_card(data_sources={"shares": "seyreltilmis_agirlikli_ortalama"})
        validate.check(c)
        assert not any("VERI KALITESI" in w for w in c["flags"]["warnings"])


class TestRealCards:
    def test_clean_fixture_card_passes(self):
        c = cards.build(fixtures.lscc(), source="test")
        assert c["data_quality"]["status"] in ("iyi", "sinirli")

    def test_every_card_gets_data_quality_block(self):
        for name in ("DBX", "LSCC", "KVYO"):
            c = cards.build(fixtures.ALL[name](), source="test")
            assert "data_quality" in c
            assert c["data_quality"]["status"] in ("iyi", "sinirli", "kotu")

    def test_summarize_counts_statuses(self):
        cs = [cards.build(fixtures.ALL[n](), source="test")
              for n in ("DBX", "LSCC", "KVYO")]
        s = validate.summarize(cs)
        assert sum(s["counts"].values()) == 3


class TestPartialTtmBugIsFixed:
    """LYFT hatasi: son iki ceyrekte hasilat yokken ttm_period() eksikleri
    atlayip 2 ceyreklik toplami TTM diye sunuyordu."""

    def _fund_with_gap(self):
        f = Fundamentals(ticker="GAP")
        vals = [1000, 1100, 1200, 1300, None, None]
        for i, v in enumerate(vals):
            f.quarters.append(Period(period_end=f"2025-{(i % 4) * 3 + 3:02d}-30",
                                     period_type="Q", revenue=v, assets=5000))
        # tarihleri artan yap
        for i, p in enumerate(f.quarters):
            p.period_end = f"20{24 + i // 4}-{(i % 4) * 3 + 3:02d}-30"
        return f

    def test_partial_window_does_not_produce_partial_sum(self):
        f = self._fund_with_gap()
        ttm = f.ttm_period()
        # Son 4 ceyrek: 1200, 1300, None, None -> kismi toplam 2500 OLMAMALI
        assert ttm.revenue != 2500
        assert ttm.revenue is None

    def test_falls_back_to_annual_when_quarters_incomplete(self):
        f = self._fund_with_gap()
        f.annuals.append(Period(period_end="2025-12-31", period_type="FY",
                                revenue=4600))
        assert f.ttm_period().revenue == 4600

    def test_complete_window_still_sums(self):
        f = build_annual_fundamentals("OK", [])
        for i, v in enumerate([1000, 1100, 1200, 1300]):
            f.quarters.append(Period(period_end=f"2025-{(i + 1) * 3:02d}-30",
                                     period_type="Q", revenue=v))
        assert f.ttm_period().revenue == 4600

    def test_share_count_is_averaged_not_summed(self):
        """Hisse sayisi agirlikli ORTALAMADIR; 4 ceyregi toplamak sacmadir."""
        f = build_annual_fundamentals("SH", [])
        for i, v in enumerate([100, 101, 102, 103]):
            f.quarters.append(Period(period_end=f"2025-{(i + 1) * 3:02d}-30",
                                     period_type="Q", revenue=10,
                                     shares_diluted=v))
        assert f.ttm_period().shares_diluted == 103      # 406 DEGIL
