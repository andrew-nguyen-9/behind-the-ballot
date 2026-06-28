"""Baseline fundamentals [N3a]: the FUNDAMENTALS feature layer feeding the race model [N2a].

Before any poll is consulted, a race has a partisan prior set by how the district has voted
relative to the nation. This module computes that prior as a Cook-PVI-style lean and assembles
it, alongside incumbency and a campaign-finance signal, into a per-district feature row. These
are FEATURES, not a forecast: the race model (v1.8.2) [N2a] later combines this lean with the
polling average to produce a win probability. Nothing here is converted to a probability.

HEURISTIC (v1 — published methodology per [N12a], explainable, refine later):
- pvi: a SIGNED two-party lean = district Dem share minus national Dem share, as a fraction.
  Positive is Dem-leaning, negative is Rep-leaning (e.g. district 0.55 vs national 0.51 -> +0.04).
- incumbent_party / open_seat: incumbency signal carried through from the caller.
- finance_net: a normalized Dem-minus-Rep receipts signal supplied by the caller, stored as given.

Records are validated into a pydantic model before reporting [R7a]. Cites [R7a].
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def cook_pvi(district_dem_share: float, national_dem_share: float) -> float:
    """Cook-PVI-style signed two-party lean: district Dem share minus national Dem share [N3a].

    Both shares are two-party Dem fractions in [0, 1]. Returns the SIGNED difference as a
    fraction (positive = Dem-leaning), e.g. (0.55, 0.51) -> +0.04. Raises ValueError if either
    share falls outside [0, 1].
    """
    if not 0.0 <= district_dem_share <= 1.0:
        raise ValueError("district_dem_share must be in [0, 1]")
    if not 0.0 <= national_dem_share <= 1.0:
        raise ValueError("national_dem_share must be in [0, 1]")
    return district_dem_share - national_dem_share


class BaselineRow(BaseModel):
    """Fundamentals feature row for one district [N3a]. Extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    geoid: str
    pvi: float
    incumbent_party: str | None = None
    open_seat: bool = False
    finance_net: float = 0.0


def build_baseline(districts: list[dict], national_dem_share: float) -> list[dict]:
    """Assemble fundamentals feature rows per district [N2a,N3a], inputs to the race model.

    Each input dict has geoid, district_dem_share, and optional incumbent_party, open_seat
    (default False), and finance_net (default 0.0). pvi is computed via cook_pvi against the
    shared national_dem_share. Output is one BaselineRow per district (pvi and finance_net
    rounded to 4dp), sorted by geoid. Raises ValueError on empty districts.
    """
    if not districts:
        raise ValueError("build_baseline requires at least one district")

    rows: list[dict] = []
    for d in districts:
        pvi = cook_pvi(d["district_dem_share"], national_dem_share)
        rows.append(
            BaselineRow(
                geoid=d["geoid"],
                pvi=round(pvi, 4),
                incumbent_party=d.get("incumbent_party"),
                open_seat=d.get("open_seat", False),
                finance_net=round(d.get("finance_net", 0.0), 4),
            ).model_dump()
        )
    rows.sort(key=lambda r: r["geoid"])
    return rows
