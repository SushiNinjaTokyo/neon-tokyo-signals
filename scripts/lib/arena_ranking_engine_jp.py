from __future__ import annotations

"""Ranking calculations for AI Arena seasons."""

from datetime import datetime
from typing import Any

import duckdb
import pandas as pd


def rebuild_rankings(conn: duckdb.DuckDBPyConnection, *, run_id: str, year: int, initial_capital_jpy: float) -> dict[str, Any]:
    """Rebuild yearly, monthly, best-trade, and worst-trade ranking tables."""
    now = datetime.utcnow()
    for table in ["arena_yearly_rankings", "arena_monthly_rankings", "arena_trade_rankings"]:
        conn.execute(f"DELETE FROM {table} WHERE run_id = ?", [run_id])

    equity = conn.execute(
        "SELECT * FROM arena_equity_curve WHERE run_id = ? ORDER BY agent_id, date",
        [run_id],
    ).df()
    if equity.empty:
        return {"yearly_rows": 0, "monthly_rows": 0, "trade_rows": 0}

    yearly_rows = []
    for agent_id, g in equity.groupby("agent_id"):
        g = g.sort_values("date")
        start_equity = float(initial_capital_jpy)
        end_equity = float(g.iloc[-1]["portfolio_equity_jpy"])
        total_return = (end_equity - start_equity) / start_equity * 100.0 if start_equity else 0.0
        peak = g["portfolio_equity_jpy"].cummax()
        dd = ((g["portfolio_equity_jpy"] / peak) - 1.0) * 100.0
        max_dd = float(dd.min()) if len(dd) else 0.0
        trades = conn.execute(
            "SELECT realized_return_pct FROM arena_trades WHERE run_id = ? AND agent_id = ?",
            [run_id, agent_id],
        ).df()
        trade_count = int(len(trades))
        win_rate = float((trades["realized_return_pct"] > 0).mean() * 100.0) if trade_count else 0.0
        yearly_rows.append({
            "run_id": run_id,
            "year": year,
            "agent_id": agent_id,
            "start_equity_jpy": start_equity,
            "end_equity_jpy": end_equity,
            "total_return_pct": total_return,
            "realized_pnl_jpy": float(g.iloc[-1].get("realized_pnl_jpy") or 0.0),
            "unrealized_pnl_jpy": float(g.iloc[-1].get("unrealized_pnl_jpy") or 0.0),
            "max_drawdown_pct": max_dd,
            "win_rate_pct": win_rate,
            "trade_count": trade_count,
            "rank": 0,
            "updated_at": now,
        })
    yearly_rows.sort(key=lambda r: r["total_return_pct"], reverse=True)
    for i, r in enumerate(yearly_rows, start=1):
        r["rank"] = i
    if yearly_rows:
        df = pd.DataFrame(yearly_rows)
        conn.register("_yearly_rankings", df)
        conn.execute("INSERT INTO arena_yearly_rankings SELECT * FROM _yearly_rankings")
        conn.unregister("_yearly_rankings")

    monthly_rows = []
    equity["ym"] = pd.to_datetime(equity["date"]).dt.strftime("%Y-%m")
    for ym, mg in equity.groupby("ym"):
        month = int(ym[-2:])
        rows = []
        for agent_id, g in mg.groupby("agent_id"):
            g = g.sort_values("date")
            start = float(g.iloc[0]["portfolio_equity_jpy"])
            end = float(g.iloc[-1]["portfolio_equity_jpy"])
            ret = (end - start) / start * 100.0 if start else 0.0
            rows.append({
                "run_id": run_id,
                "year": year,
                "month": month,
                "agent_id": agent_id,
                "month_start_equity_jpy": start,
                "month_end_equity_jpy": end,
                "monthly_return_pct": ret,
                "realized_pnl_jpy": float(g.iloc[-1].get("realized_pnl_jpy") or 0.0),
                "unrealized_pnl_jpy": float(g.iloc[-1].get("unrealized_pnl_jpy") or 0.0),
                "rank": 0,
                "updated_at": now,
            })
        rows.sort(key=lambda r: r["monthly_return_pct"], reverse=True)
        for i, r in enumerate(rows, start=1):
            r["rank"] = i
        monthly_rows.extend(rows)
    if monthly_rows:
        df = pd.DataFrame(monthly_rows)
        conn.register("_monthly_rankings", df)
        conn.execute("INSERT INTO arena_monthly_rankings SELECT * FROM _monthly_rankings")
        conn.unregister("_monthly_rankings")

    trades = conn.execute(
        "SELECT * FROM arena_trades WHERE run_id = ? AND realized_return_pct IS NOT NULL",
        [run_id],
    ).df()
    trade_rows = []
    if not trades.empty:
        for ranking_type, ascending in [("best_trade", False), ("worst_trade", True)]:
            t = trades.sort_values("realized_return_pct", ascending=ascending).head(20)
            for rank, (_, r) in enumerate(t.iterrows(), start=1):
                trade_rows.append({
                    "run_id": run_id,
                    "year": year,
                    "ranking_type": ranking_type,
                    "rank": rank,
                    "agent_id": r["agent_id"],
                    "ticker": r["ticker"],
                    "name": r.get("name") or r["ticker"],
                    "entry_date": r.get("entry_date"),
                    "exit_date": r.get("exit_date"),
                    "entry_price": float(r.get("entry_price") or 0.0),
                    "exit_price": float(r.get("exit_price") or 0.0),
                    "shares": int(r.get("shares") or 0),
                    "realized_pnl_jpy": float(r.get("realized_pnl_jpy") or 0.0),
                    "realized_return_pct": float(r.get("realized_return_pct") or 0.0),
                    "holding_days": int(r.get("holding_days") or 0),
                    "entry_reason_text": r.get("entry_reason_text") or "",
                    "exit_reason_text": r.get("exit_reason_text") or "",
                    "updated_at": now,
                })
    if trade_rows:
        df = pd.DataFrame(trade_rows)
        conn.register("_trade_rankings", df)
        conn.execute("INSERT INTO arena_trade_rankings SELECT * FROM _trade_rankings")
        conn.unregister("_trade_rankings")

    return {"yearly_rows": len(yearly_rows), "monthly_rows": len(monthly_rows), "trade_rows": len(trade_rows)}
