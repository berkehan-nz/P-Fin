"""Sabah brifingi (§3.5): portföy durumu, piyasa özeti, pozisyon bazlı aksiyon,
kısa gerekçe + kaynak linki, XU100/TÜFE kıyası. Ton: kısa, net, jargonsuz.

Tüm sayılar `facts`/state'ten basılır (LLM metninden DEĞİL — Değişmez #1).
"""
from __future__ import annotations

from datetime import datetime, timezone

from jinja2 import Environment, select_autoescape

from ..config import Config
from ..agent.morning import MorningResult

_env = Environment(autoescape=select_autoescape(["html"]))

DISCLAIMER = ("Bu bir modelin önerisidir, finansal danışmanlık değildir. Model kendinden "
              "emin biçimde yanılabilir. İşlemleri Midas'ta sen yaparsın; başarı ölçütü "
              "XU100 ve TÜFE'yi geçmektir.")


def _fmt(v, suffix="", dash="—"):
    if v is None:
        return dash
    if isinstance(v, float):
        return f"{v:,.2f}{suffix}"
    return f"{v}{suffix}"


def _benchmark_lines(result: MorningResult) -> dict:
    state = result.state
    perf = state.performance
    bench = result.bundle.benchmark
    out = {
        "xu100_price": bench.get("index_quote", {}).get("price"),
        "xu100_change": bench.get("index_quote", {}).get("change_pct"),
        "tufe_yoy": bench.get("tufe_yoy_pct"),
        "tufe_note": bench.get("tufe_note"),
        "portfolio_return": None,
        "xu100_return": None,
        "relative": None,
    }
    if len(perf) >= 2:
        first, last = perf[0], perf[-1]
        if first.portfolio_value_try:
            out["portfolio_return"] = round(
                (last.portfolio_value_try / first.portfolio_value_try - 1) * 100, 2)
        if first.xu100 and last.xu100:
            out["xu100_return"] = round((last.xu100 / first.xu100 - 1) * 100, 2)
        if out["portfolio_return"] is not None and out["xu100_return"] is not None:
            out["relative"] = round(out["portfolio_return"] - out["xu100_return"], 2)
    return out


def build_briefing(result: MorningResult, config: Config) -> tuple[str, str, str]:
    """(subject, html, text) döner."""
    state = result.state
    today = datetime.now(timezone.utc).date().isoformat()
    prefix = config.get("mail", "subject_prefix", default="[Finans Ajanı]")
    bench = _benchmark_lines(result)

    accepted = result.guardrails.accepted()
    rejected = result.guardrails.rejected()
    forced = result.guardrails.forced_exits

    ctx = {
        "today": today,
        "portfolio_value": state.portfolio_value(),
        "cash": state.cash_try,
        "cash_pct": state.cash_pct() * 100,
        "open_count": len(state.open_positions()),
        "summary": result.output.market_summary,
        "notes": result.output.notes,
        "bench": bench,
        "positions": result.bundle.position_facts,
        "accepted": [(v.rec, v.notes) for v in accepted],
        "rejected": [(v.rec, v.notes) for v in rejected],
        "forced": [v.rec for v in forced],
        "new_ideas": [(v.rec, v.notes) for v in accepted if v.rec.position_id is None],
        "budget": state.budget,
        "errors": result.bundle.errors,
        "disclaimer": DISCLAIMER,
        "stub": result.used_stub,
    }

    n_actions = len([v for v in accepted if v.rec.action not in ("hold", "no_action")]) + len(forced)
    tag = "aksiyon var" if n_actions else "değişiklik yok"
    subject = f"{prefix} {today} — Sabah Brifingi ({tag})"
    html = _env.from_string(_HTML).render(**ctx)
    text = _render_text(ctx)
    return subject, html, text


