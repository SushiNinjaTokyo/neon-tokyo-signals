from __future__ import annotations

"""Render AI Arena Ranking page.

The simulation engine remains the source of truth for trading/accounting.
This renderer reads the lightweight ranking JSON plus simulation/latest.json and
creates view-only fields for the leaderboard UI: real equity sparklines, return
race paths, best/worst trades, strongest open positions, podium labels, and
champion explanation copy.
"""

import os
from pathlib import Path
from typing import Any

from render_common import OUT_DIR, copy_asset, env, read_json, write_text

RANKING_JSON = Path(
    os.getenv(
        "AI_ARENA_RANKING_JSON",
        str(OUT_DIR / "data/japan/ai-arena/ranking/latest.json"),
    )
)
SIMULATION_JSON = Path(
    os.getenv(
        "AI_ARENA_SIMULATION_JSON",
        str(OUT_DIR / "data/japan/ai-arena/simulation/latest.json"),
    )
)

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

PODIUM_LABEL_BY_RANK = {
    1: "CROWN",
    2: "ACE",
    3: "CORE",
    4: "SHADOW",
    5: "LOW",
}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _fmt_pct(value: Any) -> str:
    return f"{_to_float(value):+.2f}%"


def _fmt_jpy(value: Any) -> str:
    return f"¥{_to_float(value):,.0f}"


def _trim(text: Any, limit: int = 132) -> str:
    s = " ".join(str(text or "").split())
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 1)].rstrip() + "…"


def _simulation_by_agent(simulation: dict) -> dict[str, dict]:
    agents = simulation.get("agents") or []
    return {str(a.get("agent_id") or ""): a for a in agents if a.get("agent_id")}


def _trade_view(trade: dict | None, kind: str) -> dict | None:
    if not trade:
        return None
    return {
        "kind": kind,
        "symbol": trade.get("symbol") or "—",
        "name": trade.get("name") or "—",
        "theme": trade.get("theme") or "—",
        "return_pct": _to_float(trade.get("return_pct")),
        "pnl_jpy": _to_float(trade.get("pnl_jpy")),
        "holding_days": _to_int(trade.get("holding_days")),
        "entry_date": trade.get("entry_date") or "—",
        "exit_date": trade.get("exit_date") or "—",
        "exit_reason": trade.get("exit_reason") or "—",
        "entry_reason_short": _trim(trade.get("entry_reason"), 118),
    }


def _best_trade(closed_trades: list[dict]) -> dict | None:
    if not closed_trades:
        return None
    return _trade_view(max(closed_trades, key=lambda t: _to_float(t.get("pnl_jpy"))), "BEST")


def _worst_trade(closed_trades: list[dict]) -> dict | None:
    if not closed_trades:
        return None
    return _trade_view(min(closed_trades, key=lambda t: _to_float(t.get("pnl_jpy"))), "WORST")


def _open_position_view(position: dict | None) -> dict | None:
    if not position:
        return None
    return {
        "symbol": position.get("symbol") or "—",
        "name": position.get("name") or "—",
        "theme": position.get("theme") or "—",
        "entry_date": position.get("entry_date") or "—",
        "current_date": position.get("current_date") or "—",
        "entry_price": _to_float(position.get("entry_price")),
        "current_price": _to_float(position.get("current_price")),
        "shares": _to_int(position.get("shares")),
        "market_value_jpy": _to_float(position.get("market_value_jpy")),
        "unrealized_return_pct": _to_float(position.get("unrealized_return_pct")),
        "unrealized_pnl_jpy": _to_float(position.get("unrealized_pnl_jpy")),
        "holding_days": _to_int(position.get("holding_days")),
        "entry_reason_short": _trim(position.get("entry_reason"), 118),
    }


def _strongest_open_position(open_positions: list[dict]) -> dict | None:
    if not open_positions:
        return None
    return _open_position_view(max(open_positions, key=lambda p: _to_float(p.get("unrealized_pnl_jpy"))))


