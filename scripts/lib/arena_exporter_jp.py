from __future__ import annotations

"""Export DuckDB AI Arena season data into lightweight public JSON.

This module is intentionally presentation-aware, but not strategy-aware.
It reads the already-computed season tables and writes compact JSON files
for the static UI.  The heavy calculations remain in the season rebuild
engine and ranking engine.

Design notes:
- DuckDB stays in GitHub Actions cache and is never committed.
- Public JSON should be compact, stable, and easy for templates to render.
- Diagnostics are exported together with the normal payloads so that we can
  immediately see whether an Agent is really trading or simply sitting at
  initial capital.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from .arena_calendar_jp import downsample_points

THEME_COLOR_HEX = {
    "cyan": "#7DF9FF",
    "blue": "#70A7FF",
    "green": "#5DFFB1",
    "amber": "#FFD166",
    "yellow": "#FFD166",
    "violet": "#B779FF",
    "purple": "#B779FF",
    "magenta": "#FF4FD8",
    "pink": "#FF4FD8",
    "indigo": "#6F7DFF",
    "red": "#FF6B8A",
}


def _normalise_agent(agent: dict[str, Any]) -> dict[str, Any]:
    """Add UI-friendly aliases to an Agent profile.

    The YAML intentionally uses semantic field names such as theme_color,
    style_label, and short_description.  Templates should not need to know
    every historical alias, so the exporter normalises common UI fields here.
    """
    out = dict(agent)
    theme = str(out.get("theme_color") or "cyan").lower()
    out.setdefault("color", THEME_COLOR_HEX.get(theme, out.get("theme_color") or "#7DF9FF"))
    out.setdefault("style", out.get("style_label") or "")
    out.setdefault("description", out.get("short_description") or "")
    return out



def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically write a UTF-8 JSON file.

    GitHub Actions can be interrupted, and Vercel may deploy shortly after a
    commit.  Writing through a temporary file prevents half-written JSON from
    being committed if a process crashes mid-write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    """Atomically write a UTF-8 text file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return JSON-serialisable records from a DataFrame."""
    if df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def _scalar(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None, default: Any = 0) -> Any:
    """Run a scalar query and return a default on empty/null results."""
    try:
        row = conn.execute(sql, params or []).fetchone()
    except Exception:
        return default
    if not row or row[0] is None:
        return default
    return row[0]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or pd.isna(value):
            return default
        return int(value)
    except Exception:
        return default


def _sparkline_polyline(points: list[dict[str, Any]], *, width: int = 220, height: int = 54, pad: int = 4) -> str:
    """Convert equity sparkline points into an SVG polyline string.

    The template can render this directly without client-side charting code.
    This keeps the page static, fast, and Vercel-friendly.
    """
    if not points:
        return ""
    values = [_safe_float(p.get("equity")) for p in points]
    if not values:
        return ""
    v_min = min(values)
    v_max = max(values)
    span = v_max - v_min
    usable_w = max(1, width - pad * 2)
    usable_h = max(1, height - pad * 2)
    n = len(values)
    coords: list[str] = []
    for i, v in enumerate(values):
        x = pad + (usable_w * i / max(1, n - 1))
        if span == 0:
            y = height / 2
        else:
            y = pad + usable_h * (1 - (v - v_min) / span)
        coords.append(f"{x:.1f},{y:.1f}")
    return " ".join(coords)


def _build_monthly_heatmap(*, monthly_records: list[dict[str, Any]], agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create a 7-agent x 12-month matrix for the Summary heatmap.

    The raw monthly ranking table is row-oriented.  The UI is easier and more
    stable when the template receives fixed rows with 12 cells.
    """
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for row in monthly_records:
        by_key[(str(row.get("agent_id")), _safe_int(row.get("month")))] = row

    rows: list[dict[str, Any]] = []
    for agent in agents:
        aid = str(agent.get("agent_id"))
        cells = []
        for month in range(1, 13):
            src = by_key.get((aid, month), {})
            ret = src.get("monthly_return_pct")
            cells.append({
                "month": month,
                "label": datetime(2000, month, 1).strftime("%b"),
                "return_pct": None if ret is None else round(_safe_float(ret), 2),
                "rank": src.get("rank"),
                "has_data": bool(src),
            })
        rows.append({
            "agent_id": aid,
            "name": agent.get("name") or aid.upper(),
            "color": agent.get("color") or "#7DF9FF",
            "cells": cells,
        })
    return rows


