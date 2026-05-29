from __future__ import annotations

"""Render the AI Arena JP Positions page from the current 7-agent JSON.

Source of truth:
- site/data/japan/ai-arena/positions/latest.json
- site/data/japan/ai-arena/ranking/latest.json for the full 7-agent roster

This renderer does not use legacy simulation agents, so old 5-agent names cannot
leak into the deployed Positions page.
"""

import os
from pathlib import Path
from typing import Any

from render_common import OUT_DIR, copy_asset, env, read_json, write_text

POSITIONS_JSON = Path(os.getenv("AI_ARENA_POSITIONS_JSON", str(OUT_DIR / "data/japan/ai-arena/positions/latest.json")))
RANKING_JSON = Path(os.getenv("AI_ARENA_RANKING_JSON", str(OUT_DIR / "data/japan/ai-arena/ranking/latest.json")))

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


def first_present(*values: Any, default: Any = None) -> Any:
    for v in values:
        if v is not None and v != "":
            return v
    return default


def pct(value: Any) -> str:
    v = fnum(value)
    return f"{v:+.2f}%"


def jpy(value: Any) -> str:
    return f"¥{fnum(value):,.0f}"


def signed_jpy(value: Any) -> str:
    v = fnum(value)
    sign = "+" if v > 0 else ""
    return f"{sign}¥{v:,.0f}"


def pnl_class(value: Any) -> str:
    v = fnum(value)
    if v > 0:
        return "pos"
    if v < 0:
        return "neg"
    return "flat"


def short_date(value: Any) -> str:
    s = str(value or "")
    return s[:10] if s else "—"


