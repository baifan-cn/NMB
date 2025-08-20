from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Iterable

from app.core.config import settings


class EmailService:
    @staticmethod
    def send_email(subject: str, to_emails: Iterable[str], html: str, text: str | None = None) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.MAIL_FROM
        msg["To"] = ", ".join(to_emails)
        if text:
            msg.set_content(text)
        msg.add_alternative(html, subtype="html")

        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USERNAME:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USERNAME:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
