"""Ortak yardimcilar: guvenli matematik, JSON G/C, HTTP (geri cekilmeli), hiz siniri.

Tasarim kurali: veri yoksa ``None`` don, ISTISNA FIRLATMA. Tum hesap zinciri
``None`` tasiyabilmeli ki tek bir eksik XBRL etiketi tum karti dusurmesin.
"""

from __future__ import annotations

import json
import math
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import requests

from . import config


# --------------------------------------------------------------------------
# Zaman
# --------------------------------------------------------------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


# --------------------------------------------------------------------------
# Guvenli matematik — hepsi None tasiyabilir
# --------------------------------------------------------------------------
def num(x: Any) -> float | None:
    """Sayiya cevir; olmuyorsa None. NaN/Inf de None sayilir."""
    if x is None:
        return None
    if isinstance(x, bool):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def div(a: Any, b: Any) -> float | None:
    """a/b; paydayi sifir veya None ise None."""
    a, b = num(a), num(b)
    if a is None or b is None or b == 0:
        return None
    return a / b


def sub(a: Any, b: Any) -> float | None:
    a, b = num(a), num(b)
    if a is None or b is None:
        return None
    return a - b


def add(*xs: Any) -> float | None:
    """Toplam. Hepsi None ise None; bazilari None ise onlari 0 sayar."""
    vals = [num(x) for x in xs]
    present = [v for v in vals if v is not None]
    if not present:
        return None
    return sum(present)


def pct(a: Any, b: Any) -> float | None:
    """100 * a/b."""
    r = div(a, b)
    return None if r is None else r * 100.0


def growth_pct(new: Any, old: Any) -> float | None:
    """Yuzde buyume. Taban <= 0 ise anlamsiz -> None."""
    new, old = num(new), num(old)
    if new is None or old is None or old <= 0:
        return None
    return (new / old - 1.0) * 100.0


def cagr_pct(end: Any, start: Any, years: float) -> float | None:
    """Bilesik yillik buyume orani (%)."""
    end, start = num(end), num(start)
    if end is None or start is None or start <= 0 or years <= 0:
        return None
    if end <= 0:
        return None
    return ((end / start) ** (1.0 / years) - 1.0) * 100.0


def safe_min(xs: Iterable[Any]) -> float | None:
    vals = [v for v in (num(x) for x in xs) if v is not None]
    return min(vals) if vals else None


def safe_max(xs: Iterable[Any]) -> float | None:
    vals = [v for v in (num(x) for x in xs) if v is not None]
    return max(vals) if vals else None


def percentile_rank(value: Any, population: Sequence[Any]) -> float | None:
    """``value`` degerinin ``population`` icindeki yuzdelik sirasi (0-100).

    0 = en dusuk, 100 = en yuksek. Populasyondaki None'lar atilir.
    Kucuk populasyonlarda (< 3) anlamsiz oldugu icin None doner.
    """
    v = num(value)
    if v is None:
        return None
    pop = [p for p in (num(x) for x in population) if p is not None]
    if len(pop) < 3:
        return None
    below = sum(1 for p in pop if p < v)
    equal = sum(1 for p in pop if p == v)
    # ortalama sira yontemi — esitlikleri adil dagitir
    return 100.0 * (below + 0.5 * equal) / len(pop)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def round_or_none(x: Any, digits: int = 4) -> float | None:
    v = num(x)
    return None if v is None else round(v, digits)


