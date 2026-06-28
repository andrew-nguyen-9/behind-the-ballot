"""Census ACS 5-year demographics connector [I2a]. Census API via api.data.gov key [I2a],
yearly, 400d freshness floor [R5a]. Pre-aggregated static per-district figures [I7a].

Env-keyed (`DATA_GOV_API_KEY`) and transport-injected, so it's fully fixture-tested with
no live calls; it goes live the moment the secret exists. The Census API returns a list of
arrays — first row is headers, each subsequent row aligns to them [R7a]. ponytail: pulls a
small fixed variable set (population, median household income) per congressional district;
richer tables are added only when a feature needs them. Upsert by geoid [R4a]; integrity
gate before publish [R14a].
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

SPEC = SourceSpec(name="census_acs", cadence="yearly", freshness_floor_days=400)

# Fixed variable set: total population, median household income.
VARIABLES = ("B01001_001E", "B19013_001E")
NULL_SENTINEL = "-666666666"  # Census "no data" marker


class AcsRow(BaseModel):
    """One congressional district's ACS figures. Extra Census fields ignored."""

    model_config = ConfigDict(extra="ignore")

    geoid: str  # state FIPS + district, e.g. "3903"
    name: str | None = None
    state: str | None = None
    district: str | None = None
    population: int | None = None
    median_income: int | None = None


def get_api_key() -> str:
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        raise RuntimeError("DATA_GOV_API_KEY not set — see docs/ACCOUNTS.md provisioning")
    return key


def acs_url(year: int, api_key: str) -> str:
    params = urlencode({
        "get": "NAME," + ",".join(VARIABLES),
        "for": "congressional district:*",
        "in": "state:*",
        "key": api_key,
    })
    return f"https://api.census.gov/data/{year}/acs/acs5?{params}"


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value or value == NULL_SENTINEL:
        return None
    return int(value)


def parse_acs(body: str) -> list[dict]:
    """Zip the header row onto each value row, then validate [R7a]. The Census API returns
    a list of arrays: rows[0] is column headers, the rest are aligned values."""
    table = json.loads(body)
    if not table:
        return []
    headers = table[0]
    out: list[dict] = []
    for values in table[1:]:
        record = dict(zip(headers, values))
        state = record.get("state")
        district = record.get("congressional district")
        out.append(
            AcsRow.model_validate({
                "geoid": f"{state}{district}",
                "name": record.get("NAME"),
                "state": state,
                "district": district,
                "population": _to_int(record.get("B01001_001E")),
                "median_income": _to_int(record.get("B19013_001E")),
            }).model_dump()
        )
    return out


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    return json.loads(path.read_text()).get("rows", []) if path.exists() else []


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    year: int = 2022,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
) -> Path:
    """Fetch -> validate -> upsert by geoid [R4a] -> bake gold [R14a]."""
    if fetcher is None:
        import requests  # local import: only needed for live runs

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)

    assert fetcher is not None
    key = get_api_key()
    incoming = parse_acs(fetcher.get(acs_url(year, key)))
    rows = upsert(_existing(root), incoming, "geoid")
    return bake(SPEC, AcsRow, rows, as_of or datetime.now(timezone.utc), root)
