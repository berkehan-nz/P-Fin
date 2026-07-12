"""Kaynak karnesi (§4): iddia → sonuç eşleştirmesi.

- Yalnız NET, TARİHLİ, düşülebilir iddialar puanlanır (`scoreable`); belirsizler kaydedilir
  ama puanlanmaz.
- Bora Özkent başlangıç kaynağı ama ölçümden muaf değildir; karnesi tutan ağırlık kazanır.
- Yeni isimler otomatik "observation" (gözlem) statüsüyle girer; baştan güvenilir sayılmaz.
"""
from __future__ import annotations

import hashlib

from ..agent.schema import SourceObservation
from ..memory.schema import ClaimStatus, SourceCard, SourceClaim, State

SEED_SOURCE = "Bora Özkent"


def ensure_seed(state: State) -> None:
    """Bora Özkent'i onaylı başlangıç kaynağı olarak ekler (yoksa)."""
    card = state.source_card(SEED_SOURCE)
    if card.trust == "observation" and not card.claims:
        card.trust = "approved"


def record_observations(state: State, observations: list[SourceObservation],
                        run_date: str) -> int:
    """Ajanın topladığı iddiaları karneye ekler. Eklenen puanlanabilir iddia sayısını döner."""
    added = 0
    for obs in observations:
        card = state.source_card(obs.source_name)
        # Anonim/pump kaynakları evrene alınmaz (§4) — basit ad temelli süzgeç
        if _is_disallowed(obs.source_name):
            continue
        claim_id = _claim_id(obs.source_name, obs.claim, obs.date or run_date)
        if any(c.id == claim_id for c in card.claims):
            continue
        direction = obs.direction if obs.direction in ("up", "down", "neutral") else None
        card.claims.append(SourceClaim(
            id=claim_id,
            date=obs.date or run_date,
            symbol=obs.symbol,
            claim=obs.claim,
            direction=direction,
            scored=bool(obs.scoreable),
            status=ClaimStatus.OPEN if obs.scoreable else ClaimStatus.UNSCORED,
        ))
        if obs.scoreable:
            added += 1
    return added


def _is_disallowed(name: str) -> bool:
    low = (name or "").lower()
    banned = ["anonim", "forum", "pump", "sinyal grubu", "telegram", "kanal"]
    return any(b in low for b in banned)


def _claim_id(source: str, claim: str, date: str) -> str:
    h = hashlib.sha1(f"{source}|{claim}|{date}".encode("utf-8")).hexdigest()
    return h[:12]
