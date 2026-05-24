from __future__ import annotations

"""Render AI Arena Positions page."""

import os
from pathlib import Path
from render_common import OUT_DIR, copy_asset, env, read_json, write_text

POSITIONS_JSON = Path(os.getenv("AI_ARENA_POSITIONS_JSON", str(OUT_DIR / "data/japan/ai-arena/positions/latest.json")))


def main() -> None:
    positions = read_json(POSITIONS_JSON, {})
    html = env().get_template("ai_arena_positions_jp.html.j2").render(positions=positions)
    write_text(OUT_DIR / "japan/ai-arena/positions/index.html", html)
    copy_asset("ai_arena_positions_jp.css")


if __name__ == "__main__":
    main()
