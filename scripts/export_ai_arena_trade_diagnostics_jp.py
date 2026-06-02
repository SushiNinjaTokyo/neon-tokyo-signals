#!/usr/bin/env python3
from __future__ import annotations

"""Export high-integrity AI Arena JP trade diagnostics from DuckDB.

This script is intentionally strict.  It is not designed to make a broken run
"look successful"; it is designed to detect bad trade data, bad run_id
resolution, duplicated rows, missing returns, missing exit reasons, and missing
MFE/MAE context before those defects reach ChatGPT analysis.

Core fixes vs the broken diagnostics:
- Resolve TRADE_DIAGNOSTICS_RUN_ID=display to the actual promoted AI Arena run.
- Do not fall back to all historical closed trades unless explicitly allowed.
- Deduplicate by trade_id when available, otherwise by a stable trade key.
- Recompute realized_return_pct, MFE, MAE, giveback and excursion quality from
  prices_daily, rather than trusting stale or zero-filled exported fields.
- Preserve all seven official agents in summaries, but fail if a valid run has
  no trades and TRADE_DIAGNOSTICS_FAIL_IF_NO_TRADES=true.
- Enrich each trade with entry feature, fundamental, value and sector-relative
  context when the source tables/columns exist.
- Emit JSON + Markdown fit for quantitative agent-by-agent diagnosis.
"""

import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()

PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH", "data/cache/neon_tokyo_jp.duckdb")
RUN_ID_REQUESTED = os.getenv("TRADE_DIAGNOSTICS_RUN_ID", "display").strip() or "display"
MAX_TRADE_ROWS = int(os.getenv("TRADE_DIAGNOSTICS_MAX_TRADE_ROWS", "1500"))
TOP_N = int(os.getenv("TRADE_DIAGNOSTICS_TOP_N", "15"))
INCLUDE_CONTEXT = os.getenv("TRADE_DIAGNOSTICS_INCLUDE_CONTEXT", "true").lower() in {"1", "true", "yes", "on"}
FAIL_IF_NO_TRADES = os.getenv("TRADE_DIAGNOSTICS_FAIL_IF_NO_TRADES", "true").lower() in {"1", "true", "yes", "on"}
ALLOW_FALLBACK = os.getenv("TRADE_DIAGNOSTICS_ALLOW_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}
FAIL_ON_DATA_QUALITY = os.getenv("TRADE_DIAGNOSTICS_FAIL_ON_DATA_QUALITY", "true").lower() in {"1", "true", "yes", "on"}
STRICT_DISPLAY_RESOLUTION = os.getenv("TRADE_DIAGNOSTICS_STRICT_DISPLAY_RESOLUTION", "true").lower() in {"1", "true", "yes", "on"}

OUT_BASE = OUT_DIR / "data" / "japan" / "ai-arena" / "diagnostics" / "trade-diagnostics"
JSON_OUT = OUT_BASE / "latest.json"
MD_OUT = OUT_BASE / "latest.md"

SCHEMA_VERSION = "neon_tokyo_ai_arena_trade_diagnostics_v2"

OFFICIAL_AGENTS: list[dict[str, str]] = [
    {"agent_id": "daily_striker", "name": "KYOU", "title": "Short-Term Breakout / Momentum"},
    {"agent_id": "weekly_sage", "name": "NAGARE", "title": "Medium-Term Trend / Flow"},
    {"agent_id": "risk_sentinel", "name": "MAMORU", "title": "Risk Sentinel / Defensive Quality"},
    {"agent_id": "discovery_scout", "name": "SAGURI", "title": "Discovery / Small-Cap Scout"},
    {"agent_id": "contrarian_monk", "name": "MATSU", "title": "Pullback / Patient Reversal"},
    {"agent_id": "reversal_snapback", "name": "KAESHI", "title": "Oversold Reversal / Snapback"},
    {"agent_id": "value_mispricing", "name": "HIZUMI", "title": "Value Mispricing / Sector Relative Value"},
]
AGENT_BY_ID = {a["agent_id"]: a for a in OFFICIAL_AGENTS}

CONTEXT_FEATURE_COLS = [
    "return_1d_pct", "return_3d_pct", "return_5d_pct", "return_10d_pct", "return_20d_pct",
    "volume_ratio_20d", "rsi_14", "range_position_252d_0_1",
    "distance_from_52w_high_pct", "sma20", "sma50", "sma120", "close",
]
CONTEXT_FUND_COLS = [
    "market_cap_jpy", "per", "pbr", "psr", "roe_pct", "roa_pct",
    "operating_margin_pct", "dividend_yield_pct",
]
CONTEXT_VALUE_PATTERNS = [
    "value", "trap", "sector", "relative", "discount", "quality", "percentile",
    "pbr", "per", "roe", "operating_margin",
]


@dataclass
class TableInfo:
    exists: bool
    columns: list[str]


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "+00:00"


def safe_float(v: Any, default: float | None = None) -> float | None:
    if v is None:
        return default
    try:
        if pd.isna(v):
            return default
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except Exception:
        return default


def safe_int(v: Any, default: int = 0) -> int:
    try:
        if v is None or pd.isna(v):
            return default
        return int(v)
    except Exception:
        return default


def pct(n: float | None, digits: int = 2) -> float | None:
    if n is None:
        return None
    return round(float(n), digits)


def yen(n: float | None) -> str:
    if n is None:
        return "-"
    return f"¥{float(n):,.0f}"


def pct_label(n: float | None) -> str:
    if n is None:
        return "-"
    return f"{float(n):.2f}%"


def table_info(conn: duckdb.DuckDBPyConnection, table: str) -> TableInfo:
    try:
        cols = [str(r[1]) for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]
        return TableInfo(bool(cols), cols)
    except Exception:
        return TableInfo(False, [])


def has_table(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    return table_info(conn, table).exists


def existing_cols(conn: duckdb.DuckDBPyConnection, table: str, candidates: Iterable[str]) -> list[str]:
    info = table_info(conn, table)
    colset = set(info.columns)
    return [c for c in candidates if c in colset]


def normalize_date_value(v: Any) -> str | None:
    if v is None:
        return None
    try:
        return str(pd.to_datetime(v).date())
    except Exception:
        s = str(v).strip()
        return s[:10] if s else None


def connect_db() -> duckdb.DuckDBPyConnection:
    p = Path(PRICE_DUCKDB_PATH)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        raise SystemExit(f"DuckDB not found: {p}")
    return duckdb.connect(str(p), read_only=True)


def load_json_file(path: Path) -> dict[str, Any] | None:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def candidate_display_run_ids_from_site() -> list[str]:
    out: list[str] = []
    paths = [
        OUT_DIR / "data/japan/ai-arena/live/latest.json",
        OUT_DIR / "data/japan/ai-arena/summary/latest.json",
        OUT_DIR / "data/japan/ai-arena/ranking/latest.json",
        OUT_DIR / "data/japan/ai-arena/hero/latest.json",
    ]
    for p in paths:
        data = load_json_file(p)
        if not data:
            continue
        for key in ["run_id", "display_run_id", "current_run_id", "effective_run_id"]:
            v = data.get(key)
            if isinstance(v, str) and v.strip():
                out.append(v.strip())
        run = data.get("run")
        if isinstance(run, dict):
            v = run.get("run_id")
            if isinstance(v, str) and v.strip():
                out.append(v.strip())
    # preserve order and remove duplicates
    seen = set()
    uniq = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def resolve_display_run_id(conn: duckdb.DuckDBPyConnection) -> tuple[str | None, list[str]]:
    notes: list[str] = []
    candidates: list[str] = []

    if has_table(conn, "arena_display_runs"):
        info = table_info(conn, "arena_display_runs")
        cols = info.columns
        preferred_cols = [
            "run_id", "display_run_id", "current_run_id", "live_run_id",
            "promoted_run_id", "active_run_id", "latest_run_id",
        ]
        id_cols = [c for c in preferred_cols if c in cols]
        if not id_cols:
            id_cols = [c for c in cols if c.endswith("run_id") or c == "run_id"]
        order_col = None
        for c in ["updated_at", "created_at", "promoted_at", "generated_at"]:
            if c in cols:
                order_col = c
                break
        order_sql = f" ORDER BY {order_col} DESC" if order_col else ""
        for col in id_cols:
            try:
                rows = conn.execute(
                    f"SELECT {col} FROM arena_display_runs WHERE {col} IS NOT NULL{order_sql} LIMIT 20"
                ).fetchall()
                for r in rows:
                    v = str(r[0]).strip() if r and r[0] is not None else ""
                    if v:
                        candidates.append(v)
            except Exception as e:
                notes.append(f"Could not read arena_display_runs.{col}: {e}")

    candidates.extend(candidate_display_run_ids_from_site())

    # Keep only candidates that actually have rows in the simulation tables.
    valid: list[str] = []
    for rid in candidates:
        if not rid:
            continue
        try:
            trade_count = conn.execute("SELECT COUNT(*) FROM arena_trades WHERE run_id = ?", [rid]).fetchone()[0]
        except Exception:
            trade_count = 0
        try:
            order_count = conn.execute("SELECT COUNT(*) FROM arena_orders WHERE run_id = ?", [rid]).fetchone()[0]
        except Exception:
            order_count = 0
        try:
            equity_count = conn.execute("SELECT COUNT(*) FROM arena_equity_curve WHERE run_id = ?", [rid]).fetchone()[0]
        except Exception:
            equity_count = 0
        if trade_count > 0 or order_count > 0 or equity_count > 0:
            valid.append(rid)
            notes.append(f"display candidate `{rid}`: trades={trade_count}, orders={order_count}, equity={equity_count}")

    # Last resort: use most recent simulation run with trades.
    if not valid and has_table(conn, "arena_simulation_runs"):
        info = table_info(conn, "arena_simulation_runs")
        order_col = "created_at" if "created_at" in info.columns else None
        try:
            sql = """
                SELECT r.run_id, COUNT(t.trade_id) AS trade_count
                FROM arena_simulation_runs r
                LEFT JOIN arena_trades t ON t.run_id = r.run_id
                GROUP BY r.run_id
                HAVING COUNT(t.trade_id) > 0
            """
            if order_col:
                sql += f" ORDER BY MAX(r.{order_col}) DESC"
            else:
                sql += " ORDER BY r.run_id DESC"
            sql += " LIMIT 1"
            row = conn.execute(sql).fetchone()
            if row and row[0]:
                valid.append(str(row[0]))
                notes.append(f"resolved display by latest arena_simulation_runs with trades: `{row[0]}`")
        except Exception as e:
            notes.append(f"Could not resolve latest run from arena_simulation_runs: {e}")

    if not valid:
        return None, notes
    # Prefer the first valid candidate from display metadata/site output.
    return valid[0], notes


def resolve_effective_run_id(conn: duckdb.DuckDBPyConnection, requested: str) -> tuple[str | None, dict[str, Any]]:
    notes: list[str] = []
    requested_clean = requested.strip()
    if requested_clean.lower() == "display":
        rid, display_notes = resolve_display_run_id(conn)
        notes.extend(display_notes)
        if rid:
            return rid, {
                "requested_run_id": requested,
                "effective_run_id": rid,
                "display_resolved": True,
                "used_run_id_filter": True,
                "fallback_used": False,
                "notes": notes,
            }
        msg = "TRADE_DIAGNOSTICS_RUN_ID=display could not be resolved to a real run_id."
        notes.append(msg)
        if STRICT_DISPLAY_RESOLUTION:
            raise SystemExit(msg)
        return None, {
            "requested_run_id": requested,
            "effective_run_id": None,
            "display_resolved": False,
            "used_run_id_filter": False,
            "fallback_used": False,
            "notes": notes,
        }

    cnt = 0
    try:
        cnt = int(conn.execute("SELECT COUNT(*) FROM arena_trades WHERE run_id = ?", [requested_clean]).fetchone()[0] or 0)
    except Exception:
        pass
    if cnt > 0:
        return requested_clean, {
            "requested_run_id": requested,
            "effective_run_id": requested_clean,
            "display_resolved": False,
            "used_run_id_filter": True,
            "fallback_used": False,
            "notes": [f"requested run_id `{requested_clean}` has {cnt} arena_trades rows"],
        }

    if not ALLOW_FALLBACK:
        raise SystemExit(
            f"arena_trades has no rows for run_id='{requested_clean}'. "
            "Fallback is disabled. Set TRADE_DIAGNOSTICS_RUN_ID to the real run_id or use display after promoting a run."
        )

    return None, {
        "requested_run_id": requested,
        "effective_run_id": None,
        "display_resolved": False,
        "used_run_id_filter": False,
        "fallback_used": True,
        "notes": [
            f"WARNING: arena_trades has no rows for run_id='{requested_clean}'; "
            "falling back to all closed trades because TRADE_DIAGNOSTICS_ALLOW_FALLBACK=true."
        ],
    }


def sql_select_existing(conn: duckdb.DuckDBPyConnection, table: str, preferred: list[str]) -> list[str]:
    cols = table_info(conn, table).columns
    return [c for c in preferred if c in cols]


def fetch_trades(conn: duckdb.DuckDBPyConnection, effective_run_id: str | None) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not has_table(conn, "arena_trades"):
        raise SystemExit("arena_trades table is missing.")
    info = table_info(conn, "arena_trades")
    cols = info.columns

    where = ""
    params: list[Any] = []
    if effective_run_id:
        where = "WHERE run_id = ?"
        params = [effective_run_id]

    sql = f"SELECT * FROM arena_trades {where}"
    df = conn.execute(sql, params).df()
    raw_rows = len(df)

    if df.empty:
        return df, {
            "raw_trade_rows": raw_rows,
            "deduplicated_rows": 0,
            "duplicates_removed": 0,
            "dedupe_key": None,
        }

    # Keep only rows that represent closed trades.  arena_trades is supposed to be closed,
    # but older schemas can contain null exit_date/exit_price.
    if "exit_date" in df.columns:
        df = df[df["exit_date"].notna()].copy()
    if "exit_price" in df.columns:
        df = df[df["exit_price"].notna()].copy()

    before_dedupe = len(df)
    if "trade_id" in df.columns and df["trade_id"].notna().any():
        df = df.drop_duplicates(subset=["trade_id"], keep="last").copy()
        dedupe_key = "trade_id"
    else:
        fallback_key = [
            c for c in [
                "run_id", "agent_id", "ticker", "entry_date", "exit_date",
                "entry_price", "exit_price", "shares", "realized_pnl_jpy",
            ]
            if c in df.columns
        ]
        df = df.drop_duplicates(subset=fallback_key, keep="last").copy()
        dedupe_key = ",".join(fallback_key)

    # Stable order: exit date then agent then ticker.
    order_cols = [c for c in ["exit_date", "entry_date", "agent_id", "ticker", "trade_id"] if c in df.columns]
    if order_cols:
        df = df.sort_values(order_cols).copy()

    return df, {
        "raw_trade_rows": raw_rows,
        "closed_candidate_rows": before_dedupe,
        "deduplicated_rows": len(df),
        "duplicates_removed": max(0, before_dedupe - len(df)),
        "dedupe_key": dedupe_key,
        "available_columns": cols,
    }


def compute_trade_metrics(conn: duckdb.DuckDBPyConnection, row: dict[str, Any]) -> dict[str, Any]:
    ticker = str(row.get("ticker") or "")
    entry_date = normalize_date_value(row.get("entry_date"))
    exit_date = normalize_date_value(row.get("exit_date"))
    entry_price = safe_float(row.get("entry_price"))
    exit_price = safe_float(row.get("exit_price"))
    shares = safe_float(row.get("shares"), 0.0) or 0.0
    pnl = safe_float(row.get("realized_pnl_jpy"))

    if pnl is None and entry_price is not None and exit_price is not None:
        pnl = (exit_price - entry_price) * shares

    ret_pct = safe_float(row.get("realized_return_pct"))
    if entry_price and exit_price:
        recomputed = (exit_price / entry_price - 1.0) * 100.0
        if ret_pct is None or abs(ret_pct) < 1e-12:
            ret_pct = recomputed
        elif abs(ret_pct - recomputed) > 0.05:
            ret_pct = recomputed

    mfe_pct: float | None = None
    mae_pct: float | None = None
    mfe_price: float | None = None
    mae_price: float | None = None

    if ticker and entry_date and exit_date and entry_price:
        try:
            pr = conn.execute(
                """
                SELECT MAX(high) AS max_high, MIN(low) AS min_low
                FROM prices_daily
                WHERE ticker = ?
                  AND date BETWEEN ? AND ?
                """,
                [ticker, entry_date, exit_date],
            ).fetchone()
            if pr:
                max_high = safe_float(pr[0])
                min_low = safe_float(pr[1])
                if max_high is not None:
                    mfe_price = max_high
                    mfe_pct = (max_high / entry_price - 1.0) * 100.0
                if min_low is not None:
                    mae_price = min_low
                    mae_pct = (min_low / entry_price - 1.0) * 100.0
        except Exception:
            pass

    giveback_pct: float | None = None
    if mfe_pct is not None and ret_pct is not None:
        giveback_pct = mfe_pct - ret_pct

    hold_days = safe_int(row.get("holding_days"), 0)
    if hold_days <= 0 and entry_date and exit_date:
        try:
            hold_days = int((pd.to_datetime(exit_date).date() - pd.to_datetime(entry_date).date()).days)
        except Exception:
            hold_days = 0

    exit_reason = str(row.get("exit_reason_code") or row.get("exit_reason") or "UNKNOWN").strip() or "UNKNOWN"
    entry_reason = str(row.get("entry_reason_code") or "UNKNOWN").strip() or "UNKNOWN"

    pattern = classify_pattern(ret_pct, mfe_pct, mae_pct, hold_days, exit_reason)

    return {
        "ticker": ticker,
        "name": row.get("name") or ticker,
        "agent_id": row.get("agent_id"),
        "run_id": row.get("run_id"),
        "trade_id": row.get("trade_id"),
        "entry_signal_date": normalize_date_value(row.get("entry_signal_date")),
        "entry_date": entry_date,
        "exit_signal_date": normalize_date_value(row.get("exit_signal_date")),
        "exit_date": exit_date,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "shares": shares,
        "realized_pnl_jpy": pnl,
        "realized_return_pct": ret_pct,
        "holding_days": hold_days,
        "mfe_pct": mfe_pct,
        "mae_pct": mae_pct,
        "mfe_price": mfe_price,
        "mae_price": mae_price,
        "mfe_giveback_pct": giveback_pct,
        "exit_reason_code": exit_reason,
        "exit_reason_text": row.get("exit_reason_text"),
        "entry_reason_code": entry_reason,
        "entry_reason_text": row.get("entry_reason_text"),
        "diagnostic_pattern": pattern,
    }


def classify_pattern(ret: float | None, mfe: float | None, mae: float | None, hold_days: int, exit_reason: str) -> str:
    r = ret if ret is not None else 0.0
    m = mfe if mfe is not None else 0.0
    a = mae if mae is not None else 0.0
    if r < 0 and "STOP" in exit_reason.upper():
        return "STOP_LOSS_HIT"
    if r < 0 and a <= -8:
        return "DEEP_ADVERSE_MOVE"
    if r < 0 and m >= 8:
        return "WINNER_TURNED_LOSER"
    if r < 0 and hold_days <= 3:
        return "FAST_FAILED_ENTRY"
    if r < 0 and hold_days >= 15:
        return "SLOW_BLEED_LOSER"
    if r >= 0 and m - r >= 8:
        return "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN"
    if r >= 5 and hold_days <= 5:
        return "FAST_WINNER"
    if r >= 0:
        return "NORMAL_WIN"
    return "NORMAL_LOSS"


def fetch_context_for_trade(conn: duckdb.DuckDBPyConnection, tr: dict[str, Any]) -> dict[str, Any]:
    if not INCLUDE_CONTEXT:
        return {}
    ticker = tr.get("ticker")
    signal_date = tr.get("entry_signal_date") or tr.get("entry_date")
    if not ticker or not signal_date:
        return {}

    out: dict[str, Any] = {}

    if has_table(conn, "features_daily"):
        cols = existing_cols(conn, "features_daily", CONTEXT_FEATURE_COLS)
        if cols:
            try:
                row = conn.execute(
                    f"SELECT {', '.join(cols)} FROM features_daily WHERE ticker = ? AND date <= ? ORDER BY date DESC LIMIT 1",
                    [ticker, signal_date],
                ).fetchone()
                if row:
                    out["feature"] = {c: normalize_scalar(v) for c, v in zip(cols, row)}
            except Exception:
                pass

    if has_table(conn, "fundamentals_latest_jp"):
        cols = existing_cols(conn, "fundamentals_latest_jp", CONTEXT_FUND_COLS)
        extra_cols = [c for c in table_info(conn, "fundamentals_latest_jp").columns if c in {"sector_33_name", "sector17_name", "sector", "industry"}]
        cols = list(dict.fromkeys(cols + extra_cols))
        if cols:
            try:
                row = conn.execute(
                    f"SELECT {', '.join(cols)} FROM fundamentals_latest_jp WHERE ticker = ? LIMIT 1",
                    [ticker],
                ).fetchone()
                if row:
                    out["fundamental"] = {c: normalize_scalar(v) for c, v in zip(cols, row)}
            except Exception:
                pass

    if has_table(conn, "value_features_daily"):
        all_cols = table_info(conn, "value_features_daily").columns
        cols = [c for c in all_cols if any(p in c.lower() for p in CONTEXT_VALUE_PATTERNS)]
        cols = [c for c in cols if c not in {"ticker", "date"}][:60]
        if cols:
            try:
                row = conn.execute(
                    f"SELECT {', '.join(cols)} FROM value_features_daily WHERE ticker = ? AND date <= ? ORDER BY date DESC LIMIT 1",
                    [ticker, signal_date],
                ).fetchone()
                if row:
                    val = {c: normalize_scalar(v) for c, v in zip(cols, row)}
                    out["value"] = val
                    out["sector_relative"] = {
                        k: v for k, v in val.items()
                        if "sector" in k.lower() or "relative" in k.lower() or "percentile" in k.lower()
                    }
            except Exception:
                pass

    if has_table(conn, "agent_scores_daily"):
        cols = existing_cols(
            conn,
            "agent_scores_daily",
            [
                "rank", "score", "score_pts", "normalized_score", "action", "reason",
                "score_band", "risk_level", "classification", "theme", "bucket",
            ],
        )
        if cols:
            try:
                row = conn.execute(
                    f"""
                    SELECT {', '.join(cols)}
                    FROM agent_scores_daily
                    WHERE ticker = ? AND agent_id = ? AND date <= ?
                    ORDER BY date DESC
                    LIMIT 1
                    """,
                    [ticker, tr.get("agent_id"), signal_date],
                ).fetchone()
                if row:
                    out["score"] = {c: normalize_scalar(v) for c, v in zip(cols, row)}
            except Exception:
                pass

    return out


def normalize_scalar(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (datetime, date)):
        return str(v)
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 6)
    return v


def quantiles(values: list[float]) -> dict[str, float | None]:
    vals = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not vals:
        return {"p10": None, "p25": None, "median": None, "p75": None, "p90": None}
    s = pd.Series(vals)
    return {
        "p10": pct(float(s.quantile(0.10))),
        "p25": pct(float(s.quantile(0.25))),
        "median": pct(float(s.quantile(0.50))),
        "p75": pct(float(s.quantile(0.75))),
        "p90": pct(float(s.quantile(0.90))),
    }


def summarize_agent(agent_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    agent = AGENT_BY_ID.get(agent_id, {"name": agent_id, "title": ""})
    n = len(rows)
    rets = [safe_float(r.get("realized_return_pct")) for r in rows]
    rets_valid = [r for r in rets if r is not None]
    wins = [r for r in rets_valid if r > 0]
    losses = [r for r in rets_valid if r < 0]
    pnls = [safe_float(r.get("realized_pnl_jpy"), 0.0) or 0.0 for r in rows]
    win_pnls = [p for p in pnls if p > 0]
    loss_pnls = [p for p in pnls if p < 0]
    mfe = [safe_float(r.get("mfe_pct")) for r in rows if safe_float(r.get("mfe_pct")) is not None]
    mae = [safe_float(r.get("mae_pct")) for r in rows if safe_float(r.get("mae_pct")) is not None]
    giveback = [safe_float(r.get("mfe_giveback_pct")) for r in rows if safe_float(r.get("mfe_giveback_pct")) is not None]
    holds = [safe_int(r.get("holding_days"), 0) for r in rows]

    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    payoff = abs(avg_win / avg_loss) if avg_loss else (0.0 if not avg_win else None)
    gross_profit = sum(win_pnls)
    gross_loss = abs(sum(loss_pnls))
    pf = gross_profit / gross_loss if gross_loss else (None if gross_profit else 0.0)

    pattern_counts = Counter(str(r.get("diagnostic_pattern") or "UNKNOWN") for r in rows)
    exit_counts = Counter(str(r.get("exit_reason_code") or "UNKNOWN") for r in rows)

    # Context failure buckets based on entry context.
    context_flags = Counter()
    for r in rows:
        c = r.get("entry_context") or {}
        f = c.get("feature") or {}
        fund = c.get("fundamental") or {}
        val = c.get("value") or {}

        ret20 = safe_float(f.get("return_20d_pct"))
        ret5 = safe_float(f.get("return_5d_pct"))
        rsi = safe_float(f.get("rsi_14"))
        vol = safe_float(f.get("volume_ratio_20d"))
        rp = safe_float(f.get("range_position_252d_0_1"))
        opm = safe_float(fund.get("operating_margin_pct"))
        roe = safe_float(fund.get("roe_pct"))
        per = safe_float(fund.get("per"))
        pbr = safe_float(fund.get("pbr"))

        if ret20 is not None and ret20 >= 50:
            context_flags["entry_after_extreme_20d_runup"] += 1
        if ret5 is not None and ret5 >= 20 and rsi is not None and rsi >= 75:
            context_flags["short_term_overheat_chase"] += 1
        if ret20 is not None and ret20 <= -25 and rsi is not None and rsi <= 25:
            context_flags["falling_knife_oversold"] += 1
        if vol is not None and vol >= 3 and abs(ret5 or 0) >= 10:
            context_flags["volume_climax_or_shock"] += 1
        if rp is not None and rp >= 0.95:
            context_flags["upper_range_chase"] += 1
        if rp is not None and rp <= 0.05:
            context_flags["structural_breakdown_zone"] += 1
        if opm is not None and opm < 0:
            context_flags["operating_loss_company"] += 1
        if roe is not None and roe < 5:
            context_flags["low_roe_company"] += 1
        if per is not None and per >= 80:
            context_flags["expensive_per"] += 1
        if pbr is not None and pbr >= 8:
            context_flags["expensive_pbr"] += 1
        if safe_float(val.get("value_trap_penalty")) is not None and safe_float(val.get("value_trap_penalty")) >= 0.2:
            context_flags["value_trap_penalty_high"] += 1

    return {
        "agent_id": agent_id,
        "agent_name": agent.get("name", agent_id),
        "agent_title": agent.get("title", ""),
        "trades": n,
        "valid_return_trades": len(rets_valid),
        "win_rate_pct": pct((len(wins) / len(rets_valid) * 100.0) if rets_valid else 0.0),
        "avg_return_pct": pct((sum(rets_valid) / len(rets_valid)) if rets_valid else 0.0),
        "median_return_pct": pct(float(pd.Series(rets_valid).median()) if rets_valid else 0.0),
        "avg_win_pct": pct(avg_win),
        "avg_loss_pct": pct(avg_loss),
        "payoff_ratio": None if payoff is None else round(float(payoff), 4),
        "profit_factor": None if pf is None else round(float(pf), 4),
        "total_pnl_jpy": round(sum(pnls), 0),
        "gross_profit_jpy": round(gross_profit, 0),
        "gross_loss_jpy": round(-gross_loss, 0),
        "avg_mfe_pct": pct((sum(mfe) / len(mfe)) if mfe else None),
        "avg_mae_pct": pct((sum(mae) / len(mae)) if mae else None),
        "avg_giveback_pct": pct((sum(giveback) / len(giveback)) if giveback else None),
        "median_holding_days": float(pd.Series(holds).median()) if holds else 0,
        "return_quantiles": quantiles(rets_valid),
        "mfe_quantiles": quantiles(mfe),
        "mae_quantiles": quantiles(mae),
        "giveback_quantiles": quantiles(giveback),
        "exit_reasons": dict(exit_counts.most_common()),
        "patterns": dict(pattern_counts.most_common()),
        "context_flags": dict(context_flags.most_common()),
    }


def build_payload(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    effective_run_id, run_meta = resolve_effective_run_id(conn, RUN_ID_REQUESTED)
    trades_df, fetch_meta = fetch_trades(conn, effective_run_id)

    if trades_df.empty and FAIL_IF_NO_TRADES:
        raise SystemExit(
            f"Trade diagnostics has no closed trades for requested_run_id={RUN_ID_REQUESTED!r}, "
            f"effective_run_id={effective_run_id!r}."
        )

    trade_rows: list[dict[str, Any]] = []
    for raw in trades_df.to_dict("records"):
        tr = compute_trade_metrics(conn, raw)
        tr["entry_context"] = fetch_context_for_trade(conn, tr)
        trade_rows.append(tr)

    # Hard cap output rows after metrics/context are computed.  Keep the latest
    # rows by exit date, then agent/ticker order.
    if MAX_TRADE_ROWS > 0 and len(trade_rows) > MAX_TRADE_ROWS:
        trade_rows = sorted(
            trade_rows,
            key=lambda r: (str(r.get("exit_date") or ""), str(r.get("agent_id") or ""), str(r.get("ticker") or "")),
        )[-MAX_TRADE_ROWS:]

    by_agent: dict[str, list[dict[str, Any]]] = {a["agent_id"]: [] for a in OFFICIAL_AGENTS}
    for r in trade_rows:
        by_agent.setdefault(str(r.get("agent_id")), []).append(r)

    summaries = {aid: summarize_agent(aid, rows) for aid, rows in by_agent.items() if aid}
    official_summaries = {a["agent_id"]: summaries.get(a["agent_id"], summarize_agent(a["agent_id"], [])) for a in OFFICIAL_AGENTS}

    quality = validate_quality(trade_rows, run_meta, fetch_meta, official_summaries)

    return {
        "schema_version": SCHEMA_VERSION,
        # v1 alias remains for old one-line workflow validators.
        "compat_schema_version": "neon_tokyo_ai_arena_trade_diagnostics_v1",
        "generated_at": utc_now(),
        "requested_run_id": RUN_ID_REQUESTED,
        "effective_run_id": effective_run_id,
        "run_resolution": run_meta,
        "counts": {
            "closed_trades": len(trade_rows),
            "raw_trade_rows": fetch_meta.get("raw_trade_rows", 0),
            "deduplicated_rows": fetch_meta.get("deduplicated_rows", len(trade_rows)),
            "duplicates_removed": fetch_meta.get("duplicates_removed", 0),
            "agents_with_closed_trades": sum(1 for rows in by_agent.values() if rows),
            "official_agents": len(OFFICIAL_AGENTS),
            "agent_summaries": len(official_summaries),
            "exported_compact_trade_rows": len(trade_rows),
        },
        "quality": quality,
        "agent_summaries": official_summaries,
        "top_tables": build_top_tables(trade_rows),
        "trades": trade_rows,
    }


def validate_quality(
    trades: list[dict[str, Any]],
    run_meta: dict[str, Any],
    fetch_meta: dict[str, Any],
    summaries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    def issue(code: str, message: str, severity: str = "error") -> None:
        target = issues if severity == "error" else warnings
        target.append({"code": code, "message": message, "severity": severity})

    if run_meta.get("fallback_used"):
        issue("FALLBACK_USED", "Fallback to all trades was used. Analysis would mix runs.", "error")
    if RUN_ID_REQUESTED.lower() == "display" and not run_meta.get("display_resolved"):
        issue("DISPLAY_NOT_RESOLVED", "display run_id was not resolved to a concrete run_id.", "error")
    if fetch_meta.get("duplicates_removed", 0) > 0:
        warnings.append({
            "code": "DUPLICATES_REMOVED",
            "message": f"Removed {fetch_meta.get('duplicates_removed')} duplicate trade rows using {fetch_meta.get('dedupe_key')}.",
            "severity": "warning",
        })
    if not trades:
        issue("NO_CLOSED_TRADES", "No closed trades were found for the effective run_id.", "error" if FAIL_IF_NO_TRADES else "warning")

    n = len(trades)
    if n:
        zero_returns = sum(1 for r in trades if abs(safe_float(r.get("realized_return_pct"), 0.0) or 0.0) < 1e-12)
        zero_mfe = sum(1 for r in trades if abs(safe_float(r.get("mfe_pct"), 0.0) or 0.0) < 1e-12)
        zero_mae = sum(1 for r in trades if abs(safe_float(r.get("mae_pct"), 0.0) or 0.0) < 1e-12)
        unknown_exit = sum(1 for r in trades if str(r.get("exit_reason_code") or "UNKNOWN").upper() == "UNKNOWN")
        missing_context = sum(1 for r in trades if not r.get("entry_context"))

        if zero_returns == n:
            issue("ALL_RETURNS_ZERO", "All realized_return_pct values are zero after recomputation.", "error")
        if zero_mfe == n:
            issue("ALL_MFE_ZERO", "All MFE values are zero after price-path recomputation.", "error")
        if zero_mae == n:
            issue("ALL_MAE_ZERO", "All MAE values are zero after price-path recomputation.", "error")
        if unknown_exit == n:
            issue("ALL_EXIT_REASONS_UNKNOWN", "All exit reasons are UNKNOWN.", "error")
        elif unknown_exit / n > 0.2:
            issue("MANY_UNKNOWN_EXIT_REASONS", f"{unknown_exit}/{n} trades have UNKNOWN exit reason.", "warning")
        if missing_context / n > 0.5:
            issue("ENTRY_CONTEXT_LOW_COVERAGE", f"{missing_context}/{n} trades have no entry context.", "warning")

    for aid, s in summaries.items():
        if aid in AGENT_BY_ID and int(s.get("trades") or 0) == 0:
            warnings.append({
                "code": "AGENT_HAS_ZERO_CLOSED_TRADES",
                "message": f"{AGENT_BY_ID[aid]['name']} / {aid} has zero closed trades in this run.",
                "severity": "warning",
            })

    status = "ok"
    if issues:
        status = "failed"
    elif warnings:
        status = "warning"

    return {
        "status": status,
        "fail_on_data_quality": FAIL_ON_DATA_QUALITY,
        "issues": issues,
        "warnings": warnings,
    }


def build_top_tables(trades: list[dict[str, Any]]) -> dict[str, Any]:
    def sort_key_ret(r: dict[str, Any]) -> float:
        return safe_float(r.get("realized_return_pct"), 0.0) or 0.0

    def sort_key_pnl(r: dict[str, Any]) -> float:
        return safe_float(r.get("realized_pnl_jpy"), 0.0) or 0.0

    def sort_key_giveback(r: dict[str, Any]) -> float:
        return safe_float(r.get("mfe_giveback_pct"), 0.0) or 0.0

    def sort_key_mae(r: dict[str, Any]) -> float:
        return safe_float(r.get("mae_pct"), 0.0) or 0.0

    return {
        "best_trades": compact_trades(sorted(trades, key=sort_key_pnl, reverse=True)[:TOP_N]),
        "worst_trades": compact_trades(sorted(trades, key=sort_key_pnl)[:TOP_N]),
        "largest_mfe_givebacks": compact_trades(sorted(trades, key=sort_key_giveback, reverse=True)[:TOP_N]),
        "deepest_adverse_trades": compact_trades(sorted(trades, key=sort_key_mae)[:TOP_N]),
    }


def compact_trades(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = [
        "agent_id", "ticker", "name", "entry_date", "exit_date", "realized_return_pct",
        "realized_pnl_jpy", "holding_days", "mfe_pct", "mae_pct",
        "mfe_giveback_pct", "exit_reason_code", "diagnostic_pattern",
    ]
    out = []
    for r in rows:
        d = {k: normalize_scalar(r.get(k)) for k in keys}
        out.append(d)
    return out


def markdown_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Agent | Ticker | Name | Entry | Exit | Ret | PnL | Hold | MFE | MAE | Giveback | Exit | Pattern |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in rows:
        agent_id = str(r.get("agent_id") or "")
        agent_name = AGENT_BY_ID.get(agent_id, {}).get("name", agent_id)
        lines.append(
            f"| {agent_name} | `{r.get('ticker')}` | {r.get('name') or ''} | "
            f"{r.get('entry_date') or '-'} | {r.get('exit_date') or '-'} | "
            f"{pct_label(safe_float(r.get('realized_return_pct')))} | {yen(safe_float(r.get('realized_pnl_jpy')))} | "
            f"{safe_int(r.get('holding_days'))} | {pct_label(safe_float(r.get('mfe_pct')))} | "
            f"{pct_label(safe_float(r.get('mae_pct')))} | {pct_label(safe_float(r.get('mfe_giveback_pct')))} | "
            f"{r.get('exit_reason_code') or 'UNKNOWN'} | {r.get('diagnostic_pattern') or '-'} |"
        )
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Neon Tokyo AI Arena Trade Diagnostics")
    lines.append("")
    lines.append(f"Generated: `{payload.get('generated_at')}`")
    lines.append(f"Requested Run ID: `{payload.get('requested_run_id')}`")
    lines.append(f"Effective Run ID: `{payload.get('effective_run_id')}`")
    lines.append(f"Schema: `{payload.get('schema_version')}`")
    lines.append("")
    lines.append("> Purpose: high-integrity agent-by-agent win/loss diagnosis and rule-improvement source data.")
    lines.append("")
    counts = payload.get("counts") or {}
    quality = payload.get("quality") or {}
    lines.append("## Dataset Summary")
    lines.append("")
    lines.append(f"- Closed trades: **{counts.get('closed_trades', 0)}**")
    lines.append(f"- Raw trade rows: **{counts.get('raw_trade_rows', 0)}**")
    lines.append(f"- Duplicates removed: **{counts.get('duplicates_removed', 0)}**")
    lines.append(f"- Agents with closed trades: **{counts.get('agents_with_closed_trades', 0)}**")
    lines.append(f"- Official agents: **{counts.get('official_agents', 0)}**")
    lines.append(f"- Agent summaries: **{counts.get('agent_summaries', 0)}**")
    lines.append(f"- Quality status: **{quality.get('status', 'unknown')}**")
    lines.append("")
    run_resolution = payload.get("run_resolution") or {}
    lines.append("## Run Resolution")
    lines.append("")
    lines.append(f"- Requested run_id: `{run_resolution.get('requested_run_id')}`")
    lines.append(f"- Effective run_id: `{run_resolution.get('effective_run_id')}`")
    lines.append(f"- Display resolved: `{run_resolution.get('display_resolved')}`")
    lines.append(f"- Used run_id filter: `{run_resolution.get('used_run_id_filter')}`")
    lines.append(f"- Fallback used: `{run_resolution.get('fallback_used')}`")
    for note in run_resolution.get("notes") or []:
        lines.append(f"- {note}")
    lines.append("")
    if quality.get("issues") or quality.get("warnings"):
        lines.append("## Data Quality Gate")
        lines.append("")
        for item in quality.get("issues") or []:
            lines.append(f"- ERROR `{item.get('code')}`: {item.get('message')}")
        for item in quality.get("warnings") or []:
            lines.append(f"- WARNING `{item.get('code')}`: {item.get('message')}")
        lines.append("")
    lines.append("## Agent Summary")
    lines.append("")
    lines.append("| Agent | Trades | Win | Avg Ret | Avg Win | Avg Loss | Payoff | PF | PnL | Avg MFE | Avg MAE | Avg Giveback | Top Patterns |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for aid in [a["agent_id"] for a in OFFICIAL_AGENTS]:
        s = payload.get("agent_summaries", {}).get(aid, {})
        pats = ", ".join(f"{k}:{v}" for k, v in list((s.get("patterns") or {}).items())[:4])
        lines.append(
            f"| {s.get('agent_name', aid)} / `{aid}` | {s.get('trades', 0)} | "
            f"{pct_label(safe_float(s.get('win_rate_pct')))} | {pct_label(safe_float(s.get('avg_return_pct')))} | "
            f"{pct_label(safe_float(s.get('avg_win_pct')))} | {pct_label(safe_float(s.get('avg_loss_pct')))} | "
            f"{s.get('payoff_ratio')} | {s.get('profit_factor')} | {yen(safe_float(s.get('total_pnl_jpy')))} | "
            f"{pct_label(safe_float(s.get('avg_mfe_pct')))} | {pct_label(safe_float(s.get('avg_mae_pct')))} | "
            f"{pct_label(safe_float(s.get('avg_giveback_pct')))} | {pats or '-'} |"
        )
    lines.append("")
    for aid in [a["agent_id"] for a in OFFICIAL_AGENTS]:
        s = payload.get("agent_summaries", {}).get(aid, {})
        lines.append(f"## {s.get('agent_name', aid)} / `{aid}`")
        title = AGENT_BY_ID.get(aid, {}).get("title")
        if title:
            lines.append("")
            lines.append(title)
        lines.append("")
        lines.append("### Key Metrics")
        lines.append("")
        lines.append(f"- Trades: **{s.get('trades', 0)}**, Win rate: **{pct_label(safe_float(s.get('win_rate_pct')))}**, Total PnL: **{yen(safe_float(s.get('total_pnl_jpy')))}**")
        lines.append(f"- Avg return: **{pct_label(safe_float(s.get('avg_return_pct')))}**, Avg win: **{pct_label(safe_float(s.get('avg_win_pct')))}**, Avg loss: **{pct_label(safe_float(s.get('avg_loss_pct')))}**")
        lines.append(f"- Payoff ratio: **{s.get('payoff_ratio')}**, Profit factor: **{s.get('profit_factor')}**")
        lines.append(f"- Avg MFE: **{pct_label(safe_float(s.get('avg_mfe_pct')))}**, Avg MAE: **{pct_label(safe_float(s.get('avg_mae_pct')))}**, Avg giveback: **{pct_label(safe_float(s.get('avg_giveback_pct')))}**")
        lines.append("")
        lines.append("### Exit Reasons")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.get("exit_reasons") or {}, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### Diagnostic Patterns")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.get("patterns") or {}, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### Entry Context Risk Flags")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s.get("context_flags") or {}, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
    top = payload.get("top_tables") or {}
    for title, key in [
        ("Worst Trades", "worst_trades"),
        ("Best Trades", "best_trades"),
        ("Largest MFE Givebacks", "largest_mfe_givebacks"),
        ("Deepest Adverse Trades", "deepest_adverse_trades"),
    ]:
        lines.append(f"## {title}")
        lines.append("")
        lines.extend(markdown_table(top.get(key) or []))
        lines.append("")
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> None:
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=normalize_scalar), encoding="utf-8")
    MD_OUT.write_text(render_markdown(payload), encoding="utf-8")


def main() -> int:
    conn = connect_db()
    payload = build_payload(conn)
    write_outputs(payload)

    quality = payload.get("quality") or {}
    print(f"Wrote {JSON_OUT.relative_to(ROOT) if JSON_OUT.is_relative_to(ROOT) else JSON_OUT}")
    print(f"Wrote {MD_OUT.relative_to(ROOT) if MD_OUT.is_relative_to(ROOT) else MD_OUT}")
    print(f"schema_version={payload.get('schema_version')}")
    print(f"requested_run_id={payload.get('requested_run_id')}")
    print(f"effective_run_id={payload.get('effective_run_id')}")
    print(f"closed_trades={payload.get('counts', {}).get('closed_trades')}")
    print(f"agents={payload.get('counts', {}).get('agent_summaries')}")
    print(f"quality_status={quality.get('status')}")

    if quality.get("status") == "failed" and FAIL_ON_DATA_QUALITY:
        for item in quality.get("issues") or []:
            print(f"::error::{item.get('code')}: {item.get('message')}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
