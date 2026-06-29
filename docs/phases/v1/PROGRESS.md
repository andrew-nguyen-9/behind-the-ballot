# V1 Planning — Progress Ledger

> 🟢 **LIVE PREVIEW (iter 66):** https://behind-the-ballot.hh5zvph54s.workers.dev — Cloudflare
> Workers Static Assets, auto-deployed by Workers Build on every push to `dev` (commits are
> auto-pushed; origin/dev == local dev). Home/races/forecast return 200. Full local gate green
> (pytest 141, ruff, build, links, Lighthouse perf/a11y/bp/SEO ≥0.9).
>
> ⏳ **LIVE JOINS IN PROGRESS — architecture established (iter 67).** Pattern: `pipeline/
> btb_pipeline/export_web.py` reads gold (`data/gold/*`, ephemeral) → writes display-ready JSON
> into COMMITTED `apps/web/src/data/*` (ships in the Cloudflare build; static SSG needs data at
> build time). Nightly Action (v1.10.x) will re-bake+export+commit→auto-deploy. **REAL RACE SET
> (iter 69): 33 Class-II Senate 2026 races auto-generated from FEC** (`generate_races.py`) with
> real candidates (e.g. TX: Cornyn-INC, Talarico, Crockett…). Live joins done: **members** (537),
> **demographics** (real ACS per race), **finance** (real FEC receipts/cash per candidate). Sample
> races (OH-Sen, PA-05) removed. **Still sample/pending:** forecast (per-race needs engine on real
> PVI inputs — chamber /forecast still sample), districts/maps + House key races (TIGER/geo chain),
> gerrymander. Then v1.10.x crons + live-URL a11y/SEO/security sweep. Promise withheld until real
> data is on EVERY page.


Dual purpose: (1) the ledger this **planning** loop reads to pick the next doc;
(2) the template the **build** loop will reuse for race/module units. A fresh
session reconstructs all state from this file. One activity-log line per touched row.

Status: `pending | in-progress | review | blocked | done`. Pick the first `pending`
whose prereq is `done`.

## ⚠️ BLOCKER (iter 57) — `.env` is an EMPTY TEMPLATE; provisioning NOT actually done

The launch prompt asserts "PROVISIONING IS DONE — all secrets are in." Disk says otherwise:
`/.env` exists (gitignored) but **every value is 0 chars** — it's the unfilled scaffold.
`scripts/resume.sh --no-deploy` fails at the secret check (all 7 required vars empty), so
the gate→deploy→live-preview→freshness chain cannot run, and no figure can be verified at a
live Cloudflare URL. The credential wall `[S16a]` is still up in reality regardless of the
prompt's claim. **Human action: paste real values into `.env`** (keys already named correctly:
DATA_GOV_API_KEY, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, R2_BUCKET, DATABASE_URL,
SMTP_USER, SMTP_PASS — see `docs/SETUP_SECRETS.md`). Until then the loop builds only the
code slices of the "unblocked" units (dispatch wiring, datastore client, join logic) that are
fixture-testable now; live invocation + deploy + freshness stay gated. **`V1 COMPLETE` cannot
be emitted** — never lie to exit.

## Open questions (human decision — safest default picked, loop continues [S16a])

3. **OPEN (iter 70): per-race forecast needs a partisan-lean (PVI) source.** `race_model.predict_race`
   requires `fundamentals_pvi` per race; `baseline.cook_pvi` derives it from a prior-election
   district/state two-party Dem share minus the national share — but **no prior-election-results
   source is baked** (configs carry candidates only; ACS is demographics, not partisanship; FEC is
   money). So the chamber `/forecast` + per-race forecast sections still ship the **sample**
   `chamber-senate.json` — the most prominent fake figure left on the site. Same shape as the
   polling gap: a real published forecast can't fabricate the lean input. **UPDATE (iter 73): the
   placeholder sample forecast is now REMOVED** — `/forecast` renders an honest "not yet published"
   state (no fabricated figures shipped to users); the real forecast returns once the PVI source
   below is confirmed. **Recommended default
   (next iter):** MIT Election Data + Science Lab state presidential returns (Harvard Dataverse,
   machine-readable CSV, CC-BY) → state two-party Dem share → `cook_pvi` vs national → real
   fundamentals-only forecast (no polls in V1; methodology page already explains fundamentals).
   **Human action:** confirm MIT Election Lab is an acceptable source+license, or name another;
   then build `export_forecast` (new connector + DATA_SOURCES row + integrity). Until resolved,
   forecast stays sample and `V1 COMPLETE` is withheld.

2. **RESOLVED (iter 66): valid `CENSUS_API_KEY` in.** ACS now live-bakes **440 rows** (435
   districts + DC/territories). Finding that drove it: ACS needs a separate Census key (the
   data.gov key 302s to missing_key.html); a placeholder key 40-char'd but returned
   invalid_key.html until the human swapped in a real one. `api.census.gov`
   302-redirects a `DATA_GOV_API_KEY` to `missing_key.html` — Census requires its own key
   (census.gov/data/key_signup.html), distinct from the data.gov key that works for OpenFEC.
   **Fix shipped:** ACS connector now reads `CENSUS_API_KEY` (falls back to `DATA_GOV_API_KEY`
   for compat) + raises a clear error on the HTML missing-key page instead of a JSONDecodeError;
   SETUP_SECRETS corrected; `CENSUS_API_KEY=` added to local `.env`. **Human action:** get a free
   Census key + fill it. Demographics (v1.5.x) live-bake pends this.


1. **RESOLVED (iter 66): polling DROPPED from V1.** No open poll aggregator has a machine-readable
   feed + clean reuse license post-538 (checked PollingSource/USPollingData/RCP/270toWin/DDHQ/
   Silver Bulletin). **Human decision: ship V1 without live polling**, revisit in V1.1 (see
   `docs/BACKLOG.md`). No code change — the forecast already falls back to fundamentals-only
   (`blend_margin(None,…)`, tested) and the polling UI hides on empty (`races/[id].astro` guard).
   So polling is **not a V1-COMPLETE blocker** anymore. Original finding:

   538 poll CSVs are dead (confirmed live iter 60). Both `projects.fivethirtyeight.com/
   polls/data/*.csv` and `…/polls-page/data/*.csv` now return an **ABC News HTML shell**
   (200, `text/html`, identical 308 KB for every filename) — the public CSV downloads were
   discontinued post-ABC, exactly the risk DATA_SOURCES.md L14 flagged. Effect: the polling
   module (v1.4.x) has **no live source**; connectors correctly bake 0 rows (no crash).
   **Safest default taken:** polling degrades gracefully (no polling section renders when the
   artifact is empty) and `V1 COMPLETE` cannot claim live polling. **Human decision needed:**
   pick a replacement polling source + license (candidates: a 538/ABC GitHub mirror if one
   exists, Wikipedia race tables CC BY-SA [H1a], or another aggregator). Until then polling is
   source-pending, not done-live.

## RESUME  (current as of iter 74)

iter 74: **live-preview SEO/a11y/perf/security sweep — CLOSED GREEN.** Ran Lighthouse against the
**live Cloudflare URL** (not static dist) for 5 representative page types — scores (perf/a11y/bp/seo):
`/` 100/95/96/100 · `/races` 100/100/96/100 · `/forecast` 100/100/96/100 · `/races/us-senate-2026-TX`
100/100/96/100 · `/sources` 100/100/96/100. **All ≥90, zero assertion failures** (`assertion-results
.json` empty). With iter-72 security headers (CSP/HSTS/X-Frame/X-CTO/Referrer/Permissions all present)
+ iter-72 canary (9 routes 200, no 307), **completion gate #2 (SEO+a11y+perf+security green sitewide
at the live preview) is now MET.** No code change — verification only (lhci ran via a scratchpad
config; `.lighthouseci` not committed). Minor note: home a11y 95 (passes; likely a small contrast/
landmark nit) → BACKLOG, non-blocking. **V1-COMPLETE self-check status:** ✅ #2 live sweep · ✅ #3
freshness (finance/demographics/members real+fresh; forecast honestly pending; polling dropped) ·
⏳ #1 module completeness — BLOCKED on: forecast real (Open Q#3 PVI source, human confirm), geo chain
(TIGER/R2: v1.1.2/1.3/1.4 + v1.2.5 — heavy but autonomous-feasible), House key races (needs a
competitiveness list — human), gerrymander real geometry (TIGER). ⏳ #4 DATA_SOURCES (update when
forecast/geo sources land). **These #1 blockers are the only thing between here and V1 COMPLETE.**
**Next eligible:** start the geo chain (TIGER district-geometry connector → real gerrymander metrics
+ map prereq — the biggest autonomous-feasible remaining surface); or v1.10.3/4/5 alerts.

