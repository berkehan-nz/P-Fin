"""SMTP mail gönderimi (§3.5). Gmail için uygulama şifresi (SMTP_PASS) beklenir.

Sırlar ortamdan gelir; burada saklanmaz. Anahtar eksikse gönderim atlanır ve
çağırana False döner (çökme yok) — çıktı yine de dosyaya yazılabilir.
"""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import Secrets


def send_mail(secrets: Secrets, subject: str, html: str, text: str) -> bool:
    if not secrets.mail_ready():
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = secrets.smtp_user
    msg["To"] = secrets.mail_to
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(secrets.smtp_host, secrets.smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.login(secrets.smtp_user, secrets.smtp_pass)
        server.sendmail(secrets.smtp_user, [secrets.mail_to], msg.as_string())
    return True
