"""Generate real Senate 2026 race configs + finance gold from FEC [content curation; user
decision iter 69: auto Senate + House key races — this is the Senate slice]. For each of the 33
Class-II 2026 seats, pull real candidates from FEC `/candidates/totals/` (top by receipts), write
`apps/web/src/config/races/us-senate-2026-XX.json`, and bake the tracked candidates' totals to
gold/fec so the finance export reads real, freshness-traceable numbers.

    DATA_GOV_API_KEY=… uv run --project pipeline python -m btb_pipeline.generate_races

ponytail: editorial rule = "FEC-registered, top TOP_N by receipts above MIN_RECEIPTS". No human
candidate list to maintain; re-running refreshes against FEC. House key races are a follow-up.
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

PARTY = {"DEM": "D", "DFL": "D", "REP": "R", "IND": "I", "LIB": "L", "GRE": "G"}
HONORIFICS = {"SEN", "REP", "DR", "MR", "MRS", "MS", "HON", "JR", "SR", "II", "III", "IV", "V"}

MIN_RECEIPTS = 50_000.0  # drop negligible/paper filers
TOP_N = 6


def get_api_key() -> str:
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        raise RuntimeError("DATA_GOV_API_KEY not set — see docs/SETUP_SECRETS.md")
    return key


def totals_url(state: str, api_key: str, per_page: int = 20) -> str:
    params = urlencode({
        "api_key": api_key, "cycle": 2026, "office": "S", "state": state,
        "sort": "-receipts", "per_page": per_page,
    })
    return f"{API_ROOT}/candidates/totals/?{params}"


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


def build_state(state: str, results: list[dict]) -> tuple[dict, list[dict]]:
    """Top-N real candidates for a state → (race config dict, finance totals rows)."""
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
    config = {
        "kind": "race",
        "id": f"us-senate-2026-{state}",
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


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    states: list[str] | None = None,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
    races_dir: Path = RACES_DIR,
) -> tuple[int, Path]:
    """Write a config per state + bake the tracked candidates' totals to gold/fec."""
    if fetcher is None:
        import requests

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", "fec", root), transport)

    assert fetcher is not None
    key = get_api_key()
    races_dir.mkdir(parents=True, exist_ok=True)
    all_totals: list[dict] = []
    n = 0
    for state in (states or CLASS_II_2026):
        results = json.loads(fetcher.get(totals_url(state, key))).get("results", [])
        config, totals = build_state(state, results)
        (races_dir / f"{config['id']}.json").write_text(json.dumps(config, indent=2) + "\n")
        all_totals.extend(totals)
        n += 1
    gold = bake(FEC_SPEC, FecTotals, all_totals, as_of or datetime.now(timezone.utc), root)
    return n, gold


def main() -> int:
    n, gold = run()
    print(f"generated {n} Senate race configs; baked {len(json.loads(gold.read_text())['rows'])} finance rows → {gold}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
