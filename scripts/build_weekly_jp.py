#!/usr/bin/env python3
"""
Build Japan Weekly Screening for Neon Tokyo Signals.

Input:
- site/data/prices-jp/latest.json
- data/weekly_candidates_jp.csv, fallback data/universe_jp.csv

Output:
- site/data/japan/weekly/latest.json
- site/data/japan/weekly/YYYY-MM-DD.json
- site/data/japan/weekly/manifest.json
- compatibility copy: site/data/weekly-jp/latest.json

Design goals:
- No API calls here. This script reads the existing JP price cache only.
- Weekly model is medium-term and distinct from Daily.
- Japanese liquidity / extension / stop-limit risk is treated more strictly than US logic.
"""

from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Tokyo")

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
OUT_DIR = (ROOT / OUT_DIR).resolve() if not OUT_DIR.is_absolute() else OUT_DIR.resolve()

PRICES_JSON = Path(os.getenv("PRICES_JSON", str(OUT_DIR / "data" / "prices-jp" / "latest.json")))
PRICES_JSON = (ROOT / PRICES_JSON).resolve() if not PRICES_JSON.is_absolute() else PRICES_JSON.resolve()

WEEKLY_CSV = Path(os.getenv("WEEKLY_CANDIDATES_CSV", str(ROOT / "data" / "weekly_candidates_jp.csv")))
WEEKLY_CSV = (ROOT / WEEKLY_CSV).resolve() if not WEEKLY_CSV.is_absolute() else WEEKLY_CSV.resolve()

UNIVERSE_CSV = Path(os.getenv("UNIVERSE_CSV", str(ROOT / "data" / "universe_jp.csv")))
UNIVERSE_CSV = (ROOT / UNIVERSE_CSV).resolve() if not UNIVERSE_CSV.is_absolute() else UNIVERSE_CSV.resolve()

WEEKLY_OUT_DIR = OUT_DIR / "data" / "japan" / "weekly"
LEGACY_WEEKLY_OUT_DIR = OUT_DIR / "data" / "weekly-jp"

MIN_WEEKLY_BARS = int(os.getenv("WEEKLY_MIN_BARS", "42"))
TOP_ITEMS_LIMIT = int(os.getenv("WEEKLY_TOP_ITEMS_LIMIT", "40"))
WRITE_LEGACY_COPY = os.getenv("WEEKLY_WRITE_LEGACY_COPY", "true").lower() in {"1", "true", "yes"}

SCORE_WEIGHTS = {
    "trend_template_stage2": 220,
    "relative_strength_vs_topix": 180,
    "breakout_freshness": 160,
    "base_vcp_quality": 150,
    "volume_accumulation": 120,
    "liquidity_tradability": 100,
    "theme_confirmation": 40,
    "risk_extension_control": 30,
}


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
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    print(f"Wrote {safe_relative(path)}")


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
    return clamp((v - low) / (high - low))


def pct(cur: Any, prev: Any) -> float | None:
    c = to_float(cur)
    p = to_float(prev)
    if c is None or p is None or p == 0:
        return None
    return (c / p - 1.0) * 100.0


def load_candidate_meta() -> dict[str, dict[str, str]]:
    path = WEEKLY_CSV if WEEKLY_CSV.exists() else UNIVERSE_CSV
    if not path.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = (row.get("symbol") or "").strip()
            if symbol:
                out[symbol] = {k: (v or "").strip() for k, v in row.items()}
    return out


def bars_to_df(item: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for b in item.get("bars") or []:
        if not isinstance(b, dict) or not b.get("date"):
            continue
        rows.append({
            "date": b.get("date"),
            "Open": to_float(b.get("open")),
            "High": to_float(b.get("high")),
            "Low": to_float(b.get("low")),
            "Close": to_float(b.get("close")),
            "Volume": to_float(b.get("volume")) or 0.0,
        })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "Open", "High", "Low", "Close"])
    df = df[df["Close"] > 0]
    df = df.set_index("date").sort_index()
    return df[~df.index.duplicated(keep="last")]


