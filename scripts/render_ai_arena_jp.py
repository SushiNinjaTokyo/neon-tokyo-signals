from __future__ import annotations

"""Render AI Arena main discussion page."""

import os
from pathlib import Path
from render_common import OUT_DIR, copy_asset, env, read_json, write_text

DISCUSSION_JSON = Path(os.getenv("AI_ARENA_DISCUSSION_JSON", str(OUT_DIR / "data/japan/ai-arena/discussion/latest.json")))
LEGACY_JSON = Path(os.getenv("ARENA_JSON", str(OUT_DIR / "data/japan/ai-arena/latest.json")))


def main() -> None:
    arena = read_json(DISCUSSION_JSON, read_json(LEGACY_JSON, {}))
    html = env().get_template("ai_arena_jp.html.j2").render(arena=arena)
    write_text(OUT_DIR / "japan/ai-arena/index.html", html)
    copy_asset("ai_arena_jp.css")
    copy_asset("ai_arena_jp.js")


if __name__ == "__main__":
    main()
