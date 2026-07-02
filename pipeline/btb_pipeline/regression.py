"""Regression alerts [v1.10.3] — when the nightly gate/canary finds a regression, open (or update)
a DEDUPED GitHub issue AND email the maintainer with a summary + diff + run link + severity
[S9c, S10a, S11a]. Stdlib only (json + urllib for the GitHub REST call), reusing `notify.send_email`
for the Gmail-SMTP wire — no new deps.

    # after a gate/canary step writes a report JSON of its checks:
    uv run --project pipeline python -m btb_pipeline.regression --report canary-report.json \
        --run-url "$RUN_URL"
    uv run --project pipeline python -m btb_pipeline.regression --report r.json --dry-run  # print only

Report shape (produced by the CI step, e.g. scripts/canary.mjs):
    {"run_url": "...", "checks": [{"name": "route /races", "ok": false,
                                   "detail": "expected 200, got 307", "severity": "critical"}, ...],
     "previous": ["route /races", ...]}   # optional: names failing on the prior run, for the diff

ponytail: the composition + dedup logic is pure and fully unit-tested (injectable HTTP + email);
only `run` (unguarded) touches the wire. A healthy report is a no-op (exit 0), so the step is safe
to run every night. GitHub issue upsert is skipped (with a printed note) when GITHUB_TOKEN /
GITHUB_REPOSITORY aren't set, and email is skipped when SMTP env is absent — the two channels are
independent so one missing secret never suppresses the other.
"""

from __future__ import annotations

import json
import os
import sys
from urllib.request import Request, urlopen

from btb_pipeline import notify

ISSUE_TITLE = "[regression] Behind the Ballot nightly gate failing"
ISSUE_LABEL = "regression"
GITHUB_API = "https://api.github.com"
SEVERITY_ORDER = {"ok": 0, "warning": 1, "critical": 2}


def failing(checks: list[dict]) -> list[dict]:
    """The checks that did not pass, in report order."""
    return [c for c in checks if not c.get("ok", False)]


def severity(checks: list[dict]) -> str:
    """Overall severity = the most severe failing check ('critical' > 'warning'); 'ok' if none fail.
    A failing check defaults to 'critical' (a red route/data check is serious unless told otherwise).
    Pure."""
    worst = "ok"
    for c in failing(checks):
        sev = c.get("severity", "critical")
        if SEVERITY_ORDER.get(sev, 2) > SEVERITY_ORDER[worst]:
            worst = sev
    return worst


def diff_checks(checks: list[dict], previous: list[str] | None) -> dict[str, list[str]]:
    """Delta vs the prior run [S10a]. Returns {newly_failing, still_failing, recovered} name lists.
    previous = names that were failing last run (None → treat every current failure as new). Pure."""
    prev = set(previous or [])
    now = {c["name"] for c in failing(checks)}
    return {
        "newly_failing": sorted(now - prev),
        "still_failing": sorted(now & prev),
        "recovered": sorted(prev - now),
    }


def format_alert(
    checks: list[dict], run_url: str | None = None, previous: list[str] | None = None
) -> tuple[str, str]:
    """Compose the (subject, body) alert with summary + diff + run link + severity [S10a]. Pure."""
    sev = severity(checks)
    fails = failing(checks)
    delta = diff_checks(checks, previous)

    subject = f"Behind the Ballot — REGRESSION ({sev}): {len(fails)} check(s) failing"
    lines = [f"Severity: {sev}", f"Failing checks: {len(fails)}", ""]
    lines += [f"  ✗ {c['name']} [{c.get('severity', 'critical')}]: {c.get('detail', '')}".rstrip()
              for c in fails]
    lines += ["", "Since the last run:"]
    lines += [f"  NEW: {n}" for n in delta["newly_failing"]]
    lines += [f"  STILL: {n}" for n in delta["still_failing"]]
    lines += [f"  RECOVERED: {n}" for n in delta["recovered"]]
    if not (delta["newly_failing"] or delta["still_failing"] or delta["recovered"]):
        lines.append("  (no prior-run baseline)")
    if run_url:
        lines += ["", f"Run: {run_url}"]
    return subject, "\n".join(lines)


def _github(method: str, path: str, token: str, payload: dict | None = None, opener=urlopen):
    """One authenticated GitHub REST call → parsed JSON (or []). `opener` is injectable for tests."""
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(
        f"{GITHUB_API}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "btb-regression/1.0",
        },
    )
    with opener(req, timeout=30) as r:  # noqa: S310 (fixed https GitHub API base)
        body = r.read().decode()
    return json.loads(body) if body else []


def upsert_issue(repo: str, token: str, subject: str, body: str, opener=urlopen) -> str:
    """Open a deduped regression issue, or comment on the existing open one [S11a].

    Dedup key = the stable ISSUE_TITLE among open `regression`-labelled issues; returns a short
    action string ('created #N' / 'commented #N'). `opener` is injectable for tests."""
    open_issues = _github(
        "GET", f"/repos/{repo}/issues?state=open&labels={ISSUE_LABEL}&per_page=100", token, opener=opener
    )
    existing = next((i for i in open_issues if i.get("title") == ISSUE_TITLE), None)
    note = f"**{subject}**\n\n{body}"
    if existing:
        num = existing["number"]
        _github("POST", f"/repos/{repo}/issues/{num}/comments", token, {"body": note}, opener=opener)
        return f"commented #{num}"
    created = _github(
        "POST", f"/repos/{repo}/issues", token,
        {"title": ISSUE_TITLE, "body": note, "labels": [ISSUE_LABEL]}, opener=opener,
    )
    return f"created #{created.get('number', '?')}"


def _load_report(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    dry = "--dry-run" in args
    report_path = _opt(args, "--report")
    if not report_path:
        raise SystemExit("regression: --report <path> is required")
    run_url = _opt(args, "--run-url")

    report = _load_report(report_path)
    checks = report.get("checks", [])
    if severity(checks) == "ok":
        print("no regression — all checks passing")
        return 0

    subject, body = format_alert(checks, run_url or report.get("run_url"), report.get("previous"))
    if dry:
        print(subject + "\n\n" + body)
        return 0

    # Two independent channels — a missing secret on one never suppresses the other [S9c, S11a].
    if all(os.environ.get(k) for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "ALERT_EMAIL_TO")):
        notify.send_email(subject, body)
        print("email sent")
    else:
        print("email skipped — SMTP env not set")

    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if token and repo:
        print("issue: " + upsert_issue(repo, token, subject, body))
    else:
        print("issue skipped — GITHUB_TOKEN/GITHUB_REPOSITORY not set")
    return 0


def _opt(args: list[str], flag: str) -> str | None:
    """Value following `flag` in args, or None."""
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else None


if __name__ == "__main__":
    raise SystemExit(run())
