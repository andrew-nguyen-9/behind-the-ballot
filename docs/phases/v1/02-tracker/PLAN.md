# Phase 2 · Race tracker

> The core: per-race pages (House/Senate/Governor) with candidates, incumbency, status.
> The first config-driven module — a race = one config `[F4c]`. Units `v1.2.*`. Prereq:
> Phase 1 (roster + geo). Cite `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- A race page is generated from **one race config** + baked artifacts; adding a race is a
  config drop `[F4c,A7a]`.
- Candidates sourced from FEC filers + Congress.gov incumbents + Ballotpedia/Wikipedia
  rosters `[F?→A]`; every shown figure traces to a `DATA_SOURCES` row.
- Incumbency, party (colorblind-safe palette `[C5a]`), district link, and status render;
  map island shows the district from PMTiles `[P8a]`.
- "Find my district" uses the geocoder `[I?a]`.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.2.1-race-config` | v1.0.3 | race config schema (office, state, district, cycle, candidate refs) validates `[F4c]` | pending |
| `v1.2.2-candidate-roster` | v1.1.5 | candidate artifact: FEC filers + Congress.gov incumbents + wiki rosters, deduped `[F?a]` | pending |
| `v1.2.3-race-page` | 2.1,2.2 | per-race SSG page: candidates, incumbency, party, status; gate-green at preview | pending |
| `v1.2.4-district-map-island` | v1.1.2 | MapLibre island renders the race's district tile; lazy-hydrated `[P8a,X2a]` | pending |
| `v1.2.5-find-my-district` | v1.1.4 | address input → district → race links, via geocoder cache `[I?a]` | pending |
| `v1.2.6-race-index` | 2.3 | browsable/filterable index of all races; in sitemap, JSON-LD `[U3a]` | pending |
