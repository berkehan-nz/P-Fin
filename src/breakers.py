"""TEZ KIRICILARI — makine tarafindan degerlendirilir.

Onceki surumde ``portfolio.py`` yalnizca elle ``triggered: true`` yapilmis
kiricilari rapor ediyordu. Yani "brut marj iki ceyrek ust uste %70 altina
inerse cik" kurali kagit uzerinde duruyor, hicbir sey kendiliginden
tetiklenmiyordu. Karar anini insanin fark etmesine birakmak, sistemin
varlik sebebine aykiri.

UC KATMAN, bilerek farkli siddette:

  thesis              Tezin dayandigi SAYI bozuldu. Yapisal; cikilir.
  catastrophic_price  Fiyat girise gore %30 dustu. OTOMATIK SATIS DEGIL —
                      zorunlu yeniden degerlendirme. Duserken satmak tezin
                      yanlis oldugunu degil, paniklendigimizi gosterir.
  take_profit         Hedef fiyata ulasildi. Yarisini sat.

Portfoy seviyesinde ayrica: zirveden %20 dusus -> motor dilimine ekleme dur.

YAPILANDIRILMIS KIRICI:

    {"metric": "gross_margin", "op": "<", "value": 70.0,
     "consecutive_quarters": 2,
     "description": "Brut marj iki ceyrek ust uste %70 altina inerse"}

Metrik eslesmesi yapilamayan serbest metin kiricilar SILINMEZ; ``manual``
olarak isaretlenir ve panoda "elle kontrol" rozetiyle durur. Sessizce
dusurmek, kullanicinin yazdigi kurali yok saymak olurdu.
"""

from __future__ import annotations

from . import config
from .util import num, today_iso

OPS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}


# --------------------------------------------------------------------------
# Yapilandirilmis kirici
# --------------------------------------------------------------------------
def is_structured(breaker) -> bool:
    """Makinenin degerlendirebilecegi bicimde mi?"""
    if not isinstance(breaker, dict):
        return False
    return (bool(breaker.get("metric"))
            and breaker.get("op") in OPS
            and num(breaker.get("value")) is not None)


def normalize(breaker) -> dict:
    """Her kiriciyi ayni sozluk bicimine getirir.

    Serbest metin ("Rakip X pazar payi alirsa") makine tarafindan
    degerlendirilemez ama ATILMAZ: ``manual: True`` ile durur.
    """
    if isinstance(breaker, str):
        return {"description": breaker, "manual": True, "triggered": False}
    if not isinstance(breaker, dict):
        return {"description": str(breaker), "manual": True, "triggered": False}

    out = dict(breaker)
    out.setdefault("description", "")
    if not is_structured(out):
        # Makine degerlendiremiyor — ama ELLE tetiklenebilir. Kullanici
        # (ya da MCP uzerinden Claude) "triggered: true" yazdiysa bu bir
        # karardir ve aynen gecerlidir. Makine degerlendirmesi EKLENDI,
        # elle tetikleme KALDIRILMADI.
        out["manual"] = True
        out["triggered"] = bool(out.get("triggered"))
        out.setdefault("kind", "thesis")
        return out

    out["manual"] = False
    out.setdefault("consecutive_quarters",
                   config.BREAKERS["default_consecutive_quarters"])
    out.setdefault("kind", "thesis")
    return out


def _series_for(card: dict, metric: str) -> list:
    """Kartin ceyreklik serisinden metrigin son degerlerini alir (yeni -> eski)."""
    series = (card or {}).get("series") or {}
    raw = series.get(metric) or series.get(f"{metric}_quarterly") or []
    vals = []
    for item in raw:
        # Seriler ya duz sayi ya (tarih, deger) ciftidir.
        v = num(item[1]) if isinstance(item, (list, tuple)) and len(item) == 2 else num(item)
        if v is not None:
            vals.append(v)
    return list(reversed(vals))


def _current(card: dict, metric: str):
    cell = ((card or {}).get("metrics") or {}).get(metric)
    if isinstance(cell, dict):
        return num(cell.get("value"))
    return num(cell)


