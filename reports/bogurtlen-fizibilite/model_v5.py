"""v5 — Yalın, öz kaynaklı başlangıç: satış ortağı + kurucu ve aile emeği, kâr ettikçe eklenen fazlar.

    python reports/bogurtlen-fizibilite/model_v5.py

Varsayımlar: satış ortağı paketli ürünü komisyonla satar; pakethane yok, ürün tarlada kapaklı
PET kaba (125/250/500 g) toplanır, soğuk odada etiketlenir. Kalıcı teknisyen yok (10 da);
saha yönetimi kurucu (Ankara'dan ziyaret) + baba (Bursa) + yevmiyeli işçi. Vergi: gerçek kişi
çiftçi, ürün satışında %2 stopaj (nihai). 2026 sabit USD.
"""
from __future__ import annotations

import model_v2 as v2

FX = v2.FX
fmt, usd, pct = v2.fmt, v2.usd, v2.pct
LABEL = {0: "Y0 (Q4-2026)", 1: "2027", 2: "2028", 3: "2029", 4: "2030", 5: "2031"}

# ------------------------------------------------------------------ verim (sık dikim 0,75 m, 10 da)
YIELD = [0.6, 8, 17, 20, 20]          # 2027 sonbahar: primocane bloğu
SECOND = 0.20

# ------------------------------------------------------------------ fiyat / kanal
PACK_PRICE = v2.pack_price_per_kg()    # 5,65 $/kg üretici çıkışı (paketli)
PARTNER_COMM = 0.18                    # satış ortağının payı
PACK_SHARE = [0.50, 0.70, 0.80, 0.80, 0.80]   # 1. sınıfın ortak üzerinden paketli satılan payı
CLAMSHELL = 0.65                       # kapaklı PET kap + etiket + koli $/kg
LABEL_LABOR = 0.06                     # soğuk odada etiket/koli $/kg
DELIVERY = 0.25                        # Bursa'ya soğuk teslim $/kg
HARVEST_PACK, HARVEST_BULK = 0.70, 0.55
HAL_PRICE, HAL_COST = 2.50, 0.45       # komisyon + kasa ≈ 0,45 $/kg
PROC_PRICE, PROC_COST = 1.30, 0.09
IQF_PRICE, IQF_COST = 2.80, 0.54       # dondurma + ambalaj + navlun + komisyon
STOPAJ = 0.02

# ------------------------------------------------------------------ yatırımlar (yıl sonu ödenir)
def capex_items(area=10):
    f = area / 10
    items = [
        # (faz, yıl, kalem, USD, ömür)
        (0, 0, "Toprak hazırlığı: analiz, dip kazan, lazer tesviye, 40 t gübre, sedde", 3850 * f, 10),
        (0, 0, "Agrotekstil malç örtü", 1100 * f, 5),
        (0, 0, "Sertifikalı doku kültürü fidan, sık dikim (4.000 ad + %5 yedek) + dikim", 13400 * f, 10),
        (0, 0, "Telli terbiye, galvaniz direk 8 m aralık", 7150 * f, 10),
        (0, 0, "Sulama hidroliği: hidrant bağlantısı, filtre, ana hat, çift lateral", 2450 * f, 10),
        (0, 0, "Fertigasyon: kendi kontrolörün + venturi + asit pompası + hat içi EC/pH", 2000, 5),
        (0, 0, "Veri çekirdeği: LoRaWAN gateway, 4 DIY toprak düğümü, referans prob, mini PC", 3120 + 1120 * (f - 1), 5),
        (0, 0, "Profesyonel meteoroloji istasyonu (yaprak ıslaklığı, don alarmı)", 1600, 5),
        (0, 0, "2 zon debimetre + basınç", 400 * f, 5),
        (0, 0, "1 solar 4G PTZ AI kamera", 650, 5),
        (0, 0, "ÇKS, izinler, proje", 600, 5),
        (1, 1, "40' reefer konteyner (yenilenmiş) + kendi yapımın ön soğutma tüneli", 10000, 10),
        (1, 1, "Beton zemin + gölgelik (küçük)", 2000, 15),
        (1, 1, "Trifaze elektrik bağlantısı + pano", 3500, 15),
        (1, 1, "%35 gölge filesi + montaj", 3800 * f, 7),
        (1, 1, "NFC'li toplayıcı tartısı, 2 terazi, etiket yazıcı, hasat kasa/arabaları", 2100 * f ** 0.5, 5),
        (1, 1, "Gıda işletme kaydı + İyi Tarım + soğuk zincir logger'ları", 1300, 5),
        (2, 3, "10 kWp GES (soğuk oda elektriği)", 7500, 10),
        (2, 3, "Kamera katmanı: 3 SWD tuzak + 4 sıra kamerası + termal kamera", 2650, 4),
        (2, 3, "4 ek toprak düğümü + RCA deneme sıraları", 2620, 5),
        (3, 4, "Şok dondurucu + 2. reefer (-20 °C): IQF kanalı", 22500, 9),
    ]
    out = []
    for ph, y, k, v, life in items:
        cont = v * 0.08
        out.append((ph, y, k, v + cont, life))
    return out


