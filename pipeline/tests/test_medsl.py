"""Hermetic test for the MEDSL president connector — fixture CSV, no network."""

from __future__ import annotations

import json

from btb_pipeline.sources import medsl

# Minimal MEDSL-shaped rows: TX + CA, with a non-TOTAL mode + an OTHER party to prove filtering.
FIXTURE = (
    'year,state,state_po,office,party_simplified,mode,votes,totalvotes\n'
    '2024,TEXAS,TX,US PRESIDENT,REPUBLICAN,TOTAL,6300000,11000000\n'
    '2024,TEXAS,TX,US PRESIDENT,DEMOCRAT,TOTAL,4700000,11000000\n'
    '2024,TEXAS,TX,US PRESIDENT,LIBERTARIAN,TOTAL,80000,11000000\n'
    '2024,CALIFORNIA,CA,US PRESIDENT,DEMOCRAT,TOTAL,9276179,15865475\n'
    '2024,CALIFORNIA,CA,US PRESIDENT,REPUBLICAN,TOTAL,6081697,15865475\n'
    '2024,CALIFORNIA,CA,US PRESIDENT,DEMOCRAT,ELECTION DAY,1000000,15865475\n'  # must be ignored
    # Arizona 2024: no TOTAL mode row (mode "NA") → fall back to its own rows.
    '2024,ARIZONA,AZ,US PRESIDENT,REPUBLICAN,NA,1770000,3400000\n'
    '2024,ARIZONA,AZ,US PRESIDENT,DEMOCRAT,NA,1580000,3400000\n'
)


def test_parse_aggregates_two_party_by_state():
    rows = medsl.parse_president(FIXTURE)
    by = {r["state"]: r for r in rows}
    assert set(by) == {"TX", "CA", "AZ"}
    assert by["TX"] == {"state": "TX", "dem_votes": 4700000, "rep_votes": 6300000}
    # the ELECTION DAY row is filtered → CA Dem is the TOTAL only, not summed with it
    assert by["CA"]["dem_votes"] == 9276179
    # AZ has no TOTAL row → its NA rows are used (fallback), not dropped
    assert by["AZ"] == {"state": "AZ", "dem_votes": 1580000, "rep_votes": 1770000}


def test_bake_writes_gold(tmp_path):
    path = medsl.run(transport=lambda url: FIXTURE, root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["source"] == "medsl_president"
    assert len(payload["rows"]) == 3  # TX + CA (TOTAL) + AZ (NA fallback)
