# V1 Planning — Progress Ledger

Dual purpose: (1) the ledger this **planning** loop reads to pick the next doc;
(2) the template the **build** loop will reuse for race/module units. A fresh
session reconstructs all state from this file. One activity-log line per touched row.

Status: `pending | in-progress | review | blocked | done`. Pick the first `pending`
whose prereq is `done`.

## RESUME

Next: `docs/04_DEFINITION_OF_DONE.md` + `VERSIONING.md` + `WORKFLOW.md` (P5–P7),
then ADRs (P8). (Ledger, 01_PRODUCT_VISION, 02_ARCHITECTURE, 03_DATA_SOURCES done.)

## Planning-doc units

| # | Unit (doc) | Prereq | Status |
|---|---|---|---|
| P0 | branch `planning/v1-docs` | — | done |
| P1 | `docs/phases/v1/PROGRESS.md` (this ledger) | P0 | done |
| P2 | `docs/01_PRODUCT_VISION.md` | P1 | done |
| P3 | `docs/02_ARCHITECTURE.md` | P2 | done |
| P4 | `docs/03_DATA_SOURCES.md` | P2 | done |
| P5 | `docs/04_DEFINITION_OF_DONE.md` | P2 | pending |
| P6 | `docs/VERSIONING.md` | P2 | pending |
| P7 | `docs/WORKFLOW.md` | P2 | pending |
| P8 | `docs/adr/` (framework, datastore+tiering, no-PostGIS geo, forecast, email/alias, search/bloom, redistricting, loop-architecture) | P3 | pending |
| P9 | `docs/phases/v1/PHASES_OVERVIEW.md` (the spine) | P3,P4,P5 | pending |
| P10 | `docs/phases/v1/<segment>/PLAN.md` (per segment) | P9 | pending |
| P11 | `docs/phases/v1/LOOP_PROMPT.md` (build loop + gate + token/session rules) | P9 | pending |
| P12 | seed build-loop ledger rows into a build `PROGRESS.md` | P11 | pending |
| P13 | `design-system/` seed + logo brief | P2 | pending |
| P14 | `docs/ACCOUNTS.md` | P4 | pending |

## Activity log

- P0–P2: branched, seeded ledger, wrote Product Vision (cited to answers). — iter 1
- P4: 03_DATA_SOURCES.md — master source table (FEC/538/Census/Congress.gov/
  Voteview/congress-legislators/TIGER/Geocoder), keys, cadence, freshness floors,
  pipeline contract. Flagged RCP/Wikipedia licensing as open Qs. — iter 2
