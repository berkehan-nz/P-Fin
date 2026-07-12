"""Komut satırı girişleri (GitHub Actions ve kullanıcı bunları çağırır).

  python -m pfin.cli morning-run [--dry-run] [--no-mail] [--out out]
  python -m pfin.cli sentinel-run [--no-mail]
  python -m pfin.cli record-fill --symbol THYAO --market BIST --side buy \
        --shares 20 --price 255 --stop 240 --thesis "..." --refuter "..."
  python -m pfin.cli data-check [--symbol ASELS --market BIST]
  python -m pfin.cli show
  python -m pfin.cli init-state
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import STATE_PATH, load_config
from .memory.store import load_state, save_state


def _write_outputs(out_dir: Path, subject: str, html: str, text: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "briefing.html").write_text(html, encoding="utf-8")
    (out_dir / "briefing.txt").write_text(f"{subject}\n\n{text}", encoding="utf-8")


def cmd_morning(args) -> int:
    from .agent.morning import run_morning, _stub_result
    from .cost.budget import over_budget
    from .report.briefing import build_briefing
    from .report.mailer import send_mail

    config = load_config()
    state = load_state()

    caller = None
    if args.dry_run:
        caller = lambda *a, **k: _stub_result("dry-run: LLM atlandı")
    elif over_budget(state.budget, config):
        # §6 self-throttle: bütçe tavanı aşıldıysa pahalı LLM turunu atla (sessizce aşma)
        caller = lambda *a, **k: _stub_result("bütçe tavanı aşıldı — derin tur seyreltildi")

    result = run_morning(state, config, model_caller=caller)
    subject, html, text = build_briefing(result, config)

    if args.out:
        _write_outputs(Path(args.out), subject, html, text)
    sent = False
    if not args.no_mail:
        try:
            sent = send_mail(config.secrets, subject, html, text)
        except Exception as exc:  # mail hatası run'ı düşürmesin
            print(f"[uyarı] mail gönderilemedi: {exc!r}", file=sys.stderr)

    save_state(state)
    print(f"[morning] {subject}")
    print(f"[morning] öneri={len(result.guardrails.accepted())} "
          f"reddedilen={len(result.guardrails.rejected())} "
          f"zorunlu-çıkış={len(result.guardrails.forced_exits)} "
          f"maliyet=${result.cost_usd:.3f} mail={'gönderildi' if sent else 'atlandı'} "
          f"stub={result.used_stub}")
    return 0


def cmd_sentinel(args) -> int:
    from .report.alert import build_alert
    from .report.mailer import send_mail
    from .watchman import sentinel

    config = load_config()
    state = load_state()
    events = sentinel.check(state, config)
    critical = [e for e in events if e.severity == "critical"]

    sent = False
    if events and not args.no_mail:
        subject, html, text = build_alert([e.to_dict() for e in events], config)
        try:
            sent = send_mail(config.secrets, subject, html, text)
        except Exception as exc:
            print(f"[uyarı] acil mail gönderilemedi: {exc!r}", file=sys.stderr)
    if events:
        sentinel.mark_sent(state, events)
        from .memory.schema import LogEntry
        state.log.append(LogEntry(kind="sentinel", message=(
            f"Nöbetçi: {len(events)} olay ({len(critical)} kritik). "
            f"mail={'gönderildi' if sent else 'atlandı'}")))
    save_state(state)
    print(f"[sentinel] olay={len(events)} kritik={len(critical)} "
          f"mail={'gönderildi' if sent else 'atlandı'}")
    for e in events:
        print(f"  - [{e.severity}] {e.symbol} {e.kind}: {e.message}")
    return 0


def cmd_record_fill(args) -> int:
    from .pnl.ledger import LedgerError, record_fill

    config = load_config()
    state = load_state()
    try:
        result = record_fill(
            state, symbol=args.symbol, market=args.market, side=args.side,
            shares=args.shares, price=args.price, date=args.date, stop=args.stop,
            thesis=args.thesis or "", refuter=args.refuter or "",
            invalidation=args.invalidation or "", name=args.name or "",
            source=args.source)
    except LedgerError as exc:
        print(f"[hata] {exc}", file=sys.stderr)
        return 2
    save_state(state)
    print(f"[fill] {result.get('note','')}")
    if "realized_pnl" in result:
        print(f"[fill] gerçekleşen P&L: {result['realized_pnl']:,.2f} ₺ | "
              f"toplam: {state.realized_pnl_try:,.2f} ₺")
    print(f"[fill] nakit: {state.cash_try:,.2f} ₺ | portföy: {state.portfolio_value():,.2f} ₺")
    return 0


def cmd_data_check(args) -> int:
    """Veri katmanının GERÇEKTEN veri getirdiğini kanıtlar (Adım 2)."""
    from .data import macro, prices
    from .data.ratecounter import RateCounter
    from .memory.schema import RateLimitState

    config = load_config()
    print("== Veri katmanı canlı kontrol ==")
    sym = args.symbol
    mkt = (args.market or "BIST").upper()
    if sym:
        counter = RateCounter(RateLimitState())
        q = prices.quote_for(sym, mkt, config.secrets.twelvedata_api_key, counter)
        print(f"[quote] {sym} ({mkt}): price={q.price} {q.currency} "
              f"chg={q.change_pct} src={q.source} err={q.error}")
        fin = prices.financials_for(sym, mkt)
        print(f"[financials] {sym}: period={fin.period} items={list(fin.items.items())[:4]} "
              f"err={fin.error}")
    else:
        for s in config.get("universe", "bist", default=[])[:2]:
            q = prices.get_bist_quote(s)
            print(f"[BIST] {s}: price={q.price} chg={q.change_pct} err={q.error}")
    idx = macro.get_index_quote(config.index_symbol)
    print(f"[index] {config.index_symbol}: price={idx.price} chg={idx.change_pct} err={idx.error}")
    tufe, note = macro.get_tufe_yoy(config.secrets.evds_api_key)
    print(f"[tufe] yoy={tufe} ({note})")
    return 0


def cmd_show(args) -> int:
    config = load_config()
    state = load_state()
    print(json.dumps({
        "portfolio_value_try": round(state.portfolio_value(), 2),
        "cash_try": round(state.cash_try, 2),
        "cash_pct": round(state.cash_pct(), 3),
        "realized_pnl_try": state.realized_pnl_try,
        "open_positions": [{"symbol": p.symbol, "shares": p.shares, "entry": p.entry_price,
                            "stop": p.stop, "current": p.current_price} for p in state.open_positions()],
        "budget_usd": round(state.budget.spend_usd, 2),
        "throttled": state.budget.throttled,
        "sources": [{"name": c.name, "trust": c.trust, "claims": len(c.claims)} for c in state.sources],
        "last_run_at": state.meta.last_run_at,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_init_state(args) -> int:
    from .memory.schema import State
    from .sources.scorecard import ensure_seed

    if STATE_PATH.exists() and not args.force:
        print("state.json zaten var (--force ile üzerine yaz)", file=sys.stderr)
        return 1
    state = State(cash_try=float(args.cash))
    ensure_seed(state)
    save_state(state)
    print(f"[init] state.json oluşturuldu (nakit {state.cash_try:,.2f} ₺)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pfin", description="Kişisel Finans Ajanı")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("morning-run", help="Sabah turu (§3.2)")
    m.add_argument("--dry-run", action="store_true", help="LLM çağırma; akışı stub ile yürüt")
    m.add_argument("--no-mail", action="store_true")
    m.add_argument("--out", default="out", help="Brifing çıktı klasörü")
    m.set_defaults(func=cmd_morning)

    s = sub.add_parser("sentinel-run", help="Nöbetçi taraması (§3.1)")
    s.add_argument("--no-mail", action="store_true")
    s.set_defaults(func=cmd_sentinel)

    f = sub.add_parser("record-fill", help="Gerçekleşen işlemi kaydet (§3.6)")
    f.add_argument("--symbol", required=True)
    f.add_argument("--market", required=True, choices=["BIST", "US", "TEFAS"])
    f.add_argument("--side", required=True, choices=["buy", "sell"])
    f.add_argument("--shares", required=True, type=float)
    f.add_argument("--price", required=True, type=float)
    f.add_argument("--date")
    f.add_argument("--stop", type=float)
    f.add_argument("--thesis")
    f.add_argument("--refuter")
    f.add_argument("--invalidation")
    f.add_argument("--name")
    f.add_argument("--source")
    f.set_defaults(func=cmd_record_fill)

    d = sub.add_parser("data-check", help="Veri katmanını canlı kanıtla (Adım 2)")
    d.add_argument("--symbol")
    d.add_argument("--market")
    d.set_defaults(func=cmd_data_check)

    sh = sub.add_parser("show", help="State özeti")
    sh.set_defaults(func=cmd_show)

    i = sub.add_parser("init-state", help="Boş state.json oluştur")
    i.add_argument("--cash", default="50000", help="Başlangıç nakiti (₺)")
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=cmd_init_state)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
