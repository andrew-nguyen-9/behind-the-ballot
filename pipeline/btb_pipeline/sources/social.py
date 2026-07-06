"""Curated social connector [E-6] — official candidate/incumbent social profiles.

Like the election-calendar connector [E2.1], this is a small HAND-CURATED table, NOT an API
pull: a committed JSON (`social.json`) of official handles → profile link + (optional) latest-post
link/timestamp. `run()` validates it and bakes gold so it flows through the exact same integrity +
export path as every other source [R14a]. **Curated/static only** — no platform API, no runtime
JS, no tracking, no live embeds (spec invariant).

HONEST-EMPTY [E-6]: a handle that is not yet verified is committed with `handle: null` (and null
links). A null handle is a legitimate row — the UI renders it as honest-empty, never a fabricated
link. Until real handles are curated, `social.json` is an empty list and the social block is empty.

Social links are event-driven facts (a handle changes rarely), so freshness is event-driven; the
integrity registry marks it floor=None [see integrity.py], mirroring election_dates.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

from btb_pipeline.core import DATA_ROOT, SourceSpec, bake

SPEC = SourceSpec(name="social", cadence="event", freshness_floor_days=2000)
CURATED = Path(__file__).with_name("social.json")


class SocialProfileRow(BaseModel):
    """One (entity, platform) official profile. `handle` null → honest-empty (unverified/absent):
    the links must then be null too (no fabricated link). Extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    entity_id: str  # natural key: bioguide / candidate id / race-candidate slug
    entity_name: str
    role: str  # "candidate" | "incumbent" | ...
    state: str  # USPS postal, e.g. "AZ"
    platform: str | None = None  # "x" | "instagram" | ... (null when no handle at all)
    handle: str | None = None  # null → honest-empty
    profile_url: str | None = None
    latest_post_url: str | None = None
    latest_post_at: str | None = None  # ISO-8601 timestamp

    @field_validator("latest_post_at")
    @classmethod
    def _iso_ts(cls, v: str | None) -> str | None:
        if v is not None:
            datetime.fromisoformat(v)  # raises ValueError on a malformed timestamp
        return v

    @field_validator("profile_url", "latest_post_url", "latest_post_at")
    @classmethod
    def _no_link_without_handle(cls, v: str | None, info) -> str | None:
        # Honest-empty invariant: a link/timestamp requires a verified handle [E-6].
        if v is not None and not info.data.get("handle"):
            raise ValueError(f"{info.field_name} set but handle is null (honest-empty violated)")
        return v


def load_curated(path: Path = CURATED) -> list[dict]:
    """Read the committed curated handle list (injectable for tests). Empty list = honest-empty."""
    return json.loads(path.read_text(encoding="utf-8"))


def run(rows: list[dict] | None = None, as_of: datetime | None = None, root: Path = DATA_ROOT) -> Path:
    """Validate the curated social list -> bake gold `social` [R14a]. Empty is valid (honest-empty)."""
    rows = load_curated() if rows is None else rows
    return bake(SPEC, SocialProfileRow, rows, as_of or datetime.now(timezone.utc), root)
