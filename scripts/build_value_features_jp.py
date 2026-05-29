#!/usr/bin/env python3
from __future__ import annotations

"""Build daily value features for HIZUMI from DuckDB fundamentals.

This script intentionally does not fetch new fundamentals.  It converts the
latest available fundamentals snapshot into daily value/mispricing features by
joining it with features_daily for each covered signal date.

Why this exists:
- fetch_fundamentals_jp.py owns fundamentals_latest_jp ingestion.
- build_value_features_jp.py owns value_features_daily range generation.
- build_agent_scores_jp.py can then score HIZUMI historically without relying
  on daily/weekly JSON or a single latest-date value snapshot.
"""

import json
import math
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from lib.arena_calendar_jp import parse_date
from lib.db import ROOT, connect_db, safe_rel, scalar
from lib.duckdb_schema import initialize_schema

PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()
DIAG_PATH = OUT_DIR / "data" / "japan" / "ai-arena" / "diagnostics" / "value-features.json"

VALUE_FEATURE_COLS = [
    "ticker",
    "date",
    "valuation_discount_score",
    "quality_guard_score",
    "earnings_stability_score",
    "shareholder_return_score",
    "re_rating_signal_score",
    "value_trap_penalty",
    "value_mispricing_score",
    "valuation_bucket",
    "value_status",
    "fundamental_coverage_score",
    "source",
    "updated_at",
]


def first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def finite(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if pd.isna(value):
            return None
        v = float(value)
        if math.isfinite(v):
            return v
    except Exception:
        return None
    return None


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def scale(value: Any, lo: float, hi: float, *, invert: bool = False) -> float:
    v = finite(value)
    if v is None or hi == lo:
        return 0.0
    x = clamp01((v - lo) / (hi - lo))
    return 1.0 - x if invert else x


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)


def latest_equity_feature_date(conn) -> date | None:
    row = conn.execute(
        """
        WITH counts AS (
          SELECT f.date, COUNT(DISTINCT f.ticker) AS symbols
          FROM features_daily f
          JOIN universe_master u USING (ticker)
          WHERE COALESCE(LOWER(u.asset_type), 'equity') = 'equity'
            AND COALESCE(u.is_excluded, FALSE) = FALSE
          GROUP BY 1
        ), mx AS (SELECT MAX(symbols) AS max_symbols FROM counts)
        SELECT date
        FROM counts, mx
        WHERE symbols >= GREATEST(1, CAST(CEIL(max_symbols * 0.70) AS INTEGER))
        ORDER BY date DESC
        LIMIT 1
        """
    ).fetchone()
    return parse_date(row[0]) if row and row[0] is not None else None


def resolve_year(conn) -> int:
    raw = first_env("VALUE_FEATURE_YEAR", "AI_ARENA_YEAR", "ARENA_YEAR", "YEAR", default=str(datetime.utcnow().year))
    if raw.lower() == "auto":
        d = latest_equity_feature_date(conn)
        return int(d.year if d else datetime.utcnow().year)
    return int(raw)


def resolve_range(conn) -> tuple[date | None, date | None, dict[str, Any]]:
    year = resolve_year(conn)
    raw_start = first_env("VALUE_FEATURE_START_DATE", "AGENT_SCORE_START_DATE", "AI_ARENA_START_DATE", "START_DATE", default=f"{year}-01-01")
    raw_end = first_env("VALUE_FEATURE_END_DATE", "AGENT_SCORE_END_DATE", "AI_ARENA_END_DATE", "END_DATE", default="")

    # Keep this script tolerant of the same `auto` convention used by
    # build_agent_scores_jp.py and the AI Arena workflows.
    # - start=auto means the calendar-year season start.
    # - end=auto means the latest sufficiently covered feature date.
    if not raw_start or raw_start.lower() == "auto":
        start = date(year, 1, 1)
    else:
        start = parse_date(raw_start)

    if not raw_end or raw_end.lower() == "auto":
        end = latest_equity_feature_date(conn)
    else:
        end = parse_date(raw_end)

    return start, end, {"year": year, "start_date": str(start) if start else None, "end_date": str(end) if end else None}


def load_fundamentals(conn) -> pd.DataFrame:
    return conn.execute(
        """
        SELECT *
        FROM fundamentals_latest_jp
        WHERE ticker IS NOT NULL
        """
    ).df()


