"""Election-results connector [E3.2, decision iter: state SoS feeds] — live primary (and,
via E3.3, general) returns for the competitive race set.

Source spine = each state's Secretary-of-State / Board-of-Elections live results feed
(free public records, authoritative, minutes-latency) [E3.1]. Every state publishes a
different native format (JSON / XML / CSV / Excel / HTML), so the pattern is ONE adapter
per state that normalizes its feed to the shared `ResultRow`; adding a state = adding one
`StateAdapter` entry, no other code change. A separate lightweight Wikipedia layer
supplies ONLY the "race called" signal (SoS feeds never carry a projection) [E3.1].

Election night is fragile under load, so every pull goes through the shared
`CachingFetcher` (bronze mirror + conditional GET + last-good fallback) [R8a,R10a] and
rows upsert by the natural key `(race_id, candidate)` [R4a] so re-runs every 1–5 min only
move totals, never truncate.

NO fabricated numbers [repo rule]: `ACTIVE_STATES` (the feeds turned on for live ingestion
this cycle) is empty until election-night ops enables a state, so the default bake is
honest-empty — real rows appear only when a real feed reports. The adapters + normalizer
are exercised against fixtures in the tests, not against invented committed data.

Live bake (scheduled, election night):
    uv run --project pipeline python -m btb_pipeline.cli bake primary_results
The CLI bake defaults to the primary adapter set; a general-election night is the same
connector with `election_type="general"` and the general states listed in ACTIVE_STATES
[E3.3] — no schema, display, or exporter change.

Provisional SoS numbers are later superseded by the certified MEDSL backfill (`certify()`),
a separate manual one-shot weeks/months later that flips `is_certified=true` [E3.1,E3.3].
"""

from __future__ import annotations

import csv
import io
import json
import re
import warnings
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, ConfigDict

from btb_pipeline.connector import CachingFetcher, Transport, upsert
from btb_pipeline.core import DATA_ROOT, SourceSpec, bake, stage_dir

# Results are timestamped facts that get superseded (provisional -> certified), so freshness
# is event-driven at the artifact level; the tight election-night cadence (1–5 min) is a
# scheduler concern, documented in DATA_SOURCES.md, not a max-age floor here.
SPEC = SourceSpec(
    name="primary_results", cadence="election-night (1–5 min)", freshness_floor_days=2000
)
CYCLE = 2026

# States whose live SoS feed is TURNED ON for ingestion this cycle. Empty until
# election-night ops enables a state (keeps the committed build honest-empty — no invented
# results). Flip a state on by listing it here once its adapter is validated against the
# state's pre-published test feed [E3.1].
ACTIVE_STATES: list[str] = []

# Which election the scheduled CLI bake is counting: "primary" or "general". Ops flips this
# to "general" (alongside ACTIVE_STATES) for the Nov 2026 general so the unchanged scheduled
# command `bake primary_results` picks the general adapter set — no new CLI args [E3.3].
ACTIVE_ELECTION_TYPE = "primary"


class ResultRow(BaseModel):
    """One candidate's result in one race — the normalized shape E3.3 renders. Extra keys
    ignored so heterogeneous feeds can carry more without breaking the schema."""

    model_config = ConfigDict(extra="ignore")

    race_id: str  # matches config/races id, e.g. "us-senate-2026-OH"
    state: str  # USPS postal
    office: str  # senate | house | governor
    district: int | None = None  # house only
    # Optional county tag [E-F2]: 5-digit county FIPS (e.g. "04013" = Maricopa), matching the
    # geometry keys in apps/web/src/data/geo/az-counties.json. Null (honest-empty) for a
    # statewide/untagged feed; E-R1's AZ parser populates it so aggregate_to_county can roll
    # county-tagged rows into per-county totals. Never invented — absent county → None.
    county: str | None = None
    cycle: int
    election_type: str  # primary | general
    candidate: str
    party: str | None = None
    votes: int
    pct: float | None = None  # candidate share of the race, 0–100 (derived from votes)
    precincts_reporting: int | None = None
    precincts_total: int | None = None
    pct_reporting: float | None = None  # 0–100 (derived from precincts when present)
    # Call status comes from the Wikipedia layer, never from the SoS feed [E3.1].
    is_called: bool = False
    called_by: str | None = None  # candidate the race is called for
    call_source: str | None = None  # e.g. "Wikipedia"
    as_of: str  # ISO-8601 UTC of the pull
    source_url: str
    is_certified: bool = False  # false while provisional; MEDSL backfill flips it true


