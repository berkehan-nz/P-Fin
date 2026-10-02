"""v4 — Sanayileşme / imar senaryoları (TEKNOSAB komşuluğu). Çekirdek hesap model_v3'tedir.

    python reports/bogurtlen-fizibilite/model_v4.py
"""
from __future__ import annotations

import model_v2 as v2
import model_v3 as v3

fmt, usd, pct = v2.fmt, v2.usd, v2.pct

MOVABLE_KEYS = ("reefer", "Ön soğutma", "Paketleme odası", "top-seal", "terazi", "Hasat ekipmanı", "Transpalet",
                "GES", "kontrolör", "Dozaj", "LoRaWAN", "toprak düğümü", "referans prob", "meteoroloji",
                "debimetre", "Edge", "kamera", "Soğuk zincir sensörleri", "Şok dondurucu", "liyofilize", "Elektronik")


def registry(plan="10"):
    """(ad, alım yılı sonu, tutar, ömür, taşınabilir mi)"""
    v3.set_plan(plan)
    reg = []
    for f, g, k, v, life, start in v2.CAPEX:
        reg.append((k, start - 1, v, life, any(m.lower() in k.lower() for m in MOVABLE_KEYS)))
    for f in (1, 2):
        reg.append((f"Faz {f} beklenmeyen", 0 if f == 1 else 1, v2.capex_phase(f)[1], 10, False))
    for y, k, v, life in v3.FAZ3 + v3.REPLACE:
        reg.append((k, y, v, life, any(m.lower() in k.lower() for m in MOVABLE_KEYS)))
    for py, area in v3.blocks_extra():
        reg.append(("2. blok tarla", py - 1 + (1 if py == 1 else 0), v3.BLOCK2_FIELD * area / 10, 10, False))
        reg.append(("2. blok gölge filesi", py, v3.BLOCK2_SHADE * area / 10, 7, False))
    if v3.CUR["own_fd_year"]:
        reg.append(("liyofilize makinesi", v3.CUR["own_fd_year"], v3.FD_MACHINE, 8, True))
    return reg


def nbv(reg, year, movable=None):
    return sum(v * max(0, min(1, (y0 + life - year) / life)) for _, y0, v, life, mv in reg
               if y0 <= year and (movable is None or mv == movable))


def movable_share(plan="10"):
    reg = registry(plan)
    tot = sum(v for *_, v, _, _ in [(r[0], r[1], r[2], r[3], r[4]) for r in reg])
    mov = sum(r[2] for r in reg if r[4])
    return mov, tot


def set_adj(labor=None, corp=None, plan="10"):
    v3.set_plan(plan)
    v3.ADJ["fixed_add"] = {}
    v3.ADJ["corp_mult"] = dict(corp or {})
    if labor:
        for y, m in labor.items():
            base = sum(v[min(y, 5) - 1] for k, v in v2.FIXED.items()
                       if k.startswith(("Budama", "Daimi", "Sezonluk")))
            extra = 0.0
            for py, area in v3.blocks_extra():
                age = y - py + 1
                if age >= 1:
                    extra += (4500 if age == 1 else 9000) * area / 10 + v2.FIXED["Budama, bağlama, ot biçimi (yevmiyeli)"][min(age, 5) - 1] * area / 10
            v3.ADJ["fixed_add"][y] = (base + extra) * (m - 1)


def clear_adj():
    v3.ADJ["fixed_add"] = {}; v3.ADJ["corp_mult"] = {}


LABOR = {3: 1.10, 4: 1.15, 5: 1.25, 6: 1.25, 7: 1.30, 8: 1.30, 9: 1.35, 10: 1.35}   # TEKNOSAB istihdamı büyüdükçe
CORP = {4: 1.5, 5: 2.0, 6: 2.0, 7: 2.0, 8: 2.0, 9: 2.0, 10: 2.0}                       # TEKNOSAB firmaları kurumsal kanala


def scenario(plan="10", labor=False, corp=False, end=None, comp=1.0, salvage=0.6, partial=None):
    """end: işletmenin sona erdiği yıl (yıl sonu, kamulaştırma/imar). comp: sabit tesis+bahçe bedeli / NBV.
    partial: (yıl, oran) — yol/ray koridoru için alanın bir kısmının kamulaştırılması."""
    set_adj(LABOR if labor else None, CORP if corp else None, plan)
    shocks = {}
    for y in range(1, 11):
        sh = {}
        if labor:
            sh["harv_mult"] = LABOR.get(y, 1.0)
        if partial and y > partial[0]:
            sh["yld_mult"] = 1 - partial[1]
        if sh:
            shocks[y] = sh
    out = v3.run(shocks, plan=plan)
    reg = registry(plan)
    flows, eq = list(out["flows"]), list(out["eq"])
    if partial:
        y0, share = partial
        pay = nbv(reg, y0, movable=False) * share * comp
        flows[y0] += pay; eq[y0] += pay
        out["comp"] = pay
    if end:
        res_rv = out["residual"]
        flows[-1] -= res_rv; eq[-1] -= res_rv
        pay = nbv(reg, end, movable=False) * comp + nbv(reg, end, movable=True) * salvage
        remaining_principal = sum(r["princ"] for r in out["rows"] if r["y"] > end)
        for i in range(end + 1, 11):
            flows[i] = 0.0; eq[i] = 0.0
        flows[end] += pay
        eq[end] += pay - remaining_principal
        out["comp"] = pay
    clear_adj()
    rows = out["rows"][: end] if end else out["rows"]
    return dict(flows=flows, eq=eq, net=sum(r["net"] for r in rows), comp=out.get("comp", 0))


