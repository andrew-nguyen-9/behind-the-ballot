import pytest

from btb_pipeline.demographics import build_district_demographics, rollup_by_state

ACS = [
    {"geoid": "3903", "state": "OH", "district": "03", "population": 700000, "median_income": 60000},
    {"geoid": "3901", "state": "OH", "district": "01", "population": 300000, "median_income": 80000},
    {"geoid": "4205", "state": "PA", "district": "05", "population": 500000, "median_income": 70000},
]


def test_build_tags_geometry_version_and_sorts():
    rows = build_district_demographics(ACS, "2026-01-15")
    assert [r["geoid"] for r in rows] == ["3901", "3903", "4205"]  # sorted
    assert all(r["geometry_as_of"] == "2026-01-15" for r in rows)


def test_build_requires_geometry_version():
    with pytest.raises(ValueError):
        build_district_demographics(ACS, "")


def test_rollup_population_and_weighted_income():
    rows = build_district_demographics(ACS, "2026-01-15")
    states = rollup_by_state(rows)
    oh = next(s for s in states if s["state"] == "OH")
    assert oh["population"] == 1_000_000  # 700k + 300k
    # pop-weighted income: (60000*700000 + 80000*300000) / 1000000 = 66000
    assert oh["median_income"] == 66000
    assert [s["state"] for s in states] == ["OH", "PA"]  # sorted
