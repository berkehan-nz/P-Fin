"""Dikensiz böğürtlen v2 — soğuk zincir + paketleme + AgTech 'living lab'.

RAPOR_V2.md'deki tüm tablolar bu dosyadan üretilir:
    python reports/bogurtlen-fizibilite/model_v2.py            # özet
    python reports/bogurtlen-fizibilite/model_v2.py --tables   # markdown tablolar

Sunum: 2026 sabit fiyatlarıyla USD (reel). TL karşılıkları FX ile.
"""
from __future__ import annotations
import sys

FX = 47.0                 # TL/USD çalışma kuru (Ekim 2026)
TL_DEP = 0.18             # kredi hesabı için yıllık TL değer kaybı varsayımı
YEARS = 5
YEAR_LABEL = {0: "Y0 (Q4-2026)", 1: "Y1 2027", 2: "Y2 2028", 3: "Y3 2029", 4: "Y4 2030", 5: "Y5 2031"}
CORP_TAX = 0.25           # kurumlar vergisi (Ltd. Şti.)
CONTINGENCY = 0.08

# ------------------------------------------------------------------ CAPEX
# (faz, grup, kalem, USD, amortisman ömrü (yıl), amortisman başlangıç yılı)
CAPEX = [
    # ---- Faz 1: Q4-2026 / Q1-2027 — tarla + çekirdek AgTech
    (1, "Tarla", "Toprak analizi + dip kazan + lazer tesviye + 40 t organik gübre + sedde", 3850, 10, 2),
    (1, "Tarla", "Sedde üstü agrotekstil malç (3.400 m²)", 1100, 5, 1),
    (1, "Tarla", "Doku kültürü M1 sertifikalı fidan 3.000 ad + %5 yedek + dikim", 10050, 10, 2),
    (1, "Tarla", "Telli terbiye: ~630 galvaniz direk, 3 kat tel, T-kol, ankraj, montaj", 8500, 10, 1),
    (1, "Tarla", "Sulama hidroliği: DSİ hidrant bağlantısı, ana hat, disk+kum filtre, 6.600 m çift lateral", 2450, 10, 1),
    (1, "AgTech", "Fertigasyon beyni: kendi PLC/ESP32 kontrolörün + 4 selenoid + röle panosu", 900, 5, 1),
    (1, "AgTech", "Dozaj pompaları (2 gübre + 1 asit) + hat içi EC/pH probları", 2200, 5, 1),
    (1, "AgTech", "LoRaWAN gateway (4G backhaul) + yedek router + güneş/akü", 700, 5, 1),
    (1, "AgTech", "8 adet DIY toprak düğümü (30/60 cm nem-EC-sıcaklık, solar)", 2240, 5, 1),
    (1, "AgTech", "1 adet profesyonel referans prob (DIY sensör kalibrasyonu)", 900, 5, 1),
    (1, "AgTech", "Profesyonel mikro meteoroloji istasyonu (yaprak ıslaklığı, PAR, don)", 1600, 5, 1),
    (1, "AgTech", "Zon başı debimetre + basınç sensörü (4 zon)", 800, 5, 1),
    (1, "AgTech", "Edge sunucu (GPU'lu mini PC / Jetson) + UPS + dış ortam kabini", 1400, 4, 1),
    (1, "AgTech", "Prototipleme / geliştirme bütçesi", 1000, 3, 1),
    (1, "Güvenlik", "2 adet solar 4G PTZ AI kamera + 1 adet solar termal kamera", 2900, 5, 1),
    (1, "Diğer", "Şirket kuruluşu, proje, izinler (5403 tarımsal yapı izni dahil)", 1200, 5, 1),
    # ---- Faz 2: Q1-2028 (ilk hasattan önce) — soğuk zincir + pakethane
    (2, "Soğuk zincir & pakethane", "Beton zemin + 60 m² gölgelik (konteyner sahası)", 4000, 15, 2),
    (2, "Soğuk zincir & pakethane", "Elektrik bağlantısı (trifaze) + pano", 3500, 15, 2),
    (2, "Soğuk zincir & pakethane", "10 kWp çatı GES (lisanssız, mahsuplaşmalı)", 7500, 10, 2),
    (2, "Soğuk zincir & pakethane", "40' reefer konteyner, yenilenmiş (67 m³, 0/+2 °C)", 8500, 10, 2),
    (2, "Soğuk zincir & pakethane", "Ön soğutma tüneli (cebri hava, fan + branda + kontrol)", 1500, 5, 2),
    (2, "Soğuk zincir & pakethane", "Paketleme odası: 30 m² izoleli prefabrik, hijyenik panel, lavabo, paslanmaz masa", 9000, 15, 2),
    (2, "Soğuk zincir & pakethane", "Yarı otomatik top-seal kapatma makinesi (100/200/500 g kalıp)", 5500, 8, 2),
    (2, "Soğuk zincir & pakethane", "3 hassas terazi + 2 QR etiket yazıcı + barkod okuyucu", 1800, 5, 2),
    (2, "Soğuk zincir & pakethane", "Hasat ekipmanı: kasa, hasat arabası, NFC'li toplayıcı tartı istasyonu", 1600, 5, 2),
    (2, "Soğuk zincir & pakethane", "Transpalet + raf sistemi", 600, 8, 2),
    (2, "Soğuk zincir & pakethane", "Gıda işletme kaydı, İyi Tarım belgesi, hijyen kurulumu", 1500, 5, 2),
    (2, "AgTech", "Soğuk zincir sensörleri (oda + 10 taşınabilir sevkiyat logger'ı)", 500, 4, 2),
    (2, "AgTech", "3 adet akıllı SWD tuzak kamerası (AI ile sinek sayımı)", 450, 4, 2),
    (2, "AgTech", "4 adet sıra kamerası (meyve sayımı → rekolte tahmini)", 600, 4, 2),
    (2, "Tarla", "%35 gölge filesi + direk uzatma + montaj", 3800, 7, 2),
]
FAZ3_OPTIONS = [
    ("İkinci 40' reefer (hizmet kapasitesi)", 8500, "Y3, soğuk depo hizmet talebi > %70 doluluk olursa"),
    ("Şok dondurucu (-35 °C, 300 kg/parti) → IQF dondurulmuş böğürtlen", 14000, "Y3-Y4, 2. sınıf ürünü $1,30 → $3,00/kg'a çıkarır"),
    ("Multispektral drone + işleme yazılımı", 5000, "Y3, living lab projesi fonlarsa"),
    ("Frigorifik panelvan (2. el)", 20000, "Y4, doğrudan HoReCa dağıtımı > 5 t/yıl olursa"),
    ("Ek 10-20 da bahçe (kurumsal ortak finansmanlı)", 50000, "Y4+, Farm-as-a-Service modeli"),
]


