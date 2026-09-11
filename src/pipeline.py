"""Kosu adimlarinin ortak parcalari — run_seed / run_funnel / run_daily paylasir."""

from __future__ import annotations

from . import cards, config, funnel, portfolio, watchlist
from .config import CARDS_DIR, DATA_DIR, SEED_TICKERS
from .fundamentals import Fundamentals
from .sources import (analyst as analyst_src, edgar_api, edgar_bulk,
                      finnhub_api, finra_short, fred_api, prices)
from . import overrides
from .util import read_json, today_iso, try_fetch, write_json


def load_company(ticker: str, *, with_price: bool = True) -> Fundamentals | None:
    """EDGAR temel verisi + fiyat serisi + elle veri duzeltmeleri.

    Duzeltmeler BURADA uygulanir cunku her kosu yolu (tohum, tarama, gunluk)
    Fundamentals'i bu fonksiyondan alir. Tek nokta olmasi sart: baska bir
    yerde uygulansaydi bir kosuda duzeltilmis, digerinde duzeltilmemis veri
    ile calisilirdi.
    """
    f = try_fetch(edgar_api.load, ticker, label=f"edgar {ticker}")
    if f is None:
        return None

    applied = overrides.apply(f)
    if applied:
        f.overrides_applied = applied
        for o in applied:
            print(f"  [duzeltme] {ticker} {o['period_end']} {o['field']}: "
                  f"{o['before']} -> {o['after']}")

    if with_price:
        quote = try_fetch(prices.quote, ticker, label=f"fiyat {ticker}")
        if quote:
            prices.attach(f, quote)
    return f


def benchmarks() -> dict[str, list[tuple[str, float]]]:
    out = {}
    for symbol in config.BENCHMARK_TICKERS:
        out[symbol] = try_fetch(prices.benchmark_history, symbol,
                                label=f"benchmark {symbol}") or []
    return out


def context(tickers: list[str]) -> dict:
    """Haber, kazanc takvimi, kisa pozisyon — TEK SEFERDE cekilir."""
    earnings = try_fetch(finnhub_api.cached_earnings_calendar,
                         label="kazanc takvimi") or {}
    shorts = try_fetch(finra_short.load, label="FINRA kisa pozisyon") or {}
    return {"earnings": earnings, "shorts": shorts}


def build_cards(rows: list[dict], *, source: str, sector_table: dict,
                ctx: dict, bench: list, with_news: bool = True,
                diagnose_funnel: bool = True) -> list[dict]:
    """Degerlendirilmis satirlardan kart uretip diske yazar."""
    built = []
    for row in rows:
        ticker = row["ticker"]
        f: Fundamentals = row["fundamentals"]

        news = []
        if with_news and finnhub_api.enabled():
            news = try_fetch(finnhub_api.news, ticker, label=f"haber {ticker}") or []

        analyst = try_fetch(analyst_src.consensus, ticker, f.price,
                            label=f"analist {ticker}") or {}

        funnel_result = None
        if diagnose_funnel:
            funnel_result = funnel.diagnose(row, sector_table)

        card = cards.build(
            f,
            source=source,
            sector_table=sector_table,
            news=news,
            next_earnings=ctx["earnings"].get(ticker),
            analyst=analyst,
            short_interest=finra_short.for_ticker(ticker, ctx["shorts"]),
            insider=try_fetch(edgar_api.insider_activity, f.cik,
                              label=f"form4 {ticker}") if f.cik else {},
            benchmark=bench,
            extra_warnings=row.get("extra_warnings"),
            force_organic_suspect=ticker in config.SEED_FORCE_ORGANIC_SUSPECT,
            funnel_result=funnel_result,
            is_manual=row.get("is_manual", False),
            both_tracks=ticker in config.SEED_BOTH_TRACKS,
        )
        cards.save(card)
        built.append(card)
    return built


def write_candidates(seed_cards: list[dict], funnel_cards: list[dict],
                     manual_cards: list[dict]) -> bool:
    """``data/candidates.json`` — dashboard izgarasinin okudugu dosya.

    Elle eklenenler AYRI bolumde; siralamaya karismaz.
    """
    def rows(cs):
        return [cards.summary_row(c) for c in cs]

    ranked = sorted(rows(funnel_cards),
                    key=lambda r: (r["scores"].get("total") or -1), reverse=True)
    seeds = sorted(rows(seed_cards),
                   key=lambda r: (r["scores"].get("total") or -1), reverse=True)

    payload = {
        "candidates": ranked,
        "seed": seeds,
        "manual": rows(manual_cards),
        "counts": {
            "funnel": len(ranked),
            "seed": len(seeds),
            "manual": len(manual_cards),
        },
        "seed_date": config.SEED_DATE,
        "source": "funnel+seed+manual",
    }
    return write_json(DATA_DIR / "candidates.json", payload)


def refresh_candidates_from_disk() -> bool:
    """Kartlari diskten okuyup candidates.json'i yeniden kurar.

    Gunluk kosuda tam huni calismaz; kartlarin fiyat/haber alanlari
    guncellenir ve ozet dosyasi bu fonksiyonla tazelenir.
    """
    seed, funnel_rows, manual = [], [], []
    for path in sorted(CARDS_DIR.glob("*.json")):
        card = read_json(path)
        if not isinstance(card, dict) or not card.get("ticker"):
            continue
        if (card.get("flags") or {}).get("is_manual"):
            manual.append(card)
        elif card.get("source") == config.SEED_SOURCE_TAG:
            seed.append(card)
        else:
            funnel_rows.append(card)
    return write_candidates(seed, funnel_rows, manual)


