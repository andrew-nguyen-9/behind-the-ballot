# Election-results go-live runbook

How to take the results module from **honest-empty scaffolding** (its committed state) to
**live vote totals** for a primary or general election night, and later to **certified**
numbers. The connector, display, exporter, and schema already ship and are election-type
generic [E3.2, E3.3]; going live is data + config, not new code.

- Connector: `pipeline/btb_pipeline/sources/primary_results.py`
- Exporter: `export_results` in `pipeline/btb_pipeline/export_web.py` → `apps/web/src/data/results/<raceId>.json`
- Display: Results section in `apps/web/src/pages/races/[id].astro` (reads `apps/web/src/lib/results.ts`)
- Sample record shape: `apps/web/src/lib/__fixtures__/generalResults.sample.json`

The default build has **no** `apps/web/src/data/results/*.json` files, so every race page shows
its honest "No results yet" state. Real numbers appear only once a real feed reports —
never fabricate committed totals.

## 1. Before the night — validate adapters

For each competitive-race state:

1. Add / confirm a `StateAdapter` entry in the correct registry:
   - `STATE_ADAPTERS` for a primary, `GENERAL_ADAPTERS` for the general.
   - Point it at the state's live feed URL and a parser. Reuse `parse_json_contests` /
     `parse_csv_contests` where the shape fits; otherwise add one small parser (the only
     per-state code). Adding a state = one dict entry.
2. Validate the adapter against the state's **pre-published test feed** with an injected
   transport (see `pipeline/tests/test_primary_results.py`) — confirm `office`/`district`
   map to our race ids (`us-{office}-2026-{ST}[-DD]`), that `pct`/`pct_reporting` derive
   correctly, and that every row validates against `ResultRow`.

> **AZ (schedule armed, live fetch not built).** `STATE_ADAPTERS["AZ"]` (Clarity ENR),
> county aggregation, the `export_county_results` exporter, the `/results` display, and the
> armed `results.yml` schedule all ship DoD-green — but only against a reconstructed fixture.
> The live fetch is **unbuilt**: the AZ `feed_url` is the bare Clarity host, so a real bake
> still needs (a) `current_ver.txt` resolution, (b) `detailxml.zip` download + unzip, (c)
> statewide-vs-15-county fan-out, then (d) re-validation against real 2026 bytes (the sandbox
> hit Cloudflare-403 on the live CDN, so the fixture is reconstructed to the E-R0 schema).
> Until that lands the parser fails closed on non-XML and the scheduled workflow yields
> honest-empty — no bad data, but no live totals. Feed pattern, contest-mapping quirks, and
> parser gotchas: `docs/research/AZ_RESULTS_SOURCES.md`.

## 2. Go live (election night)

1. **Flip the switches** in `primary_results.py`:
   - `ACTIVE_STATES = ["OH", ...]` — the validated states to ingest.
   - `ACTIVE_ELECTION_TYPE = "primary"` **or** `"general"` — which adapter set the
     scheduled bake uses. (One switch; the CLI command below never changes.)
2. **Schedule the bake** at the polls-close cadence (1–5 min during the count, then hourly
   for days as mail/late ballots land):

   ```
   uv run --project pipeline python -m btb_pipeline.cli bake primary_results
   uv run --project pipeline python -m btb_pipeline.export_web   # -> src/data/results/*.json
   ```

   Each pull upserts by `(race_id, candidate)` [R4a] so re-runs only move totals, never
   truncate; the caching fetcher keeps last-good if a feed dies under load [R8a].
3. **Race calls (optional):** pass a `calls` map to `run()` (from the tiny Wikipedia layer)
   to stamp `is_called` / `called_by`. SoS feeds carry no projection; a call is always the
   attributed Wikipedia (CC BY-SA) signal.
4. **Verify** each pull: `uv run --project pipeline python -m btb_pipeline.integrity`
   (exit 0), then rebuild the web app and confirm race pages show live totals with the
   "Unofficial — provisional" banner, precincts-reporting line, and as-of stamp.

