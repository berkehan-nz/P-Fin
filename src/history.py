"""PORTFOY TARIHCESI — her islem gunu icin bir satir + kiyas serileri.

"Bugun yatirimlarim nasil gitti" sorusu tek bir anlik goruntuyle
cevaplanamaz; dunku degere ihtiyac var. Bu dosya o hafizadir:
``data/portfolio_history.json``.

IKI TASARIM KARARI

1) Her kosuda tarihce BASTAN hesaplanir (baslangic gununden bugune).
   Satir satir eklemek yerine yeniden hesaplamak, kacirilan bir gunluk
   kosunun bosluk birakmamasini ve ilk kurulumda gecmisin geriye donuk
   dolmasini saglar. Fiyat serileri zaten onbellekte; maliyet ihmal
   edilebilir.

2) Eksik veriyle hesaplanan satir ESKISININ UZERINE YAZILMAZ. Bir gun
   yfinance cevap vermezse, o gunun yeniden hesabi eksik fiyatla toplami
   sahte bicimde dusurur. Eski satir tam ise korunur. "Null bir alan veri
   yok gibi gorunur, vardi-ve-sildik gibi gorunmez" — kartlarda yasanan
   veri kaybinin portfoydeki karsiligi.

NAKIT GECMISI pozisyon kayitlarindan geri kurulur: bugunku nakit + o
gunden SONRA yapilan alimlarin maliyeti - sonra yapilan satislarin geliri
- sonra gelen dis nakit girisleri. Boylece 30 Ekim'deki QQQM parcasi
kaydedildiginde Ekim ortasindaki satirlar 149 $ eksik gorunmez.

KIYAS SERILERI ayni sermayeyle ayni gun baslar:
  hepsi SGOV'da   sermaye x SGOV toplam getirisi (dagitimlar dahil)
  hepsi QQQ'da    sermaye x QQQ toplam getirisi
  hepsi TL'de     sermaye, giris kurundan TL'ye cevrilip Berke'nin
                  mevduat kosullariyla (faiz, stopaj) tahakkuk eder
Komisyonlar kiyaslara yansitilmaz; fark birkac dolar.
"""

from __future__ import annotations

from datetime import date

from . import portfolio as pf
from .config import DATA_DIR, TL_DEPOSIT
from .util import num, read_json, today_iso, write_json

HISTORY_PATH = DATA_DIR / "portfolio_history.json"

BENCH_SGOV = "SGOV"
BENCH_QQQ = "QQQ"


def _on_or_before(series: list, day: str) -> float | None:
    """Serideki ``day`` ya da oncesine ait son deger (hafta sonu/tatil icin)."""
    val = None
    for d, v in series or []:
        if str(d)[:10] <= day:
            val = num(v)
        else:
            break
    return val


def _days(a: str, b: str) -> int:
    return (date.fromisoformat(b[:10]) - date.fromisoformat(a[:10])).days


# --------------------------------------------------------------------------
# Sermaye ve nakit
# --------------------------------------------------------------------------
def _cost(pos: dict) -> float:
    if (pos.get("asset_class") or "").upper() == "TL_DEPOSIT":
        fx = num(pos.get("usdtry_at_entry"))
        return (num(pos.get("principal_try")) or 0.0) / fx if fx else 0.0
    return (num(pos.get("shares")) or 0.0) * (num(pos.get("entry_price")) or 0.0) \
        + (num(pos.get("fees_usd")) or 0.0)


def _proceeds(pos: dict) -> float:
    return (num(pos.get("shares")) or 0.0) * (num(pos.get("exit_price")) or 0.0) \
        - (num(pos.get("exit_fees_usd")) or 0.0)


def _all_positions(data: dict) -> list[dict]:
    return list(data.get("positions") or []) + list(data.get("closed") or [])


def inception(data: dict) -> str | None:
    days = [str(p.get("entry_date") or p.get("start_date") or "")[:10]
            for p in _all_positions(data)]
    days += [str(f.get("date"))[:10] for f in data.get("cash_flows") or [] if f.get("date")]
    days = [d for d in days if d]
    return min(days) if days else None


def cash_on(data: dict, day: str, *, before_trades: bool = False) -> float:
    """``day`` gunu kapanistaki nakit (``before_trades``: o gunun islemlerinden once).

    Bugunku nakitten, o gunden SONRAKI hareketleri geri alarak hesaplanir.
    """
    after = (lambda d: d >= day) if before_trades else (lambda d: d > day)
    cash = num(data.get("cash_usd")) or 0.0
    for p in _all_positions(data):
        if after(str(p.get("entry_date") or "")[:10]):
            cash += _cost(p)
        exit_day = str(p.get("exit_date") or "")[:10]
        if exit_day and after(exit_day):
            cash -= _proceeds(p)
    for f in data.get("cash_flows") or []:
        if after(str(f.get("date") or "")[:10]):
            cash -= num(f.get("amount_usd")) or 0.0
    return cash


