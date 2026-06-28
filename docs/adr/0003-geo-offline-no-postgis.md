# 0003 · Offline geo, no PostGIS

**Status:** Accepted · 2026-06-28

## Context
District/state maps and address→district lookup need geometry processing, but PostGIS
on Neon free tier is heavy and adds a live spatial DB we don't want to operate.

## Decision
Do **all geometry work offline in CI with GeoPandas** `[O17a]`; **no PostGIS** `[L7a]`.
Ship **PMTiles** (per layer, per cycle) to R2 for MapLibre GL to read directly
`[P8a,Q2a]`. Address→district uses the **Census Geocoder API**, cached `[I?a,R10a]`.
District ↔ geography via **Census equivalency + TIGER/Line** `[I3a]`.

## Consequences
- No spatial DB to run or pay for; geometry is precomputed artifacts.
- Map updates are a CI job that regenerates tiles, not live queries.
- Point-in-polygon at request time is avoided in favor of the Geocoder + cache.
- Court-ordered map changes trigger a tile rebuild (see ADR 0007).
