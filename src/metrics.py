"""Degerleme, buyume, kalite ve saglamlik metrikleri.

Girdi: ``Fundamentals``. Cikti: ``{metrik_adi: deger}`` sozlugu + ``meta``
(roic_method gibi hesap kararlari) + ``flags`` (tek seferlik kalem, organik
buyume suphesi).

Tum degerler ``None`` olabilir. Hicbir fonksiyon istisna firlatmaz.
Parasal birim: milyon USD. Oranlar carpan, yuzdeler 0-100 olcegindedir.
"""

from __future__ import annotations

from . import config
from .config import ANOMALY, METRIC_PARAMS
from .fundamentals import Fundamentals, Period
from .util import add, cagr_pct, div, growth_pct, num, pct, sub

P = METRIC_PARAMS


# --------------------------------------------------------------------------
# Isletme degeri
# --------------------------------------------------------------------------
def enterprise_value(market_cap: float | None, period: Period) -> float | None:
    """EV = piyasa degeri + finansal borc - nakit ve kisa vadeli yatirimlar.

    Kiralama yukumlulukleri KASITLI OLARAK haric. Operasyonel kiralamayi borca
    eklemek yazilim/hizmet sirketlerini sistematik olarak pahali gosterir;
    ayri kolonda (``lease_liabilities``) saklanir.
    """
    mc = num(market_cap)
    if mc is None:
        return None
    debt = num(period.financial_debt) or 0.0
    cash = num(period.cash_and_investments) or 0.0
    return mc + debt - cash


def nopat(period: Period) -> tuple[float | None, float]:
    """Vergi sonrasi net faaliyet kari ve kullanilan vergi orani.

    Efektif vergi orani makul araligin disindaysa (zarar eden sirketlerde
    sik gorulur) varsayilan orana duser.
    """
    ebit = num(period.operating_income)
    if ebit is None:
        return None, P["default_tax_rate"]
    rate = period.effective_tax_rate
    if rate is None or not (P["tax_rate_sane_min"] <= rate <= P["tax_rate_sane_max"]):
        rate = P["default_tax_rate"]
    return ebit * (1.0 - rate), rate


def roic(period: Period) -> tuple[float | None, str]:
    """ROIC ve kullanilan yontem.

    (a) NOPAT / (ozkaynak + finansal borc - nakit)
    (b) NOPAT / net isletme varliklari

    Ozkaynak negatifse (agresif geri alim, orn. Dropbox) (a) anlamsizdir —
    payda kuculur veya negatife doner, ROIC sahte biçimde patlar. Bu durumda
    (b) kullanilir.
    """
    npt, _ = nopat(period)
    if npt is None:
        return None, "none"

    equity = num(period.equity)
    debt = num(period.financial_debt) or 0.0
    cash = num(period.cash_and_investments) or 0.0

    if equity is not None and equity > 0:
        invested = equity + debt - cash
        if invested > 0:
            return pct(npt, invested), "a"

    # (b) net isletme varliklari = isletme varliklari - isletme yukumlulukleri
    assets = num(period.assets)
    liabilities = num(period.liabilities)
    if assets is None:
        return None, "none"
    operating_assets = assets - cash
    operating_liabilities = None
    if liabilities is not None:
        operating_liabilities = liabilities - debt
    noa = operating_assets - (operating_liabilities or 0.0)
    if noa is None or noa <= 0:
        return None, "b"
    return pct(npt, noa), "b"


# --------------------------------------------------------------------------
# Momentum — fiyat serisinden
# --------------------------------------------------------------------------
def _return_over(history: list[tuple[str, float]], days: int) -> float | None:
    if not history or len(history) <= days:
        return None
    last = num(history[-1][1])
    prior = num(history[-1 - days][1])
    if last is None or prior is None or prior <= 0:
        return None
    return (last / prior - 1.0) * 100.0


def return_over(history: list[tuple[str, float]], days: int) -> float | None:
    """Belirtilen islem gunu kadar geriye gore yuzde getiri (public arayuz)."""
    return _return_over(history, days)