def _render_text(ctx: dict) -> str:
    b = ctx["bench"]
    lines = [
        f"SABAH BRİFİNGİ — {ctx['today']}",
        "",
        f"Portföy: {_fmt(ctx['portfolio_value'],' ₺')} | Nakit: {_fmt(ctx['cash'],' ₺')} "
        f"(%{_fmt(ctx['cash_pct'])}) | Açık pozisyon: {ctx['open_count']}",
        f"Kıyas: XU100 {_fmt(b['xu100_price'])} (%{_fmt(b['xu100_change'])}) | "
        f"TÜFE yıllık {_fmt(b['tufe_yoy'],'%')}",
    ]
    if b["relative"] is not None:
        lines.append(f"Başlangıçtan bu yana: portföy %{_fmt(b['portfolio_return'])} vs "
                     f"XU100 %{_fmt(b['xu100_return'])} → göreli %{_fmt(b['relative'])}")
    lines += ["", "PİYASA ÖZETİ:", ctx["summary"] or "—", ""]
    if ctx["forced"]:
        lines.append("!!! ZORUNLU ÇIKIŞLAR (stop kırıldı):")
        for r in ctx["forced"]:
            lines.append(f"  - {r.symbol}: {r.rationale}")
        lines.append("")
    if ctx["accepted"]:
        lines.append("ÖNERİLER:")
        for rec, notes in ctx["accepted"]:
            src = rec.sources[0] if rec.sources else "—"
            lines.append(f"  - [{rec.action.upper()}] {rec.symbol} (güven {rec.confidence:.2f})")
            lines.append(f"      Tez: {rec.thesis}")
            lines.append(f"      Çürütücü: {rec.refuter}")
            if rec.stop:
                lines.append(f"      Stop: {rec.stop}")
            lines.append(f"      Kaynak: {src}")
            for n in notes:
                lines.append(f"      ! {n}")
    else:
        lines.append("ÖNERİ: Değişiklik yok — tezler geçerli.")
    lines += ["", "—", ctx["disclaimer"]]
    return "\n".join(lines)


