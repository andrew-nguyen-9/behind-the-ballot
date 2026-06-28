"""Connector base shared by every source [R2a,R10a,R4a,R8a]: conditional-request HTTP
cache, retry/backoff, natural-key upsert, last-good fallback.

Network transport is injected (a callable), so the whole framework is unit-tested with
fakes — no live calls. Real connectors pass `requests.get`. ponytail: a dict-on-disk
cache is plenty at this scale; swap for a real HTTP cache only if quota pressure demands.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, TypeVar

T = TypeVar("T")


class Response(Protocol):
    status_code: int
    headers: dict[str, str]
    text: str


# transport(url, headers) -> Response. requests.get fits this shape.
Transport = Callable[[str, dict[str, str]], Response]


def backoff_retry(fn: Callable[[], T], attempts: int = 3, base: float = 0.5,
                  sleep: Callable[[float], None] = time.sleep) -> T:
    """Run fn, retrying with exponential backoff [T8a]. Re-raises the last error.
    `base=0` (and/or a no-op sleep) makes tests instant."""
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 — connectors decide what's fatal upstream
            last = e
            if i < attempts - 1 and base:
                sleep(base * (2**i))
    assert last is not None
    raise last


def upsert(existing: list[dict], incoming: list[dict], key: str) -> list[dict]:
    """Merge incoming into existing by natural `key`, no truncate, re-runnable [R4a].
    Incoming wins on conflict; order: existing order preserved, new rows appended."""
    by_key = {row[key]: row for row in existing}
    order = [row[key] for row in existing]
    for row in incoming:
        k = row[key]
        if k not in by_key:
            order.append(k)
        by_key[k] = row
    return [by_key[k] for k in order]


@dataclass
class CachingFetcher:
    """Conditional-GET cache [R10a] with last-good fallback [R8a]. Caches body + ETag/
    Last-Modified per URL under cache_dir; sends validators on the next request; on 304
    or on transport failure returns the cached body."""

    cache_dir: Path
    transport: Transport
    attempts: int = 3
    base_delay: float = 0.5
    sleep: Callable[[float], None] = time.sleep

    def _path(self, url: str) -> Path:
        safe = "".join(c if c.isalnum() else "_" for c in url)
        return self.cache_dir / f"{safe}.json"

    def get(self, url: str) -> str:
        path = self._path(url)
        cached = json.loads(path.read_text()) if path.exists() else None

        headers: dict[str, str] = {}
        if cached:
            if cached.get("etag"):
                headers["If-None-Match"] = cached["etag"]
            if cached.get("last_modified"):
                headers["If-Modified-Since"] = cached["last_modified"]

        try:
            resp = backoff_retry(lambda: self.transport(url, headers),
                                 self.attempts, self.base_delay, self.sleep)
        except Exception:
            if cached:
                return cached["body"]  # last-good [R8a]
            raise

        if resp.status_code == 304 and cached:
            return cached["body"]
        if resp.status_code >= 400:
            if cached:
                return cached["body"]
            raise RuntimeError(f"GET {url} -> {resp.status_code} and no cached last-good")

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "body": resp.text,
            "etag": resp.headers.get("ETag"),
            "last_modified": resp.headers.get("Last-Modified"),
        }))
        return resp.text
