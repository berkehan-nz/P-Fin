"""CUMA RAPORU — haftada bir, tek sayfada "neye bakmam lazim".

Sistem her gun veri uretiyor ama bu, her gun BAKILMASI gerektigi anlamina
gelmiyor. Gunluk bakmak iki sekilde zarar verir: ya gurultuye alisip
gercek sinyali kacirirsin, ya da her dalgalanmaya tepki verip islem
maliyetini tezin getirisinden buyutursun.

Bu yuzden haftada bir, SABIT bir liste:

  1. Tetiklenen tez kiricilar      — karar gerektiren tek sey bu
  2. 7 gun icindeki kazanc raporlari — once bilgi, sonra tepki
  3. Dilim sapmalari                — yeniden dengeleme
  4. Huniden gelen yeni adaylar     — gecen rapordan bu yana
  5. USD/TRY ve TL basa bas kuru    — mevduatin gercek durumu
  6. Makro takvim                   — onumuzdeki kritik tarihler

"Yeni aday" GECEN RAPORA GORE hesaplanir: rapor kendi onceki aday
listesini tasir ve farki alir. Kart dosyasinin tarihine bakmak yaniltici
olurdu — kartlar her tur yeniden uretiliyor.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from . import config, watchlist
from .config import CARDS_DIR, DATA_DIR
from .util import num, read_json, today_iso, write_json

WEEKLY_PATH = DATA_DIR / "weekly.json"

# Kazanc raporu ufku. Portfoy uyarisi 7 gun kullaniyor; haftalik rapor da
# ayni pencereyi kullanmali, yoksa iki yerde farkli sayi gorunur.
EARNINGS_HORIZON_DAYS = 7


def _days_until(target: str | None) -> int | None:
    if not target:
        return None
    try:
        return (date.fromisoformat(str(target)[:10]) - date.today()).days
    except ValueError:
        return None


def _is_friday(when: date | None = None) -> bool:
    return (when or date.today()).weekday() == 4


# --------------------------------------------------------------------------
# Bolumler
# --------------------------------------------------------------------------
def triggered_breakers(portfolio_state: dict) -> list[dict]:
    """Karar gerektiren tek bolum. Basa bu yuzden konuyor."""
    out = []
    for pos in portfolio_state.get("positions") or []:
        for b in pos.get("thesis_breakers") or []:
            if not isinstance(b, dict) or not b.get("triggered"):
                continue
            out.append({
                "ticker": pos.get("ticker"),
                "kind": b.get("kind", "thesis"),
                "level": b.get("level", "high"),
                "description": b.get("description", ""),
                "action": b.get("action", ""),
                "current_value": b.get("current_value"),
                "triggered_at": b.get("triggered_at"),
                "manual": bool(b.get("manual")),
            })
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(out, key=lambda x: order.get(x["level"], 9))


def upcoming_earnings(portfolio_state: dict, cards: dict) -> list[dict]:
    """Portfoy + izleme listesinde 7 gun icindeki bilanco tarihleri.

    Kazanc raporu bir KARAR ani degil, bir BILGI anidir: once rakam
    gelir, sonra tez yeniden tartilir. O yuzden burada "sat/al" yok.
    """
    watched = set(watchlist.tickers())
    held = {p.get("ticker") for p in (portfolio_state.get("positions") or [])}
    out = []
    for ticker in sorted(watched | held):
        card = cards.get(ticker) or {}
        when = (card.get("calendar") or {}).get("next_earnings")
        gun = _days_until(when)
        if gun is None or not (0 <= gun <= EARNINGS_HORIZON_DAYS):
            continue
        out.append({
            "ticker": ticker,
            "date": when,
            "days": gun,
            "estimated": bool((card.get("calendar") or {}).get("estimated")),
            "in_portfolio": ticker in held,
        })
    return sorted(out, key=lambda x: x["days"])


def slice_drift(portfolio_state: dict) -> list[dict]:
    """Hedeften sapan dilimler. Sapmayan dilim rapora girmez."""
    return [s for s in ((portfolio_state.get("summary") or {}).get("slices") or [])
            if s.get("off_target")]


def new_candidates(candidates: dict, previous: list[str]) -> dict:
    """Gecen rapordan bu yana huniye giren ve cikanlar.

    Cikanlari da yaziyoruz: bir sirketin listeden dusmesi de bilgidir
    (sektor kotasi doldu, puani geriledi, ya da veri bozuldu).
    """
    rows = [*(candidates.get("candidates") or [])]
    now = [r["ticker"] for r in rows if r.get("ticker")]
    onceki = set(previous or [])
    girenler = [r for r in rows if r.get("ticker") not in onceki]
    girenler.sort(key=lambda r: (r.get("scores") or {}).get("total") or -1,
                  reverse=True)
    return {
        "entered": [{
            "ticker": r["ticker"],
            "name": r.get("name"),
            "score": (r.get("scores") or {}).get("total"),
            "headline": r.get("headline"),
        } for r in girenler[:15]],
        "left": sorted(onceki - set(now))[:15],
        "current_tickers": sorted(now),
        "first_report": not previous,
    }


def fx_section(portfolio_state: dict) -> dict:
    """USD/TRY ve TL mevduatin basa bas durumu.

    Mevduatta sorulmasi gereken "faiz ne kadar" degil, "kur ne kadar
    artarsa bu faiz erir". Basa bas kura ne kadar yaklastigimiz, faiz
    oranindan daha cok sey soyler.
    """
    summary = portfolio_state.get("summary") or {}
    fx = summary.get("fx") or {}
    out = {
        "usdtry": fx.get("rate"),
        "as_of": fx.get("as_of"),
        "change_1w_pct": fx.get("change_1w_pct"),
        "deposits": [],
    }
    for pos in portfolio_state.get("positions") or []:
        tl = pos.get("tl_deposit")
        if not tl:
            continue
        out["deposits"].append({
            "ticker": pos.get("ticker"),
            "value_try": tl.get("value_try"),
            "value_usd": tl.get("value_usd"),
            "usdtry_at_entry": tl.get("usdtry_at_entry"),
            "usdtry_breakeven": tl.get("usdtry_breakeven"),
            "breakeven_headroom_pct": tl.get("breakeven_headroom_pct"),
            "usdtry_used_pct": tl.get("usdtry_used_pct"),
            "days_to_maturity": tl.get("days_to_maturity"),
            "net_interest_try": tl.get("net_interest_try"),
        })
    return out


def macro_calendar(pulse: dict, macro: dict) -> dict:
    """Onumuzdeki kritik tarihler + makro nabiz ozeti."""
    cal = pulse.get("calendar") or {}
    upcoming = []
    for item in (cal.get("upcoming") or cal.get("critical") or []):
        gun = _days_until(item.get("date"))
        if gun is not None and gun >= 0:
            upcoming.append({**item, "days": gun})
    upcoming.sort(key=lambda x: x["days"])

    series = macro.get("series") or {}
    return {
        "upcoming": upcoming[:12],
        "risk_note": pulse.get("risk_note"),
        "key_rates": {k: (v.get("value") if isinstance(v, dict) else v)
                      for k, v in series.items()
                      if k in ("us10y", "fed_funds", "cpi_yoy")},
    }


def scan_status(scan_state: dict) -> dict:
    total = (scan_state.get("universe_size_at_cycle_start")
             or len(scan_state.get("queue") or []) or 0)
    done = min(scan_state.get("cursor", 0), total) if total else 0
    kinds = scan_state.get("kill_kinds") or {}
    return {
        "cycle": scan_state.get("cycle"),
        "done": done,
        "total": total,
        "pct": round(done / total * 100, 1) if total else 0.0,
        "survivors": scan_state.get("survivor_count", 0),
        "eliminated": kinds.get("ELENDI", 0),
        "data_missing": kinds.get("VERI_YOK", 0),
        "retry_queue": len(scan_state.get("retry_queue") or []),
        "last_finalized": scan_state.get("last_finalized"),
    }


# --------------------------------------------------------------------------
# Rapor
# --------------------------------------------------------------------------
def build(*, cards: dict | None = None) -> dict:
    """Cuma raporunu kurar. Tum girdiler diskten okunur."""
    portfolio_state = read_json(DATA_DIR / "portfolio_state.json", {}) or {}
    candidates = read_json(DATA_DIR / "candidates.json", {}) or {}
    pulse = read_json(DATA_DIR / "pulse.json", {}) or {}
    macro = read_json(DATA_DIR / "macro.json", {}) or {}
    scan_state = read_json(DATA_DIR / "scan_state.json", {}) or {}
    previous = read_json(WEEKLY_PATH, {}) or {}

    if cards is None:
        cards = {}
        for path in CARDS_DIR.glob("*.json"):
            c = read_json(path)
            if isinstance(c, dict) and c.get("ticker"):
                cards[c["ticker"]] = c

    breakers = triggered_breakers(portfolio_state)
    drift = slice_drift(portfolio_state)
    earnings = upcoming_earnings(portfolio_state, cards)
    yeni = new_candidates(
        candidates,
        ((previous.get("new_candidates") or {}).get("current_tickers")) or [])

    # EYLEM GEREKTIREN madde sayisi basa yazilir: rapor uzun olabilir ama
    # "bu hafta bir sey yapmam gerekiyor mu" sorusu tek bakista cevaplanmali.
    action_count = len(breakers) + len(drift)

    return {
        "as_of": today_iso(),
        "week_of": (date.today() - timedelta(days=date.today().weekday())).isoformat(),
        "action_required": action_count,
        "triggered_breakers": breakers,
        "upcoming_earnings": earnings,
        "slice_drift": drift,
        "new_candidates": yeni,
        "fx": fx_section(portfolio_state),
        "macro": macro_calendar(pulse, macro),
        "scan": scan_status(scan_state),
        "portfolio": {
            "value_usd": (portfolio_state.get("summary") or {}).get("portfolio_value_usd"),
            "pnl_pct": (portfolio_state.get("summary") or {}).get("pnl_pct"),
            "position_count": (portfolio_state.get("summary") or {}).get("position_count"),
        },
        "source": "weekly",
    }


def write(*, force: bool = False, cards: dict | None = None) -> bool:
    """Cuma gunu (ya da ``force``) raporu yazar.

    Cuma disinda yazmamak kasitli: "gecen rapordan bu yana yeni aday"
    hesabi, raporun HAFTALIK yazilmasina dayanir. Her gun yazilsa
    "yeni" penceresi bir gune duser ve bolum anlamsizlasir.
    """
    if not (force or _is_friday()):
        return False
    return write_json(WEEKLY_PATH, build(cards=cards), stamp_matters=True)
