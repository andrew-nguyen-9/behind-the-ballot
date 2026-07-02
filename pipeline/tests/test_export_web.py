"""Live-join export [export_web] — fixture-tested gold → site JSON."""

import json
from pathlib import Path

from btb_pipeline import export_web as ew


def _write_gold(root: Path, source: str, rows: list[dict]):
    d = root / "gold" / source
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{source}.json").write_text(json.dumps({"source": source, "rows": rows}))


def test_export_members_joins_ideology_and_maps_party(tmp_path):
    _write_gold(tmp_path, "members", [
        {"bioguide_id": "A1", "name": "Ann", "party": "Democrat", "state": "OH", "chamber": "sen", "district": None},
        {"bioguide_id": "B2", "name": "Bo", "party": "Republican", "state": "PA", "chamber": "rep", "district": 5},
    ])
    _write_gold(tmp_path, "voteview", [{"bioguide_id": "A1", "nominate_dim1": -0.3}])

    [out] = ew.export_members(root=tmp_path, web_data=tmp_path / "web")
    roster = json.loads(out.read_text())
    by_id = {r["bioguide_id"]: r for r in roster}
    assert by_id["A1"]["party"] == "D"
    assert by_id["A1"]["nominate_dim1"] == -0.3
    assert by_id["B2"]["party"] == "R"
    assert by_id["B2"]["nominate_dim1"] is None  # no ideology row → None, not missing key
    assert by_id["B2"]["district"] == 5


def test_export_members_skips_when_no_gold(tmp_path):
    assert ew.export_members(root=tmp_path, web_data=tmp_path / "web") == []


def test_export_demographics_state_rollup_and_district(tmp_path, monkeypatch):
    _write_gold(tmp_path, "census_acs", [
        {"geoid": "3901", "state": "39", "district": "01", "population": 700000, "median_income": 60000},
        {"geoid": "3902", "state": "39", "district": "02", "population": 300000, "median_income": 80000},
        {"geoid": "4205", "state": "42", "district": "05", "population": 500000, "median_income": 70000},
    ])
    races = tmp_path / "races"
    races.mkdir()
    (races / "oh-sen.json").write_text(json.dumps({"id": "oh-sen", "office": "senate", "state": "OH", "district": None}))
    (races / "pa-05.json").write_text(json.dumps({"id": "pa-05", "office": "house", "state": "PA", "district": 5}))
    monkeypatch.setattr(ew, "RACES_DIR", races)

    out = ew.export_demographics(root=tmp_path, web_data=tmp_path / "web")
    assert len(out) == 2
    web = tmp_path / "web" / "demographics"
    oh = json.loads((web / "oh-sen.json").read_text())
    assert oh["area"] == "Ohio"
    assert oh["population"] == 1_000_000  # state rollup sums districts
    assert oh["median_income"] == 66000  # pop-weighted: (700k*60k+300k*80k)/1M
    assert oh["urbanization"] is None
    pa = json.loads((web / "pa-05.json").read_text())
    assert pa["area"] == "Pennsylvania District 5"
    assert pa["population"] == 500000


def test_export_forecast_covers_house_and_governor(tmp_path, monkeypatch):
    # State-level presidential margins -> per-race fundamentals PVI [E2.2].
    _write_gold(tmp_path, "medsl_president", [
        {"state": "TX", "dem_votes": 45, "rep_votes": 55},
        {"state": "PA", "dem_votes": 50, "rep_votes": 50},
        {"state": "NV", "dem_votes": 52, "rep_votes": 48},
    ])
    _write_gold(tmp_path, "members", [
        {"bioguide_id": "A1", "party": "Democrat", "chamber": "sen", "state": "TX"},
    ])
    races = tmp_path / "races"
    races.mkdir()
    (races / "us-senate-2026-TX.json").write_text(json.dumps(
        {"id": "us-senate-2026-TX", "office": "senate", "state": "TX",
         "candidates": [{"party": "D", "incumbent": True}]}))
    (races / "us-house-2026-PA-07.json").write_text(json.dumps(
        {"id": "us-house-2026-PA-07", "office": "house", "state": "PA", "district": 7}))
    (races / "us-governor-2026-NV.json").write_text(json.dumps(
        {"id": "us-governor-2026-NV", "office": "governor", "state": "NV"}))
    monkeypatch.setattr(ew, "RACES_DIR", races)

    out = ew.export_forecast(root=tmp_path, web_data=tmp_path / "web")
    written = {p.name for p in out}
    assert {"us-house-2026-PA-07.json", "us-governor-2026-NV.json"} <= written
    fc = tmp_path / "web" / "forecast"
    house = json.loads((fc / "us-house-2026-PA-07.json").read_text())
    assert set(house) == {"win_prob", "margin", "margin_lo", "margin_hi", "as_of"}
    assert 0.0 <= house["win_prob"] <= 1.0
    gov = json.loads((fc / "us-governor-2026-NV.json").read_text())
    assert gov["win_prob"] > 0.5  # NV leans Dem in the fixture -> Dem-favored governor race


