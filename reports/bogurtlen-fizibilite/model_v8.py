"""v8 — Güncel 2026 TL fiyatlarıyla 10 / 20 da seçenekleri: açık tarla böğürtlen + tünelde saksılı
ahududu + kendin-topla (U-pick). Tüm tutarlar 2026 sabit TL (reel); USD = TL / FX.

    python reports/bogurtlen-fizibilite/model_v8.py            # özet
    python reports/bogurtlen-fizibilite/model_v8.py --tables   # rapor tabloları

Fiyat kaynakları (Ekim 2026 web taraması, rapor Ek A): hal fiyatları (haldefiyat, Bursa Büyükşehir hal),
Migros/CarrefourSA raf fiyatı, fidan satıcıları, yevmiye kararları, sera/panel/damla fiyat rehberleri.
"""
from __future__ import annotations

import sys

FX = 49.1
YEARS = 10
LABEL = {0: "Y0"} | {y: str(2026 + y) for y in range(1, 11)}


def fmt(x, d=0):
    if x is None:
        return "–"
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if x < 0 else "") + s


def tl(x):
    return fmt(x) + " TL"


def mtl(x):
    return ("−" if x < 0 else "") + fmt(abs(x) / 1e6, 2) + " M TL"


def pct(x):
    return "–" if x is None else ("−" if x < 0 else "") + "%" + fmt(abs(x) * 100, 1)


# ------------------------------------------------------------------ FİYATLAR (TL/kg, 2026)
# Böğürtlen hal fiyatı mevsime göre (üretici brüt, kaliteli kültür çeşidi):
SEASON_PRICE = {"Haziran": 450, "Temmuz": 250, "Ağustos": 180, "Eylül": 220, "Ekim": 300}
SEASON_SHARE = {"Haziran": 0.05, "Temmuz": 0.30, "Ağustos": 0.35, "Eylül": 0.20, "Ekim": 0.10}   # 3 çeşitli açık tarla
HAL_GROSS = sum(SEASON_PRICE[m] * SEASON_SHARE[m] for m in SEASON_PRICE) * 0.85   # hacim/kalite iskontosu %15
HAL_COST_RATE, HAL_CRATE = 0.10, 8           # komisyon+rüsum, kasa/nakliye TL/kg
PARTNER_PRICE = 300                          # ortak üzerinden paketli (üretici çıkışı, komisyondan önce)
PARTNER_COMM = 0.18
PACK = 25                                    # kapaklı PET kap + etiket + koli, TL/kg
PICKUP = 5                                   # ortak tarladan teslim alır; yükleme TL/kg
UPICK_PRICE = 400                            # kendin-topla perakende TL/kg
UPICK_COST = 40                              # hafta sonu görevli, ilan, kap, WC TL/kg
PROC_PRICE = 65                              # 2. sınıf → işleme (Bursa halinde alt bant 60-70 TL)
SECOND = 0.20
# Ahududu (tünelde saksılı, sezon dışı: Mayıs-Haziran + Ekim-Kasım)
RASP_PRICE, RASP_SECOND, RASP_PROC = 400, 0.15, 80
# Hasat işçiliği: yevmiye 1.400 TL + dayıbaşı %10
DAILY = 1400 * 1.10
HARV_PACK = DAILY / 55                       # paket kalitesi, kişi/gün 55 kg
HARV_BULK = DAILY / 70
HARV_RASP = DAILY / 35
STOPAJ = 0.02
DISC = 0.12

# ------------------------------------------------------------------ VERİM (ton/da)
TC = [0.06, 0.8, 1.7, 2.0, 2.0, 2.0, 2.0, 2.0, 1.8, 1.6]     # doku kültürü, sık dikim
POT = [0.35, 1.5, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 1.8, 1.6]    # 2 yaşlı tüplü fidan
BB_YIELD = [0.7 * a + 0.3 * b for a, b in zip(TC, POT)]       # hibrit
RASP_YIELD = [0.6, 1.8, 2.0, 1.6, 2.0, 2.0, 1.6, 2.0, 2.0, 1.6]   # 3 yılda bir saksı yenileme yılı düşük


