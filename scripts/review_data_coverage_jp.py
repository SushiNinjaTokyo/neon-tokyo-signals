#!/usr/bin/env python3
"""
Neon Tokyo AI Arena - JP Data Coverage Review

Purpose
-------
This script audits the current Neon Tokyo AI Arena data pipeline.

It checks:
- JP universe coverage
- price data coverage
- feature data coverage
- agent score coverage
- fundamentals / value-feature coverage
- AI Arena simulation table coverage
- site output existence
- generated artifact size
- canonical DuckDB build metadata

Important design note
---------------------
The canonical DuckDB should be restored from the GitHub Release asset before this
script runs. This script does not fetch prices, fundamentals, or rebuild the arena.
It only reviews the DB and generated site artifacts that already exist.

Expected DB path:
  data/cache/neon_tokyo_jp.duckdb

Outputs:
  site/data/japan/ai-arena/diagnostics/data-coverage-latest.json
  site/data/japan/ai-arena/diagnostics/data-coverage-latest.md
  site/data/japan/ai-arena/diagnostics/latest-data-coverage.json
  site/data/japan/ai-arena/diagnostics/latest-data-coverage.md

This file is intentionally defensive:
- Missing tables do not crash the script.
- Missing files do not crash the script.
- DuckDB datetime/date/Decimal/NaN values are normalized before JSON output.
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import duckdb
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"duckdb import failed: {exc}")


# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", "site"))
DB_PATH = Path(os.getenv("PRICE_DUCKDB_PATH", "data/cache/neon_tokyo_jp.duckdb"))

REPORT_DIR = OUT_DIR / "data" / "japan" / "ai-arena" / "diagnostics"
REPORT_JSON = REPORT_DIR / "data-coverage-latest.json"
REPORT_MD = REPORT_DIR / "data-coverage-latest.md"
REPORT_JSON_ALIAS = REPORT_DIR / "latest-data-coverage.json"
REPORT_MD_ALIAS = REPORT_DIR / "latest-data-coverage.md"

MIN_BARS_REQUIRED = int(os.getenv("MIN_BARS_REQUIRED", "60"))
STALE_PRICE_DAYS = int(os.getenv("STALE_PRICE_DAYS", "5"))
MIN_FUNDAMENTAL_COVERAGE_PCT = float(os.getenv("MIN_FUNDAMENTAL_COVERAGE_PCT", "50"))
EXPECTED_AGENT_COUNT = int(os.getenv("AI_ARENA_EXPECTED_AGENT_COUNT", "7"))
MIN_AGENT_SCORE_DATE_COUNT = int(os.getenv("MIN_AGENT_SCORE_DATE_COUNT", "2"))
MIN_ARENA_ORDERS_FOR_LIVE_RUN = int(os.getenv("MIN_ARENA_ORDERS_FOR_LIVE_RUN", "1"))
MIN_VALUE_FEATURE_DATE_COUNT = int(os.getenv("MIN_VALUE_FEATURE_DATE_COUNT", "2"))

SCHEMA_VERSION = "neon_tokyo_data_coverage_review_v2"

CORE_AGENTS = {
    "daily_striker": "KYOU",
    "weekly_sage": "NAGARE",
    "risk_sentinel": "MAMORU",
    "discovery_scout": "SAGURI",
    "contrarian_monk": "MATSU",
    "reversal_snapback": "KAESHI",
    "value_mispricing": "HIZUMI",
}

# Old uppercase/internal names that may still appear in older output.
AGENT_ALIASES = {
    "DAILY_STRIKER": "daily_striker",
    "WEEKLY_SAGE": "weekly_sage",
    "RISK_SENTINEL": "risk_sentinel",
    "DISCOVERY_SCOUT": "discovery_scout",
    "CONTRARIAN_MONK": "contrarian_monk",
    "REVERSAL_SNAPBACK": "reversal_snapback",
    "VALUE_MISPRICING": "value_mispricing",
    "KYOU": "daily_striker",
    "NAGARE": "weekly_sage",
    "MAMORU": "risk_sentinel",
    "SAGURI": "discovery_scout",
    "MATSU": "contrarian_monk",
    "KAESHI": "reversal_snapback",
    "HIZUMI": "value_mispricing",
}

PRICE_FIELDS = ["open", "high", "low", "close", "volume"]
FEATURE_FIELDS = [
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
FUNDAMENTAL_FIELDS = [
    "market_cap_jpy",
    "per",
    "pbr",
    "psr",
    "roe_pct",
    "roa_pct",
    "operating_margin_pct",
    "dividend_yield_pct",
]
ARENA_TABLES = [
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
]
SITE_OUTPUTS = [
    "site/data/japan/ai-arena/live/latest.json",
    "site/data/japan/ai-arena/ranking/latest.json",
    "site/data/japan/ai-arena/summary/latest.json",
    "site/data/japan/ai-arena/signals/latest.json",
    "site/japan/ai-arena/summary/index.html",
    "site/japan/ai-arena/signals/index.html",
    "site/japan/ai-arena/agents/index.html",
]


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.relative_to(ROOT).as_posix()
    except Exception:
        return p.as_posix()


def add_warning(
    warnings: List[Dict[str, Any]],
    severity: str,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    item: Dict[str, Any] = {
        "severity": severity,
        "code": code,
        "message": message,
    }
    if details:
        item["details"] = details
    warnings.append(item)


def json_safe(value: Any) -> Any:
    """
    Convert DuckDB / pandas / Python objects into JSON-serializable values.

    Coverage review may include:
    - datetime/date from DuckDB TIMESTAMP columns
    - Decimal-like numeric values
    - NaN / Infinity from pandas or calculations
    - sets/tuples
    - numpy scalar / pandas scalar objects
    """
    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]

    # numpy scalar / pandas scalar support without importing numpy/pandas.
    if hasattr(value, "item"):
        try:
            return json_safe(value.item())
        except Exception:
            pass

    return value


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_obj = json_safe(obj)
    path.write_text(
        json.dumps(safe_obj, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )


def pct(numer: Optional[float], denom: Optional[float]) -> Optional[float]:
    if denom in (None, 0):
        return None
    if numer is None:
        return None
    return round(float(numer) / float(denom) * 100.0, 3)


def mb(size_bytes: int) -> float:
    return round(size_bytes / 1024 / 1024, 3)


def is_suspicious_ticker(ticker: str) -> bool:
    """
    Japanese listed equities should normally be:
    - 4 digits + .T
    - 3 digits + A + .T for recent TSE codes
    - market pulse ETFs are also 4 digits + .T

    This check is intentionally conservative and only flags obvious anomalies.
    """
    t = str(ticker or "").strip()
    if not t:
        return True
    if not t.endswith(".T"):
        return True
    body = t[:-2]
    if re.fullmatch(r"\d{4}", body):
        return False
    if re.fullmatch(r"\d{3}A", body):
        return False
    return True


# ---------------------------------------------------------------------------
# DuckDB helpers
# ---------------------------------------------------------------------------

class Db:
    def __init__(self, path: Path):
        self.path = path
        self.exists = path.exists()
        self.con: Optional[duckdb.DuckDBPyConnection] = None
        self.tables: set[str] = set()

    def __enter__(self) -> "Db":
        if self.exists:
            self.con = duckdb.connect(str(self.path), read_only=True)
            self.tables = {r[0] for r in self.con.execute("SHOW TABLES").fetchall()}
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.con is not None:
            self.con.close()

    def table_exists(self, table: str) -> bool:
        return table in self.tables

    def q1(self, sql: str, params: Optional[List[Any]] = None, default: Any = None) -> Any:
        if self.con is None:
            return default
        try:
            row = self.con.execute(sql, params or []).fetchone()
            if row is None:
                return default
            return row[0]
        except Exception:
            return default

    def qall(self, sql: str, params: Optional[List[Any]] = None) -> List[Tuple[Any, ...]]:
        if self.con is None:
            return []
        try:
            return self.con.execute(sql, params or []).fetchall()
        except Exception:
            return []

    def columns(self, table: str) -> List[str]:
        if not self.table_exists(table) or self.con is None:
            return []
        try:
            return [r[1] for r in self.con.execute(f"PRAGMA table_info('{table}')").fetchall()]
        except Exception:
            return []


def choose_col(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    s = set(columns)
    for c in candidates:
        if c in s:
            return c
    return None


def count_non_null(db: Db, table: str, column: str) -> int:
    return int(db.q1(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NOT NULL", default=0) or 0)


def table_count(db: Db, table: str) -> Optional[int]:
    if not db.table_exists(table):
        return None
    return int(db.q1(f"SELECT COUNT(*) FROM {table}", default=0) or 0)


def unique_count(db: Db, table: str, col_candidates: Iterable[str]) -> Optional[int]:
    if not db.table_exists(table):
        return None
    col = choose_col(db.columns(table), col_candidates)
    if not col:
        return None
    return int(db.q1(f"SELECT COUNT(DISTINCT {col}) FROM {table}", default=0) or 0)


# ---------------------------------------------------------------------------
# Review sections
# ---------------------------------------------------------------------------

def review_duckdb_metadata(db: Db) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "db_path": rel(db.path),
        "exists": db.exists,
        "size_mb": mb(db.path.stat().st_size) if db.exists else None,
        "metadata_table_exists": db.table_exists("duckdb_build_metadata"),
        "metadata": {},
    }

    if db.table_exists("duckdb_build_metadata"):
        rows = db.qall(
            """
            SELECT key, value, updated_at
            FROM duckdb_build_metadata
            ORDER BY key
            """
        )
        meta: Dict[str, Any] = {}
        for key, value, updated_at in rows:
            meta[str(key)] = {
                "value": value,
                "updated_at": updated_at,
            }
        result["metadata"] = meta

    return result


def read_csv_rows(path: Path) -> Tuple[bool, int, int]:
    if not path.exists():
        return False, 0, 0

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return True, 0, 0

    suspicious = 0
    for row in rows:
        ticker = (
            row.get("ticker")
            or row.get("symbol")
            or row.get("code")
            or row.get("Ticker")
            or row.get("Symbol")
            or ""
        )
        # If the CSV stores code without .T, avoid false-positive for index source.
        if ticker and not str(ticker).endswith(".T"):
            t = f"{ticker}.T" if re.fullmatch(r"\d{4}|\d{3}A", str(ticker)) else str(ticker)
        else:
            t = str(ticker)
        if ticker and is_suspicious_ticker(t):
            suspicious += 1

    return True, len(rows), suspicious


def review_universe(db: Db, warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "duckdb": {
            "table_exists": db.table_exists("universe_master"),
            "rows": None,
            "unique_tickers": None,
            "suspicious_tickers": None,
            "bucket_distribution": {},
        },
        "csvs": {},
    }

    if db.table_exists("universe_master"):
        cols = db.columns("universe_master")
        ticker_col = choose_col(cols, ["ticker", "symbol"])
        bucket_col = choose_col(cols, ["bucket", "universe_bucket", "segment"])

        result["duckdb"]["rows"] = table_count(db, "universe_master")
        if ticker_col:
            result["duckdb"]["unique_tickers"] = unique_count(db, "universe_master", [ticker_col])
            tickers = [r[0] for r in db.qall(f"SELECT DISTINCT {ticker_col} FROM universe_master")]
            suspicious = [t for t in tickers if is_suspicious_ticker(str(t))]
            result["duckdb"]["suspicious_tickers"] = len(suspicious)
            result["duckdb"]["suspicious_examples"] = suspicious[:20]

            if suspicious:
                add_warning(
                    warnings,
                    "warning",
                    "SUSPICIOUS_UNIVERSE_TICKERS",
                    f"Universe has {len(suspicious)} suspicious tickers.",
                    {"examples": suspicious[:20]},
                )

        if bucket_col:
            result["duckdb"]["bucket_distribution"] = {
                str(k): int(v)
                for k, v in db.qall(
                    f"SELECT {bucket_col}, COUNT(*) FROM universe_master GROUP BY {bucket_col} ORDER BY {bucket_col}"
                )
            }

    csv_paths = {
        "jp_duckdb_trial_300": Path("data/universe/jp_duckdb_trial_300.csv"),
        "jp_index_universe": Path("data/universe/jp_index_universe.csv"),
        "legacy_universe_jp": Path("data/universe_jp.csv"),
    }
    for name, path in csv_paths.items():
        exists, rows, suspicious = read_csv_rows(path)
        result["csvs"][name] = {
            "path": rel(path),
            "exists": exists,
            "rows": rows,
            "suspicious": suspicious,
        }
        if suspicious:
            add_warning(
                warnings,
                "warning",
                "SUSPICIOUS_UNIVERSE_CSV_TICKERS",
                f"CSV {name} has suspicious ticker rows.",
                {"path": rel(path), "suspicious": suspicious},
            )

    return result


def review_prices(db: Db, warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    table = "prices_daily"
    result: Dict[str, Any] = {
        "table_exists": db.table_exists(table),
        "rows": None,
        "unique_symbols": None,
        "date_range": {"min": None, "max": None},
        "field_coverage": {},
        "insufficient_bars_symbols": 0,
        "stale_symbols": 0,
        "stale_examples": [],
    }

    if not db.table_exists(table):
        add_warning(warnings, "critical", "MISSING_PRICES_TABLE", "prices_daily table does not exist.")
        return result

    cols = db.columns(table)
    symbol_col = choose_col(cols, ["ticker", "symbol"])
    date_col = choose_col(cols, ["date", "trading_date"])

    result["rows"] = table_count(db, table)
    if symbol_col:
        result["unique_symbols"] = unique_count(db, table, [symbol_col])

    if date_col:
        min_date, max_date = db.qall(f"SELECT MIN({date_col}), MAX({date_col}) FROM {table}")[0]
        result["date_range"] = {"min": min_date, "max": max_date}

    denom = result["rows"] or 0
    for field in PRICE_FIELDS:
        if field in cols:
            nn = count_non_null(db, table, field)
            result["field_coverage"][field] = {"count": nn, "pct": pct(nn, denom)}
        else:
            result["field_coverage"][field] = {"count": 0, "pct": None, "missing_column": True}

    if symbol_col:
        insufficient = db.qall(
            f"""
            SELECT {symbol_col}, COUNT(*) AS bars
            FROM {table}
            GROUP BY {symbol_col}
            HAVING COUNT(*) < ?
            ORDER BY bars ASC, {symbol_col}
            LIMIT 50
            """,
            [MIN_BARS_REQUIRED],
        )
        result["insufficient_bars_symbols"] = len(insufficient)
        result["insufficient_bars_examples"] = [
            {"symbol": s, "bars": int(b)} for s, b in insufficient
        ]
        if insufficient:
            add_warning(
                warnings,
                "warning",
                "INSUFFICIENT_PRICE_BARS",
                "Some symbols have insufficient price bars.",
                {"examples": result["insufficient_bars_examples"][:20]},
            )

    if symbol_col and date_col:
        max_date = result["date_range"]["max"]
        if max_date:
            stale = db.qall(
                f"""
                WITH latest AS (
                    SELECT {symbol_col} AS symbol, MAX({date_col}) AS latest_date
                    FROM {table}
                    GROUP BY {symbol_col}
                )
                SELECT symbol, latest_date
                FROM latest
                WHERE latest_date < (?::DATE - INTERVAL '{STALE_PRICE_DAYS} days')
                ORDER BY latest_date ASC, symbol
                LIMIT 50
                """,
                [max_date],
            )
            result["stale_symbols"] = len(stale)
            result["stale_examples"] = [
                {"symbol": s, "latest_date": d} for s, d in stale
            ]
            if stale:
                add_warning(
                    warnings,
                    "warning",
                    "STALE_PRICE_SYMBOLS",
                    "Some symbols are stale versus latest price date.",
                    {"latest_price_date": max_date, "examples": result["stale_examples"][:20]},
                )

    return result


def review_features(db: Db, warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    table = "features_daily"
    result: Dict[str, Any] = {
        "table_exists": db.table_exists(table),
        "rows": None,
        "unique_symbols": None,
        "latest_date": None,
        "latest_date_symbols": None,
        "field_coverage": {},
    }

    if not db.table_exists(table):
        add_warning(warnings, "warning", "MISSING_FEATURES_TABLE", "features_daily table does not exist.")
        return result

    cols = db.columns(table)
    symbol_col = choose_col(cols, ["ticker", "symbol"])
    date_col = choose_col(cols, ["date", "trading_date"])

    result["rows"] = table_count(db, table)
    if symbol_col:
        result["unique_symbols"] = unique_count(db, table, [symbol_col])

    if date_col:
        latest = db.q1(f"SELECT MAX({date_col}) FROM {table}")
        result["latest_date"] = latest
        if latest and symbol_col:
            latest_symbols = int(
                db.q1(
                    f"SELECT COUNT(DISTINCT {symbol_col}) FROM {table} WHERE {date_col} = ?",
                    [latest],
                    default=0,
                )
                or 0
            )
            result["latest_date_symbols"] = latest_symbols
            universe_symbols = review_cached_universe_count(db)
            if universe_symbols and latest_symbols < universe_symbols * 0.5:
                add_warning(
                    warnings,
                    "warning",
                    "LOW_FEATURE_LATEST_COVERAGE",
                    "Latest feature-date symbol coverage is low.",
                    {
                        "latest_date": latest,
                        "latest_symbols": latest_symbols,
                        "universe_symbols": universe_symbols,
                    },
                )

    denom = result["rows"] or 0
    for field in FEATURE_FIELDS:
        if field in cols:
            nn = count_non_null(db, table, field)
            result["field_coverage"][field] = {"count": nn, "pct": pct(nn, denom)}
        else:
            result["field_coverage"][field] = {"count": 0, "pct": None, "missing_column": True}

    return result


def normalize_agent_id(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    if s in AGENT_ALIASES:
        return AGENT_ALIASES[s]
    lower = s.lower()
    if lower in CORE_AGENTS:
        return lower
    return lower


def review_season_window(db: Db) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """Resolve the current AI Arena season window for diagnostics.

    Prefer explicit workflow variables.  If they are absent, infer the display
    run period from public JSON or arena_display_runs.  This prevents false
    positives during local reviews while still catching the production failure
    where only one latest agent-score date exists.
    """
    start = os.getenv("AI_ARENA_START_DATE") or os.getenv("START_DATE") or ""
    end = os.getenv("AI_ARENA_END_DATE") or os.getenv("END_DATE") or ""
    year_raw = os.getenv("AI_ARENA_YEAR") or os.getenv("ARENA_YEAR") or os.getenv("YEAR") or ""

    live_run_id = read_live_run_id()
    if live_run_id and db.table_exists("arena_simulation_runs"):
        try:
            row = db.qall(
                "SELECT year, start_date, end_date FROM arena_simulation_runs WHERE run_id = ? LIMIT 1",
                [live_run_id],
            )
            if row:
                y, st, ed = row[0]
                if not year_raw and y is not None:
                    year_raw = str(y)
                if not start and st is not None:
                    start = str(st)
                if not end and ed is not None:
                    end = str(ed)
        except Exception:
            pass

    year: Optional[int] = None
    try:
        if str(year_raw).strip().lower() not in {"", "auto"}:
            year = int(str(year_raw).strip())
    except Exception:
        year = None

    if not start and year:
        start = f"{year}-01-01"
    if not end and year:
        end = f"{year}-12-31"
    return (start or None), (end or None), year


def review_agent_scores(db: Db, warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    table = "agent_scores_daily"
    season_start, season_end, season_year = review_season_window(db)
    result: Dict[str, Any] = {
        "table_exists": db.table_exists(table),
        "rows": None,
        "unique_agents": None,
        "latest_date": None,
        "date_count": None,
        "trade_candidate_rows": None,
        "season_window": {"start_date": season_start, "end_date": season_end, "year": season_year},
        "season_rows": None,
        "season_date_count": None,
        "season_trade_candidate_rows": None,
        "agents": [],
        "missing_core_agent_ids": [],
    }

    if not db.table_exists(table):
        add_warning(warnings, "critical", "MISSING_AGENT_SCORES_TABLE", "agent_scores_daily table does not exist.")
        return result

    cols = db.columns(table)
    agent_col = choose_col(cols, ["agent_id", "agent", "agent_name", "strategy_id"])
    ticker_col = choose_col(cols, ["ticker", "symbol"])
    date_col = choose_col(cols, ["date", "score_date", "trading_date"])
    score_col = choose_col(cols, ["normalized_score", "raw_score", "score", "final_score", "final_score_0_1", "score_0_1"])
    action_col = choose_col(cols, ["action", "signal_action", "decision"])

    result["rows"] = table_count(db, table)
    if agent_col:
        raw_agents = [r[0] for r in db.qall(f"SELECT DISTINCT {agent_col} FROM {table}")]
        normalized = sorted({normalize_agent_id(a) for a in raw_agents if normalize_agent_id(a)})
        result["unique_agents"] = len(normalized)
        missing = sorted([a for a in CORE_AGENTS if a not in normalized])
        result["missing_core_agent_ids"] = missing
        if missing:
            add_warning(
                warnings,
                "critical",
                "MISSING_CORE_AGENTS_IN_SCORES",
                "Some core agents are missing from agent_scores_daily.",
                {"missing_core_agent_ids": missing},
            )

    if date_col:
        result["latest_date"] = db.q1(f"SELECT MAX({date_col}) FROM {table}")
        result["date_count"] = int(db.q1(f"SELECT COUNT(DISTINCT {date_col}) FROM {table}", default=0) or 0)
        if result["date_count"] is not None and result["date_count"] < MIN_AGENT_SCORE_DATE_COUNT and (result.get("rows") or 0) > 0:
            add_warning(
                warnings,
                "critical",
                "AGENT_SCORE_DATE_RANGE_TOO_SMALL",
                "agent_scores_daily has too few score dates. Season rebuild may produce no orders.",
                {"date_count": result["date_count"], "minimum": MIN_AGENT_SCORE_DATE_COUNT},
            )

    if action_col:
        result["trade_candidate_rows"] = int(
            db.q1(f"SELECT COUNT(*) FROM {table} WHERE {action_col} = 'Trade'", default=0) or 0
        )
        if (result["trade_candidate_rows"] or 0) == 0 and (result.get("rows") or 0) > 0:
            add_warning(warnings, "critical", "NO_AGENT_TRADE_CANDIDATES", "agent_scores_daily has no Trade candidates.")

    if date_col and season_start:
        where = f"{date_col} >= ?"
        params: List[Any] = [season_start]
        if season_end:
            where += f" AND {date_col} <= ?"
            params.append(season_end)
        result["season_rows"] = int(db.q1(f"SELECT COUNT(*) FROM {table} WHERE {where}", params, 0) or 0)
        result["season_date_count"] = int(db.q1(f"SELECT COUNT(DISTINCT {date_col}) FROM {table} WHERE {where}", params, 0) or 0)
        if action_col:
            result["season_trade_candidate_rows"] = int(
                db.q1(f"SELECT COUNT(*) FROM {table} WHERE {where} AND {action_col} = 'Trade'", params, 0) or 0
            )
        if result["season_date_count"] < MIN_AGENT_SCORE_DATE_COUNT:
            add_warning(
                warnings,
                "critical",
                "SEASON_AGENT_SCORE_RANGE_TOO_SMALL",
                "Season range has too few agent score dates. This usually means AGENT_SCORE_MODE=latest was used by mistake.",
                {
                    "start_date": season_start,
                    "end_date": season_end,
                    "season_date_count": result["season_date_count"],
                    "minimum": MIN_AGENT_SCORE_DATE_COUNT,
                },
            )
        if action_col and (result["season_trade_candidate_rows"] or 0) == 0:
            add_warning(
                warnings,
                "critical",
                "SEASON_NO_TRADE_CANDIDATES",
                "Season range has no Trade candidates in agent_scores_daily.",
                {"start_date": season_start, "end_date": season_end},
            )

    if agent_col:
        rows = db.qall(f"SELECT DISTINCT {agent_col} FROM {table} ORDER BY {agent_col}")
        for (raw_agent,) in rows:
            agent_id = normalize_agent_id(raw_agent)
            display = CORE_AGENTS.get(agent_id, str(raw_agent))
            where = f"{agent_col} = ?"
            params = [raw_agent]
            count = int(db.q1(f"SELECT COUNT(*) FROM {table} WHERE {where}", params, 0) or 0)
            tickers = (
                int(db.q1(f"SELECT COUNT(DISTINCT {ticker_col}) FROM {table} WHERE {where}", params, 0) or 0)
                if ticker_col
                else None
            )
            dates = (
                int(db.q1(f"SELECT COUNT(DISTINCT {date_col}) FROM {table} WHERE {where}", params, 0) or 0)
                if date_col
                else None
            )
            trade_rows = (
                int(db.q1(f"SELECT COUNT(*) FROM {table} WHERE {where} AND {action_col} = 'Trade'", params, 0) or 0)
                if action_col
                else None
            )
            max_score = db.q1(f"SELECT MAX({score_col}) FROM {table} WHERE {where}", params, None) if score_col else None
            avg_score = db.q1(f"SELECT AVG({score_col}) FROM {table} WHERE {where}", params, None) if score_col else None
            actions: Dict[str, int] = {}
            if action_col:
                actions = {
                    str(k): int(v)
                    for k, v in db.qall(
                        f"""
                        SELECT {action_col}, COUNT(*)
                        FROM {table}
                        WHERE {where}
                        GROUP BY {action_col}
                        ORDER BY COUNT(*) DESC, {action_col}
                        """,
                        params,
                    )
                }

            result["agents"].append({
                "agent_id": agent_id,
                "display_name": display,
                "raw_agent_value": raw_agent,
                "rows": count,
                "date_count": dates,
                "tickers": tickers,
                "trade_candidate_rows": trade_rows,
                "max_score": max_score,
                "avg_score": avg_score,
                "actions": actions,
            })

    return result

def review_cached_universe_count(db: Db) -> Optional[int]:
    if db.table_exists("universe_master"):
        cols = db.columns("universe_master")
        col = choose_col(cols, ["ticker", "symbol"])
        if col:
            return unique_count(db, "universe_master", [col])
    if db.table_exists("prices_daily"):
        cols = db.columns("prices_daily")
        col = choose_col(cols, ["ticker", "symbol"])
        if col:
            return unique_count(db, "prices_daily", [col])
    return None


def review_fundamentals(db: Db, warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    universe_count = review_cached_universe_count(db)
    result: Dict[str, Any] = {
        "company_master_jp": review_generic_ticker_table(db, "company_master_jp", universe_count),
        "fundamentals_latest_jp": review_fundamental_table(db, "fundamentals_latest_jp", universe_count),
        "fundamentals_latest": review_fundamental_table(db, "fundamentals_latest", universe_count),
        "value_features_daily": review_value_features(db, universe_count),
        "site_fundamentals_diagnostics": read_site_fundamentals_diagnostics(),
    }

    # Prefer the new JP table. If missing, use legacy table only for warning context.
    primary = result["fundamentals_latest_jp"]
    value_features = result["value_features_daily"]

    primary_rows = primary.get("rows") or 0
    primary_cov = primary.get("coverage_vs_universe_pct")
    if primary_rows == 0:
        add_warning(
            warnings,
            "warning",
            "LOW_FUNDAMENTAL_ROW_COVERAGE",
            "Fundamental row coverage is low.",
            {"table": "fundamentals_latest_jp", "rows": primary_rows, "coverage_pct": primary_cov},
        )
    elif primary_cov is not None and primary_cov < MIN_FUNDAMENTAL_COVERAGE_PCT:
        add_warning(
            warnings,
            "warning",
            "LOW_FUNDAMENTAL_ROW_COVERAGE",
            "Fundamental row coverage is low.",
            {"table": "fundamentals_latest_jp", "rows": primary_rows, "coverage_pct": primary_cov},
        )

    for field, cov in (primary.get("field_coverage") or {}).items():
        field_pct = cov.get("pct")
        if field_pct is not None and field_pct < MIN_FUNDAMENTAL_COVERAGE_PCT:
            add_warning(
                warnings,
                "warning",
                "LOW_FUNDAMENTAL_METRIC_COVERAGE",
                f"{field} coverage is low.",
                {"table": "fundamentals_latest_jp", "field": field, "coverage_pct": field_pct},
            )

    if (value_features.get("rows") or 0) == 0:
        add_warning(
            warnings,
            "critical",
            "LOW_VALUE_FEATURE_ROW_COVERAGE",
            "value_features_daily row coverage is low. HIZUMI will fall back to proxy scoring.",
            {"rows": value_features.get("rows"), "coverage_pct": value_features.get("coverage_vs_universe_pct")},
        )
    elif (value_features.get("season_date_count") or value_features.get("date_count") or 0) < MIN_VALUE_FEATURE_DATE_COUNT:
        add_warning(
            warnings,
            "critical",
            "VALUE_FEATURE_RANGE_TOO_SMALL",
            "value_features_daily has too few dates for a Season rebuild.",
            {"date_count": value_features.get("date_count"), "season_date_count": value_features.get("season_date_count")},
        )

    return result


def review_generic_ticker_table(db: Db, table: str, universe_count: Optional[int]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "exists": db.table_exists(table),
        "rows": None,
        "unique_tickers": None,
        "coverage_vs_universe_pct": None,
    }
    if not db.table_exists(table):
        return result

    cols = db.columns(table)
    ticker_col = choose_col(cols, ["ticker", "symbol"])
    result["rows"] = table_count(db, table)
    if ticker_col:
        result["unique_tickers"] = unique_count(db, table, [ticker_col])
        result["coverage_vs_universe_pct"] = pct(result["unique_tickers"], universe_count)
    return result


def review_fundamental_table(db: Db, table: str, universe_count: Optional[int]) -> Dict[str, Any]:
    result = review_generic_ticker_table(db, table, universe_count)
    result["field_coverage"] = {}

    if not db.table_exists(table):
        return result

    cols = db.columns(table)
    denom = result.get("rows") or 0
    for field in FUNDAMENTAL_FIELDS:
        if field in cols:
            nn = count_non_null(db, table, field)
            result["field_coverage"][field] = {"count": nn, "pct": pct(nn, denom)}
        else:
            result["field_coverage"][field] = {"count": 0, "pct": None, "missing_column": True}

    return result


def review_value_features(db: Db, universe_count: Optional[int]) -> Dict[str, Any]:
    table = "value_features_daily"
    result = review_generic_ticker_table(db, table, universe_count)
    result.update({
        "latest_date": None,
        "date_count": None,
        "latest_date_tickers": None,
        "season_rows": None,
        "season_date_count": None,
        "field_coverage": {},
    })
    if not db.table_exists(table):
        return result

    cols = db.columns(table)
    ticker_col = choose_col(cols, ["ticker", "symbol"])
    date_col = choose_col(cols, ["date", "trading_date", "feature_date"])
    if date_col:
        latest = db.q1(f"SELECT MAX({date_col}) FROM {table}")
        result["latest_date"] = latest
        result["date_count"] = int(db.q1(f"SELECT COUNT(DISTINCT {date_col}) FROM {table}", default=0) or 0)
        if latest and ticker_col:
            result["latest_date_tickers"] = int(
                db.q1(f"SELECT COUNT(DISTINCT {ticker_col}) FROM {table} WHERE {date_col} = ?", [latest], 0) or 0
            )
        season_start, season_end, _ = review_season_window(db)
        if season_start:
            where = f"{date_col} >= ?"
            params: List[Any] = [season_start]
            if season_end:
                where += f" AND {date_col} <= ?"
                params.append(season_end)
            result["season_rows"] = int(db.q1(f"SELECT COUNT(*) FROM {table} WHERE {where}", params, 0) or 0)
            result["season_date_count"] = int(db.q1(f"SELECT COUNT(DISTINCT {date_col}) FROM {table} WHERE {where}", params, 0) or 0)

    denom = result.get("rows") or 0
    for field in [
        "valuation_discount_score", "quality_guard_score", "earnings_stability_score",
        "shareholder_return_score", "re_rating_signal_score", "value_trap_penalty",
        "value_mispricing_score", "fundamental_coverage_score",
    ]:
        if field in cols:
            nn = count_non_null(db, table, field)
            result["field_coverage"][field] = {"count": nn, "pct": pct(nn, denom)}
        else:
            result["field_coverage"][field] = {"count": 0, "pct": None, "missing_column": True}

    return result

def read_site_fundamentals_diagnostics() -> Dict[str, Any]:
    path = OUT_DIR / "data" / "japan" / "ai-arena" / "diagnostics" / "fundamentals-latest.json"
    if not path.exists():
        return {"exists": False, "path": rel(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {"exists": True, "path": rel(path), "data": data}
    except Exception as exc:
        return {"exists": True, "path": rel(path), "error": str(exc)}


def review_arena_tables(db: Db, warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for table in ARENA_TABLES:
        exists = db.table_exists(table)
        rows = table_count(db, table) if exists else None
        result[table] = {"exists": exists, "rows": rows}

        if table in {"arena_orders", "arena_open_positions", "arena_equity_curve", "arena_yearly_rankings"}:
            if not exists:
                add_warning(warnings, "critical", "MISSING_ARENA_TABLE", f"{table} table does not exist.", {"table": table})
            elif rows == 0:
                add_warning(warnings, "critical", "EMPTY_ARENA_TABLE", f"{table} table is empty.", {"table": table})
        elif table in {"arena_trades", "arena_trade_rankings"}:
            if not exists:
                add_warning(warnings, "warning", "MISSING_ARENA_TABLE", f"{table} table does not exist.", {"table": table})

    live_run_id = read_live_run_id()
    result["live_run_id"] = live_run_id
    if live_run_id:
        for table in [
            "arena_orders", "arena_trades", "arena_open_positions", "arena_equity_curve",
            "arena_yearly_rankings", "arena_monthly_rankings", "arena_trade_rankings",
        ]:
            if db.table_exists(table):
                cols = db.columns(table)
                if "run_id" in cols:
                    n = int(db.q1(f"SELECT COUNT(*) FROM {table} WHERE run_id = ?", [live_run_id], 0) or 0)
                    result[table]["rows_for_live_run_id"] = n

        orders = (result.get("arena_orders") or {}).get("rows_for_live_run_id") or 0
        trades = (result.get("arena_trades") or {}).get("rows_for_live_run_id") or 0
        open_positions = (result.get("arena_open_positions") or {}).get("rows_for_live_run_id") or 0
        equity_rows = (result.get("arena_equity_curve") or {}).get("rows_for_live_run_id") or 0
        yearly_rows = (result.get("arena_yearly_rankings") or {}).get("rows_for_live_run_id") or 0
        monthly_rows = (result.get("arena_monthly_rankings") or {}).get("rows_for_live_run_id") or 0
        trade_ranking_rows = (result.get("arena_trade_rankings") or {}).get("rows_for_live_run_id") or 0

        result["live_run_health"] = {
            "orders": orders,
            "trades": trades,
            "open_positions": open_positions,
            "equity_rows": equity_rows,
            "yearly_ranking_rows": yearly_rows,
            "monthly_ranking_rows": monthly_rows,
            "trade_ranking_rows": trade_ranking_rows,
            "has_visible_positions_or_trades": bool(open_positions or trades),
        }

        if orders < MIN_ARENA_ORDERS_FOR_LIVE_RUN:
            add_warning(
                warnings,
                "critical",
                "LIVE_RUN_HAS_NO_ORDERS",
                "The current display run has no arena_orders. AI Arena is not actually trading.",
                {"live_run_id": live_run_id, "orders": orders},
            )
        if (open_positions + trades) == 0:
            add_warning(
                warnings,
                "critical",
                "LIVE_RUN_HAS_NO_POSITIONS_OR_TRADES",
                "The current display run has neither open positions nor closed trades.",
                {"live_run_id": live_run_id, "open_positions": open_positions, "trades": trades},
            )
        if equity_rows == 0:
            add_warning(
                warnings,
                "critical",
                "LIVE_RUN_HAS_NO_EQUITY_CURVE",
                "The current display run has no equity curve rows.",
                {"live_run_id": live_run_id},
            )
        if yearly_rows not in {EXPECTED_AGENT_COUNT}:
            add_warning(
                warnings,
                "critical",
                "LIVE_RUN_YEARLY_RANKING_INCOMPLETE",
                "The current display run does not have exactly one yearly ranking row per Agent.",
                {"live_run_id": live_run_id, "yearly_rows": yearly_rows, "expected": EXPECTED_AGENT_COUNT},
            )
        if monthly_rows == 0:
            add_warning(
                warnings,
                "warning",
                "LIVE_RUN_MONTHLY_RANKING_EMPTY",
                "The current display run has no monthly ranking rows.",
                {"live_run_id": live_run_id},
            )
        if trade_ranking_rows == 0 and trades > 0:
            add_warning(
                warnings,
                "warning",
                "LIVE_RUN_TRADE_RANKING_EMPTY",
                "Closed trades exist, but arena_trade_rankings is empty.",
                {"live_run_id": live_run_id, "trades": trades},
            )

        # Per-agent execution check for the visible run.
        if db.table_exists("arena_orders"):
            try:
                agent_orders = db.qall(
                    """
                    SELECT agent_id,
                           COUNT(*) AS orders,
                           SUM(CASE WHEN order_status = 'FILLED' AND side = 'BUY' THEN 1 ELSE 0 END) AS filled_buys,
                           SUM(CASE WHEN order_status = 'FILLED' AND side = 'SELL' THEN 1 ELSE 0 END) AS filled_sells
                    FROM arena_orders
                    WHERE run_id = ?
                    GROUP BY agent_id
                    ORDER BY agent_id
                    """,
                    [live_run_id],
                )
                result["agent_execution"] = [
                    {"agent_id": a, "orders": int(o or 0), "filled_buys": int(b or 0), "filled_sells": int(se or 0)}
                    for a, o, b, se in agent_orders
                ]
                no_buy_agents = [r["agent_id"] for r in result["agent_execution"] if r["filled_buys"] == 0]
                if no_buy_agents:
                    add_warning(
                        warnings,
                        "warning",
                        "LIVE_RUN_AGENTS_WITHOUT_FILLED_BUYS",
                        "Some Agents have no filled buy orders in the current display run.",
                        {"live_run_id": live_run_id, "agents": no_buy_agents},
                    )
            except Exception as exc:
                result["agent_execution_error"] = str(exc)

    return result

def read_live_run_id() -> Optional[str]:
    path = OUT_DIR / "data" / "japan" / "ai-arena" / "live" / "latest.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        rid = data.get("run_id")
        return str(rid) if rid else None
    except Exception:
        return None


def review_site_outputs(warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    missing = []
    outputs = {}
    for item in SITE_OUTPUTS:
        p = Path(item)
        exists = p.exists()
        outputs[item] = {
            "exists": exists,
            "size_bytes": p.stat().st_size if exists else None,
            "size_mb": mb(p.stat().st_size) if exists else None,
        }
        if not exists:
            missing.append(item)

    if missing:
        add_warning(
            warnings,
            "warning",
            "MISSING_SITE_OUTPUTS",
            "Some expected site outputs are missing.",
            {"missing": missing},
        )

    return {"missing_outputs": missing, "outputs": outputs}


def review_repo_artifacts(warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    site_data = OUT_DIR / "data"
    files: List[Path] = []
    if site_data.exists():
        files = [p for p in site_data.rglob("*") if p.is_file()]

    total_bytes = sum(p.stat().st_size for p in files)
    largest = sorted(files, key=lambda p: p.stat().st_size, reverse=True)[:15]

    prices_latest = OUT_DIR / "data" / "prices-jp" / "latest.json"
    prices_latest_mb = mb(prices_latest.stat().st_size) if prices_latest.exists() else None
    if prices_latest_mb is not None and prices_latest_mb > 5:
        add_warning(
            warnings,
            "warning",
            "PRICES_LATEST_TOO_LARGE",
            "site/data/prices-jp/latest.json is larger than expected.",
            {"size_mb": prices_latest_mb, "expected_max_mb": 5},
        )

    dated_prices = []
    prices_dir = OUT_DIR / "data" / "prices-jp"
    if prices_dir.exists():
        dated_prices = [
            p
            for p in prices_dir.glob("*.json")
            if p.name != "latest.json" and p.name != "manifest.json"
        ]
    if dated_prices:
        add_warning(
            warnings,
            "warning",
            "DATED_PRICE_JSON_REMAINING",
            "Dated prices JSON files remain under site/data/prices-jp.",
            {"count": len(dated_prices), "examples": [rel(p) for p in dated_prices[:20]]},
        )

    return {
        "site_data_files": len(files),
        "site_data_total_mb": mb(total_bytes),
        "prices_latest_mb": prices_latest_mb,
        "dated_prices_json_count": len(dated_prices),
        "largest_files": [
            {"path": rel(p), "size_mb": mb(p.stat().st_size), "size_bytes": p.stat().st_size}
            for p in largest
        ],
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def md_value(value: Any) -> str:
    value = json_safe(value)
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return str(round(value, 4))
    return str(value)


def render_md(report: Dict[str, Any]) -> str:
    warnings = report.get("warnings", [])
    universe = report.get("universe", {})
    prices = report.get("prices", {})
    features = report.get("features", {})
    agent_scores = report.get("agent_scores", {})
    fundamentals = report.get("fundamentals", {})
    arena = report.get("arena_simulation_tables", {})
    site = report.get("site_outputs", {})
    artifacts = report.get("repo_artifact_size", {})
    db_meta = report.get("duckdb_metadata", {})

    lines: List[str] = []
    lines.append("# Neon Tokyo Data Coverage Review")
    lines.append("")
    lines.append(f"Generated: {report.get('generated_at')}")
    lines.append(f"DuckDB: `{report.get('duckdb_path')}`")
    lines.append(f"DuckDB exists: **{md_value(report.get('duckdb_exists'))}**")
    lines.append("")

    lines.append("## Canonical DuckDB Metadata")
    lines.append("")
    lines.append(f"- Metadata table exists: {md_value(db_meta.get('metadata_table_exists'))}")
    lines.append(f"- DB size MB: {md_value(db_meta.get('size_mb'))}")
    metadata = db_meta.get("metadata") or {}
    if metadata:
        lines.append("")
        lines.append("| Key | Value | Updated At |")
        lines.append("|---|---|---|")
        for key, obj in metadata.items():
            if isinstance(obj, dict):
                lines.append(f"| `{key}` | {md_value(obj.get('value'))} | {md_value(obj.get('updated_at'))} |")
            else:
                lines.append(f"| `{key}` | {md_value(obj)} |  |")
    lines.append("")

    lines.append("## Executive Warnings")
    lines.append("")
    if warnings:
        lines.append("| Severity | Code | Message |")
        lines.append("|---|---|---|")
        for w in warnings:
            lines.append(f"| {w.get('severity')} | `{w.get('code')}` | {w.get('message')} |")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Universe")
    lines.append("")
    udb = universe.get("duckdb", {})
    lines.append(f"- DuckDB rows: {md_value(udb.get('rows'))}")
    lines.append(f"- DuckDB unique tickers: {md_value(udb.get('unique_tickers'))}")
    lines.append(f"- Suspicious tickers: {md_value(udb.get('suspicious_tickers'))}")
    for name, obj in (universe.get("csvs") or {}).items():
        lines.append(
            f"- CSV `{name}`: exists={md_value(obj.get('exists'))} rows={md_value(obj.get('rows'))} suspicious={md_value(obj.get('suspicious'))}"
        )
    lines.append("")

    lines.append("## Prices")
    lines.append("")
    lines.append(f"- Table exists: {md_value(prices.get('table_exists'))}")
    lines.append(f"- Rows: {md_value(prices.get('rows'))}")
    lines.append(f"- Unique symbols: {md_value(prices.get('unique_symbols'))}")
    dr = prices.get("date_range") or {}
    lines.append(f"- Date range: {md_value(dr.get('min'))} → {md_value(dr.get('max'))}")
    lines.append(f"- Insufficient bars symbols: {md_value(prices.get('insufficient_bars_symbols'))}")
    lines.append(f"- Stale symbols: {md_value(prices.get('stale_symbols'))}")
    lines.append("")

    lines.append("## Features")
    lines.append("")
    lines.append(f"- Table exists: {md_value(features.get('table_exists'))}")
    lines.append(f"- Rows: {md_value(features.get('rows'))}")
    lines.append(f"- Unique symbols: {md_value(features.get('unique_symbols'))}")
    lines.append(f"- Latest date: {md_value(features.get('latest_date'))}")
    lines.append(f"- Latest date symbols: {md_value(features.get('latest_date_symbols'))}")
    lines.append("")
    lines.append("| Feature | Coverage | Count |")
    lines.append("|---|---:|---:|")
    for field, obj in (features.get("field_coverage") or {}).items():
        lines.append(f"| `{field}` | {md_value(obj.get('pct'))}% | {md_value(obj.get('count'))} |")
    lines.append("")

    lines.append("## Agent Scores")
    lines.append("")
    lines.append(f"- Table exists: {md_value(agent_scores.get('table_exists'))}")
    lines.append(f"- Rows: {md_value(agent_scores.get('rows'))}")
    lines.append(f"- Unique agents: {md_value(agent_scores.get('unique_agents'))}")
    lines.append(f"- Latest date: {md_value(agent_scores.get('latest_date'))}")
    lines.append(f"- Date count: {md_value(agent_scores.get('date_count'))}")
    lines.append(f"- Trade candidates: {md_value(agent_scores.get('trade_candidate_rows'))}")
    sw = agent_scores.get('season_window') or {}
    lines.append(f"- Season window: {md_value(sw.get('start_date'))} → {md_value(sw.get('end_date'))}")
    lines.append(f"- Season date count: {md_value(agent_scores.get('season_date_count'))}")
    lines.append(f"- Season trade candidates: {md_value(agent_scores.get('season_trade_candidate_rows'))}")
    lines.append("")
    lines.append("| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for a in agent_scores.get("agents") or []:
        actions = a.get("actions") or {}
        action_text = ", ".join(f"{k}:{v}" for k, v in actions.items()) if actions else "N/A"
        label = f"{a.get('display_name')} / `{a.get('agent_id')}`"
        lines.append(
            f"| {label} | {md_value(a.get('rows'))} | {md_value(a.get('date_count'))} | {md_value(a.get('trade_candidate_rows'))} | {md_value(a.get('tickers'))} | {md_value(a.get('max_score'))} | {md_value(a.get('avg_score'))} | {action_text} |"
        )
    lines.append("")

    lines.append("## Company / Fundamentals")
    lines.append("")
    for table in ["company_master_jp", "fundamentals_latest_jp", "fundamentals_latest"]:
        obj = fundamentals.get(table) or {}
        lines.append(f"### `{table}`")
        lines.append("")
        lines.append(f"- Exists: {md_value(obj.get('exists'))}")
        lines.append(f"- Rows: {md_value(obj.get('rows'))}")
        lines.append(f"- Unique tickers: {md_value(obj.get('unique_tickers'))}")
        lines.append(f"- Coverage vs universe: {md_value(obj.get('coverage_vs_universe_pct'))}%")
        if obj.get("field_coverage"):
            lines.append("")
            lines.append("| Field | Coverage | Count |")
            lines.append("|---|---:|---:|")
            for field, cov in obj["field_coverage"].items():
                lines.append(f"| `{field}` | {md_value(cov.get('pct'))}% | {md_value(cov.get('count'))} |")
        lines.append("")

    vf = fundamentals.get("value_features_daily") or {}
    lines.append("### `value_features_daily`")
    lines.append("")
    lines.append(f"- Exists: {md_value(vf.get('exists'))}")
    lines.append(f"- Rows: {md_value(vf.get('rows'))}")
    lines.append(f"- Unique tickers: {md_value(vf.get('unique_tickers'))}")
    lines.append(f"- Coverage vs universe: {md_value(vf.get('coverage_vs_universe_pct'))}%")
    lines.append(f"- Latest date: {md_value(vf.get('latest_date'))}")
    lines.append(f"- Date count: {md_value(vf.get('date_count'))}")
    lines.append(f"- Latest date tickers: {md_value(vf.get('latest_date_tickers'))}")
    lines.append(f"- Season date count: {md_value(vf.get('season_date_count'))}")
    lines.append("")

    lines.append("## Arena Simulation Tables")
    lines.append("")
    health = arena.get("live_run_health") or {}
    if health:
        lines.append(f"- Live run: `{md_value(arena.get('live_run_id'))}`")
        lines.append(f"- Live orders: {md_value(health.get('orders'))}")
        lines.append(f"- Live trades: {md_value(health.get('trades'))}")
        lines.append(f"- Live open positions: {md_value(health.get('open_positions'))}")
        lines.append(f"- Live yearly ranking rows: {md_value(health.get('yearly_ranking_rows'))}")
        lines.append("")
    lines.append("| Table | Exists | Rows | Rows for live run |")
    lines.append("|---|---:|---:|---:|")
    for table in ARENA_TABLES:
        obj = arena.get(table) or {}
        lines.append(
            f"| `{table}` | {md_value(obj.get('exists'))} | {md_value(obj.get('rows'))} | {md_value(obj.get('rows_for_live_run_id'))} |"
        )
    lines.append("")

    lines.append("## Site Outputs")
    lines.append("")
    missing = site.get("missing_outputs") or []
    lines.append(f"- Missing outputs: {len(missing)}")
    if missing:
        for item in missing:
            lines.append(f"  - `{item}`")
    lines.append("")

    lines.append("## Repo Artifact Size")
    lines.append("")
    lines.append(f"- site/data files: {md_value(artifacts.get('site_data_files'))}")
    lines.append(f"- site/data total MB: {md_value(artifacts.get('site_data_total_mb'))}")
    lines.append(f"- prices latest MB: {md_value(artifacts.get('prices_latest_mb'))}")
    lines.append(f"- dated prices JSON count: {md_value(artifacts.get('dated_prices_json_count'))}")
    lines.append("")
    lines.append("| Largest file | MB |")
    lines.append("|---|---:|")
    for obj in artifacts.get("largest_files") or []:
        lines.append(f"| `{obj.get('path')}` | {md_value(obj.get('size_mb'))} |")

    lines.append("")
    return "\n".join(lines)


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_report() -> Dict[str, Any]:
    warnings: List[Dict[str, Any]] = []

    with Db(DB_PATH) as db:
        if not db.exists:
            add_warning(
                warnings,
                "critical",
                "MISSING_DUCKDB",
                "DuckDB file does not exist.",
                {"path": rel(DB_PATH)},
            )

        report: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now_iso(),
            "duckdb_path": rel(DB_PATH),
            "duckdb_exists": db.exists,
            "duckdb_metadata": review_duckdb_metadata(db),
            "warnings": warnings,
            "universe": review_universe(db, warnings),
            "prices": review_prices(db, warnings),
            "features": review_features(db, warnings),
            "agent_scores": review_agent_scores(db, warnings),
            "fundamentals": review_fundamentals(db, warnings),
            "arena_simulation_tables": review_arena_tables(db, warnings),
            "site_outputs": review_site_outputs(warnings),
            "repo_artifact_size": review_repo_artifacts(warnings),
        }

    # warnings may have been appended while nested sections were created.
    report["warnings"] = warnings
    return report


def main() -> int:
    report = build_report()
    md = render_md(report)

    write_json(REPORT_JSON, report)
    write_json(REPORT_JSON_ALIAS, report)
    write_md(REPORT_MD, md)
    write_md(REPORT_MD_ALIAS, md)

    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON_ALIAS}")
    print(f"Wrote {REPORT_MD_ALIAS}")

    criticals = [w for w in report.get("warnings", []) if w.get("severity") == "critical"]
    print(f"warnings={len(report.get('warnings', []))} criticals={len(criticals)}")

    if os.getenv("FAIL_ON_CRITICAL", "false").lower() == "true" and criticals:
        for w in criticals:
            print(f"critical: {w.get('code')} {w.get('message')}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
