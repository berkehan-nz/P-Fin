"""RİSK / GERÇEKÇİLİK TESTİ — model_final'in iyimser varsayımlarını tek tek geri çeker.

    python reports/bogurtlen-fizibilite/model_risk.py            # özet
    python reports/bogurtlen-fizibilite/model_risk.py --tables   # rapor tabloları

Yatırım listesi ve sabit giderler model_final/model_v8'den aynen alınır; yalnızca
gelir, verim, işçilik verimi ve 'görünmeyen' maliyetler senaryoya göre değişir.
Tüm tutarlar Ekim 2026 TL, reel (enflasyonsuz).
"""
from __future__ import annotations

import random
import statistics as st
import sys
from dataclasses import dataclass, field, replace

import model_final as F
import model_v8 as v8

fmt, mtl, pct, irr, npv, payback, cum = v8.fmt, v8.mtl, v8.pct, v8.irr, v8.npv, v8.payback, v8.cum
P = v8.PLANS["B"]
YRS = range(1, v8.YEARS + 1)


@dataclass
class S:
    name: str
    yields: list = field(default_factory=lambda: list(F.HYBRID))   # t/da, 10 yıl
    hal: float = v8.HAL_GROSS          # hal brüt TL/kg (sezon ağırlıklı)
    partner: float = v8.PARTNER_PRICE  # ortak paketli, komisyon öncesi
    share: tuple = (0.5, 0.75, 0.8)    # 1. sınıfın paketliye giden payı (Y1, Y2, Y3+)
    upick_t: list = field(default_factory=lambda: list(v8.UPICK_T))
    upick_price: float = v8.UPICK_PRICE
    second: float = v8.SECOND
    proc: float = v8.PROC_PRICE
    kg_pack: float = 55                # kişi/gün paket kalitesi
    kg_bulk: float = 70
    loss: float = 0.0                  # satılamayan/çürüyen/toplanamayan pay
    supervisor: float = 0.0            # sezonluk saha sorumlusu TL/yıl (Y2+)
    rent: float = 0.0                  # arazinin fırsat maliyeti TL/yıl
    father: float = 0.0                # babanın emeğinin piyasa karşılığı TL/yıl
    shock: dict = field(default_factory=dict)   # {yıl: verim çarpanı}


def run(s: S):
    it = F.items()
    rows = []
    for y in YRS:
        k = y - 1
        kg = s.yields[k] * 1000 * P["bb"] * s.shock.get(y, 1.0)
        kg_sold = kg * (1 - s.loss)
        second = kg_sold * s.second
        first = kg_sold - second
        up = min(s.upick_t[k] * 1000, first * 0.4)
        rest = first - up
        packed = rest * s.share[min(k, 2)]
        hal = rest - packed
        rev = (packed * s.partner * (1 - v8.PARTNER_COMM) + hal * s.hal * (1 - v8.HAL_COST_RATE)
               + up * s.upick_price + second * s.proc)
        hp, hb = v8.DAILY / s.kg_pack, v8.DAILY / s.kg_bulk
        # toplanıp satılamayan meyvenin de toplama maliyeti var (kaybın yarısı tarlada kalır varsayımı)
        var = (packed * (hp + v8.PACK + v8.PICKUP) + hal * (hb + v8.HAL_CRATE) + up * v8.UPICK_COST
               + second * (hb + 5) + kg * s.loss * 0.5 * hb)
        fx = sum(v8.fixed(y, P).values()) + s.rent + s.father + (s.supervisor if y >= 2 else 0)
        ebitda = rev - var - fx
        dep = sum(v / life for _, yy, _, _, _, v, life in it if yy + 1 <= y < yy + 1 + life)
        stopaj = rev * v8.STOPAJ
        cap = sum(v for _, yy, _, _, _, v, _ in it if yy == y)
        rows.append(dict(y=y, kg=kg, rev=rev, var=var, fixed=fx, net=ebitda - dep - stopaj,
                         cash=ebitda - stopaj - cap, rpk=rev / kg_sold if kg_sold else 0))
    c0 = sum(v for _, yy, _, _, _, v, _ in it if yy == 0)
    flows = [-c0] + [r["cash"] for r in rows]
    nbv = sum(v * max(0, (yy + life - v8.YEARS)) / life for _, yy, _, _, _, v, life in it)
    flows[-1] += nbv * 0.5
    c = cum(flows)
    return dict(rows=rows, flows=flows, peak=-min(c), pb=payback(flows), irr=irr(flows), npv=npv(flows),
                net5=sum(r["net"] for r in rows[:5]))


