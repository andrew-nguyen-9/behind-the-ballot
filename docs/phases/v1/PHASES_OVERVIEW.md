# V1 · Phases Overview (the spine)

> Dependency-ordered milestones for V1. Each phase decomposes into segments, each
> segment into units the build loop picks off `PROGRESS.md`. Versioning
> `v[phase].[segment].[task]` (`VERSIONING.md`). Every decision cites the answered
> `brainstorming/BTB_QUESTIONNAIRE.md` `[id]`. Phase 0 builds docs+schema+contracts+
> config format **before any business logic** `[ZZ5a]`.

## Phase table

| Phase | Name | Unblocks | Key Q |
|---|---|---|---|
| 0 | Bootstrap & contracts | all | `[P1a,P4a,O1a,ZZ5a]` |
| 1 | Data foundation (pipeline + geo + roster) | 2–8 | `[R*,O12a,I3a]` |
| 2 | Race tracker | 4,8 | `[E1a,F4c]` |
| 3 | Campaign finance | 8 | `[E2a,G*]` |
| 4 | Polling aggregation | 8 | `[H*]` |
| 5 | Demographics | 8 | `[E3a,I*]` |
| 6 | Caucus/chamber + member analytics | — | `[Q*]` |
| 7 | Gerrymander-lite | — | `[K*,L7a]` |
| 8 | Forecast | — | `[N1a,N8a]` |
| 9 | SEO / content / search | — | `[U*,L891,Y8a]` |
| 10 | Loop scale + nightly QA + alerts | — | `[S7a,S9c,F4c]` |

All work branches `unit/* → dev`; humans own `main` `[S5a]`.

## In V1 / Out (deferred)

| In V1 | id | Out (deferred) | id |
|---|---|---|---|
| Race tracker | `[E11a]` | Issue analytics (stub) | `[E6a]` |
| Campaign finance (FEC) | `[E2a]` | Party-demo analytics (stub) | `[J2a]` |
| Polling aggregation | `[H1a]` | RCP scrape | `[H1a-note]` |
| Forecast (heuristic+MC) | `[N1a]` | Forecast ML | `[N8a]` |
| Demographics (ACS) | `[E3a]` | Pollster own-rating | `[H?a-note]` |
| Caucus/chamber + members | `[Q*]` | OpenSecrets enrich | `[G14a]` |
| Gerrymander-lite | `[K*]` | | |
| SEO + a11y + perf (cross-cutting) | `[U*,W1a,X1a]` | | |

## Why this order

Phase 0 lays the **contracts** (config format, DATA_SOURCES, the gate, CI) so every later
unit is just "fill a config + bake artifacts," not a fork of code `[F4c,A7a]`. Phase 1
builds the **shared data spine** — the ETL framework (bronze→silver→gold `[O12a]`), the
geometry/tiles `[I3a]`, and the member roster `[Q?c]` — because tracker, demographics,
gerrymander, and members all key to districts + people. Module slices (2–7) come next,
each independently shippable. **Forecast (8) waits** on polling + finance + demographics
since those are its inputs `[N1a]`. SEO/content/search (9) layers over real pages. Loop
scale + nightly QA (10) turns the per-module machinery into config-driven coverage grind
across all states/races + the regression alarm `[S7a]`.

## Locked decisions (thread through every phase)

| Concern | Decision | Q / ADR |
|---|---|---|
| Framework / host | Astro + React islands, CF Pages | `[P1a,P6a]` / ADR 0001 |
| Datastore | Neon small state; R2 + static bulk | `[O2a]` / ADR 0002 |
| Geo | Offline GeoPandas, PMTiles, no PostGIS | `[L7a]` / ADR 0003 |
| Forecast | Heuristic + Monte Carlo first | `[N1a]` / ADR 0004 |
| Email | CF aliases in, Gmail SMTP out | `[T1d,T4b]` / ADR 0005 |
| Search | Pagefind static index | `[L891]` / ADR 0006 |
| Redistricting | geometry versioned by `as_of`+cycle | `[L547]` / ADR 0007 |
| Build | orchestrator + cold workers, ledger | `[S1a,S3a]` / ADR 0008 |
| Config-driven units | a race/state/module = one config | `[F4c,A7a]` |
| Pipeline | Python ETL, Actions cron per source | `[R1c,R2a]` |

## Cross-cutting acceptance criteria (stated once, applied to every unit)

The full gate is `04_DEFINITION_OF_DONE.md`: build + `astro check` + tests + axe (WCAG 2.2
AA) + Lighthouse ≥90 mobile + **data integrity (figure → DATA_SOURCES row, freshness floor
met)** + SEO + security headers + responsive screenshots 360/768/1280, re-run by the
orchestrator with evidence `[S4a,S14a]`. These are **not** separate phases — they gate
every unit in every phase.

## Phase 0 contents (the "before business logic" bootstrap) `[ZZ5a]`

- Repo scaffold: Astro + pnpm workspaces (web + pipeline) + TS strict + Tailwind/shadcn
  `[P1a,P12a,P4a,C10a]`.
- CI: the gate as a workflow (build, check, test, axe, Lighthouse, link/schema), Actions
  pinned to SHAs, Dependabot `[V3a,V4a]`.
- **Config format** for a race/state/module unit `[F4c]` — the schema every later unit
  fills.
- Drizzle + Neon connection (small-state only) + R2 bucket wiring `[O2a,O4d]`.
- ETL skeleton: bronze→silver→gold dirs, pydantic/zod validators, `--dry-run`, freshness
  check, artifact bake to CDN/R2 `[R6a,R7a,R5a,R11a]`.
- Design-system tokens seeded (`design-system/`, ADR-aligned palette) `[C5a,C4a]`.
- `DATA_SOURCES.md` wired into the integrity check.

Each is a unit on the build ledger (`PROGRESS.md`), `v1.0.*`.
