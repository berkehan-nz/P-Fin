"""Portfoy takibi — Midas'ta acilan gercek ve kagit pozisyonlar.

Midas'in API'si yok; islemler ``data/portfolio.json`` icine elle girilir.
Dashboard'daki "Islem ekle" formu bu semaya uygun bir JSON parcasi uretir.

Hesaplananlar: maliyet (komisyon dahil), guncel deger, K/Z ($ ve %), portfoy
agirligi, hedefe potansiyel, elde tutma suresi, gozden gecirmeye kalan gun,
Nasdaq 100 ve S&P 500'e karsi GIRIS TARIHINDEN ITIBAREN goreli performans.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from .config import DATA_DIR, PORTFOLIO
from .util import num, pct, read_json, today_iso, write_json

PATH = DATA_DIR / "portfolio.json"

POSITION_SCHEMA = {
    "ticker": "",
    "type": "GERCEK",          # GERCEK | KAGIT
    "broker": PORTFOLIO["default_broker"],
    "entry_date": "",
    "entry_price": 0.0,
    "shares": 0.0,
    "fees_usd": 0.0,
    "target_price": 0.0,
    "review_date": "",
    "thesis_breakers": [],
    "notes": "",
    "status": "OPEN",          # OPEN | CLOSED
}


def load() -> dict:
    data = read_json(PATH)
    if not isinstance(data, dict):
        return {"positions": [], "closed": [], "cash_usd": 0.0,
                "as_of": today_iso(), "source": "manual"}
    data.setdefault("positions", [])
    data.setdefault("closed", [])
    data.setdefault("cash_usd", 0.0)
    return data


def ensure_file() -> bool:
    if PATH.exists():
        return False
    return write_json(PATH, {"positions": [], "closed": [], "cash_usd": 0.0,
                             "source": "manual"})


def tickers() -> list[str]:
    data = load()
    return sorted({(p.get("ticker") or "").upper()
                   for p in data["positions"] if p.get("status", "OPEN") == "OPEN"
                   and p.get("ticker")})


def json_snippet(ticker: str, entry_date: str, entry_price: float, shares: float,
                 fees_usd: float = 0.0, target_price: float = 0.0,
                 notes: str = "", position_type: str = "GERCEK") -> dict:
    """Dashboard "Islem ekle" formunun urettigi parca — az alanli, hizli."""
    return {
        **POSITION_SCHEMA,
        "ticker": ticker.upper(),
        "type": position_type,
        "entry_date": entry_date,
        "entry_price": float(entry_price),
        "shares": float(shares),
        "fees_usd": float(fees_usd),
        "target_price": float(target_price),
        "notes": notes,
    }


# --------------------------------------------------------------------------
# Hesap
# --------------------------------------------------------------------------
def _days_between(a: str, b: str | None = None) -> int | None:
    try:
        start = date.fromisoformat(a[:10])
    except (ValueError, TypeError):
        return None
    end = date.fromisoformat(b[:10]) if b else date.today()
    return (end - start).days


def _benchmark_return_since(history: list[tuple[str, float]],
                            entry_date: str) -> float | None:
    """Giris tarihinden bugune endeks getirisi (%)."""
    if not history or not entry_date:
        return None
    at_entry = [v for d, v in history if d <= entry_date[:10]]
    if not at_entry:
        return None
    start, end = at_entry[-1], history[-1][1]
    return ((end / start) - 1) * 100 if start > 0 else None


def compute(quotes: dict[str, dict],
            benchmarks: dict[str, list[tuple[str, float]]] | None = None,
            earnings: dict[str, str] | None = None,
            cards: dict[str, dict] | None = None) -> dict:
    """Portfoyun tam durumunu hesaplar.

    Args:
        quotes: ``{sembol: {"price":..,"change_1d_pct":..}}``
        benchmarks: ``{"QQQ": [(tarih, kapanis)], "SPY": [...]}``
        earnings: ``{sembol: sonraki_kazanc_tarihi}``
        cards: ``{sembol: kart}`` — sektor ve tez kiricilar icin
    """
    data = load()
    benchmarks = benchmarks or {}
    earnings = earnings or {}
    cards = cards or {}

    positions = []
    total_cost = 0.0
    total_value = 0.0

    for raw in data["positions"]:
        if raw.get("status", "OPEN") != "OPEN":
            continue
        ticker = (raw.get("ticker") or "").upper()
        shares = num(raw.get("shares")) or 0.0
        entry_price = num(raw.get("entry_price")) or 0.0
        fees = num(raw.get("fees_usd")) or 0.0

        cost = shares * entry_price + fees
        quote = quotes.get(ticker) or {}
        price = num(quote.get("price"))
        value = shares * price if price is not None else None

        pnl = (value - cost) if value is not None else None
        card = cards.get(ticker) or {}

        pos = {
            **raw,
            "ticker": ticker,
            "cost_usd": round(cost, 2),
            "price": price,
            "change_1d_pct": num(quote.get("change_1d_pct")),
            "value_usd": round(value, 2) if value is not None else None,
            "pnl_usd": round(pnl, 2) if pnl is not None else None,
            "pnl_pct": round(pnl / cost * 100, 2) if (pnl is not None and cost > 0) else None,
            "upside_to_target_pct": pct(
                (num(raw.get("target_price")) or 0) - (price or 0), price
            ) if (price and num(raw.get("target_price"))) else None,
            "holding_days": _days_between(raw.get("entry_date", "")),
            "days_to_review": _days_between(today_iso(), raw.get("review_date"))
            if raw.get("review_date") else None,
            "sector": card.get("sector", ""),
            "next_earnings": earnings.get(ticker),
            "thesis_breakers": raw.get("thesis_breakers", []),
        }

        # Giris tarihinden itibaren endekse karsi fark
        pos["vs_benchmark"] = {}
        for label, symbol in PORTFOLIO["benchmarks"].items():
            bench_return = _benchmark_return_since(
                benchmarks.get(symbol, []), raw.get("entry_date", ""))
            pos["vs_benchmark"][label] = {
                "benchmark_return_pct": round(bench_return, 2) if bench_return is not None else None,
                "excess_pct": round(pos["pnl_pct"] - bench_return, 2)
                if (pos["pnl_pct"] is not None and bench_return is not None) else None,
            }

        positions.append(pos)
        total_cost += cost
        if value is not None:
            total_value += value

    cash = num(data.get("cash_usd")) or 0.0
    equity_value = total_value
    portfolio_value = equity_value + cash

    for pos in positions:
        pos["weight_pct"] = round(pos["value_usd"] / portfolio_value * 100, 2) \
            if (pos["value_usd"] is not None and portfolio_value > 0) else None

    sector_mix: dict[str, float] = defaultdict(float)
    for pos in positions:
        if pos["value_usd"]:
            sector_mix[pos.get("sector") or "Bilinmiyor"] += pos["value_usd"]
    sector_pct = {k: round(v / equity_value * 100, 2)
                  for k, v in sector_mix.items()} if equity_value > 0 else {}

    total_pnl = equity_value - total_cost if total_cost else 0.0

    summary = {
        "position_count": len(positions),
        "cost_usd": round(total_cost, 2),
        "equity_value_usd": round(equity_value, 2),
        "cash_usd": round(cash, 2),
        "portfolio_value_usd": round(portfolio_value, 2),
        "pnl_usd": round(total_pnl, 2),
        "pnl_pct": round(total_pnl / total_cost * 100, 2) if total_cost > 0 else None,
        "sector_mix_pct": sector_pct,
        "largest_position_pct": max(
            (p["weight_pct"] for p in positions if p["weight_pct"] is not None),
            default=None),
        "vs_benchmark": _portfolio_vs_benchmark(positions),
    }

    return {
        "positions": sorted(positions, key=lambda p: p.get("value_usd") or 0, reverse=True),
        "closed": data.get("closed", []),
        "summary": summary,
        "warnings": warnings_for(positions, summary),
        "as_of": today_iso(),
        "source": "manual+prices",
    }


def _portfolio_vs_benchmark(positions: list[dict]) -> dict:
    """Pozisyon buyuklugune gore agirlikli goreli performans."""
    out = {}
    for label in PORTFOLIO["benchmarks"]:
        weighted, total_w = 0.0, 0.0
        for p in positions:
            excess = (p.get("vs_benchmark", {}).get(label) or {}).get("excess_pct")
            w = p.get("value_usd")
            if excess is not None and w:
                weighted += excess * w
                total_w += w
        out[label] = round(weighted / total_w, 2) if total_w > 0 else None
    return out


def warnings_for(positions: list[dict], summary: dict) -> list[dict]:
    """UYARILAR: konsantrasyon, gecmis gozden gecirme, tez kirici, vergi, kazanc."""
    out: list[dict] = []

    for pos in positions:
        ticker = pos["ticker"]

        if pos.get("weight_pct") is not None and \
                pos["weight_pct"] > PORTFOLIO["max_position_weight_pct"]:
            out.append({
                "ticker": ticker, "level": "high", "type": "konsantrasyon",
                "message": f"{ticker} portfoyun %{pos['weight_pct']:.1f}'i — "
                           f"esik %{PORTFOLIO['max_position_weight_pct']:.0f}",
            })

        if pos.get("days_to_review") is not None and \
                pos["days_to_review"] < -PORTFOLIO["review_overdue_grace_days"]:
            out.append({
                "ticker": ticker, "level": "medium", "type": "gozden_gecirme",
                "message": f"{ticker} gozden gecirme tarihi {abs(pos['days_to_review'])} "
                           f"gun gecti ({pos.get('review_date')})",
            })

        if pos.get("thesis_breakers"):
            triggered = [t for t in pos["thesis_breakers"]
                         if isinstance(t, dict) and t.get("triggered")]
            for t in triggered:
                out.append({
                    "ticker": ticker, "level": "high", "type": "tez_kirici",
                    "message": f"{ticker} tez kirici tetiklendi: {t.get('description', '')}",
                })

        holding = pos.get("holding_days")
        if holding is not None:
            remaining = 365 - holding
            if 0 < remaining <= PORTFOLIO["tax_year_warning_days"]:
                out.append({
                    "ticker": ticker, "level": "low", "type": "vergi",
                    "message": f"{ticker} 1 yili doldurmasina {remaining} gun "
                               f"(uzun vadeli sermaye kazanci esigi)",
                })

        next_earnings = pos.get("next_earnings")
        if next_earnings:
            days = _days_between(today_iso(), next_earnings)
            if days is not None and 0 <= days <= PORTFOLIO["earnings_warning_days"]:
                out.append({
                    "ticker": ticker, "level": "medium", "type": "kazanc",
                    "message": f"{ticker} kazanc aciklamasi {days} gun sonra ({next_earnings})",
                })

    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(out, key=lambda w: order.get(w["level"], 9))
