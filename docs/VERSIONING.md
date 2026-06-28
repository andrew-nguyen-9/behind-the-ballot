# Versioning

> Scheme: **`v[phase].[segment].[task]`**. Mirrors the plan tree so a version number
> points at an exact ledger unit. Decisions cite the questionnaire `[id]`.

## Scheme

`v<phase>.<segment>.<task>`

- **phase** — top-level milestone in `phases/v1/PHASES_OVERVIEW.md` (0 = bootstrap).
- **segment** — a module/area slice within the phase (its `PLAN.md`).
- **task** — the unit within the segment, as listed on `PROGRESS.md`.

Example: `v1.3.2` = phase 1, segment 3 (e.g. polling), task 2 (e.g. aggregation island).
`v1.0.x` = Phase-0 docs/schema/contracts before any business logic `[ZZ5a]`.

## Rules

- Each shipped unit bumps its task number; a finished segment is tagged `v<phase>.<segment>.0`.
- The git tag matches the version; the PR title carries it.
- Pre-1.0 of the public site overall: the deployed site is "V1" until every V1 module
  unit is `done` and green at a live preview — that flips the `V1 COMPLETE` promise.
- Deferred scope (issue analytics, party-demo `[E6a,J2a]`) lands in a later `v1.x` /
  `v2`, tracked in `docs/BACKLOG.md`, never back-filled into a V1 task number.
