#!/usr/bin/env python3
"""
Neon Tokyo Signals - JP Data Coverage Review

Purpose
-------
This script audits the current data coverage of the Neon Tokyo / AI Arena
pipeline. It is intentionally read-only against DuckDB and only writes public
diagnostic reports under site/data/japan/ai-arena/diagnostics/.

Why this exists
---------------
AI Arena depends on several layers of data:

1. Universe
2. Daily prices
3. Daily technical features
4. Agent scores
5. Company master / fundamentals / valuation data
6. Arena simulation outputs: orders, trades, positions, equity curve
7. Static site JSON outputs

If any layer has poor coverage, some agents can silently stop trading.
This is especially important for agents such as SAGURI and HIZUMI, where
small-cap filters or valuation features can make buy conditions impossible.

Design principles
-----------------
- Never modifies DuckDB.
- Never fetches market data.
- Never calls GPT/API.
- Does not depend on Daily / Weekly page JSON.
- Produces both JSON and Markdown reports.
- Tolerates missing tables and missing columns.
- Uses dynamic column detection so schema evolution does not crash the review.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import duckdb
except Exception as exc:  # pragma: no cover - actionable runtime error
    raise SystemExit(
        "duckdb is required. Ensure requirements-render.txt includes duckdb."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "cache" / "neon_tokyo_jp.duckdb"
DEFAULT_OUT_DIR = ROOT / "site" / "data" / "japan" / "ai-arena" / "diagnostics"

CORE_AGENTS = [
    "daily_striker",
    "weekly_sage",
    "risk_sentinel",
    "discovery_scout",
    "contrarian_monk",
    "reversal_snapback",
    "value_mispricing",
]
AGENT_DISPLAY_NAMES = {
    "daily_striker": "KYOU",
    "weekly_sage": "NAGARE",
    "risk_sentinel": "MAMORU",
    "discovery_scout": "SAGURI",
    "contrarian_monk": "MATSU",
    "reversal_snapback": "KAESHI",
    "value_mispricing": "HIZUMI",
}

# JP equity ticker forms commonly seen in the project:
# - 5803.T
# - 141A.T
# - 285A.T
JP_TICKER_RE = re.compile(r"^[0-9]{3,4}[A-Z]?\.T$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def safe_round(value: Any, ndigits: int = 2) -> Optional[float]:
    if value is None:
        return None
    try:
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return round(float(value), ndigits)
    except Exception:
        return None


def pct(numerator: float, denominator: float, ndigits: int = 2) -> Optional[float]:
    if denominator in (0, 0.0) or denominator is None:
        return None
    return safe_round((float(numerator) / float(denominator)) * 100.0, ndigits)


def file_size_mb(path: Path) -> float:
    try:
        return round(path.stat().st_size / 1024 / 1024, 3)
    except FileNotFoundError:
        return 0.0


def read_json_if_exists(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Duck:
    """Small safe wrapper around DuckDB read-only queries."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.exists = db_path.exists()
        self.con = None
        self.tables: set[str] = set()
        self.columns: dict[str, set[str]] = {}

        if self.exists:
            self.con = duckdb.connect(str(db_path), read_only=True)
            self.tables = {r[0] for r in self.con.execute("SHOW TABLES").fetchall()}

    def close(self) -> None:
        if self.con is not None:
            self.con.close()

    def has_table(self, name: str) -> bool:
        return name in self.tables

    def cols(self, table: str) -> set[str]:
        if table in self.columns:
            return self.columns[table]
        if not self.has_table(table):
            self.columns[table] = set()
            return set()
        rows = self.con.execute(f"PRAGMA table_info('{table}')").fetchall()
        # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
        cols = {r[1] for r in rows}
        self.columns[table] = cols
        return cols

    def scalar(self, sql: str, params: Optional[list[Any]] = None, default: Any = None) -> Any:
        if self.con is None:
            return default
        try:
            row = self.con.execute(sql, params or []).fetchone()
            return row[0] if row else default
        except Exception:
            return default

    def rows(self, sql: str, params: Optional[list[Any]] = None) -> list[tuple]:
        if self.con is None:
            return []
        try:
            return self.con.execute(sql, params or []).fetchall()
        except Exception:
            return []


def list_site_data_files() -> dict:
    """Summarize repo-side public data size pressure."""
    site_data = ROOT / "site" / "data"
    files: list[Path] = []
    if site_data.exists():
        files = [p for p in site_data.rglob("*") if p.is_file()]

    largest = sorted(files, key=lambda p: p.stat().st_size, reverse=True)[:30]
    dated_price_json = sorted((ROOT / "site" / "data" / "prices-jp").glob("20??-??-??.json"))

    return {
        "site_data_exists": site_data.exists(),
        "site_data_file_count": len(files),
        "site_data_total_mb": safe_round(sum(p.stat().st_size for p in files) / 1024 / 1024, 3),
        "largest_files": [{"path": rel(p), "size_mb": file_size_mb(p)} for p in largest],
        "dated_prices_json_count": len(dated_price_json),
        "dated_prices_json_files": [rel(p) for p in dated_price_json[:50]],
        "prices_latest_size_mb": file_size_mb(ROOT / "site" / "data" / "prices-jp" / "latest.json"),
    }


