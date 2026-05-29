from __future__ import annotations

"""Render the AI Arena JP Ranking page from the current 7-agent JSON.

Source of truth:
- site/data/japan/ai-arena/ranking/latest.json
- site/data/japan/ai-arena/positions/latest.json, optional enrichment

This renderer deliberately avoids all old 5-agent constants.  Agents are read
from exported JSON and displayed in the canonical 7-agent order/ranking.
"""

import os
from pathlib import Path
from typing import Any

from render_common import OUT_DIR, copy_asset, env, read_json, write_text

RANKING_JSON = Path(os.getenv("AI_ARENA_RANKING_JSON", str(OUT_DIR / "data/japan/ai-arena/ranking/latest.json")))
POSITIONS_JSON = Path(os.getenv("AI_ARENA_POSITIONS_JSON", str(OUT_DIR / "data/japan/ai-arena/positions/latest.json")))

CANONICAL_AGENT_NAMES = ["KYOU", "NAGARE", "MAMORU", "SAGURI", "MATSU", "KAESHI", "HIZUMI"]
CANONICAL_COLORS = {
    "KYOU": "#FF4B5C",
    "NAGARE": "#B779FF",
    "MAMORU": "#7DF9FF",
    "SAGURI": "#5DFFB1",
    "MATSU": "#FFD166",
    "KAESHI": "#FF4FD8",
    "HIZUMI": "#4F46E5",
}


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def inum(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except Exception:
        return default


def pct(value: Any) -> str:
    return f"{fnum(value):+.2f}%"


def jpy(value: Any) -> str:
    return f"¥{fnum(value):,.0f}"


def first_present(*values: Any, default: Any = None) -> Any:
    for v in values:
        if v is not None and v != "":
            return v
    return default


def name_of(agent: dict[str, Any] | None, fallback: str) -> str:
    if not agent:
        return fallback
    return str(first_present(agent.get("name"), agent.get("display_name"), fallback))


def normalise_agent_profile(agent: dict[str, Any] | None, agent_id: str) -> dict[str, Any]:
    agent = dict(agent or {})
    name = name_of(agent, agent_id)
    color = CANONICAL_COLORS.get(name.upper()) or agent.get("color") or "#7DF9FF"
    return {
        **agent,
        "agent_id": agent_id,
        "name": name,
        "color": color,
        "image": first_present(agent.get("image"), agent.get("icon_src"), f"/assets/ai-arena/agents/{agent_id}.png"),
        "role": first_present(agent.get("role"), agent.get("style"), agent.get("style_label"), agent_id),
        "style": first_present(agent.get("style"), agent.get("style_label"), agent.get("short_description"), "AI Arena Agent"),
    }


def group_by_agent(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows or []:
        aid = str(row.get("agent_id") or "")
        if not aid:
            continue
        out.setdefault(aid, []).append(row)
    return out


def spark_points(points: list[dict[str, Any]], width: int = 260, height: int = 64, pad: int = 5) -> str:
    values = [fnum(p.get("return_pct"), 0.0) for p in points or [] if isinstance(p, dict)]
    if not values:
        return ""
    if len(values) == 1:
        return f"{pad},{height / 2:.1f}"
    lo, hi = min(values), max(values)
    span = max(0.0001, hi - lo)
    coords: list[str] = []
    for i, v in enumerate(values):
        x = pad + (width - pad * 2) * i / (len(values) - 1)
        y = pad + (height - pad * 2) * (1 - (v - lo) / span)
        coords.append(f"{x:.1f},{y:.1f}")
    return " ".join(coords)


def build_payload(ranking: dict[str, Any], positions: dict[str, Any]) -> dict[str, Any]:
    agents_profiles = {str(a.get("agent_id") or ""): a for a in ranking.get("agents") or []}
    open_by_agent = group_by_agent(positions.get("open_positions") or [])
    closed_by_agent = group_by_agent(positions.get("closed_trades") or [])
    activity_by_agent = {
        str(a.get("agent_id") or ""): a
        for a in ((ranking.get("diagnostics") or {}).get("agent_activity") or [])
    }

    rows: list[dict[str, Any]] = []
    for raw in ranking.get("ranking") or []:
        aid = str(raw.get("agent_id") or "")
        agent = normalise_agent_profile(raw.get("agent") or agents_profiles.get(aid), aid)
        name = str(agent.get("name") or aid)
        ret = fnum(first_present(raw.get("total_return_pct"), raw.get("return_pct"), 0.0))
        open_rows = open_by_agent.get(aid, [])
        closed_rows = closed_by_agent.get(aid, [])
        activity = activity_by_agent.get(aid, {})
        rows.append({
            **raw,
            "agent_id": aid,
            "agent": agent,
            "name": name,
            "color": CANONICAL_COLORS.get(name.upper()) or raw.get("color") or agent.get("color") or "#7DF9FF",
            "rank": inum(raw.get("rank"), len(rows) + 1),
            "return_pct": ret,
            "return_fmt": pct(ret),
            "return_class": "pos" if ret >= 0 else "neg",
            "end_equity_fmt": jpy(first_present(raw.get("end_equity_jpy"), raw.get("portfolio_equity_jpy"), 0)),
            "trade_count": inum(first_present(raw.get("trade_count"), raw.get("closed_trades"), len(closed_rows))),
            "open_count": len(open_rows),
            "closed_count": len(closed_rows),
            "win_rate_fmt": pct(raw.get("win_rate_pct")),
            "max_drawdown_fmt": pct(raw.get("max_drawdown_pct")),
            "executed_buys": inum(activity.get("executed_buys")),
            "executed_sells": inum(activity.get("executed_sells")),
            "trade_signals": inum(activity.get("trade_signals")),
            "sparkline_points": raw.get("sparkline_points") or spark_points(raw.get("sparkline") or []),
            "top_open": sorted(open_rows, key=lambda x: fnum(x.get("market_value_jpy")), reverse=True)[:3],
            "recent_closed": sorted(closed_rows, key=lambda x: str(first_present(x.get("exit_date"), x.get("entry_date"), "")), reverse=True)[:3],
        })

    rows.sort(key=lambda r: (inum(r.get("rank"), 999), -fnum(r.get("return_pct"))))
    for i, row in enumerate(rows, start=1):
        row["rank"] = i

    summary = {
        "agent_count": len(rows),
        "leader": rows[0] if rows else None,
        "avg_return_pct": sum(fnum(r.get("return_pct")) for r in rows) / len(rows) if rows else 0.0,
        "total_closed_trades": sum(inum(r.get("closed_count")) for r in rows),
        "total_open_positions": sum(inum(r.get("open_count")) for r in rows),
    }
    return {
        **ranking,
        "schema_version": ranking.get("schema_version") or "ai_arena_ranking_v2",
        "agents_count": len(rows),
        "expected_agents": CANONICAL_AGENT_NAMES,
        "rows": rows,
        "summary": summary,
        "run_id": ranking.get("run_id") or positions.get("run_id"),
        "year": ranking.get("year") or positions.get("year"),
        "generated_at": ranking.get("generated_at") or positions.get("generated_at"),
    }


def main() -> None:
    ranking = read_json(RANKING_JSON, {})
    positions = read_json(POSITIONS_JSON, {})
    payload = build_payload(ranking, positions)
    html = env().get_template("ai_arena_ranking_jp.html.j2").render(payload=payload)
    write_text(OUT_DIR / "japan/ai-arena/ranking/index.html", html)
    copy_asset("ai_arena_ranking_jp.css")

    out = OUT_DIR / "japan/ai-arena/ranking/index.html"
    if len(payload.get("rows") or []) != 7:
        raise RuntimeError(f"AI Arena Ranking rendered {len(payload.get('rows') or [])} agents, expected 7")
    text = out.read_text(encoding="utf-8")
    for name in CANONICAL_AGENT_NAMES:
        if name not in text:
            raise RuntimeError(f"AI Arena Ranking is missing agent name: {name}")


if __name__ == "__main__":
    main()
