# Backlog (post-V1)

Items deferred out of V1 scope. New ideas land here, not in V1 `[scope discipline]`.

## Polling source (deferred from V1 — decision iter 66)
538's public poll CSVs were discontinued post-ABC (verified iter 60: endpoints serve an HTML
shell; last real update Sept 2024). No open aggregator has both a machine-readable feed AND a
clean reuse license (checked: PollingSource = paid/no-redistribution; USPollingData = no API;
RCP/270toWin/RacetotheWH = proprietary; DDHQ/Silver Bulletin = paid). **Decision: ship V1
without live polling.** The forecast already degrades to fundamentals-only (`blend_margin(None,…)`,
tested) and the polling UI hides when the artifact is empty (`races/[id].astro` guard) — no code
change needed. Connectors (`sources/polls.py`, `pollster_ratings.py`) are kept; they bake the
moment a working source exists.

**V1.1 task:** secure a polling source, then either repoint `polls.py`/`pollster_ratings.py`
(if CSV/API) or build a new connector. Candidates to revisit: Wikipedia race tables (CC BY-SA,
attribute) · a licensed feed (PollingSource/DDHQ) if ToS permits republishing derived averages.

## Cross-party cosponsorship index (v1.6.4 follow-up)
Sponsorship COUNTS shipped (iter 65). The cross-party index `[M7a]` needs each bill's cosponsor
parties (a per-bill fan-out over Congress.gov) — deferred.

## Senate roll-call votes (v1.6.2 follow-up)
House roll-call list shipped (iter 63). Senate roll calls aren't in the Congress.gov API →
needs a GovTrack/senate.gov XML slice. Per-member vote positions (missed-votes) also follow-up.

## House races (V1.1) — DECIDED iter 79 (Andrew)
V1 is Senate-only (33 real Class-II 2026 races). House coverage needs a competitiveness list to
pick which of 435 to cover (Cook/Sabato-style ratings or a curated set). **V1.1 task:** secure a
ratings list → extend `generate_races.py` to emit House race configs → reuse the existing finance/
demographics/forecast joins (district-level). Unblocks find-my-district (needs House districts).

## Interactive map + find-my-district (V1.1) — DECIDED iter 79 (Andrew)
The 0-JS inline district SVG (v1.2.4) meets the district-shape DoD, so the MapLibre+PMTiles
interactive map [P8a] is a V1.1 enhancement. **V1.1 tasks:** (1) generate PMTiles from TIGER
(tippecanoe) → upload to R2 → MapLibre island; (2) find-my-district (v1.2.5) — needs a client-side
Census Geocoder call or a precomputed address→district lookup (the site is static-assets-only, no
Worker handler), and depends on House races to be useful. Both deferred from V1.

## Forecast model refinement (V1.1) — fundamentals beyond partisan lean
V1 forecast (iter 81) is partisan-lean-only: per-state 2024 presidential two-party margin → PVI →
race model → MC chamber sim (real Senate holdover math, Dems need 51). It does NOT yet include the
**midterm penalty** (president's party typically loses ground — material in 2026), **incumbency**,
**campaign-finance** signal, **candidate quality**, or **polls** (dropped V1, no open feed). Effect:
per-race probabilities are overconfident a year out (tight sigma) and the model ignores the midterm
tailwind. baseline.py already carries incumbent_party/finance_net fields; predict_race only consumes
pvi. **V1.1 tasks:** blend incumbency + finance into fundamentals; add a midterm-penalty term;
widen the forecast-horizon uncertainty (sigma as a function of days-to-election); re-backtest.

## ID Senate config: Risch incumbent party mis-coded "other" (should be R)
generate_races.py (FEC import) coded James Risch's party as "other" in us-senate-2026-ID.json; he is
a Republican. The forecast holdover math is robust to this (counts only party=="D" as Dem-aligned),
but the ID race PAGE shows the wrong party chip. **Fix:** correct the party in the config (or map
FEC "other"/IND→party properly in generate_races). Low-risk one-field fix; batched to a data pass.

## Gerrymander fairness (V1.1) — DECIDED iter 82 (Andrew): defer, source-walled
Efficiency gap / mean-median need House results on CURRENT (post-2020) district lines. Clean
current-lines House-by-CD isn't autonomously fetchable: MEDSL 2024-elections-official = president+
senate only; 2022-elections-official = precinct-level zips (heavy precinct→CD aggregation, precincts
split districts); constituency-returns = 1976-2018 (OLD lines); MEDSL House Dataverse = guestbook-
gated. **Decision: defer to V1.1** (same rationale as polling). Compactness (real TIGER geometry)
ships in V1; the fairness section renders an honest "pending a sourced dataset" state. **V1.1 task:**
obtain a Harvard Dataverse API token (unblocks MEDSL House 1976-2024, current lines) OR aggregate the
2022 precinct returns → CD; then `export_fairness` (compute_fairness already exists) → states.json.
