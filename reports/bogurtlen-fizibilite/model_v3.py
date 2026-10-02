"""Dikensiz böğürtlen v3 — hibrit kanal (taze çoğunluk + IQF + liyofilize), 10 yıl, Monte Carlo.

    python reports/bogurtlen-fizibilite/model_v3.py            # özet
    python reports/bogurtlen-fizibilite/model_v3.py --tables   # markdown tablolar
    python reports/bogurtlen-fizibilite/model_v3.py --mc       # risk simülasyonu (~40 sn)

Planlar: "10" (10 da), "20A" (20 da tek seferde, 2027), "20B" (20 da kademeli, 2027 + 2029).

Sunum: 2026 sabit fiyatlarıyla USD (reel). TL karşılıkları FX ile.
v2'den (model_v2.py) CAPEX kalemleri ve sabit giderler devralınır.
"""
from __future__ import annotations
import random
import sys

import model_v2 as v2

FX = v2.FX
YEARS = 10
LABEL = {0: "Y0"} | {y: f"{2026 + y}" for y in range(1, 11)}
CORP_TAX = 0.25
LOSS_CARRY = 5

# ------------------------------------------------------------------ çeşit portföyü
CULTIVARS = [
    # (çeşit, alan payı, tipi, hasat penceresi, tam verim t/da)
    ("Loch Ness", 0.30, "floricane, yarı dik", "5 Tem – 10 Ağu", 2.2),
    ("Chester", 0.40, "floricane, yarı yatık, geç", "25 Tem – 10 Eyl", 2.0),
    ("Prime-Ark Freedom / Traveler", 0.30, "primocane (1. yıl kolda sonbahar ürünü)", "15 Haz – 5 Tem (az) + 1 Eyl – 31 Eki", 1.6),
]

# ------------------------------------------------------------------ verim (ton, 10 da)
# Y1: primocane çeşitler dikim yılında sonbaharda az ürün verir
YIELD = [0.5, 5.5, 14.5, 20, 20, 20, 20, 20, 18, 16]
SECOND = 0.20                       # 2. sınıf pay

# ------------------------------------------------------------------ kanal planı
CORP_T = [0, 0, .5, 1.5, 2.5, 3, 3, 3, 3, 3]
PACK_SHARE = [0, .50, .65, .75, .80, .80, .80, .80, .80, .80]   # kurumsal dışı 1. sınıfın paketli payı
SURPLUS_TO_FREEZE = .50             # şok dondurucu varken paketlenemeyen tazenin dondurulan payı
FREEZER_FROM = 3                    # Faz 3 şok dondurucu 2029 sezonundan önce kurulur
FD_SHARE = [0, 0, .20, .30, .40, .50, .50, .50, .50, .50]       # dondurulan havuzun liyofilizeye giden payı
OWN_FD_FROM = 99                    # kendi makine bu ölçekte geri ödemiyor → fason (bkz. rapor 4.3)

# ------------------------------------------------------------------ fiyat ve maliyet (USD)
PACK_PRICE = v2.pack_price_per_kg()          # 5,65 $/kg ağırlıklı
PACK_COST = v2.pack_cost_per_kg()            # 0,60 $/kg
IQF_PRICE, IQF_PACK, IQF_COMM, IQF_FREIGHT = 2.80, 0.10, 0.05, 0.15
FREEZE_COST = 0.15                   # şok dondurma enerji + işçilik $/kg
FD_RATIO = 8.5                       # kg taze (dondurulmuş) → 1 kg liyofilize
FD_PRICE, FD_PACK = 40.0, 1.50       # $/kg kuru (B2B, alu torba + koli)
FD_TOLL = 2.00                       # fason liyofilize $/kg taze girdi
FD_OWN = 0.70                        # kendi makinede enerji + işçilik $/kg taze girdi
PROC_PRICE = 1.30                    # şok dondurucu öncesi 2. sınıf → işleme tesisi

# ------------------------------------------------------------------ ek CAPEX
FAZ3 = [  # (yıl sonu, kalem, USD, ömür)
    (2, "Şok dondurucu (-35 °C, 300 kg/parti)", 14000, 8),
    (2, "İkinci 40' reefer, -20 °C dondurulmuş stok deposu", 8500, 10),
]
REPLACE = [  # yenileme yatırımları (yıl, kalem, USD, ömür)
    (6, "Elektronik yenileme (sensör, kamera, edge)", 8000, 5),
    (8, "Gölge filesi + malç örtü yenileme", 4900, 7),
]

# ------------------------------------------------------------------ plan (alan / blok yapısı)
PLANS = {
    "10": dict(name="10 da", blocks=[(10, 1)], own_fd_year=None, pack_factor=1.0, corp_factor=1.0),
    "20A": dict(name="20 da — tek seferde (2027)", blocks=[(10, 1), (10, 1)], own_fd_year=4,
                pack_factor=0.90, corp_factor=1.5),
    "20B": dict(name="20 da — kademeli (2027 + 2029)", blocks=[(10, 1), (10, 3)], own_fd_year=5,
                pack_factor=0.90, corp_factor=1.5),
}
CUR = PLANS["10"]
FD_MACHINE = 24000      # orta boy liyofilize (~50 kg taze/parti), 8 yıl
BLOCK2_FIELD = (sum(c[3] for c in v2.CAPEX if c[1] == "Tarla" and c[0] == 1) + 2240) * (1 + v2.CONTINGENCY)
BLOCK2_SHADE = 3800 * (1 + v2.CONTINGENCY)


