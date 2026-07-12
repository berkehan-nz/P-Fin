"""config.yaml + ortam sırlarını (env / GitHub Secrets) yükler.

Sırlar koda gömülmez; yalnız ortamdan okunur. config.yaml sır içermez.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config.yaml"
STATE_PATH = REPO_ROOT / "state.json"


def _load_dotenv(path: Path) -> None:
    """.env varsa ortama yükler (lokal test kolaylığı). Actions'ta gerek yok."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


@dataclass(frozen=True)
class Secrets:
    """Ortamdan okunan sırlar. Eksik olması normaldir (özellik devre dışı kalır)."""
    anthropic_api_key: str | None = None
    twelvedata_api_key: str | None = None
    evds_api_key: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_pass: str | None = None
    mail_to: str | None = None

    @classmethod
    def from_env(cls) -> "Secrets":
        def _int(name: str, default: int) -> int:
            raw = os.environ.get(name)
            try:
                return int(raw) if raw else default
            except ValueError:
                return default

        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
            twelvedata_api_key=os.environ.get("TWELVEDATA_API_KEY") or None,
            evds_api_key=os.environ.get("EVDS_API_KEY") or None,
            smtp_host=os.environ.get("SMTP_HOST") or None,
            smtp_port=_int("SMTP_PORT", 587),
            smtp_user=os.environ.get("SMTP_USER") or None,
            smtp_pass=os.environ.get("SMTP_PASS") or None,
            mail_to=os.environ.get("MAIL_TO") or None,
        )

    def mail_ready(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_pass and self.mail_to)


@dataclass(frozen=True)
class Config:
    raw: dict[str, Any] = field(default_factory=dict)
    secrets: Secrets = field(default_factory=Secrets)

    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.raw
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    # Sık kullanılan kısayollar
    @property
    def model_id(self) -> str:
        return self.get("model", "id", default="claude-opus-4-8")

    @property
    def index_symbol(self) -> str:
        return self.get("benchmarks", "index_symbol", default="XU100")


def load_config(config_path: Path | None = None) -> Config:
    _load_dotenv(REPO_ROOT / ".env")
    path = config_path or CONFIG_PATH
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    return Config(raw=raw or {}, secrets=Secrets.from_env())
