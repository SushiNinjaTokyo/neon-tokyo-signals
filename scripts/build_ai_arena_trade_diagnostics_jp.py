#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export Neon Tokyo AI Arena trade diagnostics.

Outputs:
- site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json
- site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.md

Key design:
- Always exports all 7 agents, even if an agent has 0 closed trades.
- Uses arena_trades as the primary source.
- Optionally enriches worst-trade context from:
  - agent_scores_daily
  - features_daily
  - value_features_daily
  - value_features_sector_relative_jp
  - fundamentals_latest_jp
  - company_master_jp
- Safe against missing optional tables/columns.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


SCHEMA_VERSION = "neon_tokyo_ai_arena_trade_diagnostics_v1"

DEFAULT_DB_PATH = "data/cache/neon_tokyo_jp.duckdb"
DEFAULT_OUT_DIR = "site/data/japan/ai-arena/diagnostics/trade-diagnostics"

EXPECTED_AGENTS: list[tuple[str, str]] = [
    ("KYOU", "daily_striker"),
    ("NAGARE", "weekly_sage"),
    ("MAMORU", "risk_sentinel"),
    ("SAGURI", "discovery_scout"),
    ("MATSU", "contrarian_monk"),
    ("KAESHI", "reversal_snapback"),
    ("HIZUMI", "value_mispricing"),
]

AGENT_ORDER = {agent: i for i, (agent, _) in enumerate(EXPECTED_AGENTS)}

AGENT_KEY_ALIASES: dict[str, str] = {
    "daily_striker": "KYOU",
    "weekly_sage": "NAGARE",
    "risk_sentinel": "MAMORU",
    "discovery_scout": "SAGURI",
    "contrarian_monk": "MATSU",
    "reversal_snapback": "KAESHI",
    "value_mispricing": "HIZUMI",
}

AGENT_NAME_ALIASES: dict[str, str] = {
    "KYOU": "daily_striker",
    "NAGARE": "weekly_sage",
    "MAMORU": "risk_sentinel",
    "SAGURI": "discovery_scout",
    "MATSU": "contrarian_monk",
    "KAESHI": "reversal_snapback",
    "HIZUMI": "value_mispricing",
}


@dataclass
class TradeRow:
    agent: str
    agent_key: str
    symbol: str
    name: str
    entry_date: str
    exit_date: str
    entry_price: float | None
    exit_price: float | None
    shares: float | None
    pnl_jpy: float
    return_pct: float
    holding_days: int
    mfe_pct: float
    mae_pct: float
    exit_reason: str
    pattern: str


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


def pct(value: Any) -> float:
    return round(safe_float(value), 4)


def money(value: Any) -> float:
    return round(safe_float(value), 2)


def table_exists(con: duckdb.DuckDBPyConnection, table: str) -> bool:
    try:
        return (
            con.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table],
            ).fetchone()[0]
            > 0
        )
    except Exception:
        return False


def column_exists(con: duckdb.DuckDBPyConnection, table: str, column: str) -> bool:
    try:
        rows = con.execute(f"PRAGMA table_info('{table}')").fetchall()
        return any(str(r[1]) == column for r in rows)
    except Exception:
        return False


def first_existing_column(
    con: duckdb.DuckDBPyConnection,
    table: str,
    candidates: list[str],
) -> str | None:
    for col in candidates:
        if column_exists(con, table, col):
            return col
    return None


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def normalize_agent(agent_raw: Any, agent_key_raw: Any) -> tuple[str, str]:
    a = str(agent_raw or "").strip()
    k = str(agent_key_raw or "").strip()

    if a in AGENT_NAME_ALIASES:
        return a, AGENT_NAME_ALIASES[a]

    if k in AGENT_KEY_ALIASES:
        return AGENT_KEY_ALIASES[k], k

    upper = a.upper()
    if upper in AGENT_NAME_ALIASES:
        return upper, AGENT_NAME_ALIASES[upper]

    lower = k.lower()
    if lower in AGENT_KEY_ALIASES:
        return AGENT_KEY_ALIASES[lower], lower

    # fallback
    if a:
        return a, k or a.lower()
    if k:
        return AGENT_KEY_ALIASES.get(k, k.upper()), k

    return "UNKNOWN", "unknown"


def empty_agent_summary(agent: str, agent_key: str) -> dict[str, Any]:
    return {
        "agent": agent,
        "agent_key": agent_key,
        "label": f"{agent} / {agent_key}",
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0,
        "avg_return_pct": 0.0,
        "avg_win_pct": 0.0,
        "avg_loss_pct": 0.0,
        "payoff_ratio": 0.0,
        "profit_factor": 0.0,
        "total_pnl_jpy": 0.0,
        "avg_mfe_pct": 0.0,
        "avg_mae_pct": 0.0,
        "exit_reasons": {},
        "failure_patterns": {},
        "success_patterns": {},
        "top_failure_patterns": "",
        "worst_trades": [],
        "best_trades": [],
        "largest_mfe_givebacks": [],
        "deepest_adverse_trades": [],
        "note": "No closed trades were generated for this agent in the selected run.",
    }


