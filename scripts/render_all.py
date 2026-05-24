from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

# Render-only aggregator. It must not rebuild price/signal/backtest/simulation
# JSON. Use the dedicated workflows for data generation.
for script in [
    "render_index.py",
    "render_daily_jp.py",
    "render_weekly_jp.py",
    "render_ai_arena_jp.py",
    "render_ai_arena_positions_jp.py",
    "render_ai_arena_ranking_jp.py",
    "render_static_pages.py",
]:
    print(f"==> {script}")
    subprocess.run([sys.executable, str(SCRIPTS / script)], check=True)
