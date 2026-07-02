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

# Refinement terms [N14a, Q9.1] — additive nudges in two-party MARGIN space, applied on top of the
# poll/fundamentals blend. Deliberately small, signed, and explainable (still a published heuristic,
# not a fitted model). Each is a fraction of margin (a 0.02 term ≈ 1 point of two-party share).
INCUMBENCY_MARGIN = 0.02   # incumbents run ahead of the fundamentals; sign follows their party.
FINANCE_COEF = 0.05        # margin per unit of normalized Dem-minus-Rep finance signal in [-1, 1].
MIDTERM_PENALTY = 0.04     # the PRESIDENT'S party typically loses ground at a midterm — shift away.

# Forecast-horizon uncertainty [Q9.1]: a race a year out is far less certain than one on election
# eve, so sigma widens with days-to-election. sigma = BASE_SIGMA on/after election day, growing
# linearly to BASE_SIGMA + HORIZON_SIGMA a full year (FULL_HORIZON_DAYS) or more out.
BASE_SIGMA = 0.07
HORIZON_SIGMA = 0.06
FULL_HORIZON_DAYS = 365


def incumbency_margin(incumbent_party: str | None, bump: float = INCUMBENCY_MARGIN) -> float:
    """Incumbency nudge in Dem-margin space [Q9.1]: +bump for a Dem incumbent, -bump for a Rep
    incumbent, 0 for an open seat / independent / unknown. Pure."""
    if incumbent_party == "D":
        return bump
    if incumbent_party == "R":
        return -bump
    return 0.0


def finance_margin(finance_net: float, coef: float = FINANCE_COEF) -> float:
    """Campaign-finance nudge in Dem-margin space [Q9.1]: coef * finance_net, where finance_net is
    a normalized Dem-minus-Rep receipts signal in [-1, 1] (positive = Dem money edge). Pure."""
    return coef * finance_net


def midterm_margin(president_party: str | None, penalty: float = MIDTERM_PENALTY) -> float:
    """Midterm-penalty nudge in Dem-margin space [Q9.1]: the president's party loses ground, so the
    shift is AWAY from it — -penalty when the president is a Democrat, +penalty when Republican,
    0 when unknown. Pure."""
    if president_party == "D":
        return -penalty
    if president_party == "R":
        return penalty
    return 0.0


def sigma_for_days(
    days_to_election: int | None,
    base: float = BASE_SIGMA,
    horizon: float = HORIZON_SIGMA,
    full: int = FULL_HORIZON_DAYS,
) -> float:
    """Forecast-horizon sigma [Q9.1]: base on/after election day, widening linearly to base+horizon
    at `full` days out (and capped there). None/<=0 days → base (unchanged v1 behavior). Pure."""
    if not days_to_election or days_to_election <= 0:
        return base
    return base + horizon * min(days_to_election, full) / full


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
    *,
    incumbent_party: str | None = None,
    finance_net: float = 0.0,
    president_party: str | None = None,
    days_to_election: int | None = None,
    sigma: float | None = None,
    z: float = 1.28,
) -> dict:
    """Forecast one race [N4a,N14a,Q9.1]: blend polling + fundamentals, then apply the refinement
    nudges, into win prob, margin, range.

    office selects the blend weights [N14a]. fundamentals_pvi is the signed PVI lean. When
    poll_dem_share is given it is converted to a poll margin and blended; when None the forecast
    uses fundamentals only. The blended margin is then adjusted by incumbency, campaign finance,
    and the midterm penalty [Q9.1] (each a small signed nudge, all no-ops by default). sigma
    defaults to the horizon-aware sigma_for_days(days_to_election) — wider a year out — unless an
    explicit sigma is passed. win_prob = normal_cdf(adjusted_margin, 0, sigma); the reported range
    is margin +/- z*sigma (z=1.28 ~= 80% interval). All floats rounded to 4dp. Returns model_dump().
    """
    poll_m = None if poll_dem_share is None else poll_margin(poll_dem_share)
    fund_m = fundamentals_margin(fundamentals_pvi)
    margin = (
        blend_margin(poll_m, fund_m, office)
        + incumbency_margin(incumbent_party)
        + finance_margin(finance_net)
        + midterm_margin(president_party)
    )
    s = sigma_for_days(days_to_election) if sigma is None else sigma
    win_prob = normal_cdf(margin, 0.0, s)
    return RaceForecast(
        race_office=office,
        win_prob=round(win_prob, 4),
        margin=round(margin, 4),
        margin_lo=round(margin - z * s, 4),
        margin_hi=round(margin + z * s, 4),
    ).model_dump()


def predict_races(
    races: list[dict],
    *,
    president_party: str | None = None,
    days_to_election: int | None = None,
) -> dict[str, float]:
    """Forecast many races -> {race_id: win_prob}, ready for montecarlo.compute_forecast [N2a,N5a].

    Each race dict has race_id, office, fundamentals_pvi, and optional poll_dem_share,
    incumbent_party, finance_net. president_party + days_to_election are shared across the slate
    [Q9.1]. Returns a mapping of race_id -> Dem win probability in [0, 1]. Raises on empty races.
    """
    if not races:
        raise ValueError("predict_races requires at least one race")
    out: dict[str, float] = {}
    for r in races:
        forecast = predict_race(
            office=r["office"],
            fundamentals_pvi=r["fundamentals_pvi"],
            poll_dem_share=r.get("poll_dem_share"),
            incumbent_party=r.get("incumbent_party"),
            finance_net=r.get("finance_net", 0.0),
            president_party=president_party,
            days_to_election=days_to_election,
        )
        out[r["race_id"]] = forecast["win_prob"]
    return out
