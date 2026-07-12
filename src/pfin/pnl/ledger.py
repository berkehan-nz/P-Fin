"""Giriş/çıkış kaydı + P&L (§3.6).

Kullanıcı Midas'ta işlem yapınca GERÇEKLEŞEN fiyatı sisteme girer. Ajanın önerdiği
fiyat değil, gerçekleşen fiyat esastır; tüm P&L ve raporlama buna dayanır.

- buy  → yeni pozisyon açar veya mevcut pozisyona ekler (ortalama maliyet). Nakit düşer.
- sell → pozisyonu azaltır/kapatır; gerçekleşen P&L hesaplanır. Nakit artar.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..memory.schema import Decision, LogEntry, Market, Position, State


class LedgerError(ValueError):
    pass


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def record_fill(state: State, *, symbol: str, market: str, side: str, shares: float,
                price: float, date: str | None = None, stop: float | None = None,
                thesis: str = "", refuter: str = "", invalidation: str = "",
                name: str = "", source: str | None = None) -> dict:
    """Gerçekleşen bir işlemi kaydeder. Sonuç sözlüğü döner (realized_pnl vb.)."""
    if shares <= 0 or price <= 0:
        raise LedgerError("shares ve price pozitif olmalı")
    side = side.lower()
    date = date or _today()
    symbol_u = symbol.upper()
    mkt = Market(market.upper())
    pos = _find_open(state, symbol_u, mkt)

    if side == "buy":
        result = _apply_buy(state, pos, symbol_u, mkt, shares, price, date, stop,
                            thesis, refuter, invalidation, name, source)
    elif side == "sell":
        if pos is None:
            raise LedgerError(f"{symbol_u}: satılacak açık pozisyon yok")
        result = _apply_sell(state, pos, shares, price, date)
    else:
        raise LedgerError("side 'buy' veya 'sell' olmalı")

    state.decisions.append(Decision(
        id=f"fill-{date}-{symbol_u}-{uuid.uuid4().hex[:6]}", date=date, symbol=symbol_u,
        action="buy" if side == "buy" else "reduce",
        rationale=f"Gerçekleşen {side}: {shares} @ {price}",
        thesis=thesis, refuter=refuter, stop=stop, invalidation=invalidation,
        sources=[source] if source else [], confidence=1.0,
        outcome=result.get("note", "")))
    state.log.append(LogEntry(kind="fill", message=result.get("note", "")))
    return result


def _apply_buy(state, pos, symbol, mkt, shares, price, date, stop, thesis, refuter,
               invalidation, name, source) -> dict:
    cost = shares * price
    if cost > state.cash_try + 1e-9:
        # Uyarı ama engelleme yok (kullanıcı gerçekte yaptıysa nakit güncel değildir)
        note_cash = " [uyarı: nakit yetersiz görünüyor — nakiti güncelleyin]"
    else:
        note_cash = ""
    state.cash_try -= cost

    if pos is None:
        if not (thesis and refuter and stop):
            raise LedgerError("Yeni alım için thesis, refuter ve stop zorunlu (Değişmezler §2.2–2.4)")
        state.positions.append(Position(
            id=f"pos-{symbol}-{uuid.uuid4().hex[:6]}", symbol=symbol, market=mkt, name=name,
            entry_price=price, shares=shares, entry_date=date, stop=stop,
            thesis=thesis, refuter=refuter, invalidation=invalidation, opened_source=source,
            current_price=price, last_action="buy", status="open"))
        return {"action": "opened", "note": f"{symbol}: {shares} @ {price} yeni pozisyon açıldı.{note_cash}"}

    # Ortalama maliyet güncelle
    total_shares = pos.shares + shares
    pos.entry_price = (pos.cost_basis() + cost) / total_shares
    pos.shares = total_shares
    if stop:
        pos.stop = stop
    pos.last_action = "buy"
    return {"action": "added",
            "note": f"{symbol}: +{shares} @ {price}; yeni ort. maliyet {pos.entry_price:.4f}.{note_cash}"}


def _apply_sell(state, pos, shares, price, date) -> dict:
    if shares > pos.shares + 1e-9:
        raise LedgerError(f"{pos.symbol}: elde {pos.shares} var, {shares} satılamaz")
    realized = (price - pos.entry_price) * shares
    state.cash_try += shares * price
    state.realized_pnl_try = round(state.realized_pnl_try + realized, 2)
    pos.shares -= shares
    pos.last_action = "reduce"
    if pos.shares <= 1e-9:
        pos.status = "closed"
        pos.exit_price = price
        pos.exit_date = date
        pos.shares = 0.0
        action = "closed"
    else:
        action = "reduced"
    return {"action": action, "realized_pnl": round(realized, 2),
            "note": f"{pos.symbol}: {shares} @ {price} satıldı; gerçekleşen P&L {realized:,.2f} ₺ ({action})."}


def realized_pnl_total(state: State) -> float:
    """Birikmiş gerçekleşen P&L (satışlarda anlık hesaplanıp state'te toplanır)."""
    return round(state.realized_pnl_try, 2)


def _find_open(state: State, symbol: str, market: Market) -> Position | None:
    for p in state.positions:
        if p.status == "open" and p.symbol.upper() == symbol and p.market == market:
            return p
    return None
