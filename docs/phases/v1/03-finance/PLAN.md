# Phase 3 · Campaign finance (FEC)

> Per-candidate / per-race money: receipts, disbursements, cash-on-hand, from OpenFEC API
> + bulk `[G1→D]`. Units `v1.3.*`. Prereq: Phase 1 + Phase 2 (race/candidate refs). Cite
> `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- Connector pulls OpenFEC (`api.data.gov` key) + bulk, weekly cadence, 14 d freshness
  floor `[G3a,R5a]`; idempotent upsert `[R4a]`.
- Candidate↔committee linkage via FEC principal campaign committee `[G12a]`.
- Every figure shows "through `<coverage_end_date>`" `[G13a]` and traces to the FEC
  `DATA_SOURCES` row.
- FEC public-domain attribution rendered `[G14a]`.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.3.1-fec-connector` | v1.1.1 | OpenFEC API + bulk ingest, weekly cron, cache+backoff, schema-validated `[G1a,R10a,R7a]` | pending |
| `v1.3.2-candidate-committee-link` | 3.1 | principal-campaign-committee linkage table `[G12a]` | pending |
| `v1.3.3-finance-aggregates` | 3.2 | gold artifacts: receipts/disbursements/cash-on-hand per candidate+race, `coverage_end_date` `[G13a]` | pending |
| `v1.3.4-finance-ui` | 3.3,v1.2.3 | finance figures on race + candidate pages (charts via Observable Plot), coverage label, attribution `[P7a,G13a,G14a]` | pending |
