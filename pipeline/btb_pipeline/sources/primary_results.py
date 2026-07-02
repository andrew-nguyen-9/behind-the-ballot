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
Provisional SoS numbers are later superseded by the certified MEDSL backfill, which flips
`is_certified=true` (a separate one-shot, weeks/months later) [E3.1].
"""

from __future__ import annotations

import csv
import io
import json
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


class ResultRow(BaseModel):
    """One candidate's result in one race — the normalized shape E3.3 renders. Extra keys
    ignored so heterogeneous feeds can carry more without breaking the schema."""

    model_config = ConfigDict(extra="ignore")

    race_id: str  # matches config/races id, e.g. "us-senate-2026-OH"
    state: str  # USPS postal
    office: str  # senate | house | governor
    district: int | None = None  # house only
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
) -> list[dict]:
    """Normalize one state's contests -> ResultRows, deriving pct (share of the race by
    votes) and pct_reporting (from precincts). One row per candidate per race."""
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
                "votes": votes,
                "pct": round(votes / total * 100, 1) if total else None,
                "precincts_reporting": pr,
                "precincts_total": pt,
                "pct_reporting": round(pr / pt * 100, 1) if pr is not None and pt else None,
                "as_of": stamp,
                "source_url": source_url,
                "is_certified": False,
            })
    return rows


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
) -> Path:
    """Fetch each ACTIVE state's feed via the caching/last-good fetcher -> normalize ->
    merge Wikipedia call status -> upsert by (race_id, candidate) -> bake gold [R14a].

    Honest-empty by default: with no ACTIVE_STATES there is nothing to fetch (no network),
    so the baked artifact carries zero rows until a real feed reports."""
    stamp = as_of or datetime.now(timezone.utc)
    targets = [
        s for s in (states if states is not None else ACTIVE_STATES) if s in STATE_ADAPTERS
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
            ad = STATE_ADAPTERS[state]
            contests = ad.parse(fetcher.get(ad.feed_url))
            incoming.extend(build_rows(
                state, contests, source_url=ad.feed_url,
                election_type=ad.election_type, as_of=stamp,
            ))
        incoming = merge_call_status(incoming, calls)

    rows = merge_results(_existing(root), incoming)
    return bake(SPEC, ResultRow, rows, stamp, root)