def set_plan(key):
    global CUR
    CUR = PLANS[key]


def blocks_extra():
    """1. bloktan sonraki bloklar: (dikim yılı, alan)."""
    return [(py, a) for a, py in CUR["blocks"][1:]]


def base_kg(y):
    t = 0.0
    for area, py in CUR["blocks"]:
        age = y - py + 1
        if age >= 1:
            t += YIELD[min(age, len(YIELD)) - 1] * area / 10
    return t * 1000


def scaled(y):
    """Ek blok hasat vermeye başladıysa (yaş ≥ 2) kanal ölçek çarpanları devreye girer."""
    return any(y - py + 1 >= 2 for py, _ in blocks_extra())


def own_fd_from():
    return CUR["own_fd_year"] + 1 if CUR["own_fd_year"] else 99


# ------------------------------------------------------------------ sabit giderler
EXTRA_FIXED = {
    "Kurucu Ankara–Karacabey ulaşım/konaklama (~30 ziyaret/yıl)": 3500,
    "Arı kovanı kiralama (çiçeklenme, 15 kovan)": 300,
    "Dondurulmuş depo + şok dondurucu elektriği (2029+)": 900,
}


def fixed(y):
    base = v2.fixed_opex(min(y, 5))
    base += EXTRA_FIXED["Kurucu Ankara–Karacabey ulaşım/konaklama (~30 ziyaret/yıl)"]
    if y >= 2:
        base += EXTRA_FIXED["Arı kovanı kiralama (çiçeklenme, 15 kovan)"]
    if y >= FREEZER_FROM:
        base += EXTRA_FIXED["Dondurulmuş depo + şok dondurucu elektriği (2029+)"]
    for py, area in blocks_extra():
        age = y - py + 1
        if age < 1:
            continue
        k = min(age, 5) - 1
        f = area / 10
        for name, vals in v2.FIXED.items():
            if name.startswith(("Gübre", "Budama", "DSİ")):
                base += vals[k] * f
            elif name.startswith("Sigorta"):
                base += vals[k] * 0.5 * f
        base += (4500 if age == 1 else 9000) * f            # ikinci daimi işçi
        base += 300 * f                                      # ek arı kovanı
        if age >= 2:
            base += 1000 + 400                               # ek pazarlama + elektrik
    if y >= own_fd_from():
        base += 1200                                         # gıda üretim izni / HACCP
    return base


SERVICE = [0, 0, 1500, 3000, 4000, 4500, 5000, 5000, 5000, 5000]
LAB = [0, 0, 0, 2000, 4000, 5000, 6000, 6000, 6000, 6000]
CONSULT = [0, 0, 0, 0, 3000, 4000, 5000, 5000, 5000, 5000]


SHADE = 3800 * (1 + v2.CONTINGENCY)   # gölge filesi (önlemsiz senaryoda yok)
TARSIM = 600                          # sabit giderlerdeki TARSİM payı (önlemsiz senaryoda yok)
RESIDUAL = 0.50                       # 10. yıl sonu net defter değerinin %50'si kalıntı değer


def capex_schedule(mitigated=True):
    """yıl → USD (yıl sonunda ödenir; 0 = Faz 1, 1 = Faz 2)."""
    c = {0: sum(v2.capex_phase(1)), 1: sum(v2.capex_phase(2))}
    extra = FAZ3 + REPLACE if mitigated else [r for r in REPLACE if "file" not in r[1]]
    for y, _, v, _ in extra:
        c[y] = c.get(y, 0) + v
    if not mitigated:
        c[1] -= SHADE
    for py, area in blocks_extra():
        c[py - 1] = c.get(py - 1, 0) + BLOCK2_FIELD * area / 10
        if mitigated:
            c[py] = c.get(py, 0) + BLOCK2_SHADE * area / 10
    if CUR["own_fd_year"]:
        c[CUR["own_fd_year"]] = c.get(CUR["own_fd_year"], 0) + FD_MACHINE
    return c


def _assets(mitigated=True):
    """(alım yılı sonu, tutar, ömür) — amortisman alım yılının ertesi yılı başlar (bahçe tesisi 2028)."""
    a = []
    for f, g, k, v, life, start in v2.CAPEX:
        if not mitigated and "gölge filesi" in k:
            continue
        a.append((start - 1, v, life))
    for f in (1, 2):
        a.append((0 if f == 1 else 1, v2.capex_phase(f)[1], 10))
    extra = FAZ3 + REPLACE if mitigated else [r for r in REPLACE if "file" not in r[1]]
    a += [(y, v, life) for y, _, v, life in extra]
    for py, area in blocks_extra():
        a.append((py - 1 + (1 if py == 1 else 0), BLOCK2_FIELD * area / 10, 10))
        if mitigated:
            a.append((py, BLOCK2_SHADE * area / 10, 7))
    if CUR["own_fd_year"]:
        a.append((CUR["own_fd_year"], FD_MACHINE, 8))
    return a


