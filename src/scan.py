"""KADEMELI EVREN TARAMASI — her saat bir parti, kesintisiz veri akisi.

Neden: tam evren taramasi tek seferde saatler surer, ucretsiz kotalarda
kirilgan ve bir hata tum kosuyu cope atar. Bunun yerine evren bir KUYRUKTUR;
her saat sabit sayida sirket islenir, ilerleme repoya yazilir, kuyruk bitince
Asama 3-4 calisir ve yeni tur baslar.

Faydalari:
  - SEC'e nazik trafik (saatte ~120 sirket, saniyede 8 istek sinirinin cok altinda)
  - Her saat gorunur ilerleme; hicbir kosu 20 dakikadan uzun surmez
  - Bir parti coker se yalnizca o parti yeniden islenir, tur kaybolmaz
  - Ucretsiz Finnhub/FRED kotalari asilmaz

Durum dosyalari:
  data/scan_state.json        kuyruk, imlec, sayaclar, eleme sebepleri
  data/survivors/<T>.json     Asama 0-2'yi gecenlerin sikistirilmis goruntusu

Asama 0-2 parti sirasinda calisir (sirket bazli, komsuya ihtiyac yok).
Asama 3-4 tur sonunda calisir (goreli ucuzluk ve yuzdelikler tum havuzu ister).
"""

from __future__ import annotations

import shutil

from . import config, funnel, pipeline, validate, watchlist
from .config import DATA_DIR, SEED_TICKERS, sector_for_sic
from .fundamentals import build_annual_fundamentals
from .metrics import track_for
from .util import num, read_json, today_iso, utc_now_iso, write_json

STATE_PATH = DATA_DIR / "scan_state.json"
SURVIVOR_DIR = DATA_DIR / "survivors"

DEFAULT_BATCH_SIZE = 120

# Anlik goruntude saklanan yillik kalemler — Asama 2'nin nakit donusumu ve
# "hasilat + brut marj birlikte dusuyor" testleri bunlari ister.
SNAPSHOT_ANNUAL_FIELDS = ("period_end", "revenue", "cost_of_revenue",
                          "gross_profit", "net_income", "cfo")


# --------------------------------------------------------------------------
# Durum
# --------------------------------------------------------------------------
def empty_state() -> dict:
    return {
        "cycle": 0,
        "cycle_started": None,
        "batch_size": DEFAULT_BATCH_SIZE,
        "cursor": 0,
        "queue": [],
        "processed": 0,
        "survivor_count": 0,
        "failed": [],
        "kill_counts": {},
        "stage_counts": {"0": {"in": 0, "out": 0},
                         "1": {"in": 0, "out": 0},
                         "2": {"in": 0, "out": 0}},
        "last_batch_at": None,
        "last_finalized": None,
        "source": "scan",
    }


def load_state() -> dict:
    state = read_json(STATE_PATH)
    if not isinstance(state, dict) or "queue" not in state:
        return empty_state()
    base = empty_state()
    base.update(state)
    return base


def save_state(state: dict) -> bool:
    return write_json(STATE_PATH, state)


def progress(state: dict) -> dict:
    total = len(state.get("queue") or [])
    done = min(state.get("cursor", 0), total)
    return {
        "cycle": state.get("cycle", 0),
        "done": done,
        "total": total,
        "pct": round(done / total * 100, 1) if total else 0.0,
        "remaining": max(total - done, 0),
        "survivors": state.get("survivor_count", 0),
    }


# --------------------------------------------------------------------------
# Tur baslatma
# --------------------------------------------------------------------------
def start_cycle(state: dict, *, tickers: list[str] | None = None,
                batch_size: int | None = None, keep_survivors: bool = False) -> dict:
    """Yeni bir tarama turu baslatir; kuyrugu bastan kurar.

    ``keep_survivors=False`` onceki turun hayatta kalanlarini siler — aksi
    halde artik evrende olmayan ya da artik filtreleri gecmeyen sirketler
    havuzda kalir ve yuzdelikleri bozar.
    """
    queue = tickers if tickers is not None else pipeline.universe_tickers()

    if not keep_survivors and SURVIVOR_DIR.exists():
        shutil.rmtree(SURVIVOR_DIR)
    SURVIVOR_DIR.mkdir(parents=True, exist_ok=True)

    new = empty_state()
    new.update({
        "cycle": state.get("cycle", 0) + 1,
        "cycle_started": today_iso(),
        "batch_size": batch_size or state.get("batch_size", DEFAULT_BATCH_SIZE),
        "queue": queue,
        "last_finalized": state.get("last_finalized"),
    })
    print(f"[tarama] Tur {new['cycle']} basladi — kuyrukta {len(queue)} sembol")
    return new


