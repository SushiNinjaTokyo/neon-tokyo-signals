#!/usr/bin/env python3
"""Print which DuckDB file a workflow is using."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from lib.duckdb_build_metadata import read_metadata

TABLES_TO_SUMMARIZE = [
    "prices_daily",
    "features_daily",
    "agent_scores_daily",
    "fundamentals_latest_jp",
    "fundamentals_latest",
    "value_features_daily",
    "arena_simulation_runs",
    "arena_display_runs",
    "arena_orders",
    "arena_trades",
    "arena_open_positions",
    "arena_equity_curve",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default="data/cache/neon_tokyo_jp.duckdb")
    parser.add_argument("--fail-if-missing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)
    if not db_path.exists():
        msg = f"DuckDB file does not exist: {db_path}"
        if args.fail_if_missing:
            raise SystemExit(msg)
        print(msg)
        return 0

    print("DuckDB file:")
    print(f"- path={db_path}")
    print(f"- size_bytes={db_path.stat().st_size}")

    metadata = read_metadata(db_path)
    print("DuckDB build metadata:")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        print("DuckDB table row counts:")
        for table in TABLES_TO_SUMMARIZE:
            if table in tables:
                count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"- {table}: {count}")
            else:
                print(f"- {table}: MISSING")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
