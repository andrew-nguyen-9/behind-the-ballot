"""Election-results connector [E3.2] — per-state adapters, normalize, call layer, upsert,
honest-empty bake. Transport is injected → no network; NO fabricated committed data."""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pytest

from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import primary_results as pr

AZ_FIXTURE = (Path(__file__).parent / "fixtures" / "az_clarity_detail.xml").read_text()

AS_OF = datetime(2026, 8, 4, 23, 30, tzinfo=timezone.utc)

JSON_FEED = json.dumps({
    "contests": [
        {
            "office": "senate",
            "precincts_reporting": 900,
            "precincts_total": 1000,
            "candidates": [
                {"name": "Jane Doe", "party": "D", "votes": 600},
                {"name": "John Roe", "party": "R", "votes": 400},
            ],
        },
        {
            "office": "house",
            "district": 9,
            "precincts_reporting": 50,
            "precincts_total": 100,
            "candidates": [
                {"name": "Amy Ash", "party": "D", "votes": 100},
                {"name": "Bob Birch", "party": "R", "votes": 100},
            ],
        },
    ]
})

CSV_FEED = (
    "office,district,candidate,party,votes,precincts_reporting,precincts_total\n"
    "governor,,Carla Cole,D,300,10,20\n"
    "governor,,Dan Dune,R,100,10,20\n"
)


def test_race_id_matches_config_shape():
    assert pr.race_id("senate", "OH", None) == "us-senate-2026-OH"
    assert pr.race_id("house", "OH", 9) == "us-house-2026-OH-09"


def test_parse_json_explodes_candidates():
    contests = pr.parse_json_contests(JSON_FEED)
    assert len(contests) == 4  # 2 senate + 2 house candidates
    sen = [c for c in contests if c["office"] == "senate"]
    assert {c["candidate"] for c in sen} == {"Jane Doe", "John Roe"}


def test_parse_csv_blank_district_is_none():
    contests = pr.parse_csv_contests(CSV_FEED)
    assert all(c["district"] is None for c in contests)
    assert contests[0]["votes"] == 300


def test_build_rows_derives_pct_and_pct_reporting():
    rows = pr.build_rows(
        "OH", pr.parse_json_contests(JSON_FEED),
        source_url="https://sos.oh/", election_type="primary", as_of=AS_OF,
    )
    by_cand = {r["candidate"]: r for r in rows}
    assert by_cand["Jane Doe"]["race_id"] == "us-senate-2026-OH"
    assert by_cand["Jane Doe"]["pct"] == 60.0  # 600 / 1000
    assert by_cand["Jane Doe"]["pct_reporting"] == 90.0  # 900 / 1000
    assert by_cand["Amy Ash"]["district"] == 9
    assert all(r["is_certified"] is False for r in rows)
    assert all(r["as_of"] == AS_OF.isoformat() for r in rows)
    # every row validates against the published schema
    for r in rows:
        pr.ResultRow.model_validate(r)


def test_merge_call_status_only_stamps_named_races():
    rows = pr.build_rows(
        "OH", pr.parse_json_contests(JSON_FEED),
        source_url="https://sos.oh/", election_type="primary", as_of=AS_OF,
    )
    rows = pr.merge_call_status(rows, {"us-senate-2026-OH": {"called_by": "Jane Doe"}})
    sen = [r for r in rows if r["race_id"] == "us-senate-2026-OH"]
    house = [r for r in rows if r["race_id"] == "us-house-2026-OH-09"]
    assert all(r["is_called"] and r["called_by"] == "Jane Doe" for r in sen)
    assert all(r["call_source"] == "Wikipedia" for r in sen)  # defaulted
    assert all(not r.get("is_called") for r in house)  # uncalled race untouched


def test_merge_results_upserts_by_race_and_candidate(tmp_path):
    r1 = pr.build_rows("OH", pr.parse_json_contests(JSON_FEED),
                       source_url="u", election_type="primary", as_of=AS_OF)
    # A later poll moves Jane Doe's total; must overwrite, not duplicate.
    updated = [{**x, "votes": 999} for x in r1 if x["candidate"] == "Jane Doe"]
    merged = pr.merge_results(r1, updated)
    jane = [r for r in merged if r["candidate"] == "Jane Doe"]
    assert len(jane) == 1 and jane[0]["votes"] == 999
    assert len(merged) == len(r1)  # no new rows, no truncation
    assert "_uid" not in merged[0]  # transient key stripped


