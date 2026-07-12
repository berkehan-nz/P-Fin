"""Token / harcama sayacı ve aylık tavan (§6).

Anthropic yanıtındaki `usage`'dan token→USD hesaplar, aylık harcamayı state'te tutar.
Tavan aşılırsa `throttled=True` → sabah turu bir sonraki günlerde seyrelir (sessizce
bütçe aşılmaz). Fiyatlama config.yaml'de parametrik.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..config import Config
from ..memory.schema import BudgetState


def _month() -> str:
    return datetime.now(timezone.utc).date().isoformat()[:7]


def _price(config: Config, key: str, default: float) -> float:
    return float(config.get("budget", key, default=default))


def record_usage(state_budget: BudgetState, usage, config: Config,
                 web_search_calls: int = 0) -> float:
    """Bir Anthropic çağrısının maliyetini ekler. Eklenen USD'yi döner.

    `usage` Anthropic Usage nesnesi veya dict olabilir (input_tokens, output_tokens,
    cache_creation_input_tokens, cache_read_input_tokens).
    """
    if state_budget.month != _month():
        # Yeni ay: sayaç sıfırlanır, throttle kalkar
        state_budget.month = _month()
        state_budget.spend_usd = 0.0
        state_budget.tokens_in = state_budget.tokens_out = 0
        state_budget.cache_write_tokens = state_budget.cache_read_tokens = 0
        state_budget.web_search_calls = 0
        state_budget.throttled = False

    def _u(name: str) -> int:
        if usage is None:
            return 0
        if isinstance(usage, dict):
            return int(usage.get(name, 0) or 0)
        return int(getattr(usage, name, 0) or 0)

    tin = _u("input_tokens")
    tout = _u("output_tokens")
    cwrite = _u("cache_creation_input_tokens")
    cread = _u("cache_read_input_tokens")

    cost = (
        tin / 1e6 * _price(config, "price_input_per_mtok", 5.0)
        + tout / 1e6 * _price(config, "price_output_per_mtok", 25.0)
        + cwrite / 1e6 * _price(config, "price_cache_write_per_mtok", 6.25)
        + cread / 1e6 * _price(config, "price_cache_read_per_mtok", 0.50)
    )
    # web_search server tool ücreti (yaklaşık $10 / 1000 çağrı)
    cost += web_search_calls * 0.01

    state_budget.tokens_in += tin
    state_budget.tokens_out += tout
    state_budget.cache_write_tokens += cwrite
    state_budget.cache_read_tokens += cread
    state_budget.web_search_calls += web_search_calls
    state_budget.spend_usd = round(state_budget.spend_usd + cost, 4)

    cap = _price(config, "monthly_cap_usd", 50.0)
    if state_budget.spend_usd >= cap:
        state_budget.throttled = True
    return round(cost, 4)


def over_budget(state_budget: BudgetState, config: Config) -> bool:
    if state_budget.month != _month():
        return False
    return state_budget.spend_usd >= _price(config, "monthly_cap_usd", 50.0)
