#!/usr/bin/env python3
from __future__ import annotations

"""Build AI Arena JP trade diagnostics for human/LLM review.

This script reads the canonical AI Arena DuckDB state and writes compact but
information-rich diagnostics as JSON and Markdown.  The outputs are designed to
be pasted into ChatGPT for deeper analysis of each agent's winners, losers,
entry context, exit behavior, and rule-improvement candidates.

Inputs
------
- DuckDB tables, when available:
  - arena_display_runs
  - arena_trades
  - arena_open_positions
  - arena_orders
  - arena_equity_curve
  - arena_yearly_rankings
  - agent_scores_daily
  - features_daily
  - value_features_daily
  - fundamentals_latest_jp
  - prices_daily
  - universe_master
- data/agents/jp_agents.yml, if available, for display names.

Outputs
-------
- site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json
- site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.md

Design principles
-----------------
- Never mutates DuckDB.
- Does not depend on legacy Daily / Weekly outputs.
- Does not fail just because optional columns are missing; it records warnings.
- Uses dynamic table/column inspection so it survives small schema changes.
- Focuses on diagnostic usefulness rather than UI consumption.
"""

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import duckdb
import pandas as pd

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - PyYAML is in requirements-render.txt, but keep fallback.
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "cache" / "neon_tokyo_jp.duckdb"
DEFAULT_OUT_DIR = ROOT / "site" / "data" / "japan" / "ai-arena" / "diagnostics" / "trade-diagnostics"
DEFAULT_AGENTS_YML = ROOT / "data" / "agents" / "jp_agents.yml"

PREFERRED_FEATURE_COLUMNS = [
    "return_1d_pct",
    "return_5d_pct",
    "return_20d_pct",
    "return_60d_pct",
    "volume_ratio_20d",
    "avg_traded_value_20d_jpy",
    "rsi_14",
    "range_position_252d_0_1",
    "liquidity_score",
]

PREFERRED_VALUE_COLUMNS = [
    "value_score",
    "quality_score",
    "value_trap_penalty",
    "value_mispricing_score",
    "rerating_confirmation_score",
    "per",
    "pbr",
    "psr",
    "roe_pct",
    "roa_pct",
    "operating_margin_pct",
    "dividend_yield_pct",
    "market_cap_jpy",
]

PREFERRED_FUNDAMENTAL_COLUMNS = [
    "market_cap_jpy",
    "per",
    "pbr",
    "psr",
    "roe_pct",
    "roa_pct",
    "operating_margin_pct",
    "dividend_yield_pct",
]

PREFERRED_SCORE_COLUMNS = [
    "score",
    "rank",
    "action",
    "reason_code",
    "reason_text",
    "entry_reason_code",
    "entry_reason_text",
    "reject_reason_code",
    "reject_reason_text",
]

AGENT_ORDER = [
    "daily_striker",
    "weekly_sage",
    "risk_sentinel",
    "discovery_scout",
    "contrarian_monk",
    "reversal_snapback",
    "value_mispricing",
]

DISPLAY_AGENT_NAME = {
    "daily_striker": "KYOU",
    "weekly_sage": "NAGARE",
    "risk_sentinel": "MAMORU",
    "discovery_scout": "SAGURI",
    "contrarian_monk": "MATSU",
    "reversal_snapback": "KAESHI",
    "value_mispricing": "HIZUMI",
}


@dataclass
class TableInfo:
    exists: bool
    columns: list[str]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return default
        return int(value)
    except Exception:
        return default


def to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        return to_jsonable(value.item())
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if pd.isna(value):
        return None
    return str(value)


def round_or_none(value: Any, digits: int = 4) -> float | None:
    v = safe_float(value)
    return None if v is None else round(v, digits)


def pct(value: Any, digits: int = 2) -> str:
    v = safe_float(value)
    if v is None:
        return "N/A"
    return f"{v:.{digits}f}%"


def jpy(value: Any) -> str:
    v = safe_float(value)
    if v is None:
        return "N/A"
    return f"¥{v:,.0f}"


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def table_info(conn: duckdb.DuckDBPyConnection, table: str) -> TableInfo:
    try:
        rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
        cols = [str(r[1]) for r in rows]
        return TableInfo(bool(cols), cols)
    except Exception:
        return TableInfo(False, [])


