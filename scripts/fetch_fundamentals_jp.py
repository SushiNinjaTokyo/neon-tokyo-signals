#!/usr/bin/env python3
from __future__ import annotations

"""Fetch lightweight JP company fundamentals and build value features.

This script is intentionally pragmatic.  yfinance fundamentals for Japanese
small caps can be incomplete, so all fields are optional and coverage is
reported.  The script fills:

- fundamentals_latest_jp
- value_features_daily

It never writes public full datasets.  Public pages consume only summaries from
other exporters.
"""

import json
import math
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from lib.db import ROOT, connect_db, safe_rel
from lib.duckdb_schema import initialize_schema

PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
FUNDAMENTALS_LIMIT = int(os.getenv("FUNDAMENTALS_LIMIT", "0") or "0")
REQUEST_SLEEP_SECONDS = float(os.getenv("FUNDAMENTALS_REQUEST_SLEEP_SECONDS", "0.10") or "0.10")
MIN_MARKET_CAP_JPY = float(os.getenv("MIN_MARKET_CAP_JPY", "0") or "0")

FUNDAMENTAL_COLS = [
    "ticker", "fiscal_period", "market_cap_jpy", "revenue_jpy",
    "operating_profit_jpy", "net_income_jpy", "equity_jpy", "roe_pct",
    "roa_pct", "per", "pbr", "psr", "dividend_yield_pct",
    "enterprise_value_jpy", "ev_ebitda", "operating_margin_pct",
    "net_margin_pct", "equity_ratio_pct", "revenue_growth_yoy_pct",
    "operating_profit_growth_yoy_pct", "eps_growth_yoy_pct", "source",
    "source_quality", "error", "updated_at",
]

VALUE_FEATURE_COLS = [
    "ticker", "date", "valuation_discount_score", "quality_guard_score",
    "earnings_stability_score", "shareholder_return_score",
    "re_rating_signal_score", "value_trap_penalty", "value_mispricing_score",
    "valuation_bucket", "value_status", "fundamental_coverage_score",
    "source", "updated_at",
]


def yf_symbol(ticker: str) -> str:
    return ticker if ticker.endswith(".T") else f"{ticker}.T"


def finite(value: Any) -> float | None:
    try:
        if value is None:
            return None
        v = float(value)
        if math.isfinite(v):
            return v
    except Exception:
        return None
    return None


def pct_value(value: Any) -> float | None:
    v = finite(value)
    if v is None:
        return None
    # Yahoo frequently returns 0.123 for 12.3% on margin/yield/ROE fields.
    if abs(v) <= 2.0:
        return v * 100.0
    return v


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def scale(value: Any, lo: float, hi: float, *, invert: bool = False) -> float:
    v = finite(value)
    if v is None or hi == lo:
        return 0.0
    x = clamp01((v - lo) / (hi - lo))
    return 1.0 - x if invert else x


def load_universe(conn) -> pd.DataFrame:
    return conn.execute(
        """
        SELECT ticker, code, name, market, sector, industry, bucket,
               asset_type, is_excluded, is_value_candidate
        FROM universe_master
        WHERE COALESCE(asset_type, 'equity') = 'equity'
          AND COALESCE(is_excluded, FALSE) = FALSE
        ORDER BY is_value_candidate DESC, ticker
        """
    ).df()


