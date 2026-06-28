"""ETL skeleton: bronze->silver->gold, pydantic validation, freshness, bake [O12a,R5a,R7a].

The real per-source connector framework is v1.1.1; this is the shared spine every
connector reuses. ponytail: minimal but runnable — a SourceSpec, a validating bake, a
freshness floor, and a dry-run. Expand (cache/backoff/upsert) in v1.1.1.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, Field

# Bulk/raw lives under data/ (gitignored); gold is baked then pushed to CDN/R2 [O4d,O6a].
DATA_ROOT = Path("data")
STAGES = ("bronze", "silver", "gold")


class SourceSpec(BaseModel):
    """A data source declared in DATA_SOURCES.md [R14a]."""

    name: str = Field(min_length=1)
    cadence: str = Field(min_length=1)  # human label, e.g. "weekly"
    freshness_floor_days: int = Field(gt=0)  # max age before stale [R5a]


def stage_dir(stage: str, source: str, root: Path = DATA_ROOT) -> Path:
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; expected one of {STAGES}")
    return root / stage / source


def is_fresh(as_of: datetime, floor_days: int, now: datetime | None = None) -> bool:
    """True if `as_of` is within the freshness floor [R5a]. Stale -> caller keeps
    last-good + alerts [R8a]."""
    now = now or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    return (now - as_of).days <= floor_days


def validate_records(model: type[BaseModel], raw: Sequence[dict]) -> list[BaseModel]:
    """Validate every ingested record [R7a]. Raises pydantic ValidationError on a bad row."""
    return [model.model_validate(r) for r in raw]


def dry_run(model: type[BaseModel], raw: Sequence[dict]) -> int:
    """Smoke-validate sources + schema without writing [R6a]. Returns valid row count."""
    return len(validate_records(model, raw))


def bake(
    spec: SourceSpec,
    model: type[BaseModel],
    raw: Sequence[dict],
    as_of: datetime,
    root: Path = DATA_ROOT,
) -> Path:
    """Validate -> write gold artifact + manifest (with as_of) [R7a,R14a]. Idempotent:
    overwrites the same path (natural-key upsert is added per-source in v1.1.1 [R4a])."""
    records = validate_records(model, raw)
    out_dir = stage_dir("gold", spec.name, root)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{spec.name}.json"
    payload = {
        "source": spec.name,
        "as_of": as_of.astimezone(timezone.utc).isoformat(),
        "fresh": is_fresh(as_of, spec.freshness_floor_days),
        "rows": [r.model_dump(mode="json") for r in records],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path
