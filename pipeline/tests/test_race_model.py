import pytest

from btb_pipeline.montecarlo import compute_forecast
from btb_pipeline.race_model import (
    blend_margin,
    fundamentals_margin,
    normal_cdf,
    poll_margin,
    predict_race,
    predict_races,
)


def test_normal_cdf_center_and_one_sigma():
    assert normal_cdf(0.0) == pytest.approx(0.5, abs=1e-12)
    # One sigma above the mean is ~0.8413.
    assert normal_cdf(0.07, 0.0, 0.07) == pytest.approx(0.8413, abs=1e-3)


def test_normal_cdf_bad_sigma_raises():
    with pytest.raises(ValueError):
        normal_cdf(0.0, 0.0, 0.0)


def test_poll_margin():
    assert poll_margin(0.5) == pytest.approx(0.0, abs=1e-12)
    assert poll_margin(0.55) == pytest.approx(0.10, abs=1e-12)


def test_poll_margin_out_of_range_raises():
    with pytest.raises(ValueError):
        poll_margin(1.5)


def test_fundamentals_margin():
    assert fundamentals_margin(0.04) == pytest.approx(0.08, abs=1e-12)


def test_tied_race():
    # Perfect tie: poll at 0.5, pvi 0.0 -> margin 0.0, win_prob 0.5.
    out = predict_race("senate", fundamentals_pvi=0.0, poll_dem_share=0.5)
    assert out["margin"] == pytest.approx(0.0, abs=1e-12)
    assert out["win_prob"] == pytest.approx(0.5, abs=1e-12)


def test_senate_vs_house_blending_differs():
    # Same inputs: poll favors Dem (share 0.60 -> poll_m +0.20),
    # fundamentals favor Rep (pvi -0.05 -> fund_m -0.10).
    poll_m = poll_margin(0.60)
    fund_m = fundamentals_margin(-0.05)
    assert poll_m == pytest.approx(0.20, abs=1e-12)
    assert fund_m == pytest.approx(-0.10, abs=1e-12)

    senate = blend_margin(poll_m, fund_m, "senate")
    house = blend_margin(poll_m, fund_m, "house")

    # Senate (poll-heavy 0.7/0.3): 0.7*0.20 + 0.3*(-0.10) = +0.11.
    assert senate == pytest.approx(0.11, abs=1e-6)
    # House (fundamentals-heavy 0.3/0.7): 0.3*0.20 + 0.7*(-0.10) = -0.01.
    assert house == pytest.approx(-0.01, abs=1e-6)

    # Poll-weighted Senate leans Dem; fundamentals-weighted House leans Rep.
    assert senate > house
    assert senate > 0.0 > house


def test_unknown_office_raises():
    with pytest.raises(ValueError):
        blend_margin(0.1, 0.1, "mayor")


def test_no_polling_uses_fundamentals_only():
    # poll_dem_share=None -> fundamentals only; House weights irrelevant since poll_m is None.
    out = predict_race("house", fundamentals_pvi=0.05, poll_dem_share=None)
    # margin = fundamentals_margin(0.05) = 0.10.
    assert out["margin"] == pytest.approx(0.10, abs=1e-12)
    assert blend_margin(None, 0.10, "house") == pytest.approx(0.10, abs=1e-12)


def test_strong_dem_and_strong_rep():
    strong_dem = predict_race("senate", fundamentals_pvi=0.15, poll_dem_share=0.65)
    strong_rep = predict_race("senate", fundamentals_pvi=-0.15, poll_dem_share=0.35)
    assert strong_dem["win_prob"] > 0.9
    assert strong_rep["win_prob"] < 0.1


def test_margin_range_around_margin():
    out = predict_race("governor", fundamentals_pvi=0.0, poll_dem_share=0.55)
    # margin = 0.6*0.10 + 0.4*0.0 = 0.06; range = 0.06 +/- 1.28*0.07 = +/- 0.0896.
    assert out["margin"] == pytest.approx(0.06, abs=1e-9)
    assert out["margin_lo"] == pytest.approx(0.06 - 1.28 * 0.07, abs=1e-9)
    assert out["margin_hi"] == pytest.approx(0.06 + 1.28 * 0.07, abs=1e-9)


def test_predict_races_feeds_montecarlo_end_to_end():
    # Integration smoke: race model output -> Monte Carlo forecast engine [N2a,N5a].
    races = [
        {"race_id": "R01", "office": "senate", "fundamentals_pvi": 0.10, "poll_dem_share": 0.58},
        {"race_id": "R02", "office": "house", "fundamentals_pvi": -0.08, "poll_dem_share": 0.46},
        {"race_id": "R03", "office": "governor", "fundamentals_pvi": 0.02},  # no polling
        {"race_id": "R04", "office": "senate", "fundamentals_pvi": -0.12, "poll_dem_share": 0.40},
        {"race_id": "R05", "office": "house", "fundamentals_pvi": 0.05, "poll_dem_share": 0.52},
    ]
    probs = predict_races(races)
    assert set(probs) == {"R01", "R02", "R03", "R04", "R05"}
    assert all(0.0 <= p <= 1.0 for p in probs.values())

    forecast = compute_forecast(probs, n_sims=4000, seed=5)
    assert forecast["n_races"] == 5
    assert 0.0 <= forecast["dem_control_prob"] <= 1.0


def test_predict_races_empty_raises():
    with pytest.raises(ValueError):
        predict_races([])
