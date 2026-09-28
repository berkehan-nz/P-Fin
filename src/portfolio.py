"""Portfoy takibi — Midas'ta acilan gercek ve kagit pozisyonlar.

Midas'in API'si yok; islemler ``data/portfolio.json`` icine elle girilir.
Dashboard'daki "Islem ekle" formu bu semaya uygun bir JSON parcasi uretir.

Hesaplananlar: maliyet (komisyon dahil), guncel deger, K/Z ($ ve %), portfoy
agirligi, hedefe potansiyel, elde tutma suresi, gozden gecirmeye kalan gun,
Nasdaq 100 ve S&P 500'e karsi GIRIS TARIHINDEN ITIBAREN goreli performans.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from . import breakers as breakers_mod
from .config import (DATA_DIR, FX_PACE, MACRO_EVENTS, PORTFOLIO, TL_DEPOSIT,
                     TL_RENEWAL)
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
    """Fiyati cekilecek semboller. TL mevduat DISARIDA: onun fiyati yok;
    "TL-ISBANK" diye bir sembol aramak bosa bir istek ve bir uyari demek."""
    data = load()
    return sorted({(p.get("ticker") or "").upper()
                   for p in data["positions"] if p.get("status", "OPEN") == "OPEN"
                   and p.get("ticker")
                   and (p.get("asset_class") or "STOCK").upper() != "TL_DEPOSIT"})


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
# Varlik siniflari ve dilimler
# --------------------------------------------------------------------------
# Uc sinif var ve HER BIRI FARKLI degerlenir:
#   STOCK / ETF  fiyat x adet + giristen beri dagitimlar (temettu)
#   TL_DEPOSIT   TL anapara + tahakkuk eden NET faiz, kurla dolara cevrilir
#
# ETF dagitimlari degere DAHIL: SGOV her ay dagitim yapar ve fiyat o gun
# dagitim kadar duser. Dagitim sayilmazsa SGOV her ay "para kaybediyor"
# gorunur — TL mevduatin tahakkuk eden faizini sayip SGOV'unkini saymamak
# iki dilimi haksiz yere kiyaslamak olurdu. Dagitimlar elle nakde
# EKLENMEZ; sistem onlari kendisi sayar.

def slice_for(position: dict) -> str:
    """Pozisyonun dilimi: acik 'slice' > sembol eslemesi > varlik sinifi.

    SGOV bir ETF'tir ama cekirdek degil NAKIT CAPASIDIR; varlik sinifindan
    turetmek yanlis olurdu.
    """
    explicit = (position.get("slice") or "").strip().lower()
    if explicit in PORTFOLIO["slices"]:
        return explicit
    ticker = (position.get("ticker") or "").upper()
    if ticker in PORTFOLIO.get("ticker_slice", {}):
        return PORTFOLIO["ticker_slice"][ticker]
    klass = (position.get("asset_class") or "STOCK").upper()
    return PORTFOLIO["asset_class_slice"].get(klass, "motor")


def active_phase(on: str | None = None) -> dict:
    """Bugun (ya da verilen gun) gecerli faz.

    ``PORTFOLIO["active_phase"]`` doluysa tarih yok sayilir — alimlar
    gecikirse hedeflerin kendiliginden kaymamasi icin.
    """
    phases = PORTFOLIO["phases"]
    forced = PORTFOLIO.get("active_phase")
    if forced:
        for ph in phases:
            if ph["key"] == forced:
                return ph
    day = (on or today_iso())[:10]
    for ph in phases:
        if ph["start"] <= day and (ph["end"] is None or day < ph["end"]):
            return ph
    return phases[0] if day < phases[0]["start"] else phases[-1]


def dividends_since(divs: list | None, after: str, upto: str | None = None) -> float:
    """Hisse basina dagitim toplami: ``after`` < odeme-disi tarih <= ``upto``.

    Giris gunundeki dagitim sayilmaz: o gun alan, dagitima hak kazanmaz.
    """
    if not divs:
        return 0.0
    upto = (upto or today_iso())[:10]
    total = 0.0
    for d, amount in divs:
        if after[:10] < str(d)[:10] <= upto:
            total += num(amount) or 0.0
    return total


def tl_deposit_value(position: dict, usdtry: float | None, *,
                     as_of: str | None = None,
                     tbill_pct: float | None = None) -> dict:
    """TL vadeli mevduatin ``as_of`` gunundeki degeri ve basa bas kurlari.

    Turkiye'de mevduat faizi BASIT faizle ve 365 gun uzerinden isler;
    stopaj brut faizden kesilir.

    Iki basa bas kuru hesaplanir:
      usdtry_breakeven          kur bunun ustune cikarsa DOLAR BAZINDA zarar
      usdtry_breakeven_vs_sgov  kur bunun ustune cikarsa SGOV'DAN KOTU —
                                asil soru bu, cunku alternatif dolari
                                bosta tutmak degil, hazine bonosunda tutmak
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
        "bank": position.get("bank"),
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

    day = (as_of or today_iso())[:10]
    elapsed = _days_between(start, day)
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
        "days_to_maturity": max(term - elapsed, 0) if term is not None else None,
        "matured": bool(term is not None and elapsed >= term),
        "gross_interest_try": round(gross, 2),
        "withholding_try": round(tax, 2),
        "net_interest_try": round(net, 2),
        "daily_net_interest_try": round(
            principal * rate / 100.0 / TL_DEPOSIT["day_count"]
            * (1 - withholding / 100.0), 2),
        "value_try": round(value_try, 2),
        "value_usd": round(value_try / usdtry, 2) if usdtry else None,
        "net_interest_usd": round(net / usdtry, 2) if usdtry else None,
    })

    if entry_fx and entry_fx > 0 and term:
        full_net = principal * (rate / 100.0) * (term / TL_DEPOSIT["day_count"]) \
            * (1 - withholding / 100.0)
        at_maturity_try = principal + full_net
        usd_at_entry = principal / entry_fx
        out["value_try_at_maturity"] = round(at_maturity_try, 2)
        be = at_maturity_try / usd_at_entry
        out["usdtry_breakeven"] = round(be, 4)
        out["breakeven_headroom_pct"] = round((be / entry_fx - 1) * 100, 2)
        if usdtry and be != entry_fx:
            out["usdtry_used_pct"] = round((usdtry - entry_fx) / (be - entry_fx) * 100, 1)

        if tbill_pct is not None:
            sgov_growth = 1 + (tbill_pct / 100.0) * (term / 365.0)
            be_sgov = at_maturity_try / (usd_at_entry * sgov_growth)
            out["tbill_pct_used"] = tbill_pct
            out["usdtry_breakeven_vs_sgov"] = round(be_sgov, 4)
            out["breakeven_vs_sgov_headroom_pct"] = round((be_sgov / entry_fx - 1) * 100, 2)
    return out