def latest_covered_feature_date(conn):
    row = conn.execute(
        """
        WITH counts AS (
          SELECT f.date, COUNT(DISTINCT f.ticker) AS symbols
          FROM features_daily f
          JOIN universe_master u USING (ticker)
          WHERE COALESCE(u.asset_type, 'equity') = 'equity'
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
    return row[0] if row else None


def get_info(ticker: str) -> tuple[dict[str, Any], str | None]:
    try:
        t = yf.Ticker(yf_symbol(ticker))
        info = t.get_info()
        if not isinstance(info, dict) or not info:
            return {}, "empty_info"
        return info, None
    except Exception as exc:
        return {}, f"{type(exc).__name__}: {exc}"


def build_fundamental_row(ticker: str, info: dict[str, Any], error: str | None) -> dict[str, Any]:
    market_cap = finite(info.get("marketCap"))
    revenue = finite(info.get("totalRevenue"))
    op_margin = pct_value(info.get("operatingMargins"))
    net_margin = pct_value(info.get("profitMargins"))
    roe = pct_value(info.get("returnOnEquity"))
    roa = pct_value(info.get("returnOnAssets"))
    per = finite(info.get("trailingPE")) or finite(info.get("forwardPE"))
    pbr = finite(info.get("priceToBook"))
    psr = finite(info.get("priceToSalesTrailing12Months"))
    dividend_yield = pct_value(info.get("dividendYield"))
    enterprise_value = finite(info.get("enterpriseValue"))
    ev_ebitda = finite(info.get("enterpriseToEbitda"))
    shares = finite(info.get("sharesOutstanding"))
    book_value = finite(info.get("bookValue"))

    operating_profit = None
    if revenue is not None and op_margin is not None:
        operating_profit = revenue * op_margin / 100.0
    net_income = finite(info.get("netIncomeToCommon"))
    if net_income is None and revenue is not None and net_margin is not None:
        net_income = revenue * net_margin / 100.0
    equity = None
    if book_value is not None and shares is not None:
        equity = book_value * shares
    elif market_cap is not None and pbr not in (None, 0):
        equity = market_cap / pbr

    present = sum(v is not None for v in [market_cap, per, pbr, psr, roe, roa, revenue, operating_profit, net_income, equity])
    source_quality = "ok" if present >= 4 else "partial" if present > 0 else "empty"
    if error:
        source_quality = "error"

    return {
        "ticker": ticker,
        "fiscal_period": str(info.get("mostRecentQuarter") or info.get("lastFiscalYearEnd") or "latest"),
        "market_cap_jpy": market_cap,
        "revenue_jpy": revenue,
        "operating_profit_jpy": operating_profit,
        "net_income_jpy": net_income,
        "equity_jpy": equity,
        "roe_pct": roe,
        "roa_pct": roa,
        "per": per,
        "pbr": pbr,
        "psr": psr,
        "dividend_yield_pct": dividend_yield,
        "enterprise_value_jpy": enterprise_value,
        "ev_ebitda": ev_ebitda,
        "operating_margin_pct": op_margin,
        "net_margin_pct": net_margin,
        "equity_ratio_pct": None,
        "revenue_growth_yoy_pct": pct_value(info.get("revenueGrowth")),
        "operating_profit_growth_yoy_pct": None,
        "eps_growth_yoy_pct": pct_value(info.get("earningsGrowth")),
        "source": "yfinance",
        "source_quality": source_quality,
        "error": error,
        "updated_at": datetime.utcnow(),
    }


def score_value_row(fund: dict[str, Any], feature: dict[str, Any] | None) -> dict[str, Any]:
    per = fund.get("per")
    pbr = fund.get("pbr")
    psr = fund.get("psr")
    roe = fund.get("roe_pct")
    opm = fund.get("operating_margin_pct")
    dy = fund.get("dividend_yield_pct")
    market_cap = fund.get("market_cap_jpy")
    f = feature or {}

    # Lower valuation ratios are better, but avoid rewarding impossible/negative values.
    per_score = 0.0 if per is None or per <= 0 else scale(per, 8, 35, invert=True)
    pbr_score = 0.0 if pbr is None or pbr <= 0 else scale(pbr, 0.6, 4.0, invert=True)
    psr_score = 0.0 if psr is None or psr <= 0 else scale(psr, 0.5, 8.0, invert=True)
    valuation_discount = clamp01(per_score * 0.42 + pbr_score * 0.38 + psr_score * 0.20)

    quality = clamp01(scale(roe, 4, 18) * 0.45 + scale(opm, 4, 22) * 0.35 + scale(market_cap, 20_000_000_000, 2_000_000_000_000) * 0.20)
    shareholder = clamp01(scale(dy, 0.0, 4.0))
    r20 = f.get("return_20d_pct")
    r60 = f.get("return_60d_pct")
    range252 = f.get("range_position_252d_0_1")
    liq = f.get("liquidity_score")
    rerating = clamp01(scale(r20, -5, 18) * 0.35 + scale(r60, -15, 35) * 0.25 + scale(range252, 0.10, 0.75) * 0.20 + scale(liq, 0.15, 0.90) * 0.20)

    trap_penalty = 0.0
    if roe is not None and roe < 0:
        trap_penalty += 0.25
    if opm is not None and opm < 0:
        trap_penalty += 0.20
    if f.get("return_60d_pct") is not None and f.get("return_60d_pct") < -45:
        trap_penalty += 0.20
    trap_penalty = clamp01(trap_penalty)

    coverage = sum(x is not None for x in [per, pbr, psr, roe, opm, market_cap]) / 6.0
    mispricing = clamp01(valuation_discount * 0.36 + quality * 0.24 + rerating * 0.24 + shareholder * 0.06 + coverage * 0.10 - trap_penalty * 0.35)
    status = "tradeable_value" if coverage >= 0.5 else "proxy_only" if coverage > 0 else "no_fundamentals"
    bucket = "deep_value" if valuation_discount >= 0.7 and quality >= 0.45 else "quality_value" if mispricing >= 0.62 else "watch_value" if mispricing >= 0.45 else "not_value"

    return {
        "valuation_discount_score": round(valuation_discount, 6),
        "quality_guard_score": round(quality, 6),
        "earnings_stability_score": round(quality, 6),
        "shareholder_return_score": round(shareholder, 6),
        "re_rating_signal_score": round(rerating, 6),
        "value_trap_penalty": round(trap_penalty, 6),
        "value_mispricing_score": round(mispricing, 6),
        "valuation_bucket": bucket,
        "value_status": status,
        "fundamental_coverage_score": round(coverage, 6),
        "source": "yfinance+price_features",
    }


def main() -> int:
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)
    universe = load_universe(conn)
    if FUNDAMENTALS_LIMIT > 0:
        universe = universe.head(FUNDAMENTALS_LIMIT)
    if universe.empty:
        raise SystemExit("universe_master has no equity rows. Run universe + price build first.")

    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for idx, r in universe.iterrows():
        ticker = str(r["ticker"])
        print(f"[{len(rows)+len(failures)+1}/{len(universe)}] fundamentals {ticker}")
        info, err = get_info(ticker)
        row = build_fundamental_row(ticker, info, err)
        if err:
            failures.append({"ticker": ticker, "error": err})
        rows.append(row)
        time.sleep(REQUEST_SLEEP_SECONDS)

    # Replace latest rows for fetched tickers.
    tickers = [r["ticker"] for r in rows]
    if tickers:
        tick_df = pd.DataFrame({"ticker": tickers})
        conn.register("_fundamental_tickers", tick_df)
        conn.execute("DELETE FROM fundamentals_latest_jp USING _fundamental_tickers t WHERE fundamentals_latest_jp.ticker = t.ticker")
        conn.unregister("_fundamental_tickers")
        df = pd.DataFrame(rows)
        for col in FUNDAMENTAL_COLS:
            if col not in df.columns:
                df[col] = None
        df = df[FUNDAMENTAL_COLS]
        conn.register("_fundamentals_latest_jp", df)
        cols_sql = ", ".join(FUNDAMENTAL_COLS)
        conn.execute(f"INSERT INTO fundamentals_latest_jp ({cols_sql}) SELECT {cols_sql} FROM _fundamentals_latest_jp")
        conn.unregister("_fundamentals_latest_jp")

    feature_date = latest_covered_feature_date(conn)
    value_rows: list[dict[str, Any]] = []
    if feature_date:
        fdf = conn.execute("SELECT * FROM features_daily WHERE date = ?", [feature_date]).df()
        fmap = {str(r["ticker"]): r.to_dict() for _, r in fdf.iterrows()}
        for row in rows:
            score = score_value_row(row, fmap.get(row["ticker"]))
            value_rows.append({
                "ticker": row["ticker"],
                "date": feature_date,
                **score,
                "updated_at": datetime.utcnow(),
            })
        conn.execute("DELETE FROM value_features_daily WHERE date = ?", [feature_date])
        if value_rows:
            vdf = pd.DataFrame(value_rows)
            for col in VALUE_FEATURE_COLS:
                if col not in vdf.columns:
                    vdf[col] = None
            vdf = vdf[VALUE_FEATURE_COLS]
            conn.register("_value_features_daily", vdf)
            cols_sql = ", ".join(VALUE_FEATURE_COLS)
            conn.execute(f"INSERT INTO value_features_daily ({cols_sql}) SELECT {cols_sql} FROM _value_features_daily")
            conn.unregister("_value_features_daily")

    total = len(rows)
    metric_counts = {}
    for m in ["market_cap_jpy", "per", "pbr", "psr", "roe_pct", "operating_margin_pct", "dividend_yield_pct"]:
        metric_counts[m] = sum(1 for r in rows if r.get(m) is not None)
    diag = {
        "schema_version": "fundamentals_jp_fetch_diagnostics_v1",
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "duckdb_path": safe_rel(Path(PRICE_DUCKDB_PATH)),
        "rows_fetched": total,
        "failures": failures[:100],
        "failure_count": len(failures),
        "feature_date_for_value_features": str(feature_date) if feature_date else None,
        "value_feature_rows": len(value_rows),
        "metric_coverage": {m: {"count": c, "coverage_pct": round(c / total * 100.0, 2) if total else 0} for m, c in metric_counts.items()},
    }
    out = ROOT / "site" / "data" / "japan" / "ai-arena" / "diagnostics" / "fundamentals-latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(diag, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {safe_rel(out)}")
    print(f"fundamentals_rows={total} value_feature_rows={len(value_rows)} failures={len(failures)}")
    return 0 if total > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
