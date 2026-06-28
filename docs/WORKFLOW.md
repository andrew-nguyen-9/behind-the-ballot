# Workflow

> The branch ritual the loop and humans both follow. **`main` is a hard wall** `[S5a]`.
> Decisions cite the questionnaire `[id]`.

## Branch model

```
main      ← humans only. Loop never commits/merges/pushes here. Never force-push. [S5a]
  ▲ (human-approved PR, manual)
dev       ← integration. Loop auto-merges green units here. [S5a]
  ▲ (auto-merge on green gate)
unit/*    ← one branch per ledger unit (e.g. unit/v1.3.2-polling-aggregation)
planning/v1-docs  ← this planning effort commits here (no app code)
```

## Per-unit ritual (build loop)

1. Orchestrator picks first eligible `pending` unit from `PROGRESS.md` `[S3a,S17a]`.
2. Budget check before spawn — Actions minutes, API quota, R2/CDN bandwidth, token/session
   `[S6a]`. Tight → mark unit `blocked`, log why, pick another.
3. Spawn a **fresh cold sub-agent** on a `unit/*` branch; it re-derives from plan files,
   not chat `[Z6a]`. Model-tiered: Opus orchestrates/gates, cheaper models do mechanical
   units `[Z7a]`. ≤2–3 worktrees live `[S13a]`.
4. Worker drives the unit to `04_DEFINITION_OF_DONE.md`.
5. Orchestrator **re-runs the gate**, pastes output, attaches evidence `[S4a,S14a]`.
6. Pass → open PR `unit/* → dev`, auto-merge on green. Update one ledger row + one
   activity-log line `[S17a]`. Fail → back to worker or mark `blocked`.

## Commits & PRs

- Conventional commits; `docs:` for planning, `feat:`/`fix:` for build units.
- **No AI/assistant attribution** on commits, PR titles/bodies, or branch names
  (per `/CLAUDE.md`).
- Auto guardrails: read/build/test/git on non-main are auto; **deploy + any main change
  are human-gated** `[S12b]`.

## QA cadence (separate from the build loop)

Nightly scheduled Action re-runs the gate against the **live** site + validates data
freshness; on regression it opens/updates a deduped GitHub issue **and** emails the
maintainer with summary + diff + run link + severity `[S7a,S9c,S10a,S11a]`.
See ADR `loop-architecture` and `email-alias` for the email wiring.
