"""Sponsorship counts [v1.6.4, M5a]. Per-member sponsored + cosponsored legislation totals via
Congress.gov `/member/{bioguide}/{sponsored,cosponsored}-legislation` (api.data.gov key [T6a]).
Public domain [G14a]. Weekly, 14d floor [R5a].

ponytail: reads the cheap `pagination.count` from each endpoint (1 row of results, the count is
the whole point) — two calls per member. The cross-party cosponsorship INDEX [M7a] needs each
bill's cosponsor parties (a per-bill fan-out) and is a follow-up. Member set defaults to the baked
members artifact's bioguide_ids. ponytail: full live bake is 2×N calls (N≈537) → a cron/rate-
limited job, not a hot path. Transport-injected → fixture-tested.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from pydantic import BaseModel, ConfigDict

from btb_pipeline.connector import CachingFetcher, Transport, upsert
from btb_pipeline.core import DATA_ROOT, SourceSpec, bake, stage_dir

API_ROOT = "https://api.congress.gov/v3"
SPEC = SourceSpec(name="sponsorship", cadence="weekly", freshness_floor_days=14)


class SponsorshipRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bioguide_id: str
    sponsored_count: int = 0
    cosponsored_count: int = 0


def get_api_key() -> str:
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        raise RuntimeError("DATA_GOV_API_KEY not set — see docs/SETUP_SECRETS.md")
    return key


def _legislation_url(bioguide_id: str, kind: str, api_key: str) -> str:
    # kind: "sponsored" | "cosponsored"
    params = urlencode({"format": "json", "limit": 1, "api_key": api_key})
    return f"{API_ROOT}/member/{bioguide_id}/{kind}-legislation?{params}"


def parse_count(body: str) -> int:
    """Congress.gov returns the total in pagination.count [R7a]."""
    return int(json.loads(body).get("pagination", {}).get("count", 0))


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    return json.loads(path.read_text()).get("rows", []) if path.exists() else []


def _bioguide_ids_from_members(root: Path) -> list[str]:
    path = stage_dir("gold", "members", root) / "members.json"
    if not path.exists():
        return []
    return [r["bioguide_id"] for r in json.loads(path.read_text()).get("rows", []) if r.get("bioguide_id")]


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    bioguide_ids: list[str] | None = None,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
) -> Path:
    """For each member -> count sponsored + cosponsored -> upsert by bioguide_id -> bake gold."""
    if fetcher is None:
        import requests  # local import: only needed for live runs

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)

    assert fetcher is not None
    key = get_api_key()
    ids = bioguide_ids if bioguide_ids is not None else _bioguide_ids_from_members(root)
    incoming = [
        SponsorshipRow.model_validate({
            "bioguide_id": bid,
            "sponsored_count": parse_count(fetcher.get(_legislation_url(bid, "sponsored", key))),
            "cosponsored_count": parse_count(fetcher.get(_legislation_url(bid, "cosponsored", key))),
        }).model_dump()
        for bid in ids
    ]
    rows = upsert(_existing(root), incoming, "bioguide_id")
    return bake(SPEC, SponsorshipRow, rows, as_of or datetime.now(timezone.utc), root)
