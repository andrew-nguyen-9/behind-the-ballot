# Phase 6 · Caucus/chamber + member analytics

> Member profiles for all 535 `[M10a]` + chamber composition (incl. Class II 2026 Senate
> `[J?a]`). Units `v1.6.*`. Prereq: Phase 1 (roster), Phase 3 (finance link). Cite
> `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- Roster = congress-legislators YAML + Congress.gov, both `[M1→C]`; photos from
  unitedstates/images `[M9a]`.
- Voting record from Congress.gov roll-call + GovTrack `[M2→C]`; ideology from Voteview
  DW-NOMINATE `[M3a]`.
- Member profile: bio, district, committees, key votes, finance, ideology `[M4a]`;
  sponsorship counts `[M5a]`, missed-votes `[M6a]`, cross-party cosponsorship index
  `[M7a]`.
- Full member ↔ race ↔ finance cross-link `[M8a]`. Cadence weekly + on new roll calls
  `[M11a]`, 7 d roll-call floor in session.
- Chamber view: composition + Class II 2026 computed automatically `[J?a]`.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.6.1-member-profiles` | v1.1.5 | profile pages (bio/district/committees/photo), all 535, in sitemap `[M4a,M9a,M10a]` | pending |
| `v1.6.2-rollcall-votes` | 6.1 | Congress.gov + GovTrack roll-calls; key votes, missed-votes `[M2a,M6a]` | pending |
| `v1.6.3-ideology` | 6.1 | Voteview DW-NOMINATE scores on profile `[M3a]` | pending |
| `v1.6.4-sponsorship-bipartisanship` | 6.2 | sponsored/cosponsored counts + cross-party index `[M5a,M7a]` | pending |
| `v1.6.5-member-crosslink` | 6.1,v1.3.3 | member ↔ race ↔ finance links wired `[M8a]` | pending |
| `v1.6.6-chamber-view` | 6.1 | chamber composition + Class II 2026 auto-computed `[J?a]` | pending |