def classify_pattern(row: dict[str, Any]) -> str:
    ret = safe_float(row.get("return_pct"))
    mfe = safe_float(row.get("mfe_pct"))
    mae = safe_float(row.get("mae_pct"))
    hold = safe_int(row.get("holding_days"))
    exit_reason = str(row.get("exit_reason") or "").upper()

    if ret > 0:
        if hold <= 5 and ret >= 5:
            return "FAST_WINNER"
        if mfe >= 8 and ret < max(1.0, mfe * 0.35):
            return "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN"
        if hold >= 20 and ret >= 5:
            return "PATIENT_TREND_WINNER"
        return "NORMAL_WIN"

    if "HARD_STOP" in exit_reason or "STOP" in exit_reason:
        if mae <= -10:
            return "DEEP_ADVERSE_MOVE"
        return "STOP_LOSS_HIT"

    if mfe >= 5 and ret < 0:
        return "WINNER_TURNED_LOSER"

    if hold <= 5 and ret <= -3:
        return "FAST_FAILED_ENTRY"

    if mae <= -10:
        return "DEEP_ADVERSE_MOVE"

    return "NORMAL_LOSS"


def detect_trade_table_columns(con: duckdb.DuckDBPyConnection) -> dict[str, str | None]:
    table = "arena_trades"

    return {
        "agent": first_existing_column(con, table, ["agent", "agent_name", "agent_id"]),
        "agent_key": first_existing_column(con, table, ["agent_key", "strategy", "profile_key"]),
        "symbol": first_existing_column(con, table, ["symbol", "ticker"]),
        "name": first_existing_column(con, table, ["name", "company_name", "company"]),
        "entry_date": first_existing_column(con, table, ["entry_date", "opened_at", "entry_dt", "buy_date"]),
        "exit_date": first_existing_column(con, table, ["exit_date", "closed_at", "exit_dt", "sell_date"]),
        "entry_price": first_existing_column(con, table, ["entry_price", "buy_price"]),
        "exit_price": first_existing_column(con, table, ["exit_price", "sell_price"]),
        "shares": first_existing_column(con, table, ["shares", "quantity", "qty"]),
        "pnl_jpy": first_existing_column(con, table, ["pnl_jpy", "realized_pnl_jpy", "pnl"]),
        "return_pct": first_existing_column(con, table, ["return_pct", "ret_pct", "return_percent"]),
        "holding_days": first_existing_column(con, table, ["holding_days", "hold_days", "days_held"]),
        "mfe_pct": first_existing_column(con, table, ["mfe_pct", "max_favorable_excursion_pct"]),
        "mae_pct": first_existing_column(con, table, ["mae_pct", "max_adverse_excursion_pct"]),
        "exit_reason": first_existing_column(con, table, ["exit_reason", "reason"]),
        "run_id": first_existing_column(con, table, ["run_id", "simulation_run_id", "arena_run_id"]),
    }


def build_select_expr(cols: dict[str, str | None], key: str, default_sql: str) -> str:
    col = cols.get(key)
    if col:
        return f"{qident(col)} AS {key}"
    return f"{default_sql} AS {key}"


