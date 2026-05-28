#!/usr/bin/env python3
"""
Fetch Japanese equity OHLCV data and write normalized JSON.

Primary source:
- yfinance

Fallback:
- Stooq via pandas-datareader

Input:
- data/universe_jp.csv

Output:
- site/data/prices-jp/latest.json
- site/data/prices-jp/manifest.json

Public JSON can be controlled with PRICE_PUBLIC_JSON_MODE:
- full: legacy full OHLCV JSON, including bars and dated snapshot
- summary: lightweight latest.json without historical bars and no dated snapshot
- none: no public prices JSON; DuckDB only if enabled

This script intentionally does not calculate final Daily/Weekly scores.
It only creates a reliable price-data layer for later scoring scripts.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()
else:
    OUT_DIR = OUT_DIR.resolve()

UNIVERSE_CSV = Path(os.getenv("UNIVERSE_CSV", str(ROOT / "data" / "universe_jp.csv")))
if not UNIVERSE_CSV.is_absolute():
    UNIVERSE_CSV = (ROOT / UNIVERSE_CSV).resolve()
else:
    UNIVERSE_CSV = UNIVERSE_CSV.resolve()

PRICE_OUT_DIR = OUT_DIR / "data" / "prices-jp"

LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "520"))
MIN_BARS_REQUIRED = int(os.getenv("MIN_BARS_REQUIRED", "60"))
MIN_ACCEPTABLE_BARS = int(os.getenv("MIN_ACCEPTABLE_BARS", "20"))
REQUEST_SLEEP_SECONDS = float(os.getenv("REQUEST_SLEEP_SECONDS", "0.25"))
UNIVERSE_LIMIT = int(os.getenv("UNIVERSE_LIMIT", "0") or "0")
PRICE_STORE_MODE = os.getenv("PRICE_STORE_MODE", "json").strip().lower()
PRICE_PUBLIC_JSON_MODE = os.getenv("PRICE_PUBLIC_JSON_MODE", "full").strip().lower()
WRITE_DATED_PRICE_JSON = os.getenv("WRITE_DATED_PRICE_JSON", "true").strip().lower() in {"1", "true", "yes", "on"}
PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH", str(ROOT / "data" / "cache" / "neon_tokyo_jp.duckdb"))


TZ = ZoneInfo("Asia/Tokyo")


MARKET_PULSE_SYMBOLS = [
    {
        "symbol": "1306.T",
        "name": "TOPIX ETF",
        "theme": "Japan Broad Market",
        "bucket": "MarketPulse",
        "priority": "A",
        "asset_type": "market_pulse",
        "pulse_label": "TOPIX",
    },
    {
        "symbol": "1321.T",
        "name": "Nikkei 225 ETF",
        "theme": "Japan Large Cap Momentum",
        "bucket": "MarketPulse",
        "priority": "A",
        "asset_type": "market_pulse",
        "pulse_label": "NIKKEI",
    },
    {
        "symbol": "2516.T",
        "name": "TSE Growth ETF",
        "theme": "Japan Growth Market",
        "bucket": "MarketPulse",
        "priority": "A",
        "asset_type": "market_pulse",
        "pulse_label": "GROWTH",
    },
]


@dataclass
class UniverseRow:
    symbol: str
    name: str
    theme: str
    bucket: str
    priority: str
    asset_type: str = "equity"
    pulse_label: str | None = None


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def now_jst() -> datetime:
    return datetime.now(TZ)


def iso_now() -> str:
    return now_jst().isoformat(timespec="seconds")


def clean_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_symbol(symbol: str) -> str:
    return clean_str(symbol).upper()


def yf_symbol(symbol: str) -> str:
    return normalize_symbol(symbol)


def stooq_symbol(symbol: str) -> str:
    """
    Convert yfinance JP symbol format to Stooq symbol format.

    Example:
    - 8035.T -> 8035.JP
    - 135A.T -> 135A.JP
    """
    symbol = normalize_symbol(symbol)
    if symbol.endswith(".T"):
        return symbol[:-2] + ".JP"
    return symbol


def read_universe(path: Path) -> list[UniverseRow]:
    if not path.exists():
        raise FileNotFoundError(f"Universe CSV not found: {safe_relative(path)}")

    rows: list[UniverseRow] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        required = {"symbol", "name", "theme", "bucket", "priority"}
        actual = set(reader.fieldnames or [])

        missing = required - actual
        if missing:
            raise ValueError(
                f"Universe CSV is missing required columns: {sorted(missing)}. "
                f"Actual columns: {sorted(actual)}"
            )

        for i, raw in enumerate(reader, start=2):
            symbol = normalize_symbol(raw.get("symbol"))
            name = clean_str(raw.get("name"))
            theme = clean_str(raw.get("theme"))
            bucket = clean_str(raw.get("bucket"))
            priority = clean_str(raw.get("priority")).upper()

            if not symbol:
                continue

            if symbol.lower() == "symbol":
                raise ValueError(
                    f"Header row appears inside CSV at line {i}. "
                    f"Please remove duplicated header rows."
                )

            rows.append(
                UniverseRow(
                    symbol=symbol,
                    name=name,
                    theme=theme,
                    bucket=bucket,
                    priority=priority,
                    asset_type="equity",
                )
            )

    if not rows:
        raise ValueError(f"Universe CSV has no valid rows: {safe_relative(path)}")

    seen: set[str] = set()
    deduped: list[UniverseRow] = []

    for row in rows:
        if row.symbol in seen:
            continue
        seen.add(row.symbol)
        deduped.append(row)

    for pulse in MARKET_PULSE_SYMBOLS:
        symbol = normalize_symbol(pulse["symbol"])
        if symbol in seen:
            continue
        seen.add(symbol)
        deduped.append(
            UniverseRow(
                symbol=symbol,
                name=pulse["name"],
                theme=pulse["theme"],
                bucket=pulse["bucket"],
                priority=pulse["priority"],
                asset_type=pulse["asset_type"],
                pulse_label=pulse["pulse_label"],
            )
        )

    return deduped


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        # yfinance can return MultiIndex columns even for a single ticker.
        df = df.copy()
        df.columns = [
            str(col[0]).strip() if isinstance(col, tuple) else str(col).strip()
            for col in df.columns
        ]
    else:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]

    return df


def standardize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = flatten_columns(df)

    rename_map: dict[str, str] = {}
    for col in df.columns:
        normalized = col.lower().replace(" ", "_")
        if normalized in {"open", "high", "low", "close", "volume", "adj_close"}:
            rename_map[col] = normalized

    df = df.rename(columns=rename_map)

    required = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return pd.DataFrame()

    out = df[required].copy()

    out.index = pd.to_datetime(out.index, errors="coerce")
    out = out[~out.index.isna()]
    out = out.sort_index()

    for col in required:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out = out.dropna(subset=["open", "high", "low", "close"])
    out["volume"] = out["volume"].fillna(0)

    out = out[out["close"] > 0]

    if out.empty:
        return pd.DataFrame()

    # Remove duplicated dates if source returns duplicates.
    out = out[~out.index.duplicated(keep="last")]

    return out


def fetch_from_yfinance(symbol: str, start: datetime, end: datetime) -> tuple[pd.DataFrame, str | None]:
    try:
        df = yf.download(
            yf_symbol(symbol),
            start=start.date().isoformat(),
            end=(end.date() + timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        normalized = standardize_ohlcv(df)

        if normalized.empty:
            return normalized, "yfinance_empty"

        return normalized, None

    except Exception as exc:
        return pd.DataFrame(), f"yfinance_error: {type(exc).__name__}: {exc}"


def fetch_from_stooq(symbol: str, start: datetime, end: datetime) -> tuple[pd.DataFrame, str | None]:
    try:
        df = pdr.DataReader(
            stooq_symbol(symbol),
            "stooq",
            start=start.date().isoformat(),
            end=(end.date() + timedelta(days=1)).isoformat(),
        )

        normalized = standardize_ohlcv(df)

        if normalized.empty:
            return normalized, "stooq_empty"

        return normalized, None

    except Exception as exc:
        return pd.DataFrame(), f"stooq_error: {type(exc).__name__}: {exc}"


def finite_float(value: Any) -> float | None:
    try:
        v = float(value)
        if math.isfinite(v):
            return v
        return None
    except Exception:
        return None


def finite_int(value: Any) -> int | None:
    try:
        v = float(value)
        if math.isfinite(v):
            return int(round(v))
        return None
    except Exception:
        return None


def pct_change_from_series(values: pd.Series, periods: int) -> float | None:
    if len(values) <= periods:
        return None

    latest = finite_float(values.iloc[-1])
    base = finite_float(values.iloc[-1 - periods])

    if latest is None or base is None or base == 0:
        return None

    return (latest / base - 1.0) * 100.0


def safe_round(value: float | None, digits: int = 4) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(float(value), digits)


def compute_metrics(df: pd.DataFrame) -> dict[str, Any]:
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    latest_close = finite_float(close.iloc[-1])
    latest_volume = finite_int(volume.iloc[-1])

    value = close * volume

    avg_volume_20 = finite_float(volume.tail(20).mean()) if len(volume) >= 1 else None
    avg_volume_50 = finite_float(volume.tail(50).mean()) if len(volume) >= 1 else None
    avg_value_20 = finite_float(value.tail(20).mean()) if len(value) >= 1 else None
    avg_value_50 = finite_float(value.tail(50).mean()) if len(value) >= 1 else None

    volume_ratio_20 = None
    if avg_volume_20 and avg_volume_20 > 0 and latest_volume is not None:
        volume_ratio_20 = latest_volume / avg_volume_20

    high_20 = finite_float(high.tail(20).max()) if len(high) >= 1 else None
    high_52w = finite_float(high.tail(252).max()) if len(high) >= 1 else None
    low_20 = finite_float(low.tail(20).min()) if len(low) >= 1 else None

    distance_from_20d_high_pct = None
    if latest_close is not None and high_20 and high_20 > 0:
        distance_from_20d_high_pct = (latest_close / high_20 - 1.0) * 100.0

    distance_from_52w_high_pct = None
    if latest_close is not None and high_52w and high_52w > 0:
        distance_from_52w_high_pct = (latest_close / high_52w - 1.0) * 100.0

    range_position_20d = None
    if latest_close is not None and high_20 and low_20 and high_20 > low_20:
        range_position_20d = (latest_close - low_20) / (high_20 - low_20)

    compression_20d_pct = None
    if latest_close is not None and high_20 and low_20 and latest_close > 0:
        compression_20d_pct = ((high_20 - low_20) / latest_close) * 100.0

    daily_returns = close.pct_change().dropna()
    volatility_20d_annualized_pct = None
    if len(daily_returns) >= 10:
        volatility_20d_annualized_pct = finite_float(
            daily_returns.tail(20).std(ddof=0) * np.sqrt(252) * 100.0
        )

    latest_traded_value = None
    if latest_close is not None and latest_volume is not None:
        latest_traded_value = latest_close * latest_volume

    liquidity_status = "ok"
    liquidity_flags: list[str] = []

    if latest_close is not None and latest_close < 300:
        liquidity_flags.append("price_below_300_jpy")

    if avg_value_20 is not None:
        if avg_value_20 < 100_000_000:
            liquidity_status = "exclude_or_watch"
            liquidity_flags.append("avg_traded_value_20d_below_100m_jpy")
        elif avg_value_20 < 300_000_000:
            liquidity_status = "penalty"
            liquidity_flags.append("avg_traded_value_20d_below_300m_jpy")
    else:
        liquidity_status = "unknown"
        liquidity_flags.append("avg_traded_value_20d_unavailable")

    return {
        "latest_date": df.index[-1].date().isoformat(),
        "latest_close": safe_round(latest_close, 4),
        "latest_volume": latest_volume,
        "latest_traded_value_jpy": safe_round(latest_traded_value, 2),
        "return_1d_pct": safe_round(pct_change_from_series(close, 1), 4),
        "return_5d_pct": safe_round(pct_change_from_series(close, 5), 4),
        "return_20d_pct": safe_round(pct_change_from_series(close, 20), 4),
        "return_60d_pct": safe_round(pct_change_from_series(close, 60), 4),
        "return_120d_pct": safe_round(pct_change_from_series(close, 120), 4),
        "avg_volume_20d": safe_round(avg_volume_20, 2),
        "avg_volume_50d": safe_round(avg_volume_50, 2),
        "avg_traded_value_20d_jpy": safe_round(avg_value_20, 2),
        "avg_traded_value_50d_jpy": safe_round(avg_value_50, 2),
        "volume_ratio_20d": safe_round(volume_ratio_20, 4),
        "high_20d": safe_round(high_20, 4),
        "high_52w": safe_round(high_52w, 4),
        "distance_from_20d_high_pct": safe_round(distance_from_20d_high_pct, 4),
        "distance_from_52w_high_pct": safe_round(distance_from_52w_high_pct, 4),
        "range_position_20d_0_1": safe_round(range_position_20d, 4),
        "compression_20d_pct": safe_round(compression_20d_pct, 4),
        "volatility_20d_annualized_pct": safe_round(volatility_20d_annualized_pct, 4),
        "liquidity_status": liquidity_status,
        "liquidity_flags": liquidity_flags,
    }


def df_to_bars(df: pd.DataFrame) -> list[dict[str, Any]]:
    bars: list[dict[str, Any]] = []

    for idx, row in df.iterrows():
        bars.append(
            {
                "date": idx.date().isoformat(),
                "open": safe_round(finite_float(row["open"]), 4),
                "high": safe_round(finite_float(row["high"]), 4),
                "low": safe_round(finite_float(row["low"]), 4),
                "close": safe_round(finite_float(row["close"]), 4),
                "volume": finite_int(row["volume"]) or 0,
            }
        )

    return bars


def summarize_price_item(item: dict[str, Any]) -> dict[str, Any]:
    """Return a public lightweight version of one price item.

    The full OHLCV history is intentionally omitted. Historical bars are stored
    in DuckDB. This keeps site/data/prices-jp/latest.json small enough for Git
    and Vercel while preserving ticker-level diagnostics and latest metrics.
    """
    bars = item.get("bars") or []
    latest_bar = bars[-1] if bars else None
    return {
        "symbol": item.get("symbol"),
        "name": item.get("name"),
        "theme": item.get("theme"),
        "bucket": item.get("bucket"),
        "priority": item.get("priority"),
        "asset_type": item.get("asset_type"),
        "pulse_label": item.get("pulse_label"),
        "market": item.get("market"),
        "currency": item.get("currency"),
        "source": item.get("source"),
        "source_symbol": item.get("source_symbol"),
        "bars_count": item.get("bars_count"),
        "date_start": item.get("date_start"),
        "date_end": item.get("date_end"),
        "is_partial": item.get("is_partial"),
        "warnings": item.get("warnings") or [],
        "source_errors": item.get("source_errors") or [],
        "metrics": item.get("metrics") or {},
        "latest_bar": latest_bar,
        "bars_omitted": True,
    }


def build_public_payload(payload: dict[str, Any], mode: str) -> dict[str, Any]:
    mode = (mode or "full").strip().lower()
    if mode == "full":
        return payload
    if mode == "summary":
        items = [summarize_price_item(x) for x in payload.get("items", [])]
        market_pulse = [x for x in items if x.get("asset_type") == "market_pulse"]
        equities = [x for x in items if x.get("asset_type") == "equity"]
        summary = dict(payload)
        summary["public_json_mode"] = "summary"
        summary["bars_omitted"] = True
        summary["items"] = items
        summary["market_pulse"] = market_pulse
        summary["equities"] = equities
        return summary
    if mode in {"none", "off", "false", "0"}:
        return {}
    raise ValueError(f"Unsupported PRICE_PUBLIC_JSON_MODE={mode!r}. Use full, summary, or none.")


def fetch_symbol(row: UniverseRow, start: datetime, end: datetime) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    source_errors: list[str] = []

    df, err = fetch_from_yfinance(row.symbol, start, end)
    if err:
        source_errors.append(err)

    source = "yfinance"

    if df.empty or len(df) < MIN_BARS_REQUIRED:
        stooq_df, stooq_err = fetch_from_stooq(row.symbol, start, end)
        if stooq_err:
            source_errors.append(stooq_err)

        if not stooq_df.empty and len(stooq_df) >= max(len(df), MIN_ACCEPTABLE_BARS):
            df = stooq_df
            source = "stooq"

    if df.empty or len(df) < MIN_ACCEPTABLE_BARS:
        failure = {
            "symbol": row.symbol,
            "name": row.name,
            "asset_type": row.asset_type,
            "reason": "insufficient_data",
            "bars": int(len(df)) if df is not None else 0,
            "source_errors": source_errors,
        }
        return None, failure

    warnings: list[str] = []

    if len(df) < MIN_BARS_REQUIRED:
        warnings.append(f"bars_below_min_required:{len(df)}<{MIN_BARS_REQUIRED}")

    metrics = compute_metrics(df)

    item = {
        "symbol": row.symbol,
        "name": row.name,
        "theme": row.theme,
        "bucket": row.bucket,
        "priority": row.priority,
        "asset_type": row.asset_type,
        "pulse_label": row.pulse_label,
        "market": "JP",
        "currency": "JPY",
        "source": source,
        "source_symbol": yf_symbol(row.symbol) if source == "yfinance" else stooq_symbol(row.symbol),
        "bars_count": int(len(df)),
        "date_start": df.index[0].date().isoformat(),
        "date_end": df.index[-1].date().isoformat(),
        "is_partial": len(df) < MIN_BARS_REQUIRED,
        "warnings": warnings,
        "source_errors": source_errors,
        "metrics": metrics,
        "bars": df_to_bars(df),
    }

    return item, None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")

    tmp.replace(path)


def main() -> int:
    generated_at = iso_now()
    today = now_jst().date().isoformat()

    start = now_jst() - timedelta(days=LOOKBACK_DAYS)
    end = now_jst()

    PRICE_OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"UNIVERSE_CSV={safe_relative(UNIVERSE_CSV)}")
    print(f"PRICE_OUT_DIR={safe_relative(PRICE_OUT_DIR)}")
    print(f"LOOKBACK_DAYS={LOOKBACK_DAYS}")
    print(f"MIN_BARS_REQUIRED={MIN_BARS_REQUIRED}")
    print(f"UNIVERSE_LIMIT={UNIVERSE_LIMIT}")
    print(f"PRICE_STORE_MODE={PRICE_STORE_MODE}")
    print(f"PRICE_PUBLIC_JSON_MODE={PRICE_PUBLIC_JSON_MODE}")
    print(f"WRITE_DATED_PRICE_JSON={WRITE_DATED_PRICE_JSON}")
    print(f"PRICE_DUCKDB_PATH={PRICE_DUCKDB_PATH}")

    universe = read_universe(UNIVERSE_CSV)
    if UNIVERSE_LIMIT > 0:
        market_pulse_rows = [r for r in universe if r.asset_type == "market_pulse"]
        equity_rows = [r for r in universe if r.asset_type != "market_pulse"]
        universe = equity_rows[:UNIVERSE_LIMIT] + market_pulse_rows
        print(f"Universe limited to equities={min(len(equity_rows), UNIVERSE_LIMIT)} + market_pulse={len(market_pulse_rows)}")

    items: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for idx, row in enumerate(universe, start=1):
        print(f"[{idx}/{len(universe)}] Fetch {row.symbol} {row.name}")

        try:
            item, failure = fetch_symbol(row, start, end)
            if item:
                items.append(item)
                print(
                    f"  OK source={item['source']} bars={item['bars_count']} "
                    f"latest={item['metrics'].get('latest_date')}"
                )
            elif failure:
                failures.append(failure)
                print(f"  FAIL {failure['reason']} errors={failure.get('source_errors')}")

        except Exception as exc:
            failures.append(
                {
                    "symbol": row.symbol,
                    "name": row.name,
                    "asset_type": row.asset_type,
                    "reason": f"exception:{type(exc).__name__}",
                    "message": str(exc),
                    "traceback": traceback.format_exc(limit=5),
                }
            )
            print(f"  EXCEPTION {type(exc).__name__}: {exc}")

        time.sleep(REQUEST_SLEEP_SECONDS)

    items_sorted = sorted(
        items,
        key=lambda x: (
            0 if x.get("asset_type") == "market_pulse" else 1,
            str(x.get("bucket", "")),
            str(x.get("priority", "")),
            str(x.get("symbol", "")),
        ),
    )

    market_pulse = [x for x in items_sorted if x.get("asset_type") == "market_pulse"]
    equities = [x for x in items_sorted if x.get("asset_type") == "equity"]

    payload = {
        "schema_version": "prices-jp-v1",
        "generated_at": generated_at,
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "source_priority": ["yfinance", "stooq"],
        "price_store_mode": PRICE_STORE_MODE,
        "public_json_mode": PRICE_PUBLIC_JSON_MODE,
        "write_dated_price_json": WRITE_DATED_PRICE_JSON,
        "universe_csv": safe_relative(UNIVERSE_CSV),
        "lookback_days": LOOKBACK_DAYS,
        "min_bars_required": MIN_BARS_REQUIRED,
        "min_acceptable_bars": MIN_ACCEPTABLE_BARS,
        "symbols_total": len(universe),
        "symbols_success": len(items_sorted),
        "symbols_failed": len(failures),
        "equities_success": len(equities),
        "market_pulse_success": len(market_pulse),
        "items": items_sorted,
        "market_pulse": market_pulse,
        "equities": equities,
        "failures": failures,
    }

    if PRICE_STORE_MODE in {"json_and_duckdb", "duckdb", "duckdb_only"}:
        try:
            from lib.db import connect_db, safe_rel
            from lib.price_store_duckdb import store_price_payload

            conn = connect_db(PRICE_DUCKDB_PATH)
            store_diag = store_price_payload(conn, payload=payload, run_id=generated_at)
            payload["duckdb"] = {
                "path": safe_rel(PRICE_DUCKDB_PATH),
                **store_diag,
            }
            print(
                "DuckDB stored",
                f"items={store_diag.get('items_stored')}",
                f"bars={store_diag.get('bars_stored')}",
                f"failures={store_diag.get('failures_stored')}",
                f"path={safe_rel(PRICE_DUCKDB_PATH)}",
            )
        except Exception as exc:
            print(f"DuckDB store failed: {type(exc).__name__}: {exc}")
            if PRICE_STORE_MODE in {"duckdb", "duckdb_only", "json_and_duckdb"}:
                raise

    latest_path = PRICE_OUT_DIR / "latest.json"
    dated_path = PRICE_OUT_DIR / f"{today}.json"

    should_write_public_json = (
        PRICE_STORE_MODE != "duckdb_only"
        and PRICE_PUBLIC_JSON_MODE not in {"none", "off", "false", "0"}
    )

    if should_write_public_json:
        public_payload = build_public_payload(payload, PRICE_PUBLIC_JSON_MODE)
        write_json(latest_path, public_payload)

        history: list[dict[str, Any]] = []
        if WRITE_DATED_PRICE_JSON and PRICE_PUBLIC_JSON_MODE == "full":
            write_json(dated_path, public_payload)
            history.append({
                "date": today,
                "path": safe_relative(dated_path),
                "symbols_success": len(items_sorted),
                "symbols_failed": len(failures),
                "public_json_mode": PRICE_PUBLIC_JSON_MODE,
            })
            print(f"Wrote {safe_relative(dated_path)}")
        else:
            print("Skipped dated prices JSON output")

        manifest = {
            "schema_version": "prices-jp-manifest-v1",
            "generated_at": generated_at,
            "latest": safe_relative(latest_path),
            "latest_date": today,
            "public_json_mode": PRICE_PUBLIC_JSON_MODE,
            "write_dated_price_json": WRITE_DATED_PRICE_JSON,
            "history": history,
            "duckdb_path": safe_relative(Path(PRICE_DUCKDB_PATH)),
            "symbols_success": len(items_sorted),
            "symbols_failed": len(failures),
        }

        manifest_path = PRICE_OUT_DIR / "manifest.json"
        write_json(manifest_path, manifest)

        print(f"Wrote {safe_relative(latest_path)}")
        print(f"Wrote {safe_relative(manifest_path)}")
    else:
        print("Skipped site/data/prices-jp JSON output")
    print(f"Success={len(items_sorted)} Failed={len(failures)}")

    if len(items_sorted) == 0:
        print("No symbols fetched successfully. Failing workflow.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
