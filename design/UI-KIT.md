# UI Kit — components & foundation APIs

Load with `INDEX.md` + `FOUNDATIONS.md` for build tasks. Components live in
`apps/web/src/components/`. This documents the **E-F1 foundation pieces** and inventories the
existing kit. Astro components are 0-JS unless they hydrate a `.tsx` island.

## Logo — `Logo.astro`

The Civic Lattice mark, hand-authored inline SVG, no dependency. **Theme-aware by construction:**
modules paint in `currentColor`, so set color on the parent (e.g. `text-[var(--color-brand)]`)
and the mark follows light/dark. Reads clean at 16px, reveals structure large.

| Prop | Type | Default | Notes |
| --- | --- | --- | --- |
| `size` | `number` | `24` | px, square (width = height) |
| `title` | `string` | `"Behind the Ballot"` | accessible name (`role=img`) |
| `decorative` | `boolean` | `false` | `aria-hidden` — use beside a text wordmark |
| `accent` | `string` | — | CSS color to tint only the highlighted apex module; omit = monochrome |
| `class` | `string` | — | merged via `cn()` |

```astro
<span class="text-[var(--color-brand)]"><Logo size={26} decorative /></span>
```

### Favicon / social set (`apps/web/public/`)

Generated from the same lattice geometry (brand tile + white modules):

- `favicon.svg` — vector, brand tile, tuned for 16px legibility.
- `favicon.ico` — 16/32/48 multi-res fallback.
- `apple-touch-icon.png` (180) · `icon-192.png` · `icon-512.png` (maskable) — PWA/manifest.
- `og.svg` + `og.png` (1200×630) — social/OG card (mark + wordmark). Wiring OG `<meta>` is a
  later SEO unit; the asset ships here.

## Skeleton — `Skeleton.astro` (+ `skeleton.ts`)

Loading placeholder, **skeleton over spinner**: reserves the final layout box (no CLS) and shows
the content's shape. Shimmer uses motion tokens and is killed to a static tint under
reduced-motion (final state). `role=status` + `aria-busy` announces "Loading"; bars are
`aria-hidden`. Layout logic is unit-tested in `skeleton.ts` / `skeleton.test.ts`.

| Prop | Type | Default | Notes |
| --- | --- | --- | --- |
| `variant` | `"text" \| "block" \| "circle"` | `"text"` | shape |
| `lines` | `number` | `3` | text only; last line is short (ragged paragraph) |
| `width` | `string` | — | block/circle size or per-line width |
| `height` | `string` | — | block/circle height or line height |
| `label` | `string` | `"Loading"` | sr-only status text |
| `class` | `string` | — | merged via `cn()` |

```astro
<Skeleton lines={4} />
<Skeleton variant="circle" width="3rem" />
<Skeleton variant="block" height="6rem" />
```

**Not** `EmptyState`: skeleton = data arriving; `EmptyState` = honestly no data. See
`FOUNDATIONS` → Loading philosophy.

## Existing kit (inventory)

`Card` · `StatBlock` · `PartyBar` · `PartyLegend` · `PartySwatch` · `PartyPatternDefs` ·
`Chip` · `DataTable` · `ListRow` · `SectionHeader` · `FilterBar` · `EmptyState` ·
`TextSizeControl` · `HouseArc` · `USStateMap` · `StripeDefs` · islands `SearchDialog.tsx`.
E-D1 applies the new foundation across these; E-F1 only defines it.