PLANS = {
    "A": dict(name="10 da yalnız böğürtlen", bb=10, rasp=0, upick=False),
    "B": dict(name="10 da böğürtlen + kendin-topla", bb=10, rasp=0, upick=True),
    "C": dict(name="10 da optimize: 8,5 da böğürtlen + 1 da tünel ahududu + kendin-topla", bb=8.5, rasp=1, upick=True),
    "D": dict(name="20 da böğürtlen + kendin-topla", bb=20, rasp=0, upick=True),
    "E": dict(name="20 da optimize: 17,5 da böğürtlen + 2 da tünel ahududu + kendin-topla", bb=17.5, rasp=2, upick=True),
}
UPICK_T = [0, 0.5, 1.2, 1.5, 1.8, 2.0, 2.0, 2.0, 2.0, 2.0]   # kendin-topla satış hacmi (t), hafta sonları


def capex(p):
    """(faz, yıl sonu, grup, kalem, miktar, TL, ömür)"""
    bb, ra = p["bb"], p["rasp"]
    plants = round(bb * 453)
    tc, pot = round(plants * 0.7), round(plants * 0.3)
    rows_m = round(bb * 1000 / 3)
    big = bb > 10
    it = [
        (0, 0, "Arazi", "Toprak analizi, dip kazan, lazer tesviye, sedde", f"{fmt(bb,1)} da", 9000 * bb, 10),
        (0, 0, "Arazi", "Yanmış çiftlik gübresi 4 t/da", f"{fmt(4*bb,0)} t", 8000 * bb, 10),
        (0, 0, "Arazi", "Agrotekstil malç örtü (sedde üstü)", f"{fmt(340*bb)} m²", 8500 * bb, 5),
        (0, 0, "Fidan", "Doku kültürü fidan, viyolde (216'lık viyol ~5.300 TL) + 2-3 ay saksıda alıştırma (kendin)", f"{fmt(tc)} ad × 46 TL", tc * 46, 10),
        (0, 0, "Fidan", "2 yaşlı tüplü sertifikalı fidan (hızlı blok, %30)", f"{fmt(pot)} ad × 150 TL", pot * 150, 10),
        (0, 0, "Fidan", "Dikim işçiliği", "", 2500 * bb, 10),
        (0, 0, "Telli sistem", "Galvaniz direk 2,7 m, 8 m ara + baş direkleri", f"{fmt(rows_m/8 + bb*6.6)} ad × 350 TL", (rows_m / 8 + bb * 6.6) * 350, 10),
        (0, 0, "Telli sistem", "Galvaniz tel 3 kat (75 TL/kg) + gergi/ankraj + montaj", f"{fmt(rows_m*3)} m", rows_m * 3 * 0.039 * 75 + bb * 8000, 10),
        (0, 0, "Sulama", "Damla: basınç ayarlı çift lateral (~10.000 TL/da) + hidrant bağlantısı, disk filtre, ana hat", "", 10000 * bb + 60000 + (40000 if big else 0), 10),
        (0, 0, "Teknoloji", "Fertigasyon: ESP32 kontrolör, selenoid vanalar, venturi, asit pompası, hat içi EC/pH", "", 100000, 5),
        (0, 0, "Teknoloji", "LoRaWAN gateway + 4G router", "", 22000, 5),
        (0, 0, "Teknoloji", "Toprak düğümü: ESP32-LoRa + 2 RS485 nem/EC/sıcaklık probu + solar", f"{6 if not big else 10} × 13.500 TL", (6 if not big else 10) * 13500, 5),
        (0, 0, "Teknoloji", "Referans prob + meteoroloji istasyonu (yaprak ıslaklığı)", "", 70000, 5),
        (0, 0, "Teknoloji", "Debimetre/basınç, mini PC + UPS, solar 4G kamera", "", 70000, 5),
        (0, 0, "Diğer", "ÇKS, tarımsal yapı izni, proje", "", 30000, 5),
        (1, 1, "Soğuk zincir", "DIY soğuk oda: 100 mm panel (~32 m² × 1.000 TL), kapı, inverter klima 24k BTU, kontrolör, ön soğutma fanı" + (" ×2" if big else ""), "", 110000 * (2 if big else 1), 8),
        (1, 1, "Soğuk zincir", "Monofaze/trifaze elektrik bağlantısı + pano", "", 40000 if not big else 120000, 15),
        (1, 1, "Hasat", "NFC tartı (kendin), terazi, QR etiket yazıcı, sıcaklık logger, kasa/arabalar", "", 75000 * (1.4 if big else 1), 5),
        (1, 1, "Hasat", "Gıda işletme kaydı + İyi Tarım belgesi", "", 50000, 5),
        (1, 1, "Kalite", "%35 gölge filesi + montaj", f"{fmt(500*bb)} m²", 21000 * bb, 7),
    ]
    if ra:
        it += [
            (0, 0, "Tünel ahududu", "Galvaniz yüksek tünel (8 m açıklık, yan havalandırma, böcek tülü)", f"{fmt(ra,0)} da × 600.000 TL", 600000 * ra, 10),
            (0, 0, "Tünel ahududu", "Saksı 20 L + kokopit + damla/çubuk", f"{fmt(2400*ra)} saksı × 60 TL", 2400 * ra * 60, 3),
            (0, 0, "Tünel ahududu", "Tüplü ahududu fidanı (primocane + floricane karışık)", f"{fmt(2400*ra)} ad × 150 TL", 2400 * ra * 150, 3),
            (0, 0, "Tünel ahududu", "Tünel iklim sensörleri (sıcaklık/nem/ışık) + yan perde motoru", "", 25000 + 15000 * ra, 5),
        ]
    if p["upick"]:
        it += [(1, 1, "Kendin-topla", "Tabela, otopark düzeni, portatif WC, gölgelik, satış tezgâhı, terazi", "", 60000, 5)]
    return it


