from __future__ import annotations

from datetime import datetime
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from lib.duckdb_schema import initialize_schema


def _finite(value: Any) -> float | None:
    try:
        v = float(value)
        if np.isfinite(v):
            return v
    except Exception:
        pass
    return None


def _safe_pct(a: pd.Series, b: pd.Series) -> pd.Series:
    return ((a / b.replace(0, np.nan)) - 1.0) * 100.0


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    out = out.where(~((avg_loss == 0) & (avg_gain > 0)), 100.0)
    out = out.where(~((avg_gain == 0) & (avg_loss > 0)), 0.0)
    return out


def _max_drawdown_pct(close: pd.Series, window: int) -> pd.Series:
    rolling_max = close.rolling(window, min_periods=2).max()
    return _safe_pct(close, rolling_max)


def _score_clip(series: pd.Series, lo: float, hi: float) -> pd.Series:
    return ((series - lo) / (hi - lo)).clip(0.0, 1.0)


def build_features_frame(prices: pd.DataFrame) -> pd.DataFrame:
    if prices.empty:
        return pd.DataFrame()
    frames = []
    for ticker, g in prices.groupby("ticker", sort=False):
        g = g.sort_values("date").copy()
        close = pd.to_numeric(g["close"], errors="coerce")
        high = pd.to_numeric(g["high"], errors="coerce")
        low = pd.to_numeric(g["low"], errors="coerce")
        volume = pd.to_numeric(g["volume"], errors="coerce").fillna(0)
        traded_value = pd.to_numeric(g["traded_value_jpy"], errors="coerce")

        f = pd.DataFrame({"ticker": ticker, "date": pd.to_datetime(g["date"]).dt.date})
        f["close"] = close.values
        f["volume"] = volume.values
        f["traded_value_jpy"] = traded_value.values

        for p in [1, 3, 5, 10, 20, 60, 120]:
            f[f"return_{p}d_pct"] = close.pct_change(p).values * 100.0
        for p in [5, 10, 20, 50, 60, 120, 200]:
            ma = close.rolling(p, min_periods=max(3, min(p, 20))).mean()
            f[f"ma_{p}"] = ma.values
        for p in [20, 50, 60, 120, 200]:
            ma = f[f"ma_{p}"]
            f[f"price_vs_ma{p}_pct"] = ((close / pd.Series(ma).replace(0, np.nan)) - 1.0).values * 100.0

        for p in [20, 60, 120, 252]:
            f[f"high_{p}d"] = high.rolling(p, min_periods=max(3, min(p, 20))).max().values
            f[f"low_{p}d"] = low.rolling(p, min_periods=max(3, min(p, 20))).min().values

        f["distance_from_20d_high_pct"] = ((close / pd.Series(f["high_20d"]).replace(0, np.nan)) - 1.0).values * 100.0
        f["distance_from_52w_high_pct"] = ((close / pd.Series(f["high_252d"]).replace(0, np.nan)) - 1.0).values * 100.0
        f["distance_from_20d_low_pct"] = ((close / pd.Series(f["low_20d"]).replace(0, np.nan)) - 1.0).values * 100.0
        f["distance_from_52w_low_pct"] = ((close / pd.Series(f["low_252d"]).replace(0, np.nan)) - 1.0).values * 100.0

        for p in [20, 60, 252]:
            lo = pd.Series(f[f"low_{p}d"])
            hi = pd.Series(f[f"high_{p}d"])
            f[f"range_position_{p}d_0_1"] = ((close - lo) / (hi - lo).replace(0, np.nan)).clip(0, 1).values

        f["avg_volume_20d"] = volume.rolling(20, min_periods=5).mean().values
        f["avg_volume_50d"] = volume.rolling(50, min_periods=10).mean().values
        f["avg_traded_value_20d_jpy"] = traded_value.rolling(20, min_periods=5).mean().values
        f["avg_traded_value_50d_jpy"] = traded_value.rolling(50, min_periods=10).mean().values
        f["volume_ratio_20d"] = (volume / pd.Series(f["avg_volume_20d"]).replace(0, np.nan)).values
        f["volume_ratio_50d"] = (volume / pd.Series(f["avg_volume_50d"]).replace(0, np.nan)).values
        f["volume_dryup_10d"] = (volume.rolling(5, min_periods=3).mean() / volume.rolling(20, min_periods=10).mean().replace(0, np.nan)).values
        f["volume_reaccumulation_score"] = (_score_clip(pd.Series(f["volume_ratio_20d"]), 1.0, 3.0) * _score_clip(close.pct_change(3) * 100.0, -2.0, 6.0)).values

        daily_ret = close.pct_change()
        f["volatility_20d_annualized_pct"] = (daily_ret.rolling(20, min_periods=10).std(ddof=0) * np.sqrt(252) * 100.0).values
        f["volatility_60d_annualized_pct"] = (daily_ret.rolling(60, min_periods=20).std(ddof=0) * np.sqrt(252) * 100.0).values
        for p in [20, 60, 120]:
            f[f"max_drawdown_{p}d_pct"] = _max_drawdown_pct(close, p).values

        f["rsi_14"] = _rsi(close, 14).values
        hh14 = high.rolling(14, min_periods=10).max()
        ll14 = low.rolling(14, min_periods=10).min()
        f["williams_r_14"] = (-100.0 * (hh14 - close) / (hh14 - ll14).replace(0, np.nan)).values
        ma20 = close.rolling(20, min_periods=10).mean()
        sd20 = close.rolling(20, min_periods=10).std(ddof=0)
        upper = ma20 + 2 * sd20
        lower = ma20 - 2 * sd20
        f["bollinger_b_20"] = ((close - lower) / (upper - lower).replace(0, np.nan)).values
        f["bollinger_width_20_pct"] = (((upper - lower) / ma20.replace(0, np.nan)) * 100.0).values
        f["compression_20d_pct"] = (((pd.Series(f["high_20d"]) - pd.Series(f["low_20d"])) / close.replace(0, np.nan)) * 100.0).values

        trend_daily = (
            _score_clip(pd.Series(f["return_20d_pct"]), -5, 18) * 0.35
            + _score_clip(pd.Series(f["price_vs_ma20_pct"]), -5, 10) * 0.30
            + _score_clip(pd.Series(f["range_position_20d_0_1"]), 0.45, 1.0) * 0.35
        )
        trend_weekly = (
            _score_clip(pd.Series(f["return_60d_pct"]), -8, 35) * 0.35
            + _score_clip(pd.Series(f["price_vs_ma120_pct"]), -8, 20) * 0.30
            + _score_clip(pd.Series(f["range_position_252d_0_1"]), 0.45, 1.0) * 0.35
        )
        momentum_short = (
            _score_clip(pd.Series(f["return_1d_pct"]), -1, 8) * 0.25
            + _score_clip(pd.Series(f["return_5d_pct"]), -2, 18) * 0.35
            + _score_clip(pd.Series(f["volume_ratio_20d"]), 0.8, 4.0) * 0.40
        )
        liquidity = _score_clip(np.log10(pd.Series(f["avg_traded_value_20d_jpy"]).clip(lower=1.0)), 7.7, 9.6)
        risk = (
            liquidity * 0.35
            + (1.0 - _score_clip(pd.Series(f["volatility_60d_annualized_pct"]), 25, 95)) * 0.35
            + _score_clip(pd.Series(f["max_drawdown_60d_pct"]), -35, -5) * 0.30
        )
        reversal = (
            (1.0 - _score_clip(pd.Series(f["rsi_14"]), 25, 55)) * 0.25
            + (1.0 - _score_clip(pd.Series(f["williams_r_14"]), -90, -35)) * 0.25
            + (1.0 - _score_clip(pd.Series(f["bollinger_b_20"]), 0.0, 0.55)) * 0.20
            + _score_clip(-pd.Series(f["return_5d_pct"]), 2, 16) * 0.15
            + pd.Series(f["volume_reaccumulation_score"]).fillna(0).clip(0, 1) * 0.15
        )

        f["trend_score_daily"] = trend_daily.clip(0, 1).values
        f["trend_score_weekly_proxy"] = trend_weekly.clip(0, 1).values
        f["momentum_score_short"] = momentum_short.clip(0, 1).values
        f["liquidity_score"] = liquidity.clip(0, 1).values
        f["risk_score"] = risk.clip(0, 1).values
        f["reversal_exhaustion_score"] = reversal.clip(0, 1).values
        f["feature_quality"] = np.where(pd.Series(f["avg_traded_value_20d_jpy"]).notna(), "ok", "thin_or_incomplete")
        f["updated_at"] = datetime.utcnow()
        frames.append(f)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    out = out.replace({np.nan: None})
    return out


def rebuild_features(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    initialize_schema(conn)
    prices = conn.execute(
        """
        SELECT ticker, date, open, high, low, close, volume, traded_value_jpy
        FROM prices_daily
        WHERE close IS NOT NULL AND close > 0
        ORDER BY ticker, date
        """
    ).df()
    if prices.empty:
        raise RuntimeError("prices_daily is empty. Run fetch_prices_jp.py with PRICE_STORE_MODE=json_and_duckdb first.")
    features = build_features_frame(prices)
    conn.execute("DELETE FROM features_daily")
    if not features.empty:
        conn.register("_features_daily", features)
        conn.execute("INSERT INTO features_daily SELECT * FROM _features_daily")
        conn.unregister("_features_daily")
    return {
        "prices_rows": int(len(prices)),
        "feature_rows": int(len(features)),
        "tickers": int(features["ticker"].nunique()) if not features.empty else 0,
        "min_date": str(features["date"].min()) if not features.empty else None,
        "max_date": str(features["date"].max()) if not features.empty else None,
    }
