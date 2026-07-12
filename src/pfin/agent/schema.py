"""Sabah turu ajanının YAPILANDIRILMIŞ çıktı şeması (§3.2 — serbest metin değil).

Model çıktısını forced tool-use ile bu şemaya uymak zorunda bırakırız; böylece
korkuluk katmanı (kod) üzerinde deterministik kontrol yapabilir.

Değişmezler şemada zorunlu kılınır: her öneride `thesis` + `refuter`; alım (`buy`)
`stop` olmadan üretilemez; her öneri en az bir `source` taşımalı (§9).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Action = Literal["buy", "hold", "reduce", "exit", "switch", "no_action"]

TOOL_NAME = "emit_briefing"


class Recommendation(BaseModel):
    symbol: str
    market: Literal["BIST", "US", "TEFAS"]
    action: Action
    position_id: str | None = None            # mevcut pozisyon için (varsa)
    thesis: str                               # tez (§2.2)
    refuter: str                              # çürütücü — ZORUNLU (§2.3)
    invalidation: str = ""                    # tez-geçersizlik koşulu (§2.4)
    stop: float | None = None                 # buy/switch için zorunlu (korkuluk denetler)
    target_weight_pct: float | None = None    # önerilen portföy ağırlığı (%)
    suggested_shares: float | None = None
    switch_to: str | None = None              # action=switch için hedef sembol
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    rationale: str = ""                       # kısa, jargonsuz gerekçe
    sources: list[str] = Field(default_factory=list)   # en az 1 link (§9)


class SourceObservation(BaseModel):
    """Yorum katmanından net/tarihli iddia (§4). Belirsizler puanlanmaz."""
    source_name: str
    claim: str
    symbol: str | None = None
    direction: Literal["up", "down", "neutral"] | None = None
    scoreable: bool = False                   # net+tarihli+düşülebilir mi
    date: str | None = None


class AgentOutput(BaseModel):
    market_summary: str                       # kısa piyasa özeti (jargonsuz)
    recommendations: list[Recommendation] = Field(default_factory=list)
    new_ideas: list[Recommendation] = Field(default_factory=list)
    source_observations: list[SourceObservation] = Field(default_factory=list)
    notes: str = ""


def tool_schema() -> dict:
    """Anthropic forced tool-use için input_schema (temiz, ref'siz)."""
    rec = {
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "market": {"type": "string", "enum": ["BIST", "US", "TEFAS"]},
            "action": {"type": "string",
                       "enum": ["buy", "hold", "reduce", "exit", "switch", "no_action"]},
            "position_id": {"type": ["string", "null"]},
            "thesis": {"type": "string", "description": "Tez: aldığımız/tuttuğumuz sebep."},
            "refuter": {"type": "string",
                        "description": "Bu tezi ne çürütür — ZORUNLU. Boş bırakılamaz."},
            "invalidation": {"type": "string", "description": "Tez-geçersizlik koşulu."},
            "stop": {"type": ["number", "null"],
                     "description": "Stop seviyesi. buy/switch için zorunlu ve girişin altında olmalı."},
            "target_weight_pct": {"type": ["number", "null"]},
            "suggested_shares": {"type": ["number", "null"]},
            "switch_to": {"type": ["string", "null"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "rationale": {"type": "string"},
            "sources": {"type": "array", "items": {"type": "string"},
                        "description": "En az bir kaynak linki (§9)."},
        },
        "required": ["symbol", "market", "action", "thesis", "refuter",
                     "confidence", "sources"],
    }
    obs = {
        "type": "object",
        "properties": {
            "source_name": {"type": "string"},
            "claim": {"type": "string"},
            "symbol": {"type": ["string", "null"]},
            "direction": {"type": ["string", "null"], "enum": ["up", "down", "neutral", None]},
            "scoreable": {"type": "boolean"},
            "date": {"type": ["string", "null"]},
        },
        "required": ["source_name", "claim", "scoreable"],
    }
    return {
        "name": TOOL_NAME,
        "description": "Günlük brifingi yapılandırılmış olarak döndür. "
                       "TÜM sayısal alanlar (fiyat/stop) verilen facts'e dayanmalı.",
        "input_schema": {
            "type": "object",
            "properties": {
                "market_summary": {"type": "string"},
                "recommendations": {"type": "array", "items": rec},
                "new_ideas": {"type": "array", "items": rec},
                "source_observations": {"type": "array", "items": obs},
                "notes": {"type": "string"},
            },
            "required": ["market_summary", "recommendations"],
        },
    }
