"""Election-calendar connector [E2.1] — validates the committed curated table, bakes gold."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import election_dates as ed


def test_curated_covers_all_50_states_with_iso_dates():
    rows = ed.load_curated()
    states = {r["state"] for r in rows}
    assert len(states) == 50  # all 50 states, one row each
    assert len(rows) == 50
    for r in rows:
        assert r["cycle"] == 2026
        assert r["general"] == "2026-11-03"  # single nationwide general election day
        # every row validates against the schema (ISO dates, required fields)
        ed.ElectionDateRow.model_validate(r)


def test_bad_date_is_rejected():
    with pytest.raises(ValidationError):
        ed.ElectionDateRow.model_validate(
            {"cycle": 2026, "state": "ZZ", "state_name": "Nowhere",
             "primary": "not-a-date", "general": "2026-11-03"}
        )


def test_bake_writes_gold_artifact(tmp_path):
    path = ed.run(root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["source"] == "election_dates"
    assert len(payload["rows"]) == 50
    # the baked artifact clears the integrity gate (registered source, event-driven floor)
    assert_artifact(payload)


def test_run_accepts_injected_rows(tmp_path):
    rows = [{"cycle": 2026, "state": "TX", "state_name": "Texas",
             "primary": "2026-03-03", "runoff": "2026-05-26", "general": "2026-11-03", "note": None}]
    path = ed.run(rows=rows, root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["rows"][0]["state"] == "TX"
    assert payload["rows"][0]["runoff"] == "2026-05-26"
