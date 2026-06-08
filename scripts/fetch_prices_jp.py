#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JP price fetcher for Neon Tokyo Signals / AI Arena JP.

Design:
- DuckDB table: prices_daily
- No "name" column in prices_daily. Name belongs to universe/metadata, not daily prices.
- yfinance empty result:
    - live mode: skip immediately
    - non-live mode: skip unless fallback is explicitly desired by changing logic
- yfinance exception:
    - fallback to Stooq only when fallback is enabled
- Stooq timeout defaults to 3 seconds.
- Defensive normalization for yfinance MultiIndex / adjusted columns / column casing.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd

try:
    import duckdb
except Exception as exc:
    print(f"ERROR missing dependency duckdb: {exc}", file=sys.stderr)
    raise

try:
    import requests
except Exception as exc:
    print(f"ERROR missing dependency requests: {exc}", file=sys.stderr)
    raise

try:
    import yfinance as yf
except Exception as exc:
    print(f"ERROR missing dependency yfinance: {exc}", file=sys.stderr)
    raise


DEFAULT_DUCKDB_PATH = "data/cache/neon_tokyo_jp.duckdb"
DEFAULT_UNIVERSE_CSV = "data/universe/jp_duckdb_trial_300.csv"
DEFAULT_JSON_DIR = "data/cache/prices_jp"

PRICES_TABLE = "prices_daily"

REQUIRED_PRICE_COLUMNS = {
    "ticker": "VARCHAR",
    "date": "DATE",
    "open": "DOUBLE",
    "high": "DOUBLE",
    "low": "DOUBLE",
    "close": "DOUBLE",
    "adj_close": "DOUBLE",
    "volume": "BIGINT",
    "traded_value_jpy": "DOUBLE",
    "source": "VARCHAR",
    "updated_at": "TIMESTAMP",
}

PRICE_INSERT_COLUMNS = list(REQUIRED_PRICE_COLUMNS.keys())

CREATE_PRICES_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {PRICES_TABLE} (
    ticker VARCHAR,
    date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    adj_close DOUBLE,
    volume BIGINT,
    traded_value_jpy DOUBLE,
    source VARCHAR,
    updated_at TIMESTAMP
)
"""


@dataclass(frozen=True)
class UniverseItem:
    ticker: str
    name: str = ""


@dataclass
class FetchResult:
    ticker: str
    name: str
    status: str
    source: str = ""
    df: Optional[pd.DataFrame] = None
    latest: str = ""
    bars: int = 0
    errors: list[str] | None = None
    cache_hit: bool = False
    yfinance_success: bool = False
    skipped: bool = False
    failed: bool = False

    def error_list(self) -> list[str]:
        return self.errors or []


@dataclass
class Counters:
    total_tickers: int = 0
    cache_hit_count: int = 0
    yfinance_success_count: int = 0
    stooq_success_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    inserted_rows: int = 0
    processed_count: int = 0


def env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip()


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(str(value).strip())
    except ValueError:
        return default


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "enabled", "enable"}


def parse_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    if not s:
        raise ValueError("empty date")
    return datetime.fromisoformat(s[:10]).date()


def today_jst_like() -> date:
    # GitHub Actions is usually UTC. For JP market cache purposes, using current UTC date
    # is acceptable because explicit end date is normally supplied by workflow/env.
    return datetime.utcnow().date()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def connect_duckdb(path: Path) -> duckdb.DuckDBPyConnection:
    ensure_parent(path)
    return duckdb.connect(str(path))


def table_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    rows = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = ?
        """,
        [table_name],
    ).fetchone()
    return bool(rows and rows[0] > 0)


def get_table_columns(conn: duckdb.DuckDBPyConnection, table_name: str) -> dict[str, str]:
    if not table_exists(conn, table_name):
        return {}
    rows = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    result: dict[str, str] = {}
    for row in rows:
        # DuckDB PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
        result[str(row[1])] = str(row[2])
    return result


def ensure_prices_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(CREATE_PRICES_TABLE_SQL)

    existing = get_table_columns(conn, PRICES_TABLE)
    missing = [col for col in REQUIRED_PRICE_COLUMNS if col not in existing]

    for col in missing:
        col_type = REQUIRED_PRICE_COLUMNS[col]
        conn.execute(f"ALTER TABLE {PRICES_TABLE} ADD COLUMN {col} {col_type}")

    existing_after = get_table_columns(conn, PRICES_TABLE)
    missing_after = [col for col in REQUIRED_PRICE_COLUMNS if col not in existing_after]
    if missing_after:
        raise RuntimeError(f"prices_daily schema validation failed. missing={missing_after}")

    # Intentionally do not require or add "name".
    # If an old broken table has "name", leave it alone; upsert will not use it.


