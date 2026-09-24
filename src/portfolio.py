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

from . import breakers as breakers_mod
from .config import DATA_DIR, PORTFOLIO, TL_DEPOSIT
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


# --------------------------------------------------------------------------
# Varlik siniflari
# --------------------------------------------------------------------------
# Portfoy artik yalnizca hisse tasimiyor. Uc sinif var ve HER BIRI FARKLI
# degerlenir:
#   STOCK       fiyat x adet
#   ETF         ayni, ama tez kirici yok — yalnizca agirlik bandi
#   TL_DEPOSIT  TL anapara + tahakkuk eden faiz, kurla dolara cevrilir
#
# TL mevduatta sorulmasi gereken "faiz ne kadar" degil, "kur ne kadar
# artarsa bu faiz erir" sorusudur. O yuzden BASA BAS KUR hesaplanir.

def slice_for(position: dict) -> str:
    """Pozisyonun hangi dilime girdigi.

    Pozisyon kendi ``slice`` alanini yazarsa o kazanir: SGOV bir ETF'tir
    ama cekirdek degil NAKIT CAPASIDIR; varlik sinifindan turetmek yanlis
    olurdu.
    """
    explicit = (position.get("slice") or "").strip().lower()
    if explicit in PORTFOLIO["slices"]:
        return explicit
    klass = (position.get("asset_class") or "STOCK").upper()
    return PORTFOLIO["asset_class_slice"].get(klass, "motor")


def tl_deposit_value(position: dict, usdtry: float | None) -> dict:
    """TL vadeli mevduatin bugunku degeri ve basa bas kuru.

    Turkiye'de mevduat faizi BASIT faizle ve 365 gun uzerinden isler;
    stopaj brut faizden kesilir.
    """
    principal = num(position.get("principal_try"))
    rate = num(position.get("annual_rate_pct"))
    start = position.get("start_date")
    maturity = position.get("maturity_date")
    entry_fx = num(position.get("usdtry_at_entry"))
    withholding = num(position.get("withholding_pct"))
    if withholding is None:
        withholding = TL_DEPOSIT["default_withholding_pct"]

    out = {
        "principal_try": principal,
        "annual_rate_pct": rate,
        "withholding_pct": withholding,
        "start_date": start,
        "maturity_date": maturity,
        "usdtry_at_entry": entry_fx,
        "usdtry_now": usdtry,
    }
    if principal is None or rate is None or not start:
        out["note"] = "anapara, faiz orani veya baslangic tarihi eksik"
        return out

    elapsed = _days_between(start, today_iso())
    term = _days_between(start, maturity) if maturity else None
    if elapsed is None or elapsed < 0:
        elapsed = 0
    # Vade gectiyse faiz islemeye devam etmez.
    accrual_days = min(elapsed, term) if term is not None else elapsed

    gross = principal * (rate / 100.0) * (accrual_days / TL_DEPOSIT["day_count"])
    tax = gross * (withholding / 100.0)
    net = gross - tax
    value_try = principal + net

    out.update({
        "elapsed_days": accrual_days,
        "term_days": term,
        "days_to_maturity": (term - elapsed) if term is not None else None,
        "gross_interest_try": round(gross, 2),
        "withholding_try": round(tax, 2),
        "net_interest_try": round(net, 2),
        "value_try": round(value_try, 2),
        "value_usd": round(value_try / usdtry, 2) if usdtry else None,
    })

    # BASA BAS KUR: vade sonunda ele gecen TL'yi giristeki dolar
    # karsiligina bolersek, "kur bunun ustune cikarsa dolar bazinda
    # zarardayiz" esigini buluruz.
    if entry_fx and entry_fx > 0 and term:
        full_gross = principal * (rate / 100.0) * (term / TL_DEPOSIT["day_count"])
        full_net = full_gross * (1 - withholding / 100.0)
        at_maturity_try = principal + full_net
        usd_at_entry = principal / entry_fx
        if usd_at_entry > 0:
            be = at_maturity_try / usd_at_entry
            out["usdtry_breakeven"] = round(be, 4)
            out["breakeven_headroom_pct"] = round((be / entry_fx - 1) * 100, 2)
            if usdtry:
                out["usdtry_used_pct"] = round(
                    (usdtry - entry_fx) / (be - entry_fx) * 100, 1) \
                    if be != entry_fx else None
    return out


