#!/usr/bin/env python3
"""
Backtest Neon Tokyo Daily JP signals.

This script does NOT call external APIs.
It reads historical OHLCV bars from:
- site/data/prices-jp/latest.json

It replays past dates, truncates bars to each evaluation date,
runs the same scoring logic as build_daily_jp.py v2, then measures
future returns over configurable horizons.

Modes:
- incremental:
    Add newly matured evaluation dates only.
    Useful for scheduled daily updates.

- range:
    Rebuild a manually specified evaluation date range.
    Useful for deeper historical refresh / parameter validation.

Outputs:
- site/data/backtest-daily-jp/latest.json
- site/data/backtest-daily-jp/manifest.json
- site/data/backtest-daily-jp/YYYY-MM-DD.json
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_daily_jp as scorer  # noqa: E402


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

BACKTEST_OUT_DIR = OUT_DIR / "data" / "backtest-daily-jp"

MODE = os.getenv("BACKTEST_MODE", "incremental").strip().lower()
BACKTEST_START = os.getenv("BACKTEST_START", "").strip()
BACKTEST_END = os.getenv("BACKTEST_END", "").strip()

HORIZONS = sorted({
    int(x.strip())
    for x in os.getenv("BACKTEST_HORIZONS", "1,3,5,10,20").split(",")
    if x.strip()
})

DAILY_PRIMARY_HORIZON = int(os.getenv("BACKTEST_PRIMARY_HORIZON", "5"))
DAILY_CORE_HORIZONS = sorted({
    int(x.strip())
    for x in os.getenv("BACKTEST_CORE_HORIZONS", "1,3,5,10").split(",")
    if x.strip()
})
DAILY_REFERENCE_HORIZONS = sorted({
    int(x.strip())
    for x in os.getenv("BACKTEST_REFERENCE_HORIZONS", "20").split(",")
    if x.strip()
})

if DAILY_PRIMARY_HORIZON not in HORIZONS:
    HORIZONS = sorted(set(HORIZONS + [DAILY_PRIMARY_HORIZON]))

MIN_HISTORY_BARS = int(os.getenv("BACKTEST_MIN_HISTORY_BARS", "80"))
RANK_LIMIT = int(os.getenv("BACKTEST_RANK_LIMIT", "50"))
MAX_EVAL_DATES_INCREMENTAL = int(os.getenv("BACKTEST_MAX_EVAL_DATES", "5"))

TZ = ZoneInfo("Asia/Tokyo")


def available_horizons(candidates: list[int] | tuple[int, ...] | set[int]) -> list[int]:
    return [h for h in sorted({int(x) for x in candidates}) if h in HORIZONS]


def primary_horizon() -> int:
    if DAILY_PRIMARY_HORIZON in HORIZONS:
        return DAILY_PRIMARY_HORIZON
    core = available_horizons(DAILY_CORE_HORIZONS)
    if core:
        return max(core)
    return max(HORIZONS)


def primary_horizon_key() -> str:
    return f"{primary_horizon()}d"


def core_horizon_keys() -> list[str]:
    core = available_horizons(DAILY_CORE_HORIZONS)
    return [f"{h}d" for h in core]


def reference_horizon_keys() -> list[str]:
    refs = available_horizons(DAILY_REFERENCE_HORIZONS)
    return [f"{h}d" for h in refs]


def horizon_role(h: int) -> str:
    if h == primary_horizon():
        return "primary"
    if h in set(DAILY_CORE_HORIZONS):
        return "core"
    if h in set(DAILY_REFERENCE_HORIZONS):
        return "reference"
    return "secondary"


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
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
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


def safe_round(value: Any, digits: int = 4) -> float | None:
    v = to_float(value)
    if v is None:
        return None
    return round(v, digits)


def parse_date(value: str) -> pd.Timestamp | None:
    if not value:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return pd.Timestamp(ts).normalize()


def date_str(ts: pd.Timestamp) -> str:
    return pd.Timestamp(ts).date().isoformat()


def bars_to_df(item: dict[str, Any]) -> pd.DataFrame:
    return scorer.bars_to_df(item)


def truncate_item_to_date(item: dict[str, Any], eval_date: str) -> dict[str, Any]:
    cloned = deepcopy(item)
    bars = cloned.get("bars") or []
    cloned["bars"] = [
        bar for bar in bars
        if isinstance(bar, dict) and str(bar.get("date", "")) <= eval_date
    ]
    return cloned


def item_has_exact_date(item: dict[str, Any], eval_date: str) -> bool:
    bars = item.get("bars") or []
    return any(isinstance(bar, dict) and bar.get("date") == eval_date for bar in bars)


def get_entry_and_future_returns(
    full_df: pd.DataFrame,
    eval_date: str,
    horizons: list[int],
) -> dict[str, Any]:
    if full_df.empty:
        return {
            "valid": False,
            "reason": "empty_df",
            "entry_close": None,
            "returns": {},
            "worst_pullback": {},
        }

    eval_ts = pd.Timestamp(eval_date)

    if eval_ts not in full_df.index:
        return {
            "valid": False,
            "reason": "missing_eval_date",
            "entry_close": None,
            "returns": {},
            "worst_pullback": {},
        }

    idx = full_df.index.get_loc(eval_ts)
    if isinstance(idx, slice) or isinstance(idx, np.ndarray):
        return {
            "valid": False,
            "reason": "ambiguous_eval_date",
            "entry_close": None,
            "returns": {},
            "worst_pullback": {},
        }

    entry_close = to_float(full_df.iloc[idx]["Close"])
    if entry_close is None or entry_close <= 0:
        return {
            "valid": False,
            "reason": "invalid_entry_close",
            "entry_close": None,
            "returns": {},
            "worst_pullback": {},
        }

    returns: dict[str, float | None] = {}
    worst_pullback: dict[str, float | None] = {}

    for h in horizons:
        key = f"{h}d"
        future_idx = idx + h

        if future_idx >= len(full_df):
            returns[key] = None
            worst_pullback[key] = None
            continue

        future_close = to_float(full_df.iloc[future_idx]["Close"])
        if future_close is None or future_close <= 0:
            returns[key] = None
        else:
            returns[key] = (future_close / entry_close - 1.0) * 100.0

        window = full_df.iloc[idx + 1: future_idx + 1]
        if window.empty:
            worst_pullback[key] = None
        else:
            min_low = to_float(window["Low"].min())
            if min_low is None or min_low <= 0:
                worst_pullback[key] = None
            else:
                worst_pullback[key] = (min_low / entry_close - 1.0) * 100.0

    return {
        "valid": True,
        "reason": None,
        "entry_close": entry_close,
        "returns": returns,
        "worst_pullback": worst_pullback,
    }


def find_topix_item(market_pulse_raw: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in market_pulse_raw:
        if item.get("pulse_label") == "TOPIX" or item.get("symbol") == "1306.T":
            return item
    return None


def get_topix_df(market_pulse_raw: list[dict[str, Any]]) -> pd.DataFrame:
    item = find_topix_item(market_pulse_raw)
    if not item:
        return pd.DataFrame()
    return bars_to_df(item)


def eligible_eval_dates_from_topix(
    topix_df: pd.DataFrame,
    start: str,
    end: str,
    max_horizon: int,
) -> list[str]:
    if topix_df.empty:
        return []

    idx = topix_df.index.sort_values()
    start_ts = parse_date(start) if start else None
    end_ts = parse_date(end) if end else None

    eligible: list[str] = []
    last_allowed_pos = len(idx) - max_horizon - 1

    if last_allowed_pos < 0:
        return []

    for pos, ts in enumerate(idx):
        if pos < MIN_HISTORY_BARS:
            continue
        if pos > last_allowed_pos:
            continue
        if start_ts is not None and ts < start_ts:
            continue
        if end_ts is not None and ts > end_ts:
            continue
        eligible.append(date_str(ts))

    return eligible


def load_existing_latest() -> dict[str, Any] | None:
    latest_path = BACKTEST_OUT_DIR / "latest.json"
    if not latest_path.exists():
        return None
    try:
        return read_json(latest_path)
    except Exception:
        return None


def existing_eval_dates(existing: dict[str, Any] | None) -> set[str]:
    if not existing:
        return set()
    items = existing.get("items") or []
    return {
        str(item.get("eval_date"))
        for item in items
        if isinstance(item, dict) and item.get("eval_date")
    }


def select_eval_dates(prices_payload: dict[str, Any], topix_df: pd.DataFrame) -> list[str]:
    max_horizon = max(HORIZONS)

    all_eligible = eligible_eval_dates_from_topix(
        topix_df=topix_df,
        start=BACKTEST_START,
        end=BACKTEST_END,
        max_horizon=max_horizon,
    )

    if MODE == "range":
        return all_eligible

    if MODE != "incremental":
        raise ValueError(f"Unsupported BACKTEST_MODE: {MODE}")

    existing = load_existing_latest()
    done = existing_eval_dates(existing)

    missing = [d for d in all_eligible if d not in done]

    # For daily scheduled update, process only the latest matured dates.
    return missing[-MAX_EVAL_DATES_INCREMENTAL:]


def score_date(
    eval_date: str,
    market_pulse_raw: list[dict[str, Any]],
    equities_raw: list[dict[str, Any]],
    topix_full_df: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    truncated_pulse = [
        truncate_item_to_date(item, eval_date)
        for item in market_pulse_raw
    ]

    regime, regime_score, regime_state = scorer.market_regime_from_pulse(truncated_pulse)
    topix_last = scorer.find_topix_last(truncated_pulse)

    scored_items: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    topix_future = get_entry_and_future_returns(topix_full_df, eval_date, HORIZONS)
    topix_returns = topix_future.get("returns") or {}

    for item in equities_raw:
        symbol = item.get("symbol")
        name = item.get("name")

        if item.get("asset_type") != "equity":
            continue

        if not item_has_exact_date(item, eval_date):
            failures.append(
                {
                    "eval_date": eval_date,
                    "symbol": symbol,
                    "name": name,
                    "reason": "missing_eval_bar",
                }
            )
            continue

        full_df = bars_to_df(item)
        if full_df.empty or len(full_df) < MIN_HISTORY_BARS:
            failures.append(
                {
                    "eval_date": eval_date,
                    "symbol": symbol,
                    "name": name,
                    "reason": "insufficient_history",
                    "bars": int(len(full_df)),
                }
            )
            continue

        future = get_entry_and_future_returns(full_df, eval_date, HORIZONS)
        if not future.get("valid"):
            failures.append(
                {
                    "eval_date": eval_date,
                    "symbol": symbol,
                    "name": name,
                    "reason": future.get("reason"),
                }
            )
            continue

        truncated_item = truncate_item_to_date(item, eval_date)

        try:
            scored = scorer.score_equity_item(
                item=truncated_item,
                topix_last=topix_last,
                regime=regime,
                regime_score=regime_score,
            )
        except Exception as exc:
            failures.append(
                {
                    "eval_date": eval_date,
                    "symbol": symbol,
                    "name": name,
                    "reason": f"score_exception:{type(exc).__name__}",
                    "message": str(exc),
                }
            )
            continue

        if scored is None:
            failures.append(
                {
                    "eval_date": eval_date,
                    "symbol": symbol,
                    "name": name,
                    "reason": "scored_none",
                }
            )
            continue

        future_returns = future.get("returns") or {}
        worst_pullback = future.get("worst_pullback") or {}

        alpha_vs_topix: dict[str, float | None] = {}
        for h in HORIZONS:
            key = f"{h}d"
            r = to_float(future_returns.get(key))
            tr = to_float(topix_returns.get(key))
            alpha_vs_topix[key] = None if r is None or tr is None else r - tr

        avg_value = to_float(scored.get("avg_traded_value_20d_jpy"))
        if avg_value is None:
            liquidity_band = "Unknown"
        elif avg_value >= 1_000_000_000:
            liquidity_band = "High Liquidity"
        elif avg_value >= 300_000_000:
            liquidity_band = "Liquid"
        elif avg_value >= 100_000_000:
            liquidity_band = "Thin"
        else:
            liquidity_band = "Very Thin"

        score_pts = to_float(scored.get("score_pts")) or 0.0
        if score_pts >= 800:
            score_band = "800+"
        elif score_pts >= 700:
            score_band = "700-799"
        elif score_pts >= 600:
            score_band = "600-699"
        elif score_pts >= 500:
            score_band = "500-599"
        else:
            score_band = "<500"

        row = {
            "eval_date": eval_date,
            "symbol": scored.get("symbol"),
            "name": scored.get("name"),
            "theme": scored.get("theme"),
            "bucket": scored.get("bucket"),
            "priority": scored.get("priority"),
            "rank": None,
            "score": scored.get("score"),
            "score_pts": scored.get("score_pts"),
            "score_band": score_band,
            "triage": scored.get("triage"),
            "classification": scored.get("classification"),
            "archetype": scored.get("archetype"),
            "risk_level": scored.get("risk_level"),
            "regime": regime,
            "reason": scored.get("reason"),
            "flags": scored.get("flags") or [],
            "liquidity_band": liquidity_band,
            "latest_close": scored.get("latest_close"),
            "entry_close": safe_round(future.get("entry_close"), 4),
            "avg_traded_value_20d_jpy": scored.get("avg_traded_value_20d_jpy"),
            "volume_ratio_20d": scored.get("volume_ratio_20d"),
            "return_1d_pct": scored.get("return_1d_pct"),
            "return_5d_pct": scored.get("return_5d_pct"),
            "return_20d_pct": scored.get("return_20d_pct"),
            "distance_from_52w_high_pct": scored.get("distance_from_52w_high_pct"),
            "v2_components": scored.get("v2_components") or {},
            "penalty_details": scored.get("penalty_details") or {},
            "future_returns_pct": {
                k: safe_round(v, 4) for k, v in future_returns.items()
            },
            "alpha_vs_topix_pct": {
                k: safe_round(v, 4) for k, v in alpha_vs_topix.items()
            },
            "worst_pullback_pct": {
                k: safe_round(v, 4) for k, v in worst_pullback.items()
            },
        }

        scored_items.append(row)

    ranked = scorer.sort_ranked_items(scored_items)

    # Keep rank stable for the eval date.
    for i, row in enumerate(ranked, start=1):
        row["rank"] = i

    if RANK_LIMIT > 0:
        ranked = ranked[:RANK_LIMIT]

    date_state = {
        "eval_date": eval_date,
        "regime": regime,
        "regime_score": safe_round(regime_score, 6),
        "regime_state": regime_state,
        "topix_future_returns_pct": {
            k: safe_round(v, 4) for k, v in topix_returns.items()
        },
        "scored_count": len(ranked),
        "failure_count": len(failures),
    }

    return ranked, failures, date_state


def finite_values(values: list[Any]) -> list[float]:
    out: list[float] = []
    for v in values:
        f = to_float(v)
        if f is not None:
            out.append(f)
    return out


def stats_for_values(rows: list[dict[str, Any]], horizon_key: str) -> dict[str, Any]:
    returns = finite_values([
        (row.get("future_returns_pct") or {}).get(horizon_key)
        for row in rows
    ])
    alphas = finite_values([
        (row.get("alpha_vs_topix_pct") or {}).get(horizon_key)
        for row in rows
    ])
    pullbacks = finite_values([
        (row.get("worst_pullback_pct") or {}).get(horizon_key)
        for row in rows
    ])
    scores = finite_values([row.get("score_pts") for row in rows])

    if not returns:
        return {
            "count": 0,
            "avg_return_pct": None,
            "median_return_pct": None,
            "win_rate_pct": None,
            "avg_alpha_pct": None,
            "median_alpha_pct": None,
            "positive_alpha_rate_pct": None,
            "avg_worst_pullback_pct": None,
            "avg_score_pts": None,
        }

    return {
        "count": len(returns),
        "avg_return_pct": safe_round(np.mean(returns), 4),
        "median_return_pct": safe_round(np.median(returns), 4),
        "win_rate_pct": safe_round(sum(1 for x in returns if x > 0) / len(returns) * 100.0, 2),
        "avg_alpha_pct": safe_round(np.mean(alphas), 4) if alphas else None,
        "median_alpha_pct": safe_round(np.median(alphas), 4) if alphas else None,
        "positive_alpha_rate_pct": safe_round(sum(1 for x in alphas if x > 0) / len(alphas) * 100.0, 2) if alphas else None,
        "avg_worst_pullback_pct": safe_round(np.mean(pullbacks), 4) if pullbacks else None,
        "avg_score_pts": safe_round(np.mean(scores), 2) if scores else None,
    }


def group_summary(rows: list[dict[str, Any]], group_field: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        key = str(row.get(group_field) or "Unknown")
        grouped[key].append(row)

    out: dict[str, Any] = {}

    for key, group_rows in sorted(grouped.items()):
        out[key] = {
            f"{h}d": stats_for_values(group_rows, f"{h}d")
            for h in HORIZONS
        }

    return out



# -----------------------------------------------------------------------------
# Professional diagnostic layer
# -----------------------------------------------------------------------------

def metric_value(row: dict[str, Any], metric_family: str, horizon_key: str) -> float | None:
    container = row.get(metric_family) or {}
    if not isinstance(container, dict):
        return None
    return to_float(container.get(horizon_key))


def rows_with_metric(rows: list[dict[str, Any]], metric_family: str, horizon_key: str) -> list[dict[str, Any]]:
    return [row for row in rows if metric_value(row, metric_family, horizon_key) is not None]


def percentile(values: list[float], q: float) -> float | None:
    vals = finite_values(values)
    if not vals:
        return None
    return float(np.percentile(vals, q))


def winsorized_mean(values: list[float], lower_pct: float = 1.0, upper_pct: float = 99.0) -> float | None:
    vals = finite_values(values)
    if not vals:
        return None
    if len(vals) < 20:
        return float(np.mean(vals))
    lo = np.percentile(vals, lower_pct)
    hi = np.percentile(vals, upper_pct)
    clipped = np.clip(vals, lo, hi)
    return float(np.mean(clipped))


def avg_excluding_top_pct(values: list[float], pct: float = 1.0) -> float | None:
    vals = finite_values(values)
    if not vals:
        return None
    if len(vals) < 100:
        return float(np.mean(vals))
    cutoff = np.percentile(vals, 100.0 - pct)
    trimmed = [v for v in vals if v < cutoff]
    if not trimmed:
        return None
    return float(np.mean(trimmed))


def enhanced_stats_for_rows(rows: list[dict[str, Any]], horizon_key: str) -> dict[str, Any]:
    base = stats_for_values(rows, horizon_key)

    returns = finite_values([
        (row.get("future_returns_pct") or {}).get(horizon_key)
        for row in rows
    ])
    alphas = finite_values([
        (row.get("alpha_vs_topix_pct") or {}).get(horizon_key)
        for row in rows
    ])

    if not returns:
        base.update(
            {
                "median_average_gap_pct": None,
                "return_stddev_pct": None,
                "p10_return_pct": None,
                "p90_return_pct": None,
                "p95_return_pct": None,
                "p99_return_pct": None,
                "max_return_pct": None,
                "min_return_pct": None,
                "winsorized_avg_return_pct": None,
                "avg_return_ex_top_1pct_pct": None,
                "top_positive_contribution_pct": None,
            }
        )
        return base

    avg_return = to_float(base.get("avg_return_pct"))
    median_return = to_float(base.get("median_return_pct"))
    avg_alpha = to_float(base.get("avg_alpha_pct"))
    median_alpha = to_float(base.get("median_alpha_pct"))

    positive_returns = [max(v, 0.0) for v in returns]
    positive_sum = float(sum(positive_returns))
    top_positive = max(positive_returns) if positive_returns else 0.0

    base.update(
        {
            "median_average_gap_pct": safe_round(None if avg_return is None or median_return is None else avg_return - median_return, 4),
            "alpha_median_average_gap_pct": safe_round(None if avg_alpha is None or median_alpha is None else avg_alpha - median_alpha, 4),
            "return_stddev_pct": safe_round(np.std(returns, ddof=0), 4),
            "p10_return_pct": safe_round(percentile(returns, 10), 4),
            "p90_return_pct": safe_round(percentile(returns, 90), 4),
            "p95_return_pct": safe_round(percentile(returns, 95), 4),
            "p99_return_pct": safe_round(percentile(returns, 99), 4),
            "max_return_pct": safe_round(max(returns), 4),
            "min_return_pct": safe_round(min(returns), 4),
            "winsorized_avg_return_pct": safe_round(winsorized_mean(returns), 4),
            "avg_return_ex_top_1pct_pct": safe_round(avg_excluding_top_pct(returns, 1.0), 4),
            "top_positive_contribution_pct": safe_round((top_positive / positive_sum * 100.0) if positive_sum > 0 else None, 2),
        }
    )
    return base


def build_performance_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        f"{h}d": enhanced_stats_for_rows(rows, f"{h}d")
        for h in HORIZONS
    }


def filter_rows_by_horizon_excluding_top_pct(
    rows: list[dict[str, Any]],
    horizon_key: str,
    pct: float = 1.0,
) -> list[dict[str, Any]]:
    valid_rows = rows_with_metric(rows, "future_returns_pct", horizon_key)
    if len(valid_rows) < 100:
        return valid_rows
    values = [metric_value(row, "future_returns_pct", horizon_key) for row in valid_rows]
    vals = finite_values(values)
    cutoff = np.percentile(vals, 100.0 - pct)
    return [
        row for row in valid_rows
        if (metric_value(row, "future_returns_pct", horizon_key) is not None
            and metric_value(row, "future_returns_pct", horizon_key) < cutoff)
    ]


def build_filtered_performance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    liquidity_ok = {"High Liquidity", "Liquid"}
    filters: list[tuple[str, str, list[dict[str, Any]]]] = [
        ("rank_lte_10", "Rank <= 10", [r for r in rows if (to_float(r.get("rank")) or 999999) <= 10]),
        ("rank_lte_20", "Rank <= 20", [r for r in rows if (to_float(r.get("rank")) or 999999) <= 20]),
        ("trade_only", "Trade only", [r for r in rows if str(r.get("triage") or "") == "Trade"]),
        ("watch_only", "Watch only", [r for r in rows if str(r.get("triage") or "") == "Watch"]),
        ("trade_plus_watch", "Trade + Watch", [r for r in rows if str(r.get("triage") or "") in {"Trade", "Watch"}]),
        ("score_gte_500", "Score >= 500", [r for r in rows if (to_float(r.get("score_pts")) or 0) >= 500]),
        ("score_gte_600", "Score >= 600", [r for r in rows if (to_float(r.get("score_pts")) or 0) >= 600]),
        ("score_gte_700", "Score >= 700", [r for r in rows if (to_float(r.get("score_pts")) or 0) >= 700]),
        ("liquidity_gte_liquid", "Liquidity >= Liquid", [r for r in rows if str(r.get("liquidity_band") or "") in liquidity_ok]),
    ]

    out: dict[str, Any] = {}
    for key, label, subset in filters:
        out[key] = {
            "label": label,
            "description": "Predefined diagnostic filter. No display-layer recalculation is required.",
            "stats": build_performance_block(subset),
        }

    out["excluding_top_1pct_outliers"] = {
        "label": "Excluding top 1% return outliers",
        "description": "Horizon-specific removal of the top 1% realized return observations. If sample < 100, no trim is applied.",
        "stats": {
            f"{h}d": enhanced_stats_for_rows(
                filter_rows_by_horizon_excluding_top_pct(rows, f"{h}d", 1.0),
                f"{h}d",
            )
            for h in HORIZONS
        },
    }

    out["winsorized_average"] = {
        "label": "Winsorized average check",
        "description": "The avg_return field is unchanged; winsorized_avg_return_pct is added inside each horizon stat.",
        "stats": build_performance_block(rows),
    }

    return out


def build_rank_bucket_performance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {
        "rank_1_5": ("Rank 1-5", lambda r: 1 <= (to_float(r.get("rank")) or 999999) <= 5),
        "rank_1_10": ("Rank 1-10", lambda r: 1 <= (to_float(r.get("rank")) or 999999) <= 10),
        "rank_11_20": ("Rank 11-20", lambda r: 11 <= (to_float(r.get("rank")) or 999999) <= 20),
        "rank_21_50": ("Rank 21-50", lambda r: 21 <= (to_float(r.get("rank")) or 999999) <= 50),
    }
    return {
        key: {
            "label": label,
            "stats": build_performance_block([row for row in rows if pred(row)]),
        }
        for key, (label, pred) in buckets.items()
    }


def build_outlier_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary_key = primary_horizon_key()
    valid = rows_with_metric(rows, "future_returns_pct", primary_key)

    ranked = sorted(
        valid,
        key=lambda r: metric_value(r, "future_returns_pct", primary_key) or -999999,
        reverse=True,
    )

    returns = finite_values([metric_value(r, "future_returns_pct", primary_key) for r in valid])
    positive_total = float(sum(max(x, 0.0) for x in returns))

    def outlier_row(row: dict[str, Any]) -> dict[str, Any]:
        ret = metric_value(row, "future_returns_pct", primary_key)
        alpha = metric_value(row, "alpha_vs_topix_pct", primary_key)
        contribution = None
        if ret is not None and ret > 0 and positive_total > 0:
            contribution = ret / positive_total * 100.0
        return {
            "eval_date": row.get("eval_date"),
            "symbol": row.get("symbol"),
            "name": row.get("name"),
            "rank": row.get("rank"),
            "triage": row.get("triage"),
            "score_pts": row.get("score_pts"),
            "score_band": row.get("score_band"),
            "liquidity_band": row.get("liquidity_band"),
            "archetype": row.get("archetype"),
            "return_pct": safe_round(ret, 4),
            "alpha_pct": safe_round(alpha, 4),
            "positive_return_contribution_pct": safe_round(contribution, 2),
        }

    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in valid:
        by_symbol[str(row.get("symbol") or "Unknown")].append(row)

    symbol_contribs: list[dict[str, Any]] = []
    for symbol, symbol_rows in by_symbol.items():
        symbol_returns = finite_values([metric_value(r, "future_returns_pct", primary_key) for r in symbol_rows])
        pos = float(sum(max(x, 0.0) for x in symbol_returns))
        sample = symbol_rows[0] if symbol_rows else {}
        symbol_contribs.append(
            {
                "symbol": symbol,
                "name": sample.get("name"),
                "observations": len(symbol_rows),
                "avg_return_pct": safe_round(np.mean(symbol_returns), 4) if symbol_returns else None,
                "median_return_pct": safe_round(np.median(symbol_returns), 4) if symbol_returns else None,
                "max_return_pct": safe_round(max(symbol_returns), 4) if symbol_returns else None,
                "positive_return_contribution_pct": safe_round(pos / positive_total * 100.0, 2) if positive_total > 0 else None,
            }
        )

    symbol_contribs.sort(key=lambda x: to_float(x.get("positive_return_contribution_pct")) or -1, reverse=True)

    top_obs_contribution = to_float(outlier_row(ranked[0]).get("positive_return_contribution_pct")) if ranked else None
    top_symbol_contribution = to_float(symbol_contribs[0].get("positive_return_contribution_pct")) if symbol_contribs else None
    avg_ret = safe_round(np.mean(returns), 4) if returns else None
    med_ret = safe_round(np.median(returns), 4) if returns else None
    avg_minus_median = None if avg_ret is None or med_ret is None else avg_ret - med_ret

    warning = "OK"
    if (top_symbol_contribution is not None and top_symbol_contribution >= 20) or (avg_minus_median is not None and avg_minus_median >= 5):
        warning = "Warning"
    if (top_symbol_contribution is not None and top_symbol_contribution >= 35) or (avg_minus_median is not None and avg_minus_median >= 10):
        warning = "Fail"

    return {
        "primary_horizon": primary_key,
        "observation_count": len(valid),
        "avg_return_pct": avg_ret,
        "median_return_pct": med_ret,
        "median_average_gap_pct": safe_round(avg_minus_median, 4),
        "positive_return_pool_pct_points": safe_round(positive_total, 4),
        "top_observation_contribution_pct": safe_round(top_obs_contribution, 2),
        "top_symbol_contribution_pct": safe_round(top_symbol_contribution, 2),
        "average_return_distortion_warning": warning,
        "top_return_contributors": [outlier_row(r) for r in ranked[:20]],
        "top_symbol_contributors": symbol_contribs[:20],
    }


def build_repeated_symbol_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary_key = primary_horizon_key()
    valid = rows_with_metric(rows, "future_returns_pct", primary_key)

    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in valid:
        by_symbol[str(row.get("symbol") or "Unknown")].append(row)

    symbol_rows: list[dict[str, Any]] = []
    for symbol, group_rows in by_symbol.items():
        rets = finite_values([metric_value(r, "future_returns_pct", primary_key) for r in group_rows])
        alphas = finite_values([metric_value(r, "alpha_vs_topix_pct", primary_key) for r in group_rows])
        scores = finite_values([r.get("score_pts") for r in group_rows])
        triage_counts: dict[str, int] = defaultdict(int)
        for row in group_rows:
            triage_counts[str(row.get("triage") or "Unknown")] += 1
        sample = group_rows[0] if group_rows else {}
        symbol_rows.append(
            {
                "symbol": symbol,
                "name": sample.get("name"),
                "observations": len(group_rows),
                "eval_date_count": len({str(r.get("eval_date")) for r in group_rows if r.get("eval_date")}),
                "avg_return_pct": safe_round(np.mean(rets), 4) if rets else None,
                "median_return_pct": safe_round(np.median(rets), 4) if rets else None,
                "avg_alpha_pct": safe_round(np.mean(alphas), 4) if alphas else None,
                "median_alpha_pct": safe_round(np.median(alphas), 4) if alphas else None,
                "avg_score_pts": safe_round(np.mean(scores), 2) if scores else None,
                "triage_counts": dict(sorted(triage_counts.items())),
            }
        )

    symbol_rows.sort(key=lambda x: (int(x.get("observations") or 0), to_float(x.get("avg_return_pct")) or -999), reverse=True)

    obs_returns = finite_values([metric_value(r, "future_returns_pct", primary_key) for r in valid])
    sym_avg_returns = finite_values([r.get("avg_return_pct") for r in symbol_rows])
    total_obs = len(valid)
    max_obs = max([int(r.get("observations") or 0) for r in symbol_rows], default=0)

    return {
        "primary_horizon": primary_key,
        "symbol_count": len(symbol_rows),
        "observation_count": total_obs,
        "max_observations_single_symbol": max_obs,
        "max_symbol_observation_share_pct": safe_round(max_obs / total_obs * 100.0, 2) if total_obs else None,
        "observation_level_avg_return_pct": safe_round(np.mean(obs_returns), 4) if obs_returns else None,
        "equal_weight_symbol_avg_return_pct": safe_round(np.mean(sym_avg_returns), 4) if sym_avg_returns else None,
        "observation_vs_symbol_avg_gap_pct": safe_round(
            (np.mean(obs_returns) - np.mean(sym_avg_returns)) if obs_returns and sym_avg_returns else None,
            4,
        ),
        "most_repeated_symbols": symbol_rows[:25],
    }


def ordered_band_values(container: dict[str, Any], ordered_keys: list[str], horizon_key: str, metric: str) -> list[float | None]:
    values: list[float | None] = []
    for key in ordered_keys:
        stat = ((container.get(key) or {}).get(horizon_key) or {}) if isinstance(container.get(key) or {}, dict) else {}
        values.append(to_float(stat.get(metric)))
    return values


def monotonic_check(values: list[float | None], direction: str = "descending") -> dict[str, Any]:
    pairs = [(i, v) for i, v in enumerate(values) if v is not None]
    if len(pairs) < 2:
        return {"status": "Insufficient", "violations": 0, "pairs": len(pairs)}

    violations = 0
    comparisons = 0
    for (_, prev), (_, cur) in zip(pairs, pairs[1:]):
        comparisons += 1
        if direction == "descending":
            if prev < cur:
                violations += 1
        else:
            if prev > cur:
                violations += 1

    if violations == 0:
        status = "Pass"
    elif violations <= max(1, comparisons // 3):
        status = "Warning"
    else:
        status = "Fail"

    return {"status": status, "violations": violations, "comparisons": comparisons, "pairs": len(pairs)}


def build_model_diagnostics(summary: dict[str, Any], outlier_analysis: dict[str, Any]) -> dict[str, Any]:
    by_triage = summary.get("by_triage") or {}
    by_score_band = summary.get("by_score_band") or {}
    score_order = ["800+", "700-799", "600-699", "500-599", "<500"]
    core_keys = set(core_horizon_keys())
    reference_keys = set(reference_horizon_keys())

    horizon_checks: dict[str, Any] = {}
    for h in HORIZONS:
        hk = f"{h}d"
        trade = ((by_triage.get("Trade") or {}).get(hk) or {})
        watch = ((by_triage.get("Watch") or {}).get(hk) or {})
        ignore = ((by_triage.get("Ignore") or {}).get(hk) or {})

        trade_alpha = to_float(trade.get("avg_alpha_pct"))
        watch_alpha = to_float(watch.get("avg_alpha_pct"))
        ignore_alpha = to_float(ignore.get("avg_alpha_pct"))
        trade_median_alpha = to_float(trade.get("median_alpha_pct"))
        ignore_median_alpha = to_float(ignore.get("median_alpha_pct"))

        score_values = ordered_band_values(by_score_band, score_order, hk, "avg_alpha_pct")
        score_medians = ordered_band_values(by_score_band, score_order, hk, "median_alpha_pct")

        horizon_checks[hk] = {
            "role": horizon_role(h),
            "is_core_daily_horizon": hk in core_keys,
            "is_reference_horizon": hk in reference_keys,
            "trade_avg_alpha_pct": safe_round(trade_alpha, 4),
            "watch_avg_alpha_pct": safe_round(watch_alpha, 4),
            "ignore_avg_alpha_pct": safe_round(ignore_alpha, 4),
            "trade_minus_ignore_alpha_pct": safe_round(None if trade_alpha is None or ignore_alpha is None else trade_alpha - ignore_alpha, 4),
            "watch_minus_ignore_alpha_pct": safe_round(None if watch_alpha is None or ignore_alpha is None else watch_alpha - ignore_alpha, 4),
            "trade_minus_ignore_median_alpha_pct": safe_round(None if trade_median_alpha is None or ignore_median_alpha is None else trade_median_alpha - ignore_median_alpha, 4),
            "score_band_avg_alpha_values": dict(zip(score_order, [safe_round(v, 4) for v in score_values])),
            "score_band_median_alpha_values": dict(zip(score_order, [safe_round(v, 4) for v in score_medians])),
            "score_band_avg_alpha_monotonicity": monotonic_check(score_values, "descending"),
            "score_band_median_alpha_monotonicity": monotonic_check(score_medians, "descending"),
        }

    core_checks = {k: v for k, v in horizon_checks.items() if v.get("is_core_daily_horizon")}
    reference_checks = {k: v for k, v in horizon_checks.items() if v.get("is_reference_horizon")}

    def positive_count(container: dict[str, Any], field: str) -> int:
        return sum(
            1 for v in container.values()
            if (to_float(v.get(field)) is not None and to_float(v.get(field)) > 0)
        )

    consistency = {
        "daily_core_horizons": list(core_checks.keys()),
        "reference_horizons": list(reference_checks.keys()),
        "trade_beats_ignore_core_horizons": positive_count(core_checks, "trade_minus_ignore_alpha_pct"),
        "watch_beats_ignore_core_horizons": positive_count(core_checks, "watch_minus_ignore_alpha_pct"),
        "score_band_pass_core_horizons": sum(
            1 for v in core_checks.values()
            if ((v.get("score_band_avg_alpha_monotonicity") or {}).get("status") == "Pass")
        ),
        "core_horizon_count": len(core_checks),
        "reference_horizon_count": len(reference_checks),
        "trade_beats_ignore_all_horizons": positive_count(horizon_checks, "trade_minus_ignore_alpha_pct"),
        "watch_beats_ignore_all_horizons": positive_count(horizon_checks, "watch_minus_ignore_alpha_pct"),
        "all_horizon_count": len(horizon_checks),
    }

    return {
        "primary_horizon": primary_horizon_key(),
        "daily_core_horizons": list(core_checks.keys()),
        "reference_horizons": list(reference_checks.keys()),
        "horizon_checks": horizon_checks,
        "cross_horizon_consistency": consistency,
        "outlier_warning": outlier_analysis.get("average_return_distortion_warning"),
        "evaluation_note": "Daily model health is judged on 1D/3D/5D/10D, with 5D as the primary horizon. 20D is a reference horizon for decay/durability, not the main pass/fail target.",
    }

def build_model_health(summary: dict[str, Any], outlier_analysis: dict[str, Any], repeated_symbol_analysis: dict[str, Any], model_diagnostics: dict[str, Any]) -> dict[str, Any]:
    primary_key = primary_horizon_key()
    hc = (model_diagnostics.get("horizon_checks") or {}).get(primary_key) or {}

    trade_minus_ignore = to_float(hc.get("trade_minus_ignore_alpha_pct"))
    watch_minus_ignore = to_float(hc.get("watch_minus_ignore_alpha_pct"))
    trade_median_minus_ignore = to_float(hc.get("trade_minus_ignore_median_alpha_pct"))
    score_mono = (hc.get("score_band_avg_alpha_monotonicity") or {}).get("status") or "Insufficient"
    score_median_mono = (hc.get("score_band_median_alpha_monotonicity") or {}).get("status") or "Insufficient"

    outlier_status = outlier_analysis.get("average_return_distortion_warning") or "OK"
    top_symbol_concentration = to_float(outlier_analysis.get("top_symbol_contribution_pct"))
    median_avg_gap = to_float(outlier_analysis.get("median_average_gap_pct"))
    repeat_share = to_float(repeated_symbol_analysis.get("max_symbol_observation_share_pct"))

    checks = {
        "score_monotonicity": score_mono,
        "score_band_median_monotonicity": score_median_mono,
        "trade_vs_ignore_alpha": "Pass" if trade_minus_ignore is not None and trade_minus_ignore > 0 else "Fail" if trade_minus_ignore is not None else "Insufficient",
        "watch_vs_ignore_alpha": "Pass" if watch_minus_ignore is not None and watch_minus_ignore > 0 else "Fail" if watch_minus_ignore is not None else "Insufficient",
        "trade_vs_ignore_median_alpha": "Pass" if trade_median_minus_ignore is not None and trade_median_minus_ignore > 0 else "Fail" if trade_median_minus_ignore is not None else "Insufficient",
        "outlier_concentration": outlier_status,
        "median_average_gap": "Pass" if median_avg_gap is not None and median_avg_gap < 3 else "Warning" if median_avg_gap is not None and median_avg_gap < 7 else "Fail" if median_avg_gap is not None else "Insufficient",
        "repeated_symbol_concentration": "Pass" if repeat_share is not None and repeat_share < 5 else "Warning" if repeat_share is not None and repeat_share < 10 else "Fail" if repeat_share is not None else "Insufficient",
    }

    hard_fail = any(v == "Fail" for v in checks.values())
    warning = any(v == "Warning" for v in checks.values())
    insufficient = any(v == "Insufficient" for v in checks.values())

    verdict = "Fail" if hard_fail else "Warning" if warning or insufficient else "Pass"

    return {
        "primary_horizon": primary_key,
        "verdict": verdict,
        "checks": checks,
        "trade_minus_ignore_alpha_pct": safe_round(trade_minus_ignore, 4),
        "watch_minus_ignore_alpha_pct": safe_round(watch_minus_ignore, 4),
        "trade_minus_ignore_median_alpha_pct": safe_round(trade_median_minus_ignore, 4),
        "score_monotonicity": hc.get("score_band_avg_alpha_monotonicity"),
        "score_band_monotonicity": hc.get("score_band_avg_alpha_monotonicity"),
        "score_band_median_monotonicity": hc.get("score_band_median_alpha_monotonicity"),
        "outlier_concentration": {
            "status": outlier_status,
            "top_symbol_contribution_pct": safe_round(top_symbol_concentration, 2),
            "top_observation_contribution_pct": outlier_analysis.get("top_observation_contribution_pct"),
        },
        "median_average_gap": {
            "avg_return_pct": outlier_analysis.get("avg_return_pct"),
            "median_return_pct": outlier_analysis.get("median_return_pct"),
            "gap_pct": safe_round(median_avg_gap, 4),
        },
        "repeated_symbol_concentration": {
            "max_symbol_observation_share_pct": safe_round(repeat_share, 2),
            "max_observations_single_symbol": repeated_symbol_analysis.get("max_observations_single_symbol"),
        },
    }

def build_summary(rows: list[dict[str, Any]], date_states: list[dict[str, Any]]) -> dict[str, Any]:
    eval_dates = sorted({str(row.get("eval_date")) for row in rows if row.get("eval_date")})

    outlier_analysis = build_outlier_analysis(rows)
    repeated_symbol_analysis = build_repeated_symbol_analysis(rows)

    summary = {
        "mode": MODE,
        "eval_date_count": len(eval_dates),
        "eval_date_start": eval_dates[0] if eval_dates else None,
        "eval_date_end": eval_dates[-1] if eval_dates else None,
        "signal_count": len(rows),
        "horizons": HORIZONS,
        "evaluation_design": {
            "model": "Daily short-term trading",
            "primary_horizon": primary_horizon_key(),
            "daily_core_horizons": core_horizon_keys(),
            "reference_horizons": reference_horizon_keys(),
            "primary_note": "5D is the main Daily evaluation horizon. 1D/3D/10D are core short-term confirmation horizons. 20D is reference only for decay/durability, not the main pass/fail target.",
        },
        "overall": {
            f"{h}d": enhanced_stats_for_rows(rows, f"{h}d")
            for h in HORIZONS
        },
        "by_triage": group_summary(rows, "triage"),
        "by_archetype": group_summary(rows, "archetype"),
        "by_bucket": group_summary(rows, "bucket"),
        "by_score_band": group_summary(rows, "score_band"),
        "by_liquidity_band": group_summary(rows, "liquidity_band"),
        "by_risk_level": group_summary(rows, "risk_level"),
        "by_regime": group_summary(rows, "regime"),
        "date_states_count": len(date_states),
    }

    summary["filtered_performance"] = build_filtered_performance(rows)
    summary["rank_bucket_performance"] = build_rank_bucket_performance(rows)
    summary["outlier_analysis"] = outlier_analysis
    summary["repeated_symbol_analysis"] = repeated_symbol_analysis
    summary["model_diagnostics"] = build_model_diagnostics(summary, outlier_analysis)
    summary["model_health"] = build_model_health(
        summary=summary,
        outlier_analysis=outlier_analysis,
        repeated_symbol_analysis=repeated_symbol_analysis,
        model_diagnostics=summary["model_diagnostics"],
    )

    return summary


def merge_incremental_items(
    existing: dict[str, Any] | None,
    new_items: list[dict[str, Any]],
    new_failures: list[dict[str, Any]],
    new_date_states: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if MODE != "incremental" or not existing:
        return new_items, new_failures, new_date_states

    new_dates = {str(row.get("eval_date")) for row in new_items if row.get("eval_date")}

    old_items = [
        row for row in (existing.get("items") or [])
        if str(row.get("eval_date")) not in new_dates
    ]

    old_failures = [
        row for row in (existing.get("failures") or [])
        if str(row.get("eval_date")) not in new_dates
    ]

    old_states = [
        row for row in (existing.get("date_states") or [])
        if str(row.get("eval_date")) not in new_dates
    ]

    merged_items = old_items + new_items
    merged_failures = old_failures + new_failures
    merged_states = old_states + new_date_states

    merged_items.sort(key=lambda x: (str(x.get("eval_date")), int(x.get("rank") or 9999), str(x.get("symbol") or "")))
    merged_failures.sort(key=lambda x: (str(x.get("eval_date")), str(x.get("symbol") or "")))
    merged_states.sort(key=lambda x: str(x.get("eval_date")))

    return merged_items, merged_failures, merged_states


def main() -> int:
    generated_at = iso_now()
    today = now_jst().date().isoformat()

    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"PRICES_JSON={safe_relative(PRICES_JSON)}")
    print(f"BACKTEST_OUT_DIR={safe_relative(BACKTEST_OUT_DIR)}")
    print(f"MODE={MODE}")
    print(f"HORIZONS={HORIZONS}")
    print(f"BACKTEST_START={BACKTEST_START or '-'}")
    print(f"BACKTEST_END={BACKTEST_END or '-'}")
    print(f"MIN_HISTORY_BARS={MIN_HISTORY_BARS}")
    print(f"RANK_LIMIT={RANK_LIMIT}")

    if not HORIZONS:
        raise ValueError("BACKTEST_HORIZONS is empty")

    prices_payload = read_json(PRICES_JSON)

    if prices_payload.get("schema_version") != "prices-jp-v1":
        raise ValueError(f"Unexpected prices schema: {prices_payload.get('schema_version')}")

    market_pulse_raw = prices_payload.get("market_pulse") or []
    equities_raw = prices_payload.get("equities") or []

    if not isinstance(market_pulse_raw, list):
        raise TypeError("market_pulse must be list")
    if not isinstance(equities_raw, list):
        raise TypeError("equities must be list")

    topix_df = get_topix_df(market_pulse_raw)
    if topix_df.empty:
        raise ValueError("TOPIX market pulse data is unavailable. Cannot build JP backtest.")

    eval_dates = select_eval_dates(prices_payload, topix_df)

    print(f"Selected eval dates: {len(eval_dates)}")
    if eval_dates:
        print(f"Eval date range: {eval_dates[0]} -> {eval_dates[-1]}")

    new_items: list[dict[str, Any]] = []
    new_failures: list[dict[str, Any]] = []
    new_date_states: list[dict[str, Any]] = []

    for i, eval_date in enumerate(eval_dates, start=1):
        print(f"[{i}/{len(eval_dates)}] Backtest eval_date={eval_date}")

        rows, failures, date_state = score_date(
            eval_date=eval_date,
            market_pulse_raw=market_pulse_raw,
            equities_raw=equities_raw,
            topix_full_df=topix_df,
        )

        print(
            f"  scored={len(rows)} failures={len(failures)} "
            f"regime={date_state.get('regime')}"
        )

        new_items.extend(rows)
        new_failures.extend(failures)
        new_date_states.append(date_state)

    existing = load_existing_latest()

    items, failures, date_states = merge_incremental_items(
        existing=existing,
        new_items=new_items,
        new_failures=new_failures,
        new_date_states=new_date_states,
    )

    summary = build_summary(items, date_states)

    payload = {
        "schema_version": "backtest-daily-jp-v1",
        "generated_at": generated_at,
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "mode": MODE,
        "source_prices": safe_relative(PRICES_JSON),
        "source_prices_generated_at": prices_payload.get("generated_at"),
        "horizons": HORIZONS,
        "evaluation_design": summary.get("evaluation_design"),
        "min_history_bars": MIN_HISTORY_BARS,
        "rank_limit": RANK_LIMIT,
        "range": {
            "requested_start": BACKTEST_START or None,
            "requested_end": BACKTEST_END or None,
            "selected_count": len(eval_dates),
            "selected_start": eval_dates[0] if eval_dates else None,
            "selected_end": eval_dates[-1] if eval_dates else None,
        },
        "methodology": {
            "name": "Neon Tokyo Daily JP Backtest v1",
            "scoring_engine": "build_daily_jp.py / Daily Event Score v2",
            "api_calls": 0,
            "note": "Backtest replays scoring using historical bars already saved in prices-jp/latest.json. It does not fetch external data.",
            "return_measurement": "Entry at evaluation date close; future returns use trading-day offsets.",
            "alpha_measurement": "Stock future return minus TOPIX ETF future return for same horizon.",
        },
        "summary": summary,
        "date_states": date_states,
        "items": items,
        "failures": failures,
    }

    BACKTEST_OUT_DIR.mkdir(parents=True, exist_ok=True)

    latest_path = BACKTEST_OUT_DIR / "latest.json"
    dated_path = BACKTEST_OUT_DIR / f"{today}.json"

    write_json(latest_path, payload)
    write_json(dated_path, payload)

    manifest = {
        "schema_version": "backtest-daily-jp-manifest-v1",
        "generated_at": generated_at,
        "latest": safe_relative(latest_path),
        "latest_date": today,
        "mode": MODE,
        "horizons": HORIZONS,
        "eval_date_count": summary.get("eval_date_count"),
        "signal_count": summary.get("signal_count"),
        "history": [
            {
                "date": today,
                "path": safe_relative(dated_path),
                "mode": MODE,
                "eval_date_count": summary.get("eval_date_count"),
                "signal_count": summary.get("signal_count"),
                "eval_date_start": summary.get("eval_date_start"),
                "eval_date_end": summary.get("eval_date_end"),
            }
        ],
    }

    manifest_path = BACKTEST_OUT_DIR / "manifest.json"
    write_json(manifest_path, manifest)

    print(f"Wrote {safe_relative(latest_path)}")
    print(f"Wrote {safe_relative(dated_path)}")
    print(f"Wrote {safe_relative(manifest_path)}")
    print(f"Eval dates total={summary.get('eval_date_count')}")
    print(f"Signals total={summary.get('signal_count')}")

    if MODE == "range" and not eval_dates:
        print("No evaluation dates selected for range mode.")
        return 2

    if not items:
        print("No backtest items generated.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