def depreciation(y, mitigated=True):
    return sum(v / life for y0, v, life in _assets(mitigated) if y0 + 1 <= y < y0 + 1 + life)


def residual_value(mitigated=True, year=YEARS):
    nbv = sum(v * max(0, (y0 + life - year)) / life for y0, v, life in _assets(mitigated) if y0 < year)
    return nbv * RESIDUAL


LOAN_SHARE = 0.50


def loan_draws():
    """Kredilendirilen yatırımlar: Faz 1-2-3, ek bloklar, liyofilize makinesi (yenilemeler özsermayeden)."""
    d = {0: sum(v2.capex_phase(1)) * LOAN_SHARE, 1: sum(v2.capex_phase(2)) * LOAN_SHARE,
         2: sum(v for y, _, v, _ in FAZ3 if y == 2) * LOAN_SHARE}
    for py, area in blocks_extra():
        d[py - 1] = d.get(py - 1, 0) + BLOCK2_FIELD * area / 10 * LOAN_SHARE
        d[py] = d.get(py, 0) + BLOCK2_SHADE * area / 10 * LOAN_SHARE
    if CUR["own_fd_year"]:
        d[CUR["own_fd_year"]] = d.get(CUR["own_fd_year"], 0) + FD_MACHINE * LOAN_SHARE
    return d


def loans(mitigated=True):
    out = {}
    for dy, amt in loan_draws().items():
        for y, (i, p) in v2.loan_schedule(amt, dy).items():
            a = out.setdefault(y, [0.0, 0.0]); a[0] += i; a[1] += p
    return out


# ------------------------------------------------------------------ dış senaryo kancaları (model_v4)
ADJ = {"fixed_add": {}, "corp_mult": {}}   # yıl → ek sabit gider / kurumsal hacim çarpanı


# ------------------------------------------------------------------ çekirdek hesap
def year_pnl(y, yld_mult=1.0, pack_mult=1.0, hal_mult=1.0, harv_mult=1.0, unpicked=0.0,
             insurance_payout=0.0, freezer=True, fd=True, price_mult=1.0, contracts=True):
    k = y - 1
    kg = base_kg(y) * yld_mult * (1 - unpicked)
    second = kg * SECOND
    first = kg - second
    corp = min(CORP_T[k] * 1000 * (CUR["corp_factor"] if scaled(y) else 1) * ADJ["corp_mult"].get(y, 1.0)
               * (1 if contracts else 0), first)
    rest = first - corp
    packed = rest * PACK_SHARE[k] * (CUR["pack_factor"] if scaled(y) else 1)
    surplus = rest - packed
    has_freezer = freezer and y >= FREEZER_FROM
    to_freeze = (second + surplus * SURPLUS_TO_FREEZE) if has_freezer else 0.0
    hal = surplus - (surplus * SURPLUS_TO_FREEZE if has_freezer else 0)
    proc = 0.0 if has_freezer else second
    fd_in = to_freeze * (FD_SHARE[k] if fd else 0)
    iqf = to_freeze - fd_in
    fd_out = fd_in / FD_RATIO

    pp = PACK_PRICE * pack_mult * price_mult
    r_pack = packed * pp
    r_corp = corp * v2.CORP_PRICE * price_mult
    r_hal = hal * v2.HAL_PRICE * hal_mult * price_mult
    r_proc = proc * PROC_PRICE * price_mult
    r_iqf = iqf * IQF_PRICE * price_mult
    r_fd = fd_out * FD_PRICE * price_mult
    r_serv, r_lab, r_cons = SERVICE[k], LAB[k], CONSULT[k]
    rev = r_pack + r_corp + r_hal + r_proc + r_iqf + r_fd + r_serv + r_lab + r_cons + insurance_payout

    harvest = ((packed + corp) * v2.HARVEST["pack"] + (hal + proc + to_freeze) * v2.HARVEST["bulk"]) * harv_mult
    packaging = (packed + corp) * (PACK_COST + v2.PACKHOUSE_LABOR)
    dist = (r_pack * v2.DIST_COMM + packed * v2.COLD_TRANSPORT + corp * v2.CORP_EXTRA
            + r_hal * v2.HAL_COMM + hal * v2.HAL_PACK + r_proc * v2.PROC_COMM + proc * v2.PROC_PACK)
    frozen_cost = to_freeze * FREEZE_COST + iqf * (IQF_PACK + IQF_FREIGHT) + r_iqf * IQF_COMM
    fd_cost = fd_in * (FD_OWN if y >= own_fd_from() else FD_TOLL) + fd_out * FD_PACK
    svc = r_serv * v2.SERVICE_COST + r_lab * v2.LAB_COST + r_cons * v2.CONSULT_COST
    cogs = harvest + packaging + dist + frozen_cost + fd_cost + svc
    fx = fixed(y) + ADJ["fixed_add"].get(y, 0.0)
    return dict(y=y, kg=kg, packed=packed, corp=corp, hal=hal, proc=proc, iqf=iqf, fd_in=fd_in, fd_out=fd_out,
                r_pack=r_pack, r_corp=r_corp, r_hal=r_hal, r_proc=r_proc, r_iqf=r_iqf, r_fd=r_fd,
                r_serv=r_serv, r_lab=r_lab, r_cons=r_cons, r_ins=insurance_payout, rev=rev,
                harvest=harvest, packaging=packaging, dist=dist, frozen_cost=frozen_cost, fd_cost=fd_cost,
                svc=svc, cogs=cogs, gross=rev - cogs, fixed=fx, ebitda=rev - cogs - fx)


