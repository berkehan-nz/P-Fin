"""Veri katmanı değer tipleri. Her sayı KAYNAK + ZAMAN damgası taşır (Değişmez #1).

LLM asla bir sayının kaynağı değildir; bu tipler sayının nereden ve ne zaman
geldiğini izlenebilir kılar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Quote:
    """Bir enstrümanın fiyat anlık görüntüsü. price None ise veri gelmedi demektir."""
    symbol: str
    market: str                       # BIST | US | TEFAS | INDEX
    price: float | None
    currency: str = ""
    previous_close: float | None = None
    change_pct: float | None = None
    volume: float | None = None
    avg_volume: float | None = None
    source: str = ""                  # ör. 'borsapy', 'twelvedata', 'yfinance'
    asof: str = field(default_factory=_now_iso)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.price is not None and self.error is None


@dataclass
class FinancialSnapshot:
    """Seçili temel/bilanço kalemleri. Tez'i veriyle onaylamak için (Değişmez #2)."""
    symbol: str
    market: str
    items: dict[str, float] = field(default_factory=dict)   # ör. {'total_revenue':..}
    period: str = ""                  # en son dönem etiketi
    source: str = ""
    asof: str = field(default_factory=_now_iso)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return bool(self.items) and self.error is None
