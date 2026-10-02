"""v6 — Ek gelir odaklı yalın hibrit plan: en az CAPEX/OPEX, en çok üretim, kendi kurulan teknoloji.

    python reports/bogurtlen-fizibilite/model_v6.py            # özet
    python reports/bogurtlen-fizibilite/model_v6.py --tables   # rapor tabloları

Kurgu: satış ortağı paketli ürünü %18 komisyonla satar; ürün tarlada kapaklı PET kaba toplanır;
saha yönetimi kurucu (Ankara) + baba (Bursa) + yevmiyeli ekip; traktör kiralık/hizmet alımı.
Dikim (her 10 da): 7 da sertifikalı doku kültürü (sık, 0,75 m) + 3 da 2 yaşlı saksılı fidan.
Vergi: gerçek kişi çiftçi, satışta %2 stopaj. 2026 sabit USD.
"""
from __future__ import annotations

import sys

import model_v2 as v2

FX = v2.FX
fmt, usd, pct = v2.fmt, v2.usd, v2.pct
YEARS = 10
LABEL = {0: "Y0"} | {y: str(2026 + y) for y in range(1, 11)}

# ------------------------------------------------------------------ verim (10 da başına, ton)
TC = [0.6, 8, 17, 20, 20, 20, 20, 20, 18, 16]        # doku kültürü, sık dikim
POT = [3.5, 15, 20, 20, 20, 20, 20, 20, 18, 16]      # 2 yaşlı saksılı fidan
TC_SHARE = 0.70
YIELD = [TC_SHARE * a + (1 - TC_SHARE) * b for a, b in zip(TC, POT)]
SECOND = 0.20

# ------------------------------------------------------------------ fiyat / kanal
PACK_PRICE = v2.pack_price_per_kg()       # 5,65 $/kg
PARTNER_COMM = 0.18
PACK_SHARE = [0.60, 0.75, 0.80] + [0.80] * 7
CLAMSHELL, LABEL_LABOR, DELIVERY = 0.65, 0.06, 0.25
HARVEST_PACK, HARVEST_BULK = 0.70, 0.55
HAL_PRICE, HAL_COST = 2.50, 0.45
PROC_PRICE, PROC_COST = 1.30, 0.09
IQF_PRICE, IQF_COST = 2.80, 0.54
STOPAJ = 0.02
DISC = 0.12


