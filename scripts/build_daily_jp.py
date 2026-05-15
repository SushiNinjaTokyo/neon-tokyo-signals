#!/usr/bin/env python3
"""
Build Daily JP signal ranking from normalized JP price JSON.

Input:
- site/data/prices-jp/latest.json

Output:
- site/data/daily-jp/latest.json
- site/data/daily-jp/manifest.json
- site/data/daily-jp/YYYY-MM-DD.json

Scope:
- This script does NOT fetch prices.
- This script does NOT render HTML.
- This script builds a structured ranking JSON for /japan/daily/.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any
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
    "volume_shock": 25.0,
    "breakout_quality": 25.0,
    "relative_strength": 20.0,
    "compression": 15.0,
    "entry_timing": 15.0,
}

MAX_RAW_SCORE = sum(WEIGHTS.values())


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


def as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        v = float(value)
        if math.isfinite(v):
            return v
        return None
    except Exception:
        return None


def as_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        v = float(value)
        if math.isfinite(v):
            return int(round(v))
        return None
    except Exception:
        return None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def scale_linear(value: float | None, low: float, high: float) -> float:
    """
    Convert a value to 0..1 using linear interpolation.
    Values below low -> 0.
    Values above high -> 1.
    """
    if value is None:
        return 0.0
    if high == low:
        return 0.0
    return clamp((value - low) / (high - low), 0.0, 1.0)


def score_volume_shock(metrics: dict[str, Any]) -> tuple[float, list[str]]:
    flags: list[str] = []

    volume_ratio = as_float(metrics.get("volume_ratio_20d"))
    avg_value_20d = as_float(metrics.get("avg_traded_value_20d_jpy"))
    latest_value = as_float(metrics.get("latest_traded_value_jpy"))

    # Main volume expansion score.
    # 1.0x = no score, 2.0x = decent, 4.0x+ = very strong.
    ratio_score = scale_linear(volume_ratio, 1.0, 4.0)

    # Liquidity confirmation.
    # ¥100M = barely acceptable, ¥1B+ = strong.
    avg_value_score = scale_linear(avg_value_20d, 100_000_000, 1_000_000_000)

    # Today's traded value helps avoid tiny illiquid names ranking too high.
    latest_value_score = scale_linear(latest_value, 100_000_000, 1_500_000_000)

    combined = (
        ratio_score * 0.58
        + avg_value_score * 0.22
        + latest_value_score * 0.20
    )

    if volume_ratio is not None:
        if volume_ratio >= 4.0:
            flags.append("major_volume_shock")
        elif volume_ratio >= 2.0:
            flags.append("volume_expansion")

    if avg_value_20d is not None and avg_value_20d >= 1_000_000_000:
        flags.append("high_liquidity")

    return combined * WEIGHTS["volume_shock"], flags


def score_breakout_quality(metrics: dict[str, Any]) -> tuple[float, list[str]]:
    flags: list[str] = []

    dist_20d = as_float(metrics.get("distance_from_20d_high_pct"))
    dist_52w = as_float(metrics.get("distance_from_52w_high_pct"))
    range_pos = as_float(metrics.get("range_position_20d_0_1"))
    ret_20d = as_float(metrics.get("return_20d_pct"))

    # Near 20D high.
    # 0% or above = ideal, -10% = weak.
    near_20d_high = 1.0 - scale_linear(abs(min(dist_20d or 0.0, 0.0)), 0.0, 10.0)

    # Near 52W high.
    # 0% = ideal, -25% = weak.
    near_52w_high = 1.0 - scale_linear(abs(min(dist_52w or 0.0, 0.0)), 0.0, 25.0)

    # Closing near top of recent range.
    range_score = clamp(range_pos or 0.0, 0.0, 1.0)

    # 20D return confirms upward pressure, but should not dominate.
    return_score = scale_linear(ret_20d, 0.0, 35.0)

    combined = (
        near_20d_high * 0.32
        + near_52w_high * 0.30
        + range_score * 0.23
        + return_score * 0.15
    )

    if dist_20d is not None and dist_20d >= -3.0:
        flags.append("near_20d_high")

    if dist_52w is not None and dist_52w >= -10.0:
        flags.append("near_52w_high")

    if range_pos is not None and range_pos >= 0.80:
        flags.append("upper_range_close")

    return combined * WEIGHTS["breakout_quality"], flags


def score_relative_strength(
    metrics: dict[str, Any],
    topix_metrics: dict[str, Any] | None,
) -> tuple[float, list[str], dict[str, float | None]]:
    flags: list[str] = []

    ret_20d = as_float(metrics.get("return_20d_pct"))
    ret_60d = as_float(metrics.get("return_60d_pct"))
    ret_120d = as_float(metrics.get("return_120d_pct"))

    topix_20d = as_float((topix_metrics or {}).get("return_20d_pct"))
    topix_60d = as_float((topix_metrics or {}).get("return_60d_pct"))
    topix_120d = as_float((topix_metrics or {}).get("return_120d_pct"))

    rs_20d = ret_20d - topix_20d if ret_20d is not None and topix_20d is not None else None
    rs_60d = ret_60d - topix_60d if ret_60d is not None and topix_60d is not None else None
    rs_120d = ret_120d - topix_120d if ret_120d is not None and topix_120d is not None else None

    # If TOPIX is unavailable, fall back to absolute returns.
    base_20 = rs_20d if rs_20d is not None else ret_20d
    base_60 = rs_60d if rs_60d is not None else ret_60d
    base_120 = rs_120d if rs_120d is not None else ret_120d

    score_20 = scale_linear(base_20, -5.0, 25.0)
    score_60 = scale_linear(base_60, -5.0, 45.0)
    score_120 = scale_linear(base_120, -5.0, 70.0)

    combined = score_20 * 0.45 + score_60 * 0.35 + score_120 * 0.20

    if rs_20d is not None and rs_20d >= 10:
        flags.append("rs_20d_positive")
    if rs_60d is not None and rs_60d >= 20:
        flags.append("rs_60d_leader")
    if ret_20d is not None and ret_20d > 0:
        flags.append("positive_20d_return")

    relative_metrics = {
        "rs_vs_topix_20d_pct": round(rs_20d, 4) if rs_20d is not None else None,
        "rs_vs_topix_60d_pct": round(rs_60d, 4) if rs_60d is not None else None,
        "rs_vs_topix_120d_pct": round(rs_120d, 4) if rs_120d is not None else None,
    }

    return combined * WEIGHTS["relative_strength"], flags, relative_metrics


def score_compression(metrics: dict[str, Any]) -> tuple[float, list[str]]:
    flags: list[str] = []

    compression_20d = as_float(metrics.get("compression_20d_pct"))
    vol_20d = as_float(metrics.get("volatility_20d_annualized_pct"))
    volume_ratio = as_float(metrics.get("volume_ratio_20d"))
    range_pos = as_float(metrics.get("range_position_20d_0_1"))

    # Compression is useful when not too wide.
    # 8% or less = very tight, 35%+ = loose.
    compression_score = 1.0 - scale_linear(compression_20d, 8.0, 35.0)

    # Lower volatility helps, but very tiny volatility can also mean no interest.
    vol_score = 1.0 - scale_linear(vol_20d, 25.0, 90.0)

    # Compression + volume expansion + close near high is better.
    release_score = (
        scale_linear(volume_ratio, 1.0, 3.0) * 0.55
        + clamp(range_pos or 0.0, 0.0, 1.0) * 0.45
    )

    combined = (
        compression_score * 0.45
        + vol_score * 0.20
        + release_score * 0.35
    )

    if compression_20d is not None and compression_20d <= 18:
        flags.append("compressed_range")

    if volume_ratio is not None and volume_ratio >= 1.5 and range_pos is not None and range_pos >= 0.75:
        flags.append("compression_release")

    return combined * WEIGHTS["compression"], flags


def score_entry_timing(metrics: dict[str, Any]) -> tuple[float, list[str]]:
    flags: list[str] = []

    ret_1d = as_float(metrics.get("return_1d_pct"))
    ret_5d = as_float(metrics.get("return_5d_pct"))
    ret_20d = as_float(metrics.get("return_20d_pct"))
    dist_20d = as_float(metrics.get("distance_from_20d_high_pct"))
    range_pos = as_float(metrics.get("range_position_20d_0_1"))

    # Prefer active but not insanely extended.
    one_day_ok = 1.0 - scale_linear(abs(ret_1d or 0.0), 7.0, 20.0)
    five_day_ok = 1.0 - scale_linear(max(ret_5d or 0.0, 0.0), 18.0, 45.0)
    twenty_day_ok = 1.0 - scale_linear(max(ret_20d or 0.0, 0.0), 35.0, 85.0)

    # Near high, but not far below.
    high_proximity = 1.0 - scale_linear(abs(min(dist_20d or 0.0, 0.0)), 0.0, 12.0)

    # Closing in upper range is good.
    range_quality = clamp(range_pos or 0.0, 0.0, 1.0)

    combined = (
        one_day_ok * 0.22
        + five_day_ok * 0.22
        + twenty_day_ok * 0.18
        + high_proximity * 0.20
        + range_quality * 0.18
    )

    if ret_1d is not None and ret_1d >= 8:
        flags.append("strong_1d_move")

    if ret_5d is not None and ret_5d >= 20:
        flags.append("hot_5d_move")

    if ret_20d is not None and ret_20d >= 35:
        flags.append("hot_20d_move")

    return combined * WEIGHTS["entry_timing"], flags


def compute_penalty(item: dict[str, Any]) -> tuple[float, list[str]]:
    metrics = item.get("metrics") or {}

    penalty = 0.0
    flags: list[str] = []

    latest_close = as_float(metrics.get("latest_close"))
    avg_value_20d = as_float(metrics.get("avg_traded_value_20d_jpy"))
    latest_value = as_float(metrics.get("latest_traded_value_jpy"))
    ret_1d = as_float(metrics.get("return_1d_pct"))
    ret_5d = as_float(metrics.get("return_5d_pct"))
    ret_20d = as_float(metrics.get("return_20d_pct"))
    volume_ratio = as_float(metrics.get("volume_ratio_20d"))
    bars_count = as_int(item.get("bars_count"))
    bucket = str(item.get("bucket") or "").strip().lower()
    is_partial = bool(item.get("is_partial"))

    if latest_close is not None and latest_close < 300:
        penalty -= 15.0
        flags.append("low_price_penalty")

    if avg_value_20d is None:
        penalty -= 12.0
        flags.append("unknown_liquidity_penalty")
    elif avg_value_20d < 100_000_000:
        penalty -= 25.0
        flags.append("very_low_liquidity_penalty")
    elif avg_value_20d < 300_000_000:
        penalty -= 10.0
        flags.append("low_liquidity_penalty")

    if latest_value is not None and latest_value < 50_000_000:
        penalty -= 8.0
        flags.append("thin_latest_value_penalty")

    if ret_1d is not None and ret_1d >= 20:
        penalty -= 12.0
        flags.append("extended_1d_penalty")

    if ret_5d is not None and ret_5d >= 40:
        penalty -= 12.0
        flags.append("extended_5d_penalty")

    if ret_20d is not None and ret_20d >= 80:
        penalty -= 15.0
        flags.append("extended_20d_penalty")

    if volume_ratio is not None and volume_ratio >= 8:
        penalty -= 6.0
        flags.append("possible_event_spike_penalty")

    if bars_count is not None and bars_count < 60:
        penalty -= 10.0
        flags.append("insufficient_history_penalty")

    if is_partial:
        penalty -= 6.0
        flags.append("partial_data_penalty")

    if bucket == "watch":
        penalty -= 8.0
        flags.append("watch_bucket_penalty")

    return penalty, flags


def classify_signal(
    score: float,
    item: dict[str, Any],
    flags: list[str],
) -> str:
    metrics = item.get("metrics") or {}

    avg_value_20d = as_float(metrics.get("avg_traded_value_20d_jpy"))
    latest_close = as_float(metrics.get("latest_close"))
    ret_1d = as_float(metrics.get("return_1d_pct"))
    ret_5d = as_float(metrics.get("return_5d_pct"))
    ret_20d = as_float(metrics.get("return_20d_pct"))
    bars_count = as_int(item.get("bars_count"))

    if bars_count is not None and bars_count < 20:
        return "Insufficient Data"

    if avg_value_20d is not None and avg_value_20d < 100_000_000:
        if score >= 70:
            return "Watch: Low Liquidity Momentum"
        return "Low Liquidity"

    if latest_close is not None and latest_close < 300:
        return "Watch: Low Price"

    if (
        (ret_1d is not None and ret_1d >= 20)
        or (ret_5d is not None and ret_5d >= 40)
        or (ret_20d is not None and ret_20d >= 80)
    ):
        if score >= 75:
            return "Extended Momentum"
        return "Extended"

    if score >= 85:
        return "A+ Breakout"

    if score >= 75:
        if "near_52w_high" in flags and "volume_expansion" in flags:
            return "A Breakout"
        return "A Momentum"

    if score >= 65:
        return "B+ Momentum"

    if score >= 55:
        return "B Watch"

    if score >= 45:
        return "C Watch"

    return "No Signal"


def risk_level(item: dict[str, Any], score: float, flags: list[str]) -> str:
    metrics = item.get("metrics") or {}
    avg_value_20d = as_float(metrics.get("avg_traded_value_20d_jpy"))
    ret_5d = as_float(metrics.get("return_5d_pct"))
    ret_20d = as_float(metrics.get("return_20d_pct"))
    bucket = str(item.get("bucket") or "").strip().lower()

    if avg_value_20d is not None and avg_value_20d < 100_000_000:
        return "High"
    if bucket == "watch":
        return "High"
    if ret_5d is not None and ret_5d >= 40:
        return "High"
    if ret_20d is not None and ret_20d >= 80:
        return "High"
    if avg_value_20d is not None and avg_value_20d < 300_000_000:
        return "Medium"
    if score >= 80:
        return "Medium"
    return "Normal"


def build_market_pulse_item(item: dict[str, Any]) -> dict[str, Any]:
    metrics = item.get("metrics") or {}

    label = item.get("pulse_label") or item.get("symbol")

    ret_1d = as_float(metrics.get("return_1d_pct"))
    ret_5d = as_float(metrics.get("return_5d_pct"))
    ret_20d = as_float(metrics.get("return_20d_pct"))
    ret_60d = as_float(metrics.get("return_60d_pct"))

    if ret_20d is not None and ret_20d >= 5:
        regime = "Risk-On"
    elif ret_20d is not None and ret_20d <= -5:
        regime = "Risk-Off"
    elif ret_5d is not None and ret_5d >= 2:
        regime = "Improving"
    elif ret_5d is not None and ret_5d <= -2:
        regime = "Weakening"
    else:
        regime = "Neutral"

    pulse_score = (
        scale_linear(ret_5d, -5, 5) * 35
        + scale_linear(ret_20d, -10, 10) * 45
        + scale_linear(ret_60d, -20, 20) * 20
    )

    return {
        "symbol": item.get("symbol"),
        "label": label,
        "name": item.get("name"),
        "source": item.get("source"),
        "latest_date": metrics.get("latest_date"),
        "latest_close": metrics.get("latest_close"),
        "return_1d_pct": ret_1d,
        "return_5d_pct": ret_5d,
        "return_20d_pct": ret_20d,
        "return_60d_pct": ret_60d,
        "regime": regime,
        "pulse_score_0_100": round(pulse_score, 2),
    }


def score_equity_item(
    item: dict[str, Any],
    topix_metrics: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = item.get("metrics") or {}

    component_flags: list[str] = []

    volume_score, volume_flags = score_volume_shock(metrics)
    breakout_score, breakout_flags = score_breakout_quality(metrics)
    rs_score, rs_flags, relative_metrics = score_relative_strength(metrics, topix_metrics)
    compression_score, compression_flags = score_compression(metrics)
    entry_score, entry_flags = score_entry_timing(metrics)
    penalty_score, penalty_flags = compute_penalty(item)

    component_flags.extend(volume_flags)
    component_flags.extend(breakout_flags)
    component_flags.extend(rs_flags)
    component_flags.extend(compression_flags)
    component_flags.extend(entry_flags)
    component_flags.extend(penalty_flags)

    raw_score = (
        volume_score
        + breakout_score
        + rs_score
        + compression_score
        + entry_score
        + penalty_score
    )

    final_score = clamp(raw_score, 0.0, 100.0)

    # De-duplicate flags while preserving order.
    seen: set[str] = set()
    flags = []
    for flag in component_flags:
        if flag not in seen:
            seen.add(flag)
            flags.append(flag)

    classification = classify_signal(final_score, item, flags)

    components = {
        "volume_shock": round(volume_score, 4),
        "breakout_quality": round(breakout_score, 4),
        "relative_strength": round(rs_score, 4),
        "compression": round(compression_score, 4),
        "entry_timing": round(entry_score, 4),
        "penalty": round(penalty_score, 4),
        "raw_score": round(raw_score, 4),
    }

    latest_close = as_float(metrics.get("latest_close"))
    avg_value_20d = as_float(metrics.get("avg_traded_value_20d_jpy"))

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
        "latest_date": metrics.get("latest_date"),
        "latest_close": metrics.get("latest_close"),
        "latest_volume": metrics.get("latest_volume"),
        "latest_traded_value_jpy": metrics.get("latest_traded_value_jpy"),
        "avg_traded_value_20d_jpy": metrics.get("avg_traded_value_20d_jpy"),
        "return_1d_pct": metrics.get("return_1d_pct"),
        "return_5d_pct": metrics.get("return_5d_pct"),
        "return_20d_pct": metrics.get("return_20d_pct"),
        "return_60d_pct": metrics.get("return_60d_pct"),
        "return_120d_pct": metrics.get("return_120d_pct"),
        "volume_ratio_20d": metrics.get("volume_ratio_20d"),
        "distance_from_20d_high_pct": metrics.get("distance_from_20d_high_pct"),
        "distance_from_52w_high_pct": metrics.get("distance_from_52w_high_pct"),
        "range_position_20d_0_1": metrics.get("range_position_20d_0_1"),
        "compression_20d_pct": metrics.get("compression_20d_pct"),
        "volatility_20d_annualized_pct": metrics.get("volatility_20d_annualized_pct"),
        "liquidity_status": metrics.get("liquidity_status"),
        "liquidity_flags": metrics.get("liquidity_flags") or [],
        "risk_level": risk_level(item, final_score, flags),
        "score": round(final_score, 2),
        "score_0_1": round(final_score / 100.0, 4),
        "classification": classification,
        "components": components,
        "relative_metrics": relative_metrics,
        "flags": flags,
        "is_partial": bool(item.get("is_partial")),
        "bars_count": item.get("bars_count"),
        "date_start": item.get("date_start"),
        "date_end": item.get("date_end"),
        "warnings": item.get("warnings") or [],
        "source_errors": item.get("source_errors") or [],
        "debug": {
            "latest_close_float": latest_close,
            "avg_value_20d_float": avg_value_20d,
        },
    }


def sort_ranked_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(x: dict[str, Any]) -> tuple:
        score = as_float(x.get("score")) or 0.0

        bucket = str(x.get("bucket") or "").lower()
        bucket_order = {
            "core": 0,
            "discovery": 1,
            "watch": 2,
        }.get(bucket, 3)

        risk = str(x.get("risk_level") or "").lower()
        risk_order = {
            "normal": 0,
            "medium": 1,
            "high": 2,
        }.get(risk, 3)

        avg_value = as_float(x.get("avg_traded_value_20d_jpy")) or 0.0

        return (-score, bucket_order, risk_order, -avg_value, str(x.get("symbol") or ""))

    ranked = sorted(items, key=sort_key)

    for i, item in enumerate(ranked, start=1):
        item["rank"] = i

    return ranked


def summarize_output(items: list[dict[str, Any]]) -> dict[str, Any]:
    by_classification: dict[str, int] = {}
    by_bucket: dict[str, int] = {}
    by_risk: dict[str, int] = {}

    for item in items:
        classification = str(item.get("classification") or "Unknown")
        bucket = str(item.get("bucket") or "Unknown")
        risk = str(item.get("risk_level") or "Unknown")

        by_classification[classification] = by_classification.get(classification, 0) + 1
        by_bucket[bucket] = by_bucket.get(bucket, 0) + 1
        by_risk[risk] = by_risk.get(risk, 0) + 1

    top = items[0] if items else {}

    return {
        "items_count": len(items),
        "top_symbol": top.get("symbol"),
        "top_name": top.get("name"),
        "top_score": top.get("score"),
        "top_classification": top.get("classification"),
        "by_classification": by_classification,
        "by_bucket": by_bucket,
        "by_risk": by_risk,
    }


def main() -> int:
    generated_at = iso_now()
    today = now_jst().date().isoformat()

    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"PRICES_JSON={safe_relative(PRICES_JSON)}")
    print(f"DAILY_OUT_DIR={safe_relative(DAILY_OUT_DIR)}")

    prices_payload = read_json(PRICES_JSON)

    if prices_payload.get("schema_version") != "prices-jp-v1":
        raise ValueError(
            f"Unexpected prices schema_version: {prices_payload.get('schema_version')}"
        )

    market_pulse_raw = prices_payload.get("market_pulse") or []
    equities_raw = prices_payload.get("equities") or []

    if not isinstance(market_pulse_raw, list):
        raise TypeError("prices market_pulse must be a list")
    if not isinstance(equities_raw, list):
        raise TypeError("prices equities must be a list")

    market_pulse = [build_market_pulse_item(x) for x in market_pulse_raw]

    topix_item = None
    for item in market_pulse_raw:
        if item.get("pulse_label") == "TOPIX" or item.get("symbol") == "1306.T":
            topix_item = item
            break

    topix_metrics = (topix_item or {}).get("metrics") if topix_item else None

    scored_items = [
        score_equity_item(item, topix_metrics)
        for item in equities_raw
        if item.get("asset_type") == "equity"
    ]

    ranked_items = sort_ranked_items(scored_items)

    summary = summarize_output(ranked_items)

    payload = {
        "schema_version": "daily-jp-v1",
        "generated_at": generated_at,
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "source_prices": safe_relative(PRICES_JSON),
        "source_prices_generated_at": prices_payload.get("generated_at"),
        "weights": WEIGHTS,
        "score_notes": {
            "max_raw_score_before_penalty": MAX_RAW_SCORE,
            "score_floor": 0,
            "score_cap": 100,
            "liquidity_rule": "Low liquidity is penalized, not fully excluded, to preserve Discovery visibility.",
            "not_included_yet": [
                "news",
                "earnings",
                "timely_disclosure",
                "fundamentals",
                "short_interest",
                "credit_margin_data",
            ],
        },
        "market_pulse": market_pulse,
        "items": ranked_items,
        "summary": summary,
    }

    DAILY_OUT_DIR.mkdir(parents=True, exist_ok=True)

    latest_path = DAILY_OUT_DIR / "latest.json"
    dated_path = DAILY_OUT_DIR / f"{today}.json"

    write_json(latest_path, payload)
    write_json(dated_path, payload)

    manifest = {
        "schema_version": "daily-jp-manifest-v1",
        "generated_at": generated_at,
        "latest": safe_relative(latest_path),
        "latest_date": today,
        "history": [
            {
                "date": today,
                "path": safe_relative(dated_path),
                "items_count": len(ranked_items),
                "top_symbol": summary.get("top_symbol"),
                "top_score": summary.get("top_score"),
                "top_classification": summary.get("top_classification"),
            }
        ],
    }

    manifest_path = DAILY_OUT_DIR / "manifest.json"
    write_json(manifest_path, manifest)

    print(f"Wrote {safe_relative(latest_path)}")
    print(f"Wrote {safe_relative(dated_path)}")
    print(f"Wrote {safe_relative(manifest_path)}")
    print(f"Items={len(ranked_items)}")
    print(
        f"Top={summary.get('top_symbol')} "
        f"score={summary.get('top_score')} "
        f"classification={summary.get('top_classification')}"
    )

    if not ranked_items:
        print("No ranked items generated. Failing workflow.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
