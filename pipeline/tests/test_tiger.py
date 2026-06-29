"""Hermetic test for the TIGER compactness connector — synthesizes a 2-district shapefile zip
(lat/lon) in memory, so the read -> reproject(5070) -> metrics path runs with no network."""

from __future__ import annotations

import io
import zipfile

import shapefile  # pyshp

from btb_pipeline.sources import tiger


def _square(cx: float, cy: float, half: float = 0.5) -> list[list[float]]:
    """A clockwise lat/lon square ring around (cx, cy) — pyshp wants clockwise outer rings."""
    return [
        [cx - half, cy - half], [cx - half, cy + half],
        [cx + half, cy + half], [cx + half, cy - half],
        [cx - half, cy - half],
    ]


def _synthetic_zip() -> bytes:
    """Two OH-ish districts as lat/lon squares, packed as a cb-style shapefile zip."""
    shp, dbf, shx = io.BytesIO(), io.BytesIO(), io.BytesIO()
    w = shapefile.Writer(shp=shp, dbf=dbf, shx=shx)
    w.field("STATEFP", "C", 2)
    w.field("CD118FP", "C", 2)
    w.field("GEOID", "C", 4)
    for cd, cx in (("03", -83.0), ("12", -81.0)):
        w.poly([_square(cx, 40.0)])
        w.record("39", cd, f"39{cd}")
    w.close()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("cb_2023_us_cd118_500k.shp", shp.getvalue())
        zf.writestr("cb_2023_us_cd118_500k.dbf", dbf.getvalue())
        zf.writestr("cb_2023_us_cd118_500k.shx", shx.getvalue())
    return buf.getvalue()


def test_parse_districts_shapes_and_ranges():
    rows = tiger.parse_districts(_synthetic_zip())
    assert len(rows) == 2
    by_geoid = {r["geoid"]: r for r in rows}
    assert set(by_geoid) == {"3903", "3912"}
    for r in rows:
        assert r["state"] == "OH"  # FIPS 39 -> postal
        assert isinstance(r["district"], int)
        # Metrics are bounded ratios in (0, 1]; a near-square is reasonably compact.
        for k in ("polsby_popper", "reock", "convex_hull_ratio"):
            assert 0.0 < r[k] <= 1.0, f"{k}={r[k]} out of range"
        assert r["convex_hull_ratio"] > 0.95  # a square is ~fully convex


def test_bake_writes_gold(tmp_path):
    path = tiger.run(transport=lambda url: _synthetic_zip(), root=tmp_path)
    assert path.exists()
    import json

    payload = json.loads(path.read_text())
    assert payload["source"] == "tiger"
    assert len(payload["rows"]) == 2
