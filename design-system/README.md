# Design system

> What is actually built. Tokens live in `apps/web/src/styles/global.css` (`@theme` + `:root`);
> components live in `apps/web/src/components/`. Aesthetic: clean/editorial, NYT/538 feel `[C11a]`.
> Stack: Astro 6 (static `.astro`, 0-JS), Tailwind v4 (CSS-first `@theme`, no config file).

## Principles

- **Neutral civic base; party colors *only* in data viz** `[C4a]` — chrome stays neutral so the
  site reads non-partisan; blue/red appear only inside charts/maps/bars.
- Light-default; dark via `prefers-color-scheme` (system-only for now) `[C6a]`.
- Accessible by default: WCAG 2.2 AA contrast `[W1a]`; transitions honor
  `prefers-reduced-motion` (a11y gate).
- Class merging always via `cn()` (`apps/web/src/lib/utils.ts` — clsx + tailwind-merge).

## Color tokens (`@theme`)

### Civic chrome `[C4a]`
| Token | Light | Dark |
|---|---|---|
| `bg` | `#f4f7f9` | `#0a0f14` |
| `surface` | `#ffffff` | `#111a22` |
| `surface-2` | `#edf1f4` | `#18242e` |
| `border` | `#dbe2e8` | `#27343f` |
| `border-strong` | `#c2ccd4` | `#3a4a57` |
| `text` | `#0e1a20` | `#ecf2f5` |
| `text-muted` | `#51616c` | `#9aa8b3` |
| `text-subtle` | `#7e8c95` | `#6e7c87` |
| `brand` (links/CTA, non-party) | `#0b6e4f` | `#2fc489` |
| `brand-soft` | `#e2f1ea` | `#11281f` |
| `on-brand` | `#ffffff` | `#06140e` |
| `danger` | `#b2182b` | `#e06a6a` |

Utilities: `bg-surface`, `text-muted`, `border-[var(--color-border)]`, etc.

### Party / data-viz (charts, maps, bars only) `[C5a]`
Party hue appears **only inside data**, never in chrome, and is **constant across themes** (it
encodes data, not brand). Always paired with a label; SVG pattern fills land in E0.4 via the
`pattern?` seam on the party components (no-op today, `data-pattern` marker set when `true`).
| Token | Value | Use | Pattern (E0.4) |
|---|---|---|---|
| `party-dem` | `#2c6fb3` | Democratic (`D`) | solid |
| `party-rep` | `#c13b3b` | Republican (`R`) | diagonal hatch |
| `party-ind` | `#e69f00` | Independent / fallback | dotted |
| `party-other` | `#9061c2` | Third party / other | cross-hatch |

`partyColorClass(party)` / `partyLabel(party)` in `apps/web/src/lib/races.ts` map a party code
to its `bg-party-*` class and display label.

## Typography `[C7a]`
- **Serif** (headlines + wordmark): **Fraunces**. **Sans** (UI/body/figures, tabular nums):
  **Chivo**. **Mono** (eyebrows, labels, source notes): **Recursive Mono**.
- Type scale as `@theme --text-*` tokens (~1.2 ratio, 16px base) with paired line-heights:
  `xs .75 / sm .875 / base 1 / lg 1.25 / xl 1.5 / 2xl 1.875 / 3xl 2.25 / 4xl 3` (rem). Drives
  `text-xs … text-4xl`.
- Helpers: `.eyebrow` (mono uppercase kicker), `.tnum` (tabular figures), `h1–h4` (Fraunces).

## Spacing, radius, containers
- Spacing: 4px base. Tailwind's numeric scale (`p-4` = 1rem) is the primary tool; named
  `--space-1..16` custom props exist in `:root` for raw CSS.
- Radius (`@theme`): `--radius-sm 4px / md 8px / lg 12px` → `rounded-sm/md/lg`. One elevation
  shadow: `--shadow-elev`.
- Container widths (`:root` custom props, cap ~1280px): `--container-sm 40rem / md 48rem /
  lg 56rem / xl 72rem / 2xl 80rem`. Kept out of `@theme` so they don't clobber Tailwind's
  `max-w-{sm..2xl}` utilities; use via `max-w-[var(--container-lg)]`. Site shell is `max-w-4xl`.

## Motion `[C13b]`
- `.reveal` — subtle fade + 6px slide-up on load (`0.4s ease-out`).
- Hover/focus color transitions on `Card`, `ListRow`, `Chip` links.
- All auto-gated by the `prefers-reduced-motion: reduce` kill-switch in `global.css`.

## Components (`apps/web/src/components/`, `.astro`, 0-JS)
All accept `class?` (merged via `cn()`). Party components carry a `pattern?: boolean` seam.

| Component | Props |
|---|---|
| `PartySwatch` | `party`, `size?='sm'\|'md'\|'lg'`, `pattern?`, `class?` |
| `PartyBar` | `segments: {party,value,label?}[]`, `max?`, `pattern?`, `class?` |
| `PartyLegend` | `items: {party,label,count?}[]`, `pattern?`, `class?` |
| `StatBlock` | `value: string\|number`, `label`, `sub?`, `size?='md'\|'lg'`, `class?` |
| `ListRow` | `title`, `href?`, `party?`, `meta?`, slots `leading`/`trailing`, `class?` |
| `SectionHeader` | `title`, `id?`, `source?` (or `source` slot), `level?=2`, `class?` |
| `DataTable` | `columns: {key,label,align?}[]`, `rows: Record[]`, `caption?`, `class?` |
| `Card` | `href?`, `title?`, `eyebrow?`, default slot, `class?` |
| `Chip` | `label`, `href?`, `variant?='default'\|'solid'\|'muted'`, `class?` |
| `EmptyState` | `title`, `body?`, default slot, `class?` |

Segment math (`computeSegments`) and table helpers (`alignClass`, `rowCells`) live in
`partyBar.ts` / `dataTable.ts` beside the components and are unit-tested.

## Not implemented (intentionally, per questionnaire)
- No shadcn/ui, no Storybook, no CVA/variant lib, no new runtime deps `[C8c,C9a]` — plain
  typed Astro components.
- Charts (Observable Plot/D3) and maps (MapLibre) are for later viz units, not this layer.
- Per-page OG image generation `[C14a]` deferred to a later SEO unit.
