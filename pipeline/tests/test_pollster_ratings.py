import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import pollster_ratings


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


CSV = (
    "pollster,grade,numeric_grade,pollscore\n"
    "Quinnipiac,A,2.8,-1.1\n"
    "Marist,A-,,-0.9\n"  # blank numeric_grade -> None
    ",X,1.0,0.0\n"  # no pollster name -> skipped
)


def test_parse_standard_columns():
    rows = pollster_ratings.parse_ratings(CSV)
    assert len(rows) == 2
    assert {r["pollster"] for r in rows} == {"Quinnipiac", "Marist"}
    q = next(r for r in rows if r["pollster"] == "Quinnipiac")
    assert q["grade"] == "A"
    assert q["numeric_grade"] == 2.8
    assert q["pollscore"] == -1.1


def test_parse_blank_numeric_falls_back_to_pollscore():
    # numeric_grade variant chain ends at pollscore, so a blank numeric_grade
    # adopts pollscore (raw, not inverted); pollscore is still stored separately.
    rows = pollster_ratings.parse_ratings(CSV)
    m = next(r for r in rows if r["pollster"] == "Marist")
    assert m["numeric_grade"] == -0.9
    assert m["pollscore"] == -0.9


def test_parse_blank_numeric_is_none_when_no_pollscore():
    rows = pollster_ratings.parse_ratings("pollster,numeric_grade\nNoNum,\n")
    assert rows[0]["numeric_grade"] is None
    assert rows[0]["pollscore"] is None


def test_parse_variant_columns():
    variant = (
        "pollster_rating_name,pollster_rating,pollscore\n"
        "YouGov,B+,-0.5\n"
    )
    rows = pollster_ratings.parse_ratings(variant)
    assert len(rows) == 1
    assert rows[0]["pollster"] == "YouGov"
    assert rows[0]["grade"] == "B+"
    assert rows[0]["pollscore"] == -0.5


def test_run_bakes_integrity_clean(tmp_path):
    def transport(url, headers):
        return FakeResp(200, CSV, {"ETag": "e"})

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = pollster_ratings.run(
        fetcher=CachingFetcher(tmp_path / "b", transport),
        as_of=now,
        root=tmp_path,
    )
    payload = json.loads(path.read_text())
    assert payload["source"] == "pollster_ratings"
    assert len(payload["rows"]) == 2
    assert_artifact(payload, now=now)  # 30d floor, fresh [R14a]


def test_run_upsert_idempotent(tmp_path):
    def transport(url, headers):
        return FakeResp(200, CSV, {"ETag": "e"})

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    fetcher = CachingFetcher(tmp_path / "b", transport)
    pollster_ratings.run(fetcher=fetcher, as_of=now, root=tmp_path)
    path = pollster_ratings.run(fetcher=fetcher, as_of=now, root=tmp_path)
    payload = json.loads(path.read_text())
    pollsters = [r["pollster"] for r in payload["rows"]]
    assert len(pollsters) == len(set(pollsters)) == 2
