"""Asama 4 puanlamasi: Ucuzluk 25 / Kalite 20 / Saglamlik 15 / Momentum 15 /
Kazanc kalitesi 10 / Katalizor 15 (elle).

Alt bilesenler SEKTOR ICI YUZDELIK olarak 0-100'e olceklenir. Ham deger
kullanmak sektorler arasi karsilastirmayi bozar: yazilimda %70 brut marj
normalken perakendede olaganustudur.
"""

from __future__ import annotations

from .config import COVERAGE, SCORE_CAPS, SCORE_COMPONENTS, SCORE_WEIGHTS
from .util import num


def cap_for_scoring(metric: str, value):
    """Uc degerleri yalnizca SIRALAMA icin kirpar; gorunen deger degismez.

    NTAP'in ROIC'i %352 cikiyor cunku agresif geri alim sonrasi yatirilan
    sermaye sifira yaklasiyor. Bu, sirketin digerlerinden 20 kat iyi oldugu
    anlamina gelmez — paydanin kucuk oldugu anlamina gelir. Kirpilmazsa tek
    bir sirket tum yuzdelik dagilimini kendine dogru cekiyor.
    """
    v = num(value)
    if v is None or metric not in SCORE_CAPS:
        return v
    lo, hi = SCORE_CAPS[metric]
    if lo is not None:
        v = max(v, lo)
    if hi is not None:
        v = min(v, hi)
    return v


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
    return round(score, 1), {"components": detail, "coverage": round(coverage, 2),
                             "low_coverage": coverage < COVERAGE["low_coverage_flag"]}


def total_score(blocks: dict[str, float | None], catalyst: float | None = None,
                coverage: dict[str, float] | None = None) -> dict:
    """Agirlikli toplam puan (0-100 olceginde).

    Katalizor puani elle girilir; yoksa agirligi havuzdan cikarilir ve
    kalan bilesenler yeniden normalize edilir — otomatik puan katalizor
    girilmedi diye sistematik olarak dusuk gorunmesin.

    KAPSAMA AGIRLIGI: bir blogun alt metriklerinin ancak %30'u hesaplanabildiyse
    o puan iki metrige dayaniyor demektir. Puani cezalandirmak yanlis olurdu
    (veri yoklugu kotu haber degildir) ama o blogun SOZ HAKKI azaltilmali.
    Blok agirligi kapsama ile carpilir; boylece YOU'nun 0,30 kapsamali
    94'luk kalite puani listeyi tek basina yukari cekemez.
    """
    used_weight = 0.0
    acc = 0.0
    parts: dict[str, float | None] = {}
    coverage = coverage or {}
    applied: dict[str, float] = {}

    for key in ("value", "quality", "safety", "momentum", "earnings_quality"):
        v = num(blocks.get(key))
        parts[key] = round(v, 1) if v is not None else None
        if v is None:
            continue
        cov = num(coverage.get(key))
        factor = 1.0 if cov is None else max(cov, COVERAGE["min_weight_factor"])
        w = SCORE_WEIGHTS[key] * factor
        applied[key] = round(factor, 2)
        acc += v * w
        used_weight += w

    c = num(catalyst)
    parts["catalyst"] = round(c, 1) if c is not None else None
    if c is not None:
        acc += c * SCORE_WEIGHTS["catalyst"]
        used_weight += SCORE_WEIGHTS["catalyst"]

    parts["total"] = round(acc / used_weight, 1) if used_weight > 0 else None
    parts["weight_coverage"] = round(used_weight / sum(SCORE_WEIGHTS.values()), 2)
    parts["coverage_factors"] = applied
    return parts


def compute(percentiles: dict[str, float | None],
            catalyst: float | None = None) -> tuple[dict, dict]:
    """Tum puan bloklarini hesaplar.

    Returns:
        (``{"total":..,"value":..}``, ``{blok: alt bilesen detayi}``)
    """
    blocks: dict[str, float | None] = {}
    detail: dict[str, dict] = {}
    coverage: dict[str, float] = {}
    for block in SCORE_COMPONENTS:
        score, d = score_block(block, percentiles)
        blocks[block] = score
        detail[block] = d
        if isinstance(d, dict) and d.get("coverage") is not None:
            coverage[block] = d["coverage"]
    return total_score(blocks, catalyst, coverage), detail
