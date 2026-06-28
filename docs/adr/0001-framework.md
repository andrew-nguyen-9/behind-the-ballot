# 0001 · Framework & hosting

**Status:** Accepted · 2026-06-28

## Context
Non-partisan election tracker, static-first, mostly read-heavy figures with a few
interactive surfaces (maps, charts, forecast). Must run on free tier and be hireable
tech without repeating prior Next.js work.

## Decision
**Astro SSG + React islands** `[P1a,P3a]`, **TypeScript strict** `[P4a]`, hosted on
**Cloudflare Pages** `[P6a]`. Static HTML by default; islands hydrate only maps/charts/
forecast. On-demand/ISR **only** for live election-night results `[P5a,F6a]`. pnpm
workspaces, single repo (web + pipeline) `[P12a,P13a]`.

## Consequences
- Minimal JS shipped → easy Lighthouse ≥90 `[U8a,X1a]`.
- React stays hireable; Astro diversifies the portfolio.
- Live results need a deliberate dynamic carve-out, not the default path.
- Cloudflare Pages free tier caps build minutes — batch builds, stagger `[T8a]`.