def capex(area):
    """(faz, yıl sonu, grup, kalem, miktar, USD, ömür). Faz 0: kurulum, 1: ilk hasattan önce, 2: kârdan."""
    f = area / 10
    nodes = 6 if area <= 10 else 10
    return [
        (0, 0, "Arazi", "Toprak analizi, dip kazan, lazer tesviye, 40 t/10 da gübre, sedde", f"{area} da", 3850 * f, 10),
        (0, 0, "Arazi", "Agrotekstil malç örtü (ot işçiliğini düşürür)", f"{int(3400*f)} m²", 1100 * f, 5),
        (0, 0, "Fidan", "Sertifikalı doku kültürü fidan, sık dikim (%70 alan)", f"{int(3171*f)} ad × $3,0", 9513 * f, 10),
        (0, 0, "Fidan", "2 yaşlı saksılı sertifikalı fidan, sık dikim (%30 alan)", f"{int(1359*f)} ad × $6,5", 8834 * f, 10),
        (0, 0, "Fidan", "Dikim işçiliği + kök uyarıcı", "", 600 * f, 10),
        (0, 0, "Telli sistem", "Galvaniz direk 8 m aralık, 3 kat tel, ankraj, montaj", "", 7150 * f, 10),
        (0, 0, "Sulama", "Hidrant bağlantısı, disk filtre, ana hat, basınç ayarlı çift damla hattı", f"{int(6600*f)} m", 2450 * f, 10),
        (0, 0, "Teknoloji (kendi yapımın)", "Fertigasyon: ESP32/röle kontrolör + selenoid vanalar + venturi + asit pompası + hat içi EC/pH", "", 2000, 5),
        (0, 0, "Teknoloji (kendi yapımın)", "LoRaWAN gateway + 4G router", "1", 450, 5),
        (0, 0, "Teknoloji (kendi yapımın)", "Toprak düğümü: ESP32-LoRa + 2 endüstriyel RS485 nem/EC/sıcaklık probu + solar", f"{nodes} × $280", 280 * nodes, 5),
        (0, 0, "Teknoloji (kendi yapımın)", "Referans prob (kendi sensörlerinin kalibrasyonu)", "1", 900, 5),
        (0, 0, "Teknoloji (kendi yapımın)", "Hobi-profesyonel meteoroloji istasyonu + yaprak ıslaklığı sensörü", "1", 600, 5),
        (0, 0, "Teknoloji (kendi yapımın)", "Debimetre + basınç sensörü", "2", 400, 5),
        (0, 0, "Teknoloji (kendi yapımın)", "Mini PC sunucu + UPS (ChirpStack, InfluxDB, Grafana, Node-RED)", "1", 400, 4),
        (0, 0, "Teknoloji (kendi yapımın)", "Solar 4G PTZ güvenlik kamerası", "1", 650, 5),
        (0, 0, "Diğer", "ÇKS, 5403 tarımsal yapı izni, proje", "", 600, 5),
        ((1, 1, "Soğuk zincir", "20' reefer konteyner, yenilenmiş (0/+2 °C; 10 da tepe yükü ~300 kg/gün)", "1", 5500, 10)
         if area <= 10 else (1, 1, "Soğuk zincir", "40' reefer konteyner, yenilenmiş (0/+2 °C)", "1", 8500, 10)),
        (1, 1, "Soğuk zincir", "Ön soğutma tüneli (fan + branda + termostat, kendi yapımın)", "1", 1000, 5),
        (1, 1, "Soğuk zincir", "Trifaze elektrik bağlantısı + pano", "", 3500, 15),
        (1, 1, "Soğuk zincir", "Stabilize zemin + basit gölgelik", "", 1500, 10),
        (1, 1, "Soğuk zincir", "NFC kartlı toplayıcı tartısı (kendi yapımın) + terazi + QR etiket yazıcı + 6 logger", "", 900, 5),
        (1, 1, "Soğuk zincir", "Hasat kasaları + el arabaları", "", 1000 * f ** 0.5, 5),
        (1, 1, "Soğuk zincir", "Gıda işletme kaydı + İyi Tarım belgesi", "", 1000, 5),
        (1, 1, "Kalite", "%35 gölge filesi (güneş yanığına karşı) + montaj", "", 3800 * f, 7),
    ] + ([(2, 4, "Kârdan", "Şok dondurucu + 2. reefer (-20 °C): 2. sınıf ürün IQF", "", 22500, 9)] if area > 10 else [])


REPLACE = [(6, "Elektronik yenileme", 2500, 5), (8, "Gölge filesi + malç yenileme", 4900, 7)]
CONT = 0.08


def fixed(y, area):
    f = area / 10
    k = min(y, 5) - 1
    rows = {
        "Gübre + mücadele (biyolojik öncelikli)": [1100, 2000, 2800, 3000, 3000][k] * f,
        "Budama, bağlama, ot (yevmiyeli)": [1300, 2300, 2900, 3000, 3000][k] * f,
        "Traktör/ilaçlama hizmet alımı": [400, 600, 600, 600, 600][k] * f,
        "DSİ su ücreti": [250, 400, 500, 500, 500][k] * f,
        "Sezonluk saha işçisi (Mart-Ekim, yalnız 20 da)": (6000 if area > 10 and y >= 2 else (3000 if area > 10 else 0)),
        "Sezonluk soğuk oda/etiket yardımcısı": ([0, 1200, 1500, 1500, 1500][k] * f ** 0.5),
        "Elektrik (soğuk oda, pompa)": [100, 1000, 1200, 1200, 1200][k] + (900 if area > 10 and y >= 5 else 0),
        "Bakım-onarım": [200, 600, 800, 900, 1000][k] * f ** 0.5,
        "TARSİM sigortası": [0, 600, 800, 900, 1000][k] * f ** 0.7,
        "SIM/4G + bulut yedeği": 150,
        "Gıda güvenliği/kalıntı analizi": [0, 400, 400, 400, 400][k],
        "Arı kovanı kiralama": [0, 300, 300, 300, 300][k] * f,
        "Muhasebe (çiftçi)": 400,
        "Kurucu ulaşımı (Ankara)": 3000,
        "Baba: yakıt/harcırah": 800,
    }
    return rows