def _normalised_points(values: list[float], width: int = 320, height: int = 92, pad: int = 10) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return f"{pad},{height / 2:.1f}"
    low = min(values)
    high = max(values)
    span = max(0.0001, high - low)
    usable_w = width - pad * 2
    usable_h = height - pad * 2
    points: list[str] = []
    for i, value in enumerate(values):
        x = pad + (usable_w * i / (len(values) - 1))
        y = pad + usable_h * (1 - ((value - low) / span))
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def _race_points(values: list[float], low: float, high: float, width: int = 1000, height: int = 260, pad_x: int = 24, pad_y: int = 22) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return f"{pad_x},{height / 2:.1f}"
    span = max(0.0001, high - low)
    usable_w = width - pad_x * 2
    usable_h = height - pad_y * 2
    points: list[str] = []
    for i, value in enumerate(values):
        x = pad_x + (usable_w * i / (len(values) - 1))
        y = pad_y + usable_h * (1 - ((value - low) / span))
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def _last_xy(points: str) -> dict[str, float]:
    if not points:
        return {"x": 0.0, "y": 0.0}
    last = points.split()[-1]
    try:
        x, y = last.split(",")
        return {"x": float(x), "y": float(y)}
    except Exception:
        return {"x": 0.0, "y": 0.0}


def _curve_values(equity_curve: list[dict]) -> list[float]:
    return [_to_float(p.get("return_pct")) for p in equity_curve if isinstance(p, dict)]


def _recent_momentum(values: list[float], window: int = 10) -> float:
    if len(values) < 2:
        return 0.0
    start = values[-min(window, len(values))]
    return values[-1] - start


