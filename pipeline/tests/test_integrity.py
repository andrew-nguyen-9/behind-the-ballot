from datetime import datetime, timedelta, timezone

import pytest

from btb_pipeline.integrity import (
    IntegrityError,
    assert_artifact,
    check_doc_sync,
    scan_gold,
)


def test_doc_sync_passes_against_real_data_sources_md():
    # The shipped registry must stay in sync with docs/03_DATA_SOURCES.md [R14a].
    check_doc_sync()


def test_assert_artifact_accepts_fresh_registered_source():
    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    assert_artifact({"source": "fec", "as_of": (now - timedelta(days=5)).isoformat()}, now=now)


def test_assert_artifact_rejects_unregistered_source():
    with pytest.raises(IntegrityError, match="unregistered"):
        assert_artifact({"source": "sample", "as_of": "2026-06-28T00:00:00+00:00"})


def test_assert_artifact_rejects_stale():
    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    with pytest.raises(IntegrityError, match="stale"):
        assert_artifact({"source": "polls_538", "as_of": (now - timedelta(days=10)).isoformat()}, now=now)


def test_event_driven_source_has_no_floor():
    # voteview floor is None -> no staleness even if very old.
    assert_artifact({"source": "voteview", "as_of": "2000-01-01T00:00:00+00:00"})


def test_scan_gold_skips_internal_fixtures(tmp_path):
    d = tmp_path / "sample"
    d.mkdir()
    (d / "sample.json").write_text('{"source": "sample", "as_of": "2026-06-28T00:00:00+00:00"}')
    assert scan_gold(tmp_path) == 0  # sample is internal, skipped
