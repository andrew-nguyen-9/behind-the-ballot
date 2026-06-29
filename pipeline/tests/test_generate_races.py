"""Senate race-config generation [generate_races] — fixture-tested transform; no live calls."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.generate_races import build_state, display_name, run


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


def test_build_state_filters_and_maps():
    results = [
        _cand("S6TX1", "TALARICO, JAMES", "DEM", 40_000_000),
        _cand("S2TX1", "CORNYN, JOHN SEN", "REP", 13_000_000, inc="I"),
        _cand("S6TX9", "PAPER, FILER", "IND", 1000),  # below MIN_RECEIPTS → dropped
    ]
    config, totals = build_state("TX", results)
    assert config["id"] == "us-senate-2026-TX"
    assert config["office"] == "senate" and config["senateClass"] == 2
    ids = [c["fecCandidateId"] for c in config["candidates"]]
    assert ids == ["S6TX1", "S2TX1"]  # paper filer dropped
    cornyn = next(c for c in config["candidates"] if c["fecCandidateId"] == "S2TX1")
    assert cornyn["party"] == "R" and cornyn["incumbent"] is True
    assert config["candidates"][0]["id"] == "james-talarico"
    assert len(totals) == 2 and totals[0]["receipts"] == 40_000_000


def test_run_writes_configs_and_bakes_gold(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "k")

    def transport(url, headers):
        return FakeResp(200, json.dumps({"results": [_cand("S6XX1", "DOE, JANE", "DEM", 9_000_000)]}))

    races = tmp_path / "races"
    n, gold = run(fetcher=CachingFetcher(tmp_path / "b", transport), states=["TX", "ME"],
                  as_of=datetime(2026, 6, 28, tzinfo=timezone.utc), root=tmp_path, races_dir=races)
    assert n == 2
    assert (races / "us-senate-2026-TX.json").exists()
    payload = json.loads(gold.read_text())
    assert payload["source"] == "fec"
    assert len(payload["rows"]) == 2  # one tracked candidate per state
