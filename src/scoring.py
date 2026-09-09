"""Asama 4 puanlamasi: Ucuzluk 25 / Kalite 20 / Saglamlik 15 / Momentum 15 /
Kazanc kalitesi 10 / Katalizor 15 (elle).

Alt bilesenler SEKTOR ICI YUZDELIK olarak 0-100'e olceklenir. Ham deger
kullanmak sektorler arasi karsilastirmayi bozar: yazilimda %70 brut marj
normalken perakendede olaganustudur.
"""

from __future__ import annotations

from .config import SCORE_COMPONENTS, SCORE_WEIGHTS
from .util import num


def score_block(block: str, percentiles: dict[str, float | None]) -> tuple[float | None, dict]:
    """Bir ana puani (0-100) ve alt bilesen katkilarini hesaplar.

    Eksik alt bilesenler agirlik havuzundan cikarilir; kalan bilesenler
    yeniden normalize edilir. Boylece tek eksik veri puani sifira cekmez.
    """
    components = SCORE_COMPONENTS.get(block, [])
    total_weight = 0.0
    weighted = 0.0
    detail: dict[str, dict] = {}

    for comp in components:
        p = num(percentiles.get(comp["metric"]))
        if p is None:
            detail[comp["metric"]] = {"percentile": None, "contribution": None}
            continue
        # invert: dusuk deger iyi -> yuzdeligi ters cevir
        scaled = (100.0 - p) if comp["invert"] else p
        weighted += scaled * comp["weight"]
        total_weight += comp["weight"]
        detail[comp["metric"]] = {"percentile": round(p, 1),
                                  "scaled": round(scaled, 1),
                                  "weight": comp["weight"]}

    if total_weight == 0:
        return None, detail

    score = weighted / total_weight
    coverage = total_weight / sum(c["weight"] for c in components)
    return round(score, 1), {"components": detail, "coverage": round(coverage, 2)}


def total_score(blocks: dict[str, float | None], catalyst: float | None = None) -> dict:
    """Agirlikli toplam puan (0-100 olceginde).

    Katalizor puani elle girilir; yoksa agirligi havuzdan cikarilir ve
    kalan bilesenler yeniden normalize edilir — otomatik puan katalizor
    girilmedi diye sistematik olarak dusuk gorunmesin.
    """
    used_weight = 0.0
    acc = 0.0
    parts: dict[str, float | None] = {}

    for key in ("value", "quality", "safety", "momentum", "earnings_quality"):
        v = num(blocks.get(key))
        parts[key] = round(v, 1) if v is not None else None
        if v is None:
            continue
        w = SCORE_WEIGHTS[key]
        acc += v * w
        used_weight += w

    c = num(catalyst)
    parts["catalyst"] = round(c, 1) if c is not None else None
    if c is not None:
        acc += c * SCORE_WEIGHTS["catalyst"]
        used_weight += SCORE_WEIGHTS["catalyst"]

    parts["total"] = round(acc / used_weight, 1) if used_weight > 0 else None
    parts["weight_coverage"] = round(used_weight / sum(SCORE_WEIGHTS.values()), 2)
    return parts


def compute(percentiles: dict[str, float | None],
            catalyst: float | None = None) -> tuple[dict, dict]:
    """Tum puan bloklarini hesaplar.

    Returns:
        (``{"total":..,"value":..}``, ``{blok: alt bilesen detayi}``)
    """
    blocks: dict[str, float | None] = {}
    detail: dict[str, dict] = {}
    for block in SCORE_COMPONENTS:
        score, d = score_block(block, percentiles)
        blocks[block] = score
        detail[block] = d
    return total_score(blocks, catalyst), detail