def _build_diagnostics(
    conn: duckdb.DuckDBPyConnection,
    *,
    run_id: str,
    year: int,
    agents: list[dict[str, Any]],
    ranking_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build diagnostics explaining whether the season is actually trading.

    This is intentionally redundant with visible ranking data.  During rule
    tuning, we need to know whether an Agent has poor performance or simply no
    fills.  The JSON and Markdown diagnostics are also useful from GitHub diff.
    """
    generated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    agent_by_id = {str(a.get("agent_id")): a for a in agents}
    ranking_by_agent = {str(r.get("agent_id")): r for r in ranking_records}

    # Pull all orders/trades/positions once.  Data volumes are small because
    # this is run-scoped output, not full historical price data.
    orders = conn.execute("SELECT * FROM arena_orders WHERE run_id = ?", [run_id]).df()
    trades = conn.execute("SELECT * FROM arena_trades WHERE run_id = ?", [run_id]).df()
    positions = conn.execute("SELECT * FROM arena_open_positions WHERE run_id = ?", [run_id]).df()
    equity = conn.execute("SELECT * FROM arena_equity_curve WHERE run_id = ?", [run_id]).df()

    run_df = conn.execute("SELECT * FROM arena_simulation_runs WHERE run_id = ?", [run_id]).df()
    start_date = None
    end_date = None
    if not run_df.empty:
        start_date = str(run_df.iloc[0].get("start_date") or "") or None
        end_date = str(run_df.iloc[0].get("end_date") or "") or None

    # Agent score activity is not run-scoped, so use the run date range when
    # available.  If end_date is missing, fall back to the target year.
    score_where = "WHERE 1=1"
    score_params: list[Any] = []
    if start_date:
        score_where += " AND date >= ?"
        score_params.append(start_date)
    else:
        score_where += " AND date >= ?"
        score_params.append(f"{year}-01-01")
    if end_date:
        score_where += " AND date <= ?"
        score_params.append(end_date)
    else:
        score_where += " AND date <= ?"
        score_params.append(f"{year}-12-31")

    try:
        score_activity = conn.execute(
            f"""
            SELECT
              agent_id,
              COUNT(*) AS score_rows,
              SUM(CASE WHEN action = 'Trade' THEN 1 ELSE 0 END) AS trade_signals,
              SUM(CASE WHEN action = 'Watch' THEN 1 ELSE 0 END) AS watch_signals,
              SUM(CASE WHEN action = 'Ignore' THEN 1 ELSE 0 END) AS ignore_signals,
              MAX(date) AS latest_score_date
            FROM agent_scores_daily
            {score_where}
            GROUP BY agent_id
            """,
            score_params,
        ).df()
    except Exception:
        score_activity = pd.DataFrame()

    score_by_agent: dict[str, dict[str, Any]] = {}
    if not score_activity.empty:
        for _, row in score_activity.iterrows():
            score_by_agent[str(row["agent_id"])] = row.to_dict()

    activity: list[dict[str, Any]] = []
    for aid, agent in agent_by_id.items():
        odf = orders[orders["agent_id"] == aid] if not orders.empty else pd.DataFrame()
        tdf = trades[trades["agent_id"] == aid] if not trades.empty else pd.DataFrame()
        pdf = positions[positions["agent_id"] == aid] if not positions.empty else pd.DataFrame()
        edf = equity[equity["agent_id"] == aid].sort_values("date") if not equity.empty else pd.DataFrame()
        srow = score_by_agent.get(aid, {})
        rrow = ranking_by_agent.get(aid, {})

        buy_orders = odf[odf["side"] == "BUY"] if not odf.empty else pd.DataFrame()
        sell_orders = odf[odf["side"] == "SELL"] if not odf.empty else pd.DataFrame()
        executed_buys = buy_orders[buy_orders["order_status"] == "FILLED"] if not buy_orders.empty else pd.DataFrame()
        executed_sells = sell_orders[sell_orders["order_status"] == "FILLED"] if not sell_orders.empty else pd.DataFrame()
        cancelled_buys = buy_orders[buy_orders["order_status"] == "CANCELLED"] if not buy_orders.empty else pd.DataFrame()
        pending_orders = odf[odf["order_status"] == "PENDING"] if not odf.empty else pd.DataFrame()

        latest_equity = _safe_float(edf.iloc[-1].get("portfolio_equity_jpy")) if not edf.empty else None
        total_return = _safe_float(rrow.get("total_return_pct"), 0.0)
        closed_trades = len(tdf)
        open_positions = len(pdf)
        trade_signals = _safe_int(srow.get("trade_signals"), 0)
        executed_buy_count = len(executed_buys)

        warnings: list[str] = []
        if trade_signals == 0:
            warnings.append("NO_TRADE_SIGNALS")
        if trade_signals > 0 and executed_buy_count == 0:
            warnings.append("SIGNALS_BUT_NO_BUYS")
        if executed_buy_count > 0 and closed_trades == 0 and open_positions == 0:
            warnings.append("BUYS_WITHOUT_VISIBLE_POSITIONS_OR_TRADES")
        if abs(total_return) < 0.0001 and executed_buy_count == 0:
            warnings.append("FLAT_NO_EXECUTED_BUYS")

        activity.append({
            "agent_id": aid,
            "name": agent.get("name") or aid.upper(),
            "role": agent.get("role") or "",
            "color": agent.get("color") or "#7DF9FF",
            "score_rows": _safe_int(srow.get("score_rows"), 0),
            "trade_signals": trade_signals,
            "watch_signals": _safe_int(srow.get("watch_signals"), 0),
            "ignore_signals": _safe_int(srow.get("ignore_signals"), 0),
            "latest_score_date": str(srow.get("latest_score_date") or "") or None,
            "buy_orders": len(buy_orders),
            "executed_buys": executed_buy_count,
            "cancelled_buys": len(cancelled_buys),
            "sell_orders": len(sell_orders),
            "executed_sells": len(executed_sells),
            "pending_orders": len(pending_orders),
            "closed_trades": closed_trades,
            "open_positions": open_positions,
            "latest_equity_jpy": latest_equity,
            "total_return_pct": round(total_return, 4),
            "first_equity_date": str(edf.iloc[0].get("date")) if not edf.empty else None,
            "last_equity_date": str(edf.iloc[-1].get("date")) if not edf.empty else None,
            "warnings": warnings,
        })

    order_status_counts: list[dict[str, Any]] = []
    if not orders.empty:
        g = orders.groupby(["side", "order_status"], dropna=False).size().reset_index(name="count")
        order_status_counts = _records(g)

    cancel_reason_counts: list[dict[str, Any]] = []
    if not orders.empty:
        cancelled = orders[orders["order_status"] == "CANCELLED"]
        if not cancelled.empty:
            cg = cancelled.groupby(["side", "reason_code"], dropna=False).size().reset_index(name="count")
            cancel_reason_counts = _records(cg.sort_values("count", ascending=False))

    agents_with_executed_buys = sum(1 for a in activity if a["executed_buys"] > 0)
    agents_with_closed_trades = sum(1 for a in activity if a["closed_trades"] > 0)
    flat_agents = [a["agent_id"] for a in activity if "FLAT_NO_EXECUTED_BUYS" in a["warnings"]]

    totals = {
        "orders": int(len(orders)),
        "filled_orders": int(len(orders[orders["order_status"] == "FILLED"])) if not orders.empty else 0,
        "cancelled_orders": int(len(orders[orders["order_status"] == "CANCELLED"])) if not orders.empty else 0,
        "pending_orders": int(len(orders[orders["order_status"] == "PENDING"])) if not orders.empty else 0,
        "buy_orders": int(len(orders[orders["side"] == "BUY"])) if not orders.empty else 0,
        "sell_orders": int(len(orders[orders["side"] == "SELL"])) if not orders.empty else 0,
        "trades": int(len(trades)),
        "open_positions": int(len(positions)),
        "equity_rows": int(len(equity)),
        "agents": int(len(agents)),
        "agents_with_executed_buys": agents_with_executed_buys,
        "agents_with_closed_trades": agents_with_closed_trades,
        "flat_agents_without_buys": flat_agents,
    }

    warnings: list[str] = []
    if agents_with_executed_buys < len(agents):
        warnings.append("Some agents have no executed buy orders. Check thresholds, feature availability, and skipped orders.")
    if totals["orders"] == 0:
        warnings.append("No arena orders were generated for this run.")
    if totals["trades"] == 0:
        warnings.append("No closed trades were generated for this run.")

    return {
        "schema_version": "ai_arena_diagnostics_v1",
        "generated_at": generated_at,
        "year": year,
        "run_id": run_id,
        "period": {"start_date": start_date, "end_date": end_date},
        "totals": totals,
        "agent_activity": activity,
        "order_status_counts": order_status_counts,
        "cancel_reason_counts": cancel_reason_counts,
        "warnings": warnings,
    }


def _diagnostics_markdown(diag: dict[str, Any]) -> str:
    """Create a compact Markdown diagnostics report for Git diffs."""
    lines: list[str] = []
    lines.append("# AI Arena Diagnostics")
    lines.append("")
    lines.append(f"Generated: {diag.get('generated_at')}")
    lines.append(f"Run: `{diag.get('run_id')}`")
    lines.append(f"Year: {diag.get('year')}")
    lines.append("")
    totals = diag.get("totals", {})
    lines.append("## Totals")
    for key in [
        "orders", "filled_orders", "cancelled_orders", "buy_orders", "sell_orders",
        "trades", "open_positions", "equity_rows", "agents_with_executed_buys",
        "agents_with_closed_trades",
    ]:
        lines.append(f"- {key}: {totals.get(key, 0)}")
    if totals.get("flat_agents_without_buys"):
        lines.append(f"- flat_agents_without_buys: {', '.join(totals.get('flat_agents_without_buys'))}")
    lines.append("")

    lines.append("## Agent Activity")
    lines.append("| Agent | Trade signals | Executed buys | Executed sells | Closed trades | Open positions | Return | Warnings |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for a in diag.get("agent_activity", []):
        warnings = ", ".join(a.get("warnings") or []) or "-"
        lines.append(
            f"| {a.get('name') or a.get('agent_id')} | "
            f"{a.get('trade_signals', 0)} | {a.get('executed_buys', 0)} | "
            f"{a.get('executed_sells', 0)} | {a.get('closed_trades', 0)} | "
            f"{a.get('open_positions', 0)} | {a.get('total_return_pct', 0):.2f}% | {warnings} |"
        )
    lines.append("")

    if diag.get("warnings"):
        lines.append("## Warnings")
        for w in diag.get("warnings", []):
            lines.append(f"- {w}")
        lines.append("")
    return "\n".join(lines) + "\n"



def _safe_div(num: float, den: float, default: float = 0.0) -> float:
    try:
        if den == 0:
            return default
        return float(num) / float(den)
    except Exception:
        return default


def _agent_trade_stats(trades: pd.DataFrame, agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build per-Agent trade statistics for Summary JSON."""
    rows: list[dict[str, Any]] = []
    for agent in agents:
        aid = str(agent.get("agent_id"))
        tdf = trades[trades["agent_id"] == aid] if not trades.empty and "agent_id" in trades.columns else pd.DataFrame()
        if tdf.empty:
            rows.append({
                "agent_id": aid,
                "name": agent.get("name") or aid.upper(),
                "color": agent.get("color") or "#7DF9FF",
                "closed_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate_pct": 0.0,
                "avg_return_pct": 0.0,
                "median_return_pct": 0.0,
                "best_return_pct": None,
                "worst_return_pct": None,
                "realized_pnl_jpy": 0.0,
                "avg_holding_days": 0.0,
            })
            continue
        ret = pd.to_numeric(tdf.get("realized_return_pct"), errors="coerce").dropna()
        pnl = pd.to_numeric(tdf.get("realized_pnl_jpy"), errors="coerce").fillna(0.0)
        hold = pd.to_numeric(tdf.get("holding_days"), errors="coerce").dropna()
        wins = int((ret > 0).sum()) if not ret.empty else 0
        losses = int((ret <= 0).sum()) if not ret.empty else 0
        rows.append({
            "agent_id": aid,
            "name": agent.get("name") or aid.upper(),
            "color": agent.get("color") or "#7DF9FF",
            "closed_trades": int(len(tdf)),
            "wins": wins,
            "losses": losses,
            "win_rate_pct": round(_safe_div(wins * 100.0, max(1, len(tdf))), 2),
            "avg_return_pct": round(float(ret.mean()), 4) if not ret.empty else 0.0,
            "median_return_pct": round(float(ret.median()), 4) if not ret.empty else 0.0,
            "best_return_pct": round(float(ret.max()), 4) if not ret.empty else None,
            "worst_return_pct": round(float(ret.min()), 4) if not ret.empty else None,
            "realized_pnl_jpy": round(float(pnl.sum()), 2),
            "avg_holding_days": round(float(hold.mean()), 2) if not hold.empty else 0.0,
        })
    return rows


def _build_portfolio_snapshot(
    conn: duckdb.DuckDBPyConnection,
    *,
    run_id: str,
    positions: pd.DataFrame,
    trades: pd.DataFrame,
    agents: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build current portfolio and ticker contribution summary.

    Contribution combines closed realized P/L and current open unrealized P/L.
    This makes the Summary page useful even mid-season when some positions are
    still open and would not appear in closed-trade rankings.
    """
    agent_by_id = {str(a.get("agent_id")): a for a in agents}

    enriched_positions = positions.copy() if not positions.empty else pd.DataFrame()
    if not enriched_positions.empty:
        try:
            universe = conn.execute(
                """
                SELECT ticker, sector, industry, bucket, market
                FROM universe_master
                """
            ).df()
            if not universe.empty:
                enriched_positions = enriched_positions.merge(universe, on="ticker", how="left")
        except Exception:
            pass

    total_mv = float(pd.to_numeric(enriched_positions.get("market_value_jpy"), errors="coerce").fillna(0).sum()) if not enriched_positions.empty else 0.0

    top_positions: list[dict[str, Any]] = []
    if not enriched_positions.empty:
        work = enriched_positions.copy()
        work["market_value_jpy"] = pd.to_numeric(work.get("market_value_jpy"), errors="coerce").fillna(0.0)
        work["unrealized_pnl_jpy"] = pd.to_numeric(work.get("unrealized_pnl_jpy"), errors="coerce").fillna(0.0)
        work["weight_pct"] = work["market_value_jpy"].apply(lambda x: round(_safe_div(x * 100.0, total_mv), 3) if total_mv else 0.0)
        work["agent_name"] = work["agent_id"].map(lambda x: agent_by_id.get(str(x), {}).get("name") or str(x))
        top_positions = _records(work.sort_values("market_value_jpy", ascending=False).head(30))

    allocation_by_agent: list[dict[str, Any]] = []
    if not enriched_positions.empty:
        g = enriched_positions.groupby("agent_id", dropna=False).agg(
            market_value_jpy=("market_value_jpy", "sum"),
            unrealized_pnl_jpy=("unrealized_pnl_jpy", "sum"),
            position_count=("ticker", "count"),
        ).reset_index()
        g["weight_pct"] = g["market_value_jpy"].apply(lambda x: round(_safe_div(float(x) * 100.0, total_mv), 3) if total_mv else 0.0)
        g["agent_name"] = g["agent_id"].map(lambda x: agent_by_id.get(str(x), {}).get("name") or str(x))
        g["color"] = g["agent_id"].map(lambda x: agent_by_id.get(str(x), {}).get("color") or "#7DF9FF")
        allocation_by_agent = _records(g.sort_values("market_value_jpy", ascending=False))

    allocation_by_sector: list[dict[str, Any]] = []
    if not enriched_positions.empty and "sector" in enriched_positions.columns:
        s = enriched_positions.copy()
        s["sector"] = s["sector"].fillna("Unknown")
        sg = s.groupby("sector", dropna=False).agg(
            market_value_jpy=("market_value_jpy", "sum"),
            position_count=("ticker", "count"),
        ).reset_index()
        sg["weight_pct"] = sg["market_value_jpy"].apply(lambda x: round(_safe_div(float(x) * 100.0, total_mv), 3) if total_mv else 0.0)
        allocation_by_sector = _records(sg.sort_values("market_value_jpy", ascending=False).head(15))

    realized = pd.DataFrame()
    if not trades.empty:
        realized = trades.groupby(["ticker", "name"], dropna=False).agg(
            realized_pnl_jpy=("realized_pnl_jpy", "sum"),
            closed_trades=("ticker", "count"),
        ).reset_index()
    unrealized = pd.DataFrame()
    if not enriched_positions.empty:
        unrealized = enriched_positions.groupby(["ticker", "name"], dropna=False).agg(
            unrealized_pnl_jpy=("unrealized_pnl_jpy", "sum"),
            market_value_jpy=("market_value_jpy", "sum"),
            open_positions=("ticker", "count"),
        ).reset_index()
    if realized.empty and unrealized.empty:
        contribution_records: list[dict[str, Any]] = []
    elif realized.empty:
        contribution = unrealized.copy()
        contribution["realized_pnl_jpy"] = 0.0
        contribution["closed_trades"] = 0
    elif unrealized.empty:
        contribution = realized.copy()
        contribution["unrealized_pnl_jpy"] = 0.0
        contribution["market_value_jpy"] = 0.0
        contribution["open_positions"] = 0
    else:
        contribution = realized.merge(unrealized, on=["ticker", "name"], how="outer").fillna(0)
    if not (realized.empty and unrealized.empty):
        contribution["total_pnl_jpy"] = pd.to_numeric(contribution.get("realized_pnl_jpy"), errors="coerce").fillna(0.0) + pd.to_numeric(contribution.get("unrealized_pnl_jpy"), errors="coerce").fillna(0.0)
        contribution_records = _records(contribution.sort_values("total_pnl_jpy", ascending=False).head(20))
        worst_contribution_records = _records(contribution.sort_values("total_pnl_jpy", ascending=True).head(20))
    else:
        worst_contribution_records = []

    return {
        "total_market_value_jpy": round(total_mv, 2),
        "open_position_count": int(len(enriched_positions)) if not enriched_positions.empty else 0,
        "top_positions": top_positions,
        "allocation_by_agent": allocation_by_agent,
        "allocation_by_sector": allocation_by_sector,
        "best_ticker_contribution": contribution_records,
        "worst_ticker_contribution": worst_contribution_records,
    }


def _build_equity_overview(equity: pd.DataFrame, agents: list[dict[str, Any]]) -> dict[str, Any]:
    """Build equity timeline metadata for the Summary page."""
    if equity.empty:
        return {"latest_date": None, "agent_latest": [], "daily_leaders": []}
    agent_by_id = {str(a.get("agent_id")): a for a in agents}
    latest_date = str(equity["date"].max())
    latest = equity[equity["date"].astype(str) == latest_date].copy()
    latest["agent_name"] = latest["agent_id"].map(lambda x: agent_by_id.get(str(x), {}).get("name") or str(x))
    latest["color"] = latest["agent_id"].map(lambda x: agent_by_id.get(str(x), {}).get("color") or "#7DF9FF")
    latest_records = _records(latest.sort_values("portfolio_equity_jpy", ascending=False))

    daily_leaders: list[dict[str, Any]] = []
    try:
        work = equity.copy()
        work["rank"] = work.groupby("date")["portfolio_equity_jpy"].rank(method="first", ascending=False)
        leaders = work[work["rank"] == 1].groupby("agent_id").size().reset_index(name="leader_days")
        leaders["agent_name"] = leaders["agent_id"].map(lambda x: agent_by_id.get(str(x), {}).get("name") or str(x))
        leaders["color"] = leaders["agent_id"].map(lambda x: agent_by_id.get(str(x), {}).get("color") or "#7DF9FF")
        daily_leaders = _records(leaders.sort_values("leader_days", ascending=False))
    except Exception:
        daily_leaders = []
    return {"latest_date": latest_date, "agent_latest": latest_records, "daily_leaders": daily_leaders}

def export_arena_payloads(
    conn: duckdb.DuckDBPyConnection,
    *,
    out_dir: Path,
    run_id: str,
    year: int,
    agents: list[dict[str, Any]],
    max_spark_points: int = 120,
) -> dict[str, Path]:
    """Write public AI Arena JSON files used by pages and legacy renderers."""
    generated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    base = out_dir / "data" / "japan" / "ai-arena"
    agents = [_normalise_agent(a) for a in agents]

    run = conn.execute("SELECT * FROM arena_simulation_runs WHERE run_id = ?", [run_id]).df()
    ranking = conn.execute("SELECT * FROM arena_yearly_rankings WHERE run_id = ? ORDER BY rank", [run_id]).df()
    monthly = conn.execute("SELECT * FROM arena_monthly_rankings WHERE run_id = ? ORDER BY month, rank", [run_id]).df()
    trades = conn.execute("SELECT * FROM arena_trades WHERE run_id = ? ORDER BY exit_date DESC, created_at DESC", [run_id]).df()
    positions = conn.execute("SELECT * FROM arena_open_positions WHERE run_id = ? ORDER BY agent_id, market_value_jpy DESC", [run_id]).df()
    equity = conn.execute("SELECT * FROM arena_equity_curve WHERE run_id = ? ORDER BY agent_id, date", [run_id]).df()
    best = conn.execute("SELECT * FROM arena_trade_rankings WHERE run_id = ? AND ranking_type = 'best_trade' ORDER BY rank", [run_id]).df()
    worst = conn.execute("SELECT * FROM arena_trade_rankings WHERE run_id = ? AND ranking_type = 'worst_trade' ORDER BY rank", [run_id]).df()

    agent_by_id = {a["agent_id"]: a for a in agents}
    spark: dict[str, list[dict[str, Any]]] = {}
    if not equity.empty:
        for agent_id, g in equity.groupby("agent_id"):
            pts = [
                {
                    "date": str(r["date"]),
                    "equity": round(float(r["portfolio_equity_jpy"]), 2),
                    "return_pct": round(float(r["total_return_pct"]), 4),
                }
                for _, r in g.sort_values("date").iterrows()
            ]
            spark[str(agent_id)] = downsample_points(pts, max_spark_points)

    ranking_records = _records(ranking)
    for r in ranking_records:
        aid = r.get("agent_id")
        agent = agent_by_id.get(aid, {})
        agent_spark = spark.get(aid, [])
        r["agent"] = agent
        r["sparkline"] = agent_spark
        r["sparkline_points"] = _sparkline_polyline(agent_spark)
        r["color"] = agent.get("color") or "#7DF9FF"

    monthly_records = _records(monthly)
    diag = _build_diagnostics(conn, run_id=run_id, year=year, agents=agents, ranking_records=ranking_records)
    activity_by_agent = {a["agent_id"]: a for a in diag.get("agent_activity", [])}
    for r in ranking_records:
        r["activity"] = activity_by_agent.get(r.get("agent_id"), {})

    trade_stats = _agent_trade_stats(trades, agents)
    portfolio_snapshot = _build_portfolio_snapshot(conn, run_id=run_id, positions=positions, trades=trades, agents=agents)
    equity_overview = _build_equity_overview(equity, agents)

    visuals = {
        "monthly_heatmap": _build_monthly_heatmap(monthly_records=monthly_records, agents=agents),
        "portfolio_allocation_by_agent": portfolio_snapshot.get("allocation_by_agent", []),
        "portfolio_allocation_by_sector": portfolio_snapshot.get("allocation_by_sector", []),
        "daily_leaders": equity_overview.get("daily_leaders", []),
    }

    live_payload = {
        "schema_version": "ai_arena_live_v1",
        "generated_at": generated_at,
        "year": year,
        "run_id": run_id,
        "run": _records(run)[0] if not run.empty else {},
        "agents": agents,
        "ranking": ranking_records,
        "open_positions": _records(positions),
        "recent_trades": _records(trades.head(50)),
        "diagnostics": diag,
        "portfolio": portfolio_snapshot,
        "trade_stats": trade_stats,
        "equity_overview": equity_overview,
    }
    ranking_payload = {
        "schema_version": "ai_arena_ranking_v2",
        "generated_at": generated_at,
        "year": year,
        "run_id": run_id,
        "agents": agents,
        "ranking": ranking_records,
        "equity_sparklines": spark,
        "diagnostics": diag,
        "trade_stats": trade_stats,
    }
    positions_payload = {
        "schema_version": "ai_arena_positions_v2",
        "generated_at": generated_at,
        "year": year,
        "run_id": run_id,
        "open_positions": _records(positions),
        "closed_trades": _records(trades.tail(200)),
        "diagnostics": diag,
        "portfolio": portfolio_snapshot,
    }
    summary_payload = {
        "schema_version": "ai_arena_annual_summary_v1",
        "generated_at": generated_at,
        "year": year,
        "run_id": run_id,
        "status": str(run.iloc[0]["status"]) if not run.empty else "unknown",
        "run": _records(run)[0] if not run.empty else {},
        "rankings": {
            "annual_performance": ranking_records,
            "monthly_equity_performance": monthly_records,
            "best_trades": _records(best),
            "worst_trades": _records(worst),
        },
        "visuals": visuals,
        "diagnostics": diag,
        "portfolio": portfolio_snapshot,
        "trade_stats": trade_stats,
        "equity_overview": equity_overview,
    }

    outputs = {
        "live": base / "live" / "latest.json",
        "ranking": base / "ranking" / "latest.json",
        "positions": base / "positions" / "latest.json",
        "summary": base / "summary" / "latest.json",
        "summary_year": base / "summary" / str(year) / "latest.json",
        "diagnostics": base / "diagnostics" / "latest.json",
        "diagnostics_md": base / "diagnostics" / "latest.md",
        # Legacy compatibility while existing AI Arena pages are migrated.
        "legacy_simulation": base / "simulation" / "latest.json",
    }
    write_json(outputs["live"], live_payload)
    write_json(outputs["ranking"], ranking_payload)
    write_json(outputs["positions"], positions_payload)
    write_json(outputs["summary"], summary_payload)
    write_json(outputs["summary_year"], summary_payload)
    write_json(outputs["diagnostics"], diag)
    write_text(outputs["diagnostics_md"], _diagnostics_markdown(diag))
    write_json(outputs["legacy_simulation"], live_payload)
    return outputs
