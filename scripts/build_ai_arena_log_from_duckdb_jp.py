#!/usr/bin/env python3
from __future__ import annotations

"""Build a lightweight 7-agent Arena Log from orders and signals.

The old Arena Log can continue to exist, but this file creates a new
DuckDB-backed log that knows about KYOU/NAGARE/MAMORU/SAGURI/MATSU/KAESHI/HIZUMI.
GPT is not required; templates in jp_agent_voice_rules.yml provide deterministic
short comments.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from lib.db import ROOT, connect_db, safe_rel
from lib.duckdb_schema import initialize_schema
from lib.arena_exporter_jp import write_json

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()
PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
RUN_ID = os.getenv("RUN_ID", "")
YEAR = int(os.getenv("ARENA_YEAR", os.getenv("YEAR", str(datetime.utcnow().year))))
MAX_EVENTS = int(os.getenv("ARENA_LOG_MAX_EVENTS", "80"))
VOICE_YML = ROOT / "data" / "agents" / "jp_agent_voice_rules.yml"


def load_voice() -> dict[str, Any]:
    with VOICE_YML.open("r", encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("agents", {}) or {}


def render_template(template: str, **kw: Any) -> str:
    try:
        return template.format(**kw)
    except Exception:
        return template


def main() -> int:
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)
    rid = RUN_ID
    if not rid:
        row = conn.execute(
            "SELECT run_id FROM arena_display_runs WHERE year = ? AND display_type = 'current' ORDER BY selected_at DESC LIMIT 1",
            [YEAR],
        ).fetchone()
        rid = str(row[0]) if row else ""
    if not rid:
        raise SystemExit("No display run found. Run season rebuild first.")
    voice = load_voice()
    orders = conn.execute(
        """
        SELECT * FROM arena_orders
        WHERE run_id = ? AND order_status = 'FILLED'
        ORDER BY execution_date DESC, created_at DESC
        LIMIT ?
        """,
        [rid, MAX_EVENTS],
    ).df()
    events = []
    base_time = datetime.utcnow() - timedelta(minutes=MAX_EVENTS * 7)
    for i, (_, r) in enumerate(orders.iloc[::-1].iterrows()):
        aid = r["agent_id"]
        v = voice.get(aid, {})
        side = str(r["side"]).upper()
        badge = "IN" if side == "BUY" else "OUT"
        tmpl = v.get("in_template") if side == "BUY" else v.get("out_template")
        text = render_template(tmpl or "{ticker} {badge}", ticker=r["ticker"], badge=badge)
        events.append({
            "event_id": f"log-{i+1:04d}",
            "show_at": (base_time + timedelta(minutes=i * 7)).isoformat(timespec="seconds") + "Z",
            "event_type": "TRADE_LOG",
            "agent_id": aid,
            "agent_name": v.get("name") or aid,
            "ticker": r["ticker"],
            "name": r.get("name") or r["ticker"],
            "badge": badge,
            "side": side,
            "reason_code": r.get("reason_code") or "",
            "message": text,
        })
    payload = {"schema_version": "ai_arena_log_v1", "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z", "run_id": rid, "events": events}
    out_path = OUT_DIR / "data" / "japan" / "ai-arena" / "log" / "latest.json"
    write_json(out_path, payload)
    # Legacy compatibility for existing Arena page JS while migration continues.
    write_json(OUT_DIR / "data" / "japan" / "ai-arena" / "events" / "latest.json", payload)
    print(f"Wrote {safe_rel(out_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
