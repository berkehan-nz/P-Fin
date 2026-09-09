"""Sirket kartlari — ``data/cards/<TICKER>.json`` uretimi ve hikaye birlestirme.

KRITIK KURAL: veri hatti ``story`` ve ``decision`` bloklarina ASLA yazmaz.
Bunlari sohbetteki Claude (``claude_inbox/``) ve Berke doldurur. Kart her
yeniden uretildiginde bu iki blok korunur; aksi halde her gunluk kosu
Claude'un analizini silerdi.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from . import (config, metrics as metrics_mod, percentiles as pct_mod,
               scores as scores_mod, scoring, validate)
from .config import CARDS_DIR, INBOX_DIR, color_for, sector_for_sic
from .fundamentals import Fundamentals
from .sources import prices
from .util import num, read_json, today_iso, utc_now_iso, write_json

# story bolumunun bos semasi — SEN DOLDURMA, Claude yazar
STORY_SCHEMA = {
    "business_model": "",
    "moat": "",
    "why_cheap_diagnosis": "",
    "why_cheap_rationale": "",
    "bull_case": [],
    "bear_case": [],
    "catalyst": {"type": "", "expected_date": "", "confidence": ""},
    "thesis_breakers": [],
    "analyst_narrative": "",
    "news_summary": "",
    "claude_verdict": "",
    "author": "claude",
    "updated_at": "",
}

DECISION_SCHEMA = {
    "action": "",          # AL | BEKLE | ELE
    "date": "",
    "rationale": "",
    "author": "berke",
}


def empty_story() -> dict:
    import copy
    return copy.deepcopy(STORY_SCHEMA)


def empty_decision() -> dict:
    import copy
    return copy.deepcopy(DECISION_SCHEMA)


def card_path(ticker: str) -> Path:
    return CARDS_DIR / f"{ticker.upper()}.json"


def load_card(ticker: str) -> dict | None:
    return read_json(card_path(ticker))


# --------------------------------------------------------------------------
# Kart uretimi
# --------------------------------------------------------------------------
def build(f: Fundamentals, *,
          source: str,
          sector_table: dict | None = None,
          news: list[dict] | None = None,
          next_earnings: str | None = None,
          analyst: dict | None = None,
          short_interest: dict | None = None,
          insider: dict | None = None,
          benchmark: list[tuple[str, float]] | None = None,
          catalyst_score: float | None = None,
          extra_warnings: list[str] | None = None,
          force_organic_suspect: bool = False,
          funnel_result: dict | None = None,
          is_manual: bool = False,
          both_tracks: bool = False) -> dict:
    """Bir sirket icin tam kart sozlugu uretir."""
    mres = metrics_mod.compute(f, benchmark=benchmark)
    sres = scores_mod.compute(f, mres)

    m = {**mres["metrics"], **sres["metrics"]}
    meta = mres["meta"]
    flags = dict(mres["flags"])

    sector = sector_for_sic(f.sic)
    track = metrics_mod.track_for(m, config.STAGE3["track_b_operating_margin_pct"])
    if both_tracks:
        track = "both"

    # --- yuzdelikler ---
    sector_pcts: dict[str, float | None] = {}
    pct_basis: dict[str, str] = {}
    if sector_table:
        for key in pct_mod.SECTOR_PERCENTILE_METRICS:
            p, basis = pct_mod.sector_percentile(sector_table, sector, key, m.get(key))
            sector_pcts[key] = p
            pct_basis[key] = basis
    own_pcts = pct_mod.own_history_percentiles(f, m)

    # --- puanlar ---
    score_input = dict(sector_pcts)
    score_block, score_detail = scoring.compute(score_input, catalyst_score)

    # --- metrik hucreleri ---
    cells: dict[str, dict] = {}
    for block_metrics in config.METRIC_BLOCKS.values():
        for key in block_metrics:
            value = num(m.get(key))
            cells[key] = {
                "value": _round(value, key),
                "sector_pct": _round(sector_pcts.get(key), None, 1),
                "own_5y_pct": _round(own_pcts.get(key), None, 1),
                "color": color_for(key, value),
                "pct_basis": pct_basis.get(key, "none"),
            }
    # bloklarda gecmeyen ama gerekli olanlar
    for key in ("ebitda_margin", "rule_of_40_gap", "net_debt", "return_6m",
                "return_12m", "rel_strength_6m", "rel_strength_12m",
                "pct_off_52w_high", "rev_cagr_3y", "gross_margin_change_3y",
                "operating_margin_change_3y", "fcf_margin_change_3y"):
        if key not in cells:
            value = num(m.get(key))
            cells[key] = {
                "value": _round(value, key),
                "sector_pct": _round(sector_pcts.get(key), None, 1),
                "own_5y_pct": None,
                "color": color_for(key, value),
                "pct_basis": pct_basis.get(key, "none"),
            }

    # --- bayraklar ---
    warnings = list(extra_warnings or [])
    warnings.extend(config.SEED_PREWARNINGS.get(f.ticker, []))
    if force_organic_suspect:
        flags["rev_growth_organic_suspect"] = True
    if flags.get("one_off_earnings"):
        warnings.append(
            "Net kar EBIT'e gore asiri yuksek veya vergi orani negatif — "
            "F/K tek seferlik kalemle sismis olabilir."
        )
    if flags.get("rev_growth_organic_suspect"):
        warnings.append(
            "Buyume satin alma kaynakli olabilir; serefiye artisi ve 8-K "
            "devralma duyurulari kontrol edilmeli."
        )
    if flags.get("z_unreliable"):
        warnings.append(
            "Ozkaynak negatif — Altman Z'' anlamsiz. Faiz karsilama ve "
            "FCF/toplam borc ile degerlendir."
        )
    if meta.get("data_basis") == "annual":
        warnings.append("Ceyreklik veri yetersiz; metrikler yillik tablodan hesaplandi.")

    flags.update({
        "passed_stages": (funnel_result or {}).get("passed_stages", []),
        "would_fail_at": (funnel_result or {}).get("would_fail_at"),
        "kill_reason": (funnel_result or {}).get("kill_reason"),
        "stage1_missing": (funnel_result or {}).get("stage1_missing", []),
        "warnings": _dedupe(warnings),
        "is_manual": is_manual,
        "roic_method": meta["roic_method"],
        "data_basis": meta["data_basis"],
    })

    # --- seriler (12 ceyrek grafikleri) ---
    series = _build_series(f)
    series["price_sparkline"] = prices.sparkline(f.price_history)

    card = {
        "ticker": f.ticker,
        "name": f.name,
        "exchange": f.exchange,
        "sector": sector,
        "sic": f.sic,
        "track": track,
        "source": source,
        "as_of": today_iso(),
        "price": _round(f.price, None, 2),
        "market_cap_musd": _round(meta["market_cap_musd"], None, 1),
        "enterprise_value_musd": _round(meta["enterprise_value_musd"], None, 1),
        # Gunluk kosu fiyat degisince EV ve carpanlari BUNLARDAN yeniden
        # hesaplar. Eski carpani oranla olceklemek her gun biraz daha sapan
        # bir sayi birakirdi; TTM buyuklukleri gun icinde degismez.
        "shares_outstanding_m": _round(f.shares_outstanding, None, 4),
        "net_debt_musd": _round(m.get("net_debt"), None, 1),
        "ttm": {
            "revenue_musd": _round(meta.get("revenue_ttm_musd"), None, 1),
            "gross_profit_musd": _round(meta.get("gross_profit_ttm_musd"), None, 1),
            "ebit_musd": _round(meta.get("ebit_ttm_musd"), None, 1),
            "ebitda_musd": _round(meta.get("ebitda_ttm_musd"), None, 1),
            "net_income_musd": _round(meta.get("net_income_ttm_musd"), None, 1),
            "fcf_musd": _round(meta.get("fcf_ttm_musd"), None, 1),
            "period_end": meta.get("period_end"),
        },
        "scores": score_block,
        "score_detail": score_detail,
        "metrics": cells,
        "series": series,
        "flags": flags,
        "news": news or [],
        "calendar": {"next_earnings": next_earnings},
        "analyst": analyst or {},
        "short_interest": short_interest or {},
        "insider": insider or {},
        "reverse_dcf": {
            "implied_growth_pct": _round(m.get("implied_growth"), None, 2),
            "actual_growth_pct": _round(m.get("rev_cagr_3y"), None, 2),
            "fcf_ttm_musd": _round(meta.get("fcf_ttm_musd"), None, 1),
            "enterprise_value_musd": _round(meta.get("enterprise_value_musd"), None, 1),
            "discount_rate": config.REVERSE_DCF["discount_rate"],
            "terminal_growth": config.REVERSE_DCF["terminal_growth"],
            "projection_years": config.REVERSE_DCF["projection_years"],
        },
        "score_internals": {
            "piotroski": sres["detail"]["piotroski"],
            "altman": sres["detail"]["altman"],
            "beneish": {"m": sres["detail"]["beneish"]["m"],
                        "missing": sres["detail"]["beneish"]["missing"]},
            "solvency_fallback": sres["detail"]["solvency_fallback"],
        },
        "story": empty_story(),
        "decision": empty_decision(),
        "data_sources": {
            "fundamentals": f.sources.get("fundamentals"),
            "price": f.sources.get("price"),
            "news": "finnhub" if news else None,
            "analyst": (analyst or {}).get("source"),
            "shares": f.sources.get("shares"),
            "period_end": meta.get("period_end"),
        },
        "generated_at": utc_now_iso(),
    }

    # Yayimlamadan once makulluk denetimi: imkansiz degerler silinir,
    # supheli olanlar isaretlenir. Sessiz yanlis sayi, gorunur boslugtan kotudur.
    validate.check(card)
    return card


def _build_series(f: Fundamentals, n: int = 12) -> dict:
    """Grafikler icin son 12 ceyrek: hasilat, brut marj, FCF, hisse sayisi."""
    quarters = f.sorted_quarters()[-n:]
    if not quarters:
        annuals = f.sorted_annuals()[-n:]
        return {
            "quarters": [a.period_end for a in annuals],
            "revenue": [num(a.revenue) for a in annuals],
            "gross_margin": [_gm(a) for a in annuals],
            "fcf": [a.fcf for a in annuals],
            "share_count": [num(a.shares_diluted) for a in annuals],
            "basis": "annual",
        }
    return {
        "quarters": [f"{q.fiscal_year}-{q.period_end[5:7]}" for q in quarters],
        "period_ends": [q.period_end for q in quarters],
        "revenue": [num(q.revenue) for q in quarters],
        "gross_margin": [_gm(q) for q in quarters],
        "fcf": [q.fcf for q in quarters],
        "share_count": [num(q.shares_diluted) for q in quarters],
        "basis": "quarterly",
    }


def _gm(p) -> float | None:
    gp, rev = p.computed_gross_profit, num(p.revenue)
    return round(gp / rev * 100, 2) if (gp is not None and rev) else None


def _round(v, metric: str | None = None, digits: int | None = None):
    v = num(v)
    if v is None:
        return None
    if digits is not None:
        return round(v, digits)
    unit = (config.THRESHOLDS.get(metric or "", {}) or {}).get("unit", "")
    return round(v, 2 if unit in ("%", "x", "") else 3)


def _dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for i in items:
        if i and i not in seen:
            seen.add(i)
            out.append(i)
    return out


# --------------------------------------------------------------------------
# Hikaye birlestirme
# --------------------------------------------------------------------------
def merge_story(card: dict, *, inbox_dir: Path | None = None) -> dict:
    """``claude_inbox/<TICKER>.json`` icerigini kartla birlestirir.

    CAKISMADA INBOX KAZANIR. Inbox yalnizca ``story`` ve ``decision``
    bloklarina dokunabilir — sayisal alanlar veri hattinin sorumlulugunda
    kalir; aksi halde elle yazilmis bir sayi metriklerin uzerine yazardi.
    """
    inbox_dir = inbox_dir or INBOX_DIR
    path = Path(inbox_dir) / f"{card['ticker'].upper()}.json"
    payload = read_json(path)
    if not isinstance(payload, dict):
        return card

    story_in = payload.get("story")
    if isinstance(story_in, dict):
        story = {**card.get("story", empty_story())}
        for key, value in story_in.items():
            if key in STORY_SCHEMA and value not in (None, "", [], {}):
                story[key] = value
        story["author"] = story_in.get("author", "claude")
        story["updated_at"] = story_in.get("updated_at") or today_iso()
        card["story"] = story

    decision_in = payload.get("decision")
    if isinstance(decision_in, dict):
        decision = {**card.get("decision", empty_decision())}
        for key, value in decision_in.items():
            if key in DECISION_SCHEMA and value not in (None, ""):
                decision[key] = value
        if decision.get("action") and not decision.get("date"):
            decision["date"] = today_iso()
        card["decision"] = decision

    # Katalizor puani elle girilebilir (0-100)
    cat = num(payload.get("catalyst_score"))
    if cat is not None:
        card["scores"] = scoring.total_score(
            {k: card["scores"].get(k) for k in
             ("value", "quality", "safety", "momentum", "earnings_quality")},
            catalyst=cat,
        )
    return card


def has_content(value) -> bool:
    """Bir blokta gercekten yazilmis bir sey var mi?

    Ic ice bos semalar (orn. ``catalyst`` = {"type":"","expected_date":""})
    dolu SAYILMAZ; aksi halde bos bir kart, uzerine yeni yazilani ezerdi.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set)):
        return any(has_content(v) for v in value)
    if isinstance(value, dict):
        return any(has_content(v) for k, v in value.items()
                   if k not in ("author", "updated_at"))
    return True


