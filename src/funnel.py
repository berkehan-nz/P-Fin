"""Huni — Asama 0'dan 4'e evren daraltma.

Asama 0  Evren        : ABD borsasi, adi hisse, buyukluk/likidite esikleri
Asama 1  Sert filtre  : marj, buyume, nakit, borc, seyrelme
Asama 2  Tuzak eleme  : manipulasyon, iflas riski, nakit donusumu, vade duvari
Asama 3  Goreli ucuz  : sektor ve kendi tarihine gore carpanlar
Asama 4  Puanla       : ilk 50, sektor basina en fazla 10

TASARIM: her eleme bir ``kill_reason`` yazar. Neyin neden elendigini
gormeden esikleri iyilestirmek mumkun degil; ``funnel_log.json`` bunu tutar.
"""

from __future__ import annotations

from collections import Counter

from . import config, metrics as metrics_mod, percentiles as pct_mod, scores as scores_mod, scoring
from .config import STAGE1, STAGE2, STAGE3, UNIVERSE, sector_for_sic
from .fundamentals import Fundamentals
from .util import num

STAGE_NAMES = {
    0: "Evren", 1: "Sert filtreler", 2: "Tuzak eleme",
    3: "Goreli ucuzluk", 4: "Puanlama",
}


# --------------------------------------------------------------------------
# Degerlendirme satiri
# --------------------------------------------------------------------------
def evaluate(f: Fundamentals, benchmark: list | None = None) -> dict:
    """Bir sirket icin huninin ihtiyaci olan her seyi tek sozlukte toplar."""
    mres = metrics_mod.compute(f, benchmark=benchmark)
    sres = scores_mod.compute(f, mres)
    m = {**mres["metrics"], **sres["metrics"]}
    return {
        "ticker": f.ticker,
        "cik": f.cik,
        "name": f.name,
        "sic": f.sic,
        "sector": sector_for_sic(f.sic),
        "exchange": f.exchange,
        "ipo_date": f.ipo_date,
        "metrics": m,
        "meta": mres["meta"],
        "flags": {**mres["flags"], **sres["flags"]},
        "detail": sres["detail"],
        "fundamentals": f,
        "avg_dollar_volume_30d": f.avg_dollar_volume_30d,
        "passed_stages": [],
        "kill_reason": None,
        "killed_at": None,
    }


def _kill(row: dict, stage: int, reason: str) -> None:
    row["kill_reason"] = reason
    row["killed_at"] = stage


# --------------------------------------------------------------------------
# Asama 0 — Evren
# --------------------------------------------------------------------------
def stage0(row: dict) -> str | None:
    """Eleme sebebi doner; gecerse None."""
    sic = row.get("sic")
    if config.is_excluded_sic(sic):
        return "SIC 6000-6799 (finans/gayrimenkul) haric"

    if sic in UNIVERSE["biotech_sic_codes"]:
        revenue = num(row["meta"].get("revenue_ttm_musd"))
        if revenue is None or revenue < UNIVERSE["biotech_min_revenue_musd"]:
            return "Hasilatsiz biyoteknoloji"

    exchange = (row.get("exchange") or "").strip()
    if exchange and exchange not in UNIVERSE["allowed_exchanges"]:
        return f"Borsa disi/uygunsuz kotasyon ({exchange})"

    mcap = num(row["meta"].get("market_cap_musd"))
    if mcap is None:
        return "Piyasa degeri hesaplanamadi"
    if mcap < UNIVERSE["market_cap_musd_min"]:
        return f"Piyasa degeri < {UNIVERSE['market_cap_musd_min']:.0f}M USD"
    if mcap > UNIVERSE["market_cap_musd_max"]:
        return f"Piyasa degeri > {UNIVERSE['market_cap_musd_max']:.0f}M USD"

    price = num(row["meta"].get("price"))
    if price is None:
        return "Fiyat alinamadi"
    if price < UNIVERSE["price_min_usd"]:
        return f"Fiyat < {UNIVERSE['price_min_usd']:.0f} USD"

    adv = num(row.get("avg_dollar_volume_30d"))
    if adv is not None and adv < UNIVERSE["avg_dollar_volume_30d_min_usd"]:
        return f"30 gunluk ortalama dolar hacmi < {UNIVERSE['avg_dollar_volume_30d_min_usd']/1e6:.0f}M USD"
    return None