def race_id(office: str, state: str, district: int | None, cycle: int = CYCLE) -> str:
    """Config-matching race id so results join the existing race pages by id [F4c]."""
    if office == "house":
        return f"us-house-{cycle}-{state}-{int(district):02d}"
    return f"us-{office}-{cycle}-{state}"


# A single contest's raw, format-agnostic shape that every state adapter produces; the
# shared normalizer turns a list of these into ResultRows. Keys: office, district (house
# only), candidate, party, votes, precincts_reporting, precincts_total.
Contest = dict


def build_rows(
    state: str,
    contests: list[Contest],
    *,
    source_url: str,
    election_type: str,
    as_of: datetime,
    cycle: int = CYCLE,
    is_certified: bool = False,
) -> list[dict]:
    """Normalize one state's contests -> ResultRows, deriving pct (share of the race by
    votes) and pct_reporting (from precincts). One row per candidate per race.

    `is_certified` is False for live SoS pulls (provisional) and True for the MEDSL
    certified backfill [E3.1], which supersedes provisional numbers via the same upsert."""
    stamp = as_of.astimezone(timezone.utc).isoformat()
    by_race: dict[str, list[Contest]] = defaultdict(list)
    for c in contests:
        rid = race_id(c["office"], state, c.get("district"), cycle)
        by_race[rid].append(c)

    rows: list[dict] = []
    for rid, cs in by_race.items():
        total = sum(int(c.get("votes") or 0) for c in cs)
        for c in cs:
            votes = int(c.get("votes") or 0)
            pr = c.get("precincts_reporting")
            pt = c.get("precincts_total")
            rows.append({
                "race_id": rid,
                "state": state,
                "office": c["office"],
                "district": c.get("district"),
                "cycle": cycle,
                "election_type": election_type,
                "candidate": c["candidate"],
                "party": c.get("party"),
                "county": c.get("county"),  # county FIPS passthrough [E-F2]; None if untagged
                "votes": votes,
                "pct": round(votes / total * 100, 1) if total else None,
                "precincts_reporting": pr,
                "precincts_total": pt,
                "pct_reporting": round(pr / pt * 100, 1) if pr is not None and pt else None,
                "as_of": stamp,
                "source_url": source_url,
                "is_certified": is_certified,
            })
    return rows


# ---- County-level rollup [E-F2] ---------------------------------------------------------
# The county field name/type + this signature are the schema E-R1's AZ parser populates and
# E-R9's CountyMap consumes: county = 5-digit county FIPS str (nullable), keyed identically to
# apps/web/src/data/geo/az-counties.json. This rolls county-tagged (or precinct-split) rows up
# to per-county candidate totals. Honest-empty [repo rule]: rows without a county are dropped,
# never bucketed into an invented county.


