# 01 · Product Vision

> Decisions cite the answered `brainstorming/BTB_QUESTIONNAIRE.md` as `[id]`.

## The job

Behind the Ballot (BTB) is a **non-partisan election tracking + analytics hub** —
2026 US midterms first, architected as **evergreen** for every future election
`[A1·focus-A/B/D, A6c, A7a]`. It tracks races and ships analytics across campaign
finance, polling, demographics, congressional/caucus composition, member records,
gerrymandering, and an election forecast `[A5a]`.

**Scope:** Federal (House + Senate + key Governors) plus a high-level State view
`[A4a, E16a]`. Config-driven so a race/state/cycle is one file `[A7a, F4c]` — 2026 is
the demo, not the ceiling `[A6c]`.

## Success

Primary metric: **breadth of working, sourced analytics modules** `[A2a]`, with the
**forecast** as the signature skill-showcase `[E12a]` and portfolio depth as a
deliberate secondary goal `[A1·D]`. V1 is "done" when tracker + finance + polling +
forecast are live, all sourced, Lighthouse ≥90 `[A11a]`.

## Audience

1. Engaged voters / news consumers `[D1·A]` — primary.
2. Journalists / analysts `[D1·B]`.
3. Political hobbyists / forecasters, and recruiters viewing the work `[D1·D]`.

Mobile-first, desktop-excellent `[D2a]`. Progressive disclosure — scan headline
numbers, drill on demand `[D3c]`. "Find your district" by address/ZIP is the personal
entry point `[D5a]`. WCAG 2.2 AA is the accessibility target `[D9a]`.

## Neutrality contract (non-negotiable)

This is the credibility spine `[A3·A]`:

- Every published figure carries a **source + "as of" date + methodology link**
  `[B2c]`; every figure maps to a `DATA_SOURCES.md` row `[R14a]`.
- All parties shown, always; **colorblind-safe palette, never color-only** `[B3a, C5a]`.
- The model + data speak — **no position on any race** `[B5a]`. Forecasts framed as
  ranges with "not a prediction" + methodology `[B4a, B9a]`.
- Articles/findings may carry light analysis (B/C tone) but stay **as neutral as
  possible**, clearly labeled `[A3·note, B5·articles]`.
- Public correction changelog `[B7a]`.

## Explicitly out of V1

User accounts/auth · self-originated election-night calls (mirror AP only) · paid
tiers · non-US elections — **all excluded** `[A8e, F7a]`. Issue analytics and party-
demographic analytics are **stubbed + deferred** to v1.x `[E6a, E7a, J2a]` with real
indexable placeholder pages `[E20a]`.

## Naming & home

Public name **"Behind the Ballot"** `[A9a]`; domain **`ballot.an9.dev`** `[A10a]`.

## How we work (vision-level)

Free-tier on everything `[locked priors]`; static-first with a DB only where needed
`[O1a]`; autonomous build/QA loops with a human-owned `main` `[S1a, S5a]`; every
non-obvious call gets an ADR `[ZZ4a]`. Issue + party-demo analytics, full
gerrymandering ensemble, state-legislature depth, and newsletters are **deferred**,
tracked in `docs/BACKLOG.md` `[E6a, L11a, L13a, Y7a]`.
