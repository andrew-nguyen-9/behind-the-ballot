# Phase 7 · Gerrymander-lite

> District compactness + partisan-fairness metrics, computed **offline** `[L6a,L7a]`,
> multi-metric with a "metrics disagree" caveat — **no single verdict** `[L8a]`. Units
> `v1.7.*`. Prereq: Phase 1 (geo/tiles). Cite `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- Compactness: **Polsby-Popper + Reock + convex-hull** `[L2a]`; partisan-fairness:
  **efficiency gap + mean-median** with caveats `[L3a]`.
- Computed in Python GeoPandas/Shapely in CI → static JSON; tiles via tippecanoe→PMTiles
  on R2 `[L5a,L6a]`. No PostGIS `[L7a]` (ADR 0003).
- Framing is multi-metric + "metrics disagree" caveat, no composite score `[L8a]`; full
  formulas + limitations page `[L14a]`.
- Historical pre/post-2020 comparison where notable `[L9a]`; court-ordered changes tracked
  per state, sourced `[L10a]` (ADR 0007). Ensemble/simulation deferred `[L11a]`.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.7.1-compactness-metrics` | v1.1.2 | Polsby-Popper + Reock + convex-hull per district → JSON `[L2a]` | pending |
| `v1.7.2-fairness-metrics` | 7.1 | efficiency gap + mean-median per state, with caveats `[L3a]` | pending |
| `v1.7.3-gerrymander-ui` | 7.1,7.2 | map + metric panel, "metrics disagree" framing, no verdict `[L8a]` | pending |
| `v1.7.4-leaderboard` | 7.1 | most/least compact leaderboard + map `[L12a]` | pending |
| `v1.7.5-methodology-page` | 7.2 | full formulas + limitations page `[L14a]` | pending |
