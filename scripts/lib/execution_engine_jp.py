from __future__ import annotations

"""Execution helpers.

The simulation uses deterministic historical open/close prices from DuckDB.
Entry is designed as signal close -> next session open. Exit timing is governed
by YAML, but year-end force-close always uses the final trading day's close so
annual standings are finalized within the same calendar year.
"""

from datetime import date
from typing import Any

import duckdb


def fetch_price_row(conn: duckdb.DuckDBPyConnection, ticker: str, d: date) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT ticker, date, open, high, low, close, adj_close, volume, traded_value_jpy
        FROM prices_daily
        WHERE ticker = ? AND date = ?
        LIMIT 1
        """,
        [ticker, d],
    ).fetchone()
    if not row:
        return None
    cols = ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume", "traded_value_jpy"]
    return dict(zip(cols, row))


def choose_execution_price(price_row: dict[str, Any] | None, field: str) -> float | None:
    if not price_row:
        return None
    value = price_row.get(field)
    try:
        v = float(value)
        return v if v > 0 else None
    except Exception:
        return None
