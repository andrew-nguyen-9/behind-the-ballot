"""MEDSL 2024 state-level presidential results connector [N3a] — the partisan-lean baseline that
feeds the forecast's fundamentals (PVI). Source: MIT Election Data + Science Lab, repo
`2024-elections-official/2024-president-state.csv` (GitHub raw, CC-BY [decision iter 79]). Keyless,
no guestbook. Election returns are static historical facts → event-driven freshness (no max-age).

Per state we keep the two-party totals (Democrat, Republican); the forecast export derives the
two-party Dem share and the Cook-PVI-style lean vs the national share (`baseline.cook_pvi`).
ponytail: transport returns the CSV text (injectable → fixture-tested, no network). One file, one
bake. House district results (for gerrymander fairness) are a separate follow-up connector.
"""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from btb_pipeline.core import DATA_ROOT, SourceSpec, bake

SPEC = SourceSpec(name="medsl_president", cadence="event", freshness_floor_days=2000)
SOURCE_URL = "https://raw.githubusercontent.com/MEDSL/2024-elections-official/main/2024-president-state.csv"
ELECTION_YEAR = 2024


class PresidentStateRow(BaseModel):
    """One state's two-party 2024 presidential totals. Extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    state: str  # USPS postal, e.g. "TX"
    dem_votes: int
    rep_votes: int


def parse_president(csv_text: str) -> list[dict]:
    """Aggregate the MEDSL per-candidate rows into per-state D/R two-party totals.

    Sums `votes` by (state_po, party_simplified) over the TOTAL mode rows (the standardized
    state aggregate; filtering avoids double-counting per-mode breakdowns). Returns one row per
    state that has both a Democrat and a Republican total, sorted by state."""
    dem: dict[str, int] = defaultdict(int)
    rep: dict[str, int] = defaultdict(int)
    for r in csv.DictReader(io.StringIO(csv_text)):
        if (r.get("mode") or "").upper() != "TOTAL":
            continue
        st = r.get("state_po")
        if not st:
            continue
        party = (r.get("party_simplified") or "").upper()
        try:
            votes = int(r.get("votes") or 0)
        except ValueError:
            continue
        if party == "DEMOCRAT":
            dem[st] += votes
        elif party == "REPUBLICAN":
            rep[st] += votes
    rows = [
        {"state": st, "dem_votes": dem[st], "rep_votes": rep[st]}
        for st in sorted(set(dem) & set(rep))
    ]
    return rows


def run(transport=None, as_of: datetime | None = None, root: Path = DATA_ROOT) -> Path:
    """Fetch -> aggregate -> bake gold `medsl_president` [R14a]. transport(url)->text injectable."""
    if transport is None:
        import requests  # local import: only needed for live runs

        transport = lambda url: requests.get(url, timeout=30).text  # noqa: E731
    rows = parse_president(transport(SOURCE_URL))
    return bake(SPEC, PresidentStateRow, rows, as_of or datetime.now(timezone.utc), root)
