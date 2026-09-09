"""Analist konsensusu ve hedef fiyat — yfinance.

SARTNAME NOTU: bu bir BILGI alanidir, KARAR alani degil. Hedef fiyatlar
sistematik olarak iyimserdir ve puanlamaya girmez; kartta yalnizca "piyasa
ne bekliyor" baglami olarak gosterilir.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .. import config
from ..util import num, read_json, write_json

CACHE_DIR = config.CACHE_DIR / "analyst"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

EMPTY = {
    "buy": None, "hold": None, "sell": None,
    "target_low": None, "target_median": None, "target_high": None,
    "upside_to_median": None, "analyst_count": None, "source": None,
}


def consensus(ticker: str, price: float | None = None, *,
              max_age_hours: int = 72) -> dict:
    path = CACHE_DIR / f"{ticker.upper()}.json"
    if path.exists():
        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        if age < timedelta(hours=max_age_hours):
            cached = read_json(path, {})
            if cached:
                return _with_upside(cached, price)

    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info or {}
    except Exception as exc:  # noqa: BLE001
        print(f"  [uyari] analist {ticker}: {exc}")
        return dict(EMPTY)

    out = {
        # al/tut/sat dagilimi asagida ayri tablodan gelir; burada bos birakilir
        "buy": None, "hold": None, "sell": None,
        "target_low": num(info.get("targetLowPrice")),
        "target_median": num(info.get("targetMedianPrice")) or num(info.get("targetMeanPrice")),
        "target_high": num(info.get("targetHighPrice")),
        "analyst_count": _int(info.get("numberOfAnalystOpinions")),
        "recommendation": info.get("recommendationKey"),
        "source": "yfinance",
    }

    # yfinance al/tut/sat dagilimini ayri tabloda verir
    try:
        import yfinance as yf
        rec = yf.Ticker(ticker).recommendations_summary
        if rec is not None and not rec.empty:
            row = rec.iloc[0]
            out["buy"] = _int(row.get("strongBuy", 0)) + _int(row.get("buy", 0))
            out["hold"] = _int(row.get("hold", 0))
            out["sell"] = _int(row.get("sell", 0)) + _int(row.get("strongSell", 0))
    except Exception:  # noqa: BLE001
        pass

    write_json(path, out)
    return _with_upside(out, price)


def _with_upside(data: dict, price: float | None) -> dict:
    out = {**EMPTY, **data}
    p, target = num(price), num(out.get("target_median"))
    out["upside_to_median"] = ((target / p - 1) * 100) if (p and target and p > 0) else None
    return out


def _int(x) -> int:
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0
