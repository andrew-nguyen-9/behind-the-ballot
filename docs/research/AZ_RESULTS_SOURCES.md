# Research · Arizona Results-Source Specifics (E-R0)

> **Concrete-specifics doc for E-R1.** The generic source decision is already made in
> `RESULTS_SOURCES.md` (SoS-feed spine + Wikipedia call-status + MEDSL certified backfill;
> paid APIs out). This doc pins the *concrete AZ bytes* E-R1 writes a parser against — it does
> **not** re-litigate options. AZ 2026 statewide primary (per orchestrator brief: **2026-07-21**;
> E-R1 confirm exact date against the SoS calendar). All URLs below were fetched read-only.

## Recommendation (confirmed)

**Confirm the SoS live feed as the AZ source.** Concretely, Arizona's election-night results run
on **Clarity Elections ENR** (the SOE/Scytl platform, now under Enhanced Voting). The public,
machine-readable data files are served from CloudFront at
`https://results.enr.clarityelections.com/AZ/...` and were **verified reachable, returning real
feed bytes** (status codes below). The human portal `https://results.arizona.vote/` is a
Cloudflare **JS-challenge** wrapper (`"Just a moment..."`, HTTP 403 to any non-browser client) —
it is **not** the machine feed; do not scrape it. Consume the Clarity data files directly.

Not usable / not the pick: `results.arizona.vote` HTML (Cloudflare-gated), AP/DDHQ (paid, out).

## 1. Live feed endpoint(s) + format + sample shape

**Host / path pattern** (one Clarity site per AZ county; `<ver>` from `current_ver.txt`):

```
https://results.enr.clarityelections.com/AZ/<County>/<electionid>/current_ver.txt      → plain-text version number
https://results.enr.clarityelections.com/AZ/<County>/<electionid>/<ver>/reports/summary.zip     → summary.csv (+ .xml)  [county-grain, cleanest]
https://results.enr.clarityelections.com/AZ/<County>/<electionid>/<ver>/reports/detailxml.zip   → detail.xml            [precinct-grain]
https://results.enr.clarityelections.com/AZ/<County>/<electionid>/<ver>/json/sum.json           → gzipped JSON summary
```

E-R1 flow: GET `current_ver.txt` → substitute `<ver>` → GET the report zip → unzip → parse. Poll
`current_ver.txt`; when it changes, re-pull (that is the "new data" signal).

**Formats available:** CSV, XML, XLS, JSON. **Recommended for `StateAdapter.parse`: `summary.csv`**
— one row per candidate per contest, already close to our normalized record:

```csv
"line number","contest name","choice name","party name","total votes","percent of votes","registered voters","ballots cast","num Precinct total","num Precinct rptg","over votes","under votes"
6,"U.S. Senator (Vote For 1)","KARI, LAKE","REP",115595,55.67,282639,211595,109,109,"0","0"
7,"U.S. Senator (Vote For 1)","GALLEGO, RUBEN","DEM",86674,41.74,282639,211595,109,109,"0","0"
```

→ maps to `Contest`: `contest name`→office/district, `choice name`→candidate, `party name`→party,
`total votes`→votes, `percent of votes`→pct, `num Precinct rptg`/`num Precinct total`→`pct_reporting`.
No `is_called` (per generic doc, that comes from the Wikipedia layer, not this feed).

**detail.xml** (precinct grain) shape — the same data with per-vote-type + per-precinct nesting:

```xml
<ElectionResult>
  <Timestamp>11/14/2024 12:14:22 PM MST</Timestamp>
  <ElectionName>2024 General Election</ElectionName>
  <Region>Pinal</Region>
  <Contest key="0005" text="U.S. Senator" voteFor="1" isQuestion="false"
           precinctsReporting="109" precinctsReported="109">
    <Choice key="001" text="KARI, LAKE" party="REP" totalVotes="115595">
      <VoteType name="Election Day" votes="...">
        <Precinct name="01 KEARNY" votes="..."/>   <!-- per-precinct breakdown -->
      </VoteType>
      <VoteType name="Early Voting" votes="..."/>
      <VoteType name="Provisional" votes="..."/>
    </Choice>
  </Contest>
</ElectionResult>
```

`precinctsReporting`/`precinctsReported` (contest attrs) → `pct_reporting`. `Choice.party`/`totalVotes`
are the candidate roll-up; `VoteType` splits Election-Day / Early / Provisional.

## 2. Cadence + county granularity

- **Cadence:** AZ SoS publishes the press/ENR feed starting **8:00 pm local on election night**,
  updated in real time as counties report; `current_ver.txt` bumps on each new snapshot. Poll per
  `RESULTS_SOURCES.md` scheduler (1–5 min at polls-close, hourly after). Precinct-detail files are
  additionally offered via a media FTP/HTTPS press feed (per SoS "Election Night Results Help").
- **County granularity: YES.** Each county runs its own Clarity site (`.../AZ/<County>/...`), so a
  county's feed **is** that county's total — county-first grain is native (sum/attribute per county).
  A statewide-aggregated Clarity feed (contests carrying `<County name=...>` children) is fronted by
  `results.arizona.vote`; its statewide `electionid` could not be read here because of the Cloudflare
  challenge — **flag for E-R1 (§Ambiguities)**.