def injections(data: dict) -> list[tuple[str, float]]:
    """Sermaye girisleri: baslangic sermayesi + sonraki dis nakit girisleri."""
    start = inception(data)
    if not start:
        return []
    out = [(start, cash_on(data, start, before_trades=True))]
    for f in data.get("cash_flows") or []:
        d = str(f.get("date") or "")[:10]
        if d and d > start:
            out.append((d, num(f.get("amount_usd")) or 0.0))
    return out


# --------------------------------------------------------------------------
# Tek gunluk degerleme
# --------------------------------------------------------------------------
_SUMMED = ("shares", "value_usd", "dividends_usd", "value_try",
           "accrued_net_try", "accrued_net_usd", "principal_try")


def _add_lot(positions: dict, ticker: str, row: dict) -> None:
    cur = positions.get(ticker)
    if cur is None:
        positions[ticker] = row
        return
    for k in _SUMMED:
        if k in row or k in cur:
            a, b = num(cur.get(k)), num(row.get(k))
            cur[k] = None if (a is None and b is None) else round((a or 0) + (b or 0), 4)


def value_on(data: dict, day: str, *, price_series: dict, dividends: dict,
             fx_series: list) -> dict:
    """``day`` kapanisinda portfoy. Eksik girdi varsa ``complete=False``."""
    fx = _on_or_before(fx_series, day)
    missing: list[str] = []
    positions: dict[str, dict] = {}
    slices: dict[str, float] = {}
    total = 0.0

    for p in _all_positions(data):
        entry = str(p.get("entry_date") or p.get("start_date") or "")[:10]
        exit_day = str(p.get("exit_date") or "")[:10]
        if not entry or entry > day or (exit_day and exit_day <= day):
            continue
        ticker = (p.get("ticker") or "").upper()
        klass = (p.get("asset_class") or "STOCK").upper()
        sl = pf.slice_for(p)

        if klass == "TL_DEPOSIT":
            if not fx:
                missing.append("USDTRY")
                continue
            tl = pf.tl_deposit_value(p, fx, as_of=day)
            v = tl.get("value_usd")
            if v is None:
                missing.append(ticker)
                continue
            row = {
                "value_usd": round(v, 2),
                "value_try": tl.get("value_try"),
                "accrued_net_try": tl.get("net_interest_try"),
                "accrued_net_usd": tl.get("net_interest_usd"),
                "principal_try": num(p.get("principal_try")),
            }
        else:
            close = _on_or_before(price_series.get(ticker), day)
            divs = dividends.get(ticker)
            if close is None:
                missing.append(ticker)
                continue
            if divs is None:
                # Dagitim verisi YOK (bos liste degil, bilinmiyor). Degeri
                # hesapliyoruz ama satiri eksik sayiyoruz: SGOV icin fark
                # ayda ~%0,35 ve tam bir satirin uzerine yazilmamali.
                missing.append(f"{ticker}:dagitim")
            shares = num(p.get("shares")) or 0.0
            div_usd = shares * pf.dividends_since(divs or [], entry, day)
            v = shares * close + div_usd
            row = {"price": round(close, 4), "shares": shares,
                   "value_usd": round(v, 2), "dividends_usd": round(div_usd, 2)}

        # AYNI SEMBOLDE IKINCI PARCA (30 Ekim QQQM) ayri bir kayit olarak
        # gelir. Sozluge yeniden yazmak ilk parcayi satirdan silerdi; toplam
        # dogru kalir ama pozisyon satiri yarim gorunurdu. Parcalar toplanir.
        _add_lot(positions, ticker, row)
        total += row["value_usd"]
        slices[sl] = round(slices.get(sl, 0.0) + row["value_usd"], 2)

    cash = cash_on(data, day)
    total += cash
    slices["nakit"] = round(cash, 2)
    return {
        "date": day,
        "total_usd": round(total, 2),
        "total_try": round(total * fx, 2) if fx else None,
        "usdtry": round(fx, 4) if fx else None,
        "cash_usd": round(cash, 2),
        "slices": slices,
        "positions": positions,
        "complete": not missing,
        # KULLANILABILIR: fiyat ve kur tam, yalnizca dagitim verisi eksik
        # olabilir (deger en fazla birkac dolar eksik). Fiyati olmayan satir
        # bir pozisyonu toplamdan TAMAMEN dusurur; o satir hic yazilmaz.
        "usable": all(m.endswith(":dagitim") for m in missing),
        "missing": missing,
    }


