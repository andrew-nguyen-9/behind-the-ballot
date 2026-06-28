# Phase 0 · Bootstrap & contracts

> Builds docs+schema+contracts+config format **before any business logic** `[ZZ5a]`.
> Unblocks every later phase. Units versioned `v1.0.*`. Gate: `04_DEFINITION_OF_DONE.md`.
> Cite `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- Astro site builds + deploys to a Cloudflare Pages preview `[P1a,P6a]`.
- CI runs the full gate workflow and is green on an empty placeholder page.
- A new race/state/module can be added by dropping **one config file** that validates
  against a published schema `[F4c,A7a]` — no code fork.
- ETL skeleton runs `--dry-run` end-to-end (no real sources yet) and bakes a sample
  artifact to CDN + R2 `[R6a,R11a]`.
- Design tokens render; DATA_SOURCES integrity check is wired into CI.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.0.1-repo-scaffold` | — | pnpm workspaces (web+pipeline), Astro+React islands, TS strict, Tailwind+shadcn, builds clean `[P1a,P12a,P4a,C10a]` | pending |
| `v1.0.2-ci-gate` | 0.1 | gate workflow (build, astro check, vitest, axe, Lighthouse, link/schema); Actions pinned SHAs; Dependabot `[S4a,V3a,V4a]` | pending |
| `v1.0.3-config-schema` | 0.1 | zod schema + types for a unit config (race/state/module); one example config validates `[F4c]` | pending |
| `v1.0.4-datastore-wiring` | 0.1 | Drizzle + Neon (small-state only) + R2 bucket; migration runs; `cycle` partition convention `[O2a,O4d,L843]` | pending |
| `v1.0.5-etl-skeleton` | 0.1 | bronze→silver→gold dirs, pydantic+zod validators, `--dry-run`, freshness check, artifact bake `[O12a,R6a,R7a,R5a]` | pending |
| `v1.0.6-data-integrity-check` | 0.5 | CI step asserts every published figure → a `03_DATA_SOURCES.md` row + freshness floor `[R14a]` | pending |
| `v1.0.7-design-tokens` | 0.1 | `design-system/` tokens (colorblind-safe party palette, civic neutral base), type scale `[C5a,C4a]` | pending |
| `v1.0.8-base-layout-seo` | 0.1,0.7 | shell layout, nav, sitemap, OG/meta, JSON-LD scaffold, security headers `[U3a,U4a,U5a,V5a]` | pending |

## Notes
Phase-0 units carry no real figures, so the integrity check runs against sample data; it
becomes load-bearing in Phase 1+.
