"""Veri makullugu denetimi.

FELSEFE: bu bir yatirim araci. Sessizce YANLIS bir sayi, acikca EKSIK bir
sayidan cok daha tehlikelidir. XBRL etiketleri sirketten sirkete degisir;
bir etiket kacinca hesap zinciri sacma ama makul GORUNEN degerler uretebilir.

Bu modul kartlari yayimlanmadan once tarar, imkansiz ya da cok supheli
degerleri isaretler ve gerektiginde degeri None'a cevirir. Amac hatayi
gizlemek degil, GORUNUR kilmak.
"""

from __future__ import annotations

from .util import num

# Bir metrigi gecersiz sayacak sinirlar (fiziksel/muhasebe olarak imkansiz
# ya da neredeyse kesin ayristirma hatasi olan degerler)
IMPOSSIBLE = {
    # Brut marj NEGATIF OLABILIR (maliyetin altina satan sirket). Silmek
    # gercek veriyi yok eder. Yalnizca muhasebe olarak imkansiz olani sil:
    # %100 ustu (satis maliyeti negatif demek) ya da -%100 alti.
    "gross_margin": (-100.0, 100.0),
    "operating_margin": (-500.0, 100.0),
    "fcf_margin": (-500.0, 200.0),
    "current_ratio": (0.0, 100.0),
    "piotroski_f": (0.0, 9.0),
}

# Bu araligin disi "imkansiz degil ama supheli" — deger korunur, uyari yazilir
SUSPICIOUS = {
    # Negatif brut marj gercek olabilir ama nadirdir; dogrulanmadan
    # kullanilmamali (LYFT'te yanlis etiket eslesmesinden dogmustu).
    "gross_margin": (0.0, 95.0),
    "rev_growth_ttm": (-60.0, 200.0),
    "rev_cagr_3y": (-50.0, 150.0),
    "roic": (-200.0, 300.0),
    "ev_ebit": (0.0, 500.0),
    "ev_sales": (0.0, 100.0),
}


