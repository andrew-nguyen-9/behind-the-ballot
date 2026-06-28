# Phase 8 · Forecast (signature module)

> Transparent, heuristic-first forecast with Monte Carlo chamber sim `[N1a]`; ML compared
> to it, used only if it beats it `[N8a]` (ADR 0004). Python in CI → static JSON `[N7a]`.
> Units `v1.8.*`. Prereq: phases 4 (polling), 3 (finance), 5 (demographics). Cite
> `BTB_QUESTIONNAIRE.md` `[id]`.

## Acceptance criteria

- Inputs: polls + fundamentals (finance, incumbency, partisanship, ratings) `[N2a]`;
  partisan baseline = prior-presidential/CPVI-style lean per district `[N3a]`.
- Per-race output: **win probability + predicted margin + range** `[N4a]`. Chamber:
  **Monte Carlo → seat distribution + control probability** with national-swing
  correlation `[N5a,N6a]`.
- Senate poll-heavy, House fundamentals-heavy `[N14a]`; key governors same engine `[N15a]`.
- **Backtest on 2018/2022 + calibration shown** `[N9a]`; seeded sims, versioned model,
  tests `[N13a]`. Nightly rebuild `[N10a]`; daily snapshots → "forecast over time"
  `[N11a]`. Open methodology + downloadable inputs `[N12a]`. Post-election scorecard
  planned `[N16a]`.
- Forecast figures record union-of-input provenance `[R14a]` (no own source row).

## Units

| Slug | Prereq | Check | Status |
|---|---|---|---|
| `v1.8.1-baseline-fundamentals` | v1.5.2 | per-district partisan baseline (CPVI-style) + fundamentals features `[N3a,N2a]` | pending |
| `v1.8.2-race-model` | 8.1,v1.4.3,v1.3.3 | per-race win prob + margin + range (Senate/House/Gov variants) `[N4a,N14a]` | pending |
| `v1.8.3-montecarlo-chamber` | 8.2 | seeded MC sim w/ correlated swing → seat dist + control prob `[N5a,N6a,N13a]` | pending |
| `v1.8.4-backtest-calibration` | 8.2 | 2018/2022 backtest + calibration plot; gate blocks if uncalibrated `[N9a]` | pending |
| `v1.8.5-ml-challenger` | 8.4 | ridge/GBM on fundamentals compared to heuristic; adopt only if it beats `[N8a]` | pending |
| `v1.8.6-forecast-ui` | 8.3 | forecast pages: race + chamber, snapshots-over-time, methodology + downloads `[N11a,N12a]` | pending |
| `v1.8.7-snapshot-store` | 8.3 | nightly snapshot to Neon small-state + history artifact `[N10a,N11a,O2a]` | pending |
