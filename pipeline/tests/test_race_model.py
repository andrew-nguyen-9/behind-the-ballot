import pytest

from btb_pipeline.montecarlo import compute_forecast
from btb_pipeline.race_model import (
    BASE_SIGMA,
    HORIZON_SIGMA,
    INCUMBENCY_MARGIN,
    MIDTERM_PENALTY,
    blend_margin,
    finance_margin,
    fundamentals_margin,
    incumbency_margin,
    midterm_margin,
    normal_cdf,
    poll_margin,
    predict_race,
    predict_races,
    sigma_for_days,
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


# --- Q9.1 forecast refinements ------------------------------------------------------------------

def test_incumbency_margin_signs():
    assert incumbency_margin("D") == pytest.approx(INCUMBENCY_MARGIN)
    assert incumbency_margin("R") == pytest.approx(-INCUMBENCY_MARGIN)
    assert incumbency_margin(None) == 0.0
    assert incumbency_margin("I") == 0.0  # independent → no partisan incumbency nudge


def test_finance_margin_scales_and_signs():
    assert finance_margin(0.0) == 0.0
    assert finance_margin(1.0) == pytest.approx(0.05)   # full Dem money edge
    assert finance_margin(-1.0) == pytest.approx(-0.05)  # full Rep money edge


def test_midterm_penalty_shifts_away_from_president():
    # President's party loses ground: R president → shift toward Dems (+), D president → (-).
    assert midterm_margin("R") == pytest.approx(MIDTERM_PENALTY)
    assert midterm_margin("D") == pytest.approx(-MIDTERM_PENALTY)
    assert midterm_margin(None) == 0.0


def test_sigma_widens_with_horizon():
    assert sigma_for_days(None) == pytest.approx(BASE_SIGMA)
    assert sigma_for_days(0) == pytest.approx(BASE_SIGMA)  # election day
    assert sigma_for_days(365) == pytest.approx(BASE_SIGMA + HORIZON_SIGMA)  # a year out
    assert sigma_for_days(999) == pytest.approx(BASE_SIGMA + HORIZON_SIGMA)  # capped
    # monotonic: farther out is never more certain
    assert sigma_for_days(30) < sigma_for_days(200) < sigma_for_days(365)


def test_predict_race_refinements_compose_onto_margin():
    # Even PVI, no polls: base margin 0. Add a Dem incumbent (+0.02), a Dem finance edge
    # (0.5*0.05=0.025), and an R-administration midterm (+0.04) → +0.085.
    out = predict_race(
        "senate", fundamentals_pvi=0.0,
        incumbent_party="D", finance_net=0.5, president_party="R",
    )
    assert out["margin"] == pytest.approx(0.085, abs=1e-9)
    assert out["win_prob"] > 0.5  # the nudges push Dem-favored


def test_predict_race_horizon_widens_range_but_not_margin():
    near = predict_race("senate", fundamentals_pvi=0.10, days_to_election=1)
    far = predict_race("senate", fundamentals_pvi=0.10, days_to_election=365)
    assert near["margin"] == far["margin"]  # horizon changes only the uncertainty
    near_width = near["margin_hi"] - near["margin_lo"]
    far_width = far["margin_hi"] - far["margin_lo"]
    assert far_width > near_width  # a year out is less certain
    # farther out pulls a Dem-leaning race's win prob back toward 0.5
    assert far["win_prob"] < near["win_prob"]


def test_predict_race_defaults_unchanged():
    # No refinement args → identical to the v1 fundamentals-only behavior (sigma 0.07).
    out = predict_race("governor", fundamentals_pvi=0.0, poll_dem_share=0.55)
    assert out["margin"] == pytest.approx(0.06, abs=1e-9)
    assert out["margin_hi"] == pytest.approx(0.06 + 1.28 * BASE_SIGMA, abs=1e-9)
