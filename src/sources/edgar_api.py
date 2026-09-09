"""data.sec.gov — companyfacts, submissions, Form 4; XBRL -> Fundamentals.

Toplu veri (``edgar_bulk``) evren taramasi icindir. Bu modul TEK SIRKET
dogrulamasi ve kart uretimi icin kullanilir: companyfacts tum tarihsel
seriyi tek JSON'da verir, ceyreklik seriler ve grafikler buradan cikar.

SEC saniyede 10 istek siniri koyar ve User-Agent zorunludur.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from .. import config
from ..fundamentals import Fundamentals, Period
from ..util import read_json, sec_get

MILLION = 1e6

# Kapak sayfasi hisse sayisi, seyreltilmis ortalamanin bu oraninin altindaysa
# muhtemelen yalnizca tek hisse sinifini tasiyor demektir.
SHARE_COUNT_SANITY_RATIO = 0.70

TICKER_CACHE = config.CACHE_DIR / "company_tickers.json"
FACTS_CACHE_DIR = config.CACHE_DIR / "companyfacts"
FACTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Kavram -> XBRL etiket alternatifleri (oncelik sirasiyla)
# --------------------------------------------------------------------------
FLOW_TAGS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues", "SalesRevenueNet", "SalesRevenueServicesNet",
        "RevenueFromContractWithCustomerExcludingAssessedTaxMember",
        "RevenuesNetOfInterestExpense",
        "TotalRevenuesAndOtherIncome",
    ],
    "cost_of_revenue": [
        "CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfServices",
        "CostOfGoodsSold", "CostOfSales",
        "CostOfGoodsAndServicesSoldExcludingDepreciationDepletionAndAmortization",
    ],
    "gross_profit": ["GrossProfit"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "pretax_income": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic",
    ],
    "tax_expense": ["IncomeTaxExpenseBenefit"],
    "interest_expense": [
        "InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt",
    ],
    "sga": [
        "SellingGeneralAndAdministrativeExpense",
        "GeneralAndAdministrativeExpense",
    ],
    "rnd": ["ResearchAndDevelopmentExpense"],
    "dep_amort": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
        "DepreciationAndAmortization", "Depreciation",
    ],
    "cfo": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsForCapitalImprovements",
    ],
    "cfi": ["NetCashProvidedByUsedInInvestingActivities"],
    "cff": ["NetCashProvidedByUsedInFinancingActivities"],
    "sbc": ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"],
    "dividends_paid": ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends"],
}

STOCK_TAGS = {
    "assets": ["Assets"],
    "current_assets": ["AssetsCurrent"],
    "liabilities": ["Liabilities"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    "short_term_investments": [
        "ShortTermInvestments", "MarketableSecuritiesCurrent",
        "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
    ],
    "long_term_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "short_term_debt": ["LongTermDebtCurrent", "ShortTermBorrowings", "DebtCurrent"],
    "operating_lease_current": ["OperatingLeaseLiabilityCurrent"],
    "operating_lease_noncurrent": ["OperatingLeaseLiabilityNoncurrent"],
    "goodwill": ["Goodwill"],
    "intangibles": ["IntangibleAssetsNetExcludingGoodwill"],
    "retained_earnings": ["RetainedEarningsAccumulatedDeficit"],
    "receivables": ["AccountsReceivableNetCurrent", "ReceivablesNetCurrent"],
    "inventory": ["InventoryNet"],
    "ppe_net": ["PropertyPlantAndEquipmentNet"],
    "deferred_revenue": [
        "ContractWithCustomerLiabilityCurrent", "DeferredRevenueCurrent",
    ],
}

# Agirlikli ortalama hisse sayilari SURE bazlidir (start+end tasir), anlik
# degil. Stok olarak aranirsa hicbir zaman bulunmaz — seyrelme filtresi de
# sessizce hic calismaz.
SHARE_FLOW_TAGS = {
    "shares_diluted": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageNumberOfDilutedSharesOutstandingBasicAndDiluted",
    ],
    "shares_basic": [
        "WeightedAverageNumberOfSharesOutstandingBasic",
        "WeightedAverageNumberOfSharesOutstanding",
    ],
}

# 2 yilda vadesi gelen borc (vade duvari testi)
MATURITY_TAGS = [
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo",
]

# --------------------------------------------------------------------------
# Ticker -> CIK
# --------------------------------------------------------------------------
def ticker_map(*, refresh: bool = False) -> dict[str, dict]:
    """``{"AAPL": {"cik": 320193, "title": "Apple Inc."}}``"""
    if not refresh and TICKER_CACHE.exists():
        age = date.today() - date.fromtimestamp(TICKER_CACHE.stat().st_mtime)
        if age.days < 7:
            cached = read_json(TICKER_CACHE)
            if cached:
                return cached

    resp = sec_get(config.EDGAR["company_tickers_url"])
    raw = resp.json()
    out = {}
    for entry in raw.values():
        ticker = str(entry.get("ticker", "")).upper()
        if ticker:
            out[ticker] = {"cik": int(entry["cik_str"]), "title": entry.get("title", "")}
    TICKER_CACHE.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def cik_for(ticker: str) -> int | None:
    return (ticker_map().get(ticker.upper()) or {}).get("cik")


# --------------------------------------------------------------------------
# companyfacts
# --------------------------------------------------------------------------
def company_facts(cik: int, *, max_age_days: int = 3) -> dict | None:
    """companyfacts JSON. Diske onbelleklenir (dosya basina ~2-20 MB)."""
    path = FACTS_CACHE_DIR / f"CIK{cik:010d}.json"
    if path.exists():
        age = date.today() - date.fromtimestamp(path.stat().st_mtime)
        if age.days <= max_age_days:
            return read_json(path)

    url = config.EDGAR["companyfacts_url"].format(cik=cik)
    try:
        resp = sec_get(url)
    except Exception as exc:  # noqa: BLE001
        print(f"  [uyari] companyfacts CIK{cik}: {exc}")
        return read_json(path)  # bayat onbellek hic yoktan iyidir
    data = resp.json()
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def submissions(cik: int) -> dict | None:
    """Basvuru gecmisi — borsa, SIC, Form 4, IPO tarihi icin."""
    path = config.CACHE_DIR / "submissions" / f"CIK{cik:010d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        age = date.today() - date.fromtimestamp(path.stat().st_mtime)
        if age.days <= 3:
            return read_json(path)
    try:
        resp = sec_get(config.EDGAR["submissions_url"].format(cik=cik))
    except Exception as exc:  # noqa: BLE001
        print(f"  [uyari] submissions CIK{cik}: {exc}")
        return read_json(path)
    data = resp.json()
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


# --------------------------------------------------------------------------
# XBRL ayristirma
# --------------------------------------------------------------------------
def _facts_for_tag(facts: dict, tag: str) -> list[dict]:
    """Bir etiketin USD (veya shares) birimli tum kayitlari."""
    for ns in ("us-gaap", "ifrs-full", "dei"):
        block = facts.get("facts", {}).get(ns, {}).get(tag)
        if not block:
            continue
        for unit in ("USD", "shares", "USD/shares"):
            if unit in block.get("units", {}):
                return block["units"][unit]
    return []


def _duration_days(entry: dict) -> int | None:
    start, end = entry.get("start"), entry.get("end")
    if not start or not end:
        return None
    try:
        return (date.fromisoformat(end) - date.fromisoformat(start)).days
    except ValueError:
        return None


def _is_quarter(entry: dict) -> bool:
    d = _duration_days(entry)
    return d is not None and 80 <= d <= 100


def _is_annual(entry: dict) -> bool:
    d = _duration_days(entry)
    return d is not None and 340 <= d <= 380


def _pick_best(entries: list[dict]) -> dict | None:
    """Ayni donem icin birden fazla kayit varsa en son DOSYALANANI sec.

    Yeniden duzenlemeler (restatement) eskiyi gecersiz kilar.
    """
    if not entries:
        return None
    return max(entries, key=lambda e: (e.get("filed", ""), e.get("accn", "")))


def _collect_flow(facts: dict, tags: list[str], *, annual: bool) -> dict[str, float]:
    """{donem_sonu: deger} — ilk dolu etiket alternatifini kullanir."""
    out: dict[str, float] = {}
    for tag in tags:
        entries = _facts_for_tag(facts, tag)
        if not entries:
            continue
        bucket: dict[str, list[dict]] = {}
        for e in entries:
            ok = _is_annual(e) if annual else _is_quarter(e)
            if ok and e.get("val") is not None:
                bucket.setdefault(e["end"], []).append(e)
        for end, group in bucket.items():
            if end not in out:
                best = _pick_best(group)
                if best is not None:
                    out[end] = float(best["val"])
        if out:
            break
    return out


def _collect_stock(facts: dict, tags: list[str]) -> dict[str, float]:
    """{donem_sonu: deger} — anlik (instant) kalemler."""
    out: dict[str, float] = {}
    for tag in tags:
        entries = _facts_for_tag(facts, tag)
        if not entries:
            continue
        bucket: dict[str, list[dict]] = {}
        for e in entries:
            if e.get("start") is None and e.get("val") is not None:
                bucket.setdefault(e["end"], []).append(e)
        for end, group in bucket.items():
            if end not in out:
                best = _pick_best(group)
                if best is not None:
                    out[end] = float(best["val"])
        if out:
            break
    return out


def _shares_outstanding(facts: dict) -> tuple[float | None, str]:
    """Tedavuldeki hisse sayisi (milyon) ve hangi yontemle bulundugu.

    CIFT KONTROL GEREKIYOR: cok sinifli sirketlerde (Class A/B) kapak sayfasi
    her sinifi AYRI satirda, ``ClassOfStockAxis`` boyutuyla raporlar.
    companyfacts boyutsuz degerleri tasidigi icin bu sirketlerde etiket ya
    hic yok, ya da yalnizca TEK SINIF gorunuyor. Tek sinifi toplam sanmak
    piyasa degerini kati kati kucuk gosterir (orn. MNTN: 16M yerine 60M+).

    Bu yuzden bulunan deger, seyreltilmis agirlikli ortalama hisse sayisiyla
    karsilastirilir; belirgin dusukse o kullanilir.
    """
    cover = _cover_page_shares(facts)
    diluted = _latest_diluted_shares(facts)

    if cover is None:
        if diluted is None:
            return None, "yok"
        return diluted, "seyreltilmis_agirlikli_ortalama"

    if diluted is not None and cover < diluted * SHARE_COUNT_SANITY_RATIO:
        # Kapak sayfasi seyreltilmisin belirgin altinda -> muhtemelen tek sinif
        return diluted, "seyreltilmis_agirlikli_ortalama (kapak tek sinif gorunuyor)"

    return cover, "kapak_sayfasi"


def _cover_page_shares(facts: dict) -> float | None:
    """dei:EntityCommonStockSharesOutstanding — ayni basvurudaki siniflari topla."""
    entries = _facts_for_tag(facts, "EntityCommonStockSharesOutstanding")
    if not entries:
        entries = _facts_for_tag(facts, "CommonStockSharesOutstanding")
    if not entries:
        return None

    by_accn: dict[str, list[dict]] = {}
    for e in entries:
        if e.get("val") is None:
            continue
        by_accn.setdefault(e.get("accn", ""), []).append(e)
    if not by_accn:
        return None

    latest_accn = max(
        by_accn,
        key=lambda a: max((e.get("end", "") or "", e.get("filed", "") or "")
                          for e in by_accn[a]),
    )
    # Ayni kapak sayfasindaki farkli siniflar toplanir; ayni sinifin tekrari atlanir
    seen: set[tuple] = set()
    total = 0.0
    for e in by_accn[latest_accn]:
        key = (e.get("end"), e.get("val"))
        if key in seen:
            continue
        seen.add(key)
        total += float(e["val"])
    return total / MILLION if total > 0 else None


def _latest_diluted_shares(facts: dict) -> float | None:
    """En guncel donemin seyreltilmis agirlikli ortalama hisse sayisi.

    Tum siniflari kapsar, bu yuzden cok sinifli sirketlerde kapak sayfasindan
    daha guvenilirdir.
    """
    for tag in SHARE_FLOW_TAGS["shares_diluted"] + SHARE_FLOW_TAGS["shares_basic"]:
        entries = [e for e in _facts_for_tag(facts, tag)
                   if e.get("val") and (_is_quarter(e) or _is_annual(e))]
        if not entries:
            continue
        best = max(entries, key=lambda e: (e.get("end", ""), e.get("filed", "")))
        return float(best["val"]) / MILLION
    return None


def _derive_q4(annual: dict[str, float], quarterly: dict[str, float],
               fy_ends: dict[str, list[str]]) -> None:
    """Q4'u tureterek ``quarterly`` sozlugune ekler.

    Cogu sirket Q4'u ayri raporlamaz; 10-K yillik toplami verir. Q4 =
    yillik - (Q1 + Q2 + Q3). Bu olmadan grafiklerde her yil bir delik olur
    ve TTM hesaplari kayar.
    """
    for fy_end, quarters in fy_ends.items():
        if fy_end in quarterly or fy_end not in annual:
            continue
        parts = [quarterly.get(q) for q in quarters]
        if len(parts) != 3 or any(p is None for p in parts):
            continue
        quarterly[fy_end] = annual[fy_end] - sum(parts)  # type: ignore[arg-type]


def _fiscal_quarter_ends(facts: dict) -> dict[str, list[str]]:
    """Her mali yil sonu icin o yilin ilk uc ceyrek sonunu bulur."""
    revenue_entries: list[dict] = []
    for tag in FLOW_TAGS["revenue"]:
        revenue_entries = _facts_for_tag(facts, tag)
        if revenue_entries:
            break

    annual_ends = sorted({e["end"] for e in revenue_entries if _is_annual(e)})
    quarter_ends = sorted({e["end"] for e in revenue_entries if _is_quarter(e)})

    out: dict[str, list[str]] = {}
    for fy_end in annual_ends:
        try:
            fy_dt = date.fromisoformat(fy_end)
        except ValueError:
            continue
        window_start = fy_dt - timedelta(days=370)
        inner = [q for q in quarter_ends
                 if window_start < date.fromisoformat(q) < fy_dt]
        if len(inner) >= 3:
            out[fy_end] = sorted(inner)[-3:]
    return out


def fundamentals_from_facts(facts: dict, ticker: str, *,
                            cik: int | None = None,
                            meta: dict | None = None) -> Fundamentals:
    """companyfacts JSON -> Fundamentals (milyon USD)."""
    meta = meta or {}
    f = Fundamentals(
        ticker=ticker.upper(),
        cik=cik or facts.get("cik"),
        name=meta.get("name") or facts.get("entityName", ""),
        sic=meta.get("sic"),
        exchange=meta.get("exchange", ""),
        fiscal_year_end=meta.get("fiscal_year_end"),
        ipo_date=meta.get("ipo_date"),
    )

    fy_map = _fiscal_quarter_ends(facts)

    # --- akis kalemleri (hisse sayilari dahil: onlar da sure bazlidir) ---
    q_flows: dict[str, dict[str, float]] = {}
    a_flows: dict[str, dict[str, float]] = {}
    for field, tags in {**FLOW_TAGS, **SHARE_FLOW_TAGS}.items():
        annual = _collect_flow(facts, tags, annual=True)
        quarterly = _collect_flow(facts, tags, annual=False)
        # Hisse sayilari agirlikli ORTALAMADIR; Q4 = yil - (Q1+Q2+Q3) formulu
        # onlar icin anlamsiz sonuc uretir.
        if field not in SHARE_FLOW_TAGS:
            _derive_q4(annual, quarterly, fy_map)
        q_flows[field] = quarterly
        a_flows[field] = annual

    # --- stok kalemleri ---
    stocks: dict[str, dict[str, float]] = {
        field: _collect_stock(facts, tags) for field, tags in STOCK_TAGS.items()
    }

    # 2 yilda vadesi gelen borc = 12 ay + 2. yil
    maturity: dict[str, float] = {}
    for tag in MATURITY_TAGS:
        for end, val in _collect_stock(facts, [tag]).items():
            maturity[end] = maturity.get(end, 0.0) + val

    def _build(end: str, flows: dict[str, dict[str, float]], ptype: str) -> Period:
        p = Period(period_end=end, period_type=ptype)
        for field, series in flows.items():
            val = series.get(end)
            if val is not None:
                setattr(p, field, val / MILLION)
        # capex pozitif saklanir (SEC negatif odeme olarak verebilir)
        if p.capex is not None:
            p.capex = abs(p.capex)
        if p.interest_expense is not None:
            p.interest_expense = abs(p.interest_expense)
        # stok kalemleri: bu donem sonuna en yakin bilanco
        for field, series in stocks.items():
            val = series.get(end)
            if val is not None:
                setattr(p, field, val / MILLION)
        if end in maturity:
            p.debt_due_2y = maturity[end] / MILLION
        try:
            p.fiscal_year = date.fromisoformat(end).year
        except ValueError:
            pass
        return p

    q_ends = sorted({e for series in q_flows.values() for e in series})
    a_ends = sorted({e for series in a_flows.values() for e in series})

    f.quarters = [_build(e, q_flows, "Q") for e in q_ends]
    f.annuals = [_build(e, a_flows, "FY") for e in a_ends]

    # Bilanco tarihi ceyrek sonu ile birebir tutmayabilir; en yakini ata
    _backfill_balance_sheet(f.quarters, stocks, maturity)
    _backfill_balance_sheet(f.annuals, stocks, maturity)

    f.shares_outstanding, share_source = _shares_outstanding(facts)
    f.sources["fundamentals"] = "sec_companyfacts"
    f.sources["shares"] = share_source
    return f


def _backfill_balance_sheet(periods: list[Period], stocks: dict[str, dict[str, float]],
                            maturity: dict[str, float], tolerance_days: int = 10) -> None:
    """Bilanco tarihi donem sonuyla tam eslesmezse en yakin tarihi kullan."""
    for p in periods:
        try:
            target = date.fromisoformat(p.period_end)
        except ValueError:
            continue
        for field, series in stocks.items():
            if getattr(p, field) is not None or not series:
                continue
            best_end, best_gap = None, None
            for end in series:
                try:
                    gap = abs((date.fromisoformat(end) - target).days)
                except ValueError:
                    continue
                if gap <= tolerance_days and (best_gap is None or gap < best_gap):
                    best_end, best_gap = end, gap
            if best_end is not None:
                setattr(p, field, series[best_end] / MILLION)
        if p.debt_due_2y is None and maturity:
            for end, val in maturity.items():
                try:
                    if abs((date.fromisoformat(end) - target).days) <= tolerance_days:
                        p.debt_due_2y = val / MILLION
                        break
                except ValueError:
                    continue


def load(ticker: str, *, cik: int | None = None) -> Fundamentals | None:
    """Bir sembol icin tam Fundamentals kur (meta veri dahil)."""
    cik = cik or cik_for(ticker)
    if cik is None:
        print(f"  [uyari] {ticker}: CIK bulunamadi")
        return None

    facts = company_facts(cik)
    if not facts:
        return None

    sub = submissions(cik) or {}
    meta = {
        "name": sub.get("name") or facts.get("entityName", ""),
        "sic": _to_int(sub.get("sic")),
        "exchange": (sub.get("exchanges") or [""])[0],
        "fiscal_year_end": sub.get("fiscalYearEnd"),
        "ipo_date": _first_filing_date(sub),
    }
    return fundamentals_from_facts(facts, ticker, cik=cik, meta=meta)


def _to_int(x) -> int | None:
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def _first_filing_date(sub: dict) -> str | None:
    """Ilk 10-K/S-1 tarihi — IPO kilit suresi testi icin yaklasik gosterge."""
    recent = (sub.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    dates = recent.get("filingDate") or []
    candidates = [d for form, d in zip(forms, dates) if form in ("S-1", "424B4", "10-K")]
    return min(candidates) if candidates else None


# --------------------------------------------------------------------------
# Form 4 — iceriden alim
# --------------------------------------------------------------------------
def insider_activity(cik: int, *, days: int = 180) -> dict:
    """Son ``days`` gunde dosyalanan Form 4 sayisi.

    NOT: Bu yalnizca DOSYA SAYISIDIR, tutar degil. Tutar icin her Form 4'un
    XML'ini ayri cekmek gerekir; ucretsiz kotada evren capinda pahali.
    Kartta "sinyal" olarak gosterilir, karar girdisi degildir.
    """
    sub = submissions(cik)
    if not sub:
        return {"form4_count": None, "last_form4": None, "window_days": days}
    recent = (sub.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    dates = recent.get("filingDate") or []
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    hits = [d for form, d in zip(forms, dates) if form == "4" and d >= cutoff]
    return {
        "form4_count": len(hits),
        "last_form4": max(hits) if hits else None,
        "window_days": days,
    }
