from dataclasses import dataclass, field

import pytest

from btb_pipeline.connector import CachingFetcher, backoff_retry, upsert


@dataclass
class FakeResp:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


# ---- upsert [R4a] ----

def test_upsert_merges_by_key_no_truncate():
    existing = [{"id": "a", "v": 1}, {"id": "b", "v": 2}]
    incoming = [{"id": "b", "v": 99}, {"id": "c", "v": 3}]
    out = upsert(existing, incoming, "id")
    assert out == [{"id": "a", "v": 1}, {"id": "b", "v": 99}, {"id": "c", "v": 3}]


# ---- backoff_retry [T8a] ----

def test_backoff_retries_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("boom")
        return "ok"

    assert backoff_retry(flaky, attempts=3, base=0, sleep=lambda _: None) == "ok"
    assert calls["n"] == 3


def test_backoff_reraises_after_exhausting():
    with pytest.raises(RuntimeError):
        backoff_retry(lambda: (_ for _ in ()).throw(RuntimeError("x")),
                      attempts=2, base=0, sleep=lambda _: None)


# ---- CachingFetcher [R10a,R8a] ----

def test_fetch_caches_and_sends_validators(tmp_path):
    seen = []

    def transport(url, headers):
        seen.append(headers)
        return FakeResp(200, text="payload-1", headers={"ETag": "v1"})

    f = CachingFetcher(tmp_path, transport)
    assert f.get("http://x/data") == "payload-1"
    # second call should carry If-None-Match from the cached ETag
    f.get("http://x/data")
    assert seen[1].get("If-None-Match") == "v1"


def test_304_returns_cached_body(tmp_path):
    state = {"first": True}

    def transport(url, headers):
        if state["first"]:
            state["first"] = False
            return FakeResp(200, text="payload", headers={"ETag": "v1"})
        return FakeResp(304)

    f = CachingFetcher(tmp_path, transport)
    assert f.get("http://x") == "payload"
    assert f.get("http://x") == "payload"  # 304 -> last cached


def test_transport_failure_falls_back_to_last_good(tmp_path):
    state = {"first": True}

    def transport(url, headers):
        if state["first"]:
            state["first"] = False
            return FakeResp(200, text="good", headers={})
        raise ConnectionError("down")

    f = CachingFetcher(tmp_path, transport, base_delay=0, sleep=lambda _: None)
    assert f.get("http://x") == "good"
    assert f.get("http://x") == "good"  # upstream down -> last-good [R8a]


def test_no_cache_and_failure_raises(tmp_path):
    def transport(url, headers):
        raise ConnectionError("down")

    f = CachingFetcher(tmp_path, transport, base_delay=0, sleep=lambda _: None)
    with pytest.raises(ConnectionError):
        f.get("http://x")