def load_feature_dates(conn, start: date, end: date) -> list[date]:
    rows = conn.execute(
        """
        SELECT f.date, COUNT(DISTINCT f.ticker) AS symbols
        FROM features_daily f
        JOIN universe_master u USING (ticker)
        WHERE f.date BETWEEN ? AND ?
          AND COALESCE(LOWER(u.asset_type), 'equity') = 'equity'
          AND COALESCE(u.is_excluded, FALSE) = FALSE
        GROUP BY 1
        HAVING COUNT(DISTINCT f.ticker) > 0
        ORDER BY 1
        """,
        [start, end],
    ).fetchall()
    return [parse_date(r[0]) for r in rows if parse_date(r[0]) is not None]


def score_value_row(fund: dict[str, Any], feature: dict[str, Any] | None) -> dict[str, Any]:
    per = finite(fund.get("per"))
    pbr = finite(fund.get("pbr"))
    psr = finite(fund.get("psr"))
    roe = finite(fund.get("roe_pct"))
    roa = finite(fund.get("roa_pct"))
    opm = finite(fund.get("operating_margin_pct"))
    netm = finite(fund.get("net_margin_pct"))
    dy = finite(fund.get("dividend_yield_pct"))
    market_cap = finite(fund.get("market_cap_jpy"))
    revenue_growth = finite(fund.get("revenue_growth_yoy_pct"))
    op_growth = finite(fund.get("operating_profit_growth_yoy_pct"))
    eps_growth = finite(fund.get("eps_growth_yoy_pct"))
    f = feature or {}

    # Lower valuation ratios are better, but do not reward impossible negatives.
    per_score = 0.0 if per is None or per <= 0 else scale(per, 8, 35, invert=True)
    pbr_score = 0.0 if pbr is None or pbr <= 0 else scale(pbr, 0.6, 4.0, invert=True)
    psr_score = 0.0 if psr is None or psr <= 0 else scale(psr, 0.5, 8.0, invert=True)
    valuation_discount = clamp01(per_score * 0.42 + pbr_score * 0.38 + psr_score * 0.20)

    quality = clamp01(
        scale(roe, 4, 18) * 0.34
        + scale(roa, 2, 10) * 0.14
        + scale(opm, 4, 22) * 0.24
        + scale(netm, 2, 14) * 0.08
        + scale(market_cap, 20_000_000_000, 2_000_000_000_000) * 0.20
    )
    stability = clamp01(
        scale(revenue_growth, -8, 20) * 0.25
        + scale(op_growth, -15, 30) * 0.25
        + scale(eps_growth, -20, 35) * 0.20
        + quality * 0.30
    )
    shareholder = clamp01(scale(dy, 0.0, 4.0))

    r20 = f.get("return_20d_pct")
    r60 = f.get("return_60d_pct")
    range252 = f.get("range_position_252d_0_1")
    liq = f.get("liquidity_score")
    rerating = clamp01(
        scale(r20, -5, 18) * 0.35
        + scale(r60, -15, 35) * 0.25
        + scale(range252, 0.10, 0.75) * 0.20
        + scale(liq, 0.15, 0.90) * 0.20
    )

    trap_penalty = 0.0
    if roe is not None and roe < 0:
        trap_penalty += 0.25
    if opm is not None and opm < 0:
        trap_penalty += 0.20
    if per is not None and per <= 0:
        trap_penalty += 0.10
    if pbr is not None and pbr <= 0:
        trap_penalty += 0.10
    r60v = finite(f.get("return_60d_pct"))
    if r60v is not None and r60v < -45:
        trap_penalty += 0.20
    trap_penalty = clamp01(trap_penalty)

    coverage_inputs = [per, pbr, psr, roe, roa, opm, market_cap]
    coverage = sum(x is not None for x in coverage_inputs) / float(len(coverage_inputs))
    mispricing = clamp01(
        valuation_discount * 0.34
        + quality * 0.22
        + stability * 0.10
        + rerating * 0.22
        + shareholder * 0.04
        + coverage * 0.08
        - trap_penalty * 0.35
    )
    status = "tradeable_value" if coverage >= 0.50 else "proxy_only" if coverage > 0 else "no_fundamentals"
    bucket = "deep_value" if valuation_discount >= 0.70 and quality >= 0.45 else "quality_value" if mispricing >= 0.62 else "watch_value" if mispricing >= 0.45 else "not_value"

    return {
        "valuation_discount_score": round(valuation_discount, 6),
        "quality_guard_score": round(quality, 6),
        "earnings_stability_score": round(stability, 6),
        "shareholder_return_score": round(shareholder, 6),
        "re_rating_signal_score": round(rerating, 6),
        "value_trap_penalty": round(trap_penalty, 6),
        "value_mispricing_score": round(mispricing, 6),
        "valuation_bucket": bucket,
        "value_status": status,
        "fundamental_coverage_score": round(coverage, 6),
        "source": "fundamentals_latest_jp+features_daily",
    }


