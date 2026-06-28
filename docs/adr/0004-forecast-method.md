# 0004 · Forecast method

**Status:** Accepted · 2026-06-28

## Context
A 538-style forecast is a V1 goal, but a complex ML model is hard to validate, explain,
and defend on a non-partisan site, and risks overfitting with limited free compute.

## Decision
**Heuristic-first, Monte Carlo** simulation as the V1 forecast `[N1a]`. Add ML **only if
it measurably beats** the heuristic on backtests `[N8a]`. Inputs are the polling +
finance + demographics source rows plus prior-cycle results; every snapshot records its
input provenance `[R14a]`. Methodology is published for neutrality.

## Consequences
- Explainable, defensible, cheap to run in CI.
- Backtest harness is required before any ML is considered (a gate, not a maybe).
- Forecast figures have no upstream `DATA_SOURCES` row of their own — provenance is the
  union of input rows (noted in `03_DATA_SOURCES.md`).