# --------------------------------------------------------------------------
# Anlik goruntu (sikistirilmis satir)
# --------------------------------------------------------------------------
def to_snapshot(row: dict) -> dict:
    """Degerlendirilmis satiri diske yazilabilir kompakt bicime cevirir.

    Ham companyfacts JSON'u (sirket basina 2-20 MB) SAKLANMAZ; yalnizca
    Asama 3-4'un ve kart basliklarinin ihtiyaci olan alanlar tutulur.
    Tam kart, tur sonunda yalnizca ilk 50 icin yeniden uretilir.
    """
    f = row.get("fundamentals")
    annuals = []
    if f is not None:
        for p in f.sorted_annuals()[-5:]:
            entry = {k: num(getattr(p, k, None)) for k in SNAPSHOT_ANNUAL_FIELDS
                     if k != "period_end"}
            entry["period_end"] = p.period_end
            annuals.append(entry)

    return {
        "ticker": row["ticker"],
        "cik": row.get("cik"),
        "name": row.get("name", ""),
        "sic": row.get("sic"),
        "sector": row.get("sector", ""),
        "exchange": row.get("exchange", ""),
        "ipo_date": row.get("ipo_date"),
        "track": row.get("track"),
        "metrics": row.get("metrics", {}),
        "meta": row.get("meta", {}),
        "flags": row.get("flags", {}),
        "own_pct": row.get("own_pct", {}),
        "avg_dollar_volume_30d": row.get("avg_dollar_volume_30d"),
        "annuals": annuals,
        "passed_stages": row.get("passed_stages", []),
        "scanned_at": today_iso(),
        "cycle": row.get("cycle"),
    }


def from_snapshot(snap: dict) -> dict:
    """Anlik goruntuden Asama 3-4'e girebilecek bir satir kurar."""
    fundamentals = build_annual_fundamentals(
        snap["ticker"], snap.get("annuals") or [],
        name=snap.get("name", ""), cik=snap.get("cik"),
        sic=snap.get("sic"), exchange=snap.get("exchange", ""),
    )
    return {
        "ticker": snap["ticker"],
        "cik": snap.get("cik"),
        "name": snap.get("name", ""),
        "sic": snap.get("sic"),
        "sector": snap.get("sector") or sector_for_sic(snap.get("sic")),
        "exchange": snap.get("exchange", ""),
        "ipo_date": snap.get("ipo_date"),
        "track": snap.get("track") or track_for(
            snap.get("metrics", {}), config.STAGE3["track_b_operating_margin_pct"]),
        "metrics": snap.get("metrics", {}),
        "meta": snap.get("meta", {}),
        "flags": snap.get("flags", {}),
        "own_pct": snap.get("own_pct", {}),
        "avg_dollar_volume_30d": snap.get("avg_dollar_volume_30d"),
        "fundamentals": fundamentals,
        "passed_stages": list(snap.get("passed_stages") or []),
        "kill_reason": None,
        "killed_at": None,
        "from_snapshot": True,
    }


def survivor_path(ticker: str):
    return SURVIVOR_DIR / f"{ticker.upper()}.json"


def load_survivors() -> list[dict]:
    if not SURVIVOR_DIR.exists():
        return []
    out = []
    for path in sorted(SURVIVOR_DIR.glob("*.json")):
        snap = read_json(path)
        if isinstance(snap, dict) and snap.get("ticker"):
            out.append(snap)
    return out