def slice_summary(positions: list[dict], cash: float, portfolio_value: float,
                  phase: dict | None = None, *, complete: bool = True) -> list[dict]:
    """Dilim bazinda gercek/hedef agirlik ve sapma (aktif faza gore).

    NAKIT AYRI GOSTERILIR ve sapma hesabina girmez: bekleyen nakit genelde
    planli bir alimin parasidir (30 Ekim QQQM parcasi gibi) ve onu "hedef
    disi" saymak her planli alimdan once sahte alarm demek.

    POZISYON YOKKEN hicbir dilim "sapmis" sayilmaz: henuz hicbir sey
    almadiysan %100 nakit DOGRU durumdur. Kural tek yerde: hem uyarilar
    hem Cuma raporu buradan okur.
    """
    phase = phase or active_phase()
    targets = phase["targets"]
    actual: dict[str, float] = defaultdict(float)
    for p in positions:
        if p.get("value_usd"):
            actual[p.get("slice") or "motor"] += p["value_usd"]

    out = []
    for key, spec in PORTFOLIO["slices"].items():
        value = actual.get(key, 0.0)
        pct_now = (value / portfolio_value * 100) if portfolio_value > 0 else 0.0
        target = float(targets.get(key, 0))
        drift = pct_now - target
        out.append({
            "slice": key,
            "label": spec["label"],
            "value_usd": round(value, 2),
            "actual_pct": round(pct_now, 2),
            "target_pct": target,
            "drift_pp": round(drift, 2),
            # EKSIK VERIYLE SAPMA YOK: kur alinamazsa TL mevduat toplamdan
            # duser ve diger dilimler hedefin cok ustundeymis gibi gorunur.
            # Bu bir sapma degil, veri boslugu; alarm calmamali.
            "off_target": bool(positions) and complete
                          and abs(drift) > PORTFOLIO["slice_drift_warn_pp"],
        })
    out.append({
        "slice": "nakit",
        "label": "Nakit (USD)",
        "value_usd": round(cash, 2),
        "actual_pct": round(cash / portfolio_value * 100, 2) if portfolio_value > 0 else 0.0,
        "target_pct": None,
        "drift_pp": None,
        "off_target": False,
        "note": "planli alimlar icin bekliyor; sapma hesabina girmez",
    })
    return out


