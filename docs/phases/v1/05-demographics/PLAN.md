# Phase 5 · Demographics (ACS)

> Per-district / per-state demographics from Census ACS `[E3a,I2a]`, pre-aggregated to
> static JSON `[I7a]`. Units `v1.5.*`. Prereq: Phase 1 (geo + equivalency). Feeds the
> forecast fundamentals. Cite `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- ACS pulled via Census API (`api.data.gov` key), **pre-aggregated per district at build →
  static JSON** (no live API on hot path) `[I7a]`, yearly cadence, 400 d freshness floor.
- District-level keyed to a specific geometry version (`as_of`+cycle) `[I3a]`, ADR 0007.
- Urbanization classification via Census urbanized-area `[I?a]`.
- Every figure traces to the ACS `DATA_SOURCES` row.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.5.1-acs-connector` | v1.1.1 | Census ACS ingest via API, selected tables, schema-validated `[I2a,R7a]` | pending |
| `v1.5.2-district-aggregates` | 5.1,v1.1.3 | pre-aggregate per district+state → static JSON, keyed to geometry version `[I7a,I3a]` | pending |
| `v1.5.3-urbanization` | 5.2 | urbanized-area classification per district `[I?a]` | pending |
| `v1.5.4-demographics-ui` | 5.2,v1.2.3 | demographic panel on district/race pages, charts + source/`as_of` `[P7a,R14a]` | pending |
