# Research · Election-Results Sources (E3.1)

> **Decision doc.** Picks the election-night results source(s) for the tracker so E3.2
> (ingestion) and E3.3 (display) can build against a known shape and cadence. Feeds the
> `03_DATA_SOURCES.md` contract `[R14a]` once a row is added at ingestion time.
>
> **Hard constraint from Andrew: paid APIs are OUT (no budget).** So the two obvious
> "just buy the feed" answers — AP and Decision Desk HQ — are disqualified for ingestion
> and covered only for context. The real decision is *among the free options*.

## TL;DR recommendation

**Primary spine: state Secretary-of-State / Board-of-Elections live results feeds,
scoped to the states that hold our competitive races.** Supplement with **Wikipedia race
tables** as a gap-filler and as the source of "race called" status (which raw SoS feeds
do not carry). Use **MEDSL** only for the *post-certification* backfill — it is months
late and cannot serve election night.

One line: **scrape the state SoS feeds for the target races, borrow race-call status from
Wikipedia, reconcile to certified MEDSL later.**

The three key tradeoffs, up front:

1. **Authoritative + real-time, but N-way scrape.** SoS feeds are the ground truth AP and
   DDHQ themselves ingest, and they update within minutes — but every state's format
   differs (JSON / XML / CSV / Excel / HTML / PDF), so cost = one custom scraper per
   state. Scoping to competitive-race states only is what makes this tractable.
2. **No "winner called" signal.** SoS feeds publish vote totals and precincts-reporting,
   never a projection/call. We either derive a naive call ourselves or read Wikipedia
   (whose editors mirror AP/DDHQ calls minutes-to-hours later). That is the price of not
   paying for AP.
3. **Fragility under load.** State portals change between cycles and can wobble on
   election night. The existing bronze→last-good pattern `[R8a]` is mandatory here: mirror
   every pull, publish last-good + open an issue rather than nothing.

## The options, compared

| Source | Free? | License / ToS | Coverage | Election-night latency | Machine-readability | Scrape difficulty | Reliability |
|---|---|---|---|---|---|---|---|
| **State SoS / BoE live feeds** | **Yes** (public records) | Government data, generally free to reuse; a few portals attach a ToS — use the *published data feed*, not authenticated scraping | 50 states + DC; primaries + general; down to county/precinct in many states | **Minutes** — updates as counties report through the night | Mixed: JSON/XML/CSV/Excel in the better states, HTML/PDF in the worst | **High** — one custom parser per state, formats drift per cycle | Authoritative (it *is* the source of truth); but no race calls and uneven completeness early in the night |
| **Wikipedia race tables** | **Yes** | **CC BY-SA** — attribution + share-alike on derived tables `[H1a]` | Broad for high-profile races (Pres/Sen/Gov/competitive House); thin down-ballot | **Minutes-to-hours** — hand-updated by editors; key pages are edit-protected to experienced editors on election night | HTML table scrape (one stable-ish format); no schema guarantee | **Low-medium** — single page shape, but layout can change and totals lag | Human-curated, cites AP/DDHQ; good for *called* status, not for authoritative running totals |
| **MEDSL (MIT Election Lab)** | **Yes** | **CC BY**, attribute `[N3a]` — already used for 2024 president baseline | Gold-standard, certified, precinct-level, primaries + general | **Months** — the 2024 dataset took **500+ days** after polls closed | Clean CSV on GitHub / Harvard Dataverse | **Low** — bulk files | Highest accuracy, but **cannot serve election night** — post-hoc only |
| AP Elections API | **No — OUT** | Commercial license | All races, all states, with official race calls | Seconds | Clean JSON/XML | N/A (turnkey) | Industry benchmark |
| Decision Desk HQ | **No — OUT** | Free ad-embed widget, but **API is subscription/licensed** | All races, national, with calls | Seconds-to-minutes | Clean JSON | N/A (turnkey) | Strong; the free widget is embed-only, not a data feed we can ingest |

### What each FREE option can and cannot deliver on election night

- **State SoS feeds — CAN:** authoritative live vote totals, precincts-reporting /
  expected, county breakdowns, both primaries and general, updating every few minutes.
  **CANNOT:** give a normalized national schema (each state differs), a "race called"
  flag, or complete coverage early in the night (counties report on their own clock;
  mail/late ballots trickle for days).
- **Wikipedia — CAN:** a quick, low-effort read of who's ahead and, crucially, whether a
  race has been *called* (editors reflect AP/DDHQ), across the marquee races we care
  about. **CANNOT:** be treated as authoritative or timely to the minute, guarantee a
  stable machine schema, or cover down-ballot depth. Share-alike (CC BY-SA) applies to
  anything we derive from it.
- **MEDSL — CAN:** nothing on the night. **CANNOT** be part of the election-night path at
  all; it is the certified backfill that supersedes our provisional numbers weeks/months
  later.

## Why this recommendation (reasoning)

1. **The constraint decides it.** With paid APIs out, the only sources that produce
   *live, structured* returns on election night are the state feeds. Wikipedia is live
   but not structured/authoritative; MEDSL is structured/authoritative but not live. So
   SoS is necessarily the spine, and the other two play support.
