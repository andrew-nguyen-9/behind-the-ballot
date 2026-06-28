# 0002 · Datastore & storage tiering

**Status:** Accepted · 2026-06-28

## Context
Neon Postgres free tier caps at **500 MB** (answer note L843). FEC itemized records and
Census ACS are far larger than that. Reads are mostly hot, per-route, repeatable.

## Decision
**Neon Postgres** `[O2a]` holds **only small queryable state**: forecast snapshots, feed
items, search metadata. Everything bulk/derived is **baked JSON/Parquet on the CDN** for
hot reads `[O6a,O7a]` and **R2** for blobs/tiles/bulk + bronze raw mirror `[O4d,R11a]`.
ORM **Drizzle** `[O8a]`. Partition data by **`cycle`**; prune raw to R2 `[L843]`.

## Consequences
- Postgres stays well under 500 MB; no surprise overage.
- Most pages read static artifacts → fast, cacheable, no DB on the hot path.
- A figure that needs ad-hoc query must justify its place in Postgres or be pre-aggregated.
- Bulk history lives in R2; queries over it are batch/ETL, not live.