# ------------------------------------------------------------------ senaryolar
BASE = S("Rapor (son hâl)")
# Gerçekçi: Bursa'daki küçük üreticinin gerçekten yaşadığına yakın
REAL_Y = [0.15, 0.55, 1.1, 1.4, 1.5, 1.5, 1.5, 1.5, 1.4, 1.3]
REAL = S("Gerçekçi", yields=REAL_Y, hal=120, partner=220, share=(0.3, 0.5, 0.6),
         upick_t=[0, 0.2, 0.4, 0.6, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8], upick_price=300,
         second=0.25, proc=45, kg_pack=40, kg_bulk=55, loss=0.10,
         supervisor=200000, rent=40000)
BAD_Y = [0.1, 0.4, 0.9, 1.2, 1.2, 1.2, 1.2, 1.2, 1.1, 1.0]
BAD = S("Kötü", yields=BAD_Y, hal=90, partner=180, share=(0.2, 0.3, 0.3),
        upick_t=[0, 0.1, 0.2, 0.3, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4], upick_price=250,
        second=0.30, proc=35, kg_pack=35, kg_bulk=50, loss=0.15,
        supervisor=200000, rent=40000, shock={4: 0.4})
SCEN = [BASE, REAL, BAD]

# Tek değişken: rapordan başlayıp yalnız bir varsayımı gerçekçiye çekmek
ONE = [
    ("Hal fiyatı 199 → 120 TL/kg", dict(hal=120)),
    ("Ortak fiyatı 300 → 220 TL/kg", dict(partner=220)),
    ("Paketliye giden pay %80 → %60", dict(share=(0.3, 0.5, 0.6))),
    ("Kendin-topla 2 t → 0,8 t, 400 → 300 TL", dict(upick_t=REAL.upick_t, upick_price=300)),
    ("Tam verim 2,0 → 1,5 t/da, yavaş rampa", dict(yields=REAL_Y)),
    ("Toplama hızı 55 → 40 kg/gün (paket)", dict(kg_pack=40, kg_bulk=55)),
    ("%10 satılamayan/çürüyen ürün", dict(loss=0.10)),
    ("2. sınıf %20 → %25, 65 → 45 TL", dict(second=0.25, proc=45)),
    ("Sezonluk saha sorumlusu 200 bin TL/yıl", dict(supervisor=200000)),
    ("Arazi fırsat maliyeti (kira) 40 bin TL/yıl", dict(rent=40000)),
    ("Babanın emeği ücretli sayılırsa 240 bin TL/yıl", dict(father=240000)),
]


# ------------------------------------------------------------------ Monte Carlo
def mc(n=5000, seed=7):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        pm = rnd.lognormvariate(0, 0.20)                       # genel fiyat seviyesi
        ym = rnd.triangular(0.65, 1.05, 0.85)                  # gerçek verim / rapor verimi
        shock = {}
        partner_lost = None
        for y in YRS:
            m = 1.0
            if y >= 2:
                if rnd.random() < 0.10: m *= 0.6               # geç don / dolu (TARSİM kısmen)
                if rnd.random() < 0.15: m *= 0.75              # SWD / gri küf / kök çürüklüğü yılı
                if rnd.random() < 0.15: m *= 0.85              # sıcak dalgası, güneş yanığı
                if rnd.random() < 0.20: m *= 0.90              # işçi bulunamadı, meyve tarlada kaldı
                if partner_lost is None and rnd.random() < 0.12: partner_lost = y
            shock[y] = m
        s = S("MC", yields=[x * ym for x in F.HYBRID], hal=v8.HAL_GROSS * 0.75 * pm,
              partner=260 * pm, upick_t=[x * 0.6 for x in v8.UPICK_T], upick_price=350 * pm,
              kg_pack=rnd.uniform(38, 55), kg_bulk=rnd.uniform(50, 70), loss=rnd.uniform(0.03, 0.15),
              second=0.22, proc=55 * pm, supervisor=200000, shock=shock)
        r = run(s)
        if partner_lost:   # ortak kaybı: o yıldan sonra paketli pay %20'ye iner
            s2 = replace(s, share=(0.2, 0.2, 0.2))
            r2 = run(s2)
            rows = r["rows"][:partner_lost - 1] + r2["rows"][partner_lost - 1:]
            flows = r["flows"][:partner_lost] + r2["flows"][partner_lost:]
            c = cum(flows)
            r = dict(rows=rows, flows=flows, peak=-min(c), pb=payback(flows), irr=irr(flows), npv=npv(flows),
                     net5=sum(x["net"] for x in rows[:5]))
        out.append(r)
    return out


