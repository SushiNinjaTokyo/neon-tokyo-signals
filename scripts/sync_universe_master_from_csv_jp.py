#!/usr/bin/env python3
from __future__ import annotations

"""Synchronize universe_master in DuckDB from the AI Arena JP universe CSV.

This is intentionally small and deterministic.  It is used by GitHub Actions
before price/fundamental/feature builders so a freshly bootstrapped DuckDB has
both prices_daily and the metadata table expected by downstream joins.
"""

import argparse
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from lib.db import connect_db, safe_rel
from lib.duckdb_schema import initialize_schema

DEFAULT_DUCKDB_PATH = "data/cache/neon_tokyo_jp.duckdb"
DEFAULT_UNIVERSE_CSV = "data/universe/jp_duckdb_trial_300.csv"

UNIVERSE_COLUMNS = [
    "ticker",
    "code",
    "name",
    "market",
    "sector",
    "industry",
    "theme",
    "bucket",
    "priority",
    "asset_type",
    "is_topix500",
    "is_jpx_prime150",
    "is_growth250",
    "is_jpx_startup100",
    "is_core",
    "is_growth",
    "is_small_discovery",
    "is_value_candidate",
    "is_excluded",
    "exclude_reason",
    "source_detail",
    "source_url",
    "updated_at",
]


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "t"}


def normalize_jp_ticker(raw: Any) -> str:
    s = str(raw or "").strip().upper()
    if not s:
        return ""
    s = s.replace(".JP", ".T")
    if s.endswith(".T"):
        return s
    if s.isdigit():
        return f"{s}.T"
    return s


def ticker_code(ticker: str, raw_code: Any = None) -> str:
    code = str(raw_code or "").strip()
    if code:
        return code[:-2] if code.upper().endswith(".T") else code
    return ticker[:-2] if ticker.endswith(".T") else ticker


def first_present(row: dict[str, Any], *names: str) -> Any:
    lower = {str(k).lower().strip(): k for k in row.keys()}
    for name in names:
        key = lower.get(name.lower().strip())
        if key is not None:
            value = row.get(key)
            if value not in (None, ""):
                return value
    return ""


def derive_flags(row: dict[str, Any]) -> dict[str, bool]:
    bucket = str(first_present(row, "bucket") or "").strip().lower()
    priority = str(first_present(row, "priority") or "").strip().upper()
    theme = str(first_present(row, "theme") or "").strip().lower()
    source_detail = str(first_present(row, "source_detail", "sources", "primary_source") or "").strip().lower()

    is_topix500 = truthy(first_present(row, "is_topix500")) or bucket in {"core", "topix500"} or "topix500" in source_detail
    is_jpx_prime150 = truthy(first_present(row, "is_jpx_prime150")) or "prime150" in source_detail
    is_growth250 = truthy(first_present(row, "is_growth250")) or "growth250" in source_detail or "growth" in bucket
    is_jpx_startup100 = truthy(first_present(row, "is_jpx_startup100")) or "startup100" in source_detail or "jpx_startup100" in source_detail

    is_core = is_topix500 or is_jpx_prime150 or bucket == "core"
    is_growth = is_growth250 or is_jpx_startup100 or "growth" in bucket
    is_small_discovery = bucket in {"discovery", "small", "small_discovery"} or is_growth250 or is_jpx_startup100
    is_value_candidate = is_jpx_prime150 or priority in {"A", "B"} or bucket == "core" or is_core

    if "value" in theme:
        is_value_candidate = True

    return {
        "is_topix500": is_topix500,
        "is_jpx_prime150": is_jpx_prime150,
        "is_growth250": is_growth250,
        "is_jpx_startup100": is_jpx_startup100,
        "is_core": is_core,
        "is_growth": is_growth,
        "is_small_discovery": is_small_discovery,
        "is_value_candidate": is_value_candidate,
    }


