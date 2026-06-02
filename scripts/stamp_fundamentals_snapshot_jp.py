#!/usr/bin/env python3
from __future__ import annotations

"""Append a weekly snapshot of fundamentals_latest_jp into DuckDB.

The purpose is not to re-create historical fundamentals retroactively.  It is to
start a durable weekly history now so HIZUMI can later compare current
fundamentals and valuation against 3m/6m prior snapshots.

The script is idempotent for a given snapshot_date: it deletes the same date and
reinserts the current latest fundamentals.
"""

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("PRICE_DUCKDB_PATH", "data/cache/neon_tokyo_jp.duckdb"))
SNAPSHOT_DATE = os.getenv("FUNDAMENTALS_SNAPSHOT_DATE", "").strip()
DIAG_JSON = Path(os.getenv("FUNDAMENTALS_SNAPSHOT_DIAG_JSON", "site/data/japan/ai-arena/diagnostics/fundamentals-snapshot-latest.json"))

SNAPSHOT_COLUMNS = [
    "symbol",
    "snapshot_date",
    "market_cap_jpy",
    "enterprise_value_jpy",
    "per",
    "pbr",
    "psr",
    "roe_pct",
    "roa_pct",
    "operating_margin_pct",
    "net_margin_pct",
    "revenue_growth_yoy_pct",
    "operating_profit_growth_yoy_pct",
    "eps_growth_yoy_pct",
    "dividend_yield_pct",
    "source",
    "created_at",
]


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    return bool(conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [table]).fetchone()[0])


def columns(conn: duckdb.DuckDBPyConnection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()}


def sql_expr(colset: set[str], name: str, fallback: str = "NULL") -> str:
    return name if name in colset else f"{fallback} AS {name}"


def main() -> int:
    db_path = resolve(DB_PATH)
    diag_json = resolve(DIAG_JSON)
    if not db_path.exists():
        raise FileNotFoundError(db_path)
    snap = SNAPSHOT_DATE or date.today().isoformat()
    created_at = datetime.now(timezone.utc).isoformat()

    conn = duckdb.connect(str(db_path))
    if not table_exists(conn, "fundamentals_latest_jp"):
        raise SystemExit("fundamentals_latest_jp table does not exist. Run fetch_fundamentals_jp.py first.")
    colset = columns(conn, "fundamentals_latest_jp")
    symbol_col = "symbol" if "symbol" in colset else "ticker" if "ticker" in colset else None
    if not symbol_col:
        raise SystemExit("fundamentals_latest_jp must have symbol or ticker column")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fundamentals_snapshot_jp (
          symbol VARCHAR,
          snapshot_date DATE,
          market_cap_jpy DOUBLE,
          enterprise_value_jpy DOUBLE,
          per DOUBLE,
          pbr DOUBLE,
          psr DOUBLE,
          roe_pct DOUBLE,
          roa_pct DOUBLE,
          operating_margin_pct DOUBLE,
          net_margin_pct DOUBLE,
          revenue_growth_yoy_pct DOUBLE,
          operating_profit_growth_yoy_pct DOUBLE,
          eps_growth_yoy_pct DOUBLE,
          dividend_yield_pct DOUBLE,
          source VARCHAR,
          created_at TIMESTAMP
        )
        """
    )
    conn.execute("DELETE FROM fundamentals_snapshot_jp WHERE snapshot_date = ?", [snap])

    select_exprs = [
        f"CAST({symbol_col} AS VARCHAR) AS symbol",
        "CAST(? AS DATE) AS snapshot_date",
        sql_expr(colset, "market_cap_jpy"),
        sql_expr(colset, "enterprise_value_jpy"),
        sql_expr(colset, "per"),
        sql_expr(colset, "pbr"),
        sql_expr(colset, "psr"),
        sql_expr(colset, "roe_pct"),
        sql_expr(colset, "roa_pct"),
        sql_expr(colset, "operating_margin_pct"),
        sql_expr(colset, "net_margin_pct"),
        sql_expr(colset, "revenue_growth_yoy_pct"),
        sql_expr(colset, "operating_profit_growth_yoy_pct"),
        sql_expr(colset, "eps_growth_yoy_pct"),
        sql_expr(colset, "dividend_yield_pct"),
        "'fundamentals_latest_jp' AS source",
        "CAST(? AS TIMESTAMP) AS created_at",
    ]
    conn.execute(
        f"INSERT INTO fundamentals_snapshot_jp ({', '.join(SNAPSHOT_COLUMNS)}) SELECT {', '.join(select_exprs)} FROM fundamentals_latest_jp WHERE {symbol_col} IS NOT NULL",
        [snap, created_at],
    )
    rows = int(conn.execute("SELECT COUNT(*) FROM fundamentals_snapshot_jp WHERE snapshot_date = ?", [snap]).fetchone()[0])
    total_dates = int(conn.execute("SELECT COUNT(DISTINCT snapshot_date) FROM fundamentals_snapshot_jp").fetchone()[0])
    min_date, max_date = conn.execute("SELECT MIN(snapshot_date), MAX(snapshot_date) FROM fundamentals_snapshot_jp").fetchone()

    diag = {
        "schema_version": "fundamentals_snapshot_jp_diag_v1",
        "generated_at": created_at,
        "duckdb": str(db_path),
        "snapshot_date": snap,
        "inserted_rows": rows,
        "snapshot_date_count": total_dates,
        "min_snapshot_date": str(min_date) if min_date else None,
        "max_snapshot_date": str(max_date) if max_date else None,
    }
    diag_json.parent.mkdir(parents=True, exist_ok=True)
    diag_json.write_text(json.dumps(diag, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"fundamentals_snapshot_jp snapshot_date={snap} inserted_rows={rows} snapshot_date_count={total_dates}")
    print(f"Wrote {diag_json}")
    conn.close()
    if rows <= 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
