#!/usr/bin/env python3
"""
Build Daily JP signal ranking from normalized JP price JSON.

FutureTech-derived v2 logic for Neon Tokyo Signals.

Input:
- site/data/prices-jp/latest.json

Output:
- site/data/daily-jp/latest.json
- site/data/daily-jp/manifest.json
- site/data/daily-jp/YYYY-MM-DD.json

Design:
- Daily signal is NOT a simple momentum ranking.
- It is an event/timing score emphasizing:
  1. Volume + liquidity shock
  2. Compression release
  3. Breakout setup quality
  4. Relative strength vs TOPIX
  5. Entry timing discipline
  6. Market regime alignment
  7. Penalty controls

News/disclosure/fundamentals are intentionally excluded in this version.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()
else:
    OUT_DIR = OUT_DIR.resolve()

PRICES_JSON = Path(
    os.getenv("PRICES_JSON", str(OUT_DIR / "data" / "prices-jp" / "latest.json"))
)
if not PRICES_JSON.is_absolute():
    PRICES_JSON = (ROOT / PRICES_JSON).resolve()
else:
    PRICES_JSON = PRICES_JSON.resolve()

DAILY_OUT_DIR = OUT_DIR / "data" / "daily-jp"

TZ = ZoneInfo("Asia/Tokyo")


WEIGHTS = {
    "volume_liquidity_shock": 0.24,
    "compression_release": 0.22,
    "breakout_setup_quality": 0.20,
    "relative_strength": 0.16,
    "entry_timing": 0.15,
    "market_regime": 0.03,
}

# Post-score flow adjustment. This is intentionally not part of the base weights
# because it is a short-term discovery overlay, not a core trend model.
# The overlay is capped tightly to avoid turning every volume spike into a signal.
ACCUMULATION_BOOST_CAP = 0.075
DISTRIBUTION_PENALTY_CAP = 0.180
VOLUME_NOISE_PENALTY_CAP = 0.075
FAVORABLE_ARCHETYPE_BOOST_CAP = 0.045
VOLUME_BREAKOUT_RISK_PENALTY_CAP = 0.090
DAILY_MAIN_RANK_LIMIT = int(os.getenv("DAILY_MAIN_RANK_LIMIT", "20"))
SCORE_SCALE = 1000


def now_jst() -> datetime:
    return datetime.now(TZ)


def iso_now() -> str:
    return now_jst().isoformat(timespec="seconds")


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON not found: {safe_relative(path)}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")

    tmp.replace(path)


def to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        v = float(value)
        if not math.isfinite(v):
            return None
        return v
    except Exception:
        return None


def to_int(value: Any) -> int | None:
    v = to_float(value)
    if v is None:
        return None
    return int(round(v))


def safe_round(value: Any, digits: int = 4) -> float | None:
    v = to_float(value)
    if v is None:
        return None
    return round(v, digits)


def clamp(value: Any, low: float = 0.0, high: float = 1.0) -> float:
    v = to_float(value)
    if v is None:
        return low
    return max(low, min(high, v))


def scale(value: Any, low: float, high: float) -> float:
    v = to_float(value)
    if v is None or high == low:
        return 0.0
    return clamp((v - low) / (high - low), 0.0, 1.0)


def classify_liquidity_band(avg_value20: Any, dollar_vol: Any = None) -> str:
    """
    Tradability bands for JP daily signals.

    The previous labels made the middle bucket look cleaner than it really was.
    This version separates institutional-grade liquidity from merely tradable
    liquidity, and keeps sub-100m JPY names out of Trade by default.
    """
    avg = to_float(avg_value20)
    today = to_float(dollar_vol)

    if avg is None:
        return "Unknown"
    if avg >= 1_000_000_000:
        return "High Liquidity"
    if avg >= 300_000_000:
        return "Tradable"
    if avg >= 100_000_000:
        return "Thin"
    if today is not None and today >= 300_000_000 and avg >= 70_000_000:
        return "Event Thin"
    return "Very Thin"


def liquidity_score_from_band(band: str) -> float:
    return {
        "High Liquidity": 1.00,
        "Tradable": 0.78,
        "Thin": 0.42,
        "Event Thin": 0.34,
        "Very Thin": 0.10,
        "Unknown": 0.00,
    }.get(str(band or ""), 0.0)


def pct(cur: Any, prev: Any) -> float | None:
    c = to_float(cur)
    p = to_float(prev)
    if c is None or p is None or p == 0:
        return None
    return (c / p - 1.0) * 100.0


def bars_to_df(item: dict[str, Any]) -> pd.DataFrame:
    bars = item.get("bars") or []
    if not isinstance(bars, list) or not bars:
        return pd.DataFrame()

    rows = []
    for bar in bars:
        if not isinstance(bar, dict):
            continue
        date = bar.get("date")
        if not date:
            continue
        rows.append(
            {
                "date": date,
                "Open": to_float(bar.get("open")),
                "High": to_float(bar.get("high")),
                "Low": to_float(bar.get("low")),
                "Close": to_float(bar.get("close")),
                "Volume": to_float(bar.get("volume")) or 0.0,
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "Open", "High", "Low", "Close"])
    df = df.set_index("date").sort_index()

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df = df[df["Close"] > 0]
    df = df[~df.index.duplicated(keep="last")]

    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    d = df.copy().sort_index()

    c = d["Close"]
    h = d["High"]
    l = d["Low"]
    v = d["Volume"]

    d["sma10"] = c.rolling(10, min_periods=5).mean()
    d["sma20"] = c.rolling(20, min_periods=8).mean()
    d["sma50"] = c.rolling(50, min_periods=20).mean()
    d["sma150"] = c.rolling(150, min_periods=60).mean()

    d["high5"] = h.rolling(5, min_periods=3).max()
    d["high10"] = h.rolling(10, min_periods=5).max()
    d["high20"] = h.rolling(20, min_periods=8).max()
    d["high50"] = h.rolling(50, min_periods=20).max()
    d["high252"] = h.rolling(252, min_periods=60).max()

    d["low10"] = l.rolling(10, min_periods=5).min()
    d["low20"] = l.rolling(20, min_periods=8).min()
    d["low50"] = l.rolling(50, min_periods=20).min()

    d["vol20"] = v.rolling(20, min_periods=8).mean()
    d["vol50"] = v.rolling(50, min_periods=20).mean()

    prev_c = c.shift(1)
    tr = pd.concat(
        [
            (h - l).abs(),
            (h - prev_c).abs(),
            (l - prev_c).abs(),
        ],
        axis=1,
    ).max(axis=1)

    d["atr14"] = tr.rolling(14, min_periods=7).mean()
    d["atr_pct"] = d["atr14"] / c * 100.0

    d["ret1"] = c.pct_change(1) * 100.0
    d["ret3"] = c.pct_change(3) * 100.0
    d["ret5"] = c.pct_change(5) * 100.0
    d["ret10"] = c.pct_change(10) * 100.0
    d["ret20"] = c.pct_change(20) * 100.0
    d["ret60"] = c.pct_change(60) * 100.0
    d["ret120"] = c.pct_change(120) * 100.0

    d["vol3"] = v.rolling(3, min_periods=2).mean()
    d["rvol20"] = v / (d["vol20"] + 1e-9)
    d["rvol3_20"] = d["vol3"] / (d["vol20"] + 1e-9)

    d["day_range"] = (h - l).replace(0, np.nan)
    d["range_pos"] = (c - l) / d["day_range"]
    d["close_pos20"] = (c - d["low20"]) / ((d["high20"] - d["low20"]).replace(0, np.nan))
    d["close_pos50"] = (c - d["low50"]) / ((d["high50"] - d["low50"]).replace(0, np.nan))

    d["bb_width20"] = (c.rolling(20, min_periods=8).std() * 4.0) / c * 100.0
    d["bb_width_pct63"] = d["bb_width20"].rolling(63, min_periods=20).rank(pct=True)
    d["atr_pct_rank63"] = d["atr_pct"].rolling(63, min_periods=20).rank(pct=True)

    d["extension_sma20"] = (c / d["sma20"] - 1.0) * 100.0
    d["extension_sma50"] = (c / d["sma50"] - 1.0) * 100.0

    d["dollar_volume"] = c * v
    d["avg_dollar_volume20"] = d["dollar_volume"].rolling(20, min_periods=8).mean()
    d["avg_dollar_volume50"] = d["dollar_volume"].rolling(50, min_periods=20).mean()

    return d


def get_last_row(df: pd.DataFrame) -> pd.Series | None:
    if df is None or df.empty:
        return None
    return df.iloc[-1]


def market_regime_from_pulse(market_pulse_raw: list[dict[str, Any]]) -> tuple[str, float, dict[str, Any]]:
    """
    Market regime uses TOPIX/NIKKEI/GROWTH ETF data.
    FutureTech uses SPY/QQQ above SMA20/SMA50.
    Neon Tokyo version:
      - Risk-on: TOPIX and NIKKEI above SMA20, or TOPIX 20D return strong
      - Neutral: broad market not broken
      - Risk-off: TOPIX below SMA50 and weak 20D return
    """
    pulse_map: dict[str, dict[str, Any]] = {}

    for item in market_pulse_raw:
        label = item.get("pulse_label") or item.get("symbol")
        if label:
            pulse_map[str(label).upper()] = item

    topix = pulse_map.get("TOPIX")
    nikkei = pulse_map.get("NIKKEI")
    growth = pulse_map.get("GROWTH")

    def enriched(item: dict[str, Any] | None) -> tuple[pd.Series | None, dict[str, Any]]:
        if not item:
            return None, {}
        df = add_indicators(bars_to_df(item))
        row = get_last_row(df)
        if row is None:
            return None, {}
        close = to_float(row.get("Close"))
        sma20 = to_float(row.get("sma20"))
        sma50 = to_float(row.get("sma50"))
        return row, {
            "symbol": item.get("symbol"),
            "label": item.get("pulse_label"),
            "close": safe_round(close, 4),
            "ret1": safe_round(row.get("ret1"), 4),
            "ret5": safe_round(row.get("ret5"), 4),
            "ret20": safe_round(row.get("ret20"), 4),
            "ret60": safe_round(row.get("ret60"), 4),
            "above_sma20": bool(close is not None and sma20 is not None and close >= sma20),
            "above_sma50": bool(close is not None and sma50 is not None and close >= sma50),
        }

    topix_row, topix_state = enriched(topix)
    nikkei_row, nikkei_state = enriched(nikkei)
    growth_row, growth_state = enriched(growth)

    topix_ret20 = to_float(topix_state.get("ret20"))
    topix_ret5 = to_float(topix_state.get("ret5"))

    topix_above20 = bool(topix_state.get("above_sma20"))
    nikkei_above20 = bool(nikkei_state.get("above_sma20"))
    topix_above50 = bool(topix_state.get("above_sma50"))
    nikkei_above50 = bool(nikkei_state.get("above_sma50"))

    if topix_above20 and nikkei_above20:
        regime = "Risk-on"
        score = 1.0
    elif topix_above50 and nikkei_above50:
        regime = "Neutral"
        score = 0.65
    elif topix_ret20 is not None and topix_ret20 <= -5:
        regime = "Risk-off"
        score = 0.18
    elif topix_ret5 is not None and topix_ret5 <= -2:
        regime = "Weakening"
        score = 0.38
    else:
        regime = "Neutral"
        score = 0.55

    state = {
        "regime": regime,
        "regime_score": score,
        "topix": topix_state,
        "nikkei": nikkei_state,
        "growth": growth_state,
    }

    return regime, score, state


def build_market_pulse_item(item: dict[str, Any]) -> dict[str, Any]:
    df = add_indicators(bars_to_df(item))
    last = get_last_row(df)

    metrics = item.get("metrics") or {}
    label = item.get("pulse_label") or item.get("symbol")

    if last is None:
        ret_1d = to_float(metrics.get("return_1d_pct"))
        ret_5d = to_float(metrics.get("return_5d_pct"))
        ret_20d = to_float(metrics.get("return_20d_pct"))
        ret_60d = to_float(metrics.get("return_60d_pct"))
        close = to_float(metrics.get("latest_close"))
        above_sma20 = None
        above_sma50 = None
    else:
        ret_1d = to_float(last.get("ret1"))
        ret_5d = to_float(last.get("ret5"))
        ret_20d = to_float(last.get("ret20"))
        ret_60d = to_float(last.get("ret60"))
        close = to_float(last.get("Close"))
        sma20 = to_float(last.get("sma20"))
        sma50 = to_float(last.get("sma50"))
        above_sma20 = bool(close is not None and sma20 is not None and close >= sma20)
        above_sma50 = bool(close is not None and sma50 is not None and close >= sma50)

    if above_sma20 and ret_20d is not None and ret_20d >= 3:
        regime = "Risk-On"
    elif above_sma50:
        regime = "Neutral"
    elif ret_20d is not None and ret_20d <= -5:
        regime = "Risk-Off"
    elif ret_5d is not None and ret_5d <= -2:
        regime = "Weakening"
    else:
        regime = "Neutral"

    pulse_score = (
        scale(ret_5d, -5, 5) * 35
        + scale(ret_20d, -10, 10) * 45
        + scale(ret_60d, -20, 20) * 20
    )

    return {
        "symbol": item.get("symbol"),
        "label": label,
        "name": item.get("name"),
        "source": item.get("source"),
        "latest_date": metrics.get("latest_date"),
        "latest_close": safe_round(close, 4),
        "return_1d_pct": safe_round(ret_1d, 4),
        "return_5d_pct": safe_round(ret_5d, 4),
        "return_20d_pct": safe_round(ret_20d, 4),
        "return_60d_pct": safe_round(ret_60d, 4),
        "above_sma20": above_sma20,
        "above_sma50": above_sma50,
        "regime": regime,
        "pulse_score_0_100": round(pulse_score, 2),
    }


def score_volume_liquidity_shock(last: pd.Series, prev: pd.Series, item: dict[str, Any]) -> tuple[float, list[str]]:
    flags: list[str] = []

    close = to_float(last.get("Close")) or 0.0
    prev_close = to_float(prev.get("Close")) or close
    volume = to_float(last.get("Volume")) or 0.0
    rvol20 = max(0.0, to_float(last.get("rvol20")) or 0.0)
    range_pos = clamp(last.get("range_pos"), 0, 1)
    avg_value20 = to_float(last.get("avg_dollar_volume20"))
    dollar_vol = to_float(last.get("dollar_volume"))

    price_up = 1.0 if close > prev_close else 0.0

    # FutureTech-style saturating volume curve.
    rvol_score = 1.0 - math.exp(-rvol20 / 2.2)

    # Japan-specific liquidity confirmation.
    # ¥100M = minimally tradable, ¥1B = strong.
    avg_liq_score = scale(avg_value20, 100_000_000, 1_000_000_000)

    # Today's actual traded value matters because tiny stocks can show fake RVOL.
    today_liq_score = scale(dollar_vol, 100_000_000, 1_500_000_000)

    score = clamp(
        0.46 * rvol_score
        + 0.20 * range_pos
        + 0.14 * price_up
        + 0.12 * avg_liq_score
        + 0.08 * today_liq_score
    )

    if rvol20 >= 2.5:
        flags.append("major_volume_shock")
    elif rvol20 >= 1.3:
        flags.append("volume_expansion")

    if dollar_vol is not None and dollar_vol >= 1_000_000_000:
        flags.append("large_traded_value")

    if avg_value20 is not None and avg_value20 >= 300_000_000:
        flags.append("liquid_enough")

    return score, flags


def evaluate_volume_flow(last: pd.Series, prev: pd.Series, item: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    Classify abnormal volume into three mutually exclusive buckets:
      - abnormal_accumulation: volume expansion that can be interpreted positively
      - abnormal_distribution: volume expansion with weak price action / sell pressure
      - volume_noise: volume expanded, but direction is too ambiguous to reward

    This deliberately does not try to predict hard news. It only captures the
    tradable footprint that may appear before or immediately after a catalyst.
    """
    flags: list[str] = []

    close = to_float(last.get("Close"))
    open_ = to_float(last.get("Open"))
    prev_close = to_float(prev.get("Close"))
    rvol20 = max(0.0, to_float(last.get("rvol20")) or 0.0)
    rvol3_20 = max(0.0, to_float(last.get("rvol3_20")) or 0.0)
    range_pos = clamp(last.get("range_pos"), 0, 1)
    close_pos20 = clamp(last.get("close_pos20"), 0, 1)
    close_pos50 = clamp(last.get("close_pos50"), 0, 1)
    ret1 = to_float(last.get("ret1")) or 0.0
    ret3 = to_float(last.get("ret3")) or 0.0
    ret5 = to_float(last.get("ret5")) or 0.0
    ret10 = to_float(last.get("ret10")) or 0.0
    ret20 = to_float(last.get("ret20")) or 0.0
    avg_value20 = to_float(last.get("avg_dollar_volume20"))
    dollar_vol = to_float(last.get("dollar_volume"))
    sma20 = to_float(last.get("sma20"))
    prev_high20 = to_float(prev.get("high20"))

    above_sma20 = bool(close is not None and sma20 is not None and close >= sma20)
    green_or_flat = bool(close is not None and prev_close is not None and close >= prev_close * 0.985)
    high_zone = close_pos20 >= 0.55 or close_pos50 >= 0.55 or above_sma20
    not_collapsing = ret1 >= -3.5 and ret3 >= -8.0 and ret5 >= -12.0
    not_overheated = ret5 <= 28.0 and ret10 <= 45.0 and ret20 <= 70.0
    sufficient_today_value = dollar_vol is not None and dollar_vol >= 100_000_000
    sufficient_avg_value = avg_value20 is not None and avg_value20 >= 70_000_000
    high_today_value = dollar_vol is not None and dollar_vol >= 1_000_000_000
    high_avg_value = avg_value20 is not None and avg_value20 >= 300_000_000
    persistent_volume = rvol3_20 >= 1.8
    single_day_spike = rvol20 >= 2.5
    major_volume = rvol20 >= 4.0 or rvol3_20 >= 3.0
    volume_event = single_day_spike or persistent_volume

    weak_intraday_close = range_pos <= 0.35
    red_on_volume = bool(close is not None and open_ is not None and close < open_ and rvol20 >= 1.8)
    downside_break = ret1 <= -6.0 or ret3 <= -10.0 or ret5 <= -15.0
    low_zone_break = close_pos20 <= 0.35 and ret1 < 0

    abnormal_distribution = bool(
        volume_event
        and sufficient_today_value
        and (
            downside_break
            or (weak_intraday_close and red_on_volume)
            or low_zone_break
        )
    )

    quiet_price_with_volume = abs(ret3) <= 10.0 and -5.0 <= ret5 <= 18.0
    controlled_up_move = -3.5 <= ret1 <= 12.0 and -8.0 <= ret3 <= 18.0
    near_breakout = bool(prev_high20 is not None and close is not None and close >= prev_high20 * 0.92)

    # A second, stricter path for post-catalyst digestion. Some JP small-cap
    # theme names stay liquid after the first news spike, so RVOL vs 20D can
    # look mediocre even while the tape is still actively absorbing supply.
    # This is Watch-oriented only; it should not create Trade by itself.
    post_catalyst_digestion = bool(
        high_today_value
        and high_avg_value
        and rvol3_20 >= 0.60
        and not abnormal_distribution
        and ret1 >= -2.5
        and ret3 >= -6.0
        and -25.0 <= ret5 <= 10.0
        and ret10 >= -45.0
        and ret20 >= -45.0
        and range_pos >= 0.55
        and close_pos50 >= 0.38
    )

    abnormal_accumulation = bool(
        (
            volume_event
            and not abnormal_distribution
            and sufficient_today_value
            and sufficient_avg_value
            and not_collapsing
            and not_overheated
            and (green_or_flat or range_pos >= 0.45)
            and (high_zone or near_breakout)
            and (quiet_price_with_volume or controlled_up_move or major_volume)
        )
        or post_catalyst_digestion
    )

    volume_noise = bool(volume_event and not abnormal_accumulation and not abnormal_distribution)

    boost = 0.0
    distribution_penalty = 0.0
    noise_penalty = 0.0
    signal = "none"
    confidence = "none"

    if abnormal_accumulation:
        signal = "abnormal_accumulation"
        confidence = "high" if major_volume and close_pos20 >= 0.60 and range_pos >= 0.45 else "medium"
        # Discovery overlay: enough to lift strong accumulation into Watch,
        # but not enough to manufacture Trade without breakout/setup quality.
        boost = clamp(
            0.020
            + 0.020 * scale(rvol20, 2.0, 6.0)
            + 0.015 * scale(rvol3_20, 1.4, 4.0)
            + 0.012 * close_pos20
            + 0.008 * range_pos,
            0.0,
            ACCUMULATION_BOOST_CAP,
        )
        flags.append("abnormal_accumulation")
        if post_catalyst_digestion:
            flags.append("post_catalyst_digestion")
        if confidence == "high":
            flags.append("abnormal_accumulation_high_confidence")
        flags.append("discovery_watch_candidate")
    elif abnormal_distribution:
        signal = "abnormal_distribution"
        confidence = "high" if downside_break and weak_intraday_close else "medium"
        distribution_penalty = clamp(
            0.055
            + 0.045 * scale(rvol20, 2.0, 6.0)
            + 0.040 * scale(abs(min(ret1, 0.0)), 3.0, 12.0)
            + 0.030 * (1.0 - range_pos),
            0.0,
            DISTRIBUTION_PENALTY_CAP,
        )
        flags.append("abnormal_distribution")
        if confidence == "high":
            flags.append("abnormal_distribution_high_confidence")
    elif volume_noise:
        signal = "volume_noise"
        confidence = "low"
        noise_penalty = clamp(
            0.030
            + 0.020 * scale(rvol20, 1.6, 5.0)
            + 0.020 * (1.0 - range_pos),
            0.0,
            VOLUME_NOISE_PENALTY_CAP,
        )
        flags.append("volume_noise")

    flow = {
        "signal": signal,
        "confidence": confidence,
        "boost_0_1": safe_round(boost, 6),
        "distribution_penalty_0_1": safe_round(distribution_penalty, 6),
        "noise_penalty_0_1": safe_round(noise_penalty, 6),
        "rvol20": safe_round(rvol20, 4),
        "rvol3_20": safe_round(rvol3_20, 4),
        "ret1_pct": safe_round(ret1, 4),
        "ret3_pct": safe_round(ret3, 4),
        "ret5_pct": safe_round(ret5, 4),
        "ret10_pct": safe_round(ret10, 4),
        "ret20_pct": safe_round(ret20, 4),
        "range_pos_0_1": safe_round(range_pos, 4),
        "close_pos20_0_1": safe_round(close_pos20, 4),
        "close_pos50_0_1": safe_round(close_pos50, 4),
        "sufficient_today_value": sufficient_today_value,
        "sufficient_avg_value": sufficient_avg_value,
        "high_today_value": high_today_value,
        "high_avg_value": high_avg_value,
        "post_catalyst_digestion": post_catalyst_digestion,
        "above_sma20": above_sma20,
    }

    return flow, flags