# --------------------------------------------------------------------------
# Asama 1 — Sert filtreler
# --------------------------------------------------------------------------
def stage1(row: dict) -> str | None:
    """Sert filtreler.

    Eksik veri ELEME SEBEBI DEGILDIR (bkz. STAGE1["kill_on_missing_data"]).
    Hesaplanamayan girdiler ``row["stage1_missing"]`` listesine yazilir ve
    kartta gorunur; boylece "neden gecti" sorusu cevapsiz kalmaz.
    """
    m = row["metrics"]
    missing = row.setdefault("stage1_missing", [])
    strict = STAGE1["kill_on_missing_data"]

    gm = num(m.get("gross_margin"))
    if gm is None:
        if strict:
            return "Brut marj hesaplanamadi"
        missing.append("gross_margin")
    elif gm <= STAGE1["gross_margin_min_pct"]:
        return f"Brut marj %{gm:.1f} <= %{STAGE1['gross_margin_min_pct']:.0f}"

    growth = num(m.get("rev_growth_ttm"))
    if growth is None:
        if strict:
            return "Hasilat buyumesi hesaplanamadi"
        missing.append("rev_growth_ttm")
    elif growth <= STAGE1["rev_growth_ttm_min_pct"]:
        return f"Hasilat buyumesi %{growth:.1f} <= %{STAGE1['rev_growth_ttm_min_pct']:.0f}"

    # FCF > 0  VEYA  (yuksek buyume VE 40 Kurali)
    fcf = num(row["meta"].get("fcf_ttm_musd"))
    rule40 = num(m.get("rule_of_40"))
    fcf_ok = fcf is not None and fcf > 0
    exemption = (growth is not None
                 and growth > STAGE1["high_growth_exemption_growth_pct"]
                 and rule40 is not None
                 and rule40 >= STAGE1["high_growth_exemption_rule40_min"])
    if not (fcf_ok or exemption):
        return ("FCF negatif ve yuksek buyume istisnasi saglanmadi "
                f"(buyume {'yok' if growth is None else f'%{growth:.1f}'}, "
                f"40 Kurali {rule40 if rule40 is None else round(rule40, 1)})")

    nd_ebitda = num(m.get("net_debt_to_ebitda"))
    if nd_ebitda is not None and nd_ebitda >= STAGE1["net_debt_to_ebitda_max"]:
        return f"Net borc/FAVOK {nd_ebitda:.1f} >= {STAGE1['net_debt_to_ebitda_max']}"

    share_change = num(m.get("share_count_change_1y"))
    if share_change is not None and share_change >= STAGE1["share_count_growth_max_pct"]:
        # Yillik artis TEK SEFERLIK bir olaydan gelebilir: IPO'da imtiyazli
        # hisse donusumu (MNTN'de %268), konvertibl itfasi (QTWO), eski SPAC
        # seyrelmesi (AVPT). Bunlar surekli seyrelme degildir. Son iki ceyrekte
        # hisse sayisi ardisik dusuyorsa sirket artik seyrelmiyor demektir.
        if not (STAGE1.get("share_count_recent_decline_exempts")
                and _share_count_declining(row)):
            return (f"Hisse sayisi artisi %{share_change:.1f} >= "
                    f"%{STAGE1['share_count_growth_max_pct']:.0f}")
        row.setdefault("stage1_exemptions", []).append(
            f"Hisse artisi %{share_change:.1f} ama son iki ceyrekte hisse "
            f"sayisi dusuyor — tek seferlik seyrelme sayildi")

    sbc_fcf = num(m.get("sbc_to_fcf"))
    if sbc_fcf is not None and sbc_fcf >= STAGE1["sbc_to_fcf_max"]:
        return f"SBC/FCF {sbc_fcf:.2f} >= {STAGE1['sbc_to_fcf_max']}"
    return None


