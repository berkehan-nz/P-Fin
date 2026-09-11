"""ELLE VERI DUZELTMELERI — ``data/overrides.json``.

NEDEN VAR: EDGAR'dan gelen veri bazen eksik veya yanlis etiketli oluyor.
Ornegin sirket satis maliyetini ayri bir XBRL etiketiyle raporlamiyorsa brut
kar bos kaliyor ve sirket Asama 1'de HAKSIZ YERE eleniyor. Boyle bir durumu
duzeltmenin tek dogru yolu, degeri kaynagiyla birlikte kaydedip veri hattinin
girdisini duzeltmek; cikti tarafina (metrik, puan, kart) elle dokunmak degil.

TASARIM: duzeltme HAM DONEM VERISINE uygulanir, metrige degil. Boylece
duzeltilen brut kardan brut marj, 40 Kurali, kalite puani ve huni kararlari
kendiliginden yeniden hesaplanir. Bir metrigi dogrudan ezmek, ondan turetilen
on beş sayiyi tutarsiz birakirdi.

Her kayit KAYNAK ISTER (``source_url`` + ``reason``). Kaynaksiz bir sayi
"duzeltme" degil tahmindir; kartta hangi sayinin nereden geldigi belirsizlesir
ve sistemin tum denetlenebilirligi kaybolur.

Sema::

    {"overrides": [
      {"ticker": "YOU", "period_end": "latest", "field": "gross_profit",
       "value": 190.4, "reason": "10-Q s.4; satis maliyeti ayri etiketlenmemis",
       "source_url": "https://www.sec.gov/Archives/...",
       "author": "claude", "added_at": "2026-09-11"}
    ]}

``period_end`` ya bir ISO tarih ("2026-06-30") ya da "latest" olabilir;
"latest" en guncel ceyregi (yoksa en guncel yili) hedefler.
"""

from __future__ import annotations

from .config import DATA_DIR
from .fundamentals import FLOW_FIELDS, STOCK_FIELDS, Fundamentals, Period
from .util import num, read_json

OVERRIDES_PATH = DATA_DIR / "overrides.json"

# Yalnizca HAM donem alanlari duzeltilebilir. Turetilmis alanlar (fcf,
# financial_debt, computed_gross_profit) ozellik olarak hesaplanir; onlari
# ezmek girdiyle ciktiyi celiskiye dusururdu.
OVERRIDABLE_FIELDS = frozenset(STOCK_FIELDS) | frozenset(FLOW_FIELDS)

REQUIRED_KEYS = ("ticker", "period_end", "field", "value", "reason", "source_url")


def validate_entry(entry) -> list[str]:
    """Tek bir duzeltme kaydini denetler; sorun listesi doner."""
    problems: list[str] = []
    if not isinstance(entry, dict):
        return ["Duzeltme kaydi bir JSON nesnesi olmali"]

    for key in REQUIRED_KEYS:
        if not entry.get(key) and entry.get(key) != 0:
            problems.append(f"'{key}' zorunlu")

    field_name = entry.get("field")
    if field_name and field_name not in OVERRIDABLE_FIELDS:
        problems.append(
            f"'{field_name}' duzeltilebilir bir ham alan degil. "
            f"Yalnizca donem verisi duzeltilebilir; metrikler ve puanlar "
            f"bu ham veriden yeniden hesaplanir.")

    if "value" in entry and entry["value"] is not None and num(entry["value"]) is None:
        problems.append("'value' sayi olmali (veya null — alani bosaltmak icin)")

    url = str(entry.get("source_url") or "")
    if url and not url.startswith(("http://", "https://")):
        problems.append("'source_url' bir http(s) adresi olmali")

    return problems


def load(path=None) -> list[dict]:
    """Gecerli duzeltme kayitlarini doner. Bozuk kayitlar SESSIZCE ATILMAZ —
    ``validate()`` ile CI'da yakalanir; burada yalnizca gecerliler uygulanir."""
    payload = read_json(path or OVERRIDES_PATH)
    if not isinstance(payload, dict):
        return []
    entries = payload.get("overrides")
    if not isinstance(entries, list):
        return []
    return [e for e in entries if isinstance(e, dict) and not validate_entry(e)]


def validate_all(path=None) -> list[str]:
    """Dosyanin tamamini denetler — CI bunu kullanir."""
    payload = read_json(path or OVERRIDES_PATH)
    if payload is None:
        return []
    if not isinstance(payload, dict):
        return ["overrides.json bir JSON nesnesi olmali"]
    entries = payload.get("overrides", [])
    if not isinstance(entries, list):
        return ["overrides.json icindeki 'overrides' bir dizi olmali"]

    problems: list[str] = []
    for i, entry in enumerate(entries):
        for p in validate_entry(entry):
            label = (entry.get("ticker", "?") if isinstance(entry, dict) else "?")
            problems.append(f"overrides[{i}] ({label}): {p}")
    return problems


def _target_period(f: Fundamentals, period_end: str) -> Period | None:
    if str(period_end).lower() == "latest":
        return f.latest_period()
    for p in list(f.quarters) + list(f.annuals):
        if p.period_end == period_end:
            return p
    return None


def apply(f: Fundamentals, entries: list[dict] | None = None) -> list[dict]:
    """Duzeltmeleri ``f`` uzerine uygular; UYGULANANLARIN listesini doner.

    Doner deger karta yazilir: okuyan kisi hangi sayinin elle duzeltildigini,
    neden ve hangi kaynakla duzeltildigini gormeli.
    """
    entries = load() if entries is None else entries
    applied: list[dict] = []

    for entry in entries:
        if str(entry.get("ticker", "")).upper() != f.ticker.upper():
            continue
        period = _target_period(f, entry["period_end"])
        if period is None:
            continue

        field_name = entry["field"]
        before = getattr(period, field_name, None)
        value = entry["value"]
        setattr(period, field_name, None if value is None else float(value))

        applied.append({
            "field": field_name,
            "period_end": period.period_end,
            "before": num(before),
            "after": num(value),
            "reason": entry["reason"],
            "source_url": entry["source_url"],
            "author": entry.get("author", "claude"),
            "added_at": entry.get("added_at"),
        })

    return applied
