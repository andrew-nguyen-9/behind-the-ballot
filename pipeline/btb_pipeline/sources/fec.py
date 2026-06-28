"""FEC campaign-finance connector [G1a]. OpenFEC API via api.data.gov key [T6a], weekly,
14d freshness floor [G3a,R5a]. Public domain [G14a].

Env-keyed (`DATA_GOV_API_KEY`) and transport-injected, so it's fully fixture-tested with
no live calls; it goes live the moment the secret exists. ponytail: pulls candidate
totals (receipts/disbursements/cash-on-hand) — the headline finance figures; itemized
filings are an R2/bulk job added later (v1.3.3).
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
SPEC = SourceSpec(name="fec", cadence="weekly", freshness_floor_days=14)


class FecTotals(BaseModel):
    """One candidate's cycle totals from /candidates/totals/. Extra OpenFEC fields ignored."""

    model_config = ConfigDict(extra="ignore")

    candidate_id: str
    name: str | None = None
    cycle: int
    receipts: float = 0.0
    disbursements: float = 0.0
    last_cash_on_hand_end_period: float = 0.0
    coverage_end_date: str | None = None  # "through <date>" display [G13a]


def get_api_key() -> str:
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        raise RuntimeError("DATA_GOV_API_KEY not set — see docs/ACCOUNTS.md provisioning")
    return key


def totals_url(cycle: int, office: str, api_key: str, page: int = 1) -> str:
    params = urlencode({
        "api_key": api_key,
        "cycle": cycle,
        "office": office,  # "S" senate, "H" house, "P" president
        "per_page": 100,
        "page": page,
    })
    return f"{API_ROOT}/candidates/totals/?{params}"


def parse_totals(body: str) -> list[dict]:
    """Validate every record [R7a]; return clean dicts keyed-ready for upsert."""
    results = json.loads(body).get("results", [])
    return [FecTotals.model_validate(r).model_dump() for r in results]


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text()).get("rows", [])


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    cycle: int = 2026,
    offices: tuple[str, ...] = ("S", "H"),
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
) -> Path:
    """Fetch -> validate -> upsert by candidate_id [R4a] -> bake gold [R14a]."""
    if fetcher is None:
        import requests  # local import: only needed for live runs

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)

    assert fetcher is not None
    key = get_api_key()
    rows = _existing(root)
    for office in offices:
        incoming = parse_totals(fetcher.get(totals_url(cycle, office, key)))
        rows = upsert(rows, incoming, "candidate_id")

    return bake(SPEC, FecTotals, rows, as_of or datetime.now(timezone.utc), root)
