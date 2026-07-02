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
from btb_pipeline.demographics import (
    build_district_changes,
    build_state_changes,
    rollup_by_state,
)
from btb_pipeline.fairness import compute_fairness
from btb_pipeline.finance_aggregates import build_finance, rollup_by_race

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

# Demographic change-over-time endpoints [E2.4, Q7.5 = 2 endpoints]. States are boundary-stable
# so a longer 2018->latest horizon is valid; CDs must stay on ONE boundary regime, and the first
# ACS 5-year on 118th-Congress maps is 2022 — so a valid CD diff is 2022->latest [L547].
CHANGE_STATE_EARLY = 2018
CHANGE_CD_EARLY = 2022
CHANGE_REDISTRICTING_YEAR = 2022  # first ACS on post-2020 district maps


def _acs_release(year: int) -> str:
    return f"{year} ACS 5-year"


def _state_names_by_fips() -> dict[str, str]:
    return {fips: name for fips, name in STATES.values()}


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


def export_demographics_tables(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/census_acs → demographics/{states,districts}.json — the full per-state + per-CD ACS
    snapshot the /demographics page renders (ALL states/CDs, not just race geographies) [E2.4,I7a].

    Uses the latest baked ACS year (or untagged single-year gold). Real figures only; no gold →
    the domain is skipped and the committed sample stays."""
    acs = _gold("census_acs", root)
    if acs is None:
        return []
    years = sorted({r["year"] for r in acs if r.get("year") is not None})
    latest = years[-1] if years else None
    rows = [r for r in acs if latest is None or r.get("year") == latest]
    names = _state_names_by_fips()
    states = [
        {"state": s["state"], "area": names.get(s["state"], s["state"]),
         "population": s["population"], "median_income": s["median_income"]}
        for s in rollup_by_state(rows)
    ]
    districts = sorted(
        ({"geoid": r["geoid"], "state": r.get("state"), "district": r.get("district"),
          "area": f"{names.get(r.get('state'), r.get('state'))}-{r.get('district')}",
          "name": r.get("name"), "population": r.get("population"),
          "median_income": r.get("median_income")} for r in rows),
        key=lambda r: r["geoid"],
    )
    release = _acs_release(latest) if latest is not None else ACS_RELEASE
    meta = {"acs_release": release, "geometry_as_of": ACS_GEOMETRY}
    return [
        _write(web_data / "demographics" / "states.json", {**meta, "rows": states}),
        _write(web_data / "demographics" / "districts.json", {**meta, "rows": districts}),
    ]


def export_demographic_changes(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/census_acs (multi-year) → demographics-change/{states,districts,meta}.json [E2.4,Q7.5].

    Needs ≥2 ACS end-years in gold (bake via `acs.run_years`). With <2 the domain is skipped and
    the /demographics change section shows an honest empty state — never placeholder numbers. States
    diff 2018->latest (boundary-stable); CDs diff 2022->latest (same 118th-Congress maps) [L547]."""
    acs = _gold("census_acs", root)
    if acs is None:
        return []
    years = sorted({r["year"] for r in acs if r.get("year") is not None})
    if len(years) < 2:
        return []
    late = years[-1]
    state_early = CHANGE_STATE_EARLY if CHANGE_STATE_EARLY in years else years[0]
    cd_early = CHANGE_CD_EARLY if CHANGE_CD_EARLY in years and CHANGE_CD_EARLY < late else years[-2]
    names = _state_names_by_fips()
    states = build_state_changes(acs, state_early, late)
    for s in states:
        s["area"] = names.get(s["state"], s["state"])
    districts = build_district_changes(acs, cd_early, late)
    for d in districts:
        d["area"] = f"{names.get(d.get('state'), d.get('state'))}-{d.get('district')}"
    meta = {
        "state_early_year": state_early, "state_late_year": late,
        "cd_early_year": cd_early, "cd_late_year": late,
        "acs_release_state_early": _acs_release(state_early),
        "acs_release_cd_early": _acs_release(cd_early),
        "acs_release_late": _acs_release(late),
        # True when the state horizon straddles the 2020 redistricting — surface the caveat in UI.
        "state_crosses_redistricting": state_early < CHANGE_REDISTRICTING_YEAR <= late,
        "geometry_as_of": ACS_GEOMETRY,
    }
    return [
        _write(web_data / "demographics-change" / "states.json", states),
        _write(web_data / "demographics-change" / "districts.json", districts),
        _write(web_data / "demographics-change" / "meta.json", meta),
    ]


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

# Forecast refinements [Q9.1]. The 2026 midterm falls under a REPUBLICAN administration, so the
# midterm penalty shifts every race away from the GOP (toward Democrats); the horizon-widened
# uncertainty is a function of days to the general (fixed by statute at the Tue after the first Mon
# in Nov). Both are published-heuristic terms — see race_model / montecarlo docstrings [N12a].
PRESIDENT_PARTY = "R"
GENERAL_ELECTION_DATE = datetime(2026, 11, 3, tzinfo=timezone.utc)


def _days_to_general(now: datetime | None = None) -> int:
    """Days from now to the 2026 general (clamped at 0 on/after election day)."""
    now = now or datetime.now(timezone.utc)
    return max(0, (GENERAL_ELECTION_DATE - now).days)


def _incumbent_party(cfg: dict) -> str | None:
    """Party letter (D/R/I) of the race's incumbent candidate, or None for an open seat."""
    for cand in cfg.get("candidates", []):
        if cand.get("incumbent"):
            return cand.get("party")
    return None


def _finance_net_by_race(root: Path) -> dict[str, float]:
    """Per-race normalized Dem-minus-Rep receipts signal in [-1, 1] [Q9.1], from gold/fec joined to
    the race configs' candidate parties. Positive = Dem money edge. Empty when no FEC gold — the
    finance term then contributes nothing (honest 0.0), never a fabricated edge."""
    fec = [r for r in (_gold("fec", root) or []) if "candidate_id" in r]
    if not fec:
        return {}
    # candidate_id -> {race_id, party} from every config's fecCandidateId candidates.
    meta: dict[str, dict] = {}
    for cfg in _race_configs(RACES_DIR):
        for cand in cfg.get("candidates", []):
            cid = cand.get("fecCandidateId")
            if cid:
                meta[cid] = {"race_id": cfg["id"], "party": cand.get("party")}
    net: dict[str, float] = {}
    for row in rollup_by_race(build_finance(fec, meta)):
        by_party = row.get("by_party", {})
        dem = by_party.get("D", 0.0)
        rep = by_party.get("R", 0.0)
        total = dem + rep
        if total > 0:
            net[row["race_id"]] = round((dem - rep) / total, 4)
    return net


def export_forecast(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/medsl_president → per-Senate-race forecast + chamber control [N1a,N3a,N5a,Q9.1].

    Fundamentals-based (no live polls in V1): per state PVI = cook_pvi(state two-party Dem share,
    national share) → race_model → win prob/margin/range. The v1.1 refinements [Q9.1] layer on top:
    the midterm penalty (2026 is a Republican-administration midterm → shift toward Democrats),
    per-race incumbency (from the config's incumbent), a campaign-finance signal (from gold/fec), and
    horizon-widened uncertainty (sigma grows with days to the general). Chamber control is the REAL
    Senate math: the Monte Carlo runs over the 33 contested seats, but control needs 51 of 100, so
    the threshold is 51 minus the Democratic-aligned holdover seats (Class I/III, not up in 2026);
    reported seats add the holdover back so the figure is total-Senate (0–100), not just contested."""
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

    # Shared refinement inputs [Q9.1].
    days_out = _days_to_general()
    finance_net = _finance_net_by_race(root)
    national_sigma = montecarlo.national_sigma_for_days(days_out)

    as_of = datetime.now(timezone.utc).isoformat()
    written: list[Path] = []
    win_probs: dict[str, float] = {}
    for c in races:
        pvi = cook_pvi(state_share[c["state"]], national_share)
        rf = race_model.predict_race(
            office="senate", fundamentals_pvi=pvi,
            incumbent_party=_incumbent_party(c), finance_net=finance_net.get(c["id"], 0.0),
            president_party=PRESIDENT_PARTY, days_to_election=days_out,
        )
        win_probs[c["id"]] = rf["win_prob"]
        written.append(_write(web_data / "forecast" / f"{c['id']}.json", {
            "win_prob": rf["win_prob"], "margin": rf["margin"],
            "margin_lo": rf["margin_lo"], "margin_hi": rf["margin_hi"], "as_of": as_of,
        }))

    mc = montecarlo.compute_forecast(
        win_probs, majority=wins_needed, seed=0, national_sigma=national_sigma)
    written.append(_write(web_data / "forecast" / "chamber-senate.json", {
        "chamber": "Senate", "as_of": as_of, "n_sims": mc["n_sims"], "n_races": len(races),
        "majority": DEM_CONTROL_SEATS,
        "expected_dem_seats": round(mc["expected_dem_seats"] + holdover_dem, 1),
        "dem_seat_p10": mc["dem_seat_p10"] + holdover_dem,
        "dem_seat_p50": mc["dem_seat_p50"] + holdover_dem,
        "dem_seat_p90": mc["dem_seat_p90"] + holdover_dem,
        "dem_control_prob": mc["dem_control_prob"],
    }))

    # House + Governor per-race forecasts [E2.2, N4a]: fundamentals-only, using the STATE-level
    # PVI as the lean proxy (district-level presidential results are not yet in gold — the
    # medsl_president gold is state-granularity, so a house district inherits its state's PVI).
    # No chamber-control rollup for these offices in V1: house control needs the full 435-seat
    # baseline, but only the competitive subset is configured. race_model office weights differ
    # (house fundamentals-heavy, governor in between) [N14a].
    for c in _race_configs(RACES_DIR):
        office = c.get("office")
        if office not in ("house", "governor") or c.get("state") not in state_share:
            continue
        pvi = cook_pvi(state_share[c["state"]], national_share)
        rf = race_model.predict_race(
            office=office, fundamentals_pvi=pvi,
            incumbent_party=_incumbent_party(c), finance_net=finance_net.get(c["id"], 0.0),
            president_party=PRESIDENT_PARTY, days_to_election=days_out,
        )
        written.append(_write(web_data / "forecast" / f"{c['id']}.json", {
            "win_prob": rf["win_prob"], "margin": rf["margin"],
            "margin_lo": rf["margin_lo"], "margin_hi": rf["margin_hi"], "as_of": as_of,
        }))
    return written


def export_dates(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/election_dates → src/data/dates/<cycle>.json [E2.1]. One committed file per cycle;
    rows sorted by state name for a stable, alphabetical calendar table."""
    rows = _gold("election_dates", root)
    if rows is None:
        return []
    by_cycle: dict[int, list[dict]] = {}
    for r in rows:
        by_cycle.setdefault(r["cycle"], []).append(r)
    return [
        _write(web_data / "dates" / f"{cycle}.json",
               sorted(rs, key=lambda r: r["state_name"]))
        for cycle, rs in sorted(by_cycle.items())
    ]


def export_results(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/primary_results → per-race src/data/results/<raceId>.json [E3.2]. One committed
    file per race that has ≥1 ingested candidate result; each file is a
    {as_of, election_type, is_certified, pct_reporting, is_called, called_by, call_source,
    source_url, candidates:[...]} record the race page renders unofficial-until-certified.

    Real figures only [repo rule]: no gold, or a gold artifact with zero rows (the pre-
    election honest-empty state), leaves src/data/results untouched, so every race page
    shows its honest 'no results yet' state — never invented numbers."""
    rows = _gold("primary_results", root)
    if not rows:
        return []
    by_race: dict[str, list[dict]] = {}
    for r in rows:
        by_race.setdefault(r["race_id"], []).append(r)

    written: list[Path] = []
    for rid, rs in by_race.items():
        rs = sorted(rs, key=lambda r: (-(r.get("votes") or 0), r["candidate"]))
        head = rs[0]
        # Race-level fields are shared across a race's rows; take them off any row.
        record = {
            "race_id": rid,
            "election_type": head.get("election_type"),
            "as_of": head.get("as_of"),
            "is_certified": head.get("is_certified", False),
            "pct_reporting": head.get("pct_reporting"),
            "is_called": head.get("is_called", False),
            "called_by": head.get("called_by"),
            "call_source": head.get("call_source"),
            "source_url": head.get("source_url"),
            "candidates": [
                {
                    "candidate": r["candidate"],
                    "party": r.get("party"),
                    "votes": r.get("votes"),
                    "pct": r.get("pct"),
                }
                for r in rs
            ],
        }
        written.append(_write(web_data / "results" / f"{rid}.json", record))
    return written


def export_fairness(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> list[Path]:
    """gold/primary_results (certified House general results) ⋈ gold/tiger → per-state partisan
    fairness (efficiency gap / mean–median / seats–votes) → src/data/gerrymander/states.json
    [L3a, E2.5]. The fairness LIVE-JOIN, source-walled through V1 and unblocked by the Wave-3
    results connector [E3.2/E3.3].

    Honest by construction [repo rule]: fairness is computed for a state ONLY when the FULL set of
    its current-lines (post-2020) U.S. House districts — the TIGER district set — has reported
    two-party results, and only for multi-district states (an efficiency gap needs a map). A partial
    slate, a single-district (at-large) state, or no results at all writes NOTHING, so the page keeps
    its honest 'pending a sourced House-by-district dataset' state — never a misleading or fabricated
    number. Real rows appear the moment a state's certified House results land in the results gold."""
    rows = _gold("primary_results", root)
    tiger = _gold("tiger", root)
    if not rows or not tiger:
        return []

    # Current-lines House district set per state (the completeness requirement).
    required: dict[str, set[int]] = {}
    for d in tiger:
        required.setdefault(d["state"], set()).add(int(d["district"]))

    # Two-party House general-election votes tallied per (state, district).
    tally: dict[tuple[str, int], dict[str, int]] = {}
    for r in rows:
        if r.get("office") != "house" or r.get("election_type") != "general":
            continue
        district, party = r.get("district"), r.get("party")
        if district is None or party not in ("D", "R"):
            continue
        agg = tally.setdefault((r["state"], int(district)), {"dem_votes": 0, "rep_votes": 0})
        agg["dem_votes" if party == "D" else "rep_votes"] += int(r.get("votes") or 0)

    by_state: dict[str, list[dict]] = {}
    for (state, district), votes in tally.items():
        by_state.setdefault(state, []).append(
            {"geoid": f"{state}-{district:02d}", "district": district, **votes}
        )

    out_rows: list[dict] = []
    for state, districts in by_state.items():
        need = required.get(state, set())
        got = {d["district"] for d in districts}
        # Require a complete, multi-district, fully-reported state — else stay honestly empty.
        if len(need) < 2 or not need <= got:
            continue
        if any(d["dem_votes"] + d["rep_votes"] <= 0 for d in districts):
            continue
        report = compute_fairness(districts)
        out_rows.append({
            "state": state,
            "efficiency_gap": report["efficiency_gap"],
            "mean_median": report["mean_median"],
            "dem_seat_share": report["dem_seat_share"],
            "dem_vote_share": report["dem_vote_share"],
        })
    if not out_rows:
        return []
    out_rows.sort(key=lambda r: r["state"])
    return [_write(web_data / "gerrymander" / "states.json", out_rows)]


EXPORTERS = {
    "members": export_members,
    "demographics": export_demographics,
    "demographics_tables": export_demographics_tables,
    "demographic_changes": export_demographic_changes,
    "finance": export_finance,
    "districts": export_districts,
    "forecast": export_forecast,
    "dates": export_dates,
    "results": export_results,
    "fairness": export_fairness,
}


def main() -> int:
    for name, fn in EXPORTERS.items():
        paths = fn()
        print(f"exported {name}: {len(paths)} file(s)" if paths else f"skipped {name}: no gold artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
