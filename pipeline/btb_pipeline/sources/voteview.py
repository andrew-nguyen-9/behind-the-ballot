"""Voteview DW-NOMINATE ideology connector [M3a]: per-Congress ideal-point scores,
keyless [T6a], from voteview.com's public members CSV (CC0-ish academic release). One
ideology row per member keyed by bioguide_id, carrying the MOST RECENT congress's
NOMINATE coordinates so the gold artifact reflects a member's current ideology.

Voteview publishes per Congress (event-driven), so the integrity registry [R14a] treats
"voteview" as floor=None — no staleness check. The SPEC floor below only feeds the
artifact's own `fresh` flag.

ponytail: stdlib csv (no pandas) [T6a], transport-injected for fixture tests, dedupe by
keeping the highest `congress` per member.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from btb_pipeline.connector import CachingFetcher, Transport, upsert
from btb_pipeline.core import DATA_ROOT, SourceSpec, bake, stage_dir

SOURCE_URL = "https://voteview.com/static/data/out/members/HSall_members.csv"
SPEC = SourceSpec(name="voteview", cadence="per Congress", freshness_floor_days=400)


class IdeologyRow(BaseModel):
    """One member's most-recent DW-NOMINATE ideal point. Extra Voteview columns ignored."""

    model_config = ConfigDict(extra="ignore")

    bioguide_id: str
    icpsr: str | None = None
    congress: int | None = None
    chamber: str | None = None
    state: str | None = None
    party: str | None = None
    nominate_dim1: float | None = None
    nominate_dim2: float | None = None


def _num(v: str | None) -> float | None:
    if v is None or v.strip() == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _int(v: str | None) -> int | None:
    n = _num(v)
    return int(n) if n is not None else None


def _str(v: str | None) -> str | None:
    if v is None or v.strip() == "":
        return None
    return v.strip()


def parse_members(body: str) -> list[dict]:
    """Parse the Voteview members CSV into validated ideology rows [R7a]. Skips rows with
    no bioguide_id; when a member appears in multiple congresses, keeps the row with the
    highest `congress` (most recent ideology score)."""
    rows: list[dict] = []
    for r in csv.DictReader(io.StringIO(body)):
        bio = (r.get("bioguide_id") or "").strip()
        if not bio:
            continue
        rows.append(
            IdeologyRow.model_validate({
                "bioguide_id": bio,
                "icpsr": _str(r.get("icpsr")),
                "congress": _int(r.get("congress")),
                "chamber": _str(r.get("chamber")),
                "state": _str(r.get("state_abbrev")),
                "party": _str(r.get("party_code")),
                "nominate_dim1": _num(r.get("nominate_dim1")),
                "nominate_dim2": _num(r.get("nominate_dim2")),
            }).model_dump()
        )
    # Sort ascending by congress so the latest congress wins the upsert by bioguide_id.
    rows.sort(key=lambda row: (row["congress"] is not None, row["congress"] or 0))
    return upsert([], rows, "bioguide_id")


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    return json.loads(path.read_text()).get("rows", []) if path.exists() else []


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
) -> Path:
    """Fetch members CSV -> validate -> upsert by bioguide_id [R4a] -> bake gold [R14a]."""
    if fetcher is None:
        import requests

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)

    assert fetcher is not None
    rows = upsert(_existing(root), parse_members(fetcher.get(SOURCE_URL)), "bioguide_id")
    return bake(SPEC, IdeologyRow, rows, as_of or datetime.now(timezone.utc), root)
