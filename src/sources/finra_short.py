"""FINRA iki haftalik kisa pozisyon dosyalari.

FINRA konsolide kisa pozisyonlari ayda iki kez duz metin olarak yayinlar.
Yuksek kisa pozisyon tek basina olumsuz degildir — deger hissesinde tez
riskini, buyume hissesinde sikisma potansiyelini gosterir. Kartta baglam
olarak durur, puanlamaya girmez.
"""

from __future__ import annotations

from datetime import date, timedelta

from ..util import http_get, num, read_json, write_json
from .. import config

CACHE = config.CACHE_DIR / "finra_short.json"
URL = "https://cdn.finra.org/equity/otcmarket/biweekly/shrt{date}.txt"


def _settlement_dates(back: int = 3) -> list[str]:
    """FINRA ayin 15'i ve son gunu civarinda yayinlar; son birkacini dene."""
    out, d = [], date.today()
    for _ in range(back * 2):
        if d.day > 15:
            candidate = d.replace(day=15)
        else:
            first = d.replace(day=1)
            candidate = first - timedelta(days=1)
        out.append(candidate.strftime("%Y%m%d"))
        d = candidate - timedelta(days=1)
    return out[:back * 2]


def load(*, max_age_days: int = 7) -> dict[str, dict]:
    """``{sembol: {short_interest, avg_daily_volume, days_to_cover, date}}``"""
    cached = read_json(CACHE, {})
    if cached.get("fetched_at"):
        try:
            age = date.today() - date.fromisoformat(cached["fetched_at"])
            if age.days <= max_age_days and cached.get("data"):
                return cached["data"]
        except ValueError:
            pass

    for stamp in _settlement_dates():
        try:
            resp = http_get(URL.format(date=stamp), timeout=60, max_retries=2)
        except Exception:  # noqa: BLE001
            continue
        data = _parse(resp.text)
        if data:
            write_json(CACHE, {"fetched_at": date.today().isoformat(),
                               "settlement": stamp, "data": data})
            return data

    print("  [uyari] FINRA kisa pozisyon dosyasi alinamadi")
    return cached.get("data", {})


def _parse(text: str) -> dict[str, dict]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return {}
    header = [h.strip() for h in lines[0].split("|")]
    try:
        i_sym = header.index("symbolCode")
        i_short = header.index("currentShortPositionQuantity")
        i_vol = header.index("averageDailyVolumeQuantity")
        i_date = header.index("settlementDate")
    except ValueError:
        return {}

    out: dict[str, dict] = {}
    for line in lines[1:]:
        parts = line.split("|")
        if len(parts) <= max(i_sym, i_short, i_vol, i_date):
            continue
        sym = parts[i_sym].strip().upper()
        short = num(parts[i_short])
        vol = num(parts[i_vol])
        if not sym or short is None:
            continue
        out[sym] = {
            "short_interest": short,
            "avg_daily_volume": vol,
            "days_to_cover": (short / vol) if (vol and vol > 0) else None,
            "date": parts[i_date].strip(),
        }
    return out


def for_ticker(ticker: str, table: dict[str, dict] | None = None) -> dict:
    table = table if table is not None else load()
    return table.get(ticker.upper(), {"short_interest": None,
                                      "avg_daily_volume": None,
                                      "days_to_cover": None, "date": None})
