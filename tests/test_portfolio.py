"""portfolio.py — K/Z, agirlik, benchmark farki, uyarilar."""

from datetime import date, timedelta

import pytest

from src import portfolio


@pytest.fixture
def sample(tmp_path, monkeypatch):
    """Gercek data/portfolio.json'a dokunmadan test portfoyu kurar."""
    path = tmp_path / "portfolio.json"
    monkeypatch.setattr(portfolio, "PATH", path)
    return path


def write(path, positions, cash=1000.0):
    import json
    path.write_text(json.dumps({"positions": positions, "closed": [],
                                "cash_usd": cash}), encoding="utf-8")


def days_ago(n):
    return (date.today() - timedelta(days=n)).isoformat()


def days_ahead(n):
    return (date.today() + timedelta(days=n)).isoformat()


class TestPnL:
    def test_cost_includes_fees(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(30), 25.0, 100, fees_usd=5.0)])
        r = portfolio.compute({"DBX": {"price": 30.0}})
        assert r["positions"][0]["cost_usd"] == pytest.approx(2505.0)

    def test_pnl_dollar_and_percent(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(30), 25.0, 100, fees_usd=5.0)])
        r = portfolio.compute({"DBX": {"price": 30.0}})
        p = r["positions"][0]
        assert p["value_usd"] == pytest.approx(3000.0)
        assert p["pnl_usd"] == pytest.approx(495.0)
        assert p["pnl_pct"] == pytest.approx(19.76, abs=0.01)

    def test_weight_includes_cash(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(10), 25.0, 100)], cash=500.0)
        r = portfolio.compute({"DBX": {"price": 25.0}})
        # 2500 / (2500 + 500) = %83.33
        assert r["positions"][0]["weight_pct"] == pytest.approx(83.33, abs=0.01)

    def test_missing_price_does_not_crash(self, sample):
        write(sample, [portfolio.json_snippet("ZZZZ", days_ago(10), 25.0, 100)])
        r = portfolio.compute({})
        assert r["positions"][0]["value_usd"] is None
        assert r["positions"][0]["pnl_usd"] is None

    def test_upside_to_target(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(10), 25.0, 100,
                                              target_price=40.0)])
        r = portfolio.compute({"DBX": {"price": 32.0}})
        assert r["positions"][0]["upside_to_target_pct"] == pytest.approx(25.0)


class TestBenchmark:
    def test_excess_return_since_entry(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(100), 25.0, 100)])
        bench = [(days_ago(120), 100.0), (days_ago(100), 100.0), (days_ago(0), 110.0)]
        r = portfolio.compute({"DBX": {"price": 30.0}}, {"QQQ": bench, "SPY": bench})
        vb = r["positions"][0]["vs_benchmark"]["nasdaq100"]
        assert vb["benchmark_return_pct"] == pytest.approx(10.0)
        # pozisyon %20 getirdi, endeks %10 -> %10 fark
        assert vb["excess_pct"] == pytest.approx(10.0, abs=0.1)

    def test_portfolio_level_excess_is_value_weighted(self, sample):
        write(sample, [
            portfolio.json_snippet("A", days_ago(100), 10.0, 900),   # 9000 USD
            portfolio.json_snippet("B", days_ago(100), 10.0, 100),   # 1000 USD
        ], cash=0.0)
        bench = [(days_ago(100), 100.0), (days_ago(0), 100.0)]
        r = portfolio.compute({"A": {"price": 20.0}, "B": {"price": 5.0}},
                              {"QQQ": bench, "SPY": bench})
        # A +%100 (18000), B -%50 (500) -> agirlikli
        assert r["summary"]["vs_benchmark"]["nasdaq100"] is not None