# --------------------------------------------------------------------------
# Asama 2 — Tuzak eleme
# --------------------------------------------------------------------------
def stage2(row: dict, track: str) -> str | None:
    m = row["metrics"]
    f: Fundamentals = row["fundamentals"]

    beneish = num(m.get("beneish_m"))
    if beneish is not None and beneish > STAGE2["beneish_m_max"]:
        return f"Beneish M {beneish:.2f} > {STAGE2['beneish_m_max']} (manipulasyon suphesi)"

    z = num(m.get("altman_z"))
    if z is not None and not row["flags"].get("z_unreliable") and z < STAGE2["altman_z_min"]:
        return f"Altman Z'' {z:.2f} < {STAGE2['altman_z_min']} (sikinti bolgesi)"

    # Piotroski esigi SADECE Kol A icin — Kol B'de zaten dusuk cikar
    if track == "A":
        piotroski = num(m.get("piotroski_f"))
        if piotroski is not None and piotroski < STAGE2["piotroski_f_min_track_a"]:
            return f"Piotroski F {int(piotroski)} < {STAGE2['piotroski_f_min_track_a']} (Kol A)"

    reason = _cash_conversion_streak(f)
    if reason:
        return reason

    reason = _two_year_decline(f)
    if reason:
        return reason

    wall = num(m.get("maturity_wall_2y"))
    fcf = num(row["meta"].get("fcf_ttm_musd"))
    if (wall is not None and wall > STAGE2["maturity_wall_max"]
            and fcf is not None and fcf < 0):
        return f"Vade duvari {wall:.2f} > {STAGE2['maturity_wall_max']} ve FCF negatif"

    reason = _ipo_lockup(row)
    if reason:
        return reason
    return None


def _share_count_declining(row: dict) -> bool:
    """Son iki ceyrekte seyreltilmis hisse sayisi ardisik dustu mu?"""
    f: Fundamentals = row.get("fundamentals")
    if f is None:
        return False
    counts = [num(q.shares_diluted) for q in f.sorted_quarters()[-3:]]
    counts = [c for c in counts if c is not None]
    if len(counts) < 3:
        return False
    return counts[-1] < counts[-2] < counts[-3]


def _cash_conversion_streak(f: Fundamentals) -> str | None:
    """Nakit donusumu ust uste N yil esigin altinda mi?

    Tek yillik dusuk donusum normaldir (calisma sermayesi dalgalanmasi).
    Ust uste uc yil, karin nakde donmedigini gosterir.
    """
    years = STAGE2["cash_conversion_consecutive_years"]
    annuals = f.sorted_annuals()
    if len(annuals) < years:
        return None
    streak = 0
    for p in annuals[-years:]:
        ni, cfo = num(p.net_income), num(p.cfo)
        if ni is None or cfo is None or ni <= 0:
            streak = 0
            continue
        if (cfo / ni) < STAGE2["cash_conversion_min"]:
            streak += 1
        else:
            streak = 0
    if streak >= years:
        return (f"Nakit donusumu {years} yil ust uste "
                f"{STAGE2['cash_conversion_min']} altinda")
    return None


def _two_year_decline(f: Fundamentals) -> str | None:
    """Hasilat VE brut marj iki yildir birlikte dusuyor mu?

    Ikisinin birlikte dusmesi yapisal bozulma sinyalidir; tek basina
    hasilat dususu (fiyat artisiyla telafi edilen) bunu tetiklemez.
    """
    years = STAGE2["declining_years"]
    annuals = f.sorted_annuals()
    if len(annuals) < years + 1:
        return None
    window = annuals[-(years + 1):]

    rev_down = all(
        (num(window[i].revenue) is not None and num(window[i - 1].revenue) is not None
         and num(window[i].revenue) < num(window[i - 1].revenue))
        for i in range(1, len(window))
    )
    gms = []
    for p in window:
        gp, rev = p.computed_gross_profit, num(p.revenue)
        gms.append(gp / rev if (gp is not None and rev) else None)
    gm_down = all(
        (gms[i] is not None and gms[i - 1] is not None and gms[i] < gms[i - 1])
        for i in range(1, len(gms))
    )
    if rev_down and gm_down:
        return f"Hasilat VE brut marj {years} yildir birlikte dusuyor"
    return None