def check(card: dict) -> dict:
    """Karti denetler; ``data_quality`` blogu ve ek uyarilar dondurur.

    Kart YERINDE degistirilir: imkansiz metrikler None'a cevrilir ve rengi
    griye doner.
    """
    issues: list[dict] = []
    metrics = card.get("metrics") or {}
    ttm = card.get("ttm") or {}

    price = num(card.get("price"))
    mcap = num(card.get("market_cap_musd"))
    ev = num(card.get("enterprise_value_musd"))
    shares = num(card.get("shares_outstanding_m"))
    ebit = num(ttm.get("ebit_musd"))
    revenue = num(ttm.get("revenue_musd"))

    # --- degerleme kurulabildi mi ---
    if price is None:
        issues.append(_issue("high", "fiyat_yok",
                             "Fiyat alinamadi — tum degerleme metrikleri bos."))
    if shares is None:
        issues.append(_issue("high", "hisse_sayisi_yok",
                             "Hisse sayisi bulunamadi; piyasa degeri ve EV "
                             "hesaplanamiyor. Cok sinifli hisse olabilir."))
    elif mcap is None:
        issues.append(_issue("high", "piyasa_degeri_yok",
                             "Piyasa degeri hesaplanamadi."))

    # --- EV negatif ama sirket kar ediyor: neredeyse kesin hisse sayisi hatasi ---
    if ev is not None and ev < 0 and (ebit or 0) > 0:
        issues.append(_issue(
            "high", "ev_negatif",
            f"Isletme degeri negatif ({ev:,.0f}M USD) ama sirket faaliyet kari "
            f"uretiyor. Bu genellikle hisse sayisinin eksik yakalandigini "
            f"gosterir (cok sinifli hisse). Degerleme carpanlarina guvenme."))

    # --- TTM buyuklukleri tutarli mi ---
    if revenue is None and ebit is not None:
        issues.append(_issue("high", "hasilat_yok",
                             "TTM hasilat hesaplanamadi ama FVOK var — hasilat "
                             "etiketi eslesmemis olabilir. Marj ve buyume bos."))
    if revenue is not None and revenue <= 0:
        issues.append(_issue("high", "hasilat_sifir", "TTM hasilat sifir veya negatif."))

    gross = num(ttm.get("gross_profit_musd"))
    if gross is None and revenue is not None:
        issues.append(_issue(
            "medium", "brut_kar_yok",
            "Brut kar hesaplanamadi (satis maliyeti etiketi yok). Brut marj "
            "Asama 1'de sert filtredir — bu sirket haksiz yere elenebilir."))

    # --- hisse sayisi kaynagi ---
    source = (card.get("data_sources") or {}).get("shares")
    if source and source != "kapak_sayfasi":
        issues.append(_issue(
            "low", "hisse_sayisi_tahmini",
            f"Hisse sayisi kapak sayfasindan degil, {source} uzerinden bulundu."))

    # --- imkansiz metrikleri temizle ---
    for key, (lo, hi) in IMPOSSIBLE.items():
        cell = metrics.get(key)
        v = num(cell.get("value")) if isinstance(cell, dict) else None
        if v is None:
            continue
        if not (lo <= v <= hi):
            issues.append(_issue(
                "high", f"gecersiz_{key}",
                f"{key} = {v:,.2f} kabul araliginin ({lo:g}, {hi:g}) disinda; "
                f"ayristirma hatasi. Deger silindi."))
            cell["value"] = None
            cell["color"] = "gray"

    # --- supheli ama silinmeyen degerler ---
    for key, (lo, hi) in SUSPICIOUS.items():
        cell = metrics.get(key)
        v = num(cell.get("value")) if isinstance(cell, dict) else None
        if v is not None and not (lo <= v <= hi):
            issues.append(_issue("medium", f"supheli_{key}",
                                 f"{key} = {v:,.2f} olagandisi; dogrulamadan kullanma."))

    # --- ceyreklik seride bosluk var mi ---
    series = card.get("series") or {}
    rev_series = series.get("revenue") or []
    if rev_series:
        missing = sum(1 for v in rev_series[-4:] if v is None)
        if missing:
            issues.append(_issue(
                "medium", "ceyrek_bosluklu",
                f"Son 4 ceyregin {missing} tanesinde hasilat yok. TTM degerleri "
                f"yillik tabloya dusmus olabilir."))

    # --- ceyreklik seri ile TTM tutarli mi ---
    fcf_series = [v for v in (series.get("fcf") or [])[-4:] if v is not None]
    ttm_fcf = num(ttm.get("fcf_musd"))
    if len(fcf_series) == 4 and ttm_fcf not in (None, 0):
        sapma = abs(sum(fcf_series) - ttm_fcf) / max(abs(ttm_fcf), 1) * 100
        if sapma > 5:
            basis = (card.get("flags") or {}).get("data_basis")
            issues.append(_issue(
                "medium", "ttm_seri_uyusmazligi",
                f"Son 4 ceyregin nakit akisi toplami ({sum(fcf_series):,.0f}M) ile "
                f"TTM degeri ({ttm_fcf:,.0f}M) %{sapma:.0f} farkli"
                + (" — bazi kalemler yillik tablodan geldigi icin bu beklenen bir "
                   "durum, ama grafikle TTM ayni sayiyi gostermez."
                   if basis == "mixed" else
                   ". Ceyreklik grafikle TTM ayni donemi anlatmiyor olabilir.")))

    levels = [i["level"] for i in issues]
    status = ("kotu" if "high" in levels
              else "sinirli" if "medium" in levels
              else "iyi")

    card["data_quality"] = {
        "status": status,
        "issue_count": len(issues),
        "issues": issues,
    }

    # Yuksek onemli sorunlari kart uyarilarina da tasi
    flags = card.setdefault("flags", {})
    warnings = list(flags.get("warnings") or [])
    for i in issues:
        if i["level"] == "high":
            warnings.append(f"VERI KALITESI: {i['message']}")
    flags["warnings"] = _dedupe(warnings)

    return card["data_quality"]


def _issue(level: str, code: str, message: str) -> dict:
    return {"level": level, "code": code, "message": message}


def _dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for i in items:
        if i and i not in seen:
            seen.add(i)
            out.append(i)
    return out


def summarize(cards: list[dict]) -> dict:
    """Tum kartlarin veri kalitesi ozeti — kosu sonunda yazdirilir."""
    counts = {"iyi": 0, "sinirli": 0, "kotu": 0}
    by_code: dict[str, int] = {}
    for c in cards:
        dq = c.get("data_quality") or {}
        counts[dq.get("status", "iyi")] = counts.get(dq.get("status", "iyi"), 0) + 1
        for i in dq.get("issues", []):
            by_code[i["code"]] = by_code.get(i["code"], 0) + 1
    return {"counts": counts,
            "top_issues": dict(sorted(by_code.items(), key=lambda kv: kv[1],
                                      reverse=True)[:15])}
