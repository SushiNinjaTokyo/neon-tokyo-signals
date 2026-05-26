from __future__ import annotations

"""Render AI Arena Ranking page.

The simulation engine remains the source of truth for trading/accounting.
This renderer reads the lightweight ranking JSON plus simulation/latest.json and
creates view-only fields for the leaderboard UI: real equity sparklines, return
race paths, best/worst trades, strongest open positions, podium labels, and
champion explanation copy.
"""

import os
from datetime import datetime
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

RANK_META_BY_RANK = {
    1: {"podium_label": "GOLD CROWN", "podium_class": "gold", "podium_tier": "crown", "rank_title": "Season Leader"},
    2: {"podium_label": "SILVER CROWN", "podium_class": "silver", "podium_tier": "crown", "rank_title": "Runner Up"},
    3: {"podium_label": "BRONZE CROWN", "podium_class": "bronze", "podium_tier": "crown", "rank_title": "Third Force"},
    4: {"podium_label": "CHALLENGER", "podium_class": "challenger", "podium_tier": "badge", "rank_title": "Challenger"},
    5: {"podium_label": "LOW SIGNAL", "podium_class": "low", "podium_tier": "badge", "rank_title": "Low Signal"},
}

PROFILE_LABELS = {
    "daily_v2_core": "Momentum Strike",
    "daily_stage1": "Opening Strike",
    "daily_stage2": "Momentum Chase",
    "weekly_stage1": "Trend Watch",
    "weekly_stage2": "Trend Core",
    "risk_defender": "Capital Shield",
    "risk_stage1": "Risk Guard",
    "risk_stage2": "Capital Shield",
    "discovery_alpha": "Hidden Alpha",
    "discovery_stage1": "Hidden Alpha",
    "discovery_stage2": "Early Breakout",
    "contrarian_reentry": "Reversal Hunt",
    "contrarian_stage1": "Pullback Watch",
    "contrarian_stage2": "Reversal Setup",
}

STYLE_LABEL_BY_AGENT = {
    "daily_striker": "Momentum Strike",
    "weekly_sage": "Trend Core",
    "risk_sentinel": "Capital Shield",
    "discovery_scout": "Hidden Alpha",
    "contrarian_monk": "Reversal Hunt",
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


def _humanize_internal_text(text: Any) -> str:
    s = str(text or "")
    for raw, label in PROFILE_LABELS.items():
        s = s.replace(raw, label)
    s = s.replace("stop_loss", "Stop loss")
    s = s.replace("take_profit", "Take profit")
    s = s.replace("time_exit", "Time exit")
    s = s.replace("no daily confirmation", "confirmation still forming")
    return s


def _trim(text: Any, limit: int = 132) -> str:
    s = " ".join(_humanize_internal_text(text).split())
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


def _curve_date(point: dict) -> datetime | None:
    raw = point.get("date") or point.get("execution_date") or point.get("current_date")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw)[:10])
    except Exception:
        return None


def _return_delta_by_sessions(values: list[float], sessions: int) -> float | None:
    if len(values) < 2:
        return None
    idx = max(0, len(values) - 1 - sessions)
    if idx == len(values) - 1:
        return None
    return values[-1] - values[idx]


def _curve_equity_values(equity_curve: list[dict]) -> list[float]:
    values: list[float] = []
    for point in equity_curve:
        if not isinstance(point, dict):
            continue
        equity = _to_float(point.get("portfolio_equity_jpy") or point.get("equity_jpy"))
        if equity > 0:
            values.append(equity)
    return values


def _period_gain_vs_initial_by_sessions(equity_values: list[float], sessions: int, initial_capital: float) -> float | None:
    """Return period P/L as a % of initial capital.

    Example: if current equity is ¥17.8m, 1W-ago equity is ¥17.4m,
    and initial capital is ¥10.0m, the 1W value is +4.0%.
    This is intentionally not a percentage-point label change; it measures
    how much of the original capital was gained/lost during the period.
    """
    if len(equity_values) < 2 or initial_capital <= 0:
        return None
    idx = max(0, len(equity_values) - 1 - sessions)
    if idx == len(equity_values) - 1:
        return None
    return (equity_values[-1] - equity_values[idx]) / initial_capital * 100.0


def _performance_windows(equity_curve: list[dict], initial_capital: float) -> list[dict]:
    # Trading-session based windows. Values are period gains/losses measured
    # against the original capital, not simple changes in return percentages.
    specs = [("1W", 5), ("1M", 21), ("3M", 63), ("6M", 126)]
    equity_values = _curve_equity_values(equity_curve)
    out: list[dict] = []
    for label, sessions in specs:
        value = _period_gain_vs_initial_by_sessions(equity_values, sessions, initial_capital)
        if value is None:
            out.append({"label": label, "value": None, "class": "neutral", "display": "—"})
        else:
            out.append({
                "label": label,
                "value": value,
                "class": "positive" if value >= 0 else "negative",
                "display": f"{value:+.2f}%",
            })
    return out


def _rank_meta(rank: int) -> dict[str, str]:
    return dict(RANK_META_BY_RANK.get(rank, RANK_META_BY_RANK[5]))


def _display_profile(agent_id: str, screening_profile: Any, fallback_class: Any = "") -> str:
    raw = str(screening_profile or "").strip()
    if raw in PROFILE_LABELS:
        return PROFILE_LABELS[raw]
    if agent_id in STYLE_LABEL_BY_AGENT:
        return STYLE_LABEL_BY_AGENT[agent_id]
    if raw:
        return raw.replace("_", " ").replace("v2", "").title().strip()
    return str(fallback_class or "AI Strategy")