def _ipo_lockup(row: dict) -> str | None:
    """Halka arz 12 aydan yeni ve kilit suresi bitmemis olabilir."""
    from datetime import date
    ipo = row.get("ipo_date")
    if not ipo:
        return None
    try:
        months = (date.today() - date.fromisoformat(ipo[:10])).days / 30.44
    except ValueError:
        return None
    if months < STAGE2["ipo_lockup_months"]:
        return f"Halka arz {months:.0f} ay once — kilit suresi bitmemis olabilir"
    return None


# --------------------------------------------------------------------------
# Asama 3 — Goreli ucuzluk
# --------------------------------------------------------------------------
def stage3(row: dict, track: str, sector_table: dict) -> str | None:
    m = row["metrics"]
    sector = row["sector"]

    def spct(metric: str) -> float | None:
        p, _ = pct_mod.sector_percentile(sector_table, sector, metric, m.get(metric))
        return p

    own = row.get("own_pct") or {}

    if track == "A":
        ev_ebit_pct = spct("ev_ebit")
        fcf_yield = num(m.get("fcf_yield_ev"))
        cheap = (
            (ev_ebit_pct is not None and ev_ebit_pct <= STAGE3["track_a"]["ev_ebit_sector_pct_max"])
            or (fcf_yield is not None and fcf_yield > STAGE3["track_a"]["fcf_yield_min_pct"])
        )
        if not cheap:
            return ("Kol A ucuzluk testi: EV/EBIT sektor yuzdeligi "
                    f"{_fmt(ev_ebit_pct)} > {STAGE3['track_a']['ev_ebit_sector_pct_max']:.0f} "
                    f"ve FCF verimi {_fmt(fcf_yield)} <= %{STAGE3['track_a']['fcf_yield_min_pct']:.0f}")

        own_pct = own.get("ev_ebit")
        if own_pct is not None and own_pct > STAGE3["track_a"]["ev_ebit_own_5y_pct_max"]:
            return (f"EV/EBIT kendi 5 yil yuzdeligi {own_pct:.0f} > "
                    f"{STAGE3['track_a']['ev_ebit_own_5y_pct_max']:.0f}")
    else:
        gp_pct = spct("ev_gross_profit")
        if gp_pct is None:
            return "EV/Brut kar sektor yuzdeligi hesaplanamadi"
        if gp_pct > STAGE3["track_b"]["ev_gross_profit_sector_pct_max"]:
            return (f"EV/Brut kar sektor yuzdeligi {gp_pct:.0f} > "
                    f"{STAGE3['track_b']['ev_gross_profit_sector_pct_max']:.0f}")

        own_pct = own.get("ev_sales")
        if own_pct is not None and own_pct > STAGE3["track_b"]["ev_sales_own_5y_pct_max"]:
            return (f"EV/Hasilat kendi 5 yil yuzdeligi {own_pct:.0f} > "
                    f"{STAGE3['track_b']['ev_sales_own_5y_pct_max']:.0f}")

    # Her iki kolda ortak: fiyat gerceklesen buyumeden cok fazlasini varsayamaz
    implied = num(m.get("implied_growth"))
    actual = num(m.get("rev_cagr_3y"))
    if implied is not None and actual is not None and actual > 0:
        # Carpim tek basina yetmez: CAGR %0,3 olan bir sirkette esik %0,45'e
        # duser ve %7,7'lik makul bir ima edilen buyume "asiri" sayilir
        # (ADEA'da boyle oluyordu). Mutlak bir pay da taniyoruz; esik ikisinin
        # BUYUGU olur.
        limit = max(actual * STAGE3["implied_growth_vs_cagr_max_multiple"],
                    actual + STAGE3["implied_growth_absolute_headroom_pct"])
        if implied > limit:
            return (f"Ima edilen buyume %{implied:.1f} > izin verilen "
                    f"%{limit:.1f} (gerceklesen %{actual:.1f})")
    return None