- **Precinct-reporting counts: YES** — `num Precinct total`/`num Precinct rptg` (CSV) and
  `precinctsReported`/`precinctsReporting` (XML) → `pct_reporting`.

## 3. Pre-published test / sample feed URL (verified, real bytes)

No dedicated 2026-primary *test* site is published yet (2 weeks out). Per the brief's fallback,
use the **prior-cycle AZ Clarity feed as the shape reference + parser-validation fixture** — E-R1
validates `parse` against these real bytes before election night. The 2026 primary will appear at
the **same host pattern** with a new `electionid`.

Verified fixture (AZ / Pinal County / 2024 General, `electionid=122318`, `ver=354892`):

```
GET .../AZ/Pinal/122318/current_ver.txt              → HTTP 200, text/plain, 6 bytes ("354892")
GET .../AZ/Pinal/122318/354892/reports/summary.zip   → HTTP 200, application/zip, 4859 bytes  → summary.csv 22.7 KB
GET .../AZ/Pinal/122318/354892/reports/detailxml.zip → HTTP 200, application/zip, 155923 bytes → detail.xml 2.2 MB
GET .../AZ/Pinal/122318/354892/reports/detailtxt.zip → HTTP 200, application/zip, 162656 bytes
GET .../AZ/Pinal/122318/354892/json/sum.json         → HTTP 200, application/json (gzip)
```

(Additional live per-county example confirmed: `.../AZ/Greenlee/122271/`.) The 15 AZ counties are
Apache, Cochise, Coconino, Gila, Graham, Greenlee, La Paz, Maricopa, Mohave, Navajo, Pima, Pinal,
Santa Cruz, Yavapai, Yuma. Reference parser: openelections **`clarify`** (Python) already models
this exact XML — reuse it rather than hand-rolling. `results.arizona.vote/` → HTTP 403 (Cloudflare
JS challenge); intentionally *not* the machine feed.

## 4. Office → race-id mapping notes

**On the AZ 2026 primary ballot** (2026 is a gubernatorial year): **Governor** + all statewide
constitutional officers (SoS, AG, Treasurer, Supt. Public Instruction, Mine Inspector, Corp.
Commission), **all 9 U.S. House districts (CD1–CD9)**, and state legislature. **No U.S. Senate**
(AZ Senate seats: Kelly 2028, Gallego 2030). Tracker scope (competitive Gov/House/Senate) for AZ
2026 = **Governor + the competitive U.S. House districts**.

Feed → our id `us-{office}-2026-AZ[-DD]`:
- Governor → `us-gov-2026-AZ` — contest `text` ≈ `"Governor"`.
- U.S. House CDn → `us-house-2026-AZ-0n` — contest `text` ≈ `"U.S. Representative Congressional District n …"`.

**Ambiguities to flag for E-R1 / E-R7:**
1. **Map by contest `text`, not `key`.** Clarity `Contest key` (e.g. `"0006"`) is per-county and
   per-cycle — **not stable**. Match office/district by regex on the `text` string.
2. **`text` is free-form and truncated.** Real 2024 sample: `"U.S. Representative Congressional
   District 2 Congression"` (sic — truncated). Parser must tolerate truncation/typos.
3. **Primary contests split by party.** A primary feed carries separate REP / DEM (etc.) contests
   per office; E-R1 must fold party into the `race_id` grouping, not treat them as one race.
4. **`us-{office}` token unresolved:** `gov` vs `governor`, `house` vs `rep`. Pin the canonical
   office token for `race_id` with E-R7 (id-scheme owner) so E-R1 and the roster agree.
5. **Statewide vs 15-county aggregation:** confirm whether a single statewide AZ Clarity
   `electionid` exists for the 2026 primary (load `results.arizona.vote` in a real browser to read
   its redirect target) — else E-R1 aggregates the 15 per-county feeds.

## 5. License / ToS (one-liner for `03_DATA_SOURCES.md`)

Arizona election results are **public records** (Arizona Public Records Law, A.R.S. §39-121),
published by the AZ Secretary of State / county election officials via the Clarity ENR feed —
free to reuse, **no API key, no rate-limit/ToS gate on the data files** (the Cloudflare gate is on
the HTML portal only). Attribute *"Arizona Secretary of State / county election officials"*.
Freshness floor on the night: tight (hours); mirror each pull to R2 bronze + last-good `[R8a]`.

## Sources consulted

- AZ SoS elections + "Election Night Results Help" (press feed = raw XML via FTP/HTTPS, summary +
  precinct detail, from 8pm local): <https://azsos.gov/elections>,
  <https://azsos.gov/election-night-results-help> (both HTTP 403 to non-browser — Cloudflare).
- AZ statewide portal: <https://results.arizona.vote/> (Cloudflare JS challenge).
- Live Clarity ENR feed (verified 200, real bytes): `https://results.enr.clarityelections.com/AZ/`
  (Pinal `122318`, Greenlee `122271`).
- openelections `clarify` (Clarity XML parser + schema): <https://github.com/openelections/clarify>.
