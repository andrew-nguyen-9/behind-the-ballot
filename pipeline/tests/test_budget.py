"""Pure tests for the budget quota check — no network."""

from __future__ import annotations

from btb_pipeline import budget


def test_under_threshold_not_breached():
    breached, frac, msg = budget.check_quota(limit=60, remaining=59)
    assert breached is False
    assert frac < 0.05
    assert "1/60" in msg


def test_at_threshold_breached():
    breached, frac, _ = budget.check_quota(limit=100, remaining=20)  # 80% used
    assert breached is True
    assert frac == 0.8


def test_missing_header_skips():
    breached, frac, msg = budget.check_quota(limit=0, remaining=0)
    assert breached is False and frac == 0.0
    assert "skipped" in msg
