"""Akademik skor modelleri ve ters DCF.

Piotroski F  — temel saglik (0-9)
Altman Z''   — iflas riski (imalat disi versiyon)
Beneish M    — kazanc manipulasyonu olasiligi
Sloan        — tahakkuk orani
Ters DCF     — bugunku fiyatin varsaydigi buyume

Her fonksiyon eksik veriye dayanikli: hesaplanamayan alt test 0 puan degil,
"veri yok" olarak raporlanir; boylece 9 uzerinden 3 sadece veri eksikliginden
kaynaklaniyorsa bunu gorebiliriz.
"""

from __future__ import annotations

from scipy.optimize import brentq

from .config import REVERSE_DCF
from .fundamentals import Fundamentals, Period
from .util import div, num


# --------------------------------------------------------------------------
# Piotroski F-Score
# --------------------------------------------------------------------------
PIOTROSKI_TESTS = (
    ("roa_positive", "ROA > 0"),
    ("cfo_positive", "Isletme nakit akisi > 0"),
    ("roa_improving", "ROA artiyor"),
    ("accruals", "CFO > net kar"),
    ("leverage_down", "Uzun vadeli borc/varlik dusuyor"),
    ("liquidity_up", "Cari oran artiyor"),
    ("no_dilution", "Hisse ihraci yok"),
    ("margin_up", "Brut marj artiyor"),
    ("turnover_up", "Varlik devir hizi artiyor"),
)


def piotroski_f(cur: Period, prev: Period) -> dict:
    """9 maddelik F-Score.

    Returns:
        ``{"score": int|None, "max_possible": int, "tests": {ad: True|False|None}}``
        Test degeri ``None`` ise veri eksik demektir.
    """
    t: dict[str, bool | None] = {}

    assets_c, assets_p = num(cur.assets), num(prev.assets)
    ni_c, ni_p = num(cur.net_income), num(prev.net_income)
    cfo_c = num(cur.cfo)

    roa_c = div(ni_c, assets_c)
    roa_p = div(ni_p, assets_p)

    t["roa_positive"] = None if roa_c is None else roa_c > 0
    t["cfo_positive"] = None if cfo_c is None else cfo_c > 0
    t["roa_improving"] = None if (roa_c is None or roa_p is None) else roa_c > roa_p
    t["accruals"] = None if (cfo_c is None or ni_c is None) else cfo_c > ni_c

    # 5) uzun vadeli borc / varlik dusuyor mu
    lev_c = div(num(cur.long_term_debt), assets_c)
    lev_p = div(num(prev.long_term_debt), assets_p)
    if num(cur.long_term_debt) is None or num(prev.long_term_debt) is None:
        t["leverage_down"] = None
    else:
        lev_c = lev_c if lev_c is not None else 0.0
        lev_p = lev_p if lev_p is not None else 0.0
        t["leverage_down"] = lev_c < lev_p

    # 6) cari oran artiyor mu
    cr_c = div(cur.current_assets, cur.current_liabilities)
    cr_p = div(prev.current_assets, prev.current_liabilities)
    t["liquidity_up"] = None if (cr_c is None or cr_p is None) else cr_c > cr_p

    # 7) yeni hisse ihraci yok (seyreltilmis hisse sayisi artmadi)
    sh_c, sh_p = num(cur.shares_diluted), num(prev.shares_diluted)
    t["no_dilution"] = None if (sh_c is None or sh_p is None) else sh_c <= sh_p

    # 8) brut marj artiyor mu
    gm_c = div(cur.computed_gross_profit, cur.revenue)
    gm_p = div(prev.computed_gross_profit, prev.revenue)
    t["margin_up"] = None if (gm_c is None or gm_p is None) else gm_c > gm_p

    # 9) varlik devir hizi artiyor mu
    to_c = div(cur.revenue, assets_c)
    to_p = div(prev.revenue, assets_p)
    t["turnover_up"] = None if (to_c is None or to_p is None) else to_c > to_p

    known = [v for v in t.values() if v is not None]
    score = sum(1 for v in known if v) if known else None
    return {"score": score, "max_possible": len(known), "tests": t}


