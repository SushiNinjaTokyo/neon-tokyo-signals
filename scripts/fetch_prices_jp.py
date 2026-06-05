#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch / update Japanese equity daily price cache.

Design goals:
- Safe with existing DuckDB files.
- Validate and migrate prices_daily schema before writing.
- Avoid long live-update stalls.
- In live mode:
    - If yfinance returns empty data, skip immediately.
    - If yfinance raises an exception, use stooq fallback only when enabled.
    - stooq fallback timeout is short by default.
- Print clear fetch statistics.

Expected DuckDB table:
    prices_daily(
        ticker VARCHAR,
        name VARCHAR,
        date DATE,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        adj_close DOUBLE,
        volume BIGINT,
        source VARCHAR,
        fetched_at TIMESTAMP
    )

Environment variables:
    OUT_DIR
    PRICE_DUCKDB_PATH
    PRICE_STORE_MODE
    PRICE_FETCH_MODE
    PRICE_REFRESH_MODE
    JP_UNIVERSE_CSV
    FETCH_START_DATE
    FETCH_END_DATE
    STOOQ_FALLBACK_ENABLED
    STOOQ_TIMEOUT_SECONDS
    YFINANCE_TIMEOUT_SECONDS
    MAX_TICKERS
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd


try:
    import duckdb  # type: ignore
except Exception:
    duckdb = None


try:
    import yfinance as yf  # type: ignore
except Exception:
    yf = None


# =============================================================================
# Configuration
# =============================================================================


DEFAULT_START_DATE = "2025-01-01"
DEFAULT_OUT_DIR = "site"
DEFAULT_DUCKDB_PATH = "data/cache/neon_tokyo_jp.duckdb"
DEFAULT_UNIVERSE_CSV = "data/universe/jp_duckdb_trial_300.csv"


PRICE_COLUMNS = [
    "ticker",
    "name",
    "date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "source",
    "fetched_at",
]


NUMERIC_PRICE_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
]


@dataclass(frozen=True)
class TickerItem:
    ticker: str
    name: str = ""


@dataclass
class FetchResult:
    ticker: str
    name: str
    status: str
    source: str = ""
    df: Optional[pd.DataFrame] = None
    error: str = ""
    bars: int = 0
    latest: str = ""


@dataclass
class Stats:
    total_tickers: int = 0
    cache_hit_count: int = 0
    yfinance_success_count: int = 0
    stooq_success_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    written_rows: int = 0


