# Behind the Ballot — V1 Build Loop (self-contained orchestrator prompt)

Paste this whole file as the first message of a **fresh build session** (or run
`/ralph-loop` on it — launch line at the bottom). It drives V1 **construction** unit by
unit from `PROGRESS.md` to a live Cloudflare Pages preview, autonomously, token-
disciplined, serena-powered. You honor `/CLAUDE.md` above everything here (no AI
attribution on git artifacts). This is the contract ADR 0008 describes.

---

## Step 0 — Boot (every cold start)

1. **Modes:** `/caveman full` + `/ponytail full` + learning/explanatory insights on.
2. **Serena:** `activate_project` this repo, then `initial_instructions`. Use serena
   `get_symbols_overview` / `find_symbol` / `find_referencing_symbols` /
   `search_for_pattern` for navigation instead of reading whole files — primary token saver.
3. **Re-derive state from disk, not memory:** read the build ledger
   `docs/phases/v1/PROGRESS.md` (`## RESUME` + unit table). Read the relevant
   `docs/phases/v1/<segment>/PLAN.md` for the unit you pick. Everything is on disk + in
   git. Never assume context from a prior session.

## Inputs (read only what the current unit needs)

- `PHASES_OVERVIEW.md` — the spine + phase order + cross-cutting AC.
- `<segment>/PLAN.md` — the unit's acceptance criteria + unit table.
- `04_DEFINITION_OF_DONE.md` — the gate (re-run it; don't trust the worker).
- `03_DATA_SOURCES.md` — the integrity contract (figure → row + freshness floor).
- `VERSIONING.md`, `WORKFLOW.md`, `docs/adr/` — conventions + locked decisions.

## The loop (each iteration)

1. **Step 0** (modes + serena + read ledger).
2. **Pick** the first eligible `pending` unit whose prereq is `done` `[S3a]`.
3. **Budget check before spawn** `[S6a]` — Actions minutes, `api.data.gov` quota, R2/CDN
   bandwidth, **and your token/session budget (below)**. Tight → mark the unit `blocked`,
   log why, pick another eligible unit. A blocked unit never halts the loop `[S16a]`.
4. **Spawn a fresh cold sub-agent** on a `unit/<version>-<slug>` branch `[Z6a]`. It
   re-derives from the PLAN + ADRs, not your chat. Model-tiered: **Opus orchestrates +
   gates; cheaper models (Haiku/Sonnet) do mechanical units** `[Z7a]`. Keep ≤2–3
   worktrees live `[S13a]`.
5. Worker drives the unit to **every** criterion in its PLAN + the cross-cutting gate.
6. **Re-run the gate yourself** `[S4a]` and paste output: `pnpm build` green; `astro
   check` + `tsc` clean; Vitest + Playwright green; eslint/prettier clean; axe zero
   serious/critical (WCAG 2.2 AA); **Lighthouse ≥90 mobile**; **data integrity — every
   figure → a `03_DATA_SOURCES.md` row + freshness floor met**; SEO (JSON-LD/sitemap/OG);
   security headers + pinned Action SHAs; responsive screenshots **360/768/1280**.
   "It builds" is not done.
7. Pass → open PR `unit/* → dev` with **evidence** (3 screenshots + Lighthouse +
   data-integrity log) `[S14a]`; auto-merge on green. **Never touch `main`** `[S5a]`;
   never force-push. Fail → back to the worker or mark `blocked`.
8. **Update one ledger row + one activity-log line** in `PROGRESS.md` `[S17a]`.
9. Respect token/session discipline (below).

## Hard rules (non-negotiable)

- **`main` is a wall** `[S5a]` — loop merges only to `dev`; humans own `main`; no force-push.
- **Gate before done** `[S4a]` — re-run by you, output pasted, evidence attached.
- **Evidence or it didn't happen** `[S14a]`.
- **Scope discipline** — build only what the answered questionnaire sanctioned; new ideas
  → `docs/BACKLOG.md`, not into a unit.
- **Cold workers** re-derive from plan files; never pass chat history as the context.

## Token & session discipline (obey precisely — same rule as the planning loop)

1. **Checkpoint atomic + frequent.** After each unit (and before any long step) flush
   state to `PROGRESS.md` (+ the file in progress). Important state lives on disk, never
   only in context.
2. **Context ~98%** → finish the current atomic write, append a `RESUME:` note to
   `PROGRESS.md`, then hand off to a fresh cold sub-agent / end the turn for the loop to
   re-feed — rather than overflowing mid-thought.
3. **Usage session ~98%** → do **not** keep working. (a) Checkpoint + `RESUME:` note.
   (b) Find when the usage window resets. (c) Call **`ScheduleWakeup`** with
   `delaySeconds = (seconds until reset) + 60` — wake ~1 min after refresh — passing
   **this same prompt** back. Reason: "sleeping past session reset to avoid mid-unit
   cutoff." Pick the delay from the real reset time (runtime clamps `[60,3600]`; if reset
   is further out, wake at the clamp and re-check). (d) Stop. On wake: Step 0, continue
   from `RESUME:`.
4. **Frugality every turn:** serena over file reads; rtk on dev ops; caveman/ponytail keep
   output + builds minimal; context7 only when a library doc is actually needed; batch
   independent tool calls; don't re-read files the harness already tracks.

## Completion

Output `<promise>V1 COMPLETE</promise>` **only when ALL are true**:
- Every V1 module unit (`v1.0.*`–`v1.10.*`) is `done` on this ledger and passing the gate
  at a **live Cloudflare Pages preview**.
- SEO + a11y + perf + security cross-cutting gates green sitewide.
- `03_DATA_SOURCES.md` complete — every live figure traces to a row, freshness floors met.
- Nightly QA + regression-alert wiring live `[S7a]`.

Until then, **never** emit the promise — keep iterating. Do not lie to exit. Genuinely
blocked on a human-only decision → write it to a top-of-doc `## Open questions`, pick the
safest default, log it, continue with another eligible unit `[S16a]`.

## Stop conditions

No eligible unit · budget wall · scheduled session-reset sleep · human pause. On stop,
report ledger state + open PRs (and, if sleeping, the wake time).

---

### Launch line

```
/ralph-loop "Read docs/phases/v1/PROGRESS.md then run docs/phases/v1/LOOP_PROMPT.md from Step 0. Build V1 unit by unit, serena-on, gate every unit, token/session sleep discipline. Emit V1 COMPLETE only when its self-check passes." --completion-promise "V1 COMPLETE" --max-iterations 400
```
