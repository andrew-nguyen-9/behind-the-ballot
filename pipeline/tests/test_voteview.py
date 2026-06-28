import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import voteview


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


CSV = (
    "congress,bioguide_id,icpsr,chamber,state_abbrev,party_code,nominate_dim1,nominate_dim2\n"
    "117,A000001,1001,House,OH,100,-0.300,0.100\n"
    "118,A000001,1001,House,OH,100,-0.250,\n"  # newer congress for same member
    "118,B000002,2002,Senate,CA,200,0.420,-0.050\n"
    "118,,3003,House,TX,100,0.100,0.200\n"  # no bioguide_id -> skipped
)


def test_parse_keeps_highest_congress_per_member():
    rows = voteview.parse_members(CSV)
    by_bio = {r["bioguide_id"] for r in rows}
    assert by_bio == {"A000001", "B000002"}  # idless row skipped
    a = next(r for r in rows if r["bioguide_id"] == "A000001")
    assert a["congress"] == 118  # most recent kept
    assert a["nominate_dim1"] == -0.250


def test_parse_numeric_coercion_and_blank_none():
    rows = voteview.parse_members(CSV)
    a = next(r for r in rows if r["bioguide_id"] == "A000001")
    assert a["nominate_dim2"] is None  # blank -> None
    b = next(r for r in rows if r["bioguide_id"] == "B000002")
    assert b["nominate_dim1"] == 0.420
    assert isinstance(b["congress"], int)


def test_run_bakes_integrity_clean(tmp_path):
    def transport(url, headers):
        return FakeResp(200, CSV, {"ETag": "e"})

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = voteview.run(
        fetcher=CachingFetcher(tmp_path / "b", transport),
        as_of=now,
        root=tmp_path,
    )
    payload = json.loads(path.read_text())
    assert payload["source"] == "voteview"
    assert len(payload["rows"]) == 2
    assert_artifact(payload, now=now)  # voteview floor=None -> any as_of fine [R14a]


def test_run_upsert_idempotent(tmp_path):
    def transport(url, headers):
        return FakeResp(200, CSV, {"ETag": "e"})

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    kw = {"as_of": now, "root": tmp_path}
    voteview.run(fetcher=CachingFetcher(tmp_path / "b", transport), **kw)
    path = voteview.run(fetcher=CachingFetcher(tmp_path / "b", transport), **kw)
    rows = json.loads(path.read_text())["rows"]
    bios = [r["bioguide_id"] for r in rows]
    assert len(bios) == len(set(bios)) == 2  # no duplicate bioguide_id across runs