def q(xs, p):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))]


# ------------------------------------------------------------------ tablolar
def md_scen():
    R = [run(s) for s in SCEN]
    out = ["| | " + " | ".join(s.name for s in SCEN) + " |", "|---|" + "---:|" * len(SCEN)]
    def line(lab, f): out.append(f"| {lab} | " + " | ".join(f(r) for r in R) + " |")
    line("Ortalama satış fiyatı 2031 (TL/kg, tüm kanallar)", lambda r: fmt(r["rows"][4]["rpk"]))
    line("Rekolte 2031 (ton)", lambda r: fmt(r["rows"][4]["kg"] / 1000, 1))
    for i, yy in enumerate(range(2027, 2032)):
        line(f"Net kâr {yy}", lambda r, i=i: mtl(r["rows"][i]["net"]))
    line("**5 yıl toplam net**", lambda r: f"**{mtl(r['net5'])}**")
    line("Cepten en yüksek (kümülatif nakit dibi)", lambda r: mtl(r["peak"]))
    line("Geri dönüş", lambda r: f"{fmt(r['pb'], 1)} yıl" if r["pb"] else "dönmüyor")
    line("10 yıl IRR (reel)", lambda r: pct(r["irr"]) if r["irr"] is not None else "—")
    line("NPV @%12 reel", lambda r: mtl(r["npv"]))
    return "\n".join(out)


def md_one():
    b = run(BASE)
    out = ["| Tek başına geri çekilen varsayım | 2031 net | Fark | 5 yıl net | Geri dönüş |", "|---|---:|---:|---:|---:|"]
    res = []
    for lab, kw in ONE:
        r = run(replace(BASE, **kw)); res.append((r["rows"][4]["net"] - b["rows"][4]["net"], lab, r))
    out.append(f"| *Rapor (son hâl)* | {mtl(b['rows'][4]['net'])} | — | {mtl(b['net5'])} | {fmt(b['pb'],1)} yıl |")
    for d, lab, r in sorted(res):
        out.append(f"| {lab} | {mtl(r['rows'][4]['net'])} | {mtl(d)} | {mtl(r['net5'])} | "
                   f"{fmt(r['pb'],1) + ' yıl' if r['pb'] else 'dönmüyor'} |")
    return "\n".join(out)


def md_mc():
    R = mc()
    y5 = [r["rows"][4]["net"] for r in R]; n5 = [r["net5"] for r in R]; nv = [r["npv"] for r in R]
    pbs = [r["pb"] for r in R]
    lines = ["| Gösterge | Kötü %10 | Medyan | İyi %10 |", "|---|---:|---:|---:|",
             f"| 2031 net kâr | {mtl(q(y5,.1))} | {mtl(q(y5,.5))} | {mtl(q(y5,.9))} |",
             f"| 5 yıl toplam net | {mtl(q(n5,.1))} | {mtl(q(n5,.5))} | {mtl(q(n5,.9))} |",
             f"| NPV @%12 reel (10 yıl) | {mtl(q(nv,.1))} | {mtl(q(nv,.5))} | {mtl(q(nv,.9))} |"]
    pb_ok = [p for p in pbs if p is not None]
    stats = dict(p_loss=sum(1 for v in nv if v < 0) / len(nv),
                 p_y5_neg=sum(1 for v in y5 if v < 0) / len(y5),
                 p_pb4=sum(1 for p in pbs if p is not None and p <= 4) / len(pbs),
                 p_nopb=sum(1 for p in pbs if p is None) / len(pbs),
                 pb_med=st.median(pb_ok) if pb_ok else None,
                 p_y5_1m=sum(1 for v in y5 if v >= 1_000_000) / len(y5))
    return "\n".join(lines), stats


if __name__ == "__main__":
    if "--tables" in sys.argv:
        print(md_scen()); print(); print(md_one()); print(); t, s = md_mc(); print(t); print(s)
    else:
        for s in SCEN:
            r = run(s)
            print(f"{s.name:18} 2031 net {mtl(r['rows'][4]['net']):>14}  5y {mtl(r['net5']):>14}  "
                  f"pb {r['pb']}  irr {r['irr']}  peak {mtl(r['peak'])}  rpk {r['rows'][4]['rpk']:.0f}")