def read_universe_csv_summary(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "path": rel(path)}

    rows = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception as exc:
        return {"exists": True, "path": rel(path), "read_error": str(exc)}

    ticker_col = "ticker" if rows and "ticker" in rows[0] else "symbol"
    tickers = [str(r.get(ticker_col, "")).strip() for r in rows if str(r.get(ticker_col, "")).strip()]
    suspicious = [t for t in tickers if not JP_TICKER_RE.match(t)]
    bucket_counts = Counter(str(r.get("bucket", "")).strip() or "(blank)" for r in rows)
    market_counts = Counter(str(r.get("market", "")).strip() or "(blank)" for r in rows)

    return {
        "exists": True,
        "path": rel(path),
        "rows": len(rows),
        "tickers": len(tickers),
        "unique_tickers": len(set(tickers)),
        "duplicate_tickers": len(tickers) - len(set(tickers)),
        "suspicious_ticker_count": len(suspicious),
        "suspicious_tickers_sample": suspicious[:30],
        "bucket_counts": dict(bucket_counts.most_common()),
        "market_counts": dict(market_counts.most_common(20)),
    }


def review_universe(db: Duck) -> dict:
    csv_summaries = {
        "jp_duckdb_trial_300": read_universe_csv_summary(ROOT / "data" / "universe" / "jp_duckdb_trial_300.csv"),
        "jp_index_universe": read_universe_csv_summary(ROOT / "data" / "universe" / "jp_index_universe.csv"),
        "legacy_universe_jp": read_universe_csv_summary(ROOT / "data" / "universe_jp.csv"),
    }

    result: dict[str, Any] = {
        "csv": csv_summaries,
        "duckdb": {"table_exists": db.has_table("universe_master")},
    }
    if not db.has_table("universe_master"):
        return result

    cols = db.cols("universe_master")
    ticker_col = "ticker" if "ticker" in cols else "symbol" if "symbol" in cols else None
    if not ticker_col:
        result["duckdb"]["error"] = "No ticker/symbol column found."
        return result

    total = db.scalar(f"SELECT COUNT(*) FROM universe_master", default=0)
    unique = db.scalar(f"SELECT COUNT(DISTINCT {ticker_col}) FROM universe_master", default=0)
    suspicious = []
    for (t,) in db.rows(f"SELECT DISTINCT {ticker_col} FROM universe_master WHERE {ticker_col} IS NOT NULL"):
        if not JP_TICKER_RE.match(str(t)):
            suspicious.append(str(t))

    result["duckdb"].update({
        "rows": total,
        "unique_tickers": unique,
        "duplicate_tickers": max(0, int(total or 0) - int(unique or 0)),
        "suspicious_ticker_count": len(suspicious),
        "suspicious_tickers_sample": suspicious[:30],
    })

    if "bucket" in cols:
        result["duckdb"]["bucket_counts"] = dict(db.rows(
            "SELECT COALESCE(bucket, '(blank)') AS bucket, COUNT(*) FROM universe_master GROUP BY 1 ORDER BY 2 DESC"
        ))
    if "source" in cols:
        result["duckdb"]["source_counts"] = dict(db.rows(
            "SELECT COALESCE(source, '(blank)') AS source, COUNT(*) FROM universe_master GROUP BY 1 ORDER BY 2 DESC"
        ))

    return result


def latest_date_expr(table: str, cols: set[str]) -> Optional[str]:
    for c in ["date", "trade_date", "score_date", "as_of_date"]:
        if c in cols:
            return c
    return None


def review_prices(db: Duck, stale_days: int, min_bars: int) -> dict:
    table = "prices_daily"
    result: dict[str, Any] = {"table_exists": db.has_table(table)}
    if not db.has_table(table):
        return result

    cols = db.cols(table)
    date_col = latest_date_expr(table, cols)
    ticker_col = "ticker" if "ticker" in cols else "symbol" if "symbol" in cols else None
    if not ticker_col or not date_col:
        result["error"] = "prices_daily lacks ticker/symbol or date column."
        return result

    total_rows = db.scalar(f"SELECT COUNT(*) FROM {table}", default=0)
    unique_symbols = db.scalar(f"SELECT COUNT(DISTINCT {ticker_col}) FROM {table}", default=0)
    min_date = db.scalar(f"SELECT MIN({date_col}) FROM {table}")
    max_date = db.scalar(f"SELECT MAX({date_col}) FROM {table}")

    result.update({
        "rows": total_rows,
        "unique_symbols": unique_symbols,
        "min_date": str(min_date) if min_date is not None else None,
        "max_date": str(max_date) if max_date is not None else None,
    })

    # Per-symbol recency and bar coverage.
    per_symbol = db.rows(f"""
        SELECT
          {ticker_col} AS ticker,
          COUNT(*) AS bars,
          MAX({date_col}) AS latest_date
        FROM {table}
        GROUP BY 1
    """)
    stale = []
    insufficient = []
    if max_date is not None:
        for ticker, bars, latest in per_symbol:
            if int(bars or 0) < min_bars:
                insufficient.append({"ticker": ticker, "bars": int(bars or 0), "latest_date": str(latest)})
            # DuckDB date arithmetic is easier in SQL for exact counts.
        stale = [
            {"ticker": r[0], "bars": int(r[1]), "latest_date": str(r[2])}
            for r in db.rows(f"""
                SELECT {ticker_col}, COUNT(*) AS bars, MAX({date_col}) AS latest_date
                FROM {table}
                GROUP BY 1
                HAVING MAX({date_col}) < (SELECT MAX({date_col}) - INTERVAL {int(stale_days)} DAY FROM {table})
                ORDER BY latest_date ASC
                LIMIT 100
            """)
        ]

    result.update({
        "symbols_with_insufficient_bars": len(insufficient),
        "insufficient_bars_sample": insufficient[:50],
        "stale_symbols_count": len(stale),
        "stale_symbols_sample": stale[:50],
    })

    # OHLCV non-null coverage. Use only existing columns.
    non_null = {}
    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        if col in cols:
            nn = db.scalar(f"SELECT SUM(CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END) FROM {table}", default=0)
            non_null[col] = {"count": int(nn or 0), "coverage_pct": pct(nn or 0, total_rows or 0)}
    result["non_null_coverage"] = non_null

    if db.has_table("price_fetch_failures"):
        fcols = db.cols("price_fetch_failures")
        result["fetch_failures"] = {
            "rows": db.scalar("SELECT COUNT(*) FROM price_fetch_failures", default=0),
        }
        if "ticker" in fcols:
            result["fetch_failures"]["unique_tickers"] = db.scalar(
                "SELECT COUNT(DISTINCT ticker) FROM price_fetch_failures", default=0
            )
            result["fetch_failures"]["latest_sample"] = [
                dict(zip(["ticker", "reason"], r))
                for r in db.rows("""
                    SELECT ticker, COALESCE(error, reason, '') AS reason
                    FROM price_fetch_failures
                    ORDER BY 1
                    LIMIT 30
                """)
            ]

    return result


