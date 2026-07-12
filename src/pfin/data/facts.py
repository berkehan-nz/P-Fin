"""Deterministik "facts" paketi (Değişmez #1: sayılar API'den).

Sabah turu modele bu paketi verir. Modelin gördüğü tüm sayılar buradan gelir ve
kaynak+zaman damgalıdır. Model bu sayıları YORUMLAR ama üretmez. Rapor da bu
paketten basılır, LLM metninden değil.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import Config
from ..memory.schema import State
from . import macro, prices
from .models import FinancialSnapshot, Quote
from .ratecounter import RateCounter


@dataclass
class FactBundle:
    asof: str
    portfolio: dict                                # nakit, toplam değer, nakit %
    position_facts: list[dict] = field(default_factory=list)   # açık pozisyon + canlı fiyat
    watchlist_quotes: list[dict] = field(default_factory=list)
    benchmark: dict = field(default_factory=dict)  # XU100 + TÜFE
    errors: list[str] = field(default_factory=list)

    def to_model_context(self) -> dict:
        """Modele verilecek kompakt sözlük (sayılar burada, kaynaklı)."""
        return {
            "asof": self.asof,
            "portfolio": self.portfolio,
            "positions": self.position_facts,
            "watchlist": self.watchlist_quotes,
            "benchmark": self.benchmark,
            "data_errors": self.errors,
        }


def _quote_dict(q: Quote) -> dict:
    return {
        "symbol": q.symbol, "market": q.market, "price": q.price,
        "currency": q.currency, "previous_close": q.previous_close,
        "change_pct": q.change_pct, "volume": q.volume, "avg_volume": q.avg_volume,
        "source": q.source, "asof": q.asof, "error": q.error,
    }


def _fin_dict(f: FinancialSnapshot) -> dict:
    return {"period": f.period, "items": f.items, "source": f.source,
            "asof": f.asof, "error": f.error}


def build_fact_bundle(state: State, config: Config,
                      include_watchlist: bool = True) -> FactBundle:
    """Portföy + izleme evreni için canlı facts paketi kurar."""
    td_key = config.secrets.twelvedata_api_key
    counter = RateCounter(
        state.ratelimit,
        per_minute=config.get("twelvedata", "calls_per_minute", default=8),
        per_day=config.get("twelvedata", "calls_per_day", default=800),
    )
    bundle = FactBundle(
        asof=_now(),
        portfolio={
            "cash_try": round(state.cash_try, 2),
            "total_value_try": round(state.portfolio_value(), 2),
            "cash_pct": round(state.cash_pct(), 3),
            "open_position_count": len(state.open_positions()),
        },
    )

    # 1) Açık pozisyonlar — fiyat + temel veri + stop mesafesi
    for pos in state.open_positions():
        q = prices.quote_for(pos.symbol, pos.market.value, td_key, counter)
        if q.ok:
            pos.current_price = q.price
            pos.price_asof = q.asof
        else:
            bundle.errors.append(f"{pos.symbol}: {q.error}")
        fin = prices.financials_for(pos.symbol, pos.market.value)
        stop_dist = None
        if q.price is not None and pos.stop:
            stop_dist = round((q.price - pos.stop) / q.price * 100, 2)
        bundle.position_facts.append({
            "id": pos.id, "symbol": pos.symbol, "market": pos.market.value,
            "entry_price": pos.entry_price, "shares": pos.shares, "stop": pos.stop,
            "thesis": pos.thesis, "refuter": pos.refuter,
            "quote": _quote_dict(q),
            "financials": _fin_dict(fin),
            "unrealized_pnl_try": pos.unrealized_pnl(),
            "stop_distance_pct": stop_dist,
            "stop_broken": bool(q.price is not None and pos.stop and q.price <= pos.stop),
        })

    # 2) İzleme evreni (fiyat özeti; temel veri sabah turunda talep üzerine)
    if include_watchlist:
        seen = {p.symbol for p in state.open_positions()}
        for market_key, syms in (("BIST", config.get("universe", "bist", default=[])),
                                  ("US", config.get("universe", "us", default=[])),
                                  ("TEFAS", config.get("universe", "tefas", default=[]))):
            for sym in list(syms) + [w for w in state.watchlist if w not in syms]:
                if sym in seen:
                    continue
                seen.add(sym)
                q = prices.quote_for(sym, market_key, td_key, counter)
                bundle.watchlist_quotes.append(_quote_dict(q))

    # 3) Kıyas: XU100 + TÜFE (§2.6 — isteğe bağlı değil)
    idx = macro.get_index_quote(config.index_symbol)
    tufe, tufe_note = macro.get_tufe_yoy(config.secrets.evds_api_key)
    bundle.benchmark = {
        "index_symbol": config.index_symbol,
        "index_quote": _quote_dict(idx),
        "tufe_yoy_pct": tufe,
        "tufe_note": tufe_note,
    }
    if not idx.ok:
        bundle.errors.append(f"{config.index_symbol}: {idx.error}")
    if tufe is None:
        bundle.errors.append(f"TÜFE: {tufe_note}")

    return bundle


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