def env_str(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip()


def env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on", "enabled"}


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(str(raw).strip())
    except Exception:
        return default


def parse_date(value: Any) -> date:
    if value is None:
        raise ValueError("date value is None")
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    if not text:
        raise ValueError("date value is empty")
    return datetime.fromisoformat(text[:10]).date()


def today_jst() -> date:
    # GitHub Actions usually runs in UTC. Japan market logic only needs date.
    # The project already treats generated_at separately, so date.today is enough
    # for cache range end in this script.
    return date.today()


def normalize_ticker(raw: Any) -> str:
    ticker = str(raw or "").strip().upper()
    ticker = ticker.replace(" ", "")
    return ticker


def normalize_name(raw: Any) -> str:
    return str(raw or "").strip()


# =============================================================================
# Universe loading
# =============================================================================


def load_universe(csv_path: Path) -> list[TickerItem]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Universe CSV not found: {csv_path}")

    rows: list[TickerItem] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [str(x or "").strip() for x in (reader.fieldnames or [])]

        if not fieldnames:
            raise ValueError(f"Universe CSV has no header: {csv_path}")

        lower_map = {c.lower(): c for c in fieldnames}

        ticker_col = (
            lower_map.get("ticker")
            or lower_map.get("symbol")
            or lower_map.get("code")
            or lower_map.get("銘柄コード")
        )
        name_col = (
            lower_map.get("name")
            or lower_map.get("company_name")
            or lower_map.get("company")
            or lower_map.get("銘柄名")
        )

        if ticker_col is None:
            raise ValueError(
                f"Universe CSV must include ticker/symbol/code column. "
                f"columns={fieldnames}"
            )

        for r in reader:
            ticker = normalize_ticker(r.get(ticker_col, ""))
            name = normalize_name(r.get(name_col, "")) if name_col else ""

            if not ticker:
                continue

            # Accept both 7203 and 7203.T, but normalize JP equities to .T.
            if ticker.isdigit():
                ticker = f"{ticker}.T"

            rows.append(TickerItem(ticker=ticker, name=name))

    # De-duplicate while preserving order.
    seen: set[str] = set()
    unique: list[TickerItem] = []
    for item in rows:
        if item.ticker in seen:
            continue
        seen.add(item.ticker)
        unique.append(item)

    if not unique:
        raise ValueError(f"Universe CSV has no valid tickers: {csv_path}")

    return unique


# =============================================================================
# DuckDB schema management
# =============================================================================


def connect_duckdb(path: Path):
    if duckdb is None:
        raise RuntimeError("duckdb package is not installed")

    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def table_exists(conn, table_name: str) -> bool:
    result = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = ?
        """,
        [table_name],
    ).fetchone()
    return bool(result and result[0] > 0)


def get_table_columns(conn, table_name: str) -> dict[str, str]:
    if not table_exists(conn, table_name):
        return {}

    rows = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    # PRAGMA table_info returns:
    # cid, name, type, notnull, dflt_value, pk
    return {str(row[1]).lower(): str(row[2]).upper() for row in rows}


def ensure_price_schema(conn) -> None:
    """
    Create and migrate prices_daily safely.

    This function is intentionally defensive because existing DuckDB files may
    have been created by older versions of the pipeline.

    Important:
    CREATE TABLE IF NOT EXISTS never adds missing columns to an existing table.
    So we inspect the current schema and apply ALTER TABLE migrations.
    """

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prices_daily (
            ticker VARCHAR NOT NULL,
            name VARCHAR,
            date DATE NOT NULL,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            adj_close DOUBLE,
            volume BIGINT,
            source VARCHAR,
            fetched_at TIMESTAMP
        )
        """
    )

    required_columns: list[tuple[str, str]] = [
        ("ticker", "VARCHAR"),
        ("name", "VARCHAR"),
        ("date", "DATE"),
        ("open", "DOUBLE"),
        ("high", "DOUBLE"),
        ("low", "DOUBLE"),
        ("close", "DOUBLE"),
        ("adj_close", "DOUBLE"),
        ("volume", "BIGINT"),
        ("source", "VARCHAR"),
        ("fetched_at", "TIMESTAMP"),
    ]

    existing = get_table_columns(conn, "prices_daily")

    for col_name, col_type in required_columns:
        if col_name.lower() not in existing:
            print(f"Schema migration: ALTER prices_daily ADD COLUMN {col_name} {col_type}")
            conn.execute(f"ALTER TABLE prices_daily ADD COLUMN {col_name} {col_type}")

    validate_price_schema(conn)

    # Compatibility view. If a physical table with this name exists, skip.
    try:
        row = conn.execute(
            """
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = 'prices_daily_jp'
            LIMIT 1
            """
        ).fetchone()

        if row and str(row[0]).upper() == "BASE TABLE":
            print("Warning: prices_daily_jp exists as table; compatibility view skipped")
        else:
            conn.execute(
                """
                CREATE OR REPLACE VIEW prices_daily_jp AS
                SELECT
                    ticker,
                    name,
                    date,
                    open,
                    high,
                    low,
                    close,
                    adj_close,
                    volume,
                    source,
                    fetched_at
                FROM prices_daily
                """
            )
    except Exception as exc:
        print(f"Warning: could not create prices_daily_jp view: {exc}")