def run(shocks=None, mitigated=True, plan="10", **kw):
    """10 yıllık gelir tablosu + nakit akışı. shocks: {yıl: dict(year_pnl argümanları)}"""
    set_plan(plan)
    capex = capex_schedule(mitigated)
    if not mitigated:
        kw = dict(kw, freezer=False, fd=False, contracts=False)
    L = loans()
    losses = []          # [(yıl, tutar)]
    rows = []
    for y in range(1, YEARS + 1):
        args = dict(kw); args.update((shocks or {}).get(y, {}))
        r = year_pnl(y, **args)
        if not mitigated and y >= 2:
            r["fixed"] -= TARSIM; r["ebitda"] += TARSIM
        r["dep"] = depreciation(y, mitigated)
        r["intr"], r["princ"] = L.get(y, (0.0, 0.0))
        r["ebt"] = r["ebitda"] - r["dep"] - r["intr"]
        losses = [(yy, a) for yy, a in losses if y - yy <= LOSS_CARRY and a > 0]
        tax = 0.0
        if r["ebt"] < 0:
            losses.append((y, -r["ebt"]))
        else:
            taxable = r["ebt"]
            for i, (yy, a) in enumerate(losses):
                use = min(a, taxable); taxable -= use; losses[i] = (yy, a - use)
            tax = taxable * CORP_TAX
        r["tax"] = tax
        r["net"] = r["ebt"] - tax
        r["capex"] = capex.get(y, 0.0)
        r["loan_in"] = loan_draws().get(y, 0.0)
        r["fcf"] = r["ebitda"] - tax - r["capex"]
        r["eq_cf"] = r["fcf"] + r["loan_in"] - r["intr"] - r["princ"]
        rows.append(r)
    c0 = capex[0]
    rv = residual_value(mitigated)
    flows = [-c0] + [r["fcf"] for r in rows]
    eq = [-c0 + loan_draws()[0]] + [r["eq_cf"] for r in rows]
    flows[-1] += rv; eq[-1] += rv
    return dict(rows=rows, flows=flows, eq=eq, residual=rv)


def npv(flows, r=0.12):
    return sum(v / (1 + r) ** i for i, v in enumerate(flows))


def payback(flows):
    cum = 0
    for i, v in enumerate(flows):
        prev = cum; cum += v
        if i > 0 and cum >= 0 and v > 0:
            return i - 1 + (-prev) / v
    return None


def min_cum(flows):
    c = m = 0
    for v in flows:
        c += v; m = min(m, c)
    return m


SCEN = {
    "Baz": {},
    "Pesimistik": dict(yld_mult=0.75, price_mult=0.80, harv_mult=1.30),
    "İyimser": dict(yld_mult=1.20, price_mult=1.05),
}


# ------------------------------------------------------------------ Monte Carlo
EVENTS = [
    # (olay, olasılık/yıl, önlemsiz etki, önlemli etki)  — etki: verim çarpanı kaybı
    ("Sıcak dalgası / güneş yanığı", 0.30, 0.15, 0.05),
    ("Hasat döneminde yoğun yağış (meyve çürümesi)", 0.15, 0.10, 0.06),
    ("SWD (Drosophila suzukii) salgını", 0.35, 0.20, 0.05),
    ("Geç bahar donu", 0.05, 0.20, 0.10),
    ("Dolu", 0.05, 0.40, 0.40),
]
LABOR = (0.20, (1.35, 0.06), (1.15, 0.01))      # olasılık, (önlemsiz işçilik çarpanı, hasat edilemeyen), (önlemli)
GLUT = (0.25, (0.70, 0.90), (0.70, 0.95))       # olasılık, (hal, paketli) fiyat çarpanı önlemsiz / önlemli
TARSIM_COVER = 0.60                              # dolu/don kaybının sigortadan dönen payı (muafiyet sonrası)


# Baz verim (2,0 t/da) önlemli planda "ortalama bir yıl" kabul edilir: olayların beklenen
# kaybı potansiyel verime geri eklenir, böylece önlemli simülasyonun ortalaması baz verime denk gelir.
POTENTIAL = 1 / (1 - sum(p * m for _, p, _, m in EVENTS))


