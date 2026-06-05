#!/usr/bin/env python3
from __future__ import annotations

"""
Fetch Japanese equity prices for Neon Tokyo Signals.

Design:
- Primary source: yfinance
- Fallback source: Stooq
- Live/update mode:
    - yfinance empty       -> SKIP immediately
    - yfinance error       -> Stooq fallback only if enabled
    - Stooq timeout        -> 3 seconds by default
- Writes:
    - DuckDB table: prices_daily
    - compatibility view: prices_daily_jp
    - public JSON: site/data/prices-jp/latest.json
    - manifest: site/data/prices-jp/manifest.json

Key env vars:
- UNIVERSE_CSV
- OUT_DIR
- PRICE_DUCKDB_PATH
- PRICE_STORE_MODE
- PRICE_PUBLIC_JSON_MODE
- WRITE_DATED_PRICE_JSON
- FETCH_MODE
- PRICE_REFRESH_MODE
- ENABLE_STOOQ_FALLBACK
- STOOQ_TIMEOUT_SECONDS
- YFINANCE_TIMEOUT_SECONDS
- LOOKBACK_DAYS
- PRICE_INCREMENTAL_OVERLAP_DAYS
- MIN_BARS_REQUIRED
- MIN_ACCEPTABLE_BARS
"""

import csv
import io
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

JST = timezone(timedelta(hours=9))

OUT_DIR = ROOT / os.getenv("OUT_DIR", "site")
UNIVERSE_CSV = ROOT / os.getenv("UNIVERSE_CSV", "data/universe/jp_duckdb_trial_300.csv")
PRICE_DUCKDB_PATH = ROOT / os.getenv("PRICE_DUCKDB_PATH", "data/cache/neon_tokyo_jp.duckdb")

PRICE_STORE_MODE = os.getenv("PRICE_STORE_MODE", "json_and_duckdb").strip().lower()
PRICE_PUBLIC_JSON_MODE = os.getenv("PRICE_PUBLIC_JSON_MODE", "summary").strip().lower()
WRITE_DATED_PRICE_JSON = os.getenv("WRITE_DATED_PRICE_JSON", "false").strip().lower() in {"1", "true", "yes", "y"}

FETCH_MODE = os.getenv("FETCH_MODE", os.getenv("PRICE_FETCH_MODE", "live")).strip().lower()
PRICE_REFRESH_MODE = os.getenv("PRICE_REFRESH_MODE", "incremental").strip().lower()

ENABLE_STOOQ_FALLBACK = os.getenv("ENABLE_STOOQ_FALLBACK", "true").strip().lower() in {"1", "true", "yes", "y"}
STOOQ_TIMEOUT_SECONDS = float(os.getenv("STOOQ_TIMEOUT_SECONDS", "3"))
YFINANCE_TIMEOUT_SECONDS = float(os.getenv("YFINANCE_TIMEOUT_SECONDS", "12"))

LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "520"))
PRICE_INCREMENTAL_OVERLAP_DAYS = int(os.getenv("PRICE_INCREMENTAL_OVERLAP_DAYS", "10"))

MIN_BARS_REQUIRED = int(os.getenv("MIN_BARS_REQUIRED", "60"))
MIN_ACCEPTABLE_BARS = int(os.getenv("MIN_ACCEPTABLE_BARS", "20"))

SLEEP_SECONDS = float(os.getenv("PRICE_FETCH_SLEEP_SECONDS", "0.05"))
MAX_TICKERS = int(os.getenv("MAX_TICKERS", "0"))

PRICES_OUT_DIR = OUT_DIR / "data" / "prices-jp"
LATEST_JSON = PRICES_OUT_DIR / "latest.json"
MANIFEST_JSON = PRICES_OUT_DIR / "manifest.json"


@dataclass
class TickerItem:
    ticker: str
    name: str = ""


@dataclass
class FetchResult:
    ticker: str
    name: str
    status: str
    source: str = ""
    bars: int = 0
    latest_date: str = ""
    errors: list[str] | None = None
    df: pd.DataFrame | None = None