def daily_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    # Use W-FRI as the weekly bucket label, but keep the real latest
    # trading date separately. Without this, a Wednesday run can look like
    # it used a future Friday close.
    date_series = pd.Series(df.index, index=df.index)
    wk = pd.DataFrame({
        "Open": df["Open"].resample("W-FRI").first(),
        "High": df["High"].resample("W-FRI").max(),
        "Low": df["Low"].resample("W-FRI").min(),
        "Close": df["Close"].resample("W-FRI").last(),
        "Volume": df["Volume"].resample("W-FRI").sum(),
        "LastTradingDate": date_series.resample("W-FRI").max(),
    }).dropna(subset=["Open", "High", "Low", "Close", "LastTradingDate"])
    wk = wk[wk["Close"] > 0]
    wk["WeekLabel"] = wk.index
    wk["IsPartialWeek"] = wk["LastTradingDate"].dt.normalize() < wk.index.normalize()
    return wk


def add_weekly_indicators(w: pd.DataFrame) -> pd.DataFrame:
    if w.empty:
        return w
    d = w.copy().sort_index()
    c, h, l, v = d["Close"], d["High"], d["Low"], d["Volume"]
    d["sma10w"] = c.rolling(10, min_periods=6).mean()
    d["sma30w"] = c.rolling(30, min_periods=18).mean()
    d["sma40w"] = c.rolling(40, min_periods=24).mean()
    d["sma30w_slope_4w_pct"] = pct(d["sma30w"], d["sma30w"].shift(4))
    d["high4w"] = h.rolling(4, min_periods=2).max()
    d["high10w"] = h.rolling(10, min_periods=6).max()
    d["high13w"] = h.rolling(13, min_periods=8).max()
    d["high52w"] = h.rolling(52, min_periods=30).max()
    d["low10w"] = l.rolling(10, min_periods=6).min()
    d["low30w"] = l.rolling(30, min_periods=18).min()
    d["low52w"] = l.rolling(52, min_periods=30).min()
    d["vol10w"] = v.rolling(10, min_periods=6).mean()
    d["vol30w"] = v.rolling(30, min_periods=18).mean()
    d["rvol10w"] = v / (d["vol10w"] + 1e-9)
    d["dollar_volume"] = c * v
    d["avg_dollar_volume10w"] = d["dollar_volume"].rolling(10, min_periods=6).mean()
    d["avg_dollar_volume30w"] = d["dollar_volume"].rolling(30, min_periods=18).mean()
    d["ret1w"] = c.pct_change(1) * 100.0
    d["ret2w"] = c.pct_change(2) * 100.0
    d["ret4w"] = c.pct_change(4) * 100.0
    d["ret8w"] = c.pct_change(8) * 100.0
    d["ret12w"] = c.pct_change(12) * 100.0
    d["ret26w"] = c.pct_change(26) * 100.0
    d["ret52w"] = c.pct_change(52) * 100.0
    d["week_range"] = (h - l).replace(0, np.nan)
    d["range_pos"] = (c - l) / d["week_range"]
    d["close_pos10w"] = (c - d["low10w"]) / ((d["high10w"] - d["low10w"]).replace(0, np.nan))
    d["close_pos30w"] = (c - d["low30w"]) / ((d["high10w"] - d["low30w"]).replace(0, np.nan))
    d["base_depth10w_pct"] = (d["high10w"] / d["low10w"] - 1.0) * 100.0
    d["base_depth13w_pct"] = (d["high13w"] / l.rolling(13, min_periods=8).min() - 1.0) * 100.0
    d["extension_sma10w_pct"] = (c / d["sma10w"] - 1.0) * 100.0
    d["extension_sma30w_pct"] = (c / d["sma30w"] - 1.0) * 100.0
    d["distance_from_52w_high_pct"] = (c / d["high52w"] - 1.0) * 100.0
    d["distance_from_10w_high_pct"] = (c / d["high10w"] - 1.0) * 100.0
    prev_c = c.shift(1)
    tr = pd.concat([(h-l).abs(), (h-prev_c).abs(), (l-prev_c).abs()], axis=1).max(axis=1)
    d["atr10w_pct"] = tr.rolling(10, min_periods=6).mean() / c * 100.0
    return d


