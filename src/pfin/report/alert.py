"""Acil uyarı maili (§3.5): stop kırıldı / kritik gelişme / istisnai fırsat.

Nöbetçi (deterministik) üretir; LLM'e sorulmaz. Kısa ve net.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..config import Config


def build_alert(triggers: list[dict], config: Config) -> tuple[str, str, str]:
    """(subject, html, text). `triggers`: nöbetçinin ürettiği tetik kayıtları."""
    prefix = config.get("mail", "subject_prefix", default="[Finans Ajanı]")
    now = datetime.now(timezone.utc).isoformat(timespec="minutes")
    kinds = ", ".join(sorted({t.get("kind", "uyarı") for t in triggers})) or "uyarı"
    subject = f"{prefix} ACİL — {kinds}"

    rows_html = "".join(
        f'<li style="margin:6px 0"><b>{t.get("symbol","")}</b> — '
        f'{t.get("kind","")}: {t.get("message","")}</li>'
        for t in triggers
    )
    html = (
        '<div style="font-family:sans-serif;max-width:640px;margin:auto">'
        f'<h2 style="color:#b00">Acil Uyarı</h2><div style="color:#666">{now}</div>'
        f'<ul>{rows_html}</ul>'
        '<p style="color:#999;font-size:12px">Nöbetçi (deterministik) üretti; LLM çağrılmadı. '
        'İşlem kararı ve uygulama sende — Midas.</p></div>'
    )
    text_lines = [f"ACİL UYARI — {now}", ""]
    for t in triggers:
        text_lines.append(f"- {t.get('symbol','')} [{t.get('kind','')}]: {t.get('message','')}")
    text_lines += ["", "Nöbetçi üretti; LLM çağrılmadı. Karar/işlem sende (Midas)."]
    return subject, html, "\n".join(text_lines)
