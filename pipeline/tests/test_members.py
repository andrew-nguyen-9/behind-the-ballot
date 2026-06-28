import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import members


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


SAMPLE = json.dumps([
    {
        "id": {"bioguide": "B001"},
        "name": {"first": "Jane", "last": "Doe", "official_full": "Jane Q. Doe"},
        "terms": [
            {"type": "rep", "state": "OH", "district": 3, "party": "Democrat", "start": "2021"},
            {"type": "sen", "state": "OH", "party": "Democrat", "start": "2025"},
        ],
    },
    {
        "id": {"bioguide": "R002"},
        "name": {"first": "John", "last": "Roe"},
        "terms": [{"type": "rep", "state": "PA", "district": 5, "party": "Republican"}],
    },
    {"id": {}, "name": {"first": "No", "last": "Id"}, "terms": []},  # no bioguide -> skipped
])


def test_parse_uses_current_term_and_skips_idless():
    rows = members.parse_legislators(SAMPLE)
    assert len(rows) == 2
    jane = next(r for r in rows if r["bioguide_id"] == "B001")
    assert jane["chamber"] == "sen"  # last term wins
    assert jane["district"] is None  # senator has no district
    assert jane["name"] == "Jane Q. Doe"
    john = next(r for r in rows if r["bioguide_id"] == "R002")
    assert john["district"] == 5
    assert john["name"] == "John Roe"


def test_run_bakes_integrity_clean(tmp_path):
    def transport(url, headers):
        return FakeResp(200, SAMPLE, {"ETag": "e"})

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = members.run(fetcher=CachingFetcher(tmp_path / "b", transport), as_of=now, root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["source"] == "members"
    assert len(payload["rows"]) == 2
    assert_artifact(payload, now=now)  # 14d floor [R14a]