def classify_liquidity(avg_value10w: Any, today_value: Any) -> tuple[str, float, list[str]]:
    avg = to_float(avg_value10w)
    today = to_float(today_value)
    flags: list[str] = []
    if avg is None:
        return "Unknown", 0.0, ["unknown_liquidity"]
    if avg >= 5_000_000_000:
        return "Institutional", 1.0, ["institutional_liquidity"]
    if avg >= 1_000_000_000:
        return "High Liquidity", 0.88, ["high_liquidity"]
    if avg >= 300_000_000:
        return "Tradable", 0.68, ["tradable_liquidity"]
    if avg >= 100_000_000:
        return "Thin", 0.36, ["thin_liquidity"]
    if today is not None and today >= 300_000_000 and avg >= 70_000_000:
        return "Event Thin", 0.30, ["event_thin_liquidity"]
    return "Very Thin", 0.06, ["very_thin_liquidity"]


def sane_benchmark_return(value: Any, limit_abs_pct: float) -> float | None:
    v = to_float(value)
    if v is None or abs(v) > limit_abs_pct:
        return None
    return v


def benchmark_weekly(prices: dict[str, Any]) -> tuple[pd.Series | None, dict[str, pd.Series | None], dict[str, Any]]:
    pulse = {str(x.get("pulse_label") or x.get("symbol") or "").upper(): x for x in prices.get("market_pulse") or [] if isinstance(x, dict)}
    out: dict[str, pd.Series | None] = {}
    states: dict[str, Any] = {}
    for label in ["TOPIX", "NIKKEI", "GROWTH"]:
        item = pulse.get(label)
        row = None
        state: dict[str, Any] = {"label": label, "available": False}
        if item:
            w = add_weekly_indicators(daily_to_weekly(bars_to_df(item)))
            if not w.empty:
                row = w.iloc[-1]
                close = to_float(row.get("Close"))
                sma10 = to_float(row.get("sma10w"))
                sma30 = to_float(row.get("sma30w"))
                ret4_raw = to_float(row.get("ret4w"))
                ret12_raw = to_float(row.get("ret12w"))
                ret26_raw = to_float(row.get("ret26w"))
                ret4 = sane_benchmark_return(ret4_raw, 20.0)
                ret12 = sane_benchmark_return(ret12_raw, 30.0)
                ret26 = sane_benchmark_return(ret26_raw, 50.0)
                data_quality = "valid" if ret4 is not None and ret12 is not None and ret26 is not None else "invalid"
                if close is not None:
                    if data_quality != "valid":
                        trend = "Benchmark check"
                        tape = "Return anomaly"
                    elif sma10 is not None and sma30 is not None and close >= sma10 >= sma30:
                        trend = "Risk-On trend"
                    elif sma30 is not None and close >= sma30:
                        trend = "Neutral trend"
                    else:
                        trend = "Risk-Off trend"
                    tape = tape if data_quality != "valid" else ("Strong tape" if (ret4 or 0) >= 4 else "Weak tape" if (ret4 or 0) <= -4 else "Mixed tape")
                    state.update({
                        "available": True,
                        "symbol": item.get("symbol"),
                        "close": safe_round(close, 4),
                        "ret4w_pct": safe_round(ret4, 4),
                        "ret12w_pct": safe_round(ret12, 4),
                        "raw_ret4w_pct": safe_round(ret4_raw, 4),
                        "raw_ret12w_pct": safe_round(ret12_raw, 4),
                        "data_quality": data_quality,
                        "above_sma10w": bool(data_quality == "valid" and sma10 is not None and close >= sma10),
                        "above_sma30w": bool(data_quality == "valid" and sma30 is not None and close >= sma30),
                        "broad_trend": trend,
                        "short_term_tape": tape,
                    })
        out[label] = row
        states[label] = state
    return out.get("TOPIX"), out, states


