from __future__ import annotations

"""Entry filtering for AI Arena agents.

Agent scores are rankings, not orders. This module applies explicit strategy
rules that convert high scores into executable candidates.  The entry filter now
joins daily technical features with value/fundamental features so HIZUMI and
SAGURI can use actual financial gates rather than only generic price momentum.
"""

from datetime import date
from typing import Any

import duckdb

from .arena_calendar_jp import trading_days_until_year_end


def num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    try:
        return bool(conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [table]).fetchone()[0])
    except Exception:
        return False


def fetch_feature_map(conn: duckdb.DuckDBPyConnection, d: date) -> dict[str, dict[str, Any]]:
    """Return per-ticker feature rows for entry/exit rules.

    The base table is features_daily.  When available, this also joins
    value_features_daily, fundamentals_latest_jp, and universe_master.  This is
    necessary because the score builder may use value features, but the execution
    rule engine also needs to validate value/quality/trap gates before ordering.
    """
    value_cols = ""
    value_join = ""
    if _table_exists(conn, "value_features_daily"):
        value_cols = """,
          vf.valuation_discount_score,
          vf.quality_guard_score,
          vf.earnings_stability_score,
          vf.shareholder_return_score,
          vf.re_rating_signal_score,
          vf.value_trap_penalty,
          vf.value_mispricing_score,
          vf.valuation_bucket,
          vf.value_status,
          vf.fundamental_coverage_score
        """
        value_join = "LEFT JOIN value_features_daily vf ON f.ticker = vf.ticker AND f.date = vf.date"

    fund_cols = ""
    fund_join = ""
    if _table_exists(conn, "fundamentals_latest_jp"):
        fund_cols = """,
          fl.market_cap_jpy,
          fl.per,
          fl.pbr,
          fl.psr,
          fl.roe_pct,
          fl.roa_pct,
          fl.operating_margin_pct,
          fl.net_margin_pct,
          fl.dividend_yield_pct,
          fl.revenue_growth_yoy_pct,
          fl.operating_profit_growth_yoy_pct,
          fl.eps_growth_yoy_pct
        """
        fund_join = "LEFT JOIN fundamentals_latest_jp fl ON f.ticker = fl.ticker"

    universe_cols = ""
    universe_join = ""
    if _table_exists(conn, "universe_master"):
        universe_cols = """,
          u.name,
          u.sector,
          u.theme,
          u.bucket,
          u.asset_type,
          u.is_core,
          u.is_growth,
          u.is_small_discovery,
          u.is_value_candidate,
          u.is_excluded
        """
        universe_join = "LEFT JOIN universe_master u ON f.ticker = u.ticker"

    rows = conn.execute(
        f"""
        SELECT
          f.*
          {value_cols}
          {fund_cols}
          {universe_cols}
        FROM features_daily f
        {value_join}
        {fund_join}
        {universe_join}
        WHERE f.date = ?
        """,
        [d],
    ).fetchdf()
    if rows.empty:
        return {}
    return {str(r["ticker"]): r.to_dict() for _, r in rows.iterrows()}


def fetch_score_map(conn: duckdb.DuckDBPyConnection, d: date) -> dict[tuple[str, str], dict[str, Any]]:
    rows = conn.execute("SELECT * FROM agent_scores_daily WHERE date = ?", [d]).fetchdf()
    if rows.empty:
        return {}
    return {(str(r["agent_id"]), str(r["ticker"])): r.to_dict() for _, r in rows.iterrows()}


def _bucket_allowed(score_row: dict[str, Any], feature_row: dict[str, Any], entry: dict[str, Any]) -> tuple[bool, str]:
    bucket = text(score_row.get("universe_bucket") or feature_row.get("bucket"), "")
    if "require_bucket" in entry and bucket != text(entry.get("require_bucket")):
        return False, "bucket_not_allowed"
    allowed = entry.get("allowed_buckets")
    if allowed:
        allowed_set = {text(x) for x in allowed}
        if bucket not in allowed_set:
            return False, "bucket_not_allowed"
    return True, "bucket_allowed"


def _passes_numeric_financial_gates(feature_row: dict[str, Any], entry: dict[str, Any]) -> tuple[bool, str]:
    checks = [
        ("require_market_cap_jpy_min", "market_cap_jpy", "market_cap_too_small", ">="),
        ("require_market_cap_jpy_max", "market_cap_jpy", "market_cap_too_large", "<="),
        ("require_operating_margin_pct_min", "operating_margin_pct", "operating_margin_below_threshold", ">="),
        ("require_roe_pct_min", "roe_pct", "roe_below_threshold", ">="),
        ("require_roa_pct_min", "roa_pct", "roa_below_threshold", ">="),
        ("require_quality_guard_score_min", "quality_guard_score", "quality_guard_below_threshold", ">="),
        ("require_value_mispricing_score_min", "value_mispricing_score", "value_mispricing_below_threshold", ">="),
        ("require_valuation_discount_score_min", "valuation_discount_score", "valuation_discount_below_threshold", ">="),
        ("reject_if_value_trap_penalty_gt", "value_trap_penalty", "value_trap_penalty_too_high", "<="),
        ("reject_if_psr_gt", "psr", "psr_too_high", "<="),
        ("reject_if_pbr_gt", "pbr", "pbr_too_high", "<="),
        ("reject_if_per_gt", "per", "per_too_high", "<="),
    ]
    for rule_key, feature_key, reason, op in checks:
        if rule_key not in entry:
            continue
        actual = num(feature_row.get(feature_key), None)  # type: ignore[arg-type]
        threshold = num(entry.get(rule_key), None)  # type: ignore[arg-type]
        if actual is None or threshold is None:
            return False, f"{feature_key}_missing"
        if op == ">=" and actual < threshold:
            return False, reason
        if op == "<=" and actual > threshold:
            return False, reason

    allowed_valuation_buckets = entry.get("allowed_valuation_buckets")
    if allowed_valuation_buckets:
        bucket = text(feature_row.get("valuation_bucket"), "")
        if bucket not in {text(x) for x in allowed_valuation_buckets}:
            return False, "valuation_bucket_not_allowed"
    return True, "financial_gates_passed"