def test_run_no_targets_is_honest_empty_no_network(tmp_path):
    # No active targets → no fetch, zero rows, artifact still bakes + clears integrity. Post
    # go-live [E-R10] ACTIVE_STATES=["AZ"], so pass states=[] to exercise the honest-empty bake
    # path itself, decoupled from the ops on-switch; a live AZ fetch needs E-R1's fetch-layer
    # wiring (current_ver.txt resolution + detailxml.zip unzip), routed to runbook §1.
    path = pr.run(root=tmp_path, states=[])
    payload = json.loads(path.read_text())
    assert payload["source"] == "primary_results"
    assert payload["rows"] == []
    assert_artifact(payload)


def test_run_with_injected_transport_bakes_normalized_rows(tmp_path):
    feeds = {
        "https://liveresults.ohiosos.gov/": JSON_FEED,
        "https://dp.electionresults.sos.ca.gov/": CSV_FEED,
    }

    class Resp:
        def __init__(self, body):
            self.status_code = 200
            self.headers = {}
            self.text = body

    transport = lambda url, headers: Resp(feeds[url])  # noqa: E731
    path = pr.run(
        transport=transport,
        calls={"us-senate-2026-OH": {"called_by": "Jane Doe"}},
        as_of=AS_OF, root=tmp_path, states=["OH", "CA"],
    )
    payload = json.loads(path.read_text())
    rids = {r["race_id"] for r in payload["rows"]}
    assert "us-senate-2026-OH" in rids
    assert "us-governor-2026-CA" in rids
    sen = [r for r in payload["rows"] if r["race_id"] == "us-senate-2026-OH"]
    assert all(r["is_called"] for r in sen)
    assert_artifact(payload)

    # Re-run with a higher OH total → idempotent upsert (no dupes, totals move).
    bumped = json.dumps({
        "contests": [{
            "office": "senate", "precincts_reporting": 1000, "precincts_total": 1000,
            "candidates": [
                {"name": "Jane Doe", "party": "D", "votes": 700},
                {"name": "John Roe", "party": "R", "votes": 500},
            ],
        }]
    })
    transport2 = lambda url, headers: Resp(bumped)  # noqa: E731
    path = pr.run(transport=transport2, as_of=AS_OF, root=tmp_path, states=["OH"])
    payload = json.loads(path.read_text())
    jane = [r for r in payload["rows"] if r["candidate"] == "Jane Doe"]
    assert len(jane) == 1 and jane[0]["votes"] == 700


# ---- E3.3 general-election readiness -----------------------------------------------------


def test_general_adapters_stamp_election_type_general(tmp_path):
    # Same connector, general adapter set → every row is election_type="general".
    class Resp:
        def __init__(self, body):
            self.status_code, self.headers, self.text = 200, {}, body

    transport = lambda url, headers: Resp(JSON_FEED)  # noqa: E731
    path = pr.run(
        transport=transport, as_of=AS_OF, root=tmp_path,
        states=["OH"], election_type="general",
    )
    payload = json.loads(path.read_text())
    assert payload["rows"], "general run should bake rows"
    assert {r["election_type"] for r in payload["rows"]} == {"general"}
    assert "us-senate-2026-OH" in {r["race_id"] for r in payload["rows"]}
    assert_artifact(payload)


def test_active_election_type_switches_the_default_adapter_set(monkeypatch, tmp_path):
    # The scheduled no-arg bake follows ACTIVE_ELECTION_TYPE (ops' one switch).
    class Resp:
        def __init__(self, body):
            self.status_code, self.headers, self.text = 200, {}, body

    monkeypatch.setattr(pr, "ACTIVE_ELECTION_TYPE", "general")
    transport = lambda url, headers: Resp(CSV_FEED)  # noqa: E731
    path = pr.run(transport=transport, as_of=AS_OF, root=tmp_path, states=["CA"])
    payload = json.loads(path.read_text())
    assert {r["election_type"] for r in payload["rows"]} == {"general"}


MEDSL_FEED = (
    "state,office,district,candidate,party,votes\n"
    "OH,senate,,Jane Doe,D,720\n"
    "OH,senate,,John Roe,R,480\n"
)


def test_certify_flips_is_certified_and_supersedes_provisional(tmp_path):
    # Provisional live pull first (called for Jane), then MEDSL certified backfill.
    class Resp:
        def __init__(self, body):
            self.status_code, self.headers, self.text = 200, {}, body

    transport = lambda url, headers: Resp(JSON_FEED)  # noqa: E731
    pr.run(
        transport=transport, calls={"us-senate-2026-OH": {"called_by": "Jane Doe"}},
        as_of=AS_OF, root=tmp_path, states=["OH"], election_type="general",
    )
    path = pr.certify(MEDSL_FEED, as_of=AS_OF, root=tmp_path)
    payload = json.loads(path.read_text())
    sen = {r["candidate"]: r for r in payload["rows"] if r["race_id"] == "us-senate-2026-OH"}
    # Certified numbers supersede provisional, is_certified flipped, no dupes.
    assert sen["Jane Doe"]["votes"] == 720
    assert all(r["is_certified"] for r in sen.values())
    assert len([r for r in payload["rows"] if r["candidate"] == "Jane Doe"]) == 1
    # Borrowed call attribution carried forward onto the certified row.
    assert sen["Jane Doe"]["is_called"] and sen["Jane Doe"]["called_by"] == "Jane Doe"
    assert_artifact(payload)


