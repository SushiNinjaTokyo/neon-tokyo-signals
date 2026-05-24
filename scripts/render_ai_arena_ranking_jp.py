from __future__ import annotations

"""Render AI Arena Ranking page."""

import os
from pathlib import Path
from render_common import OUT_DIR, copy_asset, env, read_json, write_text

RANKING_JSON = Path(os.getenv("AI_ARENA_RANKING_JSON", str(OUT_DIR / "data/japan/ai-arena/ranking/latest.json")))


def main() -> None:
    ranking = read_json(RANKING_JSON, {})
    html = env().get_template("ai_arena_ranking_jp.html.j2").render(ranking=ranking)
    write_text(OUT_DIR / "japan/ai-arena/ranking/index.html", html)
    copy_asset("ai_arena_ranking_jp.css")


if __name__ == "__main__":
    main()