# --------------------------------------------------------------------------
# Kur temposu, yenileme olcutleri, siradaki isler, takvim
# --------------------------------------------------------------------------
TR_MACRO_PATH = DATA_DIR / "tr_macro.json"


def load_tr_macro() -> dict:
    """Elle girilen Turkiye makro verisi (politika faizi, enflasyon, secim)."""
    data = read_json(TR_MACRO_PATH, {}) or {}
    data.setdefault("tcmb_meetings", [])
    return data


def _rate_on_or_before(series: list, day: str) -> float | None:
    val = None
    for d, v in series or []:
        if str(d)[:10] <= day:
            val = num(v)
        else:
            break
    return val


def fx_pace(fx: dict, entry_rate: float | None = None) -> dict:
    """USD/TRY'nin son ~ceyrekteki degisimi ve renk sinifi."""
    rate = num(fx.get("rate"))
    series = fx.get("series") or []
    window = FX_PACE["window_days"]
    out = {"rate": rate, "as_of": fx.get("as_of"), "window_days": window,
           "change_quarter_pct": None, "color": "gray",
           "change_since_entry_pct": None}
    if rate and entry_rate:
        out["change_since_entry_pct"] = round((rate / entry_rate - 1) * 100, 2)
    if not rate or not series:
        return out
    last_day = str(series[-1][0])[:10]
    past_day = (date.fromisoformat(last_day) - timedelta(days=window)).isoformat()
    past = _rate_on_or_before(series, past_day)
    if not past:
        return out
    chg = (rate / past - 1) * 100
    out["change_quarter_pct"] = round(chg, 2)
    out["color"] = ("green" if chg < FX_PACE["green_max_pct"]
                    else "yellow" if chg <= FX_PACE["yellow_max_pct"] else "red")
    return out


def renewal_criteria(pace: dict, tr_macro: dict) -> list[dict]:
    """TL mevduat vade sonu yenileme icin uc olcut: yesil / kirmizi / gri.

    Gri = veri yok ya da eski. Tahmin yazmaktansa "bilmiyoruz" demek dogru.
    """
    stale_days = TL_RENEWAL["stale_after_days"]
    as_of = tr_macro.get("as_of")
    age = _days_between(as_of) if as_of else None
    stale = age is None or age > stale_days

    out = []
    policy = num(tr_macro.get("policy_rate_pct"))
    cpi = num(tr_macro.get("cpi_yoy_pct"))
    if policy is None or cpi is None or stale:
        durum, detay = "gray", ("politika faizi ve enflasyon girilmedi" if policy is None or cpi is None
                                else f"veri {age} gunluk — guncellenmeli")
    else:
        durum = "green" if policy > cpi else "red"
        detay = f"politika faizi %{policy:g} vs enflasyon %{cpi:g}"
    out.append({"key": "reel_faiz", "label": "Politika faizi enflasyonun ustunde",
                "status": durum, "detail": detay})

    chg = pace.get("change_quarter_pct")
    if chg is None:
        out.append({"key": "kur_temposu", "label": "Kur temposu ceyrekte %7'nin altinda",
                    "status": "gray", "detail": "kur serisi alinamadi"})
    else:
        ok = chg < TL_RENEWAL["fx_pace_max_pct"]
        out.append({"key": "kur_temposu", "label": "Kur temposu ceyrekte %7'nin altinda",
                    "status": "green" if ok else "red",
                    "detail": f"son {pace['window_days']} gunde %{chg:.1f}"})

    secim = tr_macro.get("early_election_announced")
    if secim is None or stale:
        out.append({"key": "erken_secim", "label": "Erken secim tarihi kesinlesmemis",
                    "status": "gray", "detail": "bilgi girilmedi"})
    else:
        out.append({"key": "erken_secim", "label": "Erken secim tarihi kesinlesmemis",
                    "status": "red" if secim else "green",
                    "detail": "kesinlesti" if secim else "kesinlesmedi"})
    return out


