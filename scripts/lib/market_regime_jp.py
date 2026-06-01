from __future__ import annotations

"""Market-regime utilities for JP AI Arena agents.

The Arena agents mostly trade single stocks, but HIZUMI, KAESHI, and SAGURI are
especially sensitive to broad market conditions:

- HIZUMI can mistake a falling market for value.
- KAESHI can buy oversold names before a real reversal.
- SAGURI can lose liquidity in weak small-cap regimes.

This module derives a compact daily market regime from market-pulse ETFs stored
in `prices_daily`.  It deliberately uses simple, inspectable rules rather than a
black-box model so the trading behavior remains maintainable.

Default proxies:
- 1306.T: TOPIX ETF
- 1321.T: Nikkei 225 ETF
- 2516.T: TSE Growth ETF

Output columns are safe to join onto equity feature rows.  If market-pulse data
is missing for a date, the latest prior regime is forward-filled so scheduled
runs do not fail merely because a proxy ETF has a holiday/stale quote mismatch.
"""

import math
import os
from datetime import date
from typing import Any

import duckdb
import pandas as pd


TOPIX_PROXY = os.getenv("JP_MARKET_REGIME_TOPIX_PROXY", "1306.T").upper()
NIKKEI_PROXY = os.getenv("JP_MARKET_REGIME_NIKKEI_PROXY", "1321.T").upper()
GROWTH_PROXY = os.getenv("JP_MARKET_REGIME_GROWTH_PROXY", "2516.T").upper()

REGIME_COLUMNS = [
    "date",
    "market_regime_state",
    "market_regime_score",
    "topix_return_5d_pct",
    "topix_return_20d_pct",
    "topix_price_vs_ma25_pct",
    "nikkei_return_5d_pct",
    "nikkei_return_20d_pct",
    "nikkei_price_vs_ma25_pct",
    "growth_return_5d_pct",
    "growth_return_20d_pct",
    "growth_price_vs_ma25_pct",
]

FEATURE_REGIME_COLUMNS = [c for c in REGIME_COLUMNS if c != "date"]


