# 0008 · Autonomous loop architecture

**Status:** Accepted · 2026-06-28

## Context
V1 is large (8 modules × many states/races). Building it by hand is slow; building it in
one long agent session overflows context and burns tokens. Need a repeatable, resumable,
budget-aware build process.

## Decision
**ralph-loop + `LOOP_PROMPT.md` + `PROGRESS.md` ledger** `[S1a]`. An **orchestrator**
(Opus) reads the ledger, picks the first eligible `pending` unit, **spawns a fresh cold
sub-agent** that re-derives from plan files (not chat) `[S3a,Z6a]`, then **re-runs the
gate itself**, opens a PR with evidence, updates one ledger row, repeats `[S4a,S14a,S17a]`.
Model-tiered: Opus orchestrates/gates, cheaper models do mechanical units `[Z7a]`.

**Hard rules:** `main` is a wall — loop merges to `dev`, humans own main, never
force-push `[S5a]`. Budget check before every spawn (Actions/API/bandwidth/tokens) `[S6a]`;
tight → mark `blocked`, continue. ≤2–3 worktrees `[S13a]`. Token/session discipline:
checkpoint atomically, and `ScheduleWakeup` past a usage-window reset rather than dying
mid-unit. Nightly QA is a **separate** cadence `[S7a]`.

## Consequences
- Any unit is resumable from `PROGRESS.md` by a cold session — no context heirloom.
- A blocked unit never halts the whole loop `[S16a]`.
- Correctness rests on the orchestrator re-running the gate, not trusting the worker.
- This is the contract `LOOP_PROMPT.md` (P11) encodes verbatim.
