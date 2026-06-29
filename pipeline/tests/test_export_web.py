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
