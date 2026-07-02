"""Demographics aggregates [I7a]: reshape Census ACS rows into per-district artifacts
tagged with the geometry version (as_of + cycle, ADR 0007) and per-state rollups the
demographics UI consumes. Pure transform over the `census_acs` gold artifact.

ponytail: a tag + a rollup; the ACS connector already lands per-district rows. Keying to
a geometry version is what lets a district page show "boundaries as of <date>" [L547].
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DistrictDemographics(BaseModel):
    model_config = ConfigDict(extra="ignore")

    geoid: str
    state: str | None = None
    district: str | None = None
    population: int | None = None
    median_income: int | None = None
    geometry_as_of: str  # which boundary version these figures are keyed to [L547]


def build_district_demographics(acs_rows: list[dict], geometry_as_of: str) -> list[dict]:
    """Tag each ACS row with the geometry version it's keyed to [I3a]. Sorted by geoid."""
    if not geometry_as_of:
        raise ValueError("geometry_as_of required (which boundary version) [L547]")
    out = [
        DistrictDemographics.model_validate({**r, "geometry_as_of": geometry_as_of}).model_dump()
        for r in acs_rows
    ]
    return sorted(out, key=lambda x: x["geoid"])


def rollup_by_state(rows: list[dict]) -> list[dict]:
    """Per-state totals: summed population + population-weighted median income. Rows with
    no state skipped. Sorted by state."""
    states: dict[str, dict] = {}
    for r in rows:
        st = r.get("state")
        if not st:
            continue
        agg = states.setdefault(st, {"state": st, "population": 0, "_inc_wsum": 0.0, "_pop_w": 0})
        pop = r.get("population") or 0
        agg["population"] += pop
        inc = r.get("median_income")
        if inc is not None and pop:
            agg["_inc_wsum"] += inc * pop
            agg["_pop_w"] += pop
    out = []
    for agg in states.values():
        median_income = round(agg["_inc_wsum"] / agg["_pop_w"]) if agg["_pop_w"] else None
        out.append({"state": agg["state"], "population": agg["population"], "median_income": median_income})
    return sorted(out, key=lambda x: x["state"])


def _pct(old: int | None, new: int | None) -> float | None:
    """Percent change old -> new, 1 dp. None when either endpoint is missing or old is 0."""
    if old is None or new is None or old == 0:
        return None
    return round((new - old) / old * 100, 1)


def _delta_fields(early: dict, late: dict) -> dict:
    """population/median_income at each endpoint + absolute & percent change [E2.4]."""
    pe, pl = early.get("population"), late.get("population")
    ie, il = early.get("median_income"), late.get("median_income")
    return {
        "population_early": pe,
        "population_late": pl,
        "population_delta": (pl - pe) if pe is not None and pl is not None else None,
        "population_pct": _pct(pe, pl),
        "median_income_early": ie,
        "median_income_late": il,
        "median_income_delta": (il - ie) if ie is not None and il is not None else None,
        "median_income_pct": _pct(ie, il),
    }


def _rows_for_year(rows: list[dict], year: int) -> list[dict]:
    return [r for r in rows if r.get("year") == year]


def build_state_changes(acs_rows: list[dict], early_year: int, late_year: int) -> list[dict]:
    """Per-state population + median-income change between two ACS end-years [E2.4, Q7.5].

    Rolls each year up to state totals (rollup_by_state), then diffs states present in BOTH
    years. State boundaries are stable across ACS vintages, so a state diff is clean even
    across a redistricting (unlike the district diff below). Sorted by state (FIPS)."""
    early = {r["state"]: r for r in rollup_by_state(_rows_for_year(acs_rows, early_year))}
    late = {r["state"]: r for r in rollup_by_state(_rows_for_year(acs_rows, late_year))}
    out = [
        {"state": st, "early_year": early_year, "late_year": late_year, **_delta_fields(early[st], late[st])}
        for st in early.keys() & late.keys()
    ]
    return sorted(out, key=lambda r: r["state"])


def build_district_changes(acs_rows: list[dict], early_year: int, late_year: int) -> list[dict]:
    """Per-district (CD) change between two ACS end-years, joined by geoid [E2.4].

    ECOLOGICAL / BOUNDARY CAVEAT [L547]: a geoid join is only valid when BOTH years use the
    SAME district boundaries (e.g. both post-2020 / 118th-Congress maps — the first such ACS
    5-year is 2022). Across a redistricting the same code is a different geography, so callers
    must pass same-boundary endpoints. Districts present in both years only. Sorted by geoid."""
    early = {r["geoid"]: r for r in _rows_for_year(acs_rows, early_year)}
    late = {r["geoid"]: r for r in _rows_for_year(acs_rows, late_year)}
    out = [
        {
            "geoid": gid,
            "state": late[gid].get("state"),
            "district": late[gid].get("district"),
            "name": late[gid].get("name"),
            "early_year": early_year,
            "late_year": late_year,
            **_delta_fields(early[gid], late[gid]),
        }
        for gid in early.keys() & late.keys()
    ]
    return sorted(out, key=lambda r: r["geoid"])
