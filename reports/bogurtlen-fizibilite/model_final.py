"""SON HÂL — 10 da böğürtlen + kendin-topla, hibrit fidan, dengeli teknoloji paketi, Ekim 2026 TL fiyatları.

    python reports/bogurtlen-fizibilite/model_final.py            # özet
    python reports/bogurtlen-fizibilite/model_final.py --tables   # rapor tabloları

Gelir/gider varsayımları model_v8'den; yatırım listesi doğrulanmış fiyatlarla yeniden kuruldu.
"""
from __future__ import annotations

import sys

import model_v8 as v8

fmt, mtl, pct, FX = v8.fmt, v8.mtl, v8.pct, v8.FX
CONT = 0.08

# (faz, yıl sonu, grup, kalem, miktar, TL, ömür, fiyat dayanağı)  D = doğrulandı, T = tahmin
CAPEX = [
    (0, 0, "Arazi", "Dip kazan + diskaro + sedde (40 cm); lazer tesviye yok", "10 da", 60000, 10, "T"),
    (0, 0, "Arazi", "Yanmış çiftlik gübresi ~3 t/da, temin + serme (~45 m³ × 1.771 TL)", "45 m³", 80000, 10, "D"),
    (0, 0, "Arazi", "Siyah PE malç 1,2 m (500 m rulo 1.450-2.220 TL) + serme", "7 rulo", 20000, 3, "D"),
    (0, 0, "Fidan", "Doku kültürü fidan, viyolde (216'lık viyol ~5.300 TL) + 2-3 ay saksıda alıştırma", "3.171 ad × 46 TL", 3171 * 46, 10, "D"),
    (0, 0, "Fidan", "2 yaşlı tüplü fidan, hızlı blok (%30; tek tek 250 TL, toplu teklif)", "1.359 ad × 150 TL", 1359 * 150, 10, "T"),
    (0, 0, "Fidan", "Dikim işçiliği (~18 yevmiye)", "", 25000, 10, "D"),
    (0, 0, "Telli sistem", "Galvaniz direk 2,7 m, 8 m ara + baş direkleri", "483 ad × 350 TL", 483 * 350, 10, "D"),
    (0, 0, "Telli sistem", "Galvaniz tel 3 kat (75 TL/kg) + gergi/ankraj + montaj", "~10.000 m", 110000, 10, "D"),
    (0, 0, "Sulama", "Damla sulama (9.000-12.000 TL/da) + hidrant bağlantısı, disk filtre, ana hat", "10 da", 160000, 10, "D"),
    (0, 0, "Teknoloji", "Fertigasyon: 3 × Hunter PGV 1\" selenoid (1.299 TL), venturi + bypass, ESP32 kontrolör + 24 VAC trafo", "3 zon", 12000, 5, "D/T"),
    (0, 0, "Teknoloji", "Hat içi EC probu (gübre suyu uzaktan izleme)", "1", 5000, 5, "T"),
    (0, 0, "Teknoloji", "Hanna HI98129 pH/EC/TDS el ölçer", "1", 13400, 5, "D"),
    (0, 0, "Teknoloji", "Toprak düğümü: 2 × RS485 nem/sıcaklık/EC probu (4.232 TL) + Heltec ESP32-LoRa + solar/akü/kutu", "3 × 12.000 TL", 36000, 5, "D"),
    (0, 0, "Teknoloji", "LoRaWAN gateway (Dragino, ~€160-245) + 4G modem", "1", 13000, 5, "D"),
    (0, 0, "Teknoloji", "Hava düğümü: sıcaklık/nem + yaprak ıslaklığı + yağmur ölçer + ESP32/solar", "1", 8000, 5, "D/T"),
    (0, 0, "Teknoloji", "Ana hat debimetresi (darbe çıkışlı)", "1", 4000, 5, "T"),
    (0, 0, "Teknoloji", "Raspberry Pi 5 + UPS + SSD (yerel sunucu, internet kesilse de çalışır)", "1", 12000, 4, "D/T"),
    (0, 0, "Teknoloji", "Solar 4G güvenlik kamerası (3.100-8.000 TL)", "1", 7000, 5, "D"),
    (0, 0, "Diğer", "ÇKS kaydı, tarımsal yapı bildirimi, küçük giderler", "", 15000, 5, "T"),
    (1, 1, "Soğuk zincir", "Soğuk oda: 100 mm panel ~32 m² (890-1.050 TL/m²) + kapı/profil/montaj", "~12 m³", 51000, 10, "D"),
    (1, 1, "Soğuk zincir", "24.000 BTU inverter klima (54-75 bin TL) + termostat kontrolü + ön soğutma fanı", "1", 70000, 7, "D"),
    (1, 1, "Soğuk zincir", "Elektrik bağlantısı (monofaze) + pano", "", 40000, 15, "T"),
    (1, 1, "Soğuk zincir", "Wi-Fi sıcaklık sensörü + Telegram alarmı + 2 logger", "", 5000, 5, "T"),
    (1, 1, "Kalite", "%35 gölge filesi (güney cephe + Chester sıraları, ~3.000 m² × ~35 TL) + montaj", "~3.000 m²", 125000, 7, "D/T"),
    (1, 1, "Hasat", "60 hasat kasası, 2 el arabası, terazi, etiket yazıcı", "", 30000, 5, "T"),
    (1, 1, "Hasat", "Gıda işletme kaydı (İyi Tarım ortak isterse sonra)", "", 10000, 5, "T"),
    (1, 1, "Kendin-topla", "Tabela, satış tezgâhı, gölgelik (WC kiralık)", "", 20000, 5, "T"),
]
REPLACE = [(6, "Elektronik yenileme", 60000, 5), (4, "PE malç yenileme", 20000, 3), (7, "PE malç yenileme", 20000, 3),
           (8, "Gölge filesi yenileme", 125000, 7), (8, "Klima yenileme", 70000, 7)]