def items(area):
    out = []
    for ph, y, g, k, q, v, life in capex(area):
        out.append((ph, y, g, k, q, v * (1 + CONT), life))
    for y, k, v, life in REPLACE:
        out.append((3, y, "Yenileme", k, "", v, life))
    return out


def run(area=20, price_mult=1.0, yield_mult=1.0, harvest_mult=1.0, partner_comm=PARTNER_COMM):
    f = area / 10
    it = items(area)
    rows = []
    for y in range(1, YEARS + 1):
        k = y - 1
        kg = YIELD[k] * 1000 * f * yield_mult
        second = kg * SECOND
        first = kg - second
        packed = first * PACK_SHARE[k]
        hal = first - packed
        has_iqf = area > 10 and y >= 5
        iqf = second if has_iqf else 0.0
        proc = second - iqf
        pp = PACK_PRICE * price_mult
        rev = (packed * pp * (1 - partner_comm) + hal * HAL_PRICE * price_mult
               + proc * PROC_PRICE * price_mult + iqf * IQF_PRICE * price_mult)
        var = (packed * (HARVEST_PACK * harvest_mult + CLAMSHELL + LABEL_LABOR + DELIVERY)
               + hal * (HARVEST_BULK * harvest_mult + HAL_COST) + proc * (HARVEST_BULK * harvest_mult + PROC_COST)
               + iqf * (HARVEST_BULK * harvest_mult + IQF_COST))
        fx = sum(fixed(y, area).values())
        ebitda = rev - var - fx
        dep = sum(v / life for _, yy, _, _, _, v, life in it if yy + 1 <= y < yy + 1 + life)
        stopaj = rev * STOPAJ
        cap = sum(v for _, yy, _, _, _, v, _ in it if yy == y)
        rows.append(dict(y=y, kg=kg, packed=packed, rev=rev, var=var, fixed=fx, ebitda=ebitda, dep=dep,
                         ebt=ebitda - dep, stopaj=stopaj, net=ebitda - dep - stopaj, capex=cap,
                         cash=ebitda - stopaj - cap))
    c0 = sum(v for _, yy, _, _, _, v, _ in it if yy == 0)
    flows = [-c0] + [r["cash"] for r in rows]
    nbv10 = sum(v * max(0, (yy + life - YEARS)) / life for _, yy, _, _, _, v, life in it)
    flows[-1] += nbv10 * 0.5
    return dict(rows=rows, flows=flows, c0=c0, items=it, resid=nbv10 * 0.5)


def credit_flows(area):
    r = run(area)
    it = r["items"]
    flows = list(r["flows"])
    for dy in (0, 1):
        amt = sum(v for ph, yy, *_ , v, _ in [(i[0], i[1], i[2], i[3], i[4], i[5], i[6]) for i in it] if yy == dy and ph <= 1) * 0.5
        flows[dy] += amt
        for yy, (i, p) in v2.loan_schedule(amt, dy).items():
            flows[yy] -= i + p
    return flows


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


