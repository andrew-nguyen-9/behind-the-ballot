"""Data-integrity gate [R14a]: every published figure traces to a DATA_SOURCES.md row
and meets its freshness floor [R5a]. Two guards:

  1. check_doc_sync  — every source in the code registry is named in 03_DATA_SOURCES.md,
     so code can't silently drift from the contract.
  2. assert_artifact — a baked artifact's source is registered and (if a floor applies)
     fresh; raises IntegrityError otherwise. Connectors call this before publish.

Run: uv run --project pipeline python -m btb_pipeline.integrity
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Repo root = two levels up from this file (pipeline/btb_pipeline/integrity.py).
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_SOURCES_MD = REPO_ROOT / "docs" / "03_DATA_SOURCES.md"


class IntegrityError(Exception):
    pass


@dataclass(frozen=True)
class Source:
    floor_days: int | None  # None = event-driven / no max-age (TIGER, Voteview, geocoder)
    doc_token: str  # a string guaranteed to appear in DATA_SOURCES.md


# Registry — one entry per DATA_SOURCES.md row that backs a published figure [R14a].
# Floors mirror the "Freshness floor" column [R5a]. Internal fixtures (e.g. the ETL
# `sample`) are intentionally absent: they are not published figures.
SOURCES: dict[str, Source] = {
    "fec": Source(14, "OpenFEC"),
    "polls_538": Source(3, "538 polls CSV"),
    "pollster_ratings": Source(30, "pollster ratings"),
    "census_acs": Source(400, "Census ACS"),
    "members": Source(14, "congress-legislators"),
    "committees": Source(30, "Committees & leadership"),
    "rollcall": Source(7, "Roll-call votes"),
    "voteview": Source(None, "Voteview"),
    "tiger": Source(None, "TIGER/Line"),
    "geocoder": Source(None, "Geocoder"),
}


def check_doc_sync(md_path: Path = DATA_SOURCES_MD) -> None:
    """Fail if any registered source is not named in DATA_SOURCES.md [R14a]."""
    text = md_path.read_text(encoding="utf-8")
    missing = [k for k, s in SOURCES.items() if s.doc_token not in text]
    if missing:
        raise IntegrityError(
            f"sources not found in {md_path.name}: "
            + ", ".join(f"{k} (token {SOURCES[k].doc_token!r})" for k in missing)
        )


def assert_artifact(artifact: dict, now: datetime | None = None) -> None:
    """Validate a published artifact: known source + within freshness floor [R14a,R5a]."""
    source = artifact.get("source")
    if source not in SOURCES:
        raise IntegrityError(f"unregistered source {source!r} — add a DATA_SOURCES.md row")
    floor = SOURCES[source].floor_days
    if floor is None:
        return
    raw = artifact.get("as_of")
    if not raw:
        raise IntegrityError(f"source {source!r} artifact missing as_of")
    as_of = datetime.fromisoformat(raw)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    if (now - as_of).days > floor:
        raise IntegrityError(
            f"source {source!r} stale: as_of {as_of.date()} older than {floor}d floor"
        )


def scan_gold(gold_dir: Path) -> int:
    """Assert every gold artifact under a published source dir. Returns count checked.
    Skips sources not in the registry (internal fixtures)."""
    if not gold_dir.exists():
        return 0
    checked = 0
    for path in gold_dir.glob("*/*.json"):
        artifact = json.loads(path.read_text(encoding="utf-8"))
        if artifact.get("source") not in SOURCES:
            continue
        assert_artifact(artifact)
        checked += 1
    return checked


def main() -> int:
    check_doc_sync()
    n = scan_gold(REPO_ROOT / "data" / "gold")
    print(f"integrity ok: {len(SOURCES)} sources in sync with DATA_SOURCES.md, {n} artifacts checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