def review_features(db: Duck, min_symbols_expected: Optional[int] = None) -> dict:
    table = "features_daily"
    result: dict[str, Any] = {"table_exists": db.has_table(table)}
    if not db.has_table(table):
        return result

    cols = db.cols(table)
    date_col = latest_date_expr(table, cols)
    ticker_col = "ticker" if "ticker" in cols else "symbol" if "symbol" in cols else None
    if not ticker_col or not date_col:
        result["error"] = "features_daily lacks ticker/symbol or date column."
        return result

    rows = db.scalar(f"SELECT COUNT(*) FROM {table}", default=0)
    unique_symbols = db.scalar(f"SELECT COUNT(DISTINCT {ticker_col}) FROM {table}", default=0)
    max_date = db.scalar(f"SELECT MAX({date_col}) FROM {table}")

    result.update({
        "rows": rows,
        "unique_symbols": unique_symbols,
        "max_date": str(max_date) if max_date is not None else None,
    })

    if max_date is not None:
        latest_symbols = db.scalar(
            f"SELECT COUNT(DISTINCT {ticker_col}) FROM {table} WHERE {date_col} = (SELECT MAX({date_col}) FROM {table})",
            default=0,
        )
        result["latest_date_symbols"] = latest_symbols
        if min_symbols_expected:
            result["latest_date_symbol_coverage_vs_price_pct"] = pct(latest_symbols, min_symbols_expected)

    important_cols = [
        "return_1d_pct", "return_5d_pct", "return_20d_pct", "return_60d_pct",
        "volume_ratio_20d", "avg_traded_value_20d_jpy", "rsi_14",
        "range_position_252d_0_1", "liquidity_score", "volatility_20d_pct",
        "price_above_ma20", "price_above_ma50", "ma20", "ma50",
    ]
    non_null = {}
    for col in important_cols:
        if col in cols:
            nn = db.scalar(f"SELECT SUM(CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END) FROM {table}", default=0)
            non_null[col] = {"count": int(nn or 0), "coverage_pct": pct(nn or 0, rows or 0)}
    result["non_null_coverage"] = non_null

    return result


def review_agent_scores(db: Duck) -> dict:
    table = "agent_scores_daily"
    result: dict[str, Any] = {"table_exists": db.has_table(table)}
    if not db.has_table(table):
        return result

    cols = db.cols(table)
    ticker_col = "ticker" if "ticker" in cols else "symbol" if "symbol" in cols else None
    agent_col = "agent_id" if "agent_id" in cols else "agent" if "agent" in cols else None
    date_col = latest_date_expr(table, cols)
    score_col = "score" if "score" in cols else "agent_score" if "agent_score" in cols else None

    if not ticker_col or not agent_col:
        result["error"] = "agent_scores_daily lacks ticker/symbol or agent_id/agent column."
        return result

    rows = db.scalar(f"SELECT COUNT(*) FROM {table}", default=0)
    unique_symbols = db.scalar(f"SELECT COUNT(DISTINCT {ticker_col}) FROM {table}", default=0)
    unique_agents = db.scalar(f"SELECT COUNT(DISTINCT {agent_col}) FROM {table}", default=0)
    result.update({
        "rows": rows,
        "unique_symbols": unique_symbols,
        "unique_agents": unique_agents,
    })
    if date_col:
        max_date = db.scalar(f"SELECT MAX({date_col}) FROM {table}")
        result["max_date"] = str(max_date) if max_date is not None else None

    # Agent-level counts and score ranges.
    select_score = f"MAX({score_col}), AVG({score_col})" if score_col else "NULL, NULL"
    action_expr = "action" if "action" in cols else "decision" if "decision" in cols else None

    agent_rows = []
    for row in db.rows(f"""
        SELECT
          {agent_col} AS agent,
          COUNT(*) AS rows,
          COUNT(DISTINCT {ticker_col}) AS tickers,
          {select_score}
        FROM {table}
        GROUP BY 1
        ORDER BY 1
    """):
        agent, nrows, tickers, max_score, avg_score = row
        item = {
            "agent": str(agent).lower(),
            "rows": int(nrows or 0),
            "unique_tickers": int(tickers or 0),
            "max_score": safe_round(max_score, 4),
            "avg_score": safe_round(avg_score, 4),
        }
        if action_expr:
            actions = dict(db.rows(f"""
                SELECT COALESCE({action_expr}, '(blank)') AS action, COUNT(*)
                FROM {table}
                WHERE LOWER({agent_col}) = ?
                GROUP BY 1
                ORDER BY 2 DESC
            """, [str(agent).lower()]))
            item["action_counts"] = actions
        agent_rows.append(item)

    result["by_agent"] = agent_rows
    result["missing_core_agents"] = [a for a in CORE_AGENTS if a not in {x["agent"] for x in agent_rows}]
    return result


