from __future__ import annotations

"""Export DuckDB AI Arena season data into lightweight public JSON."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from .arena_calendar_jp import downsample_points


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")
    tmp.replace(path)


def _records(df) -> list[dict[str, Any]]:
    if df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


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

    run = conn.execute("SELECT * FROM arena_simulation_runs WHERE run_id = ?", [run_id]).df()
    ranking = conn.execute("SELECT * FROM arena_yearly_rankings WHERE run_id = ? ORDER BY rank", [run_id]).df()
    monthly = conn.execute("SELECT * FROM arena_monthly_rankings WHERE run_id = ? ORDER BY month, rank", [run_id]).df()
    trades = conn.execute("SELECT * FROM arena_trades WHERE run_id = ? ORDER BY exit_date DESC, created_at DESC", [run_id]).df()
    positions = conn.execute("SELECT * FROM arena_open_positions WHERE run_id = ? ORDER BY agent_id, market_value_jpy DESC", [run_id]).df()
    equity = conn.execute("SELECT * FROM arena_equity_curve WHERE run_id = ? ORDER BY agent_id, date", [run_id]).df()
    best = conn.execute("SELECT * FROM arena_trade_rankings WHERE run_id = ? AND ranking_type = 'best_trade' ORDER BY rank", [run_id]).df()
    worst = conn.execute("SELECT * FROM arena_trade_rankings WHERE run_id = ? AND ranking_type = 'worst_trade' ORDER BY rank", [run_id]).df()

    agent_by_id = {a["agent_id"]: a for a in agents}
    spark = {}
    if not equity.empty:
        for agent_id, g in equity.groupby("agent_id"):
            pts = [
                {"date": str(r["date"]), "equity": round(float(r["portfolio_equity_jpy"]), 2), "return_pct": round(float(r["total_return_pct"]), 4)}
                for _, r in g.sort_values("date").iterrows()
            ]
            spark[agent_id] = downsample_points(pts, max_spark_points)

    ranking_records = _records(ranking)
    for r in ranking_records:
        r["agent"] = agent_by_id.get(r.get("agent_id"), {})
        r["sparkline"] = spark.get(r.get("agent_id"), [])

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
    }
    ranking_payload = {
        "schema_version": "ai_arena_ranking_v2",
        "generated_at": generated_at,
        "year": year,
        "run_id": run_id,
        "agents": agents,
        "ranking": ranking_records,
        "equity_sparklines": spark,
    }
    positions_payload = {
        "schema_version": "ai_arena_positions_v2",
        "generated_at": generated_at,
        "year": year,
        "run_id": run_id,
        "open_positions": _records(positions),
        "closed_trades": _records(trades.tail(200)),
    }
    summary_payload = {
        "schema_version": "ai_arena_annual_summary_v1",
        "generated_at": generated_at,
        "year": year,
        "run_id": run_id,
        "status": str(run.iloc[0]["status"]) if not run.empty else "unknown",
        "rankings": {
            "annual_performance": ranking_records,
            "monthly_equity_performance": _records(monthly),
            "best_trades": _records(best),
            "worst_trades": _records(worst),
        },
    }

    outputs = {
        "live": base / "live" / "latest.json",
        "ranking": base / "ranking" / "latest.json",
        "positions": base / "positions" / "latest.json",
        "summary": base / "summary" / "latest.json",
        "summary_year": base / "summary" / str(year) / "latest.json",
        # Legacy compatibility while existing AI Arena pages are migrated.
        "legacy_simulation": base / "simulation" / "latest.json",
    }
    write_json(outputs["live"], live_payload)
    write_json(outputs["ranking"], ranking_payload)
    write_json(outputs["positions"], positions_payload)
    write_json(outputs["summary"], summary_payload)
    write_json(outputs["summary_year"], summary_payload)
    write_json(outputs["legacy_simulation"], live_payload)
    return outputs