def score_compression_release(last: pd.Series, prev: pd.Series) -> tuple[float, list[str]]:
    flags: list[str] = []

    bb_rank_raw = to_float(last.get("bb_width_pct63"))
    atr_rank_raw = to_float(last.get("atr_pct_rank63"))

    # Lower rank means tighter compression.
    bb_compression = 1.0 - clamp(bb_rank_raw if bb_rank_raw is not None else 0.50)
    atr_compression = 1.0 - clamp(atr_rank_raw if atr_rank_raw is not None else 0.50)

    close = to_float(last.get("Close")) or 0.0
    prev_high20 = to_float(prev.get("high20"))
    prev_high50 = to_float(prev.get("high50"))

    high20_break = 1.0 if prev_high20 is not None and close >= prev_high20 else 0.0
    high50_break = 1.0 if prev_high50 is not None and close >= prev_high50 else 0.0

    rvol20 = max(0.0, to_float(last.get("rvol20")) or 0.0)
    range_pos = clamp(last.get("range_pos"), 0, 1)
    close_pos20 = clamp(last.get("close_pos20"), 0, 1)

    release_confirmation = clamp(
        0.42 * scale(rvol20, 0.9, 2.3)
        + 0.34 * range_pos
        + 0.24 * close_pos20
    )

    score = clamp(
        0.32 * bb_compression
        + 0.22 * atr_compression
        + 0.18 * high20_break
        + 0.10 * high50_break
        + 0.18 * release_confirmation
    )

    if bb_compression >= 0.60 or atr_compression >= 0.60:
        flags.append("compressed_setup")

    if release_confirmation >= 0.65:
        flags.append("compression_release")

    if high20_break:
        flags.append("breaks_20d_high")

    return score, flags