def score_item(item: dict[str, Any], meta: dict[str, str], topix_row: pd.Series | None) -> dict[str, Any] | None:
    w = add_weekly_indicators(daily_to_weekly(bars_to_df(item)))
    if len(w) < MIN_WEEKLY_BARS:
        return None
    last = w.iloc[-1]
    prev = w.iloc[-2] if len(w) >= 2 else last

    week_label_ts = pd.Timestamp(last.name).normalize()
    latest_trading_ts = pd.Timestamp(last.get("LastTradingDate")).normalize() if pd.notna(last.get("LastTradingDate")) else week_label_ts
    week_label = str(week_label_ts.date())
    latest_trading_date = str(latest_trading_ts.date())
    is_partial_week = bool(latest_trading_ts < week_label_ts)

    close = to_float(last.get("Close"))
    if close is None:
        return None
    symbol = item.get("symbol")
    bucket = meta.get("bucket") or item.get("bucket") or "Watch"
    priority = meta.get("priority") or item.get("priority") or "C"
    theme = meta.get("theme") or item.get("theme") or "Japan Equity"
    name = meta.get("name") or item.get("name") or symbol

    sma10 = to_float(last.get("sma10w"))
    sma30 = to_float(last.get("sma30w"))
    sma40 = to_float(last.get("sma40w"))
    slope30 = to_float(last.get("sma30w_slope_4w_pct")) or 0.0
    high52 = to_float(last.get("high52w"))
    low52 = to_float(last.get("low52w"))
    high10_prev = to_float(prev.get("high10w"))
    high52_prev = to_float(prev.get("high52w"))
    low10 = to_float(last.get("low10w"))
    avg_value10 = to_float(last.get("avg_dollar_volume10w"))
    dollar_value = to_float(last.get("dollar_volume"))
    ret1w = to_float(last.get("ret1w")) or 0.0
    ret4w = to_float(last.get("ret4w")) or 0.0
    ret12w = to_float(last.get("ret12w")) or 0.0
    ret26w = to_float(last.get("ret26w")) or 0.0
    rvol = max(0.0, to_float(last.get("rvol10w")) or 0.0)
    range_pos = clamp(last.get("range_pos"), 0, 1)
    close_pos10 = clamp(last.get("close_pos10w"), 0, 1)
    base_depth = to_float(last.get("base_depth10w_pct"))
    ext10 = to_float(last.get("extension_sma10w_pct")) or 0.0
    ext30 = to_float(last.get("extension_sma30w_pct")) or 0.0
    dist52 = to_float(last.get("distance_from_52w_high_pct"))
    atr10 = to_float(last.get("atr10w_pct"))

    topix_ret4 = sane_benchmark_return(topix_row.get("ret4w"), 20.0) if topix_row is not None else 0.0
    topix_ret12 = sane_benchmark_return(topix_row.get("ret12w"), 30.0) if topix_row is not None else 0.0
    topix_ret26 = sane_benchmark_return(topix_row.get("ret26w"), 50.0) if topix_row is not None else 0.0
    benchmark_return_quality = {
        "4w": "valid" if topix_ret4 is not None else "invalid",
        "12w": "valid" if topix_ret12 is not None else "invalid",
        "26w": "valid" if topix_ret26 is not None else "invalid",
    }
    rs4 = ret4w - (topix_ret4 if topix_ret4 is not None else 0.0)
    rs12 = ret12w - (topix_ret12 if topix_ret12 is not None else 0.0)
    rs26 = ret26w - (topix_ret26 if topix_ret26 is not None else 0.0)

    liq_band, liq_score, liq_flags = classify_liquidity(avg_value10, dollar_value)

    above10 = close >= sma10 if sma10 is not None else False
    above30 = close >= sma30 if sma30 is not None else False
    above40 = close >= sma40 if sma40 is not None else False
    near_high52 = dist52 is not None and dist52 >= -25.0
    well_off_low = bool(low52 is not None and close >= low52 * 1.30)

    trend_score = clamp(
        0.20 * float(above10) + 0.25 * float(above30) + 0.15 * float(above40)
        + 0.18 * scale(slope30, -3, 8)
        + 0.12 * float(near_high52)
        + 0.10 * float(well_off_low)
    )
    trend_pts = round(SCORE_WEIGHTS["trend_template_stage2"] * trend_score)

    rs_score = clamp(0.24 * scale(rs4, -8, 14) + 0.46 * scale(rs12, -12, 32) + 0.30 * scale(rs26, -18, 55))
    rs_pts = round(SCORE_WEIGHTS["relative_strength_vs_topix"] * rs_score)

    fresh_10w_breakout = bool(high10_prev is not None and close >= high10_prev * 0.995)
    fresh_52w_area = bool(high52_prev is not None and close >= high52_prev * 0.96)
    breakout_score = clamp(
        0.34 * float(fresh_10w_breakout)
        + 0.24 * float(fresh_52w_area)
        + 0.20 * close_pos10
        + 0.12 * scale(rvol, 0.8, 2.4)
        + 0.10 * scale(rs4, -4, 12)
    )
    breakout_pts = round(SCORE_WEIGHTS["breakout_freshness"] * breakout_score)

    depth_score = 1.0 - scale(base_depth, 12, 55)
    not_too_choppy = 1.0 - scale(atr10, 4, 18)
    constructive_pullback = clamp(0.55 * depth_score + 0.25 * close_pos10 + 0.20 * not_too_choppy)
    base_score = clamp(constructive_pullback)
    base_pts = round(SCORE_WEIGHTS["base_vcp_quality"] * base_score)

    up_week = ret1w >= 0 and range_pos >= 0.50
    accumulation_score = clamp(0.42 * scale(rvol, 0.8, 2.5) + 0.22 * range_pos + 0.18 * float(up_week) + 0.18 * scale(dollar_value, 100_000_000, 2_000_000_000))
    volume_pts = round(SCORE_WEIGHTS["volume_accumulation"] * accumulation_score)

    liquidity_pts = round(SCORE_WEIGHTS["liquidity_tradability"] * liq_score)

    theme_score = 0.45
    if bucket == "Core":
        theme_score += 0.25
    elif bucket == "Discovery":
        theme_score += 0.12
    if priority == "A":
        theme_score += 0.25
    elif priority == "B":
        theme_score += 0.12
    theme_score = clamp(theme_score)
    theme_pts = round(SCORE_WEIGHTS["theme_confirmation"] * theme_score)

    extended = ret4w >= 35 or ret12w >= 80 or ext10 >= 28 or ext30 >= 60
    very_extended = ret4w >= 50 or ret12w >= 120 or ext10 >= 42 or ext30 >= 85
    weak_close = range_pos <= 0.35 and rvol >= 1.3
    distribution_week = ret1w <= -8 and rvol >= 1.4 and range_pos <= 0.45
    low_price = close < 300
    very_low_liquidity = liq_band in {"Very Thin", "Unknown"}
    thin_liquidity = liq_band in {"Thin", "Event Thin", "Very Thin", "Unknown"}
    limit_like_risk = abs(ret1w) >= 18 or (rvol >= 5 and abs(ret1w) >= 10)

    risk_score = clamp(
        1.0
        - 0.34 * float(extended)
        - 0.24 * float(weak_close)
        - 0.30 * float(distribution_week)
        - 0.20 * float(thin_liquidity)
        - 0.18 * float(low_price)
        - 0.18 * float(limit_like_risk)
    )
    risk_pts = round(SCORE_WEIGHTS["risk_extension_control"] * risk_score)

    component_pts = {
        "trend_template_stage2": trend_pts,
        "relative_strength_vs_topix": rs_pts,
        "breakout_freshness": breakout_pts,
        "base_vcp_quality": base_pts,
        "volume_accumulation": volume_pts,
        "liquidity_tradability": liquidity_pts,
        "theme_confirmation": theme_pts,
        "risk_extension_control": risk_pts,
    }
    raw_score = sum(component_pts.values())

    cap = 1000
    cap_reasons: list[str] = []
    if very_low_liquidity:
        cap = min(cap, 580)
        cap_reasons.append("very low liquidity cap")
    elif thin_liquidity and bucket != "Core":
        cap = min(cap, 680)
        cap_reasons.append("thin discovery liquidity cap")
    if extended:
        cap = min(cap, 760)
        cap_reasons.append("extension cap")
    if very_extended:
        cap = min(cap, 650)
        cap_reasons.append("extreme extension cap")
    if weak_close or distribution_week:
        cap = min(cap, 620)
        cap_reasons.append("distribution week cap")
    if low_price:
        cap = min(cap, 700)
        cap_reasons.append("low price cap")
    if not (above30 and slope30 > 0):
        cap = min(cap, 720)
        cap_reasons.append("stage 2 not confirmed cap")

    score_pts = int(min(raw_score, cap))

    if very_extended or distribution_week or very_low_liquidity or score_pts < 520:
        quality = "E Avoid"
    elif extended:
        quality = "D Extended"
    elif score_pts >= 820 and trend_pts >= 180 and rs_pts >= 135 and breakout_pts >= 115 and volume_pts >= 75:
        quality = "A+ Fresh Breakout"
    elif score_pts >= 750 and trend_pts >= 175 and rs_pts >= 135:
        quality = "A Leader"
    elif score_pts >= 680 and trend_pts >= 150 and (base_pts >= 90 or breakout_pts >= 90):
        quality = "B Constructive Setup"
    elif score_pts >= 600 and trend_pts >= 125 and rs_pts >= 80:
        quality = "C Early Watch"
    elif extended:
        quality = "D Extended"
    else:
        quality = "E Avoid"

    if quality in {"A+ Fresh Breakout", "A Leader"} and score_pts >= 750 and liq_band in {"Institutional", "High Liquidity", "Tradable"} and not extended and not weak_close:
        signal = "Trade"
    elif quality in {"B Constructive Setup", "C Early Watch"} and not very_low_liquidity and not distribution_week:
        signal = "Watch"
    else:
        signal = "Avoid"

    why: list[str] = []
    if quality == "A+ Fresh Breakout":
        why.append("fresh weekly breakout")
    elif quality == "A Leader":
        why.append("weekly RS leader")
    elif quality == "B Constructive Setup":
        why.append("constructive base forming")
    elif quality == "C Early Watch":
        why.append("early weekly setup")
    if rs_pts >= 130:
        why.append("TOPIX-relative strength")
    if volume_pts >= 80:
        why.append("volume accumulation")
    if breakout_pts >= 100:
        why.append("near breakout zone")
    if not why:
        why.append("not enough weekly confirmation")

    risk_notes: list[str] = []
    if extended:
        risk_notes.append("extended from weekly averages")
    if weak_close:
        risk_notes.append("weak close on volume")
    if distribution_week:
        risk_notes.append("distribution week")
    if thin_liquidity:
        risk_notes.append("liquidity constraint")
    if limit_like_risk:
        risk_notes.append("limit-move / gap risk")
    if not risk_notes:
        risk_notes.append("normal weekly risk")

    return {
        "rank": None,
        "symbol": symbol,
        "name": name,
        "theme": theme,
        "bucket": bucket,
        "priority": priority,
        "market": "JP",
        "currency": "JPY",
        "latest_week": latest_trading_date,
        "latest_trading_date": latest_trading_date,
        "week_label": week_label,
        "is_partial_week": is_partial_week,
        "price": safe_round(close, 4),
        "score_pts": score_pts,
        "score_0_1": safe_round(score_pts / 1000.0, 4),
        "signal": signal,
        "quality": quality,
        "classification": quality,
        "why_now": "; ".join(why[:3]),
        "main_risk": "; ".join(risk_notes[:3]),
        "liquidity_band": liq_band,
        "liquidity_score_0_1": safe_round(liq_score, 4),
        "entry_quality": "Confirmed" if signal == "Trade" else "Developing" if signal == "Watch" else "Blocked",
        "extension_status": "Extreme" if very_extended else "Extended" if extended else "Controlled",
        "relative_strength_status": "Leader" if rs_pts >= 135 else "Constructive" if rs_pts >= 95 else "Weak",
        "component_pts": component_pts,
        "component_scores_0_1": {k: safe_round(v / SCORE_WEIGHTS[k], 4) for k, v in component_pts.items()},
        "benchmark_return_quality": benchmark_return_quality,
        "metrics": {
            "return_1w_pct": safe_round(ret1w, 4),
            "return_4w_pct": safe_round(ret4w, 4),
            "return_12w_pct": safe_round(ret12w, 4),
            "return_26w_pct": safe_round(ret26w, 4),
            "rs_vs_topix_4w_pct": safe_round(rs4, 4),
            "rs_vs_topix_12w_pct": safe_round(rs12, 4),
            "rs_vs_topix_26w_pct": safe_round(rs26, 4),
            "rvol_10w": safe_round(rvol, 4),
            "avg_traded_value_10w_jpy": safe_round(avg_value10, 2),
            "latest_traded_value_jpy": safe_round(dollar_value, 2),
            "distance_from_52w_high_pct": safe_round(dist52, 4),
            "base_depth_10w_pct": safe_round(base_depth, 4),
            "extension_sma10w_pct": safe_round(ext10, 4),
            "extension_sma30w_pct": safe_round(ext30, 4),
            "range_pos_0_1": safe_round(range_pos, 4),
            "atr_10w_pct": safe_round(atr10, 4),
        },
        "flags": [
            *liq_flags,
            *( ["stage2_trend"] if above10 and above30 and above40 and slope30 > 0 else [] ),
            *( ["fresh_10w_breakout"] if fresh_10w_breakout else [] ),
            *( ["near_52w_high"] if fresh_52w_area else [] ),
            *( ["volume_accumulation"] if volume_pts >= 80 else [] ),
            *( ["extended"] if extended else [] ),
            *( ["very_extended"] if very_extended else [] ),
            *( ["weak_close"] if weak_close else [] ),
            *( ["distribution_week"] if distribution_week else [] ),
            *( ["limit_move_risk"] if limit_like_risk else [] ),
        ],
        "cap_reasons": cap_reasons,
        "source": item.get("source"),
        "bars_count_daily": item.get("bars_count"),
        "bars_count_weekly": len(w),
    }


