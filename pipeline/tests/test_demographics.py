import pytest

from btb_pipeline.demographics import (
    build_district_changes,
    build_district_demographics,
    build_state_changes,
    rollup_by_state,
)

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


# Two ACS end-years for the change transforms (rows tagged with `year`) [E2.4].
ACS_2Y = [
    {"geoid": "3901", "state": "39", "district": "01", "population": 300000, "median_income": 80000, "year": 2018},
    {"geoid": "3903", "state": "39", "district": "03", "population": 700000, "median_income": 60000, "year": 2018},
    {"geoid": "3901", "state": "39", "district": "01", "population": 330000, "median_income": 88000, "year": 2023},
    {"geoid": "3903", "state": "39", "district": "03", "population": 700000, "median_income": 60000, "year": 2023},
    {"geoid": "4205", "state": "42", "district": "05", "population": 500000, "median_income": 70000, "year": 2018},
    # 42 has no 2023 row -> excluded from the diff (present in both years only).
]


def test_state_changes_abs_and_pct_delta():
    [oh] = [r for r in build_state_changes(ACS_2Y, 2018, 2023) if r["state"] == "39"]
    assert oh["population_early"] == 1_000_000  # 300k + 700k
    assert oh["population_late"] == 1_030_000   # 330k + 700k
    assert oh["population_delta"] == 30_000
    assert oh["population_pct"] == 3.0
    assert oh["early_year"] == 2018 and oh["late_year"] == 2023


def test_state_changes_drops_states_missing_an_endpoint():
    states = build_state_changes(ACS_2Y, 2018, 2023)
    assert [s["state"] for s in states] == ["39"]  # 42 lacks a 2023 row


def test_district_changes_joins_by_geoid_and_computes_delta():
    rows = build_district_changes(ACS_2Y, 2018, 2023)
    assert [r["geoid"] for r in rows] == ["3901", "3903"]  # sorted, both years present
    d = {r["geoid"]: r for r in rows}
    assert d["3901"]["population_delta"] == 30_000
    assert d["3901"]["median_income_pct"] == 10.0  # 80000 -> 88000
    assert d["3903"]["population_delta"] == 0
    assert d["3903"]["population_pct"] == 0.0


def test_change_pct_is_none_when_endpoint_missing_or_zero():
    rows = build_district_changes(
        [
            {"geoid": "0100", "state": "01", "population": 0, "median_income": None, "year": 2018},
            {"geoid": "0100", "state": "01", "population": 100, "median_income": 50000, "year": 2023},
        ],
        2018,
        2023,
    )
    assert rows[0]["population_pct"] is None  # old is 0 -> undefined pct
    assert rows[0]["median_income_delta"] is None  # missing early income