HYBRID = [0.7 * a + 0.3 * b for a, b in zip(v8.TC, v8.POT)]


def items(_p=None):
    out = [(ph, y, g, k, q, v * (1 + CONT), life) for ph, y, g, k, q, v, life, _ in CAPEX]
    out += [(3, y, "Yenileme", k, "", v, life) for y, k, v, life in REPLACE]
    return out


def run(**kw):
    oi, oy = v8.items, list(v8.BB_YIELD)
    v8.items = items; v8.BB_YIELD[:] = HYBRID
    try:
        return v8.run("B", **kw), v8.summary("B", **kw)
    finally:
        v8.items = oi; v8.BB_YIELD[:] = oy


def steady(ton, price_mult=1.0):
    """Tam verim yılında (2031 koşulları) belirli rekolteyle net kâr."""
    oy = list(v8.BB_YIELD); oi = v8.items
    v8.items = items
    v8.BB_YIELD[:] = [x if i != 4 else ton / 10 for i, x in enumerate(HYBRID)]
    try:
        return v8.run("B", price_mult=price_mult)["rows"][4]
    finally:
        v8.BB_YIELD[:] = oy; v8.items = oi


# ------------------------------------------------------------------ tablolar
def md_capex():
    out = ["| Faz | Grup | Kalem | Miktar | TL | Fiyat |", "|---|---|---|---|---:|:---:|"]
    for ph, y, g, k, q, v, life, src in CAPEX:
        out.append(f"| {ph} | {g} | {k} | {q} | {fmt(v*(1+CONT))} | {src} |")
    groups = {}
    for ph, y, g, k, q, v, life, src in CAPEX:
        groups[g] = groups.get(g, 0) + v * (1 + CONT)
    tot = sum(groups.values())
    for ph, lab in ((0, "Faz 0 — dikimden önce (Kasım 2026 – Mart 2027)"), (1, "Faz 1 — 2027 içinde, ilk büyük hasattan önce")):
        s = sum(v for p, *_, v, _l, _s in CAPEX if p == ph) * (1 + CONT)
        out.append(f"| | | **{lab}** | | **{fmt(s)}** | |")
    out.append(f"| | | **TOPLAM BAŞLANGIÇ YATIRIMI** | | **{fmt(tot)}** | ≈ ${fmt(tot/FX)} |")
    out.append("\n*D: Ekim 2026 internet fiyatıyla doğrulandı · T: tahmin, teklif alınmalı · D/T: ana bileşen doğrulandı, kalan tahmin. Tutarlar %8 beklenmeyen gider payı dahil.*")
    return "\n".join(out), groups, tot


def md_groups():
    _, g, tot = md_capex()
    out = ["| Grup | TL | Pay |", "|---|---:|---:|"]
    for k, v in sorted(g.items(), key=lambda x: -x[1]):
        out.append(f"| {k} | {fmt(v)} | %{v/tot*100:.0f} |")
    out.append(f"| **Toplam** | **{fmt(tot)}** | |")
    return "\n".join(out)


