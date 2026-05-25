from __future__ import annotations

"""Render AI Arena Ranking page.

The ranking page is intentionally presentation-heavy.  The raw simulation JSON is
kept simple, while this renderer derives view-only fields such as bar widths,
avatar classes, and small SVG sparklines.  Keeping those transforms here avoids
polluting the simulation engine with UI concerns.
"""

import os
from pathlib import Path
from render_common import OUT_DIR, copy_asset, env, read_json, write_text

RANKING_JSON = Path(os.getenv("AI_ARENA_RANKING_JSON", str(OUT_DIR / "data/japan/ai-arena/ranking/latest.json")))

AVATAR_BY_AGENT = {
    "daily_striker": "pixel_warrior",
    "weekly_sage": "pixel_mage",
    "risk_sentinel": "pixel_shield",
    "discovery_scout": "pixel_archer",
    "contrarian_monk": "pixel_monk",
    "momentum_hunter": "pixel_warrior",
    "theme_raider": "pixel_mage",
    "contrarian_quant": "pixel_monk",
}

AVATAR_IMAGE_BY_AGENT = {
    "daily_striker": "/assets/ai-arena/agents/daily_striker.png",
    "weekly_sage": "/assets/ai-arena/agents/weekly_sage.png",
    "risk_sentinel": "/assets/ai-arena/agents/risk_sentinel.png",
    "discovery_scout": "/assets/ai-arena/agents/discovery_scout.png",
    "contrarian_monk": "/assets/ai-arena/agents/contrarian_monk.png",
}

TONE_BY_AGENT = {
    "daily_striker": "cyan",
    "weekly_sage": "violet",
    "risk_sentinel": "blue",
    "discovery_scout": "green",
    "contrarian_monk": "amber",
    "momentum_hunter": "cyan",
    "theme_raider": "violet",
    "contrarian_quant": "amber",
}


def _to_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _spark_points(return_pct: float, drawdown_pct: float, rank: int) -> str:
    """Create a deterministic SVG sparkline from summary stats.

    We do not have per-day ranking equity in the lightweight ranking JSON yet.
    This view-only sparkline is therefore a compact visual encoding of current
    return, drawdown, and rank rather than a historical performance chart.
    """
    width, height = 260, 70
    ret = max(-8.0, min(12.0, return_pct))
    dd = max(-12.0, min(0.0, drawdown_pct))
    rank_bias = max(0, 6 - rank) * 1.8
    levels = [
        34 - rank_bias,
        33 - rank_bias * .5,
        36 + abs(dd) * .65,
        32 - ret * .72,
        30 - ret * .92,
        28 - ret * 1.05,
    ]
    points = []
    for i, y in enumerate(levels):
        x = 12 + i * ((width - 24) / (len(levels) - 1))
        y = max(8, min(height - 8, y))
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def enrich_ranking(ranking: dict) -> dict:
    agents = ranking.get("agents") or []
    returns = [_to_float(a.get("return_pct")) for a in agents]
    min_ret = min(returns) if returns else 0.0
    max_ret = max(returns) if returns else 0.0
    span = max(0.01, max_ret - min_ret)

    enriched = []
    for a in agents:
        item = dict(a)
        agent_id = str(item.get("agent_id") or "")
        ret = _to_float(item.get("return_pct"))
        dd = _to_float(item.get("max_drawdown_pct"))
        rank = int(item.get("rank") or 99)
        # Use a 10-100 visual range so negative performers still remain visible.
        item["bar_width_pct"] = max(10.0, min(100.0, 10.0 + ((ret - min_ret) / span) * 90.0)) if agents else 50.0
        item["return_class"] = "positive" if ret >= 0 else "negative"
        item["avatar_style"] = item.get("avatar_style") or AVATAR_BY_AGENT.get(agent_id, "pixel_warrior")
        item["avatar_image"] = item.get("avatar_image") or AVATAR_IMAGE_BY_AGENT.get(agent_id)
        item["ui_tone"] = item.get("ui_tone") or TONE_BY_AGENT.get(agent_id, "cyan")
        item["spark_points"] = _spark_points(ret, dd, rank)
        item["rank_glow"] = "champion" if rank == 1 else "challenger"
        enriched.append(item)
    ranking = dict(ranking)
    ranking["agents"] = enriched
    ranking["podium"] = enriched[:3]
    ranking["return_spread_pct"] = (max_ret - min_ret) if enriched else 0.0
    if enriched:
        champion_id = (ranking.get("champion") or {}).get("agent_id")
        ranking["champion"] = next((a for a in enriched if a.get("agent_id") == champion_id), enriched[0])
    return ranking


def main() -> None:
    ranking = enrich_ranking(read_json(RANKING_JSON, {}))
    html = env().get_template("ai_arena_ranking_jp.html.j2").render(ranking=ranking)
    write_text(OUT_DIR / "japan/ai-arena/ranking/index.html", html)
    copy_asset("ai_arena_ranking_jp.css")


if __name__ == "__main__":
    main()
