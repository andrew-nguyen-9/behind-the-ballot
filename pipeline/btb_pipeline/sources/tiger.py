"""TIGER/Line congressional-district geometry connector [L6a] → real compactness metrics
[L2a]. Keyless, public-domain Census cartographic boundary file (118th Congress districts).

Pipeline: download the cb_2023 CD118 shapefile zip → read each district polygon (pyshp) →
**reproject lat/lon (EPSG:4269) to CONUS Albers equal-area (EPSG:5070)** → Polsby-Popper /
Reock / convex-hull ratio (`geometry.compute_metrics`) → bake gold `tiger`.

WHY reproject: the metrics use planar `.area`/`.length`; on raw lat/lon degrees those are
distorted. EPSG:5070 is the standard US equal-area projection. CAVEAT [L8a]: 5070 is tuned for
the contiguous US, so AK/HI/territory compactness is approximate — surfaced in the methodology,
never as a single verdict. Fairness metrics (efficiency gap etc.) need district ELECTION RESULTS,
a source not yet wired (shares the forecast partisan-lean gap, Open Q#3) — so this unit ships
compactness only; the fairness table stays its sample until that source lands.

ponytail: transport returns the zip BYTES (injectable → the test feeds a synthetic shapefile,
no network). One fixed source, one bake; richer geos (block/precinct) only when a feature needs.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from btb_pipeline.core import DATA_ROOT, SourceSpec, bake
from btb_pipeline.geometry import compute_metrics

SPEC = SourceSpec(name="tiger", cadence="yearly", freshness_floor_days=800)


class DistrictCompactnessRow(BaseModel):
    """One district's compactness for the gerrymander page [L2a]. Extra keys ignored."""

    model_config = ConfigDict(extra="ignore")

    geoid: str
    state: str
    district: int
    polsby_popper: float
    reock: float
    convex_hull_ratio: float

# 118th-Congress district cartographic boundaries (1:500k), NAD83 geographic (EPSG:4269).
SOURCE_URL = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_cd118_500k.zip"
GEOMETRY_VINTAGE = "2023 cb / 118th Congress"
SRC_CRS = "EPSG:4269"  # NAD83 lat/lon (TIGER/cb default)
EQUAL_AREA_CRS = "EPSG:5070"  # NAD83 CONUS Albers equal-area (meters)

# State FIPS -> USPS postal. Geo domain reference; kept local to avoid a sources->web import.
FIPS_POSTAL: dict[str, str] = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
    "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
    "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
    "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
    "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
    "55": "WI", "56": "WY", "72": "PR",
}


def _reprojector():
    """A lat/lon (4269) -> equal-area (5070) point transform for shapely.ops.transform."""
    from pyproj import Transformer

    t = Transformer.from_crs(SRC_CRS, EQUAL_AREA_CRS, always_xy=True)
    return t.transform


def parse_districts(zip_bytes: bytes) -> list[dict]:
    """cb CD118 shapefile zip -> compactness rows [L2a]. Reprojects to equal-area before metrics.

    Returns one row per numbered district: {geoid, state, district, polsby_popper, reock,
    convex_hull_ratio}. Districts whose code isn't numeric (non-CD areas) are skipped.
    """
    import shapefile  # pyshp
    from shapely.geometry import shape
    from shapely.ops import transform as shp_transform

    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    name = next(n[:-4] for n in zf.namelist() if n.endswith(".shp"))
    reader = shapefile.Reader(
        shp=io.BytesIO(zf.read(name + ".shp")),
        dbf=io.BytesIO(zf.read(name + ".dbf")),
        shx=io.BytesIO(zf.read(name + ".shx")),
    )
    project = _reprojector()

    geoms: dict[str, object] = {}
    meta: dict[str, dict] = {}
    for sr in reader.iterShapeRecords():
        rec = sr.record.as_dict()
        statefp = rec.get("STATEFP")
        cd = rec.get("CD118FP")
        geoid = rec.get("GEOID") or f"{statefp}{cd}"
        try:
            district = int(cd)
        except (TypeError, ValueError):
            continue  # non-numeric (e.g. "ZZ" unassigned) — not a published district
        geoms[geoid] = shp_transform(project, shape(sr.shape.__geo_interface__))
        meta[geoid] = {"state": FIPS_POSTAL.get(statefp, statefp), "district": district}

    rows = compute_metrics(geoms)  # geoid + 3 metrics, sorted by geoid [L2a]
    for r in rows:
        r.update(meta[r["geoid"]])
    return rows


def run(transport=None, as_of: datetime | None = None, root: Path = DATA_ROOT) -> Path:
    """Download -> parse -> bake gold `tiger` [R14a]. transport(url)->bytes is injectable."""
    if transport is None:
        import requests  # local import: only needed for live runs

        transport = lambda url: requests.get(url, timeout=60).content  # noqa: E731
    rows = parse_districts(transport(SOURCE_URL))
    return bake(SPEC, DistrictCompactnessRow, rows, as_of or datetime.now(timezone.utc), root)
