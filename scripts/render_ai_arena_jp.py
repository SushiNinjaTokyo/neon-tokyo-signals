from __future__ import annotations

"""Render Neon Tokyo AI Arena static page.

This renderer is intentionally thin: all Arena calculations and AI text are
produced by scripts/build_ai_arena_jp.py. Keeping rendering separate lets you
iterate on HTML/CSS without rebuilding the Arena JSON or calling OpenAI.
"""

import os
from pathlib import Path

from render_common import OUT_DIR, copy_asset, env, read_json, write_text

ROOT = Path(__file__).resolve().parents[1]
ARENA_JSON = Path(os.getenv("ARENA_JSON", str(OUT_DIR / "data/japan/ai-arena/latest.json")))


def main() -> None:
    arena = read_json(ARENA_JSON, {})
    template = env().get_template("ai_arena_jp.html.j2")
    html = template.render(arena=arena)
    write_text(OUT_DIR / "japan/ai-arena/index.html", html)
    copy_asset("ai_arena_jp.css")
    copy_asset("ai_arena_jp.js")


if __name__ == "__main__":
    main()
