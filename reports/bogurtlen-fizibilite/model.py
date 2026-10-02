"""Dikensiz boğürtlen (10 da) fizibilite modeli.

Raporun (RAPOR.md) tüm tabloları bu dosyadan üretilir:
    python reports/bogurtlen-fizibilite/model.py
Varsayımlar dosyanın başında toplanmıştır; değiştirip yeniden çalıştırın.
"""
from __future__ import annotations

FX = 47.0          # TL/USD (Ekim 2026 çalışma varsayımı — güncel kurla değiştirin)
YEARS = 10         # ekonomik ömür (boğürtlen bahçesi 10-12 yıl)
DISC = 0.12        # USD bazlı iskonto oranı (tarım projesi risk primi dahil)
AREA_DA = 10
PLANTS = 3000

# ---------------------------------------------------------------- CAPEX (USD)
CAPEX = [
    # (grup, kalem, miktar/açıklama, tutar)
    ("A. Arazi hazırlığı", "Toprak analizi (2 derinlik, 4 nokta) + drenaj kontrolü", "1 set", 250),
    ("A. Arazi hazırlığı", "Dip kazan (subsoiler) + diskaro + rototiller", "10 da", 600),
    ("A. Arazi hazırlığı", "Lazerli tesviye (%0,2-0,3 drenaj eğimi bırakılarak)", "10 da", 550),
    ("A. Arazi hazırlığı", "Yanmış çiftlik gübresi / kompost (4 t/da)", "40 t", 2000),
    ("A. Arazi hazırlığı", "Yüksek sedde (30-40 cm) yapımı, sedde makinesi", "~3.300 m", 450),
    ("A. Arazi hazırlığı", "Sedde üstü agrotekstil malç örtü (1 m en)", "3.400 m²", 1100),
    ("B. Fidan", "Doku kültürü M1 mavi sertifikalı fidan (Chester/Loch Ness)", "3.000 ad × $3,00", 9000),
    ("B. Fidan", "Yedek fidan (%5 tutmama) + dikim işçiliği", "150 ad + 15 yevmiye", 1050),
    ("C. Telli terbiye", "Galvaniz direk 2,7 m (6 m ara, 33 sıra)", "~630 ad × $8,5", 5350),
    ("C. Telli terbiye", "Gergi teli 2,5 mm (3 kat) + gergi/ankraj seti", "~10.000 m + 66 ankraj", 1650),
    ("C. Telli terbiye", "T-kol (cross-arm) + montaj işçiliği", "set", 1500),
    ("D. Sulama & fertigasyon", "Ana hat PE + vanalar + DSİ hidrant bağlantısı", "set", 900),
    ("D. Sulama & fertigasyon", "Disk + kum filtre grubu", "1 set", 700),
    ("D. Sulama & fertigasyon", "Damla lateral (16 mm, 33 cm, PC) çift hat", "~6.600 m", 850),
    ("D. Sulama & fertigasyon", "Fertigasyon kontrolörü (4G/Wi-Fi), 4 selenoid vana", "4 zon", 1800),
    ("D. Sulama & fertigasyon", "EC/pH dozaj ünitesi (2 gübre + 1 asit kanalı)", "1 ad", 2400),
    ("E. AgTech sensör", "Toprak istasyonu (30/60 cm nem+EC+sıcaklık), LoRa/4G", "3 ad × $650", 1950),
    ("E. AgTech sensör", "Mikro meteoroloji istasyonu (yaprak ıslaklığı, don alarmı)", "1 ad", 1900),
    ("E. AgTech sensör", "Gateway, kurulum, kalibrasyon, 1. yıl platform", "set", 600),
    ("F. Güvenlik", "Solar 4G PTZ AI kamera (360°)", "2 ad × $650", 1300),
    ("F. Güvenlik", "Solar termal kamera (gece / insan-hayvan ayrımı)", "1 ad", 1600),
    ("G. Gölgeleme", "%35 beyaz gölge filesi, sıra üstü şerit (yalnız güney 2/3 alan)", "~4.500 m²", 2700),
    ("G. Gölgeleme", "Direk uzatma + file teli + montaj", "set", 1100),
    ("H. Diğer", "Proje/danışmanlık, ruhsat, TARSİM ilk poliçe", "", 900),
]
CONTINGENCY = 0.07    # öngörülemeyen giderler
COLD_ROOM = 8500      # ön soğutma + 20 m³ soğuk oda (+2/+4°C) — kritik ek kalem

