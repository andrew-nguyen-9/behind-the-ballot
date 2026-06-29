"""ETL CLI — per-source dispatch [v1.1.6, R13a].

    uv run --project pipeline python -m btb_pipeline.cli --dry-run        # sample, no write
    uv run --project pipeline python -m btb_pipeline.cli                  # bake sample
    uv run --project pipeline python -m btb_pipeline.cli bake members     # live bake one source
    uv run --project pipeline python -m btb_pipeline.cli bake all         # live bake every source

Live sources fetch over the network (FEC/ACS are env-keyed via DATA_GOV_API_KEY); each
connector's `run()` does fetch -> validate -> upsert -> bake gold. ponytail: a flat
name->run registry, no plugin framework — add a source by adding one dict entry.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from btb_pipeline.core import bake, dry_run, is_fresh
from btb_pipeline.sources import (
    acs,
    committee_link,
    fec,
    members,
    polls,
    pollster_ratings,
    rollcall,
    sample,
    sponsorship,
    voteview,
)

# name -> live bake callable (arg-free; defaults fetch over the network) [R13a]
SOURCES: dict[str, Callable[[], Path]] = {
    "fec": fec.run,
    "committee_link": committee_link.run,
    "members": members.run,
    "acs": acs.run,
    "polls": polls.run,
    "pollster_ratings": pollster_ratings.run,
    "rollcall": rollcall.run,
    "sponsorship": sponsorship.run,
    "voteview": voteview.run,
}


def _bake_sample(dry: bool) -> int:
    raw = sample.fetch_raw()
    if dry:
        n = dry_run(sample.SampleRow, raw)
        print(f"dry-run ok: {sample.SPEC.name} validated {n} rows")
        return 0
    when = sample.as_of()
    path = bake(sample.SPEC, sample.SampleRow, raw, when)
    print(f"baked {path} (fresh={is_fresh(when, sample.SPEC.freshness_floor_days)})")
    return 0


def _bake_source(name: str) -> int:
    path = SOURCES[name]()
    print(f"baked {name}: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="btb-etl")
    p.add_argument("--dry-run", action="store_true", help="validate sample, no write")
    p.add_argument(
        "command", nargs="?", default="sample",
        help="'sample' (default) or 'bake'",
    )
    p.add_argument(
        "source", nargs="?",
        help="with 'bake': a source name (%s) or 'all'" % ", ".join(SOURCES),
    )
    args = p.parse_args(argv)

    if args.command == "sample":
        return _bake_sample(args.dry_run)

    if args.command == "bake":
        if args.source in (None, "all"):
            if args.source is None:
                p.error("bake needs a source name or 'all'")
            for name in SOURCES:
                _bake_source(name)
            return 0
        if args.source not in SOURCES:
            p.error(f"unknown source {args.source!r}; choices: {', '.join(SOURCES)}, all")
        return _bake_source(args.source)

    p.error(f"unknown command {args.command!r}")
    return 2  # unreachable; argparse.error exits


if __name__ == "__main__":
    raise SystemExit(main())