def _fmt(v) -> str:
    return "yok" if v is None else f"{v:.0f}"


# --------------------------------------------------------------------------
# Tam huni
# --------------------------------------------------------------------------
def run(rows: list[dict], *, top_n: int | None = None,
        max_per_sector: int | None = None) -> dict:
    """Huniyi bastan sona calistirir.

    Returns:
        ``{"candidates": [...], "all_rows": [...], "log": {...}}``
    """
    top_n = top_n or config.FINAL_CANDIDATE_COUNT
    max_per_sector = max_per_sector or config.MAX_PER_SECTOR

    log = {"stages": [], "kill_reasons": {}}
    survivors = list(rows)

    # --- Asama 0 ---
    log["stages"].append({"stage": 0, "name": STAGE_NAMES[0], "input": len(survivors)})
    passed = []
    for row in survivors:
        reason = stage0(row)
        if reason:
            _kill(row, 0, reason)
        else:
            row["passed_stages"].append(0)
            passed.append(row)
    log["stages"][-1]["output"] = len(passed)
    survivors = passed

    # --- Asama 1 ---
    log["stages"].append({"stage": 1, "name": STAGE_NAMES[1], "input": len(survivors)})
    passed = []
    for row in survivors:
        reason = stage1(row)
        if reason:
            _kill(row, 1, reason)
        else:
            row["passed_stages"].append(1)
            passed.append(row)
    log["stages"][-1]["output"] = len(passed)
    survivors = passed

    # --- Kol atamasi (Asama 2 ve 3 kola bagli) ---
    for row in survivors:
        row["track"] = metrics_mod.track_for(
            row["metrics"], STAGE3["track_b_operating_margin_pct"])

    # --- Asama 2 ---
    log["stages"].append({"stage": 2, "name": STAGE_NAMES[2], "input": len(survivors)})
    passed = []
    for row in survivors:
        reason = stage2(row, row["track"])
        if reason:
            _kill(row, 2, reason)
        else:
            row["passed_stages"].append(2)
            passed.append(row)
    log["stages"][-1]["output"] = len(passed)
    survivors = passed

    # --- Asama 3 ve 4 ---
    selected, sector_table = rank(survivors, log=log, top_n=top_n,
                                  max_per_sector=max_per_sector,
                                  compute_own_pct=True)

    log["kill_reasons"] = dict(Counter(
        r["kill_reason"] for r in rows if r.get("kill_reason")).most_common(30))

    return {"candidates": selected, "all_rows": rows, "log": log,
            "sector_table": sector_table}