def test_export_dates_partitions_by_cycle_sorted_by_state(tmp_path):
    _write_gold(tmp_path, "election_dates", [
        {"cycle": 2026, "state": "TX", "state_name": "Texas", "primary": "2026-03-03",
         "runoff": "2026-05-26", "general": "2026-11-03", "note": None},
        {"cycle": 2026, "state": "CA", "state_name": "California", "primary": "2026-06-02",
         "runoff": None, "general": "2026-11-03", "note": None},
        {"cycle": 2028, "state": "TX", "state_name": "Texas", "primary": "2028-03-07",
         "runoff": None, "general": "2028-11-07", "note": None},
    ])
    out = ew.export_dates(root=tmp_path, web_data=tmp_path / "web")
    assert {p.name for p in out} == {"2026.json", "2028.json"}  # one file per cycle
    rows_2026 = json.loads((tmp_path / "web" / "dates" / "2026.json").read_text())
    assert [r["state"] for r in rows_2026] == ["CA", "TX"]  # sorted by state name


def test_export_dates_skips_when_no_gold(tmp_path):
    assert ew.export_dates(root=tmp_path, web_data=tmp_path / "web") == []


def test_export_results_groups_by_race_with_race_level_fields(tmp_path):
    _write_gold(tmp_path, "primary_results", [
        {"race_id": "us-senate-2026-OH", "candidate": "Jane Doe", "party": "D", "votes": 600,
         "pct": 60.0, "election_type": "primary", "as_of": "2026-08-04T23:30:00+00:00",
         "is_certified": False, "pct_reporting": 90.0, "is_called": True, "called_by": "Jane Doe",
         "call_source": "Wikipedia", "source_url": "https://sos.oh/"},
        {"race_id": "us-senate-2026-OH", "candidate": "John Roe", "party": "R", "votes": 400,
         "pct": 40.0, "election_type": "primary", "as_of": "2026-08-04T23:30:00+00:00",
         "is_certified": False, "pct_reporting": 90.0, "is_called": True, "called_by": "Jane Doe",
         "call_source": "Wikipedia", "source_url": "https://sos.oh/"},
    ])
    out = ew.export_results(root=tmp_path, web_data=tmp_path / "web")
    assert {p.name for p in out} == {"us-senate-2026-OH.json"}
    rec = json.loads((tmp_path / "web" / "results" / "us-senate-2026-OH.json").read_text())
    assert rec["is_called"] is True and rec["called_by"] == "Jane Doe"
    assert rec["pct_reporting"] == 90.0 and rec["is_certified"] is False
    # candidates sorted by votes desc, race-level fields hoisted off the rows
    assert [c["candidate"] for c in rec["candidates"]] == ["Jane Doe", "John Roe"]
    assert rec["candidates"][0]["pct"] == 60.0


def test_export_results_skips_when_no_gold_or_empty(tmp_path):
    # no gold at all
    assert ew.export_results(root=tmp_path, web_data=tmp_path / "web") == []
    # honest-empty gold artifact (zero rows) → still nothing written, no invented numbers
    _write_gold(tmp_path, "primary_results", [])
    assert ew.export_results(root=tmp_path, web_data=tmp_path / "web") == []


def _house(state, district, dem, rep):
    return [
        {"race_id": f"us-house-2026-{state}-{district:02d}", "state": state, "office": "house",
         "district": district, "election_type": "general", "party": "D", "votes": dem},
        {"race_id": f"us-house-2026-{state}-{district:02d}", "state": state, "office": "house",
         "district": district, "election_type": "general", "party": "R", "votes": rep},
    ]


def test_export_fairness_honest_empty_without_results(tmp_path):
    # No results gold at all → nothing written (page keeps its honest pending state).
    assert ew.export_fairness(root=tmp_path, web_data=tmp_path / "web") == []
    # Even with a district geometry set, an empty results artifact stays honestly empty.
    _write_gold(tmp_path, "tiger", [{"state": "XX", "district": 1, "geoid": "XX01"}])
    _write_gold(tmp_path, "primary_results", [])
    assert ew.export_fairness(root=tmp_path, web_data=tmp_path / "web") == []