def replacements(p):
    r = [(6, "Elektronik yenileme", 120000, 5), (8, "Gölge filesi + malç yenileme", (21000 + 8500) * p["bb"], 7)]
    if p["rasp"]:
        for y in (3, 6, 9):
            r.append((y, "Ahududu saksı/fidan yenileme", 2400 * p["rasp"] * 180, 3))
        r.append((5, "Tünel plastiği yenileme", 110000 * p["rasp"], 4))
    return r


CONT = 0.08


def items(p):
    out = [(ph, y, g, k, q, v * (1 + CONT), life) for ph, y, g, k, q, v, life in capex(p)]
    out += [(3, y, "Yenileme", k, "", v, life) for y, k, v, life in replacements(p)]
    return out


def fixed(y, p):
    bb, ra = p["bb"], p["rasp"]
    k = min(y, 5) - 1
    big = bb > 10
    rows = {
        "Gübre + mücadele (böğürtlen)": [3000, 5500, 7000, 7500, 7500][k] * bb,
        "Budama, bağlama, ot (yevmiyeli)": [5000, 9000, 11000, 12000, 12000][k] * bb,
        "Traktör/ilaçlama hizmet alımı": 1800 * bb,
        "DSİ sulama ücreti": 1500 * bb,
        "Tünel ahududu: gübre, substrat, budama/bağlama": (70000 * ra if ra else 0),
        "Sezonluk saha işçisi (yalnız 20 da, Mart-Ekim)": (8 * 40214 if big and y >= 2 else (4 * 40214 if big else 0)),
        "Sezonluk soğuk oda/etiket yardımcısı": [0, 45000, 60000, 60000, 60000][k] * (1.5 if big else 1),
        "Elektrik (soğuk oda)": [3000, 10000, 15000, 16000, 16000][k] * (1.8 if big else 1),
        "Bakım-onarım": [10000, 30000, 40000, 45000, 50000][k] * (1.4 if big else 1),
        "TARSİM sigortası": [0, 30000, 40000, 45000, 50000][k] * (1.6 if big else 1) + 15000 * ra,
        "Arı kovanı kiralama": [0, 15000, 15000, 15000, 15000][k] * (bb + ra) / 10,
        "SIM/4G + bulut, muhasebe, analiz": 50000,
        "Kurucu ulaşımı (Ankara, ~20-25 ziyaret)": 125000,
        "Baba: yakıt/harcırah": 40000,
        "Kendin-topla: ilan, sosyal medya": (25000 if p["upick"] and y >= 2 else 0),
    }
    return rows