def _build_champion_reasons(champion: dict, agents: list[dict]) -> list[str]:
    if not champion:
        return []

    reasons: list[str] = []
    champ_id = champion.get("agent_id")
    champ_return = _to_float(champion.get("return_pct"))
    best_return = max((_to_float(a.get("return_pct")) for a in agents), default=champ_return)
    if champ_return >= best_return - 0.0001:
        reasons.append(f"Leads the season return table at {_fmt_pct(champ_return)}.")

    strongest = champion.get("strongest_open_position")
    if strongest and _to_float(strongest.get("unrealized_pnl_jpy")) > 0:
        reasons.append(
            f"Strongest open contributor: {strongest.get('symbol')} at {_fmt_pct(strongest.get('unrealized_return_pct'))} / {_fmt_jpy(strongest.get('unrealized_pnl_jpy'))}."
        )

    best_trade = champion.get("best_trade")
    if best_trade and _to_float(best_trade.get("pnl_jpy")) > 0:
        reasons.append(
            f"Best closed trade: {best_trade.get('symbol')} produced {_fmt_jpy(best_trade.get('pnl_jpy'))}."
        )

    champ_dd = abs(_to_float(champion.get("max_drawdown_pct")))
    peers = [a for a in agents if a.get("agent_id") != champ_id]
    peer_dds = [abs(_to_float(a.get("max_drawdown_pct"))) for a in peers]
    if peer_dds and champ_dd <= sorted(peer_dds + [champ_dd])[len(peer_dds + [champ_dd]) // 2]:
        reasons.append(f"Drawdown remains controlled at {_fmt_pct(champion.get('max_drawdown_pct'))}.")

    if not reasons:
        reasons.append("Ranks first on current portfolio equity after realised and unrealised P/L.")
    return reasons[:3]


def enrich_ranking(ranking: dict, simulation: dict) -> dict:
    agents = ranking.get("agents") or []
    sim_by_agent = _simulation_by_agent(simulation)

    returns = [_to_float(a.get("return_pct")) for a in agents]
    min_ret = min(returns) if returns else 0.0
    max_ret = max(returns) if returns else 0.0
    span = max(0.01, max_ret - min_ret)

    # Global bounds for the multi-agent race chart. Use all daily return points,
    # not only final returns, so lines are scaled consistently across agents.
    all_curve_values: list[float] = []
    for a in agents:
        sim_agent = sim_by_agent.get(str(a.get("agent_id") or ""), {})
        all_curve_values.extend(_curve_values(sim_agent.get("equity_curve") or []))
    race_low = min(all_curve_values) if all_curve_values else min_ret
    race_high = max(all_curve_values) if all_curve_values else max_ret
    if race_low == race_high:
        race_low -= 1.0
        race_high += 1.0
    else:
        margin = max(0.25, (race_high - race_low) * 0.08)
        race_low -= margin
        race_high += margin

    enriched: list[dict] = []
    for a in agents:
        item = dict(a)
        agent_id = str(item.get("agent_id") or "")
        sim_agent = sim_by_agent.get(agent_id, {})
        ret = _to_float(item.get("return_pct"))
        rank = _to_int(item.get("rank"), 99)
        closed_trades = sim_agent.get("closed_trades") or []
        open_positions = sim_agent.get("open_positions") or []
        equity_curve = sim_agent.get("equity_curve") or []
        curve_values = _curve_values(equity_curve)

        item["bar_width_pct"] = max(10.0, min(100.0, 10.0 + ((ret - min_ret) / span) * 90.0)) if agents else 50.0
        item["return_class"] = "positive" if ret >= 0 else "negative"
        item["avatar_style"] = item.get("avatar_style") or sim_agent.get("avatar_style") or AVATAR_BY_AGENT.get(agent_id, "pixel_warrior")
        item["avatar_image"] = item.get("avatar_image") or sim_agent.get("avatar_image") or AVATAR_IMAGE_BY_AGENT.get(agent_id)
        item["ui_tone"] = item.get("ui_tone") or sim_agent.get("ui_tone") or TONE_BY_AGENT.get(agent_id, "cyan")
        item["personality"] = sim_agent.get("personality") or ""
        item["philosophy"] = sim_agent.get("philosophy") or ""
        item["podium_label"] = PODIUM_LABEL_BY_RANK.get(rank, "LOW")
        item["rank_glow"] = "champion" if rank == 1 else "challenger"

        item["equity_curve"] = equity_curve
        item["equity_curve_count"] = len(equity_curve)
        item["spark_points"] = _normalised_points(curve_values)
        item["race_points"] = _race_points(curve_values or [ret], race_low, race_high)
        item["race_last_xy"] = _last_xy(item["race_points"])
        item["recent_momentum_pct"] = _recent_momentum(curve_values)
        item["recent_momentum_class"] = "positive" if item["recent_momentum_pct"] >= 0 else "negative"

        item["best_trade"] = _best_trade(closed_trades)
        item["worst_trade"] = _worst_trade(closed_trades)
        item["strongest_open_position"] = _strongest_open_position(open_positions)
        item["closed_trade_list_count"] = len(closed_trades)
        item["open_position_list_count"] = len(open_positions)
        item["has_real_curve"] = len(curve_values) >= 2
        enriched.append(item)

    enriched.sort(key=lambda x: _to_int(x.get("rank"), 99))

    ranking = dict(ranking)
    ranking["agents"] = enriched
    ranking["podium"] = enriched[:3]
    ranking["return_spread_pct"] = (max_ret - min_ret) if enriched else 0.0
    ranking["race"] = {
        "min_return_pct": race_low,
        "max_return_pct": race_high,
        "start_date": (ranking.get("range") or {}).get("start_date") or (simulation.get("range") or {}).get("start_date") or "—",
        "end_date": (ranking.get("range") or {}).get("end_date") or (simulation.get("range") or {}).get("end_date") or "—",
        "has_real_curves": any(a.get("has_real_curve") for a in enriched),
    }

    if enriched:
        champion_id = (ranking.get("champion") or {}).get("agent_id")
        champion = next((a for a in enriched if a.get("agent_id") == champion_id), enriched[0])
        champion = dict(champion)
        champion["why_leading"] = _build_champion_reasons(champion, enriched)
        ranking["champion"] = champion
    else:
        ranking["champion"] = None

    return ranking


def main() -> None:
    ranking_raw = read_json(RANKING_JSON, {})
    simulation_raw = read_json(SIMULATION_JSON, {})
    ranking = enrich_ranking(ranking_raw, simulation_raw)
    html = env().get_template("ai_arena_ranking_jp.html.j2").render(ranking=ranking)
    write_text(OUT_DIR / "japan/ai-arena/ranking/index.html", html)
    copy_asset("ai_arena_ranking_jp.css")


if __name__ == "__main__":
    main()
