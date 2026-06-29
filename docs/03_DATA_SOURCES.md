# 03 · Data Sources

> The **contract** `[R14a]`: every published figure on the site maps to exactly one
> row below — source, URL, license, key, cadence, freshness floor. A figure with no
> row fails the verification gate (`04_DEFINITION_OF_DONE.md`). Decisions cite
> `brainstorming/BTB_QUESTIONNAIRE.md` as `[id]`.

## Open questions

- **Wikipedia / RCP for polling** `[H1a]` — Wikipedia race tables (CC BY-SA, attribute)
  and an RCP scrape (no clean license; ToS-gray). Default: **538 CSV is the spine**;
  Wikipedia is supplementary with attribution; **RCP scrape deferred** to `v1.x` and
  excluded from V1 figures until licensing is confirmed. Logged here, not blocking.
- **538 CSV longevity** — post-ABC-cuts the 538 polls CSV may move/freeze. Mirror each
  pull to R2 (bronze) so a dead upstream keeps last-good `[R8a]`; revisit source if it
  stops updating.

## Keys & access (free tier)

- **`api.data.gov`** is one key shared by FEC + Census + Congress.gov `[T6a]`. Single
  secret `DATA_GOV_API_KEY` in Actions secrets + host env `[T7a]`.
- **538**, **Voteview**, **congress-legislators**, **TIGER/Line** — no key (public
  files / bulk) `[T6a]`.
- Per-service signup uses a Cloudflare alias (`fec@…`, `census@…`) → one inbox `[T1d]`.

## Master source table

Cadence is per-source, independent `[R3a]`. Freshness floor = max age before the
nightly QA marks the figure stale and alerts `[R5a,S15a]`; pipeline keeps last-good and
opens an issue rather than publishing nothing `[R8a]`.

| Dataset / figures | Module | Source | URL | License | Key | Cadence `[R3a]` | Freshness floor `[R5a]` |
|---|---|---|---|---|---|---|---|
| Candidate filers, committees, contributions, disbursements, cash-on-hand | finance | OpenFEC API **+** FEC bulk `[G1→D]` | `api.open.fec.gov` / `cg-…fec.gov/bulk` | US public domain `[G14a]` | `api.data.gov` | weekly `[G3a]` | 14 d |
| Candidate→committee linkage (principal campaign cmte) | finance | OpenFEC linkages `[G12a]` | `api.open.fec.gov` | public domain | `api.data.gov` | weekly | 14 d |
| Poll results (HoR/Sen/Gov, by race) | polling | 538 polls CSV `[H1a]` ⚠️ **DEAD** (iter 60: endpoint returns ABC HTML shell; replacement pending — PROGRESS Open Q#1) | `projects.fivethirtyeight.com/polls/data/…csv` | 538 terms, attribute | none | daily | 3 d |
| Pollster quality ratings | polling | 538 pollster ratings `[H?a]` ⚠️ **DEAD** (same) | 538 ratings CSV | 538 terms, attribute | none | weekly | 30 d |
| Race rosters / candidate lists (supplementary) | tracker | Wikipedia race tables `[H1a]` | per-race wiki page | CC BY-SA, attribute | none | weekly | 30 d |
| ACS demographics per district/state | demographics | Census ACS via Census API `[I2a]` | `api.census.gov/data` | US public domain | `api.data.gov` | yearly (ACS release) `[I7a]` | 400 d |
| District ↔ geography equivalency (119th Congress) | demographics/geo | Census district equivalency `[I3a]` | census.gov equivalency files | public domain | none | per redistricting `[L547]` | event-driven |
| District / state boundary shapes | geo / gerrymander-lite | Census TIGER/Line `[K?a,I3a]` | `www2.census.gov/geo/tiger` | public domain | none | yearly + court orders `[L547]` | event-driven |
| Address → district lookup | tracker (find-my-district) | Census Geocoder API `[I?a]` | `geocoding.geo.census.gov` | public domain | none | on-request, cached `[R10a]` | n/a (cache 30 d) |
| Members of Congress (roster, bioguide, party, state, district) | members/caucus | congress-legislators YAML **+** Congress.gov `[Q?→C]` | `github.com/unitedstates/congress-legislators` / `api.congress.gov` | CC0 (YAML) / public domain | `api.data.gov` (Congress.gov) | weekly | 14 d |
| Committees & leadership | caucus/chamber | Congress.gov API `[Q?a]` | `api.congress.gov` | public domain | `api.data.gov` | weekly | 30 d |
| Roll-call votes | member analytics | Congress.gov roll-call **+** GovTrack `[Q?→C]` | `api.congress.gov` / `govtrack.us` | public domain / GovTrack terms | `api.data.gov` | daily (in session) | 7 d (in session) |
| Sponsored/cosponsored legislation counts | member analytics | Congress.gov sponsorship `[M5a]` | `api.congress.gov` | public domain | `api.data.gov` | weekly | 14 d |
| Ideology scores (DW-NOMINATE) | member analytics | Voteview `[Q?a]` | `voteview.com/data` | academic, free, attribute | none | per Congress | event-driven |
| Incumbents for race tracker | tracker | FEC filers + Congress.gov + Ballotpedia/Wikipedia `[F?→A]` | (above) | (above) | (above) | weekly | 30 d |

> Forecast (module) publishes **derived** figures — it has no upstream row of its own;
> its inputs are the polling + finance + demographics rows above, plus prior-cycle
> results. Provenance = the union of input rows, recorded per snapshot `[N1a,R14a]`.

## Pipeline contract (applies to every row)

- Python ETL, GitHub Actions cron per source `[R1c,R2a]`; bronze→silver→gold; mirror
  raw to R2 bronze so a dead upstream keeps last-good `[O12a,R8a,R11a]`.
- Idempotent upsert by natural key, no truncate, re-runnable `[R4a]`; parameterized
  `--cycle --since` backfill `[R13a]`.
- `--dry-run` smoke validates sources + schema before publish `[R6a]`; pydantic/zod on
  every record `[R7a]`; range/null/row-count assertions `[R9a]`.
- Cache + conditional requests + backoff, staggered across nights to respect free
  quotas `[R10a,T8a]`.
- Freshness display: finance shows "through `<coverage_end_date>`" per filing `[G13a]`;
  every figure carries an `as_of`.

## Attribution

FEC/Census/Congress.gov/Geocoder/TIGER = US public domain (no attribution required, we
credit anyway). OpenSecrets (if added later) requires attribution `[G14a]`. Wikipedia =
CC BY-SA. Voteview + GovTrack = credit per their terms. A site-wide `/sources` page
renders this table `[R14a]`.
