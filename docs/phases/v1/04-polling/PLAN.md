# Phase 4 · Polling aggregation

> Per-race poll aggregation from the 538 polls CSV `[H1a]`, with pollster-quality
> weighting `[H?a]`. Units `v1.4.*`. Prereq: Phase 1 + Phase 2. Feeds the forecast.
> Cite `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- Connector pulls the 538 polls CSV daily, 3 d freshness floor, mirrors raw to R2 bronze
  (dead-upstream → last-good) `[H1a,R5a,R8a]`.
- Aggregation weights by 538 pollster ratings where available `[H?a]`; method published
  for neutrality.
- Wikipedia race tables are **supplementary with attribution**; **RCP scrape excluded**
  from V1 figures (open question, licensing) `[H1a-note]`.
- Every aggregate traces to its source rows + shows `as_of`.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.4.1-poll-connector` | v1.1.1 | 538 CSV ingest, daily cron, R2 bronze mirror, schema-validated `[H1a,R8a,R7a]` | pending |
| `v1.4.2-pollster-ratings` | 4.1 | 538 pollster ratings joined as weights `[H?a]` | pending |
| `v1.4.3-aggregation` | 4.2 | weighted polling average per race (trend + CI), method doc, gold artifact `[H?a]` | pending |
| `v1.4.4-polling-ui` | 4.3,v1.2.3 | polling trend chart on race page, `as_of` + source list `[P7a,R14a]` | pending |
