from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import duckdb
import pandas as pd

from lib.duckdb_schema import initialize_schema


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _ticker_code(ticker: str) -> str:
    t = (ticker or "").upper().strip()
    if t.endswith(".T"):
        return t[:-2]
    return t


def _universe_flags(item: dict[str, Any]) -> dict[str, bool]:
    bucket = str(item.get("bucket") or "").lower()
    priority = str(item.get("priority") or "").upper()
    theme = str(item.get("theme") or "").lower()
    is_topix500 = _to_bool(item.get("is_topix500")) or bucket in {"core", "topix500"}
    is_jpx_prime150 = _to_bool(item.get("is_jpx_prime150"))
    is_growth250 = _to_bool(item.get("is_growth250")) or "growth" in bucket
    is_jpx_startup100 = _to_bool(item.get("is_jpx_startup100")) or "startup" in theme
    return {
        "is_topix500": is_topix500,
        "is_jpx_prime150": is_jpx_prime150,
        "is_growth250": is_growth250,
        "is_jpx_startup100": is_jpx_startup100,
        "is_core": is_topix500 or is_jpx_prime150 or bucket == "core",
        "is_growth": is_growth250 or is_jpx_startup100 or "growth" in bucket,
        "is_small_discovery": bucket in {"discovery", "small", "small_discovery"} or is_growth250 or is_jpx_startup100,
        "is_value_candidate": is_jpx_prime150 or priority in {"A", "B"} or bucket == "core",
    }


def store_price_payload(
    conn: duckdb.DuckDBPyConnection,
    *,
    payload: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    initialize_schema(conn)
    run_id = run_id or str(payload.get("generated_at") or datetime.utcnow().isoformat())
    updated_at = datetime.utcnow()
    items = list(payload.get("items") or [])
    failures = list(payload.get("failures") or [])

    tickers = [str(x.get("symbol") or "").upper().strip() for x in items if x.get("symbol")]
    if tickers:
        conn.register("_tickers_to_refresh", pd.DataFrame({"ticker": tickers}))
        conn.execute("DELETE FROM universe_master USING _tickers_to_refresh t WHERE universe_master.ticker = t.ticker")
        conn.execute("DELETE FROM prices_daily USING _tickers_to_refresh t WHERE prices_daily.ticker = t.ticker")
        conn.unregister("_tickers_to_refresh")

    universe_rows = []
    price_rows = []
    for item in items:
        ticker = str(item.get("symbol") or "").upper().strip()
        if not ticker:
            continue
        flags = _universe_flags(item)
        universe_rows.append(
            {
                "ticker": ticker,
                "code": _ticker_code(ticker),
                "name": item.get("name") or ticker,
                "market": item.get("market") or "JP",
                "sector": item.get("sector") or "",
                "industry": item.get("industry") or "",
                "theme": item.get("theme") or "",
                "bucket": item.get("bucket") or "",
                "priority": item.get("priority") or "",
                "asset_type": item.get("asset_type") or "equity",
                **flags,
                "is_excluded": False,
                "exclude_reason": "",
                "source_detail": item.get("source") or "",
                "source_url": "",
                "updated_at": updated_at,
            }
        )
        for bar in item.get("bars") or []:
            date = bar.get("date")
            close = bar.get("close")
            volume = bar.get("volume") or 0
            traded_value = None
            try:
                traded_value = float(close) * float(volume)
            except Exception:
                traded_value = None
            price_rows.append(
                {
                    "ticker": ticker,
                    "date": date,
                    "open": bar.get("open"),
                    "high": bar.get("high"),
                    "low": bar.get("low"),
                    "close": close,
                    "adj_close": close,
                    "volume": volume,
                    "traded_value_jpy": traded_value,
                    "source": item.get("source") or "",
                    "updated_at": updated_at,
                }
            )

    if universe_rows:
        conn.register("_universe_rows", pd.DataFrame(universe_rows))
        conn.execute("INSERT INTO universe_master SELECT * FROM _universe_rows")
        conn.unregister("_universe_rows")

    if price_rows:
        conn.register("_price_rows", pd.DataFrame(price_rows))
        conn.execute("""
            INSERT INTO prices_daily
              (ticker, date, open, high, low, close, adj_close, volume, traded_value_jpy, source, updated_at)
            SELECT
              ticker, date, open, high, low, close, adj_close, volume, traded_value_jpy, source, updated_at
            FROM _price_rows
        """)
        conn.unregister("_price_rows")

    failure_rows = []
    for f in failures:
        failure_rows.append(
            {
                "run_id": run_id,
                "ticker": str(f.get("symbol") or "").upper().strip(),
                "name": f.get("name") or "",
                "asset_type": f.get("asset_type") or "",
                "reason": f.get("reason") or "",
                "source_errors": json.dumps(f.get("source_errors") or [], ensure_ascii=False),
                "created_at": updated_at,
            }
        )
    if failure_rows:
        conn.register("_failure_rows", pd.DataFrame(failure_rows))
        conn.execute("INSERT INTO price_fetch_failures SELECT * FROM _failure_rows")
        conn.unregister("_failure_rows")

    return {
        "items_stored": len(universe_rows),
        "bars_stored": len(price_rows),
        "failures_stored": len(failure_rows),
        "run_id": run_id,
    }