def table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    return table_info(conn, table).exists


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def first_col(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    cset = set(columns)
    for c in candidates:
        if c in cset:
            return c
    return None


def load_agent_names(path: Path = DEFAULT_AGENTS_YML) -> dict[str, str]:
    names = dict(DISPLAY_AGENT_NAME)
    if not path.exists() or yaml is None:
        return names
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for agent in data.get("agents", []) or []:
            aid = str(agent.get("agent_id") or "").strip()
            nm = str(agent.get("name") or "").strip()
            if aid and nm:
                names[aid] = nm
    except Exception:
        pass
    return names


def load_run_id(conn: duckdb.DuckDBPyConnection, requested: str | None, warnings: list[dict[str, str]]) -> str:
    requested = (requested or "").strip()
    if requested and requested.lower() not in {"latest", "display", "auto"}:
        return requested

    if table_exists(conn, "arena_display_runs"):
        info = table_info(conn, "arena_display_runs")
        if "run_id" in info.columns:
            try:
                # Prefer latest updated row if timestamp columns exist; otherwise first row.
                order_col = first_col(info.columns, ["updated_at", "created_at", "generated_at"])
                order_sql = f" ORDER BY {qident(order_col)} DESC" if order_col else ""
                row = conn.execute(f"SELECT run_id FROM arena_display_runs{order_sql} LIMIT 1").fetchone()
                if row and row[0]:
                    return str(row[0])
            except Exception as exc:
                warnings.append({"severity": "warning", "code": "DISPLAY_RUN_LOOKUP_FAILED", "message": str(exc)})

    if table_exists(conn, "arena_simulation_runs"):
        info = table_info(conn, "arena_simulation_runs")
        if "run_id" in info.columns:
            order_col = first_col(info.columns, ["updated_at", "created_at", "generated_at", "started_at"])
            order_sql = f" ORDER BY {qident(order_col)} DESC" if order_col else ""
            row = conn.execute(f"SELECT run_id FROM arena_simulation_runs{order_sql} LIMIT 1").fetchone()
            if row and row[0]:
                return str(row[0])

    raise SystemExit("Unable to determine run_id. Pass --run-id explicitly or ensure arena_display_runs exists.")


def read_trades(conn: duckdb.DuckDBPyConnection, run_id: str) -> pd.DataFrame:
    info = table_info(conn, "arena_trades")
    if not info.exists:
        return pd.DataFrame()
    if "run_id" in info.columns:
        return conn.execute("SELECT * FROM arena_trades WHERE run_id = ?", [run_id]).fetchdf()
    return conn.execute("SELECT * FROM arena_trades").fetchdf()


def read_open_positions(conn: duckdb.DuckDBPyConnection, run_id: str) -> pd.DataFrame:
    info = table_info(conn, "arena_open_positions")
    if not info.exists:
        return pd.DataFrame()
    if "run_id" in info.columns:
        return conn.execute("SELECT * FROM arena_open_positions WHERE run_id = ?", [run_id]).fetchdf()
    return conn.execute("SELECT * FROM arena_open_positions").fetchdf()


def read_yearly_rankings(conn: duckdb.DuckDBPyConnection, run_id: str) -> pd.DataFrame:
    info = table_info(conn, "arena_yearly_rankings")
    if not info.exists:
        return pd.DataFrame()
    if "run_id" in info.columns:
        return conn.execute("SELECT * FROM arena_yearly_rankings WHERE run_id = ?", [run_id]).fetchdf()
    return conn.execute("SELECT * FROM arena_yearly_rankings").fetchdf()


def read_equity_curve(conn: duckdb.DuckDBPyConnection, run_id: str) -> pd.DataFrame:
    info = table_info(conn, "arena_equity_curve")
    if not info.exists:
        return pd.DataFrame()
    if "run_id" in info.columns:
        return conn.execute("SELECT * FROM arena_equity_curve WHERE run_id = ?", [run_id]).fetchdf()
    return conn.execute("SELECT * FROM arena_equity_curve").fetchdf()


def date_key(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (datetime, date)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    text = str(value)[:10]
    return text if len(text) == 10 else None


def build_table_lookup(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    columns_preferred: list[str],
    warnings: list[dict[str, str]],
) -> dict[tuple[str, str], dict[str, Any]]:
    info = table_info(conn, table)
    if not info.exists:
        warnings.append({"severity": "warning", "code": f"{table.upper()}_MISSING", "message": f"{table} is missing."})
        return {}

    ticker_col = first_col(info.columns, ["ticker", "symbol"])
    date_col = first_col(info.columns, ["date", "as_of_date", "score_date"])
    if not ticker_col or not date_col:
        warnings.append({"severity": "warning", "code": f"{table.upper()}_KEY_COLUMNS_MISSING", "message": f"{table} lacks ticker/date columns."})
        return {}

    wanted = [ticker_col, date_col] + [c for c in columns_preferred if c in info.columns]
    if len(wanted) <= 2:
        # Keep a small number of useful non-key numeric columns if preferred names are absent.
        for c in info.columns:
            if c not in wanted and len(wanted) < 16:
                wanted.append(c)

    sql = "SELECT " + ", ".join(qident(c) for c in wanted) + f" FROM {qident(table)}"
    df = conn.execute(sql).fetchdf()
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in df.to_dict("records"):
        ticker = str(row.get(ticker_col) or "").strip()
        d = date_key(row.get(date_col))
        if not ticker or not d:
            continue
        payload = {k: to_jsonable(v) for k, v in row.items() if k not in {ticker_col, date_col} and not pd.isna(v)}
        out[(ticker, d)] = payload
    return out


def build_score_lookup(conn: duckdb.DuckDBPyConnection, warnings: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    table = "agent_scores_daily"
    info = table_info(conn, table)
    if not info.exists:
        warnings.append({"severity": "warning", "code": "AGENT_SCORES_DAILY_MISSING", "message": "agent_scores_daily is missing."})
        return {}

    ticker_col = first_col(info.columns, ["ticker", "symbol"])
    date_col = first_col(info.columns, ["date", "as_of_date", "score_date"])
    agent_col = first_col(info.columns, ["agent_id", "agent", "strategy_id"])
    if not ticker_col or not date_col or not agent_col:
        warnings.append({"severity": "warning", "code": "AGENT_SCORE_KEY_COLUMNS_MISSING", "message": "agent_scores_daily lacks ticker/date/agent columns."})
        return {}

    wanted = [agent_col, ticker_col, date_col] + [c for c in PREFERRED_SCORE_COLUMNS if c in info.columns]
    # Include JSON-ish component/reason columns if present.
    for c in info.columns:
        lc = c.lower()
        if c not in wanted and ("component" in lc or "reason" in lc or "diagnostic" in lc):
            wanted.append(c)
    sql = "SELECT " + ", ".join(qident(c) for c in wanted) + f" FROM {qident(table)}"
    df = conn.execute(sql).fetchdf()
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in df.to_dict("records"):
        agent = str(row.get(agent_col) or "").strip()
        ticker = str(row.get(ticker_col) or "").strip()
        d = date_key(row.get(date_col))
        if not agent or not ticker or not d:
            continue
        payload = {k: to_jsonable(v) for k, v in row.items() if k not in {agent_col, ticker_col, date_col} and not pd.isna(v)}
        out[(agent, ticker, d)] = payload
    return out


def build_fundamental_lookup(conn: duckdb.DuckDBPyConnection, warnings: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    table = "fundamentals_latest_jp"
    info = table_info(conn, table)
    if not info.exists:
        warnings.append({"severity": "warning", "code": "FUNDAMENTALS_LATEST_JP_MISSING", "message": "fundamentals_latest_jp is missing."})
        return {}
    ticker_col = first_col(info.columns, ["ticker", "symbol"])
    if not ticker_col:
        warnings.append({"severity": "warning", "code": "FUNDAMENTALS_TICKER_MISSING", "message": "fundamentals_latest_jp lacks ticker column."})
        return {}
    wanted = [ticker_col] + [c for c in PREFERRED_FUNDAMENTAL_COLUMNS if c in info.columns]
    name_col = first_col(info.columns, ["name", "company_name", "short_name"])
    if name_col and name_col not in wanted:
        wanted.append(name_col)
    sql = "SELECT " + ", ".join(qident(c) for c in wanted) + f" FROM {qident(table)}"
    df = conn.execute(sql).fetchdf()
    out: dict[str, dict[str, Any]] = {}
    for row in df.to_dict("records"):
        ticker = str(row.get(ticker_col) or "").strip()
        if not ticker:
            continue
        out[ticker] = {k: to_jsonable(v) for k, v in row.items() if k != ticker_col and not pd.isna(v)}
    return out


def fetch_price_path(
    conn: duckdb.DuckDBPyConnection,
    ticker: str,
    start_date: str | None,
    end_date: str | None,
    warnings: list[dict[str, str]],
) -> pd.DataFrame:
    info = table_info(conn, "prices_daily")
    if not info.exists or not ticker or not start_date or not end_date:
        return pd.DataFrame()
    date_col = first_col(info.columns, ["date"])
    ticker_col = first_col(info.columns, ["ticker", "symbol"])
    if not date_col or not ticker_col:
        return pd.DataFrame()
    cols = [ticker_col, date_col]
    for c in ["open", "high", "low", "close", "adj_close", "volume"]:
        if c in info.columns:
            cols.append(c)
    try:
        sql = (
            "SELECT " + ", ".join(qident(c) for c in cols) +
            f" FROM {qident('prices_daily')} WHERE {qident(ticker_col)} = ? AND {qident(date_col)} BETWEEN ? AND ? ORDER BY {qident(date_col)}"
        )
        return conn.execute(sql, [ticker, start_date, end_date]).fetchdf()
    except Exception as exc:
        warnings.append({"severity": "warning", "code": "PRICE_PATH_QUERY_FAILED", "message": f"{ticker}: {exc}"})
        return pd.DataFrame()


def infer_exit_reason(row: dict[str, Any]) -> str:
    for key in ["exit_reason_code", "exit_reason", "reason_code", "status"]:
        val = row.get(key)
        if val is not None and not pd.isna(val) and str(val).strip():
            return str(val)
    return "UNKNOWN"


def get_return_pct(row: dict[str, Any]) -> float | None:
    for key in ["return_pct", "realized_return_pct", "pnl_pct", "trade_return_pct"]:
        v = safe_float(row.get(key))
        if v is not None:
            return v
    ep = safe_float(row.get("entry_price"))
    xp = safe_float(row.get("exit_price"))
    if ep and xp:
        return (xp / ep - 1.0) * 100.0
    return None


def get_pnl_jpy(row: dict[str, Any]) -> float | None:
    for key in ["pnl_jpy", "realized_pnl_jpy", "profit_jpy"]:
        v = safe_float(row.get(key))
        if v is not None:
            return v
    ep = safe_float(row.get("entry_price"))
    xp = safe_float(row.get("exit_price"))
    shares = safe_float(row.get("shares"))
    if ep is not None and xp is not None and shares is not None:
        return (xp - ep) * shares
    return None


def classify_pattern(return_pct: float | None, mfe: float | None, mae: float | None, holding_days: int | None, exit_reason: str) -> tuple[str, str]:
    """Return (success_pattern, failure_pattern). One side will usually be blank."""
    r = return_pct
    mfe_v = mfe
    mae_v = mae
    hd = holding_days if holding_days is not None else 0
    er = exit_reason.upper()

    if r is None:
        return "", "UNKNOWN_RETURN"

    if r >= 0:
        if mfe_v is not None and mfe_v >= max(8.0, r * 2.5) and r < 3.0:
            return "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN", ""
        if hd <= 10 and r >= 6.0:
            return "FAST_WINNER", ""
        if hd >= 35 and r >= 8.0:
            return "PATIENT_TREND_WINNER", ""
        if "TIME" in er and r > 0:
            return "TIME_EXIT_GREEN", ""
        return "NORMAL_WIN", ""

    # Losing trade patterns.
    if mae_v is not None and mae_v <= -12.0:
        return "", "DEEP_ADVERSE_MOVE"
    if mfe_v is not None and mfe_v >= 5.0 and r < 0:
        return "", "WINNER_TURNED_LOSER"
    if "STOP" in er:
        return "", "STOP_LOSS_HIT"
    if hd <= 7 and r <= -4.0:
        return "", "FAST_FAILED_ENTRY"
    if hd >= 30 and r < 0:
        return "", "SLOW_BLEED_LOSER"
    return "", "NORMAL_LOSS"


def enrich_trade(
    conn: duckdb.DuckDBPyConnection,
    raw: dict[str, Any],
    feature_lookup: dict[tuple[str, str], dict[str, Any]],
    value_lookup: dict[tuple[str, str], dict[str, Any]],
    score_lookup: dict[tuple[str, str, str], dict[str, Any]],
    fundamental_lookup: dict[str, dict[str, Any]],
    agent_names: dict[str, str],
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    ticker = str(raw.get("ticker") or raw.get("symbol") or "").strip()
    agent_id = str(raw.get("agent_id") or raw.get("agent") or "").strip()
    entry_date = date_key(raw.get("entry_date"))
    entry_signal_date = date_key(raw.get("entry_signal_date")) or entry_date
    exit_date = date_key(raw.get("exit_date")) or date_key(raw.get("last_date"))
    return_pct = get_return_pct(raw)
    pnl_jpy = get_pnl_jpy(raw)
    holding_days = safe_int(raw.get("holding_days"), 0)
    exit_reason = infer_exit_reason(raw)

    # Entry context is keyed to the signal date if available. This aligns with
    # next-open execution: score/features on signal date, fill on next open.
    context_date = entry_signal_date or entry_date
    entry_features = feature_lookup.get((ticker, context_date), {}) if context_date else {}
    entry_value = value_lookup.get((ticker, context_date), {}) if context_date else {}
    entry_score = score_lookup.get((agent_id, ticker, context_date), {}) if context_date else {}
    fundamentals = fundamental_lookup.get(ticker, {})

    ep = safe_float(raw.get("entry_price"))
    xp = safe_float(raw.get("exit_price"))
    mfe = None
    mae = None
    close_retention = None
    price_obs = 0
    if ep and entry_date and exit_date:
        path = fetch_price_path(conn, ticker, entry_date, exit_date, warnings)
        price_obs = len(path)
        if not path.empty:
            high_col = "high" if "high" in path.columns else ("close" if "close" in path.columns else None)
            low_col = "low" if "low" in path.columns else ("close" if "close" in path.columns else None)
            if high_col:
                mfe = ((float(path[high_col].max()) / ep) - 1.0) * 100.0
            if low_col:
                mae = ((float(path[low_col].min()) / ep) - 1.0) * 100.0
            if mfe is not None and mfe > 0 and return_pct is not None:
                close_retention = max(-999.0, min(999.0, return_pct / mfe * 100.0))

    success_pattern, failure_pattern = classify_pattern(return_pct, mfe, mae, holding_days, exit_reason)

    return {
        "trade_id": to_jsonable(raw.get("trade_id") or raw.get("position_id") or raw.get("order_id")),
        "run_id": to_jsonable(raw.get("run_id")),
        "agent_id": agent_id,
        "agent_name": agent_names.get(agent_id, DISPLAY_AGENT_NAME.get(agent_id, agent_id or "UNKNOWN")),
        "ticker": ticker,
        "name": to_jsonable(raw.get("name") or fundamentals.get("name") or fundamentals.get("company_name")),
        "entry_signal_date": entry_signal_date,
        "entry_date": entry_date,
        "exit_date": exit_date,
        "holding_days": holding_days,
        "entry_price": round_or_none(raw.get("entry_price"), 4),
        "exit_price": round_or_none(raw.get("exit_price"), 4),
        "shares": safe_int(raw.get("shares"), 0),
        "return_pct": round_or_none(return_pct, 4),
        "pnl_jpy": round_or_none(pnl_jpy, 2),
        "exit_reason": exit_reason,
        "mfe_pct": round_or_none(mfe, 4),
        "mae_pct": round_or_none(mae, 4),
        "close_vs_mfe_retention_pct": round_or_none(close_retention, 4),
        "price_observations_during_trade": price_obs,
        "win_loss": "WIN" if (return_pct is not None and return_pct >= 0) else "LOSS",
        "success_pattern": success_pattern,
        "failure_pattern": failure_pattern,
        "entry_score_context": entry_score,
        "entry_feature_context": entry_features,
        "entry_value_context": entry_value,
        "fundamental_context": fundamentals,
    }


def summarize_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(trades)
    wins = [t for t in trades if safe_float(t.get("return_pct")) is not None and safe_float(t.get("return_pct"), 0) >= 0]
    losses = [t for t in trades if safe_float(t.get("return_pct")) is not None and safe_float(t.get("return_pct"), 0) < 0]
    returns = [safe_float(t.get("return_pct")) for t in trades if safe_float(t.get("return_pct")) is not None]
    pnls = [safe_float(t.get("pnl_jpy")) for t in trades if safe_float(t.get("pnl_jpy")) is not None]
    win_pnls = [safe_float(t.get("pnl_jpy"), 0) for t in wins if safe_float(t.get("pnl_jpy")) is not None]
    loss_pnls = [safe_float(t.get("pnl_jpy"), 0) for t in losses if safe_float(t.get("pnl_jpy")) is not None]
    avg_win = sum(safe_float(t.get("return_pct"), 0) or 0 for t in wins) / len(wins) if wins else 0.0
    avg_loss = sum(safe_float(t.get("return_pct"), 0) or 0 for t in losses) / len(losses) if losses else 0.0
    gross_profit = sum(v for v in win_pnls if v is not None and v > 0)
    gross_loss = abs(sum(v for v in loss_pnls if v is not None and v < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None
    avg_mfe = [safe_float(t.get("mfe_pct")) for t in trades if safe_float(t.get("mfe_pct")) is not None]
    avg_mae = [safe_float(t.get("mae_pct")) for t in trades if safe_float(t.get("mae_pct")) is not None]
    exit_reasons = Counter(str(t.get("exit_reason") or "UNKNOWN") for t in trades)
    failure_patterns = Counter(str(t.get("failure_pattern") or "") for t in trades if t.get("failure_pattern"))
    success_patterns = Counter(str(t.get("success_pattern") or "") for t in trades if t.get("success_pattern"))
    symbols_profit: dict[str, float] = defaultdict(float)
    symbols_count: Counter[str] = Counter()
    for t in trades:
        ticker = str(t.get("ticker") or "")
        if not ticker:
            continue
        symbols_count[ticker] += 1
        symbols_profit[ticker] += safe_float(t.get("pnl_jpy"), 0) or 0

    return {
        "trade_count": n,
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate_pct": round((len(wins) / n * 100.0), 4) if n else 0.0,
        "avg_return_pct": round(sum(returns) / len(returns), 4) if returns else None,
        "median_return_pct": round(float(pd.Series(returns).median()), 4) if returns else None,
        "avg_win_pct": round(avg_win, 4) if wins else None,
        "avg_loss_pct": round(avg_loss, 4) if losses else None,
        "payoff_ratio": round(abs(avg_win / avg_loss), 4) if avg_loss else None,
        "total_pnl_jpy": round(sum(pnls), 2) if pnls else None,
        "gross_profit_jpy": round(gross_profit, 2),
        "gross_loss_jpy": round(gross_loss, 2),
        "profit_factor": round(profit_factor, 4) if profit_factor is not None else None,
        "avg_mfe_pct": round(sum(avg_mfe) / len(avg_mfe), 4) if avg_mfe else None,
        "avg_mae_pct": round(sum(avg_mae) / len(avg_mae), 4) if avg_mae else None,
        "exit_reasons": dict(exit_reasons.most_common(12)),
        "failure_patterns": dict(failure_patterns.most_common(12)),
        "success_patterns": dict(success_patterns.most_common(12)),
        "top_profit_symbols": [
            {"ticker": k, "pnl_jpy": round(v, 2), "trades": symbols_count[k]}
            for k, v in sorted(symbols_profit.items(), key=lambda x: x[1], reverse=True)[:10]
        ],
        "worst_profit_symbols": [
            {"ticker": k, "pnl_jpy": round(v, 2), "trades": symbols_count[k]}
            for k, v in sorted(symbols_profit.items(), key=lambda x: x[1])[:10]
        ],
    }


def rank_sort_key(agent_id: str) -> tuple[int, str]:
    try:
        return (AGENT_ORDER.index(agent_id), agent_id)
    except ValueError:
        return (999, agent_id)


def build_payload(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    max_trade_rows: int,
    top_n: int,
    include_trade_context: bool,
) -> dict[str, Any]:
    warnings: list[dict[str, str]] = []
    agent_names = load_agent_names()
    trades_df = read_trades(conn, run_id)
    open_df = read_open_positions(conn, run_id)
    ranking_df = read_yearly_rankings(conn, run_id)
    equity_df = read_equity_curve(conn, run_id)

    if trades_df.empty:
        warnings.append({"severity": "critical", "code": "NO_TRADES_FOR_RUN", "message": f"arena_trades has no rows for run_id={run_id}."})

    feature_lookup = build_table_lookup(conn, "features_daily", PREFERRED_FEATURE_COLUMNS, warnings)
    value_lookup = build_table_lookup(conn, "value_features_daily", PREFERRED_VALUE_COLUMNS, warnings)
    score_lookup = build_score_lookup(conn, warnings)
    fundamental_lookup = build_fundamental_lookup(conn, warnings)

    trades_raw = trades_df.to_dict("records")
    enriched: list[dict[str, Any]] = []
    for raw in trades_raw:
        enriched.append(enrich_trade(conn, raw, feature_lookup, value_lookup, score_lookup, fundamental_lookup, agent_names, warnings))

    by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in enriched:
        by_agent[str(t.get("agent_id") or "UNKNOWN")].append(t)

    agent_summaries: dict[str, Any] = {}
    for agent_id in sorted(by_agent.keys(), key=rank_sort_key):
        arr = by_agent[agent_id]
        arr_sorted = sorted(arr, key=lambda x: safe_float(x.get("return_pct"), 0) or 0)
        summary = summarize_trades(arr)
        summary.update({
            "agent_id": agent_id,
            "agent_name": agent_names.get(agent_id, DISPLAY_AGENT_NAME.get(agent_id, agent_id)),
            "worst_trades": arr_sorted[:top_n],
            "best_trades": list(reversed(arr_sorted[-top_n:])),
            "largest_mfe_givebacks": sorted(
                [t for t in arr if safe_float(t.get("mfe_pct")) is not None and safe_float(t.get("return_pct")) is not None],
                key=lambda t: (safe_float(t.get("mfe_pct"), 0) or 0) - (safe_float(t.get("return_pct"), 0) or 0),
                reverse=True,
            )[:top_n],
            "deepest_adverse_trades": sorted(
                [t for t in arr if safe_float(t.get("mae_pct")) is not None],
                key=lambda t: safe_float(t.get("mae_pct"), 0) or 0,
            )[:top_n],
        })
        agent_summaries[agent_id] = summary

    # Ranking snapshot if columns are available.
    ranking_snapshot: list[dict[str, Any]] = []
    if not ranking_df.empty:
        for row in ranking_df.to_dict("records"):
            aid = str(row.get("agent_id") or row.get("agent") or "").strip()
            item = {k: to_jsonable(v) for k, v in row.items() if not pd.isna(v)}
            if aid:
                item["agent_name"] = agent_names.get(aid, DISPLAY_AGENT_NAME.get(aid, aid))
            ranking_snapshot.append(item)

    open_positions: list[dict[str, Any]] = []
    if not open_df.empty:
        for row in open_df.to_dict("records"):
            d = {k: to_jsonable(v) for k, v in row.items() if not pd.isna(v)}
            aid = str(d.get("agent_id") or "")
            if aid:
                d["agent_name"] = agent_names.get(aid, DISPLAY_AGENT_NAME.get(aid, aid))
            open_positions.append(d)

    all_sorted = sorted(enriched, key=lambda x: abs(safe_float(x.get("pnl_jpy"), 0) or 0), reverse=True)
    if max_trade_rows > 0:
        exported_trades = all_sorted[:max_trade_rows]
    else:
        exported_trades = all_sorted

    if not include_trade_context:
        for t in exported_trades:
            t.pop("entry_feature_context", None)
            t.pop("entry_value_context", None)
            t.pop("fundamental_context", None)
            t.pop("entry_score_context", None)

    payload = {
        "schema_version": "neon_tokyo_ai_arena_trade_diagnostics_v1",
        "generated_at": utc_now_iso(),
        "run_id": run_id,
        "purpose": "Paste this JSON or the companion Markdown into ChatGPT to analyze each AI Arena agent's success/failure drivers.",
        "diagnostic_notes": [
            "MFE/MAE are estimated from prices_daily high/low when available, otherwise close.",
            "Entry context uses entry_signal_date when available; otherwise entry_date.",
            "The script is schema-tolerant and records missing optional tables/columns as warnings.",
        ],
        "warnings": warnings,
        "counts": {
            "closed_trades": len(enriched),
            "open_positions": len(open_positions),
            "agents_with_closed_trades": len(agent_summaries),
            "exported_trade_rows": len(exported_trades),
            "equity_curve_rows": len(equity_df),
        },
        "ranking_snapshot": ranking_snapshot,
        "agent_summaries": agent_summaries,
        "open_positions": open_positions,
        "trade_rows": exported_trades,
    }
    return to_jsonable(payload)


def md_trade_table(trades: list[dict[str, Any]], max_rows: int = 12) -> str:
    if not trades:
        return "_None_\n"
    lines = ["| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for t in trades[:max_rows]:
        pattern = t.get("failure_pattern") or t.get("success_pattern") or ""
        lines.append(
            "| "
            + " | ".join([
                md_escape(t.get("ticker")),
                md_escape(t.get("name")),
                md_escape(t.get("entry_date")),
                md_escape(t.get("exit_date")),
                pct(t.get("return_pct")),
                jpy(t.get("pnl_jpy")),
                str(safe_int(t.get("holding_days"), 0)),
                pct(t.get("mfe_pct")),
                pct(t.get("mae_pct")),
                md_escape(t.get("exit_reason")),
                md_escape(pattern),
            ])
            + " |"
        )
    return "\n".join(lines) + "\n"


def md_context_bullets(trades: list[dict[str, Any]], max_rows: int = 8) -> str:
    bullets: list[str] = []
    for t in trades[:max_rows]:
        score = t.get("entry_score_context") or {}
        feat = t.get("entry_feature_context") or {}
        val = t.get("entry_value_context") or {}
        fund = t.get("fundamental_context") or {}
        bits = []
        for label, source, keys in [
            ("score", score, ["score", "rank", "action"]),
            ("feature", feat, ["return_5d_pct", "return_20d_pct", "volume_ratio_20d", "rsi_14", "range_position_252d_0_1"]),
            ("value", val, ["value_score", "quality_score", "value_trap_penalty", "per", "pbr", "roe_pct"]),
            ("fund", fund, ["market_cap_jpy", "per", "pbr", "roe_pct", "operating_margin_pct"]),
        ]:
            kv = []
            for k in keys:
                if isinstance(source, dict) and source.get(k) is not None:
                    kv.append(f"{k}={source.get(k)}")
            if kv:
                bits.append(f"{label}: " + ", ".join(kv))
        if bits:
            bullets.append(f"- `{t.get('ticker')}` {t.get('entry_date')} → {t.get('exit_date')} {pct(t.get('return_pct'))}: " + " / ".join(bits))
    return "\n".join(bullets) + ("\n" if bullets else "_No compact context available._\n")


def render_markdown(payload: dict[str, Any], top_n: int) -> str:
    lines: list[str] = []
    lines.append("# Neon Tokyo AI Arena Trade Diagnostics")
    lines.append("")
    lines.append(f"Generated: `{payload.get('generated_at')}`")
    lines.append(f"Run ID: `{payload.get('run_id')}`")
    lines.append("")
    lines.append("> Purpose: paste this Markdown into ChatGPT and ask for detailed agent-by-agent win/loss diagnosis and rule-improvement ideas.")
    lines.append("")

    counts = payload.get("counts", {}) or {}
    lines.append("## Dataset Summary")
    lines.append("")
    lines.append(f"- Closed trades: **{counts.get('closed_trades')}**")
    lines.append(f"- Open positions: **{counts.get('open_positions')}**")
    lines.append(f"- Agents with closed trades: **{counts.get('agents_with_closed_trades')}**")
    lines.append(f"- Exported compact trade rows in JSON: **{counts.get('exported_trade_rows')}**")
    lines.append(f"- Equity curve rows: **{counts.get('equity_curve_rows')}**")
    lines.append("")

    warnings = payload.get("warnings", []) or []
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        lines.append("| Severity | Code | Message |")
        lines.append("|---|---|---|")
        for w in warnings[:30]:
            lines.append(f"| {md_escape(w.get('severity'))} | `{md_escape(w.get('code'))}` | {md_escape(w.get('message'))} |")
        lines.append("")

    summaries = payload.get("agent_summaries", {}) or {}
    lines.append("## Agent Summary")
    lines.append("")
    lines.append("| Agent | Trades | Win | Avg Ret | Avg Win | Avg Loss | Payoff | PF | PnL | Avg MFE | Avg MAE | Top Failure Patterns |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for aid in sorted(summaries.keys(), key=rank_sort_key):
        s = summaries[aid]
        fp = ", ".join([f"{k}:{v}" for k, v in (s.get("failure_patterns") or {}).items()][:4])
        lines.append(
            f"| {md_escape(s.get('agent_name'))} / `{md_escape(aid)}` | "
            f"{s.get('trade_count')} | {pct(s.get('win_rate_pct'))} | {pct(s.get('avg_return_pct'))} | "
            f"{pct(s.get('avg_win_pct'))} | {pct(s.get('avg_loss_pct'))} | "
            f"{s.get('payoff_ratio')} | {s.get('profit_factor')} | {jpy(s.get('total_pnl_jpy'))} | "
            f"{pct(s.get('avg_mfe_pct'))} | {pct(s.get('avg_mae_pct'))} | {md_escape(fp)} |"
        )
    lines.append("")

    for aid in sorted(summaries.keys(), key=rank_sort_key):
        s = summaries[aid]
        lines.append(f"## {s.get('agent_name')} / `{aid}`")
        lines.append("")
        lines.append("### Key Metrics")
        lines.append("")
        lines.append(f"- Trades: **{s.get('trade_count')}**, Win rate: **{pct(s.get('win_rate_pct'))}**, Total PnL: **{jpy(s.get('total_pnl_jpy'))}**")
        lines.append(f"- Avg return: **{pct(s.get('avg_return_pct'))}**, Avg win: **{pct(s.get('avg_win_pct'))}**, Avg loss: **{pct(s.get('avg_loss_pct'))}**")
        lines.append(f"- Payoff ratio: **{s.get('payoff_ratio')}**, Profit factor: **{s.get('profit_factor')}**")
        lines.append(f"- Avg MFE: **{pct(s.get('avg_mfe_pct'))}**, Avg MAE: **{pct(s.get('avg_mae_pct'))}**")
        lines.append("")
        lines.append("### Exit Reasons")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.get("exit_reasons") or {}, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### Failure Patterns")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.get("failure_patterns") or {}, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### Success Patterns")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.get("success_patterns") or {}, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### Worst Trades")
        lines.append("")
        lines.append(md_trade_table(s.get("worst_trades") or [], max_rows=top_n))
        lines.append("")
        lines.append("### Best Trades")
        lines.append("")
        lines.append(md_trade_table(s.get("best_trades") or [], max_rows=top_n))
        lines.append("")
        lines.append("### Largest MFE Givebacks")
        lines.append("")
        lines.append(md_trade_table(s.get("largest_mfe_givebacks") or [], max_rows=min(top_n, 10)))
        lines.append("")
        lines.append("### Deepest Adverse Trades")
        lines.append("")
        lines.append(md_trade_table(s.get("deepest_adverse_trades") or [], max_rows=min(top_n, 10)))
        lines.append("")
        lines.append("### Compact Entry Context For Worst Trades")
        lines.append("")
        lines.append(md_context_bullets(s.get("worst_trades") or [], max_rows=min(8, top_n)))
        lines.append("")

    lines.append("## Prompt Suggestion")
    lines.append("")
    lines.append("```text")
    lines.append("このTrade Diagnosticsをもとに、各Agentの勝因・敗因を定量的に分析してください。特に、勝率と損益の非対称性、MFE/MAE、exit reason、entry context、fundamental/value contextを見て、Agent別に改善すべき売買ルールを優先順位付きで提案してください。")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], out_dir: Path, top_n: int) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "latest.json"
    md_path = out_dir / "latest.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload, top_n=top_n), encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build AI Arena JP agent win/loss trade diagnostics JSON and Markdown.")
    parser.add_argument("--db-path", default=os.getenv("PRICE_DUCKDB_PATH", str(DEFAULT_DB_PATH)))
    parser.add_argument("--run-id", default=os.getenv("AI_ARENA_DIAGNOSTICS_RUN_ID", "display"))
    parser.add_argument("--out-dir", default=os.getenv("TRADE_DIAGNOSTICS_OUT_DIR", str(DEFAULT_OUT_DIR)))
    parser.add_argument("--max-trade-rows", type=int, default=int(os.getenv("TRADE_DIAGNOSTICS_MAX_TRADE_ROWS", "1500")))
    parser.add_argument("--top-n", type=int, default=int(os.getenv("TRADE_DIAGNOSTICS_TOP_N", "15")))
    parser.add_argument("--no-trade-context", action="store_true", default=os.getenv("TRADE_DIAGNOSTICS_INCLUDE_CONTEXT", "true").lower() == "false")
    parser.add_argument("--fail-if-no-trades", action="store_true", default=os.getenv("TRADE_DIAGNOSTICS_FAIL_IF_NO_TRADES", "true").lower() == "true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    if not db_path.exists():
        raise SystemExit(f"DuckDB not found: {db_path}")

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    conn = duckdb.connect(str(db_path), read_only=True)
    run_id = load_run_id(conn, args.run_id, warnings=[])
    payload = build_payload(
        conn,
        run_id=run_id,
        max_trade_rows=max(0, int(args.max_trade_rows)),
        top_n=max(1, int(args.top_n)),
        include_trade_context=not bool(args.no_trade_context),
    )
    json_path, md_path = write_outputs(payload, out_dir, top_n=max(1, int(args.top_n)))

    closed = int((payload.get("counts") or {}).get("closed_trades") or 0)
    warnings = payload.get("warnings") or []
    criticals = [w for w in warnings if str(w.get("severity", "")).lower() == "critical"]
    print(f"run_id={run_id}")
    print(f"closed_trades={closed}")
    print(f"warnings={len(warnings)} criticals={len(criticals)}")
    print(f"wrote_json={json_path.relative_to(ROOT)}")
    print(f"wrote_md={md_path.relative_to(ROOT)}")

    if args.fail_if_no_trades and closed <= 0:
        raise SystemExit("No closed trades were available for diagnostics.")
    if criticals:
        for w in criticals[:20]:
            print(f"critical: {w.get('code')} {w.get('message')}")
        if args.fail_if_no_trades:
            raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