def _passes_discovery_financial_setup(feature_row: dict[str, Any], setup: dict[str, Any]) -> tuple[bool, str]:
    if not setup:
        return False, "discovery_financial_setup_missing"
    ok, reason = _passes_numeric_financial_gates(feature_row, setup)
    if not ok:
        return False, reason
    if "require_volume_ratio_20d_min" in setup and num(feature_row.get("volume_ratio_20d")) < num(setup["require_volume_ratio_20d_min"]):
        return False, "volume_ratio_below_threshold"
    if "require_range_position_60d_0_1_min" in setup and num(feature_row.get("range_position_60d_0_1")) < num(setup["require_range_position_60d_0_1_min"]):
        return False, "range_position_60d_too_low"
    if "require_range_position_20d_0_1_min" in setup and num(feature_row.get("range_position_20d_0_1")) < num(setup["require_range_position_20d_0_1_min"]):
        return False, "range_position_20d_too_low"
    return True, "discovery_financial_setup_passed"


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
    common = agent_rule.get("common", {}) or {}
    if not feature_row:
        return False, "missing_feature_row"

    if trading_days_until_year_end(trading_dates, signal_date) < int(agent_rule.get("year_end_entry_block_trading_days", 0) or 0):
        return False, "blocked_near_year_end"

    action = text(score_row.get("action"))
    allowed = set(entry.get("allowed_actions") or ["Trade"])
    if action not in allowed:
        return False, "action_not_allowed"

    score = num(score_row.get("normalized_score"))
    if score < num(entry.get("min_score"), 0.0):
        return False, "score_below_entry_threshold"

    if int(score_row.get("rank") or 999999) > int(entry.get("max_rank_per_day", 999999)):
        return False, "rank_below_cutoff"

    bucket_ok, bucket_reason = _bucket_allowed(score_row, feature_row, entry)
    if not bucket_ok:
        if entry.get("bucket_optional_if_financial_setup"):
            setup_ok, setup_reason = _passes_discovery_financial_setup(feature_row, entry.get("discovery_financial_setup") or {})
            if not setup_ok:
                return False, bucket_reason
        else:
            return False, bucket_reason

    if num(feature_row.get("liquidity_score")) < num(entry.get("min_liquidity_score"), 0.0):
        return False, "liquidity_below_threshold"

    if num(feature_row.get("avg_traded_value_20d_jpy")) < num(entry.get("min_avg_traded_value_20d_jpy"), 0.0):
        return False, "traded_value_below_threshold"

    close = num(feature_row.get("close"))
    min_price = num(common.get("min_price_jpy"), 0.0)
    max_price = num(common.get("max_price_jpy"), 10**18)
    if close < min_price:
        return False, "price_too_low"
    if close > max_price:
        return False, "price_too_high"

    if entry.get("require_price_above_ma20") and close <= num(feature_row.get("ma_20")):
        return False, "price_not_above_ma20"
    if entry.get("require_price_above_ma50") and close <= num(feature_row.get("ma_50")):
        return False, "price_not_above_ma50"
    if entry.get("require_price_above_ma120") and close <= num(feature_row.get("ma_120")):
        return False, "price_not_above_ma120"

    if "require_volume_ratio_20d_min" in entry and num(feature_row.get("volume_ratio_20d")) < num(entry["require_volume_ratio_20d_min"]):
        return False, "volume_ratio_below_threshold"
    if "require_return_1d_pct_min" in entry and num(feature_row.get("return_1d_pct")) < num(entry["require_return_1d_pct_min"]):
        return False, "one_day_return_too_low"
    if "require_range_position_20d_0_1_min" in entry and num(feature_row.get("range_position_20d_0_1")) < num(entry["require_range_position_20d_0_1_min"]):
        return False, "range_position_20d_too_low"
    if "require_range_position_60d_0_1_min" in entry and num(feature_row.get("range_position_60d_0_1")) < num(entry["require_range_position_60d_0_1_min"]):
        return False, "range_position_60d_too_low"
    if "require_range_position_252d_0_1_min" in entry and num(feature_row.get("range_position_252d_0_1")) < num(entry["require_range_position_252d_0_1_min"]):
        return False, "year_range_position_too_low"
    if "require_range_position_252d_0_1_max" in entry and num(feature_row.get("range_position_252d_0_1")) > num(entry["require_range_position_252d_0_1_max"]):
        return False, "year_range_position_too_high"

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
    if "reject_if_return_20d_pct_gt" in entry and num(feature_row.get("return_20d_pct")) > num(entry["reject_if_return_20d_pct_gt"]):
        return False, "twenty_day_move_too_extended"
    if "reject_if_return_20d_pct_lt" in entry and num(feature_row.get("return_20d_pct")) < num(entry["reject_if_return_20d_pct_lt"]):
        return False, "pullback_too_deep"
    if "require_trend_score_weekly_proxy_min" in entry and num(feature_row.get("trend_score_weekly_proxy")) < num(entry["require_trend_score_weekly_proxy_min"]):
        return False, "weekly_trend_too_weak"

    ok, reason = _passes_numeric_financial_gates(feature_row, entry)
    if not ok:
        return False, reason

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