def review_company_and_fundamentals(db: Duck) -> dict:
    """Review company metadata and valuation/fundamental coverage.

    The project has used both fundamentals_latest and fundamentals_latest_jp.
    This audit checks both if present, because older/newer implementations may
    write different table names.
    """
    result: dict[str, Any] = {}

    # Choose a universe denominator.
    universe_total = None
    if db.has_table("universe_master"):
        ucols = db.cols("universe_master")
        ticker_col = "ticker" if "ticker" in ucols else "symbol" if "symbol" in ucols else None
        if ticker_col:
            universe_total = db.scalar(f"SELECT COUNT(DISTINCT {ticker_col}) FROM universe_master", default=0)

    for table in ["company_master_jp", "company_master"]:
        item = {"table_exists": db.has_table(table)}
        if db.has_table(table):
            cols = db.cols(table)
            ticker_col = "ticker" if "ticker" in cols else "symbol" if "symbol" in cols else None
            rows = db.scalar(f"SELECT COUNT(*) FROM {table}", default=0)
            item["rows"] = rows
            if ticker_col:
                item["unique_tickers"] = db.scalar(f"SELECT COUNT(DISTINCT {ticker_col}) FROM {table}", default=0)
                item["coverage_vs_universe_pct"] = pct(item["unique_tickers"], universe_total or 0)
            non_null = {}
            for col in ["name_en", "name_ja", "market", "sector", "industry", "description_en", "website"]:
                if col in cols:
                    nn = db.scalar(f"SELECT SUM(CASE WHEN {col} IS NOT NULL AND CAST({col} AS VARCHAR) <> '' THEN 1 ELSE 0 END) FROM {table}", default=0)
                    non_null[col] = {"count": int(nn or 0), "coverage_pct": pct(nn or 0, rows or 0)}
            item["non_null_coverage"] = non_null
        result[table] = item

    for table in ["fundamentals_latest_jp", "fundamentals_latest"]:
        item = {"table_exists": db.has_table(table)}
        if db.has_table(table):
            cols = db.cols(table)
            ticker_col = "ticker" if "ticker" in cols else "symbol" if "symbol" in cols else None
            rows = db.scalar(f"SELECT COUNT(*) FROM {table}", default=0)
            item["rows"] = rows
            if ticker_col:
                unique = db.scalar(f"SELECT COUNT(DISTINCT {ticker_col}) FROM {table}", default=0)
                item["unique_tickers"] = unique
                item["coverage_vs_universe_pct"] = pct(unique, universe_total or 0)

            metrics = [
                "market_cap_jpy", "market_cap", "per", "trailing_pe", "forward_pe",
                "pbr", "price_to_book", "psr", "price_to_sales",
                "roe_pct", "return_on_equity", "roa_pct", "operating_margin_pct",
                "revenue_jpy", "operating_profit_jpy", "net_income_jpy",
                "dividend_yield_pct", "equity_jpy",
            ]
            non_null = {}
            for col in metrics:
                if col in cols:
                    nn = db.scalar(f"SELECT SUM(CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END) FROM {table}", default=0)
                    non_null[col] = {"count": int(nn or 0), "coverage_pct": pct(nn or 0, rows or 0)}
            item["non_null_coverage"] = non_null

            sample_cols = [c for c in ["ticker", "symbol", "market_cap_jpy", "per", "pbr", "roe_pct", "psr", "dividend_yield_pct", "updated_at"] if c in cols]
            if sample_cols:
                order_col = "updated_at" if "updated_at" in cols else sample_cols[0]
                item["sample"] = [
                    dict(zip(sample_cols, r))
                    for r in db.rows(f"SELECT {', '.join(sample_cols)} FROM {table} ORDER BY {order_col} DESC NULLS LAST LIMIT 20")
                ]
        result[table] = item

    table = "value_features_daily"
    value_item = {"table_exists": db.has_table(table)}
    if db.has_table(table):
        cols = db.cols(table)
        ticker_col = "ticker" if "ticker" in cols else "symbol" if "symbol" in cols else None
        rows = db.scalar(f"SELECT COUNT(*) FROM {table}", default=0)
        value_item["rows"] = rows
        if ticker_col:
            value_item["unique_tickers"] = db.scalar(f"SELECT COUNT(DISTINCT {ticker_col}) FROM {table}", default=0)
            value_item["coverage_vs_universe_pct"] = pct(value_item["unique_tickers"], universe_total or 0)
        non_null = {}
        for col in ["valuation_score", "quality_score", "value_score", "roe_pct", "per", "pbr", "psr"]:
            if col in cols:
                nn = db.scalar(f"SELECT SUM(CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END) FROM {table}", default=0)
                non_null[col] = {"count": int(nn or 0), "coverage_pct": pct(nn or 0, rows or 0)}
        value_item["non_null_coverage"] = non_null
    result["value_features_daily"] = value_item

    return result