def write_macro() -> bool:
    snapshot = try_fetch(fred_api.snapshot, label="FRED makro") or {}
    return write_json(DATA_DIR / "macro.json",
                      {"series": snapshot, "source": "fred"})


def write_thresholds() -> bool:
    return write_json(DATA_DIR / "thresholds.json",
                      {**config.thresholds_payload(), "source": "config.py"})


def write_universe(rows: list[dict], log: dict) -> bool:
    """Evren ozeti — huni ekraninin okudugu dosya."""
    payload = {
        "total_evaluated": len(rows),
        "log": log,
        "sectors": _sector_counts(rows),
        "source": "funnel",
    }
    return write_json(DATA_DIR / "universe.json", payload)


def _sector_counts(rows: list[dict]) -> dict:
    out: dict[str, int] = {}
    for r in rows:
        out[r.get("sector") or "Bilinmiyor"] = out.get(r.get("sector") or "Bilinmiyor", 0) + 1
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


def append_funnel_log(log: dict) -> bool:
    """Her kosuyu ``funnel_log.json``'a ekler — esik degisimlerinin etkisi izlensin."""
    path = DATA_DIR / "funnel_log.json"
    existing = read_json(path, {"runs": []})
    runs = existing.get("runs", [])
    entry = {
        "date": today_iso(),
        "stages": log.get("stages", []),
        "kill_reasons": log.get("kill_reasons", {}),
        "sector_distribution": log.get("sector_distribution", {}),
        "sector_quota_overflow": log.get("sector_quota_overflow", 0),
        "thresholds_snapshot": {
            "stage1": config.STAGE1, "stage2": config.STAGE2, "stage3": config.STAGE3,
        },
    }
    runs = [r for r in runs if r.get("date") != entry["date"]]
    runs.append(entry)
    runs = runs[-60:]     # son 60 kosu yeter
    return write_json(path, {"runs": runs, "source": "funnel"})


def write_portfolio_state(quotes: dict, bench: dict, ctx: dict) -> bool:
    card_map = {}
    for path in CARDS_DIR.glob("*.json"):
        c = read_json(path)
        if isinstance(c, dict) and c.get("ticker"):
            card_map[c["ticker"]] = c
    state = portfolio.compute(quotes, bench, ctx["earnings"], card_map)
    return write_json(DATA_DIR / "portfolio_state.json", state)


def write_overview(ctx: dict, quotes: dict) -> bool:
    """Genel bakis ekraninin "bugun ne olmus" seridi."""
    watched = set(watchlist.tickers()) | set(portfolio.tickers())
    movers = []
    for ticker in sorted(watched):
        q = quotes.get(ticker) or {}
        if q.get("change_1d_pct") is not None:
            movers.append({"ticker": ticker, "price": q.get("price"),
                           "change_1d_pct": round(q["change_1d_pct"], 2)})
    movers.sort(key=lambda x: abs(x["change_1d_pct"]), reverse=True)

    news_items = []
    if finnhub_api.enabled():
        for ticker in sorted(watched):
            for item in (try_fetch(finnhub_api.news, ticker, days=2, limit=3,
                                   label=f"haber {ticker}") or []):
                news_items.append({**item, "ticker": ticker})
    news_items.sort(key=lambda n: n.get("date", ""), reverse=True)

    return write_json(DATA_DIR / "overview.json", {
        "movers": movers[:20],
        "news": news_items[:25],
        "watched_count": len(watched),
        "source": "prices+finnhub",
    })


def universe_tickers(limit: int | None = None, *, auto_sync: bool = True) -> list[str]:
    """Onbellekteki SEC sirketlerinden sembol listesi kurar.

    Toplu veri CIK tasir, sembol tasimaz; ``company_tickers.json`` ile
    eslestirilir. Eslesmeyenler (ADR, ozel sirket) elenir.

    Onbellek bossa (ilk kosu, ya da Actions onbellegi dusmus) once toplu
    veriyi indirir — aksi halde evren sessizce yalnizca tohum listesine
    duser ve bunu kimse fark etmez.
    """
    companies = edgar_bulk.companies()
    if not companies and auto_sync:
        print("[evren] SEC toplu veri onbellegi bos — senkronize ediliyor...")
        edgar_bulk.sync()
        companies = edgar_bulk.companies()

    tmap = edgar_api.ticker_map()
    cik_to_ticker: dict[int, str] = {}
    for ticker, info in tmap.items():
        cik_to_ticker.setdefault(info["cik"], ticker)

    out = []
    for company in companies:
        cik = company.get("cik")
        sic = company.get("sic")
        if cik is None or cik not in cik_to_ticker:
            continue
        if config.is_excluded_sic(sic):
            continue
        out.append(cik_to_ticker[cik])

    out = sorted(set(out) | set(SEED_TICKERS) | set(watchlist.tickers()))
    return out[:limit] if limit else out
