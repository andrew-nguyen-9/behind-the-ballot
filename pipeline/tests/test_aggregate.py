from datetime import date

import pytest

from btb_pipeline.aggregate import aggregate, pollster_weight, recency_weight

AS_OF = date(2024, 11, 1)


def _poll(state, party, end_date, pct, pollster=None):
    row = {"state": state, "party": party, "end_date": end_date, "pct": pct}
    if pollster is not None:
        row["pollster"] = pollster
    return row


def test_recency_weight_half_life():
    # 0.5 ** (days_old / 30): 0 -> 1.0, 30 -> 0.5, 60 -> 0.25.
    assert recency_weight(0) == pytest.approx(1.0, abs=1e-9)
    assert recency_weight(30) == pytest.approx(0.5, abs=1e-9)
    assert recency_weight(60) == pytest.approx(0.25, abs=1e-9)


def test_recency_weight_negative_treated_as_zero():
    # A poll dated after as_of -> days_old<0 -> treated as 0 -> full weight 1.0.
    assert recency_weight(-5) == pytest.approx(1.0, abs=1e-9)


def test_pollster_weight_lookup_and_neutral():
    ratings = {"Acme": 2.5}
    assert pollster_weight("Acme", ratings) == 2.5
    assert pollster_weight("Unknown", ratings) == 1.0  # missing -> neutral
    assert pollster_weight(None, ratings) == 1.0  # unnamed -> neutral


def test_equal_recency_no_ratings_is_simple_mean():
    # Both polls end on as_of -> recency 1.0 each, no ratings -> weight 1.0 each.
    # weighted mean = (50 + 40) / 2 = 45.0 (the simple mean).
    rows = [
        _poll("CA", "DEM", "2024-11-01", 50.0),
        _poll("CA", "DEM", "2024-11-01", 40.0),
    ]
    out = aggregate(rows, as_of=AS_OF)
    assert len(out) == 1
    assert out[0]["avg_pct"] == pytest.approx(45.0, abs=1e-9)
    assert out[0]["n_polls"] == 2
    assert out[0]["latest_end_date"] == "2024-11-01"


def test_recency_pulls_toward_recent_poll():
    # Recent poll: end == as_of -> days_old=0 -> recency 1.0, pct 50.
    # Old poll: 30 days earlier (2024-10-02) -> days_old=30 -> recency 0.5, pct 40.
    # weighted mean = (1.0*50 + 0.5*40) / (1.0 + 0.5) = (50 + 20) / 1.5 = 70/1.5 = 46.6667.
    rows = [
        _poll("CA", "DEM", "2024-11-01", 50.0),
        _poll("CA", "DEM", "2024-10-02", 40.0),
    ]
    out = aggregate(rows, as_of=AS_OF)
    assert out[0]["avg_pct"] == pytest.approx(70.0 / 1.5, abs=1e-4)
    assert out[0]["latest_end_date"] == "2024-11-01"


def test_ratings_higher_weight_dominates():
    # Both end on as_of -> recency 1.0 each. Strong pollster weight 3.0 (pct 50),
    # Weak pollster weight 1.0 (pct 40).
    # weighted mean = (3.0*50 + 1.0*40) / (3.0 + 1.0) = (150 + 40) / 4 = 190/4 = 47.5.
    rows = [
        _poll("CA", "DEM", "2024-11-01", 50.0, pollster="Strong"),
        _poll("CA", "DEM", "2024-11-01", 40.0, pollster="Weak"),
    ]
    out = aggregate(rows, ratings={"Strong": 3.0, "Weak": 1.0}, as_of=AS_OF)
    assert out[0]["avg_pct"] == pytest.approx(47.5, abs=1e-9)
    # The simple mean would be 45.0; the higher-weighted poll pulls it toward 50.
    assert out[0]["avg_pct"] > 45.0


def test_grouping_states_and_parties_sorted():
    rows = [
        _poll("TX", "REP", "2024-11-01", 55.0),
        _poll("CA", "DEM", "2024-11-01", 60.0),
        _poll("CA", "REP", "2024-11-01", 35.0),
        _poll("TX", "DEM", "2024-11-01", 42.0),
    ]
    out = aggregate(rows, as_of=AS_OF)
    keys = [(r["state"], r["party"]) for r in out]
    assert keys == [("CA", "DEM"), ("CA", "REP"), ("TX", "DEM"), ("TX", "REP")]
    assert all(r["n_polls"] == 1 for r in out)


def test_skip_missing_pct_and_bad_end_date():
    rows = [
        _poll("CA", "DEM", "2024-11-01", 50.0),  # good
        _poll("CA", "DEM", "2024-11-01", None),  # missing pct -> skipped
        _poll("CA", "DEM", "not-a-date", 99.0),  # bad end_date -> skipped
        _poll("CA", "DEM", None, 99.0),  # missing end_date -> skipped
    ]
    out = aggregate(rows, as_of=AS_OF)
    assert len(out) == 1
    assert out[0]["n_polls"] == 1  # only the good row counts
    assert out[0]["avg_pct"] == pytest.approx(50.0, abs=1e-9)


def test_empty_input_raises():
    with pytest.raises(ValueError):
        aggregate([])
