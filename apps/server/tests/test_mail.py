"""app.mail: SMTP (Mailpit) or logs, chosen by the settings; a failure never raises."""

import logging
from email.message import EmailMessage

import pytest

from app import mail
from app.mail import Email, LogMailer, SmtpMailer, get_mailer, send_safely
from app.settings import Settings

EMAIL = Email(to="marie.dupont@example.org", subject="Sujet", body="Bonjour Marie")


class _FakeSmtp:
    """Stands for smtplib.SMTP: records the connection and the message sent."""

    sent: list[tuple[str, int, EmailMessage]] = []

    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host, self.port = host, port

    def __enter__(self) -> "_FakeSmtp":
        return self

    def __exit__(self, *_) -> None:
        pass

    def send_message(self, message: EmailMessage) -> None:
        self.sent.append((self.host, self.port, message))


def test_smtp_mailer_sends_the_email(monkeypatch: pytest.MonkeyPatch):
    _FakeSmtp.sent = []
    monkeypatch.setattr(mail.smtplib, "SMTP", _FakeSmtp)

    SmtpMailer("mailpit", 1025, "Gaspirator <noreply@gaspirator.fr>").send(EMAIL)

    [(host, port, message)] = _FakeSmtp.sent
    assert (host, port) == ("mailpit", 1025)
    assert message["From"] == "Gaspirator <noreply@gaspirator.fr>"
    assert message["To"] == "marie.dupont@example.org"
    assert message["Subject"] == "Sujet"
    assert message.get_content().strip() == "Bonjour Marie"


def test_log_mailer_writes_the_email_to_the_logs(caplog: pytest.LogCaptureFixture):
    with caplog.at_level(logging.INFO, logger="app.mail"):
        LogMailer().send(EMAIL)

    assert "marie.dupont@example.org" in caplog.text
    assert "Sujet" in caplog.text


def test_get_mailer_uses_smtp_when_configured(monkeypatch: pytest.MonkeyPatch):
    settings = Settings(smtp_host="mailpit", smtp_port=1025)
    monkeypatch.setattr(mail, "get_settings", lambda: settings)

    mailer = get_mailer()

    assert mailer == SmtpMailer("mailpit", 1025, settings.mail_from)


def test_get_mailer_logs_without_smtp_host(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(mail, "get_settings", lambda: Settings(smtp_host=None))

    assert isinstance(get_mailer(), LogMailer)


def test_send_safely_never_raises(caplog: pytest.LogCaptureFixture):
    class _BrokenMailer:
        def send(self, email: Email) -> None:
            raise ConnectionRefusedError("SMTP down")

    with caplog.at_level(logging.ERROR, logger="app.mail"):
        send_safely(_BrokenMailer(), EMAIL)

    assert "Could not send the e-mail" in caplog.text
