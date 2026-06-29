"""Live joins — export baked gold artifacts into the committed per-page JSON the Astro site reads
[ADR 0002: baked JSON on the CDN]. The site is static (SSG, 0-JS) so data must exist at BUILD
time; gold (`data/gold/*`) is gitignored/ephemeral, so this step writes the derived, display-ready
JSON into `apps/web/src/data/*` which IS committed and ships in the Cloudflare build.

Run after a bake (`python -m btb_pipeline.cli bake all`), then locally or in the nightly Action:

    uv run --project pipeline python -m btb_pipeline.export_web

ponytail: one export fn per domain, a flat dispatch — add a domain by adding a function. Each
reads gold + reuses the existing transform math, writes one JSON file. Missing gold → the domain
is skipped (the committed sample stays), so a partial bake never corrupts the site.
"""

from __future__ import annotations

import json
from pathlib import Path

from btb_pipeline.core import DATA_ROOT, stage_dir
from btb_pipeline.demographics import rollup_by_state

WEB_DATA = Path("apps/web/src/data")
RACES_DIR = Path("apps/web/src/config/races")

PARTY_LETTER = {"Democrat": "D", "Republican": "R", "Independent": "I"}

# postal -> (2-digit state FIPS, display name). Used to join race configs (postal) to ACS (FIPS).
STATES: dict[str, tuple[str, str]] = {
    "AL": ("01", "Alabama"), "AK": ("02", "Alaska"), "AZ": ("04", "Arizona"),
    "AR": ("05", "Arkansas"), "CA": ("06", "California"), "CO": ("08", "Colorado"),
    "CT": ("09", "Connecticut"), "DE": ("10", "Delaware"), "DC": ("11", "District of Columbia"),
    "FL": ("12", "Florida"), "GA": ("13", "Georgia"), "HI": ("15", "Hawaii"),
    "ID": ("16", "Idaho"), "IL": ("17", "Illinois"), "IN": ("18", "Indiana"),
    "IA": ("19", "Iowa"), "KS": ("20", "Kansas"), "KY": ("21", "Kentucky"),
    "LA": ("22", "Louisiana"), "ME": ("23", "Maine"), "MD": ("24", "Maryland"),
    "MA": ("25", "Massachusetts"), "MI": ("26", "Michigan"), "MN": ("27", "Minnesota"),
    "MS": ("28", "Mississippi"), "MO": ("29", "Missouri"), "MT": ("30", "Montana"),
    "NE": ("31", "Nebraska"), "NV": ("32", "Nevada"), "NH": ("33", "New Hampshire"),
    "NJ": ("34", "New Jersey"), "NM": ("35", "New Mexico"), "NY": ("36", "New York"),
    "NC": ("37", "North Carolina"), "ND": ("38", "North Dakota"), "OH": ("39", "Ohio"),
    "OK": ("40", "Oklahoma"), "OR": ("41", "Oregon"), "PA": ("42", "Pennsylvania"),
    "RI": ("44", "Rhode Island"), "SC": ("45", "South Carolina"), "SD": ("46", "South Dakota"),
    "TN": ("47", "Tennessee"), "TX": ("48", "Texas"), "UT": ("49", "Utah"),
    "VT": ("50", "Vermont"), "VA": ("51", "Virginia"), "WA": ("53", "Washington"),
    "WV": ("54", "West Virginia"), "WI": ("55", "Wisconsin"), "WY": ("56", "Wyoming"),
}

ACS_RELEASE = "2022 ACS 5-year"   # connector bakes ACS5 year=2022
ACS_GEOMETRY = "2022-01-01"       # 118th-Congress district boundaries [L547]


def _race_configs(races_dir: Path = RACES_DIR) -> list[dict]:
    if not races_dir.exists():
        return []
    return [json.loads(p.read_text()) for p in sorted(races_dir.glob("*.json"))]


def _gold(source: str, root: Path) -> list[dict] | None:
    path = stage_dir("gold", source, root) / f"{source}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text()).get("rows", [])


def _party_letter(party: str | None) -> str:
    if not party:
        return "?"
    return PARTY_LETTER.get(party, party[0].upper())


def _write(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def export_members(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/members ⋈ gold/voteview (ideology) → src/data/members/roster.json [M1a,M3a]."""
    members = _gold("members", root)
    if members is None:
        return []
    ideology = {r["bioguide_id"]: r.get("nominate_dim1") for r in (_gold("voteview", root) or [])}
    roster = [
        {
            "bioguide_id": m["bioguide_id"],
            "name": m.get("name"),
            "party": _party_letter(m.get("party")),
            "state": m.get("state"),
            "chamber": m.get("chamber"),
            "district": m.get("district"),
            "nominate_dim1": ideology.get(m["bioguide_id"]),
        }
        for m in members
        if m.get("bioguide_id")
    ]
    return [_write(web_data / "members" / "roster.json", roster)]


def export_demographics(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/census_acs → per-race src/data/demographics/<raceId>.json [I7a]. Senate/governor =
    state rollup; house = the district. urbanization left null (no urban/rural split in gold)."""
    acs = _gold("census_acs", root)
    if acs is None:
        return []
    by_state = {r["state"]: r for r in rollup_by_state(acs)}  # FIPS -> {population, median_income}
    by_geoid = {r["geoid"]: r for r in acs}
    written: list[Path] = []
    for cfg in _race_configs(RACES_DIR):
        fips, name = STATES.get(cfg.get("state", ""), (None, cfg.get("state")))
        if fips is None:
            continue
        office = cfg.get("office")
        if office in ("senate", "governor"):
            agg = by_state.get(fips)
            if not agg:
                continue
            area, pop, inc = name, agg["population"], agg["median_income"]
        elif office == "house":
            row = by_geoid.get(f"{fips}{int(cfg['district']):02d}")
            if not row:
                continue
            area, pop, inc = f"{name} District {int(cfg['district'])}", row["population"], row["median_income"]
        else:
            continue
        written.append(_write(web_data / "demographics" / f"{cfg['id']}.json", {
            "area": area, "population": pop, "median_income": inc,
            "urbanization": None, "acs_release": ACS_RELEASE, "geometry_as_of": ACS_GEOMETRY,
        }))
    return written


EXPORTERS = {"members": export_members, "demographics": export_demographics}


def main() -> int:
    for name, fn in EXPORTERS.items():
        paths = fn()
        print(f"exported {name}: {len(paths)} file(s)" if paths else f"skipped {name}: no gold artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