def now_jst() -> datetime:
    return datetime.now(JST)


def iso_now() -> str:
    return now_jst().isoformat(timespec="seconds")


def previous_business_day_jst(today: date | None = None) -> date:
    d = today or now_jst().date()
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def safe_float(v: Any) -> float | None:
    try:
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None


def safe_int(v: Any) -> int | None:
    try:
        if pd.isna(v):
            return None
        return int(float(v))
    except Exception:
        return None


def normalize_ticker(raw: Any) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    s = s.replace(".JP", ".T")
    if s.isdigit():
        return f"{s}.T"
    return s


def stooq_symbol(ticker: str) -> str:
    t = normalize_ticker(ticker)
    if t.endswith(".T"):
        return t[:-2] + ".JP"
    return t


def read_universe(path: Path) -> list[TickerItem]:
    if not path.exists():
        raise FileNotFoundError(f"UNIVERSE_CSV not found: {path}")

    rows: list[TickerItem] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"UNIVERSE_CSV has no header: {path}")

        fields = {c.lower(): c for c in reader.fieldnames}
        ticker_col = (
            fields.get("ticker")
            or fields.get("symbol")
            or fields.get("code")
            or fields.get("銘柄コード")
        )
        name_col = (
            fields.get("name")
            or fields.get("company_name")
            or fields.get("company")
            or fields.get("銘柄名")
        )

        if not ticker_col:
            raise ValueError(
                f"UNIVERSE_CSV must have ticker/symbol/code column. fields={reader.fieldnames}"
            )

        for row in reader:
            ticker = normalize_ticker(row.get(ticker_col))
            if not ticker:
                continue
            name = str(row.get(name_col) or "").strip() if name_col else ""
            rows.append(TickerItem(ticker=ticker, name=name))

    seen: set[str] = set()
    unique: list[TickerItem] = []
    for item in rows:
        if item.ticker in seen:
            continue
        seen.add(item.ticker)
        unique.append(item)

    if MAX_TICKERS > 0:
        unique = unique[:MAX_TICKERS]

    return unique


def import_duckdb():
    try:
        import duckdb  # type: ignore

        return duckdb
    except Exception as exc:
        raise RuntimeError(
            "duckdb is required when PRICE_STORE_MODE includes duckdb. "
            "Install it in requirements-render.txt."
        ) from exc


def connect_duckdb():
    PRICE_DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    duckdb = import_duckdb()
    return duckdb.connect(str(PRICE_DUCKDB_PATH))