def evaluate_one(breaker: dict, card: dict) -> dict:
    """Tek bir kiriciyi karta gore degerlendirir; kopyasini doner.

    ``consecutive_quarters`` > 1 ise seri gerekir. Seri yoksa TETIKLEMEZ ve
    sebebini yazar: veri yoklugunda alarm uretmek, guvenilmez alarm demektir
    ve bir sure sonra hepsi gormezden gelinir.
    """
    b = normalize(breaker)
    if b.get("manual"):
        return b

    metric = b["metric"]
    op = OPS[b["op"]]
    threshold = num(b["value"])
    need = int(b.get("consecutive_quarters") or 1)

    current = _current(card, metric)
    b["current_value"] = current

    if current is None:
        b["triggered"] = False
        b["status"] = "veri_yok"
        b["note"] = f"{metric} hesaplanamadi — kirici degerlendirilemedi"
        return b

    if need <= 1:
        hit = op(current, threshold)
        b["triggered"] = bool(hit)
        b["status"] = "tetiklendi" if hit else "saglam"
        if hit:
            b["triggered_at"] = b.get("triggered_at") or today_iso()
        return b

    series = _series_for(card, metric)
    if len(series) < need:
        # Guncel deger esigi asiyorsa bile, "ust uste N ceyrek" kurali
        # dogrulanamiyor. Yari bilgiyle alarm calmiyoruz.
        b["triggered"] = False
        b["status"] = "veri_yok"
        b["note"] = (f"{need} ceyreklik seri yok ({len(series)} deger) — "
                     f"guncel deger {current}")
        return b

    son = series[:need]
    hit = all(op(v, threshold) for v in son)
    b["triggered"] = bool(hit)
    b["status"] = "tetiklendi" if hit else "saglam"
    b["checked_quarters"] = son
    if hit:
        b["triggered_at"] = b.get("triggered_at") or today_iso()
    return b


# --------------------------------------------------------------------------
# Fiyat katmanlari
# --------------------------------------------------------------------------
def price_breakers(position: dict, price: float | None) -> list[dict]:
    """Girise gore cokus ve hedef fiyat katmanlari.

    Bunlar karttan degil POZISYONDAN turer: ayni sirket iki farkli fiyattan
    alinmissa esikleri de farklidir.
    """
    out: list[dict] = []
    entry = num(position.get("entry_price"))
    if price is None or entry is None or entry <= 0:
        return out

    change_pct = (price / entry - 1) * 100
    limit = config.BREAKERS["catastrophic_price_pct"]
    lvl = config.BREAKERS["levels"]["catastrophic_price"]
    hit = change_pct <= limit
    out.append({
        "kind": "catastrophic_price",
        "description": f"Giris fiyatina gore %{limit:.0f} dusus",
        "current_value": round(change_pct, 2),
        "value": limit,
        "triggered": hit,
        "status": "tetiklendi" if hit else "saglam",
        "level": lvl["level"],
        "action": lvl["action"],
        "manual": False,
        **({"triggered_at": today_iso()} if hit else {}),
    })

    target = num(position.get("target_price"))
    if target and target > 0:
        lvl2 = config.BREAKERS["levels"]["take_profit"]
        hit2 = price >= target
        out.append({
            "kind": "take_profit",
            "description": f"Hedef fiyat {target:g} USD",
            "current_value": round(price, 2),
            "value": target,
            "triggered": hit2,
            "status": "tetiklendi" if hit2 else "saglam",
            "level": lvl2["level"],
            "action": lvl2["action"],
            "manual": False,
            **({"triggered_at": today_iso()} if hit2 else {}),
        })
    return out


def evaluate_position(position: dict, card: dict | None,
                      price: float | None) -> list[dict]:
    """Bir pozisyonun TUM kiricilarini degerlendirir.

    Kaynak iki yerde olabilir: pozisyonun kendi ``thesis_breakers`` listesi
    ve kartin ``story.thesis_breakers`` listesi. Ikisi de ayni semayi
    kullanir; pozisyondaki daha ozeldir, once gelir.
    """
    card = card or {}
    lvl = config.BREAKERS["levels"]["thesis"]

    raw = list(position.get("thesis_breakers") or [])
    story = ((card.get("story") or {}).get("thesis_breakers")) or []
    raw.extend(story)

    out = []
    seen = set()
    for b in raw:
        ev = evaluate_one(b, card)
        key = (ev.get("metric"), ev.get("op"), ev.get("value"),
               ev.get("description"))
        if key in seen:
            continue
        seen.add(key)
        ev.setdefault("kind", "thesis")
        ev.setdefault("level", lvl["level"])
        ev.setdefault("action", lvl["action"])
        out.append(ev)

    out.extend(price_breakers(position, price))
    return out


def portfolio_drawdown(summary: dict, peak_value: float | None) -> dict | None:
    """Zirveden dusus — motor dilimine ekleme durdurma uyarisi."""
    value = num(summary.get("portfolio_value_usd"))
    peak = num(peak_value)
    if value is None or peak is None or peak <= 0:
        return None
    dd = (value / peak - 1) * 100
    limit = config.BREAKERS["portfolio_drawdown_pct"]
    if dd > limit:
        return None
    lvl = config.BREAKERS["levels"]["portfolio_drawdown"]
    return {
        "kind": "portfolio_drawdown",
        "description": f"Portfoy zirveden %{dd:.1f} asagida "
                       f"(esik %{limit:.0f})",
        "current_value": round(dd, 2),
        "value": limit,
        "triggered": True,
        "level": lvl["level"],
        "action": lvl["action"],
        "triggered_at": today_iso(),
    }