def load_closed_trades(
    con: duckdb.DuckDBPyConnection,
    run_id: str | None,
    max_trade_rows: int,
) -> list[TradeRow]:
    if not table_exists(con, "arena_trades"):
        raise SystemExit("missing required table: arena_trades")

    cols = detect_trade_table_columns(con)

    required = ["symbol", "entry_date", "exit_date"]
    missing = [k for k in required if not cols.get(k)]
    if missing:
        raise SystemExit(f"arena_trades missing required columns: {missing}")

    select_exprs = [
        build_select_expr(cols, "agent", "NULL"),
        build_select_expr(cols, "agent_key", "NULL"),
        build_select_expr(cols, "symbol", "NULL"),
        build_select_expr(cols, "name", "NULL"),
        build_select_expr(cols, "entry_date", "NULL"),
        build_select_expr(cols, "exit_date", "NULL"),
        build_select_expr(cols, "entry_price", "NULL"),
        build_select_expr(cols, "exit_price", "NULL"),
        build_select_expr(cols, "shares", "NULL"),
        build_select_expr(cols, "pnl_jpy", "0"),
        build_select_expr(cols, "return_pct", "0"),
        build_select_expr(cols, "holding_days", "0"),
        build_select_expr(cols, "mfe_pct", "0"),
        build_select_expr(cols, "mae_pct", "0"),
        build_select_expr(cols, "exit_reason", "'UNKNOWN'"),
    ]

    where = [f"{qident(cols['exit_date'])} IS NOT NULL"]
    params: list[Any] = []

    if run_id and cols.get("run_id"):
        where.append(f"CAST({qident(cols['run_id'])} AS VARCHAR) = ?")
        params.append(run_id)

    sql = f"""
        SELECT
          {", ".join(select_exprs)}
        FROM arena_trades
        WHERE {" AND ".join(where)}
        ORDER BY
          CAST({qident(cols["exit_date"])} AS VARCHAR),
          CAST({qident(cols["entry_date"])} AS VARCHAR),
          CAST({qident(cols["symbol"])} AS VARCHAR)
        LIMIT {int(max_trade_rows)}
    """

    rows = con.execute(sql, params).fetchall()
    out: list[TradeRow] = []

    for r in rows:
        d = {
            "agent": r[0],
            "agent_key": r[1],
            "symbol": r[2],
            "name": r[3],
            "entry_date": r[4],
            "exit_date": r[5],
            "entry_price": r[6],
            "exit_price": r[7],
            "shares": r[8],
            "pnl_jpy": r[9],
            "return_pct": r[10],
            "holding_days": r[11],
            "mfe_pct": r[12],
            "mae_pct": r[13],
            "exit_reason": r[14],
        }
        agent, agent_key = normalize_agent(d["agent"], d["agent_key"])

        pattern = classify_pattern(d)

        out.append(
            TradeRow(
                agent=agent,
                agent_key=agent_key,
                symbol=str(d["symbol"] or ""),
                name=str(d["name"] or ""),
                entry_date=str(d["entry_date"] or "")[:10],
                exit_date=str(d["exit_date"] or "")[:10],
                entry_price=safe_float(d["entry_price"], None) if d["entry_price"] is not None else None,
                exit_price=safe_float(d["exit_price"], None) if d["exit_price"] is not None else None,
                shares=safe_float(d["shares"], None) if d["shares"] is not None else None,
                pnl_jpy=money(d["pnl_jpy"]),
                return_pct=pct(d["return_pct"]),
                holding_days=safe_int(d["holding_days"]),
                mfe_pct=pct(d["mfe_pct"]),
                mae_pct=pct(d["mae_pct"]),
                exit_reason=str(d["exit_reason"] or "UNKNOWN"),
                pattern=pattern,
            )
        )

    return out


def trade_to_dict(t: TradeRow) -> dict[str, Any]:
    return {
        "agent": t.agent,
        "agent_key": t.agent_key,
        "symbol": t.symbol,
        "name": t.name,
        "entry_date": t.entry_date,
        "exit_date": t.exit_date,
        "entry_price": t.entry_price,
        "exit_price": t.exit_price,
        "shares": t.shares,
        "pnl_jpy": t.pnl_jpy,
        "return_pct": t.return_pct,
        "holding_days": t.holding_days,
        "mfe_pct": t.mfe_pct,
        "mae_pct": t.mae_pct,
        "exit_reason": t.exit_reason,
        "pattern": t.pattern,
    }


