#!/usr/bin/env python3
"""
DuckDB build metadata helpers for Neon Tokyo AI Arena.

GitHub Actions cache is not reliable as the source of truth for AI Arena state.
The canonical DuckDB is stored explicitly as a GitHub Release asset.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import duckdb

METADATA_TABLE = "duckdb_build_metadata"
SCHEMA_VERSION = "neon_tokyo_duckdb_state_v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_metadata_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {METADATA_TABLE} (
            key VARCHAR PRIMARY KEY,
            value VARCHAR,
            updated_at TIMESTAMP
        )
        """
    )


def write_metadata(db_path: str | Path, metadata: Dict[str, Any]) -> Dict[str, str]:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(path), read_only=False)
    try:
        ensure_metadata_table(con)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now_iso(),
            **{str(k): "" if v is None else str(v) for k, v in metadata.items()},
        }
        for key, value in payload.items():
            con.execute(
                f"""
                INSERT OR REPLACE INTO {METADATA_TABLE} (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                [key, value],
            )
        return payload
    finally:
        con.close()


def read_metadata(db_path: str | Path) -> Dict[str, str]:
    path = Path(db_path)
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "db_exists": "false", "db_path": str(path)}

    con = duckdb.connect(str(path), read_only=True)
    try:
        tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        if METADATA_TABLE not in tables:
            return {
                "schema_version": SCHEMA_VERSION,
                "db_exists": "true",
                "db_path": str(path),
                "metadata_table_exists": "false",
            }
        rows = con.execute(f"SELECT key, value FROM {METADATA_TABLE} ORDER BY key").fetchall()
        metadata = {str(k): "" if v is None else str(v) for k, v in rows}
        metadata.setdefault("schema_version", SCHEMA_VERSION)
        metadata["db_exists"] = "true"
        metadata["db_path"] = str(path)
        metadata["metadata_table_exists"] = "true"
        return metadata
    finally:
        con.close()
