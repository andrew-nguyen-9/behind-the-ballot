"""County rollup [E-F2] — aggregate_to_county sums county-tagged/precinct-split ResultRows
into per-county candidate totals, re-derives per-county pct + pct_reporting, and stays
honest-empty (never invents a county) when the `county` tag is absent. Fixtures only; no
network, no committed data. Owns the county-schema tests; leaves test_primary_results.py to
E-R1."""

from __future__ import annotations

from btb_pipeline.sources import primary_results as pr

# Maricopa (04013) and Pima (04019) — two precinct batches per county for one candidate to
# prove votes sum across precinct-split rows sharing (county, race_id, candidate).
ROWS = [
    {"race_id": "us-senate-2026-AZ", "state": "AZ", "office": "senate", "district": None,
     "cycle": 2026, "election_type": "primary", "candidate": "Jane Doe", "party": "D",
     "county": "04013", "votes": 100, "precincts_reporting": 5, "precincts_total": 10},
    {"race_id": "us-senate-2026-AZ", "state": "AZ", "office": "senate", "district": None,
     "cycle": 2026, "election_type": "primary", "candidate": "Jane Doe", "party": "D",
     "county": "04013", "votes": 50, "precincts_reporting": 5, "precincts_total": 10},
    {"race_id": "us-senate-2026-AZ", "state": "AZ", "office": "senate", "district": None,
     "cycle": 2026, "election_type": "primary", "candidate": "John Roe", "party": "R",
     "county": "04013", "votes": 30, "precincts_reporting": 5, "precincts_total": 10},
    {"race_id": "us-senate-2026-AZ", "state": "AZ", "office": "senate", "district": None,
     "cycle": 2026, "election_type": "primary", "candidate": "Jane Doe", "party": "D",
     "county": "04019", "votes": 40, "precincts_reporting": 2, "precincts_total": 8},
]


def test_votes_sum_per_county_candidate():
    agg = pr.aggregate_to_county(ROWS)
    maricopa = {c["candidate"]: c for c in agg if c["county"] == "04013"}
    # 100 + 50 across two precinct batches → one summed county row, no dupes.
    assert maricopa["Jane Doe"]["votes"] == 150
    assert maricopa["John Roe"]["votes"] == 30
    assert len([c for c in agg if c["county"] == "04013" and c["candidate"] == "Jane Doe"]) == 1
    # Pima kept separate from Maricopa.
    pima = [c for c in agg if c["county"] == "04019"]
    assert len(pima) == 1 and pima[0]["votes"] == 40


def test_pct_is_per_county_share():
    agg = pr.aggregate_to_county(ROWS)
    maricopa = {c["candidate"]: c for c in agg if c["county"] == "04013"}
    # Maricopa race total = 150 + 30 = 180 → Jane 150/180, John 30/180.
    assert maricopa["Jane Doe"]["pct"] == round(150 / 180 * 100, 1)
    assert maricopa["John Roe"]["pct"] == round(30 / 180 * 100, 1)
    # Pima's only reported candidate is 100% of Pima's counted race.
    pima = next(c for c in agg if c["county"] == "04019")
    assert pima["pct"] == 100.0


def test_pct_reporting_derived_per_county():
    agg = pr.aggregate_to_county(ROWS)
    maricopa = next(c for c in agg if c["county"] == "04013")
    pima = next(c for c in agg if c["county"] == "04019")
    assert maricopa["pct_reporting"] == 50.0  # 5 / 10
    assert pima["pct_reporting"] == 25.0  # 2 / 8


def test_county_null_is_honest_empty_not_bucketed():
    # A statewide/untagged row (county=None) rolls up to nothing — never an invented county.
    untagged = [{**r, "county": None} for r in ROWS]
    assert pr.aggregate_to_county(untagged) == []
    # Mixed: only the tagged rows survive.
    mixed = untagged + [ROWS[0]]
    agg = pr.aggregate_to_county(mixed)
    assert {c["county"] for c in agg} == {"04013"}


def test_missing_precincts_reporting_is_none_never_zero():
    rows = [{**r} for r in ROWS[:1]]
    rows[0].pop("precincts_reporting")
    rows[0].pop("precincts_total")
    agg = pr.aggregate_to_county(rows)
    assert agg[0]["pct_reporting"] is None  # honest "not reported", not 0.0


def test_build_rows_passes_county_through():
    # E-R1's parser tags a Contest with `county`; build_rows must carry it so the rows feed
    # aggregate_to_county. Also the schema validates with the county field present.
    from datetime import datetime, timezone

    contests = [{"office": "senate", "candidate": "Jane Doe", "party": "D", "votes": 100,
                 "county": "04013", "precincts_reporting": 5, "precincts_total": 10}]
    rows = pr.build_rows("AZ", contests, source_url="https://azsos/",
                         election_type="primary",
                         as_of=datetime(2026, 8, 4, tzinfo=timezone.utc))
    assert rows[0]["county"] == "04013"
    pr.ResultRow.model_validate(rows[0])  # county field on the published schema
    # Untagged contest → county None (default, honest-empty).
    plain = pr.build_rows("OH", [{"office": "senate", "candidate": "A", "votes": 1}],
                          source_url="u", election_type="primary",
                          as_of=datetime(2026, 8, 4, tzinfo=timezone.utc))
    assert plain[0]["county"] is None