def momentum(f: Fundamentals, benchmark: list[tuple[str, float]] | None = None) -> dict:
    """6/12 aylik getiri, Nasdaq 100'e gore goreli guc, zirveden uzaklik."""
    hist = f.price_history
    r3 = _return_over(hist, P["window_3m_days"])
    r6 = _return_over(hist, P["window_6m_days"])
    r12 = _return_over(hist, P["window_12m_days"])

    b3 = _return_over(benchmark or [], P["window_3m_days"])
    b6 = _return_over(benchmark or [], P["window_6m_days"])
    b12 = _return_over(benchmark or [], P["window_12m_days"])

    high = num(f.high_52w)
    if high is None and len(hist) >= 2:
        high = max(v for _, v in hist[-P["window_52w_days"]:])
    price = num(f.price)
    off_high = None
    if high is not None and price is not None and high > 0:
        off_high = (1.0 - price / high) * 100.0

    return {
        "return_3m": r3,
        "return_6m": r6,
        "return_12m": r12,
        "rel_strength_3m": sub(r3, b3),
        "rel_strength_6m": sub(r6, b6),
        "rel_strength_12m": sub(r12, b12),
        "pct_off_52w_high": off_high,
    }


# --------------------------------------------------------------------------
# Ana hesap
# --------------------------------------------------------------------------
def compute(f: Fundamentals, benchmark: list[tuple[str, float]] | None = None) -> dict:
    """Bir sirketin tum metriklerini hesaplar.

    Returns:
        ``{"metrics": {...}, "meta": {...}, "flags": {...}, "series": {...}}``
    """
    cur = f.ttm_period()
    prev = f.ttm_period(offset=4)
    latest = f.latest_period() or cur

    mcap = f.market_cap()
    ev = enterprise_value(mcap, latest)

    revenue = num(cur.revenue)
    gross_profit = cur.computed_gross_profit
    ebit = num(cur.operating_income)
    ebitda = cur.ebitda
    net_income = num(cur.net_income)
    cfo = num(cur.cfo)
    fcf = cur.fcf
    sbc = num(cur.sbc)

    m: dict[str, float | None] = {}

    # --- Degerleme carpanlari (payda pozitif degilse anlamsiz) ---
    m["ev_ebit"] = div(ev, ebit) if (ebit or 0) > 0 else None
    m["ev_ebitda"] = div(ev, ebitda) if (ebitda or 0) > 0 else None
    m["ev_gross_profit"] = div(ev, gross_profit) if (gross_profit or 0) > 0 else None
    m["ev_sales"] = div(ev, revenue) if (revenue or 0) > 0 else None
    m["fcf_yield_ev"] = pct(fcf, ev) if (ev or 0) > 0 else None
    m["fcf_yield_mcap"] = pct(fcf, mcap) if (mcap or 0) > 0 else None
    m["pe"] = div(mcap, net_income) if (net_income or 0) > 0 else None
    m["earnings_yield"] = pct(ebit, ev) if (ev or 0) > 0 else None

    # --- Buyume ---
    prev_revenue = num(prev.revenue)
    m["rev_growth_ttm"] = growth_pct(revenue, prev_revenue)

    ann = f.sorted_annuals()
    yrs = P["cagr_years"]
    if len(ann) > yrs:
        m["rev_cagr_3y"] = cagr_pct(ann[-1].revenue, ann[-1 - yrs].revenue, yrs)
    elif len(ann) >= 2:
        span = len(ann) - 1
        m["rev_cagr_3y"] = cagr_pct(ann[-1].revenue, ann[0].revenue, span)
    else:
        m["rev_cagr_3y"] = m["rev_growth_ttm"]

    m["peg"] = div(m["pe"], m["rev_growth_ttm"]) if (m["rev_growth_ttm"] or 0) > 0 else None

    # --- Marjlar ---
    m["gross_margin"] = pct(gross_profit, revenue)
    m["operating_margin"] = pct(ebit, revenue)
    m["fcf_margin"] = pct(fcf, revenue)
    m["ebitda_margin"] = pct(ebitda, revenue)

    back = P["margin_change_years"]
    old = f.latest_annual(back)
    if old is not None:
        m["gross_margin_change_3y"] = sub(m["gross_margin"],
                                          pct(old.computed_gross_profit, old.revenue))
        m["operating_margin_change_3y"] = sub(m["operating_margin"],
                                              pct(old.operating_income, old.revenue))
        m["fcf_margin_change_3y"] = sub(m["fcf_margin"], pct(old.fcf, old.revenue))
    else:
        m["gross_margin_change_3y"] = None
        m["operating_margin_change_3y"] = None
        m["fcf_margin_change_3y"] = None

    # --- Kalite ---
    roic_value, roic_method = roic(cur)
    m["roic"] = roic_value
    m["gross_profitability"] = div(gross_profit, latest.assets)
    # Net kar sifira yakinken CFO/NK orani patlar (KVYO'da 40,6 cikiyordu).
    # Oran "muhtesem nakit donusumu" degil, "payda sifira yakin" demektir.
    _ni_floor = (revenue or 0) * ANOMALY["cash_conversion_min_net_income_share"]
    m["cash_conversion"] = (div(cfo, net_income)
                            if (net_income or 0) > max(0.0, _ni_floor) else None)
    m["sbc_to_revenue"] = pct(sbc, revenue)
    m["sbc_to_fcf"] = div(sbc, fcf) if (fcf or 0) > 0 else None

    prev_shares = num(prev.shares_diluted)
    cur_shares = num(cur.shares_diluted)
    m["share_count_change_1y"] = growth_pct(cur_shares, prev_shares)

    # --- 40 Kurali (iki varyant; fark buyuk olcude SBC'dir) ---
    g = m["rev_growth_ttm"]
    m["rule_of_40"] = add(g, m["fcf_margin"]) if g is not None and m["fcf_margin"] is not None else None
    m["rule_of_40_ebitda"] = add(g, m["ebitda_margin"]) if g is not None and m["ebitda_margin"] is not None else None
    m["rule_of_40_gap"] = sub(m["rule_of_40_ebitda"], m["rule_of_40"])

    # --- Saglamlik ---
    # EV hesabi eksik borcu 0 sayiyor (borc etiketi olmayan sirketin borcu
    # yoktur). net_debt de AYNI kurali izlemeli; aksi halde EV hesaplanip
    # net borc bos kalir ve iki alan birbiriyle celisir.
    cash_known = num(latest.cash_and_investments)
    debt_known = num(latest.financial_debt)
    if cash_known is None and debt_known is None:
        net_debt = None
    else:
        net_debt = (debt_known or 0.0) - (cash_known or 0.0)
    m["net_debt"] = net_debt
    m["net_debt_to_ebitda"] = div(net_debt, ebitda) if (ebitda or 0) > 0 else (
        0.0 if (net_debt is not None and net_debt <= 0) else None)
    # BORCSUZ SIRKETI CEZALANDIRMA: faiz gideri yoksa metrik "veri yok" degil,
    # "sonsuz derecede rahat" demektir. Bos birakilirsa evrenin en guvenli
    # sirketleri saglamlik puanindan pay alamiyor — bu tersine bir yanlilik.
    interest = num(cur.interest_expense)
    if interest not in (None, 0):
        m["interest_coverage"] = div(ebit, abs(interest))
    elif (num(latest.financial_debt) or 0) == 0:
        m["interest_coverage"] = config.SCORE_CAPS["interest_coverage"][1]
    else:
        m["interest_coverage"] = None
    m["current_ratio"] = div(latest.current_assets, latest.current_liabilities)
    m["maturity_wall_2y"] = div(latest.debt_due_2y, latest.cash_and_investments)
    m["lease_liabilities"] = num(latest.lease_liabilities)

    # --- Bayraklar ---
    flags = {
        "one_off_earnings": _one_off_earnings(cur),
        "rev_growth_organic_suspect": _organic_suspect(f, m, mcap),
        "z_unreliable": (num(latest.equity) is not None and num(latest.equity) <= 0),
    }

    meta = {
        "roic_method": roic_method,
        "market_cap_musd": mcap,
        "enterprise_value_musd": ev,
        "price": num(f.price),
        "revenue_ttm_musd": revenue,
        "fcf_ttm_musd": fcf,
        "ebit_ttm_musd": ebit,
        "ebitda_ttm_musd": ebitda,
        "net_income_ttm_musd": net_income,
        "gross_profit_ttm_musd": gross_profit,
        "effective_tax_rate": cur.effective_tax_rate,
        "period_end": cur.period_end,
        # DURUST OLSUN: "ceyreklik TTM" derken bazi kalemler yillik tablodan
        # gelmis olabilir. Etiket yalnizca CEKIRDEK kalemlere bakar; ikincil
        # bir kalemin dusmesi etiketi degistirmez ama listede gorunur.
        "data_basis": ("annual" if not f.has_quarterly(4)
                       else "mixed" if _core_fell_back(cur)
                       else "quarterly_ttm"),
        "annual_fallback_fields": list(getattr(cur, "annual_fallback_fields", ())),
    }

    m.update(momentum(f, benchmark))

    return {"metrics": m, "meta": meta, "flags": flags}


