"""Pollster-ratings connector [H6a]: 538 pollster ratings CSV used as poll weights,
keyless [T6a], weekly, 30d freshness floor [R5a]. Raw mirrored to bronze cache so a dead
upstream keeps last-good [R8a] — 538's ratings CSV may move/freeze post-ABC.

538's ratings columns vary across vintages, so parsing is robust to column-name variants
[R7a]. We store grade fields raw (no inversion of pollscore) [R4a]; weighting math lives in
v1.4.3. ponytail: stdlib csv (no pandas), transport-injected for fixture tests [T6a].
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

CSV_URL = "https://projects.fivethirtyeight.com/polls/data/pollster-ratings.csv"
SPEC = SourceSpec(name="pollster_ratings", cadence="weekly", freshness_floor_days=30)


class RatingRow(BaseModel):
    """One 538 rating per pollster. Extra 538 columns ignored."""

    model_config = ConfigDict(extra="ignore")

    pollster: str
    grade: str | None = None
    numeric_grade: float | None = None
    pollscore: float | None = None


def _num(v: str | None) -> float | None:
    if v is None or v.strip() == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _first(r: dict, *names: str) -> str | None:
    """First non-empty value among column-name variants (538 columns drift over time)."""
    for name in names:
        v = r.get(name)
        if v is not None and v.strip() != "":
            return v
    return None


def parse_ratings(body: str) -> list[dict]:
    """Parse a 538 pollster-ratings CSV body into validated rows [R7a]. Robust to column-
    name variants; skips rows with no pollster name; dedupes by pollster (last wins) [R4a]."""
    rows: list[dict] = []
    for r in csv.DictReader(io.StringIO(body)):
        name = _first(r, "pollster", "pollster_rating_name", "Pollster")
        if name is None:
            continue
        row = RatingRow.model_validate({
            "pollster": name.strip(),
            "grade": _first(r, "grade", "538_grade", "pollster_rating"),
            "numeric_grade": _num(_first(r, "numeric_grade", "538_grade_numeric", "pollscore")),
            "pollscore": _num(r.get("pollscore")),
        })
        rows.append(row.model_dump())
    return upsert([], rows, "pollster")


def _existing(root: Path) -> list[dict]:
    path = stage_dir("gold", SPEC.name, root) / f"{SPEC.name}.json"
    return json.loads(path.read_text()).get("rows", []) if path.exists() else []


def run(
    fetcher: CachingFetcher | None = None,
    transport: Transport | None = None,
    as_of: datetime | None = None,
    root: Path = DATA_ROOT,
) -> Path:
    """Fetch CSV -> parse/validate -> upsert by pollster [R4a] -> bake gold [R14a]."""
    if fetcher is None:
        import requests

        transport = transport or (lambda url, headers: requests.get(url, headers=headers, timeout=30))
        fetcher = CachingFetcher(stage_dir("bronze", SPEC.name, root), transport)

    assert fetcher is not None
    rows = upsert(_existing(root), parse_ratings(fetcher.get(CSV_URL)), "pollster")
    return bake(SPEC, RatingRow, rows, as_of or datetime.now(timezone.utc), root)
