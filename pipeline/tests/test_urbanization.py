import pytest

from btb_pipeline.urbanization import classify, classify_districts


def test_classify_thresholds():
    assert classify(0.9) == "urban"
    assert classify(0.75) == "urban"  # floor inclusive
    assert classify(0.6) == "suburban"
    assert classify(0.40) == "rural"  # ceil inclusive
    assert classify(0.1) == "rural"


def test_classify_out_of_range_raises():
    with pytest.raises(ValueError):
        classify(1.5)


def test_classify_districts_adds_label_and_sorts():
    rows = [
        {"geoid": "3903", "urban_pop_share": 0.9},
        {"geoid": "3901", "urban_pop_share": 0.2},
    ]
    out = classify_districts(rows)
    assert [r["geoid"] for r in out] == ["3901", "3903"]
    assert out[0]["urbanization"] == "rural"
    assert out[1]["urbanization"] == "urban"