def test_export_fairness_skips_incomplete_or_single_district_states(tmp_path):
    # AA needs 3 CDs but only 2 reported → incomplete → skip. BB is a single-district (at-large)
    # state → an efficiency gap is meaningless → skip. Result: honest-empty, nothing written.
    _write_gold(tmp_path, "tiger", [
        {"state": "AA", "district": 1, "geoid": "AA01"},
        {"state": "AA", "district": 2, "geoid": "AA02"},
        {"state": "AA", "district": 3, "geoid": "AA03"},
        {"state": "BB", "district": 1, "geoid": "BB01"},
    ])
    _write_gold(tmp_path, "primary_results",
                _house("AA", 1, 60, 40) + _house("AA", 2, 45, 55) + _house("BB", 1, 51, 49))
    assert ew.export_fairness(root=tmp_path, web_data=tmp_path / "web") == []


def test_export_fairness_computes_for_a_complete_multi_district_state(tmp_path):
    _write_gold(tmp_path, "tiger", [
        {"state": "AA", "district": 1, "geoid": "AA01"},
        {"state": "AA", "district": 2, "geoid": "AA02"},
        {"state": "AA", "district": 3, "geoid": "AA03"},
    ])
    # AA fully reported: Dems win 1 of 3 despite ~48% statewide → a real EG toward Republicans.
    _write_gold(tmp_path, "primary_results",
                _house("AA", 1, 80, 20) + _house("AA", 2, 30, 70) + _house("AA", 3, 35, 65))
    [out] = ew.export_fairness(root=tmp_path, web_data=tmp_path / "web")
    rows = json.loads(out.read_text())
    assert len(rows) == 1 and rows[0]["state"] == "AA"
    assert set(rows[0]) == {"state", "efficiency_gap", "mean_median", "dem_seat_share", "dem_vote_share"}
    assert rows[0]["dem_seat_share"] == round(1 / 3, 4)
    assert -1.0 <= rows[0]["efficiency_gap"] <= 1.0


def test_export_demographics_tables_snapshot(tmp_path):
    _write_gold(tmp_path, "census_acs", [
        {"geoid": "3901", "state": "39", "district": "01", "population": 700000, "median_income": 60000},
        {"geoid": "3902", "state": "39", "district": "02", "population": 300000, "median_income": 80000},
    ])
    out = ew.export_demographics_tables(root=tmp_path, web_data=tmp_path / "web")
    assert len(out) == 2
    states = json.loads((tmp_path / "web" / "demographics" / "states.json").read_text())
    oh = next(r for r in states["rows"] if r["state"] == "39")
    assert oh["area"] == "Ohio"
    assert oh["population"] == 1_000_000
    districts = json.loads((tmp_path / "web" / "demographics" / "districts.json").read_text())
    assert districts["rows"][0]["area"] == "Ohio-01"


def test_export_demographic_changes_needs_two_years(tmp_path):
    # single-year (untagged) gold -> skipped, no placeholder change file
    _write_gold(tmp_path, "census_acs", [
        {"geoid": "3901", "state": "39", "district": "01", "population": 700000, "median_income": 60000},
    ])
    assert ew.export_demographic_changes(root=tmp_path, web_data=tmp_path / "web") == []


def test_export_demographic_changes_diffs_two_endpoints(tmp_path):
    _write_gold(tmp_path, "census_acs", [
        {"geoid": "3901", "state": "39", "district": "01", "population": 300000, "median_income": 80000, "year": 2018},
        {"geoid": "3901", "state": "39", "district": "01", "population": 330000, "median_income": 88000, "year": 2022},
        {"geoid": "3901", "state": "39", "district": "01", "population": 340000, "median_income": 90000, "year": 2023},
    ])
    out = ew.export_demographic_changes(root=tmp_path, web_data=tmp_path / "web")
    assert len(out) == 3
    web = tmp_path / "web" / "demographics-change"
    states = json.loads((web / "states.json").read_text())
    oh = next(r for r in states if r["state"] == "39")
    assert oh["area"] == "Ohio"
    assert oh["population_early"] == 300000  # 2018 endpoint
    assert oh["population_late"] == 340000   # 2023 endpoint
    districts = json.loads((web / "districts.json").read_text())
    assert districts[0]["area"] == "Ohio-01"
    assert districts[0]["population_delta"] == 10000  # CD diff = 2022 -> 2023 (same boundaries)
    meta = json.loads((web / "meta.json").read_text())
    assert meta["state_early_year"] == 2018 and meta["state_late_year"] == 2023
    assert meta["cd_early_year"] == 2022
    assert meta["state_crosses_redistricting"] is True
