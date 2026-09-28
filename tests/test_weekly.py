"""weekly.py — Cuma raporu.

Raporun isi "her seyi gostermek" degil, HAFTADA BIR BAKILMASI GEREKENI
gostermek. Bu yuzden testlerin cogu "neyin rapora GIRMEDIGI" uzerine:
sapmayan dilim, tetiklenmemis kirici, uzaktaki bilanco tarihi girmemeli.
Her seyi gosteren rapor, hicbir sey gostermeyen rapordur.
"""

from datetime import date, timedelta

import pytest

from src import weekly


def in_days(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(weekly, "DATA_DIR", tmp_path)
    monkeypatch.setattr(weekly, "WEEKLY_PATH", tmp_path / "weekly.json")
    monkeypatch.setattr(weekly, "CARDS_DIR", tmp_path / "cards")
    (tmp_path / "cards").mkdir()
    return tmp_path


class TestTriggeredBreakers:
    def test_only_triggered_ones_appear(self):
        state = {"positions": [{
            "ticker": "DBX",
            "thesis_breakers": [
                {"description": "tetiklendi", "triggered": True,
                 "level": "high", "kind": "thesis"},
                {"description": "saglam", "triggered": False},
            ],
        }]}
        out = weekly.triggered_breakers(state)
        assert [b["description"] for b in out] == ["tetiklendi"]

    def test_high_level_comes_first(self):
        state = {"positions": [{
            "ticker": "DBX",
            "thesis_breakers": [
                {"description": "orta", "triggered": True, "level": "medium"},
                {"description": "yuksek", "triggered": True, "level": "high"},
            ],
        }]}
        out = weekly.triggered_breakers(state)
        assert [b["level"] for b in out] == ["high", "medium"]

    def test_empty_portfolio_has_none(self):
        assert weekly.triggered_breakers({}) == []


class TestUpcomingEarnings:
    def test_far_away_earnings_are_excluded(self, monkeypatch):
        monkeypatch.setattr(weekly.watchlist, "tickers", lambda: ["AAA", "BBB"])
        cards = {
            "AAA": {"calendar": {"next_earnings": in_days(3)}},
            "BBB": {"calendar": {"next_earnings": in_days(40)}},
        }
        out = weekly.upcoming_earnings({}, cards)
        assert [e["ticker"] for e in out] == ["AAA"]

    def test_past_earnings_are_excluded(self, monkeypatch):
        monkeypatch.setattr(weekly.watchlist, "tickers", lambda: ["AAA"])
        cards = {"AAA": {"calendar": {"next_earnings": in_days(-2)}}}
        assert weekly.upcoming_earnings({}, cards) == []

    def test_sorted_by_proximity(self, monkeypatch):
        monkeypatch.setattr(weekly.watchlist, "tickers", lambda: ["AAA", "BBB"])
        cards = {
            "AAA": {"calendar": {"next_earnings": in_days(6)}},
            "BBB": {"calendar": {"next_earnings": in_days(1)}},
        }
        out = weekly.upcoming_earnings({}, cards)
        assert [e["ticker"] for e in out] == ["BBB", "AAA"]

    def test_portfolio_membership_is_marked(self, monkeypatch):
        monkeypatch.setattr(weekly.watchlist, "tickers", lambda: [])
        state = {"positions": [{"ticker": "AAA"}]}
        cards = {"AAA": {"calendar": {"next_earnings": in_days(2)}}}
        out = weekly.upcoming_earnings(state, cards)
        assert out[0]["in_portfolio"] is True


class TestNewCandidates:
    def test_first_report_lists_everything_as_new(self):
        cand = {"candidates": [{"ticker": "AAA", "scores": {"total": 70}}]}
        out = weekly.new_candidates(cand, [])
        assert out["first_report"] is True
        assert [c["ticker"] for c in out["entered"]] == ["AAA"]

    def test_only_the_difference_is_new(self):
        cand = {"candidates": [{"ticker": "AAA"}, {"ticker": "BBB"}]}
        out = weekly.new_candidates(cand, ["AAA"])
        assert [c["ticker"] for c in out["entered"]] == ["BBB"]

    def test_departures_are_reported_too(self):
        """Listeden dusmek de bilgidir: kota doldu, puan geriledi ya da
        veri bozuldu."""
        cand = {"candidates": [{"ticker": "AAA"}]}
        out = weekly.new_candidates(cand, ["AAA", "CCC"])
        assert out["left"] == ["CCC"]

    def test_entered_is_sorted_by_score(self):
        cand = {"candidates": [
            {"ticker": "LOW", "scores": {"total": 40}},
            {"ticker": "HIGH", "scores": {"total": 90}},
        ]}
        out = weekly.new_candidates(cand, [])
        assert [c["ticker"] for c in out["entered"]] == ["HIGH", "LOW"]


class TestSliceDrift:
    def test_on_target_slices_are_omitted(self):
        state = {"summary": {"slices": [
            {"slice": "motor", "off_target": True},
            {"slice": "sgov", "off_target": False},
        ]}}
        assert [s["slice"] for s in weekly.slice_drift(state)] == ["motor"]


class TestFx:
    def test_deposit_breakeven_is_carried(self):
        state = {
            "summary": {"fx": {"rate": 48.0, "change_1w_pct": 1.2,
                               "as_of": "2026-09-26"}},
            "positions": [{
                "ticker": "TL-01",
                "tl_deposit": {"value_try": 142500, "value_usd": 2968.75,
                               "usdtry_at_entry": 40.0,
                               "usdtry_breakeven": 57.0,
                               "breakeven_headroom_pct": 42.5},
            }],
        }
        out = weekly.fx_section(state)
        assert out["usdtry"] == 48.0
        assert out["deposits"][0]["usdtry_breakeven"] == 57.0

    def test_no_deposit_is_fine(self):
        out = weekly.fx_section({"positions": [{"ticker": "DBX"}]})
        assert out["deposits"] == []


class TestActionCount:
    """'Bu hafta bir sey yapmam gerekiyor mu' tek bakista cevaplanmali."""

    def test_counts_breakers_and_drift_only(self, isolated, monkeypatch):
        from src.util import write_json

        monkeypatch.setattr(weekly.watchlist, "tickers", lambda: ["AAA"])
        write_json(isolated / "portfolio_state.json", {
            "positions": [{
                "ticker": "DBX",
                "thesis_breakers": [{"description": "x", "triggered": True,
                                     "level": "high"}],
            }],
            "summary": {"slices": [{"slice": "motor", "off_target": True,
                                    "label": "Motor", "actual_pct": 80.0,
                                    "target_pct": 40.0, "drift_pp": 40.0}]},
        })
        # Bilanco tarihi yakin olsa bile EYLEM sayilmaz: rapor bir bilgi ani.
        write_json(isolated / "cards" / "AAA.json",
                   {"ticker": "AAA",
                    "calendar": {"next_earnings": in_days(2)}})
        r = weekly.build()
        assert r["action_required"] == 2          # 1 kirici + 1 dilim
        assert len(r["upcoming_earnings"]) == 1   # rapora girer, sayilmaz


class TestWriteGating:
    def test_not_written_outside_friday(self, isolated, monkeypatch):
        monkeypatch.setattr(weekly, "_is_friday", lambda when=None: False)
        assert weekly.write() is False
        assert not (isolated / "weekly.json").exists()

    def test_written_on_friday(self, isolated, monkeypatch):
        monkeypatch.setattr(weekly, "_is_friday", lambda when=None: True)
        monkeypatch.setattr(weekly.watchlist, "tickers", lambda: [])
        assert weekly.write() is True
        assert (isolated / "weekly.json").exists()

    def test_force_overrides_the_day(self, isolated, monkeypatch):
        monkeypatch.setattr(weekly, "_is_friday", lambda when=None: False)
        monkeypatch.setattr(weekly.watchlist, "tickers", lambda: [])
        assert weekly.write(force=True) is True