# --------------------------------------------------------------------------
# Altman Z'' (imalat disi / gelismekte olan piyasa versiyonu)
# --------------------------------------------------------------------------
def altman_z(p: Period) -> dict:
    """Z'' = 3.25 + 6.56A + 3.26B + 6.72C + 1.05D

    A = isletme sermayesi / toplam varlik
    B = dagitilmamis kar / toplam varlik
    C = EBIT / toplam varlik
    D = ozkaynak / toplam yukumluluk

    Ozkaynak negatifse D bileseni modeli bozar; ``unreliable`` True doner ve
    yerine faiz karsilama + FCF/toplam borc bakilmalidir.
    """
    assets = num(p.assets)
    if assets is None or assets <= 0:
        return {"z": None, "unreliable": True, "components": {},
                "reason": "toplam varlik yok"}

    wc = None
    ca, cl = num(p.current_assets), num(p.current_liabilities)
    if ca is not None and cl is not None:
        wc = ca - cl

    a = div(wc, assets)
    b = div(num(p.retained_earnings), assets)
    c = div(num(p.operating_income), assets)

    equity = num(p.equity)
    liabilities = num(p.liabilities)
    d = div(equity, liabilities)

    unreliable = equity is not None and equity <= 0
    components = {"A": a, "B": b, "C": c, "D": d}

    if any(x is None for x in (a, b, c, d)):
        return {"z": None, "unreliable": True, "components": components,
                "reason": "bilesen eksik"}

    z = 3.25 + 6.56 * a + 3.26 * b + 6.72 * c + 1.05 * d
    return {
        "z": z,
        "unreliable": unreliable,
        "components": components,
        "reason": "ozkaynak negatif — Z'' anlamsiz" if unreliable else None,
    }


def solvency_fallback(p: Period) -> dict:
    """Z'' guvenilmez oldugunda kullanilan yedek olculer."""
    ebit = num(p.operating_income)
    interest = num(p.interest_expense)
    debt = num(p.financial_debt)
    return {
        "interest_coverage": div(ebit, abs(interest)) if interest not in (None, 0) else None,
        "fcf_to_total_debt": div(p.fcf, debt) if (debt or 0) > 0 else None,
    }


# --------------------------------------------------------------------------
# Beneish M-Score
# --------------------------------------------------------------------------
BENEISH_COEF = {
    "const": -4.84, "DSRI": 0.92, "GMI": 0.528, "AQI": 0.404, "SGI": 0.892,
    "DEPI": 0.115, "SGAI": -0.172, "TATA": 4.679, "LVGI": -0.327,
}


def beneish_m(cur: Period, prev: Period) -> dict:
    """M = -4.84 + 0.92 DSRI + 0.528 GMI + 0.404 AQI + 0.892 SGI
             + 0.115 DEPI - 0.172 SGAI + 4.679 TATA - 0.327 LVGI

    -1.78 ustu "muhtemel manipulator". Hizli buyuyen saglikli sirketlerde
    yanlis alarm verebilir (SGI ve DSRI yukselir) — tek basina eleme sebebi
    olarak degil, Asama 2'de diger tuzak testleriyle birlikte okunmali.
    """
    v: dict[str, float | None] = {}

    rev_c, rev_p = num(cur.revenue), num(prev.revenue)

    # DSRI — alacaklarin hasilata orani
    dsr_c = div(cur.receivables, rev_c)
    dsr_p = div(prev.receivables, rev_p)
    v["DSRI"] = div(dsr_c, dsr_p)

    # GMI — brut marj bozulmasi (>1 kotulesme)
    gm_c = div(cur.computed_gross_profit, rev_c)
    gm_p = div(prev.computed_gross_profit, rev_p)
    v["GMI"] = div(gm_p, gm_c)

    # AQI — maddi olmayan varlik agirliginin artisi
    def _soft(p: Period) -> float | None:
        assets = num(p.assets)
        ca, ppe = num(p.current_assets), num(p.ppe_net)
        if assets is None or assets == 0 or ca is None or ppe is None:
            return None
        return 1.0 - (ca + ppe) / assets

    v["AQI"] = div(_soft(cur), _soft(prev))

    # SGI — satis buyumesi
    v["SGI"] = div(rev_c, rev_p)

    # DEPI — amortisman oraninin yavaslamasi
    def _dep_rate(p: Period) -> float | None:
        dep, ppe = num(p.dep_amort), num(p.ppe_net)
        if dep is None or ppe is None or (dep + ppe) == 0:
            return None
        return dep / (dep + ppe)

    v["DEPI"] = div(_dep_rate(prev), _dep_rate(cur))

    # SGAI — genel yonetim giderlerinin hasilata orani
    sga_c = div(cur.sga, rev_c)
    sga_p = div(prev.sga, rev_p)
    v["SGAI"] = div(sga_c, sga_p)

    # TATA — toplam tahakkuklar
    ni, cfo, assets = num(cur.net_income), num(cur.cfo), num(cur.assets)
    v["TATA"] = None if (ni is None or cfo is None or not assets) else (ni - cfo) / assets

    # LVGI — kaldirac artisi
    def _lev(p: Period) -> float | None:
        assets = num(p.assets)
        cl, ltd = num(p.current_liabilities), num(p.long_term_debt)
        if assets is None or assets == 0 or cl is None:
            return None
        return (cl + (ltd or 0.0)) / assets

    v["LVGI"] = div(_lev(cur), _lev(prev))

    missing = [k for k, val in v.items() if val is None]
    if missing:
        return {"m": None, "components": v, "missing": missing}

    m = BENEISH_COEF["const"] + sum(
        BENEISH_COEF[k] * v[k] for k in ("DSRI", "GMI", "AQI", "SGI", "DEPI",
                                         "SGAI", "TATA", "LVGI")
    )
    return {"m": m, "components": v, "missing": []}


