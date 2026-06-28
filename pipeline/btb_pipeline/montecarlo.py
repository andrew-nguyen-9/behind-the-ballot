"""Monte Carlo chamber forecast [N5a]: per-race win probabilities -> seat distribution.

The signature forecast piece. Given a Dem win probability per race (supplied later by the race
model [N2a]; here they arrive as fixtures), simulate the whole chamber many times to produce a
SEAT DISTRIBUTION and a chamber-CONTROL probability [N5a] — not just a point estimate.

CORRELATED NATIONAL SWING [N6a]: races do not move independently. Each simulation draws ONE
shared national swing z ~ Normal(0, national_sigma); every race's probability is nudged by the
same z on the logit scale (shifted_p_i = sigmoid(logit(p_i) + swing_scale * z)). A good national
night for Democrats lifts all races together, which fattens the tails of the seat distribution
relative to independent races — exactly the correlation that makes close chambers swingy.

Pure-math, keyless, and SEEDED for reproducibility [N13a]: a single explicit numpy Generator
(np.random.default_rng(seed)) drives every draw, so a given seed yields identical output. The
simulation is vectorized with numpy [N7a]: an (n_sims x n_races) shifted-probability matrix is
compared against uniform draws to resolve all Bernoulli race outcomes at once.

Records are validated into a pydantic model before reporting [R7a].
"""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict

_EPS = 1e-6


def logit(p: np.ndarray | float) -> np.ndarray:
    """Log-odds of p, with p clipped to [1e-6, 1-1e-6] to avoid +/-inf [N6a]."""
    p = np.clip(p, _EPS, 1.0 - _EPS)
    return np.log(p / (1.0 - p))


def sigmoid(x: np.ndarray | float) -> np.ndarray:
    """Inverse of logit: 1 / (1 + exp(-x)), mapping log-odds back to a probability [N6a]."""
    return 1.0 / (1.0 + np.exp(-x))


def simulate_chamber(
    race_probs: dict[str, float],
    n_sims: int = 10000,
    national_sigma: float = 0.05,
    swing_scale: float = 3.0,
    seed: int = 0,
    majority: int | None = None,
) -> dict:
    """Monte Carlo a chamber from per-race Dem win probabilities [N5a,N6a,N13a,N7a].

    race_probs maps race_id -> Dem win probability (0..1). For each of n_sims simulations we draw
    ONE shared national swing z ~ Normal(0, national_sigma) [N6a]; every race's probability is
    shifted to sigmoid(logit(p_i) + swing_scale * z), then a Bernoulli draw per race decides the
    Dem win. Dem seats are summed per simulation. Draws come from a single seeded numpy Generator
    so the result is reproducible [N13a], and the whole thing is vectorized [N7a]: an
    (n_sims x n_races) shifted-probability matrix is compared against uniform draws.

    majority defaults to floor(n_races / 2) + 1. Returns a dict (floats rounded to 4dp) with
    n_sims, n_races, expected_dem_seats (mean), dem_seat_p10/p50/p90 (percentiles as ints),
    dem_control_prob (fraction of sims with dem_seats >= majority), and seat_distribution
    (seat_count -> probability, nonzero buckets only). Raises ValueError on empty race_probs.
    """
    if not race_probs:
        raise ValueError("simulate_chamber requires at least one race")
    if n_sims <= 0:
        raise ValueError("n_sims must be positive")
    if national_sigma < 0:
        raise ValueError("national_sigma must be non-negative")

    n_races = len(race_probs)
    if majority is None:
        majority = n_races // 2 + 1

    rng = np.random.default_rng(seed)

    base_logit = logit(np.array(list(race_probs.values()), dtype=float))  # (n_races,)
    # One shared national swing per simulation [N6a].
    swing = rng.normal(0.0, national_sigma, size=n_sims)  # (n_sims,)
    # (n_sims x n_races) shifted-probability matrix [N7a].
    shifted = sigmoid(base_logit[None, :] + swing_scale * swing[:, None])
    draws = rng.random(size=(n_sims, n_races))
    dem_wins = draws < shifted  # Bernoulli per race
    dem_seats = dem_wins.sum(axis=1)  # (n_sims,)

    expected_dem_seats = float(dem_seats.mean())
    p10, p50, p90 = np.percentile(dem_seats, [10, 50, 90])
    dem_control_prob = float(np.mean(dem_seats >= majority))

    counts, freqs = np.unique(dem_seats, return_counts=True)
    seat_distribution = {
        int(seat): round(float(freq) / n_sims, 4) for seat, freq in zip(counts, freqs)
    }

    return {
        "n_sims": n_sims,
        "n_races": n_races,
        "expected_dem_seats": round(expected_dem_seats, 4),
        "dem_seat_p10": int(p10),
        "dem_seat_p50": int(p50),
        "dem_seat_p90": int(p90),
        "dem_control_prob": round(dem_control_prob, 4),
        "seat_distribution": seat_distribution,
    }


class ChamberForecast(BaseModel):
    """Scalar Monte Carlo chamber-forecast summary [N5a]. Extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    n_sims: int
    n_races: int
    expected_dem_seats: float
    dem_seat_p10: int
    dem_seat_p50: int
    dem_seat_p90: int
    dem_control_prob: float


def compute_forecast(race_probs: dict[str, float], **kw) -> dict:
    """Run simulate_chamber, validate scalars into a ChamberForecast, and return the dict [N5a,R7a].

    Returns model_dump() PLUS the seat_distribution key (the full per-seat-count probability map,
    which is not a scalar model field). **kw is forwarded to simulate_chamber (n_sims, seed, etc).
    Raises ValueError on empty race_probs.
    """
    if not race_probs:
        raise ValueError("compute_forecast requires at least one race")
    result = simulate_chamber(race_probs, **kw)
    forecast = ChamberForecast(**result).model_dump()
    forecast["seat_distribution"] = result["seat_distribution"]
    return forecast
