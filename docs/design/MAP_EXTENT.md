# Map extent decision (Session B → E-4)

Open question from `spec.md`: E-4 interactive-map extent — MapLibre GL + PMTiles (per the
`02_ARCHITECTURE.md` geo stack) vs. stay 0-JS static SVG. Decided against the perf budget.

## Decision

**Required this cycle: data-wiring only, 0-JS.** Wire the existing gerrymander fairness
metrics (`geometry.py` Polsby-Popper/Reock/convex-hull + `fairness.py` efficiency-gap/
mean-median/seats-votes/wasted-votes) to real House-on-current-lines data where available,
rendered with the existing static components (`USStateMap`/`HouseArc` pattern) and the
multi-metric-with-caveats presentation. No single-verdict framing.

**Interactive tiled map (MapLibre + PMTiles): STRETCH, opt-in island, not required.** If and
only if the data-wiring lands with budget to spare, add an interactive district map as a
**progressive-enhancement island** — 0-JS baseline (static SVG + a11y data-table) must render
fully without it. Constraints if built:

- Tiles are **PMTiles on R2, one per layer per cycle** (`02_ARCHITECTURE.md` §Geo) — no Mapbox
  token, no runtime tile server. MapLibre GL loads only inside the hydrated island.
- Must not regress Lighthouse ≥90 mobile on the route; the map route carries its own JS budget
  and lazy-hydrates (`client:visible`). If it can't hold the budget, ship without it.
- a11y: map has a data-table equivalent + ARIA (`02_ARCHITECTURE.md` §Geo, `[Q8a,W8a]`).

**Find-my-district (Census Geocoder): backlog, not this cycle.** Log to `docs/BACKLOG.md`.

## Rationale

The deadline-critical work is results (wave 0/1); E-4 is non-critical wave-2 depth. The
fairness data-wiring is the durable value and is fully achievable 0-JS. A tiled interactive
map is high-JS and high-risk against the perf gate for marginal added value this cycle —
correct to gate it behind "budget permitting" rather than commit to it. Ship the certain win;
treat the map as a bonus that must prove it holds the budget or is dropped without regret.
