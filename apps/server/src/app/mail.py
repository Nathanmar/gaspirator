"""E-mails sent by the API (registration decided, US-01).

Routes depend on `get_mailer` and never know how an e-mail leaves:
- `SmtpMailer` when `SMTP_HOST` is set: Mailpit in development (docker compose, web UI on
  http://localhost:8025), a real SMTP service in production;
- `LogMailer` otherwise: the e-mail is only written to the logs.

An e-mail that cannot be sent never fails the request: the contract has no error for it.
"""

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from app.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    body: str


class Mailer(Protocol):
    def send(self, email: Email) -> None: ...


@dataclass(frozen=True)
class SmtpMailer:
    """Sends through an SMTP server without authentication (Mailpit) by default."""

    host: str
    port: int
    sender: str

    def send(self, email: Email) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = email.to
        message["Subject"] = email.subject
        message.set_content(email.body)
        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            smtp.send_message(message)


class LogMailer:
    """No SMTP server configured: the e-mail is written to the logs."""

    def send(self, email: Email) -> None:
        logger.info("E-mail to %s: %s\n%s", email.to, email.subject, email.body)


def get_mailer() -> Mailer:
    """FastAPI dependency: the mailer configured by the settings."""
    settings = get_settings()
    if settings.smtp_host:
        return SmtpMailer(settings.smtp_host, settings.smtp_port, settings.mail_from)
    return LogMailer()


def send_safely(mailer: Mailer, email: Email) -> None:
    """Send `email`; a failure is logged, never raised (the decision is already stored)."""
    try:
        mailer.send(email)
    except Exception:
        logger.exception("Could not send the e-mail %r to %s", email.subject, email.to)