AREA_SCALED = ("Tarla",)            # alan büyüdükçe doğrusal artan CAPEX grupları
AREA_SCALED_ITEMS = ("toprak düğümü",)


def capex_items(area=1.0):
    out = []
    for f, g, k, v, life, start in CAPEX:
        if g in AREA_SCALED or any(t in k for t in AREA_SCALED_ITEMS):
            v = v * area
        out.append((f, g, k, v, life, start))
    return out


def capex_phase(f, area=1.0):
    base = sum(c[3] for c in capex_items(area) if c[0] == f)
    return base, round(base * CONTINGENCY, -1)


def depreciation(year, area=1.0):
    d = 0.0
    for f, _, _, v, life, start in capex_items(area):
        if start <= year < start + life:
            d += v / life
    for f in (1, 2):
        _, cont = capex_phase(f, area)
        start = 1 if f == 1 else 2
        if year >= start:
            d += cont / 10
    return d


# ------------------------------------------------------------------ Satış
# paket boyutu: (pay, üretici çıkış fiyatı USD/paket, ambalaj USD/paket)
PACKS = {"100 g": (0.15, 0.70, 0.09), "200 g": (0.55, 1.15, 0.11), "500 g": (0.30, 2.40, 0.18)}
OUTER_CARTON = 0.05     # USD/kg dış koli
PACKHOUSE_LABOR = 0.12  # USD/kg paketlenen
DIST_COMM = 0.12        # distribütör / alıcı kanal payı (paketli)
COLD_TRANSPORT = 0.30   # USD/kg soğuk sevkiyat (paketli)
CORP_PRICE, CORP_EXTRA = 9.00, 1.20   # kurumsal markalı paket USD/kg, ek marka/etkinlik maliyeti
HAL_PRICE, HAL_COMM, HAL_PACK = 2.50, 0.10, 0.20
PROC_PRICE, PROC_COMM, PROC_PACK = 1.30, 0.03, 0.05
HARVEST = {"pack": 0.70, "bulk": 0.55}   # USD/kg — punnet'e tarlada toplama daha yavaş


