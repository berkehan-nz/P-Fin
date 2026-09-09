"""Fiyat, hacim, 52 hafta araligi — Stooq (birincil) + yfinance (yedek).

Stooq gunluk CSV'yi anahtarsiz ve limitsiz verir. Ancak bazi sembolleri
(yeni halka arzlar, sinif hisseleri) tasimaz; o durumda yfinance devreye
girer. Ikisi de basarisiz olursa None doner ve kart fiyatsiz uretilir —
temel metrikler yine hesaplanir.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta

from .. import config
from ..util import http_get, num, read_json, write_json

CACHE_DIR = config.CACHE_DIR / "prices"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(ticker: str):
    return CACHE_DIR / f"{ticker.upper()}.json"


def _fresh(path, max_age_hours: int) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age < timedelta(hours=max_age_hours)


# --------------------------------------------------------------------------
# Stooq
# --------------------------------------------------------------------------
def from_stooq(ticker: str) -> list[dict] | None:
    """Gunluk OHLCV. Stooq bilinmeyen sembolde bos/hatali CSV doner."""
    url = config.STOOQ_URL.format(symbol=ticker.lower())
    resp = http_get(url, timeout=30)
    text = resp.text.strip()
    if not text or text.lower().startswith("<") or "No data" in text:
        return None

    rows = []
    for row in csv.DictReader(io.StringIO(text)):
        close = num(row.get("Close"))
        if close is None or close <= 0:
            continue
        rows.append({
            "date": row.get("Date", ""),
            "close": close,
            "high": num(row.get("High")),
            "low": num(row.get("Low")),
            "volume": num(row.get("Volume")) or 0.0,
        })
    if len(rows) < 20:
        return None
    rows.sort(key=lambda r: r["date"])
    return rows[-config.PRICE_HISTORY_DAYS:]


# --------------------------------------------------------------------------
# yfinance yedek
# --------------------------------------------------------------------------
def from_yfinance(ticker: str) -> list[dict] | None:
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        hist = yf.Ticker(ticker).history(period="3y", interval="1d", auto_adjust=False)
    except Exception as exc:  # noqa: BLE001
        print(f"  [uyari] yfinance {ticker}: {exc}")
        return None
    if hist is None or hist.empty:
        return None

    rows = []
    for idx, r in hist.iterrows():
        close = num(r.get("Close"))
        if close is None or close <= 0:
            continue
        rows.append({
            "date": idx.date().isoformat(),
            "close": close,
            "high": num(r.get("High")),
            "low": num(r.get("Low")),
            "volume": num(r.get("Volume")) or 0.0,
        })
    return rows[-config.PRICE_HISTORY_DAYS:] if len(rows) >= 20 else None


# --------------------------------------------------------------------------
# Genel arayuz
# --------------------------------------------------------------------------
def history(ticker: str, *, max_age_hours: int = 12,
            allow_cache: bool = True) -> list[dict] | None:
    """Gunluk fiyat gecmisi; once onbellek, sonra Stooq, sonra yfinance."""
    path = _cache_path(ticker)
    if allow_cache and _fresh(path, max_age_hours):
        cached = read_json(path, {})
        if cached.get("rows"):
            return cached["rows"]

    rows = None
    source = None
    try:
        rows = from_stooq(ticker)
        source = "stooq" if rows else None
    except Exception as exc:  # noqa: BLE001
        print(f"  [uyari] stooq {ticker}: {exc}")

    if not rows:
        rows = from_yfinance(ticker)
        source = "yfinance" if rows else None

    if not rows:
        cached = read_json(path, {})
        return cached.get("rows")  # bayat veri hic yoktan iyidir

    write_json(path, {"ticker": ticker.upper(), "source": source, "rows": rows})
    return rows


def quote(ticker: str, **kw) -> dict:
    """Fiyat ozeti: son fiyat, gunluk degisim, 52 hafta, ortalama dolar hacmi."""
    rows = history(ticker, **kw)
    if not rows:
        return {
            "ticker": ticker.upper(), "price": None, "change_1d_pct": None,
            "high_52w": None, "low_52w": None, "avg_dollar_volume_30d": None,
            "history": [], "as_of": None, "source": None,
        }

    last = rows[-1]
    prev = rows[-2] if len(rows) >= 2 else None
    window_52w = rows[-config.METRIC_PARAMS["window_52w_days"]:]
    window_vol = rows[-config.AVG_VOLUME_WINDOW_DAYS:]

    dollar_volumes = [r["close"] * (r["volume"] or 0) for r in window_vol]
    avg_dollar_volume = sum(dollar_volumes) / len(dollar_volumes) if dollar_volumes else None

    highs = [r["high"] or r["close"] for r in window_52w]
    lows = [r["low"] or r["close"] for r in window_52w]

    cached = read_json(_cache_path(ticker), {})
    return {
        "ticker": ticker.upper(),
        "price": last["close"],
        "change_1d_pct": ((last["close"] / prev["close"] - 1) * 100) if prev else None,
        "high_52w": max(highs) if highs else None,
        "low_52w": min(lows) if lows else None,
        "avg_dollar_volume_30d": avg_dollar_volume,
        "history": [(r["date"], r["close"]) for r in rows],
        "as_of": last["date"],
        "source": cached.get("source"),
    }


def attach(f, quote_data: dict | None = None) -> None:
    """Fiyat verisini bir ``Fundamentals`` nesnesine yazar."""
    q = quote_data or quote(f.ticker)
    f.price = q["price"]
    f.price_history = q["history"]
    f.high_52w = q["high_52w"]
    f.low_52w = q["low_52w"]
    f.avg_dollar_volume_30d = q["avg_dollar_volume_30d"]
    f.sources["price"] = q.get("source")


def benchmark_history(symbol: str = "QQQ") -> list[tuple[str, float]]:
    """Karsilastirma endeksi (QQQ = Nasdaq 100, SPY = S&P 500)."""
    rows = history(symbol)
    return [(r["date"], r["close"]) for r in rows] if rows else []


def sparkline(history_rows: list[tuple[str, float]], points: int = 60,
              days: int = 126) -> list[float]:
    """Kart uzerindeki 6 aylik mini grafik icin ornekleme."""
    window = history_rows[-days:]
    if not window:
        return []
    if len(window) <= points:
        return [round(v, 4) for _, v in window]
    step = len(window) / points
    return [round(window[int(i * step)][1], 4) for i in range(points)]