def review_arena(db: Duck) -> dict:
    result: dict[str, Any] = {}
    for table in [
        "arena_simulation_runs",
        "arena_display_runs",
        "arena_orders",
        "arena_open_positions",
        "arena_trades",
        "arena_equity_curve",
        "arena_yearly_rankings",
        "arena_monthly_rankings",
        "arena_trade_rankings",
        "agent_pick_notes_daily",
    ]:
        item = {"table_exists": db.has_table(table)}
        if db.has_table(table):
            cols = db.cols(table)
            item["rows"] = db.scalar(f"SELECT COUNT(*) FROM {table}", default=0)
            if "run_id" in cols:
                item["run_ids"] = [r[0] for r in db.rows(f"SELECT DISTINCT run_id FROM {table} ORDER BY 1 LIMIT 20")]
            if "agent_id" in cols:
                agent_rows = db.rows(f"""
                    SELECT LOWER(agent_id), COUNT(*)
                    FROM {table}
                    GROUP BY 1
                    ORDER BY 1
                """)
                item["by_agent_rows"] = dict(agent_rows)
            if table == "arena_orders":
                if "status" in cols:
                    item["status_counts"] = dict(db.rows(
                        "SELECT COALESCE(status, '(blank)'), COUNT(*) FROM arena_orders GROUP BY 1 ORDER BY 2 DESC"
                    ))
                if "side" in cols:
                    item["side_counts"] = dict(db.rows(
                        "SELECT COALESCE(side, '(blank)'), COUNT(*) FROM arena_orders GROUP BY 1 ORDER BY 2 DESC"
                    ))
            if table == "arena_trades" and "realized_return_pct" in cols:
                item["return_summary"] = {}
                for agent, n, avg_ret, max_ret, min_ret in db.rows("""
                    SELECT LOWER(agent_id), COUNT(*), AVG(realized_return_pct), MAX(realized_return_pct), MIN(realized_return_pct)
                    FROM arena_trades
                    GROUP BY 1
                    ORDER BY 1
                """):
                    item["return_summary"][agent] = {
                        "closed_trades": int(n or 0),
                        "avg_return_pct": safe_round(avg_ret, 2),
                        "best_return_pct": safe_round(max_ret, 2),
                        "worst_return_pct": safe_round(min_ret, 2),
                    }
            if table == "arena_equity_curve":
                if "date" in cols:
                    item["max_date"] = str(db.scalar("SELECT MAX(date) FROM arena_equity_curve"))
                if {"cash_jpy", "market_value_jpy", "portfolio_equity_jpy"}.issubset(cols):
                    mismatch = db.scalar("""
                        SELECT COUNT(*)
                        FROM arena_equity_curve
                        WHERE ABS(COALESCE(cash_jpy,0) + COALESCE(market_value_jpy,0) - COALESCE(portfolio_equity_jpy,0)) > 1
                    """, default=0)
                    item["cash_plus_market_value_mismatch_rows"] = int(mismatch or 0)
        result[table] = item

    return result


def review_site_outputs() -> dict:
    expected = [
        "site/data/japan/ai-arena/live/latest.json",
        "site/data/japan/ai-arena/ranking/latest.json",
        "site/data/japan/ai-arena/positions/latest.json",
        "site/data/japan/ai-arena/summary/latest.json",
        "site/data/japan/ai-arena/summary/2026/latest.json",
        "site/data/japan/ai-arena/signals/latest.json",
        "site/data/japan/ai-arena/agents/latest.json",
        "site/data/japan/ai-arena/log/latest.json",
        "site/data/japan/ai-arena/diagnostics/latest.json",
        "site/data/japan/ai-arena/diagnostics/latest.md",
        "site/japan/ai-arena/summary/index.html",
        "site/japan/ai-arena/signals/index.html",
        "site/japan/ai-arena/agents/index.html",
        "site/assets/ai_arena_summary_jp.css",
        "site/assets/ai_arena_signals_jp.css",
        "site/assets/ai_agent_profiles_jp.css",
    ]

    files = []
    for s in expected:
        p = ROOT / s
        item = {
            "path": s,
            "exists": p.exists(),
            "size_mb": file_size_mb(p),
        }
        if p.suffix == ".json" and p.exists():
            js = read_json_if_exists(p)
            item["valid_json"] = js is not None
            if isinstance(js, dict):
                item["schema_version"] = js.get("schema_version")
                item["generated_at"] = js.get("generated_at")
        files.append(item)

    return {
        "expected_outputs": files,
        "missing_outputs": [x["path"] for x in files if not x["exists"]],
    }


