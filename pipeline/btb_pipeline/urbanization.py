"""District urbanization classification [I?a]: Census urbanized-area population share ->
urban / suburban / rural label for each district. Pure transform; thresholds are the
published v1 heuristic [N12a-style transparency].

ponytail: a thresholded classifier; tune the cut points if a better convention emerges.
"""

from __future__ import annotations

# Share of district population in a Census urbanized area -> label.
# ponytail: simple 2-threshold split; refine with Census's own urban/rural defs if needed.
URBAN_FLOOR = 0.75
RURAL_CEIL = 0.40


def classify(urban_pop_share: float) -> str:
    """urban_pop_share in [0,1] -> 'urban' | 'suburban' | 'rural'."""
    if not 0.0 <= urban_pop_share <= 1.0:
        raise ValueError("urban_pop_share must be in [0,1]")
    if urban_pop_share >= URBAN_FLOOR:
        return "urban"
    if urban_pop_share <= RURAL_CEIL:
        return "rural"
    return "suburban"


def classify_districts(rows: list[dict]) -> list[dict]:
    """Each row needs geoid + urban_pop_share -> adds 'urbanization' label. Sorted by geoid."""
    out = [{**r, "urbanization": classify(r["urban_pop_share"])} for r in rows]
    return sorted(out, key=lambda x: x["geoid"])