def enrich_trade_context(
    con: duckdb.DuckDBPyConnection,
    trades: list[TradeRow],
    include_context: bool,
) -> dict[str, dict[str, Any]]:
    if not include_context or not trades:
        return {}

    contexts: dict[str, dict[str, Any]] = {}

    has_scores = table_exists(con, "agent_scores_daily")
    has_features = table_exists(con, "features_daily")
    has_value = table_exists(con, "value_features_daily")
    has_sector_relative = table_exists(con, "value_features_sector_relative_jp")
    has_fund = table_exists(con, "fundamentals_latest_jp")
    has_master = table_exists(con, "company_master_jp")

    score_cols = {}
    if has_scores:
        score_cols = {
            "date": first_existing_column(con, "agent_scores_daily", ["date", "trade_date", "as_of_date"]),
            "symbol": first_existing_column(con, "agent_scores_daily", ["symbol", "ticker"]),
            "agent": first_existing_column(con, "agent_scores_daily", ["agent", "agent_name"]),
            "agent_key": first_existing_column(con, "agent_scores_daily", ["agent_key", "strategy", "profile_key"]),
            "rank": first_existing_column(con, "agent_scores_daily", ["rank", "score_rank", "agent_rank"]),
            "action": first_existing_column(con, "agent_scores_daily", ["action", "signal_action"]),
            "score": first_existing_column(con, "agent_scores_daily", ["score", "total_score"]),
        }

    feature_cols = {}
    if has_features:
        feature_cols = {
            "date": first_existing_column(con, "features_daily", ["date", "trade_date", "as_of_date"]),
            "symbol": first_existing_column(con, "features_daily", ["symbol", "ticker"]),
            "return_5d_pct": first_existing_column(con, "features_daily", ["return_5d_pct"]),
            "return_20d_pct": first_existing_column(con, "features_daily", ["return_20d_pct"]),
            "volume_ratio_20d": first_existing_column(con, "features_daily", ["volume_ratio_20d"]),
            "rsi_14": first_existing_column(con, "features_daily", ["rsi_14"]),
            "range_position_252d_0_1": first_existing_column(con, "features_daily", ["range_position_252d_0_1"]),
        }

    value_cols = {}
    if has_value:
        value_cols = {
            "date": first_existing_column(con, "value_features_daily", ["date", "trade_date", "as_of_date"]),
            "symbol": first_existing_column(con, "value_features_daily", ["symbol", "ticker"]),
            "value_trap_penalty": first_existing_column(con, "value_features_daily", ["value_trap_penalty"]),
            "value_score": first_existing_column(con, "value_features_daily", ["value_score"]),
            "valuation_discount_score": first_existing_column(con, "value_features_daily", ["valuation_discount_score"]),
        }

    sector_cols = {}
    if has_sector_relative:
        sector_cols = {
            "symbol": first_existing_column(con, "value_features_sector_relative_jp", ["symbol", "ticker"]),
            "sector_33": first_existing_column(con, "value_features_sector_relative_jp", ["sector_33", "sector33", "sector_name_33"]),
            "sector_relative_value_score": first_existing_column(
                con,
                "value_features_sector_relative_jp",
                ["sector_relative_value_score", "sector_33_relative_value_score", "relative_value_score"],
            ),
            "per_vs_sector_median": first_existing_column(
                con,
                "value_features_sector_relative_jp",
                ["per_vs_sector_median", "per_discount_vs_sector_median", "per_sector_ratio"],
            ),
            "pbr_vs_sector_median": first_existing_column(
                con,
                "value_features_sector_relative_jp",
                ["pbr_vs_sector_median", "pbr_discount_vs_sector_median", "pbr_sector_ratio"],
            ),
        }

    fund_cols = {}
    if has_fund:
        fund_cols = {
            "symbol": first_existing_column(con, "fundamentals_latest_jp", ["symbol", "ticker"]),
            "market_cap_jpy": first_existing_column(con, "fundamentals_latest_jp", ["market_cap_jpy", "market_cap"]),
            "per": first_existing_column(con, "fundamentals_latest_jp", ["per", "trailing_pe", "pe"]),
            "pbr": first_existing_column(con, "fundamentals_latest_jp", ["pbr", "price_to_book"]),
            "roe_pct": first_existing_column(con, "fundamentals_latest_jp", ["roe_pct", "roe"]),
            "operating_margin_pct": first_existing_column(
                con,
                "fundamentals_latest_jp",
                ["operating_margin_pct", "operating_margin"],
            ),
        }

    master_cols = {}
    if has_master:
        master_cols = {
            "symbol": first_existing_column(con, "company_master_jp", ["symbol", "ticker"]),
            "sector_33": first_existing_column(con, "company_master_jp", ["sector_33", "sector33", "sector_name_33"]),
            "name": first_existing_column(con, "company_master_jp", ["name", "company_name", "company"]),
        }

    for t in trades:
        key = f"{t.agent_key}|{t.symbol}|{t.entry_date}"
        ctx: dict[str, Any] = {}

        if has_scores and score_cols.get("date") and score_cols.get("symbol"):
            where = [
                f"CAST({qident(score_cols['symbol'])} AS VARCHAR) = ?",
                f"CAST({qident(score_cols['date'])} AS DATE) = CAST(? AS DATE)",
            ]
            params: list[Any] = [t.symbol, t.entry_date]

            if score_cols.get("agent_key"):
                where.append(f"CAST({qident(score_cols['agent_key'])} AS VARCHAR) = ?")
                params.append(t.agent_key)
            elif score_cols.get("agent"):
                where.append(f"CAST({qident(score_cols['agent'])} AS VARCHAR) = ?")
                params.append(t.agent)

            sel = []
            for alias in ["rank", "action", "score"]:
                col = score_cols.get(alias)
                if col:
                    sel.append(f"{qident(col)} AS {alias}")

            if sel:
                try:
                    r = con.execute(
                        f"""
                        SELECT {", ".join(sel)}
                        FROM agent_scores_daily
                        WHERE {" AND ".join(where)}
                        LIMIT 1
                        """,
                        params,
                    ).fetchone()
                    if r:
                        ctx["score"] = {alias: r[i] for i, alias in enumerate([a for a in ["rank", "action", "score"] if score_cols.get(a)])}
                except Exception:
                    pass

        if has_features and feature_cols.get("date") and feature_cols.get("symbol"):
            sel_aliases = [
                "return_5d_pct",
                "return_20d_pct",
                "volume_ratio_20d",
                "rsi_14",
                "range_position_252d_0_1",
            ]
            sel = [f"{qident(feature_cols[a])} AS {a}" for a in sel_aliases if feature_cols.get(a)]
            if sel:
                try:
                    r = con.execute(
                        f"""
                        SELECT {", ".join(sel)}
                        FROM features_daily
                        WHERE CAST({qident(feature_cols["symbol"])} AS VARCHAR) = ?
                          AND CAST({qident(feature_cols["date"])} AS DATE) = CAST(? AS DATE)
                        LIMIT 1
                        """,
                        [t.symbol, t.entry_date],
                    ).fetchone()
                    if r:
                        aliases = [a for a in sel_aliases if feature_cols.get(a)]
                        ctx["feature"] = {alias: r[i] for i, alias in enumerate(aliases)}
                except Exception:
                    pass

        if has_value and value_cols.get("date") and value_cols.get("symbol"):
            sel_aliases = ["value_trap_penalty", "value_score", "valuation_discount_score"]
            sel = [f"{qident(value_cols[a])} AS {a}" for a in sel_aliases if value_cols.get(a)]
            if sel:
                try:
                    r = con.execute(
                        f"""
                        SELECT {", ".join(sel)}
                        FROM value_features_daily
                        WHERE CAST({qident(value_cols["symbol"])} AS VARCHAR) = ?
                          AND CAST({qident(value_cols["date"])} AS DATE) = CAST(? AS DATE)
                        LIMIT 1
                        """,
                        [t.symbol, t.entry_date],
                    ).fetchone()
                    if r:
                        aliases = [a for a in sel_aliases if value_cols.get(a)]
                        ctx["value"] = {alias: r[i] for i, alias in enumerate(aliases)}
                except Exception:
                    pass

        if has_sector_relative and sector_cols.get("symbol"):
            sel_aliases = [
                "sector_33",
                "sector_relative_value_score",
                "per_vs_sector_median",
                "pbr_vs_sector_median",
            ]
            sel = [f"{qident(sector_cols[a])} AS {a}" for a in sel_aliases if sector_cols.get(a)]
            if sel:
                try:
                    r = con.execute(
                        f"""
                        SELECT {", ".join(sel)}
                        FROM value_features_sector_relative_jp
                        WHERE CAST({qident(sector_cols["symbol"])} AS VARCHAR) = ?
                        LIMIT 1
                        """,
                        [t.symbol],
                    ).fetchone()
                    if r:
                        aliases = [a for a in sel_aliases if sector_cols.get(a)]
                        ctx["sector_relative"] = {alias: r[i] for i, alias in enumerate(aliases)}
                except Exception:
                    pass

        if has_fund and fund_cols.get("symbol"):
            sel_aliases = [
                "market_cap_jpy",
                "per",
                "pbr",
                "roe_pct",
                "operating_margin_pct",
            ]
            sel = [f"{qident(fund_cols[a])} AS {a}" for a in sel_aliases if fund_cols.get(a)]
            if sel:
                try:
                    r = con.execute(
                        f"""
                        SELECT {", ".join(sel)}
                        FROM fundamentals_latest_jp
                        WHERE CAST({qident(fund_cols["symbol"])} AS VARCHAR) = ?
                        LIMIT 1
                        """,
                        [t.symbol],
                    ).fetchone()
                    if r:
                        aliases = [a for a in sel_aliases if fund_cols.get(a)]
                        ctx["fundamental"] = {alias: r[i] for i, alias in enumerate(aliases)}
                except Exception:
                    pass

        if has_master and master_cols.get("symbol"):
            sel_aliases = ["sector_33", "name"]
            sel = [f"{qident(master_cols[a])} AS {a}" for a in sel_aliases if master_cols.get(a)]
            if sel:
                try:
                    r = con.execute(
                        f"""
                        SELECT {", ".join(sel)}
                        FROM company_master_jp
                        WHERE CAST({qident(master_cols["symbol"])} AS VARCHAR) = ?
                        LIMIT 1
                        """,
                        [t.symbol],
                    ).fetchone()
                    if r:
                        aliases = [a for a in sel_aliases if master_cols.get(a)]
                        ctx["master"] = {alias: r[i] for i, alias in enumerate(aliases)}
                except Exception:
                    pass

        contexts[key] = ctx

    return contexts


