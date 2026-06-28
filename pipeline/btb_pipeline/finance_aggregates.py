"""Finance aggregates [G13a]: reshape FEC candidate totals into per-candidate+race
finance rows (with coverage-end-date display + burn rate) and per-race rollups the
finance UI consumes. Pure transform over the `fec` gold artifact joined to candidate
metadata (race_id, party) from the roster/race configs.

ponytail: a join + a few derived fields; no new data source. Live FEC numbers flow in
once the connector runs — the transform is unchanged.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FinanceRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: str
    race_id: str | None = None
    party: str | None = None
    receipts: float = 0.0
    disbursements: float = 0.0
    cash_on_hand: float = 0.0
    burn_rate: float | None = None  # disbursements / receipts
    coverage_end_date: str | None = None  # "through <date>" [G13a]


def _burn_rate(receipts: float, disbursements: float) -> float | None:
    return round(disbursements / receipts, 4) if receipts > 0 else None


def build_finance(fec_rows: list[dict], candidate_meta: dict[str, dict]) -> list[dict]:
    """Join FEC totals to candidate metadata -> validated per-candidate finance rows.
    candidate_meta maps candidate_id -> {race_id?, party?}. Unknown candidates still
    pass through (race_id/party None). Sorted by candidate_id [R7a]."""
    out: list[dict] = []
    for r in fec_rows:
        cid = r["candidate_id"]
        meta = candidate_meta.get(cid, {})
        receipts = float(r.get("receipts", 0.0))
        disbursements = float(r.get("disbursements", 0.0))
        out.append(
            FinanceRow.model_validate({
                "candidate_id": cid,
                "race_id": meta.get("race_id"),
                "party": meta.get("party"),
                "receipts": receipts,
                "disbursements": disbursements,
                "cash_on_hand": float(r.get("last_cash_on_hand_end_period", 0.0)),
                "burn_rate": _burn_rate(receipts, disbursements),
                "coverage_end_date": r.get("coverage_end_date"),
            }).model_dump()
        )
    return sorted(out, key=lambda x: x["candidate_id"])


def rollup_by_race(finance_rows: list[dict]) -> list[dict]:
    """Per-race totals + party split + cash-on-hand leader. Rows with no race_id skipped.
    Sorted by race_id."""
    races: dict[str, dict] = {}
    for r in finance_rows:
        rid = r.get("race_id")
        if not rid:
            continue
        agg = races.setdefault(
            rid, {"race_id": rid, "total_raised": 0.0, "by_party": {}, "coh_leader": None, "_coh": -1.0}
        )
        agg["total_raised"] = round(agg["total_raised"] + r["receipts"], 2)
        party = r.get("party") or "other"
        agg["by_party"][party] = round(agg["by_party"].get(party, 0.0) + r["receipts"], 2)
        if r["cash_on_hand"] > agg["_coh"]:
            agg["_coh"] = r["cash_on_hand"]
            agg["coh_leader"] = r["candidate_id"]
    for agg in races.values():
        del agg["_coh"]
    return sorted(races.values(), key=lambda x: x["race_id"])