def score_breakout_setup_quality(last: pd.Series, prev: pd.Series) -> tuple[float, list[str]]:
    flags: list[str] = []

    close = to_float(last.get("Close")) or 0.0
    sma20 = to_float(last.get("sma20"))
    sma50 = to_float(last.get("sma50"))
    sma150 = to_float(last.get("sma150"))
    prev_high20 = to_float(prev.get("high20"))
    prev_high50 = to_float(prev.get("high50"))

    above20 = 1.0 if sma20 is not None and close >= sma20 else 0.0
    above50 = 1.0 if sma50 is not None and close >= sma50 else 0.0
    above150 = 1.0 if sma150 is not None and close >= sma150 else 0.0

    high20_break = 1.0 if prev_high20 is not None and close >= prev_high20 else 0.0
    high50_break = 1.0 if prev_high50 is not None and close >= prev_high50 else 0.0

    close_pos20 = clamp(last.get("close_pos20"), 0, 1)
    close_pos50 = clamp(last.get("close_pos50"), 0, 1)

    ret5 = to_float(last.get("ret5")) or 0.0

    score = clamp(
        0.16 * above20
        + 0.16 * above50
        + 0.08 * above150
        + 0.22 * high20_break
        + 0.14 * high50_break
        + 0.16 * close_pos20
        + 0.06 * close_pos50
        + 0.02 * scale(ret5, -3, 10)
    )

    if above20 and above50:
        flags.append("above_key_mas")

    if high20_break:
        flags.append("breakout_20d")

    if high50_break:
        flags.append("breakout_50d")

    if close_pos20 >= 0.80:
        flags.append("upper_20d_range")

    return score, flags