def calc_summary(agent: str, agent_key: str, trades: list[TradeRow], top_n: int) -> dict[str, Any]:
    if not trades:
        return empty_agent_summary(agent, agent_key)

    n = len(trades)
    wins = [t for t in trades if t.return_pct > 0]
    losses = [t for t in trades if t.return_pct <= 0]

    gross_win = sum(t.pnl_jpy for t in trades if t.pnl_jpy > 0)
    gross_loss = abs(sum(t.pnl_jpy for t in trades if t.pnl_jpy < 0))

    avg_ret = sum(t.return_pct for t in trades) / n
    avg_win = sum(t.return_pct for t in wins) / len(wins) if wins else 0.0
    avg_loss = sum(t.return_pct for t in losses) / len(losses) if losses else 0.0
    payoff = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
    pf = gross_win / gross_loss if gross_loss > 0 else 0.0

    exit_reasons = Counter(t.exit_reason or "UNKNOWN" for t in trades)
    failure_patterns = Counter(t.pattern for t in trades if t.return_pct <= 0)
    success_patterns = Counter(t.pattern for t in trades if t.return_pct > 0)

    worst = sorted(trades, key=lambda x: x.return_pct)[:top_n]
    best = sorted(trades, key=lambda x: x.return_pct, reverse=True)[:top_n]

    givebacks = sorted(
        trades,
        key=lambda x: (x.mfe_pct - max(x.return_pct, 0.0)),
        reverse=True,
    )[:top_n]

    adverse = sorted(trades, key=lambda x: x.mae_pct)[:top_n]

    top_failure_patterns = ", ".join(
        f"{k}:{v}" for k, v in failure_patterns.most_common(4)
    )

    return {
        "agent": agent,
        "agent_key": agent_key,
        "label": f"{agent} / {agent_key}",
        "trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / n * 100.0, 2),
        "avg_return_pct": round(avg_ret, 4),
        "avg_win_pct": round(avg_win, 4),
        "avg_loss_pct": round(avg_loss, 4),
        "payoff_ratio": round(payoff, 4),
        "profit_factor": round(pf, 4),
        "total_pnl_jpy": round(sum(t.pnl_jpy for t in trades), 2),
        "avg_mfe_pct": round(sum(t.mfe_pct for t in trades) / n, 4),
        "avg_mae_pct": round(sum(t.mae_pct for t in trades) / n, 4),
        "exit_reasons": dict(exit_reasons.most_common()),
        "failure_patterns": dict(failure_patterns.most_common()),
        "success_patterns": dict(success_patterns.most_common()),
        "top_failure_patterns": top_failure_patterns,
        "worst_trades": [trade_to_dict(t) for t in worst],
        "best_trades": [trade_to_dict(t) for t in best],
        "largest_mfe_givebacks": [trade_to_dict(t) for t in givebacks],
        "deepest_adverse_trades": [trade_to_dict(t) for t in adverse],
    }


