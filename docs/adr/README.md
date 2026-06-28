# Architecture Decision Records

Short, dated records of load-bearing decisions. Each cites the answered
`brainstorming/BTB_QUESTIONNAIRE.md` id `[X#a]`. Format: Status · Context · Decision ·
Consequences. Supersede, don't rewrite history.

| # | Decision | Q |
|---|---|---|
| [0001](0001-framework.md) | Astro + React islands, TS strict, Cloudflare Pages | `[P1a,P4a,P6a]` |
| [0002](0002-datastore-tiering.md) | Neon Postgres for small state; R2 + static for bulk | `[O2a,O4d,O6a]` |
| [0003](0003-geo-offline-no-postgis.md) | Offline GeoPandas in CI, PMTiles; no PostGIS | `[O17a,L7a]` |
| [0004](0004-forecast-method.md) | Heuristic + Monte Carlo first; ML only if it beats it | `[N1a,N8a]` |
| [0005](0005-email-alias.md) | CF Email Routing aliases inbound; Gmail SMTP outbound | `[T1d,T4b,S9c]` |
| [0006](0006-search.md) | Pagefind static index; bloom/compact index at scale | `[L891]` |
| [0007](0007-redistricting-versioning.md) | District geometry versioned by `as_of` + cycle | `[L547]` |
| [0008](0008-loop-architecture.md) | Orchestrator + cold workers, ledger-driven, main-wall | `[S1a,S3a,S5a]` |
