from __future__ import annotations

"""Render AI Arena main discussion page.

The discussion builder may output only LAB-specific fields such as threads/feed.
The page, however, also needs agent cards, ranking, avatar paths, season metadata,
and disclaimer.  Therefore this renderer deliberately merges the discussion JSON
with the richer legacy/latest and simulation JSON payloads before rendering.

This avoids Jinja ``Undefined`` values being passed into ``tojson`` when a
render-only workflow uses a discussion payload that does not include ``agents``.
"""

import os
from pathlib import Path
from typing import Any

from render_common import OUT_DIR, copy_asset, env, read_json, write_text

DISCUSSION_JSON = Path(os.getenv("AI_ARENA_DISCUSSION_JSON", str(OUT_DIR / "data/japan/ai-arena/discussion/latest.json")))
LEGACY_JSON = Path(os.getenv("ARENA_JSON", str(OUT_DIR / "data/japan/ai-arena/latest.json")))
SIMULATION_JSON = Path(os.getenv("AI_ARENA_SIMULATION_JSON", str(OUT_DIR / "data/japan/ai-arena/simulation/latest.json")))
POSITIONS_JSON = Path(os.getenv("AI_ARENA_POSITIONS_JSON", str(OUT_DIR / "data/japan/ai-arena/positions/latest.json")))
RANKING_JSON = Path(os.getenv("AI_ARENA_RANKING_JSON", str(OUT_DIR / "data/japan/ai-arena/ranking/latest.json")))


def _is_empty(value: Any) -> bool:
    return value is None or value == [] or value == {}


def _merge_arena_payload() -> dict[str, Any]:
    """Merge available AI Arena payloads into one render-safe dictionary.

    Precedence:
    - latest/legacy gives the broad page shape.
    - simulation/ranking/positions backfill agent cards and metrics.
    - discussion overrides feed, threads, discussion_events, ai status, and brief.
    """

    legacy = read_json(LEGACY_JSON, {}) or {}
    simulation = read_json(SIMULATION_JSON, {}) or {}
    ranking_payload = read_json(RANKING_JSON, {}) or {}
    positions_payload = read_json(POSITIONS_JSON, {}) or {}
    discussion = read_json(DISCUSSION_JSON, {}) or {}

    arena: dict[str, Any] = {}
    for source in (legacy, simulation, ranking_payload, positions_payload, discussion):
        if isinstance(source, dict):
            arena.update(source)

    # Backfill fields that discussion-only payloads do not carry.
    if _is_empty(arena.get("agents")):
        arena["agents"] = simulation.get("agents") or legacy.get("agents") or []
    if _is_empty(arena.get("ranking")):
        arena["ranking"] = ranking_payload.get("ranking") or simulation.get("ranking") or legacy.get("ranking") or []
    if _is_empty(arena.get("feed")):
        arena["feed"] = discussion.get("feed") or legacy.get("feed") or []
    if _is_empty(arena.get("range")):
        arena["range"] = discussion.get("range") or simulation.get("range") or legacy.get("range") or {}
    if _is_empty(arena.get("season")):
        arena["season"] = discussion.get("season") or simulation.get("season") or legacy.get("season") or "—"
    if _is_empty(arena.get("ai")):
        arena["ai"] = discussion.get("ai") or legacy.get("ai") or {}
    if _is_empty(arena.get("daily_brief")):
        arena["daily_brief"] = discussion.get("daily_brief") or legacy.get("daily_brief") or {}
    if _is_empty(arena.get("disclaimer")):
        arena["disclaimer"] = legacy.get("disclaimer") or "AI Arena is a quantitative simulation and discussion game. Informational only. Not investment advice."

    # Never allow Jinja to serialize Undefined/null for these front-end datasets.
    arena["agents"] = arena.get("agents") or []
    arena["ranking"] = arena.get("ranking") or []
    arena["feed"] = arena.get("feed") or []
    arena["range"] = arena.get("range") or {}
    arena["ai"] = arena.get("ai") or {}
    arena["daily_brief"] = arena.get("daily_brief") or {}
    return arena


def main() -> None:
    arena = _merge_arena_payload()
    html = env().get_template("ai_arena_jp.html.j2").render(arena=arena)
    write_text(OUT_DIR / "japan/ai-arena/index.html", html)
    copy_asset("ai_arena_jp.css")
    copy_asset("ai_arena_jp.js")


if __name__ == "__main__":
    main()
