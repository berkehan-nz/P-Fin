"""Sektor ici ve sirketin kendi tarihindeki yuzdelik dilimler.

Bir carpanin 'ucuz' olup olmadigi tek basina anlamsizdir. Iki referans var:
  1. SEKTOR ICI — ayni SIC ana grubundaki digerlerine gore nerede
  2. KENDI 5 YILI — sirketin kendi tarihsel dagiliminda nerede

Ikisi de gerekli: sektorel olarak ucuz ama kendi tarihine gore pahali bir
hisse, sektorun tamaminin ucuzladigi anlamina gelir.
"""

from __future__ import annotations

from collections import defaultdict

from .config import MIN_PEERS_FOR_SECTOR_PERCENTILE, METRIC_PARAMS
from .fundamentals import Fundamentals
from .metrics import enterprise_value
from .util import num, percentile_rank

# Sektor yuzdeligi hesaplanan metrikler
SECTOR_PERCENTILE_METRICS = [
    "ev_ebit", "ev_ebitda", "ev_gross_profit", "ev_sales",
    "fcf_yield_ev", "fcf_yield_mcap", "earnings_yield", "pe",
    "rev_growth_ttm", "rev_cagr_3y", "gross_margin", "operating_margin",
    "fcf_margin", "roic", "gross_profitability", "rule_of_40",
    "net_debt_to_ebitda", "interest_coverage", "current_ratio",
    "cash_conversion", "sloan_accruals", "beneish_m", "piotroski_f",
    "altman_z", "sbc_to_revenue", "sbc_to_fcf", "share_count_change_1y",
    "return_6m", "return_12m", "rel_strength_6m", "pct_off_52w_high",
]

# Sirketin kendi tarihine gore yuzdelik hesaplanan metrikler
OWN_HISTORY_METRICS = ["ev_ebit", "ev_sales", "ev_gross_profit", "fcf_yield_ev"]


def build_sector_table(rows: list[dict]) -> dict[str, dict[str, list[float]]]:
    """``{sektor: {metrik: [degerler]}}`` — evren genelinde bir kez kurulur."""
    table: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        sector = row.get("sector") or "Bilinmiyor"
        m = row.get("metrics", {})
        for key in SECTOR_PERCENTILE_METRICS:
            v = num(m.get(key))
            if v is not None:
                table[sector][key].append(v)
                table["__ALL__"][key].append(v)
    return {k: dict(v) for k, v in table.items()}


def sector_percentile(table: dict, sector: str, metric: str,
                      value) -> tuple[float | None, str]:
    """Sektor ici yuzdelik + hangi referansin kullanildigi.

    Sektorde yeterli sirket yoksa tum evrene duser; bu durumu ``basis``
    ile raporlar ki dashboard'da yanilticiliga yol acmasin.
    """
    v = num(value)
    if v is None:
        return None, "none"
    peers = (table.get(sector) or {}).get(metric) or []
    if len(peers) >= MIN_PEERS_FOR_SECTOR_PERCENTILE:
        return percentile_rank(v, peers), "sector"
    universe = (table.get("__ALL__") or {}).get(metric) or []
    if len(universe) >= MIN_PEERS_FOR_SECTOR_PERCENTILE:
        return percentile_rank(v, universe), "universe"
    return None, "none"


def own_history_percentiles(f: Fundamentals, current: dict) -> dict[str, float | None]:
    """Sirketin kendi son 5 yillik (ceyreklik kayan TTM) dagilimindaki yeri.

    Her ceyrek sonu icin o gunku fiyat kullanilarak tarihsel carpan serisi
    kurulur; bugunku carpanin bu serideki yuzdeligi hesaplanir.
    """
    n = METRIC_PARAMS["own_history_quarters"]
    quarters = f.sorted_quarters()[-n:]
    if len(quarters) < 8 or not f.price_history:
        return {k: None for k in OWN_HISTORY_METRICS}

    price_by_date = dict(f.price_history)
    price_dates = sorted(price_by_date)

    def price_on(day: str) -> float | None:
        """O tarihteki (veya en yakin onceki islem gunundeki) kapanis."""
        candidates = [d for d in price_dates if d <= day]
        return price_by_date[candidates[-1]] if candidates else None

    shares = num(f.shares_outstanding)
    series: dict[str, list[float]] = {k: [] for k in OWN_HISTORY_METRICS}

    all_q = f.sorted_quarters()
    for i in range(3, len(all_q)):
        if all_q[i] not in quarters:
            continue
        window = all_q[i - 3:i + 1]
        end = window[-1]
        px = price_on(end.period_end)
        if px is None or shares is None:
            continue

        rev = _sum_field(window, "revenue")
        ebit = _sum_field(window, "operating_income")
        cfo = _sum_field(window, "cfo")
        capex = _sum_field(window, "capex")
        gp = _sum_field(window, "gross_profit")
        if gp is None:
            cor = _sum_field(window, "cost_of_revenue")
            gp = (rev - cor) if (rev is not None and cor is not None) else None

        ev = enterprise_value(px * shares, end)
        if ev is None or ev <= 0:
            continue
        fcf = (cfo - (capex or 0.0)) if cfo is not None else None

        if ebit and ebit > 0:
            series["ev_ebit"].append(ev / ebit)
        if rev and rev > 0:
            series["ev_sales"].append(ev / rev)
        if gp and gp > 0:
            series["ev_gross_profit"].append(ev / gp)
        if fcf is not None:
            series["fcf_yield_ev"].append(fcf / ev * 100)

    return {
        key: percentile_rank(current.get(key), series[key])
        for key in OWN_HISTORY_METRICS
    }


def _sum_field(periods, field: str) -> float | None:
    vals = [num(getattr(p, field)) for p in periods]
    return sum(v for v in vals if v is not None) if all(v is not None for v in vals) else None
