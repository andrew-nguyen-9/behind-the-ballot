"""Budget alarm [v1.10.4] — alerts at 80% of the one quota the pipeline actually consumes:
the **api.data.gov** rate limit (FEC + Congress.gov go through it), read from the `X-RateLimit-*`
response headers [T9a]. Emails via the shared notifier when usage crosses the threshold.

The other "budgets" in the plan are N/A for V1 by construction, documented here so it's a decision
not an omission: GitHub **Actions minutes** — this repo is public, so Actions are unlimited/free;
**R2** — storage/egress is ~0 until the PMTiles map ships (v1.1.2, deferred). Revisit both if the
repo goes private or R2 starts hosting tiles. ponytail: `check_quota` is pure (tested); only `run`
touches the wire, reusing `notify.send_email`.

    uv run --project pipeline python -m btb_pipeline.budget            # check + alert if >=80%
    uv run --project pipeline python -m btb_pipeline.budget --dry-run  # print status, never email
"""

from __future__ import annotations

import os
import sys

from btb_pipeline import notify

# A cheap api.data.gov-keyed endpoint just to read the rate-limit headers (1 call).
PROBE_URL = "https://api.open.fec.gov/v1/candidates/?per_page=1&api_key={key}"
THRESHOLD = 0.8


def check_quota(limit: int, remaining: int, threshold: float = THRESHOLD) -> tuple[bool, float, str]:
    """Pure: (breached, used_fraction, message). breached when used/limit >= threshold."""
    if limit <= 0:
        return False, 0.0, "api.data.gov: no rate-limit header (skipped)"
    used = max(0, limit - remaining)
    frac = used / limit
    msg = f"api.data.gov: {used}/{limit} used ({frac:.0%}) this window"
    return frac >= threshold, frac, msg


def _probe_headers(key: str) -> tuple[int, int]:
    import requests

    r = requests.get(PROBE_URL.format(key=key), timeout=30)
    h = r.headers
    return int(h.get("X-RateLimit-Limit", 0)), int(h.get("X-RateLimit-Remaining", 0))


def run(argv: list[str] | None = None) -> int:
    dry = "--dry-run" in (argv if argv is not None else sys.argv[1:])
    key = os.environ.get("DATA_GOV_API_KEY", "")
    if not key:
        raise RuntimeError("DATA_GOV_API_KEY not set — see docs/SETUP_SECRETS.md")
    limit, remaining = _probe_headers(key)
    breached, _frac, msg = check_quota(limit, remaining)
    print(msg)
    if breached and not dry:
        notify.send_email("Behind the Ballot — BUDGET ALARM (api.data.gov >=80%)", msg)
        print("alert sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
