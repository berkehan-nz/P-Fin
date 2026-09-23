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
import time
from datetime import datetime, timezone

from . import config, funnel, pipeline, validate, watchlist
from .config import DATA_DIR, SEED_TICKERS, sector_for_sic
from .fundamentals import build_annual_fundamentals
from .metrics import track_for
from .util import (TimeoutHit, Watchdog, num, read_json, time_limit, today_iso,
                   utc_now_iso, write_json)

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
        "timeouts": {},
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


# Tarama saatte bir calisir. Uc saat hicbir parti islenmediyse bir sey
# bozulmus demektir. 22 Eylul'de iki GUN boyunca kimse fark etmedi cunku
# hicbir yerde "en son ne zaman ilerledi" yazmiyordu.
STALL_HOURS = 3


def stalled_hours(state: dict) -> float | None:
    """Son partinin uzerinden gecen saat. Hic parti yoksa None."""
    stamp = state.get("last_batch_at")
    if not stamp:
        return None
    try:
        last = datetime.fromisoformat(str(stamp))
    except ValueError:
        return None
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - last
    return round(delta.total_seconds() / 3600, 1)


def progress(state: dict) -> dict:
    total = len(state.get("queue") or [])
    done = min(state.get("cursor", 0), total)
    idle = stalled_hours(state)
    return {
        "cycle": state.get("cycle", 0),
        "done": done,
        "total": total,
        "pct": round(done / total * 100, 1) if total else 0.0,
        "remaining": max(total - done, 0),
        "survivors": state.get("survivor_count", 0),
        "last_batch_at": state.get("last_batch_at"),
        "idle_hours": idle,
        "stalled": bool(idle is not None and idle >= STALL_HOURS
                        and done < total),
    }


# --------------------------------------------------------------------------
# Tur baslatma
# --------------------------------------------------------------------------
def cycle_in_progress(state: dict) -> bool:
    """Tur devam ediyor mu? (kuyruk var ve bitmemis)"""
    queue = state.get("queue") or []
    return bool(queue) and state.get("cursor", 0) < len(queue)