def ensure_price_schema(conn) -> None:
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
            fetched_at TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
        """
    )

    # Compatibility view for scripts that refer to prices_daily_jp.
    try:
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
    except Exception:
        # If an older repo already has a table named prices_daily_jp, do not fail.
        pass


def existing_latest_date(conn, ticker: str) -> date | None:
    try:
        row = conn.execute(
            "SELECT MAX(date) FROM prices_daily WHERE ticker = ?",
            [ticker],
        ).fetchone()
        if not row or row[0] is None:
            return None
        value = row[0]
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def decide_start_date(conn, ticker: str) -> date:
    today = now_jst().date()
    default_start = today - timedelta(days=LOOKBACK_DAYS)

    if PRICE_REFRESH_MODE not in {"incremental", "update", "live"}:
        return default_start

    latest = existing_latest_date(conn, ticker)
    if not latest:
        return default_start

    return max(default_start, latest - timedelta(days=PRICE_INCREMENTAL_OVERLAP_DAYS))


def normalize_price_frame(df: pd.DataFrame, ticker: str, name: str, source: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    work = df.copy()

    if isinstance(work.columns, pd.MultiIndex):
        work.columns = [
            "_".join([str(x) for x in col if str(x) and str(x) != ticker]).strip("_")
            for col in work.columns
        ]

    rename_map: dict[str, str] = {}
    for c in work.columns:
        lc = str(c).strip().lower().replace(" ", "_")
        if lc in {"open", "open_" + ticker.lower()}:
            rename_map[c] = "open"
        elif lc in {"high", "high_" + ticker.lower()}:
            rename_map[c] = "high"
        elif lc in {"low", "low_" + ticker.lower()}:
            rename_map[c] = "low"
        elif lc in {"close", "close_" + ticker.lower()}:
            rename_map[c] = "close"
        elif lc in {"adj_close", "adj_close_" + ticker.lower(), "adjclose"}:
            rename_map[c] = "adj_close"
        elif lc in {"volume", "volume_" + ticker.lower()}:
            rename_map[c] = "volume"

    work = work.rename(columns=rename_map)

    if "date" not in work.columns:
        work = work.reset_index()

    date_col = None
    for c in work.columns:
        if str(c).strip().lower() in {"date", "datetime", "index"}:
            date_col = c
            break

    if date_col is None:
        return pd.DataFrame()

    work["date"] = pd.to_datetime(work[date_col], errors="coerce").dt.date

    required = ["open", "high", "low", "close"]
    for c in required:
        if c not in work.columns:
            return pd.DataFrame()

    if "adj_close" not in work.columns:
        work["adj_close"] = work["close"]
    if "volume" not in work.columns:
        work["volume"] = 0

    out = pd.DataFrame(
        {
            "ticker": ticker,
            "name": name,
            "date": work["date"],
            "open": pd.to_numeric(work["open"], errors="coerce"),
            "high": pd.to_numeric(work["high"], errors="coerce"),
            "low": pd.to_numeric(work["low"], errors="coerce"),
            "close": pd.to_numeric(work["close"], errors="coerce"),
            "adj_close": pd.to_numeric(work["adj_close"], errors="coerce"),
            "volume": pd.to_numeric(work["volume"], errors="coerce").fillna(0).astype("int64"),
            "source": source,
            "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None),
        }
    )

    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    out = out.drop_duplicates(subset=["ticker", "date"], keep="last")
    out = out.sort_values(["ticker", "date"]).reset_index(drop=True)
    return out


def fetch_yfinance(ticker: str, start: date, end: date) -> tuple[pd.DataFrame, str | None]:
    try:
        import yfinance as yf  # type: ignore
    except Exception as exc:
        return pd.DataFrame(), f"yfinance_import_error: {exc}"

    end_exclusive = end + timedelta(days=1)

    try:
        df = yf.download(
            ticker,
            start=start.isoformat(),
            end=end_exclusive.isoformat(),
            auto_adjust=False,
            progress=False,
            threads=False,
            timeout=YFINANCE_TIMEOUT_SECONDS,
        )
        if df is None or df.empty:
            return pd.DataFrame(), None
        return df, None
    except Exception as exc:
        return pd.DataFrame(), f"yfinance_error: {type(exc).__name__}: {exc}"


def fetch_stooq(ticker: str, start: date, end: date) -> tuple[pd.DataFrame, str | None]:
    try:
        import requests  # type: ignore
    except Exception as exc:
        return pd.DataFrame(), f"requests_import_error: {exc}"

    sym = stooq_symbol(ticker)
    url = (
        "https://stooq.com/q/d/l/"
        f"?s={sym.lower()}&i=d&d1={start.strftime('%Y%m%d')}&d2={end.strftime('%Y%m%d')}"
    )

    try:
        resp = requests.get(
            url,
            timeout=STOOQ_TIMEOUT_SECONDS,
            headers={"User-Agent": "Mozilla/5.0 NeonTokyoSignals/1.0"},
        )
        resp.raise_for_status()
        text = resp.text.strip()
        if not text or text.lower().startswith("no data"):
            return pd.DataFrame(), "stooq_empty"
        df = pd.read_csv(io.StringIO(text))
        if df.empty:
            return pd.DataFrame(), "stooq_empty"
        return df, None
    except Exception as exc:
        return pd.DataFrame(), f"stooq_error: {type(exc).__name__}: {exc}"


def upsert_prices(conn, df: pd.DataFrame) -> None:
    if df.empty:
        return

    min_date = df["date"].min()
    max_date = df["date"].max()
    tickers = sorted(df["ticker"].dropna().astype(str).unique().tolist())

    conn.register("_incoming_prices", df)
    try:
        conn.execute(
            """
            DELETE FROM prices_daily
            WHERE ticker IN (SELECT DISTINCT ticker FROM _incoming_prices)
              AND date BETWEEN ? AND ?
            """,
            [min_date, max_date],
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
            FROM _incoming_prices
            """
        )
    finally:
        conn.unregister("_incoming_prices")


