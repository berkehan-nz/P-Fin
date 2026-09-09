"""cards.py — sema, hikaye birlestirme, yazili blok koruma."""

import json

import pytest

from src import cards
from tests import fixtures


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Gercek data/ ve claude_inbox/ klasorlerine dokunmadan calis."""
    cards_dir = tmp_path / "cards"
    inbox_dir = tmp_path / "inbox"
    cards_dir.mkdir()
    inbox_dir.mkdir()
    monkeypatch.setattr(cards, "CARDS_DIR", cards_dir)
    monkeypatch.setattr(cards, "INBOX_DIR", inbox_dir)
    return cards_dir, inbox_dir


def write_inbox(inbox_dir, ticker, payload):
    (inbox_dir / f"{ticker}.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class TestSchema:
    def test_required_top_level_keys(self):
        c = cards.build(fixtures.dbx(), source="seed_20260909")
        for key in ("ticker", "name", "exchange", "sector", "sic", "track",
                    "source", "as_of", "price", "market_cap_musd",
                    "enterprise_value_musd", "scores", "metrics", "series",
                    "flags", "news", "calendar", "analyst", "story", "decision"):
            assert key in c, key

    def test_story_starts_empty(self):
        c = cards.build(fixtures.dbx(), source="test")
        assert c["story"]["claude_verdict"] == ""
        assert c["story"]["bull_case"] == []
        assert c["story"]["author"] == "claude"

    def test_decision_starts_empty(self):
        c = cards.build(fixtures.dbx(), source="test")
        assert c["decision"]["action"] == ""
        assert c["decision"]["author"] == "berke"

    def test_metric_cells_have_value_and_color(self):
        c = cards.build(fixtures.dbx(), source="test")
        cell = c["metrics"]["ev_ebit"]
        assert set(cell) >= {"value", "sector_pct", "own_5y_pct", "color", "pct_basis"}
        assert cell["color"] in ("green", "yellow", "red", "gray")

    def test_missing_metric_is_gray_not_zero(self):
        c = cards.build(fixtures.kvyo(), source="test")
        assert c["metrics"]["ev_ebit"]["value"] is None
        assert c["metrics"]["ev_ebit"]["color"] == "gray"

    def test_both_tracks_marked(self):
        f = fixtures.dbx()
        c = cards.build(f, source="test", both_tracks=True)
        assert c["track"] == "both"

    def test_seed_prewarnings_attached(self, monkeypatch):
        from src import config
        f = fixtures.dbx()
        f.ticker = "LYFT"
        monkeypatch.setitem(config.SEED_PREWARNINGS, "LYFT",
                            ["F/K 2,27 seviyesinde — tek seferlik kalem suphesi"])
        c = cards.build(f, source="seed_20260909")
        assert any("tek seferlik" in w for w in c["flags"]["warnings"])

    def test_forced_organic_suspect(self):
        c = cards.build(fixtures.lscc(), source="test", force_organic_suspect=True)
        assert c["flags"]["rev_growth_organic_suspect"] is True
        assert any("satin alma" in w for w in c["flags"]["warnings"])

    def test_negative_equity_warning_present(self):
        c = cards.build(fixtures.dbx(), source="test")
        assert any("Ozkaynak negatif" in w for w in c["flags"]["warnings"])


class TestMergeStory:
    def test_inbox_fills_story(self, isolated):
        _, inbox = isolated
        write_inbox(inbox, "DBX", {"story": {
            "business_model": "Bulut depolama aboneligi",
            "claude_verdict": "Nakit makinesi ama buyume yok.",
            "bull_case": ["Geri alimlar hisse sayisini eritiyor"],
        }})
        c = cards.build(fixtures.dbx(), source="test")
        c = cards.merge_story(c, inbox_dir=inbox)
        assert c["story"]["business_model"] == "Bulut depolama aboneligi"
        assert c["story"]["bull_case"] == ["Geri alimlar hisse sayisini eritiyor"]

    def test_inbox_wins_on_conflict(self, isolated):
        _, inbox = isolated
        c = cards.build(fixtures.dbx(), source="test")
        c["story"]["claude_verdict"] = "eski not"
        write_inbox(inbox, "DBX", {"story": {"claude_verdict": "yeni not"}})
        c = cards.merge_story(c, inbox_dir=inbox)
        assert c["story"]["claude_verdict"] == "yeni not"

    def test_empty_inbox_values_do_not_erase(self, isolated):
        _, inbox = isolated
        c = cards.build(fixtures.dbx(), source="test")
        c["story"]["moat"] = "Degistirme maliyeti"
        write_inbox(inbox, "DBX", {"story": {"moat": "", "claude_verdict": "not"}})
        c = cards.merge_story(c, inbox_dir=inbox)
        assert c["story"]["moat"] == "Degistirme maliyeti"

    def test_inbox_cannot_overwrite_numbers(self, isolated):
        """Inbox yalnizca story/decision'a dokunabilir; metrikler korunur."""
        _, inbox = isolated
        c = cards.build(fixtures.dbx(), source="test")
        original = c["metrics"]["ev_ebit"]["value"]
        write_inbox(inbox, "DBX", {
            "story": {"claude_verdict": "not"},
            "metrics": {"ev_ebit": {"value": 1.0}},
            "price": 999.0,
        })
        c = cards.merge_story(c, inbox_dir=inbox)
        assert c["metrics"]["ev_ebit"]["value"] == original
        assert c["price"] != 999.0

    def test_decision_merged_and_dated(self, isolated):
        _, inbox = isolated
        c = cards.build(fixtures.dbx(), source="test")
        write_inbox(inbox, "DBX", {"decision": {
            "action": "BEKLE", "rationale": "Buyume donene kadar"}})
        c = cards.merge_story(c, inbox_dir=inbox)
        assert c["decision"]["action"] == "BEKLE"
        assert c["decision"]["date"]        # otomatik tarihlenmeli

    def test_manual_catalyst_score_recomputes_total(self, isolated):
        _, inbox = isolated
        c = cards.build(fixtures.dbx(), source="test")
        c["scores"] = {"value": 80.0, "quality": 70.0, "safety": 60.0,
                       "momentum": 50.0, "earnings_quality": 40.0}
        write_inbox(inbox, "DBX", {"catalyst_score": 90.0})
        c = cards.merge_story(c, inbox_dir=inbox)
        assert c["scores"]["catalyst"] == 90.0
        assert c["scores"]["weight_coverage"] == 1.0

    def test_no_inbox_file_is_noop(self, isolated):
        _, inbox = isolated
        c = cards.build(fixtures.dbx(), source="test")
        assert cards.merge_story(c, inbox_dir=inbox)["story"]["claude_verdict"] == ""


