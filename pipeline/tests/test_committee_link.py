"""Candidate→committee linkage connector [v1.3.2] — fixture-tested, no live calls."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import committee_link as cl


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


def _resp(results):
    return json.dumps({"results": results})


PRINCIPAL = {"committee_id": "C00P", "name": "Doe for Senate", "designation": "P",
             "candidate_ids": ["S0OH1"]}
JOINT = {"committee_id": "C00J", "name": "Joint Fund", "designation": "J",
         "candidate_ids": ["S0OH1", "S0PA2"]}


def test_parse_picks_principal_only():
    link = cl.parse_principal(_resp([JOINT, PRINCIPAL]), "S0OH1")
    assert link["committee_id"] == "C00P"
    assert link["candidate_id"] == "S0OH1"


def test_parse_returns_none_when_no_principal():
    assert cl.parse_principal(_resp([JOINT]), "S0OH1") is None


def test_parse_ignores_principal_of_other_candidate():
    other = {**PRINCIPAL, "candidate_ids": ["S0XX9"]}
    assert cl.parse_principal(_resp([other]), "S0OH1") is None


def test_get_api_key_raises_without_env(monkeypatch):
    monkeypatch.delenv("DATA_GOV_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DATA_GOV_API_KEY"):
        cl.get_api_key()


def test_run_links_explicit_ids_integrity_clean(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "test-key")
    urls = []

    def transport(url, headers):
        urls.append(url)
        cid = "S0OH1" if "S0OH1" in url else "H0PA5"
        return FakeResp(200, _resp([{**PRINCIPAL, "committee_id": f"C{cid}",
                                     "candidate_ids": [cid]}]), {"ETag": "e"})

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = cl.run(fetcher=CachingFetcher(tmp_path / "b", transport),
                  candidate_ids=["S0OH1", "H0PA5"], as_of=now, root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["source"] == "committee_link"
    assert {r["candidate_id"] for r in payload["rows"]} == {"S0OH1", "H0PA5"}
    assert "api_key=test-key" in urls[0]
    assert_artifact(payload, now=now)  # data-integrity gate [R14a]