def test_certify_without_csv_is_honest_empty(tmp_path):
    # Safe to wire before MEDSL data exists: no CSV → re-bakes existing gold unchanged.
    path = pr.certify(root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["rows"] == []
    assert_artifact(payload)


# ---- E-R1 Arizona adapter (Clarity ENR detail.xml) ---------------------------------------
# Validated against real-SHAPE AZ Clarity bytes (fixtures/az_clarity_detail.xml) via injected
# transport — no live network. Proves: office/district mapping by free-form `text`, county-FIPS
# tagging [E-F2], out-of-scope surfacing, and end-to-end normalized bake.


def test_az_parser_maps_scope_offices_and_tags_county_fips():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        contests = pr.parse_az_clarity_xml(AZ_FIXTURE)
    # Every emitted contest tagged with Pinal's 5-digit FIPS (matches az-counties.json [E-F2]).
    assert {c["county"] for c in contests} == {"04021"}
    offices = {(c["office"], c["district"]) for c in contests}
    # Governor + U.S. House CD2 (truncated "…District 2 Congression") + CD6 mapped.
    assert ("governor", None) in offices
    assert ("house", 2) in offices  # truncation/typo tolerated
    assert ("house", 6) in offices
    # U.S. Senate and STATE Representative (no "congress" token) are OUT of scope → not emitted.
    assert all(c["office"] in {"governor", "house"} for c in contests)
    assert all(c["district"] != 8 for c in contests)  # state-leg "District 8" not mis-mapped
    # Choice roll-up read from totalVotes, not the per-precinct VoteType split.
    robson = next(c for c in contests if c["candidate"] == "ROBSON, KARRIN TAYLOR")
    assert robson["votes"] == 18422 and robson["party"] == "REP"


def test_az_parser_surfaces_out_of_scope_and_primary_collisions():
    # "Surface, don't silently drop": out-of-scope contests + partisan-primary collisions warn.
    with pytest.warns(UserWarning) as rec:
        pr.parse_az_clarity_xml(AZ_FIXTURE)
    msgs = " ".join(str(w.message) for w in rec)
    assert "out-of-scope" in msgs  # Senate + State-rep surfaced
    assert "U.S. Senator" in msgs and "State Representative" in msgs
    # REP + DEM Governor primaries collide on the same race_id (E-R7 owns disambiguation).
    assert "collision" in msgs and "governor" in msgs


def test_az_run_bakes_valid_county_tagged_rows_with_calls(tmp_path):
    class Resp:
        def __init__(self, body):
            self.status_code, self.headers, self.text = 200, {}, body

    transport = lambda url, headers: Resp(AZ_FIXTURE)  # noqa: E731
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        path = pr.run(
            transport=transport,
            calls={"us-house-2026-AZ-06": {"called_by": "ENGEL, KIRSTEN"}},
            as_of=AS_OF, root=tmp_path, states=["AZ"],
        )
    payload = json.loads(path.read_text())
    rows = payload["rows"]
    assert rows, "AZ run should bake rows"
    rids = {r["race_id"] for r in rows}
    assert {"us-governor-2026-AZ", "us-house-2026-AZ-02", "us-house-2026-AZ-06"} <= rids
    assert not any("senate" in r or "SEN" in r for r in rids)  # Senate skipped
    # Every row validates the published schema, carries the county FIPS, and pct_reporting derives.
    for r in rows:
        pr.ResultRow.model_validate(r)
        assert r["county"] == "04021"
    cd2 = next(r for r in rows if r["race_id"] == "us-house-2026-AZ-02")
    assert cd2["pct_reporting"] == 100.0  # 60/60
    gov = next(r for r in rows if r["race_id"] == "us-governor-2026-AZ")
    assert gov["pct_reporting"] == 36.7  # 40/109
    # Wikipedia call layer stamps the attributed race (SoS feed carries no projection).
    cd6 = [r for r in rows if r["race_id"] == "us-house-2026-AZ-06"]
    assert all(r["is_called"] and r["call_source"] == "Wikipedia" for r in cd6)
    assert_artifact(payload)

    # County-tagged rows roll up through E-F2's aggregate_to_county (join key = FIPS 04021).
    agg = pr.aggregate_to_county(rows)
    assert agg and {a["county"] for a in agg} == {"04021"}
    engel = next(a for a in agg if a["candidate"] == "ENGEL, KIRSTEN")
    assert engel["votes"] == 41230
