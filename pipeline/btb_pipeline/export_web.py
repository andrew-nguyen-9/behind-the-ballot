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
from datetime import datetime, timezone
from pathlib import Path

import btb_pipeline.montecarlo as montecarlo
import btb_pipeline.race_model as race_model
from btb_pipeline.baseline import cook_pvi
from btb_pipeline.core import DATA_ROOT, stage_dir
from btb_pipeline.demographics import rollup_by_state
from btb_pipeline.finance_aggregates import build_finance

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


def export_finance(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/fec ⋈ race-config candidates → per-race src/data/finance/<raceId>.json [G13a].
    candidate_meta (race_id, party) comes from the race configs' fecCandidateId; build_finance
    adds burn rate + coverage date. One file per race that has ≥1 matched candidate."""
    fec = _gold("fec", root)
    if fec is None:
        return []
    meta: dict[str, dict] = {}
    for cfg in _race_configs(RACES_DIR):
        for c in cfg.get("candidates", []):
            if c.get("fecCandidateId"):
                meta[c["fecCandidateId"]] = {"race_id": cfg["id"], "party": c.get("party")}
    rows = [r for r in build_finance(fec, meta) if r.get("race_id")]
    by_race: dict[str, list[dict]] = {}
    for r in rows:
        by_race.setdefault(r["race_id"], []).append(r)
    return [_write(web_data / "finance" / f"{rid}.json", rs) for rid, rs in by_race.items()]


def export_districts(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/tiger (real TIGER compactness) → src/data/gerrymander/districts.json [L2a]. Replaces
    the sample fixture with all 441 baked districts. (State fairness still needs district election
    results — a source not yet wired — so gerrymander/states.json stays sample for now.)"""
    rows = _gold("tiger", root)
    if rows is None:
        return []
    districts = sorted(rows, key=lambda r: r["geoid"])
    return [_write(web_data / "gerrymander" / "districts.json", districts)]


DEM_CONTROL_SEATS = 51  # 2026: Republican VP breaks ties, so Democrats need 51 for Senate control.


def export_forecast(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/medsl_president → per-Senate-race forecast + chamber control [N1a,N3a,N5a].

    Fundamentals-only (no live polls in V1): per state PVI = cook_pvi(state two-party Dem share,
    national share) → race_model → win prob/margin/range. Chamber control is the REAL Senate math:
    the Monte Carlo runs over the 33 contested seats, but control needs 51 of 100, so the threshold
    is 51 minus the Democratic-aligned holdover seats (Class I/III, not up in 2026); reported seats
    add the holdover back so the figure is total-Senate (0–100), not just the contested slice."""
    pres = _gold("medsl_president", root)
    members = _gold("members", root)
    if pres is None or members is None:
        return []
    nat_d = sum(r["dem_votes"] for r in pres)
    nat_r = sum(r["rep_votes"] for r in pres)
    national_share = nat_d / (nat_d + nat_r)
    state_share = {r["state"]: r["dem_votes"] / (r["dem_votes"] + r["rep_votes"]) for r in pres}

    # Current Senate composition from the real roster: D-aligned = Democrats + Independents (caucus).
    senate = [m for m in members if m.get("chamber") == "sen"]
    current_dem_aligned = sum(1 for m in senate if m.get("party") in ("Democrat", "Independent"))

    races = [c for c in _race_configs(RACES_DIR)
             if c.get("office") == "senate" and c.get("state") in state_share]
    # Dem-aligned seats AMONG the 33 up = configs whose incumbent is a Democrat (no independent is
    # up in 2026 — both current independents are Class I holdovers).
    up_dem = sum(1 for c in races
                 if any(x.get("incumbent") and x.get("party") == "D" for x in c.get("candidates", [])))
    holdover_dem = current_dem_aligned - up_dem
    wins_needed = DEM_CONTROL_SEATS - holdover_dem  # Dem wins required AMONG the contested 33

    as_of = datetime.now(timezone.utc).isoformat()
    written: list[Path] = []
    win_probs: dict[str, float] = {}
    for c in races:
        pvi = cook_pvi(state_share[c["state"]], national_share)
        rf = race_model.predict_race(office="senate", fundamentals_pvi=pvi)
        win_probs[c["id"]] = rf["win_prob"]
        written.append(_write(web_data / "forecast" / f"{c['id']}.json", {
            "win_prob": rf["win_prob"], "margin": rf["margin"],
            "margin_lo": rf["margin_lo"], "margin_hi": rf["margin_hi"], "as_of": as_of,
        }))

    mc = montecarlo.compute_forecast(win_probs, majority=wins_needed, seed=0)
    written.append(_write(web_data / "forecast" / "chamber-senate.json", {
        "chamber": "Senate", "as_of": as_of, "n_sims": mc["n_sims"], "n_races": len(races),
        "majority": DEM_CONTROL_SEATS,
        "expected_dem_seats": round(mc["expected_dem_seats"] + holdover_dem, 1),
        "dem_seat_p10": mc["dem_seat_p10"] + holdover_dem,
        "dem_seat_p50": mc["dem_seat_p50"] + holdover_dem,
        "dem_seat_p90": mc["dem_seat_p90"] + holdover_dem,
        "dem_control_prob": mc["dem_control_prob"],
    }))
    return written


EXPORTERS = {
    "members": export_members,
    "demographics": export_demographics,
    "finance": export_finance,
    "districts": export_districts,
    "forecast": export_forecast,
}


def main() -> int:
    for name, fn in EXPORTERS.items():
        paths = fn()
        print(f"exported {name}: {len(paths)} file(s)" if paths else f"skipped {name}: no gold artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
