"""Nöbetçi tetikleyici tipleri ve eşikleri (§3.1).

TASARIM KISITI: Nöbetçi, tetikleyicisi DEĞİŞTİRİLEBİLİR bağımsız bir modüldür.
Eşik/olay tanımları burada; izleme mantığı `sentinel.py`'de; onu ÇAĞIRAN zamanlayıcı
(bugün GitHub Actions cron, yarın VPS) dışarıdadır. Zamanlayıcı değişse KOD DEĞİŞMEZ —
yalnız `python -m pfin.cli sentinel-run`'ı çağıran yer değişir.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TriggerEvent:
    kind: str                         # stop_broken | sharp_move | abnormal_volume | kap
    symbol: str
    message: str
    severity: str = "warning"         # warning | critical
    dedupe_key: str = ""
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"kind": self.kind, "symbol": self.symbol, "message": self.message,
                "severity": self.severity}


@dataclass
class Thresholds:
    intraday_move_pct: float = 0.07   # ±%7
    abnormal_volume_mult: float = 3.0
    kap_lookback_hours: int = 24

    @classmethod
    def from_config(cls, config) -> "Thresholds":
        s = config.get("sentinel", default={}) or {}
        return cls(
            intraday_move_pct=float(s.get("intraday_move_pct", 0.07)),
            abnormal_volume_mult=float(s.get("abnormal_volume_mult", 3.0)),
            kap_lookback_hours=int(s.get("kap_lookback_hours", 24)),
        )
