"""Hermetic tests for the weekly-review notifier — no network, no SMTP."""

from __future__ import annotations

import json

from btb_pipeline import notify


def _seed(web_data):
    (web_data / "members").mkdir(parents=True)
    (web_data / "members" / "roster.json").write_text(json.dumps([{"x": 1}] * 3))
    (web_data / "finance").mkdir()
    (web_data / "gerrymander").mkdir()
    (web_data / "gerrymander" / "districts.json").write_text(json.dumps([{"g": 1}] * 5))
    for i in range(2):
        (web_data / "finance" / f"r{i}.json").write_text("[]")


def test_build_digest_ok(tmp_path):
    _seed(tmp_path)
    subject, body = notify.build_digest(web_data=tmp_path, base_url="http://x", fetch=lambda u: 200)
    assert "OK" in subject
    assert "all routes 200" in body
    assert "members (roster): 3" in body
    assert "races w/ finance:  2" in body
    assert "districts (compactness): 5" in body


def test_build_digest_flags_degraded(tmp_path):
    _seed(tmp_path)
    # /forecast returns 500
    fetch = lambda u: 500 if u.endswith("/forecast") else 200  # noqa: E731
    subject, body = notify.build_digest(web_data=tmp_path, base_url="http://x", fetch=fetch)
    assert "ATTENTION" in subject
    assert "/forecast=500" in body


def test_send_email_speaks_smtp(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port):
            sent["addr"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self):
            sent["tls"] = True

        def login(self, u, p):
            sent["login"] = (u, p)

        def send_message(self, msg):
            sent["to"] = msg["To"]
            sent["subject"] = msg["Subject"]

    monkeypatch.setattr(notify.smtplib, "SMTP", FakeSMTP)
    cfg = {"SMTP_HOST": "h", "SMTP_PORT": "587", "SMTP_USER": "u@x", "SMTP_PASS": "pw", "ALERT_EMAIL_TO": "to@x"}
    notify.send_email("subj", "body", cfg=cfg)
    assert sent["addr"] == ("h", 587)
    assert sent["tls"] is True
    assert sent["login"] == ("u@x", "pw")
    assert sent["to"] == "to@x" and sent["subject"] == "subj"