class TestWarnings:
    def test_concentration_warning(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(10), 25.0, 100)], cash=0.0)
        r = portfolio.compute({"DBX": {"price": 25.0}})
        assert any(w["type"] == "konsantrasyon" for w in r["warnings"])

    def test_overdue_review_warning(self, sample):
        pos = portfolio.json_snippet("DBX", days_ago(200), 25.0, 10)
        pos["review_date"] = days_ago(15)
        write(sample, [pos], cash=100000.0)
        r = portfolio.compute({"DBX": {"price": 25.0}})
        assert any(w["type"] == "gozden_gecirme" for w in r["warnings"])

    def test_thesis_breaker_warning(self, sample):
        pos = portfolio.json_snippet("DBX", days_ago(10), 25.0, 10)
        pos["thesis_breakers"] = [
            {"description": "Brut marj %70'in altina duserse", "triggered": True},
            {"description": "Net musteri kaybi", "triggered": False},
        ]
        write(sample, [pos], cash=100000.0)
        r = portfolio.compute({"DBX": {"price": 25.0}})
        breakers = [w for w in r["warnings"] if w["type"] == "tez_kirici"]
        assert len(breakers) == 1

    def test_tax_year_warning(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(350), 25.0, 10)],
              cash=100000.0)
        r = portfolio.compute({"DBX": {"price": 25.0}})
        assert any(w["type"] == "vergi" for w in r["warnings"])

    def test_no_tax_warning_after_one_year(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(400), 25.0, 10)],
              cash=100000.0)
        r = portfolio.compute({"DBX": {"price": 25.0}})
        assert not any(w["type"] == "vergi" for w in r["warnings"])

    def test_earnings_warning(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(30), 25.0, 10)],
              cash=100000.0)
        r = portfolio.compute({"DBX": {"price": 25.0}}, earnings={"DBX": days_ahead(3)})
        assert any(w["type"] == "kazanc" for w in r["warnings"])

    def test_distant_earnings_no_warning(self, sample):
        write(sample, [portfolio.json_snippet("DBX", days_ago(30), 25.0, 10)],
              cash=100000.0)
        r = portfolio.compute({"DBX": {"price": 25.0}}, earnings={"DBX": days_ahead(45)})
        assert not any(w["type"] == "kazanc" for w in r["warnings"])

    def test_warnings_sorted_by_severity(self, sample):
        pos = portfolio.json_snippet("DBX", days_ago(350), 25.0, 100)
        pos["review_date"] = days_ago(10)
        write(sample, [pos], cash=0.0)
        r = portfolio.compute({"DBX": {"price": 25.0}})
        levels = [w["level"] for w in r["warnings"]]
        assert levels == sorted(levels, key=lambda l: {"high": 0, "medium": 1, "low": 2}[l])


class TestSectorMix:
    def test_sector_allocation(self, sample):
        write(sample, [
            portfolio.json_snippet("A", days_ago(10), 10.0, 100),
            portfolio.json_snippet("B", days_ago(10), 10.0, 100),
        ], cash=0.0)
        cards = {"A": {"sector": "Yazilim"}, "B": {"sector": "Yazilim"}}
        r = portfolio.compute({"A": {"price": 10.0}, "B": {"price": 10.0}}, cards=cards)
        assert r["summary"]["sector_mix_pct"]["Yazilim"] == pytest.approx(100.0)

    def test_closed_positions_excluded(self, sample):
        pos = portfolio.json_snippet("DBX", days_ago(10), 25.0, 100)
        pos["status"] = "CLOSED"
        write(sample, [pos])
        r = portfolio.compute({"DBX": {"price": 30.0}})
        assert r["summary"]["position_count"] == 0


