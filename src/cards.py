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
    flags = {**mres["flags"], **sres["flags"]}

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
                # Renk GOSTERILEN degerden hesaplanir. Yuvarlanmamis degerden
                # hesaplanirsa kartta "0,30x" yazip sari boyanabiliyor; oysa
                # ekrandaki kurala gore 0,30 yesil. Sayi ile rengi ayni girdiye
                # bagla ki ikisi birbirini yalanlamasin.
                "color": color_for(key, _round(value, key)),
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
                # Renk GOSTERILEN degerden hesaplanir. Yuvarlanmamis degerden
                # hesaplanirsa kartta "0,30x" yazip sari boyanabiliyor; oysa
                # ekrandaki kurala gore 0,30 yesil. Sayi ile rengi ayni girdiye
                # bagla ki ikisi birbirini yalanlamasin.
                "color": color_for(key, _round(value, key)),
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
        # Gerekce iki farkli sebepten gelebilir (negatif ozkaynak VEYA
        # abonelik/ertelenmis gelir istisnasi); sabit metin yazmak yanlis
        # teshis gosterirdi.
        warnings.append(
            flags.get("z_unreliable_reason")
            or "Altman Z'' guvenilmez. Faiz karsilama ve FCF/toplam borc ile degerlendir."
        )
    # NET KAR EBIT'E GORE IMKANSIZ KUCUK.
    # ConEd'de TTM net kar 2,0 mn $ gorunuyordu; hasilat 17,4 mlr, EBIT 3,0 mlr.
    # Gercek net kar ~2 mlr — yani bin kat yanlis. Sonuc panoda 19.158x F/K.
    # Vergi ve faiz karin %98'ini yiyemez; boyle bir oran veri hatasidir.
    _ni = num(meta.get("net_income_ttm_musd"))
    _ebit = num(meta.get("ebit_ttm_musd"))
    if _ni is not None and _ebit is not None and _ebit > 50 and 0 < _ni < _ebit * 0.02:
        warnings.append(
            f"NET KAR SUPHELI: TTM net kar {_ni:,.1f} mn $ ama EBIT {_ebit:,.0f} mn $. "
            f"Vergi ve faiz karin %98'ini yiyemez; kalem buyuk olasilikla eksik veya "
            f"yanlis olcekte alinmis. F/K, PEG ve kazanc kalitesi puani bu sayidan "
            f"turedigi icin guvenilmez.")

    # FAIZ ILE BORC TUTARLI MI? Borc etiketi kacirilinca sirket "borcsuz"
    # gorunuyor, faiz karsilama tavan degeri (100) aliyor ve saglamlik puaninda
    # en guvenli sirket gibi puanlaniyordu (COLL: 1.036 mn $ borc, 76 mn $ faiz,
    # kartta borc sifir). Odenen faizden ima edilen oran bu ayrismayi yakalar.
    _last, _cur = f.latest_period(), f.ttm_period()
    _debt = (num(_last.long_term_debt) or 0.0) + (num(_last.short_term_debt) or 0.0) if _last else 0.0
    _interest = abs(num(_cur.interest_expense) or 0.0) if _cur else 0.0
    _ebit = num(_cur.operating_income) if _cur else None
    if _interest > 0 and _ebit and _interest > abs(_ebit) * 0.02:
        if _debt <= 0:
            warnings.append(
                f"BORC GORUNMUYOR AMA FAIZ ODENIYOR: TTM faiz gideri "
                f"{_interest:,.1f} mn $, bilancoda finansal borc yok. Borc donem "
                f"icinde kapanmis olabilir ya da borc etiketi okunamadi; "
                f"net borc ve isletme degeri eksik olabilir.")
        elif _interest / _debt > 0.15:
            warnings.append(
                f"BORC EKSIK OLABILIR: {_interest:,.1f} mn $ faiz, {_debt:,.1f} mn $ "
                f"borca %{_interest / _debt * 100:.0f} faiz orani ima ediyor. "
                f"Bir borc kalemi okunamamis olabilir.")

    not_scored = (score_block or {}).get("not_scored")
    if not_scored:
        warnings.append(f"PUANLANAMADI: {not_scored}")

    for o in (getattr(f, "overrides_applied", None) or []):
        warnings.append(
            f"ELLE DUZELTME: {o['period_end']} donemi {o['field']} alani "
            f"{o['before']} yerine {o['after']} olarak alindi. "
            f"Gerekce: {o['reason']} Kaynak: {o['source_url']}")

    if meta.get("data_basis") == "annual":
        warnings.append("Ceyreklik veri yetersiz; metrikler yillik tablodan hesaplandi.")
    elif meta.get("data_basis") == "mixed":
        from .fundamentals import CORE_FLOW_FIELDS
        core = [f for f in meta.get("annual_fallback_fields", [])
                if f in CORE_FLOW_FIELDS]
        fields = ", ".join(core[:6])
        warnings.append(
            f"Bazi kalemler ceyreklerden degil YILLIK tablodan geldi ({fields}). "
            f"Bu kalemlerde TTM, son mali yil demektir; ceyreklik grafikle "
            f"toplami tutmayabilir."
        )

    flags.update({
        "passed_stages": (funnel_result or {}).get("passed_stages", []),
        "would_fail_at": (funnel_result or {}).get("would_fail_at"),
        "kill_reason": (funnel_result or {}).get("kill_reason"),
        "stage1_missing": (funnel_result or {}).get("stage1_missing", []),
        "warnings": _dedupe(warnings),
        "is_manual": is_manual,
        "roic_method": meta["roic_method"],
        "data_basis": meta["data_basis"],
        "annual_fallback_fields": meta.get("annual_fallback_fields", []),
    })

    # --- seriler (12 ceyrek grafikleri) ---
    series = _build_series(f)

    # CEYREKLIK GRAFIK ILE TTM METRIGI CELISIYOR MU?
    # Bir kalem yillik tablodan geldiginde grafik ceyrekleri, metrik ise mali
    # yili gosterir. INOD'da grafik %44 brut marj cizerken metrik %31 diyordu;
    # ayni sayfada iki farkli gercek. Genel "tutmayabilir" uyarisi hangi
    # grafigin tutmadigini soylemiyor — farki OLC ve yaz.
    if series.get("basis") != "annual":
        for field, label, ttm_value in (
            ("revenue", "Satislar", num(meta.get("revenue_ttm_musd"))),
            ("fcf", "Serbest nakit akisi", num(meta.get("fcf_ttm_musd"))),
        ):
            q = [num(x) for x in (series.get(field) or [])[-4:]]
            if len(q) == 4 and all(x is not None for x in q) and ttm_value:
                diff = abs(sum(q) - ttm_value) / abs(ttm_value)
                if diff > 0.05:
                    warnings.append(
                        f"GRAFIK-METRIK CELISKISI: {label} grafiginin son 4 ceyregi "
                        f"{sum(q):,.0f} mn $ ediyor ama TTM {ttm_value:,.0f} mn $ "
                        f"(%{diff * 100:.0f} fark). Bu kalem yillik tablodan gelmis "
                        f"olabilir; grafik ile metrik ayni donemi anlatmiyor.")

        # TEK CEYREK AYKIRI DEGERI. CRI'de brut marj %43'ten %67'ye sicriyor;
        # perakendede bir ceyrekte 24 puan marj artisi gercek degil, etiket
        # kapsami sorunudur (ceyreklik hasilata kumulatif brut kar gibi).
        # Sayiyi sessizce duzeltmek yanlis olur — isaretle, insan baksin.
        gm_all = [num(x) for x in (series.get("gross_margin") or []) if num(x) is not None]
        if len(gm_all) >= 5:
            ordered = sorted(gm_all[:-1])
            median = ordered[len(ordered) // 2]
            last = gm_all[-1]
            if abs(last - median) > 15:
                warnings.append(
                    f"AYKIRI CEYREK: son ceyregin brut marji %{last:.1f}, onceki "
                    f"ceyreklerin ortancasi %{median:.1f}. {abs(last - median):.0f} "
                    f"puanlik sicrama muhtemelen XBRL etiket kapsami sorunudur; "
                    f"bu ceyrek TTM'e de giriyor, dogrulanmadan guvenme.")

        gm_series = [num(x) for x in (series.get("gross_margin") or []) if num(x) is not None]
        gm_ttm = m.get("gross_margin")
        if len(gm_series) >= 4 and gm_ttm is not None:
            recent = sum(gm_series[-4:]) / 4
            if abs(recent - gm_ttm) > 8:
                warnings.append(
                    f"GRAFIK-METRIK CELISKISI: Brut marj grafiginin son 4 ceyrek "
                    f"ortalamasi %{recent:.1f} ama TTM brut marj %{gm_ttm:.1f}. "
                    f"Aradaki {abs(recent - gm_ttm):.1f} puanlik fark, kalemlerin "
                    f"farkli donemlerden geldigini gosterir.")
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
        "price_as_of": (f.price_history[-1][0] if f.price_history else None),
        # Yuzdeliklerin hangi havuza gore hesaplandigi. Tarama bitene kadar
        # havuz kucuk; 40'lik bir puan 50 sirketlik havuzda baska, 3.000'lik
        # havuzda baska sey demek.
        "percentile_pool": _pool_size(sector_table, sector),
        "market_cap_musd": _round(meta["market_cap_musd"], None, 1),
        "enterprise_value_musd": _round(meta["enterprise_value_musd"], None, 1),
        # Gunluk kosu fiyat degisince EV ve carpanlari BUNLARDAN yeniden
        # hesaplar. Eski carpani oranla olceklemek her gun biraz daha sapan
        # bir sayi birakirdi; TTM buyuklukleri gun icinde degismez.
        "shares_outstanding_m": _round(f.shares_outstanding, None, 4),
        # Metrik hucresiyle AYNI yuvarlama: ayni buyuklugun iki yerde
        # farkli gorunmesi (5,25 ve 5,3) denetimde celiski sayilir.
        "net_debt_musd": _round(m.get("net_debt"), "net_debt"),
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
        "calendar": {"next_earnings": next_earnings, "estimated": False},
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
        "overrides": list(getattr(f, "overrides_applied", None) or []),
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
    # Sirket yatirim harcamasini HIC raporlamiyorsa FCF = CFO dogrudur.
    # Ama BAZI ceyreklerde raporlayip bazilarinda raporlamiyorsa, eksik
    # ceyrekte cfo'yu FCF diye gostermek grafigi sisirir ve TTM'den koparir.
    reports_capex = any(num(q.capex) is not None for q in quarters)
    return {
        "quarters": [f"{q.fiscal_year}-{q.period_end[5:7]}" for q in quarters],
        "period_ends": [q.period_end for q in quarters],
        "revenue": [num(q.revenue) for q in quarters],
        "gross_margin": [_gm(q) for q in quarters],
        "fcf": [_quarter_fcf(q, reports_capex) for q in quarters],
        "share_count": [num(q.shares_diluted) for q in quarters],
        "basis": "quarterly",
    }


def _quarter_fcf(period, reports_capex: bool):
    """Ceyreklik serbest nakit akisi; eksik yatirim harcamasini 0 sayma."""
    cfo = num(period.cfo)
    if cfo is None:
        return None
    capex = num(period.capex)
    if capex is None:
        return cfo if not reports_capex else None
    return cfo - capex


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
def block_coverage(score_detail: dict | None) -> dict[str, float]:
    """Karttaki blok detaylarindan kapsama oranlarini geri okur.

    ``scoring.compute`` kapsamayi hesaplar ama toplam puanla birlikte
    saklamaz; yalnizca ``score_detail[blok]["coverage"]`` icinde durur.
    Puani yeniden hesaplayan her yol bunu tekrar vermek zorunda.
    """
    out: dict[str, float] = {}
    for block, detail in (score_detail or {}).items():
        if isinstance(detail, dict):
            cov = num(detail.get("coverage"))
            if cov is not None:
                out[block] = cov
    return out


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
        # KAPSAMA CARPANI KORUNMALI. Bu yol puani BASTAN hesapliyor; kapsama
        # verilmezse total_score her blogun carpanini 1,0 kabul eder ve
        # kartta 0,30 kapsamali bir kalite puani tam agirlikla geri doner.
        # YOU tam olarak boyle 1. siraya cikmisti.
        card["scores"] = scoring.total_score(
            {k: card["scores"].get(k) for k in
             ("value", "quality", "safety", "momentum", "earnings_quality")},
            catalyst=cat,
            coverage=block_coverage(card.get("score_detail")),
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


def low_coverage_blocks(card: dict) -> dict[str, list[str]]:
    """Kapsamasi dusuk bloklar ve o bloklarda HESAPLANAMAYAN alt metrikler.

    "Veri yetersiz" rozeti tek basina neyin eksik oldugunu soylemiyor;
    eksik metrigi bilmek veriyi duzeltmenin ilk adimi.
    """
    out: dict[str, list[str]] = {}
    for block, detail in (card.get("score_detail") or {}).items():
        if not isinstance(detail, dict) or not detail.get("low_coverage"):
            continue
        missing = [k for k, v in (detail.get("components") or {}).items()
                   if not isinstance(v, dict) or v.get("percentile") is None]
        out[block] = missing
    return out


def _pool_size(sector_table: dict | None, sector: str | None) -> dict:
    """Yuzdelik havuzunun buyuklugu: tum evren ve sirketin sektoru."""
    if not sector_table:
        return {"universe": 0, "sector": 0}
    def widest(block):
        return max((len(v) for v in (block or {}).values()), default=0)
    return {"universe": widest(sector_table.get("__ALL__")),
            "sector": widest(sector_table.get(sector))}


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
        # Kol fark etmeksizin HER satirda olan cekirdek metrikler. headline
        # kola gore degisiyor (Kol A'da buyume yok); karsilastirma ve Chat
        # ajani icin ortak bir set gerekiyordu.
        "core": {k: (m.get(k) or {}).get("value") for k in
                 ("rev_growth_ttm", "gross_margin", "fcf_yield_ev",
                  "piotroski_f", "roic", "net_debt_to_ebitda")},
        "price_as_of": card.get("price_as_of"),
        "percentile_pool": card.get("percentile_pool"),
        "low_coverage_blocks": low_coverage_blocks(card),
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