# --------------------------------------------------------------------------
# Parti
# --------------------------------------------------------------------------
def run_batch(state: dict, *, size: int | None = None,
              bench: list | None = None) -> dict:
    """Kuyruktan bir parti isler: Asama 0, 1, 2.

    Asama 3-4 BURADA CALISMAZ — goreli ucuzluk ve sektor yuzdelikleri
    havuzun tamamini ister; onlar tur sonunda ``finalize`` ile calisir.
    """
    size = size or state.get("batch_size", DEFAULT_BATCH_SIZE)
    queue = state["queue"]
    start = state["cursor"]
    batch = queue[start:start + size]

    if not batch:
        return state

    SURVIVOR_DIR.mkdir(parents=True, exist_ok=True)
    counts = state["stage_counts"]
    kills = state["kill_counts"]

    print(f"[tarama] Tur {state['cycle']} · {start + 1}-{start + len(batch)} / {len(queue)}")

    for i, ticker in enumerate(batch, 1):
        if i % 25 == 0:
            print(f"  {i}/{len(batch)}")

        f = pipeline.load_company(ticker)
        if f is None:
            state["failed"] = (state["failed"] + [ticker])[-200:]
            continue

        row = funnel.evaluate(f, benchmark=bench or [])
        row["cycle"] = state["cycle"]

        killed_at, reason = _run_early_stages(row, counts)
        if reason:
            kills[reason] = kills.get(reason, 0) + 1
            # Onceki turdan kalan bir kayit varsa temizle
            path = survivor_path(ticker)
            if path.exists():
                path.unlink()
        else:
            from . import percentiles
            row["own_pct"] = percentiles.own_history_percentiles(f, row["metrics"])
            write_json(survivor_path(ticker), to_snapshot(row))

        state["processed"] += 1

    state["cursor"] = start + len(batch)
    state["survivor_count"] = len(list(SURVIVOR_DIR.glob("*.json")))
    state["last_batch_at"] = utc_now_iso()
    return state


def _run_early_stages(row: dict, counts: dict) -> tuple[int | None, str | None]:
    """Asama 0 -> 1 -> 2. Ilk basarisiz asamayi ve sebebini doner."""
    counts["0"]["in"] += 1
    reason = funnel.stage0(row)
    if reason:
        return 0, reason
    counts["0"]["out"] += 1
    row["passed_stages"].append(0)

    counts["1"]["in"] += 1
    reason = funnel.stage1(row)
    if reason:
        return 1, reason
    counts["1"]["out"] += 1
    row["passed_stages"].append(1)

    row["track"] = track_for(row["metrics"],
                             config.STAGE3["track_b_operating_margin_pct"])

    counts["2"]["in"] += 1
    reason = funnel.stage2(row, row["track"])
    if reason:
        return 2, reason
    counts["2"]["out"] += 1
    row["passed_stages"].append(2)
    return None, None


