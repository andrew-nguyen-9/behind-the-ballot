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

    out = ew.export_members(root=tmp_path, web_data=tmp_path / "web")
    roster = json.loads(out.read_text())
    by_id = {r["bioguide_id"]: r for r in roster}
    assert by_id["A1"]["party"] == "D"
    assert by_id["A1"]["nominate_dim1"] == -0.3
    assert by_id["B2"]["party"] == "R"
    assert by_id["B2"]["nominate_dim1"] is None  # no ideology row → None, not missing key
    assert by_id["B2"]["district"] == 5


def test_export_members_skips_when_no_gold(tmp_path):
    assert ew.export_members(root=tmp_path, web_data=tmp_path / "web") is None
