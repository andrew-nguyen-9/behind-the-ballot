"""Roll-call (Congress.gov House) connector [v1.6.2] — fixture-tested, no live calls."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import rollcall


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


def _page(votes):
    return json.dumps({"houseRollCallVotes": votes})


VOTE = {
    "identifier": 11912025240,
    "congress": 119,
    "sessionNumber": 1,
    "rollCallNumber": 240,
    "result": "Passed",
    "voteType": "2/3 Yea-And-Nay",
    "legislationType": "HR",
    "legislationNumber": "3424",
    "legislationUrl": "https://www.congress.gov/bill/119/house-bill/3424",
    "startDate": "2025-09-08T18:56:00-04:00",
    "extra_field": "ignored",
}


def test_parse_maps_camelcase_and_drops_extra():
    rows = rollcall.parse_votes(_page([VOTE]))
    assert rows[0]["roll_call_number"] == 240
    assert rows[0]["legislation_number"] == "3424"
    assert rows[0]["result"] == "Passed"
    assert "extra_field" not in rows[0]


def test_parse_rejects_missing_required():
    with pytest.raises(Exception):
        rollcall.parse_votes(_page([{"congress": 119, "sessionNumber": 1}]))  # no identifier


def test_get_api_key_raises_without_env(monkeypatch):
    monkeypatch.delenv("DATA_GOV_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DATA_GOV_API_KEY"):
        rollcall.get_api_key()


def test_run_bakes_integrity_clean_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "test-key")

    urls = []

    def transport(url, headers):
        urls.append(url)
        # distinct vote per session so upsert keeps both
        n = 240 if "/1?" in url else 12
        return FakeResp(200, _page([{**VOTE, "identifier": VOTE["identifier"] + n,
                                     "sessionNumber": 1 if "/1?" in url else 2}]), {"ETag": "e"})

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = rollcall.run(fetcher=CachingFetcher(tmp_path / "bronze", transport), as_of=now, root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["source"] == "rollcall"
    assert len(payload["rows"]) == 2  # one per session
    assert "api_key=test-key" in urls[0]
    assert_artifact(payload, now=now)  # passes the data-integrity gate [R14a]


def test_run_upserts_idempotently(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "k")

    def transport(url, headers):
        return FakeResp(200, _page([VOTE]))  # same identifier every call

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    rollcall.run(fetcher=CachingFetcher(tmp_path / "b1", transport), sessions=(1,), as_of=now, root=tmp_path)
    path = rollcall.run(fetcher=CachingFetcher(tmp_path / "b2", transport), sessions=(1,), as_of=now, root=tmp_path)
    assert len(json.loads(path.read_text())["rows"]) == 1  # not duplicated [R4a]
