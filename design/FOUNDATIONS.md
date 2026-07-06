# Foundations — tokens, motion, loading, a11y

Load with `INDEX.md` for any build/token task. **Single source of truth for the values here is
`apps/web/src/styles/global.css` `@theme`** — this doc explains intent; the CSS is canonical.
Components reference tokens; never hardcode a hex or a millisecond.

## Color (civic chrome)

One confident green (`--color-brand`) on cool blue-gray neutrals. Light defaults; dark overrides
in the `prefers-color-scheme` media query and the `html[data-theme="dark"]` manual toggle.

- Surfaces: `--color-bg` / `--color-surface` / `--color-surface-2` / `--color-border(-strong)`.
- Text: `--color-text` / `--color-muted` / `--color-subtle`.
- Brand: `--color-brand` / `--color-brand-soft` / `--color-on-brand`. `--color-accent` aliases brand.
- **Party colors (`--color-party-*`) are data-viz ONLY** — colorblind-aware, paired with
  patterns (`.pf-hatch/.pf-dots/.pf-crosshatch`), constant across themes. Never brand chrome.

## Type

- `--font-serif` Fraunces (display/headlines) · `--font-sans` Chivo (UI/body/figures) ·
  `--font-mono` Recursive (mono eyebrows/metadata via `.eyebrow`).
- Scale `--text-xs … --text-4xl` (~1.2 ratio, 16px base) drives Tailwind `text-*`, with paired
  line-heights. Tabular figures: `.tnum` for results/tables.
- Root rem scales via `[data-text-size]` (s/m/l = 100/112/125%) — everything rem-based reflows.

## Space & radius

- Spacing (`--space-*`) and container caps (`--container-sm…2xl`, ~1280px) in `:root`.
- Radius restrained: `--radius-sm` 4px · `--radius-md` 8px · `--radius-lg` 12px.

## Motion

Motion **clarifies, never decorates** — it shows state change (a total updating, a race called)
and spatial relationships (where a number came from). It is always cuttable. One small,
retunable scale (add here, not in components):

| Durations | | Easings | |
| --- | --- | --- | --- |
| `--duration-instant` | 90ms — taps/toggles | `--ease-standard` | symmetric, most UI |
| `--duration-fast` | 160ms — hovers, small enter/exit | `--ease-decelerate` | enter (fast→settle) |
| `--duration-base` | 240ms — default UI transition | `--ease-accelerate` | exit (rest→leave) |
| `--duration-slow` | 420ms — larger reveals, bars/counts | | |

Rules: **CSS-first** (transitions/keyframes). JS-driven animation only inside an island that
already hydrates for another reason — never add JS to a 0-JS page for motion. Election-night
motion (counts filling, bars growing) **reuses these same tokens** (E-R9/E-D1 territory).

**`prefers-reduced-motion: reduce` is a hard kill-switch** — `global.css` sets
`animation: none !important; transition: none !important` on everything, so any tokened motion
snaps to its final state. This is a DoD/a11y gate, verified in `skeleton.test.ts`.

## Loading philosophy

Static-first means **most pages have no loading state** (pre-baked HTML). Loading UI exists only
for (a) island hydration (charts/maps/search) and (b) genuinely live surfaces (election-night
refresh). Principle: **skeleton over spinner** — reserve layout, show the content's shape, avoid
layout shift (CLS is a Lighthouse gate). See `Skeleton` in `UI-KIT`.

**Honest-empty (`EmptyState`) ≠ loading.** Never show a skeleton/spinner where the truth is "no
data" — that implies data is coming when it is not. Skeleton = "data is arriving"; EmptyState =
"there is honestly nothing here (yet)."

## A11y (gates, not nice-to-haves)

WCAG 2.2 AA · axe 0 serious/critical · Lighthouse ≥90 mobile · contrast met on both themes ·
focus visible & keyboard reachable · reduced-motion honored · no CLS · every published figure
traces to a `docs/03_DATA_SOURCES.md` row and meets its freshness floor (or is hidden).