SCENARIOS = [
    ("A. Baz (v3)", {}),
    ("B. İşgücü baskısı (hasat ve sabit işçilik 2031'den +%25-35)", dict(labor=True)),
    ("C. TEKNOSAB pazarı (kurumsal hacim 2 katı)", dict(corp=True)),
    ("D. Sanayi komşusu — en olası (B + C)", dict(labor=True, corp=True)),
    ("E. Kısmi kamulaştırma: yol/ray koridoru, alanın %10'u (2029 sonu)", dict(labor=True, corp=True, partial=(3, 0.10))),
    ("F. Tam kamulaştırma / OSB genişlemesi (2032 sonu)", dict(labor=True, corp=True, end=6)),
    ("F2. Tam kamulaştırma 2032, bahçe bedeli gelir yöntemiyle (NBV × 2)", dict(labor=True, corp=True, end=6, comp=2.0)),
    ("G. İmar gelir, gönüllü çıkış (2034 sonu)", dict(labor=True, corp=True, end=8)),
]


def md_scenarios(plan="10"):
    out = ["| Senaryo | Proje IRR | Özsermaye IRR | NPV (%12) | Dönem net kârı | Tesis/bahçe bedeli |",
           "|---|---:|---:|---:|---:|---:|"]
    for lab, kw in SCENARIOS:
        r = scenario(plan, **kw)
        out.append(f"| {lab} | {pct(v2.irr(r['flows']))} | {pct(v2.irr(r['eq']))} | {usd(v3.npv(r['flows']))} | "
                   f"{usd(r['net'])} | {usd(r['comp']) if r['comp'] else '–'} |")
    return "\n".join(out)


# Arazi değeri (yalnız bilgi amaçlı; proje nakit akışına girmez)
LAND = [  # (durum, TL/m² aralığı)
    ("Muratlı tarla, mevcut (ilan aralığı alt-orta)", 550, 1000),
    ("TEKNOSAB çevresi tarla (ilanlar)", 600, 2000),
    ("TEKNOSAB'a bitişik, ana yol cepheli tarla (ilan)", 5000, 5600),
    ("Karacabey sanayi imarlı arsa (ilan)", 3500, 8000),
]


def md_land(area_m2=10000):
    out = ["| Durum | TL/m² (ilan) | 10 da değeri (TL) | 10 da değeri (USD) |", "|---|---:|---:|---:|"]
    for k, lo, hi in LAND:
        out.append(f"| {k} | {fmt(lo)}–{fmt(hi)} | {fmt(lo*area_m2/1e6,1)}–{fmt(hi*area_m2/1e6,1)} M | "
                   f"{usd(lo*area_m2/v2.FX)}–{usd(hi*area_m2/v2.FX)} |")
    return "\n".join(out)


if __name__ == "__main__":
    for p in ("10", "20B"):
        print(v3.PLANS[p]["name"]); print(md_scenarios(p)); print()
        m, t = movable_share(p); print("taşınabilir", round(m), round(t), m / t)
    print(md_land())


# 2036'ya kadar araziyi etkileyecek sonuç için uzman tahmini olasılıklar (rapor Bölüm 8.4)
PROBS = [
    ("Tarım sürer, sanayi komşusu (D)", 0.55, dict(labor=True, corp=True)),
    ("Kısmi kamulaştırma, koridor (E)", 0.18, dict(labor=True, corp=True, partial=(3, 0.10))),
    ("Tam kamulaştırma / OSB genişlemesi 2032 (F/F2 ortalaması)", 0.12, None),
    ("İmar gelir, gönüllü çıkış 2034 (G)", 0.15, dict(labor=True, corp=True, end=8)),
]


def expected(plan="10"):
    rows, ev = [], 0.0
    for lab, p, kw in PROBS:
        if kw is None:
            a = v3.npv(scenario(plan, labor=True, corp=True, end=6)["flows"])
            b = v3.npv(scenario(plan, labor=True, corp=True, end=6, comp=2.0)["flows"])
            n = (a + b) / 2
        else:
            n = v3.npv(scenario(plan, **kw)["flows"])
        rows.append((lab, p, n)); ev += p * n
    return rows, ev


def md_expected():
    r10, e10 = expected("10"); r20, e20 = expected("20B")
    out = ["| Sonuç (2036'ya kadar) | Olasılık (tahmin) | NPV 10 da | NPV 20 da kademeli |", "|---|---:|---:|---:|"]
    for (lab, p, a), (_, _, b) in zip(r10, r20):
        out.append(f"| {lab} | %{p*100:.0f} | {usd(a)} | {usd(b)} |")
    out.append(f"| **Olasılık ağırlıklı beklenen NPV (%12)** | | **{usd(e10)}** | **{usd(e20)}** |")
    return "\n".join(out)
