"""Candidate→committee linkage [v1.3.2, G12a]. Each candidate's PRINCIPAL campaign committee
(FEC designation "P") via OpenFEC `/candidate/{id}/committees/` (api.data.gov key [T6a]). Public
domain [G14a]. Weekly, 14d floor [R5a]. This is the join that ties FEC finance to a candidate
identity (feeds the v1.6.5 finance crosslink).

ponytail: one principal committee per candidate — the linkage [G12a] needs. Authorized/joint
committees (designation A/J/U) are ignored for V1. Candidate set defaults to the baked FEC totals
artifact's candidate_ids; pass an explicit list to scope a smaller bake. Transport-injected →
fixture-tested.
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

API_ROOT = "https://api.open.fec.gov/v1"
SPEC = SourceSpec(name="committee_link", cadence="weekly", freshness_floor_days=14)


class CommitteeLink(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: str
    committee_id: str
    committee_name: str | None = None


def get_api_key() -> str:
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        raise RuntimeError("DATA_GOV_API_KEY not set — see docs/SETUP_SECRETS.md")
    return key


def committees_url(candidate_id: str, api_key: str) -> str:
    params = urlencode({"api_key": api_key, "per_page": 100})
    return f"{API_ROOT}/candidate/{candidate_id}/committees/?{params}"


def parse_principal(body: str, candidate_id: str) -> dict | None:
    """Pick the candidate's principal campaign committee (designation 'P') [G12a]."""
    for c in json.loads(body).get("results", []):
        if c.get("designation") == "P" and candidate_id in (c.get("candidate_ids") or []):
            return CommitteeLink.model_validate({
                "candidate_id": candidate_id,
                "committee_id": c["committee_id"],
                "committee_name": c.get("name"),
            }).model_dump()
    return None


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    return json.loads(path.read_text()).get("rows", []) if path.exists() else []


def _candidate_ids_from_fec(root: Path) -> list[str]:
    path = stage_dir("gold", "fec", root) / "fec.json"
    if not path.exists():
        return []
    return [r["candidate_id"] for r in json.loads(path.read_text()).get("rows", []) if r.get("candidate_id")]


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    candidate_ids: list[str] | None = None,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
) -> Path:
    """For each candidate -> fetch committees -> keep principal -> upsert by candidate_id -> bake."""
    if fetcher is None:
        import requests  # local import: only needed for live runs

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)

    assert fetcher is not None
    key = get_api_key()
    ids = candidate_ids if candidate_ids is not None else _candidate_ids_from_fec(root)
    incoming = [link for cid in ids if (link := parse_principal(fetcher.get(committees_url(cid, key)), cid))]
    rows = upsert(_existing(root), incoming, "candidate_id")
    return bake(SPEC, CommitteeLink, rows, as_of or datetime.now(timezone.utc), root)
