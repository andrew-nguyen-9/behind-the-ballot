"""Partisan-fairness metrics [L3a]: efficiency gap + mean-median over per-district results.

Pure-math, keyless, deterministic — gerrymander-lite scored over per-district two-party vote
counts already in hand. Joining to real election results (FEC/state returns) is the live step
(later); this module only scores districts handed to it.

Each district is a dict {"geoid": str, "dem_votes": int, "rep_votes": int}. We use the classic
TWO-PARTY framing and ignore third parties for these metrics — that is a real limitation: a
strong third-party share is invisible here. As with compactness, the metrics can disagree and
there is no single fairness verdict [L8a]; we report several and let the reader weigh them.

Records are validated into pydantic models before reporting [R7a].
"""

from __future__ import annotations

from statistics import mean, median

from pydantic import BaseModel, ConfigDict


def wasted_votes(dem: int, rep: int) -> tuple[float, float]:
    """Efficiency-gap wasted-vote rule for one two-party district [L3a].

    total = dem + rep; the majority threshold to win is total // 2 + 1. The winner wastes every
    vote beyond that threshold (surplus); the loser wastes all of their votes. Returns
    (dem_wasted, rep_wasted). A tie (dem == rep) is treated as no winner: both sides waste all
    their votes.
    """
    total = dem + rep
    threshold = total // 2 + 1
    if dem > rep:
        return float(dem - threshold), float(rep)
    if rep > dem:
        return float(dem), float(rep - threshold)
    return float(dem), float(rep)


def efficiency_gap(districts: list[dict]) -> float:
    """EG = (sum_dem_wasted - sum_rep_wasted) / total_votes [L3a].

    Sign convention: POSITIVE favors REP (Democrats waste more votes), NEGATIVE favors DEM.
    Raises ValueError on empty input or zero total two-party votes.
    """
    if not districts:
        raise ValueError("efficiency_gap requires at least one district")
    dem_wasted_total = 0.0
    rep_wasted_total = 0.0
    total_votes = 0
    for d in districts:
        dem, rep = d["dem_votes"], d["rep_votes"]
        dw, rw = wasted_votes(dem, rep)
        dem_wasted_total += dw
        rep_wasted_total += rw
        total_votes += dem + rep
    if total_votes <= 0:
        raise ValueError("efficiency_gap requires nonzero total votes")
    return (dem_wasted_total - rep_wasted_total) / total_votes


def mean_median(districts: list[dict]) -> float:
    """mean(dem_share) - median(dem_share), where dem_share = dem / (dem + rep) [L3a].

    A common gerrymander signal: a gap between mean and median district share suggests the
    distribution is skewed (packing/cracking). Sign convention: POSITIVE means the mean Dem
    share exceeds the median, i.e. Dem support is concentrated in fewer districts (a sign the
    map disadvantages Democrats). Raises ValueError on empty input.
    """
    if not districts:
        raise ValueError("mean_median requires at least one district")
    shares = []
    for d in districts:
        dem, rep = d["dem_votes"], d["rep_votes"]
        total = dem + rep
        if total <= 0:
            raise ValueError("mean_median requires nonzero votes in every district")
        shares.append(dem / total)
    return mean(shares) - median(shares)


def seats_votes(districts: list[dict]) -> tuple[float, float]:
    """Return (dem_seat_share, dem_vote_share) [L3a].

    seat share = fraction of districts Democrats win (dem > rep); vote share = total Dem votes
    / total two-party votes. A handy summary of the seats-votes relationship. Raises ValueError
    on empty input or zero total votes.
    """
    if not districts:
        raise ValueError("seats_votes requires at least one district")
    seats_won = 0
    dem_total = 0
    two_party_total = 0
    for d in districts:
        dem, rep = d["dem_votes"], d["rep_votes"]
        if dem > rep:
            seats_won += 1
        dem_total += dem
        two_party_total += dem + rep
    if two_party_total <= 0:
        raise ValueError("seats_votes requires nonzero total votes")
    return seats_won / len(districts), dem_total / two_party_total


class FairnessReport(BaseModel):
    """Partisan-fairness summary. Metrics can disagree — no single verdict [L8a]."""

    model_config = ConfigDict(extra="ignore")

    efficiency_gap: float
    mean_median: float
    dem_seat_share: float
    dem_vote_share: float
    n_districts: int


def compute_fairness(districts: list[dict]) -> dict:
    """Assemble a FairnessReport (values rounded to 4dp) and return model_dump() [L3a,L8a,R7a].

    Raises ValueError on empty input.
    """
    if not districts:
        raise ValueError("compute_fairness requires at least one district")
    dem_seat_share, dem_vote_share = seats_votes(districts)
    report = FairnessReport(
        efficiency_gap=round(efficiency_gap(districts), 4),
        mean_median=round(mean_median(districts), 4),
        dem_seat_share=round(dem_seat_share, 4),
        dem_vote_share=round(dem_vote_share, 4),
        n_districts=len(districts),
    )
    return report.model_dump()