def build_rows_for_date(conn, fundamentals: pd.DataFrame, d: date, updated_at: datetime) -> list[dict[str, Any]]:
    fdf = conn.execute("SELECT * FROM features_daily WHERE date = ?", [d]).df()
    fmap = {str(r["ticker"]): r.to_dict() for _, r in fdf.iterrows()} if not fdf.empty else {}
    rows: list[dict[str, Any]] = []
    for _, fr in fundamentals.iterrows():
        fund = fr.to_dict()
        ticker = str(fund.get("ticker") or "")
        if not ticker:
            continue
        score = score_value_row(fund, fmap.get(ticker))
        rows.append({"ticker": ticker, "date": d, **score, "updated_at": updated_at})
    return rows


def insert_value_rows(conn, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    df = pd.DataFrame(rows)
    for col in VALUE_FEATURE_COLS:
        if col not in df.columns:
            df[col] = None
    df = df[VALUE_FEATURE_COLS]
    conn.register("_value_features_daily", df)
    cols_sql = ", ".join(VALUE_FEATURE_COLS)
    conn.execute(f"INSERT INTO value_features_daily ({cols_sql}) SELECT {cols_sql} FROM _value_features_daily")
    conn.unregister("_value_features_daily")


def main() -> int:
    generated_at = datetime.utcnow()
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)

    fundamentals_rows = int(scalar(conn, "SELECT COUNT(*) FROM fundamentals_latest_jp") or 0)
    if fundamentals_rows <= 0:
        raise SystemExit("fundamentals_latest_jp is empty. Run scripts/fetch_fundamentals_jp.py or restore canonical DuckDB first.")

    start, end, range_diag = resolve_range(conn)
    if start is None or end is None:
        raise SystemExit("Could not resolve value feature date range. Check features_daily coverage.")
    if start > end:
        raise SystemExit(f"Invalid value feature range: start={start} end={end}")

    fundamentals = load_fundamentals(conn)
    if fundamentals.empty:
        raise SystemExit("No fundamentals rows loaded from fundamentals_latest_jp.")

    feature_dates = load_feature_dates(conn, start, end)
    if not feature_dates:
        raise SystemExit(f"No features_daily dates found for {start} - {end}")

    conn.execute("DELETE FROM value_features_daily WHERE date BETWEEN ? AND ?", [start, end])
    total_rows = 0
    chunk: list[dict[str, Any]] = []
    chunk_size = int(os.getenv("VALUE_FEATURE_INSERT_CHUNK_ROWS", "50000") or "50000")
    for d in feature_dates:
        rows = build_rows_for_date(conn, fundamentals, d, generated_at)
        chunk.extend(rows)
        total_rows += len(rows)
        if len(chunk) >= chunk_size:
            insert_value_rows(conn, chunk)
            chunk = []
    insert_value_rows(conn, chunk)

    inserted_rows = int(scalar(conn, "SELECT COUNT(*) FROM value_features_daily WHERE date BETWEEN ? AND ?", [start, end]) or 0)
    date_count = int(scalar(conn, "SELECT COUNT(DISTINCT date) FROM value_features_daily WHERE date BETWEEN ? AND ?", [start, end]) or 0)
    hizumi_ready_rows = int(scalar(conn, "SELECT COUNT(*) FROM value_features_daily WHERE date BETWEEN ? AND ? AND value_mispricing_score IS NOT NULL", [start, end]) or 0)

    diag = {
        "schema_version": "value_features_jp_diagnostics_v1",
        "generated_at": generated_at.isoformat(timespec="seconds") + "Z",
        "duckdb_path": safe_rel(Path(PRICE_DUCKDB_PATH)),
        "range": range_diag,
        "fundamentals_rows": fundamentals_rows,
        "feature_date_count": len(feature_dates),
        "value_feature_rows_built": total_rows,
        "value_feature_rows_inserted": inserted_rows,
        "value_feature_date_count": date_count,
        "hizumi_ready_rows": hizumi_ready_rows,
        "first_feature_date": str(feature_dates[0]) if feature_dates else None,
        "last_feature_date": str(feature_dates[-1]) if feature_dates else None,
    }
    write_json(DIAG_PATH, diag)
    print(f"Wrote {safe_rel(DIAG_PATH)}")
    print(f"value_feature_rows_inserted={inserted_rows}")
    print(f"value_feature_date_count={date_count}")
    if inserted_rows <= 0 or date_count <= 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