def build_warnings(report: dict, args: argparse.Namespace) -> list[dict]:
    warnings: list[dict] = []

    def warn(code: str, severity: str, message: str, detail: Any = None) -> None:
        warnings.append({"code": code, "severity": severity, "message": message, "detail": detail})

    if not report["duckdb"]["exists"]:
        warn("DUCKDB_MISSING", "critical", "DuckDB file was not found. Coverage review is incomplete.", report["duckdb"]["path"])
        return warnings

    universe_db = report.get("universe", {}).get("duckdb", {})
    u_count = int(universe_db.get("unique_tickers") or 0)
    if u_count == 0:
        warn("UNIVERSE_EMPTY", "critical", "universe_master has no tickers.")
    if universe_db.get("suspicious_ticker_count", 0) > 0:
        warn("SUSPICIOUS_UNIVERSE_TICKERS", "warning", "Universe contains suspicious ticker codes.", universe_db.get("suspicious_tickers_sample"))

    prices = report.get("prices", {})
    if not prices.get("table_exists"):
        warn("PRICES_TABLE_MISSING", "critical", "prices_daily table does not exist.")
    else:
        if prices.get("unique_symbols", 0) < max(1, u_count - 10):
            warn("LOW_PRICE_SYMBOL_COVERAGE", "warning", "prices_daily symbol coverage is lower than universe.", {
                "price_symbols": prices.get("unique_symbols"),
                "universe_tickers": u_count,
            })
        if prices.get("symbols_with_insufficient_bars", 0) > 0:
            warn("INSUFFICIENT_PRICE_BARS", "warning", "Some symbols have fewer bars than MIN_BARS_REQUIRED.", prices.get("insufficient_bars_sample", [])[:10])
        if prices.get("stale_symbols_count", 0) > 0:
            warn("STALE_PRICE_SYMBOLS", "warning", "Some symbols are stale versus latest price date.", prices.get("stale_symbols_sample", [])[:10])

    features = report.get("features", {})
    if not features.get("table_exists"):
        warn("FEATURES_TABLE_MISSING", "critical", "features_daily table does not exist.")
    else:
        latest_cov = features.get("latest_date_symbol_coverage_vs_price_pct")
        if latest_cov is not None and latest_cov < args.min_feature_latest_coverage_pct:
            warn("LOW_FEATURE_LATEST_COVERAGE", "warning", "Latest feature-date symbol coverage is low.", {
                "coverage_pct": latest_cov,
                "threshold_pct": args.min_feature_latest_coverage_pct,
            })

    scores = report.get("agent_scores", {})
    if not scores.get("table_exists"):
        warn("AGENT_SCORES_TABLE_MISSING", "critical", "agent_scores_daily table does not exist.")
    else:
        missing_agents = scores.get("missing_core_agents") or []
        if missing_agents:
            warn("MISSING_CORE_AGENTS_IN_SCORES", "critical", "Some core agents are missing from agent_scores_daily.", missing_agents)

    fundamentals = report.get("company_and_fundamentals", {})
    flj = fundamentals.get("fundamentals_latest_jp", {})
    fl = fundamentals.get("fundamentals_latest", {})
    if not flj.get("table_exists") and not fl.get("table_exists"):
        warn("FUNDAMENTALS_TABLE_MISSING", "warning", "No fundamentals_latest_jp/fundamentals_latest table found.")
    else:
        # Prefer JP table, fall back to older table.
        fitem = flj if flj.get("table_exists") else fl
        coverage = fitem.get("coverage_vs_universe_pct")
        if coverage is not None and coverage < args.min_fundamental_coverage_pct:
            warn("LOW_FUNDAMENTAL_ROW_COVERAGE", "warning", "Fundamental row coverage is low.", {
                "coverage_pct": coverage,
                "threshold_pct": args.min_fundamental_coverage_pct,
            })
        non_null = fitem.get("non_null_coverage", {})
        for metric in ["per", "pbr", "roe_pct", "market_cap_jpy"]:
            if metric in non_null and (non_null[metric].get("coverage_pct") or 0) < args.min_fundamental_coverage_pct:
                warn("LOW_FUNDAMENTAL_METRIC_COVERAGE", "warning", f"{metric} coverage is low.", non_null[metric])

    arena = report.get("arena", {})
    trades = arena.get("arena_trades", {})
    orders = arena.get("arena_orders", {})
    equity = arena.get("arena_equity_curve", {})
    if trades.get("table_exists") and "by_agent_rows" in trades:
        rows_by_agent = {str(k).lower(): int(v) for k, v in trades.get("by_agent_rows", {}).items()}
        for agent in CORE_AGENTS:
            if rows_by_agent.get(agent, 0) == 0:
                warn("AGENT_ZERO_CLOSED_TRADES", "info", f"{agent} has zero closed trades.", {"agent": agent})
    if orders.get("table_exists") and "by_agent_rows" in orders:
        rows_by_agent = {str(k).lower(): int(v) for k, v in orders.get("by_agent_rows", {}).items()}
        for agent in CORE_AGENTS:
            if rows_by_agent.get(agent, 0) == 0:
                warn("AGENT_ZERO_ORDERS", "warning", f"{agent} has zero orders.", {"agent": agent})
    if equity.get("cash_plus_market_value_mismatch_rows", 0) > 0:
        warn("EQUITY_ACCOUNTING_MISMATCH", "critical", "cash + market_value != portfolio_equity for some rows.", equity.get("cash_plus_market_value_mismatch_rows"))

    site = report.get("site_outputs", {})
    if site.get("missing_outputs"):
        warn("MISSING_SITE_OUTPUTS", "warning", "Some expected AI Arena site outputs are missing.", site["missing_outputs"])

    size = report.get("repo_artifacts", {})
    if (size.get("prices_latest_size_mb") or 0) > args.max_prices_latest_mb:
        warn("PRICES_LATEST_TOO_LARGE", "warning", "site/data/prices-jp/latest.json is larger than expected.", {
            "size_mb": size.get("prices_latest_size_mb"),
            "threshold_mb": args.max_prices_latest_mb,
        })
    if size.get("dated_prices_json_count", 0) > 0:
        warn("DATED_PRICE_JSON_REMAINING", "warning", "Dated price JSON files remain under site/data/prices-jp.", size.get("dated_prices_json_files"))

    return warnings


