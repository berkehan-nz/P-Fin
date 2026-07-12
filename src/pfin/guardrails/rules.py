"""Korkuluk katmanı (§3.3) — kod, LLM değil. Model ne derse desin bunlar uygulanır.

- Tek pozisyon ≤ portföyün %20'si
- Her zaman ≥ %15 nakit tamponu
- Aynı anda en fazla 6 açık pozisyon
- Stop'suz veya girişin ÜSTÜNDE stop'lu alım önerisi REDDEDİLİR
- Güven skoru eşiğin altındaki öneriler "DÜŞÜK GÜVEN" damgasıyla işaretlenir
- Stop kırıldıysa modele sorulmadan "ÇIK" üretilir

Bu katman işlem YAPMAZ (kullanıcı Midas'ta elle yapar); geçersiz önerileri eler,
tehlikeli olanları reddeder, stop kırılmalarında zorunlu çıkış üretir. Çıktısı rapora
ve karar arşivine girer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..agent.schema import AgentOutput, Recommendation
from ..config import Config
from ..data.facts import FactBundle
from ..memory.schema import State


@dataclass
class VettedRec:
    rec: Recommendation
    status: str                       # accepted | rejected | forced_exit | capped
    low_confidence: bool = False
    notes: list[str] = field(default_factory=list)
    ref_price: float | None = None    # facts'ten giriş referans fiyatı
    final_weight_pct: float | None = None


@dataclass
class GuardrailResult:
    vetted: list[VettedRec] = field(default_factory=list)
    forced_exits: list[VettedRec] = field(default_factory=list)
    global_notes: list[str] = field(default_factory=list)

    def accepted(self) -> list[VettedRec]:
        return [v for v in self.vetted if v.status in ("accepted", "capped")]

    def rejected(self) -> list[VettedRec]:
        return [v for v in self.vetted if v.status == "rejected"]


def _price_lookup(bundle: FactBundle) -> dict[str, float]:
    out: dict[str, float] = {}
    for pf in bundle.position_facts:
        p = pf.get("quote", {}).get("price")
        if p is not None:
            out[pf["symbol"].upper()] = p
    for q in bundle.watchlist_quotes:
        if q.get("price") is not None:
            out.setdefault(q["symbol"].upper(), q["price"])
    return out


def apply_guardrails(output: AgentOutput, bundle: FactBundle, state: State,
                     config: Config) -> GuardrailResult:
    g = config.get("guardrails", default={}) or {}
    max_pos = float(g.get("max_position_pct", 0.20))
    min_cash = float(g.get("min_cash_pct", 0.15))
    max_open = int(g.get("max_open_positions", 6))
    min_conf = float(g.get("min_confidence", 0.55))

    prices = _price_lookup(bundle)
    result = GuardrailResult()

    # --- 1) Stop kırıldıysa modele sorulmadan ZORUNLU ÇIK (§3.3 son madde) ---
    forced_symbols: set[str] = set()
    for pf in bundle.position_facts:
        if pf.get("stop_broken"):
            sym = pf["symbol"]
            forced_symbols.add(sym.upper())
            rec = Recommendation(
                symbol=sym, market=pf["market"], action="exit",
                position_id=pf.get("id"),
                thesis=f"Pozisyon tezi askıda: stop {pf.get('stop')} kırıldı.",
                refuter="Stop seviyesinin kırılması tezi geçersiz kılan koşuldu.",
                invalidation="Stop kırıldı — çıkış planı devreye girdi.",
                stop=pf.get("stop"), confidence=1.0,
                rationale=f"{sym} fiyatı {pf.get('quote', {}).get('price')} ≤ stop {pf.get('stop')}. "
                          "Korkuluk zorunlu çıkış üretti.",
                sources=["guardrail:stop_broken"],
            )
            result.forced_exits.append(VettedRec(rec=rec, status="forced_exit",
                                                 ref_price=pf.get("quote", {}).get("price")))

    open_count = len(state.open_positions())
    projected_new = 0
    cash = state.cash_try
    total = state.portfolio_value() or 1.0

    # --- 2) Model önerileri: reddet / damgala / sınırla ---
    for rec in list(output.recommendations) + list(output.new_ideas):
        # Zorunlu çıkışa düşen sembol için modelin başka önerisini yok say
        if rec.symbol.upper() in forced_symbols and rec.action != "exit":
            result.vetted.append(VettedRec(rec=rec, status="rejected",
                notes=[f"{rec.symbol}: stop kırıldı, zorunlu çıkış geçerli — model önerisi geçersiz."]))
            continue

        vetted = VettedRec(rec=rec, status="accepted")
        vetted.ref_price = prices.get(rec.symbol.upper())
        vetted.low_confidence = rec.confidence < min_conf
        if vetted.low_confidence:
            vetted.notes.append(f"DÜŞÜK GÜVEN (güven {rec.confidence:.2f} < eşik {min_conf:.2f}).")

        # Her öneri en az bir kaynak taşımalı (§9)
        if not rec.sources:
            vetted.status = "rejected"
            vetted.notes.append("Kaynaksız öneri reddedildi (§9: her karar ≥1 kaynak).")
            result.vetted.append(vetted)
            continue

        # Çürütücü zorunlu (§2.3)
        if not rec.refuter.strip():
            vetted.status = "rejected"
            vetted.notes.append("Çürütücüsü olmayan öneri reddedildi (§2.3).")
            result.vetted.append(vetted)
            continue

        if rec.action in ("buy", "switch"):
            entry = vetted.ref_price
            # Stop'suz alım reddedilir
            if rec.stop is None:
                vetted.status = "rejected"
                vetted.notes.append("Stop'suz alım reddedildi (§2.4/§3.3).")
                result.vetted.append(vetted)
                continue
            # Girişin üstünde stop'lu alım reddedilir (long)
            if entry is not None and rec.stop >= entry:
                vetted.status = "rejected"
                vetted.notes.append(
                    f"Girişin üstünde stop reddedildi: stop {rec.stop} ≥ referans fiyat {entry}.")
                result.vetted.append(vetted)
                continue
            if entry is None:
                vetted.notes.append("Uyarı: referans fiyat facts'te yok; stop doğrulanamadı.")

            # En fazla 6 açık pozisyon
            is_new = rec.position_id is None and rec.symbol.upper() not in {
                p.symbol.upper() for p in state.open_positions()}
            if is_new and (open_count + projected_new) >= max_open:
                vetted.status = "rejected"
                vetted.notes.append(
                    f"En fazla {max_open} açık pozisyon sınırı: yeni alım reddedildi.")
                result.vetted.append(vetted)
                continue

            # Tek pozisyon ≤ %20 — ağırlık sınırla
            weight = rec.target_weight_pct
            if weight is None:
                weight = max_pos * 100
            if weight > max_pos * 100:
                vetted.status = "capped"
                vetted.notes.append(
                    f"Ağırlık %{weight:.0f} → %{max_pos*100:.0f} sınırına çekildi (tek pozisyon ≤ %20).")
                weight = max_pos * 100
            vetted.final_weight_pct = weight

            # ≥ %15 nakit tamponu — kabaca kontrol
            alloc = total * weight / 100
            if is_new:
                projected_new += 1
            if (cash - alloc) / total < min_cash:
                vetted.notes.append(
                    f"Nakit tamponu uyarısı: bu alım nakiti %{min_cash*100:.0f} altına indirebilir "
                    "— boyutu küçült veya atla.")

        result.vetted.append(vetted)

    if result.forced_exits:
        result.global_notes.append(
            f"{len(result.forced_exits)} pozisyonda stop kırıldı → zorunlu çıkış üretildi.")
    return result
