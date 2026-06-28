# V1 Planning — Progress Ledger

Dual purpose: (1) the ledger this **planning** loop reads to pick the next doc;
(2) the template the **build** loop will reuse for race/module units. A fresh
session reconstructs all state from this file. One activity-log line per touched row.

Status: `pending | in-progress | review | blocked | done`. Pick the first `pending`
whose prereq is `done`.

## RESUME

**Phase A (planning) COMPLETE** — P0–P14 all done: full doc tree (01–04, VERSIONING,
WORKFLOW, 8 ADRs, PHASES_OVERVIEW, 11 segment PLANs), self-contained LOOP_PROMPT.md,
60-unit build ledger below, design-system seed + logo brief, ACCOUNTS.

Next: **Phase B (build)** via `LOOP_PROMPT.md` — first eligible build unit
`v1.0.1-repo-scaffold` (pure code, no account). Account-gated units (Neon/CF/domain/
API keys, 2FA) are human-only → mark `blocked`, log, build code-only units meanwhile.
`V1 COMPLETE` only when all build units `done` + live preview + gates green sitewide.

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
| P11 | `docs/phases/v1/LOOP_PROMPT.md` (build loop + gate + token/session rules) | P9 | done |
| P12 | seed build-loop ledger rows (## Build ledger below) | P11 | done |
| P13 | `design-system/` seed + logo brief | P2 | done |
| P14 | `docs/ACCOUNTS.md` | P4 | done |

## Build ledger (Phase B — the units LOOP_PROMPT.md grinds)

All `pending`. Pick first eligible whose prereq is `done`. Detail per unit lives in the
matching `<segment>/PLAN.md`. Prereqs use the version slug. Build RESUME (Phase B): `v1.0.6-data-integrity-check` (then 0.8 base-layout-seo).
0.4 datastore is account-blocked. After Phase 0: Phase 1 has account-blocked data
units; eligible code-only ones thin out — expect more `blocked` rows ahead. Account-gated units (need Neon/R2/domain/API keys + 2FA) → `blocked` until the
human provisions: **v1.0.4-datastore-wiring** and every data connector
(v1.1.x/v1.3.x/v1.4.x/v1.5.x/v1.6.x) + live-preview gate parts.
Build branches: `dev` (integration) ← `unit/*`. `main` untouched `[S5a]`.

| Unit | Prereq | Status |
|---|---|---|
| v1.0.1-repo-scaffold | — | done |
| v1.0.2-ci-gate | v1.0.1 | done |
| v1.0.3-config-schema | v1.0.1 | done |
| v1.0.4-datastore-wiring | v1.0.1 | pending |
| v1.0.5-etl-skeleton | v1.0.1 | done |
| v1.0.6-data-integrity-check | v1.0.5 | pending |
| v1.0.7-design-tokens | v1.0.1 | done |
| v1.0.8-base-layout-seo | v1.0.1, v1.0.7 | pending |
| v1.1.1-etl-framework | v1.0.5 | pending |
| v1.1.2-geo-tiles | v1.0.4 | pending |
| v1.1.3-district-equivalency | v1.1.2 | pending |
| v1.1.4-geocoder | v1.1.1 | pending |
| v1.1.5-member-roster | v1.1.1 | pending |
| v1.1.6-artifact-bake | v1.1.1 | pending |
| v1.2.1-race-config | v1.0.3 | pending |
| v1.2.2-candidate-roster | v1.1.5 | pending |
| v1.2.3-race-page | v1.2.1, v1.2.2 | pending |
| v1.2.4-district-map-island | v1.1.2 | pending |
| v1.2.5-find-my-district | v1.1.4 | pending |
| v1.2.6-race-index | v1.2.3 | pending |
| v1.3.1-fec-connector | v1.1.1 | pending |
| v1.3.2-candidate-committee-link | v1.3.1 | pending |
| v1.3.3-finance-aggregates | v1.3.2 | pending |
| v1.3.4-finance-ui | v1.3.3, v1.2.3 | pending |
| v1.4.1-poll-connector | v1.1.1 | pending |
| v1.4.2-pollster-ratings | v1.4.1 | pending |
| v1.4.3-aggregation | v1.4.2 | pending |
| v1.4.4-polling-ui | v1.4.3, v1.2.3 | pending |
| v1.5.1-acs-connector | v1.1.1 | pending |
| v1.5.2-district-aggregates | v1.5.1, v1.1.3 | pending |
| v1.5.3-urbanization | v1.5.2 | pending |
| v1.5.4-demographics-ui | v1.5.2, v1.2.3 | pending |
| v1.6.1-member-profiles | v1.1.5 | pending |
| v1.6.2-rollcall-votes | v1.6.1 | pending |
| v1.6.3-ideology | v1.6.1 | pending |
| v1.6.4-sponsorship-bipartisanship | v1.6.2 | pending |
| v1.6.5-member-crosslink | v1.6.1, v1.3.3 | pending |
| v1.6.6-chamber-view | v1.6.1 | pending |
| v1.7.1-compactness-metrics | v1.1.2 | pending |
| v1.7.2-fairness-metrics | v1.7.1 | pending |
| v1.7.3-gerrymander-ui | v1.7.1, v1.7.2 | pending |
| v1.7.4-leaderboard | v1.7.1 | pending |
| v1.7.5-methodology-page | v1.7.2 | pending |
| v1.8.1-baseline-fundamentals | v1.5.2 | pending |
| v1.8.2-race-model | v1.8.1, v1.4.3, v1.3.3 | pending |
| v1.8.3-montecarlo-chamber | v1.8.2 | pending |
| v1.8.4-backtest-calibration | v1.8.2 | pending |
| v1.8.5-ml-challenger | v1.8.4 | pending |
| v1.8.6-forecast-ui | v1.8.3 | pending |
| v1.8.7-snapshot-store | v1.8.3 | pending |
| v1.9.1-search | phases 2–8 | pending |
| v1.9.2-sitemap-jsonld | phases 2–8 | pending |
| v1.9.3-articles-mdx | v1.0.8 | pending |
| v1.9.4-sources-page | — | pending |
| v1.9.5-home-nav | v1.9.1 | pending |
| v1.10.1-coverage-configs | phases 2–8 | pending |
| v1.10.2-nightly-qa | v1.10.1 | pending |
| v1.10.3-regression-alerts | v1.10.2 | pending |
| v1.10.4-budget-alarms | v1.10.2 | pending |
| v1.10.5-weekly-review-routine | v1.10.2 | pending |

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
- P11–P12: LOOP_PROMPT.md (self-contained build contract: Step 0, loop, gate,
  main-wall, token/session sleep rules, completion) + seeded 60-unit build ledger
  above (v1.0.1–v1.10.5) with prereq DAG. — iter 7
- **Phase B start** v1.0.1-repo-scaffold: pnpm monorepo (apps/web Astro 5 + React
  islands + Tailwind v4 + TS strict + shadcn-ready cn util) + Python pipeline (uv).
  Gate: pnpm build green, astro check 0/0/0, static index ships 0 JS. Branch
  unit/v1.0.1 → merged dev. main untouched. Env note: PRs merged locally (no
  remote); gh-PR flow applies once a remote exists. — iter 9
- v1.0.2-ci-gate: .github/workflows/gate.yml (build-test, lighthouse-a11y LHCI
  >=0.9 mobile, pipeline-lint ruff), Dependabot, lighthouserc, scripts/check-links.mjs.
  Actions SHA-pinned. Local gate green (check 0/0/0, vitest 2/2, build, links).
  CI Lighthouse/uv run on GitHub once a remote exists. → merged dev. — iter 10
- v1.0.3-config-schema: zod UnitConfig discriminated union (race kind), cross-field
  rules, SourceBinding for integrity check, example OH-senate JSON, 4 schema tests.
  Gate: check 0/0/0, vitest 6/6, build, links. → merged dev. — iter 11
- v1.0.5-etl-skeleton: pipeline core.py (SourceSpec, validate_records, is_fresh,
  dry_run, bake gold+manifest) + sample source + CLI; hatchling build-system,
  uv.lock. Gate: pytest 4/4, ruff clean, dry-run+bake verified. → dev. — iter 12
- v1.0.7-design-tokens: Tailwind v4 @theme — party blue/red/purple [C5a], civic
  neutrals w/ dark override [C4a,C6a], sans+serif, reduced-motion. Tokens verified
  compiled into output CSS; index showcases swatches. Gate green. → dev. — iter 13
- P13–P14: design-system seed (neutral civic chrome + colorblind-safe party viz
  palette, type, motion-with-reduced-motion, components) + LOGO_BRIEF; ACCOUNTS
  (services/aliases/free-limits/80% alarms, no secrets). **Phase A complete.** — iter 8