def slice_summary(positions: list[dict], cash: float,
                  portfolio_value: float) -> list[dict]:
    """Dilim bazinda gercek/hedef agirlik ve sapma."""
    actual: dict[str, float] = defaultdict(float)
    for p in positions:
        if p.get("value_usd"):
            actual[p.get("slice") or "motor"] += p["value_usd"]
    actual["nakit"] += cash

    out = []
    for key, spec in PORTFOLIO["slices"].items():
        value = actual.get(key, 0.0)
        pct_now = (value / portfolio_value * 100) if portfolio_value > 0 else 0.0
        target = spec["target_pct"]
        drift = pct_now - target
        out.append({
            "slice": key,
            "label": spec["label"],
            "value_usd": round(value, 2),
            "actual_pct": round(pct_now, 2),
            "target_pct": target,
            "drift_pp": round(drift, 2),
            "off_target": abs(drift) > PORTFOLIO["slice_drift_warn_pp"],
        })
    return out


def compute(quotes: dict[str, dict],
            benchmarks: dict[str, list[tuple[str, float]]] | None = None,
            earnings: dict[str, str] | None = None,
            cards: dict[str, dict] | None = None,
            fx: dict | None = None) -> dict:
    """Portfoyun tam durumunu hesaplar.

    Args:
        quotes: ``{sembol: {"price":..,"change_1d_pct":..}}``
        benchmarks: ``{"QQQ": [(tarih, kapanis)], "SPY": [...]}``
        earnings: ``{sembol: sonraki_kazanc_tarihi}``
        cards: ``{sembol: kart}`` — sektor ve tez kiricilar icin
    """
    data = load()
    benchmarks = benchmarks or {}
    fx = fx or {}
    usdtry = num(fx.get("rate"))
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

        asset_class = (raw.get("asset_class") or "STOCK").upper()
        card = cards.get(ticker) or {}
        tl = None

        if asset_class == "TL_DEPOSIT":
            # TL mevduatta "adet x fiyat" yoktur: anapara + tahakkuk eden
            # net faiz, kurla dolara cevrilir.
            tl = tl_deposit_value(raw, usdtry)
            entry_fx = num(raw.get("usdtry_at_entry"))
            principal = num(raw.get("principal_try")) or 0.0
            cost = principal / entry_fx if entry_fx else 0.0
            price = None
            value = tl.get("value_usd")
        else:
            cost = shares * entry_price + fees
            quote = quotes.get(ticker) or {}
            price = num(quote.get("price"))
            value = shares * price if price is not None else None

        pnl = (value - cost) if (value is not None and cost) else None

        pos = {
            **raw,
            "ticker": ticker,
            "cost_usd": round(cost, 2),
            "price": price,
            "change_1d_pct": num((quotes.get(ticker) or {}).get("change_1d_pct")),
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
            "asset_class": asset_class,
            "slice": slice_for(raw),
            # KIRICILAR ARTIK MAKINE TARAFINDAN DEGERLENDIRILIYOR. Onceki
            # surumde yalnizca elle "triggered: true" yapilmis olanlar
            # raporlaniyordu; yani kural kagit uzerinde kaliyordu.
            "thesis_breakers": breakers_mod.evaluate_position(raw, card, price),
        }
        if tl is not None:
            pos["tl_deposit"] = tl

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
        "slices": slice_summary(positions, cash, portfolio_value),
        "fx": fx,
    }

    # Zirve degeri dosyada tutulur: portfoy dususu ancak gecmise gore
    # olculebilir ve her kosuda sifirdan hesaplanamaz.
    peak = max(num(data.get("peak_value_usd")) or 0.0, portfolio_value)
    summary["peak_value_usd"] = round(peak, 2)
    drawdown = breakers_mod.portfolio_drawdown(summary, peak)

    return {
        "positions": sorted(positions, key=lambda p: p.get("value_usd") or 0, reverse=True),
        "closed": data.get("closed", []),
        "summary": summary,
        "warnings": warnings_for(positions, summary, drawdown=drawdown,
                                 planned=data.get("planned_tranches")),
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


def warnings_for(positions: list[dict], summary: dict, *,
                 drawdown: dict | None = None,
                 planned: list | None = None) -> list[dict]:
    """UYARILAR: konsantrasyon, gozden gecirme, tez kirici, vergi, kazanc,
    dilim sapmasi, kademeli alim ve portfoy dususu."""
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

        for t in pos.get("thesis_breakers") or []:
            if not isinstance(t, dict):
                continue
            if t.get("manual") and not t.get("triggered"):
                # Makine degerlendiremiyor ve elle de tetiklenmemis: kural
                # duruyor, kullanici elle baksin diye gorunur kalmali.
                out.append({
                    "ticker": ticker, "level": "low", "type": "elle_kontrol",
                    "message": f"{ticker} elle kontrol: {t.get('description', '')}",
                })
                continue
            if t.get("status") == "veri_yok":
                out.append({
                    "ticker": ticker, "level": "low", "type": "kirici_veri_yok",
                    "message": f"{ticker} kirici degerlendirilemedi: "
                               f"{t.get('note') or t.get('description', '')}",
                })
                continue
            if t.get("triggered"):
                # Tur adi KIND'e gore. "tez_kirici" korunuyor: panoda ve
                # testlerde bu ada bagli kod var, yapisal kirici hala odur.
                kind = t.get("kind", "thesis")
                tur = {"thesis": "tez_kirici",
                       "catastrophic_price": "kirici_fiyat_cokusu",
                       "take_profit": "kirici_hedef"}.get(kind, f"kirici_{kind}")
                aksiyon = t.get("action") or ""
                out.append({
                    "ticker": ticker,
                    "level": t.get("level", "high"),
                    "type": tur,
                    "message": (f"{ticker} tez kirici tetiklendi: "
                                f"{t.get('description', '')}"
                                + (f" -> {aksiyon}" if aksiyon else "")),
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

    # DILIM SAPMASI — hedeften uzaklasma tek tek pozisyonlarda gorunmez.
    # Portfoy BOSKEN uyarmiyoruz: dort dilimin dordu birden "sapma" derse
    # bu bilgi degil gurultudur ve ilk gunden itibaren uyarilarin
    # gormezden gelinmesini ogretir. Dengelenecek bir sey olmali.
    if positions:
        for sl in summary.get("slices") or []:
            if sl.get("off_target"):
                yon = "uzerinde" if sl["drift_pp"] > 0 else "altinda"
                out.append({
                    "ticker": "", "level": "medium", "type": "dilim_sapmasi",
                    "message": f"{sl['label']}: %{sl['actual_pct']:.1f} "
                               f"(hedef %{sl['target_pct']:.0f}, "
                               f"{abs(sl['drift_pp']):.1f} puan {yon})",
                })

    # KADEMELI ALIM — sirada bekleyen parca.
    for tr in planned or []:
        if not isinstance(tr, dict) or tr.get("done"):
            continue
        gun = _days_between(today_iso(), tr.get("date"))
        if gun is None or gun > 7:
            continue
        ne_zaman = f"{gun} gun sonra" if gun > 0 else (
            "bugun" if gun == 0 else f"{abs(gun)} gun GECTI")
        out.append({
            "ticker": tr.get("ticker", ""), "level": "medium",
            "type": "kademeli_alim",
            "message": f"Siradaki parca {ne_zaman} ({tr.get('date')}): "
                       f"{tr.get('amount_usd', '?')} USD "
                       f"{tr.get('ticker', '')}".strip(),
        })

    if drawdown:
        out.append({
            "ticker": "", "level": drawdown["level"],
            "type": "portfoy_dususu",
            "message": f"{drawdown['description']} -> {drawdown['action']}",
        })

    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(out, key=lambda w: order.get(w["level"], 9))
