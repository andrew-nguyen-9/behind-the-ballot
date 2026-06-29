import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from btb_pipeline.connector import CachingFetcher
from btb_pipeline.integrity import assert_artifact
from btb_pipeline.sources import acs


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


SAMPLE = json.dumps([
    ["NAME", "B01001_001E", "B19013_001E", "state", "congressional district"],
    ["Congressional District 3, Ohio", "700000", "65000", "39", "03"],
    ["Congressional District 5, Pennsylvania", "710000", "-666666666", "42", "05"],
])


def test_parse_rejects_missing_key_html():
    with pytest.raises(RuntimeError, match="CENSUS_API_KEY"):
        acs.parse_acs("<!doctype html><html>missing_key</html>")


def test_parse_zips_headers_and_builds_geoid():
    rows = acs.parse_acs(SAMPLE)
    assert len(rows) == 2
    oh = next(r for r in rows if r["geoid"] == "3903")
    assert oh["name"] == "Congressional District 3, Ohio"
    assert oh["state"] == "39"
    assert oh["district"] == "03"
    assert oh["population"] == 700000  # numeric coercion
    assert oh["median_income"] == 65000


def test_parse_maps_census_null_sentinel_to_none():
    rows = acs.parse_acs(SAMPLE)
    pa = next(r for r in rows if r["geoid"] == "4205")
    assert pa["population"] == 710000
    assert pa["median_income"] is None  # "-666666666" -> None


def test_get_api_key_raises_without_env(monkeypatch):
    # hermetic: ACS reads CENSUS_API_KEY first, falling back to DATA_GOV_API_KEY — clear both
    monkeypatch.delenv("CENSUS_API_KEY", raising=False)
    monkeypatch.delenv("DATA_GOV_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="CENSUS_API_KEY"):
        acs.get_api_key()


def test_run_bakes_integrity_clean_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "test")
    monkeypatch.delenv("DATA_GOV_API_KEY", raising=False)

    calls = {"urls": []}

    def transport(url, headers):
        calls["urls"].append(url)
        return FakeResp(200, SAMPLE, {"ETag": "e"})

    fetcher = CachingFetcher(tmp_path / "bronze", transport)
    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    path = acs.run(fetcher=fetcher, as_of=now, root=tmp_path)

    payload = json.loads(path.read_text())
    assert payload["source"] == "census_acs"
    assert {r["geoid"] for r in payload["rows"]} == {"3903", "4205"}
    assert "key=test" in calls["urls"][0]
    assert_artifact(payload, now=now)  # passes the data-integrity gate [R14a]


def test_run_upserts_idempotently(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_GOV_API_KEY", "test")

    def transport(url, headers):
        return FakeResp(200, SAMPLE)

    now = datetime(2026, 6, 28, tzinfo=timezone.utc)
    # two runs -> still two rows, no duplicate geoid [R4a]
    acs.run(fetcher=CachingFetcher(tmp_path / "b1", transport), as_of=now, root=tmp_path)
    path = acs.run(fetcher=CachingFetcher(tmp_path / "b2", transport), as_of=now, root=tmp_path)
    rows = json.loads(path.read_text())["rows"]
    assert len(rows) == 2
    assert len({r["geoid"] for r in rows}) == 2
