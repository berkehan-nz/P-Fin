"""KART TUTARLILIK DENETIMI — panoda yanlis sayi gorunmesin.

Her karti KENDI icinde dogrular: kartta yazan TTM buyuklukleri ve isletme
degeriyle metrikleri yeniden hesaplar, saklanan degerle karsilastirir.
Boylece birim hatasi (oran mi yuzde mi), isaret hatasi, bayat turev deger ve
grafik-metrik celiskisi yakalanir.

NEDEN GEREKLI: metriklerin bir kismi gunluk kosuda fiyata gore tazelenir,
bir kismi tam yeniden uretimde hesaplanir. Ikisi arasinda bir alan unutulursa
(peg, ima edilen buyume) kart gunler icinde kendi icinde celisir ve bunu
kimse fark etmez. Bu betik CI'da calisir.

    python scripts/audit_cards.py
    python scripts/audit_cards.py --strict    # uyarilar da hata sayilir
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict


def _decimals(x: float) -> int:
    s = repr(float(x))
    return len(s.split(".")[1]) if "." in s else 0


class Audit:
    def __init__(self) -> None:
        self.errors: dict[str, list[str]] = defaultdict(list)
        self.notes: dict[str, list[str]] = defaultdict(list)

    def check(self, card, name, stored, expected, den=None):
        """Saklanan deger tanimdan hesaplanani tutuyor mu?

        IKI YONLU YUVARLAMA. Hem sonuc hem de GIRDILER gosterildikleri
        hassasiyette saklaniyor. Payda kucukse girdinin yuvarlanmasi sonucta
        buyuk GORELI fark yaratir: ConEd'in net kari 2,0 olarak saklaniyor,
        gercegi 2,02; F/K farki %1,1 cikiyor ama ortada hata yok. ``den``
        verilirse paydanin hassasiyetinden gelen belirsizlik tolere edilir.
        """
        if stored is None or expected is None:
            return
        if round(expected, _decimals(stored)) == stored:
            return

        tol = 0.005
        if den:
            # Girdinin son basamagi +-yarim birim oynayabilir.
            tol = max(tol, (0.5 * 10 ** -_decimals(den)) / abs(den))
        # Girdi ve cikti yuvarlamasi BIRLIKTE olusabilir: MQ'da EBIT -12,9
        # (gercegi -12,95'e kadar) -> -1,3079 -> kartta -1,31. Ikisini ayri
        # ayri tolere etmek bu durumu hata sayiyordu; belirsizlikler toplanir.
        if stored:
            tol += (0.5 * 10 ** -_decimals(stored)) / abs(stored)
        if abs(expected) > 1e-9 and abs(stored - expected) / abs(expected) <= tol:
            return
        self.errors[name].append(
            f"{card['ticker']}: kartta {stored:.6g}, tanimdan {expected:.6g}")

    def note(self, name, msg):
        self.notes[name].append(msg)


def val(card, key):
    cell = (card.get("metrics") or {}).get(key)
    return cell.get("value") if isinstance(cell, dict) else None


def audit_card(a: Audit, c: dict) -> None:
    t = c.get("ttm") or {}
    rev, ebit = t.get("revenue_musd"), t.get("ebit_musd")
    ebitda, fcf = t.get("ebitda_musd"), t.get("fcf_musd")
    gp, ni = t.get("gross_profit_musd"), t.get("net_income_musd")
    ev, mcap, nd = (c.get("enterprise_value_musd"), c.get("market_cap_musd"),
                    c.get("net_debt_musd"))

    if None not in (ev, mcap, nd):
        a.check(c, "EV = piyasa degeri + net borc", ev, mcap + nd)
    if nd is not None:
        a.check(c, "net_debt metrigi = net_debt_musd", val(c, "net_debt"), nd)

    if rev:
        for key, top in (("gross_margin", gp), ("operating_margin", ebit),
                         ("ebitda_margin", ebitda), ("fcf_margin", fcf)):
            a.check(c, f"{key} = kalem / hasilat", val(c, key),
                    (top / rev * 100) if top is not None else None, den=top)
    if ev:
        for key, den in (("ev_ebit", ebit), ("ev_ebitda", ebitda),
                         ("ev_sales", rev), ("ev_gross_profit", gp)):
            a.check(c, f"{key} = EV / kalem", val(c, key),
                    (ev / den) if den else None, den=den)
        # Pay da yuvarlanmis saklaniyor (EBIT 0,1 mn hassasiyetle); kucuk
        # EBIT'te bu tek basina %0,5'i asan goreli fark yaratir.
        a.check(c, "fcf_yield_ev = FCF / EV", val(c, "fcf_yield_ev"),
                (fcf / ev * 100) if fcf is not None else None, den=fcf)
        a.check(c, "earnings_yield = EBIT / EV", val(c, "earnings_yield"),
                (ebit / ev * 100) if ebit is not None else None, den=ebit)
    if mcap:
        a.check(c, "fcf_yield_mcap = FCF / piyasa degeri", val(c, "fcf_yield_mcap"),
                (fcf / mcap * 100) if fcf is not None else None)
        if ni and ni > 0:
            a.check(c, "pe = piyasa degeri / net kar", val(c, "pe"), mcap / ni, den=ni)

    g, fm, em = val(c, "rev_growth_ttm"), val(c, "fcf_margin"), val(c, "ebitda_margin")
    if g is not None and fm is not None:
        a.check(c, "rule_of_40 = buyume + FCF marji", val(c, "rule_of_40"), g + fm)
    if g is not None and em is not None:
        a.check(c, "rule_of_40_ebitda = buyume + FAVOK marji",
                val(c, "rule_of_40_ebitda"), g + em)
    if nd is not None and ebitda and ebitda > 0:
        a.check(c, "net_debt_to_ebitda = net borc / FAVOK",
                val(c, "net_debt_to_ebitda"), nd / ebitda, den=ebitda)

    # TUREV ALANLAR BAYAT MI? Gunluk kosu pe'yi tazeleyip peg'i unutursa
    # ikisi gunler icinde birbirinden kopar.
    pe = val(c, "pe")
    if pe is not None and g is not None and g > 0:
        a.check(c, "peg = F/K / buyume (bayat turev)", val(c, "peg"), pe / g, den=g)

    d = c.get("reverse_dcf") or {}
    if d.get("enterprise_value_musd") is not None and ev is not None:
        a.check(c, "ters DCF'teki EV = karttaki EV", d["enterprise_value_musd"], ev)
    if d.get("fcf_ttm_musd") is not None and fcf is not None:
        a.check(c, "ters DCF'teki FCF = TTM FCF", d["fcf_ttm_musd"], fcf)
    if d.get("implied_growth_pct") is not None:
        a.check(c, "implied_growth metrigi = ters DCF alani",
                val(c, "implied_growth"), d["implied_growth_pct"])

    # Net kar EBIT'e gore imkansiz kucukse kalem yanlis alinmistir.
    if ni is not None and ebit is not None and ebit > 50 and 0 < ni < ebit * 0.02:
        a.note("net kar EBIT'e gore imkansiz kucuk",
               f"{c['ticker']}: net kar {ni:,.1f}, EBIT {ebit:,.0f} "
               f"-> F/K {(mcap / ni):,.0f}" if mcap else f"{c['ticker']}")

    # --- puan yeniden hesabi ---
    th = json.load(open("data/thresholds.json", encoding="utf-8"))
    W = th["score_weights"]
    sc = c.get("scores") or {}
    cf = sc.get("coverage_factors") or {}
    acc = used = 0.0
    for k in ("value", "quality", "safety", "momentum", "earnings_quality"):
        if sc.get(k) is None:
            continue
        w = W[k] * cf.get(k, 1.0)
        acc += sc[k] * w
        used += w
    if sc.get("catalyst") is not None:
        acc += sc["catalyst"] * W["catalyst"]
        used += W["catalyst"]
    if used > 0:
        if sc.get("total") is not None:
            a.check(c, "toplam puan = agirlikli ortalama", sc["total"], acc / used)
        a.check(c, "weight_coverage", sc.get("weight_coverage"), used / sum(W.values()))

    # --- dusuk kapsama: HANGI alt metrikler bos ---
    for block, detail in (c.get("score_detail") or {}).items():
        if isinstance(detail, dict) and detail.get("low_coverage"):
            missing = [k for k, v in (detail.get("components") or {}).items()
                       if not isinstance(v, dict) or v.get("percentile") is None]
            a.note(f"dusuk kapsama ({block})",
                   f"{c['ticker']}: kapsama {detail.get('coverage')}, bos: {', '.join(missing)}")

    # --- grafik ile metrik ayni seyi mi soyluyor ---
    s = c.get("series") or {}
    if s.get("basis") != "annual":
        for field, label, ttm_value in (("revenue", "Satis", rev),
                                        ("fcf", "FCF", fcf)):
            q = [x for x in (s.get(field) or [])[-4:] if isinstance(x, (int, float))]
            if len(q) == 4 and ttm_value and abs(sum(q) - ttm_value) / abs(ttm_value) > 0.05:
                a.note("grafik-metrik celiskisi",
                       f"{c['ticker']}: {label} son4={sum(q):.0f} vs TTM={ttm_value:.0f}")
        gm = [x for x in (s.get("gross_margin") or []) if isinstance(x, (int, float))]
        if len(gm) >= 5:
            ordered = sorted(gm[:-1])
            median = ordered[len(ordered) // 2]
            if abs(gm[-1] - median) > 15:
                a.note("aykiri ceyrek (brut marj)",
                       f"{c['ticker']}: son ceyrek %{gm[-1]:.1f}, ortanca %{median:.1f}")

    spark = [x for x in (s.get("price_sparkline") or []) if isinstance(x, (int, float))]
    if spark and c.get("price") and abs(spark[-1] - c["price"]) / c["price"] > 0.05:
        a.note("fiyat grafigi guncel fiyattan uzak",
               f"{c['ticker']}: grafik {spark[-1]:.2f}, fiyat {c['price']:.2f}")


def audit_display(a: Audit) -> None:
    """Panoda gosterilen her metrigin anlatimi tam mi?"""
    th = json.load(open("data/thresholds.json", encoding="utf-8"))
    TH, blocks = th["thresholds"], th["metric_blocks"]
    shown = {k for arr in blocks.values() for k in arr}

    for key in sorted(shown):
        spec = TH.get(key)
        if not spec:
            a.errors["panoda gosterilen metrigin tanimi yok"].append(key)
            continue
        for field in ("label", "direction", "plain", "sentence"):
            if not spec.get(field):
                a.errors[f"metrik taniminda '{field}' eksik"].append(key)
        # Negatif deger alabilen yuzde metrikleri yon bilgisini kaybetmemeli
        if spec.get("unit") == "%" and not spec.get("sentence_neg"):
            sentence = spec.get("sentence", "")
            if not any(w in sentence for w in ("degisti", "farkli")):
                a.note("negatifte yonu belirsiz cumle", f"{key}: {sentence}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Kart tutarlilik denetimi")
    ap.add_argument("--strict", action="store_true", help="uyarilari da hata say")
    args = ap.parse_args()

    a = Audit()
    cards = []
    for path in sorted(glob.glob("data/cards/*.json")):
        with open(path, encoding="utf-8") as fh:
            c = json.load(fh)
        if isinstance(c, dict) and c.get("ticker"):
            cards.append(c)
            audit_card(a, c)
    audit_display(a)

    print(f"Denetlenen kart: {len(cards)}\n")

    for title, bucket in (("HATA", a.errors), ("INCELENMELI", a.notes)):
        if not bucket:
            continue
        print(f"--- {title} ---")
        for name, items in sorted(bucket.items(), key=lambda kv: -len(kv[1])):
            print(f"[{len(items):3}] {name}")
            for it in items[:5]:
                print(f"        {it}")
            if len(items) > 5:
                print(f"        ... {len(items) - 5} tane daha")
        print()

    if not a.errors and not a.notes:
        print("TEMIZ — tum kartlar kendi icinde tutarli.")
    if a.errors:
        return 1
    return 1 if (args.strict and a.notes) else 0


if __name__ == "__main__":
    sys.exit(main())
