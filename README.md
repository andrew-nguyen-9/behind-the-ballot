# Behind the Ballot

Non-partisan tracking and analytics for the 2026 U.S. midterms — and every election
after. **Every published figure traces to a public data source** with a freshness floor.

> Status: V1 in active build on `dev`. The full app + pipeline are built and tested
> against sample data; live data + deployment are pending account provisioning (see
> [`docs/ACCOUNTS.md`](docs/ACCOUNTS.md)). `main` is intentionally untouched until a human
> promotes `dev`.

## What's here

| Area | Tech | Notes |
|---|---|---|
| Web app | Astro 5 SSG + React islands, Tailwind v4, TS strict | static-first, 0-JS pages (bar search) |
| Pipeline | Python (uv), pydantic, numpy, shapely | bronze→silver→gold ETL, fixture-tested |
| Hosting (planned) | Cloudflare Pages + R2 | static + blobs/tiles |
| Data (planned) | Neon Postgres (small state only) | bulk → R2 / baked JSON |

Architecture and decisions: [`docs/02_ARCHITECTURE.md`](docs/02_ARCHITECTURE.md) +
[`docs/adr/`](docs/adr/). The data contract: [`docs/03_DATA_SOURCES.md`](docs/03_DATA_SOURCES.md).

## Layout

```
apps/web/        Astro site (pages, layouts, lib, config-driven race/data fixtures)
pipeline/        Python ETL — connectors (FEC/538/Census/Congress/Voteview), forecast,
                 gerrymander metrics, data-integrity gate
docs/            Planning docs, ADRs, per-phase plans, the build ledger (phases/v1/PROGRESS.md)
design-system/   Tokens (colorblind-safe party palette) + logo brief
.github/         CI gate workflow (build, test, Lighthouse, axe) + Dependabot
```

## Develop

```bash
# Web (Node 22+, pnpm)
pnpm install
pnpm --filter web dev        # local dev server
pnpm --filter web check      # astro check + tsc (strict)
pnpm --filter web test       # vitest
pnpm --filter web build      # SSG build + Pagefind search index

# Pipeline (uv)
uv run --project pipeline pytest pipeline/tests -q
uv run --project pipeline ruff check pipeline
uv run --project pipeline python -m btb_pipeline.cli --dry-run
```

Current health: **153 tests green** (121 Python + 32 web), `astro check` 0/0/0, 14 pages.

## The build loop

This repo is built by an autonomous loop. The contract is
[`docs/phases/v1/LOOP_PROMPT.md`](docs/phases/v1/LOOP_PROMPT.md); live state + the unit
ledger are in [`docs/phases/v1/PROGRESS.md`](docs/phases/v1/PROGRESS.md). `main` is a wall —
work merges to `dev`; a human owns `main`.

## Forecast (methodology)

Heuristic-first: per-race win probability blends a recency/quality-weighted polling
average with fundamentals (partisan lean, incumbency, finance); a Monte Carlo simulation
with correlated national swing turns per-race probabilities into a chamber seat
distribution + control probability. Backtested and calibration-checked before publishing;
an ML challenger is adopted only if it beats the heuristic. See `pipeline/btb_pipeline/`
(`aggregate`, `baseline`, `race_model`, `montecarlo`, `backtest`, `forecast`).

## Neutrality

Non-partisan by construction: party colors appear only in data viz (colorblind-safe),
multiple gerrymander metrics are shown with caveats (no single verdict), and every figure
links to its source on [`/sources`](docs/03_DATA_SOURCES.md).