def _closed_pnl_jpy(closed_trades: list[dict]) -> float:
    return sum(_to_float(t.get("pnl_jpy")) for t in closed_trades if isinstance(t, dict))


def _open_unrealized_pnl_jpy(open_positions: list[dict]) -> float:
    return sum(_to_float(p.get("unrealized_pnl_jpy")) for p in open_positions if isinstance(p, dict))


def _build_champion_reasons(champion: dict, agents: list[dict]) -> list[str]:
    if not champion:
        return []

    reasons: list[str] = []
    champ_id = champion.get("agent_id")
    champ_return = _to_float(champion.get("return_pct"))
    best_return = max((_to_float(a.get("return_pct")) for a in agents), default=champ_return)
    if champ_return >= best_return - 0.0001:
        reasons.append(f"Leads on total portfolio return at {_fmt_pct(champ_return)}.")

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
        reasons.append("Ranks first on total portfolio return, including realised and unrealised P/L.")
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

        initial_capital = _to_float(item.get("initial_capital_jpy") or (sim_agent.get("summary") or {}).get("initial_capital_jpy"))
        portfolio_equity = _to_float(item.get("portfolio_equity_jpy") or (sim_agent.get("summary") or {}).get("portfolio_equity_jpy"))
        realised_pnl = _closed_pnl_jpy(closed_trades)
        unrealised_pnl = _open_unrealized_pnl_jpy(open_positions)
        total_return_pct = ((portfolio_equity - initial_capital) / initial_capital * 100.0) if initial_capital else ret

        # Ranking is total portfolio equity based: cash + current market value.
        # Realised and unrealised P/L are shown separately for explainability, but
        # the rank itself follows total_return_pct.
        ret = total_return_pct
        item["return_pct"] = total_return_pct
        item["total_return_pct"] = total_return_pct
        item["realized_pnl_jpy"] = realised_pnl
        item["realized_return_pct"] = (realised_pnl / initial_capital * 100.0) if initial_capital else 0.0
        item["unrealized_pnl_jpy"] = unrealised_pnl
        item["unrealized_return_pct"] = (unrealised_pnl / initial_capital * 100.0) if initial_capital else 0.0
        item["ranking_basis_label"] = "Total Return"

        item["bar_width_pct"] = max(10.0, min(100.0, 10.0 + ((ret - min_ret) / span) * 90.0)) if agents else 50.0
        item["return_class"] = "positive" if ret >= 0 else "negative"
        item["avatar_style"] = item.get("avatar_style") or sim_agent.get("avatar_style") or AVATAR_BY_AGENT.get(agent_id, "pixel_warrior")
        item["avatar_image"] = item.get("avatar_image") or sim_agent.get("avatar_image") or AVATAR_IMAGE_BY_AGENT.get(agent_id)
        item["ui_tone"] = item.get("ui_tone") or sim_agent.get("ui_tone") or TONE_BY_AGENT.get(agent_id, "cyan")
        item["personality"] = sim_agent.get("personality") or ""
        item["philosophy"] = sim_agent.get("philosophy") or ""
        item["display_profile"] = _display_profile(agent_id, item.get("screening_profile"), item.get("class"))
        item.update(_rank_meta(rank))
        item["rank_glow"] = "champion" if rank == 1 else "challenger"

        item["equity_curve"] = equity_curve
        item["equity_curve_count"] = len(equity_curve)
        item["spark_points"] = _normalised_points(curve_values)
        item["race_points"] = _race_points(curve_values or [ret], race_low, race_high)
        item["race_last_xy"] = _last_xy(item["race_points"])
        item["curve_sessions_label"] = f"{len(equity_curve)} sessions" if equity_curve else "No curve"
        item["recent_momentum_pct"] = _recent_momentum(curve_values)
        item["recent_momentum_class"] = "positive" if item["recent_momentum_pct"] >= 0 else "negative"
        item["recent_momentum_display"] = f"{item['recent_momentum_pct']:+.2f}%"
        item["performance_windows"] = _performance_windows(equity_curve, initial_capital)

        item["best_trade"] = _best_trade(closed_trades)
        item["worst_trade"] = _worst_trade(closed_trades)
        item["strongest_open_position"] = _strongest_open_position(open_positions)
        item["best_trade_label"] = "BEST CLOSED"
        item["worst_trade_label"] = "WORST CLOSED"
        item["open_position_label"] = "STRONGEST OPEN" if item["strongest_open_position"] and _to_float(item["strongest_open_position"].get("unrealized_pnl_jpy")) >= 0 else "LARGEST OPEN"
        item["closed_trade_list_count"] = len(closed_trades)
        item["open_position_list_count"] = len(open_positions)
        item["has_real_curve"] = len(curve_values) >= 2
        enriched.append(item)

    enriched.sort(key=lambda x: (_to_float(x.get("total_return_pct")), _to_float(x.get("portfolio_equity_jpy"))), reverse=True)
    for idx, item in enumerate(enriched, start=1):
        item["rank"] = idx
        item.update(_rank_meta(idx))

    # Recalculate bar widths after the rank basis has been normalised.
    final_returns = [_to_float(a.get("total_return_pct")) for a in enriched]
    min_ret = min(final_returns) if final_returns else 0.0
    max_ret = max(final_returns) if final_returns else 0.0
    span = max(0.01, max_ret - min_ret)
    for item in enriched:
        ret = _to_float(item.get("total_return_pct"))
        item["bar_width_pct"] = max(10.0, min(100.0, 10.0 + ((ret - min_ret) / span) * 90.0)) if enriched else 50.0
        item["return_class"] = "positive" if ret >= 0 else "negative"

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