# ---------------------------------------------------------------- OPEX (USD, yıl 1..4+)
OPEX_FIXED = {
    # kalem: [Y1, Y2, Y3, Y4+]
    "Gübre (fertigasyon + organik)":        [700, 1100, 1500, 1600],
    "Biyolojik/kimyasal mücadele (SWD tuzak, Bt, avcı akar, bakır)": [400, 900, 1300, 1400],
    "Budama + sürgün bağlama işçiliği":      [600, 1300, 1800, 1900],
    "Ot/sıra arası biçim, malç bakımı":      [500, 550, 600, 600],
    "DSİ su ücreti + pompa elektriği":       [250, 400, 500, 500],
    "IoT veri/4G SIM + platform aboneliği":  [500, 950, 950, 950],
    "Bakım-onarım (ekipman %4)":             [0, 700, 900, 1000],
    "TARSİM sigorta":                        [0, 500, 700, 750],
    "Soğuk oda elektriği (varsa)":           [0, 400, 700, 750],
    "Muhasebe, borsa tescil, nakliye (sabit)": [300, 500, 600, 600],
}
ESC_YEARS = 3         # USD bazlı maliyet artışı ilk 3 yıl birikir, sonra yatay kalır
HARVEST_COST = 0.60   # USD/kg elle hasat (kullanıcı bandı 0,50-0,70)

# kanal bazında kg başı değişken maliyet (ambalaj+lojistik+komisyon oranı)
CHANNELS = {
    #            fiyat, ambalaj+lojistik USD/kg, komisyon/kayıp oranı
    "toptan":     (2.50, 0.20, 0.10),   # hal komisyonu %8 + rüsum/stopaj ~%2
    "perakende":  (4.00, 0.75, 0.15),   # 250 g klapa, etiket, soğuk zincir, iade/fire
    "işleme":     (1.30, 0.05, 0.03),   # dondurma/püre/reçel tesisi, kasa ile
}


def fmt(x, d=0):
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x):
    return "hesaplanamaz (negatif)" if x is None else f"%{x*100:.1f}".replace(".", ",")


def capex_total(cold_room=True):
    base = sum(c[3] for c in CAPEX)
    cont = round(base * CONTINGENCY, -1)
    return base, cont, base + cont + (COLD_ROOM if cold_room else 0)


def opex_fixed(year, esc=0.0):
    idx = min(year, 4) - 1
    v = sum(vals[idx] for vals in OPEX_FIXED.values())
    return v * (1 + esc) ** (year - 1)


def cashflows(yields_t, mix, harvest=HARVEST_COST, price_mult=1.0, esc=0.0,
              cold_room=True, capex_mult=1.0):
    """yields_t: yıl 1..10 rekolte (ton); mix: {kanal: pay}"""
    _, _, capex = capex_total(cold_room)
    capex *= capex_mult
    rows = []
    cum = -capex
    for y in range(1, YEARS + 1):
        kg = yields_t[y - 1] * 1000
        rev = var = 0.0
        for ch, share in mix.items():
            p, pack, comm = CHANNELS[ch]
            p *= price_mult
            q = kg * share
            rev += q * p
            var += q * pack + q * p * comm
        e = (1 + esc) ** min(y - 1, ESC_YEARS)
        hv = kg * harvest * e
        fx = opex_fixed(y) * e
        net = rev - var - hv - fx
        cum += net
        rows.append(dict(y=y, kg=kg, rev=rev, var=var, harv=hv, fix=fx, net=net, cum=cum))
    return capex, rows


def payback(capex, rows):
    cum = -capex
    for r in rows:
        if cum + r["net"] >= 0:
            return r["y"] - 1 + (-cum) / r["net"]
        cum += r["net"]
    return None


def npv(capex, rows, r=DISC):
    return -capex + sum(x["net"] / (1 + r) ** x["y"] for x in rows)


def irr(capex, rows):
    if npv(capex, rows, -0.9) <= 0:
        return None
    lo, hi = -0.99, 3.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(capex, rows, mid) > 0:
            lo = mid
        else:
            hi = mid
    return mid