# --------------------------------------------------------------------------
# Kiyaslar
# --------------------------------------------------------------------------
def _total_return(series: list, divs: list | None, start: str, day: str) -> float | None:
    a = _on_or_before(series, start)
    b = _on_or_before(series, day)
    if not a or b is None:
        return None
    return (b + pf.dividends_since(divs or [], start, day)) / a


def _tl_terms(data: dict) -> tuple[float, float, float | None]:
    """Kiyas icin mevduat kosullari: Berke'nin gercek mevduati, yoksa varsayilan."""
    for p in data.get("positions") or []:
        if (p.get("asset_class") or "").upper() == "TL_DEPOSIT":
            w = num(p.get("withholding_pct"))
            return (num(p.get("annual_rate_pct")) or 0.0,
                    TL_DEPOSIT["default_withholding_pct"] if w is None else w,
                    num(p.get("usdtry_at_entry")))
    return 0.0, TL_DEPOSIT["default_withholding_pct"], None


def benchmarks_on(data: dict, day: str, *, price_series: dict, dividends: dict,
                  fx_series: list) -> dict:
    """Ayni sermaye ayni gun: SGOV'da, QQQ'da ya da TL mevduatta olsaydi."""
    fx_now = _on_or_before(fx_series, day)
    rate, withholding, entry_fx = _tl_terms(data)
    inc = injections(data)
    out = {"all_sgov_usd": 0.0, "all_qqq_usd": 0.0, "all_tl_usd": 0.0}
    for i, (t0, amount) in enumerate(inc):
        if t0 > day:
            continue
        for key, sym in (("all_sgov_usd", BENCH_SGOV), ("all_qqq_usd", BENCH_QQQ)):
            g = _total_return(price_series.get(sym), dividends.get(sym), t0, day)
            out[key] = None if (g is None or out[key] is None) else out[key] + amount * g

        # TL: ilk sermaye Berke'nin gercek cevrim kurundan (Midas 50,3),
        # sonraki girisler o gunun kurundan cevrilir.
        fx0 = entry_fx if (i == 0 and entry_fx) else _on_or_before(fx_series, t0)
        if not fx0 or not fx_now or out["all_tl_usd"] is None:
            out["all_tl_usd"] = None
            continue
        growth = 1 + (rate / 100.0) * (1 - withholding / 100.0) * _days(t0, day) \
            / TL_DEPOSIT["day_count"]
        out["all_tl_usd"] += amount * fx0 * growth / fx_now
    return {k: (round(v, 2) if v is not None else None) for k, v in out.items()}


# --------------------------------------------------------------------------
# Tarihce
# --------------------------------------------------------------------------
def trading_days(data: dict, price_series: dict, fx_series: list,
                 upto: str | None = None) -> list[str]:
    """Baslangictan bugune, elde tutulan varliklarin fiyatlandigi gunler."""
    start = inception(data)
    if not start:
        return []
    upto = (upto or today_iso())[:10]
    held = {(p.get("ticker") or "").upper() for p in _all_positions(data)
            if (p.get("asset_class") or "STOCK").upper() != "TL_DEPOSIT"}
    days: set[str] = set()
    for t in held:
        days |= {str(d)[:10] for d, _ in price_series.get(t) or []}
    if not days:
        days = {str(d)[:10] for d, _ in fx_series or []}
    return sorted(d for d in days if start <= d <= upto)


def rebuild(data: dict, *, price_series: dict, dividends: dict,
            fx_series: list, upto: str | None = None) -> list[dict]:
    rows = []
    for day in trading_days(data, price_series, fx_series, upto):
        row = value_on(data, day, price_series=price_series, dividends=dividends,
                       fx_series=fx_series)
        row["benchmarks"] = benchmarks_on(data, day, price_series=price_series,
                                          dividends=dividends, fx_series=fx_series)
        rows.append(row)
    return rows


def merge(old_rows: list[dict], new_rows: list[dict]) -> list[dict]:
    """Yeni satirlari eskilerle birlestirir. EKSIK yeni satir, TAM eskiyi ezmez."""
    by_day = {r["date"]: r for r in old_rows or [] if r.get("date")}
    for r in new_rows:
        old = by_day.get(r["date"])
        if r.get("complete"):
            by_day[r["date"]] = r                 # tam satir her zaman kazanir
        elif r.get("usable") and not (old and old.get("complete")):
            by_day[r["date"]] = r                 # yaklasik, ama elde daha iyisi yok
        # Kullanilamaz satir (fiyat/kur eksik) HIC yazilmaz: bir pozisyonu
        # toplamdan tamamen dusurur ve sahte bir cokus gibi gorunur.
    return [by_day[d] for d in sorted(by_day)]


