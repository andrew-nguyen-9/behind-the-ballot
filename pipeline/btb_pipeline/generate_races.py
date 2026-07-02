"""Generate real 2026 race configs + finance gold from FEC [content curation; user decision
iter 69: auto Senate + House key races; E2.2: House competitive set + Governor]. Three offices:

  * Senate — every Class-II 2026 seat (33 states), candidates from FEC `office=S`.
  * House  — the competitive set (Toss-up + Lean per Wikipedia race ratings, Q7.3), candidates
             from FEC `office=H` filtered by `state`+`district`.
  * Governor — the competitive set (Toss-up + Lean per Wikipedia), STATE races. FEC covers only
             FEDERAL offices, so governors have NO finance join; candidates are left to a wired
             state-office roster source (see .done.md gotcha) — the config carries none for now.

For each Senate/House seat we pull real candidates (top by receipts), write a config under
`apps/web/src/config/races/`, and bake the tracked candidates' totals to gold/fec so the finance
export reads real, freshness-traceable numbers. Governor configs are emitted with no FEC join.

    DATA_GOV_API_KEY=… uv run --project pipeline python -m btb_pipeline.generate_races

ponytail: editorial rule = "FEC-registered, top TOP_N by receipts above MIN_RECEIPTS". The
competitive House/Gov sets are the only hand-curated input (sourced from Wikipedia race ratings,
Toss-up + Lean); re-running refreshes candidates/finance against FEC.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from btb_pipeline.connector import CachingFetcher, Transport
from btb_pipeline.core import DATA_ROOT, bake, stage_dir
from btb_pipeline.sources.fec import SPEC as FEC_SPEC
from btb_pipeline.sources.fec import FecTotals

RACES_DIR = Path("apps/web/src/config/races")
API_ROOT = "https://api.open.fec.gov/v1"

# 33 Class-II Senate seats up in 2026 (mirrors apps/web CLASS_II_2026_STATES).
CLASS_II_2026 = [
    "AL", "AK", "AR", "CO", "DE", "GA", "ID", "IL", "IA", "KS", "KY", "LA", "ME",
    "MA", "MI", "MN", "MS", "MT", "NE", "NH", "NJ", "NM", "NC", "OK", "OR", "RI",
    "SC", "SD", "TN", "TX", "VA", "WV", "WY",
]

# Competitive 2026 U.S. House districts — Toss-up + Lean (Q7.3) per Wikipedia's "2026 United
# States House of Representatives elections" race-ratings tables (Q7.2). (state, district).
# This is the ONLY curated selection input; candidates + finance come live from FEC.
COMPETITIVE_HOUSE_2026: list[tuple[str, int]] = [
    ("AZ", 1), ("AZ", 6), ("CA", 13), ("CA", 22), ("CA", 27), ("CA", 41), ("CA", 45),
    ("CO", 8), ("IA", 1), ("IA", 3), ("ME", 2), ("MI", 7), ("MI", 10), ("MN", 2),
    ("NC", 1), ("NE", 2), ("NJ", 7), ("NM", 2), ("NV", 3), ("NY", 4), ("NY", 17),
    ("NY", 19), ("OH", 9), ("OH", 13), ("OR", 5), ("PA", 7), ("PA", 8), ("PA", 10),
    ("TX", 34), ("VA", 2), ("WA", 3), ("WI", 3),
]

# Competitive 2026 Governor races — Toss-up + Lean per Wikipedia's "2026 United States
# gubernatorial elections" ratings. Governor is a STATE office (no FEC finance); candidate
# rosters await a wired state-office source, so configs carry none for now (see .done.md).
COMPETITIVE_GOV_2026: list[str] = [
    "AZ", "GA", "KS", "ME", "MI", "NV", "NH", "OH", "PA", "WI",
]

PARTY = {"DEM": "D", "DFL": "D", "REP": "R", "IND": "I", "LIB": "L", "GRE": "G"}
HONORIFICS = {"SEN", "REP", "DR", "MR", "MRS", "MS", "HON", "JR", "SR", "II", "III", "IV", "V"}

MIN_RECEIPTS = 50_000.0  # drop negligible/paper filers
TOP_N = 6


def get_api_key() -> str:
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        raise RuntimeError("DATA_GOV_API_KEY not set — see docs/SETUP_SECRETS.md")
    return key


def totals_url(
    office: str, state: str, api_key: str, district: int | None = None, per_page: int = 20
) -> str:
    """OpenFEC candidates/totals URL. office is the FEC code ('S' Senate, 'H' House);
    district is required for House and ignored otherwise."""
    params: dict[str, object] = {
        "api_key": api_key, "cycle": 2026, "office": office, "state": state,
        "sort": "-receipts", "per_page": per_page,
    }
    if office == "H" and district is not None:
        params["district"] = f"{district:02d}"
    return f"{API_ROOT}/candidates/totals/?{urlencode(params)}"


def _party(fec_party: str | None) -> str:
    return PARTY.get((fec_party or "").upper(), "other")


def display_name(fec_name: str) -> str:
    """FEC 'LAST, FIRST SUFFIX' → 'First Last', dropping honorific tokens (SEN/REP/...)."""
    last, _, first = (fec_name or "").partition(",")
    first_tokens = [t for t in first.split() if t.upper().strip(".") not in HONORIFICS]
    parts = [*first_tokens, last.strip()]
    return " ".join(p.title() for p in parts if p).strip()


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def race_id(office: str, state: str, district: int | None = None) -> str:
    """Stable, globally-unique race id. house includes the zero-padded district."""
    if office == "house":
        return f"us-house-2026-{state}-{district:02d}"
    return f"us-{office}-2026-{state}"


def _candidates_and_totals(results: list[dict]) -> tuple[list[dict], list[dict]]:
    """Top-N FEC filers above MIN_RECEIPTS → (candidate configs, finance totals rows)."""
    kept = [r for r in results if float(r.get("receipts") or 0) >= MIN_RECEIPTS][:TOP_N]
    candidates, totals = [], []
    for r in kept:
        name = display_name(r.get("name", ""))
        candidates.append({
            "id": slug(name) or r["candidate_id"].lower(),
            "name": name,
            "party": _party(r.get("party")),
            "incumbent": r.get("incumbent_challenge") == "I",
            "fecCandidateId": r["candidate_id"],
        })
        totals.append({
            "candidate_id": r["candidate_id"],
            "name": name,
            "cycle": 2026,
            "receipts": float(r.get("receipts") or 0.0),
            "disbursements": float(r.get("disbursements") or 0.0),
            "last_cash_on_hand_end_period": float(r.get("last_cash_on_hand_end_period") or 0.0),
            "coverage_end_date": r.get("coverage_end_date"),
        })
    return candidates, totals


def build_senate(state: str, results: list[dict]) -> tuple[dict, list[dict]]:
    """Class-II Senate seat → (race config, finance totals)."""
    candidates, totals = _candidates_and_totals(results)
    config = {
        "kind": "race",
        "id": race_id("senate", state),
        "cycle": 2026,
        "title": f"{state} U.S. Senate 2026",
        "office": "senate",
        "state": state,
        "senateClass": 2,
        "status": "upcoming",
        "sources": ["fec", "forecast"],
        "candidates": candidates,
    }
    return config, totals


def build_house(state: str, district: int, results: list[dict]) -> tuple[dict, list[dict]]:
    """Competitive House district → (race config, finance totals)."""
    candidates, totals = _candidates_and_totals(results)
    config = {
        "kind": "race",
        "id": race_id("house", state, district),
        "cycle": 2026,
        "title": f"{state}-{district:02d} U.S. House 2026",
        "office": "house",
        "state": state,
        "district": district,
        "status": "upcoming",
        "sources": ["fec", "forecast"],
        "candidates": candidates,
    }
    return config, totals


def build_governor(state: str) -> dict:
    """Competitive Governor race → race config. State office: no FEC finance, so no candidates
    and `sources` omits `fec` (forecast + demographics still attach downstream)."""
    return {
        "kind": "race",
        "id": race_id("governor", state),
        "cycle": 2026,
        "title": f"{state} Governor 2026",
        "office": "governor",
        "state": state,
        "status": "upcoming",
        "sources": ["forecast"],
        "candidates": [],
    }


# Backwards-compat alias — some callers/tests referenced the Senate-only builder.
build_state = build_senate


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    states: list[str] | None = None,
    house_districts: list[tuple[str, int]] | None = None,
    gov_states: list[str] | None = None,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
    races_dir: Path = RACES_DIR,
) -> tuple[int, Path]:
    """Write a config per Senate seat, competitive House district, and Governor race, then bake
    the tracked (Senate+House) candidates' totals to gold/fec.

    `states` overrides the Senate set; `house_districts`/`gov_states` override the House/Gov sets
    (pass `[]` to skip an office). Returns (configs written, gold path)."""
    if fetcher is None:
        import requests

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", "fec", root), transport)

    assert fetcher is not None
    key = get_api_key()
    races_dir.mkdir(parents=True, exist_ok=True)
    senate = CLASS_II_2026 if states is None else states
    house = COMPETITIVE_HOUSE_2026 if house_districts is None else house_districts
    governors = COMPETITIVE_GOV_2026 if gov_states is None else gov_states

    all_totals: list[dict] = []
    n = 0

    def _emit(config: dict) -> None:
        nonlocal n
        (races_dir / f"{config['id']}.json").write_text(json.dumps(config, indent=2) + "\n")
        n += 1

    for state in senate:
        results = json.loads(fetcher.get(totals_url("S", state, key))).get("results", [])
        config, totals = build_senate(state, results)
        _emit(config)
        all_totals.extend(totals)

    for state, district in house:
        url = totals_url("H", state, key, district=district)
        results = json.loads(fetcher.get(url)).get("results", [])
        config, totals = build_house(state, district, results)
        _emit(config)
        all_totals.extend(totals)

    for state in governors:
        _emit(build_governor(state))

    gold = bake(FEC_SPEC, FecTotals, all_totals, as_of or datetime.now(timezone.utc), root)
    return n, gold


def main() -> int:
    n, gold = run()
    rows = len(json.loads(gold.read_text())["rows"])
    print(f"generated {n} race configs; baked {rows} finance rows → {gold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
