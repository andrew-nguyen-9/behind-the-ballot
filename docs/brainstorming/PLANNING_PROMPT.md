# Behind the Ballot — Planning-Document Generation Prompt

Paste this whole file as the prompt (fresh session, or `/ralph-loop` pointed at it)
to turn the **answered** questionnaire into the full V1 planning doc tree. This
prompt's job is to *plan*, not to build app code. It is loop-first and
token-disciplined by design.

**Operating modes (run these first if not already active):** `/caveman full` + `/ponytail full` + learning/explanatory insights on; honor `/CLAUDE.md` (no AI attribution on git artifacts).

---

## Role

You are the **planning architect** for Behind the Ballot (BTB) — a non-partisan
2026-midterm tracking + analytics site, architected for every future election.
You honor `/CLAUDE.md` above everything here (no AI attribution on git artifacts;
caveman + ponytail active; learning/explanatory insights as you go).

Your deliverable is a complete, dependency-ordered, **loop-executable** planning
doc set where every decision traces to an answered questionnaire id. You do **not**
write application code, run migrations, or scaffold the app. You write the plan the
autonomous build loop will later execute.

## Read first (in this order, then stop and confirm scope)

1. `docs/brainstorming/BTB_QUESTIONNAIRE.md` — **the answered questionnaire (~356
   MCQs).** This is the source of truth. Read every `→` answer. Where an answer is
   bare (`→ A`), the choice is locked. Where it has prose (`→ A for now, B later`),
   capture both the V1 lock *and* the deferred note. Multi-letter (`→ A + C`) = both.
2. `docs/brainstorming/PLANNING_TECHNIQUES.md` — the patterns to reuse (questionnaire
   graduation chain, phase overview shape, vertical slices, the orchestrator/worker
   loop, config-driven units, free-tier-as-measured-constraint).
3. Skim sibling repo `../metrotrack/docs/` for concrete shapes only
   (`phases/v2/PHASES_OVERVIEW.md`, `LOOP_PROMPT.md`, `VERSIONING.md`,
   `WORKFLOW.md`, `DEFINITION_OF_DONE.md`). Use serena/Explore — don't read whole
   files into context; lift structure, not prose.

Then post a **one-screen scope confirmation** (locked stack + module cut + the
flagged open questions below) and proceed without waiting unless something contradicts.

## Locked spine (from the answers — cite ids, don't re-litigate)

Pull the full set from the file; these are the load-bearing ones to thread through:

- **Stack:** Astro + React islands `[P1a]`, TypeScript strict `[P4a]`, static-first /
  git-as-data, DB only where needed `[O1a]`. Cloudflare Pages host `[P6a]`.
- **Data store:** Neon Postgres `[O2a]` **but flag the 500 MB free cap (answer L843
  note)** → R2 for blobs/tiles/bulk `[O4d]`, baked JSON/Parquet on CDN for hot reads
  `[O6a]`. Drizzle `[O8a]`. Offline geo (GeoPandas in CI), **no PostGIS** `[O17a,L7a]`.
- **Modules V1:** tracker + finance + polling + forecast + demographics + caucus +
  members + gerrymander-lite `[E11a]`; issue + party-demo deferred, stubbed `[E6a,J2a]`.
- **Forecast:** heuristic-first, Monte Carlo, ML only if it beats it `[N1a,N8a]`.
- **Pipeline:** Python ETL `[R1c]`, GitHub Actions cron per source `[R2a]`,
  bronze→silver→gold `[O12a]`, idempotent upsert `[R4a]`, freshness floors `[R5a]`.
- **Config-driven units:** a race/state/module = one config file `[F4c,A7a]` so the
  loop can grind coverage without forking code.
- **Email/accounts:** custom domain + Cloudflare Email Routing catch-all → unlimited
  aliases → one inbox `[T1d]`; Resend for outbound alerts `[T4a]`.
- **Cross-cutting gates (every segment, not separate phases):** WCAG 2.2 AA `[W1a]`,
  Lighthouse ≥90 mobile in CI `[U8a]`, perf budgets `[X1a]`, JSON-LD/sitemap/OG SEO
  `[U3a,U4a,U5a]`, security headers + Dependabot + pinned Action SHAs `[V5a,V3a,V4a]`,
  every figure → a `DATA_SOURCES.md` row `[R14a]`.

**Flagged open questions to resolve into ADRs (don't skip):**
- Neon 500 MB cap (L843) → ADR: storage tiering (what lives in Postgres vs R2 vs
  static; partition by `cycle`; prune raw to R2).
- Efficient search (L891) → ADR: static client index (Pagefind) + note on
  bloom-filter / compact-index techniques for scale.
- 2026 redistricting (L547) → ADR: district-geometry versioning; track court-ordered
  map changes per state with `as_of`.

## Outputs to produce (the doc tree)

Create under `docs/` (and `design-system/`), each cross-linked, each decision cited:

1. `docs/01_PRODUCT_VISION.md` — job, audience, neutrality contract, scope `[A*,B*,D*]`.
2. `docs/02_ARCHITECTURE.md` — stack, data flow, storage tiering, geo-offline, hosting.
3. `docs/03_DATA_SOURCES.md` — one row per figure: source, url, license, key, cadence,
   freshness-floor `[R14a]`. Seed every V1 module's sources (FEC, Census, Congress.gov,
   Voteview, 538, congress-legislators, TIGER, Geocoder).
