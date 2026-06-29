"""Live joins — export baked gold artifacts into the committed per-page JSON the Astro site reads
[ADR 0002: baked JSON on the CDN]. The site is static (SSG, 0-JS) so data must exist at BUILD
time; gold (`data/gold/*`) is gitignored/ephemeral, so this step writes the derived, display-ready
JSON into `apps/web/src/data/*` which IS committed and ships in the Cloudflare build.

Run after a bake (`python -m btb_pipeline.cli bake all`), then locally or in the nightly Action:

    uv run --project pipeline python -m btb_pipeline.export_web

ponytail: one export fn per domain, a flat dispatch — add a domain by adding a function. Each
reads gold + reuses the existing transform math, writes one JSON file. Missing gold → the domain
is skipped (the committed sample stays), so a partial bake never corrupts the site.
"""

from __future__ import annotations

import json
from pathlib import Path

from btb_pipeline.core import DATA_ROOT, stage_dir

WEB_DATA = Path("apps/web/src/data")

PARTY_LETTER = {"Democrat": "D", "Republican": "R", "Independent": "I"}


def _gold(source: str, root: Path) -> list[dict] | None:
    path = stage_dir("gold", source, root) / f"{source}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text()).get("rows", [])


def _party_letter(party: str | None) -> str:
    if not party:
        return "?"
    return PARTY_LETTER.get(party, party[0].upper())


def export_members(root: Path = DATA_ROOT, web_data: Path = WEB_DATA) -> Path | None:
    """gold/members ⋈ gold/voteview (ideology) → src/data/members/roster.json [M1a,M3a]."""
    members = _gold("members", root)
    if members is None:
        return None
    ideology = {r["bioguide_id"]: r.get("nominate_dim1") for r in (_gold("voteview", root) or [])}
    roster = [
        {
            "bioguide_id": m["bioguide_id"],
            "name": m.get("name"),
            "party": _party_letter(m.get("party")),
            "state": m.get("state"),
            "chamber": m.get("chamber"),
            "district": m.get("district"),
            "nominate_dim1": ideology.get(m["bioguide_id"]),
        }
        for m in members
        if m.get("bioguide_id")
    ]
    out = web_data / "members" / "roster.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(roster, indent=2) + "\n")
    return out


EXPORTERS = {"members": export_members}


def main() -> int:
    for name, fn in EXPORTERS.items():
        path = fn()
        print(f"exported {name}: {path}" if path else f"skipped {name}: no gold artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