def score_relative_strength(last: pd.Series, topix_last: pd.Series | None) -> tuple[float, list[str], dict[str, float | None]]:
    flags: list[str] = []

    ret5 = to_float(last.get("ret5")) or 0.0
    ret20 = to_float(last.get("ret20")) or 0.0
    ret60 = to_float(last.get("ret60")) or 0.0
    ret120 = to_float(last.get("ret120")) or 0.0

    if topix_last is not None:
        topix_ret5 = to_float(topix_last.get("ret5")) or 0.0
        topix_ret20 = to_float(topix_last.get("ret20")) or 0.0
        topix_ret60 = to_float(topix_last.get("ret60")) or 0.0
        topix_ret120 = to_float(topix_last.get("ret120")) or 0.0
    else:
        topix_ret5 = 0.0
        topix_ret20 = 0.0
        topix_ret60 = 0.0
        topix_ret120 = 0.0

    rs5 = ret5 - topix_ret5
    rs20 = ret20 - topix_ret20
    rs60 = ret60 - topix_ret60
    rs120 = ret120 - topix_ret120

    # More daily-oriented than weekly: 5D/20D matter more.
    score = clamp(
        0.30 * scale(rs5, -4, 12)
        + 0.42 * scale(rs20, -6, 24)
        + 0.20 * scale(rs60, -8, 45)
        + 0.08 * scale(rs120, -10, 80)
    )

    if rs20 >= 8:
        flags.append("rs_20d_positive")
    if rs60 >= 20:
        flags.append("rs_60d_leader")

    return score, flags, {
        "rs_vs_topix_5d_pct": safe_round(rs5, 4),
        "rs_vs_topix_20d_pct": safe_round(rs20, 4),
        "rs_vs_topix_60d_pct": safe_round(rs60, 4),
        "rs_vs_topix_120d_pct": safe_round(rs120, 4),
    }


def score_entry_timing(last: pd.Series, prev: pd.Series) -> tuple[float, list[str]]:
    flags: list[str] = []

    close = to_float(last.get("Close")) or 0.0
    open_ = to_float(last.get("Open")) or close

    ret1 = to_float(last.get("ret1")) or 0.0
    ret5 = to_float(last.get("ret5")) or 0.0
    ret20 = to_float(last.get("ret20")) or 0.0
    atr_pct = to_float(last.get("atr_pct")) or 0.0
    ext20 = to_float(last.get("extension_sma20")) or 0.0
    ext50 = to_float(last.get("extension_sma50")) or 0.0
    range_pos = clamp(last.get("range_pos"), 0, 1)
    close_pos20 = clamp(last.get("close_pos20"), 0, 1)

    not_extended = 1.0 - clamp(
        max(ext20 - 8.0, 0.0) / 18.0
        + max(ext50 - 20.0, 0.0) / 32.0
        + max(ret1 - 10.0, 0.0) / 16.0
        + max(ret5 - 22.0, 0.0) / 30.0
        + max(ret20 - 55.0, 0.0) / 50.0
    )

    # Stop distance proxy. Lower ATR is easier to control, but too low can mean no movement.
    stop_distance = min(10.0, max(3.0, atr_pct * 1.6))
    rr_quality = clamp((12.0 - stop_distance) / 10.0)

    candle_ok = 1.0 if close >= open_ else 0.0

    score = clamp(
        0.38 * not_extended
        + 0.24 * range_pos
        + 0.16 * close_pos20
        + 0.12 * rr_quality
        + 0.10 * candle_ok
    )

    if ret1 >= 10:
        flags.append("strong_1d_move")
    if ret5 >= 22:
        flags.append("hot_5d_move")
    if ret20 >= 55:
        flags.append("hot_20d_move")
    if not_extended <= 0.45:
        flags.append("extended_risk")

    return score, flags


