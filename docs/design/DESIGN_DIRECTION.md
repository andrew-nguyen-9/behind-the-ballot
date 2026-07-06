# Design Direction — North Star (Session B brainstorm → E-F1 builds `design/INDEX.md`)

Durable design decisions for the V2 rebrand. E-F1 expands this into `design/INDEX.md`
(the shipped North Star); E-D1 rolls it out site-wide. Keep it honest, neutral, fast.

## Identity: "The Civic Lattice"

Logo direction is **decided** — see `docs/brainstorming/LOGO.md` §"A Premium Direction:
The Civic Lattice". Core mark: **12 identical rounded-rectangle modules on a disciplined
grid**; rotating/offsetting a few modules lets negative space read as ballot-into-slot +
capitol dome + upward trend without drawing any of them literally.

- **16px favicon:** clean geometric emblem, no secondary meaning required to read.
- **Large sizes:** the hidden geometry emerges.
- **Dynamic system (optional, not required for E-F1):** one highlighted module; its position/
  density can shift per context (state vs county). Ship the static mark first; the live
  election-night "modules illuminate" behavior is a stretch, not a gate.
- Geometric, rounded corners, consistent stroke widths. Theme-aware (light/dark). Replaces
  the current inline ballot-box glyph.

## Voice

Neutral, precise, quietly confident. We report; we do not editorialize. Swiss-typography
sensibility: precision, neutrality, trust. Numbers speak; chrome recedes. Never imply
certainty we don't have — "provisional", "% reporting", "as-of" are first-class UI, not
footnotes.

## Motion principles

Motion clarifies, never decorates. It shows **state change** (a total updating, a race
being called, a district connecting) and **spatial relationships** (where a number came
from). It is always cuttable.

- **`prefers-reduced-motion` is a hard kill-switch**, not a dimmer. Reduced-motion users get
  the final state instantly, zero transition. This is a DoD/a11y gate, not a nicety.
- Token the system in `global.css @theme`: a small scale of **durations** (e.g. instant/
  fast/base/slow) + **easings** (standard/decelerate/accelerate). Components reference tokens,
  never hardcode ms. One place to retune the whole feel.
- Budget: motion is CSS-first (transitions/keyframes). JS-driven animation only inside an
  island that already hydrates for another reason — never add JS to a 0-JS page for motion.
- Election-night motion (counts filling, bars growing) reuses the same tokens; it is E-R9/
  E-D1 territory, seeded here.

## Loading philosophy

Static-first means most pages have **no loading state** — they're pre-baked HTML. Loading
UI exists only for (a) island hydration (charts/maps/search) and (b) genuinely live surfaces
(election-night results refresh). Principle: **skeleton over spinner** — reserve layout, show
the shape of the content, avoid layout shift (CLS is a Lighthouse gate). Honest-empty
(`EmptyState`) is distinct from loading; never show a spinner where the truth is "no data".

E-F1 ships ≥1 reusable skeleton/loading component + tests, honoring reduced-motion.

## Non-negotiables inherited by every design unit

- 0-JS-first; islands hydrate only maps/charts/search. Motion must not break the no-JS baseline.
- WCAG 2.2 AA (axe 0 serious/critical), Lighthouse ≥90 mobile, colorblind-safe party palette
  (party colors only in data viz). Focus visible, keyboard reachable, contrast met.
- Party/neutrality rules unchanged: no single-verdict framing; multi-metric with caveats.
