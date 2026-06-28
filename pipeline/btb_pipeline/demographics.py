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