4. `docs/04_DEFINITION_OF_DONE.md` — the cross-cutting gate (build+tests+a11y+Lighthouse
   +data-integrity+SEO) applied to every unit.
5. `docs/VERSIONING.md` (`v[phase].[segment].[task]`) + `docs/WORKFLOW.md` (branch ritual).
6. `docs/adr/` — ADRs for: framework `[P1a]`, datastore+tiering `[O2a]`, no-PostGIS geo
   `[L7a]`, forecast method `[N1a]`, email/alias strategy `[T1d]`, search `[L891]`,
   redistricting versioning `[L547]`, **and the loop architecture itself.**
7. `docs/phases/v1/PHASES_OVERVIEW.md` — the spine (see shape below).
8. `docs/phases/v1/<segment>/PLAN.md` — per-segment acceptance criteria + unit list.
9. **`docs/phases/v1/LOOP_PROMPT.md`** — the autonomous build/rollout contract.
10. **`docs/phases/v1/PROGRESS.md`** — the ledger the loop reads/writes.
11. `design-system/` seed — tokens (colorblind-safe party palette `[C5a]`, neutral
    civic base `[C4a]`), type, the logo brief for Claude Design MCP `[C2a]`.
12. `docs/ACCOUNTS.md` (gitignored if sensitive) — service, alias used, free limits,
    budget alarms at 80% `[T9a,T10a]`.

### PHASES_OVERVIEW shape (copy metrotrack's, adapt)

- `Phase | Branch | Name | Unblocks` table, dependency-ordered.
- `In V1 | Out (deferred)` scope table, every row citing an id.
- "Why this order" prose (Phase-0 bootstrap → data foundation + config schema →
  per-module slices → forecast → SEO/content → loop scale).
- Locked-decisions table `Concern | Decision | Q`.
- Cross-cutting acceptance criteria stated once.
- Phase-0 = docs+schema+contracts+config-format before any business logic `[ZZ5a]`.

## Loop-first mandate (the spine — integrate deeply, not as an appendix)

The plan must be **executable by a mostly-autonomous loop**, not just readable.
Bake these in at every level:

1. **Everything is a unit.** Each phase/segment decomposes into units the loop picks
   off `PROGRESS.md`: a config-driven race/state/module = one unit `[F4c]`. A unit has
   a slug, a prereq, a status (`pending|in-progress|review|blocked|done`), and an
   acceptance check.
2. **Orchestrator / cold-worker split** `[S3a,Z6a].` Author `LOOP_PROMPT.md` as the
   single contract: orchestrator reads the ledger, picks the first eligible `pending`
   unit, **spawns a fresh cold sub-agent** (re-derives from plan files, not chat —
   the token saver), gates the result itself, opens a PR with evidence, updates one
   ledger row, repeats. Model tiering: Opus orchestrates/gates, Haiku/Sonnet do
   mechanical worker units `[Z7a]`.
3. **Hard verification gate, non-negotiable** `[S4a].` A unit advances only when, re-run
   by the orchestrator: build green; tests green; `astro check` clean; a11y (axe) +
   Lighthouse ≥90 mobile; **data-integrity — every published figure traces to a
   `DATA_SOURCES.md` row and the freshness floor is met**; responsive screenshots at
   360/768/1280. "It builds" is not done. Paste the output.
4. **`main` is a hard wall** `[S5a].` Loop never commits/merges/pushes to main. Auto-merge
   green work to `dev`; humans own main. Never force-push.
5. **Budget check before every spawn** `[S6a].` Confirm headroom: Actions minutes, API
   quotas (api.data.gov), R2/CDN bandwidth, **and your own token/session budget (below)**.
   Tight budget → mark unit `blocked`, log why, stop. Stagger across nights to stay free.
6. **Nightly autonomous QA is a separate cadence** `[S7a].` Plan a scheduled Action that
   re-runs the gate against the live site + validates data freshness, and on regression
   **opens/updates a deduped GitHub issue + emails you via Resend** `[S9d,S11a]` with
   summary + diff + run link + severity `[S10a]`.
7. **Self-emailed issues** `[S9d].` Specify the Resend wiring (alias sender, your inbox,
   secret in Actions) in the plan so item-4 ("email issues to myself") is concrete.
8. **Concurrency cap** ≤2–3 worktrees `[S13a]`; **evidence-or-it-didn't-happen** on every
   unit PR `[S14a]`; **stop conditions**: no eligible unit / budget wall / human pause
   `[S16a]`.