def _finite(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or pd.isna(value):
            return default
        v = float(value)
        if math.isfinite(v):
            return v
    except Exception:
        return default
    return default


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _trend_component(close_vs_ma25_pct: Any, return_20d_pct: Any, return_5d_pct: Any) -> float:
    """Convert one market proxy into a 0-1 trend score."""
    cv = _finite(close_vs_ma25_pct, 0.0) or 0.0
    r20 = _finite(return_20d_pct, 0.0) or 0.0
    r5 = _finite(return_5d_pct, 0.0) or 0.0
    score = 0.0
    if cv > 0:
        score += 0.35
    if r20 > 0:
        score += 0.25
    # Reward resilience; heavily weak 5D action should not receive this point.
    if r5 > -2.0:
        score += 0.20
    # Smooth slope bonus so borderline regimes do not flip too violently.
    score += _clamp01((r20 + 8.0) / 20.0) * 0.20
    return _clamp01(score)


def _regime_state(*, score: float, topix_r5: float, topix_r20: float, growth_r5: float, growth_r20: float) -> str:
    if topix_r5 <= -4.0 or growth_r5 <= -7.0:
        return "PANIC"
    if topix_r20 <= -5.0 or growth_r20 <= -8.0 or score < 0.45:
        return "BEAR"
    if score >= 0.70:
        return "BULL"
    return "NEUTRAL"


def build_market_regime_frame(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Build a daily regime frame from prices_daily market-pulse proxy ETFs."""
    tickers = [TOPIX_PROXY, NIKKEI_PROXY, GROWTH_PROXY]
    prices = conn.execute(
        """
        SELECT ticker, date, close
        FROM prices_daily
        WHERE ticker IN (?, ?, ?)
          AND close IS NOT NULL
          AND close > 0
        ORDER BY ticker, date
        """,
        tickers,
    ).df()
    if prices.empty:
        return pd.DataFrame(columns=REGIME_COLUMNS)

    frames: list[pd.DataFrame] = []
    label_by_ticker = {TOPIX_PROXY: "topix", NIKKEI_PROXY: "nikkei", GROWTH_PROXY: "growth"}
    for ticker, g in prices.groupby("ticker", sort=False):
        label = label_by_ticker.get(str(ticker).upper())
        if not label:
            continue
        g = g.sort_values("date").copy()
        close = pd.to_numeric(g["close"], errors="coerce")
        ma25 = close.rolling(25, min_periods=10).mean()
        f = pd.DataFrame({"date": pd.to_datetime(g["date"]).dt.date})
        f[f"{label}_return_5d_pct"] = close.pct_change(5) * 100.0
        f[f"{label}_return_20d_pct"] = close.pct_change(20) * 100.0
        f[f"{label}_price_vs_ma25_pct"] = ((close / ma25.replace(0, pd.NA)) - 1.0) * 100.0
        frames.append(f)

    if not frames:
        return pd.DataFrame(columns=REGIME_COLUMNS)

    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on="date", how="outer")
    out = out.sort_values("date").reset_index(drop=True)

    # Forward-fill proxy metrics to handle ETF-specific missing dates.  Use zero
    # for early rows without enough rolling history so the regime starts neutral.
    metric_cols = [c for c in out.columns if c != "date"]
    out[metric_cols] = out[metric_cols].ffill().fillna(0.0)

    states: list[str] = []
    scores: list[float] = []
    for _, row in out.iterrows():
        topix_score = _trend_component(row.get("topix_price_vs_ma25_pct"), row.get("topix_return_20d_pct"), row.get("topix_return_5d_pct"))
        nikkei_score = _trend_component(row.get("nikkei_price_vs_ma25_pct"), row.get("nikkei_return_20d_pct"), row.get("nikkei_return_5d_pct"))
        growth_score = _trend_component(row.get("growth_price_vs_ma25_pct"), row.get("growth_return_20d_pct"), row.get("growth_return_5d_pct"))
        score = _clamp01(topix_score * 0.40 + nikkei_score * 0.25 + growth_score * 0.35)
        topix_r5 = _finite(row.get("topix_return_5d_pct"), 0.0) or 0.0
        topix_r20 = _finite(row.get("topix_return_20d_pct"), 0.0) or 0.0
        growth_r5 = _finite(row.get("growth_return_5d_pct"), 0.0) or 0.0
        growth_r20 = _finite(row.get("growth_return_20d_pct"), 0.0) or 0.0
        states.append(_regime_state(score=score, topix_r5=topix_r5, topix_r20=topix_r20, growth_r5=growth_r5, growth_r20=growth_r20))
        scores.append(round(score, 6))

    out["market_regime_state"] = states
    out["market_regime_score"] = scores

    for col in REGIME_COLUMNS:
        if col not in out.columns:
            out[col] = 0.0 if col != "market_regime_state" else "NEUTRAL"
    return out[REGIME_COLUMNS]


def attach_market_regime(features: pd.DataFrame, conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Attach market-regime columns to a feature frame by date."""
    if features.empty or "date" not in features.columns:
        return features
    regime = build_market_regime_frame(conn)
    out = features.copy()
    if regime.empty:
        out["market_regime_state"] = "NEUTRAL"
        out["market_regime_score"] = 0.50
        for c in FEATURE_REGIME_COLUMNS:
            if c not in out.columns:
                out[c] = 0.0 if c != "market_regime_state" else "NEUTRAL"
        return out
    out["_regime_join_date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    regime = regime.rename(columns={"date": "_regime_join_date"})
    out = out.merge(regime, on="_regime_join_date", how="left")
    out = out.drop(columns=["_regime_join_date"])
    out["market_regime_state"] = out["market_regime_state"].fillna("NEUTRAL")
    out["market_regime_score"] = pd.to_numeric(out["market_regime_score"], errors="coerce").fillna(0.50)
    numeric_cols = [c for c in FEATURE_REGIME_COLUMNS if c not in {"market_regime_state"}]
    for c in numeric_cols:
        out[c] = pd.to_numeric(out.get(c), errors="coerce").fillna(0.0)
    return out


def regime_for_date(conn: duckdb.DuckDBPyConnection, d: date) -> dict[str, Any]:
    """Return the latest available regime at or before `d`."""
    frame = build_market_regime_frame(conn)
    if frame.empty:
        return {"market_regime_state": "NEUTRAL", "market_regime_score": 0.50}
    frame = frame.copy()
    frame["_d"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
    eligible = frame[frame["_d"] <= d]
    if eligible.empty:
        row = frame.iloc[0].to_dict()
    else:
        row = eligible.sort_values("_d").iloc[-1].to_dict()
    row.pop("date", None)
    row.pop("_d", None)
    return row