def evaluate_archetype_adjustment(
    components: dict[str, float],
    last: pd.Series,
    flags: list[str],
) -> tuple[float, float, list[str], dict[str, Any]]:
    """
    Post-score archetype overlay derived from the first backtest diagnostics.

    Positive:
      - Relative Strength
      - Compression + Breakout
      - Volume + Compression

    Negative:
      - Volume + Breakout without compression. In JP daily data this behaved
        like short-term exhaustion / sell-the-news more often than a clean
        continuation setup.
    """
    out_flags: list[str] = []

    volume = float(components.get("volume_liquidity_shock") or 0.0)
    compression = float(components.get("compression_release") or 0.0)
    setup = float(components.get("breakout_setup_quality") or 0.0)
    rs = float(components.get("relative_strength") or 0.0)
    entry = float(components.get("entry_timing") or 0.0)

    ret1 = to_float(last.get("ret1")) or 0.0
    ret5 = to_float(last.get("ret5")) or 0.0
    range_pos = clamp(last.get("range_pos"), 0, 1)
    close_pos20 = clamp(last.get("close_pos20"), 0, 1)

    has_bad_flow = "abnormal_distribution" in flags or "volume_noise" in flags
    not_extended = ret5 < 35.0

    favorable_boost = 0.0

    favored_relative_strength = bool(
        rs >= 0.70
        and entry >= 0.48
        and close_pos20 >= 0.50
        and not has_bad_flow
        and not_extended
    )
    if favored_relative_strength:
        favorable_boost += 0.018 + 0.012 * scale(rs, 0.70, 0.95)
        out_flags.append("favored_relative_strength")

    favored_compression_breakout = bool(
        compression >= 0.58
        and setup >= 0.58
        and range_pos >= 0.55
        and not has_bad_flow
        and not_extended
    )
    if favored_compression_breakout:
        favorable_boost += 0.020 + 0.012 * min(scale(compression, 0.58, 0.90), scale(setup, 0.58, 0.90))
        out_flags.append("favored_compression_breakout")

    favored_volume_compression = bool(
        volume >= 0.52
        and compression >= 0.55
        and range_pos >= 0.45
        and ret1 >= -3.0
        and not has_bad_flow
        and not_extended
    )
    if favored_volume_compression:
        favorable_boost += 0.016 + 0.010 * min(scale(volume, 0.52, 0.90), scale(compression, 0.55, 0.90))
        out_flags.append("favored_volume_compression")

    volume_breakout_risk = bool(
        volume >= 0.60
        and setup >= 0.62
        and compression < 0.52
    )
    volume_breakout_penalty = 0.0
    if volume_breakout_risk:
        volume_breakout_penalty = clamp(
            0.035
            + 0.020 * scale(volume, 0.60, 0.95)
            + 0.020 * scale(setup, 0.62, 0.95)
            + 0.015 * scale(ret5, 8.0, 35.0)
            + 0.015 * (1.0 - range_pos),
            0.0,
            VOLUME_BREAKOUT_RISK_PENALTY_CAP,
        )
        out_flags.append("volume_breakout_risk")
        out_flags.append("trade_block_volume_breakout")

    favorable_boost = clamp(favorable_boost, 0.0, FAVORABLE_ARCHETYPE_BOOST_CAP)

    details = {
        "favored_relative_strength": favored_relative_strength,
        "favored_compression_breakout": favored_compression_breakout,
        "favored_volume_compression": favored_volume_compression,
        "volume_breakout_risk": volume_breakout_risk,
        "favorable_archetype_boost_0_1": safe_round(favorable_boost, 6),
        "volume_breakout_risk_penalty_0_1": safe_round(volume_breakout_penalty, 6),
    }
    return favorable_boost, volume_breakout_penalty, out_flags, details


def compute_penalty(last: pd.Series, item: dict[str, Any], bucket: str) -> tuple[float, list[str], dict[str, float | None]]:
    flags: list[str] = []

    close = to_float(last.get("Close"))
    open_ = to_float(last.get("Open"))
    rvol20 = to_float(last.get("rvol20")) or 0.0
    range_pos = clamp(last.get("range_pos"), 0, 1)
    ret1 = to_float(last.get("ret1")) or 0.0
    ret5 = to_float(last.get("ret5")) or 0.0
    ret20 = to_float(last.get("ret20")) or 0.0
    ret60 = to_float(last.get("ret60")) or 0.0
    ext20 = to_float(last.get("extension_sma20")) or 0.0
    ext50 = to_float(last.get("extension_sma50")) or 0.0
    avg_value20 = to_float(last.get("avg_dollar_volume20"))
    dollar_vol = to_float(last.get("dollar_volume"))

    penalty = 0.0

    # Liquidity: Japan-specific and much stricter than US.
    liquidity_penalty = 0.0
    if avg_value20 is None:
        liquidity_penalty += 0.10
        flags.append("unknown_liquidity")
    elif avg_value20 < 100_000_000:
        liquidity_penalty += 0.22
        flags.append("very_low_liquidity")
    elif avg_value20 < 300_000_000:
        liquidity_penalty += 0.10
        flags.append("low_liquidity")

    if dollar_vol is not None and dollar_vol < 50_000_000:
        liquidity_penalty += 0.06
        flags.append("thin_today_value")

    low_price_penalty = 0.0
    if close is not None and close < 300:
        low_price_penalty = 0.12
        flags.append("low_price")

    extension_penalty = clamp(
        max(ret1 - 15.0, 0.0) / 35.0
        + max(ret5 - 30.0, 0.0) / 45.0
        + max(ret20 - 65.0, 0.0) / 70.0
        + max(ext20 - 18.0, 0.0) / 35.0
        + max(ext50 - 35.0, 0.0) / 45.0
    )

    extension_penalty *= 0.55

    if extension_penalty >= 0.10:
        flags.append("extended_penalty")

    weak_close_penalty = 0.0
    if range_pos < 0.45 and rvol20 >= 1.3:
        weak_close_penalty += 0.10
        flags.append("weak_close_on_volume")
    if close is not None and open_ is not None and close < open_ and rvol20 >= 1.4:
        weak_close_penalty += 0.08
        flags.append("red_close_on_volume")

    no_confirmation_penalty = 0.0
    if ret1 < 0 and rvol20 < 1.0:
        no_confirmation_penalty += 0.10
        flags.append("no_daily_confirmation")
    if ret5 < -5:
        no_confirmation_penalty += 0.06
        flags.append("weak_5d_momentum")

    watch_bucket_penalty = 0.0
    if bucket.lower() == "watch":
        watch_bucket_penalty += 0.05
        flags.append("watch_bucket")

    partial_data_penalty = 0.0
    if bool(item.get("is_partial")) or (to_int(item.get("bars_count")) or 0) < 60:
        partial_data_penalty += 0.08
        flags.append("partial_data")

    penalty = clamp(
        liquidity_penalty
        + low_price_penalty
        + extension_penalty
        + weak_close_penalty
        + no_confirmation_penalty
        + watch_bucket_penalty
        + partial_data_penalty,
        0.0,
        0.38,
    )

    details = {
        "liquidity_penalty": safe_round(liquidity_penalty, 6),
        "low_price_penalty": safe_round(low_price_penalty, 6),
        "extension_penalty": safe_round(extension_penalty, 6),
        "weak_close_penalty": safe_round(weak_close_penalty, 6),
        "no_confirmation_penalty": safe_round(no_confirmation_penalty, 6),
        "watch_bucket_penalty": safe_round(watch_bucket_penalty, 6),
        "partial_data_penalty": safe_round(partial_data_penalty, 6),
    }

    return penalty, flags, details


def apply_score_caps(score01: float, last: pd.Series, item: dict[str, Any]) -> tuple[float, list[str]]:
    """
    FutureTech evidence showed high score alone is not enough.
    For JP daily, weak volume or no daily confirmation should cap score.
    """
    flags: list[str] = []

    rvol20 = to_float(last.get("rvol20")) or 0.0
    ret1 = to_float(last.get("ret1")) or 0.0
    ret5 = to_float(last.get("ret5")) or 0.0
    ret20 = to_float(last.get("ret20")) or 0.0
    range_pos = clamp(last.get("range_pos"), 0, 1)
    close_pos20 = clamp(last.get("close_pos20"), 0, 1)
    avg_value20 = to_float(last.get("avg_dollar_volume20"))

    cap = 1.0

    has_price_confirmation = ret1 >= 0.0 and range_pos >= 0.65
    has_breakout_confirmation = range_pos >= 0.80 and close_pos20 >= 0.75

    if rvol20 < 0.60 and not has_breakout_confirmation:
        cap = min(cap, 0.55)
        flags.append("score_cap_weak_volume")
    elif rvol20 < 0.80 and not has_price_confirmation:
        cap = min(cap, 0.62)
        flags.append("score_cap_low_volume_confirmation")

    if ret1 < 0 and rvol20 < 1.0:
        cap = min(cap, 0.58)
        flags.append("score_cap_no_daily_confirmation")

    if ret5 >= 35:
        cap = min(cap, 0.72)
        flags.append("score_cap_hot_5d")
    if ret20 >= 75:
        cap = min(cap, 0.68)
        flags.append("score_cap_hot_20d")

    if avg_value20 is not None and avg_value20 < 100_000_000:
        cap = min(cap, 0.62)
        flags.append("score_cap_very_low_liquidity")

    return min(score01, cap), flags


