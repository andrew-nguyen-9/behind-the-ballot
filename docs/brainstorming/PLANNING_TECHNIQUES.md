# Planning Techniques — mined from prior projects

Source repos studied: `metrotrack` (v2), `ACOS`, `portfolio-website`,
`fantasy-football-tool`, `music-festival-analyzer`, `trivia-generator`.
Goal: steal the **most token-efficient, most productive** planning patterns and
reuse them here. Ranked by leverage.

## 1. Questionnaire-driven scope lock (metrotrack — highest leverage)

A front-loaded **MCQ questionnaire** (metrotrack v2 = 200 Qs) answered *once*
before any building.

- **Format:** `**B1. <question>?**` → 3–4 lettered options on one line → `⭐` on
  the recommended default → `→` blank for the answer. "Other always allowed."
  "Skip what you don't care about yet" (skip = take the ⭐).
- **Why it's cheap:** answering is a single letter. Defaults mean a skipped
  question is still decided. 200 decisions cost ~30 min, not days of back-and-forth.
- **The graduation chain:** surviving answers get promoted into `docs/phases/`,
  `design-system/`, and ADRs. **Every locked decision cites its question id**
  (`[B1a]`). A build agent reads `Tenancy: single DB, metro_id everywhere [B1a]`
  instead of re-deriving it — traceability with near-zero tokens.

## 2. Dependency-ordered phase overview (metrotrack `PHASES_OVERVIEW.md`)

One table: `Phase | Branch | Name | Unblocks`. Plus:
- **Scope-at-a-glance**: a two-column `In v<n> | Out (deferred)` table, every row
  citing a question id.
- **"Why this order"**: prose justifying the dependency chain (foundation before
  features, SEO scaffold before content, template metro before the grind).
- **Locked decisions table**: `Concern | Decision | Q`.
- **Cross-cutting acceptance criteria** stated once, applied to every segment
  (a11y, perf budget, Lighthouse ≥90, data-integrity) — *not* separate phases.

## 3. Vertical-slice rule (ACOS)

> Build vertically, not horizontally. Each phase ships a working, testable
> vertical slice. **No phase begins until the prior phase's acceptance criteria
> pass.** Numbered docs `01_PRODUCT_VISION … 08_ROADMAP` + `adr/` from Phase 0
> ("bootstrap": docs + schema + contracts before any business logic).

## 4. Autonomous loop contract (metrotrack `LOOP_PROMPT.md` + ralph-loop)

The pattern for item-4 (autonomous pipelines/QA):
- **Orchestrator + worker split.** One prompt = orchestrator. It reads a ledger
  (`PROGRESS.md`), picks the first `pending` unit whose prereq is `done`, spawns
  a **fresh cold sub-session** per unit (re-derives from plan files, *not* from
  chat — this is the token saver), gates the result, opens a PR with evidence,
  updates one ledger row, repeats.
- **Hard verification gate, non-negotiable:** build + tests + advisors/security +
  data-integrity (every published figure traces to a source row + freshness floor)
  + Lighthouse ≥90 + responsive screenshots. "It builds" is not done.
- **`main` is a hard wall:** loop auto-merges green work to the dev branch; humans
  own `main`. Budget check before each spawn (Actions minutes, API quota, bandwidth).
- **Nightly autonomous QA** is a *separate cadence*: a scheduled Action re-runs the
  gate against live pages, opens an issue + emails on regression.

## 5. Config-driven multiplicity ("add a unit = 1 file + 1 run")

metrotrack's `[B13a]`: adding a metro = author `metros/<slug>.toml` + run pipeline
`--metro=slug`. No code fork. "If you're editing shared logic per-unit, that's a
bug in the abstraction." → Here: adding an **election / race / state** should be
one config file, so the loop can grind races autonomously.

## 6. Free-tier as a measured constraint, not a guess

metrotrack measured actual sizes ("Chicago gold DB = 232 KB … free cap fits ~2000
metros — storage is not the constraint; the real limits are Actions minutes, API
quota, bandwidth"). **Bake slow-changing data static at build (git-as-data);** use
a DB only where you truly need queries. Stagger jobs across nights to stay free.

## 7. Supporting rituals (shared across repos)

`docs/VERSIONING.md` (`v[phase].[segment].[task]`), `WORKFLOW.md` (branch ritual),
`DEFINITION_OF_DONE.md`, `DECISIONS.md`/`adr/`, `BACKLOG.md` intake, `DATA_SOURCES.md`
(every figure → a row). Design decisions imported via Claude Design MCP (logos).

---

### What we adopt for Behind the Ballot

1. `BTB_QUESTIONNAIRE.md` (300 MCQs) → answer once. ← **this is step one.**
2. Survivors graduate into `docs/phases/v1/PHASES_OVERVIEW.md` with `[id]` cites.
3. Vertical slices, acceptance criteria cross-cutting (SEO/sec/a11y/perf baked in).
4. `LOOP_PROMPT.md` + `PROGRESS.md` ledger + nightly-QA Action + self-email on regression.
5. Config-driven races/states so the loop can grind coverage.
6. Measure free-tier limits; bake static where possible.
