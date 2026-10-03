"""GÜÇLENDİRME — daha büyük yatırımla risk azalır mı? Sözleşme, otel kanalı + agro-turizm, dondurma, tünel, 20 da.

    python reports/bogurtlen-fizibilite/model_guc.py            # özet
    python reports/bogurtlen-fizibilite/model_guc.py --tables   # rapor tabloları

Her seçenek model_risk ile aynı 5.000 rastgele 10 yıl üzerinde (ortak rastgele sayılar)
koşturulur; fark yalnızca seçeneğin kendisinden gelir. Ekim 2026 TL, reel.
T işaretli parametreler tahmindir; teklif/üretici görüşmesiyle teyit edilmelidir.
"""
from __future__ import annotations

import random
import statistics as st
import sys
from dataclasses import dataclass

import model_final as F
import model_v8 as v8

fmt, mtl, pct, irr, npv, payback, cum = v8.fmt, v8.mtl, v8.pct, v8.irr, v8.npv, v8.payback, v8.cum
YRS = range(1, v8.YEARS + 1)
FIELD = ("Arazi", "Fidan", "Telli sistem", "Sulama", "Kalite")

# --- T: tahmini parametreler
TUNNEL_CAPEX = 450000      # TL/da, böğürtlen için yağmur örtülü yüksek tünel (v8 ahududu tüneli 600k, böcek tüllü)
TUNNEL_PLASTIC = 80000     # TL/da, 4 yılda bir
TUNNEL_FIX = 15000         # TL/da/yıl bakım, perde, bağlama
TUNNEL_YIELD = 1.15        # örtü altı verim çarpanı
TUNNEL_PREMIUM = 1.25      # 2-3 hafta erken hasat → Haziran/Temmuz başı fiyatı
FROZEN_CAPEX = 400000      # şok dondurucu dolap (-35 °C) + -20 °C donuk oda panel + paketleme + işletme kaydı
FROZEN_FIX = 50000         # elektrik, etiket, analiz, kayıt
FROZEN_GROSS = 200         # TL/kg B2B (pastane, kafe, smoothie, ortağın donuk hattı)
FROZEN_COST = 30           # TL/kg dondurma + poşet + koli + depolama
FROZEN_CAP = 4.0           # t/yıl donuk talep sınırı
PARTNER_CAP = 10.0         # t/yıl ortağın taze paketli alabileceği hacim (sorulacak)
HORECA_GROSS = 250         # TL/kg otel kahvaltı/pastane, yıllık sabit fiyat (sorulacak)
HORECA_CAP = 3.0           # t/yıl otellerin taze alabileceği hacim (sorulacak)
HORECA2_GROSS = 100        # TL/kg 2. sınıf → otel reçel/tatlı/smoothie
HORECA2_CAP = 2.0
AGRO_MULT = 1.5            # otel misafiri + tur → kendin-topla hacmi
AGRO_PRICE = 450           # TL/kg deneyim fiyatı (giriş + toplanan)
AGRO_CAPEX = 80000
AGRO_FIX = 40000           # sezonluk ziyaretçi görevlisi payı, sigorta, ilan


@dataclass
class Opt:
    key: str
    name: str
    bb: float = 10
    tunnel: float = 0
    frozen: bool = False
    contract: bool = False
    horeca: bool = False           # ortağın otelleri: kahvaltı/pastane taze + 2. sınıf reçel/tatlı
    agro: bool = False             # otel misafirleriyle kendin-topla / bahçe ziyareti
    supervisor: float = 200000


def capex(o: Opt):
    out = []
    for ph, y, g, k, q, v, life in F.items():
        if g in FIELD:
            v *= o.bb / 10
        elif g == "Soğuk zincir" and o.bb > 10:
            v *= 1.6
        elif g == "Hasat" and o.bb > 10:
            v *= 1.4
        elif g == "Yenileme" and ("malç" in k or "filesi" in k):
            v *= o.bb / 10
        out.append((ph, y, g, k, q, v, life))
    if o.tunnel:
        out.append((0, 0, "Tünel", "Yağmur örtülü yüksek tünel", f"{fmt(o.tunnel,0)} da", TUNNEL_CAPEX * o.tunnel * (1 + F.CONT), 10))
        out += [(3, y, "Yenileme", "Tünel plastiği", "", TUNNEL_PLASTIC * o.tunnel, 4) for y in (4, 8)]
    if o.agro:
        out.append((1, 1, "Agro-turizm", "Ziyaretçi alanı: gölgelik, oturma, WC, otopark, tabela", "", AGRO_CAPEX * (1 + F.CONT), 7))
    if o.frozen:
        out.append((1, 1, "Dondurma", "Şok dondurucu + donuk oda + paketleme + kayıt", "", FROZEN_CAPEX * (1 + F.CONT), 8))
    return out