def fetch_one(conn, item: TickerItem, index: int, total: int, target_latest: date) -> FetchResult:
    ticker = item.ticker
    name = item.name
    errors: list[str] = []

    cached_latest = existing_latest_date(conn, ticker)
    if cached_latest and cached_latest >= target_latest and not truthy(os.getenv("FORCE_PRICE_REFRESH"), False):
        print(f"[{index}/{total}] Cache {ticker} {name} latest={cached_latest.isoformat()}")
        return FetchResult(
            ticker=ticker,
            name=name,
            status="cache_hit",
            source="duckdb_cache",
            bars=0,
            latest_date=cached_latest.isoformat(),
            errors=[],
        )

    start = decide_start_date(conn, ticker)
    end = now_jst().date()

    print(f"[{index}/{total}] Fetch {ticker} {name}".rstrip())

    raw_yf, yf_error = fetch_yfinance(ticker, start, end)

    if yf_error:
        errors.append(yf_error)
    else:
        yf_df = normalize_price_frame(raw_yf, ticker, name, "yfinance")
        if not yf_df.empty:
            latest = str(yf_df["date"].max())
            bars = int(len(yf_df))
            print(f"  OK source=duckdb_cache+yfinance bars={bars} latest={latest}")
            return FetchResult(
                ticker=ticker,
                name=name,
                status="yfinance_success",
                source="yfinance",
                bars=bars,
                latest_date=latest,
                errors=[],
                df=yf_df,
            )

        # Important rule:
        # In live/update mode, yfinance empty means listed but no data / insufficient source data.
        # Do not call Stooq here. This prevents 800+ ticker runs from hanging.
        if FETCH_MODE in {"live", "update", "incremental"}:
            msg = "yfinance_empty"
            errors.append(msg)
            print(f"  SKIP yfinance_empty")
            return FetchResult(
                ticker=ticker,
                name=name,
                status="skipped",
                source="yfinance",
                bars=0,
                latest_date="",
                errors=errors,
            )

        errors.append("yfinance_empty")

    if not ENABLE_STOOQ_FALLBACK:
        print(f"  FAIL fallback_disabled errors={errors}")
        return FetchResult(
            ticker=ticker,
            name=name,
            status="failed",
            source="",
            bars=0,
            latest_date="",
            errors=errors,
        )

    raw_stooq, stooq_error = fetch_stooq(ticker, start, end)
    if stooq_error:
        errors.append(stooq_error)
        print(f"  FAIL insufficient_data errors={errors}")
        return FetchResult(
            ticker=ticker,
            name=name,
            status="failed",
            source="stooq",
            bars=0,
            latest_date="",
            errors=errors,
        )

    stooq_df = normalize_price_frame(raw_stooq, ticker, name, "stooq")
    if stooq_df.empty:
        errors.append("stooq_empty_after_normalize")
        print(f"  FAIL insufficient_data errors={errors}")
        return FetchResult(
            ticker=ticker,
            name=name,
            status="failed",
            source="stooq",
            bars=0,
            latest_date="",
            errors=errors,
        )

    latest = str(stooq_df["date"].max())
    bars = int(len(stooq_df))
    print(f"  OK source=duckdb_cache+stooq bars={bars} latest={latest}")
    return FetchResult(
        ticker=ticker,
        name=name,
        status="stooq_success",
        source="stooq",
        bars=bars,
        latest_date=latest,
        errors=[],
        df=stooq_df,
    )


