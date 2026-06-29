"""Focused test for export_forecast's Senate seat math (holdover offset + control threshold)."""

from __future__ import annotations

import json

from btb_pipeline import export_web


def test_chamber_adds_holdover_and_bounds(monkeypatch, tmp_path):
    # gold: 2 states, one safe-D (state share .80) one safe-R (.20); national .50.
    pres = [
        {"state": "AA", "dem_votes": 80, "rep_votes": 20},
        {"state": "BB", "dem_votes": 20, "rep_votes": 80},
    ]
    # roster: 10 senate seats, 6 D-aligned (5 D + 1 Independent), 4 R.
    members = (
        [{"chamber": "sen", "party": "Democrat"}] * 5
        + [{"chamber": "sen", "party": "Independent"}]
        + [{"chamber": "sen", "party": "Republican"}] * 4
    )
    monkeypatch.setattr(export_web, "_gold",
                        lambda src, root: pres if src == "medsl_president" else members)
    # two contested races: AA held by a D incumbent (up_dem=1), BB an R incumbent.
    races = [
        {"id": "r-AA", "office": "senate", "state": "AA",
         "candidates": [{"party": "D", "incumbent": True}]},
        {"id": "r-BB", "office": "senate", "state": "BB",
         "candidates": [{"party": "R", "incumbent": True}]},
    ]
    monkeypatch.setattr(export_web, "_race_configs", lambda d: races)

    export_web.export_forecast(root=tmp_path, web_data=tmp_path)
    ch = json.loads((tmp_path / "forecast" / "chamber-senate.json").read_text())

    # current D-aligned = 6, up_dem = 1 -> holdover = 5. Seats reported are total-Senate (>= holdover).
    assert ch["n_races"] == 2
    assert ch["dem_seat_p10"] >= 5  # holdover floor
    assert ch["dem_seat_p10"] <= ch["dem_seat_p50"] <= ch["dem_seat_p90"]
    assert 5 <= ch["expected_dem_seats"] <= 7  # holdover(5) + 0..2 contested wins
    assert 0.0 <= ch["dem_control_prob"] <= 1.0
    # per-race files exist + are bounded
    aa = json.loads((tmp_path / "forecast" / "r-AA.json").read_text())
    assert 0.0 <= aa["win_prob"] <= 1.0 and aa["margin_lo"] <= aa["margin_hi"]
