"""Nöbetçi (§3.1) — deterministik, LLM YOK, maliyet ~sıfır.

Sık koşar. Görevi: eşik izlemek ve gerekirse pahalı ajanı UYANDIRMAK / acil mail
üretmek. Açık pozisyonların stop'unu, gün içi sert hareketi, anormal hacmi ve
portföydeki şirketlerden KAP bildirimini izler.

Tekrar-uyarı önleme: aynı olay (aynı gün) `state.alerts_sent`'te tutulur.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..config import Config
from ..data import kap, prices
from ..data.ratecounter import RateCounter
from ..memory.schema import State
from .triggers import Thresholds, TriggerEvent


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def check(state: State, config: Config) -> list[TriggerEvent]:
    """Deterministik eşik taraması. Tetiklenen (ve daha önce uyarılmamış) olayları döner."""
    th = Thresholds.from_config(config)
    td_key = config.secrets.twelvedata_api_key
    counter = RateCounter(state.ratelimit,
                          per_minute=config.get("twelvedata", "calls_per_minute", default=8),
                          per_day=config.get("twelvedata", "calls_per_day", default=800))
    seen = set(state.alerts_sent)
    events: list[TriggerEvent] = []

    # 1) Açık pozisyon fiyat tabanlı tetikler
    bist_symbols: list[str] = []
    for pos in state.open_positions():
        if pos.market.value == "BIST":
            bist_symbols.append(pos.symbol)
        q = prices.quote_for(pos.symbol, pos.market.value, td_key, counter)
        if not q.ok:
            continue
        pos.current_price = q.price
        pos.price_asof = q.asof

        # Stop kırılması → KRİTİK (LLM'e sorulmadan acil)
        if pos.stop and q.price <= pos.stop:
            key = f"stop:{pos.symbol}:{_today()}"
            if key not in seen:
                events.append(TriggerEvent(
                    kind="stop_broken", symbol=pos.symbol, severity="critical",
                    message=f"Stop kırıldı: fiyat {q.price} ≤ stop {pos.stop}. Çıkış planı devrede.",
                    dedupe_key=key, data={"price": q.price, "stop": pos.stop}))

        # Gün içi sert hareket
        if q.change_pct is not None and abs(q.change_pct) >= th.intraday_move_pct * 100:
            key = f"move:{pos.symbol}:{_today()}:{round(q.change_pct)}"
            if key not in seen:
                events.append(TriggerEvent(
                    kind="sharp_move", symbol=pos.symbol,
                    severity="critical" if abs(q.change_pct) >= th.intraday_move_pct * 150 else "warning",
                    message=f"Gün içi sert hareket: %{q.change_pct}.",
                    dedupe_key=key, data={"change_pct": q.change_pct}))

        # Anormal hacim
        if q.volume and q.avg_volume and q.volume >= q.avg_volume * th.abnormal_volume_mult:
            key = f"vol:{pos.symbol}:{_today()}"
            if key not in seen:
                events.append(TriggerEvent(
                    kind="abnormal_volume", symbol=pos.symbol, severity="warning",
                    message=f"Anormal hacim: {q.volume:.0f} (ort. {q.avg_volume:.0f}).",
                    dedupe_key=key, data={"volume": q.volume, "avg_volume": q.avg_volume}))

    # 2) KAP bildirimleri (portföydeki BIST şirketleri)
    for d in kap.recent_disclosures(bist_symbols, hours=th.kap_lookback_hours):
        key = f"kap:{d.symbol}:{d.published_at}"
        if key in seen:
            continue
        events.append(TriggerEvent(
            kind="kap", symbol=d.symbol, severity="warning",
            message=f"KAP bildirimi: {d.title} ({d.url})".strip(),
            dedupe_key=key, data={"url": d.url}))

    return events


def mark_sent(state: State, events: list[TriggerEvent]) -> None:
    for e in events:
        if e.dedupe_key and e.dedupe_key not in state.alerts_sent:
            state.alerts_sent.append(e.dedupe_key)
    # dedupe listesini sınırla (bellek şişmesi)
    if len(state.alerts_sent) > 500:
        state.alerts_sent = state.alerts_sent[-500:]