def load_latest_rows_for_json(conn) -> pd.DataFrame:
    try:
        return conn.execute(
            """
            WITH latest AS (
                SELECT ticker, MAX(date) AS date
                FROM prices_daily
                GROUP BY ticker
            )
            SELECT p.*
            FROM prices_daily p
            JOIN latest l
              ON p.ticker = l.ticker
             AND p.date = l.date
            ORDER BY p.ticker
            """
        ).df()
    except Exception:
        return pd.DataFrame()


def build_public_json(conn, results: list[FetchResult], generated_at: str, stats: dict[str, int]) -> dict[str, Any]:
    latest_df = load_latest_rows_for_json(conn)

    latest_records: list[dict[str, Any]] = []
    if not latest_df.empty:
        for row in latest_df.to_dict("records"):
            latest_records.append(
                {
                    "ticker": str(row.get("ticker") or ""),
                    "name": str(row.get("name") or ""),
                    "date": str(row.get("date") or "")[:10],
                    "open": safe_float(row.get("open")),
                    "high": safe_float(row.get("high")),
                    "low": safe_float(row.get("low")),
                    "close": safe_float(row.get("close")),
                    "adj_close": safe_float(row.get("adj_close")),
                    "volume": safe_int(row.get("volume")),
                    "source": str(row.get("source") or ""),
                }
            )

    payload: dict[str, Any] = {
        "schema_version": "neon_tokyo_prices_jp_v2",
        "generated_at": generated_at,
        "duckdb_path": str(PRICE_DUCKDB_PATH.relative_to(ROOT)) if PRICE_DUCKDB_PATH.is_absolute() else str(PRICE_DUCKDB_PATH),
        "fetch_mode": FETCH_MODE,
        "refresh_mode": PRICE_REFRESH_MODE,
        "price_store_mode": PRICE_STORE_MODE,
        "public_json_mode": PRICE_PUBLIC_JSON_MODE,
        "stats": stats,
        "latest": latest_records,
    }

    if PRICE_PUBLIC_JSON_MODE == "full":
        # Keep public JSON usable but avoid writing the full historical matrix unless explicitly requested.
        try:
            full_df = conn.execute(
                """
                SELECT *
                FROM prices_daily
                ORDER BY ticker, date
                """
            ).df()
            payload["prices"] = [
                {
                    "ticker": str(r.get("ticker") or ""),
                    "name": str(r.get("name") or ""),
                    "date": str(r.get("date") or "")[:10],
                    "open": safe_float(r.get("open")),
                    "high": safe_float(r.get("high")),
                    "low": safe_float(r.get("low")),
                    "close": safe_float(r.get("close")),
                    "adj_close": safe_float(r.get("adj_close")),
                    "volume": safe_int(r.get("volume")),
                    "source": str(r.get("source") or ""),
                }
                for r in full_df.to_dict("records")
            ]
        except Exception as exc:
            payload["full_export_error"] = str(exc)

    payload["fetch_results"] = [
        {
            "ticker": r.ticker,
            "name": r.name,
            "status": r.status,
            "source": r.source,
            "bars": r.bars,
            "latest_date": r.latest_date,
            "errors": r.errors or [],
        }
        for r in results
    ]

    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def print_header(total: int) -> None:
    print("=== JP price fetch ===")
    print(f"total tickers: {total}")
    print(f"fetch mode: {FETCH_MODE}")
    print(f"refresh mode: {PRICE_REFRESH_MODE}")
    print(f"fallback enabled/disabled: {'enabled' if ENABLE_STOOQ_FALLBACK else 'disabled'}")
    print(f"stooq timeout seconds: {STOOQ_TIMEOUT_SECONDS:g}")
    print(f"yfinance timeout seconds: {YFINANCE_TIMEOUT_SECONDS:g}")
    print(f"store mode: {PRICE_STORE_MODE}")
    print(f"duckdb path: {PRICE_DUCKDB_PATH}")
    print(f"universe csv: {UNIVERSE_CSV}")
    print("======================")


