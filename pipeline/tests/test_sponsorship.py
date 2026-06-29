"""Sponsorship-counts connector [v1.6.4] — fixture-tested, no live calls."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import sponsorship as sp


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


def _count(n):
    return json.dumps({"pagination": {"count": n}})


def test_parse_count_reads_pagination():
    assert sp.parse_count(_count(199)) == 199
    assert sp.parse_count(json.dumps({"pagination": {}})) == 0  # missing → 0


def test_get_api_key_raises_without_env(monkeypatch):
    monkeypatch.delenv("DATA_GOV_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DATA_GOV_API_KEY"):
        sp.get_api_key()


def test_run_counts_per_member_integrity_clean(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "test-key")
    counts = {"P000197": {"sponsored": 199, "cosponsored": 5083}}
    urls = []

    def transport(url, headers):
        urls.append(url)
        bid = "P000197" if "P000197" in url else "X000000"
        kind = "sponsored" if "sponsored-legislation" in url and "cosponsored" not in url else "cosponsored"
        return FakeResp(200, _count(counts.get(bid, {}).get(kind, 0)), {"ETag": "e"})

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = sp.run(fetcher=CachingFetcher(tmp_path / "b", transport),
                  bioguide_ids=["P000197", "X000000"], as_of=now, root=tmp_path)
    payload = json.loads(path.read_text())
    assert payload["source"] == "sponsorship"
    pelosi = next(r for r in payload["rows"] if r["bioguide_id"] == "P000197")
    assert pelosi["sponsored_count"] == 199
    assert pelosi["cosponsored_count"] == 5083
    assert "api_key=test-key" in urls[0]
    assert_artifact(payload, now=now)  # data-integrity gate [R14a]
