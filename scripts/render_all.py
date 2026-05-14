from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

for script in [
    "render_index.py",
    "render_daily_jp.py",
    "render_weekly_jp.py",
    "render_static_pages.py",
]:
    print(f"==> {script}")
    subprocess.run([sys.executable, str(SCRIPTS / script)], check=True)