def start_cycle(state: dict, *, tickers: list[str] | None = None,
                batch_size: int | None = None, keep_survivors: bool = False) -> dict:
    """Yeni bir tarama turu baslatir; kuyrugu bastan kurar.

    ``keep_survivors=False`` onceki turun hayatta kalanlarini siler — aksi
    halde artik evrende olmayan ya da artik filtreleri gecmeyen sirketler
    havuzda kalir ve yuzdelikleri bozar.

    DIKKAT: bu islem YARIM KALAN BIR TURU COPE ATAR. Cagiran tarafin
    ``cycle_in_progress`` ile kontrol etmesi gerekir; ``run()`` bunu yapar.
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


def write_survivors_index() -> bool:
    """``data/survivors.json`` — Asama 2'yi gecenlerin KOMPAKT listesi.

    Pano bir klasoru listeleyemez; 157 ayri dosyayi tek tek cekmek de sacma.
    Huni sayfasi bu tek dosyayi okur. Tur bitmeden puan olmadigi icin burada
    puan YOKTUR — yalnizca kimlik ve ham metrikler vardir; sayfada da boyle
    sunulur ki "puansiz" ile "puani dusuk" karistirilmasin.
    """
    rows = []
    for snap in load_survivors():
        m = snap.get("metrics") or {}
        rows.append({
            "ticker": snap.get("ticker"),
            "name": snap.get("name"),
            "sector": snap.get("sector"),
            "track": snap.get("track"),
            "exchange": snap.get("exchange"),
            "market_cap_musd": (snap.get("meta") or {}).get("market_cap_musd"),
            "scanned_at": snap.get("scanned_at"),
            "cycle": snap.get("cycle"),
            "metrics": {k: m.get(k) for k in (
                "ev_ebit", "ev_sales", "ev_gross_profit", "fcf_yield_ev",
                "rev_growth_ttm", "gross_margin", "roic", "rule_of_40",
                "net_debt_to_ebitda", "piotroski_f")},
        })
    rows.sort(key=lambda r: (r.get("sector") or "", r.get("ticker") or ""))
    # Yol SURVIVOR_DIR'den turetilir, DATA_DIR'den DEGIL: testler SURVIVOR_DIR'i
    # gecici klasore yonlendiriyor ama DATA_DIR'i yonlendirmiyor. Sabit
    # DATA_DIR kullanilirsa test kosusu GERCEK data/survivors.json'i sifirlar.
    return write_json(SURVIVOR_DIR.parent / "survivors.json",
                      {"count": len(rows), "survivors": rows, "source": "scan"})


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
def load_one(ticker: str, state: dict) -> object | None:
    """Tek sirketi ZAMAN SINIRI ile yukler. Asilirsa None doner, parti surer.

    Ayni sembol ust uste ``COMPANY_TIMEOUT_SKIP_AFTER`` kez asarsa artik hic
    denenmez: bir sonraki turda da 90 saniye harcamasinin anlami yok.
    """
    timeouts = state.setdefault("timeouts", {})
    if timeouts.get(ticker, 0) >= config.COMPANY_TIMEOUT_SKIP_AFTER:
        return None
    try:
        with time_limit(config.COMPANY_TIMEOUT_SEC, f"{ticker} verisi"):
            return pipeline.load_company(ticker)
    except TimeoutHit as exc:
        timeouts[ticker] = timeouts.get(ticker, 0) + 1
        print(f"  [zaman asimi] {exc} — atlandi "
              f"({timeouts[ticker]}. kez)", flush=True)
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"  [hata] {ticker}: {str(exc)[:120]}", flush=True)
        return None


def run_batch(state: dict, *, size: int | None = None,
              bench: list | None = None, deadline: float | None = None,
              beat=None) -> dict:
    """Kuyruktan bir parti isler: Asama 0, 1, 2.

    Asama 3-4 BURADA CALISMAZ — goreli ucuzluk ve sektor yuzdelikleri
    havuzun tamamini ister; onlar tur sonunda ``finalize`` ile calisir.

    IMLEC HER SIRKETTEN SONRA ILERLER ve durum araliklarla diske yazilir.
    Onceki surumde imlec yalnizca parti SONUNDA guncelleniyordu; tek bir
    sirket asildiginda is akisi partiyi 50. dakikada iptal ediyor, "Commit"
    adimi atlaniyor ve 120 sirketlik emek tamamen kayboluyordu. Sistem
    22 Eylul'den beri her saat ayni sirkette bu sekilde takiliydi.
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
    timeouts = state.setdefault("timeouts", {})

    print(f"[tarama] Tur {state['cycle']} · {start + 1}-{start + len(batch)} "
          f"/ {len(queue)}", flush=True)

    for i, ticker in enumerate(batch, 1):
        if deadline is not None and time.monotonic() >= deadline:
            print(f"[tarama] Sure butcesi doldu — parti {i - 1}/{len(batch)} "
                  f"sirkette duzgun sonlandi, ilerleme kaydedildi.", flush=True)
            break

        if beat is not None:
            beat(f"{ticker} ({start + i}/{len(queue)})")
        if i % 10 == 0:
            print(f"  {i}/{len(batch)} · {ticker}", flush=True)

        if timeouts.get(ticker, 0) >= config.COMPANY_TIMEOUT_SKIP_AFTER:
            print(f"  [atlandi] {ticker}: daha once "
                  f"{timeouts[ticker]} kez zaman asimina ugradi", flush=True)
        else:
            f = load_one(ticker, state)
            if f is None:
                state["failed"] = (state["failed"] + [ticker])[-200:]
            else:
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
                    row["own_pct"] = percentiles.own_history_percentiles(
                        f, row["metrics"])
                    write_json(survivor_path(ticker), to_snapshot(row))

        # Sirket bitti: imleci ILERLET. Buradan sonra surec olse bile bu
        # sirket bir daha islenmez.
        state["processed"] += 1
        state["cursor"] = start + i
        state["last_batch_at"] = utc_now_iso()

        if i % config.STATE_FLUSH_EVERY == 0:
            state["survivor_count"] = len(list(SURVIVOR_DIR.glob("*.json")))
            save_state(state)

    state["survivor_count"] = len(list(SURVIVOR_DIR.glob("*.json")))
    state["last_batch_at"] = utc_now_iso()
    save_state(state)
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
# Ara sonuc — tur bitmeden gosterilecek gecici siralama
# --------------------------------------------------------------------------
# Bir tur 5-10 gun suruyor. Asama 3-4'u yalnizca tur sonunda calistirmak,
# kullanicinin bu sure boyunca HICBIR yeni sirket gormemesi demek. Oysa
# biriken hayatta kalanlar uzerinden simdiden siralama yapilabilir; yalnizca
# bunun GECICI oldugu ve havuz buyudukce degisecegi acikca soylenmeli.
INTERIM_MIN_SURVIVORS = 15      # bu sayinin altinda siralama anlamsiz
INTERIM_CARDS_PER_BATCH = 12    # her partide en fazla kac yeni tam kart