def group_by_agent(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows or []:
        aid = str(row.get("agent_id") or "")
        if aid:
            out.setdefault(aid, []).append(row)
    return out


def normalise_position(row: dict[str, Any]) -> dict[str, Any]:
    ticker = first_present(row.get("ticker"), row.get("symbol"), "—")
    name = first_present(row.get("name"), row.get("company_name"), ticker)
    mv = fnum(row.get("market_value_jpy"))
    pnl = fnum(row.get("unrealized_pnl_jpy"))
    ret = fnum(row.get("unrealized_return_pct"))
    return {
        **row,
        "ticker": ticker,
        "name": name,
        "entry_date_fmt": short_date(row.get("entry_date")),
        "current_date_fmt": short_date(first_present(row.get("current_date"), row.get("last_date"))),
        "shares_fmt": f"{inum(row.get('shares')):,}",
        "market_value_fmt": jpy(mv),
        "unrealized_pnl_fmt": signed_jpy(pnl),
        "unrealized_return_fmt": pct(ret),
        "pnl_class": pnl_class(pnl),
        "market_value_jpy": mv,
        "unrealized_pnl_jpy": pnl,
        "unrealized_return_pct": ret,
        "holding_days": inum(row.get("holding_days")),
    }


def normalise_trade(row: dict[str, Any]) -> dict[str, Any]:
    ticker = first_present(row.get("ticker"), row.get("symbol"), "—")
    name = first_present(row.get("name"), row.get("company_name"), ticker)
    pnl = fnum(first_present(row.get("pnl_jpy"), row.get("realized_pnl_jpy")))
    ret = fnum(first_present(row.get("return_pct"), row.get("realized_return_pct")))
    return {
        **row,
        "ticker": ticker,
        "name": name,
        "entry_date_fmt": short_date(row.get("entry_date")),
        "exit_date_fmt": short_date(row.get("exit_date")),
        "pnl_fmt": signed_jpy(pnl),
        "return_fmt": pct(ret),
        "pnl_class": pnl_class(pnl),
        "pnl_jpy": pnl,
        "return_pct": ret,
        "holding_days": inum(row.get("holding_days")),
    }


def build_payload(positions: dict[str, Any], ranking: dict[str, Any]) -> dict[str, Any]:
    profiles = {str(a.get("agent_id") or ""): a for a in ranking.get("agents") or []}
    rank_by_agent = {str(r.get("agent_id") or ""): r for r in ranking.get("ranking") or []}
    activity_by_agent = {
        str(a.get("agent_id") or ""): a
        for a in ((positions.get("diagnostics") or ranking.get("diagnostics") or {}).get("agent_activity") or [])
    }
    open_by_agent = group_by_agent(positions.get("open_positions") or [])
    closed_by_agent = group_by_agent(positions.get("closed_trades") or [])

    agents: list[dict[str, Any]] = []
    # Ranking JSON is the roster.  It should be 7 rows after the new season rebuild.
    ranking_rows = ranking.get("ranking") or []
    for rank_row in sorted(ranking_rows, key=lambda r: inum(r.get("rank"), 999)):
        aid = str(rank_row.get("agent_id") or "")
        profile = profiles.get(aid) or rank_row.get("agent") or {}
        name = str(first_present(profile.get("name"), rank_row.get("agent_name"), aid))
        color = CANONICAL_COLORS.get(name.upper()) or rank_row.get("color") or profile.get("color") or "#7DF9FF"
        opens = [normalise_position(p) for p in open_by_agent.get(aid, [])]
        closed = [normalise_trade(t) for t in closed_by_agent.get(aid, [])]
        opens.sort(key=lambda p: fnum(p.get("market_value_jpy")), reverse=True)
        closed.sort(key=lambda t: str(first_present(t.get("exit_date"), t.get("entry_date"), "")), reverse=True)
        realized = sum(fnum(t.get("pnl_jpy")) for t in closed)
        unrealized = sum(fnum(p.get("unrealized_pnl_jpy")) for p in opens)
        wins = [t for t in closed if fnum(t.get("pnl_jpy")) > 0]
        activity = activity_by_agent.get(aid, {})
        agents.append({
            "agent_id": aid,
            "name": name,
            "role": first_present(profile.get("role"), profile.get("style"), profile.get("style_label"), aid),
            "description": first_present(profile.get("short_description"), profile.get("description"), "AI Arena Agent"),
            "image": first_present(profile.get("image"), f"/assets/ai-arena/agents/{aid}.png"),
            "color": color,
            "rank": inum(rank_row.get("rank"), len(agents) + 1),
            "return_pct": fnum(first_present(rank_row.get("total_return_pct"), rank_row.get("return_pct"))),
            "return_fmt": pct(first_present(rank_row.get("total_return_pct"), rank_row.get("return_pct"))),
            "equity_fmt": jpy(first_present(rank_row.get("end_equity_jpy"), rank_row.get("portfolio_equity_jpy"))),
            "open_positions": opens,
            "closed_trades": closed,
            "recent_closed_trades": closed[:12],
            "open_count": len(opens),
            "closed_count": len(closed),
            "realized_pnl_fmt": signed_jpy(realized),
            "unrealized_pnl_fmt": signed_jpy(unrealized),
            "realized_class": pnl_class(realized),
            "unrealized_class": pnl_class(unrealized),
            "win_rate_fmt": pct((len(wins) / len(closed) * 100.0) if closed else rank_row.get("win_rate_pct")),
            "executed_buys": inum(activity.get("executed_buys")),
            "executed_sells": inum(activity.get("executed_sells")),
            "trade_signals": inum(activity.get("trade_signals")),
        })

    all_open = [p for a in agents for p in a["open_positions"]]
    all_closed = [dict(t, agent_name=a["name"], color=a["color"]) for a in agents for t in a["closed_trades"]]
    all_closed.sort(key=lambda t: str(first_present(t.get("exit_date"), t.get("entry_date"), "")), reverse=True)
    total_open_value = sum(fnum(p.get("market_value_jpy")) for p in all_open)
    total_unrealized = sum(fnum(p.get("unrealized_pnl_jpy")) for p in all_open)
    total_realized = sum(fnum(t.get("pnl_jpy")) for t in all_closed)
    wins = [t for t in all_closed if fnum(t.get("pnl_jpy")) > 0]

    return {
        **positions,
        "schema_version": positions.get("schema_version") or "ai_arena_positions_v2",
        "run_id": positions.get("run_id") or ranking.get("run_id"),
        "year": positions.get("year") or ranking.get("year"),
        "generated_at": positions.get("generated_at") or ranking.get("generated_at"),
        "agents": agents,
        "agent_count": len(agents),
        "history": {
            "open_count": len(all_open),
            "closed_count": len(all_closed),
            "total_open_value_fmt": jpy(total_open_value),
            "total_unrealized_fmt": signed_jpy(total_unrealized),
            "total_unrealized_class": pnl_class(total_unrealized),
            "total_realized_fmt": signed_jpy(total_realized),
            "total_realized_class": pnl_class(total_realized),
            "win_rate_fmt": pct((len(wins) / len(all_closed) * 100.0) if all_closed else 0),
            "recent_closed_trades": all_closed[:80],
        },
    }


def main() -> None:
    positions = read_json(POSITIONS_JSON, {})
    ranking = read_json(RANKING_JSON, {})
    payload = build_payload(positions, ranking)
    html = env().get_template("ai_arena_positions_jp.html.j2").render(payload=payload)
    write_text(OUT_DIR / "japan/ai-arena/positions/index.html", html)
    copy_asset("ai_arena_positions_jp.css")

    out = OUT_DIR / "japan/ai-arena/positions/index.html"
    if len(payload.get("agents") or []) != 7:
        raise RuntimeError(f"AI Arena Positions rendered {len(payload.get('agents') or [])} agents, expected 7")
    text = out.read_text(encoding="utf-8")
    for name in CANONICAL_AGENT_NAMES:
        if name not in text:
            raise RuntimeError(f"AI Arena Positions is missing agent name: {name}")


if __name__ == "__main__":
    main()
