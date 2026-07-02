"""Race-config generation [generate_races] — fixture-tested transform; no live calls.
Covers Senate, competitive House, and Governor (state office, no FEC)."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.generate_races import (
    build_governor,
    build_house,
    build_senate,
    build_state,
    display_name,
    race_id,
    run,
    totals_url,
)


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


def _cand(cid, name, party, receipts, inc="C"):
    return {"candidate_id": cid, "name": name, "party": party, "receipts": receipts,
            "disbursements": receipts / 2, "last_cash_on_hand_end_period": receipts / 4,
            "coverage_end_date": "2026-03-31", "incumbent_challenge": inc}


def test_display_name_drops_honorifics():
    assert display_name("CORNYN, JOHN SEN") == "John Cornyn"
    assert display_name("TALARICO, JAMES") == "James Talarico"


def test_race_id_scheme():
    assert race_id("senate", "TX") == "us-senate-2026-TX"
    assert race_id("governor", "PA") == "us-governor-2026-PA"
    assert race_id("house", "PA", 7) == "us-house-2026-PA-07"  # zero-padded district


def test_totals_url_house_includes_padded_district():
    url = totals_url("H", "PA", "k", district=7)
    assert "office=H" in url and "district=07" in url
    assert "district=" not in totals_url("S", "TX", "k")  # senate: no district param


def test_build_senate_filters_and_maps():
    results = [
        _cand("S6TX1", "TALARICO, JAMES", "DEM", 40_000_000),
        _cand("S2TX1", "CORNYN, JOHN SEN", "REP", 13_000_000, inc="I"),
        _cand("S6TX9", "PAPER, FILER", "IND", 1000),  # below MIN_RECEIPTS → dropped
    ]
    config, totals = build_senate("TX", results)
    assert config["id"] == "us-senate-2026-TX"
    assert config["office"] == "senate" and config["senateClass"] == 2
    ids = [c["fecCandidateId"] for c in config["candidates"]]
    assert ids == ["S6TX1", "S2TX1"]  # paper filer dropped
    cornyn = next(c for c in config["candidates"] if c["fecCandidateId"] == "S2TX1")
    assert cornyn["party"] == "R" and cornyn["incumbent"] is True
    assert config["candidates"][0]["id"] == "james-talarico"
    assert len(totals) == 2 and totals[0]["receipts"] == 40_000_000
    assert build_state is build_senate  # back-compat alias


def test_build_house_shape():
    results = [_cand("H2PA07001", "SMITH, JANE", "DEM", 2_000_000, inc="I")]
    config, totals = build_house("PA", 7, results)
    assert config["id"] == "us-house-2026-PA-07"
    assert config["office"] == "house" and config["district"] == 7
    assert "senateClass" not in config  # house has no senate class
    assert config["title"] == "PA-07 U.S. House 2026"
    assert config["sources"] == ["fec", "forecast"]
    assert len(config["candidates"]) == 1 and len(totals) == 1


def test_build_governor_is_state_office_without_fec():
    config = build_governor("PA")
    assert config["id"] == "us-governor-2026-PA"
    assert config["office"] == "governor" and config["state"] == "PA"
    assert "district" not in config and "senateClass" not in config
    assert config["candidates"] == []  # no FEC roster for state office
    assert config["sources"] == ["forecast"]  # no fec binding


def test_run_writes_all_three_offices_and_bakes_gold(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "k")

    def transport(url, headers):
        return FakeResp(200, json.dumps({"results": [_cand("X6XX1", "DOE, JANE", "DEM", 9_000_000)]}))

    races = tmp_path / "races"
    n, gold = run(
        fetcher=CachingFetcher(tmp_path / "b", transport),
        states=["TX", "ME"], house_districts=[("PA", 7)], gov_states=["NV"],
        as_of=datetime(2026, 6, 28, tzinfo=timezone.utc), root=tmp_path, races_dir=races,
    )
    assert n == 4  # 2 senate + 1 house + 1 governor
    assert (races / "us-senate-2026-TX.json").exists()
    assert (races / "us-house-2026-PA-07.json").exists()
    gov = json.loads((races / "us-governor-2026-NV.json").read_text())
    assert gov["office"] == "governor" and gov["candidates"] == []
    payload = json.loads(gold.read_text())
    assert payload["source"] == "fec"
    assert len(payload["rows"]) == 3  # senate TX + ME + house PA-07 (governor bakes nothing)


def test_run_can_skip_offices(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "k")

    def transport(url, headers):
        return FakeResp(200, json.dumps({"results": [_cand("S6XX1", "DOE, JANE", "DEM", 9_000_000)]}))

    races = tmp_path / "races"
    n, _ = run(fetcher=CachingFetcher(tmp_path / "b", transport), states=["TX", "ME"],
               house_districts=[], gov_states=[],
               as_of=datetime(2026, 6, 28, tzinfo=timezone.utc), root=tmp_path, races_dir=races)
    assert n == 2  # senate only