def read_universe_csv(path: Path) -> list[UniverseItem]:
    if not path.exists():
        raise FileNotFoundError(f"universe csv not found: {path}")

    items: list[UniverseItem] = []
    seen: set[str] = set()

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"universe csv has no header: {path}")

        lower_map = {c.lower().strip(): c for c in reader.fieldnames}
        ticker_col = (
            lower_map.get("ticker")
            or lower_map.get("symbol")
            or lower_map.get("code")
            or lower_map.get("銘柄コード")
        )
        name_col = (
            lower_map.get("name")
            or lower_map.get("company")
            or lower_map.get("company_name")
            or lower_map.get("銘柄名")
        )

        if not ticker_col:
            raise ValueError(
                f"universe csv must have ticker/symbol/code column. columns={reader.fieldnames}"
            )

        for row in reader:
            raw_ticker = str(row.get(ticker_col, "")).strip()
            if not raw_ticker:
                continue
            ticker = normalize_jp_ticker(raw_ticker)
            if not ticker or ticker in seen:
                continue
            seen.add(ticker)
            name = str(row.get(name_col, "")).strip() if name_col else ""
            items.append(UniverseItem(ticker=ticker, name=name))

    if not items:
        raise ValueError(f"universe csv produced zero tickers: {path}")

    return items


def normalize_jp_ticker(raw: str) -> str:
    s = str(raw).strip().upper()
    if not s:
        return ""
    s = s.replace(".JP", ".T")
    if s.endswith(".T"):
        return s
    if s.isdigit():
        return f"{s}.T"
    return s


def ticker_to_stooq_symbol(ticker: str) -> str:
    s = normalize_jp_ticker(ticker)
    if s.endswith(".T"):
        return s.replace(".T", ".JP")
    return s


def get_latest_cached_date(
    conn: duckdb.DuckDBPyConnection,
    ticker: str,
) -> Optional[date]:
    try:
        row = conn.execute(
            f"SELECT MAX(date) FROM {PRICES_TABLE} WHERE ticker = ?",
            [ticker],
        ).fetchone()
        if not row or row[0] is None:
            return None
        return parse_date(row[0])
    except Exception:
        return None


def get_cached_bars_count(
    conn: duckdb.DuckDBPyConnection,
    ticker: str,
) -> int:
    try:
        row = conn.execute(
            f"SELECT COUNT(*) FROM {PRICES_TABLE} WHERE ticker = ?",
            [ticker],
        ).fetchone()
        return int(row[0] or 0) if row else 0
    except Exception:
        return 0


def should_use_cache(
    latest_cached: Optional[date],
    end_date: date,
    refresh_mode: str,
) -> bool:
    if latest_cached is None:
        return False

    refresh_mode = refresh_mode.lower().strip()

    if refresh_mode in {"full", "force", "rebuild"}:
        return False

    # JP market latest can be previous business day. Allow same day or later only here.
    # Workflow can choose incremental to fetch gaps.
    return latest_cached >= end_date