## RESUME  (current as of iter 73)

iter 73: **integrity fix — stopped publishing the fabricated forecast.** `/forecast` was rendering
the SAMPLE `chamber-senate.json` as a real result ("48% Dem Senate control, as of 2026-03-15,
10,000 sims") — fabricated figures on a live site whose tagline is "every figure traces to a public
source." Removed `src/data/forecast/chamber-senate.json`; the page's existing empty-state now shows
honest copy: "not yet published … we don't publish placeholder numbers" + sources link. Home page's
Senate-control headline was already `{senate && …}`-guarded → degrades cleanly (no break). Made
`forecast.test.ts` data-agnostic (asserts no fabricated chamber rows; any real row must carry a
sources-traceable as_of). Matches the polling graceful-degradation precedent. The real forecast
returns once Open Q#3's PVI source is confirmed. Gate: astro check 0/0/0, vitest 35, build, links
ok; verified built page has 0 fabricated figures + the honest copy. Per-race forecast was already
absent (no per-race files → section hidden). Direct to dev. **Now: NO fake figures anywhere on the
live site** — finance/demographics/members real; forecast honestly pending; polling hidden. **Next
eligible:** lighthouse-at-live-URL; forecast real (Open Q#3); geo chain; v1.10.3/4/5 alerts.

## RESUME  (current as of iter 72)

iter 72: **redirect fix CONFIRMED LIVE + post-deploy canary shipped.** Re-curled after Workers
Build redeployed: all 9 key routes (`/races /forecast /sources /members /gerrymander /chamber
/articles /search /`) now **200, no 307** — iter-71 `drop-trailing-slash` fix verified at the live
preview ✓ (the earlier persistent 307 was deploy lag). Codified the live-health checks into
`scripts/canary.mjs` (dependency-free, `redirect:"manual"` so a 307 = fail; checks 9 routes 200 +
CSP/HSTS/X-CTO headers) + `.github/workflows/canary.yml` (scheduled 09:40 UTC, ~20m after the
nightly refresh redeploys, + manual dispatch). ponytail: NO SMTP — a red scheduled job triggers
GitHub's native owner-failure email; richer delta alerts = v1.10.3. Canary run locally now: **ok —
9 routes 200, headers present.** Live sweep status: routes ✓, security headers ✓, perf/a11y/SEO
green on static dist (local lhci, iter 56) — **still want a lighthouse run against the live URL**
to fully close the sweep. **Next eligible:** lighthouse-at-live-URL; forecast (Open Q#3 PVI source);
geo chain; v1.10.3/4/5 alerts.

## RESUME  (current as of iter 71)

iter 71: **live-preview sweep started — fixed a real redirect regression.** Curled the live
Worker: security headers all present (CSP/HSTS/X-Frame/X-CTO/Referrer/Permissions — `_headers`
IS honored on Workers Static Assets ✓), all pages reachable, BUT `/races` `/forecast` `/sources`
etc. returned **307 → /races/**: Astro emits directory-format pages while every internal nav link
is slashless, and wrangler's default `auto-trailing-slash` redirected each → a hop on every nav
(perf/SEO papercut; local link-checker missed it, resolves on disk). **Fix:** `wrangler.jsonc`
`assets.html_handling: "drop-trailing-slash"` (confirmed valid enum via CF docs) → serves the
index at the slashless path (200, no redirect), matching the links. jsonc valid; no build/test
impact (runtime Worker config). Direct to dev → Workers Build redeploys. **Verify next iter:**
re-curl `/races` should be 200 (no 307). No styled 404 page exists (Astro has none) → left
`not_found_handling` default (live 404 returns 404 code); styled-404 → BACKLOG. **Sweep remaining:**
re-curl confirms post-deploy + lighthouse-at-live-URL. **Next eligible:** finish sweep; forecast
(Open Q#3 PVI source); geo chain; v1.10.3/4/5 alerts.

## RESUME  (current as of iter 70)

iter 70: **built the nightly live-join refresh Action** (the workflow the ledger kept deferring
to). `.github/workflows/refresh.yml` — schedule (09:17 UTC) + manual dispatch, `contents:write`,
concurrency-guarded; bakes ONLY the consumed sources (`members voteview acs fec`, not `bake all`,
to respect api.data.gov quota [S6a]), runs `export_web`, commits any `apps/web/src/data` change to
`dev` → connected Workers Build auto-deploys. Race set NOT regenerated nightly (stable roster).
**Verified the workflow's commands locally with real keys:** baked all 4 sources + exported (1
roster, 33 demographics, 33 finance) — pipeline green end-to-end; export is deterministic (no diff
vs iter 69 → confirms freshness already met, idempotent). Gate: yaml valid, pytest 147, ruff clean
(web untouched). Logged **Open Q#3**: per-race forecast still sample — needs a real PVI/partisan-lean
source (recommended MIT Election Lab); chamber `/forecast` is the most prominent fake figure left.
**Next eligible:** resolve Open Q#3 → `export_forecast`; OR geo chain (TIGER/R2: v1.1.2/1.3/1.4,
v1.2.5); OR live-preview a11y/SEO/security sweep; OR v1.10.3/4/5 (regression/budget/weekly alerts).

## RESUME  (iter 69)

iter 69: **REAL race set + finance live join** (user decision: auto Senate + House key races —
Senate slice this iter). `generate_races.py` pulls the 33 Class-II 2026 Senate seats from FEC
`/candidates/totals/` (top-6 by receipts ≥ $50k), writes real configs (candidates: name/party/
incumbent/fecCandidateId) + bakes 141 real candidate totals to gold/fec. `export_finance` joins
gold/fec ⋈ configs → per-race finance (TX: Cornyn $13.5M, Talarico $40.3M…). Removed the 2 sample
races (OH-Sen not a real Class-II seat; PA-05 → House key races later) + their orphan data. Fixed
6 sample-coupled tests (schema/demographics/finance → real TX; polling/forecast-per-race/geo →
null, reflecting dropped/pending domains). Gate: pytest 147, ruff, astro 0/0/0, vitest 35, build
33 real Senate race pages, links ok. **Live joins done: members, demographics, finance.**
**Next:** House key races (needs a competitiveness list — ask/curate), per-race forecast
(export_forecast: engine on real PVI/finance inputs; chamber /forecast still sample), gerrymander.

## RESUME  (iter 68)

iter 68: **live joins — demographics.** `export_demographics` (gold/census_acs → per-race
`src/data/demographics/<id>.json`): senate/governor = state rollup (reused `rollup_by_state`),
house = the district; FIPS↔postal map added. Real: OH 11.77M/$67,478, PA-05 763k/$83,666.
urbanization left `null` (ACS gold has no urban/rural split) → made the field optional in TS +
the UI hides it. 2 demographics tests made data-agnostic. Gate: pytest 144, ruff, astro 0/0/0,
vitest 37, build, links ok. **Live-join done: members, demographics. Next: finance** (gold/fec +
committee_link + race-config candidates → per-race finance), then forecast, districts, gerrymander.

## RESUME  (iter 67)

iter 67: **live joins started — pattern proven on members.** New `export_web.py` (gold →
committed `src/data/*`); `export_members` joins gold/members ⋈ gold/voteview → `roster.json`
(537 REAL members, real ideology, party mapped to letters). Build emits 537 real member pages
(was 3 sample). Made the 4 fixture-coupled member tests data-agnostic (they asserted sample IDs/
counts; now assert invariants over the real roster). Gate: pytest 143, ruff, astro 0/0/0, vitest
37, build 537 member pages, links ok. **Next export_* fns:** finance (gold/fec + committee_link +
race configs), demographics (gold/census_acs), forecast (run engine on real inputs), then
districts/gerrymander. Each = one export fn + repoint/keep loader + data-agnostic tests.

## RESUME  (iter 66)

iter 66: **major unblock — human fixed all remaining secrets + ran the prod DB migrate.**
- All 7 `.env` secrets now valid (CLOUDFLARE_ACCOUNT_ID, SMTP_PASS, CENSUS_API_KEY filled).
- **Live Neon migrate applied** (human ran `db:migrate`); `forecast_snapshots` table verified on
  the real DB (exact schema, 0 rows) → v1.0.4 + v1.8.7 LIVE.
- **ACS live-bakes 440 rows** (valid Census key) → v1.5.1 LIVE.
- **Polling DROPPED from V1** (human decision): no open feed + clean license post-538; forecast
  already falls back to fundamentals-only, UI hides empty; backlogged to V1.1 (`docs/BACKLOG.md`).
  Polling no longer blocks V1 COMPLETE.

**Live real data now — 7 sources:** FEC 200 · members 537 · voteview 12,584 · rollcall 477 ·
committee_link · sponsorship · census_acs 440. **DEPLOY CONFIRMED LIVE** (iter 66) at https://behind-the-ballot.hh5zvph54s.workers.dev —
Workers Build auto-deploys on push to dev (commits auto-push). Full gate green incl. Lighthouse.
**Remaining for V1 COMPLETE:** (1) **live joins** (THE big one) — site loaders read sample
fixtures (`src/data/*`); wire the 7 baked gold artifacts into the build so pages show real
figures + freshness; (2) geo chain (TIGER/R2: v1.1.2/1.3/1.4, v1.2.5); (3) v1.10.x crons/alerts
(Actions+Gmail, secrets now in); (4) a11y/SEO/security sweep at the LIVE preview (local Lighthouse
green; need the live-URL run + security headers check). THEN the promise self-check.

## RESUME  (iter 65)

iter 65: **built v1.6.4 sponsorship counts + live-verified.** `sources/sponsorship.py` — per-member
sponsored + cosponsored totals from Congress.gov `pagination.count` (2 calls/member); CLI-registered;
new DATA_SOURCES row + integrity `sponsorship` (floor 14, doc-sync ok). 3 fixture tests (141 pytest,
ruff clean). Live: Pelosi 199/5083, Sanders 1180/7896 — real. Cross-party cosponsorship INDEX [M7a]
deferred (per-bill cosponsor-party fan-out). **Live real data now (6 sources): FEC 200, members 537,
voteview 12,584, rollcall 477, committee_link, sponsorship.** Deploy still blocked: CLOUDFLARE_ACCOUNT_ID
+ SMTP_PASS empty; CENSUS_API_KEY invalid; 538 polls dead; prod DB migrate human-gated. Next buildable:
geo chain (TIGER bulk, no key) or v1.10.x workflows/scripts.

## RESUME  (iter 64)

iter 64: **built v1.3.2 candidate→committee linkage + live-verified.** `sources/committee_link.py`
— OpenFEC `/candidate/{id}/committees/`, picks the principal committee (designation "P") [G12a];
CLI-registered; new integrity row `committee_link` (floor 14, token "OpenFEC linkages", doc-sync
ok). 5 fixture tests (138 pytest, ruff clean). Live: 3/4 real FEC candidates linked to real
principal committee IDs (4th has none filed — correct). This is the join feeding finance-identity
(v1.6.5). **Live real data now (5 sources): FEC 200, members 537, voteview 12,584, rollcall 477,
committee_link.** Deploy still blocked: CLOUDFLARE_ACCOUNT_ID + SMTP_PASS empty; CENSUS_API_KEY
invalid; 538 polls dead; prod DB migrate human-gated.

## RESUME  (iter 63)

iter 63: **built v1.6.2 House roll-call connector + live-baked 477 real rows.** Verified the
data.gov key authenticates Congress.gov (unlike Census). `sources/rollcall.py` (Congress.gov
`/house-vote/{congress}/{session}`, env-keyed, transport-injected), registered in the CLI
dispatch + integrity `rollcall` row (floor 7). 5 fixture tests (133 pytest, ruff clean), then a
real `bake rollcall` → 477 House votes. Senate roll calls (not in Congress.gov API → GovTrack/
senate.gov) + per-member positions (missed-votes, v1.6.4) are follow-ups. **Also found:** the
human-filled `CENSUS_API_KEY` is invalid (api.census.gov → invalid_key.html) — placeholder, needs
a real key (Open Q#2). **Live real data now: FEC 200, members 537, voteview 12,584, rollcall 477.**
Still gated: ACS (bad Census key), polls (538 dead), deploy (CLOUDFLARE_ACCOUNT_ID empty), alerts
(SMTP_PASS empty), prod DB migrate (auto-mode denied → human).

## RESUME  (iter 62)

iter 62: added `dbCredentials` to `drizzle.config.ts` (needed by push/migrate; `generate` still
works with no env). **Attempted the live Neon migration** (`drizzle-kit migrate`) to create the
`forecast_snapshots` table in prod + smoke-test the snapshot store against real Postgres —
**auto-mode classifier DENIED it as an unauthorized production DB deploy** (correct). The live
migration is **human-gated**: run `pnpm --filter web db:migrate` outside auto mode (or via
`resume.sh` once authorized) to apply the schema to Neon. Snapshot-store logic is already proven
against in-process pglite, so this is the connection/prod-apply step only. Config committed.

## RESUME  (iter 61)

iter 61: **secrets present are REAL** (iter-60 "placeholder" worry was a probe bug — I measured
variable-NAME lengths, not values). `DATA_GOV_API_KEY` is 40 chars, proven by a live **FEC bake
= 200 real rows**. `DATABASE_URL` is real too. Genuinely empty: `CLOUDFLARE_ACCOUNT_ID`,
`SMTP_PASS` (+ new `CENSUS_API_KEY`). So `resume.sh` still fails its presence check on the 2
missing → no deploy yet. **Live-data status now:** FEC ✓ (200), members ✓ (537), voteview ✓
(12,584) — all real, fresh. ACS ✗ needs `CENSUS_API_KEY` (Open Q#2, connector fixed). polls ✗
538 source dead (Open Q#1). **Human to-dos to unblock the rest:** fill `CLOUDFLARE_ACCOUNT_ID`
(deploy), `SMTP_PASS` (alerts), `CENSUS_API_KEY` (demographics); decide a replacement polling
source. Then `./scripts/resume.sh` runs the live gate+deploy.

## RESUME  (iter 60)

iter 60: **partial secrets arrived (5/7)** — DATA_GOV_API_KEY, CLOUDFLARE_API_TOKEN, R2_BUCKET,
DATABASE_URL, SMTP_USER present; CLOUDFLARE_ACCOUNT_ID + SMTP_PASS still empty (resume.sh still
fails presence check; some present values look like short placeholders, e.g. DATABASE_URL=12
chars). Did the first **real live bakes** of the keyless connectors via the v1.1.6 dispatch:
`members` → **537 rows**, `voteview` → **12,584 rows** (real, fresh as_of today) — proves the
dispatch end-to-end with real data, not fixtures. `polls`/`pollster_ratings` baked **0 rows** →
investigated → **538 CSV endpoints dead** (see Open questions #1). No code change this turn;
findings logged. v1.1.6 now: live-baked for keyless members/voteview; FEC/ACS keyed bakes pend a
real api.data.gov key (present value may be a placeholder); polls pend a replacement source.

## RESUME  (iter 59)

iter 59: **built v1.8.7-snapshot-store.** `src/lib/db/snapshots.ts` — `writeSnapshot` /
`recentSnapshots(unitId, limit)` (db injected, so prod uses getDb() + cron, tests use pglite).
Verified against an in-process pglite Postgres (applies the real generated migration) — 2 tests,
no live Neon needed. Gate: astro check 0/0/0, vitest 37, build 15 pages, links ok. Live writes
pend DATABASE_URL (empty) + the v1.10.x cron that calls it. Three clean no-secret code slices now
done (v1.1.6 dispatch, v1.0.4 schema/client, v1.8.7 store). **Remaining units genuinely need
secrets or bulk data to even verify:** geo chain (R2/TIGER), live joins (live APIs), v1.10.x
crons (deploy+Actions+Gmail), live bake + deploy + freshness (the ⚠️ BLOCKER — `.env` empty).

## RESUME  (iter 58)

iter 58: **built v1.0.4-datastore-wiring code slice.** Drizzle + Neon-http added; one table
`forecast_snapshots` (the V1 snapshot consumer), lazy client throwing on absent DATABASE_URL,
migration generated (`drizzle/0000_*.sql`) — verified without a DB. Gate: drizzle-kit generate
ok, astro check 0/0/0, vitest 35, build 15 pages, links ok. Live connect pends DATABASE_URL.
Next buildable-without-secrets slice unclear: v1.8.7 store logic needs a DB to test; geo chain
needs R2/TIGER; live joins need live data. Remaining units mostly need the empty secrets below.

## RESUME  (iter 57)

iter 57: **built the v1.1.6-artifact-bake code slice.** `cli.py` now has per-source dispatch
(`btb-etl bake <source>` / `bake all`) routing to each connector's `run()` via a flat
name→run registry; `sample`/`--dry-run` preserved. 6 new tests (`test_cli.py`) prove dispatch
without network (monkeypatched run callables); `bake fec` with no key fails cleanly on the
real env check. Gate: pytest 127, ruff clean. Live invocation pends the real secrets above
(`.env` empty) + network + deploy. Discovered the provisioning blocker (see ⚠️ above).

## RESUME  (historical — iter 54)

**Phase A (planning): COMPLETE** (P0–P14). **Phase B (build): all autonomously-buildable
units COMPLETE** — ~49 units green + 1 partial, merged to `dev`; `main` untouched throughout.
(iter 53 built `v1.6.6-chamber-view`, fixed stale `v1.9.5` row. iter 54 shipped the
source-honest slice of `v1.6.5-member-crosslink` — geographic member↔race links; its
finance-identity join is the only remaining non-deploy work and it needs the live
FEC↔bioguide crosswalk. **No remaining unit is buildable without provisioning.**)
iter 56: ran the Lighthouse gate locally for the first time — perf/a11y/best-practices/SEO
all ≥0.9 on the tested pages (incl. /chamber). The a11y/perf DoD bar is now evidenced, not
just asserted. Full 15-page Lighthouse + real-data freshness still pend deploy.

**iter 57+ — PROVISIONING DONE (human).** All accounts/secrets per `docs/SETUP_SECRETS.md`
are in (data.gov, Cloudflare Pages+R2, Neon, Gmail SMTP, GitHub Actions). The credential
wall is LIFTING. Resume driver added: `scripts/resume.sh` (verifies secrets → full gate →
`wrangler pages deploy apps/web/dist`, branch-guarded to dev, no main push). Cloudflare
Pages build config corrected (root dir = repo root, output = `apps/web/dist`, NODE_VERSION
20 — the "root directory not found" error was Root dir wrongly set to `apps/web/dist`).
**Next eligible units now unblocked, build order:** `v1.1.6-artifact-bake` (live per-source
dispatch — the CLI only bakes `sample` today; wire FEC/ACS/Congress/poll connectors into a
real bake) → `v1.0.4-datastore-wiring` (Neon+R2) → geo chain (`v1.1.2/1.3/1.4`, `v1.2.5`) →
live joins (`v1.3.2`, `v1.6.2/6.4`, `v1.6.5` finance) → `v1.8.7-snapshot-store` →
`v1.10.x` (deploy/QA/alerts/budget/weekly via Actions + Gmail).

Built (fixture-tested, locally-gated; 153 tests = 121 Python + 32 web, `astro check`
0/0/0): Phase-0 infra · 6 connectors (FEC/538/Census/Congress/Voteview/pollster-ratings)
· gerrymander metrics · full forecast engine (aggregation→baseline→race-model→Monte
Carlo→backtest→ML-challenger→runner) · data-prep transforms · the whole site (home, race
tracker index+detail with candidates/finance/polling/forecast/demographics/district-SVG,
forecast, member profiles, gerrymander, sources, Pagefind search, MDX articles, SEO) ·
README · CI gate.

**Everything NOT done is provisioning-gated (human-only):**
- Deploy + live preview (all pages) → Cloudflare Pages + `dev` push
- Live data in every figure → `api.data.gov` key, Neon, domain
- Interactive MapLibre map (`v1.2.4` shipped as SVG) → R2 PMTiles
- Find-my-district (`v1.2.5`) → live Census Geocoder
- Roll-call analytics (`v1.6.2/6.4/6.5`) → live Congress.gov (`6.6` chamber-view shipped)
- Nightly QA + alerts + budget alarms + weekly review (`v1.10.x`) → deploy + Gmail + Actions

**`V1 COMPLETE`** needs all the above live + the gate green at a real Cloudflare preview.
Until provisioning, the loop is at the credential wall `[S16a]` — hold + report; do not
emit the promise. See `docs/ACCOUNTS.md → Provisioning checklist`.

**Build conventions learned:** commit small units DIRECTLY to `dev` with a branch-guard
(`[ "$(git branch --show-current)" = dev ]`) — an external process switches HEAD→main on
`unit/*` creation (incidents iter 28, 32; details below). UI gate runs locally (build +
astro check + vitest + link check; CI runs Lighthouse/axe on push). Dispatch any cold
worker with `isolation: "worktree"`.

## Planning-doc units

| # | Unit (doc) | Prereq | Status |
|---|---|---|---|
| P0 | branch `planning/v1-docs` | — | done |
| P1 | `docs/phases/v1/PROGRESS.md` (this ledger) | P0 | done |
| P2 | `docs/01_PRODUCT_VISION.md` | P1 | done |
| P3 | `docs/02_ARCHITECTURE.md` | P2 | done |
| P4 | `docs/03_DATA_SOURCES.md` | P2 | done |
| P5 | `docs/04_DEFINITION_OF_DONE.md` | P2 | done |
| P6 | `docs/VERSIONING.md` | P2 | done |
| P7 | `docs/WORKFLOW.md` | P2 | done |
| P8 | `docs/adr/` (framework, datastore+tiering, no-PostGIS geo, forecast, email/alias, search/bloom, redistricting, loop-architecture) | P3 | done |
| P9 | `docs/phases/v1/PHASES_OVERVIEW.md` (the spine) | P3,P4,P5 | done |
| P10 | `docs/phases/v1/<segment>/PLAN.md` (per segment) | P9 | done (11 segments) |
| P11 | `docs/phases/v1/LOOP_PROMPT.md` (build loop + gate + token/session rules) | P9 | done |
| P12 | seed build-loop ledger rows (## Build ledger below) | P11 | done |
| P13 | `design-system/` seed + logo brief | P2 | done |
| P14 | `docs/ACCOUNTS.md` | P4 | done |

## Build ledger (Phase B — the units LOOP_PROMPT.md grinds)

Per-unit detail lives in the matching `<segment>/PLAN.md`; prereqs use the version slug.
Status of every unit is in the table below — the top `## RESUME` has the current summary.
Reference notes (UI-buildable, HEAD-switch incident) kept below for resumability.

### ✅ NOTE — UI units are buildable + gatable locally (not deploy-walled)
Earlier turns over-stated a "hard wall." Reality: every UI unit's gate runs **locally**:
`pnpm build` → `astro check` → vitest → **axe via Playwright** → **Lighthouse ≥90 via
`@lhci/cli` with `staticDistDir: apps/web/dist`** (no live server) → responsive
screenshots 360/768/1280 via Playwright. Pages consume **fixture/sample gold artifacts**
(write a small `data/gold/<source>/<source>.json` fixture, or run a connector with the
fixture transport). Only the literal *deployed Cloudflare URL* + *real-data freshness*
need provisioning — everything else (the actual pages + local gate) is doable now.

**NEXT PHASE = UI**, start at the tracker. Recipe per UI unit:
1. Ensure/generate the gold-artifact fixture(s) the page reads.
2. Build the Astro page + React island(s) (charts: Observable Plot; party colors from
   design tokens; islands lazy-hydrated).
3. Add a Vitest/Playwright test + an axe a11y check.
4. Local gate: build, astro check, vitest, axe, `pnpm dlx @lhci/cli autorun
   --config apps/web/lighthouserc.json`, screenshots. (Add @playwright/test +
   @axe-core/playwright devDeps; `pnpm exec playwright install chromium`.)
5. Commit DIRECTLY to `dev` with a branch-guard (`[ "$(git branch --show-current)" =
   dev ]`) — do NOT use `unit/*` branches (HEAD-switch interference, below). Or dispatch
   a worker with `isolation: "worktree"`.
Build order: v1.2.3-race-page (core) → v1.2.4 map island → v1.2.6 race-index →
finance/polling UI on race page (v1.3.4, v1.4.4) → v1.6.1 member-profiles → v1.8.6
forecast-ui → v1.7.3 gerrymander-ui → demographics UI → v1.9.x SEO/search → v1.10.x
(QA/alerts need accounts). Heavy units → fresh re-feed or isolated worker (context).

### ⚠️ RECURRING: external process switches HEAD→main after `git switch -c unit/*` (iters 28, 32)
Happens even with NO worker running (iter 32, in-thread build) — something external/
concurrent checks out `main` right after a unit-branch create. **Mitigation: commit small
units DIRECTLY to `dev`** (verify `git branch --show-current`==dev immediately before the
commit) instead of the unit-branch→merge dance, which keeps getting interrupted. `main`
stays untouched regardless. Always preserve uncommitted files to scratchpad first; recover
with `git switch --discard-changes dev`. Root cause still unknown (possibly the ralph/loop
harness or a concurrent session). All commits remain safe in git.

### ⚠️ INCIDENT (iter 28) + FIX — worker switched HEAD to main
A dispatched cold worker ran a `git` command that switched HEAD `unit/v1.8.4-backtest →
main`, leaving dev's files untracked + pyproject.toml missing from the working tree. **No
data lost** (all commits intact; recovered via `git switch --discard-changes dev`, 2
uncommitted backtest files preserved to scratchpad first). **FIX: dispatch all future
cold workers with `isolation: "worktree"`** so they operate in an isolated git worktree
and can never touch the main repo's HEAD/branch. Workers are also told "do NOT run git"
but isolation is the real guardrail. Verify branch (`git branch --show-current`) after
any worker returns before gating.

Status per unit is below; current summary is the top `## RESUME`. `pending` rows are all
provisioning-gated (live data / deploy / R2 / Gmail) — see `ACCOUNTS.md`. `dev` integrates
all `done` units; `main` untouched `[S5a]`.

| Unit | Prereq | Status |
|---|---|---|
| v1.0.1-repo-scaffold | — | done |
| v1.0.2-ci-gate | v1.0.1 | done |
| v1.0.3-config-schema | v1.0.1 | done |
| v1.0.4-datastore-wiring | v1.0.1 | done + LIVE (iter 66: migration applied to Neon by human; table verified on live DB) |
| v1.0.5-etl-skeleton | v1.0.1 | done |
| v1.0.6-data-integrity-check | v1.0.5 | done |
| v1.0.7-design-tokens | v1.0.1 | done |
| v1.0.8-base-layout-seo | v1.0.1, v1.0.7 | done |
| v1.1.1-etl-framework | v1.0.5 | done |
| v1.1.2-geo-tiles | v1.0.4 | pending |
| v1.1.3-district-equivalency | v1.1.2 | pending |
| v1.1.4-geocoder | v1.1.1 | pending |
| v1.1.5-member-roster | v1.1.1 | done (code; keyless) |
| v1.1.6-artifact-bake | v1.1.1 | done (per-source dispatch CLI + tests; live fetch pends real DATA_GOV_API_KEY/network + deploy) |
| v1.2.1-race-config | v1.0.3 | done (schema + 2 validated race configs) |
| v1.2.2-candidate-roster | v1.1.5 | partial: config-embedded candidates; live FEC/Congress roster join pends data |
| v1.2.3-race-page | v1.2.1, v1.2.2 | done (local gate; CI lhci/axe on push) |
| v1.2.4-district-map-island | v1.1.2 | done as SVG (0-JS); MapLibre+PMTiles pends R2 |
| v1.2.5-find-my-district | v1.1.4 | pending |
| v1.2.6-race-index | v1.2.3 | done (local gate; CI lhci/axe on push) |
| v1.3.1-fec-connector | v1.1.1 | done + LIVE (iter 61: real bake, 200 rows via DATA_GOV_API_KEY) |
| v1.3.2-candidate-committee-link | v1.3.1 | done + LIVE (iter 64: principal-cmte linkage via OpenFEC, real links verified) |
| v1.3.3-finance-aggregates | v1.3.2 | done (math; committed direct to dev) |
| v1.3.4-finance-ui | v1.3.3, v1.2.3 | done (local gate; sample artifact; live FEC pends key) |
| v1.4.1-poll-connector | v1.1.1 | done (code); SOURCE DEFERRED to V1.1 — 538 dead, no clean open feed (iter 66, BACKLOG) |
| v1.4.2-pollster-ratings | v1.4.1 | done (code); SOURCE DEFERRED to V1.1 (same) |
| v1.4.3-aggregation | v1.4.2 | done (math); no live polls in V1 (deferred) |
| v1.4.4-polling-ui | v1.4.3, v1.2.3 | done (UI hides when empty — graceful no-polling in V1) |
| v1.5.1-acs-connector | v1.1.1 | done + LIVE (iter 66: 440 rows via CENSUS_API_KEY; +clean missing-key guard) |
| v1.5.2-district-aggregates | v1.5.1, v1.1.3 | done (math; direct to dev) |
| v1.5.3-urbanization | v1.5.2 | done (math; direct to dev) |
| v1.5.4-demographics-ui | v1.5.2, v1.2.3 | done (local gate; sample artifact) |
| v1.6.1-member-profiles | v1.1.5 | done (local gate; +v1.6.3 ideology shown) |
| v1.6.2-rollcall-votes | v1.6.1 | partial + LIVE (iter 63: House roll-call list via Congress.gov, 477 real rows; Senate/GovTrack + per-member positions follow-up) |
| v1.6.3-ideology | v1.6.1 | done (code; keyless) |
| v1.6.4-sponsorship-bipartisanship | v1.6.2 | partial + LIVE (iter 65: sponsored/cosponsored counts via Congress.gov, real; cross-party index [M7a] follow-up) |
| v1.6.5-member-crosslink | v1.6.1, v1.3.3 | partial: geographic member↔race links (local gate); finance-identity join pends FEC↔bioguide crosswalk (live data) |
| v1.6.6-chamber-view | v1.6.1 | done (local gate; composition + Class II 2026) |
| v1.7.1-compactness-metrics | v1.1.2 | done (math; TIGER read+bake pends geo data) |
| v1.7.2-fairness-metrics | v1.7.1 | done (math; live results join pends data) |
| v1.7.3-gerrymander-ui | v1.7.1, v1.7.2 | done (local gate) |
| v1.7.4-leaderboard | v1.7.1 | done (on gerrymander page) |
| v1.7.5-methodology-page | v1.7.2 | done (methodology section) |
| v1.8.1-baseline-fundamentals | v1.5.2 | done (math; live inputs pend data) |
| v1.8.2-race-model | v1.8.1, v1.4.3, v1.3.3 | done (math; live inputs pend data) |
| v1.8.3-montecarlo-chamber | v1.8.2 | done (math; race-prob inputs from fixtures) |
| v1.8.4-backtest-calibration | v1.8.2 | done (math; live backtest data pends) |
| v1.8.5-ml-challenger | v1.8.4 | done (math; real backtest decision pends live data) |
| v1.8.6-forecast-ui | v1.8.3 | done (runner + per-race + chamber /forecast; local gate) |
| v1.8.7-snapshot-store | v1.8.3 | done (write/read store, pglite-tested; live schema applied to Neon iter 66; live writes pend the v1.10.x cron) |
| v1.9.1-search | phases 2–8 | done (Pagefind static index; local gate) |
| v1.9.2-sitemap-jsonld | phases 2–8 | done (sitemap+robots+WebSite+OG+per-type Person) |
| v1.9.3-articles-mdx | v1.0.8 | done (local gate) |
| v1.9.4-sources-page | — | done (local gate) |
| v1.9.5-home-nav | v1.9.1 | done (local gate; built iter 46) |
| v1.10.1-coverage-configs | phases 2–8 | pending |
| v1.10.2-nightly-qa | v1.10.1 | done (refresh.yml: nightly bake→export→commit→auto-deploy; cmds live-verified locally w/ real keys iter 70. QA-screenshot sweep folds into v1.10.3) |
| v1.10.3-regression-alerts | v1.10.2 | pending |
| v1.10.4-budget-alarms | v1.10.2 | pending |
| v1.10.5-weekly-review-routine | v1.10.2 | pending |

## Activity log

- P0–P2: branched, seeded ledger, wrote Product Vision (cited to answers). — iter 1
- P4: 03_DATA_SOURCES.md — master source table (FEC/538/Census/Congress.gov/
  Voteview/congress-legislators/TIGER/Geocoder), keys, cadence, freshness floors,
  pipeline contract. Flagged RCP/Wikipedia licensing as open Qs. — iter 2
- P5–P7: DEFINITION_OF_DONE (10-point gate + evidence), VERSIONING
  (v[phase].[segment].[task]), WORKFLOW (main-wall branch ritual, QA cadence).
  Corrected outbound email to Gmail SMTP [S9c/T4b], not Resend. — iter 2
- P8: 8 ADRs + index (framework, datastore-tiering, geo-no-postgis, forecast,
  email-alias, search, redistricting-versioning, loop-architecture). — iter 3
- P9: PHASES_OVERVIEW — 11 phases (0 bootstrap → 1 data foundation → 2–7 module
  slices → 8 forecast → 9 SEO/search → 10 loop-scale), scope in/out, why-order,
  locked decisions, cross-cutting AC, Phase-0 contents. — iter 4
- P10 (part): PLAN.md for phases 0 bootstrap, 1 data-foundation, 2 tracker,
  3 finance, 4 polling — each with acceptance criteria + unit table. — iter 5
- P10 (rest): PLAN.md for phases 5 demographics, 6 members/chamber, 7
  gerrymander-lite, 8 forecast, 9 SEO/search, 10 loop-scale. All 11 done. — iter 6
- P11–P12: LOOP_PROMPT.md (self-contained build contract: Step 0, loop, gate,
  main-wall, token/session sleep rules, completion) + seeded 60-unit build ledger
  above (v1.0.1–v1.10.5) with prereq DAG. — iter 7
- **Phase B start** v1.0.1-repo-scaffold: pnpm monorepo (apps/web Astro 5 + React
  islands + Tailwind v4 + TS strict + shadcn-ready cn util) + Python pipeline (uv).
  Gate: pnpm build green, astro check 0/0/0, static index ships 0 JS. Branch
  unit/v1.0.1 → merged dev. main untouched. Env note: PRs merged locally (no
  remote); gh-PR flow applies once a remote exists. — iter 9
- v1.0.2-ci-gate: .github/workflows/gate.yml (build-test, lighthouse-a11y LHCI
  >=0.9 mobile, pipeline-lint ruff), Dependabot, lighthouserc, scripts/check-links.mjs.
  Actions SHA-pinned. Local gate green (check 0/0/0, vitest 2/2, build, links).
  CI Lighthouse/uv run on GitHub once a remote exists. → merged dev. — iter 10
- v1.0.3-config-schema: zod UnitConfig discriminated union (race kind), cross-field
  rules, SourceBinding for integrity check, example OH-senate JSON, 4 schema tests.
  Gate: check 0/0/0, vitest 6/6, build, links. → merged dev. — iter 11
- v1.0.5-etl-skeleton: pipeline core.py (SourceSpec, validate_records, is_fresh,
  dry_run, bake gold+manifest) + sample source + CLI; hatchling build-system,
  uv.lock. Gate: pytest 4/4, ruff clean, dry-run+bake verified. → dev. — iter 12
- v1.0.7-design-tokens: Tailwind v4 @theme — party blue/red/purple [C5a], civic
  neutrals w/ dark override [C4a,C6a], sans+serif, reduced-motion. Tokens verified
  compiled into output CSS; index showcases swatches. Gate green. → dev. — iter 13
- v1.0.6-data-integrity-check: pipeline/integrity.py — source registry (10 rows)
  with check_doc_sync vs DATA_SOURCES.md [R14a] + assert_artifact freshness [R5a] +
  scan_gold; wired into CI. Gate: pytest 10/10, ruff, CLI green. → dev. — iter 14
- v1.0.8-base-layout-seo: Layout.astro (skip-link, nav, footer), @astrojs/sitemap,
  robots.txt, WebSite JSON-LD, canonical/OG meta, CF Pages _headers (CSP/HSTS),
  section stubs. Gate: check 0/0/0, 5 pages+sitemap, links ok, 0 JS. → dev. — iter 15
  **Phase 0 code-only units complete; remainder is account-gated (credential wall).**
- v1.1.1-etl-framework: connector.py — backoff_retry [T8a], upsert by natural key
  [R4a], CachingFetcher (conditional GET + 304 + transport-failure last-good)
  [R10a,R8a], transport injected for full fixture testing. pytest 17/17, ruff.
  → dev. **Credential wall reached — autonomous loop paused (see RESUME).** — iter 16
- iter 16: user chose "provision accounts" → wrote ACCOUNTS provisioning checklist,
  pivoted loop to env-keyed fixture-tested connectors.
- v1.3.1-fec-connector: OpenFEC totals connector (env key, FecTotals model, upsert,
  bake integrity-clean), 5 fixture tests, no live calls. pytest 22/22, ruff. Code
  done; live run pends DATA_GOV_API_KEY. → dev. — iter 17
- v1.4.1-poll-connector: 538 CSV connector (keyless), PollRow validation, composite-key
  upsert, last-good, bake (polls_538, 3d floor). 3 fixture tests. pytest 25/25, ruff.
  → dev. — iter 18
- v1.1.5-member-roster: congress-legislators JSON connector (keyless), MemberRow from
  current term, upsert by bioguide_id, bake (members, 14d). 2 fixture tests. pytest
  27/27, ruff. → dev. — iter 19. (Honoring new ~90% context rule: ending turn here,
  future connector units to be dispatched to cold sub-agents.)
- v1.5.1-acs-connector: Census ACS5 connector (env-keyed) — header-array parse, AcsRow
  (geoid/pop/median_income, -666666666→None), upsert by geoid, bake (census_acs, 400d).
  **Built by a cold worker, orchestrator-gated** (pytest 32/32, ruff). → dev. — iter 20
- v1.6.3-ideology: Voteview DW-NOMINATE connector (keyless), IdeologyRow, most-recent-
  congress dedupe by bioguide_id, bake (voteview, event-driven floor). Cold worker,
  orchestrator-gated. pytest 36/36, ruff. → dev. — iter 21
- v1.7.1-compactness-metrics: geometry.py — Polsby-Popper/Reock/convex-hull via shapely
  + compute_metrics; fixture-tested vs known shapes (unit square pp≈0.785). shapely dep
  added. Cold worker, orchestrator-gated. pytest 43/43, ruff. → dev. — iter 22
- v1.7.2-fairness-metrics: fairness.py — efficiency gap, mean-median, seats-votes,
  compute_fairness report; two-party caveat [L8a]. Cold worker, orchestrator-gated
  (hand-computed expectations verified). pytest 51/51, ruff. → dev. — iter 23
- v1.4.2-pollster-ratings: 538 ratings connector (keyless), RatingRow, column-variant
  robust (numeric_grade→pollscore fallback), upsert by pollster, bake (pollster_ratings,
  30d). Cold worker self-corrected a test to match the spec'd fallback; orchestrator-
  gated. pytest 57 passed, ruff. → dev. — iter 24
- v1.4.3-aggregation: aggregate.py — recency (30d half-life) × pollster weighted mean
  per (state,party), AggregateRow; published heuristic. Cold worker, orchestrator-gated
  (arithmetic verified 46.67/47.5). pytest 66/66, ruff. → dev. — iter 25
- v1.8.3-montecarlo-chamber: montecarlo.py — numpy-vectorized seat sim, shared national
  swing on logit scale [N6a], seeded [N13a]; seat dist + control prob + p10/50/90. numpy
  dep. Cold worker, orchestrator-gated. pytest 74 passed, ruff. → dev. — iter 26
- v1.8.1-baseline-fundamentals: baseline.py — cook_pvi signed lean + BaselineRow
  fundamentals feature layer (pvi/incumbent/open_seat/finance_net). Cold worker,
  orchestrator-gated. pytest 79, ruff. → dev. — iter 27
- v1.8.2-race-model: race_model.py — office-weighted blend of poll + fundamentals
  margins → win_prob/margin/range (stdlib erf), predict_races feeds the MC sim
  (end-to-end forecast integration tested). Forecast engine chain complete: baseline →
  race-model → montecarlo. Cold worker, orchestrator-gated. pytest 92, ruff. — iter 28
- v1.8.4-backtest-calibration: backtest.py — Brier/log-loss/ECE/accuracy + is_calibrated
  gate helper [N9a]. Worker incident (switched HEAD→main) recovered, no data lost; files
  preserved + re-gated full suite. pytest 104, ruff. → dev. Future workers use
  isolation:worktree. — iter 29
- v1.8.5-ml-challenger: numpy logistic regression + choose_model (adopt ML only if it
  beats heuristic Brier on same holdout [N8a]). Built in-thread (post-incident, no
  worker). pytest 110, ruff. → dev. **Forecast module pure-math complete.** — iter 30
- v1.8.6 (runner): forecast.py run_forecast composes race_model → win-probs →
  montecarlo into one reproducible bundle [N1a]. In-thread. pytest 113, ruff. → dev.
  Forecast UI pends deploy. — iter 31
- v1.3.3-finance-aggregates: build_finance (FEC↔candidate-meta join, burn_rate,
  coverage_end_date) + rollup_by_race. Direct to dev (HEAD-switch workaround). pytest
  115. — iter 32
- v1.5.2-district-aggregates: demographics.py — build_district_demographics (tags
  geometry_as_of [L547]) + rollup_by_state (pop-weighted income). Direct to dev. pytest
  118, ruff. — iter 33
- v1.5.3-urbanization: urbanization.py — classify districts urban/suburban/rural by
  Census urbanized-area share. Direct to dev. pytest 121, ruff. — iter 34.
  **All pure-compute + data-prep V1 units now done; remainder is UI/deploy/QA only.**
- **UI phase start** v1.2.3-race-page: config-driven SSG race detail pages
  (src/pages/races/[id].astro via getStaticPaths over race configs), candidates with
  colorblind-safe party tokens + incumbent badge + status; races.ts loader/validator;
  2 sample races (OH-Sen, PA-05). v1.2.1 config done. Local gate: check 0/0/0, vitest
  9/9, build 7 pages, links ok, 0 JS. CI lhci/axe runs on push. Direct to dev. — iter 35
- v1.2.6-race-index: real /races index (grouped by office, party-dot chips, status,
  links to detail) replacing the stub. Local gate: check 0/0/0, build, links ok,
  tests 9/9. Direct to dev. — iter 36
- v1.3.4-finance-ui: finance section on race detail (accessible CSS bars, receipts +
  cash-on-hand, "through <coverage_end_date>" + FEC source link [G13a]); finance.ts
  loader + fmtUSD; sample OH artifact; candidates linked by fecCandidateId. Local gate:
  check 0/0/0, build, links, 0 JS, tests 12/12. Live FEC pends key. dev. — iter 37
- v1.4.4-polling-ui: polling-average section on race detail (per-party 0-JS bars, as_of,
  538 source); polling.ts loader; sample OH artifact. Trend sparkline (needs snapshot
  history) deferred. Local gate: check 0/0/0, build, links, 0 JS, tests 14/14. — iter 38
- v1.8.6 (per-race UI): forecast section on race detail (Dem win prob %, predicted
  margin + 80% range, methodology link); forecast.ts loader + marginLabel; sample OH
  artifact. Race detail now has candidates+finance+polling+forecast. Local gate: check
  0/0/0, build, links, 0 JS, tests 17/17. Chamber /forecast page next. — iter 39
- v1.8.6 (chamber): real /forecast page — Dem control prob, expected seats, p10–p90
  range per chamber (sample Senate); methodology/sources notes. allChamberForecasts
  loader. v1.8.6 now fully done. Local gate: check 0/0/0, build, links, 0 JS, tests
  18/18. — iter 40
- v1.6.1-member-profiles: members/[id] profile pages (party, chamber, seat, DW-NOMINATE
  ideology w/ plain-language band + Voteview source) + real /members index (by chamber);
  members.ts loader + ideologyLabel. Sample roster (3). Local gate: check 0/0/0, build
  10 pages, links, 0 JS, tests 21/21. — iter 41
- v1.7.3+7.4+7.5-gerrymander: /gerrymander page — per-state fairness (efficiency gap+
  mean-median, caveated [L8a]), least-compact leaderboard, methodology; gerrymander.ts
  loader; nav link "Maps". Local gate: check 0/0/0, 11 pages, links, 0 JS, tests 24/24.
  — iter 42
- v1.5.4-demographics-ui: demographics panel on race detail (population, median income,
  urbanization, ACS release + Census source); demographics.ts loader. Local gate: check
  0/0/0, 11 pages, links, 0 JS, tests 27/27. — iter 43
- v1.9.4-sources-page: real /sources renders the DATA_SOURCES contract table (9 sources:
  provider/license/cadence/freshness-floor/modules) [R14a]; sources.ts. Local gate: check
  0/0/0, 11 pages, links, 0 JS, tests 29/29. — iter 44
- v1.9.1-search: Pagefind static search [L891] — build runs `pagefind --site dist`,
  /search page mounts PagefindUI (the one interactive island); main tagged
  data-pagefind-body, nav "Search" link. Local gate: check 0/0/0, links ok (/pagefind/*
  resolve), tests 29/29. ponytail: pagefind-ui works; Component UI is the upgrade path.
  — iter 45
- v1.9.5-home-nav: real landing — value prop, CTA buttons (dynamic race count +
  Senate-control headline from forecast), section cards to all modules. Local gate:
  check 0/0/0, 12 pages, links, 0 JS. — iter 46
- v1.9.3-articles-mdx: MDX article pipeline — content collection (zod frontmatter) +
  /articles index + /articles/[slug]; sample explainer; /mdx; "Articles" nav.
  Local gate: check 0/0/0, 14 pages, links, 0 JS. — iter 47
- v1.9.2-sitemap-jsonld: per-type JSON-LD — Layout `schema` prop; member profiles emit
  a Person schema (sitemap/robots/WebSite/OG already done). Local gate: check 0/0/0, 14
  pages, links. SEO/content phase (v1.9.x) complete. — iter 48
- v1.2.4 (district shape): inline-SVG district boundary on house race pages (0-JS,
  TIGER source, as_of); geo.ts ringToSvg projector. MapLibre+PMTiles interactive map
  [P8a] deferred until R2 hosting. Local gate: check 0/0/0, 14 pages, links, 0 JS, tests
  32/32. — iter 49
- Repo README.md (overview, layout, develop commands, forecast methodology,
  neutrality) + full-suite verification snapshot: 153 tests green (121 py + 32 web),
  astro check 0/0/0, 14 pages, links ok. — iter 51
- v1.6.6-chamber-view: /chamber page — per-chamber party composition bars computed from
  the roster + the 33 Class II 2026 Senate seats (static rota constant); nav "Chamber".
  Fixed a sort bug (`"DR".indexOf` returned -1 for I, sorting it first → ranked D/R/other).
  Also corrected stale ledger row v1.9.5-home-nav (shipped iter 46). Local gate: check
  0/0/0, vitest 34/34, build 15 pages, links ok, 0 JS. Direct to dev. — iter 53
- iter 56: **first real Lighthouse run** (`pnpm dlx @lhci/cli autorun --config
  apps/web/lighthouserc.json`, static `dist`, no live server). All four categories
  (perf/a11y/best-practices/SEO) **≥0.9** — `All results processed!`, exit 0. lhci
  default-caps auto-globbed URLs at 5, so it covered the distinct page types (home,
  articles index, article detail, /chamber, forecast); full-page sweep runs at deploy CI.
  This is the a11y/perf gate confirmed for the first time (was only ever CI-on-push, which
  never ran without a remote). No code change; verification only.
- v1.6.5-member-crosslink (partial): geographic member↔race crosslink — `membersForRace`
  joins on state/district; member profile lists 2026 races in their state, race page lists
  current officeholders for the seat. Finance-identity link (per-candidate $) still pends
  the live FEC↔bioguide crosswalk — not faked in fixtures (source-traceability gate).
  Local gate: check 0/0/0, vitest 35/35, build 15 pages, links ok, 0 JS. Direct to dev.
  — iter 54
- v1.1.6-artifact-bake (code slice): per-source dispatch CLI — `bake <source>`/`bake all`
  over a name→run registry (fec/members/acs/polls/pollster_ratings/voteview), sample+dry-run
  kept. test_cli.py (6) proves routing without network; `bake fec` errors cleanly on absent
  key. Discovered `.env` is an empty template → provisioning NOT actually done (see ⚠️ BLOCKER).
  Gate: pytest 127, ruff clean. Direct to dev. — iter 57
- v1.0.4-datastore-wiring (code slice): Drizzle + @neondatabase/serverless added [ADR 0002].
  `src/lib/db/schema.ts` — one table `forecast_snapshots` (cycle-partitioned append-only run
  history, the V1 snapshot-store consumer [v1.8.7]); skipped feed/search tables (no V1 writer;
  Pagefind does search staticly). `src/lib/db/client.ts` — lazy Neon-http drizzle client,
  throws on absent DATABASE_URL (hot path reads baked JSON, never the DB). `drizzle.config.ts`
  + generated migration `drizzle/0000_*.sql` (the no-DB verifiable check). `db:generate`/
  `db:migrate` scripts. Gate: drizzle-kit generate ok, astro check 0/0/0, vitest 35, build 15
  pages, links ok. Live connect/migrate pends DATABASE_URL (still empty — see ⚠️ BLOCKER).
  Direct to dev. — iter 58
- iter 60: first **real live bakes** via v1.1.6 dispatch (keyless, network only): members
  537 rows, voteview 12,584 rows (real + fresh). polls/pollster_ratings 0 rows → confirmed
  **538 CSV endpoints dead** (ABC HTML shell at both /polls/data and /polls-page/data paths).
  Logged Open question #1 (replacement polling source = human decision) + marked the two rows
  DEAD in DATA_SOURCES.md. Secrets now 5/7 (CLOUDFLARE_ACCOUNT_ID, SMTP_PASS still empty).
  Docs-only; no code change. Direct to dev.
- iter 61: **FEC live-bake proven** (200 real rows; DATA_GOV_API_KEY is genuine — iter-60
  placeholder worry was a probe bug measuring var-NAME lengths). **ACS fix:** connector reads
  `CENSUS_API_KEY` (api.census.gov rejects the data.gov key → 302 missing_key.html) with a clear
  error on the HTML page instead of JSONDecodeError; +1 test (128 pytest, ruff clean).
  SETUP_SECRETS corrected (data.gov key ≠ Census key); `CENSUS_API_KEY=` added to local .env.
  Direct to dev.
- v1.6.2-rollcall-votes (House slice): `sources/rollcall.py` — Congress.gov House roll-call
  list connector (data.gov key authenticates Congress.gov, verified live), CLI-registered, 5
  fixture tests. Live bake = 477 real rows. Senate + per-member positions deferred. pytest 133,
  ruff clean. Found CENSUS_API_KEY invalid (placeholder). Direct to dev. — iter 63
- v1.3.2-candidate-committee-link: `sources/committee_link.py` — OpenFEC principal-committee
  linkage [G12a], CLI-registered, integrity row added (doc-sync ok), 5 tests. Live: 3/4 real
  candidates → real principal committee IDs. pytest 138, ruff clean. Direct to dev. — iter 64
- v1.6.4-sponsorship-bipartisanship (counts slice): `sources/sponsorship.py` — sponsored/
  cosponsored totals via Congress.gov pagination.count, CLI-registered, DATA_SOURCES + integrity
  rows added (doc-sync ok), 3 tests. Live: Pelosi 199/5083, Sanders 1180/7896. Cross-party index
  deferred. pytest 141, ruff clean. Direct to dev. — iter 65
- iter 66: human fixed all secrets + ran prod `db:migrate` (Neon table verified live). ACS live
  = 440 rows (valid Census key). **Polling dropped from V1** (no clean open feed post-538;
  forecast/UI already degrade gracefully) → `docs/BACKLOG.md` for V1.1. Docs-only commit
  (decision + ledger); connectors/forecast/UI unchanged. Direct to dev.
- iter 67: **live joins — members.** `export_web.py` exports gold → committed `src/data/*`;
  `roster.json` = 537 real members (members ⋈ voteview), build emits 537 real profile pages.
  Member tests made data-agnostic. pytest 143, vitest 37, build+links green. Direct to dev. — iter 67
- iter 68: **live joins — demographics.** `export_demographics` gold/census_acs → per-race JSON
  (state rollup / district); real OH+PA-05 figures; urbanization optional (null, UI hides).
  2 tests data-agnostic. pytest 144, vitest 37, build+links green. Direct to dev. — iter 68
- iter 69: **real Senate race set + finance live-join.** `generate_races.py` → 33 Class-II 2026
  Senate configs from FEC (real candidates) + 141 baked finance rows; `export_finance` → per-race
  real finance. Removed 2 sample races + orphans. 6 sample-coupled tests fixed. pytest 147, vitest
  35, build 33 race pages, links ok. v1.3.2 finance now LIVE on the tracker. Direct to dev. — iter 69
- iter 74: **live-preview sweep CLOSED green.** Lighthouse at the live Cloudflare URL, 5 page
  types, all categories ≥90 (perf 100, a11y 95–100, bp 96, seo 100), 0 failures. + headers + canary
  → completion gate #2 met. Verification only (no code). Ledger updated. — iter 74
- iter 73: **integrity — removed fabricated forecast.** `/forecast` was showing sample
  chamber-senate.json as a real result; deleted it → honest "not yet published" empty state (home
  headline already guarded). forecast.test.ts made data-agnostic. astro 0/0/0, vitest 35, build,
  links; built page has 0 fake figures. No fabricated data anywhere on the live site now. Real
  forecast pends Open Q#3 PVI source. Direct to dev. — iter 73
- iter 72: **redirect fix verified live + canary.** 9 routes confirmed 200 (no 307) post-redeploy.
  Added `scripts/canary.mjs` + `canary.yml` (scheduled live-health check: routes 200 + security
  headers; red job → GitHub native email, no SMTP). Canary ok locally. Direct to dev. — iter 72
- iter 71: **live-preview sweep — fixed 307 nav redirect.** Live Worker security headers all
  present (CSP/HSTS/etc., `_headers` honored). Found `/races` etc. 307→`/races/` (directory output
  vs slashless links + default `auto-trailing-slash`). Fix: `wrangler.jsonc` `html_handling:
  drop-trailing-slash`. No build/test impact. Direct to dev. — iter 71
- iter 70: **v1.10.2 nightly refresh Action.** `.github/workflows/refresh.yml` re-bakes the 4
  consumed sources (members/voteview/acs/fec, not `bake all` — quota [S6a]), re-exports
  `src/data/*`, commits any change to `dev` → Workers Build auto-deploys. Commands live-verified
  locally with real keys (1 roster + 33 demographics + 33 finance; deterministic, no diff →
  freshness already met). pytest 147, ruff, yaml valid. Open Q#3 logged (forecast PVI source).
  Direct to dev. — iter 70
- P13–P14: design-system seed (neutral civic chrome + colorblind-safe party viz
  palette, type, motion-with-reduced-motion, components) + LOGO_BRIEF; ACCOUNTS
  (services/aliases/free-limits/80% alarms, no secrets). **Phase A complete.** — iter 8
