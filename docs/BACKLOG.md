# Backlog (post-V1)

Items deferred out of V1 scope. New ideas land here, not in V1 `[scope discipline]`.

## Session-D review — parked findings (E4.2 integration review)
Surfaced during the `dev..integration` code review + browser QA. All are latent (guard-tightening on
data paths that ship honest-empty today), so parked rather than fixed at promotion. Fixed items (brand
CTA contrast, mobile-header overflow, table keyboard access, SVG-map link a11y, House 435/218,
alert-channel isolation, certified-only fairness gate) landed on `integration`.

- **CD demographic-change can cross a redistricting boundary** (`export_web.py` `export_demographic_changes`):
  when `CHANGE_CD_EARLY` (2022) is absent from baked ACS years, `cd_early` falls back to `years[-2]`,
  which can be a pre-2020-lines vintage → joins the same geoid across different geography (the [L547]
  error the 2022 constant exists to prevent), with no `cd_crosses_redistricting` caveat flag (states
  have one). **Fix:** require `cd_early >= CHANGE_REDISTRICTING_YEAR`; else skip CD changes / stay
  honest-empty. Latent until a multi-year CD ACS bake runs (ties to the CENSUS_API_KEY multi-year work).
- **FEC fetch failure masquerades as an empty candidate list** (`generate_races.py`): `json.loads(...).get("results", [])`
  turns any FEC error/rate-limit body into `[]`, committing a race that looks honest-empty but is a
  fetch failure. **Fix:** assert HTTP 200 / a `results` key and raise-or-skip-and-warn. Bake-time only.
- **Primary-results bake has no per-state isolation** (`sources/primary_results.py` `run()`): one state's
  fetch/parse exception aborts the whole election-night bake. **Fix:** try/except per state, log + continue.
  Election-night-ops hardening; `ACTIVE_STATES=[]` today so unreachable.
- **Fairness race-level fields taken from an arbitrary row** (`export_web.py` `export_results`, `rs[0]`):
  mixed provisional/certified rows inherit the top-vote row's `is_certified`/`pct_reporting`/`as_of`.
  **Fix:** derive from a consistent source (all-certified check / max `as_of`). Results empty today.
- **National demographic totals coalesce missing population to 0** (`demographicChange.ts` `nationalTotals`):
  `r.population ?? 0` understates the sum shown as an authoritative total. **Fix:** skip null-population
  rows (as median-income already does) or flag "partial". Data-gated (needs 2nd ACS year).
- **Search overlay swallows all Pagefind errors** (`SearchDialog.tsx` `.catch(() => {})`): intended for
  the dev-404 case but also hides real prod init failures with no user feedback. **Fix:** narrow to the
  expected 404; surface other errors. Low — progressive-enhancement overlay, `/search` page is the fallback.
- **SVG party fills use `fill="var(--color-party-*)"` presentation attributes** (`USStateMap.astro`,
  `HouseArc.astro`): var() in an SVG presentation attribute is unsupported pre-Safari 16.2 → falls back
  to black. **Verified rendering correct in current Chromium AND WebKit** — not a defect today; noted so
  a future very-old-Safari report has a paper trail. Upgrade path: apply fills via `style="fill:…"` / a class.

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

## Gerrymander fairness — LIVE-JOIN WIRED (E4.1); data-pending (not code-pending)
Efficiency gap / mean-median need House results on CURRENT (post-2020) district lines. Deferred
iter 82 (Andrew) because clean current-lines House-by-CD wasn't autonomously fetchable. **E4.1
resolved the CODE wall:** the Wave-3 election-results connector (`sources/primary_results.py`, state
SoS feeds + Wikipedia call flag + MEDSL certified backfill [E3.2/E3.3]) is now the source, and
`export_web.export_fairness` joins `gold/primary_results` (House general results) ⋈ `gold/tiger`
(current-lines district set) → `compute_fairness` → `gerrymander/states.json`. It is HONEST by
construction: a state's metrics compute only when the FULL set of its (multi-district) House CDs has
reported two-party results — a partial slate, an at-large state, or no results writes nothing, so the
page keeps its honest pending state. **What remains (DATA, not code):** the results connector ships
`ACTIVE_STATES = []` (no committed numbers) and V1 configures only a competitive House subset, so no
state is complete today → fairness is still honestly empty on the live site. Real rows appear the
moment election-night ops turns on a state's House feeds (or runs the MEDSL certified House backfill)
and a full state reports — no further code needed. A future nicety: a nationwide MEDSL House backfill
(Harvard Dataverse token) to populate all 50 states at once instead of per-state as they certify.

## E-3 interactivity — deferred tiers (Wave-2a)

E-3 shipped `docs/design/INTERACTIVITY.md` **Tier 1** (chart readout, table filter/sort, reveal-on-view
islands under `apps/web/src/components/charts/`). Deferred:

- **Tier 2.4 — Scrubbable forecast timeline** over `forecast_snapshots` (slider swaps a pre-baked
  snapshot; all snapshots already static). No-JS: latest snapshot shown. Deferred to keep per-route JS
  in the Lighthouse budget; a natural fit for E-6 (owns `forecast.astro`) to embed a future
  `SnapshotScrubber` island.
- **Tier 2.5 — Map hover highlight** on the results/gerrymander choropleths (county name + value on
  hover/focus). The `ChartReadout` island already delivered by E-3 covers this pattern — E-4 (maps) can
  adopt it by adding `data-readout` marks to the county paths; deferred here only because those pages
  are outside E-3's ownership seam.
- **Tier 3 (do-not-build)** — cross-filtering/brushing between charts, real-time websocket updates,
  anything needing a runtime API or third-party JS. Breaks the static-first + no-tracking invariants.