OPTIONS = [
    ("Pakethane: top-seal makinesi + 30 m² hijyenik oda (kendi markanla raf)", 14500, "Ortak kendi markanı isterse / 2030+"),
    ("3 da yüksek tünel (sezon uzatma, fiyat primi)", 11000, "Pilot sonuçları iyiyse"),
    ("Liyofilize (fason ile başla)", 0, "Dondurucudan sonra, 2030+"),
    ("2. 10 da (bu planda yoksa)", 41000, "Ortak 2028'de hacim isterse 2029 dikimi"),
]


# ------------------------------------------------------------------ sabit giderler
def fixed(y, area=10):
    f = area / 10
    k = y - 1
    rows = {
        "Gübre + biyolojik/kimyasal mücadele": [1100, 2000, 2800, 3000, 3000][k] * f,
        "Budama, bağlama, ot (yevmiyeli; teknisyen yok)": [1300, 2300, 2900, 3000, 3000][k] * f,
        "DSİ su ücreti": [250, 400, 500, 500, 500][k] * f,
        "Kurucu ulaşımı (Ankara)": 3500,
        "Baba: yakıt/harcırah (maaş değil)": 800,
        "Sezonluk soğuk oda/etiket yardımcısı": [0, 1200, 1500, 1500, 1500][k] * f ** 0.5,
        "Daimi işçi (yalnız 20 da)": ([0, 9000, 9000, 9000, 9000][k] if area > 10 else 0),
        "Elektrik (2030'dan GES'le düşer; 2031 dondurucu)": [100, 1200, 1300, 700, 1100][k],
        "Bakım-onarım": [200, 700, 1000, 1300, 1500][k] * f ** 0.5,
        "Sigorta (TARSİM + tesis)": [0, 800, 1000, 1100, 1300][k] * f ** 0.7,
        "Bulut/SIM/yazılım": 300,
        "Gıda güvenliği denetimi + kalıntı analizi": [0, 500, 500, 500, 500][k],
        "Arı kovanı": [0, 300, 300, 300, 300][k] * f,
        "Muhasebe + numune/marka": 700,
    }
    return rows


def run(area=10, credit=False):
    f = area / 10
    caps = capex_items(area)
    rows = []
    for y in range(1, 6):
        k = y - 1
        kg = YIELD[k] * 1000 * f
        second = kg * SECOND
        first = kg - second
        packed = first * PACK_SHARE[k]
        hal = first - packed
        iqf = second if y >= 5 else 0.0
        proc = second - iqf
        r_pack = packed * PACK_PRICE * (1 - PARTNER_COMM)
        rev = r_pack + hal * HAL_PRICE + proc * PROC_PRICE + iqf * IQF_PRICE
        var = (packed * (HARVEST_PACK + CLAMSHELL + LABEL_LABOR + DELIVERY)
               + hal * (HARVEST_BULK + HAL_COST) + proc * (HARVEST_BULK + PROC_COST)
               + iqf * (HARVEST_BULK + IQF_COST))
        fx = sum(fixed(y, area).values())
        ebitda = rev - var - fx
        dep = sum(v / life for ph, yy, _, v, life in caps if yy + 1 <= y < yy + 1 + life)
        stopaj = rev * STOPAJ
        capex = sum(v for ph, yy, _, v, _ in caps if yy == y)
        rows.append(dict(y=y, kg=kg, packed=packed, rev=rev, var=var, fixed=fx, ebitda=ebitda, dep=dep,
                         ebt=ebitda - dep, stopaj=stopaj, net=ebitda - dep - stopaj, capex=capex,
                         cash=ebitda - stopaj - capex))
    c0 = sum(v for ph, yy, _, v, _ in caps if yy == 0)
    flows = [-c0] + [r["cash"] for r in rows]
    debt_left = 0.0
    if credit:   # Faz 0 + Faz 1'in %50'si Ziraat Hazine destekli kredi
        flows = list(flows)
        for dy, amt in ((0, c0 * 0.5), (1, sum(v for ph, yy, _, v, _ in caps if yy == 1) * 0.5)):
            flows[dy] += amt
            for yy, (i, p) in v2.loan_schedule(amt, dy).items():
                if yy <= 5:
                    flows[yy] -= i + p
                else:
                    debt_left += p
    nbv5 = sum(v * max(0, (yy + life - 5)) / life for ph, yy, _, v, life in caps)
    return dict(rows=rows, flows=flows, c0=c0, caps=caps, debt_left=debt_left, nbv5=nbv5)