def run(o: Opt, d):
    """d: tek bir rastgele dünya (fiyat seviyesi, verim, olaylar)."""
    it = capex(o)
    big = o.bb > 10
    p = dict(bb=o.bb, rasp=0, upick=True)
    pm = d["pm"]
    partner = max(220, 260 * pm) if o.contract else 260 * pm
    lost = d["lost_c"] if o.contract else d["lost"]
    hal_net = v8.HAL_GROSS * 0.75 * pm * (1 - v8.HAL_COST_RATE) - v8.HAL_CRATE
    fr_net = FROZEN_GROSS * pm ** 0.5 * (1 - v8.PARTNER_COMM) - FROZEN_COST   # donuk fiyat daha az oynak
    ho_net = HORECA_GROSS * pm ** 0.5 * (1 - v8.PARTNER_COMM) - 10      # kasa, teslim
    ho2_net = HORECA2_GROSS * pm ** 0.5 * (1 - v8.PARTNER_COMM) - 5
    kg_pack = d["kg_pack"] - (7 if big else 0)
    hp, hb = v8.DAILY / kg_pack, v8.DAILY / d["kg_bulk"]
    rows = []
    for y in YRS:
        k = y - 1
        base = F.HYBRID[k] * d["ym"]
        ev = d["ev"][k]
        lab = ev["lab"] if not big else ev["lab_big"]
        m_open = ev["frost"] * ev["dis"] * ev["heat"] * lab
        m_tun = ev["heat"] * lab * (1 - (1 - ev["dis"]) * 0.4)
        kg_o = base * 1000 * (o.bb - o.tunnel) * m_open
        kg_t = base * 1000 * o.tunnel * TUNNEL_YIELD * m_tun
        loss = d["loss"]
        sold_o, sold_t = kg_o * (1 - loss), kg_t * (1 - loss / 2)
        sec = sold_o * 0.22 + sold_t * 0.10
        first_o, first_t = sold_o * 0.78, sold_t * 0.90
        up = min(v8.UPICK_T[k] * 600 * (1.3 if big else 1) * (AGRO_MULT if o.agro else 1), first_o * 0.4)
        up_price = (AGRO_PRICE if o.agro else 350) * pm ** (0.5 if o.agro else 1)
        share = (0.2 if (lost and y >= lost) else ([0.5, 0.75, 0.8][min(k, 2)] if not o.contract else [0.6, 0.75, 0.8][min(k, 2)]))
        cap = PARTNER_CAP * 1000 * (0.25 if (lost and y >= lost) else 1)
        pk_t = min(first_t * share if not o.contract else first_t * 0.95, cap)
        pk_o = min((first_o - up) * share, cap - pk_t)
        rest = first_o - up - pk_o + (first_t - pk_t)
        ho = min(rest, HORECA_CAP * 1000) if o.horeca and ho_net > hal_net else 0.0
        rest -= ho
        ho2 = min(sec, HORECA2_CAP * 1000) if o.horeca else 0.0
        sec_left = sec - ho2
        fz = 0.0
        if o.frozen and fr_net > hal_net:
            fz = min(rest, FROZEN_CAP * 1000); rest -= fz
        fz_sec = min(sec_left, FROZEN_CAP * 1000 - fz) if o.frozen else 0.0
        proc = sec_left - fz_sec
        rev = (pk_o * partner * (1 - v8.PARTNER_COMM) + pk_t * partner * TUNNEL_PREMIUM * (1 - v8.PARTNER_COMM)
               + rest * hal_net + up * up_price + proc * 55 * pm + ho * ho_net + ho2 * ho2_net
               + fz * fr_net + fz_sec * (fr_net - 25))
        var = ((pk_o + pk_t) * (hp + v8.PACK + v8.PICKUP) + ho * hp + (rest + fz) * hb + up * v8.UPICK_COST
               + sec * (hb + 5) + (kg_o + kg_t) * loss * 0.5 * hb)
        fx = (sum(v8.fixed(y, p).values()) + (o.supervisor if y >= 2 else 0)
              + TUNNEL_FIX * o.tunnel + (FROZEN_FIX if o.frozen and y >= 2 else 0) + (AGRO_FIX if o.agro and y >= 2 else 0))
        ebitda = rev - var - fx
        dep = sum(v / life for _, yy, _, _, _, v, life in it if yy + 1 <= y < yy + 1 + life)
        capy = sum(v for _, yy, _, _, _, v, _ in it if yy == y)
        stop = rev * v8.STOPAJ
        rows.append(dict(net=ebitda - dep - stop, cash=ebitda - stop - capy, kg=kg_o + kg_t, rev=rev))
    c0 = sum(v for _, yy, _, _, _, v, _ in it if yy == 0)
    flows = [-c0] + [r["cash"] for r in rows]
    flows[-1] += sum(v * max(0, (yy + life - v8.YEARS)) / life for _, yy, _, _, _, v, life in it) * 0.5
    return dict(rows=rows, flows=flows, npv=npv(flows), pb=payback(flows), peak=-min(cum(flows)),
                net5=sum(r["net"] for r in rows[:5]), start=sum(v for ph, yy, *_ , v, _ in [(i[0], i[1], i[5], i[6]) for i in it] if ph <= 1))


