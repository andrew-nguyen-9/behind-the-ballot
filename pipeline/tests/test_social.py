"""Curated social connector [E-6] — validates the committed handle list, bakes gold. Curated/
static only (no platform API); honest-empty when a handle is unset."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import social


def test_committed_list_is_valid_and_honest_empty_by_default():
    rows = social.load_curated()
    assert isinstance(rows, list)  # committed file parses
    for r in rows:
        social.SocialProfileRow.model_validate(r)  # every committed row validates


def test_null_handle_row_is_a_legit_honest_empty_row():
    row = social.SocialProfileRow.model_validate(
        {"entity_id": "AZ-gov-x", "entity_name": "Jane Doe", "role": "candidate", "state": "AZ"}
    )
    assert row.handle is None and row.profile_url is None  # honest-empty, no fabricated link


def test_verified_handle_row_carries_links():
    row = social.SocialProfileRow.model_validate(
        {
            "entity_id": "AZ-gov-x", "entity_name": "Jane Doe", "role": "candidate", "state": "AZ",
            "platform": "x", "handle": "janedoe",
            "profile_url": "https://x.com/janedoe",
            "latest_post_url": "https://x.com/janedoe/status/1",
            "latest_post_at": "2026-07-01T12:00:00+00:00",
        }
    )
    assert row.handle == "janedoe" and row.profile_url.endswith("/janedoe")


def test_link_without_handle_is_rejected():
    # Honest-empty invariant: a profile link requires a verified handle.
    with pytest.raises(ValidationError):
        social.SocialProfileRow.model_validate(
            {"entity_id": "x", "entity_name": "N", "role": "candidate", "state": "AZ",
             "profile_url": "https://x.com/x"}
        )


def test_bad_timestamp_is_rejected():
    with pytest.raises(ValidationError):
        social.SocialProfileRow.model_validate(
            {"entity_id": "x", "entity_name": "N", "role": "candidate", "state": "AZ",
             "handle": "x", "latest_post_at": "not-a-timestamp"}
        )


def test_bake_empty_list_writes_gold_and_clears_integrity(tmp_path):
    path = social.run(rows=[], root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["source"] == "social"
    assert payload["rows"] == []  # honest-empty bakes an empty artifact, not a fabricated one
    assert_artifact(payload)  # registered source, event-driven floor → passes


def test_bake_accepts_injected_rows(tmp_path):
    rows = [{"entity_id": "AZ-gov-x", "entity_name": "Jane Doe", "role": "candidate",
             "state": "AZ", "platform": "x", "handle": "janedoe",
             "profile_url": "https://x.com/janedoe"}]
    path = social.run(rows=rows, root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["rows"][0]["handle"] == "janedoe"
    assert_artifact(payload)