def pack_price_per_kg():
    return sum(s * p / (int(k.split()[0]) / 1000) for k, (s, p, _) in PACKS.items())


def pack_cost_per_kg():
    return sum(s * c / (int(k.split()[0]) / 1000) for k, (s, _, c) in PACKS.items()) + OUTER_CARTON


SCENARIOS = {
    "Baz": dict(
        yields=[0, 5, 14, 20, 20], second=0.20,
        pack_share=[0, .50, .65, .75, .80], corp_t=[0, 0, .5, 1.5, 2.5],
        service=[0, 0, 1500, 3000, 4000], lab=[0, 0, 0, 2000, 4000], consult=[0, 0, 0, 0, 3000],
        price_mult=1.0, harvest_mult=1.0, grant=0.0),
    "Pesimistik": dict(
        yields=[0, 3.75, 10.5, 15, 15], second=0.25,
        pack_share=[0, .40, .50, .55, .60], corp_t=[0, 0, 0, .5, 1.0],
        service=[0, 0, 0, 1000, 1500], lab=[0, 0, 0, 0, 0], consult=[0, 0, 0, 0, 0],
        price_mult=0.80, harvest_mult=1.30, grant=0.0),
    "İyimser": dict(
        yields=[0, 6, 17, 24, 25], second=0.15,
        pack_share=[0, .55, .70, .80, .85], corp_t=[0, .3, 1.5, 3, 4],
        service=[0, 0, 2500, 4500, 6000], lab=[0, 0, 2000, 6000, 10000], consult=[0, 0, 0, 4000, 8000],
        price_mult=1.05, harvest_mult=1.0, grant=0.50),
}

# ------------------------------------------------------------------ Sabit OPEX (Y1..Y5)
FIXED = {
    "Gübre + biyolojik/kimyasal mücadele":            [1100, 2000, 2800, 3000, 3000],
    "Budama, bağlama, ot biçimi (yevmiyeli)":           [1100, 1850, 2400, 2500, 2500],
    "DSİ su ücreti + pompa":                            [250, 400, 500, 500, 500],
    "Daimi tarım teknisyeni (asgari ücret, işveren maliyeti)": [4500, 9000, 9000, 9000, 9000],
    "Sezonluk pakethane sorumlusu":                     [0, 1500, 2500, 2500, 2500],
    "Elektrik (GES mahsubu sonrası)":                   [150, 500, 700, 700, 700],
    "Bakım-onarım":                                     [300, 1200, 1800, 2000, 2000],
    "Sigorta (TARSİM + tesis)":                         [0, 900, 1100, 1150, 1150],
    "Bulut, SIM, yazılım, veri saklama":                [500, 600, 600, 700, 700],
    "İyi Tarım denetimi, gıda güvenliği analizleri":    [0, 700, 700, 700, 700],
    "Marka, ambalaj tasarımı, web, numune, fuar":       [1000, 2000, 2500, 2500, 2500],
    "Muhasebe, hukuk, şirket giderleri":                [1200, 1500, 1500, 1500, 1500],
}
SERVICE_COST, LAB_COST, CONSULT_COST = 0.35, 0.25, 0.10


FIXED_AREA = ("Gübre", "Budama", "DSİ")


def fixed_opex(y, area=1.0, no_tech=False):
    t = 0.0
    for k, v in FIXED.items():
        x = v[y - 1]
        if no_tech and k.startswith("Daimi"):
            x = 0
        if any(k.startswith(a) for a in FIXED_AREA):
            x *= area
        elif k.startswith("Sigorta"):
            x *= 1 + 0.5 * (area - 1)
        t += x
    return t


