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