def classify_and_triage(
    score01: float,
    components: dict[str, float],
    last: pd.Series,
    item: dict[str, Any],
    penalty: float,
    regime: str,
    flags: list[str],
) -> tuple[str, str, str, str]:
    score_pts = int(round(score01 * SCORE_SCALE))

    volume = components["volume_liquidity_shock"]
    compression = components["compression_release"]
    setup = components["breakout_setup_quality"]
    entry = components["entry_timing"]

    rvol20 = to_float(last.get("rvol20")) or 0.0
    ret1 = to_float(last.get("ret1")) or 0.0
    ret5 = to_float(last.get("ret5")) or 0.0
    ret20 = to_float(last.get("ret20")) or 0.0
    avg_value20 = to_float(last.get("avg_dollar_volume20"))
    range_pos = clamp(last.get("range_pos"), 0, 1)
    close_pos20 = clamp(last.get("close_pos20"), 0, 1)

    archetype_parts: list[str] = []
    if volume >= 0.60:
        archetype_parts.append("Volume")
    if compression >= 0.55:
        archetype_parts.append("Compression")
    if setup >= 0.62:
        archetype_parts.append("Breakout")
    if not archetype_parts:
        if components["relative_strength"] >= 0.68:
            archetype_parts.append("Relative Strength")
        else:
            archetype_parts.append("Mixed")
    archetype = " + ".join(archetype_parts[:3])

    very_low_liquidity = avg_value20 is not None and avg_value20 < 100_000_000
    low_liquidity = avg_value20 is not None and avg_value20 < 300_000_000
    extended = ret5 >= 35 or ret20 >= 75
    no_confirmation = ret1 < 0 and rvol20 < 1.0
    weak_close = "weak_close_on_volume" in flags or "red_close_on_volume" in flags
    abnormal_accumulation = "abnormal_accumulation" in flags
    abnormal_distribution = "abnormal_distribution" in flags
    volume_noise = "volume_noise" in flags
    volume_breakout_risk = "volume_breakout_risk" in flags
    favored_relative_strength = "favored_relative_strength" in flags
    favored_compression_breakout = "favored_compression_breakout" in flags
    favored_volume_compression = "favored_volume_compression" in flags
    discovery_watch_candidate = "discovery_watch_candidate" in flags
    post_catalyst_digestion = "post_catalyst_digestion" in flags

    trade_ok = (
        score_pts >= 730
        and volume >= 0.56
        and (compression >= 0.55 or setup >= 0.64)
        and avg_value20 is not None
        and avg_value20 >= 300_000_000
        and range_pos >= 0.65
        and close_pos20 >= 0.70
        and not extended
        and not no_confirmation
        and not weak_close
        and not abnormal_distribution
        and not volume_noise
        and not volume_breakout_risk
        and penalty < 0.18
        and regime != "Risk-off"
    )

    watch_ok = (
        score_pts >= 620
        and (
            volume >= 0.45
            or (compression >= 0.55 and setup >= 0.55)
            or (setup >= 0.70 and components["relative_strength"] >= 0.65)
            or favored_relative_strength
            or favored_compression_breakout
            or favored_volume_compression
        )
        and not no_confirmation
        and not abnormal_distribution
        and not volume_noise
    )

    discovery_watch_ok = (
        abnormal_accumulation
        and discovery_watch_candidate
        and avg_value20 is not None
        and avg_value20 >= 70_000_000
        and not very_low_liquidity
        and not abnormal_distribution
        and not extended
        and (
            score_pts >= 500
            or (
                post_catalyst_digestion
                and score_pts >= 400
                and avg_value20 >= 300_000_000
                and range_pos >= 0.65
                and ret1 >= 0.0
            )
        )
    )

    if abnormal_distribution or volume_noise:
        trade_ok = False
        watch_ok = False

    if volume_breakout_risk:
        # Keep it visible if the score is still respectable, but do not let the
        # historically weak Volume + Breakout pattern become Trade by itself.
        trade_ok = False

    if trade_ok:
        triage = "Trade"
    elif watch_ok or discovery_watch_ok:
        triage = "Watch"
    else:
        triage = "Ignore"

    if very_low_liquidity and triage == "Trade":
        triage = "Watch"

    if no_confirmation and triage != "Ignore":
        triage = "Watch"

    if extended and triage == "Trade":
        triage = "Watch"

    if score_pts >= 800 and triage == "Trade":
        classification = "A+ Timing"
    elif score_pts >= 720 and triage in {"Trade", "Watch"}:
        classification = "A Setup"
    elif volume_breakout_risk and triage == "Watch":
        classification = "Exhaustion Watch"
    elif abnormal_accumulation and triage == "Watch":
        classification = "Discovery Watch"
    elif abnormal_distribution:
        classification = "Distribution Risk"
    elif volume_noise:
        classification = "Volume Noise"
    elif score_pts >= 620 and triage == "Watch":
        classification = "B Watch"
    elif very_low_liquidity:
        classification = "Low Liquidity"
    elif extended:
        classification = "Extended"
    else:
        classification = "No Signal"

    if very_low_liquidity:
        risk_level = "High"
    elif abnormal_distribution or volume_noise:
        risk_level = "High"
    elif volume_breakout_risk:
        risk_level = "Medium"
    elif low_liquidity or extended or penalty >= 0.18:
        risk_level = "Medium"
    elif triage == "Trade":
        risk_level = "Medium"
    else:
        risk_level = "Normal"

    return classification, triage, archetype, risk_level


def build_reason(components: dict[str, float], last: pd.Series, penalty: float, flags: list[str]) -> str:
    reason: list[str] = []

    rvol20 = to_float(last.get("rvol20")) or 0.0

    if components["volume_liquidity_shock"] >= 0.60:
        reason.append(f"RVOL {rvol20:.2f}x")
    if components["compression_release"] >= 0.55:
        reason.append("compression release")
    if components["breakout_setup_quality"] >= 0.62:
        reason.append("breakout setup")
    if components["relative_strength"] >= 0.68:
        reason.append("relative strength")
    if "abnormal_accumulation" in flags:
        reason.append("abnormal accumulation")
    if "abnormal_distribution" in flags:
        reason.append("abnormal distribution risk")
    if "volume_noise" in flags:
        reason.append("volume noise")
    if "volume_breakout_risk" in flags:
        reason.append("volume breakout risk")
    if "favored_relative_strength" in flags:
        reason.append("favored relative strength")
    if "favored_compression_breakout" in flags:
        reason.append("favored compression breakout")
    if "favored_volume_compression" in flags:
        reason.append("favored volume compression")
    if "no_daily_confirmation" in flags:
        reason.append("no daily confirmation")
    if "very_low_liquidity" in flags:
        reason.append("very low liquidity")
    if penalty >= 0.18:
        reason.append("penalty drag")

    if not reason:
        reason.append("mixed signal")

    return "; ".join(reason)


