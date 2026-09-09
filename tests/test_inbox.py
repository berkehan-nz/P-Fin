"""inbox.py — baska bir ajanin yazdigi dosyanin sozlesmesi.

TASARIM KARARI: inbox'a yazan taraf SAYISAL ALANLARA DOKUNAMAZ. Bu testler
o sinirin gercekten uygulandigini dogrular.
"""

import json

import pytest

from src import cards, inbox
from tests import fixtures


class TestAllowedFields:
    def test_template_is_valid(self):
        assert inbox.validate_file(inbox.template("DBX"), "DBX") == []

    def test_numeric_fields_rejected(self):
        for bad in ({"price": 12.0}, {"metrics": {}}, {"scores": {"total": 99}},
                    {"market_cap_musd": 1}, {"ttm": {}}):
            problems = inbox.validate_file({"ticker": "DBX", **bad}, "DBX")
            assert problems, f"{bad} kabul edilmemeliydi"
            assert "Izin verilmeyen" in problems[0]

    def test_story_and_decision_allowed(self):
        payload = {"ticker": "DBX",
                   "story": {"claude_verdict": "not"},
                   "decision": {"action": "AL"},
                   "catalyst_score": 70}
        assert inbox.validate_file(payload, "DBX") == []

    def test_unknown_story_field_rejected(self):
        problems = inbox.validate_file(
            {"story": {"gizli_alan": "x"}}, "DBX")
        assert any("gizli_alan" in p for p in problems)

    def test_ticker_mismatch_caught(self):
        problems = inbox.validate_file({"ticker": "LSCC"}, "DBX")
        assert any("DBX.json" in p for p in problems)


class TestTypes:
    def test_bull_case_must_be_list(self):
        problems = inbox.validate_file({"story": {"bull_case": "tek metin"}}, "DBX")
        assert any("list olmali" in p for p in problems)

    def test_text_length_limit(self):
        problems = inbox.validate_file(
            {"story": {"claude_verdict": "x" * 5000}}, "DBX")
        assert any("cok uzun" in p for p in problems)

    def test_list_item_limit(self):
        problems = inbox.validate_file(
            {"story": {"bull_case": ["x"] * 20}}, "DBX")
        assert any("en fazla" in p for p in problems)

    def test_invalid_action_rejected(self):
        for bad in ("SAT", "BUY", "al"):
            problems = inbox.validate_file({"decision": {"action": bad}}, "DBX")
            assert any("gecersiz" in p for p in problems), bad

    def test_valid_actions_accepted(self):
        for good in ("AL", "BEKLE", "ELE"):
            assert inbox.validate_file({"decision": {"action": good}}, "DBX") == []

    def test_catalyst_score_range(self):
        assert inbox.validate_file({"catalyst_score": 150}, "DBX")
        assert inbox.validate_file({"catalyst_score": -5}, "DBX")
        assert inbox.validate_file({"catalyst_score": 70}, "DBX") == []

    def test_catalyst_score_must_be_number(self):
        assert inbox.validate_file({"catalyst_score": "yuksek"}, "DBX")

    def test_non_object_rejected(self):
        assert inbox.validate_file(["liste"], "DBX")
        assert inbox.validate_file(None, "DBX")


class TestMergeRespectsBoundary:
    """Dogrulamayi gecen bir dosya bile sayisal alanlari degistirememeli."""

    @pytest.fixture
    def isolated(self, tmp_path, monkeypatch):
        cards_dir = tmp_path / "cards"
        inbox_dir = tmp_path / "inbox"
        cards_dir.mkdir(); inbox_dir.mkdir()
        monkeypatch.setattr(cards, "CARDS_DIR", cards_dir)
        monkeypatch.setattr(cards, "INBOX_DIR", inbox_dir)
        return inbox_dir

    def test_story_reaches_card(self, isolated):
        (isolated / "DBX.json").write_text(json.dumps({
            "ticker": "DBX",
            "story": {"claude_verdict": "Nakit makinesi, buyume yok.",
                      "bull_case": ["Geri alimlar"]},
        }), encoding="utf-8")
        c = cards.build(fixtures.dbx(), source="test")
        c = cards.merge_story(c, inbox_dir=isolated)
        assert c["story"]["claude_verdict"] == "Nakit makinesi, buyume yok."
        assert c["story"]["bull_case"] == ["Geri alimlar"]

    def test_metrics_survive_hostile_payload(self, isolated):
        """Dosyada sayisal alan olsa bile kart metrikleri korunmali."""
        (isolated / "DBX.json").write_text(json.dumps({
            "ticker": "DBX",
            "story": {"claude_verdict": "not"},
            "price": 9999, "metrics": {"ev_ebit": {"value": 0.1}},
            "scores": {"total": 100},
        }), encoding="utf-8")
        c = cards.build(fixtures.dbx(), source="test")
        original_ev = c["metrics"]["ev_ebit"]["value"]
        original_price = c["price"]
        c = cards.merge_story(c, inbox_dir=isolated)
        assert c["metrics"]["ev_ebit"]["value"] == original_ev
        assert c["price"] == original_price
        assert c["story"]["claude_verdict"] == "not"

    def test_decision_reaches_card(self, isolated):
        (isolated / "DBX.json").write_text(json.dumps({
            "decision": {"action": "BEKLE", "rationale": "Buyume donsun"},
        }), encoding="utf-8")
        c = cards.build(fixtures.dbx(), source="test")
        c = cards.merge_story(c, inbox_dir=isolated)
        assert c["decision"]["action"] == "BEKLE"
        assert c["decision"]["date"]
