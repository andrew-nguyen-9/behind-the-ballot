"""Polling connector [H1a]: 538 polls CSV, keyless [T6a], daily, 3d freshness floor
[R5a]. Raw mirrored to bronze cache so a dead upstream keeps last-good [R8a] — 538's CSV
may move/freeze post-ABC (flagged in DATA_SOURCES.md open questions).

ponytail: stdlib csv (no pandas needed to parse), transport-injected for fixture tests.
Aggregation/weighting is v1.4.3; this connector just lands clean per-poll rows.
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

CSV_ROOT = "https://projects.fivethirtyeight.com/polls/data"
DEFAULT_FILES = ("senate_polls.csv", "house_polls.csv", "governor_polls.csv")
SPEC = SourceSpec(name="polls_538", cadence="daily", freshness_floor_days=3)


class PollRow(BaseModel):
    """One pollster reading for one candidate in one poll. Extra 538 columns ignored."""

    model_config = ConfigDict(extra="ignore")

    key: str  # natural key: "<poll_id>:<candidate_name>"
    poll_id: str
    pollster: str | None = None
    state: str | None = None
    end_date: str | None = None
    candidate_name: str | None = None
    party: str | None = None
    pct: float | None = None


def _num(v: str | None) -> float | None:
    if v is None or v.strip() == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def parse_csv(body: str) -> list[dict]:
    """Parse a 538 polls CSV body into validated rows [R7a]. Skips rows with no poll id."""
    out: list[dict] = []
    for r in csv.DictReader(io.StringIO(body)):
        poll_id = (r.get("poll_id") or r.get("question_id") or "").strip()
        if not poll_id:
            continue
        candidate = (r.get("candidate_name") or "").strip()
        row = PollRow.model_validate({
            "key": f"{poll_id}:{candidate}",
            "poll_id": poll_id,
            "pollster": r.get("pollster"),
            "state": r.get("state"),
            "end_date": r.get("end_date"),
            "candidate_name": candidate or None,
            "party": r.get("party"),
            "pct": _num(r.get("pct")),
        })
        out.append(row.model_dump())
    return out


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    return json.loads(path.read_text()).get("rows", []) if path.exists() else []


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    files: tuple[str, ...] = DEFAULT_FILES,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
) -> Path:
    """Fetch each CSV -> parse/validate -> upsert by key [R4a] -> bake gold [R14a]."""
    if fetcher is None:
        import requests

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)

    assert fetcher is not None
    rows = _existing(root)
    for name in files:
        rows = upsert(rows, parse_csv(fetcher.get(f"{CSV_ROOT}/{name}")), "key")

    return bake(SPEC, PollRow, rows, as_of or datetime.now(timezone.utc), root)