def run(key, price_mult=1.0, yield_mult=1.0, labor_mult=1.0, partner_price=PARTNER_PRICE):
    p = PLANS[key]
    it = items(p)
    rows = []
    for y in range(1, YEARS + 1):
        k = y - 1
        # --- böğürtlen
        kg = BB_YIELD[k] * 1000 * p["bb"] * yield_mult
        second = kg * SECOND
        first = kg - second
        up = min(UPICK_T[k] * 1000, first * 0.4) if p["upick"] else 0.0
        rest = first - up
        share = [0.5, 0.75, 0.8][min(k, 2)]
        packed = rest * share
        hal = rest - packed
        pp, hg = partner_price * price_mult, HAL_GROSS * price_mult
        r_pack = packed * pp * (1 - PARTNER_COMM)
        r_hal = hal * hg * (1 - HAL_COST_RATE)
        r_up = up * UPICK_PRICE * price_mult
        r_proc = second * PROC_PRICE * price_mult
        c_bb = (packed * (HARV_PACK * labor_mult + PACK + PICKUP) + hal * (HARV_BULK * labor_mult + HAL_CRATE)
                + up * UPICK_COST + second * (HARV_BULK * labor_mult + 5))
        # --- ahududu
        rkg = RASP_YIELD[k] * 1000 * p["rasp"] * yield_mult
        r1 = rkg * (1 - RASP_SECOND)
        r_rasp = r1 * RASP_PRICE * price_mult * (1 - PARTNER_COMM) + (rkg - r1) * RASP_PROC * price_mult
        c_rasp = r1 * (HARV_RASP * labor_mult + PACK + PICKUP) + (rkg - r1) * (HARV_RASP * labor_mult)
        rev = r_pack + r_hal + r_up + r_proc + r_rasp
        var = c_bb + c_rasp
        fx = sum(fixed(y, p).values())
        fx += (labor_mult - 1) * fixed(y, p)["Budama, bağlama, ot (yevmiyeli)"]
        ebitda = rev - var - fx
        dep = sum(v / life for _, yy, _, _, _, v, life in it if yy + 1 <= y < yy + 1 + life)
        stopaj = rev * STOPAJ
        cap = sum(v for _, yy, _, _, _, v, _ in it if yy == y)
        rows.append(dict(y=y, bb_kg=kg, rasp_kg=rkg, up=up, rev=rev, r_pack=r_pack, r_hal=r_hal, r_up=r_up,
                         r_proc=r_proc, r_rasp=r_rasp, var=var, fixed=fx, ebitda=ebitda, dep=dep,
                         ebt=ebitda - dep, stopaj=stopaj, net=ebitda - dep - stopaj, capex=cap,
                         cash=ebitda - stopaj - cap))
    c0 = sum(v for _, yy, _, _, _, v, _ in it if yy == 0)
    flows = [-c0] + [r["cash"] for r in rows]
    nbv = sum(v * max(0, (yy + life - YEARS)) / life for _, yy, _, _, _, v, life in it)
    flows[-1] += nbv * 0.5
    return dict(rows=rows, flows=flows, items=it, c0=c0)


def irr(fl):
    def f(r): return sum(v / (1 + r) ** i for i, v in enumerate(fl))
    if f(-0.9) <= 0:
        return None
    lo, hi = -0.9, 5.0
    for _ in range(200):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if f(m) > 0 else (lo, m)
    return m


def cum(fl):
    c, o = 0, []
    for v in fl:
        c += v; o.append(c)
    return o


def payback(fl):
    c = 0
    for i, v in enumerate(fl):
        p = c; c += v
        if i > 0 and c >= 0 and v > 0:
            return i - 1 + (-p) / v
    return None


def npv(fl, r=DISC):
    return sum(v / (1 + r) ** i for i, v in enumerate(fl))


def summary(key, **kw):
    r = run(key, **kw); c = cum(r["flows"]); it = r["items"]
    return dict(start=sum(i[5] for i in it if i[0] <= 1), peak=-min(c), y2=r["rows"][1], y5=r["rows"][4],
                net10=sum(x["net"] for x in r["rows"]), irr=irr(r["flows"]), npv=npv(r["flows"]),
                pb=payback(r["flows"]))


