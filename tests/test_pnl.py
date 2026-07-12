import pytest

from pfin.memory.schema import State
from pfin.pnl.ledger import LedgerError, record_fill


def test_buy_then_partial_sell_pnl():
    s = State(cash_try=50000)
    record_fill(s, symbol="THYAO", market="BIST", side="buy", shares=20, price=255,
                stop=240, thesis="tez", refuter="çürütücü")
    assert s.cash_try == 50000 - 20 * 255
    assert len(s.open_positions()) == 1

    res = record_fill(s, symbol="THYAO", market="BIST", side="sell", shares=10, price=275)
    assert res["realized_pnl"] == pytest.approx((275 - 255) * 10)
    assert s.realized_pnl_try == pytest.approx(200.0)
    assert s.open_positions()[0].shares == 10


def test_full_sell_closes_position():
    s = State(cash_try=50000)
    record_fill(s, symbol="X", market="US", side="buy", shares=5, price=100,
                stop=90, thesis="t", refuter="r")
    record_fill(s, symbol="X", market="US", side="sell", shares=5, price=120)
    assert s.open_positions() == []
    assert s.realized_pnl_try == pytest.approx(100.0)


def test_average_cost_on_add():
    s = State(cash_try=100000)
    record_fill(s, symbol="A", market="BIST", side="buy", shares=10, price=100,
                stop=90, thesis="t", refuter="r")
    record_fill(s, symbol="A", market="BIST", side="buy", shares=10, price=120)
    assert s.open_positions()[0].entry_price == pytest.approx(110.0)


def test_new_buy_requires_thesis_refuter_stop():
    s = State(cash_try=50000)
    with pytest.raises(LedgerError):
        record_fill(s, symbol="Z", market="BIST", side="buy", shares=1, price=10)


def test_cannot_oversell():
    s = State(cash_try=50000)
    record_fill(s, symbol="A", market="BIST", side="buy", shares=5, price=10,
                stop=9, thesis="t", refuter="r")
    with pytest.raises(LedgerError):
        record_fill(s, symbol="A", market="BIST", side="sell", shares=10, price=12)
