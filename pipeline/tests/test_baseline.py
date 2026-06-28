import pytest

from btb_pipeline.baseline import build_baseline, cook_pvi


def test_cook_pvi_dem_leaning():
    # district 0.55 vs national 0.51 -> +0.04 Dem lean.
    assert cook_pvi(0.55, 0.51) == pytest.approx(0.04, abs=1e-9)


def test_cook_pvi_rep_leaning():
    # district 0.40 vs national 0.50 -> -0.10 (Rep-leaning).
    assert cook_pvi(0.40, 0.50) == pytest.approx(-0.10, abs=1e-9)


def test_cook_pvi_out_of_range_raises():
    with pytest.raises(ValueError):
        cook_pvi(1.5, 0.50)
    with pytest.raises(ValueError):
        cook_pvi(0.50, -0.1)


def test_build_baseline_pvi_and_fields_with_defaults():
    districts = [
        {
            "geoid": "0102",
            "district_dem_share": 0.55,
            "incumbent_party": "D",
            "open_seat": False,
            "finance_net": 0.1234,
        },
        {
            "geoid": "0101",
            "district_dem_share": 0.40,
            # incumbent_party, open_seat, finance_net omitted -> defaults.
        },
        {
            "geoid": "0103",
            "district_dem_share": 0.51,
            "incumbent_party": "R",
            "open_seat": True,
        },
    ]
    out = build_baseline(districts, national_dem_share=0.51)

    assert len(out) == 3
    # Sorted by geoid.
    assert [r["geoid"] for r in out] == ["0101", "0102", "0103"]

    by_geoid = {r["geoid"]: r for r in out}

    # 0101: pvi 0.40 - 0.51 = -0.11; defaults applied.
    r0101 = by_geoid["0101"]
    assert r0101["pvi"] == pytest.approx(-0.11, abs=1e-9)
    assert r0101["incumbent_party"] is None
    assert r0101["open_seat"] is False
    assert r0101["finance_net"] == pytest.approx(0.0, abs=1e-9)

    # 0102: pvi 0.55 - 0.51 = +0.04; fields carried through, finance rounded 4dp.
    r0102 = by_geoid["0102"]
    assert r0102["pvi"] == pytest.approx(0.04, abs=1e-9)
    assert r0102["incumbent_party"] == "D"
    assert r0102["open_seat"] is False
    assert r0102["finance_net"] == pytest.approx(0.1234, abs=1e-9)

    # 0103: pvi 0.51 - 0.51 = 0.0; open seat, Rep incumbent.
    r0103 = by_geoid["0103"]
    assert r0103["pvi"] == pytest.approx(0.0, abs=1e-9)
    assert r0103["incumbent_party"] == "R"
    assert r0103["open_seat"] is True
    assert r0103["finance_net"] == pytest.approx(0.0, abs=1e-9)


def test_build_baseline_empty_raises():
    with pytest.raises(ValueError):
        build_baseline([], national_dem_share=0.51)