def aggregate_to_county(rows: list[dict]) -> list[dict]:
    """Roll county-tagged `ResultRow`s up to per-county candidate totals [E-F2].

    Input rows carry an optional `county` (5-digit county FIPS str). Rows with no county are
    skipped (honest-empty — never a fabricated bucket). Rows sharing `(county, race_id,
    candidate)` are summed on `votes` (e.g. precinct-split or early/day-of batches merged into
    one county figure). `pct` is re-derived as each candidate's share of that county's race by
    votes. `pct_reporting` is derived ONCE per county from the county's most-complete contest
    (largest `precincts_total`) — counties share their precinct set across contests, so the
    fullest contest's coverage represents the county — and is None when no precinct counts
    reported (honest "not reported", never zero-filled).

    Returns one dict per `(county, race_id, candidate)`, sorted by
    `(county, race_id, -votes, candidate)` for deterministic output:
        {county, race_id, state, office, district, cycle, election_type, candidate, party,
         votes, pct, pct_reporting}
    """
    # county -> race_id -> candidate -> accumulated row
    by_county: dict[str, dict[str, dict[str, dict]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    # county -> best (largest total) precinct pair seen: (precincts_reporting, precincts_total)
    county_reporting: dict[str, tuple[int, int]] = {}

    for r in rows:
        county = r.get("county")
        if not county:  # honest-empty: an untagged row does not belong to any county
            continue
        cand = by_county[county][r["race_id"]].setdefault(
            r["candidate"],
            {
                "county": county,
                "race_id": r["race_id"],
                "state": r.get("state"),
                "office": r.get("office"),
                "district": r.get("district"),
                "cycle": r.get("cycle"),
                "election_type": r.get("election_type"),
                "candidate": r["candidate"],
                "party": r.get("party"),
                "votes": 0,
            },
        )
        cand["votes"] += int(r.get("votes") or 0)

        pt = r.get("precincts_total")
        if pt:
            pr = int(r.get("precincts_reporting") or 0)
            best = county_reporting.get(county)
            if best is None or int(pt) > best[1]:
                county_reporting[county] = (pr, int(pt))

    out: list[dict] = []
    for county, by_race in by_county.items():
        report = county_reporting.get(county)
        pct_reporting = round(report[0] / report[1] * 100, 1) if report else None
        for race_id_, cands in by_race.items():
            total = sum(c["votes"] for c in cands.values())
            for c in cands.values():
                c["pct"] = round(c["votes"] / total * 100, 1) if total else None
                c["pct_reporting"] = pct_reporting
                out.append(c)

    out.sort(key=lambda c: (c["county"], c["race_id"], -c["votes"], c["candidate"]))
    return out


# ---- Native-format parsers (the per-state work) -----------------------------------------
# States publish heterogeneous formats [E3.1]; these are the two dominant machine-readable
# shapes. Each returns a list[Contest]. A new state either reuses one of these (pointing at
# its column/key names) or adds its own parser — the only per-state code.


def parse_json_contests(text: str) -> list[Contest]:
    """Generic JSON feed: a top-level `contests` array of
    {office, district?, candidates:[{name, party, votes}], precincts_reporting?,
    precincts_total?}. Explodes each contest's candidates into flat Contest rows."""
    doc = json.loads(text)
    out: list[Contest] = []
    for c in doc.get("contests", []):
        base = {
            "office": c["office"],
            "district": c.get("district"),
            "precincts_reporting": c.get("precincts_reporting"),
            "precincts_total": c.get("precincts_total"),
        }
        for cand in c.get("candidates", []):
            out.append({
                **base,
                "candidate": cand["name"],
                "party": cand.get("party"),
                "votes": cand.get("votes"),
            })
    return out


def parse_csv_contests(text: str) -> list[Contest]:
    """Generic CSV feed: one row per candidate with columns office, district, candidate,
    party, votes, precincts_reporting, precincts_total (blanks -> None)."""
    out: list[Contest] = []
    for r in csv.DictReader(io.StringIO(text)):
        district = (r.get("district") or "").strip()
        out.append({
            "office": (r.get("office") or "").strip(),
            "district": int(district) if district else None,
            "candidate": (r.get("candidate") or "").strip(),
            "party": (r.get("party") or "").strip() or None,
            "votes": int(r["votes"]) if (r.get("votes") or "").strip() else 0,
            "precincts_reporting": _int_or_none(r.get("precincts_reporting")),
            "precincts_total": _int_or_none(r.get("precincts_total")),
        })
    return out


def _int_or_none(v: str | None) -> int | None:
    v = (v or "").strip()
    return int(v) if v else None


# ---- Arizona adapter: Clarity ENR feed [E-R1] -------------------------------------------
# AZ election-night results run on the Clarity Elections ENR platform — public record
# (A.R.S. §39-121), no API key [E-R0]. Each county publishes its OWN Clarity site whose
# detail.xml carries <Region>{county}</Region>, so a county's feed IS that county's total; the
# parser tags every Contest with that county's 5-digit FIPS [E-F2] so aggregate_to_county can
# roll it up (and the county map joins geometry by FIPS). Only new per-state code is this one
# parser — the shared build_rows/normalizer/upsert are reused unchanged.
#
# Feed resolution (live, done by the fetch layer at go-live [E-R10], NOT here): GET
# .../AZ/<County>/<electionid>/current_ver.txt -> substitute <ver> -> GET
# .../<ver>/reports/detailxml.zip -> unzip -> this parser. The CachingFetcher returns text and
# Clarity serves a zip, so the ver-resolution + unzip (+ statewide-vs-15-county fan-out, still
# unconfirmed — E-R0 §Ambiguities) is remaining go-live wiring, out of this unit's boundary.

# AZ county name -> 5-digit FIPS, keyed identically to apps/web/src/data/geo/az-counties.json
# [E-F2] so county-tagged results join the county geometry by FIPS.
_AZ_COUNTY_FIPS: dict[str, str] = {
    "apache": "04001", "cochise": "04003", "coconino": "04005", "gila": "04007",
    "graham": "04009", "greenlee": "04011", "la paz": "04012", "maricopa": "04013",
    "mohave": "04015", "navajo": "04017", "pima": "04019", "pinal": "04021",
    "santa cruz": "04023", "yavapai": "04025", "yuma": "04027",
}

# Contest `text` -> office/district. Clarity's numeric `key` is per-county/per-cycle and NOT
# stable, so map on the free-form `text` [E-R0]. `text` is truncated/typo'd in real feeds
# (2024 sample: "...Congressional District 2 Congression"), so the regexes are lenient.
# House REQUIRES a "congress" token so state-legislative "Representative District N" contests
# are NOT mis-mapped to U.S. House.
_AZ_HOUSE_RE = re.compile(r"congress.*?district\s*0*(\d+)", re.I | re.S)
_AZ_GOV_RE = re.compile(r"\bgovernor\b", re.I)


def _az_office(text: str) -> tuple[str, int | None] | None:
    """Map a Clarity contest `text` to (office, district) for the AZ tracker scope — Governor +
    U.S. House (no U.S. Senate: AZ Senate seats are 2028/2030) [E-R0]. Returns None for
    out-of-scope contests (Senate/state exec/legislature/questions) so the caller surfaces +
    skips them. `text` may be truncated; whitespace is normalized first."""
    t = " ".join(text.split())
    m = _AZ_HOUSE_RE.search(t)
    if m:
        return "house", int(m.group(1))
    if _AZ_GOV_RE.search(t):
        return "governor", None
    return None


def parse_az_clarity_xml(text: str) -> list[Contest]:
    """Parse a Clarity ENR **detail.xml** feed (AZ SoS, one site per county) into Contests for
    the AZ tracker scope (Governor + U.S. House) [E-R0].

    Reads <Region> -> the county's 5-digit FIPS [E-F2] and tags every emitted Contest with it,
    so aggregate_to_county can roll the county's rows up. Each <Contest> maps by its free-form,
    truncation-tolerant `text` (NOT the unstable numeric `key`); out-of-scope contests are
    surfaced via a warning and skipped, never silently dropped. Each <Choice> ->
    candidate/party/votes (Choice.totalVotes is the roll-up; per-precinct <VoteType> children
    are ignored). Contest precinct attrs -> precincts_reporting/total -> pct_reporting (derived
    downstream in build_rows).

    Partisan-primary note [E-R0]: a primary feed splits a race into separate per-party contests.
    Both are emitted, but two contests mapping to the SAME (office, district) raise a warning —
    disambiguating them in the id is owned by E-R7, because race_id() has no party axis today,
    so they otherwise collapse into one race_id."""
    root = ET.fromstring(text)
    region = (root.findtext("Region") or "").strip()
    county = _AZ_COUNTY_FIPS.get(region.lower())
    if region and county is None:
        warnings.warn(
            f"AZ Clarity: unknown Region {region!r} — county tag left null (honest-empty)",
            stacklevel=2,
        )

    out: list[Contest] = []
    contests_per_race: dict[tuple[str, int | None], int] = defaultdict(int)
    skipped: list[str] = []
    for contest in root.iter("Contest"):
        ctext = contest.get("text") or ""
        mapped = _az_office(ctext)
        if mapped is None:
            skipped.append(" ".join(ctext.split()))
            continue
        office, district = mapped
        contests_per_race[(office, district)] += 1
        pr = _int_or_none(contest.get("precinctsReporting"))
        pt = (
            _int_or_none(contest.get("precinctsParticipating"))
            or _int_or_none(contest.get("precinctsReported"))
            or _int_or_none(contest.get("precinctsTotal"))
        )
        for choice in contest.findall("Choice"):
            out.append({
                "office": office,
                "district": district,
                "candidate": (choice.get("text") or "").strip(),
                "party": (choice.get("party") or "").strip() or None,
                "votes": _int_or_none(choice.get("totalVotes")) or 0,
                "precincts_reporting": pr,
                "precincts_total": pt,
                "county": county,  # 5-digit FIPS tag for aggregate_to_county [E-F2]
            })

    collisions = [k for k, n in contests_per_race.items() if n > 1]
    if collisions:
        labels = [f"{o}-{d:02d}" if d is not None else o for o, d in collisions]
        warnings.warn(
            f"AZ Clarity: partisan-primary contest collision on {labels} — race_id() has no "
            "party axis; multiple party primaries collapse into one race_id, owned by E-R7 "
            "[E-R0]",
            stacklevel=2,
        )
    if skipped:
        warnings.warn(
            f"AZ Clarity: {len(skipped)} out-of-scope contest(s) surfaced + skipped (tracker "
            f"scope = Governor + U.S. House): {skipped}",
            stacklevel=2,
        )
    return out


@dataclass(frozen=True)
class StateAdapter:
    """Binds a state to its live feed + native parser + which election is running. Adding a
    state = adding one entry to STATE_ADAPTERS; turning it on = listing it in ACTIVE_STATES."""

    state: str
    feed_url: str
    election_type: str  # primary | general
    parse: Callable[[str], list[Contest]]


# Representative registry (illustrative feed URLs from E3.1's format survey). These prove
# the per-state / heterogeneous-format pattern; the full competitive-state map is filled in
# as each state's feed is validated against its pre-published test feed. Not yet ACTIVE.
STATE_ADAPTERS: dict[str, StateAdapter] = {
    "OH": StateAdapter("OH", "https://liveresults.ohiosos.gov/", "primary", parse_json_contests),
    "CA": StateAdapter("CA", "https://dp.electionresults.sos.ca.gov/", "primary", parse_csv_contests),
    # AZ SoS Clarity ENR feed [E-R1]. election_type="primary" for the 2026 statewide primary
    # (2026-07-21). URL = Clarity host base (per-county/<electionid>/<ver>/reports/detailxml.zip
    # resolved by the fetch layer at go-live [E-R10]; see parse_az_clarity_xml). NOT yet ACTIVE
    # — E-R10 lists AZ in ACTIVE_STATES to turn it on. Validated against real-shape feed bytes.
    "AZ": StateAdapter("AZ", "https://results.enr.clarityelections.com/AZ/", "primary", parse_az_clarity_xml),
}

# General-election adapters [E3.3] — Nov 2026 readiness. Same per-state pattern as the
# primary registry, only election_type="general". Many states reuse the SAME SoS portal for
# both elections (a general-night endpoint or an election-id query param), so most entries
# reuse the primary parser; adding a general state is still ONE dict entry. Illustrative +
# fixture-tested, NOT active — a state goes live only when listed in ACTIVE_STATES.
GENERAL_ADAPTERS: dict[str, StateAdapter] = {
    "OH": StateAdapter("OH", "https://liveresults.ohiosos.gov/general/", "general", parse_json_contests),
    "CA": StateAdapter("CA", "https://dp.electionresults.sos.ca.gov/general/", "general", parse_csv_contests),
}

# run() selects the adapter set by which election is being counted tonight. One election
# runs at a time per state, so a single ACTIVE_STATES list + this election_type switch is
# all ops needs to flip the connector from primary to general [E3.3].
ADAPTER_SETS: dict[str, dict[str, StateAdapter]] = {
    "primary": STATE_ADAPTERS,
    "general": GENERAL_ADAPTERS,
}


# ---- Wikipedia "race called" layer ------------------------------------------------------
# The ONLY thing borrowed from Wikipedia (CC BY-SA) is call status, keyed on race_id — never
# vote totals [E3.1]. Shape: {race_id: {"called_by": name, "call_source": "Wikipedia"}}.
Calls = dict


def merge_call_status(rows: list[dict], calls: Calls | None) -> list[dict]:
    """Stamp is_called / called_by / call_source onto every row of a called race. Best-effort,
    clearly attributed — SoS feeds carry no projection, so a called flag is always borrowed."""
    if not calls:
        return rows
    for r in rows:
        call = calls.get(r["race_id"])
        if call:
            r["is_called"] = True
            r["called_by"] = call.get("called_by")
            r["call_source"] = call.get("call_source", "Wikipedia")
    return rows


# ---- MEDSL certified backfill (one-shot) [E3.1,E3.3] ------------------------------------
# Weeks/months after election night, MIT Election Lab (MEDSL, CC BY) publishes certified
# totals. The backfill normalizes them with is_certified=True and upserts over the
# provisional gold by (race_id, candidate) — superseding provisional numbers and flipping
# each race page from "Unofficial — provisional" to "Certified". It is a manual one-shot,
# NOT a scheduled source, so it stays out of the CLI SOURCES registry.
MEDSL_SOURCE_URL = "https://github.com/MEDSL"


def parse_medsl_csv(text: str) -> dict[str, list[Contest]]:
    """MEDSL certified export -> {state: [Contest]}. One row per candidate with columns
    state, office, district, candidate, party, votes — office already normalized to our
    tokens (senate|house|governor). Precinct counts are irrelevant post-certification."""
    by_state: dict[str, list[Contest]] = defaultdict(list)
    for r in csv.DictReader(io.StringIO(text)):
        district = (r.get("district") or "").strip()
        by_state[(r.get("state") or "").strip().upper()].append({
            "office": (r.get("office") or "").strip(),
            "district": int(district) if district else None,
            "candidate": (r.get("candidate") or "").strip(),
            "party": (r.get("party") or "").strip() or None,
            "votes": int(r["votes"]) if (r.get("votes") or "").strip() else 0,
        })
    return dict(by_state)


def certify(
    medsl_csv: str | None = None,
    *,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
    election_type: str = "general",
    cycle: int = CYCLE,
) -> Path:
    """One-shot MEDSL certified backfill [E3.1]. Normalizes certified totals
    (is_certified=True) and upserts them over the provisional gold by (race_id, candidate),
    superseding provisional numbers and flipping the page to "Certified". Any race-call
    attribution already on the provisional row is carried forward. Honest-empty when no CSV
    is supplied (re-bakes existing gold unchanged), so it is safe to wire before data exists.

    Invoke at backfill time (not scheduled):
        python -c "from btb_pipeline.sources import primary_results as pr; \\
                   pr.certify(open('medsl_2026.csv').read())"
    """
    stamp = as_of or datetime.now(timezone.utc)
    existing = _existing(root)
    incoming: list[dict] = []
    if medsl_csv:
        prior = {_uid(r): r for r in existing}
        for state, contests in parse_medsl_csv(medsl_csv).items():
            certified = build_rows(
                state, contests, source_url=MEDSL_SOURCE_URL,
                election_type=election_type, as_of=stamp, cycle=cycle, is_certified=True,
            )
            for row in certified:
                prev = prior.get(_uid(row))
                if prev and prev.get("is_called"):  # keep the borrowed call attribution
                    row["is_called"] = True
                    row["called_by"] = prev.get("called_by")
                    row["call_source"] = prev.get("call_source")
            incoming.extend(certified)

    rows = merge_results(existing, incoming)
    return bake(SPEC, ResultRow, rows, stamp, root)


# ---- upsert by (race_id, candidate) [R4a] -----------------------------------------------


def _uid(r: dict) -> str:
    return f"{r['race_id']}::{r['candidate']}"


def merge_results(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """Idempotent upsert on the natural key (race_id, candidate) — reuses connector.upsert
    via a transient composite key so a 1–5 min re-poll only moves totals [R4a]."""
    e = [{**r, "_uid": _uid(r)} for r in existing]
    i = [{**r, "_uid": _uid(r)} for r in incoming]
    merged = upsert(e, i, "_uid")
    for r in merged:
        r.pop("_uid", None)
    return merged


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    return json.loads(path.read_text()).get("rows", []) if path.exists() else []


def run(
    transport: Transport | None = None,
    calls: Calls | None = None,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
    states: list[str] | None = None,
    election_type: str | None = None,
) -> Path:
    """Fetch each ACTIVE state's feed via the caching/last-good fetcher -> normalize ->
    merge Wikipedia call status -> upsert by (race_id, candidate) -> bake gold [R14a].

    `election_type` selects the adapter set ("primary" or "general" [E3.3]); the display,
    schema, and upsert key are identical, so a general night is just `election_type="general"`
    plus the general states listed in ACTIVE_STATES. Defaults to `ACTIVE_ELECTION_TYPE` so
    the scheduled no-arg CLI bake follows whichever election ops has flipped on.

    Honest-empty by default: with no ACTIVE_STATES there is nothing to fetch (no network),
    so the baked artifact carries zero rows until a real feed reports."""
    stamp = as_of or datetime.now(timezone.utc)
    adapters = ADAPTER_SETS[election_type or ACTIVE_ELECTION_TYPE]
    targets = [
        s for s in (states if states is not None else ACTIVE_STATES) if s in adapters
    ]

    incoming: list[dict] = []
    if targets:
        if transport is None:
            import requests  # local import: only needed for live runs

            transport = lambda url, headers: requests.get(  # noqa: E731
                url, headers=headers, timeout=30
            )
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)
        for state in targets:
            ad = adapters[state]
            contests = ad.parse(fetcher.get(ad.feed_url))
            incoming.extend(build_rows(
                state, contests, source_url=ad.feed_url,
                election_type=ad.election_type, as_of=stamp,
            ))
        incoming = merge_call_status(incoming, calls)

    rows = merge_results(_existing(root), incoming)
    return bake(SPEC, ResultRow, rows, stamp, root)