# --------------------------------------------------------------------------
# Anomali tespitleri
# --------------------------------------------------------------------------
def _core_fell_back(period: Period) -> bool:
    """Kartin baslik sayilarini besleyen bir kalem yillik tabloya dustu mu?"""
    from .fundamentals import CORE_FLOW_FIELDS
    fell = set(getattr(period, "annual_fallback_fields", ()))
    return bool(fell & set(CORE_FLOW_FIELDS))


def _one_off_earnings(p: Period) -> bool:
    """Tek seferlik kalem suphesi (LYFT tipi: F/K 2 ama is degismedi).

    Iki tetikleyici: net kar / EBIT orani asiri yuksek (vergi varligi kaydi,
    dava tazminati, elden cikarma kari) veya efektif vergi orani negatif.
    """
    ebit = num(p.operating_income)
    ni = num(p.net_income)
    if ebit is not None and ni is not None and ebit > 0:
        if ni / ebit > ANOMALY["net_income_to_ebit_ratio_max"]:
            return True
    if ANOMALY["negative_tax_rate_flag"]:
        rate = p.effective_tax_rate
        if rate is not None and rate < 0:
            return True
    return False


def _organic_suspect(f: Fundamentals, m: dict, mcap: float | None) -> bool:
    """Satin alma kaynakli buyume suphesi (CPAY/GPN/NTAP tipi).

    Bu olcekte %20+ ceyreklik buyume organik olamaz. Ikinci sinyal serefiyenin
    yillik %15'ten fazla artmasidir — devralma bilancoda serefiye birakir.
    """
    growth = m.get("rev_growth_ttm")
    if (growth is not None and mcap is not None
            and growth > ANOMALY["organic_suspect_growth_pct"]
            and mcap > ANOMALY["organic_suspect_market_cap_musd"]):
        return True

    ann = f.sorted_annuals()
    if len(ann) >= 2:
        gw_now = num(ann[-1].goodwill)
        gw_prev = num(ann[-2].goodwill)
        gw_growth = growth_pct(gw_now, gw_prev)
        if gw_growth is not None and gw_growth > ANOMALY["organic_suspect_goodwill_growth_pct"]:
            return True
    return False


def track_for(m: dict, stage3_op_margin: float) -> str:
    """Kol A mi Kol B mi? EBIT <= 0 veya faaliyet marji dusukse Kol B."""
    op_margin = m.get("operating_margin")
    if op_margin is None:
        return "B"
    return "B" if op_margin < stage3_op_margin else "A"
