"""ETL CLI. `--dry-run` validates without writing [R6a]; otherwise bakes the gold
artifact. Real CLI gains `--cycle --since` backfill + per-source dispatch in v1.1.1 [R13a].

    uv run --project pipeline python -m btb_pipeline.cli --dry-run
    uv run --project pipeline python -m btb_pipeline.cli
"""

from __future__ import annotations

import argparse

from btb_pipeline.core import bake, dry_run, is_fresh
from btb_pipeline.sources import sample


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="btb-etl")
    p.add_argument("--dry-run", action="store_true", help="validate sources+schema, no write")
    args = p.parse_args(argv)

    raw = sample.fetch_raw()
    if args.dry_run:
        n = dry_run(sample.SampleRow, raw)
        print(f"dry-run ok: {sample.SPEC.name} validated {n} rows")
        return 0

    when = sample.as_of()
    path = bake(sample.SPEC, sample.SampleRow, raw, when)
    print(f"baked {path} (fresh={is_fresh(when, sample.SPEC.freshness_floor_days)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