def md_pnl5():
    r, s = run()
    R = r["rows"][:5]; c = v8.cum(r["flows"])
    out = ["| TL | 2027 | 2028 | 2029 | 2030 | 2031 | 5 yıl |", "|---|---:|---:|---:|---:|---:|---:|"]
    def line(lab, fn, bold=False, tot=True):
        vals = [fn(x) for x in R]
        cells = [fmt(v) for v in vals] + [fmt(sum(vals)) if tot else ""]
        if bold:
            cells = [f"**{c}**" if c else c for c in cells]; lab = f"**{lab}**"
        out.append(f"| {lab} | " + " | ".join(cells) + " |")
    out.append("| Rekolte (t) | " + " | ".join(fmt(x["bb_kg"] / 1000, 1) for x in R) + f" | {fmt(sum(x['bb_kg'] for x in R)/1000,1)} |")
    line("— Ortak üzerinden paketli", lambda x: x["r_pack"])
    line("— Kendin-topla", lambda x: x["r_up"])
    line("— Hal", lambda x: x["r_hal"])
    line("— 2. sınıf → işleme", lambda x: x["r_proc"])
    line("Gelir", lambda x: x["rev"], True)
    line("Değişken gider (hasat, kap, kanal)", lambda x: -x["var"])
    line("Sabit gider (OPEX)", lambda x: -x["fixed"])
    line("FAVÖK", lambda x: x["ebitda"], True)
    line("Amortisman", lambda x: -x["dep"])
    line("Stopaj (%2)", lambda x: -x["stopaj"])
    line("Net kâr", lambda x: x["net"], True)
    line("Aylık net kâr", lambda x: x["net"] / 12, tot=False)
    line("Yatırım (CAPEX) / yenileme", lambda x: -x["capex"])
    out.append("| **Kümülatif nakit (yatırım dahil)** | " + " | ".join(f"**{fmt(c[i])}**" for i in range(1, 6)) + " | |")
    return "\n".join(out), r, s


def md_opex():
    p = v8.PLANS["B"]
    out = ["| Sabit gider (TL/yıl) | 2027 | 2028 | 2029 | 2030 | 2031 |", "|---|---:|---:|---:|---:|---:|"]
    for k in v8.fixed(1, p):
        vals = [v8.fixed(y, p)[k] for y in range(1, 6)]
        if any(vals):
            out.append(f"| {k} | " + " | ".join(fmt(v) for v in vals) + " |")
    out.append("| **Toplam** | " + " | ".join(f"**{fmt(sum(v8.fixed(y, p).values()))}**" for y in range(1, 6)) + " |")
    return "\n".join(out)


def md_max():
    out = ["| Üretim düzeyi (tam verim) | t/da | Rekolte | Net kâr / yıl | Aylık | Fiyat −%30 ile net |", "|---|---:|---:|---:|---:|---:|"]
    for lab, t in (("Temkinli", 15), ("Baz (iyi yönetim)", 20), ("Çok iyi yönetim", 25), ("Üst sınır (açık tarla Chester/Loch Ness)", 28)):
        r = steady(t); r30 = steady(t, 0.7)
        out.append(f"| {lab} | {fmt(t/10,1)} | {t} t | {mtl(r['net'])} | {fmt(r['net']/12)} TL | {mtl(r30['net'])} |")
    return "\n".join(out)


def md_stress():
    out = ["| Senaryo | 2031 net | Geri dönüş | 10 yıl IRR |", "|---|---:|---:|---:|"]
    for lab, kw in [("Baz", {}), ("Tüm fiyatlar −%30", dict(price_mult=0.7)), ("Verim −%25", dict(yield_mult=0.75)),
                    ("İşçilik +%40", dict(labor_mult=1.4)), ("Ortak fiyatı 200 TL (hal düzeyi)", dict(partner_price=200)),
                    ("Fiyat −%30 + verim −%15 + işçilik +%20", dict(price_mult=0.7, yield_mult=0.85, labor_mult=1.2))]:
        r, s = run(**kw)
        out.append(f"| {lab} | {mtl(s['y5']['net'])} | {(fmt(s['pb'],1)+' yıl') if s['pb'] else 'dönmez'} | {pct(s['irr'])} |")
    return "\n".join(out)


if __name__ == "__main__":
    t, g, tot = md_capex()
    if "--tables" in sys.argv:
        print(t); print(); print(md_groups()); print(); print(md_opex()); print(); print(md_pnl5()[0]); print(); print(md_max()); print(); print(md_stress())
    else:
        r, s = run()
        print("toplam", round(tot), "tek", round(g["Teknoloji"]), "peak", round(s["peak"]), "pb", round(s["pb"], 2), "irr", pct(s["irr"]))
        print([round(x["net"]) for x in r["rows"]])
        print(md_max())