class TestAssetClasses:
    """Portfoy artik yalnizca hisse tasimiyor: ETF ve TL mevduat da var.

    Her sinif FARKLI degerlenir. TL mevduatta "adet x fiyat" yoktur;
    anapara + tahakkuk eden net faiz, kurla dolara cevrilir.
    """

    def test_tl_deposit_accrues_net_interest(self):
        from src import portfolio as P

        pos = {
            "asset_class": "TL_DEPOSIT",
            "principal_try": 100_000.0,
            "annual_rate_pct": 50.0,
            "withholding_pct": 15.0,
            "start_date": days_ago(365),
            "maturity_date": days_ago(0),
            "usdtry_at_entry": 40.0,
        }
        out = P.tl_deposit_value(pos, usdtry=48.0)
        # Bir yil, %50 brut -> 50.000 TL; %15 stopaj -> 42.500 TL net
        assert round(out["gross_interest_try"]) == 50_000
        assert round(out["net_interest_try"]) == 42_500
        assert round(out["value_try"]) == 142_500
        assert round(out["value_usd"], 2) == round(142_500 / 48.0, 2)

    def test_breakeven_rate_is_reported(self):
        """Sorulmasi gereken 'faiz ne kadar' degil, 'kur ne kadar artarsa erir'."""
        from src import portfolio as P

        pos = {
            "asset_class": "TL_DEPOSIT", "principal_try": 100_000.0,
            "annual_rate_pct": 50.0, "withholding_pct": 15.0,
            "start_date": days_ago(30), "maturity_date": days_ago(-335),
            "usdtry_at_entry": 40.0,
        }
        out = P.tl_deposit_value(pos, usdtry=42.0)
        # Giriste 2.500 USD; vade sonunda 142.500 TL -> basa bas 57,0
        assert round(out["usdtry_breakeven"], 1) == 57.0
        assert out["breakeven_headroom_pct"] > 0

    def test_missing_fields_do_not_crash(self):
        from src import portfolio as P

        out = P.tl_deposit_value({"asset_class": "TL_DEPOSIT"}, usdtry=42.0)
        assert out["note"]
        assert out.get("value_usd") is None

    def test_slice_comes_from_asset_class(self):
        from src import portfolio as P

        assert P.slice_for({"asset_class": "STOCK"}) == "motor"
        assert P.slice_for({"asset_class": "ETF"}) == "cekirdek_etf"
        assert P.slice_for({"asset_class": "TL_DEPOSIT"}) == "tl"

    def test_explicit_slice_wins(self):
        """SGOV bir ETF'tir ama cekirdek degil NAKIT CAPASIDIR."""
        from src import portfolio as P

        # Sembol eslemesi varlik sinifindan once gelir
        assert P.slice_for({"asset_class": "ETF", "ticker": "SGOV"}) == "sgov"
        # Acik alan her seyden once gelir
        assert P.slice_for({"asset_class": "ETF", "ticker": "QQQM",
                            "slice": "sgov"}) == "sgov"


class TestSlices:
    def test_drift_is_flagged(self, sample, monkeypatch):
        from src import portfolio as P

        # Faz tarihe bagli; test 16 Kasim'da kendiliginden bozulmasin.
        monkeypatch.setitem(P.PORTFOLIO, "active_phase", "faz2")   # motor %40
        pos = P.json_snippet("DBX", days_ago(10), 25.0, 10)          # 250 USD motor
        write(sample, [pos], cash=750.0)
        r = P.compute({"DBX": {"price": 25.0}})
        slices = {s["slice"]: s for s in r["summary"]["slices"]}
        assert slices["motor"]["actual_pct"] == 25.0
        assert slices["motor"]["target_pct"] == 40.0
        assert slices["motor"]["off_target"] is True
        assert any(w["type"] == "dilim_sapmasi" for w in r["warnings"])

    def test_cash_is_shown_but_never_counts_as_drift(self, sample, monkeypatch):
        """Bekleyen nakit genelde planli bir alimin parasidir (30 Ekim QQQM
        parcasi gibi); onu 'hedef disi' saymak her planli alimdan once
        sahte alarm demek."""
        from src import portfolio as P

        monkeypatch.setitem(P.PORTFOLIO, "active_phase", "faz2")
        pos = P.json_snippet("DBX", days_ago(10), 25.0, 10)
        write(sample, [pos], cash=750.0)
        r = P.compute({"DBX": {"price": 25.0}})
        nakit = next(s for s in r["summary"]["slices"] if s["slice"] == "nakit")
        assert nakit["actual_pct"] == 75.0
        assert nakit["off_target"] is False and nakit["target_pct"] is None

    def test_empty_portfolio_is_not_nagged(self, sample):
        """Dengelenecek bir sey yokken dilimler uyarmasin."""
        from src import portfolio as P

        write(sample, [], cash=1000.0)
        r = P.compute({})
        assert r["summary"]["slices"]                      # ozet yine uretilir
        assert not any(w["type"] == "dilim_sapmasi" for w in r["warnings"])

    def test_every_phase_sums_to_100(self):
        from src.config import PORTFOLIO

        for ph in PORTFOLIO["phases"]:
            assert sum(ph["targets"].values()) == 100, ph["key"]

    def test_phase_is_chosen_by_date(self, monkeypatch):
        from src import portfolio as P

        monkeypatch.setitem(P.PORTFOLIO, "active_phase", None)
        assert P.active_phase("2026-10-01")["key"] == "faz0"
        assert P.active_phase("2026-11-16")["key"] == "faz1"   # sinir gunu yeni faz
        assert P.active_phase("2027-06-01")["key"] == "faz2"

    def test_forced_phase_ignores_date(self, monkeypatch):
        """Faz 1 alimlari gecikirse hedefler kendiliginden kaymamali."""
        from src import portfolio as P

        monkeypatch.setitem(P.PORTFOLIO, "active_phase", "faz0")
        assert P.active_phase("2027-06-01")["key"] == "faz0"


