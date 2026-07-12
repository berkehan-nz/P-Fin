"""Fiyat + temel veri katmanı.

- BIST fiyat/bilanço + TEFAS fon: borsapy (anahtarsız çoğu yol)
- ABD fiyat: Twelve Data ücretsiz Basic (çağrı sayaçlı)
- ABD temel/bilanço: yfinance (anahtarsız Yahoo) — TD ücretsiz katmanda temel veri kısıtlı

Her fonksiyon Quote / FinancialSnapshot döner; hata olursa .error dolu, .price None.
Sistem tek bir sembol için veri gelmese de çökmeden devam eder.
"""
from __future__ import annotations

from typing import Iterable

import requests

from .models import FinancialSnapshot, Quote
from .ratecounter import RateCounter, RateLimitExceeded

# yfinance/balance_sheet satır adları (yaklaşık eşleşme) → kısa anahtar
_FIN_ROWS = {
    "total_revenue": ["Total Revenue", "TotalRevenue", "Revenue"],
    "net_income": ["Net Income", "NetIncome", "Net Income Common Stockholders"],
    "gross_profit": ["Gross Profit", "GrossProfit"],
    "operating_income": ["Operating Income", "OperatingIncome"],
    "total_assets": ["Total Assets", "TotalAssets"],
    "total_debt": ["Total Debt", "TotalDebt", "Total Liabilities Net Minority Interest"],
    "total_equity": ["Total Equity Gross Minority Interest", "Stockholders Equity",
                     "Common Stock Equity"],
    "cash": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
}


def _num(x) -> float | None:
    try:
        if x is None:
            return None
        val = float(x)
        return None if val != val else val  # NaN filtresi
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- BIST
def get_bist_quote(symbol: str) -> Quote:
    try:
        import borsapy as bp

        t = bp.Ticker(symbol)
        price = prev = currency = vol = None
        try:
            fi = t.fast_info
            price = _num(_fi_get(fi, "last_price", "lastPrice", "last"))
            prev = _num(_fi_get(fi, "previous_close", "previousClose", "regular_market_previous_close"))
            currency = _fi_get(fi, "currency") or "TRY"
            vol = _num(_fi_get(fi, "last_volume", "volume", "regular_market_volume"))
        except Exception:
            currency = "TRY"

        avg_vol = None
        if price is None or prev is None or vol is None:
            hist = t.history(period="1mo")
            if hist is not None and len(hist):
                closes = hist["Close"].dropna()
                if len(closes):
                    price = price if price is not None else _num(closes.iloc[-1])
                    if prev is None and len(closes) >= 2:
                        prev = _num(closes.iloc[-2])
                if "Volume" in hist:
                    vols = hist["Volume"].dropna()
                    if len(vols):
                        vol = vol if vol is not None else _num(vols.iloc[-1])
                        avg_vol = _num(vols.mean())

        change = _pct(price, prev)
        return Quote(symbol=symbol, market="BIST", price=price, currency=currency or "TRY",
                     previous_close=prev, change_pct=change, volume=vol, avg_volume=avg_vol,
                     source="borsapy")
    except Exception as exc:  # pragma: no cover - ağ/kaynak hatası
        return Quote(symbol=symbol, market="BIST", price=None, source="borsapy",
                     error=repr(exc)[:200])


def get_bist_financials(symbol: str) -> FinancialSnapshot:
    try:
        import borsapy as bp

        t = bp.Ticker(symbol)
        return _extract_financials(symbol, "BIST", t.balance_sheet, t.income_stmt, "borsapy")
    except Exception as exc:
        return FinancialSnapshot(symbol=symbol, market="BIST", source="borsapy",
                                 error=repr(exc)[:200])


# --------------------------------------------------------------------------- TEFAS
def get_tefas_fund(code: str) -> Quote:
    try:
        import borsapy as bp

        f = bp.Fund(code)
        info = getattr(f, "info", None) or {}
        price = _num(_dget(info, "price", "fiyat", "last_price", "nav"))
        prev = _num(_dget(info, "previous_price", "onceki_fiyat", "previous_close"))
        if price is None:
            hist = f.history(period="1mo")
            if hist is not None and len(hist):
                col = "Close" if "Close" in hist else hist.columns[-1]
                closes = hist[col].dropna()
                if len(closes):
                    price = _num(closes.iloc[-1])
                    if len(closes) >= 2:
                        prev = _num(closes.iloc[-2])
        return Quote(symbol=code, market="TEFAS", price=price, currency="TRY",
                     previous_close=prev, change_pct=_pct(price, prev), source="borsapy")
    except Exception as exc:
        return Quote(symbol=code, market="TEFAS", price=None, source="borsapy",
                     error=repr(exc)[:200])


