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

### Civic neutral (chrome) `[C4a]`
| Token | Light | Dark |
|---|---|---|
| `bg` | `#ffffff` | `#0d1117` |
| `surface` | `#f6f8fa` | `#161b22` |
| `border` | `#d0d7de` | `#30363d` |
| `text` | `#1f2328` | `#e6edf3` |
| `text-muted` | `#636c76` | `#9198a1` |
| `accent` (links/CTA, non-party) | `#0969da` | `#4493f8` |

### Party / data-viz (charts & maps only) `[C5a]`
Colorblind-safe blue/red (ColorBrewer RdBu endpoints), **plus patterns** for safety, and a
**purple-through-middle margin gradient** for continuous margins `[C5a+C]`.
| Token | Value | Use |
|---|---|---|
| `party-dem` | `#2166ac` | Democratic |
| `party-rep` | `#b2182b` | Republican |
| `party-ind` | `#5a4fa0` | Independent/other |
| `margin-scale` | `#b2182b → #f7f7f7 → #2166ac` | diverging margin (rep↔dem) |
| `pattern-dem` / `pattern-rep` | diagonal / dot overlays | redundant encoding for CVD safety |

## Typography `[C7a]`
- **Sans** (UI + figures): one readable variable sans (e.g. Inter).
- **Serif** (long-form articles): one serif (e.g. Source Serif / Lora).
- Scale: 12 / 14 / 16 (base) / 20 / 24 / 32 / 48; line-height 1.5 body, 1.2 headings.

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
