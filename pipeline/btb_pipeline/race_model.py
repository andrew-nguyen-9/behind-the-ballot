"""Per-race forecast model [N2a,N4a]: blend the polling average with fundamentals.

This is the forecast core. For a single race it combines two upstream feature layers — the
weighted polling average [aggregate.py] and the fundamentals lean [baseline.py, signed PVI] —
into a per-race Dem WIN PROBABILITY, a predicted MARGIN, and a margin RANGE [N4a]. The win_prob
output is exactly the per-race input the Monte Carlo chamber sim consumes
(montecarlo.compute_forecast takes dict[race_id -> dem_win_prob]); win_prob is kept in [0, 1].

HEURISTIC (v1 — published methodology per [N12a], explainable, refine later):
- We work in two-party Dem MARGIN space (Dem share minus Rep share), a signed value in [-1, 1]:
    poll margin       = 2 * dem_two_party_share - 1
    fundamentals margin = 2 * pvi   (signed lean -> approximate margin)
- The two margins are combined by a fixed weighted blend that DEPENDS ON OFFICE [N14a]:
  Senate races are poll-heavy (polling is plentiful and predictive), House races are
  fundamentals-heavy (most districts are sparsely polled, so the partisan lean dominates),
  with governors in between. See OFFICE_WEIGHTS. When a race has no polling at all, the blend
  falls back to fundamentals only (weight 1.0 on fundamentals).
- The win probability is normal_cdf(blended_margin, mu=0, sigma) [N4a]: a margin of 0 is a
  coin flip (0.5), and the margin's distance from 0 in units of sigma sets how confident we are.
  sigma is the assumed forecast standard deviation of the margin; z*sigma sets the reported
  range (z=1.28 -> roughly an 80% interval).

The blend weights and sigma are the published v1 heuristic [N12a] — deliberately simple and
explainable, not a fitted model. Pure stdlib math (math.erf for the normal CDF); no scipy,
no network, no accounts [N2a]. Records are validated into a pydantic model before reporting.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict

# Office-specific blend weights [N14a]: Senate poll-heavy, House fundamentals-heavy.
OFFICE_WEIGHTS: dict[str, dict[str, float]] = {
    "senate": {"poll": 0.7, "fund": 0.3},
    "house": {"poll": 0.3, "fund": 0.7},
    "governor": {"poll": 0.6, "fund": 0.4},
}


def normal_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """Standard normal CDF via math.erf: 0.5 * (1 + erf((x - mu) / (sigma * sqrt(2)))).

    sigma must be positive. normal_cdf(mu) = 0.5; normal_cdf(mu + sigma) ~= 0.8413.
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0))))


def poll_margin(dem_two_party_share: float) -> float:
    """Two-party Dem margin from a Dem two-party share: 2 * share - 1, in [-1, 1] [N4a].

    share=0.5 -> 0.0; share=0.55 -> +0.10. Raises ValueError if share is outside [0, 1].
    """
    if not 0.0 <= dem_two_party_share <= 1.0:
        raise ValueError("dem_two_party_share must be in [0, 1]")
    return 2.0 * dem_two_party_share - 1.0


def fundamentals_margin(pvi: float) -> float:
    """Approximate Dem margin from a signed PVI lean: 2 * pvi [N3a].

    A signed two-party lean (e.g. +0.04) maps to an approximate margin (e.g. +0.08).
    """
    return 2.0 * pvi


def blend_margin(poll_m: float | None, fund_m: float, office: str) -> float:
    """Weighted blend of poll and fundamentals margins per office [N14a].

    If poll_m is None (no polling), use fundamentals only (weight 1.0 on fundamentals).
    Otherwise blend with OFFICE_WEIGHTS[office]. Unknown office raises ValueError.
    """
    if office not in OFFICE_WEIGHTS:
        raise ValueError(f"unknown office: {office!r}")
    if poll_m is None:
        return fund_m
    w = OFFICE_WEIGHTS[office]
    return w["poll"] * poll_m + w["fund"] * fund_m


class RaceForecast(BaseModel):
    """Per-race forecast: win prob, margin, and range [N4a]. Extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    race_office: str
    win_prob: float
    margin: float
    margin_lo: float
    margin_hi: float


def predict_race(
    office: str,
    fundamentals_pvi: float,
    poll_dem_share: float | None = None,
    sigma: float = 0.07,
    z: float = 1.28,
) -> dict:
    """Forecast one race [N4a,N14a]: blend polling + fundamentals into win prob, margin, range.

    office selects the blend weights [N14a]. fundamentals_pvi is the signed PVI lean. When
    poll_dem_share is given it is converted to a poll margin and blended; when None the forecast
    uses fundamentals only. win_prob = normal_cdf(blended_margin, 0, sigma). The reported range is
    margin +/- z*sigma (z=1.28 ~= 80% interval). All floats rounded to 4dp. Returns model_dump().
    """
    poll_m = None if poll_dem_share is None else poll_margin(poll_dem_share)
    fund_m = fundamentals_margin(fundamentals_pvi)
    margin = blend_margin(poll_m, fund_m, office)
    win_prob = normal_cdf(margin, 0.0, sigma)
    return RaceForecast(
        race_office=office,
        win_prob=round(win_prob, 4),
        margin=round(margin, 4),
        margin_lo=round(margin - z * sigma, 4),
        margin_hi=round(margin + z * sigma, 4),
    ).model_dump()


def predict_races(races: list[dict]) -> dict[str, float]:
    """Forecast many races -> {race_id: win_prob}, ready for montecarlo.compute_forecast [N2a,N5a].

    Each race dict has race_id, office, fundamentals_pvi, and optional poll_dem_share. Returns a
    mapping of race_id -> Dem win probability in [0, 1]. Raises ValueError on empty races.
    """
    if not races:
        raise ValueError("predict_races requires at least one race")
    out: dict[str, float] = {}
    for r in races:
        forecast = predict_race(
            office=r["office"],
            fundamentals_pvi=r["fundamentals_pvi"],
            poll_dem_share=r.get("poll_dem_share"),
        )
        out[r["race_id"]] = forecast["win_prob"]
    return out