# --------------------------------------------------------------------------
# Tur sonu
# --------------------------------------------------------------------------
def finalize(state: dict, *, ctx: dict | None = None,
             bench: list | None = None, build_cards: bool = True) -> dict:
    """Kuyruk bitince Asama 3-4'u calistirir, kartlari ve ozet dosyalari yazar."""
    snapshots = load_survivors()
    print(f"[tarama] Tur {state['cycle']} tamamlandi — "
          f"{state['processed']} sirket islendi, {len(snapshots)} tanesi Asama 2'yi gecti")

    if not snapshots:
        print("[tarama] Hayatta kalan yok; Asama 3-4 atlandi.")
        state["last_finalized"] = today_iso()
        return state

    rows = [from_snapshot(s) for s in snapshots]

    log = {"stages": [
        {"stage": 0, "name": funnel.STAGE_NAMES[0],
         "input": state["stage_counts"]["0"]["in"], "output": state["stage_counts"]["0"]["out"]},
        {"stage": 1, "name": funnel.STAGE_NAMES[1],
         "input": state["stage_counts"]["1"]["in"], "output": state["stage_counts"]["1"]["out"]},
        {"stage": 2, "name": funnel.STAGE_NAMES[2],
         "input": state["stage_counts"]["2"]["in"], "output": state["stage_counts"]["2"]["out"]},
    ]}

    # own_pct anlik goruntude hazir; yeniden hesaplamak icin fiyat gecmisi gerekirdi
    selected, sector_table = funnel.rank(rows, log=log, compute_own_pct=False)

    log["kill_reasons"] = dict(sorted(state["kill_counts"].items(),
                                      key=lambda kv: kv[1], reverse=True)[:30])

    for s in log["stages"]:
        print(f"   Asama {s['stage']} {s['name']:16} {s['input']:6} -> {s['output']:6}")

    if build_cards:
        ctx = ctx if ctx is not None else pipeline.context([])
        manual = set(watchlist.tickers())

        # Tam kart yalnizca ilk 50 + tohum + elle eklenenler icin uretilir;
        # bu, companyfacts'i yeniden indirmeyi ~60 sirketle sinirlar.
        wanted = {r["ticker"] for r in selected} | set(SEED_TICKERS) | manual
        print(f"[tarama] {len(wanted)} sirket icin tam kart uretiliyor...")

        by_ticker = {r["ticker"]: r for r in rows}
        card_rows = []
        for ticker in sorted(wanted):
            f = pipeline.load_company(ticker)
            if f is None:
                continue
            full = funnel.evaluate(f, benchmark=bench or [])
            full["is_manual"] = ticker in manual
            base = by_ticker.get(ticker)
            full["passed_stages"] = base["passed_stages"] if base else []
            card_rows.append(full)

        selected_tickers = {r["ticker"] for r in selected}
        for row in card_rows:
            source = ("manual" if row["ticker"] in manual
                      else config.SEED_SOURCE_TAG if row["ticker"] in SEED_TICKERS
                      else "funnel")
            pipeline.build_cards([row], source=source, sector_table=sector_table,
                                 ctx=ctx, bench=bench or [])
        print(f"[tarama] {len(card_rows)} kart yazildi "
              f"({len(selected_tickers)} aday, {len(manual)} elle eklenen)")

        written = [c for c in (pipeline.read_json(pipeline.CARDS_DIR / f"{t}.json")
                               for t in sorted(wanted)) if isinstance(c, dict)]
        summary = validate.summarize(written)
        print(f"[tarama] Veri kalitesi: {summary['counts']}")
        state["data_quality"] = summary

    pipeline.write_thresholds()
    pipeline.write_universe(rows, log)
    pipeline.append_funnel_log(log)
    pipeline.refresh_candidates_from_disk()

    state["last_finalized"] = today_iso()
    state["last_log"] = log
    return state


# --------------------------------------------------------------------------
# Ust seviye kosu
# --------------------------------------------------------------------------
def run(*, batch_size: int | None = None, new_cycle: bool = False,
        tickers: list[str] | None = None, build_cards: bool = True) -> dict:
    """Bir saatlik parti calistirir; kuyruk bittiyse tur sonunu isler."""
    state = load_state()

    if new_cycle or not state.get("queue"):
        state = start_cycle(state, tickers=tickers, batch_size=batch_size)

    if batch_size:
        state["batch_size"] = batch_size

    bench_map = pipeline.benchmarks()
    bench = bench_map.get("QQQ", [])

    state = run_batch(state, bench=bench)

    p = progress(state)
    print(f"[tarama] Ilerleme: {p['done']}/{p['total']} (%{p['pct']}) · "
          f"hayatta kalan {p['survivors']}")

    if state["cursor"] >= len(state["queue"]):
        ctx = pipeline.context([])
        state = finalize(state, ctx=ctx, bench=bench, build_cards=build_cards)
        # Tur sonu isini HEMEN kaydet. Yeni kuyrugu kurmak ag ister ve
        # basarisiz olabilir; o yuzden once biten turu guvene al, yoksa
        # saatlerce suren tarama sonucu tek bir ag hatasiyla cope gider.
        save_state(state)
        try:
            state = start_cycle(state, tickers=tickers,
                                batch_size=state.get("batch_size"))
        except Exception as exc:  # noqa: BLE001
            print(f"[tarama] Yeni tur kurulamadi ({exc}); "
                  f"sonraki kosuda tekrar denenecek.")
            state["queue"] = []
            state["cursor"] = 0

    save_state(state)
    return state
