"""Finnhub — sirket haberleri ve kazanc takvimi (ucretsiz kota: 60 istek/dk).

Anahtar yoksa modul sessizce bos doner; veri hatti calismaya devam eder.
Haber KARAR girdisi degil, BAGLAM girdisidir: kartta listelenir, sohbetteki
Claude ozetler, puanlamaya girmez.
"""

from __future__ import annotations

from datetime import date, timedelta

from .. import config
from ..util import FINNHUB_LIMITER, http_get, read_json, write_json

CACHE_DIR = config.CACHE_DIR / "finnhub"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def enabled() -> bool:
    return bool(config.FINNHUB_API_KEY)


def _get(url: str, params: dict) -> list | dict | None:
    if not enabled():
        return None
    params = {**params, "token": config.FINNHUB_API_KEY}
    try:
        resp = http_get(url, params=params, limiter=FINNHUB_LIMITER)
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"  [uyari] finnhub {url.rsplit('/', 1)[-1]}: {exc}")
        return None


def news(ticker: str, *, days: int | None = None, limit: int | None = None) -> list[dict]:
    """Son ``days`` gunun sirket haberleri."""
    days = days or config.FINNHUB["news_lookback_days"]
    limit = limit or config.FINNHUB["max_news_per_ticker"]

    raw = _get(config.FINNHUB["news_url"], {
        "symbol": ticker.upper(),
        "from": (date.today() - timedelta(days=days)).isoformat(),
        "to": date.today().isoformat(),
    })
    if not isinstance(raw, list):
        return []

    items = []
    for entry in raw:
        headline = (entry.get("headline") or "").strip()
        if not headline:
            continue
        ts = entry.get("datetime")
        items.append({
            "date": date.fromtimestamp(ts).isoformat() if ts else "",
            "headline": headline,
            "url": entry.get("url", ""),
            "source": entry.get("source", ""),
        })
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:limit]


def earnings_calendar(*, days_ahead: int = 120) -> dict[str, str]:
    """``{sembol: sonraki_kazanc_tarihi}`` — tum piyasa icin TEK istek."""
    raw = _get(config.FINNHUB["earnings_url"], {
        "from": date.today().isoformat(),
        "to": (date.today() + timedelta(days=days_ahead)).isoformat(),
    })
    if not isinstance(raw, dict):
        return {}

    out: dict[str, str] = {}
    for entry in raw.get("earningsCalendar", []) or []:
        sym, when = entry.get("symbol"), entry.get("date")
        if sym and when and (sym not in out or when < out[sym]):
            out[sym] = when
    return out


def cached_earnings_calendar(*, max_age_hours: int = 20) -> dict[str, str]:
    """Kazanc takvimini gunde bir cek; her sembol icin ayri istek yapma."""
    path = CACHE_DIR / "earnings_calendar.json"
    if path.exists():
        from datetime import datetime
        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        if age < timedelta(hours=max_age_hours):
            return read_json(path, {}).get("calendar", {})

    cal = earnings_calendar()
    if cal:
        write_json(path, {"calendar": cal})
    return cal
