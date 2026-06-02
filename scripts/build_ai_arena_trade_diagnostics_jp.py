#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export Neon Tokyo AI Arena JP trade diagnostics.

Outputs:
  site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json
  site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.md

Design goals:
- Do not fail just because diagnostics run_id is "display" while arena_trades uses a real simulation run_id.
- Always include all 7 JP AI Arena agents in summaries and Markdown.
- Use best-effort joins for entry context, feature context, fundamentals, and sector-relative value context.
- Fail loudly only for genuinely fatal conditions: missing DuckDB, missing arena_trades, or no closed trades when fail-if-no-trades is enabled.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


AGENTS: list[tuple[str, str, str]] = [
    ("KYOU", "daily_striker", "Short-Term Breakout / Momentum"),
    ("NAGARE", "weekly_sage", "Medium-Term Trend / Flow"),
    ("MAMORU", "risk_sentinel", "Risk Sentinel / Defensive Quality"),
    ("SAGURI", "discovery_scout", "Discovery / Small-Cap Scout"),
    ("MATSU", "contrarian_monk", "Pullback / Patient Reversal"),
    ("KAESHI", "reversal_snapback", "Oversold Reversal / Snapback"),
    ("HIZUMI", "value_mispricing", "Value Mispricing / Sector Relative Value"),
]

AGENT_NAME_BY_KEY = {k: n for n, k, _ in AGENTS}
AGENT_KEY_BY_NAME = {n: k for n, k, _ in AGENTS}
AGENT_DESC_BY_KEY = {k: d for n, k, d in AGENTS}

DEFAULT_OUT_DIR = "site/data/japan/ai-arena/diagnostics/trade-diagnostics"


# ----------------------------
# Utility
# ----------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def qident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def table_exists(con: duckdb.DuckDBPyConnection, table: str) -> bool:
    try:
        return bool(
            con.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table],
            ).fetchone()[0]
        )
    except Exception:
        return False