def cum(flows):
    c, out = 0, []
    for v in flows:
        c += v; out.append(c)
    return out


def md_capex(area=10):
    caps = capex_items(area)
    out = ["| Faz | Ne zaman | Kalem | USD (%8 payla) | TL |", "|---|---|---|---:|---:|"]
    when = {0: "Q4-2026 / Q1-2027", 1: "2027 sonu (2028 hasadından önce)", 3: "2029 sonu (2029 kârından)", 4: "2030 sonu (2030 kârından)"}
    for ph, y, k, v, _ in caps:
        out.append(f"| {ph} | {when[y]} | {k} | {fmt(v)} | {fmt(v*FX)} |")
    for ph in range(4):
        s = sum(v for p, _, _, v, _ in caps if p == ph)
        out.append(f"| **{ph}** | | **Faz {ph} toplamı** | **{fmt(s)}** | **{fmt(s*FX)}** |")
    tot = sum(v for *_, v, _ in caps)
    out.append(f"| | | **5 yıl toplam yatırım** | **{fmt(tot)}** | **{fmt(tot*FX)}** |")
    return "\n".join(out)


def md_pnl(area=10):
    r = run(area)
    R = r["rows"]
    out = ["| USD | " + " | ".join(LABEL[x["y"]] for x in R) + " | 5 yıl |", "|---|" + "---:|" * 6]
    def line(lab, key, bold=False, neg=False, d=0):
        vals = [(-x[key] if neg else x[key]) for x in R]
        tot = sum(vals) if key != "kg" else sum(vals)
        cells = [fmt(v / 1000, 1) if key == "kg" else fmt(v) for v in vals] + [fmt(tot / 1000, 1) if key == "kg" else fmt(tot)]
        if bold:
            cells = [f"**{c}**" for c in cells]; lab = f"**{lab}**"
        out.append(f"| {lab} | " + " | ".join(cells) + " |")
    line("Rekolte (t)", "kg")
    line("Gelir (ortak komisyonu düşülmüş)", "rev", bold=True)
    line("Değişken gider (hasat, kap, teslimat, kanal)", "var", neg=True)
    line("Sabit gider", "fixed", neg=True)
    line("FAVÖK", "ebitda", bold=True)
    line("Amortisman", "dep", neg=True)
    line("Vergi öncesi kâr", "ebt", bold=True)
    line("Stopaj (%2)", "stopaj", neg=True)
    line("Net kâr", "net", bold=True)
    line("Yatırım (kârdan eklenen fazlar)", "capex", neg=True)
    c = cum(r["flows"])
    out.append("| **Kümülatif nakit (Y0 dahil)** | " + " | ".join(f"**{fmt(v)}**" for v in c[1:]) + " | |")
    return "\n".join(out), c


def summary(area=10):
    r = run(area); c = cum(r["flows"])
    rc = run(area, credit=True); cc = cum(rc["flows"])
    return dict(c0=r["c0"], peak=-min(c), peak_credit=-min(cc), end5=c[-1], end5_credit=cc[-1],
                debt_left=rc["debt_left"], nbv5=r["nbv5"], y5_rev=r["rows"][4]["rev"],
                net5=sum(x["net"] for x in r["rows"]), y5_net=r["rows"][4]["net"], y5_ebitda=r["rows"][4]["ebitda"],
                capex5=sum(v for *_, v, _ in r["caps"]), irr10=None)


if __name__ == "__main__":
    for a in (10, 20):
        print(f"\n===== {a} da")
        print(md_capex(a)); print()
        t, c = md_pnl(a); print(t); print()
        s = summary(a); print({k: (round(v) if isinstance(v, float) else v) for k, v in s.items()})
        for x in run(a)["rows"]:
            print(x["y"], {k: round(v) for k, v in x.items() if k in ("rev", "var", "fixed", "ebitda")})