def validate_price_schema(conn) -> None:
    existing = get_table_columns(conn, "prices_daily")
    missing = [col for col in PRICE_COLUMNS if col.lower() not in existing]

    if missing:
        raise RuntimeError(
            "DuckDB schema validation failed. "
            f"prices_daily missing columns: {missing}. "
            f"existing={existing}"
        )

    # Hard checks for dangerous type mismatches.
    # DuckDB can cast many values, but date/ticker absence or incompatible types
    # should be caught before the long fetch loop.
    date_type = existing.get("date", "")
    ticker_type = existing.get("ticker", "")

    if "DATE" not in date_type and "TIMESTAMP" not in date_type:
        raise RuntimeError(
            f"prices_daily.date has suspicious type: {date_type}. "
            "Expected DATE or TIMESTAMP."
        )

    if not any(x in ticker_type for x in ["VARCHAR", "TEXT", "STRING"]):
        raise RuntimeError(
            f"prices_daily.ticker has suspicious type: {ticker_type}. "
            "Expected VARCHAR/TEXT/STRING."
        )


def get_latest_cached_date(conn, ticker: str) -> Optional[date]:
    try:
        row = conn.execute(
            """
            SELECT MAX(date)
            FROM prices_daily
            WHERE ticker = ?
            """,
            [ticker],
        ).fetchone()
        if not row or row[0] is None:
            return None
        return parse_date(row[0])
    except Exception:
        return None


# =============================================================================
# Fetch helpers
# =============================================================================


def normalize_price_df(
    df: pd.DataFrame,
    ticker: str,
    name: str,
    source: str,
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=PRICE_COLUMNS)

    out = df.copy()

    # yfinance may return MultiIndex columns.
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [
            str(c[0]).strip() if isinstance(c, tuple) else str(c).strip()
            for c in out.columns
        ]

    # Date can be index or column.
    if "Date" in out.columns:
        date_series = out["Date"]
    elif "date" in out.columns:
        date_series = out["date"]
    else:
        date_series = out.index

    normalized = pd.DataFrame()
    normalized["date"] = pd.to_datetime(date_series, errors="coerce").date

    col_map = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "AdjClose": "adj_close",
        "Volume": "volume",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "adj_close": "adj_close",
        "adj close": "adj_close",
        "volume": "volume",
    }

    for src, dst in col_map.items():
        if src in out.columns and dst not in normalized.columns:
            normalized[dst] = out[src]

    # If adjusted close is unavailable, use close.
    if "adj_close" not in normalized.columns:
        normalized["adj_close"] = normalized.get("close")

    for col in ["open", "high", "low", "close", "adj_close"]:
        if col not in normalized.columns:
            normalized[col] = None
        normalized[col] = pd.to_numeric(normalized[col], errors="coerce")

    if "volume" not in normalized.columns:
        normalized["volume"] = 0
    normalized["volume"] = pd.to_numeric(normalized["volume"], errors="coerce").fillna(0).astype("int64")

    normalized["ticker"] = ticker
    normalized["name"] = name
    normalized["source"] = source
    normalized["fetched_at"] = datetime.utcnow()

    normalized = normalized[PRICE_COLUMNS]
    normalized = normalized.dropna(subset=["date"])
    normalized = normalized.drop_duplicates(subset=["ticker", "date"], keep="last")
    normalized = normalized.sort_values(["ticker", "date"]).reset_index(drop=True)

    # Remove rows that are completely unusable.
    normalized = normalized.dropna(subset=["close"], how="all")

    return normalized