# --------------------------------------------------------------------------
# JSON G/C — her kayitta as_of ve source
# --------------------------------------------------------------------------
def read_json(path: Path | str, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        with p.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path: Path | str, payload: Any, *, source: str | None = None,
               as_of: str | None = None) -> bool:
    """JSON yaz. Icerik degismediyse dosyaya DOKUNMA (bos commit onlemek icin).

    ``as_of``/``source`` alanlarini sozluk kokunde otomatik ekler. Degisiklik
    tespiti bu iki alan haric yapilir; yoksa her kosuda dosya degisir.

    Returns:
        Dosya gercekten degistiyse True.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(payload, dict):
        payload = dict(payload)
        payload.setdefault("as_of", as_of or today_iso())
        if source is not None:
            payload.setdefault("source", source)

    def _strip_stamps(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _strip_stamps(v) for k, v in obj.items()
                    if k not in ("as_of", "generated_at", "updated_at")}
        if isinstance(obj, list):
            return [_strip_stamps(v) for v in obj]
        return obj

    new_text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str)

    if p.exists():
        old = read_json(p)
        if old is not None and _strip_stamps(old) == _strip_stamps(payload):
            return False

    p.write_text(new_text + "\n", encoding="utf-8")
    return True


# --------------------------------------------------------------------------
# Hiz siniri
# --------------------------------------------------------------------------
class RateLimiter:
    """Basit token-bucket. Is parcaciklari arasinda paylasilabilir."""

    def __init__(self, calls_per_sec: float):
        self.min_interval = 1.0 / calls_per_sec if calls_per_sec > 0 else 0.0
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delta = now - self._last
            if delta < self.min_interval:
                time.sleep(self.min_interval - delta)
            self._last = time.monotonic()


SEC_LIMITER = RateLimiter(config.SEC_RATE_LIMIT_PER_SEC)
FINNHUB_LIMITER = RateLimiter(config.FINNHUB_RATE_LIMIT_PER_MIN / 60.0)


# --------------------------------------------------------------------------
# HTTP — ustel geri cekilme
# --------------------------------------------------------------------------
class FetchError(RuntimeError):
    """Tum denemeler tukendikten sonra firlatilir. Cagiran yakalayip None yazar."""


def http_get(url: str, *, headers: dict | None = None, params: dict | None = None,
             limiter: RateLimiter | None = None, timeout: int | None = None,
             stream: bool = False, max_retries: int | None = None) -> requests.Response:
    """GET + ustel geri cekilme (2, 4, 8, 16, 32 sn).

    429 ve 5xx yeniden denenir. 403/404 gibi kalici hatalar hemen firlatilir —
    tekrar denemek SEC tarafinda IP engeline yol acar.
    """
    retries = max_retries if max_retries is not None else config.HTTP_MAX_RETRIES
    timeout = timeout or config.HTTP_TIMEOUT_SEC
    last_exc: Exception | None = None

    for attempt in range(retries):
        if limiter is not None:
            limiter.wait()
        try:
            resp = requests.get(url, headers=headers, params=params,
                                timeout=timeout, stream=stream)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 500, 502, 503, 504):
                last_exc = FetchError(f"{resp.status_code} {url}")
            elif resp.status_code == 403:
                raise FetchError(
                    f"403 {url} — SEC User-Agent eksik veya gecersiz olabilir. "
                    f"SEC_USER_AGENT='ad e-posta' bicimindedir."
                )
            else:
                raise FetchError(f"{resp.status_code} {url}")
        except requests.RequestException as exc:
            last_exc = exc

        if attempt < retries - 1:
            time.sleep(config.HTTP_BACKOFF_BASE_SEC * (2 ** attempt))

    raise FetchError(f"{url} basarisiz ({retries} deneme): {last_exc}")


def sec_get(url: str, **kw) -> requests.Response:
    hdrs = {"User-Agent": config.SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    hdrs.update(kw.pop("headers", None) or {})
    return http_get(url, headers=hdrs, limiter=SEC_LIMITER, **kw)


def try_fetch(fn: Callable, *args, label: str = "", **kwargs):
    """Bir kaynak cagrisini calistir; hata olursa None don ve devam et.

    Veri hattinin tamami tek bir kaynagin cokmesiyle durmamali.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 — kasitli genis yakalama
        print(f"  [uyari] {label or getattr(fn, '__name__', 'kaynak')}: {exc}")
        return None