# ------------------------------------------------------------------ markdown
def md_options():
    keys = list(PLANS)
    S = {k: summary(k) for k in keys}
    out = ["| Seçenek | Başlangıç yatırımı | Cepten en yüksek | 2028 net | 2031 net | 2031 aylık ek gelir | Geri dönüş | 10 yıl IRR |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for k in keys:
        s = S[k]
        out.append(f"| **{k}.** {PLANS[k]['name']} | {mtl(s['start'])} | {mtl(s['peak'])} | {mtl(s['y2']['net'])} | "
                   f"{mtl(s['y5']['net'])} | {tl(s['y5']['net']/12)} | {fmt(s['pb'],1)} yıl | {pct(s['irr'])} |")
    return "\n".join(out)


def md_capex(key):
    it = items(PLANS[key])
    out = ["| Faz | Grup | Kalem | Miktar | TL | USD |", "|---|---|---|---|---:|---:|"]
    for ph, y, g, k, q, v, _ in it:
        if ph <= 1:
            out.append(f"| {ph} | {g} | {k} | {q} | {fmt(v)} | {fmt(v/FX)} |")
    for ph, lab in ((0, "Faz 0 — kurulum (Q4-2026 / Q1-2027)"), (1, "Faz 1 — ilk büyük hasattan önce (2027 sonu)")):
        s = sum(i[5] for i in it if i[0] == ph)
        out.append(f"| | | **{lab}** | | **{fmt(s)}** | **{fmt(s/FX)}** |")
    s = sum(i[5] for i in it if i[0] <= 1)
    out.append(f"| | | **BAŞLANGIÇ YATIRIMI TOPLAMI** | | **{fmt(s)}** | **{fmt(s/FX)}** |")
    out.append("\n*%8 beklenmeyen gider payı dahildir. Yenilemeler (elektronik, file, tünel plastiği, saksı) 10 yıllık nakit akışında ayrıca yer alır.*")
    return "\n".join(out)


def md_fixed(key):
    p = PLANS[key]
    out = ["| Sabit gider (TL/yıl) | 2027 | 2028 | 2029 | 2030 | 2031+ |", "|---|---:|---:|---:|---:|---:|"]
    for k in fixed(1, p):
        vals = [fixed(y, p)[k] for y in range(1, 6)]
        if any(vals):
            out.append(f"| {k} | " + " | ".join(fmt(v) for v in vals) + " |")
    out.append("| **Toplam** | " + " | ".join(f"**{fmt(sum(fixed(y, p).values()))}**" for y in range(1, 6)) + " |")
    return "\n".join(out)


def md_pnl(key):
    r = run(key); R = r["rows"]; c = cum(r["flows"])
    out = ["| TL | " + " | ".join(LABEL[x["y"]] for x in R) + " |", "|---|" + "---:|" * len(R)]
    def line(lab, fn, bold=False):
        cells = [fn(x) for x in R]
        if bold:
            cells = [f"**{v}**" for v in cells]; lab = f"**{lab}**"
        out.append(f"| {lab} | " + " | ".join(cells) + " |")
    line("Böğürtlen (t)", lambda x: fmt(x["bb_kg"] / 1000, 1))
    if PLANS[key]["rasp"]:
        line("Ahududu (t)", lambda x: fmt(x["rasp_kg"] / 1000, 1))
    line("— Ortak üzerinden paketli", lambda x: fmt(x["r_pack"] / 1000) + "k")
    line("— Hal", lambda x: fmt(x["r_hal"] / 1000) + "k")
    if PLANS[key]["upick"]:
        line("— Kendin-topla", lambda x: fmt(x["r_up"] / 1000) + "k")
    line("— 2. sınıf → işleme", lambda x: fmt(x["r_proc"] / 1000) + "k")
    if PLANS[key]["rasp"]:
        line("— Tünel ahududu", lambda x: fmt(x["r_rasp"] / 1000) + "k")
    line("Gelir", lambda x: fmt(x["rev"] / 1000) + "k", True)
    line("Değişken gider (hasat, kap, kanal)", lambda x: fmt(-x["var"] / 1000) + "k")
    line("Sabit gider", lambda x: fmt(-x["fixed"] / 1000) + "k")
    line("FAVÖK", lambda x: fmt(x["ebitda"] / 1000) + "k", True)
    line("Amortisman", lambda x: fmt(-x["dep"] / 1000) + "k")
    line("Stopaj %2", lambda x: fmt(-x["stopaj"] / 1000) + "k")
    line("Net kâr", lambda x: fmt(x["net"] / 1000) + "k", True)
    line("Aylık net", lambda x: fmt(x["net"] / 12 / 1000) + "k")
    line("Yatırım / yenileme", lambda x: fmt(-x["capex"] / 1000) + "k")
    line("Kümülatif nakit", lambda x: fmt(c[x["y"]] / 1000) + "k", True)
    out.append("\n*Tutarlar bin TL (k), 2026 sabit fiyatlarıyla.*")
    return "\n".join(out)


def md_stress(key):
    out = ["| Senaryo | 2031 net | Geri dönüş | 10 yıl IRR |", "|---|---:|---:|---:|"]
    for lab, kw in [("Baz", {}), ("Tüm fiyatlar −%30", dict(price_mult=0.7)), ("Verim −%25", dict(yield_mult=0.75)),
                    ("İşçilik +%40 (TEKNOSAB)", dict(labor_mult=1.4)), ("Ortak fiyatı hal fiyatına iner (200 TL)", dict(partner_price=200)),
                    ("Fiyat −%30 + verim −%15 + işçilik +%20", dict(price_mult=0.7, yield_mult=0.85, labor_mult=1.2))]:
        s = summary(key, **kw)
        out.append(f"| {lab} | {mtl(s['y5']['net'])} | {(fmt(s['pb'],1)+' yıl') if s['pb'] else 'dönmez'} | {pct(s['irr'])} |")
    return "\n".join(out)


def md_prices():
    out = ["| Ay | Hal fiyatı varsayımı (TL/kg) | Açık tarla hasat payı |", "|---|---:|---:|"]
    for m in SEASON_PRICE:
        out.append(f"| {m} | {SEASON_PRICE[m]} | %{SEASON_SHARE[m]*100:.0f} |")
    out.append(f"| **Ağırlıklı (−%15 hacim/kalite iskontosu ile)** | **{fmt(HAL_GROSS)}** | |")
    return "\n".join(out)


def unit_table():
    rows = [
        ("Kendin-topla (perakende, hasat işçiliği yok)", UPICK_PRICE - UPICK_COST),
        ("Tünel ahududu (ortak, sezon dışı)", RASP_PRICE * (1 - PARTNER_COMM) - HARV_RASP - PACK - PICKUP),
        ("Böğürtlen, ortak üzerinden paketli", PARTNER_PRICE * (1 - PARTNER_COMM) - HARV_PACK - PACK - PICKUP),
        ("Böğürtlen, hal", HAL_GROSS * (1 - HAL_COST_RATE) - HARV_BULK - HAL_CRATE),
        ("Böğürtlen, 2. sınıf işleme", PROC_PRICE - HARV_BULK - 5),
    ]
    out = ["| Kanal | kg başı katkı (TL) | USD |", "|---|---:|---:|"]
    out += [f"| {a} | {fmt(b)} | {fmt(b/FX,2)} |" for a, b in rows]
    return "\n".join(out)


if __name__ == "__main__":
    print("hal ağırlıklı", HAL_GROSS, "hasat TL/kg", HARV_PACK, HARV_BULK, HARV_RASP)
    if "--tables" in sys.argv:
        print(md_options()); print(); print(unit_table()); print(); print(md_prices())
        for k in ("C", "E"):
            print(); print(md_capex(k)); print(); print(md_fixed(k)); print(); print(md_pnl(k)); print(); print(md_stress(k))
    else:
        print(md_options()); print(); print(unit_table())
        for k in PLANS:
            r = run(k); print(k, [round(x["net"] / 1000) for x in r["rows"]])
