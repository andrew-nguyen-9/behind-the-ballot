# Behind the Ballot — Design North Star

The shipped, durable design system for the V2 rebrand: **"The Civic Lattice."** This is the
authoritative reference (it supersedes the `docs/design/DESIGN_DIRECTION.md` brainstorm, which
seeded it). Keep it honest, neutral, fast. Every design decision traces back here.

## Load map — read only what your task needs

Split so agents (and humans) load the minimum. `INDEX.md` is always first; then:

| Task | Load |
| --- | --- |
| **Building UI / components / pages** (dev) | `INDEX.md` + [`FOUNDATIONS.md`](./FOUNDATIONS.md) + [`UI-KIT.md`](./UI-KIT.md) |
| **Writing copy / labels / microcopy** | `INDEX.md` + [`VOICE.md`](./VOICE.md) |
| **Retuning tokens / motion / a11y** | `INDEX.md` + [`FOUNDATIONS.md`](./FOUNDATIONS.md) |

Do **not** re-derive taste from scratch — read the relevant file, then build.

## The idea in one paragraph

A symbol built from **12 identical rounded-rectangle modules** on a disciplined 4×3 grid. A
rising subset steps bottom-left → top-right (an upward trend) toward **one highlighted apex
module**; the ghosted lattice and the gaps let negative space read as ballot-into-slot and a
capitol dome without drawing any literally. At 16px it's a clean geometric emblem; large, the
structure emerges. It balances institutional trust with modern data-viz — at home on a
government report or a real-time dashboard. Full concept: `docs/brainstorming/LOGO.md`
§"The Civic Lattice".

## Non-negotiables (inherited by every design unit)

- **0-JS first.** Islands hydrate only maps/charts/search. Motion must not break the no-JS
  baseline — it's CSS-first (see `FOUNDATIONS` → Motion).
- **`prefers-reduced-motion` is a hard kill-switch,** not a dimmer: reduced-motion users get
  the final state instantly, zero transition. This is an a11y/DoD gate.
- **WCAG 2.2 AA** (axe 0 serious/critical), **Lighthouse ≥90 mobile**, focus visible, keyboard
  reachable, contrast met. No layout shift (CLS is a gate) — loading reserves layout.
- **Neutrality.** Party colors are data-viz only, never brand chrome. No single-verdict framing;
  provisional/% -reporting/as-of are first-class UI. See `VOICE`.

## What ships where

- Tokens: `apps/web/src/styles/global.css` `@theme` (colors, type, radius, **motion**).
- Logo: `apps/web/src/components/Logo.astro` + favicon set in `apps/web/public/` (see `UI-KIT`).
- Loading: `apps/web/src/components/Skeleton.astro` (+ `skeleton.ts` logic).
- Live preview of the foundation: route `/design-demo` (not in nav; E-D1 does the real rollout).

## Status

E-F1 ships the **foundation**: identity, motion tokens, loading system, docs. It does **not**
roll out site-wide — that is E-D1 (swaps `Layout.astro`, applies across pages). Interactivity
islands are E-3. The live "modules illuminate on election night" behavior is a seeded stretch,
not shipped here.
