"""Roll-call votes connector [v1.6.2, M2a]. Congress.gov House roll-call list via the
api.data.gov key [T6a] (verified iter 63: the data.gov key authenticates Congress.gov,
unlike Census). Public domain [G14a]. Daily in session, 7d floor [R5a].

ponytail: bakes the vote-LEVEL list (number/result/bill/date) — the headline "key votes"
feed. Per-member positions (missed-votes, the v1.6.4 cross-party index) are a second
endpoint (/house-vote/{c}/{s}/{n}/members) added when that feature lands. Senate roll calls
aren't in the Congress.gov API → a GovTrack/senate.gov slice is a follow-up. Transport-injected
→ fully fixture-tested, goes live the moment the key exists.
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
SPEC = SourceSpec(name="rollcall", cadence="daily", freshness_floor_days=7)


class HouseRollCall(BaseModel):
    """One House roll-call vote. Extra Congress.gov fields ignored."""

    model_config = ConfigDict(extra="ignore")

    identifier: int  # unique per vote → upsert key
    congress: int
    session_number: int
    roll_call_number: int
    result: str | None = None
    vote_type: str | None = None
    legislation_type: str | None = None
    legislation_number: str | None = None
    legislation_url: str | None = None
    start_date: str | None = None
    url: str | None = None


def get_api_key() -> str:
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        raise RuntimeError("DATA_GOV_API_KEY not set — see docs/SETUP_SECRETS.md")
    return key


def votes_url(congress: int, session: int, api_key: str, limit: int = 250, offset: int = 0) -> str:
    params = urlencode({"format": "json", "limit": limit, "offset": offset, "api_key": api_key})
    return f"{API_ROOT}/house-vote/{congress}/{session}?{params}"


def parse_votes(body: str) -> list[dict]:
    """Map Congress.gov camelCase records to validated snake_case rows [R7a]."""
    out: list[dict] = []
    for v in json.loads(body).get("houseRollCallVotes", []):
        out.append(
            HouseRollCall.model_validate({
                "identifier": v["identifier"],
                "congress": v["congress"],
                "session_number": v.get("sessionNumber"),
                "roll_call_number": v.get("rollCallNumber"),
                "result": v.get("result"),
                "vote_type": v.get("voteType"),
                "legislation_type": v.get("legislationType"),
                "legislation_number": v.get("legislationNumber"),
                "legislation_url": v.get("legislationUrl"),
                "start_date": v.get("startDate"),
                "url": v.get("url"),
            }).model_dump()
        )
    return out


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    return json.loads(path.read_text()).get("rows", []) if path.exists() else []


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    congress: int = 119,
    sessions: tuple[int, ...] = (1, 2),
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
) -> Path:
    """Fetch House roll-call list -> validate -> upsert by identifier [R4a] -> bake gold [R14a]."""
    if fetcher is None:
        import requests  # local import: only needed for live runs

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)

    assert fetcher is not None
    key = get_api_key()
    rows = _existing(root)
    for session in sessions:
        rows = upsert(rows, parse_votes(fetcher.get(votes_url(congress, session, key))), "identifier")
    return bake(SPEC, HouseRollCall, rows, as_of or datetime.now(timezone.utc), root)
