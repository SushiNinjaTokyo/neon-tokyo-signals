#!/usr/bin/env python3
from __future__ import annotations

"""Promote an existing AI Arena run_id to the public display run."""

import os
from datetime import datetime
from pathlib import Path

from lib.db import connect_db, ROOT
from lib.duckdb_schema import initialize_schema
from lib.arena_run_manager_jp import promote_display_run
from lib.arena_exporter_jp import export_arena_payloads
from lib.arena_run_manager_jp import load_yaml

PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
YEAR = int(os.getenv("ARENA_YEAR", os.getenv("YEAR", str(datetime.utcnow().year))))
RUN_ID = os.getenv("RUN_ID", "").strip()
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()


def main() -> int:
    if not RUN_ID:
        raise SystemExit("RUN_ID is required.")
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)
    exists = conn.execute("SELECT COUNT(*) FROM arena_simulation_runs WHERE run_id = ?", [RUN_ID]).fetchone()[0]
    if not exists:
        raise SystemExit(f"Run does not exist: {RUN_ID}")
    promote_display_run(conn, year=YEAR, run_id=RUN_ID, note="Promoted by workflow")
    agents = (load_yaml(ROOT / "data" / "agents" / "jp_agents.yml").get("agents") or [])
    export_arena_payloads(conn, out_dir=OUT_DIR, run_id=RUN_ID, year=YEAR, agents=agents)
    print(f"Promoted {RUN_ID} for {YEAR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
