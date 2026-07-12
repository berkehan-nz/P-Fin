"""Korkuluk katmanı testleri (§3.3) — değişmezlerin kodda tutulduğunu kanıtlar."""
from pfin.agent.schema import AgentOutput, Recommendation
from pfin.config import Config
from pfin.data.facts import FactBundle
from pfin.guardrails.rules import apply_guardrails
from pfin.memory.schema import Market, Position, State

CFG = Config(raw={"guardrails": {"max_position_pct": 0.20, "min_cash_pct": 0.15,
                                 "max_open_positions": 6, "min_confidence": 0.55}})


def _bundle(quotes=None, position_facts=None):
    b = FactBundle(asof="t", portfolio={})
    b.watchlist_quotes = [{"symbol": s, "price": p} for s, p in (quotes or {}).items()]
    b.position_facts = position_facts or []
    return b


def _rec(**kw):
    base = dict(symbol="X", market="BIST", action="buy", thesis="tez", refuter="çürütücü",
                confidence=0.7, sources=["https://s"])
    base.update(kw)
    return Recommendation(**base)


def test_stopless_buy_rejected():
    out = AgentOutput(market_summary="", new_ideas=[_rec(symbol="THYAO", stop=None)])
    r = apply_guardrails(out, _bundle({"THYAO": 100}), State(cash_try=50000), CFG)
    assert r.rejected() and "Stop'suz" in r.rejected()[0].notes[0]


def test_stop_above_entry_rejected():
    out = AgentOutput(market_summary="", new_ideas=[_rec(symbol="THYAO", stop=120)])
    r = apply_guardrails(out, _bundle({"THYAO": 100}), State(cash_try=50000), CFG)
    assert r.rejected(), "girişin üstünde stop reddedilmeli"


def test_missing_source_rejected():
    out = AgentOutput(market_summary="", recommendations=[_rec(action="hold", sources=[])])
    r = apply_guardrails(out, _bundle(), State(), CFG)
    assert r.rejected() and "Kaynaksız" in r.rejected()[0].notes[0]


def test_missing_refuter_rejected():
    out = AgentOutput(market_summary="", recommendations=[_rec(action="hold", refuter="  ")])
    r = apply_guardrails(out, _bundle(), State(), CFG)
    assert r.rejected() and "Çürütücü" in r.rejected()[0].notes[0]


def test_oversized_capped_to_20pct():
    out = AgentOutput(market_summary="", new_ideas=[_rec(symbol="THYAO", stop=90, target_weight_pct=40)])
    r = apply_guardrails(out, _bundle({"THYAO": 100}), State(cash_try=50000), CFG)
    acc = r.accepted()
    assert acc and acc[0].status == "capped" and acc[0].final_weight_pct == 20.0


def test_max_open_positions_enforced():
    state = State(cash_try=50000)
    for i in range(6):
        state.positions.append(Position(id=f"p{i}", symbol=f"S{i}", market=Market.BIST,
            entry_price=10, shares=1, stop=9, thesis="t", refuter="r"))
    out = AgentOutput(market_summary="", new_ideas=[_rec(symbol="NEW", stop=90)])
    r = apply_guardrails(out, _bundle({"NEW": 100}), state, CFG)
    assert r.rejected() and "6 açık pozisyon" in r.rejected()[0].notes[-1]


def test_low_confidence_stamped():
    out = AgentOutput(market_summary="", recommendations=[_rec(action="hold", confidence=0.4)])
    r = apply_guardrails(out, _bundle(), State(), CFG)
    v = r.accepted()[0]
    assert v.low_confidence and "DÜŞÜK GÜVEN" in v.notes[0]


def test_stop_broken_forces_exit_and_overrides_model():
    state = State(cash_try=40000)
    state.positions.append(Position(id="p1", symbol="EREGL", market=Market.BIST,
        entry_price=45, shares=200, stop=42, thesis="t", refuter="r"))
    pf = [{"id": "p1", "symbol": "EREGL", "market": "BIST", "stop": 42,
           "quote": {"symbol": "EREGL", "price": 41}, "stop_broken": True}]
    out = AgentOutput(market_summary="", recommendations=[
        _rec(symbol="EREGL", action="hold", confidence=0.9)])
    r = apply_guardrails(out, _bundle(position_facts=pf), state, CFG)
    assert r.forced_exits and r.forced_exits[0].rec.action == "exit"
    assert r.vetted[0].status == "rejected"  # model HOLD'u geçersiz
