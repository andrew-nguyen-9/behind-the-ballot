from btb_pipeline.finance_aggregates import build_finance, rollup_by_race

FEC_ROWS = [
    {"candidate_id": "S0OH1", "receipts": 1000.0, "disbursements": 600.0,
     "last_cash_on_hand_end_period": 400.0, "coverage_end_date": "2026-03-31"},
    {"candidate_id": "S0OH2", "receipts": 800.0, "disbursements": 800.0,
     "last_cash_on_hand_end_period": 50.0, "coverage_end_date": "2026-03-31"},
    {"candidate_id": "Z9NONE", "receipts": 0.0, "disbursements": 0.0,
     "last_cash_on_hand_end_period": 0.0},
]
META = {
    "S0OH1": {"race_id": "us-senate-2026-OH", "party": "D"},
    "S0OH2": {"race_id": "us-senate-2026-OH", "party": "R"},
}


def test_build_finance_joins_and_derives():
    rows = build_finance(FEC_ROWS, META)
    by_id = {r["candidate_id"]: r for r in rows}
    assert by_id["S0OH1"]["race_id"] == "us-senate-2026-OH"
    assert by_id["S0OH1"]["burn_rate"] == 0.6  # 600/1000
    assert by_id["S0OH2"]["burn_rate"] == 1.0  # spent everything
    assert by_id["Z9NONE"]["burn_rate"] is None  # no receipts -> guard
    assert by_id["Z9NONE"]["race_id"] is None  # unknown candidate passes through
    assert by_id["S0OH1"]["coverage_end_date"] == "2026-03-31"
    # sorted by candidate_id
    assert [r["candidate_id"] for r in rows] == ["S0OH1", "S0OH2", "Z9NONE"]


def test_rollup_by_race_totals_party_split_and_leader():
    rows = build_finance(FEC_ROWS, META)
    races = rollup_by_race(rows)
    assert len(races) == 1  # Z9NONE has no race_id -> skipped
    oh = races[0]
    assert oh["race_id"] == "us-senate-2026-OH"
    assert oh["total_raised"] == 1800.0  # 1000 + 800
    assert oh["by_party"] == {"D": 1000.0, "R": 800.0}
    assert oh["coh_leader"] == "S0OH1"  # 400 > 50
    assert "_coh" not in oh  # internal field stripped