# ------------------------------------------------------------------ Kredi
LOAN_SHARE, LOAN_RATE, GRACE, TERM = 0.50, 0.185, 2, 5


def loan_schedule(principal_usd, draw_year):
    """TL kredi; yıl bazında (faiz USD, anapara USD) döner."""
    p_tl = principal_usd * FX * (1 + TL_DEP) ** draw_year
    bal = p_tl
    out = {}
    for k in range(1, TERM + 1):
        y = draw_year + k
        fx = FX * (1 + TL_DEP) ** y
        intr = bal * LOAN_RATE
        princ = 0 if k <= GRACE else p_tl / (TERM - GRACE)
        bal -= princ
        out[y] = (intr / fx, princ / fx)
    return out


def run(name, horizon=YEARS):
    s = SCENARIOS[name]
    area = s.get("area", 1.0)
    pk_price = pack_price_per_kg() * s["price_mult"]
    pk_cost = pack_cost_per_kg()
    c1 = sum(capex_phase(1, area))
    c2 = sum(capex_phase(2, area))
    post = sum(c[3] for c in CAPEX if c[0] == 2 and c[1] == "Soğuk zincir & pakethane")
    grant = post * s["grant"]
    loans = {}
    for amt, dy in ((c1 * LOAN_SHARE, 0), (c2 * LOAN_SHARE, 1)):
        for y, (i, p) in loan_schedule(amt, dy).items():
            a = loans.setdefault(y, [0.0, 0.0]); a[0] += i; a[1] += p
    rows = []
    loss_cf = 0.0
    cash = 0.0
    for y in range(1, horizon + 1):
        k = min(y, 5) - 1
        yt = s["yields"][k] if y <= 5 else s["yields"][4] * (0.9 if y == 9 else 0.8 if y == 10 else 1)
        kg = yt * 1000 * area
        second = kg * s["second"]
        fresh = kg - second
        corp = min(s["corp_t"][k] * 1000, fresh)
        rest = fresh - corp
        packed = rest * s["pack_share"][k]
        hal = rest - packed
        r_pack = packed * pk_price
        r_corp = corp * CORP_PRICE * s["price_mult"]
        r_hal = hal * HAL_PRICE * s["price_mult"]
        r_proc = second * PROC_PRICE * s["price_mult"]
        r_serv, r_lab, r_cons = s["service"][k], s["lab"][k], s["consult"][k]
        rev = r_pack + r_corp + r_hal + r_proc + r_serv + r_lab + r_cons
        harvest = ((packed + corp) * HARVEST["pack"] + (hal + second) * HARVEST["bulk"]) * s["harvest_mult"]
        packaging = (packed + corp) * (pk_cost + PACKHOUSE_LABOR)
        dist = r_pack * DIST_COMM + packed * COLD_TRANSPORT + corp * CORP_EXTRA \
            + r_hal * HAL_COMM + hal * HAL_PACK + r_proc * PROC_COMM + second * PROC_PACK
        svc_cost = r_serv * SERVICE_COST + r_lab * LAB_COST + r_cons * CONSULT_COST
        cogs = harvest + packaging + dist + svc_cost
        fixed = fixed_opex(min(y, 5), area, s.get("no_tech", False))
        ebitda = rev - cogs - fixed
        dep = depreciation(y, area)
        intr, princ = loans.get(y, (0.0, 0.0))
        ebt = ebitda - dep - intr
        taxable = ebt
        if taxable < 0:
            loss_cf += -taxable; tax = 0.0
        else:
            use = min(loss_cf, taxable); loss_cf -= use
            tax = (taxable - use) * CORP_TAX
        net = ebt - tax
        capex = c2 if y == 1 else 0.0
        grant_in = grant if y == 2 else 0.0
        fcf_unlev = ebitda - tax - capex + grant_in
        rows.append(dict(y=y, kg=kg, packed=packed, corp=corp, hal=hal, second=second,
                         r_pack=r_pack, r_corp=r_corp, r_hal=r_hal, r_proc=r_proc,
                         r_serv=r_serv, r_lab=r_lab, r_cons=r_cons, rev=rev,
                         harvest=harvest, packaging=packaging, dist=dist, svc_cost=svc_cost,
                         cogs=cogs, gross=rev - cogs, fixed=fixed, ebitda=ebitda, dep=dep,
                         intr=intr, ebt=ebt, tax=tax, net=net, princ=princ, capex=capex,
                         grant=grant_in, fcf=fcf_unlev))
    return dict(c1=c1, c2=c2, grant=grant, rows=rows, loans=loans, pk_price=pk_price)