# --------------------------------------------------------------------------- ABD
def get_us_quote(symbol: str, td_key: str | None, counter: RateCounter | None = None) -> Quote:
    """ABD fiyatı: Twelve Data ücretsiz Basic. Anahtar yoksa/limit doluysa .error."""
    if not td_key:
        return Quote(symbol=symbol, market="US", price=None, source="twelvedata",
                     error="TWELVEDATA_API_KEY yok")
    if counter is not None and not counter.can_call():
        return Quote(symbol=symbol, market="US", price=None, source="twelvedata",
                     error="Twelve Data çağrı limiti (sayaç)")
    try:
        if counter is not None:
            counter.record()
        resp = requests.get(
            "https://api.twelvedata.com/quote",
            params={"symbol": symbol, "apikey": td_key},
            timeout=20,
        )
        data = resp.json()
        if data.get("status") == "error" or "close" not in data:
            return Quote(symbol=symbol, market="US", price=None, source="twelvedata",
                         error=str(data.get("message", data))[:200])
        price = _num(data.get("close"))
        prev = _num(data.get("previous_close"))
        return Quote(symbol=symbol, market="US", price=price,
                     currency=data.get("currency", "USD"), previous_close=prev,
                     change_pct=_num(data.get("percent_change")) if data.get("percent_change") else _pct(price, prev),
                     volume=_num(data.get("volume")),
                     avg_volume=_num(data.get("average_volume")), source="twelvedata")
    except RateLimitExceeded as exc:
        return Quote(symbol=symbol, market="US", price=None, source="twelvedata",
                     error=str(exc))
    except Exception as exc:
        return Quote(symbol=symbol, market="US", price=None, source="twelvedata",
                     error=repr(exc)[:200])


def get_us_financials(symbol: str) -> FinancialSnapshot:
    """ABD temel/bilanço: yfinance (anahtarsız Yahoo)."""
    try:
        import yfinance as yf

        t = yf.Ticker(symbol)
        return _extract_financials(symbol, "US", t.balance_sheet, t.income_stmt, "yfinance")
    except Exception as exc:
        return FinancialSnapshot(symbol=symbol, market="US", source="yfinance",
                                 error=repr(exc)[:200])


# --------------------------------------------------------------------------- ortak
def _extract_financials(symbol, market, balance, income, source) -> FinancialSnapshot:
    items: dict[str, float] = {}
    period = ""
    for df in (income, balance):
        if df is None or not hasattr(df, "index") or df.empty:
            continue
        latest_col = df.columns[0]
        period = str(getattr(latest_col, "date", lambda: latest_col)()) if hasattr(latest_col, "date") else str(latest_col)
        for key, candidates in _FIN_ROWS.items():
            if key in items:
                continue
            for cand in candidates:
                if cand in df.index:
                    val = _num(df.loc[cand, latest_col])
                    if val is not None:
                        items[key] = val
                        break
    if not items:
        return FinancialSnapshot(symbol=symbol, market=market, source=source,
                                 error="finansal tablo boş / kalem bulunamadı")
    return FinancialSnapshot(symbol=symbol, market=market, items=items,
                             period=period[:10], source=source)


def _fi_get(fi, *names):
    for n in names:
        try:
            v = fi[n]
            if v is not None:
                return v
        except Exception:
            pass
        v = getattr(fi, n, None)
        if v is not None:
            return v
    return None


def _dget(d: dict, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) is not None:
            return d[k]
    return None


def _pct(price, prev) -> float | None:
    if price is None or prev in (None, 0):
        return None
    return round((price - prev) / prev * 100, 2)


def quote_for(symbol: str, market: str, td_key: str | None = None,
              counter: RateCounter | None = None) -> Quote:
    """Pazar tipine göre doğru kaynağa yönlendirir."""
    market = market.upper()
    if market == "BIST":
        return get_bist_quote(symbol)
    if market == "TEFAS":
        return get_tefas_fund(symbol)
    if market == "US":
        return get_us_quote(symbol, td_key, counter)
    return Quote(symbol=symbol, market=market, price=None, error=f"bilinmeyen pazar {market}")


def financials_for(symbol: str, market: str) -> FinancialSnapshot:
    market = market.upper()
    if market == "BIST":
        return get_bist_financials(symbol)
    if market == "US":
        return get_us_financials(symbol)
    return FinancialSnapshot(symbol=symbol, market=market, error=f"temel veri yok: {market}")
