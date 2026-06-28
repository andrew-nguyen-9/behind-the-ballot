# V1 Planning — Progress Ledger

Dual purpose: (1) the ledger this **planning** loop reads to pick the next doc;
(2) the template the **build** loop will reuse for race/module units. A fresh
session reconstructs all state from this file. One activity-log line per touched row.

Status: `pending | in-progress | review | blocked | done`. Pick the first `pending`
whose prereq is `done`.

## RESUME

Next: `docs/phases/v1/LOOP_PROMPT.md` (P11, self-contained build loop + gate +
token/session rules). Then build ledger (P12), design-system (P13), ACCOUNTS (P14).
(P0–P10 done: full doc spine incl. all 11 segment PLANs.)

## Planning-doc units

| # | Unit (doc) | Prereq | Status |
|---|---|---|---|
| P0 | branch `planning/v1-docs` | — | done |
| P1 | `docs/phases/v1/PROGRESS.md` (this ledger) | P0 | done |
| P2 | `docs/01_PRODUCT_VISION.md` | P1 | done |
| P3 | `docs/02_ARCHITECTURE.md` | P2 | done |
| P4 | `docs/03_DATA_SOURCES.md` | P2 | done |
| P5 | `docs/04_DEFINITION_OF_DONE.md` | P2 | done |
| P6 | `docs/VERSIONING.md` | P2 | done |
| P7 | `docs/WORKFLOW.md` | P2 | done |
| P8 | `docs/adr/` (framework, datastore+tiering, no-PostGIS geo, forecast, email/alias, search/bloom, redistricting, loop-architecture) | P3 | done |
| P9 | `docs/phases/v1/PHASES_OVERVIEW.md` (the spine) | P3,P4,P5 | done |
| P10 | `docs/phases/v1/<segment>/PLAN.md` (per segment) | P9 | done (11 segments) |
| P11 | `docs/phases/v1/LOOP_PROMPT.md` (build loop + gate + token/session rules) | P9 | pending |
| P12 | seed build-loop ledger rows into a build `PROGRESS.md` | P11 | pending |
| P13 | `design-system/` seed + logo brief | P2 | pending |
| P14 | `docs/ACCOUNTS.md` | P4 | pending |

## Activity log

- P0–P2: branched, seeded ledger, wrote Product Vision (cited to answers). — iter 1
- P4: 03_DATA_SOURCES.md — master source table (FEC/538/Census/Congress.gov/
  Voteview/congress-legislators/TIGER/Geocoder), keys, cadence, freshness floors,
  pipeline contract. Flagged RCP/Wikipedia licensing as open Qs. — iter 2
- P5–P7: DEFINITION_OF_DONE (10-point gate + evidence), VERSIONING
  (v[phase].[segment].[task]), WORKFLOW (main-wall branch ritual, QA cadence).
  Corrected outbound email to Gmail SMTP [S9c/T4b], not Resend. — iter 2
- P8: 8 ADRs + index (framework, datastore-tiering, geo-no-postgis, forecast,
  email-alias, search, redistricting-versioning, loop-architecture). — iter 3
- P9: PHASES_OVERVIEW — 11 phases (0 bootstrap → 1 data foundation → 2–7 module
  slices → 8 forecast → 9 SEO/search → 10 loop-scale), scope in/out, why-order,
  locked decisions, cross-cutting AC, Phase-0 contents. — iter 4
- P10 (part): PLAN.md for phases 0 bootstrap, 1 data-foundation, 2 tracker,
  3 finance, 4 polling — each with acceptance criteria + unit table. — iter 5
- P10 (rest): PLAN.md for phases 5 demographics, 6 members/chamber, 7
  gerrymander-lite, 8 forecast, 9 SEO/search, 10 loop-scale. All 11 done. — iter 6