def score_equity_item(
    item: dict[str, Any],
    topix_last: pd.Series | None,
    regime: str,
    regime_score: float,
) -> dict[str, Any] | None:
    df = add_indicators(bars_to_df(item))
    if df.empty or len(df) < 20:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last

    bucket = str(item.get("bucket") or "")
    metrics = item.get("metrics") or {}

    volume_score, volume_flags = score_volume_liquidity_shock(last, prev, item)
    compression_score, compression_flags = score_compression_release(last, prev)
    setup_score, setup_flags = score_breakout_setup_quality(last, prev)
    rs_score, rs_flags, relative_metrics = score_relative_strength(last, topix_last)
    entry_score, entry_flags = score_entry_timing(last, prev)
    penalty, penalty_flags, penalty_details = compute_penalty(last, item, bucket)
    volume_flow, flow_flags = evaluate_volume_flow(last, prev, item)
    flow_boost = to_float(volume_flow.get("boost_0_1")) or 0.0
    flow_distribution_penalty = to_float(volume_flow.get("distribution_penalty_0_1")) or 0.0
    flow_noise_penalty = to_float(volume_flow.get("noise_penalty_0_1")) or 0.0

    raw_score01 = (
        WEIGHTS["volume_liquidity_shock"] * volume_score
        + WEIGHTS["compression_release"] * compression_score
        + WEIGHTS["breakout_setup_quality"] * setup_score
        + WEIGHTS["relative_strength"] * rs_score
        + WEIGHTS["entry_timing"] * entry_score
        + WEIGHTS["market_regime"] * regime_score
    )

    score01_before_penalty = clamp(raw_score01)

    base_components = {
        "volume_liquidity_shock": round(volume_score, 6),
        "compression_release": round(compression_score, 6),
        "breakout_setup_quality": round(setup_score, 6),
        "relative_strength": round(rs_score, 6),
        "entry_timing": round(entry_score, 6),
        "market_regime": round(regime_score, 6),
    }

    pre_adjustment_flags: list[str] = []
    for flag in (
        volume_flags
        + compression_flags
        + setup_flags
        + rs_flags
        + entry_flags
        + penalty_flags
        + flow_flags
    ):
        if flag not in pre_adjustment_flags:
            pre_adjustment_flags.append(flag)

    favorable_boost, volume_breakout_penalty, archetype_flags, archetype_adjustment = evaluate_archetype_adjustment(
        base_components,
        last,
        pre_adjustment_flags,
    )

    score01_after_penalty = clamp(score01_before_penalty - penalty)
    score01_after_flow = clamp(
        score01_after_penalty
        + flow_boost
        + favorable_boost
        - flow_distribution_penalty
        - flow_noise_penalty
        - volume_breakout_penalty
    )

    cap_score01, cap_flags = apply_score_caps(score01_after_flow, last, item)

    score01 = clamp(cap_score01)
    score_pts = int(round(score01 * SCORE_SCALE))

    components = {
        **base_components,
        "penalty": round(penalty, 6),
        "abnormal_flow_boost": round(flow_boost, 6),
        "favorable_archetype_boost": round(favorable_boost, 6),
        "abnormal_distribution_penalty": round(flow_distribution_penalty, 6),
        "volume_noise_penalty": round(flow_noise_penalty, 6),
        "volume_breakout_risk_penalty": round(volume_breakout_penalty, 6),
    }

    flags: list[str] = []
    for flag in (
        pre_adjustment_flags
        + archetype_flags
        + cap_flags
    ):
        if flag not in flags:
            flags.append(flag)

    classification, triage, archetype, risk = classify_and_triage(
        score01=score01,
        components=components,
        last=last,
        item=item,
        penalty=penalty,
        regime=regime,
        flags=flags,
    )

    reason = build_reason(components, last, penalty, flags)

    close = to_float(last.get("Close"))
    volume = to_int(last.get("Volume"))
    dollar_volume = to_float(last.get("dollar_volume"))
    avg_value20 = to_float(last.get("avg_dollar_volume20"))

    ret1 = to_float(last.get("ret1"))
    ret3 = to_float(last.get("ret3"))
    ret5 = to_float(last.get("ret5"))
    ret10 = to_float(last.get("ret10"))
    ret20 = to_float(last.get("ret20"))
    ret60 = to_float(last.get("ret60"))
    ret120 = to_float(last.get("ret120"))

    high252 = to_float(last.get("high252"))
    dist_52w = pct(close, high252) if close is not None and high252 else metrics.get("distance_from_52w_high_pct")

    return {
        "rank": None,
        "symbol": item.get("symbol"),
        "name": item.get("name"),
        "theme": item.get("theme"),
        "bucket": item.get("bucket"),
        "priority": item.get("priority"),
        "market": "JP",
        "currency": "JPY",
        "source": item.get("source"),
        "source_symbol": item.get("source_symbol"),
        "as_of": str(last.name.date()),
        "latest_date": str(last.name.date()),
        "price": safe_round(close, 4),
        "latest_close": safe_round(close, 4),
        "volume": volume,
        "latest_volume": volume,
        "latest_traded_value_jpy": safe_round(dollar_volume, 2),
        "avg_traded_value_20d_jpy": safe_round(avg_value20, 2),
        "return_1d_pct": safe_round(ret1, 4),
        "return_3d_pct": safe_round(ret3, 4),
        "return_5d_pct": safe_round(ret5, 4),
        "return_10d_pct": safe_round(ret10, 4),
        "return_20d_pct": safe_round(ret20, 4),
        "return_60d_pct": safe_round(ret60, 4),
        "return_120d_pct": safe_round(ret120, 4),
        "volume_ratio_20d": safe_round(last.get("rvol20"), 4),
        "volume_ratio_3d_vs_20d": safe_round(last.get("rvol3_20"), 4),
        "range_position_0_1": safe_round(last.get("range_pos"), 4),
        "range_position_20d_0_1": safe_round(last.get("close_pos20"), 4),
        "compression_20d_pct": safe_round(metrics.get("compression_20d_pct"), 4),
        "bb_width20_pct": safe_round(last.get("bb_width20"), 4),
        "bb_width_pct63": safe_round(last.get("bb_width_pct63"), 4),
        "atr_pct": safe_round(last.get("atr_pct"), 4),
        "atr_pct_rank63": safe_round(last.get("atr_pct_rank63"), 4),
        "extension_sma20_pct": safe_round(last.get("extension_sma20"), 4),
        "extension_sma50_pct": safe_round(last.get("extension_sma50"), 4),
        "distance_from_52w_high_pct": safe_round(dist_52w, 4),
        "score": round(score01 * 100.0, 2),
        "score_0_1": round(score01, 6),
        "score_pts": score_pts,
        "score_before_penalty_0_1": round(score01_before_penalty, 6),
        "score_after_penalty_0_1": round(score01_after_penalty, 6),
        "score_after_flow_0_1": round(score01_after_flow, 6),
        "classification": classification,
        "triage": triage,
        "archetype": archetype,
        "risk_level": risk,
        "regime": regime,
        "reason": reason,
        "components": {
            "volume_shock": round(volume_score * 24, 4),
            "compression": round(compression_score * 22, 4),
            "breakout_quality": round(setup_score * 20, 4),
            "relative_strength": round(rs_score * 16, 4),
            "entry_timing": round(entry_score * 15, 4),
            "market_regime": round(regime_score * 3, 4),
            "abnormal_flow_boost": round(flow_boost * 100, 4),
            "favorable_archetype_boost": round(favorable_boost * 100, 4),
            "abnormal_distribution_penalty": round(-flow_distribution_penalty * 100, 4),
            "volume_noise_penalty": round(-flow_noise_penalty * 100, 4),
            "volume_breakout_risk_penalty": round(-volume_breakout_penalty * 100, 4),
            "penalty": round(-penalty * 100, 4),
            "raw_score": round(score01_before_penalty * 100, 4),
        },
        "v2_components": components,
        "score_components": {
            "volume_anomaly": round(volume_score, 6),
            "compression_release": round(compression_score, 6),
            "trends_breakout": round(setup_score, 6),
            "relative_strength": round(rs_score, 6),
            "entry_timing": round(entry_score, 6),
            "market_regime": round(regime_score, 6),
        },
        "score_weights": {
            "volume_anomaly": WEIGHTS["volume_liquidity_shock"],
            "compression_release": WEIGHTS["compression_release"],
            "trends_breakout": WEIGHTS["breakout_setup_quality"],
            "relative_strength": WEIGHTS["relative_strength"],
            "entry_timing": WEIGHTS["entry_timing"],
            "market_regime": WEIGHTS["market_regime"],
        },
        "relative_metrics": relative_metrics,
        "volume_flow": volume_flow,
        "penalty_details": {
            **penalty_details,
            "abnormal_flow_boost": safe_round(flow_boost, 6),
            "favorable_archetype_boost": safe_round(favorable_boost, 6),
            "abnormal_distribution_penalty": safe_round(flow_distribution_penalty, 6),
            "volume_noise_penalty": safe_round(flow_noise_penalty, 6),
            "volume_breakout_risk_penalty": safe_round(volume_breakout_penalty, 6),
        },
        "archetype_adjustment": archetype_adjustment,
        "flags": flags,
        "liquidity_band": classify_liquidity_band(avg_value20, dollar_volume),
        "liquidity_score_0_1": safe_round(liquidity_score_from_band(classify_liquidity_band(avg_value20, dollar_volume)), 4),
        "liquidity_status": metrics.get("liquidity_status"),
        "liquidity_flags": metrics.get("liquidity_flags") or [],
        "is_partial": bool(item.get("is_partial")),
        "bars_count": item.get("bars_count"),
        "date_start": item.get("date_start"),
        "date_end": item.get("date_end"),
        "warnings": item.get("warnings") or [],
        "source_errors": item.get("source_errors") or [],
    }