class TestBreakerEngine:
    """Kiricilar artik MAKINE tarafindan degerlendiriliyor."""

    def test_structured_breaker_triggers_without_manual_flag(self, sample):
        from src import portfolio as P

        pos = P.json_snippet("DBX", days_ago(10), 25.0, 10)
        pos["thesis_breakers"] = [{
            "metric": "gross_margin", "op": "<", "value": 70.0,
            "consecutive_quarters": 1,
            "description": "Brut marj %70 altina inerse",
        }]
        write(sample, [pos], cash=1000.0)
        card = {"metrics": {"gross_margin": {"value": 65.0}}}
        r = P.compute({"DBX": {"price": 25.0}}, cards={"DBX": card})
        assert any(w["type"] == "tez_kirici" for w in r["warnings"])

    def test_structured_breaker_stays_quiet_when_healthy(self, sample):
        from src import portfolio as P

        pos = P.json_snippet("DBX", days_ago(10), 25.0, 10)
        pos["thesis_breakers"] = [{
            "metric": "gross_margin", "op": "<", "value": 70.0,
            "consecutive_quarters": 1, "description": "x",
        }]
        write(sample, [pos], cash=1000.0)
        card = {"metrics": {"gross_margin": {"value": 80.0}}}
        r = P.compute({"DBX": {"price": 25.0}}, cards={"DBX": card})
        assert not any(w["type"] == "tez_kirici" for w in r["warnings"])

    def test_price_collapse_is_a_reevaluation_not_a_sale(self, sample):
        from src import portfolio as P

        pos = P.json_snippet("DBX", days_ago(10), 100.0, 10)
        write(sample, [pos], cash=1000.0)
        r = P.compute({"DBX": {"price": 60.0}})      # -%40
        w = [x for x in r["warnings"] if x["type"] == "kirici_fiyat_cokusu"]
        assert len(w) == 1
        assert "otomatik satis degil" in w[0]["message"].lower()

    def test_manual_breaker_can_still_be_triggered_by_hand(self, sample):
        """Makine degerlendirmesi EKLENDI, elle tetikleme KALDIRILMADI."""
        from src import portfolio as P

        pos = P.json_snippet("DBX", days_ago(10), 25.0, 10)
        pos["thesis_breakers"] = [
            {"description": "Rakip pazar payi alirsa", "triggered": True},
        ]
        write(sample, [pos], cash=1000.0)
        r = P.compute({"DBX": {"price": 25.0}})
        assert any(w["type"] == "tez_kirici" for w in r["warnings"])

    def test_unevaluable_breaker_does_not_cry_wolf(self, sample):
        """Veri yoksa alarm calmaz — guvenilmez alarm bir sure sonra
        hepsinin gormezden gelinmesine yol acar."""
        from src import portfolio as P

        pos = P.json_snippet("DBX", days_ago(10), 25.0, 10)
        pos["thesis_breakers"] = [{
            "metric": "gross_margin", "op": "<", "value": 70.0,
            "consecutive_quarters": 4, "description": "x",
        }]
        write(sample, [pos], cash=1000.0)
        card = {"metrics": {"gross_margin": {"value": 10.0}}, "series": {}}
        r = P.compute({"DBX": {"price": 25.0}}, cards={"DBX": card})
        assert not any(w["type"] == "tez_kirici" for w in r["warnings"])
        assert any(w["type"] == "kirici_veri_yok" for w in r["warnings"])