VARIANTS = {
    "Baz (tam paket, 10 da)": {},
    "+ KKYDP %50 hibe (pakethane)": dict(grant=0.50),
    "+ Saha emeği ortaktan (teknisyen yok)": dict(no_tech=True),
    "+ Hibe + ortak emeği": dict(grant=0.50, no_tech=True),
    "20 da (aynı pakethane, hibesiz)": dict(area=2.0),
    "20 da + hibe": dict(area=2.0, grant=0.50),
}


def variant_rows():
    out = []
    for lab, kw in VARIANTS.items():
        SCENARIOS["_v"] = dict(SCENARIOS["Baz"], **kw)
        m = project_metrics("_v"); r = run("_v")
        cum = 0; mn = 0
        _, mn = md_cash("_v")
        out.append((lab, r["c1"] + r["c2"], r["rows"][4]["ebt"], m["irr"], m["eq_irr"], m["payback"], mn))
        del SCENARIOS["_v"]
    return out


def md_variants():
    o = ["| Varyant | CAPEX | Y5 vergi öncesi kâr | Proje IRR | Özsermaye IRR | Geri dönüş | Azami özsermaye ihtiyacı |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for lab, c, e, i, ei, pb, mn in variant_rows():
        o.append(f"| {lab} | {usd(c)} | {usd(e)} | {pct(i)} | {pct(ei)} | "
                 f"{'–' if pb is None else fmt(pb, 1) + ' yıl'} | ${fmt(-mn)} |")
    return "\n".join(o)


def irr(flows):
    def f(r): return sum(v / (1 + r) ** i for i, v in enumerate(flows))
    if f(-0.9) <= 0:
        return None
    lo, hi = -0.9, 5.0
    for _ in range(200):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if f(m) > 0 else (lo, m)
    return m


def project_metrics(name):
    """10 yıllık: Y6'da elektronik yenileme ($8k), Y10 sonunda kalıntı değer yok."""
    res = run(name, horizon=10)
    flows = [-res["c1"]]
    for r in res["rows"]:
        f = r["fcf"] - (8000 if r["y"] == 6 else 0)
        flows.append(f)
    eq = [-res["c1"] * (1 - LOAN_SHARE)]
    for r in res["rows"]:
        loan_in = res["c2"] * LOAN_SHARE if r["y"] == 1 else 0
        f = r["fcf"] - (8000 if r["y"] == 6 else 0) - r["intr"] - r["princ"] + loan_in
        eq.append(f)
    cum, pb = 0, None
    for i, v in enumerate(flows):
        prev = cum; cum += v
        if pb is None and i > 0 and cum >= 0:
            pb = i - 1 + (-prev) / v
    return dict(irr=irr(flows), eq_irr=irr(eq), payback=pb, flows=flows, eq=eq)


# ------------------------------------------------------------------ çıktı
def fmt(x, d=0):
    if x is None:
        return "–"
    neg = x < 0
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if neg else "") + s


def pct0(x):
    return ("−" if x < 0 else "") + f"%{abs(x)*100:.0f}"


def pct(x):
    if x is None:
        return "negatif"
    return ("−" if x < 0 else "") + "%" + f"{abs(x)*100:.1f}".replace(".", ",")


def md_capex():
    out = ["| Faz | Grup | Kalem | USD | TL | Ömür |", "|---|---|---|---:|---:|---:|"]
    for f, g, k, v, life, _ in CAPEX:
        out.append(f"| {f} | {g} | {k} | {fmt(v)} | {fmt(v*FX)} | {life} yıl |")
    return "\n".join(out)