class TestPreserveAuthored:
    def test_regeneration_keeps_story(self):
        old = cards.build(fixtures.dbx(), source="test")
        old["story"]["claude_verdict"] = "Onceki analiz"
        new = cards.build(fixtures.dbx(), source="test")
        merged = cards.preserve_authored(new, old)
        assert merged["story"]["claude_verdict"] == "Onceki analiz"

    def test_regeneration_keeps_decision(self):
        old = cards.build(fixtures.dbx(), source="test")
        old["decision"] = {"action": "AL", "date": "2026-09-01",
                           "rationale": "Ucuz", "author": "berke"}
        new = cards.build(fixtures.dbx(), source="test")
        merged = cards.preserve_authored(new, old)
        assert merged["decision"]["action"] == "AL"

    def test_empty_old_story_does_not_override(self):
        old = cards.build(fixtures.dbx(), source="test")
        new = cards.build(fixtures.dbx(), source="test")
        new["story"]["claude_verdict"] = "yeni"
        merged = cards.preserve_authored(new, old)
        assert merged["story"]["claude_verdict"] == "yeni"

    def test_save_roundtrip_preserves_story(self, isolated):
        cards_dir, inbox = isolated
        c = cards.build(fixtures.dbx(), source="test")
        c["story"]["claude_verdict"] = "Ilk analiz"
        cards.save(c, merge=False)
        # yeniden uretim
        c2 = cards.build(fixtures.dbx(), source="test")
        cards.save(c2, merge=False)
        reloaded = cards.load_card("DBX")
        assert reloaded["story"]["claude_verdict"] == "Ilk analiz"

    def test_unchanged_card_is_not_rewritten(self, isolated):
        """Degisiklik yoksa dosyaya dokunma — bos commit olmasin."""
        c = cards.build(fixtures.dbx(), source="test")
        assert cards.save(c, merge=False) is True
        assert cards.save(c, merge=False) is False


class TestSummaryRow:
    def test_headline_metrics_follow_track(self):
        a = cards.summary_row(cards.build(fixtures.dbx(), source="test"))
        b = cards.summary_row(cards.build(fixtures.kvyo(), source="test"))
        assert set(a["headline"]) == {"ev_ebit", "fcf_yield_ev", "roic"}
        assert set(b["headline"]) == {"ev_sales", "rev_growth_ttm", "rule_of_40"}

    def test_verdict_truncated_to_140_chars(self):
        c = cards.build(fixtures.dbx(), source="test")
        c["story"]["claude_verdict"] = "x" * 300
        assert len(cards.summary_row(c)["claude_verdict"]) == 140

    def test_warning_count(self):
        c = cards.build(fixtures.dbx(), source="test")
        row = cards.summary_row(c)
        assert row["warning_count"] == len(c["flags"]["warnings"])
