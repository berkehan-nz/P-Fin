"""Sabah Turu (§3.2) — günün tek pahalı çağrısı.

Akış (deterministik iskele, LLM sadece muhakeme eder):
  1. Facts paketini çek (sayılar API'den).
  2. Hafızayı ÖZETLE (ham dökme — §3.4).
  3. Modeli çağır: Opus + web_search/web_fetch + forced tool-use (emit_briefing).
  4. Korkulukları uygula (§3.3) — model ne derse desin.
  5. Kararları arşivle, performans/kaynak karnesi/bütçeyi güncelle.
  6. Brifing (rapor) üret.

Model çağrısı `model_caller` ile enjekte edilebilir; anahtar yoksa veya dry-run'da
boş bir çıktı ile guardrail+rapor akışı yine de çalışır (çökme yok).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from ..config import Config
from ..cost import budget as budget_mod
from ..data.facts import FactBundle, build_fact_bundle
from ..guardrails.rules import GuardrailResult, apply_guardrails
from ..memory.schema import Decision, LogEntry, PerfPoint, State
from ..memory.summarize import prune_state, summarize_for_model
from ..sources import scorecard
from . import prompts
from .schema import TOOL_NAME, AgentOutput

ModelCaller = Callable[[list, list, list, Config], "ModelResult"]


@dataclass
class ModelResult:
    output: AgentOutput
    usage: object | None = None
    web_search_calls: int = 0
    used_stub: bool = False


@dataclass
class MorningResult:
    state: State
    bundle: FactBundle
    output: AgentOutput
    guardrails: GuardrailResult
    new_decisions: list[Decision] = field(default_factory=list)
    cost_usd: float = 0.0
    used_stub: bool = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def run_morning(state: State, config: Config,
                model_caller: ModelCaller | None = None,
                include_watchlist: bool = True) -> MorningResult:
    scorecard.ensure_seed(state)

    # 1) Facts (sayılar API'den)
    bundle = build_fact_bundle(state, config, include_watchlist=include_watchlist)

    # 2) Özet hafıza (ham dökme)
    model_context = summarize_for_model(state)

    # 3) Model çağrısı
    caller = model_caller or _default_model_caller
    system_blocks = prompts.build_system_blocks()
    tools = prompts.build_tools(config)
    user_content = prompts.build_user_message(model_context, bundle.to_model_context())
    result = caller(system_blocks, tools, user_content, config)
    output = result.output

    # Bütçe (§6)
    cost = budget_mod.record_usage(state.budget, result.usage, config,
                                   web_search_calls=result.web_search_calls)

    # 4) Korkuluklar (§3.3)
    guard = apply_guardrails(output, bundle, state, config)

    # 5) Kararları arşivle + zorunlu çıkışları uygula
    new_decisions: list[Decision] = []
    for vetted in guard.forced_exits + guard.vetted:
        rec = vetted.rec
        dec = Decision(
            id=_decision_id(rec.symbol, _today(), len(state.decisions) + len(new_decisions)),
            date=_today(), symbol=rec.symbol, action=rec.action,
            rationale=rec.rationale or vetted.rec.thesis,
            sources=rec.sources, confidence=rec.confidence,
            thesis=rec.thesis, refuter=rec.refuter, stop=rec.stop,
            invalidation=rec.invalidation, low_confidence=vetted.low_confidence,
            guardrail_notes=vetted.notes, rejected=(vetted.status == "rejected"),
        )
        new_decisions.append(dec)
    state.decisions.extend(new_decisions)

    # Kaynak karnesi (§4)
    scored = scorecard.record_observations(state, output.source_observations, _today())

    # Performans serisi + kıyas (§7) — deterministik
    _append_perf_point(state, bundle)

    # Ritim + günlük + budama
    state.meta.last_run_at = _now_iso()
    state.log.append(LogEntry(kind="morning", message=(
        f"Sabah turu: {len(guard.accepted())} öneri, {len(guard.rejected())} reddedildi, "
        f"{len(guard.forced_exits)} zorunlu çıkış, {scored} puanlanabilir iddia. "
        f"Maliyet ${cost:.3f}." + (" [STUB — LLM çağrılmadı]" if result.used_stub else ""))))
    prune_state(state)

    return MorningResult(state=state, bundle=bundle, output=output, guardrails=guard,
                         new_decisions=new_decisions, cost_usd=cost,
                         used_stub=result.used_stub)


def _append_perf_point(state: State, bundle: FactBundle) -> None:
    idx_q = bundle.benchmark.get("index_quote", {})
    xu100 = idx_q.get("price")
    tufe = bundle.benchmark.get("tufe_yoy_pct")
    base = state.performance[0].xu100 if state.performance and state.performance[0].xu100 else xu100
    state.performance.append(PerfPoint(
        date=_today(),
        portfolio_value_try=round(state.portfolio_value(), 2),
        cash_try=round(state.cash_try, 2),
        xu100=xu100, tufe_yoy=tufe, xu100_base=base,
    ))


def _decision_id(symbol: str, date: str, seq: int) -> str:
    return f"{date}-{symbol}-{seq}"


# --------------------------------------------------------------------------- model
def _default_model_caller(system_blocks, tools, user_content, config: Config) -> ModelResult:
    """Gerçek Anthropic çağrısı. Anahtar yoksa boş çıktı (stub) döner — akış çökmez."""
    secrets = config.secrets
    if not secrets.anthropic_api_key:
        return _stub_result("ANTHROPIC_API_KEY yok — LLM atlandı")

    import anthropic

    client = anthropic.Anthropic(api_key=secrets.anthropic_api_key)
    m = config.get("model", default={}) or {}
    messages = [{"role": "user", "content": user_content}]

    total_usage = _UsageAccumulator()
    web_calls = 0
    output: AgentOutput | None = None

    for attempt in range(3):
        force = attempt >= 1  # ilk denemede serbest (arama yapabilsin), sonra emit'e zorla
        resp = client.messages.create(
            model=m.get("id", "claude-opus-4-8"),
            max_tokens=int(m.get("max_tokens", 8000)),
            system=system_blocks,
            tools=tools,
            tool_choice=({"type": "tool", "name": TOOL_NAME} if force else {"type": "auto"}),
            messages=messages,
            extra_headers={"anthropic-beta": "web-fetch-2025-09-10"},
        )
        total_usage.add(resp.usage)
        web_calls += _web_search_count(resp.usage)

        emit_input = _find_emit(resp)
        if emit_input is not None:
            output = AgentOutput.model_validate(emit_input)
            break
        # emit yoksa: yanıtı bağlama ekle, bir sonraki turda emit'e zorla
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content":
                         f"Şimdi sonucu `{TOOL_NAME}` aracıyla döndür."})

    if output is None:
        return ModelResult(output=_empty_output(
            "Model emit_briefing döndürmedi; brifing üretilemedi."),
            usage=total_usage.value, web_search_calls=web_calls)
    return ModelResult(output=output, usage=total_usage.value, web_search_calls=web_calls)


def _find_emit(resp) -> dict | None:
    for block in getattr(resp, "content", []) or []:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == TOOL_NAME:
            return block.input
    return None


def _web_search_count(usage) -> int:
    st = getattr(usage, "server_tool_use", None)
    if st is None:
        return 0
    return int(getattr(st, "web_search_requests", 0) or 0)


class _UsageAccumulator:
    def __init__(self):
        self.value = {"input_tokens": 0, "output_tokens": 0,
                      "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}

    def add(self, usage):
        for k in self.value:
            self.value[k] += int(getattr(usage, k, 0) or 0)


def _stub_result(reason: str) -> ModelResult:
    return ModelResult(output=_empty_output(reason), usage=None,
                       web_search_calls=0, used_stub=True)


def _empty_output(note: str) -> AgentOutput:
    return AgentOutput(
        market_summary=f"(Otomatik) {note}",
        recommendations=[], new_ideas=[], source_observations=[],
        notes=note,
    )
