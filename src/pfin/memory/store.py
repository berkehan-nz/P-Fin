"""state.json atomik yükleme/kaydetme. Boş dosyada da çalışır (Adım 1 gerekliliği).

Actions runner'ları geçici; state.json run sonunda repoya commit'lenir (§3.4).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from ..config import STATE_PATH
from .schema import State


def load_state(path: Path | None = None) -> State:
    """state.json'ı yükler. Yoksa/boşsa boş bir State döner."""
    path = path or STATE_PATH
    if not path.exists():
        return State()
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return State()
    return State.model_validate_json(text)


def save_state(state: State, path: Path | None = None) -> None:
    """Atomik yazım: geçici dosyaya yaz, sonra rename. Yarım dosya bırakmaz."""
    path = path or STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    data = state.model_dump(mode="json")
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
