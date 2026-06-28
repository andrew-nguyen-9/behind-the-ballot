# Phase 1 · Data foundation (pipeline + geo + roster)

> The shared data spine every module keys to: the ETL framework, district geometry, and
> the member/people roster. Unblocks phases 2–8. Units `v1.1.*`. Prereq: Phase 0 done.
> Cite `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- A source connector is **config-driven**: declaring a source + cadence + freshness floor
  is enough to schedule its Actions cron and validate it `[R2a,R3a,R5a]`.
- District + state geometry is processed **offline** (GeoPandas in CI) into PMTiles on R2,
  versioned by `as_of`+`cycle`; **no PostGIS** `[O17a,L7a]` (ADR 0003, 0007).
- A canonical member roster (bioguide-keyed) is baked and queryable, joining
  congress-legislators YAML + Congress.gov `[Q?→C]`.
- Address→district lookup works via Census Geocoder, cached `[R10a]`.
- Idempotent upsert by natural key; `--cycle --since` backfill; last-good on failure
  `[R4a,R13a,R8a]`.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.1.1-etl-framework` | v1.0.5 | source-connector base: schedule from config, cache+backoff, conditional requests, upsert, last-good `[R2a,R10a,R4a,R8a]` | pending |
| `v1.1.2-geo-tiles` | v1.0.4 | GeoPandas CI job → district/state PMTiles to R2, versioned `as_of`+`cycle`; TIGER source `[L7a,L547,I3a]` | pending |
| `v1.1.3-district-equivalency` | 1.2 | Census equivalency mapping units across geometry versions; baked lookup `[I3a]` | pending |
| `v1.1.4-geocoder` | 1.1 | address→district via Census Geocoder API, cached 30 d `[I?a,R10a]` | pending |
| `v1.1.5-member-roster` | v1.1.1 | congress-legislators YAML + Congress.gov → canonical bioguide roster artifact `[Q?→C]` | pending |
| `v1.1.6-artifact-bake` | v1.1.1 | gold→baked JSON/Parquet per route+cycle to CDN; manifest with `as_of` `[O6a,O7a]` | pending |

## Notes
Connectors for module-specific sources (FEC, 538, ACS, roll-calls, Voteview) live in their
**own module phases** but reuse `v1.1.1`'s base — keeps each module independently shippable.
