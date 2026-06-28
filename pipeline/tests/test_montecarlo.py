import pytest

from btb_pipeline.montecarlo import compute_forecast, simulate_chamber


def _probs(n: int, p: float) -> dict[str, float]:
    return {f"R{i:02d}": p for i in range(n)}


def test_reproducible_same_seed():
    a = simulate_chamber(_probs(5, 0.5), n_sims=5000, seed=42)
    b = simulate_chamber(_probs(5, 0.5), n_sims=5000, seed=42)
    assert a["dem_control_prob"] == b["dem_control_prob"]
    assert a["expected_dem_seats"] == b["expected_dem_seats"]
    assert a["seat_distribution"] == b["seat_distribution"]


def test_different_seed_runs():
    # Just assert it runs and is well-formed; values may differ.
    out = simulate_chamber(_probs(5, 0.5), n_sims=5000, seed=99)
    assert out["n_races"] == 5
    assert 0.0 <= out["dem_control_prob"] <= 1.0


def test_certain_dem_wins():
    out = simulate_chamber(_probs(7, 1.0), n_sims=2000, national_sigma=0.05, seed=1)
    assert out["expected_dem_seats"] == 7
    assert out["dem_control_prob"] == 1.0


def test_certain_dem_losses():
    out = simulate_chamber(_probs(7, 0.0), n_sims=2000, national_sigma=0.05, seed=1)
    assert out["expected_dem_seats"] == 0
    assert out["dem_control_prob"] == 0.0


def test_symmetric_odd_chamber():
    # 3 races at p=0.5, no national swing -> independent fair coins.
    # Dem control needs >= 2 of 3 seats; by symmetry that probability is ~0.5.
    out = simulate_chamber(_probs(3, 0.5), n_sims=20000, national_sigma=0.0, seed=7)
    assert 0.45 <= out["dem_control_prob"] <= 0.55
    assert 1.4 <= out["expected_dem_seats"] <= 1.6


def test_correlated_swing_widens_spread():
    # Correlated national swing fattens the tails of the seat distribution [N6a].
    races = _probs(11, 0.5)
    corr = simulate_chamber(races, n_sims=20000, national_sigma=0.15, seed=3)
    indep = simulate_chamber(races, n_sims=20000, national_sigma=0.0, seed=3)
    corr_spread = corr["dem_seat_p90"] - corr["dem_seat_p10"]
    indep_spread = indep["dem_seat_p90"] - indep["dem_seat_p10"]
    assert corr_spread >= indep_spread


def test_compute_forecast_keys_and_distribution():
    out = compute_forecast(_probs(6, 0.55), n_sims=4000, seed=11)
    assert set(out) == {
        "n_sims",
        "n_races",
        "expected_dem_seats",
        "dem_seat_p10",
        "dem_seat_p50",
        "dem_seat_p90",
        "dem_control_prob",
        "seat_distribution",
    }
    assert out["n_races"] == 6
    # Buckets are each independently rounded to 4dp, so the sum carries a little rounding
    # slack (up to ~5e-5 per bucket); 1e-3 still catches any missing/extra mass.
    total = sum(out["seat_distribution"].values())
    assert total == pytest.approx(1.0, abs=1e-3)


def test_empty_raises():
    with pytest.raises(ValueError):
        simulate_chamber({})
    with pytest.raises(ValueError):
        compute_forecast({})