def fetch_yfinance(
    ticker: str,
    name: str,
    start: date,
    end: date,
    timeout_seconds: int,
) -> FetchResult:
    if yf is None:
        return FetchResult(
            ticker=ticker,
            name=name,
            status="error",
            source="yfinance",
            error="yfinance package is not installed",
        )

    # yfinance end is exclusive, so add one day.
    yf_end = end + timedelta(days=1)

    try:
        raw = yf.download(
            ticker,
            start=start.isoformat(),
            end=yf_end.isoformat(),
            progress=False,
            auto_adjust=False,
            actions=False,
            threads=False,
            timeout=timeout_seconds,
        )

        if raw is None or raw.empty:
            return FetchResult(
                ticker=ticker,
                name=name,
                status="empty",
                source="yfinance",
                error="yfinance_empty",
            )

        df = normalize_price_df(raw, ticker=ticker, name=name, source="yfinance")
        if df.empty:
            return FetchResult(
                ticker=ticker,
                name=name,
                status="empty",
                source="yfinance",
                error="yfinance_empty_after_normalize",
            )

        latest_value = str(max(df["date"]))[:10]

        return FetchResult(
            ticker=ticker,
            name=name,
            status="ok",
            source="yfinance",
            df=df,
            bars=len(df),
            latest=latest_value,
        )

    except Exception as exc:
        return FetchResult(
            ticker=ticker,
            name=name,
            status="error",
            source="yfinance",
            error=f"{type(exc).__name__}: {exc}",
        )


def to_stooq_symbol(ticker: str) -> str:
    t = normalize_ticker(ticker)
    if t.endswith(".T"):
        return t[:-2] + ".JP"
    if t.endswith(".JP"):
        return t
    if t.isdigit():
        return t + ".JP"
    return t