def sort_ranked_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    triage_order = {"Trade": 0, "Watch": 1, "Ignore": 2}
    bucket_order = {"Core": 0, "Discovery": 1, "Watch": 2}
    risk_order = {"Normal": 0, "Medium": 1, "High": 2}

    def key(x: dict[str, Any]) -> tuple:
        triage = triage_order.get(str(x.get("triage") or ""), 9)
        bucket = bucket_order.get(str(x.get("bucket") or ""), 9)
        risk = risk_order.get(str(x.get("risk_level") or ""), 9)
        score = to_float(x.get("score_pts")) or 0.0
        avg_value = to_float(x.get("avg_traded_value_20d_jpy")) or 0.0
        return (triage, -score, bucket, risk, -avg_value, str(x.get("symbol") or ""))

    ranked = sorted(items, key=key)
    for i, item in enumerate(ranked, start=1):
        item["rank"] = i

    return ranked


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    def count_by(field: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in items:
            key = str(item.get(field) or "Unknown")
            out[key] = out.get(key, 0) + 1
        return out

    top = items[0] if items else {}

    return {
        "items_count": len(items),
        "top_symbol": top.get("symbol"),
        "top_name": top.get("name"),
        "top_score": top.get("score"),
        "top_score_pts": top.get("score_pts"),
        "top_classification": top.get("classification"),
        "top_triage": top.get("triage"),
        "top_archetype": top.get("archetype"),
        "trade": sum(1 for x in items if x.get("triage") == "Trade"),
        "watch": sum(1 for x in items if x.get("triage") == "Watch"),
        "ignore": sum(1 for x in items if x.get("triage") == "Ignore"),
        "by_triage": count_by("triage"),
        "by_archetype": count_by("archetype"),
        "by_classification": count_by("classification"),
        "by_bucket": count_by("bucket"),
        "by_risk": count_by("risk_level"),
    }


def find_topix_last(market_pulse_raw: list[dict[str, Any]]) -> pd.Series | None:
    for item in market_pulse_raw:
        if item.get("pulse_label") == "TOPIX" or item.get("symbol") == "1306.T":
            df = add_indicators(bars_to_df(item))
            return get_last_row(df)
    return None


def main() -> int:
    generated_at = iso_now()
    today = now_jst().date().isoformat()

    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"PRICES_JSON={safe_relative(PRICES_JSON)}")
    print(f"DAILY_OUT_DIR={safe_relative(DAILY_OUT_DIR)}")

    prices_payload = read_json(PRICES_JSON)

    if prices_payload.get("schema_version") != "prices-jp-v1":
        raise ValueError(f"Unexpected schema_version: {prices_payload.get('schema_version')}")

    market_pulse_raw = prices_payload.get("market_pulse") or []
    equities_raw = prices_payload.get("equities") or []

    if not isinstance(market_pulse_raw, list):
        raise TypeError("market_pulse must be a list")
    if not isinstance(equities_raw, list):
        raise TypeError("equities must be a list")

    regime, regime_score, regime_state = market_regime_from_pulse(market_pulse_raw)
    topix_last = find_topix_last(market_pulse_raw)

    market_pulse = [build_market_pulse_item(x) for x in market_pulse_raw]

    scored: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for item in equities_raw:
        if item.get("asset_type") != "equity":
            continue

        try:
            row = score_equity_item(
                item=item,
                topix_last=topix_last,
                regime=regime,
                regime_score=regime_score,
            )
            if row is None:
                failed.append(
                    {
                        "symbol": item.get("symbol"),
                        "name": item.get("name"),
                        "reason": "insufficient_bars_for_scoring",
                    }
                )
            else:
                scored.append(row)
        except Exception as exc:
            failed.append(
                {
                    "symbol": item.get("symbol"),
                    "name": item.get("name"),
                    "reason": f"exception:{type(exc).__name__}",
                    "message": str(exc),
                }
            )

    ranked_items = sort_ranked_items(scored)
    summary = summarize(ranked_items)

    payload = {
        "schema_version": "daily-jp-v2",
        "generated_at": generated_at,
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "source_prices": safe_relative(PRICES_JSON),
        "source_prices_generated_at": prices_payload.get("generated_at"),
        "methodology": {
            "name": "Neon Tokyo Daily Event Score v2",
            "derived_from": "FutureTech Daily Event Score principles",
            "objective": "Rank timing-sensitive JP equity candidates by volume/liquidity shock, compression release, breakout setup quality, relative strength, entry timing and market regime.",
            "news_included": False,
            "weights": {
                "volume_liquidity_shock": int(WEIGHTS["volume_liquidity_shock"] * 1000),
                "compression_release": int(WEIGHTS["compression_release"] * 1000),
                "breakout_setup_quality": int(WEIGHTS["breakout_setup_quality"] * 1000),
                "relative_strength": int(WEIGHTS["relative_strength"] * 1000),
                "entry_timing": int(WEIGHTS["entry_timing"] * 1000),
                "market_regime_alignment": int(WEIGHTS["market_regime"] * 1000),
                "penalties_max": -380,
            },
            "important_controls": [
                "Low volume without daily confirmation caps final score.",
                "Very low liquidity cannot become Trade.",
                "Daily main board focuses on top 20. Rank 21-50 remains reference/discovery only.",
                "Volume + Breakout without compression is treated as exhaustion risk and cannot become Trade by itself.",
                "Extended 5D/20D moves are capped and usually Watch, not Trade.",
                "Weak close on volume is penalized.",
                "Abnormal accumulation can lift a candidate into Discovery Watch, not automatically Trade.",
                "Abnormal distribution is penalized and blocks Trade/Watch promotion.",
                "Trade/Watch/Ignore is separated from rank.",
            ],
        },
        "regime": regime,
        "regime_score": round(regime_score, 6),
        "regime_state": regime_state,
        "market_pulse": market_pulse,
        "items": ranked_items[:DAILY_MAIN_RANK_LIMIT],
        "all_items": ranked_items,
        "summary": summary,
        "failed": failed,
    }

    DAILY_OUT_DIR.mkdir(parents=True, exist_ok=True)

    latest_path = DAILY_OUT_DIR / "latest.json"
    dated_path = DAILY_OUT_DIR / f"{today}.json"

    write_json(latest_path, payload)
    write_json(dated_path, payload)

    manifest = {
        "schema_version": "daily-jp-manifest-v2",
        "generated_at": generated_at,
        "latest": safe_relative(latest_path),
        "latest_date": today,
        "history": [
            {
                "date": today,
                "path": safe_relative(dated_path),
                "items_count": len(ranked_items),
                "trade": summary.get("trade"),
                "watch": summary.get("watch"),
                "ignore": summary.get("ignore"),
                "top_symbol": summary.get("top_symbol"),
                "top_score": summary.get("top_score"),
                "top_score_pts": summary.get("top_score_pts"),
                "top_triage": summary.get("top_triage"),
                "top_archetype": summary.get("top_archetype"),
                "top_classification": summary.get("top_classification"),
            }
        ],
    }

    manifest_path = DAILY_OUT_DIR / "manifest.json"
    write_json(manifest_path, manifest)

    print(f"Wrote {safe_relative(latest_path)}")
    print(f"Wrote {safe_relative(dated_path)}")
    print(f"Wrote {safe_relative(manifest_path)}")
    print(
        f"Items={len(ranked_items)} "
        f"Trade={summary.get('trade')} "
        f"Watch={summary.get('watch')} "
        f"Ignore={summary.get('ignore')}"
    )
    print(
        f"Top={summary.get('top_symbol')} "
        f"score={summary.get('top_score')} "
        f"pts={summary.get('top_score_pts')} "
        f"triage={summary.get('top_triage')} "
        f"archetype={summary.get('top_archetype')}"
    )

    if not ranked_items:
        print("No ranked items generated. Failing workflow.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
