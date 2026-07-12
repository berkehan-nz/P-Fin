from pfin.config import Config
from pfin.cost.budget import over_budget, record_usage
from pfin.memory.schema import BudgetState

CFG = Config(raw={"budget": {"monthly_cap_usd": 50.0, "price_input_per_mtok": 5.0,
                             "price_output_per_mtok": 25.0,
                             "price_cache_write_per_mtok": 6.25,
                             "price_cache_read_per_mtok": 0.50}})


def test_cost_computation():
    b = BudgetState()
    usage = {"input_tokens": 1_000_000, "output_tokens": 1_000_000,
             "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
    cost = record_usage(b, usage, CFG)
    assert cost == 30.0  # 1M*5 + 1M*25 = 30
    assert b.spend_usd == 30.0
    assert not b.throttled


def test_cache_read_is_cheap():
    b = BudgetState()
    usage = {"input_tokens": 0, "output_tokens": 0,
             "cache_read_input_tokens": 1_000_000, "cache_creation_input_tokens": 0}
    assert record_usage(b, usage, CFG) == 0.5


def test_throttle_when_over_cap():
    b = BudgetState()
    record_usage(b, {"input_tokens": 12_000_000, "output_tokens": 0}, CFG)  # $60 > $50
    assert b.throttled
    assert over_budget(b, CFG)


def test_none_usage_no_crash():
    b = BudgetState()
    assert record_usage(b, None, CFG) == 0.0