def load_rows(universe_csv: Path) -> list[dict[str, Any]]:
    if not universe_csv.exists():
        raise FileNotFoundError(f"universe csv not found: {universe_csv}")

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    updated_at = datetime.utcnow()

    with universe_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"universe csv has no header: {universe_csv}")
        for raw in reader:
            ticker = normalize_jp_ticker(first_present(raw, "ticker", "symbol", "code", "銘柄コード"))
            if not ticker or ticker in seen:
                continue
            seen.add(ticker)
            flags = derive_flags(raw)
            bucket = str(first_present(raw, "bucket") or "").strip()
            priority = str(first_present(raw, "priority") or "").strip()
            rows.append(
                {
                    "ticker": ticker,
                    "code": ticker_code(ticker, first_present(raw, "code")),
                    "name": str(first_present(raw, "name", "company", "company_name", "銘柄名") or ticker).strip() or ticker,
                    "market": str(first_present(raw, "market") or "JP").strip() or "JP",
                    "sector": str(first_present(raw, "sector") or "").strip(),
                    "industry": str(first_present(raw, "industry") or "").strip(),
                    "theme": str(first_present(raw, "theme") or "").strip(),
                    "bucket": bucket,
                    "priority": priority,
                    "asset_type": str(first_present(raw, "asset_type") or "equity").strip() or "equity",
                    **flags,
                    "is_excluded": truthy(first_present(raw, "is_excluded", "excluded")),
                    "exclude_reason": str(first_present(raw, "exclude_reason") or "").strip(),
                    "source_detail": str(first_present(raw, "source_detail", "sources", "primary_source") or "").strip(),
                    "source_url": str(first_present(raw, "source_url") or "").strip(),
                    "updated_at": updated_at,
                }
            )

    if not rows:
        raise ValueError(f"universe csv produced zero rows: {universe_csv}")
    return rows


def sync_universe_master(db_path: str, universe_csv: str) -> dict[str, Any]:
    db = Path(db_path)
    csv_path = Path(universe_csv)
    db.parent.mkdir(parents=True, exist_ok=True)

    rows = load_rows(csv_path)
    conn = connect_db(str(db))
    initialize_schema(conn)

    df = pd.DataFrame(rows)
    for col in UNIVERSE_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[UNIVERSE_COLUMNS]

    conn.register("_universe_sync_rows", df)
    conn.execute("DELETE FROM universe_master USING _universe_sync_rows r WHERE universe_master.ticker = r.ticker")
    cols = ", ".join(UNIVERSE_COLUMNS)
    conn.execute(f"INSERT INTO universe_master ({cols}) SELECT {cols} FROM _universe_sync_rows")
    conn.unregister("_universe_sync_rows")

    row_count = conn.execute("SELECT COUNT(*) FROM universe_master").fetchone()[0]
    equity_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM universe_master
        WHERE COALESCE(asset_type, 'equity') = 'equity'
          AND COALESCE(is_excluded, FALSE) = FALSE
        """
    ).fetchone()[0]
    conn.close()

    return {
        "db_path": safe_rel(db),
        "universe_csv": safe_rel(csv_path),
        "csv_rows_loaded": len(rows),
        "universe_master_rows": int(row_count or 0),
        "universe_master_equity_rows": int(equity_count or 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync JP universe CSV to DuckDB universe_master")
    parser.add_argument("--db-path", default=os.getenv("PRICE_DUCKDB_PATH", DEFAULT_DUCKDB_PATH))
    parser.add_argument("--universe-csv", default=os.getenv("UNIVERSE_CSV", DEFAULT_UNIVERSE_CSV))
    args = parser.parse_args()

    result = sync_universe_master(args.db_path, args.universe_csv)
    print("=== universe_master sync ===")
    for k, v in result.items():
        print(f"{k}: {v}")
    if result["universe_master_equity_rows"] <= 0:
        raise SystemExit("universe_master has no active equity rows after sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
