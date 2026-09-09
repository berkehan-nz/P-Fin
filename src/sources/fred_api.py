"""FRED — makro seriler (10 yillik tahvil, TUFE, issizlik, sanayi uretimi).

Anahtar yoksa bos doner. Makro veri dashboard'un ust seridinde baglam olarak
gosterilir; huniye veya puanlamaya girmez.
"""

from __future__ import annotations

from datetime import date, timedelta

from .. import config
from ..util import http_get, num


def enabled() -> bool:
    return bool(config.FRED_API_KEY)


def series(series_id: str, *, days: int = 800) -> list[tuple[str, float]]:
    if not enabled():
        return []
    try:
        resp = http_get(config.FRED_URL, params={
            "series_id": series_id,
            "api_key": config.FRED_API_KEY,
            "file_type": "json",
            "observation_start": (date.today() - timedelta(days=days)).isoformat(),
        })
        obs = resp.json().get("observations", [])
    except Exception as exc:  # noqa: BLE001
        print(f"  [uyari] fred {series_id}: {exc}")
        return []

    out = []
    for o in obs:
        v = num(o.get("value"))
        if v is not None:
            out.append((o.get("date", ""), v))
    return out


def _yoy_pct(points: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Seviye serisini yillik yuzde degisime cevirir (TUFE, sanayi uretimi)."""
    by_date = dict(points)
    out = []
    for d, v in points:
        try:
            y, m, rest = d.split("-")
            prior = f"{int(y) - 1}-{m}-{rest}"
        except ValueError:
            continue
        pv = by_date.get(prior)
        if pv and pv != 0:
            out.append((d, (v / pv - 1) * 100))
    return out


def snapshot() -> dict:
    """Dashboard makro seridi icin ozet."""
    out: dict[str, dict] = {}
    for key, spec in config.FRED_SERIES.items():
        points = series(spec["id"])
        if spec.get("transform") == "yoy_pct":
            points = _yoy_pct(points)
        if not points:
            out[key] = {"label": spec["label"], "unit": spec["unit"],
                        "value": None, "date": None, "change_3m": None}
            continue

        last_date, last_value = points[-1]
        prior = points[-63] if len(points) > 63 else points[0]
        out[key] = {
            "label": spec["label"],
            "unit": spec["unit"],
            "value": round(last_value, 2),
            "date": last_date,
            "change_3m": round(last_value - prior[1], 2),
            "series": [(d, round(v, 3)) for d, v in points[-260:]],
        }
    return out