_HTML = """\
<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;max-width:680px;margin:auto;color:#1a1a2e">
  <h2 style="margin-bottom:4px">Sabah Brifingi</h2>
  <div style="color:#666;font-size:13px">{{ today }}{% if stub %} · <span style="color:#b00">STUB: LLM çağrılmadı</span>{% endif %}</div>

  <div style="background:#f5f6fa;border-radius:10px;padding:14px;margin:14px 0">
    <b>Portföy:</b> {{ "%.2f"|format(portfolio_value) }} ₺ ·
    <b>Nakit:</b> {{ "%.2f"|format(cash) }} ₺ (%{{ "%.1f"|format(cash_pct) }}) ·
    <b>Açık pozisyon:</b> {{ open_count }}
    <div style="margin-top:8px;font-size:13px;color:#333">
      <b>Kıyas:</b> XU100 {{ bench.xu100_price or "—" }}
      {% if bench.xu100_change is not none %}(%{{ "%.2f"|format(bench.xu100_change) }}){% endif %}
      · TÜFE yıllık {% if bench.tufe_yoy is not none %}%{{ "%.2f"|format(bench.tufe_yoy) }}{% else %}—{% endif %}
      {% if bench.relative is not none %}
      <br><b>Başlangıçtan:</b> portföy %{{ "%.2f"|format(bench.portfolio_return) }}
      vs XU100 %{{ "%.2f"|format(bench.xu100_return) }} →
      <b style="color:{{ '#0a7d2c' if bench.relative >= 0 else '#b00' }}">göreli %{{ "%.2f"|format(bench.relative) }}</b>
      {% endif %}
    </div>
  </div>

  {% if forced %}
  <div style="background:#fdecea;border-left:4px solid #b00;padding:10px 12px;border-radius:6px;margin:12px 0">
    <b style="color:#b00">Zorunlu çıkışlar (stop kırıldı):</b>
    <ul>{% for r in forced %}<li>{{ r.symbol }} — {{ r.rationale }}</li>{% endfor %}</ul>
  </div>
  {% endif %}

  <h3>Piyasa özeti</h3>
  <p style="line-height:1.5">{{ summary or "—" }}</p>

  <h3>Açık pozisyonlar</h3>
  <table style="width:100%;border-collapse:collapse;font-size:13px">
    <tr style="background:#eef;text-align:left">
      <th style="padding:6px">Sembol</th><th>Giriş</th><th>Son</th><th>P&amp;L</th><th>Stop</th><th>Stop mes.</th>
    </tr>
    {% for p in positions %}
    <tr style="border-bottom:1px solid #eee">
      <td style="padding:6px"><b>{{ p.symbol }}</b> <span style="color:#999">{{ p.market }}</span></td>
      <td>{{ p.entry_price }}</td>
      <td>{{ p.quote.price if p.quote.price is not none else "—" }}</td>
      <td>{% if p.unrealized_pnl_try is not none %}{{ "%.0f"|format(p.unrealized_pnl_try) }} ₺{% else %}—{% endif %}</td>
      <td>{{ p.stop }}</td>
      <td>{% if p.stop_distance_pct is not none %}%{{ "%.1f"|format(p.stop_distance_pct) }}{% else %}—{% endif %}</td>
    </tr>
    {% else %}
    <tr><td colspan="6" style="padding:6px;color:#999">Açık pozisyon yok.</td></tr>
    {% endfor %}
  </table>

  <h3>Öneriler</h3>
  {% if accepted %}
    {% for rec, notes in accepted %}
    <div style="border:1px solid #e3e3ef;border-radius:8px;padding:10px 12px;margin:8px 0">
      <div><b>[{{ rec.action|upper }}]</b> {{ rec.symbol }}
        <span style="color:#999">· güven {{ "%.2f"|format(rec.confidence) }}</span></div>
      <div style="font-size:13px;margin-top:4px"><b>Tez:</b> {{ rec.thesis }}</div>
      <div style="font-size:13px"><b>Çürütücü:</b> {{ rec.refuter }}</div>
      {% if rec.stop %}<div style="font-size:13px"><b>Stop:</b> {{ rec.stop }}</div>{% endif %}
      {% if rec.sources %}<div style="font-size:12px;margin-top:4px">Kaynak:
        {% for s in rec.sources %}<a href="{{ s }}">{{ s }}</a>{% if not loop.last %}, {% endif %}{% endfor %}</div>{% endif %}
      {% for n in notes %}<div style="font-size:12px;color:#b06">! {{ n }}</div>{% endfor %}
    </div>
    {% endfor %}
  {% else %}
    <p style="color:#0a7d2c"><b>Değişiklik yok</b> — tezler geçerli. (Bu beklenen ve geçerli bir çıktıdır.)</p>
  {% endif %}

  {% if rejected %}
  <details style="margin-top:8px"><summary style="cursor:pointer;color:#b00">Korkuluk reddettikleri ({{ rejected|length }})</summary>
    {% for rec, notes in rejected %}
    <div style="font-size:12px;color:#666;margin:4px 0">{{ rec.symbol }} [{{ rec.action }}]:
      {% for n in notes %}{{ n }} {% endfor %}</div>
    {% endfor %}
  </details>
  {% endif %}

  {% if errors %}
  <details style="margin-top:8px"><summary style="cursor:pointer;color:#a60">Veri uyarıları ({{ errors|length }})</summary>
    <ul style="font-size:12px;color:#666">{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>
  </details>
  {% endif %}

  <div style="color:#999;font-size:12px;margin-top:16px;border-top:1px solid #eee;padding-top:8px">
    Bu ay API harcaması: ${{ "%.2f"|format(budget.spend_usd) }}{% if budget.throttled %} · <b style="color:#b00">bütçe tavanı aşıldı — seyreltiliyor</b>{% endif %}<br>
    {{ disclaimer }}
  </div>
</div>
"""
