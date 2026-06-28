"""Canonical member roster [M1->C]: unitedstates/congress-legislators (keyless, CC0) is
the spine; Congress.gov enrichment (committees etc.) layers on later (env-keyed, v1.6.x).
Weekly, 14d floor [M11a,R5a].

Uses the project's published JSON (no YAML dep). Transport-injected -> fixture-tested.
ponytail: take each legislator's current term for chamber/state/district/party; richer
term history is added only if a feature needs it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from btb_pipeline.connector import CachingFetcher, Transport, upsert
from btb_pipeline.core import DATA_ROOT, SourceSpec, bake, stage_dir

SOURCE_URL = "https://unitedstates.github.io/congress-legislators/legislators-current.json"
SPEC = SourceSpec(name="members", cadence="weekly", freshness_floor_days=14)


class MemberRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bioguide_id: str
    name: str | None = None
    party: str | None = None
    state: str | None = None
    chamber: str | None = None  # "sen" | "rep" (from term type)
    district: int | None = None


def _full_name(name: dict) -> str | None:
    if name.get("official_full"):
        return name["official_full"]
    parts = [name.get("first"), name.get("last")]
    joined = " ".join(p for p in parts if p)
    return joined or None


def parse_legislators(body: str) -> list[dict]:
    """Build one MemberRow per legislator from their current (last) term [R7a]."""
    out: list[dict] = []
    for leg in json.loads(body):
        bio = (leg.get("id") or {}).get("bioguide")
        if not bio:
            continue
        terms = leg.get("terms") or []
        cur = terms[-1] if terms else {}
        district = cur.get("district")
        out.append(
            MemberRow.model_validate({
                "bioguide_id": bio,
                "name": _full_name(leg.get("name") or {}),
                "party": cur.get("party"),
                "state": cur.get("state"),
                "chamber": cur.get("type"),
                "district": int(district) if district is not None else None,
            }).model_dump()
        )
    return out


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    return json.loads(path.read_text()).get("rows", []) if path.exists() else []


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
) -> Path:
    """Fetch roster -> validate -> upsert by bioguide_id [R4a] -> bake gold [R14a]."""
    if fetcher is None:
        import requests

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)

    assert fetcher is not None
    rows = upsert(_existing(root), parse_legislators(fetcher.get(SOURCE_URL)), "bioguide_id")
    return bake(SPEC, MemberRow, rows, as_of or datetime.now(timezone.utc), root)