def preserve_authored(new_card: dict, old_card: dict | None) -> dict:
    """Yeniden uretimde Claude'un ve Berke'nin yazdiklarini korur.

    Veri hatti gunde bir kez tum kartlari yeniden uretir; bu koruma olmadan
    her kosu Claude'un analizini ve Berke'nin kararini silerdi.
    """
    if not old_card:
        return new_card
    for key in ("story", "decision"):
        old = old_card.get(key)
        if isinstance(old, dict) and has_content(old):
            new_card[key] = old
    return new_card


def save(card: dict, *, merge: bool = True) -> bool:
    """Karti diske yazar. Once eski kartin yazili bloklarini korur,
    sonra inbox'i birlestirir. Icerik degismediyse dosyaya dokunmaz."""
    old = load_card(card["ticker"])
    card = preserve_authored(card, old)
    if merge:
        card = merge_story(card)
    card["story_age_days"] = _story_age(card)
    return write_json(card_path(card["ticker"]), card)


def _story_age(card: dict) -> int | None:
    updated = (card.get("story") or {}).get("updated_at")
    if not updated:
        return None
    try:
        return (date.today() - date.fromisoformat(updated[:10])).days
    except ValueError:
        return None


def summary_row(card: dict) -> dict:
    """``candidates.json`` icin kompakt satir — dashboard izgarasi bunu okur."""
    m = card.get("metrics", {})
    track = card.get("track", "A")
    headline_keys = config.HEADLINE_METRICS.get(
        "B" if track == "B" else "A", config.HEADLINE_METRICS["A"])
    verdict = (card.get("story") or {}).get("claude_verdict") or ""
    return {
        "ticker": card["ticker"],
        "name": card.get("name", ""),
        "sector": card.get("sector", ""),
        "track": track,
        "source": card.get("source", ""),
        "price": card.get("price"),
        "market_cap_musd": card.get("market_cap_musd"),
        "scores": card.get("scores", {}),
        "headline": {k: m.get(k, {}) for k in headline_keys},
        "why_cheap": (card.get("story") or {}).get("why_cheap_diagnosis", ""),
        "claude_verdict": verdict[:140],
        "story_age_days": card.get("story_age_days"),
        "data_quality": (card.get("data_quality") or {}).get("status", "iyi"),
        "decision": (card.get("decision") or {}).get("action", ""),
        "warnings": (card.get("flags") or {}).get("warnings", []),
        "warning_count": len((card.get("flags") or {}).get("warnings", [])),
        "flags": {k: (card.get("flags") or {}).get(k) for k in
                  ("rev_growth_organic_suspect", "one_off_earnings",
                   "z_unreliable", "is_manual")},
        "sparkline": (card.get("series") or {}).get("price_sparkline", []),
        "as_of": card.get("as_of"),
    }