def print_summary(stats: dict[str, int]) -> None:
    print("=== JP price fetch summary ===")
    print(f"total tickers: {stats['total_tickers']}")
    print(f"fetch mode: {FETCH_MODE}")
    print(f"fallback enabled/disabled: {'enabled' if ENABLE_STOOQ_FALLBACK else 'disabled'}")
    print(f"cache hit count: {stats['cache_hit_count']}")
    print(f"yfinance success count: {stats['yfinance_success_count']}")
    print(f"stooq success count: {stats['stooq_success_count']}")
    print(f"skipped count: {stats['skipped_count']}")
    print(f"failed count: {stats['failed_count']}")
    print(f"written rows: {stats['written_rows']}")
    print("==============================")


def main() -> int:
    started = time.time()
    generated_at = iso_now()

    try:
        universe = read_universe(UNIVERSE_CSV)
    except Exception as exc:
        print(f"ERROR failed to read universe: {exc}", file=sys.stderr)
        return 2

    total = len(universe)
    print_header(total)

    if total <= 0:
        print("ERROR universe is empty.", file=sys.stderr)
        return 2

    uses_duckdb = "duckdb" in PRICE_STORE_MODE
    uses_json = "json" in PRICE_STORE_MODE or PRICE_STORE_MODE in {"json", "json_and_duckdb"}

    if not uses_duckdb:
        print("ERROR this complete version requires DuckDB storage. Set PRICE_STORE_MODE=json_and_duckdb.", file=sys.stderr)
        return 2

    conn = connect_duckdb()
    ensure_price_schema(conn)

    target_latest = previous_business_day_jst()

    stats = {
        "total_tickers": total,
        "cache_hit_count": 0,
        "yfinance_success_count": 0,
        "stooq_success_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "written_rows": 0,
    }

    results: list[FetchResult] = []

    try:
        for i, item in enumerate(universe, start=1):
            result = fetch_one(conn, item, i, total, target_latest)
            results.append(result)

            if result.status == "cache_hit":
                stats["cache_hit_count"] += 1
            elif result.status == "yfinance_success":
                stats["yfinance_success_count"] += 1
            elif result.status == "stooq_success":
                stats["stooq_success_count"] += 1
            elif result.status == "skipped":
                stats["skipped_count"] += 1
            else:
                stats["failed_count"] += 1

            if result.df is not None and not result.df.empty:
                upsert_prices(conn, result.df)
                stats["written_rows"] += int(len(result.df))

            if SLEEP_SECONDS > 0:
                time.sleep(SLEEP_SECONDS)

        if uses_json and PRICE_PUBLIC_JSON_MODE != "none":
            public_payload = build_public_json(conn, results, generated_at, stats)
            write_json(LATEST_JSON, public_payload)

            manifest = {
                "schema_version": "neon_tokyo_prices_jp_manifest_v2",
                "generated_at": generated_at,
                "latest_json": str(LATEST_JSON.relative_to(ROOT)),
                "duckdb_path": str(PRICE_DUCKDB_PATH.relative_to(ROOT)),
                "stats": stats,
                "fetch_mode": FETCH_MODE,
                "refresh_mode": PRICE_REFRESH_MODE,
                "fallback_enabled": ENABLE_STOOQ_FALLBACK,
                "stooq_timeout_seconds": STOOQ_TIMEOUT_SECONDS,
                "elapsed_seconds": round(time.time() - started, 3),
            }
            write_json(MANIFEST_JSON, manifest)

            if WRITE_DATED_PRICE_JSON:
                dated = PRICES_OUT_DIR / f"{now_jst().date().isoformat()}.json"
                write_json(dated, public_payload)

        print_summary(stats)

        # Do not fail the whole Action just because a few tickers are unavailable.
        # Fail only if nothing useful exists.
        if stats["cache_hit_count"] + stats["yfinance_success_count"] + stats["stooq_success_count"] <= 0:
            print("ERROR no usable price data from cache/yfinance/stooq.", file=sys.stderr)
            return 3

        return 0

    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR unexpected failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
