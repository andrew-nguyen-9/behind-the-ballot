# 04 · Definition of Done

> The single cross-cutting gate `[S4a]`. It applies to **every unit** — a race
> config, a module slice, a content page — not as separate phases. A unit advances
> from `review` → `done` only when the orchestrator **re-runs** this list and pastes
> the output. "It builds" is not done `[S4a]`. Decisions cite the questionnaire `[id]`.

## The gate (all must pass, re-run by the orchestrator)

1. **Build green** — `pnpm build` (Astro SSG) exits 0.
2. **Types clean** — `astro check` + `tsc --noEmit`, zero errors; TS strict `[P4a]`.
3. **Tests green** — Vitest unit + Playwright e2e for the unit's surface `[P14a]`.
4. **Lint/format** — eslint + prettier clean.
5. **Accessibility** — axe has zero serious/critical violations; WCAG 2.2 AA `[W1a,W9a]`;
   keyboard reachable, focus visible, contrast met (colorblind-safe palette `[C5a]`).
6. **Lighthouse ≥ 90 mobile** in CI on the unit's route(s) — perf, a11y, best-practices,
   SEO `[U8a]`. Perf budgets respected (JS/route ceiling) `[X1a]`.
7. **Data integrity (load-bearing)** `[R14a,S15a]` — **every published figure traces to a
   `03_DATA_SOURCES.md` row**; the source's **freshness floor is met** (`as_of` within
   max-age) or the figure is hidden with a stale notice, never shown silently.
8. **SEO** — JSON-LD where applicable, in sitemap, OG/meta present `[U3a,U4a,U5a]`.
9. **Security** — security headers set, no secret in client bundle, deps pass Dependabot,
   Actions pinned to SHAs `[V5a,V3a,V4a]`.
10. **Responsive evidence** — screenshots at **360 / 768 / 1280** attached to the PR
    `[S14a]`.

## Evidence requirement

Every unit PR carries: the three responsive screenshots, the Lighthouse scores, and the
data-integrity log (figure → source row → `as_of`) `[S14a]`. No evidence = not done.

## Scope guard

A unit ships only what the answered questionnaire sanctioned. New ideas → `docs/BACKLOG.md`,
never smuggled into a unit `[scope]`.
