from pathlib import Path

from pfin.memory.schema import Market, Position, State
from pfin.memory.store import load_state, save_state
from pfin.memory.summarize import prune_state, summarize_for_model, KEEP_DECISIONS
from pfin.memory.schema import Decision


def test_empty_state_works():
    s = State()
    assert s.portfolio_value() == 0.0
    assert s.cash_pct() == 1.0
    assert summarize_for_model(s)["portfolio"]["open_position_count"] == 0


def test_round_trip(tmp_path: Path):
    s = State(cash_try=40000)
    s.positions.append(Position(id="p1", symbol="ASELS", market=Market.BIST,
        entry_price=100.0, shares=100, stop=90.0, thesis="t", refuter="r"))
    s.positions[0].current_price = 110.0
    p = tmp_path / "state.json"
    save_state(s, p)
    s2 = load_state(p)
    assert s2.positions[0].symbol == "ASELS"
    assert abs(s2.portfolio_value() - 51000.0) < 1e-6
    assert s2.positions[0].unrealized_pnl() == 1000.0


def test_missing_file_returns_empty(tmp_path: Path):
    assert load_state(tmp_path / "nope.json").portfolio_value() == 0.0


def test_prune_caps_history():
    s = State()
    s.decisions = [Decision(id=str(i), action="hold", rationale="x") for i in range(KEEP_DECISIONS + 50)]
    prune_state(s)
    assert len(s.decisions) == KEEP_DECISIONS
