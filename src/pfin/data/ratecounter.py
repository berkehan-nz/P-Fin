"""Twelve Data ücretsiz katman sayacı (8 çağrı/dk, 800/gün).

Plan §5: "çağrı sayacı tutulmalı." Sayaç state.json'da yaşar, run'lar arası korunur.
Limit aşımı yaklaşınca çağrı reddedilir (sessizce limit aşıp banlanmaktansa).
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..memory.schema import RateLimitState


class RateLimitExceeded(RuntimeError):
    pass


class RateCounter:
    def __init__(self, state: RateLimitState, per_minute: int = 8, per_day: int = 800):
        self.state = state
        self.per_minute = per_minute
        self.per_day = per_day

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _roll(self) -> None:
        now = self._now()
        today = now.date().isoformat()
        minute = now.strftime("%Y-%m-%dT%H:%M")
        if self.state.day != today:
            self.state.day = today
            self.state.calls_today = 0
        if self.state.minute_bucket != minute:
            self.state.minute_bucket = minute
            self.state.calls_this_minute = 0

    def can_call(self) -> bool:
        self._roll()
        return (self.state.calls_today < self.per_day
                and self.state.calls_this_minute < self.per_minute)

    def record(self) -> None:
        """Bir çağrı yapıldığında sayacı artır. Limit aşılıyorsa hata fırlatır."""
        self._roll()
        if self.state.calls_today >= self.per_day:
            raise RateLimitExceeded(f"Twelve Data günlük limit ({self.per_day}) doldu")
        if self.state.calls_this_minute >= self.per_minute:
            raise RateLimitExceeded(f"Twelve Data dakika limiti ({self.per_minute}) doldu")
        self.state.calls_today += 1
        self.state.calls_this_minute += 1

    def remaining_today(self) -> int:
        self._roll()
        return max(0, self.per_day - self.state.calls_today)
