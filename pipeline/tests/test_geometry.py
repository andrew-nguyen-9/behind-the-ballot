import math

import pytest
from shapely.geometry import Polygon

from btb_pipeline.geometry import (
    compute_metrics,
    convex_hull_ratio,
    polsby_popper,
    reock,
)

UNIT_SQUARE = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
# Concave L-shape: hull is a 2x2 square (area 4), shape area 3.
L_SHAPE = Polygon([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)])
THIN_RECT = Polygon([(0, 0), (4, 0), (4, 0.25), (0, 0.25)])


def test_unit_square_polsby_popper():
    # 4*pi*1 / 16 == pi/4 ~= 0.7854
    assert polsby_popper(UNIT_SQUARE) == pytest.approx(math.pi / 4, abs=1e-3)


def test_unit_square_convex_hull_ratio_is_one():
    assert convex_hull_ratio(UNIT_SQUARE) == pytest.approx(1.0, abs=1e-9)


def test_unit_square_reock():
    # min bounding circle radius = sqrt(2)/2, area = pi*0.5 ~= 1.5708, reock ~= 0.6366
    expected = 1.0 / (math.pi * 0.5)
    assert reock(UNIT_SQUARE) == pytest.approx(expected, abs=1e-2)


def test_convex_shape_hull_ratio_one_concave_less():
    assert convex_hull_ratio(UNIT_SQUARE) == pytest.approx(1.0, abs=1e-9)
    assert convex_hull_ratio(L_SHAPE) < 1.0


def test_compact_square_beats_thin_rectangle():
    assert polsby_popper(UNIT_SQUARE) > polsby_popper(THIN_RECT)


def test_compute_metrics_sorted_and_rounded():
    rows = compute_metrics({"02": UNIT_SQUARE, "01": L_SHAPE})
    assert len(rows) == 2
    assert [r["geoid"] for r in rows] == ["01", "02"]
    for row in rows:
        assert set(row) == {"geoid", "polsby_popper", "reock", "convex_hull_ratio"}
        for key in ("polsby_popper", "reock", "convex_hull_ratio"):
            assert row[key] == round(row[key], 4)


def test_empty_geometry_raises():
    with pytest.raises(ValueError):
        polsby_popper(Polygon())
    with pytest.raises(ValueError):
        reock(Polygon())
    with pytest.raises(ValueError):
        convex_hull_ratio(Polygon())