def performance(rows: list[dict], data: dict) -> dict:
    """Genel bakis basligi: bugun, baslangictan beri, kiyaslar."""
    start = inception(data)
    today = today_iso()
    inc = injections(data)
    invested = sum(a for _, a in inc)
    base = {"inception": start, "invested_usd": round(invested, 2)}

    if not start or start > today or not rows:
        return {**base, "status": "baslamadi",
                "days_to_start": _days(today, start) if start and start > today else 0,
                "note": "Ilk kapanistan sonra dolar."}

    last = rows[-1]
    prev = rows[-2] if len(rows) >= 2 else None
    total = last["total_usd"]

    # Dis nakit girisi (maas, havale) portfoyu "kazandirmaz": gunluk
    # degisimden dusulur. Alim-satim nakdi pozisyona tasir, toplami
    # degistirmez (komisyon haric — o gercek bir maliyet).
    added = sum(a for d, a in inc[1:] if prev and prev["date"] < d <= last["date"])
    day_chg = (total - prev["total_usd"] - added) if prev else None
    rate, _w, entry_fx = _tl_terms(data)
    invested_try = sum(a * (entry_fx if (i == 0 and entry_fx) else (last.get("usdtry") or 0))
                       for i, (_d, a) in enumerate(inc))

    b = last.get("benchmarks") or {}

    def fark(key):
        v = b.get(key)
        return round(total - v, 2) if v is not None else None

    return {
        **base,
        "status": "aktif",
        "as_of": last["date"],
        "days": _days(start, today),
        "value_usd": total,
        "value_try": last.get("total_try"),
        "usdtry": last.get("usdtry"),
        "day_change_usd": round(day_chg, 2) if day_chg is not None else None,
        "day_change_pct": round(day_chg / prev["total_usd"] * 100, 2)
        if (day_chg is not None and prev["total_usd"]) else None,
        "prev_date": prev["date"] if prev else None,
        "positions_day": positions_day(prev, last),
        "return_usd": round(total - invested, 2),
        "return_pct": round((total / invested - 1) * 100, 2) if invested else None,
        "return_try_pct": round((last["total_try"] / invested_try - 1) * 100, 2)
        if (last.get("total_try") and invested_try) else None,
        "benchmarks": b,
        "vs_all_sgov_usd": fark("all_sgov_usd"),
        "vs_all_tl_usd": fark("all_tl_usd"),
        "vs_all_qqq_usd": fark("all_qqq_usd"),
        "peak_value_usd": max(r["total_usd"] for r in rows),
        "complete": last.get("complete", False),
        "missing": last.get("missing", []),
    }


def positions_day(prev: dict | None, last: dict) -> dict:
    """Pozisyon bazinda gunluk degisim ($ ve %).

    Yeni bir parca alinan gun deger farki "kazanc" degildir: pay sayisi
    degistiyse degisim fiyat farkindan, bugunku pay sayisiyla hesaplanir.
    TL mevduatta anapara ayni kaldigi surece fark = faiz + kur etkisi.
    """
    out: dict[str, dict] = {}
    if not prev:
        return out
    before = prev.get("positions") or {}
    for ticker, now in (last.get("positions") or {}).items():
        was = before.get(ticker)
        if not was:
            continue
        v_now, v_was = num(now.get("value_usd")), num(was.get("value_usd"))
        if v_now is None or v_was is None:
            continue
        if "price" in now:
            same = num(now.get("shares")) == num(was.get("shares"))
            p_now, p_was = num(now.get("price")), num(was.get("price"))
            if same:
                chg = v_now - v_was
            elif p_now is not None and p_was is not None:
                chg = (num(now.get("shares")) or 0.0) * (p_now - p_was)
            else:
                continue
            base = v_now - chg
        else:
            if num(now.get("principal_try")) != num(was.get("principal_try")):
                continue
            chg, base = v_now - v_was, v_was
        out[ticker] = {"usd": round(chg, 2),
                       "pct": round(chg / base * 100, 2) if base else None}
    return out


def load() -> list[dict]:
    return (read_json(HISTORY_PATH, {}) or {}).get("rows") or []


def write(rows: list[dict]) -> bool:
    return write_json(HISTORY_PATH, {"rows": rows, "source": "history"},
                      stamp_matters=True)