# --------------------------------------------------------------------------
# Sloan tahakkuk orani
# --------------------------------------------------------------------------
def sloan_accruals(p: Period) -> float | None:
    """(Net kar - CFO - Yatirim nakit akisi) / Toplam varlik.

    Yuksek deger: kar nakde donmemis, gelecek donem getirisi zayif olma
    egiliminde (Sloan 1996).
    """
    ni, cfo, cfi, assets = (num(p.net_income), num(p.cfo), num(p.cfi), num(p.assets))
    if ni is None or cfo is None or cfi is None or not assets:
        return None
    return (ni - cfo - cfi) / assets


# --------------------------------------------------------------------------
# Ters DCF
# --------------------------------------------------------------------------
def dcf_value(fcf0: float, growth: float, *, r: float | None = None,
              terminal_g: float | None = None, years: int | None = None) -> float:
    """10 yil ``growth`` ile buyuyen FCF + Gordon terminal degeri."""
    r = REVERSE_DCF["discount_rate"] if r is None else r
    terminal_g = REVERSE_DCF["terminal_growth"] if terminal_g is None else terminal_g
    years = REVERSE_DCF["projection_years"] if years is None else years

    pv = 0.0
    fcf = fcf0
    for t in range(1, years + 1):
        fcf = fcf * (1.0 + growth)
        pv += fcf / ((1.0 + r) ** t)

    terminal_fcf = fcf * (1.0 + terminal_g)
    terminal = terminal_fcf / (r - terminal_g)
    pv += terminal / ((1.0 + r) ** years)
    return pv


def implied_growth(fcf0: float | None, enterprise_value: float | None) -> float | None:
    """Bugunku fiyatin varsaydigi 10 yillik FCF buyumesi (%).

    FCF <= 0 ise model anlamsiz -> None. Kok bulma ``brentq`` ile yapilir;
    aralik disinda kalirsa (asiri ucuz/pahali) sinir degeri dondurulur.
    """
    fcf0 = num(fcf0)
    ev = num(enterprise_value)
    if fcf0 is None or ev is None or fcf0 <= 0 or ev <= 0:
        return None

    lo, hi = REVERSE_DCF["growth_search_min"], REVERSE_DCF["growth_search_max"]

    def f(g: float) -> float:
        return dcf_value(fcf0, g) - ev

    try:
        f_lo, f_hi = f(lo), f(hi)
    except (OverflowError, ZeroDivisionError):
        return None

    if f_lo > 0:
        return lo * 100.0      # en dusuk buyumede bile deger > fiyat: cok ucuz
    if f_hi < 0:
        return hi * 100.0      # en yuksek buyumede bile deger < fiyat: cok pahali

    try:
        g = brentq(f, lo, hi, xtol=1e-6, maxiter=200)
    except (ValueError, RuntimeError):
        return None
    return g * 100.0


# --------------------------------------------------------------------------
# Toplayici
# --------------------------------------------------------------------------
def compute(f: Fundamentals, metrics: dict) -> dict:
    """Tum skorlari hesaplar ve metrik sozlugune eklenecek degerleri doner."""
    cur = f.ttm_period()
    prev = f.ttm_period(offset=4)

    piotroski = piotroski_f(cur, prev)
    z = altman_z(cur)
    beneish = beneish_m(cur, prev)
    sloan = sloan_accruals(cur)

    ev = metrics.get("meta", {}).get("enterprise_value_musd")
    fcf = metrics.get("meta", {}).get("fcf_ttm_musd")
    ig = implied_growth(fcf, ev)

    actual_growth = metrics.get("metrics", {}).get("rev_cagr_3y")
    implied_vs_actual = None
    # Oran YALNIZCA ikisi de pozitifken anlamlidir. Fiyat dusus varsayiyorsa
    # (ig <= 0) "gerceklesenin -0,12 katini varsayiyor" gibi yorumlanamaz bir
    # sayi cikar; boyle bir durumda ima edilen buyumeyi MUTLAK okumak gerekir.
    if (ig is not None and ig > 0
            and actual_growth is not None and actual_growth > 0):
        implied_vs_actual = ig / actual_growth

    return {
        "metrics": {
            "piotroski_f": piotroski["score"],
            "altman_z": z["z"],
            "beneish_m": beneish["m"],
            "sloan_accruals": sloan,
            "implied_growth": ig,
            "implied_vs_actual_growth": implied_vs_actual,
        },
        "detail": {
            "piotroski": piotroski,
            "altman": z,
            "beneish": beneish,
            "solvency_fallback": solvency_fallback(cur) if z["unreliable"] else None,
        },
    }