def summarize(items: list[dict[str, Any]], benchmark_state: dict[str, Any], latest_week: str | None) -> dict[str, Any]:
    def count_where(key: str, value: str) -> int:
        return sum(1 for x in items if x.get(key) == value)
    by_signal = {s: count_where("signal", s) for s in ["Trade", "Watch", "Avoid"]}
    by_bucket: dict[str, int] = {}
    by_theme: dict[str, int] = {}
    by_quality: dict[str, int] = {}
    for x in items:
        by_bucket[x.get("bucket") or "Unknown"] = by_bucket.get(x.get("bucket") or "Unknown", 0) + 1
        by_theme[x.get("theme") or "Unknown"] = by_theme.get(x.get("theme") or "Unknown", 0) + 1
        by_quality[x.get("quality") or "Unknown"] = by_quality.get(x.get("quality") or "Unknown", 0) + 1
    tradable = [x for x in items if x.get("signal") in {"Trade", "Watch"}]
    risk_count = sum(1 for x in items if x.get("signal") == "Avoid" or x.get("extension_status") != "Controlled")
    best_theme = None
    if items:
        score_by_theme: dict[str, list[int]] = {}
        for x in items[:15]:
            score_by_theme.setdefault(x.get("theme") or "Unknown", []).append(int(x.get("score_pts") or 0))
        best_theme = max(score_by_theme.items(), key=lambda kv: (sum(kv[1]) / len(kv[1]), len(kv[1])))[0]
    market_state = benchmark_state.get("TOPIX", {})
    if market_state.get("data_quality") == "invalid":
        market_state = benchmark_state.get("NIKKEI", market_state)
    if by_signal.get("Trade", 0) > 0:
        verdict = "TRADE SETUPS AVAILABLE"
        risk_message = "Weekly Trade candidates passed trend, RS and liquidity filters."
    elif by_signal.get("Watch", 0) > 0:
        verdict = "WATCHLIST BUILDING"
        risk_message = "No full Trade basket. Monitor Watch names for weekly confirmation."
    else:
        verdict = "NO WEEKLY ACTION"
        risk_message = "Weekly model did not find a strong enough setup."
    return {
        "latest_week": latest_week,
        "latest_trading_date": items[0].get("latest_trading_date") if items else latest_week,
        "week_label": items[0].get("week_label") if items else latest_week,
        "is_partial_week": bool(items[0].get("is_partial_week")) if items else False,
        "items_count": len(items),
        "top_symbol": items[0].get("symbol") if items else None,
        "top_name": items[0].get("name") if items else None,
        "top_score_pts": items[0].get("score_pts") if items else None,
        "top_signal": items[0].get("signal") if items else None,
        "top_quality": items[0].get("quality") if items else None,
        "trade": by_signal.get("Trade", 0),
        "watch": by_signal.get("Watch", 0),
        "avoid": by_signal.get("Avoid", 0),
        "by_signal": by_signal,
        "by_bucket": dict(sorted(by_bucket.items())),
        "by_quality": dict(sorted(by_quality.items())),
        "best_theme": best_theme,
        "top3": items[:3],
        "tradable_count": len(tradable),
        "risk_count": risk_count,
        "market_state": market_state,
        "verdict": verdict,
        "risk_message": risk_message,
    }


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"PRICES_JSON={safe_relative(PRICES_JSON)}")
    prices = read_json(PRICES_JSON)
    meta_map = load_candidate_meta()
    topix_row, benchmarks, benchmark_state = benchmark_weekly(prices)

    raw_items = prices.get("items") or prices.get("equities") or []
    scored: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    allowed = set(meta_map.keys()) if meta_map else set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        symbol = str(raw.get("symbol") or "").strip()
        if not symbol:
            continue
        if allowed and symbol not in allowed:
            continue
        try:
            item = score_item(raw, meta_map.get(symbol, {}), topix_row)
            if item:
                scored.append(item)
            else:
                failures.append({"symbol": symbol, "reason": "insufficient weekly data"})
        except Exception as exc:
            failures.append({"symbol": symbol, "reason": str(exc)[:240]})

    scored.sort(key=lambda x: (int(x.get("score_pts") or 0), x.get("signal") == "Trade", x.get("quality") or ""), reverse=True)
    for idx, item in enumerate(scored, 1):
        item["rank"] = idx

    latest_week = scored[0].get("latest_week") if scored else None
    latest_trading_date = scored[0].get("latest_trading_date") if scored else latest_week
    week_label = scored[0].get("week_label") if scored else latest_week
    is_partial_week = bool(scored[0].get("is_partial_week")) if scored else False
    date_key = latest_trading_date or latest_week or now_jst().strftime("%Y-%m-%d")
    items = scored[:TOP_ITEMS_LIMIT]

    payload = {
        "schema_version": "weekly-jp-v1",
        "date": date_key,
        "latest_trading_date": latest_trading_date,
        "week_label": week_label,
        "is_partial_week": is_partial_week,
        "generated_at": iso_now(),
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "benchmark": "TOPIX",
        "source_prices": safe_relative(PRICES_JSON),
        "source_prices_generated_at": prices.get("generated_at"),
        "universe_csv": safe_relative(WEEKLY_CSV if WEEKLY_CSV.exists() else UNIVERSE_CSV),
        "methodology": {
            "name": "Neon Tokyo Weekly JP Score v1",
            "description": "Weekly medium-term Japan equity screen using trend template, relative strength vs TOPIX, breakout freshness, base quality, volume accumulation, tradability and risk controls.",
            "api_calls": 0,
            "score_weights": SCORE_WEIGHTS,
            "trade_rule": "A+ Fresh Breakout or A Leader, score >= 750, sufficient liquidity, controlled extension.",
            "watch_rule": "B Constructive Setup or C Early Watch without severe liquidity/distribution risk.",
            "avoid_rule": "Extended, distribution week, very low liquidity, low score or stage-2 failure.",
        },
        "benchmarks": benchmark_state,
        "summary": summarize(items, benchmark_state, latest_week),
        "items": items,
        "all_items": scored,
        "failures": failures[:100],
    }

    write_json(WEEKLY_OUT_DIR / f"{date_key}.json", payload)
    write_json(WEEKLY_OUT_DIR / "latest.json", payload)
    manifest = {
        "schema_version": "weekly-jp-manifest-v1",
        "generated_at": iso_now(),
        "latest": "latest.json",
        "date": date_key,
        "count": len(scored),
        "source_prices_generated_at": prices.get("generated_at"),
    }
    write_json(WEEKLY_OUT_DIR / "manifest.json", manifest)

    if WRITE_LEGACY_COPY:
        write_json(LEGACY_WEEKLY_OUT_DIR / "latest.json", payload)
        write_json(LEGACY_WEEKLY_OUT_DIR / "manifest.json", manifest)

    print("weekly scored=", len(scored))
    print("weekly items=", len(items))
    print("trade=", payload["summary"].get("trade"), "watch=", payload["summary"].get("watch"), "avoid=", payload["summary"].get("avoid"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