def get_columns(con: duckdb.DuckDBPyConnection, table: str) -> list[str]:
    if not table_exists(con, table):
        return []
    rows = con.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = ?
        ORDER BY ordinal_position
        """,
        [table],
    ).fetchall()
    return [str(r[0]) for r in rows]


def first_existing(cols: set[str], candidates: list[str]) -> str | None:
    for c in candidates:
        if c in cols:
            return c
    return None


def safe_float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def safe_int(v: Any, default: int = 0) -> int:
    if v is None:
        return default
    try:
        return int(float(v))
    except Exception:
        return default


def pct(v: Any) -> float:
    x = safe_float(v, 0.0)
    return x


def money(v: Any) -> float:
    return safe_float(v, 0.0)


def fmt_pct(v: Any, digits: int = 2) -> str:
    x = safe_float(v, 0.0)
    return f"{x:.{digits}f}%"


def fmt_money(v: Any) -> str:
    x = safe_float(v, 0.0)
    return f"¥{x:,.0f}"


def fmt_float(v: Any, digits: int = 4) -> str:
    x = safe_float(v, 0.0)
    return f"{x:.{digits}f}"


def normalize_date(v: Any) -> str:
    if v is None:
        return ""
    s = str(v)
    return s[:10]


def normalize_agent(agent: Any, agent_key: Any) -> tuple[str, str]:
    raw_agent = str(agent or "").strip()
    raw_key = str(agent_key or "").strip()

    if raw_key in AGENT_NAME_BY_KEY:
        return AGENT_NAME_BY_KEY[raw_key], raw_key

    if raw_agent in AGENT_KEY_BY_NAME:
        return raw_agent, AGENT_KEY_BY_NAME[raw_agent]

    lower_key = raw_key.lower()
    lower_agent = raw_agent.lower()

    aliases = {
        "daily": ("KYOU", "daily_striker"),
        "daily_striker": ("KYOU", "daily_striker"),
        "kyou": ("KYOU", "daily_striker"),
        "weekly": ("NAGARE", "weekly_sage"),
        "weekly_sage": ("NAGARE", "weekly_sage"),
        "nagare": ("NAGARE", "weekly_sage"),
        "risk": ("MAMORU", "risk_sentinel"),
        "risk_sentinel": ("MAMORU", "risk_sentinel"),
        "mamoru": ("MAMORU", "risk_sentinel"),
        "discovery": ("SAGURI", "discovery_scout"),
        "discovery_scout": ("SAGURI", "discovery_scout"),
        "saguri": ("SAGURI", "discovery_scout"),
        "contrarian": ("MATSU", "contrarian_monk"),
        "contrarian_monk": ("MATSU", "contrarian_monk"),
        "matsu": ("MATSU", "contrarian_monk"),
        "reversal": ("KAESHI", "reversal_snapback"),
        "reversal_snapback": ("KAESHI", "reversal_snapback"),
        "kaeshi": ("KAESHI", "reversal_snapback"),
        "value": ("HIZUMI", "value_mispricing"),
        "value_mispricing": ("HIZUMI", "value_mispricing"),
        "hizumi": ("HIZUMI", "value_mispricing"),
    }

    for token in [lower_key, lower_agent]:
        if token in aliases:
            return aliases[token]

    for known_key, known_name in AGENT_NAME_BY_KEY.items():
        if known_key in lower_key or known_key in lower_agent:
            return known_name, known_key

    if raw_agent:
        return raw_agent.upper(), raw_key or raw_agent.lower()

    return "UNKNOWN", raw_key or "unknown"


def value_or_none(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


# ----------------------------
# Dataclasses
# ----------------------------

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
    entry_context: dict[str, Any]


@dataclass
class AgentSummary:
    agent: str
    agent_key: str
    description: str
    trades: int
    wins: int
    losses: int
    win_rate_pct: float
    total_pnl_jpy: float
    avg_return_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    payoff_ratio: float
    profit_factor: float
    avg_mfe_pct: float
    avg_mae_pct: float
    exit_reasons: dict[str, int]
    failure_patterns: dict[str, int]
    success_patterns: dict[str, int]


# ----------------------------
# Column detection
# ----------------------------

def detect_trade_columns(con: duckdb.DuckDBPyConnection) -> dict[str, str | None]:
    cols = set(get_columns(con, "arena_trades"))

    return {
        "run_id": first_existing(cols, ["run_id", "simulation_run_id", "display_run_id"]),
        "agent": first_existing(cols, ["agent", "agent_name", "name_agent"]),
        "agent_key": first_existing(cols, ["agent_key", "agent_id", "strategy", "strategy_key"]),
        "symbol": first_existing(cols, ["symbol", "ticker", "code"]),
        "name": first_existing(cols, ["name", "company_name", "company_name_jp", "security_name"]),
        "entry_date": first_existing(cols, ["entry_date", "entry_at", "buy_date", "opened_at"]),
        "exit_date": first_existing(cols, ["exit_date", "exit_at", "sell_date", "closed_at"]),
        "entry_price": first_existing(cols, ["entry_price", "buy_price", "open_price"]),
        "exit_price": first_existing(cols, ["exit_price", "sell_price", "close_price"]),
        "shares": first_existing(cols, ["shares", "quantity", "qty", "position_size"]),
        "pnl_jpy": first_existing(cols, ["pnl_jpy", "realized_pnl_jpy", "pnl", "profit_jpy"]),
        "return_pct": first_existing(cols, ["return_pct", "ret_pct", "trade_return_pct", "return"]),
        "holding_days": first_existing(cols, ["holding_days", "hold_days", "days_held"]),
        "mfe_pct": first_existing(cols, ["mfe_pct", "max_favorable_excursion_pct"]),
        "mae_pct": first_existing(cols, ["mae_pct", "max_adverse_excursion_pct"]),
        "exit_reason": first_existing(cols, ["exit_reason", "reason", "close_reason"]),
    }


def select_expr(cols: dict[str, str | None], logical: str, default_sql: str) -> str:
    col = cols.get(logical)
    if col:
        return f"{qident(col)} AS {qident(logical)}"
    return f"{default_sql} AS {qident(logical)}"


# ----------------------------
# Classification
# ----------------------------

def classify_pattern(d: dict[str, Any]) -> str:
    ret = pct(d.get("return_pct"))
    mfe = pct(d.get("mfe_pct"))
    mae = pct(d.get("mae_pct"))
    hold = safe_int(d.get("holding_days"))
    exit_reason = str(d.get("exit_reason") or "").upper()

    if ret >= 0:
        if ret >= 5.0 and hold <= 5:
            return "FAST_WINNER"
        if mfe >= 8.0 and ret < max(1.0, mfe * 0.35):
            return "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN"
        if hold >= 20 and ret >= 8.0:
            return "PATIENT_TREND_WINNER"
        return "NORMAL_WIN"

    if "HARD_STOP" in exit_reason or "STOP" in exit_reason:
        if mae <= -10.0:
            return "DEEP_ADVERSE_MOVE"
        return "STOP_LOSS_HIT"

    if mfe >= 5.0 and ret < 0:
        return "WINNER_TURNED_LOSER"

    if hold <= 4 and ret <= -4.0:
        return "FAST_FAILED_ENTRY"

    if mae <= -10.0:
        return "DEEP_ADVERSE_MOVE"

    return "NORMAL_LOSS"


# ----------------------------
# Entry context loading
# ----------------------------

def load_feature_context(
    con: duckdb.DuckDBPyConnection,
    symbol: str,
    entry_date: str,
) -> dict[str, Any]:
    context: dict[str, Any] = {}

    if not symbol or not entry_date:
        return context

    # features_daily
    if table_exists(con, "features_daily"):
        cols = set(get_columns(con, "features_daily"))
        sym_col = first_existing(cols, ["symbol", "ticker", "code"])
        date_col = first_existing(cols, ["date", "trade_date", "as_of_date"])

        wanted = [
            "return_5d_pct",
            "return_20d_pct",
            "volume_ratio_20d",
            "rsi_14",
            "range_position_252d_0_1",
            "close",
            "volume",
            "atr_14_pct",
            "volatility_20d_pct",
        ]
        available = [c for c in wanted if c in cols]

        if sym_col and date_col and available:
            sql = f"""
                SELECT {", ".join(qident(c) for c in available)}
                FROM features_daily
                WHERE CAST({qident(sym_col)} AS VARCHAR) = ?
                  AND CAST({qident(date_col)} AS DATE) <= CAST(? AS DATE)
                ORDER BY CAST({qident(date_col)} AS DATE) DESC
                LIMIT 1
            """
            try:
                row = con.execute(sql, [symbol, entry_date]).fetchone()
                if row:
                    context["feature"] = {
                        k: value_or_none(row[i])
                        for i, k in enumerate(available)
                    }
            except Exception as e:
                context["feature_error"] = str(e)

    # value_features_daily
    if table_exists(con, "value_features_daily"):
        cols = set(get_columns(con, "value_features_daily"))
        sym_col = first_existing(cols, ["symbol", "ticker", "code"])
        date_col = first_existing(cols, ["date", "trade_date", "as_of_date"])

        wanted = [
            "value_score",
            "value_score_raw",
            "value_trap_penalty",
            "quality_score",
            "mispricing_score",
            "revaluation_confirmation_score",
            "sector_relative_value_score",
            "sector_relative_discount_score",
            "sector_relative_quality_score",
        ]
        available = [c for c in wanted if c in cols]

        if sym_col and date_col and available:
            sql = f"""
                SELECT {", ".join(qident(c) for c in available)}
                FROM value_features_daily
                WHERE CAST({qident(sym_col)} AS VARCHAR) = ?
                  AND CAST({qident(date_col)} AS DATE) <= CAST(? AS DATE)
                ORDER BY CAST({qident(date_col)} AS DATE) DESC
                LIMIT 1
            """
            try:
                row = con.execute(sql, [symbol, entry_date]).fetchone()
                if row:
                    context["value"] = {
                        k: value_or_none(row[i])
                        for i, k in enumerate(available)
                    }
            except Exception as e:
                context["value_error"] = str(e)

    # value_features_sector_relative_jp
    if table_exists(con, "value_features_sector_relative_jp"):
        cols = set(get_columns(con, "value_features_sector_relative_jp"))
        sym_col = first_existing(cols, ["symbol", "ticker", "code"])

        wanted = [
            "sector_33",
            "sector_33_name",
            "sector_relative_value_score",
            "sector_relative_discount_score",
            "sector_relative_quality_score",
            "sector_relative_composite_score",
            "per_vs_sector_median",
            "pbr_vs_sector_median",
            "roe_vs_sector_median",
            "operating_margin_vs_sector_median",
            "sector_sample_count",
        ]
        available = [c for c in wanted if c in cols]

        if sym_col and available:
            sql = f"""
                SELECT {", ".join(qident(c) for c in available)}
                FROM value_features_sector_relative_jp
                WHERE CAST({qident(sym_col)} AS VARCHAR) = ?
                LIMIT 1
            """
            try:
                row = con.execute(sql, [symbol]).fetchone()
                if row:
                    context["sector_relative_value"] = {
                        k: value_or_none(row[i])
                        for i, k in enumerate(available)
                    }
            except Exception as e:
                context["sector_relative_value_error"] = str(e)

    # fundamentals_latest_jp
    for table in ["fundamentals_latest_jp", "fundamentals_latest"]:
        if not table_exists(con, table):
            continue

        cols = set(get_columns(con, table))
        sym_col = first_existing(cols, ["symbol", "ticker", "code"])

        wanted = [
            "market_cap_jpy",
            "market_cap",
            "per",
            "pbr",
            "roe_pct",
            "operating_margin_pct",
            "profit_margin_pct",
            "revenue_growth_pct",
            "earnings_growth_pct",
            "debt_to_equity",
            "sector_33",
            "sector_33_name",
            "sector",
            "industry",
        ]
        available = [c for c in wanted if c in cols]

        if sym_col and available:
            sql = f"""
                SELECT {", ".join(qident(c) for c in available)}
                FROM {qident(table)}
                WHERE CAST({qident(sym_col)} AS VARCHAR) = ?
                LIMIT 1
            """
            try:
                row = con.execute(sql, [symbol]).fetchone()
                if row:
                    context["fundamental"] = {
                        k: value_or_none(row[i])
                        for i, k in enumerate(available)
                    }
                    break
            except Exception as e:
                context["fundamental_error"] = str(e)

    return context


# ----------------------------
# Load trades
# ----------------------------

def load_closed_trades(
    con: duckdb.DuckDBPyConnection,
    run_id: str | None,
    max_trade_rows: int,
    include_context: bool,
) -> tuple[list[TradeRow], dict[str, Any]]:
    if not table_exists(con, "arena_trades"):
        raise SystemExit("missing required table: arena_trades")

    cols = detect_trade_columns(con)

    required = ["symbol", "entry_date", "exit_date"]
    missing = [k for k in required if not cols.get(k)]
    if missing:
        raise SystemExit(f"arena_trades missing required columns: {missing}")

    select_exprs = [
        select_expr(cols, "agent", "NULL"),
        select_expr(cols, "agent_key", "NULL"),
        select_expr(cols, "symbol", "NULL"),
        select_expr(cols, "name", "NULL"),
        select_expr(cols, "entry_date", "NULL"),
        select_expr(cols, "exit_date", "NULL"),
        select_expr(cols, "entry_price", "NULL"),
        select_expr(cols, "exit_price", "NULL"),
        select_expr(cols, "shares", "NULL"),
        select_expr(cols, "pnl_jpy", "0"),
        select_expr(cols, "return_pct", "0"),
        select_expr(cols, "holding_days", "0"),
        select_expr(cols, "mfe_pct", "0"),
        select_expr(cols, "mae_pct", "0"),
        select_expr(cols, "exit_reason", "'UNKNOWN'"),
    ]

    base_where = [f"{qident(cols['exit_date'])} IS NOT NULL"]

    def fetch_rows(use_run_filter: bool) -> list[Any]:
        where = list(base_where)
        params: list[Any] = []

        if use_run_filter and run_id and cols.get("run_id"):
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
        return con.execute(sql, params).fetchall()

    diagnostics: dict[str, Any] = {
        "requested_run_id": run_id,
        "run_id_column": cols.get("run_id"),
        "used_run_filter": False,
        "fallback_used": False,
        "warnings": [],
        "detected_trade_columns": cols,
    }

    rows = fetch_rows(use_run_filter=True)
    if rows and run_id and cols.get("run_id"):
        diagnostics["used_run_filter"] = True

    if not rows and run_id:
        msg = (
            f"arena_trades has no closed trades for run_id={run_id!r}; "
            "falling back to all closed trades in the current DuckDB."
        )
        print("WARNING:", msg)
        diagnostics["warnings"].append(msg)
        diagnostics["fallback_used"] = True
        rows = fetch_rows(use_run_filter=False)

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
        symbol = str(d["symbol"] or "")
        entry_date = normalize_date(d["entry_date"])

        context = {}
        if include_context:
            context = load_feature_context(con, symbol, entry_date)

        out.append(
            TradeRow(
                agent=agent,
                agent_key=agent_key,
                symbol=symbol,
                name=str(d["name"] or ""),
                entry_date=entry_date,
                exit_date=normalize_date(d["exit_date"]),
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
                entry_context=context,
            )
        )

    diagnostics["closed_trade_rows_loaded"] = len(out)
    return out, diagnostics


# ----------------------------
# Summaries
# ----------------------------

def summarize_agent(agent: str, agent_key: str, trades: list[TradeRow]) -> AgentSummary:
    n = len(trades)
    wins = [t for t in trades if t.return_pct > 0]
    losses = [t for t in trades if t.return_pct <= 0]

    total_pnl = sum(t.pnl_jpy for t in trades)
    avg_ret = sum(t.return_pct for t in trades) / n if n else 0.0
    avg_win = sum(t.return_pct for t in wins) / len(wins) if wins else 0.0
    avg_loss = sum(t.return_pct for t in losses) / len(losses) if losses else 0.0

    gross_win = sum(t.pnl_jpy for t in wins if t.pnl_jpy > 0)
    gross_loss_abs = abs(sum(t.pnl_jpy for t in losses if t.pnl_jpy < 0))

    payoff = abs(avg_win / avg_loss) if avg_loss < 0 else 0.0
    pf = gross_win / gross_loss_abs if gross_loss_abs > 0 else (999.0 if gross_win > 0 else 0.0)

    exit_reasons = Counter(t.exit_reason or "UNKNOWN" for t in trades)
    failure_patterns = Counter(t.pattern for t in trades if t.return_pct <= 0)
    success_patterns = Counter(t.pattern for t in trades if t.return_pct > 0)

    return AgentSummary(
        agent=agent,
        agent_key=agent_key,
        description=AGENT_DESC_BY_KEY.get(agent_key, ""),
        trades=n,
        wins=len(wins),
        losses=len(losses),
        win_rate_pct=(len(wins) / n * 100.0) if n else 0.0,
        total_pnl_jpy=total_pnl,
        avg_return_pct=avg_ret,
        avg_win_pct=avg_win,
        avg_loss_pct=avg_loss,
        payoff_ratio=payoff,
        profit_factor=pf,
        avg_mfe_pct=(sum(t.mfe_pct for t in trades) / n if n else 0.0),
        avg_mae_pct=(sum(t.mae_pct for t in trades) / n if n else 0.0),
        exit_reasons=dict(exit_reasons.most_common()),
        failure_patterns=dict(failure_patterns.most_common()),
        success_patterns=dict(success_patterns.most_common()),
    )


def build_summaries(trades: list[TradeRow]) -> dict[str, AgentSummary]:
    by_agent_key: dict[str, list[TradeRow]] = defaultdict(list)
    for t in trades:
        by_agent_key[t.agent_key].append(t)

    summaries: dict[str, AgentSummary] = {}
    for agent, agent_key, _desc in AGENTS:
        summaries[agent_key] = summarize_agent(agent, agent_key, by_agent_key.get(agent_key, []))

    # Preserve unknown agents too, but official 7 always exist.
    for key, rows in sorted(by_agent_key.items()):
        if key not in summaries:
            agent = rows[0].agent if rows else key.upper()
            summaries[key] = summarize_agent(agent, key, rows)

    return summaries


def top_trades(
    trades: list[TradeRow],
    agent_key: str,
    kind: str,
    n: int,
) -> list[TradeRow]:
    rows = [t for t in trades if t.agent_key == agent_key]

    if kind == "worst":
        return sorted(rows, key=lambda t: (t.return_pct, t.pnl_jpy))[:n]
    if kind == "best":
        return sorted(rows, key=lambda t: (t.return_pct, t.pnl_jpy), reverse=True)[:n]
    if kind == "mfe_giveback":
        def giveback(t: TradeRow) -> float:
            return t.mfe_pct - t.return_pct
        return sorted(rows, key=giveback, reverse=True)[:n]
    if kind == "deepest_adverse":
        return sorted(rows, key=lambda t: t.mae_pct)[:n]

    return rows[:n]


# ----------------------------
# JSON
# ----------------------------

def build_json_payload(
    trades: list[TradeRow],
    summaries: dict[str, AgentSummary],
    run_id: str,
    max_trade_rows: int,
    top_n: int,
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    official_agent_count = len(AGENTS)

    return {
        "schema_version": "neon_tokyo_ai_arena_trade_diagnostics_v1",
        "generated_at": utc_now_iso(),
        "run_id": run_id,
        "counts": {
            "closed_trades": len(trades),
            "agents_with_closed_trades": len(set(t.agent_key for t in trades)),
            "official_agents": official_agent_count,
            "agent_summaries": len(summaries),
            "exported_compact_trade_rows": min(len(trades), max_trade_rows),
        },
        "diagnostics": diagnostics,
        "agent_summaries": {
            k: asdict(v)
            for k, v in summaries.items()
        },
        "top_trades": {
            agent_key: {
                "worst": [asdict(t) for t in top_trades(trades, agent_key, "worst", top_n)],
                "best": [asdict(t) for t in top_trades(trades, agent_key, "best", top_n)],
                "largest_mfe_givebacks": [asdict(t) for t in top_trades(trades, agent_key, "mfe_giveback", top_n)],
                "deepest_adverse": [asdict(t) for t in top_trades(trades, agent_key, "deepest_adverse", top_n)],
            }
            for _agent, agent_key, _desc in AGENTS
        },
        "compact_trades": [asdict(t) for t in trades[:max_trade_rows]],
    }


# ----------------------------
# Markdown
# ----------------------------

def md_counter(d: dict[str, int]) -> str:
    if not d:
        return "-"
    return ", ".join(f"{k}:{v}" for k, v in list(d.items())[:5])


def md_trade_table(rows: list[TradeRow]) -> str:
    if not rows:
        return "_No trades._\n"

    lines = [
        "| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    for t in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    t.symbol,
                    (t.name or "").replace("|", "／"),
                    t.entry_date,
                    t.exit_date,
                    fmt_pct(t.return_pct),
                    fmt_money(t.pnl_jpy),
                    str(t.holding_days),
                    fmt_pct(t.mfe_pct),
                    fmt_pct(t.mae_pct),
                    t.exit_reason.replace("|", "／"),
                    t.pattern.replace("|", "／"),
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def md_context_lines(rows: list[TradeRow]) -> str:
    if not rows:
        return "_No entry context._\n"

    lines: list[str] = []

    for t in rows:
        ctx = t.entry_context or {}
        parts: list[str] = []

        feature = ctx.get("feature") or {}
        if feature:
            parts.append(
                "feature: "
                + ", ".join(
                    f"{k}={feature.get(k)}"
                    for k in [
                        "return_5d_pct",
                        "return_20d_pct",
                        "volume_ratio_20d",
                        "rsi_14",
                        "range_position_252d_0_1",
                    ]
                    if k in feature
                )
            )

        value = ctx.get("value") or {}
        if value:
            parts.append(
                "value: "
                + ", ".join(
                    f"{k}={value.get(k)}"
                    for k in [
                        "value_score",
                        "value_trap_penalty",
                        "sector_relative_value_score",
                        "sector_relative_discount_score",
                    ]
                    if k in value
                )
            )

        srv = ctx.get("sector_relative_value") or {}
        if srv:
            parts.append(
                "sector_relative: "
                + ", ".join(
                    f"{k}={srv.get(k)}"
                    for k in [
                        "sector_33",
                        "sector_33_name",
                        "sector_relative_value_score",
                        "sector_relative_composite_score",
                        "per_vs_sector_median",
                        "pbr_vs_sector_median",
                        "sector_sample_count",
                    ]
                    if k in srv
                )
            )

        fund = ctx.get("fundamental") or {}
        if fund:
            parts.append(
                "fund: "
                + ", ".join(
                    f"{k}={fund.get(k)}"
                    for k in [
                        "market_cap_jpy",
                        "per",
                        "pbr",
                        "roe_pct",
                        "operating_margin_pct",
                        "sector_33",
                        "sector_33_name",
                    ]
                    if k in fund
                )
            )

        if not parts:
            parts.append("context: unavailable")

        lines.append(
            f"- `{t.symbol}` {t.entry_date} → {t.exit_date} "
            f"{fmt_pct(t.return_pct)}: "
            + " / ".join(parts)
        )

    return "\n".join(lines) + "\n"


def build_markdown(
    payload: dict[str, Any],
    trades: list[TradeRow],
    summaries: dict[str, AgentSummary],
    top_n: int,
) -> str:
    counts = payload["counts"]

    lines: list[str] = []
    lines.append("# Neon Tokyo AI Arena Trade Diagnostics")
    lines.append("")
    lines.append(f"Generated: `{payload['generated_at']}`")
    lines.append(f"Run ID: `{payload['run_id']}`")
    lines.append("")
    lines.append("> Purpose: agent-by-agent win/loss diagnosis and rule-improvement source data.")
    lines.append("")
    lines.append("## Dataset Summary")
    lines.append("")
    lines.append(f"- Closed trades: **{counts['closed_trades']}**")
    lines.append(f"- Agents with closed trades: **{counts['agents_with_closed_trades']}**")
    lines.append(f"- Official agents: **{counts['official_agents']}**")
    lines.append(f"- Agent summaries: **{counts['agent_summaries']}**")
    lines.append(f"- Exported compact trade rows in JSON: **{counts['exported_compact_trade_rows']}**")
    lines.append("")
    lines.append("## Diagnostics Notes")
    lines.append("")

    diag = payload.get("diagnostics") or {}
    warnings = diag.get("warnings") or []
    if warnings:
        for w in warnings:
            lines.append(f"- WARNING: {w}")
    else:
        lines.append("- No loader warnings.")

    lines.append(f"- Requested run_id: `{diag.get('requested_run_id')}`")
    lines.append(f"- Used run_id filter: `{diag.get('used_run_filter')}`")
    lines.append(f"- Fallback used: `{diag.get('fallback_used')}`")
    lines.append("")
    lines.append("## Agent Summary")
    lines.append("")
    lines.append(
        "| Agent | Trades | Win | Avg Ret | Avg Win | Avg Loss | Payoff | PF | PnL | Avg MFE | Avg MAE | Top Failure Patterns |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"
    )

    for agent, agent_key, _desc in AGENTS:
        s = summaries[agent_key]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"{s.agent} / `{s.agent_key}`",
                    str(s.trades),
                    fmt_pct(s.win_rate_pct),
                    fmt_pct(s.avg_return_pct),
                    fmt_pct(s.avg_win_pct),
                    fmt_pct(s.avg_loss_pct),
                    fmt_float(s.payoff_ratio),
                    fmt_float(s.profit_factor),
                    fmt_money(s.total_pnl_jpy),
                    fmt_pct(s.avg_mfe_pct),
                    fmt_pct(s.avg_mae_pct),
                    md_counter(s.failure_patterns),
                ]
            )
            + " |"
        )

    lines.append("")

    for agent, agent_key, desc in AGENTS:
        s = summaries[agent_key]
        lines.append(f"## {agent} / `{agent_key}`")
        lines.append("")
        lines.append(desc)
        lines.append("")
        lines.append("### Key Metrics")
        lines.append("")
        lines.append(f"- Trades: **{s.trades}**, Win rate: **{fmt_pct(s.win_rate_pct)}**, Total PnL: **{fmt_money(s.total_pnl_jpy)}**")
        lines.append(f"- Avg return: **{fmt_pct(s.avg_return_pct)}**, Avg win: **{fmt_pct(s.avg_win_pct)}**, Avg loss: **{fmt_pct(s.avg_loss_pct)}**")
        lines.append(f"- Payoff ratio: **{fmt_float(s.payoff_ratio)}**, Profit factor: **{fmt_float(s.profit_factor)}**")
        lines.append(f"- Avg MFE: **{fmt_pct(s.avg_mfe_pct)}**, Avg MAE: **{fmt_pct(s.avg_mae_pct)}**")
        lines.append("")
        lines.append("### Exit Reasons")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.exit_reasons, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### Failure Patterns")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.failure_patterns, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### Success Patterns")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.success_patterns, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### Worst Trades")
        lines.append("")
        worst = top_trades(trades, agent_key, "worst", top_n)
        lines.append(md_trade_table(worst))
        lines.append("")
        lines.append("### Best Trades")
        lines.append("")
        lines.append(md_trade_table(top_trades(trades, agent_key, "best", top_n)))
        lines.append("")
        lines.append("### Largest MFE Givebacks")
        lines.append("")
        lines.append(md_trade_table(top_trades(trades, agent_key, "mfe_giveback", top_n)))
        lines.append("")
        lines.append("### Deepest Adverse Trades")
        lines.append("")
        lines.append(md_trade_table(top_trades(trades, agent_key, "deepest_adverse", top_n)))
        lines.append("")
        lines.append("### Compact Entry Context For Worst Trades")
        lines.append("")
        lines.append(md_context_lines(worst))
        lines.append("")

    lines.append("## Prompt Suggestion")
    lines.append("")
    lines.append("```text")
    lines.append(
        "このTrade Diagnosticsをもとに、各Agentの勝因・敗因を定量的に分析してください。"
        "特に、勝率と損益の非対称性、MFE/MAE、exit reason、entry context、"
        "fundamental/value/sector-relative value contextを見て、Agent別に改善すべき売買ルールを優先順位付きで提案してください。"
    )
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


# ----------------------------
# Validation
# ----------------------------

def validate_payload(payload: dict[str, Any], md: str, fail_if_no_trades: bool) -> None:
    schema = str(payload.get("schema_version", ""))
    if schema != "neon_tokyo_ai_arena_trade_diagnostics_v1":
        raise SystemExit(f"Unexpected schema_version: {schema}")

    counts = payload.get("counts") or {}
    closed_trades = int(counts.get("closed_trades") or 0)

    if fail_if_no_trades and closed_trades <= 0:
        raise SystemExit("Trade diagnostics has no closed trades")

    summaries = payload.get("agent_summaries") or {}
    if len(summaries) < 7:
        raise SystemExit(f"Expected at least 7 agent summaries, got {len(summaries)}")

    for agent, agent_key, _desc in AGENTS:
        if agent_key not in summaries:
            raise SystemExit(f"Missing official agent summary: {agent} / {agent_key}")
        if agent not in md:
            raise SystemExit(f"Markdown missing agent token: {agent}")
        if agent_key not in md:
            raise SystemExit(f"Markdown missing agent_key token: {agent_key}")


# ----------------------------
# Main
# ----------------------------

def parse_bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db-path",
        default=os.environ.get("PRICE_DUCKDB_PATH", "data/cache/neon_tokyo_jp.duckdb"),
    )
    parser.add_argument(
        "--out-dir",
        default=os.environ.get("TRADE_DIAGNOSTICS_OUT_DIR", DEFAULT_OUT_DIR),
    )
    parser.add_argument(
        "--run-id",
        default=os.environ.get("AI_ARENA_DIAGNOSTICS_RUN_ID", "display"),
    )
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
        action="store_true",
        default=parse_bool_env("TRADE_DIAGNOSTICS_INCLUDE_CONTEXT", True),
    )
    parser.add_argument(
        "--fail-if-no-trades",
        action="store_true",
        default=parse_bool_env("TRADE_DIAGNOSTICS_FAIL_IF_NO_TRADES", True),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    db_path = Path(args.db_path)
    if not db_path.exists() or db_path.stat().st_size <= 0:
        raise SystemExit(f"DuckDB not found or empty: {db_path}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = str(args.run_id or "").strip()
    if not run_id:
        run_id = "all"

    con = duckdb.connect(str(db_path), read_only=True)

    try:
        trades, loader_diagnostics = load_closed_trades(
            con=con,
            run_id=None if run_id == "all" else run_id,
            max_trade_rows=args.max_trade_rows,
            include_context=bool(args.include_context),
        )
    finally:
        con.close()

    summaries = build_summaries(trades)

    payload = build_json_payload(
        trades=trades,
        summaries=summaries,
        run_id=run_id,
        max_trade_rows=args.max_trade_rows,
        top_n=args.top_n,
        diagnostics=loader_diagnostics,
    )

    md = build_markdown(
        payload=payload,
        trades=trades,
        summaries=summaries,
        top_n=args.top_n,
    )

    validate_payload(payload, md, fail_if_no_trades=bool(args.fail_if_no_trades))

    json_path = out_dir / "latest.json"
    md_path = out_dir / "latest.md"

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(md, encoding="utf-8")

    print("trade_diagnostics_schema_ok")
    print("closed_trades=", payload["counts"]["closed_trades"])
    print("agents=", len(payload["agent_summaries"]))
    print("wrote=", json_path)
    print("wrote=", md_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
