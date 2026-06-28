# Behind the Ballot — Autonomous V1 Driver (fresh-session starting prompt)

Paste this whole file as the first message of a **fresh session** in this repo on
branch `planning/v1-docs` (or run `/ralph-loop` pointed at it — launch line at the
bottom). It drives Behind the Ballot from the current half-planned state **all the
way through a shipped V1**, autonomously, token-disciplined, serena-powered.

You honor `/CLAUDE.md` above everything here (no AI attribution on git artifacts).

---

## Step 0 — Boot (do this first, every cold start)

1. **Operating modes:** ensure `/caveman full` + `/ponytail full` + learning/
   explanatory insights are active.
2. **Activate serena for cheap navigation:** call serena `activate_project` on this
   repo, then `initial_instructions`. Use serena `get_symbols_overview` /
   `find_symbol` / `find_referencing_symbols` / `search_for_pattern` for code +
   doc navigation instead of reading whole files — this is the primary token saver.
3. **Re-derive state from disk, not memory:** read `docs/phases/v1/PROGRESS.md`
   (the ledger). It has a `## RESUME` line and a unit table. Everything you need to
   continue is there + in git history. Never assume context from a prior session.

## Mission

Finish V1 end-to-end, in two phases, without human babysitting between units:

- **Phase A — Planning** (if not yet `PLANNING COMPLETE`): execute
  `docs/brainstorming/PLANNING_PROMPT.md` from its `RESUME` pointer until the full
  doc tree exists (incl. `LOOP_PROMPT.md` + a seeded build ledger). Commit each chunk.
- **Phase B — Build**: execute `docs/phases/v1/LOOP_PROMPT.md` as the build
  orchestrator — pick the first eligible `pending` unit from the build ledger, drive
  it to the Definition of Done, gate it, open a PR to `dev` with evidence, update the
  ledger, repeat — until every V1 module is live and green.

V1 modules (from `[E11a]`): race tracker, campaign finance, polling aggregation,
forecast, demographics, caucus/chamber, member analytics, gerrymander-lite. Issue +
party-demo analytics are stubbed/deferred `[E6a,J2a]`.

## Hard rules (non-negotiable)

- **`main` is a wall** `[S5a]`. Never commit/merge/push to `main`. Planning commits to
  `planning/v1-docs`; build auto-merges green units to `dev`; humans own `main`. Never
  force-push.
- **Verification gate before any unit is "done"** `[S4a]` — re-run yourself, paste
  output: build green; `astro check` clean; tests green; axe + Lighthouse ≥90 mobile;
  **every published figure traces to a `DATA_SOURCES.md` row + freshness floor met**;
  responsive screenshots 360/768/1280. "It builds" is not done.
- **Budget check before every spawn/heavy step** `[S6a]` — Actions minutes, API quota
  (`api.data.gov`), R2/CDN bandwidth, **and your token/session budget (below)**. Tight
  → mark unit `blocked`, log why, continue with another eligible unit.
- **Evidence or it didn't happen** `[S14a]` — each unit PR carries screenshots +
  Lighthouse + the data-integrity log.
- **Cold workers, model-tiered** `[Z6a,Z7a]` — dispatch a fresh sub-agent per build
  unit (it re-derives from plan files, not your chat). Opus orchestrates + gates;
  cheaper models do mechanical units. Keep ≤2–3 worktrees live `[S13a]`.
- **Scope discipline** — build only what the answered questionnaire sanctioned. New
  ideas → `docs/BACKLOG.md`, not into V1.

## Token & session discipline (the sleep-through-reset rule — obey precisely)

Never die mid-write; never burn into a hard stop.

1. **Checkpoint is atomic + frequent.** After each unit (and before any long step)
   flush state to `PROGRESS.md` (+ the file in progress) so a cold restart loses
   nothing. Important state lives on disk, never only in context.
2. **Context handoff — start fresh, never compact.** Two thresholds:
   - **~90%** → do **not** start a new unit. Finish the current atomic write, update
     `RESUME:`, and **end the turn**; the loop re-feeds and the next iteration continues
     from `PROGRESS.md` in a fresh, smaller context. This is the "continue in a new
     session" behavior.
   - **~98%** → hard stop mid-flight: write `RESUME:` and end immediately.
   Prefer **dispatching a cold sub-agent** for heavy-output units so the orchestrator
   window stays lean. (Capability limit: an agent can't literally open a new chat window
   and close the old — auto-compaction is the platform default. Cold sub-agents +
   checkpoint-then-end-turn / `ScheduleWakeup` give the same continuity since all state
   is on disk.)
3. **Usage session ~98%** → do **not** keep working. (a) Checkpoint + `RESUME:` note.
   (b) Determine when the usage window resets. (c) Call **`ScheduleWakeup`** with
   `delaySeconds = (seconds until that reset) + 60` — i.e. **wake ~1 minute after the
   session refreshes** — and pass **this same prompt** back as the wake prompt so the
   loop self-resumes. Reason: "sleeping past session reset to avoid mid-unit cutoff."
   Pick the delay from the real reset time, not a round number (runtime clamps
   `[60,3600]`; if reset is further out, wake at the clamp and re-check). (d) Stop.
   On wake: Step 0 again (serena + read ledger), continue from `RESUME:`.
4. **Frugality every turn:** serena over file reads; rtk on dev ops; caveman/ponytail
   keep output + builds minimal; context7 only when a library doc is actually needed;
   batch independent tool calls; don't re-read files the harness already tracks.

## Loop control (this prompt runs under /ralph-loop)

Same prompt re-feeds each iteration; your work persists in files + git. Each iteration:

1. Step 0 (modes + serena + read ledger).
2. Do the next eligible unit (Phase A doc, or Phase B build unit) → gate → commit /
   PR → update one ledger row + activity log.
3. Respect the token/session discipline above.
4. **Completion:** output `<promise>V1 COMPLETE</promise>` **only when ALL are true**:
   Phase A done (full doc tree incl. `LOOP_PROMPT.md`); every V1 module unit `done`
   on the build ledger and passing the gate at a live Cloudflare Pages preview; SEO +
   a11y + perf + security cross-cutting gates green sitewide; `DATA_SOURCES.md`
   complete. Until then, **never** emit the promise — keep iterating. Do not lie to
   exit. If genuinely blocked on a human-only decision, write it to a top-of-doc
   `## Open questions`, pick the safest default, log it, and continue with another
   eligible unit — a blocked unit never halts the whole loop `[S16a]`.

## Stop conditions

No eligible unit left · a budget wall · a scheduled session-reset sleep · a human
pause. On stop, report the ledger state + open PRs (and, if sleeping, the wake time).

---

### Launch line (paste in the fresh session)

```
/ralph-loop "Read docs/phases/v1/PROGRESS.md then run docs/brainstorming/AUTONOMOUS_V1_PROMPT.md from Step 0. Autonomous through V1, serena-on, token and session sleep discipline. Emit the V1 COMPLETE promise tag only when its self-check passes." --completion-promise "V1 COMPLETE" --max-iterations 200
```

(`--max-iterations` is a backstop; the real stop is the genuine `V1 COMPLETE`
promise. Run `/caveman full` + `/ponytail full` first if not active.)