def md_capex_summary(name="Baz"):
    rows = []
    groups = {}
    for f, g, _, v, *_ in CAPEX:
        groups[(f, g)] = groups.get((f, g), 0) + v
    out = ["| Faz | Grup | USD | TL |", "|---|---|---:|---:|"]
    tot = 0
    for f in (1, 2):
        for (ff, g), v in groups.items():
            if ff == f:
                out.append(f"| {f} | {g} | {fmt(v)} | {fmt(v*FX)} |")
        b, c = capex_phase(f)
        out.append(f"| {f} | Beklenmeyen giderler (%8) | {fmt(c)} | {fmt(c*FX)} |")
        out.append(f"| **{f}** | **Faz {f} toplamı** | **{fmt(b+c)}** | **{fmt((b+c)*FX)}** |")
        tot += b + c
    out.append(f"| | **GENEL TOPLAM (Faz 1 + 2)** | **{fmt(tot)}** | **{fmt(tot*FX)}** |")
    return "\n".join(out), tot


def md_pnl(name):
    res = run(name)
    R = res["rows"]
    hdr = "| Kalem (USD) | " + " | ".join(YEAR_LABEL[r["y"]] for r in R) + " |"
    sep = "|---|" + "---:|" * len(R)
    lines = [hdr, sep]

    def line(label, key, bold=False, neg=False):
        vals = []
        for r in R:
            v = r[key] if isinstance(key, str) else key(r)
            v = -v if neg else v
            vals.append(f"**{fmt(v)}**" if bold else fmt(v, 1 if label.startswith("Rekolte") else 0))
        lab = f"**{label}**" if bold else label
        lines.append(f"| {lab} | " + " | ".join(vals) + " |")
    line("Rekolte (ton)", lambda r: r["kg"] / 1000)
    line("— Paketli satış (100/200/500 g)", "r_pack")
    line("— Kurumsal markalı paket", "r_corp")
    line("— Hal / dökme taze", "r_hal")
    line("— 2. sınıf → işleme", "r_proc")
    line("— Soğuk depo / paketleme hizmeti", "r_serv")
    line("— Living lab / test-bed projeleri", "r_lab")
    line("— Danışmanlık", "r_cons")
    line("TOPLAM GELİR", "rev", bold=True)
    line("Hasat işçiliği", "harvest", neg=True)
    line("Ambalaj + pakethane işçiliği", "packaging", neg=True)
    line("Dağıtım, komisyon, soğuk sevkiyat", "dist", neg=True)
    line("Hizmet gelirlerinin maliyeti", "svc_cost", neg=True)
    line("BRÜT KÂR", "gross", bold=True)
    line("Sabit işletme giderleri", "fixed", neg=True)
    line("FAVÖK (EBITDA)", "ebitda", bold=True)
    line("Amortisman", "dep", neg=True)
    line("Finansman gideri (Ziraat kredisi faizi)", "intr", neg=True)
    line("VERGİ ÖNCESİ KÂR", "ebt", bold=True)
    line("Kurumlar vergisi (%25, zarar mahsuplu)", "tax", neg=True)
    line("NET KÂR (VERGİ SONRASI)", "net", bold=True)
    lines.append("| FAVÖK marjı | " + " | ".join(
        ("–" if r["rev"] == 0 else pct0(r['ebitda'] / r['rev'])) for r in R) + " |")
    lines.append("| Net kâr marjı | " + " | ".join(
        ("–" if r["rev"] == 0 else pct0(r['net'] / r['rev'])) for r in R) + " |")
    return "\n".join(lines)


