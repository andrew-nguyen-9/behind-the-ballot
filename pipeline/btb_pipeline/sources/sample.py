"""A trivial sample source proving the bronze->silver->gold flow end to end.

Real connectors (FEC, 538, ACS, ...) replace `fetch_raw` with cached HTTP + their own
record model, reusing core.bake / dry_run. ponytail: hardcoded rows here, no network.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from btb_pipeline.core import SourceSpec

SPEC = SourceSpec(name="sample", cadence="weekly", freshness_floor_days=14)


class SampleRow(BaseModel):
    state: str = Field(pattern=r"^[A-Z]{2}$")
    value: int = Field(ge=0)


def fetch_raw() -> list[dict]:
    return [{"state": "OH", "value": 1}, {"state": "PA", "value": 2}]


def as_of() -> datetime:
    return datetime.now(timezone.utc)
