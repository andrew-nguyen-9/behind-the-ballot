"""Polling aggregation [H?a]: a weighted polling average per race, pure-math and keyless.

Consumes PollRow shapes from the polls connector [H1a] (poll_id, state, end_date,
candidate_name, party, pct) and optional pollster weights derived from pollster ratings
[H6a] (e.g. numeric_grade normalized to a positive multiplier by the caller). Produces one
AggregateRow per (state, party). This average is an INPUT to the forecast [N2a]; records are
validated into pydantic models before reporting [R7a].

HEURISTIC (v1 — published methodology per [N12a], explainable, refine later):
Each poll contributes pct to a WEIGHTED MEAN where its weight is

    weight = recency_weight(days_old) * pollster_weight(pollster)

- recency_weight: exponential decay with a 30-day half-life — a poll loses half its weight
  every 30 days (0.5 ** (days_old / half_life_days)). A poll taken on as_of has weight 1.0.
- pollster_weight: caller-supplied multiplier per pollster (missing -> neutral 1.0). Rows from
  the polls connector carry no 'pollster' field by default, so they fall back to recency only.

avg_pct = sum(w_i * pct_i) / sum(w_i) over contributing rows. This is a deliberately simple v1:
no house-effect adjustment, no trend line, no likely-voter screen — just decayed, rated mean.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


def recency_weight(days_old: float, half_life_days: float = 30.0) -> float:
    """0.5 ** (days_old / half_life_days). 30-day half-life decay [H?a].

    days_old=0 -> 1.0; days_old=half_life_days -> 0.5. Negative days_old (a poll dated after
    as_of) is treated as 0 -> full weight 1.0. Raises ValueError on non-positive half_life_days.
    """
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    if days_old < 0:
        days_old = 0.0
    return 0.5 ** (days_old / half_life_days)


def pollster_weight(pollster: str | None, ratings: dict[str, float]) -> float:
    """Caller-supplied multiplier for a pollster; neutral 1.0 when unknown or unnamed [H6a].

    ratings maps pollster name -> a positive weight (e.g. from numeric_grade normalized).
    A missing pollster name, or a name absent from ratings, yields the neutral weight 1.0.
    """
    if not pollster:
        return 1.0
    return ratings.get(pollster, 1.0)


class AggregateRow(BaseModel):
    """Weighted polling average for one (state, party) race. Extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    state: str
    party: str
    avg_pct: float
    n_polls: int
    latest_end_date: str | None


def _parse_date(value: object) -> date | None:
    """Parse an ISO 'YYYY-MM-DD' string to a date, or None if missing/unparseable [R7a]."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def aggregate(
    poll_rows: list[dict],
    ratings: dict[str, float] | None = None,
    as_of: date | None = None,
    half_life_days: float = 30.0,
) -> list[dict]:
    """Weighted polling average per (state, party) [H?a], an input to the forecast [N2a].

    Groups poll_rows by (state, party) and computes a weighted mean of pct where each poll's
    weight is recency_weight(days from end_date to as_of) * pollster_weight(pollster). Rows
    with missing/unparseable end_date or missing pct are skipped (excluded from n_polls).
    as_of defaults to today() — tests pass an explicit as_of for determinism. Output is one
    AggregateRow per group (4dp avg_pct), sorted by (state, party). Raises ValueError on empty
    poll_rows.
    """
    if not poll_rows:
        raise ValueError("aggregate requires at least one poll row")
    ratings = ratings or {}
    as_of = as_of or date.today()

    groups: dict[tuple[str, str], dict] = {}
    for row in poll_rows:
        end = _parse_date(row.get("end_date"))
        pct = row.get("pct")
        if end is None or pct is None:
            continue
        state = row.get("state") or ""
        party = row.get("party") or ""
        days_old = (as_of - end).days
        weight = recency_weight(days_old, half_life_days) * pollster_weight(
            row.get("pollster"), ratings
        )
        g = groups.setdefault(
            (state, party),
            {"weighted_sum": 0.0, "weight_total": 0.0, "n": 0, "latest": None},
        )
        g["weighted_sum"] += weight * pct
        g["weight_total"] += weight
        g["n"] += 1
        if g["latest"] is None or row["end_date"] > g["latest"]:
            g["latest"] = row["end_date"]

    rows: list[dict] = []
    for (state, party) in sorted(groups):
        g = groups[(state, party)]
        avg = g["weighted_sum"] / g["weight_total"] if g["weight_total"] > 0 else 0.0
        rows.append(
            AggregateRow(
                state=state,
                party=party,
                avg_pct=round(avg, 4),
                n_polls=g["n"],
                latest_end_date=g["latest"],
            ).model_dump()
        )
    return rows