def simulate(n=5000, mitigated=True, seed=42, plan="10"):
    set_plan(plan)
    rnd = random.Random(seed)
    res = []
    for _ in range(n):
        shocks = {}
        for y in range(2, YEARS + 1):
            loss = 0.0; insured_loss = 0.0
            for name, p, un, mi in EVENTS:
                if rnd.random() < p:
                    hit = mi if mitigated else un
                    loss += hit
                    if mitigated and name in ("Dolu", "Geç bahar donu"):
                        insured_loss += hit
            ym = max(0.2, POTENTIAL * rnd.gauss(1.0, 0.08) * (1 - loss))
            lp, lu, lm = LABOR
            hm, up = (lm if mitigated else lu) if rnd.random() < lp else (1.0, 0.0)
            gp, gu, gm = GLUT
            halm, packm = (gm if mitigated else gu) if rnd.random() < gp else (1.0, 1.0)
            pm = max(0.5, rnd.gauss(1.0, 0.07))
            base_rev_per_kg = 4.0  # sigorta ödemesi için kayıp değer tahmini ($/kg)
            payout = insured_loss * base_kg(y) * base_rev_per_kg * TARSIM_COVER
            shocks[y] = dict(yld_mult=ym, harv_mult=hm, unpicked=up, hal_mult=halm,
                             pack_mult=packm, price_mult=pm, insurance_payout=payout)
        out = run(shocks, mitigated=mitigated, plan=plan)
        rows = out["rows"]
        res.append(dict(npv=npv(out["flows"]), npv0=npv(out["flows"], 0.0), irr=v2.irr(out["flows"]), ebt=[r["ebt"] for r in rows],
                        loss_years=sum(1 for r in rows[3:] if r["ebt"] < 0)))
    return res


def mc_summary(res):
    res_npv = sorted(r["npv"] for r in res)
    n = len(res)
    q = lambda a, p: a[int(p * (len(a) - 1))]
    steady = sorted(e for r in res for e in r["ebt"][4:])     # 2031-2036
    return dict(
        p_npv_neg=sum(1 for v in res_npv if v < 0) / n,
        p_capital_loss=sum(1 for r in res if r["npv0"] < 0) / n,
        irr_p10=q(sorted((r["irr"] if r["irr"] is not None else -1) for r in res), .10),
        irr_p50=q(sorted((r["irr"] if r["irr"] is not None else -1) for r in res), .50),
        irr_p90=q(sorted((r["irr"] if r["irr"] is not None else -1) for r in res), .90),
        npv_p10=q(res_npv, .10), npv_p50=q(res_npv, .50), npv_p90=q(res_npv, .90),
        ebt_p10=q(steady, .10), ebt_p50=q(steady, .50), ebt_p90=q(steady, .90),
        p_loss_year=sum(1 for e in steady if e < 0) / len(steady),
        avg_loss_years=sum(r["loss_years"] for r in res) / n,
        p_2plus=sum(1 for r in res if r["loss_years"] >= 2) / n,
    )


# ------------------------------------------------------------------ çıktı
fmt = v2.fmt
usd = v2.usd
pct = v2.pct
pct0 = v2.pct0


def md_pnl(res, years=range(1, 11)):
    R = [r for r in res["rows"] if r["y"] in years]
    lines = ["| USD | " + " | ".join(LABEL[r["y"]] for r in R) + " |", "|---|" + "---:|" * len(R)]

    def line(lab, key, bold=False, neg=False, d=0):
        vals = []
        for r in R:
            v = key(r) if callable(key) else r[key]
            v = -v if neg else v
            vals.append(f"**{fmt(v, d)}**" if bold else fmt(v, d))
        lines.append(f"| {'**'+lab+'**' if bold else lab} | " + " | ".join(vals) + " |")
    line("Rekolte (t)", lambda r: r["kg"] / 1000, d=1)
    line("Taze paketli", "r_pack")
    line("Kurumsal paket", "r_corp")
    line("Hal / dökme taze", "r_hal")
    line("İşleme (2. sınıf, dondurucu öncesi)", "r_proc")
    line("IQF dondurulmuş", "r_iqf")
    line("Liyofilize (kuru)", "r_fd")
    line("Hizmet + lab + danışmanlık", lambda r: r["r_serv"] + r["r_lab"] + r["r_cons"])
    line("TOPLAM GELİR", "rev", bold=True)
    line("Hasat", "harvest", neg=True)
    line("Ambalaj + pakethane", "packaging", neg=True)
    line("Dağıtım + komisyon", "dist", neg=True)
    line("Dondurma + IQF lojistik", "frozen_cost", neg=True)
    line("Liyofilize (fason/kendi) + ambalaj", "fd_cost", neg=True)
    line("Hizmet maliyeti", "svc", neg=True)
    line("Sabit giderler", "fixed", neg=True)
    line("FAVÖK", "ebitda", bold=True)
    line("Amortisman", "dep", neg=True)
    line("Faiz", "intr", neg=True)
    line("VERGİ ÖNCESİ KÂR", "ebt", bold=True)
    line("Kurumlar vergisi (%25)", "tax", neg=True)
    line("NET KÂR", "net", bold=True)
    lines.append("| Net marj | " + " | ".join("–" if r["rev"] == 0 else pct0(r["net"] / r["rev"]) for r in R) + " |")
    return "\n".join(lines)


