import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import polls


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


CSV = (
    "poll_id,pollster,state,end_date,candidate_name,party,pct\n"
    "1,Quinnipiac,Ohio,2026-03-01,Jane Doe,DEM,48.5\n"
    "1,Quinnipiac,Ohio,2026-03-01,John Roe,REP,46.0\n"
    ",BadPoll,Ohio,2026-03-01,No Id,DEM,10\n"  # no poll_id -> skipped
)


def test_parse_csv_skips_idless_and_builds_keys():
    rows = polls.parse_csv(CSV)
    assert len(rows) == 2
    assert {r["key"] for r in rows} == {"1:Jane Doe", "1:John Roe"}
    assert rows[0]["pct"] == 48.5


def test_parse_csv_blank_pct_is_none():
    rows = polls.parse_csv("poll_id,candidate_name,pct\n9,X,\n")
    assert rows[0]["pct"] is None


def test_run_bakes_integrity_clean(tmp_path):
    def transport(url, headers):
        return FakeResp(200, CSV, {"ETag": "e"})

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = polls.run(
        fetcher=CachingFetcher(tmp_path / "b", transport),
        files=("senate_polls.csv",),
        as_of=now,
        root=tmp_path,
    )
    payload = json.loads(path.read_text())
    assert payload["source"] == "polls_538"
    assert len(payload["rows"]) == 2
    assert_artifact(payload, now=now)  # 3d floor, fresh [R14a]
