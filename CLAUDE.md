# Behind the Ballot — build contract

Non-partisan 2026 U.S. midterm tracking + analytics. Static-first: **Astro 5 SSG + React
islands, Tailwind v4, TS strict** (`apps/web`) + **Python (uv) ETL** (`pipeline`), hosted on
**Cloudflare** (Pages/Workers + R2), small state in **Neon Postgres**. Architecture:
`docs/02_ARCHITECTURE.md`; full gate: `docs/04_DEFINITION_OF_DONE.md`; data contract:
`docs/03_DATA_SOURCES.md`; live-results runbook: `docs/RESULTS_GO_LIVE.md`.

## DoD

DoD: re-run and paste before any unit is "done" (full gate in `docs/04_DEFINITION_OF_DONE.md`).
Web: `pnpm --filter web check` (astro check + tsc strict, 0 errors) && `pnpm --filter web test`
(vitest) && `pnpm --filter web build` (SSG + Pagefind). Pipeline changes also:
`uv run --project pipeline pytest pipeline/tests -q` && `uv run --project pipeline ruff check pipeline`
&& `uv run --project pipeline python -m btb_pipeline.cli --dry-run` &&
`uv run --project pipeline python -m btb_pipeline.integrity` (exit 0). Cross-cutting, enforced
in CI: WCAG 2.2 AA (axe 0 serious/critical) · Lighthouse ≥90 mobile · every published figure
traces to a `docs/03_DATA_SOURCES.md` row + meets its freshness floor (or is hidden, never
shown silently) · security headers + no secret in client bundle + Actions pinned to SHAs.

## Secrets

Secrets: GitHub Actions secrets + host (Cloudflare) env; local dev in `.env` (gitignored — see
`docs/SETUP_SECRETS.md`). Never committed. Provisioned: DATA_GOV_API_KEY (spans FEC/Census/
Congress), CENSUS_API_KEY, Cloudflare API token/account id/R2, Neon DATABASE_URL, Gmail SMTP.

## Branches

Branches: unit branches use prefix `feat/`; **local-merge integration model** — long-lived
`integration` branched off `main`, units branch off `integration`, D fast-forwards `main`.
Default branch: `main`. **`main` is production** — V2 policy: ship-to-prod on green DoD, but the
**first production cutover is human-gated** (see `.orchestrator/blockers.md`). `dev` mirrors
`main` (legacy promotion branch; currently `dev == main`).
