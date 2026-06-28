from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from btb_pipeline.core import bake, dry_run, is_fresh
from btb_pipeline.sources import sample


def test_freshness_floor():
    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    assert is_fresh(now - timedelta(days=10), 14, now)
    assert not is_fresh(now - timedelta(days=20), 14, now)


def test_dry_run_validates():
    assert dry_run(sample.SampleRow, sample.fetch_raw()) == 2


def test_dry_run_rejects_bad_record():
    with pytest.raises(ValidationError):
        dry_run(sample.SampleRow, [{"state": "ohio", "value": 1}])


def test_bake_writes_gold_artifact(tmp_path):
    when = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = bake(sample.SPEC, sample.SampleRow, sample.fetch_raw(), when, root=tmp_path)
    assert path.exists()
    import json

    payload = json.loads(path.read_text())
    assert payload["source"] == "sample"
    assert len(payload["rows"]) == 2
    assert payload["as_of"].startswith("2026-06-28")