def _stage_log(state: dict) -> list[dict]:
    """Asama 0-2 sayaclarini gunluk bicimine cevirir."""
    counts = state.get("stage_counts") or {}
    out = []
    for n in (0, 1, 2):
        c = counts.get(str(n))
        if c:
            out.append({"stage": n, "name": funnel.STAGE_NAMES[n],
                        "input": c["in"], "output": c["out"]})
    return out


def interim(state: dict, *, ctx: dict | None = None, bench: list | None = None,
            build_cards: bool = True, deadline: float | None = None,
            beat=None) -> dict | None:
    """Biriken hayatta kalanlari siralar ve GECICI aday listesi yazar.

    Tur sonundaki ``finalize`` ile ayni kodu (``funnel.rank``) kullanir;
    fark, sonucun ``partial: true`` ile isaretlenmesi ve kart uretiminin
    parti basina sinirlanmasi.
    """
    snapshots = load_survivors()
    if len(snapshots) < INTERIM_MIN_SURVIVORS:
        return None

    rows = [from_snapshot(s) for s in snapshots]
    log = {"stages": _stage_log(state)}
    selected, sector_table = funnel.rank(rows, log=log, compute_own_pct=False)

    # HUNI GUNLUGU HER PARTIDE. Onceden yalnizca tur sonunda (finalize)
    # yaziliyordu; tur 1 bir kilitlenme duzeltmesiyle sifirlaninca finalize
    # hic calismadi ve funnel_log.json 9 Eylul'den beri bos kaldi. Ayni
    # gunun kaydi uzerine yazilir; tur ici kayitlar "partial" isaretlidir.
    log["kill_reasons"] = dict(sorted(state["kill_counts"].items(),
                                      key=lambda kv: kv[1], reverse=True)[:30])
    pipeline.append_funnel_log(log, partial=True, cycle=state.get("cycle"),
                               scanned=progress(state)["done"])

    p = progress(state)
    if build_cards:
        _build_missing_cards(selected, sector_table, ctx=ctx, bench=bench,
                             limit=INTERIM_CARDS_PER_BATCH,
                             deadline=deadline, state=state, beat=beat)

    pipeline.refresh_candidates_from_disk(partial={
        "is_partial": True,
        "scanned": p["done"],
        "universe": p["total"],
        "pct": p["pct"],
        "survivors": len(snapshots),
        "ranked": len(selected),
        "cycle": p["cycle"],
        # Panoda "en son ne zaman ilerledi" yazsin ki bir daha iki gun
        # sessizce durmasin.
        "last_batch_at": p["last_batch_at"],
        "remaining": p["remaining"],
    })
    print(f"[tarama] Ara sonuc: {len(snapshots)} hayatta kalan siralandi, "
          f"{len(selected)} aday (tarama %{p['pct']})")
    return {"selected": selected, "sector_table": sector_table}


def _build_missing_cards(selected: list[dict], sector_table: dict, *,
                         ctx: dict | None, bench: list | None,
                         limit: int, deadline: float | None = None,
                         state: dict | None = None, beat=None) -> int:
    """Aday olup karti olmayan sirketler icin tam kart uretir (sinirli sayida).

    Her kart bir companyfacts indirmesi demek; parti suresini sismemek icin
    kosu basina ``limit`` taneyle sinirli. Kalanlar sonraki partilerde uretilir.
    """
    missing = [r for r in selected
               if not (pipeline.CARDS_DIR / f"{r['ticker']}.json").exists()]
    if not missing:
        return 0

    ctx = ctx if ctx is not None else pipeline.context([])
    built = 0
    for row in missing[:limit]:
        if deadline is not None and time.monotonic() >= deadline:
            print("[tarama] Sure butcesi doldu — kalan kartlar sonraki kosuda.",
                  flush=True)
            break
        if beat is not None:
            beat(f"kart {row['ticker']}")
        f = load_one(row["ticker"], state if state is not None else {})
        if f is None:
            continue
        full = funnel.evaluate(f, benchmark=bench or [])
        full["passed_stages"] = row.get("passed_stages", [])
        pipeline.build_cards([full], source="funnel", sector_table=sector_table,
                             ctx=ctx, bench=bench or [])
        built += 1
    if built:
        print(f"[tarama] {built} yeni kart uretildi "
              f"({len(missing) - built} tanesi sonraki partilere kaldi)")
    return built


