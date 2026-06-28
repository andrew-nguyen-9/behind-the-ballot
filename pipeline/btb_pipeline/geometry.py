"""Compactness metrics for districts [L2a]: Polsby-Popper + Reock + convex-hull ratio.

Keyless, deterministic, pure-geometry core of gerrymander-lite. Offline GeoPandas/Shapely
[L6a] — no network, no API keys. We report multiple metrics and let the reader weigh them;
there is no single compactness verdict [L8a].

ponytail: pure shapely 2.x, no pandas/geopandas needed for the metrics themselves.
Reading real TIGER shapefiles via geopandas + baking per-district artifacts is the live
geometry step (v1.1.2/later) — NOT here. This module only scores geometries already in hand.
"""

from __future__ import annotations

import math

import shapely
from pydantic import BaseModel, ConfigDict
from shapely.geometry.base import BaseGeometry


def _require_nondegenerate(geom: BaseGeometry) -> None:
    """Raise on empty/degenerate geometry — metrics are undefined there."""
    if geom is None or geom.is_empty:
        raise ValueError("compactness metrics require a non-empty geometry")


def polsby_popper(geom: BaseGeometry) -> float:
    """4*pi*area / perimeter**2. 1.0 == perfect circle; lower == less compact [L2a]."""
    _require_nondegenerate(geom)
    perimeter = geom.length
    if perimeter <= 0:
        return 0.0
    return 4 * math.pi * geom.area / perimeter**2


def convex_hull_ratio(geom: BaseGeometry) -> float:
    """area / convex_hull.area. 1.0 == convex; lower == more concave [L2a]."""
    _require_nondegenerate(geom)
    hull_area = geom.convex_hull.area
    if hull_area <= 0:
        return 0.0
    return geom.area / hull_area


def _min_bounding_circle_area(geom: BaseGeometry) -> float:
    """Area of the minimum bounding circle, robust across shapely 2.x versions.

    Prefers shapely.minimum_bounding_circle (returns the circle polygon); falls back to
    shapely.minimum_bounding_radius (pi*r**2) on older builds.
    """
    if hasattr(shapely, "minimum_bounding_circle"):
        return shapely.minimum_bounding_circle(geom).area
    radius = shapely.minimum_bounding_radius(geom)
    return math.pi * radius**2


def reock(geom: BaseGeometry) -> float:
    """area / area_of_minimum_bounding_circle. 1.0 == circle; lower == less compact [L2a]."""
    _require_nondegenerate(geom)
    circle_area = _min_bounding_circle_area(geom)
    if circle_area <= 0:
        return 0.0
    return geom.area / circle_area


class CompactnessRow(BaseModel):
    """Per-district compactness scores. No single verdict — all three reported [L8a]."""

    model_config = ConfigDict(extra="ignore")

    geoid: str
    polsby_popper: float
    reock: float
    convex_hull_ratio: float


def compute_metrics(geoms: dict[str, BaseGeometry]) -> list[dict]:
    """Score each geoid->geometry into a CompactnessRow (4dp), sorted by geoid [L2a,L8a]."""
    rows: list[dict] = []
    for geoid in sorted(geoms):
        geom = geoms[geoid]
        row = CompactnessRow(
            geoid=geoid,
            polsby_popper=round(polsby_popper(geom), 4),
            reock=round(reock(geom), 4),
            convex_hull_ratio=round(convex_hull_ratio(geom), 4),
        )
        rows.append(row.model_dump())
    return rows