def md_cash(res):
    R = res["rows"]
    c0 = capex_schedule()[0]
    lines = ["| USD | Y0 | " + " | ".join(LABEL[r["y"]] for r in R) + " |", "|---|---:|" + "---:|" * len(R)]
    seq = [dict(ebitda=0, tax=0, capex=-c0, loan_in=loan_draws()[0], intr=0, princ=0)]
    for r in R:
        seq.append(dict(ebitda=r["ebitda"], tax=-r["tax"], capex=-r["capex"], loan_in=r["loan_in"],
                        intr=-r["intr"], princ=-r["princ"]))
    for d in seq:
        d["resid"] = 0.0
    seq[-1]["resid"] = res["residual"]
    cum = 0
    for d in seq:
        d["net"] = sum(d.values()); cum += d["net"]; d["cum"] = cum
    for lab, k in [("FAVÖK", "ebitda"), ("Vergi", "tax"), ("Yatırım + yenileme", "capex"),
                   ("Kalıntı değer (net defter değerinin %50'si)", "resid"),
                   ("Kredi kullanımı", "loan_in"), ("Faiz", "intr"), ("Anapara", "princ"),
                   ("**Özsermaye nakit akışı**", "net"), ("**Kümülatif**", "cum")]:
        lines.append(f"| {lab} | " + " | ".join(fmt(d[k]) for d in seq) + " |")
    return "\n".join(lines)


