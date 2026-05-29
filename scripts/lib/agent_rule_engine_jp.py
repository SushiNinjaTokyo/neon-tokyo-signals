from __future__ import annotations

"""Entry filtering for AI Arena agents.

Agent scores are rankings, not orders. This module applies the explicit strategy
rules that convert a high score into an executable candidate. Keeping this logic
outside the score builder makes the system easier to tune and easier to explain
on the Agent Profiles page.
"""

from datetime import date
from typing import Any

import duckdb

from .arena_calendar_jp import trading_days_until_year_end


def num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def fetch_feature_map(conn: duckdb.DuckDBPyConnection, d: date) -> dict[str, dict[str, Any]]:
    rows = conn.execute("SELECT * FROM features_daily WHERE date = ?", [d]).fetchdf()
    if rows.empty:
        return {}
    return {str(r["ticker"]): r.to_dict() for _, r in rows.iterrows()}


def fetch_score_map(conn: duckdb.DuckDBPyConnection, d: date) -> dict[tuple[str, str], dict[str, Any]]:
    rows = conn.execute("SELECT * FROM agent_scores_daily WHERE date = ?", [d]).fetchdf()
    if rows.empty:
        return {}
    return {(str(r["agent_id"]), str(r["ticker"])): r.to_dict() for _, r in rows.iterrows()}


def passes_entry_rule(
    *,
    score_row: dict[str, Any],
    feature_row: dict[str, Any] | None,
    agent_rule: dict[str, Any],
    trading_dates: list[date],
    signal_date: date,
) -> tuple[bool, str]:
    """Return whether a scored row is eligible for a new position."""
    entry = agent_rule.get("entry", {}) or {}
    if not feature_row:
        return False, "missing_feature_row"

    if trading_days_until_year_end(trading_dates, signal_date) < int(agent_rule.get("year_end_entry_block_trading_days", 0) or 0):
        return False, "blocked_near_year_end"

    action = str(score_row.get("action") or "")
    allowed = set(entry.get("allowed_actions") or ["Trade"])
    if action not in allowed:
        return False, "action_not_allowed"

    score = num(score_row.get("normalized_score"))
    if score < num(entry.get("min_score"), 0.0):
        return False, "score_below_entry_threshold"

    if int(score_row.get("rank") or 999999) > int(entry.get("max_rank_per_day", 999999)):
        return False, "rank_below_cutoff"

    if "require_bucket" in entry and str(score_row.get("universe_bucket") or "") != str(entry["require_bucket"]):
        return False, "bucket_not_allowed"

    if num(feature_row.get("liquidity_score")) < num(entry.get("min_liquidity_score"), 0.0):
        return False, "liquidity_below_threshold"

    if num(feature_row.get("avg_traded_value_20d_jpy")) < num(entry.get("min_avg_traded_value_20d_jpy"), 0.0):
        return False, "traded_value_below_threshold"

    close = num(feature_row.get("close"))
    if close < num((agent_rule.get("common") or {}).get("min_price_jpy"), 0.0):
        return False, "price_too_low"

    if entry.get("require_price_above_ma20") and close <= num(feature_row.get("ma_20")):
        return False, "price_not_above_ma20"
    if entry.get("require_price_above_ma50") and close <= num(feature_row.get("ma_50")):
        return False, "price_not_above_ma50"
    if entry.get("require_price_above_ma120") and close <= num(feature_row.get("ma_120")):
        return False, "price_not_above_ma120"

    if "require_volume_ratio_20d_min" in entry and num(feature_row.get("volume_ratio_20d")) < num(entry["require_volume_ratio_20d_min"]):
        return False, "volume_ratio_below_threshold"
    if "reject_if_rsi_14_gt" in entry and num(feature_row.get("rsi_14")) > num(entry["reject_if_rsi_14_gt"]):
        return False, "rsi_overheated"
    if "require_rsi_14_max" in entry and num(feature_row.get("rsi_14")) > num(entry["require_rsi_14_max"]):
        return False, "rsi_not_oversold_enough"
    if "require_bollinger_b_20_max" in entry and num(feature_row.get("bollinger_b_20")) > num(entry["require_bollinger_b_20_max"]):
        return False, "bollinger_not_low_enough"
    if "require_return_5d_pct_max" in entry and num(feature_row.get("return_5d_pct")) > num(entry["require_return_5d_pct_max"]):
        return False, "recent_return_too_high_for_reversal"
    if "require_reversal_exhaustion_score_min" in entry and num(feature_row.get("reversal_exhaustion_score")) < num(entry["require_reversal_exhaustion_score_min"]):
        return False, "reversal_score_too_low"
    if "require_return_60d_pct_min" in entry and num(feature_row.get("return_60d_pct")) < num(entry["require_return_60d_pct_min"]):
        return False, "medium_return_too_low"
    if "reject_if_return_60d_pct_lt" in entry and num(feature_row.get("return_60d_pct")) < num(entry["reject_if_return_60d_pct_lt"]):
        return False, "medium_return_too_weak"
    if "reject_if_volatility_60d_annualized_pct_gt" in entry and num(feature_row.get("volatility_60d_annualized_pct")) > num(entry["reject_if_volatility_60d_annualized_pct_gt"]):
        return False, "volatility_too_high"
    if "reject_if_max_drawdown_60d_pct_lt" in entry and num(feature_row.get("max_drawdown_60d_pct")) < num(entry["reject_if_max_drawdown_60d_pct_lt"]):
        return False, "drawdown_too_deep"
    if "reject_if_return_5d_pct_gt" in entry and num(feature_row.get("return_5d_pct")) > num(entry["reject_if_return_5d_pct_gt"]):
        return False, "five_day_move_too_extended"
    if "reject_if_return_20d_pct_lt" in entry and num(feature_row.get("return_20d_pct")) < num(entry["reject_if_return_20d_pct_lt"]):
        return False, "pullback_too_deep"
    if "require_trend_score_weekly_proxy_min" in entry and num(feature_row.get("trend_score_weekly_proxy")) < num(entry["require_trend_score_weekly_proxy_min"]):
        return False, "weekly_trend_too_weak"
    if "require_range_position_252d_0_1_max" in entry and num(feature_row.get("range_position_252d_0_1")) > num(entry["require_range_position_252d_0_1_max"]):
        return False, "year_range_position_too_high"

    if "require_rsi_14_between" in entry:
        lo, hi = entry["require_rsi_14_between"]
        rsi = num(feature_row.get("rsi_14"))
        if rsi < num(lo) or rsi > num(hi):
            return False, "rsi_outside_pullback_band"
    if "require_price_vs_ma50_pct_between" in entry:
        lo, hi = entry["require_price_vs_ma50_pct_between"]
        v = num(feature_row.get("price_vs_ma50_pct"))
        if v < num(lo) or v > num(hi):
            return False, "price_vs_ma50_outside_band"

    return True, "entry_rule_passed"
