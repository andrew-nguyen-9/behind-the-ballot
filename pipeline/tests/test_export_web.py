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