def build_summaries(trades: list[TradeRow], top_n: int) -> dict[str, dict[str, Any]]:
    by_agent: dict[str, list[TradeRow]] = defaultdict(list)

    for t in trades:
        label = f"{t.agent} / {t.agent_key}"
        by_agent[label].append(t)

    summaries: dict[str, dict[str, Any]] = {}

    for agent, agent_key in EXPECTED_AGENTS:
        label = f"{agent} / {agent_key}"
        summaries[label] = calc_summary(agent, agent_key, by_agent.get(label, []), top_n)

    # Include unexpected agents, but after the canonical 7.
    for label, rows in sorted(by_agent.items()):
        if label not in summaries:
            agent = rows[0].agent
            agent_key = rows[0].agent_key
            summaries[label] = calc_summary(agent, agent_key, rows, top_n)

    return summaries


def compact_context_line(t: dict[str, Any], ctx: dict[str, Any]) -> str:
    parts = [
        f"`{t['symbol']}` {t['entry_date']} → {t['exit_date']} {t['return_pct']:.2f}%"
    ]

    score = ctx.get("score") or {}
    if score:
        parts.append(
            "score: "
            + ", ".join(f"{k}={v}" for k, v in score.items() if v is not None)
        )

    feature = ctx.get("feature") or {}
    if feature:
        parts.append(
            "feature: "
            + ", ".join(f"{k}={v}" for k, v in feature.items() if v is not None)
        )

    value = ctx.get("value") or {}
    if value:
        parts.append(
            "value: "
            + ", ".join(f"{k}={v}" for k, v in value.items() if v is not None)
        )

    sector = ctx.get("sector_relative") or {}
    if sector:
        parts.append(
            "sector_relative: "
            + ", ".join(f"{k}={v}" for k, v in sector.items() if v is not None)
        )

    fund = ctx.get("fundamental") or {}
    if fund:
        parts.append(
            "fund: "
            + ", ".join(f"{k}={v}" for k, v in fund.items() if v is not None)
        )

    return " / ".join(parts)


def md_money(v: Any) -> str:
    return f"¥{safe_float(v):,.0f}"


def md_pct(v: Any) -> str:
    return f"{safe_float(v):.2f}%"