9. **Loop state lives in `PROGRESS.md`** `[S17a]` — the ledger + a one-line activity log
   per touched row. A fresh session reconstructs everything from it.

`LOOP_PROMPT.md` must be self-contained enough that pasting it (or `/ralph-loop` on it)
drives a build session with zero extra context.

## Token & session discipline (build this into LOOP_PROMPT.md and obey it now)

Sessions must never die mid-write. Treat context and the usage-session window as
**budgeted resources with a checkpoint-then-sleep protocol**:

1. **Checkpoint is atomic and frequent.** After each unit (and before any risky long
   step) flush state to `PROGRESS.md` + the doc being written so a cold restart loses
   nothing. Never hold important state only in context.
2. **The 98% rule (context).** When the harness context indicator approaches **~98%**
   (or you notice you're near the window): finish the current atomic write, append a
   `RESUME:` note to `PROGRESS.md` (next unit + any half-done step), then **end the
   turn cleanly / spawn a fresh cold sub-agent to continue** rather than pushing into
   an overflow that truncates mid-thought. Cold continuation re-derives from the ledger.
3. **The 98% rule (usage session).** When you observe the usage meter near the
   **session cap (~98%)**: do **not** keep working into a hard stop. Checkpoint, then
   **`ScheduleWakeup`** with `delaySeconds = (seconds until the session window resets) + 60`
   — i.e. wake **1 minute after the session refresh** — passing this same prompt back so
   the loop resumes itself. Pick the delay from the actual reset time, not a round
   number; clamp is `[60, 3600]`. Reason string: "sleeping past session reset to avoid
   mid-unit cutoff." Then stop. On wake, re-read `PROGRESS.md` and continue from `RESUME:`.
4. **Token frugality every turn** `[Z*]:` serena for symbol-level nav (don't read whole
   files); rtk proxy on dev ops; caveman/ponytail keep output + builds minimal; cold
   sub-agents driven by plan files; context7 only when a lib doc is actually needed;
   Opus only for planning/gating, cheaper models for mechanical units `[Z7a]`.
5. **Encode all of the above verbatim into `LOOP_PROMPT.md`** so the build loop inherits
   the same discipline — this is a permanent operating rule, not a one-off.

## Graduation rules

- Every locked decision in every doc cites its questionnaire id `[X#a]`. Prose answers
  carry both the V1 lock and the deferred note (e.g. "stub now, B/C in v1.x `[J2a+note]`").
- Multi-letter answers (`A + C`) → state both and how they coexist.
- If an answer is ambiguous or two answers conflict, **list it in a `## Open
  questions` block at the top of the relevant doc** and pick the safest default —
  don't silently guess.
- Don't invent scope the questionnaire didn't sanction. New scope → `docs/BACKLOG.md`.

## Order of work

1. Read inputs → post scope confirmation.
2. Phase-0 docs (01–04, VERSIONING, WORKFLOW) + ADRs.
3. `PHASES_OVERVIEW.md` (the spine).
4. Per-segment `PLAN.md`s.
5. `LOOP_PROMPT.md` + `PROGRESS.md` (seed the ledger with Phase-0..N units).
6. `design-system/` seed + logo brief + `ACCOUNTS.md`.
7. Self-review: does every doc cite ids? Is the loop runnable from `LOOP_PROMPT.md`
   alone? Are the token/session rules in it? Are flagged ADRs written? Then report.

## Done = 

The doc tree exists, internally consistent, every decision cited; `LOOP_PROMPT.md`
is self-contained and embeds the verification gate + the token/session protocol;
`PROGRESS.md` is seeded; ADRs cover the flagged questions. No app code written. Post a
short index of what was created and the first 3 ledger units the build loop will pick.

## Ralph-loop control (this prompt runs under /ralph-loop)

Same prompt re-feeds each iteration; you see prior work in the files + git, so build
the doc tree **incrementally** — one or a few docs per iteration, checkpointing to
git between. Each iteration:

1. Read `PROGRESS.md` if it exists (else start at "Order of work" step 1). It is also
   *this planning effort's* ledger — track which docs are `done` vs `pending` there.
2. Do the next chunk of work (respect the **token/session discipline** above —
   checkpoint + `ScheduleWakeup` past a session reset instead of dying mid-write).
3. Commit the chunk (`docs:` scope, no AI attribution per `/CLAUDE.md`). Never push.
4. **Self-check before promising:** every doc in "Outputs to produce" exists, every
   decision cites an id, `LOOP_PROMPT.md` is self-contained + embeds the gate and the
   token/session rules, `PROGRESS.md` seeded, flagged ADRs written.

**Completion:** only when the self-check fully passes, output exactly:

`<promise>PLANNING COMPLETE</promise>`

Until then, do **not** emit the promise — keep iterating. If blocked on a real human
decision, write it to a top-of-doc `## Open questions` block, pick the safest default,
and continue; do not stall the loop on it.