# ------------------------------------------------------------------ markdown
def md_capex(area):
    it = items(area)
    out = [f"| Faz | Ne zaman | Grup | Kalem | Miktar | USD | TL |", "|---|---|---|---|---|---:|---:|"]
    when = {0: "Q4-2026 / Q1-2027", 1: "2027 sonu", 4: "2030 sonu (kârdan)"}
    for ph, y, g, k, q, v, _ in it:
        if ph == 3:
            continue
        out.append(f"| {ph} | {when.get(y, LABEL[y])} | {g} | {k} | {q} | {fmt(v)} | {fmt(v*FX)} |")
    for ph, lab in ((0, "Faz 0 — kurulum"), (1, "Faz 1 — ilk büyük hasattan önce"), (2, "Faz 2 — kârdan")):
        s = sum(i[5] for i in it if i[0] == ph)
        if s:
            out.append(f"| | | | **{lab} toplamı** | | **{fmt(s)}** | **{fmt(s*FX)}** |")
    s01 = sum(i[5] for i in it if i[0] <= 1)
    out.append(f"| | | | **Başlangıç yatırımı (Faz 0 + 1)** | | **{fmt(s01)}** | **{fmt(s01*FX)}** |")
    out.append("\n*Tutarlar %8 beklenmeyen gider payı dahildir.*")
    return "\n".join(out)


def md_fixed(area):
    out = ["| Sabit gider (USD/yıl) | 2027 | 2028 | 2029 | 2030 | 2031+ |", "|---|---:|---:|---:|---:|---:|"]
    keys = list(fixed(1, area).keys())
    for k in keys:
        vals = [fixed(y, area)[k] for y in range(1, 6)]
        if any(vals):
            out.append(f"| {k} | " + " | ".join(fmt(v) for v in vals) + " |")
    out.append("| **Toplam** | " + " | ".join(f"**{fmt(sum(fixed(y, area).values()))}**" for y in range(1, 6)) + " |")
    return "\n".join(out)


def md_pnl(area, years=range(1, 11)):
    r = run(area)
    R = [x for x in r["rows"] if x["y"] in years]
    c = cum(r["flows"])
    out = ["| USD | " + " | ".join(LABEL[x["y"]] for x in R) + " |", "|---|" + "---:|" * len(R)]
    def line(lab, fn, bold=False):
        cells = [fn(x) for x in R]
        if bold:
            cells = [f"**{v}**" for v in cells]; lab = f"**{lab}**"
        out.append(f"| {lab} | " + " | ".join(cells) + " |")
    line("Rekolte (t)", lambda x: fmt(x["kg"] / 1000, 1))
    line("Gelir (ortak komisyonu düşülmüş)", lambda x: fmt(x["rev"]), True)
    line("Değişken gider (hasat, kap, teslimat, kanal)", lambda x: fmt(-x["var"]))
    line("Sabit gider", lambda x: fmt(-x["fixed"]))
    line("FAVÖK", lambda x: fmt(x["ebitda"]), True)
    line("Amortisman", lambda x: fmt(-x["dep"]))
    line("Vergi öncesi kâr", lambda x: fmt(x["ebt"]), True)
    line("Stopaj (%2)", lambda x: fmt(-x["stopaj"]))
    line("Net kâr", lambda x: fmt(x["net"]), True)
    line("Aylık ortalama net kâr (TL)", lambda x: fmt(x["net"] / 12 * FX))
    line("Yatırım / yenileme", lambda x: fmt(-x["capex"]))
    line("Kümülatif nakit (Y0 dahil)", lambda x: fmt(c[x["y"]]), True)
    return "\n".join(out)


def summary(area):
    r = run(area); c = cum(r["flows"]); cf = cum(credit_flows(area))
    it = r["items"]
    return dict(start=sum(i[5] for i in it if i[0] <= 1), c0=r["c0"], peak=-min(c), peak_credit=-min(cf),
                irr=v2.irr(r["flows"]), npv=npv(r["flows"]), pb=payback(r["flows"]),
                net5=sum(x["net"] for x in r["rows"][:5]), net10=sum(x["net"] for x in r["rows"]),
                y5=r["rows"][4], y2=r["rows"][1], resid=r["resid"])