def format_metric(value: Any) -> str:
    if value is None:
        return "N/A"
    return str(value)


def markdown_report(report: dict) -> str:
    warnings = report.get("warnings", [])
    sev_order = {"critical": 0, "warning": 1, "info": 2}
    warnings_sorted = sorted(warnings, key=lambda x: (sev_order.get(x.get("severity"), 9), x.get("code", "")))

    lines = []
    lines.append("# Neon Tokyo Data Coverage Review")
    lines.append("")
    lines.append(f"Generated: {report.get('generated_at')}")
    lines.append(f"DuckDB: `{report.get('duckdb', {}).get('path')}`")
    lines.append(f"DuckDB exists: **{report.get('duckdb', {}).get('exists')}**")
    lines.append("")

    lines.append("## Executive Warnings")
    lines.append("")
    if warnings_sorted:
        lines.append("| Severity | Code | Message |")
        lines.append("|---|---|---|")
        for w in warnings_sorted:
            lines.append(f"| {w.get('severity')} | `{w.get('code')}` | {w.get('message')} |")
    else:
        lines.append("No warnings.")
    lines.append("")

    universe = report.get("universe", {})
    lines.append("## Universe")
    lines.append("")
    dbu = universe.get("duckdb", {})
    lines.append(f"- DuckDB rows: {format_metric(dbu.get('rows'))}")
    lines.append(f"- DuckDB unique tickers: {format_metric(dbu.get('unique_tickers'))}")
    lines.append(f"- Suspicious tickers: {format_metric(dbu.get('suspicious_ticker_count'))}")
    for name, item in universe.get("csv", {}).items():
        lines.append(f"- CSV `{name}`: exists={item.get('exists')} rows={item.get('rows')} suspicious={item.get('suspicious_ticker_count')}")
    lines.append("")

    prices = report.get("prices", {})
    lines.append("## Prices")
    lines.append("")
    lines.append(f"- Table exists: {prices.get('table_exists')}")
    lines.append(f"- Rows: {format_metric(prices.get('rows'))}")
    lines.append(f"- Unique symbols: {format_metric(prices.get('unique_symbols'))}")
    lines.append(f"- Date range: {format_metric(prices.get('min_date'))} → {format_metric(prices.get('max_date'))}")
    lines.append(f"- Insufficient bars symbols: {format_metric(prices.get('symbols_with_insufficient_bars'))}")
    lines.append(f"- Stale symbols: {format_metric(prices.get('stale_symbols_count'))}")
    lines.append("")

    features = report.get("features", {})
    lines.append("## Features")
    lines.append("")
    lines.append(f"- Table exists: {features.get('table_exists')}")
    lines.append(f"- Rows: {format_metric(features.get('rows'))}")
    lines.append(f"- Unique symbols: {format_metric(features.get('unique_symbols'))}")
    lines.append(f"- Latest date: {format_metric(features.get('max_date'))}")
    lines.append(f"- Latest date symbols: {format_metric(features.get('latest_date_symbols'))}")
    if features.get("non_null_coverage"):
        lines.append("")
        lines.append("| Feature | Coverage | Count |")
        lines.append("|---|---:|---:|")
        for col, item in features["non_null_coverage"].items():
            lines.append(f"| `{col}` | {format_metric(item.get('coverage_pct'))}% | {format_metric(item.get('count'))} |")
    lines.append("")

    scores = report.get("agent_scores", {})
    lines.append("## Agent Scores")
    lines.append("")
    lines.append(f"- Table exists: {scores.get('table_exists')}")
    lines.append(f"- Rows: {format_metric(scores.get('rows'))}")
    lines.append(f"- Unique agents: {format_metric(scores.get('unique_agents'))}")
    lines.append(f"- Latest date: {format_metric(scores.get('max_date'))}")
    if scores.get("by_agent"):
        lines.append("")
        lines.append("| Agent | Rows | Tickers | Max Score | Avg Score | Actions |")
        lines.append("|---|---:|---:|---:|---:|---|")
        for a in scores["by_agent"]:
            actions = ", ".join(f"{k}:{v}" for k, v in (a.get("action_counts") or {}).items())
            lines.append(
                f"| {AGENT_DISPLAY_NAMES.get(a.get('agent'), a.get('agent'))} / `{a.get('agent')}` | {a.get('rows')} | {a.get('unique_tickers')} | "
                f"{format_metric(a.get('max_score'))} | {format_metric(a.get('avg_score'))} | {actions} |"
            )
    lines.append("")

    fundamentals = report.get("company_and_fundamentals", {})
    lines.append("## Company / Fundamentals")
    lines.append("")
    for table in ["company_master_jp", "fundamentals_latest_jp", "fundamentals_latest", "value_features_daily"]:
        item = fundamentals.get(table, {})
        lines.append(f"### `{table}`")
        lines.append("")
        lines.append(f"- Exists: {item.get('table_exists')}")
        lines.append(f"- Rows: {format_metric(item.get('rows'))}")
        lines.append(f"- Unique tickers: {format_metric(item.get('unique_tickers'))}")
        lines.append(f"- Coverage vs universe: {format_metric(item.get('coverage_vs_universe_pct'))}%")
        non_null = item.get("non_null_coverage") or {}
        if non_null:
            lines.append("")
            lines.append("| Field | Coverage | Count |")
            lines.append("|---|---:|---:|")
            for col, cov in non_null.items():
                lines.append(f"| `{col}` | {format_metric(cov.get('coverage_pct'))}% | {format_metric(cov.get('count'))} |")
        lines.append("")

    arena = report.get("arena", {})
    lines.append("## Arena Simulation Tables")
    lines.append("")
    lines.append("| Table | Exists | Rows |")
    lines.append("|---|---:|---:|")
    for table, item in arena.items():
        lines.append(f"| `{table}` | {item.get('table_exists')} | {format_metric(item.get('rows'))} |")
    lines.append("")

    for table in ["arena_orders", "arena_trades", "arena_open_positions", "arena_equity_curve"]:
        item = arena.get(table, {})
        if item.get("by_agent_rows"):
            lines.append(f"### `{table}` by agent")
            lines.append("")
            lines.append("| Agent | Rows |")
            lines.append("|---|---:|")
            for agent, count in item["by_agent_rows"].items():
                lines.append(f"| {agent} | {count} |")
            lines.append("")

    site = report.get("site_outputs", {})
    lines.append("## Site Outputs")
    lines.append("")
    lines.append(f"- Missing outputs: {len(site.get('missing_outputs') or [])}")
    if site.get("missing_outputs"):
        for p in site["missing_outputs"]:
            lines.append(f"  - `{p}`")
    lines.append("")

    artifacts = report.get("repo_artifacts", {})
    lines.append("## Repo Artifact Size")
    lines.append("")
    lines.append(f"- site/data files: {format_metric(artifacts.get('site_data_file_count'))}")
    lines.append(f"- site/data total MB: {format_metric(artifacts.get('site_data_total_mb'))}")
    lines.append(f"- prices latest MB: {format_metric(artifacts.get('prices_latest_size_mb'))}")
    lines.append(f"- dated prices JSON count: {format_metric(artifacts.get('dated_prices_json_count'))}")
    lines.append("")
    if artifacts.get("largest_files"):
        lines.append("| Largest file | MB |")
        lines.append("|---|---:|")
        for f in artifacts["largest_files"][:15]:
            lines.append(f"| `{f['path']}` | {f['size_mb']} |")
    lines.append("")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review JP data coverage for Neon Tokyo AI Arena.")
    parser.add_argument("--db-path", default=os.environ.get("PRICE_DUCKDB_PATH", str(DEFAULT_DB_PATH)))
    parser.add_argument("--out-dir", default=os.environ.get("DATA_COVERAGE_OUT_DIR", str(DEFAULT_OUT_DIR)))
    parser.add_argument("--min-bars", type=int, default=int(os.environ.get("MIN_BARS_REQUIRED", "60")))
    parser.add_argument("--stale-days", type=int, default=int(os.environ.get("STALE_PRICE_DAYS", "5")))
    parser.add_argument("--min-feature-latest-coverage-pct", type=float, default=float(os.environ.get("MIN_FEATURE_LATEST_COVERAGE_PCT", "90")))
    parser.add_argument("--min-fundamental-coverage-pct", type=float, default=float(os.environ.get("MIN_FUNDAMENTAL_COVERAGE_PCT", "50")))
    parser.add_argument("--max-prices-latest-mb", type=float, default=float(os.environ.get("MAX_PRICES_LATEST_MB", "5")))
    parser.add_argument("--fail-on-critical", action="store_true", default=os.environ.get("FAIL_ON_CRITICAL", "false").lower() == "true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    db = Duck(db_path)
    try:
        price_symbol_count = None
        report: dict[str, Any] = {
            "schema_version": "neon_tokyo_data_coverage_review_v1",
            "generated_at": utc_now_iso(),
            "duckdb": {
                "path": rel(db_path),
                "exists": db.exists,
                "table_count": len(db.tables),
                "tables": sorted(db.tables),
            },
            "config": {
                "min_bars": args.min_bars,
                "stale_days": args.stale_days,
                "min_feature_latest_coverage_pct": args.min_feature_latest_coverage_pct,
                "min_fundamental_coverage_pct": args.min_fundamental_coverage_pct,
                "max_prices_latest_mb": args.max_prices_latest_mb,
            },
            "repo_artifacts": list_site_data_files(),
        }

        report["universe"] = review_universe(db)
        report["prices"] = review_prices(db, stale_days=args.stale_days, min_bars=args.min_bars)
        if isinstance(report.get("prices"), dict):
            price_symbol_count = report["prices"].get("unique_symbols")
        report["features"] = review_features(db, min_symbols_expected=price_symbol_count)
        report["agent_scores"] = review_agent_scores(db)
        report["company_and_fundamentals"] = review_company_and_fundamentals(db)
        report["arena"] = review_arena(db)
        report["site_outputs"] = review_site_outputs()
        report["warnings"] = build_warnings(report, args)

        json_path = out_dir / "data-coverage-latest.json"
        md_path = out_dir / "data-coverage-latest.md"
        write_json(json_path, report)
        write_text(md_path, markdown_report(report))

        # Backward-friendly aliases that are easy to open in GitHub/Vercel.
        write_json(out_dir / "latest-data-coverage.json", report)
        write_text(out_dir / "latest-data-coverage.md", markdown_report(report))

        print(f"Wrote {rel(json_path)}")
        print(f"Wrote {rel(md_path)}")
        print(f"Warnings: {len(report['warnings'])}")
        for w in report["warnings"][:20]:
            print(f"- {w['severity']} {w['code']}: {w['message']}")

        if args.fail_on_critical and any(w.get("severity") == "critical" for w in report["warnings"]):
            print("Critical warnings found and fail-on-critical is enabled.", file=sys.stderr)
            return 2

        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