def md_cash(name):
    res = run(name)
    R = res["rows"]
    c1 = res["c1"]
    hdr = "| Nakit akışı (USD) | Y0 | " + " | ".join(YEAR_LABEL[r["y"]] for r in R) + " |"
    lines = [hdr, "|---|---:|" + "---:|" * len(R)]
    cols = []
    cum = 0
    data = {k: [] for k in ["ebitda", "tax", "capex", "grant", "loan_in", "intr", "princ", "eq", "net", "cum"]}
    # Y0
    y0 = dict(ebitda=0, tax=0, capex=-c1, grant=0, loan_in=c1 * LOAN_SHARE, intr=0, princ=0)
    seq = [y0]
    for r in R:
        seq.append(dict(ebitda=r["ebitda"], tax=-r["tax"], capex=-r["capex"], grant=r["grant"],
                        loan_in=res["c2"] * LOAN_SHARE if r["y"] == 1 else 0,
                        intr=-r["intr"], princ=-r["princ"]))
    min_cum = 0
    for d in seq:
        n = sum(d.values())
        cum += n
        min_cum = min(min_cum, cum)
        d["net"], d["cum"] = n, cum
    labels = [("FAVÖK", "ebitda"), ("Ödenen vergi", "tax"), ("Yatırım (CAPEX)", "capex"),
              ("Hibe (KKYDP)", "grant"), ("Kredi kullanımı", "loan_in"), ("Faiz ödemesi", "intr"),
              ("Anapara ödemesi", "princ"), ("**Net nakit (özsermaye)**", "net"),
              ("**Kümülatif**", "cum")]
    for lab, k in labels:
        if k == "grant" and not any(d[k] for d in seq):
            continue
        lines.append(f"| {lab} | " + " | ".join(fmt(d[k]) for d in seq) + " |")
    return "\n".join(lines), min_cum


def md_fixed():
    out = ["| Sabit gider (USD/yıl) | Y1 | Y2 | Y3 | Y4 | Y5 |", "|---|---:|---:|---:|---:|---:|"]
    for k, v in FIXED.items():
        out.append(f"| {k} | " + " | ".join(fmt(x) for x in v) + " |")
    out.append("| **Toplam** | " + " | ".join(f"**{fmt(fixed_opex(y))}**" for y in range(1, 6)) + " |")
    return "\n".join(out)


def md_unit():
    p = pack_price_per_kg(); c = pack_cost_per_kg()
    out = ["| Paket | Kanal payı | Üretici çıkış fiyatı | USD/kg | TL/paket | Ambalaj USD/paket |",
           "|---|---:|---:|---:|---:|---:|"]
    for k, (s, pr, cc) in PACKS.items():
        g = int(k.split()[0]) / 1000
        out.append(f"| {k} | %{s*100:.0f} | ${fmt(pr,2)} | ${fmt(pr/g,2)} | {fmt(pr*FX)} TL | ${fmt(cc,2)} |")
    out.append(f"| **Ağırlıklı** | | | **${fmt(p,2)}/kg** | | **${fmt(c,2)}/kg (koli dahil)** |")
    return "\n".join(out)


def md_unit_econ():
    p = pack_price_per_kg(); c = pack_cost_per_kg()
    rows = [
        ("Ağırlıklı satış fiyatı", p),
        ("Distribütör/kanal payı (%12)", -p * DIST_COMM),
        ("Soğuk sevkiyat", -COLD_TRANSPORT),
        ("Ambalaj (punnet + film + QR etiket + koli)", -c),
        ("Pakethane işçiliği", -PACKHOUSE_LABOR),
        ("Hasat işçiliği (punnet'e tarlada)", -HARVEST["pack"]),
    ]
    margin = sum(v for _, v in rows)
    hal = HAL_PRICE * (1 - HAL_COMM) - HAL_PACK - HARVEST["bulk"]
    out = ["| kg başı (USD) | Paketli | Hal (dökme) |", "|---|---:|---:|"]
    out.append(f"| Satış fiyatı | {fmt(p,2)} | {fmt(HAL_PRICE,2)} |")
    out.append(f"| Kanal payı / komisyon | {fmt(-p*DIST_COMM,2)} | {fmt(-HAL_PRICE*HAL_COMM,2)} |")
    out.append(f"| Soğuk sevkiyat / kasa | {fmt(-COLD_TRANSPORT,2)} | {fmt(-HAL_PACK,2)} |")
    out.append(f"| Ambalaj + koli | {fmt(-c,2)} | – |")
    out.append(f"| Pakethane işçiliği | {fmt(-PACKHOUSE_LABOR,2)} | – |")
    out.append(f"| Hasat işçiliği | {fmt(-HARVEST['pack'],2)} | {fmt(-HARVEST['bulk'],2)} |")
    out.append(f"| **Katkı payı** | **{fmt(margin,2)}** | **{fmt(hal,2)}** |")
    return "\n".join(out), margin, hal


def usd(x):
    return ("−$" if x < 0 else "$") + fmt(abs(x))


