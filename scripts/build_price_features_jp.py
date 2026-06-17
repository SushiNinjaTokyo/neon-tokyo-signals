#!/usr/bin/env python3
from __future__ import annotations

"""Rebuild JP technical features from canonical DuckDB prices_daily.

This small wrapper exists so GitHub Actions can explicitly materialize
features_daily before fundamentals/value/HIZUMI steps run.  build_agent_scores_jp
also rebuilds features internally, but relying on that side effect is too late
for build_value_features_jp during a fresh canonical DuckDB bootstrap.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from lib.db import ROOT, connect_db, safe_rel, scalar
from lib.feature_engine_jp import rebuild_features
from lib.duckdb_schema import initialize_schema

PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()
DIAG_PATH = OUT_DIR / "data" / "japan" / "ai-arena" / "diagnostics" / "price-features.json"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    db_path = Path(PRICE_DUCKDB_PATH)
    if not db_path.exists():
        raise SystemExit(f"DuckDB not found: {PRICE_DUCKDB_PATH}. Run fetch_prices_jp.py first.")

    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)

    universe_rows = int(scalar(conn, "SELECT COUNT(*) FROM universe_master") or 0)
    active_equity_rows = int(
        scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM universe_master
            WHERE COALESCE(LOWER(asset_type), 'equity') = 'equity'
              AND COALESCE(is_excluded, FALSE) = FALSE
            """,
        )
        or 0
    )
    price_rows = int(scalar(conn, "SELECT COUNT(*) FROM prices_daily") or 0)

    if active_equity_rows <= 0:
        raise SystemExit("universe_master has no active equity rows. Run sync_universe_master_from_csv_jp.py first.")
    if price_rows <= 0:
        raise SystemExit("prices_daily is empty. Run fetch_prices_jp.py first.")

    feature_diag = rebuild_features(conn)
    feature_rows = int(feature_diag.get("feature_rows") or 0)
    if feature_rows <= 0:
        raise SystemExit("features_daily was not populated from prices_daily.")

    diag = {
        "schema_version": "price_features_jp_rebuild_diagnostics_v1",
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "duckdb_path": safe_rel(db_path),
        "universe_master_rows": universe_rows,
        "active_equity_rows": active_equity_rows,
        "price_rows": price_rows,
        **feature_diag,
    }
    write_json(DIAG_PATH, diag)
    print("=== JP price feature rebuild ===")
    for k in ["duckdb_path", "universe_master_rows", "active_equity_rows", "price_rows", "feature_rows", "tickers", "min_date", "max_date"]:
        print(f"{k}: {diag.get(k)}")
    print(f"diagnostics: {safe_rel(DIAG_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
