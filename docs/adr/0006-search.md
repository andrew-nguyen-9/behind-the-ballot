# 0006 · Search

**Status:** Accepted · 2026-06-28

## Context
Site needs search over races, members, articles, districts. A server search service adds
infra and cost; the site is static-first on a free tier (open question L891).

## Decision
**Pagefind** — a static client-side index generated at build, served from the CDN, no
backend. For scale beyond what a single downloaded index serves comfortably, the upgrade
path is a **sharded / compact index with a bloom-filter prefilter** to avoid shipping the
whole index to the client `[L891]`.

## Consequences
- Zero search infra; works on static hosting.
- Index size grows with content → watch the downloaded-bytes budget `[X1a]`; shard when
  it crosses the perf budget.
- No typo-tolerant server ranking in V1; acceptable for the content scale.

`// ponytail: Pagefind until the index measurably blows the perf budget, then shard.`
