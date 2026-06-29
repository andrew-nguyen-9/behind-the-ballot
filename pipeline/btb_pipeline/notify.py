"""Weekly review + alert email [v1.10.5] — composes a short health/coverage digest and sends it
via Gmail SMTP [T4b]. Stdlib only (smtplib + urllib), no new deps.

    uv run --project pipeline python -m btb_pipeline.notify           # send weekly review
    uv run --project pipeline python -m btb_pipeline.notify --dry-run # print, don't send

Env (gitignored .env or CI secrets): SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, ALERT_EMAIL_TO.
ponytail: `build_digest` is pure (counts from committed src/data + injected route fetch) so it's
fully unit-tested with no network/SMTP; only `send_email` touches the wire.
"""

from __future__ import annotations

import json
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from urllib.request import Request, urlopen

WEB_DATA = Path("apps/web/src/data")
BASE_URL = "https://behind-the-ballot.hh5zvph54s.workers.dev"
ROUTES = ("/", "/races", "/forecast", "/members", "/gerrymander", "/sources")


def _count(path: Path) -> int:
    """Rows in a JSON array file, else 0."""
    if not path.exists():
        return 0
    data = json.loads(path.read_text())
    return len(data) if isinstance(data, list) else 1


def _http_status(url: str) -> int:
    # Send a real User-Agent: Cloudflare 403s the default "Python-urllib/x" bot UA.
    req = Request(url, headers={"User-Agent": "btb-weekly-review/1.0"})
    try:
        with urlopen(req, timeout=20) as r:  # noqa: S310 (fixed https base)
            return r.status
    except Exception as e:  # surface as a non-200 in the digest
        return getattr(e, "code", 0) or 0


def build_digest(web_data: Path = WEB_DATA, base_url: str = BASE_URL, fetch=_http_status) -> tuple[str, str]:
    """Return (subject, body). Pure given `fetch` — counts come from committed src/data."""
    roster = _count(web_data / "members" / "roster.json")
    races = len(list((web_data / "finance").glob("*.json")))
    demo = len(list((web_data / "demographics").glob("*.json")))
    districts = _count(web_data / "gerrymander" / "districts.json")

    checks = [(p, fetch(base_url + p)) for p in ROUTES]
    bad = [p for p, code in checks if code != 200]
    health = "all routes 200" if not bad else f"DEGRADED: {', '.join(f'{p}={c}' for p, c in checks if c != 200)}"

    subject = f"Behind the Ballot — weekly review ({'OK' if not bad else 'ATTENTION'})"
    body = "\n".join([
        f"Live preview: {base_url}",
        f"Health: {health}",
        "",
        "Real data shipped:",
        f"  members (roster): {roster}",
        f"  races w/ finance:  {races}",
        f"  races w/ demographics: {demo}",
        f"  districts (compactness): {districts}",
        "",
        "Honestly pending a sourced input (not fabricated): forecast + gerrymander fairness",
        "(both need an election-results source — see PROGRESS Open Q#3); polling dropped to V1.1.",
    ])
    return subject, body


def _cfg() -> dict[str, str]:
    need = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "ALERT_EMAIL_TO")
    cfg = {k: os.environ.get(k, "") for k in need}
    missing = [k for k in need if not cfg[k]]
    if missing:
        raise RuntimeError(f"missing SMTP env: {', '.join(missing)} — see docs/SETUP_SECRETS.md")
    return cfg


def send_email(subject: str, body: str, cfg: dict[str, str] | None = None) -> None:
    """Send a plain-text email over Gmail SMTP (STARTTLS on 587) [T4b]."""
    cfg = cfg or _cfg()
    msg = EmailMessage()
    msg["From"] = cfg["SMTP_USER"]
    msg["To"] = cfg["ALERT_EMAIL_TO"]
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(cfg["SMTP_HOST"], int(cfg["SMTP_PORT"])) as s:
        s.starttls()
        s.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
        s.send_message(msg)


def main(argv: list[str] | None = None) -> int:
    dry = "--dry-run" in (argv if argv is not None else sys.argv[1:])
    subject, body = build_digest()
    if dry:
        print(subject + "\n\n" + body)
        return 0
    send_email(subject, body)
    print(f"sent: {subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
