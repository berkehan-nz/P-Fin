"""Hafıza şeması (state.json) — panelle paylaşılan SÖZLEŞME.

Değişmez (plan §3.4): Position her zaman giriş fiyatı (kullanıcıdan), adet, stop,
tez, çürütücü ve açılış tarihi taşır. Sayısal alanlar API/kullanıcı kaynaklıdır;
LLM bir sayının kaynağı olamaz.

Alan adları panelin (`finans-ajani-panel.jsx`) okuyacağı adlarla birebir eşleşir.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


class Market(str, Enum):
    BIST = "BIST"
    US = "US"
    TEFAS = "TEFAS"


Action = Literal["buy", "hold", "reduce", "exit", "switch", "no_action"]


class Position(BaseModel):
    """Açık (veya kapanmış) pozisyon. Değişmez alanlar zorunludur."""
    id: str
    symbol: str
    market: Market
    name: str = ""
    # --- Değişmez: gerçekleşen giriş (kullanıcıdan) + çıkış planı ---
    entry_price: float                       # gerçekleşen giriş fiyatı (Midas'tan)
    shares: float
    entry_date: str = Field(default_factory=_today_iso)
    stop: float                              # her girişte çıkış planı (§2.4)
    thesis: str                              # alım gerekçesi (§2.2)
    refuter: str                             # "bu tezi ne çürütür" (§2.3)
    invalidation: str = ""                   # tez-geçersizlik koşulu
    # --- Deterministik olarak güncellenen alanlar (facts'ten) ---
    current_price: float | None = None       # son fiyat (API kaynaklı, LLM değil)
    price_asof: str | None = None
    status: Literal["open", "closed"] = "open"
    last_action: Action | None = None
    confidence: float | None = None
    opened_source: str | None = None         # tezi başlatan kaynak (varsa)
    exit_price: float | None = None          # kapanışta gerçekleşen çıkış
    exit_date: str | None = None
    notes: str = ""

    def cost_basis(self) -> float:
        return self.entry_price * self.shares

    def market_value(self) -> float | None:
        if self.current_price is None:
            return None
        return self.current_price * self.shares

    def unrealized_pnl(self) -> float | None:
        mv = self.market_value()
        return None if mv is None else mv - self.cost_basis()


class ClaimStatus(str, Enum):
    OPEN = "open"           # sonuç henüz gözlenmedi
    HIT = "hit"             # iddia tuttu
    MISS = "miss"           # iddia tutmadı
    UNSCORED = "unscored"   # belirsiz/tarihsiz → puanlanmaz (§4)


class SourceClaim(BaseModel):
    """Bir kaynağın net, tarihli, düşülebilir iddiası (§4)."""
    id: str
    date: str
    symbol: str | None = None
    claim: str
    direction: Literal["up", "down", "neutral"] | None = None
    horizon_days: int | None = None
    scored: bool = False                     # belirsiz yorumlar kaydedilir ama puanlanmaz
    status: ClaimStatus = ClaimStatus.OPEN
    outcome_note: str = ""


class SourceCard(BaseModel):
    """Kaynak karnesi (§4). Bora Özkent başlangıç; hiçbiri ölçümden muaf değil."""
    name: str
    trust: Literal["approved", "observation", "rejected"] = "observation"
    claims: list[SourceClaim] = Field(default_factory=list)

    def hit_rate(self) -> float | None:
        scored = [c for c in self.claims if c.scored and c.status in (ClaimStatus.HIT, ClaimStatus.MISS)]
        if not scored:
            return None
        hits = sum(1 for c in scored if c.status == ClaimStatus.HIT)
        return hits / len(scored)


class Decision(BaseModel):
    """Karar arşivi kaydı (§3.4). Her karar gerekçe + en az bir kaynak taşır (§9)."""
    id: str
    date: str = Field(default_factory=_today_iso)
    symbol: str | None = None
    action: Action
    rationale: str
    sources: list[str] = Field(default_factory=list)   # kaynak linkleri (§9)
    confidence: float = 0.0
    thesis: str = ""
    refuter: str = ""
    stop: float | None = None
    invalidation: str = ""
    low_confidence: bool = False                        # korkuluk damgası
    guardrail_notes: list[str] = Field(default_factory=list)
    rejected: bool = False                              # korkuluk reddetti mi
    outcome: str = ""                                   # sonra ne oldu (sonradan doldurulur)


class Pattern(BaseModel):
    """Örüntü hafızası (§3.4): hangi tez tipleri tuttu/tutmadı."""
    thesis_type: str
    wins: int = 0
    losses: int = 0
    note: str = ""


class PerfPoint(BaseModel):
    """Performans serisi (§3.4/§7): portföy vs XU100 vs TÜFE."""
    date: str
    portfolio_value_try: float
    cash_try: float
    xu100: float | None = None
    tufe_yoy: float | None = None            # TÜFE yıllık (%)
    xu100_base: float | None = None          # kıyas normalize taban (ilk gün)


class BudgetState(BaseModel):
    """Aylık API harcama sayacı (§6). Tavan aşılırsa sistem kendini kısar."""
    month: str = Field(default_factory=lambda: _today_iso()[:7])
    spend_usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    web_search_calls: int = 0
    throttled: bool = False


class RateLimitState(BaseModel):
    """Twelve Data ücretsiz katman sayacı (8/dk, 800/gün)."""
    day: str = Field(default_factory=_today_iso)
    calls_today: int = 0
    minute_bucket: str = ""                  # 'YYYY-MM-DDTHH:MM'
    calls_this_minute: int = 0


class LogEntry(BaseModel):
    """Panel için ajan günlüğü satırı."""
    ts: str = Field(default_factory=_utc_now_iso)
    kind: Literal["morning", "sentinel", "fill", "alert", "system"] = "system"
    message: str


class Meta(BaseModel):
    schema_version: int = 1
    created_at: str = Field(default_factory=_utc_now_iso)
    last_run_at: str | None = None
    next_review_at: str | None = None


class State(BaseModel):
    """Kök hafıza nesnesi — state.json. Boşken de geçerlidir."""
    meta: Meta = Field(default_factory=Meta)
    cash_try: float = 0.0
    realized_pnl_try: float = 0.0                          # kapanan işlemlerden birikmiş gerçekleşen P&L
    positions: list[Position] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    sources: list[SourceCard] = Field(default_factory=list)
    patterns: list[Pattern] = Field(default_factory=list)
    performance: list[PerfPoint] = Field(default_factory=list)
    watchlist: list[str] = Field(default_factory=list)
    budget: BudgetState = Field(default_factory=BudgetState)
    ratelimit: RateLimitState = Field(default_factory=RateLimitState)
    log: list[LogEntry] = Field(default_factory=list)
    alerts_sent: list[str] = Field(default_factory=list)   # nöbetçi tekrar-uyarı önleyici anahtarları

    # --- Türetilmiş değerler (deterministik) ---
    def open_positions(self) -> list[Position]:
        return [p for p in self.positions if p.status == "open"]

    def positions_value(self) -> float:
        return sum(p.market_value() or p.cost_basis() for p in self.open_positions())

    def portfolio_value(self) -> float:
        return self.cash_try + self.positions_value()

    def cash_pct(self) -> float:
        total = self.portfolio_value()
        return (self.cash_try / total) if total > 0 else 1.0

    def source_card(self, name: str) -> SourceCard:
        for card in self.sources:
            if card.name.lower() == name.lower():
                return card
        card = SourceCard(name=name)
        self.sources.append(card)
        return card
