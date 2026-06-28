# Phase 9 · SEO / content / search

> Site-wide discoverability + editorial layer over the module pages. Units `v1.9.*`.
> Prereq: real pages exist (phases 2–8). Cross-cutting SEO/a11y/perf already gate every
> unit; this phase adds the **site-level** surfaces. Cite `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- **Pagefind** static search index built at build, served from CDN, no backend `[L891]`
  (ADR 0006); within the perf budget `[X1a]`.
- Sitemap + robots + per-type JSON-LD complete `[U3a,U4a]`; OG/meta on every route
  `[U5a]`.
- MDX articles with embeddable live figures `[P11a,Y8a]`; `/sources` page renders the
  DATA_SOURCES table `[R14a]`.
- Lighthouse ≥90 mobile sitewide `[U8a]`; a11y AA `[W1a]`.

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.9.1-search` | phases 2–8 | Pagefind index over races/members/districts/articles; results page `[L891]` | pending |
| `v1.9.2-sitemap-jsonld` | phases 2–8 | sitemap, robots, JSON-LD per type, OG/meta audited `[U3a,U4a,U5a]` | pending |
| `v1.9.3-articles-mdx` | v1.0.8 | MDX article pipeline + embeddable live figures `[P11a,Y8a]` | pending |
| `v1.9.4-sources-page` | — | `/sources` renders DATA_SOURCES contract table `[R14a]` | pending |
| `v1.9.5-home-nav` | 9.1 | homepage + global nav surfacing all modules + search | pending |
