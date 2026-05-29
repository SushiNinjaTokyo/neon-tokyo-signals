from __future__ import annotations

"""Render static Neon Tokyo pages from already-generated JSON.

This file is intentionally render-only.  It must not fetch prices, rebuild
signals, run backtests, or mutate DuckDB.  Data-generation workflows should run
before this script.  The purpose of this aggregator is to make sure the visible
HTML pages are always regenerated after AI Arena JSON changes.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

# Order matters: TOP uses hero/latest.json; the AI Arena pages use the JSON
# exported by scripts/lib/arena_exporter_jp.py during season rebuild/live update.
RENDER_SCRIPTS = [
    "render_index.py",
    "render_ai_arena_summary_jp.py",
    "render_ai_arena_ranking_jp.py",
    "render_ai_arena_positions_jp.py",
    "render_ai_arena_jp.py",
    "render_ai_arena_signals_jp.py",
    "render_ai_agent_profiles_jp.py",
    "render_daily_jp.py",
    "render_weekly_jp.py",
    "render_static_pages.py",
]


def main() -> int:
    for script in RENDER_SCRIPTS:
        path = SCRIPTS / script
        if not path.exists():
            print(f"skip missing renderer: {script}")
            continue
        print(f"==> {script}")
        subprocess.run([sys.executable, str(path)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
