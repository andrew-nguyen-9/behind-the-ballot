import pytest

from btb_pipeline.fairness import (
    compute_fairness,
    efficiency_gap,
    mean_median,
    seats_votes,
    wasted_votes,
)


def _d(geoid: str, dem: int, rep: int) -> dict:
    return {"geoid": geoid, "dem_votes": dem, "rep_votes": rep}


# Perfectly symmetric: Dems win one, Reps win the other, mirror images.
SYMMETRIC = [_d("01", 60, 40), _d("02", 40, 60)]

# Packed/cracked: D crushed into one district, narrowly cracked in two.
PACKED_CRACKED = [_d("01", 80, 20), _d("02", 45, 55), _d("03", 45, 55)]


def test_wasted_votes_basic():
    # dem=60, rep=40, total=100, threshold=100//2+1=51.
    # Dem wins -> wastes 60-51=9. Rep loses -> wastes all 40.
    assert wasted_votes(60, 40) == (9.0, 40.0)


def test_wasted_votes_rep_winner():
    # dem=45, rep=55, total=100, threshold=51. Rep wins -> wastes 55-51=4. Dem wastes all 45.
    assert wasted_votes(45, 55) == (45.0, 4.0)


def test_symmetric_map_has_zero_eg_and_mean_median():
    assert efficiency_gap(SYMMETRIC) == pytest.approx(0.0, abs=1e-9)
    assert mean_median(SYMMETRIC) == pytest.approx(0.0, abs=1e-9)


def test_packed_cracked_efficiency_gap():
    # D1 80-20: D wins, wastes 80-51=29; R wastes 20.
    # D2 45-55: R wins, wastes 55-51=4; D wastes 45.
    # D3 45-55: R wins, wastes 55-51=4; D wastes 45.
    # sum_dem_wasted = 29+45+45 = 119; sum_rep_wasted = 20+4+4 = 28; total = 300.
    # EG = (119-28)/300 = 91/300 = 0.303333...
    assert efficiency_gap(PACKED_CRACKED) == pytest.approx(91 / 300, abs=1e-6)


def test_packed_cracked_mean_median():
    # shares = 0.80, 0.45, 0.45. mean = 1.70/3 = 0.566667; median = 0.45.
    # mean - median = 0.116667.
    assert mean_median(PACKED_CRACKED) == pytest.approx(1.7 / 3 - 0.45, abs=1e-6)


def test_seats_votes_known_map():
    # PACKED_CRACKED: Dems win 1 of 3 seats -> 1/3. Dem votes = 80+45+45 = 170 of 300.
    seat_share, vote_share = seats_votes(PACKED_CRACKED)
    assert seat_share == pytest.approx(1 / 3, abs=1e-9)
    assert vote_share == pytest.approx(170 / 300, abs=1e-9)


def test_compute_fairness_returns_all_keys():
    report = compute_fairness(PACKED_CRACKED)
    assert set(report) == {
        "efficiency_gap",
        "mean_median",
        "dem_seat_share",
        "dem_vote_share",
        "n_districts",
    }
    assert report["n_districts"] == 3
    assert report["efficiency_gap"] == round(91 / 300, 4)
    assert report["dem_seat_share"] == round(1 / 3, 4)


def test_empty_input_raises():
    with pytest.raises(ValueError):
        efficiency_gap([])
    with pytest.raises(ValueError):
        mean_median([])
    with pytest.raises(ValueError):
        seats_votes([])
    with pytest.raises(ValueError):
        compute_fairness([])
