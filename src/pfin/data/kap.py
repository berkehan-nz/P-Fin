"""KAP bildirimleri — nöbetçinin gün içi uyanma tetiğinin ana kaynağı (§3.1, §5).

KAP (Kamuyu Aydınlatma Platformu) halka açık bildirimleri yayınlar. Buradaki amaç
DETERMİNİSTİK: portföydeki şirketlerden yeni bir bildirim düştü mü? LLM yorumu yok;
yalnız "yeni bildirim var" sinyali. İçeriği sonra sabah turu/ajan değerlendirir.

Ağ/kaynak değişimlerine karşı savunmacı: veri gelmezse boş liste döner, çökmemeli.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests

KAP_DISCLOSURE_URL = "https://www.kap.org.tr/tr/api/disclosures"


@dataclass
class Disclosure:
    symbol: str
    title: str
    published_at: str
    url: str = ""
    source: str = "kap"


def recent_disclosures(symbols: list[str], hours: int = 24) -> list[Disclosure]:
    """Verilen BIST sembolleri için son `hours` saatteki KAP bildirimleri.

    Önce KAP genel akışını dener; başarısız olursa borsapy haber akışına düşer.
    """
    wanted = {s.upper() for s in symbols}
    if not wanted:
        return []
    out = _from_kap(wanted, hours)
    if out is None:  # KAP erişilemedi → borsapy fallback
        out = _from_borsapy(wanted, hours)
    return out or []


def _from_kap(wanted: set[str], hours: int) -> list[Disclosure] | None:
    try:
        resp = requests.get(KAP_DISCLOSURE_URL, timeout=20,
                            headers={"User-Agent": "pfin-sentinel/0.1"})
        if resp.status_code != 200:
            return None
        rows = resp.json()
        if not isinstance(rows, list):
            return None
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        out: list[Disclosure] = []
        for row in rows:
            code = str(row.get("stockCodes") or row.get("companyName") or "").upper()
            if not any(w in code for w in wanted):
                continue
            ts = _parse_ts(row.get("publishDate") or row.get("date"))
            if ts and ts < cutoff:
                continue
            did = row.get("disclosureIndex") or row.get("id") or ""
            out.append(Disclosure(
                symbol=next((w for w in wanted if w in code), code),
                title=str(row.get("title") or row.get("summary") or "KAP bildirimi"),
                published_at=(ts or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
                url=f"https://www.kap.org.tr/tr/Bildirim/{did}" if did else "",
            ))
        return out
    except Exception:
        return None


def _from_borsapy(wanted: set[str], hours: int) -> list[Disclosure]:
    out: list[Disclosure] = []
    try:
        import borsapy as bp

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        for sym in wanted:
            try:
                news = bp.Ticker(sym).news or []
            except Exception:
                continue
            for item in news[:10]:
                content = item.get("content", item) if isinstance(item, dict) else {}
                title = content.get("title") or item.get("title") if isinstance(item, dict) else None
                if not title:
                    continue
                ts = _parse_ts(content.get("pubDate") or item.get("providerPublishTime"))
                if ts and ts < cutoff:
                    continue
                out.append(Disclosure(
                    symbol=sym, title=str(title),
                    published_at=(ts or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
                    url=(content.get("canonicalUrl", {}) or {}).get("url", "") if isinstance(content, dict) else "",
                    source="borsapy-news",
                ))
    except Exception:
        return out
    return out


def _parse_ts(raw) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        except Exception:
            return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(raw)[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None
