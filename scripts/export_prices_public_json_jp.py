#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""Export a small public JP price summary JSON from DuckDB.

DuckDB `prices_daily` is the canonical store.  This script exists only for
static-site compatibility/fallback use.  It deliberately omits historical bars so
`site/data/prices-jp/latest.json` cannot grow into a heavy artifact again.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import duckdb

JST = timezone(timedelta(hours=9))
DEFAULT_DUCKDB_PATH = "data/cache/neon_tokyo_jp.duckdb"
DEFAULT_OUT = "site/data/prices-jp/latest.json"
DEFAULT_MANIFEST = "site/data/prices-jp/manifest.json"
DEFAULT_UNIVERSE = "data/universe/jp_duckdb_trial_300.csv"
REQUIRED_COLUMNS = {
    "ticker", "date", "open", "high", "low", "close", "adj_close",
    "volume", "traded_value_jpy", "source", "updated_at",
}


def now_jst_iso() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


def read_universe_names(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return out
        lower = {c.lower().strip(): c for c in reader.fieldnames}
        ticker_col = lower.get("ticker") or lower.get("symbol") or lower.get("code") or lower.get("銘柄コード")
        name_col = lower.get("name") or lower.get("company") or lower.get("company_name") or lower.get("銘柄名")
        if not ticker_col:
            return out
        for row in reader:
            ticker = normalize_ticker(row.get(ticker_col, ""))
            if ticker:
                out[ticker] = str(row.get(name_col, "") if name_col else "").strip()
    return out


def normalize_ticker(value: Any) -> str:
    s = str(value or "").strip().upper().replace(".JP", ".T")
    if not s:
        return ""
    if s.endswith(".T"):
        return s
    if s.isdigit():
        return f"{s}.T"
    return s


def table_columns(conn: duckdb.DuckDBPyConnection, table: str) -> set[str]:
    try:
        return {str(r[1]) for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()}
    except Exception:
        return set()


def validate_schema(conn: duckdb.DuckDBPyConnection) -> None:
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if "prices_daily" not in tables:
        raise RuntimeError("prices_daily table does not exist")
    cols = table_columns(conn, "prices_daily")
    missing = sorted(REQUIRED_COLUMNS - cols)
    if missing:
        raise RuntimeError(f"prices_daily missing required columns: {missing}")


def scalar(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> Any:
    row = conn.execute(sql, params or []).fetchone()
    return row[0] if row else None


def build_items(conn: duckdb.DuckDBPyConnection, names: dict[str, str], limit: int) -> list[dict[str, Any]]:
    sql = """
    WITH latest AS (
      SELECT ticker, MAX(date) AS latest_date
      FROM prices_daily
      GROUP BY ticker
    ), current_rows AS (
      SELECT p.*
      FROM prices_daily p
      JOIN latest l ON p.ticker = l.ticker AND p.date = l.latest_date
    ), previous_rows AS (
      SELECT p.ticker, p.close AS previous_close
      FROM prices_daily p
      JOIN (
        SELECT p2.ticker, MAX(p2.date) AS previous_date
        FROM prices_daily p2
        JOIN latest l2 ON p2.ticker = l2.ticker
        WHERE p2.date < l2.latest_date
        GROUP BY p2.ticker
      ) prev ON p.ticker = prev.ticker AND p.date = prev.previous_date
    )
    SELECT
      c.ticker, c.date, c.open, c.high, c.low, c.close, c.adj_close,
      c.volume, c.traded_value_jpy, c.source, c.updated_at, pr.previous_close
    FROM current_rows c
    LEFT JOIN previous_rows pr ON c.ticker = pr.ticker
    ORDER BY c.ticker
    """
    if limit > 0:
        sql += f" LIMIT {int(limit)}"
    rows = conn.execute(sql).fetchall()
    cols = [d[0] for d in conn.description]
    items: list[dict[str, Any]] = []
    for row in rows:
        r = dict(zip(cols, row))
        close = _float(r.get("close"))
        prev = _float(r.get("previous_close"))
        ret = None
        if close is not None and prev and prev > 0:
            ret = (close / prev - 1.0) * 100.0
        ticker = str(r.get("ticker") or "")
        items.append({
            "ticker": ticker,
            "symbol": ticker,
            "name": names.get(ticker, ""),
            "date": _date_str(r.get("date")),
            "open": close_or_float(r.get("open")),
            "high": close_or_float(r.get("high")),
            "low": close_or_float(r.get("low")),
            "close": close_or_float(r.get("close")),
            "adj_close": close_or_float(r.get("adj_close")),
            "volume": int(r.get("volume") or 0),
            "traded_value_jpy": close_or_float(r.get("traded_value_jpy")),
            "return_1d_pct": round(ret, 4) if ret is not None else None,
            "source": r.get("source") or "",
            "updated_at": _dt_str(r.get("updated_at")),
        })
    return items


def _float(v: Any) -> float | None:
    try:
        x = float(v)
        if x != x:
            return None
        return x
    except Exception:
        return None


def close_or_float(v: Any) -> float | None:
    x = _float(v)
    return round(x, 6) if x is not None else None


def _date_str(v: Any) -> str:
    return str(v)[:10] if v is not None else ""


def _dt_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc).isoformat(timespec="seconds")
    return str(v)


def build_payload(conn: duckdb.DuckDBPyConnection, names: dict[str, str], limit: int = 0, max_stale_calendar_days: int = 3) -> dict[str, Any]:
    validate_schema(conn)
    generated_at = now_jst_iso()
    latest_price_date = scalar(conn, "SELECT MAX(date) FROM prices_daily")
    previous_price_date = scalar(conn, "SELECT MAX(date) FROM prices_daily WHERE date < (SELECT MAX(date) FROM prices_daily)")
    ticker_count = int(scalar(conn, "SELECT COUNT(DISTINCT ticker) FROM prices_daily") or 0)
    latest_date_ticker_count = int(scalar(conn, "SELECT COUNT(DISTINCT ticker) FROM prices_daily WHERE date = (SELECT MAX(date) FROM prices_daily)") or 0)
    row_count = int(scalar(conn, "SELECT COUNT(*) FROM prices_daily") or 0)
    items = build_items(conn, names, limit)
    latest_str = _date_str(latest_price_date)
    stale_reason = ""
    is_stale = False
    if not latest_str:
        is_stale = True
        stale_reason = "prices_daily_empty"
    else:
        try:
            age = (datetime.now(JST).date() - datetime.fromisoformat(latest_str).date()).days
            if age > max_stale_calendar_days:
                is_stale = True
                stale_reason = f"latest_price_date_age_{age}_days"
        except Exception:
            is_stale = True
            stale_reason = "invalid_latest_price_date"
    return {
        "schema_version": "neon_tokyo_prices_jp_summary_v2",
        "generated_at": generated_at,
        "source": {"type": "duckdb", "table": "prices_daily"},
        "public_json_mode": "summary",
        "bars_omitted": True,
        "latest_price_date": latest_str,
        "previous_price_date": _date_str(previous_price_date),
        "ticker_count": ticker_count,
        "latest_date_ticker_count": latest_date_ticker_count,
        "row_count": row_count,
        "items": items,
        "freshness": {
            "is_stale": is_stale,
            "stale_reason": stale_reason,
            "max_stale_calendar_days": max_stale_calendar_days,
        },
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Export lightweight public JP price JSON from DuckDB")
    ap.add_argument("--duckdb-path", default=os.getenv("PRICE_DUCKDB_PATH", DEFAULT_DUCKDB_PATH))
    ap.add_argument("--out", default=os.getenv("PRICE_PUBLIC_JSON", DEFAULT_OUT))
    ap.add_argument("--manifest", default=os.getenv("PRICE_PUBLIC_MANIFEST_JSON", DEFAULT_MANIFEST))
    ap.add_argument("--universe-csv", default=os.getenv("JP_UNIVERSE_CSV", DEFAULT_UNIVERSE))
    ap.add_argument("--limit", type=int, default=int(os.getenv("PRICE_PUBLIC_JSON_LIMIT", "0") or 0))
    ap.add_argument("--max-stale-calendar-days", type=int, default=int(os.getenv("PRICE_MAX_STALE_CALENDAR_DAYS", "3") or 3))
    args = ap.parse_args()
    db_path = Path(args.duckdb_path)
    if not db_path.exists():
        print(f"ERROR DuckDB not found: {db_path}", file=sys.stderr)
        return 1
    names = read_universe_names(Path(args.universe_csv))
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        payload = build_payload(con, names, limit=int(args.limit), max_stale_calendar_days=int(args.max_stale_calendar_days))
    finally:
        con.close()
    out = Path(args.out)
    write_json(out, payload)
    manifest = {
        "schema_version": "neon_tokyo_prices_jp_manifest_v2",
        "generated_at": payload["generated_at"],
        "latest_price_date": payload.get("latest_price_date"),
        "ticker_count": payload.get("ticker_count"),
        "latest_date_ticker_count": payload.get("latest_date_ticker_count"),
        "public_json": str(out).replace("\\", "/"),
        "bars_omitted": True,
        "freshness": payload.get("freshness", {}),
    }
    write_json(Path(args.manifest), manifest)
    print("=== public price JSON export ===")
    print(f"out: {out}")
    print(f"latest_price_date: {payload.get('latest_price_date')}")
    print(f"ticker_count: {payload.get('ticker_count')}")
    print(f"latest_date_ticker_count: {payload.get('latest_date_ticker_count')}")
    print(f"is_stale: {payload.get('freshness', {}).get('is_stale')}")
    print(f"file_size: {out.stat().st_size if out.exists() else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
