#!/usr/bin/env python3
"""Stamp DuckDB with source metadata before publishing it as the canonical DB."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.duckdb_build_metadata import write_metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--source-workflow", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-run-attempt", default="")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--source-ref", default="")
    parser.add_argument("--artifact-kind", default="github-release-asset")
    parser.add_argument("--release-tag", default="ai-arena-duckdb-latest")
    parser.add_argument("--asset-name", default="neon_tokyo_jp_latest.duckdb.zst")
    parser.add_argument("--manifest-path", default="data/cache/neon_tokyo_jp_latest_manifest.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)
    if not db_path.exists():
        raise SystemExit(f"DuckDB file not found: {db_path}")

    metadata = write_metadata(
        db_path,
        {
            "build_id": f"{args.source_run_id}-{args.source_run_attempt or '1'}",
            "source_workflow": args.source_workflow,
            "source_run_id": args.source_run_id,
            "source_run_attempt": args.source_run_attempt or "1",
            "source_sha": args.source_sha,
            "source_ref": args.source_ref,
            "artifact_kind": args.artifact_kind,
            "release_tag": args.release_tag,
            "asset_name": args.asset_name,
        },
    )

    manifest = {
        "schema_version": "neon_tokyo_duckdb_release_manifest_v1",
        "db_path": str(db_path),
        "db_size_bytes": db_path.stat().st_size,
        "metadata": metadata,
    }
    manifest_path = Path(args.manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Stamped DuckDB metadata")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Wrote manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