def upcoming_actions(data: dict, tl_rows: list[dict], criteria: list[dict]) -> list[dict]:
    """Siradaki isler: planli alimlar, faz gecisleri, mevduat vadeleri."""
    today = today_iso()
    out = []
    for tr in data.get("planned_tranches") or []:
        if not isinstance(tr, dict) or tr.get("done"):
            continue
        tutar = num(tr.get("amount_usd"))
        out.append({"date": tr.get("date"), "kind": "alim",
                    "title": f"{tr.get('ticker', '')} parcasi"
                             + (f" — ${tutar:,.0f}" if tutar is not None else ""),
                    "amount_usd": tutar, "ticker": tr.get("ticker"),
                    "note": tr.get("note", "")})
    for ph in PORTFOLIO["phases"]:
        if ph["start"] > today:
            hedef = ", ".join(f"{PORTFOLIO['slices'][k]['label']} %{v:g}"
                              for k, v in ph["targets"].items() if v)
            out.append({"date": ph["start"], "kind": "faz",
                        "title": f"{ph['label']} basliyor", "note": f"hedef: {hedef}"})
    for tl in tl_rows:
        if tl.get("maturity_date"):
            out.append({"date": tl["maturity_date"], "kind": "vade",
                        "title": f"TL mevduat vadesi ({tl.get('bank') or 'banka'})",
                        "note": "yenileme karari", "criteria": criteria})
    out = [a for a in out if a.get("date") and a["date"] >= today]
    for a in out:
        a["days"] = _days_between(today, a["date"])
    return sorted(out, key=lambda a: a["date"])


def macro_calendar(tr_macro: dict) -> list[dict]:
    today = today_iso()
    events = [dict(e) for e in MACRO_EVENTS]
    for d in tr_macro.get("tcmb_meetings") or []:
        events.append({"date": str(d)[:10], "title": "TCMB PPK toplantisi", "kind": "tcmb"})
    events = [e for e in events if (e.get("end") or e["date"]) >= today]
    for e in events:
        e["days"] = _days_between(today, e["date"])
    return sorted(events, key=lambda e: e["date"])


