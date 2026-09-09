"""Elle eklenen sirketler.

Dashboard statik oldugu icin dosyaya YAZAMAZ. Akis:
  1. Dashboard'daki "Sirket ekle" formu bir JSON parcasi uretir
  2. Berke ya panoya kopyalayip Claude Code'a yapistirir, ya da
     "GitHub'da ac" ile ``data/watchlist.json`` duzenleyicisini acar
  3. Bu modul listeyi okur, huniden GECMESELER BILE tam metrik seti uretir
  4. Elle eklenenler ``candidates.json`` icinde AYRI bolumde durur;
     siralamaya karismaz ama dashboard'da ve Claude'un okudugu dosyada gorunur
"""

from __future__ import annotations

from .config import DATA_DIR
from .util import read_json, today_iso, write_json

PATH = DATA_DIR / "watchlist.json"

ENTRY_SCHEMA = {
    "ticker": "",
    "added_date": "",
    "added_by": "berke",
    "reason": "",          # neden izliyoruz
    "tags": [],
    "active": True,
}


def load() -> dict:
    data = read_json(PATH)
    if not isinstance(data, dict):
        return {"entries": [], "as_of": today_iso(), "source": "manual"}
    data.setdefault("entries", [])
    return data


def tickers(*, active_only: bool = True) -> list[str]:
    entries = load().get("entries", [])
    return [e["ticker"].upper() for e in entries
            if e.get("ticker") and (not active_only or e.get("active", True))]


def entry_for(ticker: str) -> dict | None:
    for e in load().get("entries", []):
        if (e.get("ticker") or "").upper() == ticker.upper():
            return e
    return None


def add(ticker: str, *, reason: str = "", tags: list[str] | None = None) -> bool:
    """Bir sembol ekler. Zaten varsa tekrar eklemez (True doner degisiklik varsa)."""
    ticker = ticker.upper().strip()
    if not ticker:
        return False
    data = load()
    for e in data["entries"]:
        if (e.get("ticker") or "").upper() == ticker:
            if not e.get("active", True):
                e["active"] = True
                return write_json(PATH, data)
            return False
    data["entries"].append({
        **ENTRY_SCHEMA,
        "ticker": ticker,
        "added_date": today_iso(),
        "reason": reason,
        "tags": tags or [],
    })
    return write_json(PATH, data)


def remove(ticker: str) -> bool:
    """Listeden cikarmaz, PASIFE ceker — neden ekledigimizin kaydi kalsin."""
    data = load()
    changed = False
    for e in data["entries"]:
        if (e.get("ticker") or "").upper() == ticker.upper() and e.get("active", True):
            e["active"] = False
            e["removed_date"] = today_iso()
            changed = True
    return write_json(PATH, data) if changed else False


def ensure_file() -> bool:
    """Dosya yoksa bos sema ile olustur (dashboard 404 almasin)."""
    if PATH.exists():
        return False
    return write_json(PATH, {"entries": [], "source": "manual"})


def json_snippet(ticker: str, reason: str = "") -> dict:
    """Dashboard formunun urettigi JSON parcasi.

    Berke bunu ya Claude Code'a yapistirir ya da GitHub web duzenleyicisine.
    """
    return {
        "ticker": ticker.upper(),
        "added_date": today_iso(),
        "added_by": "berke",
        "reason": reason,
        "tags": [],
        "active": True,
    }
