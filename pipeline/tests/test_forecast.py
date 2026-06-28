from datetime import datetime, timezone

import pytest

from btb_pipeline.forecast import run_forecast


def _races():
    return [
        {"race_id": "OH-Sen", "office": "senate", "fundamentals_pvi": 0.03, "poll_dem_share": 0.52},
        {"race_id": "PA-Sen", "office": "senate", "fundamentals_pvi": -0.02, "poll_dem_share": 0.49},
        {"race_id": "TX-03", "office": "house", "fundamentals_pvi": -0.10},  # no polling
    ]


def test_run_forecast_bundle_shape():
    out = run_forecast(_races(), n_sims=4000, seed=1)
    assert {r["race_id"] for r in out["races"]} == {"OH-Sen", "PA-Sen", "TX-03"}
    for r in out["races"]:
        assert 0.0 <= r["win_prob"] <= 1.0
        assert "margin" in r and "margin_lo" in r and "margin_hi" in r
    ch = out["chamber"]
    assert ch["n_races"] == 3
    assert 0.0 <= ch["dem_control_prob"] <= 1.0
    assert out["as_of"].startswith("20")


def test_run_forecast_is_reproducible():
    a = run_forecast(_races(), n_sims=4000, seed=7, as_of=datetime(2026, 6, 28, tzinfo=timezone.utc))
    b = run_forecast(_races(), n_sims=4000, seed=7, as_of=datetime(2026, 6, 28, tzinfo=timezone.utc))
    assert a == b


def test_run_forecast_empty_raises():
    with pytest.raises(ValueError):
        run_forecast([])