def md_compare():
    S = {a: summary(a) for a in (10, 20)}
    out = ["| Gösterge | 10 da | 20 da |", "|---|---:|---:|"]
    rows = [
        ("Başlangıç yatırımı (Faz 0 + 1)", lambda s: usd(s["start"]) + f" ({fmt(s['start']*FX/1e6,1)} M TL)"),
        ("Cepten çıkan en yüksek tutar (işletme açıkları dahil)", lambda s: usd(s["peak"]) + f" ({fmt(s['peak']*FX/1e6,1)} M TL)"),
        ("— Ziraat faiz destekli kredi (%50) ile", lambda s: usd(s["peak_credit"]) + f" ({fmt(s['peak_credit']*FX/1e6,1)} M TL)"),
        ("2028 rekolte / net kâr", lambda s: fmt(s["y2"]["kg"] / 1000, 1) + " t / " + usd(s["y2"]["net"])),
        ("2031 rekolte / net kâr", lambda s: fmt(s["y5"]["kg"] / 1000, 1) + " t / " + usd(s["y5"]["net"])),
        ("2031 aylık ortalama ek gelir (net)", lambda s: fmt(s["y5"]["net"] / 12 * FX) + " TL"),
        ("5 yıl toplam net kâr", lambda s: usd(s["net5"])),
        ("10 yıl toplam net kâr", lambda s: usd(s["net10"])),
        ("Geri dönüş (Y0'dan)", lambda s: fmt(s["pb"], 1) + " yıl" if s["pb"] else "–"),
        ("10 yıllık IRR / NPV (%12)", lambda s: pct(s["irr"]) + " / " + usd(s["npv"])),
    ]
    for lab, fn in rows:
        out.append(f"| {lab} | {fn(S[10])} | {fn(S[20])} |")
    return "\n".join(out)


def md_stress(area=20):
    out = ["| Senaryo | 2031 net kâr | Geri dönüş | 10 yıl IRR |", "|---|---:|---:|---:|"]
    for lab, kw in [("Baz", {}), ("Fiyat −%20", dict(price_mult=0.8)), ("Verim −%25", dict(yield_mult=0.75)),
                    ("Hasat işçiliği +%35 (TEKNOSAB etkisi)", dict(harvest_mult=1.35)),
                    ("Ortak komisyonu %25", dict(partner_comm=0.25)),
                    ("Fiyat −%20 + verim −%15 + işçilik +%20", dict(price_mult=0.8, yield_mult=0.85, harvest_mult=1.2))]:
        r = run(area, **kw)
        pb = payback(r["flows"])
        out.append(f"| {lab} | {usd(r['rows'][4]['net'])} | {fmt(pb,1) + ' yıl' if pb else 'dönmez'} | {pct(v2.irr(r['flows']))} |")
    return "\n".join(out)


def md_yield():
    out = ["| Yıl | Doku kültürü bloğu (7 da) | Saksılı blok (3 da) | Toplam / 10 da | Toplam / 20 da |", "|---|---:|---:|---:|---:|"]
    for k in range(10):
        out.append(f"| {LABEL[k+1]} | {fmt(TC[k]*TC_SHARE,1)} t | {fmt(POT[k]*(1-TC_SHARE),1)} t | {fmt(YIELD[k],1)} t | {fmt(YIELD[k]*2,1)} t |")
    return "\n".join(out)


if __name__ == "__main__":
    if "--tables" in sys.argv:
        for a in (10, 20):
            print(md_capex(a)); print(); print(md_fixed(a)); print(); print(md_pnl(a)); print()
        print(md_compare()); print(); print(md_stress()); print(); print(md_yield())
    else:
        for a in (10, 20):
            s = summary(a)
            print(a, {k: (round(v) if isinstance(v, float) else v) for k, v in s.items() if k not in ("y5", "y2")},
                  "y2net", round(s["y2"]["net"]), "y5net", round(s["y5"]["net"]))
            print("  ", [round(x["net"]) for x in run(a)["rows"]], [round(v) for v in cum(run(a)["flows"])])
