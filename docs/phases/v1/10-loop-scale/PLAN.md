# Phase 10 · Loop scale + nightly QA + alerts

> Turns the per-module machinery into **config-driven coverage** across all states/races
> `[F4c]`, plus the regression alarm. Units `v1.10.*`. Prereq: module phases shippable.
> Cite `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- All in-scope races/states/members exist as **config units** the loop grinds without code
  forks `[F4c,A7a]`; coverage is complete for V1 scope.
- Nightly scheduled Action re-runs the gate against the **live** site + validates data
  freshness `[S7a,S15a]`; Playwright + Lighthouse CI + link/schema checks `[S8a]`.
- On regression: **open/update a deduped GitHub issue** `[S11a]` **and email** the
  maintainer (Gmail SMTP `[S9c,T4b]`) with summary + diff + run link + severity `[S10a]`.
- Budget alarms at 80% of Actions minutes + API quotas `[T9a]`; stagger crons across
  nights `[T8a]`. Higher-level weekly review via a Claude routine `[S18a]`.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.10.1-coverage-configs` | phases 2–8 | config units for all V1 races/states/members; coverage report green `[F4c]` | pending |
| `v1.10.2-nightly-qa` | 10.1 | scheduled gate vs live site + freshness validation; Playwright+LHCI+link/schema `[S7a,S8a]` | pending |
| `v1.10.3-regression-alerts` | 10.2 | dedup GitHub issue + Gmail-SMTP email w/ summary+diff+link+severity `[S9c,S10a,S11a]` | pending |
| `v1.10.4-budget-alarms` | 10.2 | Actions-minutes + API-quota tracking, alert at 80% `[T9a]` | pending |
| `v1.10.5-weekly-review-routine` | 10.2 | Claude scheduled routine for higher-level weekly review `[S18a]` | pending |