# --------------------------------------------------------------------------
# Tur sonu
# --------------------------------------------------------------------------
def finalize(state: dict, *, ctx: dict | None = None,
             bench: list | None = None, build_cards: bool = True,
             beat=None) -> dict:
    """Kuyruk bitince Asama 3-4'u calistirir, kartlari ve ozet dosyalari yazar."""
    snapshots = load_survivors()
    print(f"[tarama] Tur {state['cycle']} tamamlandi — "
          f"{state['processed']} sirket islendi, {len(snapshots)} tanesi Asama 2'yi gecti")

    if not snapshots:
        print("[tarama] Hayatta kalan yok; Asama 3-4 atlandi.")
        state["last_finalized"] = today_iso()
        return state

    rows = [from_snapshot(s) for s in snapshots]

    log = {"stages": _stage_log(state)}

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
            if beat is not None:
                beat(f"tur sonu karti {ticker}")
            f = load_one(ticker, state)
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
        tickers: list[str] | None = None, build_cards: bool = True,
        force: bool = False) -> dict:
    """Bir saatlik parti calistirir; kuyruk bittiyse tur sonunu isler."""
    state = load_state()

    if new_cycle and cycle_in_progress(state) and not force:
        # Yarim kalan tur cope gitmesin. Haftalik kosu her pazar --new-cycle
        # cagiriyordu; tur 5-10 gun surdugu icin her seferinde sifirlaniyor
        # ve SONUC HIC URETILMIYORDU. Yeni tur ancak mevcut tur bitince
        # ya da acikca --force verilince baslar.
        p = progress(state)
        print(f"[tarama] Tur {p['cycle']} devam ediyor ({p['done']}/{p['total']}, "
              f"%{p['pct']}) — yeni tur baslatilmadi. Zorlamak icin --force.")
    elif new_cycle or not state.get("queue"):
        state = start_cycle(state, tickers=tickers, batch_size=batch_size)

    # Tek seferlik --batch, kayitli parti boyutunu KALICI degistirmesin;
    # yalnizca bu kosuda gecerli olsun.
    run_batch_size = batch_size or state.get("batch_size", DEFAULT_BATCH_SIZE)

    # ZAMAN BUTCESI. Is akisinin sert siniri (50 dk) partiyi IPTAL eder ve
    # "Commit" adimini atlar; o noktaya gelinirse kosu bosa gider. Kendi
    # butcemiz her zaman once dolar, parti duzgun biter ve ilerleme islenir.
    started = time.monotonic()
    batch_deadline = started + config.BATCH_BUDGET_SEC
    run_deadline = started + config.RUN_BUDGET_SEC

    # SON CARE: Python sinyali C icinde kilitlenen bir kutuphaneye
    # ulasamaz. O durumda bekci sureci 0 ile kapatir; diske yazilmis
    # imlec korunur ve is akisi commit atar.
    watchdog = Watchdog(config.WATCHDOG_LIMIT_SEC,
                        on_timeout=lambda label: save_state(state)).start()
    beat = watchdog.beat

    try:
        beat("karsilastirma endeksi")
        bench_map = pipeline.benchmarks()
        bench = bench_map.get("QQQ", [])

        state = run_batch(state, size=run_batch_size, bench=bench,
                          deadline=batch_deadline, beat=beat)

        # ARA SONUC: tur bitmesini beklemeden biriken hayatta kalanlari sirala.
        # Tur 5 gun surerken kullanici hicbir yeni sirket gormemeli degil.
        beat("ara sonuc")
        interim(state, ctx=None, bench=bench, build_cards=build_cards,
                deadline=run_deadline, beat=beat)

        # Huni sayfasinin okudugu kompakt liste. Her partide tazelenir ki
        # tur ortasinda da kimlerin gectigi gorunsun.
        beat("hayatta kalanlar dizini")
        write_survivors_index()

        p = progress(state)
        print(f"[tarama] Ilerleme: {p['done']}/{p['total']} (%{p['pct']}) · "
              f"hayatta kalan {p['survivors']}", flush=True)

        if state["cursor"] >= len(state["queue"]):
            beat("tur sonu")
            ctx = pipeline.context([])
            state = finalize(state, ctx=ctx, bench=bench,
                             build_cards=build_cards, beat=beat)
            # Tur sonu isini HEMEN kaydet. Yeni kuyrugu kurmak ag ister ve
            # basarisiz olabilir; o yuzden once biten turu guvene al, yoksa
            # saatlerce suren tarama sonucu tek bir ag hatasiyla cope gider.
            save_state(state)
            try:
                beat("yeni tur kuruluyor")
                state = start_cycle(state, tickers=tickers,
                                    batch_size=state.get("batch_size"))
            except Exception as exc:  # noqa: BLE001
                print(f"[tarama] Yeni tur kurulamadi ({exc}); "
                      f"sonraki kosuda tekrar denenecek.")
                state["queue"] = []
                state["cursor"] = 0
    finally:
        watchdog.stop()

    save_state(state)
    return state
