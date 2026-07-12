"""Nöbetçi testleri (§3.1) — stop kırılması kritik olay + tekrar-uyarı önleme.

Ağa çıkmadan test etmek için veri katmanı monkeypatch'lenir.
"""
from pfin.config import Config
from pfin.data.models import Quote
from pfin.memory.schema import Market, Position, State
from pfin.watchman import sentinel

CFG = Config(raw={"sentinel": {"intraday_move_pct": 0.07, "abnormal_volume_mult": 3.0,
                               "kap_lookback_hours": 24},
                  "twelvedata": {"calls_per_minute": 8, "calls_per_day": 800}})


def _state_with_position(stop=42.0):
    s = State(cash_try=40000)
    s.positions.append(Position(id="p1", symbol="EREGL", market=Market.BIST,
        entry_price=45, shares=200, stop=stop, thesis="t", refuter="r"))
    return s


def test_stop_broken_is_critical(monkeypatch):
    monkeypatch.setattr(sentinel.prices, "quote_for",
        lambda *a, **k: Quote(symbol="EREGL", market="BIST", price=41.0, change_pct=-1.0,
                              source="test"))
    monkeypatch.setattr(sentinel.kap, "recent_disclosures", lambda *a, **k: [])
    s = _state_with_position()
    events = sentinel.check(s, CFG)
    stop_events = [e for e in events if e.kind == "stop_broken"]
    assert stop_events and stop_events[0].severity == "critical"


def test_dedupe_prevents_repeat(monkeypatch):
    monkeypatch.setattr(sentinel.prices, "quote_for",
        lambda *a, **k: Quote(symbol="EREGL", market="BIST", price=41.0, change_pct=-1.0,
                              source="test"))
    monkeypatch.setattr(sentinel.kap, "recent_disclosures", lambda *a, **k: [])
    s = _state_with_position()
    first = sentinel.check(s, CFG)
    sentinel.mark_sent(s, first)
    second = sentinel.check(s, CFG)
    assert [e for e in first if e.kind == "stop_broken"]
    assert not [e for e in second if e.kind == "stop_broken"], "aynı gün tekrar uyarı olmamalı"


def test_sharp_move_triggers(monkeypatch):
    monkeypatch.setattr(sentinel.prices, "quote_for",
        lambda *a, **k: Quote(symbol="EREGL", market="BIST", price=60.0, change_pct=9.0,
                              source="test"))
    monkeypatch.setattr(sentinel.kap, "recent_disclosures", lambda *a, **k: [])
    s = _state_with_position(stop=30.0)   # stop kırılmasın, sadece hareket
    events = sentinel.check(s, CFG)
    assert any(e.kind == "sharp_move" for e in events)