# --------------------------------------------------------------------------
# Portfoy durumu
# --------------------------------------------------------------------------
def compute(quotes: dict[str, dict],
            benchmarks: dict[str, list[tuple[str, float]]] | None = None,
            earnings: dict[str, str] | None = None,
            cards: dict[str, dict] | None = None,
            fx: dict | None = None,
            dividends: dict[str, list] | None = None,
            tbill_pct: float | None = None,
            peak_value: float | None = None) -> dict:
    """Portfoyun tam durumunu hesaplar.

    Args:
        quotes: ``{sembol: {"price":..,"change_1d_pct":..,"as_of":..}}``
        benchmarks: ``{"QQQ": [(tarih, kapanis)], "SPY": [...]}``
        earnings: ``{sembol: sonraki_kazanc_tarihi}``
        cards: ``{sembol: kart}`` — sektor ve tez kiricilar icin
        fx: ``prices.fx_rate()`` ciktisi (seri dahil)
        dividends: ``{sembol: [(odeme-disi tarih, hisse basina tutar)]}``
        tbill_pct: 3 aylik hazine bonosu — SGOV'a gore basa bas kuru icin
        peak_value: tarihceden en yuksek portfoy degeri (zirveden dusus icin)
    """
    data = load()
    benchmarks = benchmarks or {}
    fx = fx or {}
    usdtry = num(fx.get("rate"))
    earnings = earnings or {}
    cards = cards or {}
    dividends = dividends or {}
    phase = active_phase()

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
        entry_date = str(raw.get("entry_date") or "")[:10]

        asset_class = (raw.get("asset_class") or "STOCK").upper()
        card = cards.get(ticker) or {}
        tl = None
        divs_usd = 0.0
        started = True

        if asset_class == "TL_DEPOSIT":
            tl = tl_deposit_value(raw, usdtry, tbill_pct=tbill_pct)
            entry_fx = num(raw.get("usdtry_at_entry"))
            principal = num(raw.get("principal_try")) or 0.0
            cost = principal / entry_fx if entry_fx else 0.0
            price = None
            started = not (raw.get("start_date") and raw["start_date"] > today_iso())
            # Baslamamis mevduat MALIYETIYLE gorunur: henuz faiz islemedi ve
            # bugunku kurla degerlemek, var olmayan bir kur karini/zararini
            # gosterir.
            value = tl.get("value_usd") if started else (cost or None)

            # GIRIS KURU KONTROLU. Giris kuru, baslangic gunundeki piyasa
            # kurundan belirgin farkliysa ya kayit hatali ya da kurda sert
            # bir hareket var. Ikisi de sessiz gecilmemeli: fark ilk gun
            # dogrudan kar/zarar olarak gorunur.
            start_day = str(raw.get("start_date") or "")[:10]
            market0 = _rate_on_or_before(fx.get("series") or [], start_day) if start_day else None
            if entry_fx and market0:
                gap = (entry_fx / market0 - 1) * 100
                tl["usdtry_market_at_start"] = round(market0, 4)
                tl["entry_vs_market_pct"] = round(gap, 2)
                tl["entry_rate_suspect"] = abs(gap) > 1.5
        else:
            cost = shares * entry_price + fees
            quote = quotes.get(ticker) or {}
            price = num(quote.get("price"))
            price_day = str(quote.get("as_of") or "")[:10]
            # HENUZ FIYATLANMAMIS POZISYON: son kapanis giris gununden
            # onceyse, o kapanis bu pozisyona ait degildir. Onu kullanmak,
            # henuz sahip olmadigin bir hissenin dunku hareketini senin
            # kar/zararin gibi gosterir.
            if entry_date and (entry_date > today_iso()
                               or (price_day and price_day < entry_date)):
                started = False
            if started and price is not None:
                divs_usd = shares * dividends_since(dividends.get(ticker), entry_date, price_day)
                value = shares * price + divs_usd
            elif not started:
                value = shares * entry_price
            else:
                value = None

        pnl = (value - cost) if (value is not None and cost and started) else None

        pos = {
            **raw,
            "ticker": ticker,
            "cost_usd": round(cost, 2),
            "price": price,
            "price_as_of": (quotes.get(ticker) or {}).get("as_of"),
            "started": started,
            "change_1d_pct": num((quotes.get(ticker) or {}).get("change_1d_pct")) if started else None,
            "dividends_usd": round(divs_usd, 2),
            "value_usd": round(value, 2) if value is not None else None,
            "pnl_usd": round(pnl, 2) if pnl is not None else None,
            "pnl_pct": round(pnl / cost * 100, 2) if (pnl is not None and cost > 0) else None,
            "upside_to_target_pct": pct(
                (num(raw.get("target_price")) or 0) - (price or 0), price
            ) if (price and num(raw.get("target_price"))) else None,
            "holding_days": max(_days_between(entry_date) or 0, 0) if entry_date else None,
            "days_to_review": _days_between(today_iso(), raw.get("review_date"))
            if raw.get("review_date") else None,
            "sector": card.get("sector", ""),
            "next_earnings": earnings.get(ticker),
            "asset_class": asset_class,
            "slice": slice_for(raw),
            # KIRICILAR ARTIK MAKINE TARAFINDAN DEGERLENDIRILIYOR. ETF ve
            # mevduatta tez kirici yok; fiyat katmanlari yine calisir.
            "thesis_breakers": breakers_mod.evaluate_position(raw, card, price)
            if asset_class == "STOCK" or raw.get("thesis_breakers") else [],
        }
        if tl is not None:
            pos["tl_deposit"] = tl

        pos["vs_benchmark"] = {}
        for label, symbol in PORTFOLIO["benchmarks"].items():
            bench_return = _benchmark_return_since(benchmarks.get(symbol, []), entry_date)
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
        if pos["value_usd"] and pos["asset_class"] == "STOCK":
            sector_mix[pos.get("sector") or "Bilinmiyor"] += pos["value_usd"]
    stock_value = sum(sector_mix.values())
    sector_pct = {k: round(v / stock_value * 100, 2)
                  for k, v in sector_mix.items()} if stock_value > 0 else {}

    total_pnl = equity_value - total_cost if total_cost else 0.0

    unvalued = sorted(p["ticker"] for p in positions if p.get("value_usd") is None)

    tl_rows = [p["tl_deposit"] for p in positions if p.get("tl_deposit")]
    entry_fx = next((t.get("usdtry_at_entry") for t in tl_rows if t.get("usdtry_at_entry")), None)
    pace = fx_pace(fx, entry_fx)
    tr_macro = load_tr_macro()
    criteria = renewal_criteria(pace, tr_macro)

    fx_public = {k: v for k, v in fx.items() if k != "series"}

    summary = {
        "position_count": len(positions),
        "cost_usd": round(total_cost, 2),
        "equity_value_usd": round(equity_value, 2),
        "cash_usd": round(cash, 2),
        "portfolio_value_usd": round(portfolio_value, 2),
        "portfolio_value_try": round(portfolio_value * usdtry, 2) if usdtry else None,
        "pnl_usd": round(total_pnl, 2),
        "pnl_pct": round(total_pnl / total_cost * 100, 2) if total_cost > 0 else None,
        "sector_mix_pct": sector_pct,
        "largest_position_pct": max(
            (p["weight_pct"] for p in positions
             if p["weight_pct"] is not None and p["asset_class"] == "STOCK"),
            default=None),
        "vs_benchmark": _portfolio_vs_benchmark(positions),
        "phase": {"key": phase["key"], "label": phase["label"],
                  "start": phase["start"], "end": phase["end"]},
        "slices": slice_summary(positions, cash, portfolio_value, phase,
                                complete=not unvalued),
        "slices_incomplete": unvalued,
        "fx": fx_public,
        "fx_pace": pace,
        "tbill_pct": tbill_pct,
    }

    # Zirve TARIHCEDEN gelir. Onceki surum zirveyi portfolio.json'dan okuyor
    # ama hic yazmiyordu; "zirveden -%20" uyarisi hicbir zaman
    # tetiklenemezdi.
    peak = max(num(peak_value) or 0.0, portfolio_value)
    summary["peak_value_usd"] = round(peak, 2)
    drawdown = breakers_mod.portfolio_drawdown(summary, peak)

    return {
        "positions": sorted(positions, key=lambda p: p.get("value_usd") or 0, reverse=True),
        "closed": data.get("closed", []),
        "summary": summary,
        "tl_renewal": {"criteria": criteria,
                       "maturity_date": next((t.get("maturity_date") for t in tl_rows), None)},
        "actions": upcoming_actions(data, tl_rows, criteria),
        "calendar": macro_calendar(tr_macro),
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

        # Konsantrasyon siniri TEK HISSE icindir. TL mevduat portfoyun
        # yarisi olacak sekilde PLANLANDI; ETF'ler zaten dagitik.
        if pos.get("asset_class", "STOCK") == "STOCK" and \
                pos.get("weight_pct") is not None and \
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
    # "Portfoy bos" durumu slice_summary icinde ele aliniyor (off_target
    # orada False kalir); burada ikinci bir kontrol OLMAMALI, yoksa kural
    # iki yere dagilir ve biri degisince digeri sessizce eskir.
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

    for pos in positions:
        tl = pos.get("tl_deposit") or {}
        if tl.get("entry_rate_suspect"):
            out.append({
                "ticker": pos["ticker"], "level": "medium", "type": "giris_kuru",
                "message": f"{pos['ticker']} giris kuru {tl['usdtry_at_entry']:g}, baslangic "
                           f"gunu piyasa kuru {tl['usdtry_market_at_start']:g} "
                           f"(%{tl['entry_vs_market_pct']:+.1f}). Kayit dogru mu? Fark ilk "
                           f"gun dogrudan kar/zarar olarak gorunur.",
            })

    eksik = summary.get("slices_incomplete") or []
    if eksik:
        out.append({
            "ticker": "", "level": "low", "type": "veri_eksik",
            "message": f"Degerlenemeyen pozisyon: {', '.join(eksik)} (fiyat ya da kur "
                       f"alinamadi). Toplam ve dilim agirliklari eksik; sapma "
                       f"uyarilari bu yuzden kapali.",
        })

    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(out, key=lambda w: order.get(w["level"], 9))
