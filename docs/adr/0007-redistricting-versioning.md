# 0007 · Redistricting / district-geometry versioning

**Status:** Accepted · 2026-06-28

## Context
2026 districts can change mid-cycle by court order (open question L547). Figures keyed to
a district must stay correct as the map under them shifts.

## Decision
Version district geometry: every boundary set carries an **`as_of` date + `cycle`**, and
state-level map changes are tracked per state `[L547]`. Demographics, results, and tiles
all reference a specific geometry version; a court-ordered change is a **new version**, not
an in-place edit. TIGER/Line is the base; equivalency files map units across versions
`[I3a]`.

## Consequences
- A district page can show "boundaries as of `<date>`" and historical comparisons stay
  valid.
- A map change triggers: new tiles (ADR 0003) + re-aggregation of demographics for the
  affected state, keyed to the new version.
- Adds a version dimension to district-keyed tables/artifacts — partition with `cycle`.