def worlds(n=5000, seed=7):
    rnd = random.Random(seed)
    W = []
    for _ in range(n):
        d = dict(pm=rnd.lognormvariate(0, 0.20), ym=rnd.triangular(0.65, 1.05, 0.85),
                 kg_pack=rnd.uniform(38, 55), kg_bulk=rnd.uniform(50, 70), loss=rnd.uniform(0.03, 0.15), ev=[])
        lost = lost_c = None
        for y in YRS:
            e = dict(frost=1.0, dis=1.0, heat=1.0, lab=1.0, lab_big=1.0)
            if y >= 2:
                if rnd.random() < 0.10: e["frost"] = 0.6
                if rnd.random() < 0.15: e["dis"] = 0.75
                if rnd.random() < 0.15: e["heat"] = 0.85
                u = rnd.random()
                if u < 0.20: e["lab"] = 0.90
                if u < 0.35: e["lab_big"] = 0.85
                v = rnd.random()
                if lost is None and v < 0.12: lost = y
                if lost_c is None and v < 0.04: lost_c = y
            d["ev"].append(e)
        d["lost"], d["lost_c"] = lost, lost_c
        W.append(d)
    return W


OPTS = [
    Opt("0", "Son hâl (sözleşmesiz)"),
    Opt("1", "+ VeryBerry ile yazılı taban fiyatlı sözleşme", contract=True),
    Opt("2", "1 + otel kanalı + agro-turizm", contract=True, horeca=True, agro=True),
    Opt("3", "2 + kendi dondurma hattı", contract=True, horeca=True, agro=True, frozen=True),
    Opt("4", "2 + 3 da yağmur örtülü tünel", contract=True, horeca=True, agro=True, tunnel=3),
    Opt("5", "2 + 10 da'nın tamamı tünelde", contract=True, horeca=True, agro=True, tunnel=10),
    Opt("6", "20 da + 2", bb=20, contract=True, horeca=True, agro=True),
]


def q(xs, p):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))]


def evaluate(o, W):
    R = [run(o, d) for d in W]
    nv = [r["npv"] for r in R]; y5 = [r["rows"][4]["net"] for r in R]
    pbs = [r["pb"] for r in R]; ok = [p for p in pbs if p is not None]
    return dict(start=R[0]["start"], p_loss=sum(v < 0 for v in nv) / len(nv), npv_med=q(nv, .5), npv_p10=q(nv, .1),
                y5_med=q(y5, .5), y5_p10=q(y5, .1), y5_p90=q(y5, .9), net5_med=q([r["net5"] for r in R], .5),
                pb_med=st.median(ok) if ok else None, p_nopb=sum(p is None for p in pbs) / len(pbs),
                peak_p90=q([r["peak"] for r in R], .9))


def md_table():
    W = worlds()
    out = ["| Seçenek | Başlangıç yatırımı | Para kaybetme ihtimali | 2031 net (kötü %10) | 2031 net (medyan) | 2031 net (iyi %10) | Medyan geri dönüş | Kötü durumda cepten (%90) |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    res = {}
    for o in OPTS:
        e = evaluate(o, W); res[o.key] = e
        out.append(f"| **{o.key}.** {o.name} | {mtl(e['start'])} | %{e['p_loss']*100:.0f} | {mtl(e['y5_p10'])} | "
                   f"{mtl(e['y5_med'])} | {mtl(e['y5_p90'])} | {fmt(e['pb_med'],1) + ' yıl' if e['pb_med'] else '—'} | {mtl(e['peak_p90'])} |")
    return "\n".join(out), res


if __name__ == "__main__":
    t, res = md_table()
    print(t)
    if "--tables" in sys.argv:
        for k, e in res.items(): print(k, {a: (round(b) if isinstance(b, float) and abs(b) > 10 else b) for a, b in e.items()})