def normalize_price_dataframe(
    raw: pd.DataFrame,
    ticker: str,
    source: str,
) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()

    df = raw.copy()

    # yfinance can return MultiIndex columns.
    if isinstance(df.columns, pd.MultiIndex):
        # Case 1: one ticker, columns like ('Close', '7203.T')
        # Case 2: group_by variations.
        new_cols: list[str] = []
        for col in df.columns:
            parts = [str(x) for x in col if str(x) and str(x) != "nan"]
            lower_parts = [p.lower() for p in parts]

            known = None
            for candidate in ["open", "high", "low", "close", "adj close", "volume"]:
                if candidate in lower_parts:
                    known = candidate
                    break

            if known:
                new_cols.append(known)
            elif parts:
                new_cols.append(parts[0].lower())
            else:
                new_cols.append("")
        df.columns = new_cols
    else:
        df.columns = [str(c).strip().lower() for c in df.columns]

    # Normalize common column aliases. Preserve adjusted close separately when available.
    rename_map = {
        "adj close": "adj_close",
        "adjusted close": "adj_close",
        "open price": "open",
        "high price": "high",
        "low price": "low",
        "close price": "close",
        "vol": "volume",
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    # If duplicate columns appear after rename, keep first non-null by bfill.
    if len(set(df.columns)) != len(df.columns):
        merged = pd.DataFrame(index=df.index)
        for col in dict.fromkeys(df.columns):
            same = df.loc[:, df.columns == col]
            if isinstance(same, pd.Series):
                merged[col] = same
            else:
                merged[col] = same.bfill(axis=1).iloc[:, 0]
        df = merged

    # Date handling.
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    else:
        idx = df.index
        df = df.reset_index()
        date_col = None
        for c in df.columns:
            if str(c).strip().lower() in {"date", "datetime", "index"}:
                date_col = c
                break
        if date_col is None:
            # Last resort: original index
            df["date"] = pd.to_datetime(idx, errors="coerce").date
        else:
            df["date"] = pd.to_datetime(df[date_col], errors="coerce").dt.date

    required_ohlc = ["open", "high", "low", "close"]
    for col in required_ohlc:
        if col not in df.columns:
            return pd.DataFrame()

    if "volume" not in df.columns:
        df["volume"] = 0

    keep_cols = ["date", "open", "high", "low", "close", "volume"]
    if "adj_close" in df.columns:
        keep_cols.append("adj_close")
    out = df[keep_cols].copy()
    out["ticker"] = ticker
    out["source"] = source
    out["updated_at"] = datetime.utcnow()

    for col in ["open", "high", "low", "close", "adj_close"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "adj_close" not in out.columns:
        out["adj_close"] = out["close"]
    out["adj_close"] = out["adj_close"].fillna(out["close"])

    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").fillna(0).astype("int64")
    out["traded_value_jpy"] = out["close"] * out["volume"]
    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    out = out[out["close"] > 0]
    out = out.drop_duplicates(subset=["ticker", "date"], keep="last")
    out = out.sort_values(["ticker", "date"])

    return out[PRICE_INSERT_COLUMNS]


def fetch_yfinance_raw(
    ticker: str,
    start_date: date,
    end_date: date,
    timeout_seconds: int,
) -> pd.DataFrame:
    # yfinance end is exclusive-ish. Add one day to avoid missing end_date.
    yf_end = end_date + timedelta(days=1)

    # timeout parameter is supported in recent yfinance.
    return yf.download(
        tickers=ticker,
        start=start_date.isoformat(),
        end=yf_end.isoformat(),
        interval="1d",
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
        timeout=timeout_seconds,
        group_by="column",
    )


def fetch_yfinance(
    ticker: str,
    start_date: date,
    end_date: date,
    timeout_seconds: int,
    debug_raw: bool,
) -> tuple[pd.DataFrame, list[str], bool]:
    errors: list[str] = []

    try:
        raw = fetch_yfinance_raw(ticker, start_date, end_date, timeout_seconds)
    except Exception as exc:
        errors.append(f"yfinance_exception:{type(exc).__name__}:{str(exc)[:300]}")
        return pd.DataFrame(), errors, False

    if raw is None or raw.empty:
        errors.append("yfinance_empty")
        return pd.DataFrame(), errors, True

    normalized = normalize_price_dataframe(raw, ticker=ticker, source="yfinance")

    if normalized.empty:
        errors.append("yfinance_empty_after_normalize")
        if debug_raw:
            print("  DEBUG yfinance raw non-empty but normalized empty")
            print(f"  DEBUG raw shape={getattr(raw, 'shape', None)}")
            print(f"  DEBUG raw columns={list(raw.columns)}")
            try:
                print("  DEBUG raw head:")
                print(raw.head(3).to_string())
            except Exception:
                pass
        return pd.DataFrame(), errors, True

    return normalized, errors, True


def fetch_stooq(
    ticker: str,
    start_date: date,
    end_date: date,
    timeout_seconds: int,
) -> tuple[pd.DataFrame, list[str]]:
    errors: list[str] = []
    symbol = ticker_to_stooq_symbol(ticker)

    url = "https://stooq.com/q/d/l/"
    params = {
        "s": symbol.lower(),
        "i": "d",
        "d1": start_date.strftime("%Y%m%d"),
        "d2": end_date.strftime("%Y%m%d"),
    }

    try:
        resp = requests.get(url, params=params, timeout=timeout_seconds)
        resp.raise_for_status()
    except Exception as exc:
        errors.append(f"stooq_error:{type(exc).__name__}:{str(exc)[:300]}")
        return pd.DataFrame(), errors

    text = resp.text.strip()
    if not text or text.lower().startswith("no data"):
        errors.append("stooq_empty")
        return pd.DataFrame(), errors

    try:
        from io import StringIO

        raw = pd.read_csv(StringIO(text))
    except Exception as exc:
        errors.append(f"stooq_parse_error:{type(exc).__name__}:{str(exc)[:300]}")
        return pd.DataFrame(), errors

    if raw.empty:
        errors.append("stooq_empty")
        return pd.DataFrame(), errors

    normalized = normalize_price_dataframe(raw, ticker=ticker, source="stooq")
    if normalized.empty:
        errors.append("stooq_empty_after_normalize")
        return pd.DataFrame(), errors

    return normalized, errors


def filter_incremental_rows(
    df: pd.DataFrame,
    latest_cached: Optional[date],
    refresh_mode: str,
) -> pd.DataFrame:
    if df.empty:
        return df

    if latest_cached is None:
        return df

    if refresh_mode.lower().strip() in {"full", "force", "rebuild"}:
        return df

    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    out = out[out["date"] > latest_cached]
    return out


def upsert_prices(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> int:
    if df is None or df.empty:
        return 0

    required_cols = PRICE_INSERT_COLUMNS
    if "adj_close" not in df.columns and "close" in df.columns:
        df = df.copy()
        df["adj_close"] = df["close"]
    if "traded_value_jpy" not in df.columns and {"close", "volume"}.issubset(df.columns):
        df = df.copy()
        df["traded_value_jpy"] = pd.to_numeric(df["close"], errors="coerce") * pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"upsert dataframe missing required columns: {missing}")

    clean = df[required_cols].copy()
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce").dt.date
    clean["updated_at"] = pd.to_datetime(clean["updated_at"], errors="coerce")
    clean["adj_close"] = pd.to_numeric(clean["adj_close"], errors="coerce").fillna(pd.to_numeric(clean["close"], errors="coerce"))
    clean["traded_value_jpy"] = pd.to_numeric(clean["traded_value_jpy"], errors="coerce")

    clean = clean.dropna(subset=["ticker", "date", "open", "high", "low", "close"])
    clean = clean.drop_duplicates(subset=["ticker", "date"], keep="last")

    if clean.empty:
        return 0

    conn.register("incoming_prices", clean)

    # Do not reference "name".
    conn.execute(
        f"""
        DELETE FROM {PRICES_TABLE}
        USING incoming_prices
        WHERE {PRICES_TABLE}.ticker = incoming_prices.ticker
          AND {PRICES_TABLE}.date = incoming_prices.date
        """
    )

    conn.execute(
        f"""
        INSERT INTO {PRICES_TABLE}
            (ticker, date, open, high, low, close, adj_close, volume, traded_value_jpy, source, updated_at)
        SELECT
            ticker, date, open, high, low, close, adj_close, volume, traded_value_jpy, source, updated_at
        FROM incoming_prices
        """
    )

    conn.unregister("incoming_prices")
    return int(len(clean))


def write_json_cache(json_dir: Path, ticker: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return

    json_dir.mkdir(parents=True, exist_ok=True)
    safe = ticker.replace("/", "_").replace("\\", "_")
    path = json_dir / f"{safe}.json"

    out = df.copy()
    out["date"] = out["date"].astype(str)
    out["updated_at"] = out["updated_at"].astype(str)

    records = out.sort_values("date").to_dict(orient="records")
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def fetch_one(
    item: UniverseItem,
    conn: duckdb.DuckDBPyConnection,
    start_date: date,
    end_date: date,
    fetch_mode: str,
    refresh_mode: str,
    fallback_enabled: bool,
    yfinance_timeout_seconds: int,
    stooq_timeout_seconds: int,
    min_acceptable_bars: int,
    debug_raw_limit_remaining: int,
) -> FetchResult:
    ticker = item.ticker
    errors: list[str] = []

    latest_cached = get_latest_cached_date(conn, ticker)
    cached_bars = get_cached_bars_count(conn, ticker)

    if should_use_cache(latest_cached, end_date, refresh_mode):
        return FetchResult(
            ticker=ticker,
            name=item.name,
            status="CACHE_HIT",
            source="duckdb_cache",
            latest=latest_cached.isoformat() if latest_cached else "",
            bars=cached_bars,
            errors=[],
            cache_hit=True,
        )

    fetch_start = start_date
    if latest_cached and refresh_mode.lower().strip() not in {"full", "force", "rebuild"}:
        fetch_start = latest_cached + timedelta(days=1)

    debug_raw = debug_raw_limit_remaining > 0

    yf_df, yf_errors, yf_completed = fetch_yfinance(
        ticker=ticker,
        start_date=fetch_start,
        end_date=end_date,
        timeout_seconds=yfinance_timeout_seconds,
        debug_raw=debug_raw,
    )
    errors.extend(yf_errors)

    if not yf_df.empty:
        yf_df = filter_incremental_rows(yf_df, latest_cached, refresh_mode)
        if yf_df.empty:
            return FetchResult(
                ticker=ticker,
                name=item.name,
                status="CACHE_CURRENT_AFTER_YF",
                source="duckdb_cache+yfinance",
                latest=latest_cached.isoformat() if latest_cached else "",
                bars=cached_bars,
                errors=errors,
                cache_hit=True,
                yfinance_success=True,
            )

        return FetchResult(
            ticker=ticker,
            name=item.name,
            status="OK",
            source="duckdb_cache+yfinance" if latest_cached else "yfinance",
            df=yf_df,
            latest=str(max(yf_df["date"])),
            bars=len(yf_df),
            errors=errors,
            yfinance_success=True,
        )

    # Important rule:
    # yfinance_empty means no fallback in live mode.
    if "yfinance_empty" in errors and fetch_mode.lower().strip() == "live":
        return FetchResult(
            ticker=ticker,
            name=item.name,
            status="SKIP",
            source="yfinance",
            latest=latest_cached.isoformat() if latest_cached else "",
            bars=cached_bars,
            errors=errors,
            skipped=True,
        )

    # yfinance_empty_after_normalize indicates a likely parser/schema problem.
    # Treat as failed to avoid hiding a common bug as insufficient_data.
    if "yfinance_empty_after_normalize" in errors:
        return FetchResult(
            ticker=ticker,
            name=item.name,
            status="FAIL",
            source="yfinance",
            latest=latest_cached.isoformat() if latest_cached else "",
            bars=cached_bars,
            errors=errors,
            failed=True,
        )

    # Fallback only on yfinance exception or non-live empty when enabled.
    should_fallback = fallback_enabled and any(e.startswith("yfinance_exception") for e in errors)

    if not should_fallback:
        return FetchResult(
            ticker=ticker,
            name=item.name,
            status="SKIP",
            source="yfinance",
            latest=latest_cached.isoformat() if latest_cached else "",
            bars=cached_bars,
            errors=errors,
            skipped=True,
        )

    stooq_df, stooq_errors = fetch_stooq(
        ticker=ticker,
        start_date=fetch_start,
        end_date=end_date,
        timeout_seconds=stooq_timeout_seconds,
    )
    errors.extend(stooq_errors)

    if not stooq_df.empty:
        stooq_df = filter_incremental_rows(stooq_df, latest_cached, refresh_mode)
        if stooq_df.empty:
            return FetchResult(
                ticker=ticker,
                name=item.name,
                status="CACHE_CURRENT_AFTER_STOOQ",
                source="duckdb_cache+stooq",
                latest=latest_cached.isoformat() if latest_cached else "",
                bars=cached_bars,
                errors=errors,
                cache_hit=True,
            )

        if len(stooq_df) < min_acceptable_bars and latest_cached is None:
            return FetchResult(
                ticker=ticker,
                name=item.name,
                status="SKIP",
                source="stooq",
                latest=str(max(stooq_df["date"])) if not stooq_df.empty else "",
                bars=len(stooq_df),
                errors=errors + ["insufficient_data"],
                skipped=True,
            )

        return FetchResult(
            ticker=ticker,
            name=item.name,
            status="OK",
            source="duckdb_cache+stooq" if latest_cached else "stooq",
            df=stooq_df,
            latest=str(max(stooq_df["date"])),
            bars=len(stooq_df),
            errors=errors,
        )

    return FetchResult(
        ticker=ticker,
        name=item.name,
        status="FAIL",
        source="yfinance+stooq",
        latest=latest_cached.isoformat() if latest_cached else "",
        bars=cached_bars,
        errors=errors,
        failed=True,
    )


def print_header(
    total_tickers: int,
    fetch_mode: str,
    refresh_mode: str,
    fallback_enabled: bool,
    stooq_timeout_seconds: int,
    yfinance_timeout_seconds: int,
    store_mode: str,
    duckdb_path: Path,
    universe_csv: Path,
    start_date: date,
    end_date: date,
) -> None:
    print("=== JP price fetch ===")
    print(f"total tickers: {total_tickers}")
    print(f"fetch mode: {fetch_mode}")
    print(f"refresh mode: {refresh_mode}")
    print(f"fallback enabled/disabled: {'enabled' if fallback_enabled else 'disabled'}")
    print(f"stooq timeout seconds: {stooq_timeout_seconds}")
    print(f"yfinance timeout seconds: {yfinance_timeout_seconds}")
    print(f"store mode: {store_mode}")
    print(f"duckdb path: {duckdb_path}")
    print(f"universe csv: {universe_csv}")
    print(f"start date: {start_date.isoformat()}")
    print(f"end date: {end_date.isoformat()}")
    print("======================")


def print_result_line(index: int, total: int, item: UniverseItem, result: FetchResult) -> None:
    label_name = f" {item.name}" if item.name else ""
    print(f"[{index}/{total}] Fetch {item.ticker}{label_name}")

    if result.status == "OK":
        print(f"  OK source={result.source} bars={result.bars} latest={result.latest}")
    elif result.status in {"CACHE_HIT", "CACHE_CURRENT_AFTER_YF", "CACHE_CURRENT_AFTER_STOOQ"}:
        print(f"  CACHE source={result.source} bars={result.bars} latest={result.latest}")
    elif result.status == "SKIP":
        print(f"  SKIP source={result.source} bars={result.bars} latest={result.latest} errors={result.error_list()}")
    else:
        print(f"  FAIL source={result.source} bars={result.bars} latest={result.latest} errors={result.error_list()}")


def print_summary(counters: Counters, fetch_mode: str, fallback_enabled: bool) -> None:
    print("=== JP price fetch summary ===")
    print(f"total tickers: {counters.total_tickers}")
    print(f"fetch mode: {fetch_mode}")
    print(f"fallback enabled/disabled: {'enabled' if fallback_enabled else 'disabled'}")
    print(f"cache hit count: {counters.cache_hit_count}")
    print(f"yfinance success count: {counters.yfinance_success_count}")
    print(f"stooq success count: {counters.stooq_success_count}")
    print(f"skipped count: {counters.skipped_count}")
    print(f"failed count: {counters.failed_count}")
    print(f"inserted rows: {counters.inserted_rows}")
    print("==============================")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fetch JP daily prices into DuckDB/JSON cache.")

    p.add_argument("--duckdb-path", default=env_str("PRICE_DUCKDB_PATH", DEFAULT_DUCKDB_PATH))
    p.add_argument("--universe-csv", default=env_str("JP_UNIVERSE_CSV", DEFAULT_UNIVERSE_CSV))
    p.add_argument("--json-dir", default=env_str("PRICE_JSON_DIR", DEFAULT_JSON_DIR))

    p.add_argument("--start", default=env_str("PRICE_START_DATE", "2025-01-01"))
    p.add_argument("--end", default=env_str("PRICE_END_DATE", today_jst_like().isoformat()))

    p.add_argument("--fetch-mode", default=env_str("PRICE_FETCH_MODE", env_str("FETCH_MODE", "live")))
    p.add_argument("--refresh-mode", default=env_str("PRICE_REFRESH_MODE", env_str("REFRESH_MODE", "incremental")))
    p.add_argument("--store-mode", default=env_str("PRICE_STORE_MODE", "json_and_duckdb"))

    p.add_argument("--fallback-enabled", default=None)
    p.add_argument("--stooq-timeout-seconds", type=int, default=env_int("STOOQ_TIMEOUT_SECONDS", 3))
    p.add_argument("--yfinance-timeout-seconds", type=int, default=env_int("YFINANCE_TIMEOUT_SECONDS", 12))

    p.add_argument("--min-acceptable-bars", type=int, default=env_int("MIN_ACCEPTABLE_BARS", 20))
    p.add_argument("--max-tickers", type=int, default=env_int("MAX_TICKERS", 0))
    p.add_argument("--sleep-seconds", type=float, default=float(env_str("PRICE_FETCH_SLEEP_SECONDS", "0")))
    p.add_argument("--debug-raw-limit", type=int, default=env_int("YFINANCE_DEBUG_RAW_LIMIT", 3))

    return p


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    duckdb_path = Path(args.duckdb_path)
    universe_csv = Path(args.universe_csv)
    json_dir = Path(args.json_dir)

    start_date = parse_date(args.start)
    end_date = parse_date(args.end)

    if end_date < start_date:
        raise ValueError(f"end date must be >= start date. start={start_date} end={end_date}")

    fetch_mode = str(args.fetch_mode).strip().lower()
    refresh_mode = str(args.refresh_mode).strip().lower()
    store_mode = str(args.store_mode).strip().lower()

    if args.fallback_enabled is None:
        fallback_enabled = env_bool("STOOQ_FALLBACK_ENABLED", True)
    else:
        fallback_enabled = str(args.fallback_enabled).strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
            "enabled",
        }

    conn: Optional[duckdb.DuckDBPyConnection] = None
    counters = Counters()

    try:
        items = read_universe_csv(universe_csv)
        if int(args.max_tickers or 0) > 0:
            items = items[: int(args.max_tickers)]

        counters.total_tickers = len(items)

        print_header(
            total_tickers=counters.total_tickers,
            fetch_mode=fetch_mode,
            refresh_mode=refresh_mode,
            fallback_enabled=fallback_enabled,
            stooq_timeout_seconds=int(args.stooq_timeout_seconds),
            yfinance_timeout_seconds=int(args.yfinance_timeout_seconds),
            store_mode=store_mode,
            duckdb_path=duckdb_path,
            universe_csv=universe_csv,
            start_date=start_date,
            end_date=end_date,
        )

        conn = connect_duckdb(duckdb_path)
        ensure_prices_schema(conn)

        debug_raw_remaining = int(args.debug_raw_limit or 0)

        for idx, item in enumerate(items, start=1):
            result = fetch_one(
                item=item,
                conn=conn,
                start_date=start_date,
                end_date=end_date,
                fetch_mode=fetch_mode,
                refresh_mode=refresh_mode,
                fallback_enabled=fallback_enabled,
                yfinance_timeout_seconds=int(args.yfinance_timeout_seconds),
                stooq_timeout_seconds=int(args.stooq_timeout_seconds),
                min_acceptable_bars=int(args.min_acceptable_bars),
                debug_raw_limit_remaining=debug_raw_remaining,
            )

            if "yfinance_empty_after_normalize" in result.error_list() and debug_raw_remaining > 0:
                debug_raw_remaining -= 1

            print_result_line(idx, counters.total_tickers, item, result)

            counters.processed_count += 1

            if result.cache_hit:
                counters.cache_hit_count += 1

            if result.yfinance_success:
                counters.yfinance_success_count += 1

            if result.status == "OK" and "stooq" in result.source:
                counters.stooq_success_count += 1

            if result.skipped or result.status == "SKIP":
                counters.skipped_count += 1

            if result.failed or result.status == "FAIL":
                counters.failed_count += 1

            if result.status == "OK" and result.df is not None and not result.df.empty:
                inserted = 0

                if store_mode in {"duckdb", "json_and_duckdb", "duckdb_and_json"}:
                    inserted = upsert_prices(conn, result.df)
                    counters.inserted_rows += inserted

                if store_mode in {"json", "json_and_duckdb", "duckdb_and_json"}:
                    write_json_cache(json_dir, item.ticker, result.df)

            if args.sleep_seconds and float(args.sleep_seconds) > 0:
                time.sleep(float(args.sleep_seconds))

        print_summary(counters, fetch_mode=fetch_mode, fallback_enabled=fallback_enabled)

        # Hard fail only on actual failures, not skips.
        # If every ticker was skipped, fail because live update produced no useful data.
        if counters.failed_count > 0:
            print(f"ERROR failed tickers detected: {counters.failed_count}", file=sys.stderr)
            return 1

        if counters.yfinance_success_count == 0 and counters.stooq_success_count == 0 and counters.cache_hit_count == 0:
            print(
                "ERROR no successful fetch/cache result. Possible yfinance outage, API block, or normalization bug.",
                file=sys.stderr,
            )
            return 1

        return 0

    except Exception as exc:
        print(f"ERROR unexpected failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
