"""Regression-alerts tests [v1.10.3] — pure alert composition + deduped GitHub issue upsert, all
with injected HTTP/email (no wire)."""

from __future__ import annotations

import json

import pytest

from btb_pipeline import regression


def _checks(*specs):
    # spec = (name, ok, severity)
    return [{"name": n, "ok": ok, "detail": "d", "severity": sev} for n, ok, sev in specs]


def test_severity_picks_worst_failing():
    assert regression.severity(_checks(("a", True, "critical"))) == "ok"
    assert regression.severity(_checks(("a", False, "warning"))) == "warning"
    assert regression.severity(
        _checks(("a", False, "warning"), ("b", False, "critical"))
    ) == "critical"


def test_failing_check_defaults_to_critical():
    # no explicit severity on a failing check → treated as critical
    assert regression.severity([{"name": "x", "ok": False}]) == "critical"


def test_diff_classifies_new_still_recovered():
    checks = _checks(("route /races", False, "critical"), ("route /", True, "critical"))
    delta = regression.diff_checks(checks, previous=["route /", "route /forecast"])
    assert delta["newly_failing"] == ["route /races"]
    assert delta["recovered"] == ["route /", "route /forecast"]
    assert delta["still_failing"] == []


def test_diff_without_previous_is_all_new():
    checks = _checks(("a", False, "critical"), ("b", False, "critical"))
    delta = regression.diff_checks(checks, previous=None)
    assert delta["newly_failing"] == ["a", "b"]
    assert delta["still_failing"] == [] and delta["recovered"] == []


def test_format_alert_carries_summary_diff_link_severity():
    checks = _checks(("route /races", False, "critical"), ("ok-check", True, "warning"))
    subject, body = regression.format_alert(
        checks, run_url="https://gh/run/1", previous=["route /races"]
    )
    assert "critical" in subject and "1 check(s) failing" in subject
    assert "route /races" in body           # summary
    assert "STILL: route /races" in body    # diff
    assert "Run: https://gh/run/1" in body  # link
    assert "Severity: critical" in body     # severity


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _opener_recording(responses, calls):
    """Return an opener that records (method, path, json-body) and replies from `responses` queue."""
    def opener(req, timeout=0):
        body = json.loads(req.data.decode()) if req.data else None
        calls.append((req.get_method(), req.full_url, body))
        return _FakeResp(responses.pop(0))
    return opener


def test_upsert_issue_creates_when_none_open():
    calls: list = []
    # GET open issues -> none; POST create -> issue #7
    opener = _opener_recording([[], {"number": 7}], calls)
    action = regression.upsert_issue("o/r", "tok", "subj", "body", opener=opener)
    assert action == "created #7"
    methods = [c[0] for c in calls]
    assert methods == ["GET", "POST"]
    assert "/repos/o/r/issues" in calls[1][1] and calls[1][2]["title"] == regression.ISSUE_TITLE
    assert calls[1][2]["labels"] == [regression.ISSUE_LABEL]


def test_upsert_issue_comments_when_open_dedup():
    calls: list = []
    existing = [{"number": 3, "title": regression.ISSUE_TITLE}]
    opener = _opener_recording([existing, {"id": 99}], calls)
    action = regression.upsert_issue("o/r", "tok", "subj", "body", opener=opener)
    assert action == "commented #3"
    assert calls[1][1].endswith("/repos/o/r/issues/3/comments")  # dedup → comment, not new issue


def test_run_no_regression_is_noop(tmp_path, capsys):
    report = tmp_path / "r.json"
    report.write_text(json.dumps({"checks": _checks(("a", True, "critical"))}))
    assert regression.run(["--report", str(report)]) == 0
    assert "no regression" in capsys.readouterr().out


def test_run_dry_run_prints_and_sends_nothing(tmp_path, capsys, monkeypatch):
    # a wired send would blow up (no SMTP env) — dry-run must not touch it
    monkeypatch.setattr(regression.notify, "send_email",
                        lambda *a, **k: pytest.fail("dry-run must not send"))
    report = tmp_path / "r.json"
    report.write_text(json.dumps({
        "run_url": "https://gh/run/9",
        "checks": _checks(("route /races", False, "critical")),
    }))
    assert regression.run(["--report", str(report), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "REGRESSION (critical)" in out and "route /races" in out


def test_run_missing_report_flag_errors():
    with pytest.raises(SystemExit):
        regression.run([])