Every published figure is provisional and labeled as such until certification.

## 3. Certified backfill (one-shot, weeks/months later)

When MIT Election Lab (MEDSL, CC BY) publishes certified totals, run the manual one-shot —
it is **not** a scheduled source:

```
uv run --project pipeline python -c \
  "from btb_pipeline.sources import primary_results as pr; pr.certify(open('medsl_2026.csv').read())"
uv run --project pipeline python -m btb_pipeline.export_web
```

`certify()` normalizes the certified totals with `is_certified=True` and upserts them over
the provisional gold by `(race_id, candidate)` — superseding provisional numbers, carrying
forward any race-call attribution, and flipping each page from "Unofficial — provisional"
to "Certified". Expected MEDSL CSV columns: `state, office, district, candidate, party,
votes` (office normalized to `senate|house|governor`).

## 4. Stand down

Leave the certified numbers in place. To return a race to honest-empty (e.g. bad data),
delete its `apps/web/src/data/results/<raceId>.json` and rebuild — the page reverts to
"No results yet".

## Notes / gotchas

- **Fixture vs live feed:** the sample fixture is the *record* shape (post-export). A live
  SoS feed is the *raw* shape a `StateAdapter.parse` must convert to `Contest`s. Validate
  the parser against real feed bytes, not the fixture.
- **Honest by construction:** missing precinct counts → `pct_reporting = null` → "not
  reported"; a race with no reported candidates → no file → "No results yet". No zero-fill.
- **Freshness:** `primary_results` has no max-age floor (event-driven); the tight cadence is
  a scheduler concern, deliberately not an integrity failure when honest-empty.
- **Source name:** the artifact/source is historically named `primary_results` but is the
  general results connector too — `election_type` distinguishes; no rename needed.

## 5. County results + scheduled election-night deploy [E-F2]

Foundation for the county map (E-R9) and the automated go-live (E-R10). No live flip here —
all three pieces ship framework-shaped and disabled/honest-empty.

- **County schema.** `ResultRow` carries an optional `county: str | None` (5-digit county
  FIPS, e.g. `"04013"` = Maricopa; `None`/honest-empty for a statewide/untagged feed).
  `build_rows` passes a Contest's `county` key straight through, so E-R1's AZ adapter just
  tags each Contest with its county FIPS — no other change. `aggregate_to_county(rows) ->
  list[dict]` rolls county-tagged (or precinct-split) rows up to per-county candidate totals:
  votes summed per `(county, race_id, candidate)`, `pct` re-derived as the county-race share,
  `pct_reporting` derived once per county from its most-complete contest (`None` when no
  precinct counts — never zero-filled). Rows with no `county` roll up to nothing.
- **County geometry.** `apps/web/scripts/gen-us-counties.mjs` bakes the us-atlas counties
  TopoJSON to committed per-state JSON (`node scripts/gen-us-counties.mjs`), AZ first ->
  `apps/web/src/data/geo/az-counties.json` (`{ state, viewBox, counties: { <fips>: { name,
  d } } }`, viewBox cropped to the state). Add a state = one row in the script's `STATES`
  map + re-run. This JSON is what E-R9's `CountyMap` renders; the FIPS keys match the schema
  `county` field so results join geometry by FIPS.
- **Scheduled deploy.** `.github/workflows/results.yml` runs the tight election-night loop
  (bake `primary_results` -> `export_web` -> integrity gate -> `pnpm --filter web build` ->
  Cloudflare Pages **prod** deploy). **Shipped disabled** (`workflow_dispatch` only; the
  `schedule:` block is commented with a `# ENABLED BY E-R10` marker). A manual dispatch while
  `ACTIVE_STATES` is empty is a green no-op (honest-empty). E-R10 uncomments the schedule to
  arm the cadence at go-live.