def extend(y4, first):
    """yıl 1..4 verilir, 5-8 sabit, 9-10 %10 düşüş (yaşlanma)."""
    v = list(first) + [y4] * 4 + [y4 * 0.9, y4 * 0.8]
    return v[:YEARS]


USER_Y = extend(28, [0, 10, 25, 28])
REAL_Y = extend(20, [0, 5, 14, 20])
STRESS_Y = [v * 0.75 for v in REAL_Y]      # yaz sıcağı/güneş yanığı, SWD, kalite kaybı

SCEN = {
    "S1 Talep — toptan $2,50":            dict(yields=USER_Y, mix={"toptan": 1.0}),
    "S2 Talep — perakende $4,00":         dict(yields=USER_Y, mix={"perakende": 1.0}),
    "S3 Uzman gerçekçi (karma kanal)":    dict(yields=REAL_Y, mix={"toptan": .55, "perakende": .25, "işleme": .20}),
    "S4 Pesimistik stres":                dict(yields=STRESS_Y, mix={"toptan": .55, "perakende": .25, "işleme": .20},
                                               price_mult=0.70, harvest=0.84, esc=0.08, capex_mult=1.15),
}


def table(rows, capex):
    out = ["| Yıl | Rekolte (t) | Brüt gelir | Ambalaj+komisyon | Hasat işçiliği | Sabit OPEX | Net nakit | Kümülatif |",
           "|---|---:|---:|---:|---:|---:|---:|---:|",
           f"| 0 | – | – | – | – | – | −{fmt(capex)} | −{fmt(capex)} |"]
    for r in rows:
        out.append(f"| {r['y']} | {fmt(r['kg']/1000,1)} | {fmt(r['rev'])} | {fmt(r['var'])} | {fmt(r['harv'])} | "
                   f"{fmt(r['fix'])} | {fmt(r['net'])} | {fmt(r['cum'])} |")
    return "\n".join(out).replace("| -", "| −")


def breakeven_price(yield_t, mix, harvest, esc_year_fix, comm_pack_mult=1.0, capex=None):
    """Tam verim yılında (a) nakit başabaş, (b) 10 yıl NPV=0 ağırlıklı fiyat."""
    kg = yield_t * 1000
    # ağırlıklı ambalaj ve komisyon
    pack = sum(CHANNELS[c][1] * s for c, s in mix.items())
    comm = sum(CHANNELS[c][2] * s for c, s in mix.items())
    fixed = esc_year_fix
    p = (fixed / kg + harvest + pack) / (1 - comm)
    return p