2. **Scope makes the hard part tractable.** The tracker follows a *competitive set* of
   House/Senate/Governor races `[E2.2]`, not all-50-states-all-offices. We only need
   scrapers for the handful of states holding those races — a bounded, cycle-planned list
   — not a 51-jurisdiction moonshot. This is the difference between "infeasible for a
   free project" and "a weekend of parsers per cycle."
3. **It fits decisions already made.** Wikipedia is already the project's supplementary
   roster/ratings source under CC BY-SA `[H1a]`, and MEDSL is already the certified
   prior-results baseline `[N3a]`. Reusing both for results keeps the source surface and
   the attribution story consistent — no new vendor, no new license class.
4. **It fits the pipeline contract.** Bronze mirror + last-good + issue-on-staleness
   `[R8a]`, idempotent upsert by natural key `[R4a]`, `--dry-run` schema smoke `[R6a]`,
   and per-source cadence `[R3a]` all apply cleanly. Provisional SoS numbers get
   *superseded* by MEDSL on certification — same "last-good, then better-good" flow.

## What E3.2 / E3.3 should build against

**Normalized record (silver/gold), one row per candidate per race:**

```
race_id, state, office, district, cycle, election_type (primary|general),
candidate, party, votes, pct,
precincts_reporting, precincts_total, pct_reporting,
is_called, called_by, call_source,     # from Wikipedia layer, not SoS
as_of (UTC), source_url, is_certified  # false live; true after MEDSL backfill
```

**Ingestion (E3.2):**
- One scraper per target state, each normalizing that state's native format to the record
  above; register each as its own `03_DATA_SOURCES.md` row `[R14a]` (license = that
  state's data terms; the aggregate freshness floor on the night is tight, e.g. hours).
- Separate lightweight Wikipedia scraper that supplies **only** `is_called` / `called_by`
  keyed on `race_id` — do not use it for vote totals.
- Mirror every raw pull to R2 bronze `[R8a]`; upsert by `(race_id, candidate)` `[R4a]`.

**Cadence / election-night latency (E3.2 scheduler):**
- **Polls-close window:** poll each state feed every **1–5 min** (respect the feed; back
  off on errors `[R10a]`). Expect coverage to *ramp* — pct_reporting climbs over hours.
- **Election night → +several days:** drop to hourly; late/mail/provisional ballots keep
  moving totals. Keep `is_certified = false` and show an "unofficial, X% reporting"
  banner.
- **Post-certification (weeks-to-months):** one-shot MEDSL backfill flips
  `is_certified = true` and supersedes provisional numbers.

**Display (E3.3):**
- Always render `as_of`, `pct_reporting`, and an **unofficial/provisional** label until
  certified `[R5a]`. Show `called_by` as attribution when a race is marked called.
- Attribution surface: state SoS credited per race; Wikipedia CC BY-SA credited for
  call-status; MEDSL CC BY credited on certified numbers — all flow into `/sources`
  `[R14a]`.

## Risks

- **Per-state format drift / breakage.** Feeds change between cycles and can fail under
  election-night load. Mitigate with `--dry-run` schema smoke `[R6a]`, last-good publish
  `[R8a]`, and building/testing scrapers against each state's *test feed* before the night
  (state officials publish these ahead of time).
- **No authoritative call signal.** Borrowing `is_called` from Wikipedia inherits its lag
  and its CC BY-SA share-alike obligation; a self-derived "call" would be editorially
  risky. Treat call status as clearly-attributed, best-effort.
- **Coverage gaps early in the night** (counties report unevenly; some states publish only
  HTML/PDF) — set expectations in the UI, never imply completeness.
- **ToS edge cases.** Most SoS data is public-domain-ish, but a couple of portals wrap a
  ToS; consume the published *data* endpoints, not scraped authenticated pages, and record
  each state's terms in the source row.
- **Effort scales with the competitive map.** If the competitive set grows, so does the
  scraper count; keep the target-state list explicit and cycle-scoped.

## Sources consulted

- MinnPost *Election Night API* (open-source SoS scraper/aggregator; confirms per-state
  custom parsing, cron polling, JSON/XML/Excel formats): <https://github.com/MinnPost/election-night-api>
- State examples of live machine-readable feeds: CA SoS `dp.electionresults.sos.ca.gov`,
  OH `liveresults.ohiosos.gov`, MO `enr.sos.mo.gov`, NM `electionresults.sos.nm.gov`.
- MEDSL release latency (500+ days for 2024): MIT Election Lab, *Inside the 2024 Precinct
  Project* — <https://electionlab.mit.edu/articles/inside-2024-precinct-project>; data +
  license at <https://electionlab.mit.edu/data> and <https://github.com/MEDSL>.
- Decision Desk HQ products (free embed vs. subscription/licensed API):
  <https://www.decisiondeskhq.com/products>.
- Wikipedia election-night editing (edit-protection, editor-curated, cites AP/DDHQ):
  Wikimedia Foundation, *What Wikipedia saw during election week* —
  <https://wikimediafoundation.org/news/2020/12/17/what-wikipedia-saw-during-election-week/>.
</content>