def rank(survivors: list[dict], *, log: dict | None = None,
         top_n: int | None = None, max_per_sector: int | None = None,
         sector_table: dict | None = None,
         compute_own_pct: bool = True) -> tuple[list[dict], dict]:
    """Asama 3 (goreli ucuzluk) + Asama 4 (puanlama, sektor kotasi, ilk N).

    ``funnel.run`` ve kademeli tarayici (``scan.finalize``) ayni kodu
    kullansin diye ayri fonksiyon. Kademeli taramada Asama 0-2 saatlik
    partiler halinde onceden calistirilmis olur; buraya yalnizca hayatta
    kalanlar gelir.

    ``compute_own_pct=False`` ise satirlar ``own_pct`` degerini hazir
    tasidigi varsayilir (anlik goruntuden geri yuklenmis satirlar).
    """
    top_n = top_n or config.FINAL_CANDIDATE_COUNT
    max_per_sector = max_per_sector or config.MAX_PER_SECTOR
    log = log if log is not None else {"stages": []}
    log.setdefault("stages", [])

    # Yuzdelikler HAYATTA KALANLAR uzerinden hesaplanir. Asama 0-2'de elenenler
    # referans havuzunu bozar (iflas riskli sirketler carpanlari yapay olarak
    # dusurur, saglikli sirketler pahali gorunur).
    if sector_table is None:
        sector_table = pct_mod.build_sector_table(survivors)

    if compute_own_pct:
        for row in survivors:
            if row.get("fundamentals") is not None:
                row["own_pct"] = pct_mod.own_history_percentiles(
                    row["fundamentals"], row["metrics"])

    for row in survivors:
        row.setdefault("track", metrics_mod.track_for(
            row["metrics"], STAGE3["track_b_operating_margin_pct"]))
        row.setdefault("passed_stages", [])
        row.setdefault("own_pct", {})

    # --- Asama 3 ---
    log["stages"].append({"stage": 3, "name": STAGE_NAMES[3], "input": len(survivors)})
    passed = []
    for row in survivors:
        reason = stage3(row, row["track"], sector_table)
        if reason:
            _kill(row, 3, reason)
        else:
            row["passed_stages"].append(3)
            passed.append(row)
    log["stages"][-1]["output"] = len(passed)
    survivors = passed

    # --- Asama 4: puanla, sektor kotasi uygula, ilk N ---
    log["stages"].append({"stage": 4, "name": STAGE_NAMES[4], "input": len(survivors)})
    for row in survivors:
        pcts = {}
        for key in pct_mod.SECTOR_PERCENTILE_METRICS:
            p, _ = pct_mod.sector_percentile(sector_table, row["sector"], key,
                                             row["metrics"].get(key))
            pcts[key] = p
        row["sector_pct"] = pcts
        row["scores"], row["score_detail"] = scoring.compute(pcts)
        row["passed_stages"].append(4)

    ranked = sorted(survivors,
                    key=lambda r: (r["scores"].get("total") is not None,
                                   r["scores"].get("total") or 0),
                    reverse=True)

    per_sector: Counter = Counter()
    selected, overflow = [], []
    for row in ranked:
        if per_sector[row["sector"]] >= max_per_sector:
            overflow.append(row)
            row["kill_reason"] = f"Sektor kotasi dolu (en fazla {max_per_sector})"
            continue
        per_sector[row["sector"]] += 1
        selected.append(row)
        if len(selected) >= top_n:
            break

    log["stages"][-1]["output"] = len(selected)
    log["sector_distribution"] = dict(per_sector)
    log["sector_quota_overflow"] = len(overflow)

    return selected, sector_table


# --------------------------------------------------------------------------
# Tohum listesi: "huni calissaydi nerede elenirdi?"
# --------------------------------------------------------------------------
def diagnose(row: dict, sector_table: dict | None = None) -> dict:
    """Bir sirketin huninin hangi asamasinda elenecegini hesaplar.

    Tohum listesindeki 36 sirket huniden BAGIMSIZ olarak islenir ama bu
    bilgi kartta gosterilir — esiklerin dogru olup olmadigini ogrenmek icin.
    """
    passed: list[int] = []

    reason = stage0(row)
    if reason:
        return {"passed_stages": passed, "would_fail_at": 0, "kill_reason": reason}
    passed.append(0)

    reason = stage1(row)
    if reason:
        return {"passed_stages": passed, "would_fail_at": 1, "kill_reason": reason,
                "stage1_missing": row.get("stage1_missing", [])}
    passed.append(1)

    track = metrics_mod.track_for(row["metrics"], STAGE3["track_b_operating_margin_pct"])
    reason = stage2(row, track)
    if reason:
        return {"passed_stages": passed, "would_fail_at": 2, "kill_reason": reason}
    passed.append(2)

    if sector_table:
        reason = stage3(row, track, sector_table)
        if reason:
            return {"passed_stages": passed, "would_fail_at": 3, "kill_reason": reason}
        passed.append(3)

    return {"passed_stages": passed, "would_fail_at": None, "kill_reason": None,
            "stage1_missing": row.get("stage1_missing", [])}
