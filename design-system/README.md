# Design system (seed)

> Token + component spec the build loop turns into a Tailwind config + a small shadcn/ui
> component lib `[C8c,C9a,C10a]`. Planning seed — concrete values, no app code yet.
> Aesthetic: clean/editorial, NYT/538 feel `[C11a]`. Cite `BTB_QUESTIONNAIRE.md` `[id]`.

## Principles

- **Neutral civic base; party colors *only* in data viz** `[C4a]` — chrome stays neutral
  so the site reads non-partisan; blue/red appear only inside charts/maps.
- Light-default + dark toggle `[C6a]`.
- Accessible by default: WCAG 2.2 AA contrast `[W1a]`; **rich transitions** `[C13b]` but
  `prefers-reduced-motion` honored (a11y gate requires it).

## Color tokens

> Brand v1.0 — one confident green on cool blue-gray neutrals (no party color in chrome).
> Implemented in `apps/web/src/styles/global.css` (`@theme`); this table is the spec.

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

### Party / data-viz (charts & maps only) `[C5a]`
Party hue appears **only inside data**, never in brand chrome, and **always paired with a
pattern + label** so meaning never rests on hue alone `[C5a+C]`. Constant across themes.
| Token | Value | Use | Pattern |
|---|---|---|---|
| `party-dem` | `#2c6fb3` | Democratic | solid |
| `party-rep` | `#c13b3b` | Republican | diagonal hatch |
| `party-ind` | `#e69f00` | Independent | dotted |
| `party-other` | `#9061c2` | Third party / other | cross-hatch |

## Typography `[C7a]`
- **Display/serif** (headlines + wordmark): **Fraunces** — optical serif, authority + warmth.
- **Sans** (UI + body + figures, tabular nums): **Chivo** — grotesque workhorse.
- **Mono** (eyebrows, labels, metadata, source notes): **Recursive Mono**.
- Scale: 12 / 14 / 16 (base) / 20 / 24 / 32 / 48; line-height 1.5 body, ~1.1 headings.

## Spacing & radius
4-pt scale (`4 8 12 16 24 32 48 64`); radius `sm 4 / md 8 / lg 12`; one elevation shadow.

## Motion `[C13b]`
Rich but tasteful transitions (150–250 ms ease-out); **all wrapped in
`@media (prefers-reduced-motion: reduce)` no-op**.

## Components `[C9a]`
shadcn/ui (Radix) — hireable, accessible. Icons **Lucide** `[C12a]`. Storybook deferred
`[C8c]`. Charts Observable Plot + D3 `[P7a]`; maps MapLibre GL `[P8a]`.

## OG/share `[C14a]`
Auto-generate a per-page OG image at build (race card → image).

## Logo
See `LOGO_BRIEF.md` — generated via Claude Design MCP `[C2a]`.