class TestPlanAndFx:
    """Genel bakistaki 'siradaki isler' ve kur karti bu fonksiyonlardan beslenir."""

    def test_breakeven_vs_sgov_is_below_plain_breakeven(self):
        """Alternatif dolari bosta tutmak degil hazine bonosunda tutmak;
        TL'nin SGOV'u gecmesi icin kurun DAHA ASAGIDA kalmasi gerekir."""
        from src import portfolio as P

        pos = {"asset_class": "TL_DEPOSIT", "principal_try": 60000.0,
               "annual_rate_pct": 36.0, "withholding_pct": 15.0,
               "start_date": "2026-09-29", "maturity_date": "2026-12-30",
               "usdtry_at_entry": 50.3}
        out = P.tl_deposit_value(pos, 50.3, as_of="2026-09-29", tbill_pct=3.9)
        assert out["term_days"] == 92
        assert out["usdtry_breakeven_vs_sgov"] < out["usdtry_breakeven"]
        # 60.000 x %36 x 92/365 x 0,85 = 4.627,73 TL net faiz
        assert out["value_try_at_maturity"] == pytest.approx(64627.73, abs=0.01)
        assert out["daily_net_interest_try"] == pytest.approx(50.3, abs=0.01)

    def test_fx_pace_colors(self):
        from src import portfolio as P

        def pace(chg):
            series = [("2026-06-01", 100.0), ("2026-09-01", 100.0 * (1 + chg / 100))]
            return P.fx_pace({"rate": series[-1][1], "series": series})["color"]

        assert pace(3.0) == "green"
        assert pace(5.0) == "yellow"
        assert pace(8.0) == "red"

    def test_renewal_criteria_are_gray_without_data(self):
        """Tahmin yazmaktansa 'bilmiyoruz' demek dogru."""
        from src import portfolio as P

        c = {x["key"]: x["status"] for x in P.renewal_criteria({"change_quarter_pct": None,
                                                                 "window_days": 91}, {})}
        assert c == {"reel_faiz": "gray", "kur_temposu": "gray", "erken_secim": "gray"}

    def test_renewal_criteria_with_data(self):
        from src import portfolio as P
        from src.util import today_iso

        tr = {"policy_rate_pct": 40.0, "cpi_yoy_pct": 30.0,
              "early_election_announced": False, "as_of": today_iso()}
        c = {x["key"]: x["status"] for x in P.renewal_criteria(
            {"change_quarter_pct": 8.0, "window_days": 91}, tr)}
        assert c == {"reel_faiz": "green", "kur_temposu": "red", "erken_secim": "green"}

    def test_future_entry_is_not_priced(self, sample):
        """Son kapanis giris gununden onceyse o hareket bu pozisyona ait degil."""
        from src import portfolio as P

        pos = P.json_snippet("SGOV", "2099-01-01", 100.0, 5)
        write(sample, [pos], cash=0.0)
        r = P.compute({"SGOV": {"price": 90.0, "as_of": "2026-09-28"}})
        p = r["positions"][0]
        assert p["started"] is False
        assert p["value_usd"] == 500.0 and p["pnl_usd"] is None

    def test_concentration_limit_is_for_single_stocks_only(self, sample):
        """TL mevduat portfoyun yarisi olacak sekilde PLANLANDI."""
        from src import portfolio as P

        dep = {"ticker": "TL-X", "asset_class": "TL_DEPOSIT", "principal_try": 50000.0,
               "annual_rate_pct": 36.0, "start_date": days_ago(5),
               "maturity_date": days_ago(-60), "usdtry_at_entry": 50.0,
               "entry_date": days_ago(5), "status": "OPEN"}
        write(sample, [dep], cash=10.0)
        r = P.compute({}, fx={"rate": 50.0})
        assert not any(w["type"] == "konsantrasyon" for w in r["warnings"])

    def test_tl_deposit_is_not_a_price_ticker(self, sample):
        from src import portfolio as P

        dep = {"ticker": "TL-X", "asset_class": "TL_DEPOSIT", "status": "OPEN"}
        write(sample, [dep, P.json_snippet("SGOV", days_ago(1), 100.0, 1)], cash=0.0)
        assert P.tickers() == ["SGOV"]


