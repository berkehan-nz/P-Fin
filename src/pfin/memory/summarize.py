"""Bağlam özetleme + budama (§3.4 — bu projedeki 1 numaralı maliyet riski).

Modele hafıza HAM dökülmez. Bu modül modele beslenecek KOMPAKT bir özet üretir:
açık pozisyonlar (tez+çürütücü+durum), son N kararın kısası, kaynak karnesi
üst-satırı, örüntü hafızası, performans serisinin son noktaları. Eski kararlar
budanır; yalnız özet taşınır.

Ayrıca çalışan hafızanın kendisini de budar (`prune_state`) ki state.json ve
context sonsuza dek şişmesin.
"""
from __future__ import annotations

from .schema import State

# Modele taşınacak pencereler (context bütçesini korur)
RECENT_DECISIONS = 12
RECENT_PERF_POINTS = 8
MAX_CLAIMS_PER_SOURCE_IN_CONTEXT = 5

# Kalıcı hafızada tutulacak üst sınırlar (state.json şişmesini önler)
KEEP_DECISIONS = 200
KEEP_PERF_POINTS = 400
KEEP_LOG = 200
KEEP_CLAIMS_PER_SOURCE = 60


def summarize_for_model(state: State) -> dict:
    """Modele verilecek kompakt, özetlenmiş bağlam. Ham hafıza dökülmez."""
    open_pos = state.open_positions()

    positions = [
        {
            "id": p.id,
            "symbol": p.symbol,
            "market": p.market.value,
            "entry_price": p.entry_price,
            "shares": p.shares,
            "stop": p.stop,
            "thesis": p.thesis,
            "refuter": p.refuter,
            "invalidation": p.invalidation,
            "opened_source": p.opened_source,
            "entry_date": p.entry_date,
        }
        for p in open_pos
    ]

    recent_decisions = [
        {
            "date": d.date,
            "symbol": d.symbol,
            "action": d.action,
            "confidence": round(d.confidence, 2),
            "rationale": _clip(d.rationale, 240),
            "outcome": _clip(d.outcome, 160) if d.outcome else "",
        }
        for d in state.decisions[-RECENT_DECISIONS:]
    ]

    sources = []
    for card in state.sources:
        hr = card.hit_rate()
        sources.append({
            "name": card.name,
            "trust": card.trust,
            "hit_rate": None if hr is None else round(hr, 2),
            "recent_claims": [
                {"date": c.date, "symbol": c.symbol, "claim": _clip(c.claim, 160),
                 "status": c.status.value}
                for c in card.claims[-MAX_CLAIMS_PER_SOURCE_IN_CONTEXT:]
            ],
        })

    patterns = [
        {"thesis_type": pt.thesis_type, "wins": pt.wins, "losses": pt.losses,
         "note": _clip(pt.note, 120)}
        for pt in state.patterns
    ]

    perf = state.performance[-RECENT_PERF_POINTS:]
    perf_summary = [
        {"date": pp.date, "portfolio": round(pp.portfolio_value_try, 2),
         "xu100": pp.xu100, "tufe_yoy": pp.tufe_yoy}
        for pp in perf
    ]

    return {
        "portfolio": {
            "cash_try": round(state.cash_try, 2),
            "total_value_try": round(state.portfolio_value(), 2),
            "cash_pct": round(state.cash_pct(), 3),
            "open_position_count": len(open_pos),
        },
        "open_positions": positions,
        "recent_decisions": recent_decisions,
        "sources": sources,
        "patterns": patterns,
        "performance_recent": perf_summary,
        "watchlist": state.watchlist,
        "budget": {
            "month": state.budget.month,
            "spend_usd": round(state.budget.spend_usd, 2),
            "throttled": state.budget.throttled,
        },
    }


def prune_state(state: State) -> State:
    """Kalıcı hafızayı budar: eski kararlar/performans/log/iddialar kırpılır."""
    if len(state.decisions) > KEEP_DECISIONS:
        state.decisions = state.decisions[-KEEP_DECISIONS:]
    if len(state.performance) > KEEP_PERF_POINTS:
        state.performance = state.performance[-KEEP_PERF_POINTS:]
    if len(state.log) > KEEP_LOG:
        state.log = state.log[-KEEP_LOG:]
    for card in state.sources:
        if len(card.claims) > KEEP_CLAIMS_PER_SOURCE:
            card.claims = card.claims[-KEEP_CLAIMS_PER_SOURCE:]
    return state


def _clip(text: str, limit: int) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
