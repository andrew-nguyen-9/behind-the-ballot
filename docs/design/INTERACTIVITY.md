# Interactivity — prioritized enhancement set (Session B brainstorm → E-3)

The rule for every item: **progressive enhancement over a 0-JS baseline**. The page must be
complete, correct, and accessible with JavaScript disabled; interactivity is added by an
island that hydrates on top. No item may regress Lighthouse ≥90 mobile or the perf budget,
and each honors `prefers-reduced-motion` (motion tokens from E-F1).

Priority tiers — E-3 ships Tier 1 for sure, Tier 2 if budget allows, Tier 3 is backlog.

## Tier 1 — ship (high value, low JS, clean no-JS fallback)

1. **Chart hover/scrub readout.** A hover (and keyboard-focus) tooltip on the existing
   Observable-Plot/D3 charts showing the exact value under the cursor. No-JS fallback: the
   `DataTable` companion already renders every value; the chart is decorative-plus. Delivered
   as a reusable island component under `components/charts/` so E-5/E-D1 can adopt it.
2. **Filterable dashboards (client refine).** The server already renders the full list (0-JS);
   an island adds instant client-side filter/sort on top of `FilterBar`/`DataTable`. No-JS:
   full unfiltered list is present and usable. Reuse existing `filterBar`/`dataTable` logic.
3. **Animated forecast reveal.** On the forecast surface, bars/distribution animate from 0 to
   final on first view (IntersectionObserver), reduced-motion → final state instantly. Pure
   CSS transition triggered by an island; no-JS → final state rendered directly.

## Tier 2 — if perf budget holds

4. **Scrubbable forecast timeline** over `forecast_snapshots` (slider → island swaps a
   pre-baked snapshot; all snapshots already static). No-JS: latest snapshot shown.
5. **Map hover highlight** on the results/gerrymander choropleths (county name + value on
   hover/focus). No-JS: the a11y data-table equivalent already carries the values.

## Tier 3 — backlog (do NOT build this cycle; log to `docs/BACKLOG.md`)

- Cross-filtering / brushing between charts. Real-time websocket updates. Anything needing a
  runtime API or third-party JS. These break the static-first + no-tracking invariants.

## Ownership seam (why E-3 doesn't collide with E-5/E-D1)

E-3 **owns the reusable interaction islands** (`apps/web/src/components/charts/*`) and applies
them on chart-heavy pages it owns outright: `chamber.astro`, `house.astro`, `senate.astro`.
E-5 (dashboards) and E-D1 (rollout) **embed** those islands on the `[id]` pages and elsewhere —
they depend on E-3, they don't re-implement it. This keeps writes disjoint within the wave.