def render_trade_table(title: str, rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append(f"### {title}")
    lines.append("")
    if not rows:
        lines.append("_No trades._")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|")

    for r in rows:
        lines.append(
            "| {symbol} | {name} | {entry_date} | {exit_date} | {ret} | {pnl} | {hold} | {mfe} | {mae} | {exit_reason} | {pattern} |".format(
                symbol=r.get("symbol", ""),
                name=str(r.get("name") or "").replace("|", "／"),
                entry_date=r.get("entry_date", ""),
                exit_date=r.get("exit_date", ""),
                ret=md_pct(r.get("return_pct")),
                pnl=md_money(r.get("pnl_jpy")),
                hold=r.get("holding_days", 0),
                mfe=md_pct(r.get("mfe_pct")),
                mae=md_pct(r.get("mae_pct")),
                exit_reason=r.get("exit_reason", ""),
                pattern=r.get("pattern", ""),
            )
        )

    lines.append("")
    return "\n".join(lines)


def render_markdown(
    data: dict[str, Any],
    contexts: dict[str, dict[str, Any]],
    include_context: bool,
) -> str:
    lines: list[str] = []

    lines.append("# Neon Tokyo AI Arena Trade Diagnostics")
    lines.append("")
    lines.append(f"Generated: `{data['generated_at']}`")
    lines.append(f"Run ID: `{data.get('run_id') or 'latest'}`")
    lines.append("")
    lines.append("> Purpose: detailed agent-by-agent win/loss diagnosis and rule-improvement source data.")
    lines.append("")
    lines.append("## Dataset Summary")
    lines.append("")
    counts = data["counts"]
    lines.append(f"- Closed trades: **{counts['closed_trades']}**")
    lines.append(f"- Open positions: **{counts['open_positions']}**")
    lines.append(f"- Agents with closed trades: **{counts['agents_with_closed_trades']}**")
    lines.append(f"- Agent summaries exported: **{counts['agent_summaries']}**")
    lines.append(f"- Exported compact trade rows in JSON: **{counts['compact_trade_rows']}**")
    lines.append(f"- Equity curve rows: **{counts['equity_curve_rows']}**")
    lines.append("")

    lines.append("## Agent Summary")
    lines.append("")
    lines.append(
        "| Agent | Trades | Win | Avg Ret | Avg Win | Avg Loss | Payoff | PF | PnL | Avg MFE | Avg MAE | Top Failure Patterns |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")

    for label, s in data["agent_summaries"].items():
        lines.append(
            "| {label} | {trades} | {win} | {avg_ret} | {avg_win} | {avg_loss} | {payoff} | {pf} | {pnl} | {mfe} | {mae} | {fail} |".format(
                label=label.replace("|", "／"),
                trades=s["trades"],
                win=md_pct(s["win_rate"]),
                avg_ret=md_pct(s["avg_return_pct"]),
                avg_win=md_pct(s["avg_win_pct"]),
                avg_loss=md_pct(s["avg_loss_pct"]),
                payoff=s["payoff_ratio"],
                pf=s["profit_factor"],
                pnl=md_money(s["total_pnl_jpy"]),
                mfe=md_pct(s["avg_mfe_pct"]),
                mae=md_pct(s["avg_mae_pct"]),
                fail=s.get("top_failure_patterns") or "",
            )
        )

    lines.append("")

    for label, s in data["agent_summaries"].items():
        agent = s["agent"]
        agent_key = s["agent_key"]

        lines.append(f"## {agent} / `{agent_key}`")
        lines.append("")
        lines.append("### Key Metrics")
        lines.append("")

        if s["trades"] == 0:
            lines.append("- Trades: **0**")
            lines.append("- Note: No closed trades were generated for this agent in the selected run.")
            lines.append("")
            continue

        lines.append(
            f"- Trades: **{s['trades']}**, Win rate: **{md_pct(s['win_rate'])}**, Total PnL: **{md_money(s['total_pnl_jpy'])}**"
        )
        lines.append(
            f"- Avg return: **{md_pct(s['avg_return_pct'])}**, Avg win: **{md_pct(s['avg_win_pct'])}**, Avg loss: **{md_pct(s['avg_loss_pct'])}**"
        )
        lines.append(
            f"- Payoff ratio: **{s['payoff_ratio']}**, Profit factor: **{s['profit_factor']}**"
        )
        lines.append(
            f"- Avg MFE: **{md_pct(s['avg_mfe_pct'])}**, Avg MAE: **{md_pct(s['avg_mae_pct'])}**"
        )
        lines.append("")

        for title, key in [
            ("Exit Reasons", "exit_reasons"),
            ("Failure Patterns", "failure_patterns"),
            ("Success Patterns", "success_patterns"),
        ]:
            lines.append(f"### {title}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(s.get(key) or {}, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")

        lines.append(render_trade_table("Worst Trades", s["worst_trades"]))
        lines.append(render_trade_table("Best Trades", s["best_trades"]))
        lines.append(render_trade_table("Largest MFE Givebacks", s["largest_mfe_givebacks"]))
        lines.append(render_trade_table("Deepest Adverse Trades", s["deepest_adverse_trades"]))

        if include_context and s["worst_trades"]:
            lines.append("### Compact Entry Context For Worst Trades")
            lines.append("")
            for t in s["worst_trades"]:
                ctx_key = f"{agent_key}|{t['symbol']}|{t['entry_date']}"
                ctx = contexts.get(ctx_key) or {}
                if ctx:
                    lines.append(f"- {compact_context_line(t, ctx)}")
                else:
                    lines.append(
                        f"- `{t['symbol']}` {t['entry_date']} → {t['exit_date']} {t['return_pct']:.2f}%: context unavailable"
                    )
            lines.append("")

    lines.append("## Prompt Suggestion")
    lines.append("")
    lines.append("```text")
    lines.append(
        "このTrade Diagnosticsをもとに、各Agentの勝因・敗因を定量的に分析してください。特に、勝率と損益の非対称性、MFE/MAE、exit reason、entry context、fundamental/value/sector-relative contextを見て、Agent別に改善すべき売買ルールを優先順位付きで提案してください。"
    )
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def count_open_positions(con: duckdb.DuckDBPyConnection, run_id: str | None) -> int:
    if not table_exists(con, "arena_open_positions"):
        return 0

    run_col = first_existing_column(con, "arena_open_positions", ["run_id", "simulation_run_id", "arena_run_id"])
    if run_id and run_col:
        try:
            return int(
                con.execute(
                    f"SELECT COUNT(*) FROM arena_open_positions WHERE CAST({qident(run_col)} AS VARCHAR) = ?",
                    [run_id],
                ).fetchone()[0]
            )
        except Exception:
            return 0

    try:
        return int(con.execute("SELECT COUNT(*) FROM arena_open_positions").fetchone()[0])
    except Exception:
        return 0


def count_equity_curve_rows(con: duckdb.DuckDBPyConnection, run_id: str | None) -> int:
    if not table_exists(con, "arena_equity_curve"):
        return 0

    run_col = first_existing_column(con, "arena_equity_curve", ["run_id", "simulation_run_id", "arena_run_id"])
    if run_id and run_col:
        try:
            return int(
                con.execute(
                    f"SELECT COUNT(*) FROM arena_equity_curve WHERE CAST({qident(run_col)} AS VARCHAR) = ?",
                    [run_id],
                ).fetchone()[0]
            )
        except Exception:
            return 0

    try:
        return int(con.execute("SELECT COUNT(*) FROM arena_equity_curve").fetchone()[0])
    except Exception:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default=os.environ.get("PRICE_DUCKDB_PATH", DEFAULT_DB_PATH))
    parser.add_argument("--out-dir", default=os.environ.get("TRADE_DIAGNOSTICS_OUT_DIR", DEFAULT_OUT_DIR))
    parser.add_argument("--run-id", default=os.environ.get("AI_ARENA_DIAGNOSTICS_RUN_ID") or None)
    parser.add_argument(
        "--max-trade-rows",
        type=int,
        default=int(os.environ.get("TRADE_DIAGNOSTICS_MAX_TRADE_ROWS", "1500")),
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=int(os.environ.get("TRADE_DIAGNOSTICS_TOP_N", "15")),
    )
    parser.add_argument(
        "--include-context",
        default=os.environ.get("TRADE_DIAGNOSTICS_INCLUDE_CONTEXT", "true"),
    )
    parser.add_argument(
        "--fail-if-no-trades",
        default=os.environ.get("TRADE_DIAGNOSTICS_FAIL_IF_NO_TRADES", "true"),
    )
    args = parser.parse_args()

    include_context = str(args.include_context).lower() in {"1", "true", "yes", "y", "on"}
    fail_if_no_trades = str(args.fail_if_no_trades).lower() in {"1", "true", "yes", "y", "on"}

    db_path = Path(args.db_path)
    if not db_path.exists() or db_path.stat().st_size <= 0:
        raise SystemExit(f"DuckDB not found or empty: {db_path}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))

    trades = load_closed_trades(
        con=con,
        run_id=args.run_id,
        max_trade_rows=args.max_trade_rows,
    )

    if fail_if_no_trades and not trades:
        raise SystemExit("Trade diagnostics has no closed trades")

    summaries = build_summaries(trades, args.top_n)
    contexts = enrich_trade_context(con, trades, include_context)

    compact_rows = [trade_to_dict(t) for t in trades]

    agents_with_closed = len({f"{t.agent} / {t.agent_key}" for t in trades})

    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_utc_iso(),
        "run_id": args.run_id or "latest",
        "duckdb": str(db_path),
        "counts": {
            "closed_trades": len(trades),
            "open_positions": count_open_positions(con, args.run_id),
            "agents_with_closed_trades": agents_with_closed,
            "agent_summaries": len(summaries),
            "compact_trade_rows": len(compact_rows),
            "equity_curve_rows": count_equity_curve_rows(con, args.run_id),
        },
        "expected_agents": [
            {"agent": agent, "agent_key": agent_key, "label": f"{agent} / {agent_key}"}
            for agent, agent_key in EXPECTED_AGENTS
        ],
        "agent_summaries": summaries,
        "compact_trades": compact_rows,
    }

    if include_context:
        data["entry_contexts"] = contexts

    json_path = out_dir / "latest.json"
    md_path = out_dir / "latest.md"

    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    md_path.write_text(
        render_markdown(data, contexts, include_context),
        encoding="utf-8",
    )

    con.close()

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"closed_trades={len(trades)}")
    print(f"agent_summaries={len(summaries)}")
    print("agents=" + ",".join(data["agent_summaries"].keys()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
