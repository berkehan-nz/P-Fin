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
from ..util import (FetchError, SourceBreaker, TimeoutHit, http_get, num,
                    read_json, time_limit, write_json)

CACHE_DIR = config.CACHE_DIR / "prices"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Fiyat kaynaklari istege baglidir; cokerlerse tum partiyi bekletmesinler.
STOOQ_BREAKER = SourceBreaker("Stooq")
YF_BREAKER = SourceBreaker("yfinance")


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
def from_stooq(ticker: str, *, fx: bool = False) -> list[dict] | None:
    """Gunluk OHLCV. Stooq bilinmeyen sembolde bos/hatali CSV doner.

    ``fx=True`` doviz sembolleri icindir: onlar ".us" soneki almaz.
    """
    tmpl = config.STOOQ_FX_URL if fx else config.STOOQ_URL
    url = tmpl.format(symbol=ticker.lower())
    # SEC'in sabirli politikasi DEGIL: fiyat gelmezse kart yine uretilir,
    # ama 120 sirketlik parti tek kaynagin coktugu icin saatlerce surmemeli.
    resp = http_get(url, timeout=config.PRICE_TIMEOUT_SEC,
                    max_retries=config.PRICE_MAX_RETRIES)
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
    """Stooq'un tasimadigi semboller icin yedek.

    ZAMAN SINIRI SART: yfinance borsadan cikmis sembollerde yanit vermeden
    asilabiliyor ve kendi zaman asimi her yolda islemiyor. 22 Eylul 2026'da
    tarama tam burada, "L" harfinde donup kaldi; her saat ayni sirkette
    50 dakikalik is akisi sinirina carpti ve HICBIR ILERLEME KAYDEDILMEDI.
    """
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        with time_limit(config.YF_TIMEOUT_SEC, f"yfinance {ticker}"):
            try:
                hist = yf.Ticker(ticker).history(
                    period="3y", interval="1d", auto_adjust=False,
                    timeout=config.YF_TIMEOUT_SEC)
            except TypeError:  # eski surumlerde timeout parametresi yok
                hist = yf.Ticker(ticker).history(
                    period="3y", interval="1d", auto_adjust=False)
    except TimeoutHit as exc:
        # Zaman asimi KAYNAK sorunudur; "sembol yok" degil.
        YF_BREAKER.miss()
        print(f"  [uyari] yfinance {ticker}: {exc}", flush=True)
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"  [uyari] yfinance {ticker}: {str(exc)[:120]}")
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
    if STOOQ_BREAKER.ok():
        try:
            rows = from_stooq(ticker)
            STOOQ_BREAKER.hit()       # yanit verdi (bos olsa da sorun kaynakta degil)
            source = "stooq" if rows else None
        except FetchError as exc:
            STOOQ_BREAKER.miss(str(exc)[:80])
        except Exception as exc:  # noqa: BLE001
            STOOQ_BREAKER.miss()
            print(f"  [uyari] stooq {ticker}: {str(exc)[:120]}")

    if not rows and YF_BREAKER.ok():
        before = YF_BREAKER.consecutive
        rows = from_yfinance(ticker)
        source = "yfinance" if rows else None
        if YF_BREAKER.consecutive == before:
            YF_BREAKER.hit()

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


def implied_shares(ticker: str) -> float | None:
    """Tum hisse siniflarini kapsayan tedavuldeki hisse sayisi (milyon).

    yfinance ``impliedSharesOutstanding`` TUM SINIFLARI toplar;
    ``sharesOutstanding`` yalnizca islem goren sinifi verir (GOOGL: 5,9 mlr
    yerine 12,2 mlr). EDGAR cok sinifli sirketlerde guncel toplami
    tasimadiginda ikinci kaynak olarak kullanilir.
    """
    try:
        import yfinance as yf
        with time_limit(config.YF_TIMEOUT_SEC, f"yfinance bilgi {ticker}"):
            info = yf.Ticker(ticker).info or {}
    except TimeoutHit as exc:
        print(f"  [uyari] yfinance hisse {ticker}: {exc}", flush=True)
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"  [uyari] yfinance hisse {ticker}: {str(exc)[:60]}")
        return None
    val = num(info.get("impliedSharesOutstanding")) or num(info.get("sharesOutstanding"))
    return val / 1e6 if val and val > 0 else None


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
    # SON NOKTA MUTLAKA ALINMALI. Onceki surum int(i * len/points) kullaniyordu;
    # en buyuk indeks len-1'e hic ulasmiyor, grafik birkac gun geride bitiyordu.
    # Kartta guncel fiyat yaninda duran grafik ondan %5-8 sapabiliyordu.
    step = (len(window) - 1) / (points - 1)
    return [round(window[round(i * step)][1], 4) for i in range(points)]


# --------------------------------------------------------------------------
# Doviz — USD/TRY
# --------------------------------------------------------------------------
# TL vadeli mevduatin dolar karsiligi ve BASA BAS KUR bunsuz hesaplanamaz.
# Mevduat TL kazandirir; sorulmasi gereken "faiz ne kadar" degil, "kur ne
# kadar artarsa bu faiz erir" sorusudur. Stooq 'usdtry' sembolunu tasir;
# yfinance yedegi 'TRY=X'.
FX_SYMBOLS = {"USDTRY": ("usdtry", "TRY=X")}


def fx_rate(pair: str = "USDTRY", *, max_age_hours: int = 12) -> dict:
    """Guncel kur + 1 hafta once. Bulunamazsa deger None doner, hata atmaz."""
    stooq_sym, yf_sym = FX_SYMBOLS.get(pair.upper(), (pair.lower(), pair))
    rows = None
    if STOOQ_BREAKER.ok():
        try:
            rows = from_stooq(stooq_sym, fx=True)
            STOOQ_BREAKER.hit()
        except FetchError as exc:
            STOOQ_BREAKER.miss(str(exc)[:80])
        except Exception as exc:  # noqa: BLE001
            STOOQ_BREAKER.miss()
            print(f"  [uyari] stooq {stooq_sym}: {str(exc)[:100]}")
    if not rows and YF_BREAKER.ok():
        rows = from_yfinance(yf_sym)

    if not rows:
        return {"pair": pair.upper(), "rate": None, "as_of": None,
                "change_1w_pct": None, "source": None}

    last = rows[-1]
    week = rows[-6] if len(rows) >= 6 else rows[0]
    change = ((last["close"] / week["close"] - 1) * 100
              if week["close"] else None)
    return {
        "pair": pair.upper(),
        "rate": last["close"],
        "as_of": last["date"],
        "change_1w_pct": round(change, 2) if change is not None else None,
        "source": "stooq/yfinance",
    }
