"""Election-calendar connector [E2.1] — per-state 2026 primary / runoff / general dates.

Unlike the API-backed connectors, the election calendar is a small HAND-CURATED table (state
election authorities, aggregated by NCSL's "2026 State Primary Election Dates"). It ships as a
committed JSON next to this module (`election_dates.json`); `run()` validates it and bakes gold so
it flows through the exact same integrity + export path as every other source [R14a].

Rows are partitioned by `cycle`, so a future cycle is added by appending rows — no code change.
Election dates are legislatively fixed scheduled facts, so freshness is event-driven (re-baked only
when a state moves its calendar); the integrity registry marks it floor=None [see integrity.py].
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

from btb_pipeline.core import DATA_ROOT, SourceSpec, bake

SPEC = SourceSpec(name="election_dates", cadence="event", freshness_floor_days=2000)
CURATED = Path(__file__).with_name("election_dates.json")


class ElectionDateRow(BaseModel):
    """One state's dates for a cycle. `runoff`/`note` are nullable. Extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    cycle: int
    state: str  # USPS postal, e.g. "TX"
    state_name: str
    primary: str  # ISO date (YYYY-MM-DD)
    runoff: str | None = None
    general: str  # ISO date
    note: str | None = None

    @field_validator("primary", "general")
    @classmethod
    def _iso_date(cls, v: str) -> str:
        datetime.strptime(v, "%Y-%m-%d")  # raises ValueError on a malformed date
        return v

    @field_validator("runoff")
    @classmethod
    def _iso_date_optional(cls, v: str | None) -> str | None:
        if v is not None:
            datetime.strptime(v, "%Y-%m-%d")
        return v


def load_curated(path: Path = CURATED) -> list[dict]:
    """Read the committed curated calendar (injectable for tests)."""
    return json.loads(path.read_text(encoding="utf-8"))


def run(rows: list[dict] | None = None, as_of: datetime | None = None, root: Path = DATA_ROOT) -> Path:
    """Validate the curated calendar -> bake gold `election_dates` [R14a]."""
    rows = load_curated() if rows is None else rows
    return bake(SPEC, ElectionDateRow, rows, as_of or datetime.now(timezone.utc), root)
