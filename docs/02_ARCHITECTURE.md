# 02 · Architecture

> Decisions cite `brainstorming/BTB_QUESTIONNAIRE.md` as `[id]`. Free-tier on
> everything; static-first; DB only where it earns its place.

## Open questions

- **Neon 500 MB free cap** (answer note, finance itemized + Census are large) → see
  ADR `datastore-tiering`. Rule below: Postgres holds only small queryable state;
  everything bulk/derived lives static or in R2.

## Shape (data flow)

```
upstream APIs/bulk  ──►  Python ETL (GitHub Actions, cron per source)  [R1c,R2a,R3a]
  FEC, Census, Congress.gov,        │  bronze → silver → gold  [O12a]
  Voteview, 538, congress-          │  validate (pydantic) [R7a], dry-run smoke [R6a],
  legislators, TIGER, Geocoder      │  idempotent upsert by natural key [R4a]
                                    ▼
        ┌──────────────── published artifacts ────────────────┐
        │  baked JSON + Parquet (per route, per cycle)         │  ← hot reads [O6a,O7a]
        │  PMTiles (district geometry, per layer per cycle)    │  ← R2 [O4d,Q2a,Q10a]
        │  Neon Postgres (small queryable state only)          │  ← forecast snapshots,
        └──────────────────────────────────────────────────────┘     feed items, search meta
                                    ▼
   Astro SSG + React islands  [P1a,P5a]  ──►  Cloudflare Pages (CDN)  [P6a]
   static HTML + minimal JS; islands hydrate maps/charts/forecast only
```

## Frontend

- **Astro** content shell + **React islands** `[P1a,P3a]` — diversifies from prior
  Next.js work while keeping React hireable; ship minimal JS, static by default `[X2a]`.
- **TypeScript strict** everywhere `[P4a]`. **pnpm** workspaces, single repo (web +
  pipeline) `[P12a,P13a]`.
- **SSG + islands**; on-demand/ISR **only** for live election-night results `[P5a,F6a]`.
- Charts **Observable Plot + D3** `[P7a]`; maps **MapLibre GL + PMTiles** `[P8a]`;
  styling **Tailwind + shadcn/ui (Radix)** `[C10a,C9a]`; icons **Lucide** `[C12a]`.
- Articles **MDX in repo**, live figures embeddable `[P11a,Y8a]`.
- Tests **Vitest + Playwright**; axe in CI `[P14a,W9a]`.

## Data & storage tiering `[O1a,O2a,O4d,O6a]`

| Tier | Holds | Where |
|---|---|---|
| **bronze** | raw upstream pulls | `data/bronze/<cycle>/<source>/`; small canonical committed, large gitignored + refetch, archived to **R2** `[O4d]` |
| **silver** | cleaned/typed | CI-only intermediate |
| **gold** | published figures | **baked JSON + Parquet** per route/cycle, served on CDN `[O7a]` |
| **DB (Neon Postgres)** | *only* small queryable state: forecast daily snapshots, `feed_items`, search metadata | Neon free `[O2a,O9a]` — **never on the hot read path** `[O6a]` |
| **blobs** | PMTiles, bulk CSV, raw filings | **R2** (free egress) `[O4d]` |

- **Drizzle** ORM + migrations `[O8a]`. **No PostGIS** — geometry/compactness computed
  offline with GeoPandas/Shapely in CI → static JSON `[O17a,L6a,L7a]`.
- Partition everything by **`cycle`** (2026, 2028…) from day one `[O16a]`.
- Provenance: `as_of` + `source_hash` on every dataset `[O11a]`; every figure → a
  `DATA_SOURCES.md` row `[R14a]`.
- **Search:** static client index (**Pagefind**) `[O14a]`; ADR notes compact-index /
  bloom-filter techniques for scale (answer L891). Own-data **API = static JSON
  endpoints**, documented `[O15a]`.
- **Backups:** git is the backup for static; weekly Neon snapshot → R2 `[O13a]`.

## Pipeline `[R*]`

- **Python** (pandas/geopandas/requests) `[R1c]`; **GitHub Actions cron, independent
  schedule per source** (finance weekly, polls daily, etc.) `[R2a,R3a]`.
- Idempotent upsert by natural key, re-runnable, no truncate `[R4a]`; `--dry-run`
  validates sources+schema first `[R6a]`; **freshness floors** per source → alert if
  stale `[R5a]`; fail one source → keep last-good + open issue `[R8a]`.
- Schema validation (pydantic) on every record `[R7a]`; range/null/row-count data
  tests `[R9a]`; cache + conditional requests to respect quotas `[R10a]`.
- Output: commit JSON/Parquet + push blobs to R2 `[R11c]`; pinned env (uv) `[R12a]`;
  parameterized `--cycle --since` backfill `[R13a]`.

## Geo `[Q*,L*]`

Minimal custom base map (no Mapbox token) `[Q1a]`; PMTiles vector, pre-simplified per
zoom via tippecanoe `[Q2a,Q3a,L5a]`; address→district via **Census Geocoder** `[Q5a]`;
tiles on R2, one PMTiles per layer per cycle `[Q10a]`. Map a11y = data-table
equivalent + ARIA `[Q8a,W8a]`.

## Hosting, secrets, budget

Cloudflare Pages `[P6a]`. Secrets in **GitHub Actions secrets + host env**, never
committed `[O18a]`. **Measured constraints** (not storage): Actions minutes, API
quotas (one `api.data.gov` key spans FEC/Census/Congress), R2/CDN bandwidth — budget
alarms at 80% `[O10a,T9a]`. Stagger jobs across nights to stay free.

## Cross-cutting (every build unit, enforced in CI — not separate phases)

WCAG 2.2 AA `[W1a]` · Lighthouse ≥90 mobile `[U8a]` · perf budgets `[X1a]` · JSON-LD +
sitemap + per-page OG `[U3a,U4a,U5a]` · CSP/HSTS headers + Dependabot + pinned Action
SHAs `[V5a,V3a,V4a]` · every figure traces to a source row + freshness floor `[R14a,R5a]`.
See `04_DEFINITION_OF_DONE.md`.