def main():
    base, cont, tot = capex_total()
    print("CAPEX alt toplam", base, "beklenmeyen", cont, "soğuk oda", COLD_ROOM, "toplam", tot,
          "soğuk odasız", base + cont)
    groups = {}
    for g, *_ , v in CAPEX:
        groups[g] = groups.get(g, 0) + v
    for g, v in groups.items():
        print(f"  {g}: {v}  ({v/tot*100:.1f}%)")
    for y in range(1, 5):
        print("OPEX sabit Y", y, opex_fixed(y))
    for name, s in SCEN.items():
        kw = {k: v for k, v in s.items() if k not in ("yields", "mix")}
        capex, rows = cashflows(s["yields"], s["mix"], **kw)
        print(f"\n## {name}  CAPEX={capex:.0f}  payback={payback(capex, rows)}  "
              f"NPV12={npv(capex, rows):.0f}  IRR={pct(irr(capex, rows))}")
        print(table(rows, capex))
    # başabaş
    print("\nBaşabaş fiyatları (tam verim yılı, nakit):")
    for lbl, yt, mix, hv, esc in [
        ("S3 gerçekçi 20 t", 20, SCEN["S3 Uzman gerçekçi (karma kanal)"]["mix"], 0.60, 0),
        ("S4 stres 15 t", 15, SCEN["S3 Uzman gerçekçi (karma kanal)"]["mix"], 0.84, 0.08),
        ("Talep 28 t toptan", 28, {"toptan": 1}, 0.60, 0),
    ]:
        fixed = opex_fixed(4) * (1 + esc) ** ESC_YEARS
        print(lbl, round(breakeven_price(yt, mix, hv * (1 + esc) ** ESC_YEARS, fixed), 2))
    # NPV=0 için gereken fiyat çarpanı (S4 koşullarında)
    s = SCEN["S4 Pesimistik stres"]
    lo, hi = 0.1, 3
    for _ in range(100):
        m = (lo + hi) / 2
        c, r = cashflows(s["yields"], s["mix"], harvest=0.84, price_mult=m, esc=0.08, capex_mult=1.15)
        if npv(c, r, 0.0) > 0: hi = m
        else: lo = m
    print("S4: 10 yılda sermayeyi geri ödeyen (NPV@0) fiyat çarpanı", round(m, 3))
    lo, hi = 0.1, 3
    for _ in range(100):
        m = (lo + hi) / 2
        c, r = cashflows(s["yields"], s["mix"], harvest=0.84, price_mult=m, esc=0.08, capex_mult=1.15)
        if npv(c, r) > 0: hi = m
        else: lo = m
    print("S4: NPV@12 = 0 fiyat çarpanı", round(m, 3))
    # S3'te verim başabaşı
    s3 = SCEN["S3 Uzman gerçekçi (karma kanal)"]
    lo, hi = 0.05, 2
    for _ in range(100):
        m = (lo + hi) / 2
        c, r = cashflows([v * m for v in s3["yields"]], s3["mix"])
        if npv(c, r) > 0: hi = m
        else: lo = m
    print("S3: NPV@12=0 verim çarpanı", round(m, 3), "-> tam verim t", round(20 * m, 1))
    # stres alt senaryoları (tek faktör)
    print("\nTek faktör duyarlılık (S3 bazında):")
    tests = {
        "Baz S3": {},
        "Fiyat −%30 (tüccar baskısı)": dict(price_mult=0.7),
        "Verim −%25 (sıcak stresi)": dict(ymult=0.75),
        "Hasat $0,84/kg (işçi krizi +%40)": dict(harvest=0.84),
        "USD bazlı maliyet artışı %8/yıl (reel TL değerlenmesi)": dict(esc=0.08),
        "CAPEX +%15": dict(capex_mult=1.15),
        "Hepsi birlikte (S4)": dict(price_mult=0.7, ymult=0.75, harvest=0.84, esc=0.08, capex_mult=1.15),
    }
    for k, t in tests.items():
        t = dict(t)
        ym = t.pop("ymult", 1)
        c, r = cashflows([v * ym for v in s3["yields"]], s3["mix"], **t)
        pb = payback(c, r)
        print(f"| {k} | {fmt(r[4]['net'])} | {('%.1f' % pb) if pb else 'yok'} | {fmt(npv(c, r))} | {pct(irr(c, r))} |")
    return


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------- Yalın CAPEX
LEAN_CUTS = [
    ("Fidan pazarlığı: 3.000 ad toplu alımda $3,00 → $2,50", 1500),
    ("Galvaniz direk aralığı 6 m → 8 m (ara direk + gergi ile)", 1350),
    ("Termal kamerayı 2. yıla ertele (PTZ AI yeterli)", 1600),
    ("Gölge filesini 1. yıl almayıp 2. yıl kur (fidan yılı yaz ışığına dayanır)", 3800),
    ("EC/pH dozajı: 3 kanal yerine venturi + tek asit pompası", 1100),
]

# ---------------------------------------------------------------- Waterfall
def waterfall(capex, rows, owner_rev_share=0.05, hurdle=0.12,
              t1=(0.85, 0.15), t2=(0.70, 0.30), t3=(0.50, 0.50)):
    """Yatırımcı: CAPEX + negatif yılların açığı. Arazi sahibi: arazi, su, emek.

    Tier 0: brüt gelirin %5'i arazi sahibine saha ücreti (operasyon gideri gibi).
    Tier 1: kalan nakit t1 oranında, yatırımcı sermayesi geri dönene kadar.
    Tier 2: t2 oranında, yatırımcı USD IRR'si hurdle'a ulaşana kadar.
    Tier 3: t3 oranında (kalıcı ortaklık payı).
    """
    inv_flows, own_flows = [-capex], [0.0]
    cap_bal = capex          # iade edilmemiş sermaye
    hur_bal = capex          # hurdle ile büyüyen alacak
    for r in rows:
        hur_bal *= 1 + hurdle
        fee = r["rev"] * owner_rev_share
        cash = r["net"] - fee
        inv = own = 0.0
        if cash < 0:
            inv = cash
            cap_bal += -cash
            hur_bal += -cash
        else:
            rem = cash
            for share, cap in ((t1, "cap"), (t2, "hur"), (t3, None)):
                if rem <= 0:
                    break
                if cap == "cap":
                    need = cap_bal
                elif cap == "hur":
                    need = hur_bal
                else:
                    need = float("inf")
                if need <= 0:
                    continue
                d = min(rem, need / share[0])
                inv += d * share[0]; own += d * share[1]; rem -= d
                cap_bal = max(cap_bal - d * share[0], 0)
                hur_bal = max(hur_bal - d * share[0], 0)
        inv_flows.append(inv)
        own_flows.append(own + fee)
    return inv_flows, own_flows