def fetch_stooq(
    ticker: str,
    name: str,
    start: date,
    end: date,
    timeout_seconds: int,
) -> FetchResult:
    symbol = to_stooq_symbol(ticker).lower()
    url = (
        "https://stooq.com/q/d/l/"
        f"?s={symbol}&i=d&d1={start.strftime('%Y%m%d')}&d2={end.strftime('%Y%m%d')}"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 price-cache-fetcher",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as res:
            body = res.read().decode("utf-8", errors="replace")

        if not body.strip() or "No data" in body:
            return FetchResult(
                ticker=ticker,
                name=name,
                status="empty",
                source="stooq",
                error="stooq_empty",
            )

        raw = pd.read_csv(io.StringIO(body))
        if raw.empty:
            return FetchResult(
                ticker=ticker,
                name=name,
                status="empty",
                source="stooq",
                error="stooq_empty",
            )

        # Stooq columns usually: Date,Open,High,Low,Close,Volume
        df = normalize_price_df(raw, ticker=ticker, name=name, source="stooq")

        if df.empty:
            return FetchResult(
                ticker=ticker,
                name=name,
                status="empty",
                source="stooq",
                error="stooq_empty_after_normalize",
            )

        latest_value = str(max(df["date"]))[:10]

        return FetchResult(
            ticker=ticker,
            name=name,
            status="ok",
            source="stooq",
            df=df,
            bars=len(df),
            latest=latest_value,
        )

    except Exception as exc:
        return FetchResult(
            ticker=ticker,
            name=name,
            status="error",
            source="stooq",
            error=f"stooq_error: {type(exc).__name__}: {exc}",
        )


# =============================================================================
# Store helpers
# =============================================================================


def validate_price_frame(df: pd.DataFrame) -> None:
    if df is None:
        raise ValueError("price DataFrame is None")

    missing = [col for col in PRICE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"price DataFrame missing columns: {missing}")

    if df.empty:
        return

    if df["ticker"].isna().any():
        raise ValueError("price DataFrame contains null ticker")

    if df["date"].isna().any():
        raise ValueError("price DataFrame contains null date")

    # Ensure numeric columns are coercible.
    for col in NUMERIC_PRICE_COLUMNS:
        pd.to_numeric(df[col], errors="coerce")


def upsert_prices(conn, df: pd.DataFrame) -> int:
    validate_price_schema(conn)
    validate_price_frame(df)

    if df.empty:
        return 0

    work = df[PRICE_COLUMNS].copy()
    work["ticker"] = work["ticker"].astype(str)
    work["name"] = work["name"].fillna("").astype(str)
    work["source"] = work["source"].fillna("").astype(str)
    work["date"] = pd.to_datetime(work["date"], errors="coerce").dt.date
    work["fetched_at"] = pd.to_datetime(work["fetched_at"], errors="coerce")

    for col in ["open", "high", "low", "close", "adj_close"]:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    work["volume"] = pd.to_numeric(work["volume"], errors="coerce").fillna(0).astype("int64")

    work = work.dropna(subset=["ticker", "date"])
    work = work.drop_duplicates(subset=["ticker", "date"], keep="last")

    if work.empty:
        return 0

    conn.register("_incoming_prices_daily", work)

    try:
        # Delete overlapping ticker/date first, then insert.
        # This avoids depending on an existing primary key or MERGE support.
        conn.execute(
            """
            DELETE FROM prices_daily
            USING _incoming_prices_daily s
            WHERE prices_daily.ticker = s.ticker
              AND prices_daily.date = CAST(s.date AS DATE)
            """
        )

        conn.execute(
            """
            INSERT INTO prices_daily (
                ticker,
                name,
                date,
                open,
                high,
                low,
                close,
                adj_close,
                volume,
                source,
                fetched_at
            )
            SELECT
                CAST(ticker AS VARCHAR) AS ticker,
                CAST(name AS VARCHAR) AS name,
                CAST(date AS DATE) AS date,
                CAST(open AS DOUBLE) AS open,
                CAST(high AS DOUBLE) AS high,
                CAST(low AS DOUBLE) AS low,
                CAST(close AS DOUBLE) AS close,
                CAST(adj_close AS DOUBLE) AS adj_close,
                CAST(volume AS BIGINT) AS volume,
                CAST(source AS VARCHAR) AS source,
                CAST(fetched_at AS TIMESTAMP) AS fetched_at
            FROM _incoming_prices_daily
            """
        )
    finally:
        try:
            conn.unregister("_incoming_prices_daily")
        except Exception:
            pass

    return int(len(work))


def write_json_cache(out_dir: Path, df: pd.DataFrame) -> int:
    if df is None or df.empty:
        return 0

    json_dir = out_dir / "data" / "prices-jp"
    json_dir.mkdir(parents=True, exist_ok=True)

    written = 0

    for ticker, g in df.groupby("ticker"):
        safe = str(ticker).replace("/", "_")
        path = json_dir / f"{safe}.json"

        records: list[dict[str, Any]] = []
        for row in g.sort_values("date").to_dict(orient="records"):
            item = dict(row)
            for k, v in list(item.items()):
                if isinstance(v, (datetime, date)):
                    item[k] = v.isoformat()
                elif pd.isna(v):
                    item[k] = None
            records.append(item)

        payload = {
            "ticker": ticker,
            "name": str(g["name"].iloc[-1] or ""),
            "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "rows": records,
        }

        path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        written += len(records)

    return written


# =============================================================================
# Main fetch logic
# =============================================================================


def resolve_fetch_window(
    conn,
    ticker: str,
    fetch_mode: str,
    refresh_mode: str,
    default_start: date,
    default_end: date,
) -> tuple[Optional[date], Optional[date], bool]:
    """
    Returns:
        start, end, cache_hit
    """

    end = default_end

    if refresh_mode == "full":
        return default_start, end, False

    latest = get_latest_cached_date(conn, ticker)

    if latest is None:
        return default_start, end, False

    if latest >= end:
        return None, None, True

    # Incremental fetch from the day after latest cached date.
    start = latest + timedelta(days=1)

    if start > end:
        return None, None, True

    return start, end, False


def should_use_stooq_fallback(
    fetch_mode: str,
    yf_result: FetchResult,
    fallback_enabled: bool,
) -> bool:
    if not fallback_enabled:
        return False

    # Requested behavior:
    # live update:
    #   - yfinance empty -> skip immediately
    #   - yfinance error -> stooq fallback
    if fetch_mode == "live":
        return yf_result.status == "error"

    # Non-live modes can fallback for both empty and error.
    return yf_result.status in {"empty", "error"}


def fetch_one(
    item: TickerItem,
    start: date,
    end: date,
    fetch_mode: str,
    fallback_enabled: bool,
    yfinance_timeout: int,
    stooq_timeout: int,
) -> FetchResult:
    yf_result = fetch_yfinance(
        ticker=item.ticker,
        name=item.name,
        start=start,
        end=end,
        timeout_seconds=yfinance_timeout,
    )

    if yf_result.status == "ok":
        return yf_result

    if should_use_stooq_fallback(fetch_mode, yf_result, fallback_enabled):
        stooq_result = fetch_stooq(
            ticker=item.ticker,
            name=item.name,
            start=start,
            end=end,
            timeout_seconds=stooq_timeout,
        )

        if stooq_result.status == "ok":
            return stooq_result

        combined_error = "; ".join(
            x
            for x in [
                yf_result.error,
                stooq_result.error,
            ]
            if x
        )

        return FetchResult(
            ticker=item.ticker,
            name=item.name,
            status="error" if stooq_result.status == "error" else "empty",
            source="yfinance+stooq",
            error=combined_error,
        )

    # No fallback path.
    return yf_result


def print_header(
    total_tickers: int,
    fetch_mode: str,
    refresh_mode: str,
    fallback_enabled: bool,
    stooq_timeout: int,
    yfinance_timeout: int,
    store_mode: str,
    duckdb_path: Path,
    universe_csv: Path,
) -> None:
    print("=== JP price fetch ===")
    print(f"total tickers: {total_tickers}")
    print(f"fetch mode: {fetch_mode}")
    print(f"refresh mode: {refresh_mode}")
    print(f"fallback enabled/disabled: {'enabled' if fallback_enabled else 'disabled'}")
    print(f"stooq timeout seconds: {stooq_timeout}")
    print(f"yfinance timeout seconds: {yfinance_timeout}")
    print(f"store mode: {store_mode}")
    print(f"duckdb path: {duckdb_path}")
    print(f"universe csv: {universe_csv}")
    print("======================")


def print_summary(stats: Stats, fetch_mode: str, fallback_enabled: bool) -> None:
    print("=== JP price fetch summary ===")
    print(f"total tickers: {stats.total_tickers}")
    print(f"fetch mode: {fetch_mode}")
    print(f"fallback enabled/disabled: {'enabled' if fallback_enabled else 'disabled'}")
    print(f"cache hit count: {stats.cache_hit_count}")
    print(f"yfinance success count: {stats.yfinance_success_count}")
    print(f"stooq success count: {stats.stooq_success_count}")
    print(f"skipped count: {stats.skipped_count}")
    print(f"failed count: {stats.failed_count}")
    print(f"written rows: {stats.written_rows}")
    print("==============================")


def main() -> int:
    out_dir = Path(env_str("OUT_DIR", DEFAULT_OUT_DIR))
    duckdb_path = Path(env_str("PRICE_DUCKDB_PATH", DEFAULT_DUCKDB_PATH))
    universe_csv = Path(env_str("JP_UNIVERSE_CSV", DEFAULT_UNIVERSE_CSV))

    store_mode = env_str("PRICE_STORE_MODE", "json_and_duckdb").lower()
    fetch_mode = env_str("PRICE_FETCH_MODE", "live").lower()
    refresh_mode = env_str("PRICE_REFRESH_MODE", "incremental").lower()

    fallback_enabled = env_bool("STOOQ_FALLBACK_ENABLED", True)
    stooq_timeout = env_int("STOOQ_TIMEOUT_SECONDS", 3)
    yfinance_timeout = env_int("YFINANCE_TIMEOUT_SECONDS", 12)
    max_tickers = env_int("MAX_TICKERS", 0)

    start_date = parse_date(env_str("FETCH_START_DATE", DEFAULT_START_DATE))
    end_date = parse_date(env_str("FETCH_END_DATE", today_jst().isoformat()))

    if refresh_mode not in {"incremental", "full"}:
        raise ValueError(f"Invalid PRICE_REFRESH_MODE: {refresh_mode}")

    if fetch_mode not in {"live", "backfill", "manual"}:
        # Keep unknown modes usable, but make behavior explicit.
        print(f"Warning: unknown PRICE_FETCH_MODE={fetch_mode}; treating as live")
        fetch_mode = "live"

    if store_mode not in {"duckdb", "json", "json_and_duckdb"}:
        raise ValueError(f"Invalid PRICE_STORE_MODE: {store_mode}")

    if end_date < start_date:
        raise ValueError(f"FETCH_END_DATE is before FETCH_START_DATE: {start_date} -> {end_date}")

    universe = load_universe(universe_csv)
    if max_tickers > 0:
        universe = universe[:max_tickers]

    stats = Stats(total_tickers=len(universe))

    print_header(
        total_tickers=len(universe),
        fetch_mode=fetch_mode,
        refresh_mode=refresh_mode,
        fallback_enabled=fallback_enabled,
        stooq_timeout=stooq_timeout,
        yfinance_timeout=yfinance_timeout,
        store_mode=store_mode,
        duckdb_path=duckdb_path,
        universe_csv=universe_csv,
    )

    conn = None
    if store_mode in {"duckdb", "json_and_duckdb"}:
        conn = connect_duckdb(duckdb_path)
        ensure_price_schema(conn)

    all_fetched_frames: list[pd.DataFrame] = []

    try:
        for idx, item in enumerate(universe, start=1):
            prefix = f"[{idx}/{len(universe)}] Fetch {item.ticker}"
            if item.name:
                prefix += f" {item.name}"
            print(prefix)

            # If DuckDB is not enabled, no incremental cache check is possible.
            if conn is not None:
                fetch_start, fetch_end, cache_hit = resolve_fetch_window(
                    conn=conn,
                    ticker=item.ticker,
                    fetch_mode=fetch_mode,
                    refresh_mode=refresh_mode,
                    default_start=start_date,
                    default_end=end_date,
                )
                if cache_hit:
                    stats.cache_hit_count += 1
                    stats.skipped_count += 1
                    print("  SKIP cache_hit")
                    continue
            else:
                fetch_start, fetch_end = start_date, end_date

            if fetch_start is None or fetch_end is None:
                stats.cache_hit_count += 1
                stats.skipped_count += 1
                print("  SKIP cache_hit")
                continue

            result = fetch_one(
                item=item,
                start=fetch_start,
                end=fetch_end,
                fetch_mode=fetch_mode,
                fallback_enabled=fallback_enabled,
                yfinance_timeout=yfinance_timeout,
                stooq_timeout=stooq_timeout,
            )

            if result.status == "ok" and result.df is not None and not result.df.empty:
                if result.source == "yfinance":
                    stats.yfinance_success_count += 1
                elif result.source == "stooq":
                    stats.stooq_success_count += 1

                if conn is not None:
                    written = upsert_prices(conn, result.df)
                    stats.written_rows += written

                if store_mode in {"json", "json_and_duckdb"}:
                    all_fetched_frames.append(result.df)

                print(
                    f"  OK source={result.source} "
                    f"bars={result.bars} latest={result.latest}"
                )
                continue

            if result.status == "empty":
                stats.skipped_count += 1
                print(f"  SKIP insufficient_data errors=['{result.error}']")
                continue

            stats.failed_count += 1
            print(f"  FAIL errors=['{result.error}']")

        if store_mode in {"json", "json_and_duckdb"} and all_fetched_frames:
            merged = pd.concat(all_fetched_frames, ignore_index=True)
            write_json_cache(out_dir, merged)

        print_summary(stats, fetch_mode=fetch_mode, fallback_enabled=fallback_enabled)

        # In live mode, failed individual tickers should not necessarily fail the whole run.
        # But schema/data-structure exceptions should fail immediately because they are caught outside.
        if fetch_mode == "live":
            return 0

        return 1 if stats.failed_count > 0 else 0

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR unexpected failure: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise SystemExit(1)
