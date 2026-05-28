from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import duckdb

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DUCKDB_PATH = ROOT / "data" / "cache" / "neon_tokyo_jp.duckdb"


def resolve_project_path(value: str | Path | None, default: Path = DEFAULT_DUCKDB_PATH) -> Path:
    if value is None or str(value).strip() == "":
        path = default
    else:
        path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def connect_db(path: str | Path | None = None, *, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    db_path = resolve_project_path(path or os.getenv("PRICE_DUCKDB_PATH"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path), read_only=read_only)


def safe_rel(path: str | Path) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(p)


def table_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    rows = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = ?
        """,
        [table_name],
    ).fetchone()
    return bool(rows and rows[0])


def scalar(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> Any:
    row = conn.execute(sql, params or []).fetchone()
    return row[0] if row else None