def md_scen():
    out = ["| Gösterge | " + " | ".join(SCENARIOS) + " |", "|---|" + "---:|" * len(SCENARIOS)]
    res = {n: run(n) for n in SCENARIOS}
    met = {n: project_metrics(n) for n in SCENARIOS}
    def row(lab, fn):
        out.append(f"| {lab} | " + " | ".join(fn(n) for n in SCENARIOS) + " |")
    row("Y5 rekolte", lambda n: fmt(res[n]["rows"][4]["kg"] / 1000, 1) + " t")
    row("Y5 gelir", lambda n: usd(res[n]["rows"][4]["rev"]))
    row("Y5 FAVÖK", lambda n: usd(res[n]["rows"][4]["ebitda"]))
    row("Y5 vergi öncesi kâr", lambda n: usd(res[n]["rows"][4]["ebt"]))
    row("Y5 net kâr", lambda n: usd(res[n]["rows"][4]["net"]))
    row("5 yıl kümülatif net kâr", lambda n: usd(sum(r["net"] for r in res[n]["rows"])))
    row("Proje IRR (10 yıl, kaldıraçsız)", lambda n: pct(met[n]["irr"]))
    row("Özsermaye IRR (kredili)", lambda n: pct(met[n]["eq_irr"]))
    row("Geri dönüş (kaldıraçsız, Y0'dan)", lambda n: ("geri dönmez" if met[n]["payback"] is None else fmt(met[n]["payback"], 1) + " yıl"))
    return "\n".join(out)


def breakevens():
    """Y5 baz yapıda: vergi öncesi kârı sıfırlayan paketli fiyat çarpanı ve rekolte."""
    base = SCENARIOS["Baz"]
    out = {}
    for key in ("price", "yield"):
        lo, hi = 0.05, 1.5
        for _ in range(80):
            m = (lo + hi) / 2
            if key == "price":
                SCENARIOS["_t"] = dict(base, price_mult=m)
            else:
                SCENARIOS["_t"] = dict(base, yields=[v * m for v in base["yields"]],
                                       corp_t=[v * m for v in base["corp_t"]])
            e = run("_t")["rows"][4]["ebt"]
            lo, hi = (lo, m) if e > 0 else (m, hi)
        out[key] = m
    del SCENARIOS["_t"]
    return out


def core_only():
    """Sadece meyve gelirleri (hizmet/lab/danışmanlık = 0)."""
    SCENARIOS["_c"] = dict(SCENARIOS["Baz"], service=[0]*5, lab=[0]*5, consult=[0]*5)
    r = run("_c")["rows"]
    del SCENARIOS["_c"]
    return r


def tax_compare():
    r = run("Baz")["rows"][4]
    fruit = r["r_pack"] + r["r_corp"] + r["r_hal"] + r["r_proc"]
    other = r["r_serv"] + r["r_lab"] + r["r_cons"]
    return fruit, other, r


if __name__ == "__main__":
    if "--tables" in sys.argv:
        print(md_capex()); print(); print(md_capex_summary()[0]); print()
        print(md_unit()); print(); print(md_unit_econ()[0]); print(); print(md_fixed())
        for n in SCENARIOS:
            print(f"\n### {n}\n"); print(md_pnl(n)); print(); print(md_cash(n)[0])
        print(); print(md_scen()); print(); print(md_variants())
    else:
        print("Faz1", capex_phase(1), "Faz2", capex_phase(2), "toplam",
              sum(capex_phase(1)) + sum(capex_phase(2)))
        print("paket fiyat", pack_price_per_kg(), "ambalaj", pack_cost_per_kg())
        for n in SCENARIOS:
            m = project_metrics(n)
            R = run(n)["rows"]
            print(n, [round(r["rev"]) for r in R], [round(r["ebt"]) for r in R], [round(r["net"]) for r in R],
                  pct(m["irr"]), pct(m["eq_irr"]), m["payback"], "mincum", round(md_cash(n)[1]))
        print("başabaş", breakevens())
        co = core_only(); print("sadece meyve", [round(r["ebt"]) for r in co], [round(r["net"]) for r in co])
        print("dep", [round(depreciation(y)) for y in range(1, 6)])
