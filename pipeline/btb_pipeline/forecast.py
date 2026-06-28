"""Forecast runner — the capstone that composes the engine into one call [N1a,N4a,N5a]:
per-race model -> win probabilities -> Monte Carlo chamber sim -> a single forecast
bundle the forecast UI/cron consume. Forecast figures are DERIVED: provenance is the
union of input source rows (polls/finance/demographics), recorded per snapshot [R14a] —
there is no own DATA_SOURCES row.

ponytail: thin orchestrator over already-tested modules; the math lives in race_model +
montecarlo. Live inputs (real polls/fundamentals) arrive once connectors run; the engine
is identical, only the inputs change.
"""

from __future__ import annotations

from datetime import datetime, timezone

import btb_pipeline.montecarlo as montecarlo
import btb_pipeline.race_model as race_model


def run_forecast(
    races: list[dict],
    n_sims: int = 10000,
    national_sigma: float = 0.05,
    seed: int = 0,
    as_of: datetime | None = None,
) -> dict:
    """Compose the engine over a list of race inputs.

    Each race dict: race_id, office, fundamentals_pvi, optional poll_dem_share.
    Returns {as_of, races: [per-race forecast...], chamber: {seat dist + control prob}}.
    """
    if not races:
        raise ValueError("no races to forecast")

    per_race: list[dict] = []
    for r in races:
        rf = race_model.predict_race(
            office=r["office"],
            fundamentals_pvi=r["fundamentals_pvi"],
            poll_dem_share=r.get("poll_dem_share"),
        )
        rf["race_id"] = r["race_id"]
        per_race.append(rf)

    win_probs = {r["race_id"]: rf["win_prob"] for r, rf in zip(races, per_race)}
    chamber = montecarlo.compute_forecast(
        win_probs, n_sims=n_sims, national_sigma=national_sigma, seed=seed
    )

    return {
        "as_of": (as_of or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
        "races": per_race,
        "chamber": chamber,
    }