def flows_irr(fl):
    def f(r):
        return sum(v / (1 + r) ** i for i, v in enumerate(fl))
    if f(-0.9) <= 0:
        return None
    lo, hi = -0.9, 3.0
    for _ in range(200):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if f(m) > 0 else (lo, m)
    return m


# ---------------------------------------------------------------- Ziraat kredisi
def loan(capex_usd, share=0.50, rate_tl=0.185, grace=2, term=5, tl_dep=0.18):
    """TL kredi: geri ödemesiz dönemde faiz ödenir, sonra eşit anapara."""
    p0 = capex_usd * share * FX
    bal = p0
    rows = []
    for y in range(1, term + 1):
        fx = FX * (1 + tl_dep) ** y
        intr = bal * rate_tl
        princ = 0 if y <= grace else p0 / (term - grace)
        bal -= princ
        rows.append(dict(y=y, fx=fx, intr=intr, princ=princ, pay_tl=intr + princ,
                         pay_usd=(intr + princ) / fx, bal=bal))
    return p0, rows


def report_extras():
    print("\n### Yalın CAPEX")
    base, cont, tot = capex_total(cold_room=False)
    cut = sum(v for _, v in LEAN_CUTS)
    lean = base - cut
    print("tam (soğuk odasız)", base + cont, "kesinti", cut, "yalın+%7", lean * 1.07,
          "yalın + soğuk oda", lean * 1.07 + COLD_ROOM)
    for k, v in LEAN_CUTS:
        print(" -", k, v)

    print("\n### Waterfall")
    for name in ["S1 Talep — toptan $2,50", "S3 Uzman gerçekçi (karma kanal)", "S2 Talep — perakende $4,00"]:
        s = SCEN[name]
        c, r = cashflows(s["yields"], s["mix"])
        inv, own = waterfall(c, r)
        print(name, "yatırımcı IRR", pct(flows_irr(inv)), "yatırımcı toplam net", round(sum(inv)),
              "sahip toplam", round(sum(own)))
        print("  inv", [round(x) for x in inv])
        print("  own", [round(x) for x in own])

    print("\n### Kredi")
    _, _, tot = capex_total()
    p0, lr = loan(tot)
    print("kredi TL", round(p0), "USD", tot * 0.5)
    for x in lr:
        print(x["y"], round(x["fx"], 1), round(x["intr"]), round(x["princ"]), round(x["pay_tl"]),
              round(x["pay_usd"]), round(x["bal"]))
    tot_usd = sum(x["pay_usd"] for x in lr)
    print("toplam geri ödeme USD", round(tot_usd), "efektif USD maliyet",
          round((tot_usd / (tot * 0.5) - 1) * 100, 1), "%")
    # kaldıraçlı özsermaye IRR (S3)
    s = SCEN["S3 Uzman gerçekçi (karma kanal)"]
    c, r = cashflows(s["yields"], s["mix"])
    eq = [-c * 0.5] + [r[i]["net"] - (lr[i]["pay_usd"] if i < len(lr) else 0) for i in range(YEARS)]
    print("S3 özsermaye IRR (kredili)", pct(flows_irr(eq)), "kredisiz", pct(irr(c, r)))
    cum = 0
    out = []
    for v in eq:
        cum += v; out.append(round(cum))
    print("  kümülatif özsermaye", out)


if __name__ == "__main__":
    report_extras()
