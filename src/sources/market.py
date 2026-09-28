"""KURESEL PIYASA GORUNUMU — endeksler, faiz, emtia, kur.

Kaynak yfinance; ANAHTAR GEREKTIRMEZ ve ucretsizdir. Stooq endeks
sembollerini guvenilir tasimadigi icin (ve bazi aglardan dogrulama duvari
cikardigi icin) burada dogrudan yfinance kullanilir.

TASARIM: bu dosya YALNIZCA anlik goruntu uretir — 30 gunluk seri ve son
kapanis. Karar mantigi yok; pano ne gosterecegine kendi karar verir.
Bir sembol cekilemezse o satir DUSER, kosu devam eder: tek bir endeks
yuzunden butun serit bos kalmamali.
"""

from __future__ import annotations

from .. import config
from ..util import num

# (sembol, gosterilecek ad, grup, birim)
# Gruplar panoda serit basliklarini olusturur.
INSTRUMENTS = [
    ("^GSPC",     "S&P 500",        "Hisse",  "puan"),
    ("^IXIC",     "Nasdaq",         "Hisse",  "puan"),
    ("^RUT",      "Russell 2000",   "Hisse",  "puan"),
    ("^STOXX50E", "Euro Stoxx 50",  "Hisse",  "puan"),
    ("^N225",     "Nikkei 225",     "Hisse",  "puan"),
    ("XU100.IS",  "BIST 100",       "Hisse",  "puan"),
    ("^VIX",      "VIX (korku)",    "Risk",   "puan"),
    ("^TNX",      "ABD 10 yillik",  "Faiz",   "%"),
    ("DX-Y.NYB",  "Dolar endeksi",  "Kur",    "puan"),
    ("EURUSD=X",  "EUR/USD",        "Kur",    "kur"),
    ("TRY=X",     "USD/TRY",        "Kur",    "kur"),
    ("CL=F",      "Brent/WTI ham",  "Emtia",  "USD"),
    ("GC=F",      "Altin",          "Emtia",  "USD"),
    ("BTC-USD",   "Bitcoin",        "Kripto", "USD"),
]


def _history(symbol: str, days: int = 40):
    import yfinance as yf
    return yf.Ticker(symbol).history(period=f"{days}d", interval="1d",
                                     auto_adjust=False)


def snapshot(instruments=None) -> list[dict]:
    """Her enstruman icin son fiyat, gunluk/haftalik degisim ve mini seri."""
    rows: list[dict] = []
    for symbol, label, group, unit in (instruments or INSTRUMENTS):
        try:
            hist = _history(symbol)
        except Exception as exc:  # noqa: BLE001
            print(f"  [uyari] piyasa {symbol}: {str(exc)[:60]}")
            continue
        if hist is None or hist.empty:
            print(f"  [uyari] piyasa {symbol}: veri bos")
            continue

        closes = [num(v) for v in hist["Close"].tolist()]
        closes = [c for c in closes if c is not None]
        if not closes:
            continue

        last = closes[-1]
        prev = closes[-2] if len(closes) > 1 else None
        week = closes[-6] if len(closes) > 5 else None

        rows.append({
            "symbol": symbol,
            "label": label,
            "group": group,
            "unit": unit,
            "value": round(last, 4),
            "change_1d_pct": round((last / prev - 1) * 100, 2) if prev else None,
            "change_5d_pct": round((last / week - 1) * 100, 2) if week else None,
            # Serit grafigi icin son 30 kapanis
            "series": [round(c, 4) for c in closes[-30:]],
            "as_of": str(hist.index[-1].date()) if len(hist.index) else None,
        })
    return rows


def risk_note(rows: list[dict]) -> str | None:
    """VIX ve 10 yillik tahvilden tek cumlelik risk okumasi.

    Sayiyi gostermek yeterli degil: VIX 28 gordugunde bunun ne anlama
    geldigini bilmeyen biri icin 28 sadece bir sayidir.
    """
    by = {r["symbol"]: r for r in rows}
    vix = (by.get("^VIX") or {}).get("value")
    if vix is None:
        return None
    if vix >= config.MARKET_RISK["vix_high"]:
        return (f"VIX {vix:.0f} — piyasa gergin. Dususler daha sert olur; "
                f"pozisyon acmak icin acele etme.")
    if vix <= config.MARKET_RISK["vix_low"]:
        return (f"VIX {vix:.0f} — piyasa sakin, hatta rehavette. Ucuzluk "
                f"aramak zorlasir; iyi fiyat genelde korkuyla gelir.")
    return f"VIX {vix:.0f} — normal aralikta."
