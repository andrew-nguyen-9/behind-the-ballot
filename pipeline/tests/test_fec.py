import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import fec


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


def _page(results):
    return json.dumps({"results": results})


def test_parse_totals_validates_and_drops_extra_fields():
    body = _page([
        {"candidate_id": "S0OH1", "name": "Doe", "cycle": 2026, "receipts": 10.0,
         "junk_field": "ignored", "coverage_end_date": "2026-03-31"},
    ])
    rows = fec.parse_totals(body)
    assert rows[0]["candidate_id"] == "S0OH1"
    assert "junk_field" not in rows[0]


def test_parse_totals_rejects_missing_required():
    with pytest.raises(Exception):
        fec.parse_totals(_page([{"name": "no id", "cycle": 2026}]))


def test_get_api_key_raises_without_env(monkeypatch):
    monkeypatch.delenv("DATA_GOV_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DATA_GOV_API_KEY"):
        fec.get_api_key()


def test_run_bakes_integrity_clean_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "test-key")

    calls = {"urls": []}

    def transport(url, headers):
        calls["urls"].append(url)
        # senate page then house page; one candidate each
        cid = "S0OH1" if "office=S" in url else "H0PA5"
        return FakeResp(200, _page([
            {"candidate_id": cid, "name": "X", "cycle": 2026, "receipts": 5.0},
        ]), {"ETag": "e"})

    fetcher = CachingFetcher(tmp_path / "bronze", transport)
    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = fec.run(fetcher=fetcher, as_of=now, root=tmp_path)

    payload = json.loads(path.read_text())
    assert payload["source"] == "fec"
    assert {r["candidate_id"] for r in payload["rows"]} == {"S0OH1", "H0PA5"}
    assert "api_key=test-key" in calls["urls"][0]
    assert_artifact(payload, now=now)  # passes the data-integrity gate [R14a]


def test_run_upserts_idempotently(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "k")

    def transport(url, headers):
        return FakeResp(200, _page([
            {"candidate_id": "S0OH1", "name": "X", "cycle": 2026, "receipts": 7.0},
        ]))

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    # two runs (offices=S only) -> still one row, not duplicated [R4a]
    fec.run(fetcher=CachingFetcher(tmp_path / "b1", transport), offices=("S",), as_of=now, root=tmp_path)
    path = fec.run(fetcher=CachingFetcher(tmp_path / "b2", transport), offices=("S",), as_of=now, root=tmp_path)
    rows = json.loads(path.read_text())["rows"]
    assert len(rows) == 1
