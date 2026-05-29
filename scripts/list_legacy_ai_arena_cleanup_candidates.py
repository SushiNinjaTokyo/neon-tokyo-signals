#!/usr/bin/env python3
from __future__ import annotations

"""Write a documented list of future cleanup candidates.

This does not delete anything. It exists so that once the new AI Arena pipeline
is verified, the project can remove legacy Daily/Weekly/old-Arena files with a
clear, auditable list.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from lib.db import ROOT, safe_rel
from lib.arena_exporter_jp import write_json

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()

CANDIDATES = {
    "daily_workflows": [
        ".github/workflows/build-daily-jp.yml",
        ".github/workflows/daily-jp-auto.yml",
        ".github/workflows/daily-jp-simulation.yml",
        ".github/workflows/backtest-daily-jp-incremental.yml",
        ".github/workflows/backtest-daily-jp-range.yml",
        ".github/workflows/render-daily-jp.yml",
        ".github/workflows/render-backtest-daily-jp.yml",
    ],
    "weekly_workflows": [
        ".github/workflows/weekly-jp-analysis.yml",
        ".github/workflows/weekly-jp-screening.yml",
    ],
    "old_ai_arena_workflows": [
        ".github/workflows/ai-arena-jp.yml",
        ".github/workflows/ai-arena-jp-historical-simulation.yml",
    ],
    "daily_weekly_scripts": [
        "scripts/build_daily_jp.py",
        "scripts/render_daily_jp.py",
        "scripts/backtest_daily_jp.py",
        "scripts/render_backtest_daily_jp.py",
        "scripts/rebuild_daily_simulation_jp.py",
        "scripts/render_daily_simulation_jp.py",
        "scripts/build_weekly_jp.py",
        "scripts/render_weekly_jp.py",
        "scripts/rebuild_weekly_backtest_jp.py",
        "scripts/render_weekly_backtest_jp.py",
        "scripts/rebuild_weekly_simulation_jp.py",
        "scripts/render_weekly_simulation_jp.py",
    ],
    "old_ai_arena_scripts": [
        "scripts/rebuild_ai_arena_simulation_jp.py",
        "scripts/build_ai_arena_historical_daily_snapshots_jp.py",
    ],
    "large_legacy_data": [
        "site/data/backtest-daily-jp/latest.json",
        "site/data/backtest-daily-jp/20??-??-??.json",
        "site/data/weekly-jp/backtest/*.json",
        "site/data/japan/weekly/backtest/*.json",
    ],
}

KEEP_UNTIL_VERIFIED = [
    "scripts/render_ai_arena_jp.py",
    "scripts/render_ai_arena_positions_jp.py",
    "scripts/render_ai_arena_ranking_jp.py",
    "templates/ai_arena_jp.html.j2",
    "templates/ai_arena_positions_jp.html.j2",
    "templates/ai_arena_ranking_jp.html.j2",
    "site/assets/ai-arena/agents/*.png",
    "data/universe/*.csv",
]


def main() -> int:
    payload = {
        "schema_version": "ai_arena_legacy_cleanup_candidates_v1",
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "delete_policy": "Do not delete until new AI Arena season rebuild, live update, summary, signals, positions, ranking, and log have been verified.",
        "candidates": CANDIDATES,
        "keep_until_verified": KEEP_UNTIL_VERIFIED,
    }
    out_json = OUT_DIR / "data" / "japan" / "ai-arena" / "legacy_cleanup_candidates.json"
    write_json(out_json, payload)
    md = ["# Legacy Cleanup Candidates", "", payload["delete_policy"], ""]
    for group, items in CANDIDATES.items():
        md.append(f"## {group}")
        md.extend([f"- `{x}`" for x in items])
        md.append("")
    md.append("## Keep until verified")
    md.extend([f"- `{x}`" for x in KEEP_UNTIL_VERIFIED])
    out_md = OUT_DIR / "data" / "japan" / "ai-arena" / "legacy_cleanup_candidates.md"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {safe_rel(out_json)}")
    print(f"Wrote {safe_rel(out_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