def md_volumes(plan="10"):
    res = run(plan=plan)
    out = ["| Yıl | Rekolte | Taze paketli | Kurumsal | Hal | IQF | Liyofilize girdi → kuru | Taze payı |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in res["rows"]:
        fresh = r["packed"] + r["corp"] + r["hal"]
        share = fresh / r["kg"] if r["kg"] else 0
        out.append(f"| {LABEL[r['y']]} | {fmt(r['kg']/1000,1)} t | {fmt(r['packed']/1000,1)} t | {fmt(r['corp']/1000,1)} t | "
                   f"{fmt(r['hal']/1000,1)} t | {fmt(r['iqf']/1000,1)} t | {fmt(r['fd_in']/1000,1)} t → {fmt(r['fd_out'])} kg | %{share*100:.0f} |")
    return "\n".join(out)


def md_scen():
    out = ["| Gösterge | " + " | ".join(SCEN) + " |", "|---|" + "---:|" * len(SCEN)]
    R = {n: run(**kw) for n, kw in SCEN.items()}
    def row(lab, fn): out.append(f"| {lab} | " + " | ".join(fn(R[n]) for n in SCEN) + " |")
    row("10 yıl toplam gelir", lambda r: usd(sum(x["rev"] for x in r["rows"])))
    row("10 yıl toplam vergi öncesi kâr", lambda r: usd(sum(x["ebt"] for x in r["rows"])))
    row("10 yıl toplam net kâr", lambda r: usd(sum(x["net"] for x in r["rows"])))
    row("Tam verim yılı (2032) net kâr", lambda r: usd(r["rows"][5]["net"]))
    row("Proje NPV (%12)", lambda r: usd(npv(r["flows"])))
    row("Proje IRR", lambda r: pct(v2.irr(r["flows"])))
    row("Özsermaye IRR (kredili)", lambda r: pct(v2.irr(r["eq"])))
    row("Geri dönüş (kaldıraçsız)", lambda r: "geri dönmez" if payback(r["flows"]) is None else fmt(payback(r["flows"]), 1) + " yıl")
    row("Azami özsermaye ihtiyacı", lambda r: usd(-min_cum(r["eq"])))
    return "\n".join(out)


def md_block2_capex():
    rows = [(k, v) for f, g, k, v, *_ in v2.CAPEX if g == "Tarla" and f == 1]
    out = ["| Kalem (2. blok, 10 da) | USD | TL |", "|---|---:|---:|"]
    for k, v in rows + [("8 adet ek DIY toprak düğümü (LoRaWAN ağı genişletme)", 2240)]:
        out.append(f"| {k} | {fmt(v)} | {fmt(v*FX)} |")
    base = sum(v for _, v in rows) + 2240
    out.append(f"| Beklenmeyen giderler (%8) | {fmt(base*v2.CONTINGENCY)} | {fmt(base*v2.CONTINGENCY*FX)} |")
    out.append(f"| **Tarla kurulumu toplamı** (dikimden önceki kış) | **{fmt(BLOCK2_FIELD)}** | **{fmt(BLOCK2_FIELD*FX)}** |")
    out.append(f"| Gölge filesi (ilk hasattan önce, %8 dahil) | {fmt(BLOCK2_SHADE)} | {fmt(BLOCK2_SHADE*FX)} |")
    out.append(f"| Kendi liyofilize makinesi + kurulum (20 da'da ekonomik) | {fmt(FD_MACHINE)} | {fmt(FD_MACHINE*FX)} |")
    out.append(f"| **20 da için ek yatırım toplamı** | **{fmt(BLOCK2_FIELD+BLOCK2_SHADE+FD_MACHINE)}** | **{fmt((BLOCK2_FIELD+BLOCK2_SHADE+FD_MACHINE)*FX)}** |")
    return "\n".join(out)


def md_capex_extra():
    out = ["| Yıl | Kalem | USD | Ömür |", "|---|---|---:|---:|"]
    for y, k, v, life in sorted(FAZ3 + REPLACE):
        out.append(f"| {LABEL[y]} sonu | {k} | {fmt(v)} | {life} yıl |")
    return "\n".join(out)


def md_mc():
    a = mc_summary(simulate(mitigated=False))
    b = mc_summary(simulate(mitigated=True))
    rows = [
        ("Sermayenin 10 yılda geri dönmeme olasılığı (reel)", pct(a["p_capital_loss"]), pct(b["p_capital_loss"])),
        ("%12 hedef getirinin altında kalma olasılığı (NPV@12 < 0)", pct(a["p_npv_neg"]), pct(b["p_npv_neg"])),
        ("Proje IRR — kötü / ortanca / iyi (P10/P50/P90)", " / ".join(pct(a[k]) for k in ("irr_p10", "irr_p50", "irr_p90")),
         " / ".join(pct(b[k]) for k in ("irr_p10", "irr_p50", "irr_p90"))),
        ("Olgun yıllarda (2031-36) bir yılın zararla kapanma olasılığı", pct(a["p_loss_year"]), pct(b["p_loss_year"])),
        ("Olgun yıl vergi öncesi kâr — kötü (P10)", usd(a["ebt_p10"]), usd(b["ebt_p10"])),
        ("Olgun yıl vergi öncesi kâr — ortanca (P50)", usd(a["ebt_p50"]), usd(b["ebt_p50"])),
        ("Olgun yıl vergi öncesi kâr — iyi (P90)", usd(a["ebt_p90"]), usd(b["ebt_p90"])),
        ("2030-36'da ortalama zarar yılı sayısı (7 yılda)", fmt(a["avg_loss_years"], 1), fmt(b["avg_loss_years"], 1)),
        ("7 yılda 2+ zarar yılı yaşama olasılığı", pct(a["p_2plus"]), pct(b["p_2plus"])),
    ]
    out = ["| Gösterge (5.000 simülasyon) | Önlemsiz | Önlemli (bu plan) |", "|---|---:|---:|"]
    out += [f"| {x} | {y} | {z} |" for x, y, z in rows]
    return "\n".join(out)


def md_events():
    out = ["| Olay | Yıllık olasılık | Önlemsiz verim kaybı | Önlemli verim kaybı |", "|---|---:|---:|---:|"]
    for n, p, u, m in EVENTS:
        out.append(f"| {n} | %{p*100:.0f} | %{u*100:.0f} | %{m*100:.0f}{' (+ TARSİM %60)' if n in ('Dolu', 'Geç bahar donu') else ''} |")
    out.append(f"| İşçi bulamama | %{LABOR[0]*100:.0f} | işçilik +%35, ürünün %6'sı toplanamaz | işçilik +%15, %1 |")
    out.append(f"| Pazar bolluğu (fiyat çöküşü) | %{GLUT[0]*100:.0f} | hal −%30, paketli −%10 | hal −%30, paketli −%5, fazla ürün dondurucuya |")
    out.append("| Normal dalgalanma (her yıl) | – | verim σ %8, fiyat σ %7 | aynı |")
    return "\n".join(out)


def md_plans():
    keys = list(PLANS)
    R = {k: run(plan=k) for k in keys}
    caps = {}
    for k in keys:
        set_plan(k); caps[k] = capex_schedule()
    out = ["| Gösterge | " + " | ".join(PLANS[k]["name"] for k in keys) + " |", "|---|" + "---:|" * len(keys)]
    def row(lab, fn): out.append(f"| {lab} | " + " | ".join(fn(k) for k in keys) + " |")
    row("Toplam yatırım (10 yıl, yenileme dahil)", lambda k: usd(sum(caps[k].values())))
    row("2032 rekolte", lambda k: fmt(R[k]["rows"][5]["kg"] / 1000, 0) + " t")
    row("2032 gelir", lambda k: usd(R[k]["rows"][5]["rev"]))
    row("2032 vergi öncesi kâr", lambda k: usd(R[k]["rows"][5]["ebt"]))
    row("10 yıl toplam gelir", lambda k: usd(sum(x["rev"] for x in R[k]["rows"])))
    row("10 yıl toplam net kâr", lambda k: usd(sum(x["net"] for x in R[k]["rows"])))
    row("Proje IRR", lambda k: pct(v2.irr(R[k]["flows"])))
    row("Özsermaye IRR (kredili)", lambda k: pct(v2.irr(R[k]["eq"])))
    row("Proje NPV (%12)", lambda k: usd(npv(R[k]["flows"])))
    row("Geri dönüş (kaldıraçsız)", lambda k: fmt(payback(R[k]["flows"]), 1) + " yıl")
    row("Azami özsermaye ihtiyacı", lambda k: usd(-min_cum(R[k]["eq"])))
    return "\n".join(out)


def md_mc_plans(keys=("10", "20A", "20B")):
    S = {k: mc_summary(simulate(plan=k)) for k in keys}
    out = ["| Önlemli plan, 5.000 simülasyon | " + " | ".join(PLANS[k]["name"] for k in keys) + " |",
           "|---|" + "---:|" * len(keys)]
    def row(lab, fn): out.append(f"| {lab} | " + " | ".join(fn(S[k]) for k in keys) + " |")
    row("Sermayenin geri dönmeme olasılığı", lambda a: pct(a["p_capital_loss"]))
    row("%12 hedefin altında kalma olasılığı", lambda a: pct(a["p_npv_neg"]))
    row("Proje IRR P10 / P50 / P90", lambda a: " / ".join(pct(a[x]) for x in ("irr_p10", "irr_p50", "irr_p90")))
    row("Olgun yılın zararla kapanma olasılığı", lambda a: pct(a["p_loss_year"]))
    row("Olgun yıl vergi öncesi kâr P10 / P50", lambda a: usd(a["ebt_p10"]) + " / " + usd(a["ebt_p50"]))
    return "\n".join(out)


if __name__ == "__main__":
    if "--tables" in sys.argv:
        b = run()
        print(md_volumes()); print(); print(md_pnl(b, range(1, 6))); print(); print(md_pnl(b, range(6, 11)))
        print(); print(md_cash(run())); print(); print(md_scen()); print(); print(md_capex_extra())
        print(); print(md_plans()); print(); print(md_block2_capex())
        b20 = run(plan="20B")
        print(); print(md_volumes("20B")); print(); print(md_pnl(b20, range(1, 6))); print(); print(md_pnl(b20, range(6, 11)))
        print(); print(md_cash(run(plan="20B")))
    elif "--mc" in sys.argv:
        print(md_events()); print(); print(md_mc()); print(); print(md_mc_plans())
    else:
        for n, kw in SCEN.items():
            r = run(**kw)
            print(n, "rev", [round(x["rev"]) for x in r["rows"]])
            print("   ebt", [round(x["ebt"]) for x in r["rows"]], "net", [round(x["net"]) for x in r["rows"]])
            print("   irr", pct(v2.irr(r["flows"])), "eq", pct(v2.irr(r["eq"])), "npv", round(npv(r["flows"])),
                  "pb", payback(r["flows"]), "mincum", round(min_cum(r["eq"])))
        print("capex", capex_schedule())


def channel_margins():
    """Taze kg başına katkı payı (hasat dahil, sabit gider hariç)."""
    H, B = v2.HARVEST["pack"], v2.HARVEST["bulk"]
    fd_rev = FD_PRICE / FD_RATIO
    rows = [
        ("Kurumsal markalı paket", v2.CORP_PRICE - PACK_COST - v2.PACKHOUSE_LABOR - v2.CORP_EXTRA - H, "Ön sözleşmeli, fiyat sabit"),
        ("Taze paketli (100/200/500 g)", PACK_PRICE * (1 - v2.DIST_COMM) - v2.COLD_TRANSPORT - PACK_COST - v2.PACKHOUSE_LABOR - H, "Ana kanal; raf ömrü 7-10 gün"),
        ("Liyofilize — kendi makine", fd_rev - FD_PACK / FD_RATIO - FD_OWN - FREEZE_COST - B, "Makine + izin: ~$4.200/yıl sabit"),
        ("Liyofilize — fason", fd_rev - FD_PACK / FD_RATIO - FD_TOLL - FREEZE_COST - B, "Yatırımsız, 12-24 ay raf ömrü"),
        ("IQF dondurulmuş", IQF_PRICE * (1 - IQF_COMM) - IQF_PACK - IQF_FREIGHT - FREEZE_COST - B, "Kış satışı, emniyet supabı"),
        ("Hal / dökme taze", v2.HAL_PRICE * (1 - v2.HAL_COMM) - v2.HAL_PACK - B, "Bolluk yılında −%30"),
        ("İşleme tesisine 2. sınıf", PROC_PRICE * (1 - v2.PROC_COMM) - v2.PROC_PACK - B, "Dondurucu yoksa tek çıkış"),
    ]
    return rows


def md_channels():
    out = ["| Kanal | Taze kg başına katkı (USD) | Not |", "|---|---:|---|"]
    for k, v, n in channel_margins():
        out.append(f"| {k} | {fmt(v, 2)} | {n} |")
    return "\n".join(out)


def own_fd_breakeven():
    saving = FD_TOLL - FD_OWN
    fixed_cost = 24000 / 8 + 1200
    return fixed_cost / saving
