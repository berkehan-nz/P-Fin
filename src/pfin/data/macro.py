"""Makro / kıyas verisi (§2.6): XU100 endeksi + TÜFE.

XU100: borsapy Index. TÜFE: borsapy Inflation (TÜİK) — bazı yollar ücretsiz EVDS
anahtarı ister. Anahtar yoksa TÜFE None döner ama sistem çökmemeli (kıyas eksik kalır).
"""
from __future__ import annotations

from .models import Quote


def _num(x) -> float | None:
    try:
        if x is None:
            return None
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def get_index_quote(symbol: str = "XU100") -> Quote:
    """XU100 (veya verilen endeks) son değeri + günlük değişim."""
    try:
        import borsapy as bp

        idx = bp.Index(symbol)
        price = prev = None
        try:
            fi = idx.fast_info
            price = _num(getattr(fi, "last_price", None) or (fi["last_price"] if _has(fi, "last_price") else None))
            prev = _num(getattr(fi, "previous_close", None) or (fi["previous_close"] if _has(fi, "previous_close") else None))
        except Exception:
            pass
        if price is None:
            hist = idx.history(period="1mo")
            if hist is not None and len(hist):
                closes = hist["Close"].dropna() if "Close" in hist else hist.iloc[:, -1].dropna()
                if len(closes):
                    price = _num(closes.iloc[-1])
                    if len(closes) >= 2:
                        prev = _num(closes.iloc[-2])
        change = None
        if price is not None and prev not in (None, 0):
            change = round((price - prev) / prev * 100, 2)
        return Quote(symbol=symbol, market="INDEX", price=price, currency="TRY",
                     previous_close=prev, change_pct=change, source="borsapy")
    except Exception as exc:
        return Quote(symbol=symbol, market="INDEX", price=None, source="borsapy",
                     error=repr(exc)[:200])


def get_tufe_yoy(evds_key: str | None = None) -> tuple[float | None, str]:
    """TÜFE yıllık (%) döner. (value, note). Anahtar yoksa mümkünse anahtarsız dener."""
    try:
        import borsapy as bp

        if evds_key:
            try:
                bp.set_evds_key(evds_key)
            except Exception:
                pass
        inf = bp.Inflation()
        # borsapy Inflation: latest() / tufe() — sürüme göre değişebilir, savunmacı dene
        for meth in ("latest", "tufe"):
            fn = getattr(inf, meth, None)
            if fn is None:
                continue
            try:
                res = fn()
            except Exception:
                continue
            val = _extract_yoy(res)
            if val is not None:
                return val, f"TÜFE yıllık (borsapy.Inflation.{meth})"
        return None, "TÜFE alınamadı (EVDS anahtarı gerekebilir)"
    except Exception as exc:
        return None, f"TÜFE hatası: {repr(exc)[:160]}"


def _extract_yoy(res) -> float | None:
    """Inflation sonucundan yıllık % değerini savunmacı biçimde çıkar."""
    if res is None:
        return None
    if isinstance(res, (int, float)):
        return _num(res)
    if isinstance(res, dict):
        for k in ("yoy", "annual", "yillik", "yearly", "value", "tufe"):
            if k in res:
                return _num(res[k])
    for attr in ("yoy", "annual", "yillik", "value"):
        v = getattr(res, attr, None)
        if v is not None:
            return _num(v)
    # pandas Series/DataFrame: son değeri al
    try:
        return _num(res.iloc[-1])
    except Exception:
        return None


def _has(fi, key) -> bool:
    try:
        _ = fi[key]
        return True
    except Exception:
        return False