class TestMissingDataNoFalseAlarm:
    def test_missing_fx_does_not_fake_drift(self, sample, monkeypatch):
        """Kur yoksa TL dilimi toplamdan duser; bu SAPMA degil veri boslugu."""
        from src import portfolio as P

        monkeypatch.setitem(P.PORTFOLIO, "active_phase", "faz0")
        dep = {"ticker": "TL-X", "asset_class": "TL_DEPOSIT", "principal_try": 50000.0,
               "annual_rate_pct": 36.0, "start_date": days_ago(5),
               "maturity_date": days_ago(-60), "usdtry_at_entry": 50.0,
               "entry_date": days_ago(5), "status": "OPEN"}
        write(sample, [dep, P.json_snippet("SGOV", days_ago(5), 100.0, 5)], cash=0.0)
        r = P.compute({"SGOV": {"price": 100.0}}, fx={})     # kur yok
        assert r["summary"]["slices_incomplete"] == ["TL-X"]
        assert not any(w["type"] == "dilim_sapmasi" for w in r["warnings"])
        assert any(w["type"] == "veri_eksik" for w in r["warnings"])


class TestTlEntryRate:
    def _dep(self, entry_fx):
        return {"ticker": "TL-X", "asset_class": "TL_DEPOSIT", "principal_try": 60000.0,
                "annual_rate_pct": 36.0, "withholding_pct": 15.0,
                "start_date": days_ago(2), "maturity_date": days_ago(-90),
                "usdtry_at_entry": entry_fx, "entry_date": days_ago(2), "status": "OPEN"}

    def _fx(self, rate):
        return {"rate": rate, "series": [(days_ago(10), rate), (days_ago(2), rate)]}

    def test_entry_rate_far_from_market_is_flagged(self, sample):
        from src import portfolio as P

        write(sample, [self._dep(50.3)], cash=0.0)
        r = P.compute({}, fx=self._fx(48.96))
        assert any(w["type"] == "giris_kuru" for w in r["warnings"])

    def test_entry_rate_close_to_market_is_quiet(self, sample):
        from src import portfolio as P

        write(sample, [self._dep(49.1)], cash=0.0)
        r = P.compute({}, fx=self._fx(48.96))
        assert not any(w["type"] == "giris_kuru" for w in r["warnings"])

    def test_not_started_deposit_is_valued_at_cost(self, sample):
        from src import portfolio as P

        dep = self._dep(50.0)
        dep["start_date"] = dep["entry_date"] = "2099-01-01"
        write(sample, [dep], cash=0.0)
        r = P.compute({}, fx=self._fx(40.0))      # kur cok farkli olsa bile
        assert r["positions"][0]["value_usd"] == pytest.approx(60000 / 50.0)
