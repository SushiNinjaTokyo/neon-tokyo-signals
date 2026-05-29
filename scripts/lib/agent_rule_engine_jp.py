from __future__ import annotations

"""Entry filtering for AI Arena JP agents.

Agent scores are rankings, not executable orders.  This module converts scored
rows into executable candidates by applying explicit, explainable strategy rules.

Sixth-batch changes:
- HIZUMI can use value_features_daily directly at entry.
- SAGURI can use small-cap / financial-quality guards at entry.
- KYOU, NAGARE, MAMORU and MATSU can use richer existing daily features.
- Reject reasons are deliberately granular so agent-rejection diagnostics are
  useful for tuning.
"""

from datetime import date
from typing import Any

import duckdb

from .arena_calendar_jp import trading_days_until_year_end


def num(value: Any, default: float = 0.0) -> float:
    try:
        v = float(value)
        if v == v and v not in (float("inf"), float("-inf")):
            return v
    except Exception:
        pass
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
    """Return daily features enriched with value/fundamental fields when present."""
    value_join = ""
    value_cols = ""
    if _table_exists(conn, "value_features_daily"):
        value_join = "LEFT JOIN value_features_daily vf ON f.ticker = vf.ticker AND f.date = vf.date"
        value_cols = """
          , vf.valuation_discount_score
          , vf.quality_guard_score
          , vf.earnings_stability_score
          , vf.shareholder_return_score
          , vf.re_rating_signal_score
          , vf.value_trap_penalty
          , vf.value_mispricing_score
          , vf.valuation_bucket
          , vf.value_status
          , vf.fundamental_coverage_score
        """

    fundamental_join = ""
    fundamental_cols = ""
    if _table_exists(conn, "fundamentals_latest_jp"):
        fundamental_join = "LEFT JOIN fundamentals_latest_jp fl ON f.ticker = fl.ticker"
        fundamental_cols = """
          , fl.market_cap_jpy AS fundamental_market_cap_jpy
          , fl.revenue_jpy AS fundamental_revenue_jpy
          , fl.operating_profit_jpy AS fundamental_operating_profit_jpy
          , fl.net_income_jpy AS fundamental_net_income_jpy
          , fl.equity_jpy AS fundamental_equity_jpy
          , fl.roe_pct AS fundamental_roe_pct
          , fl.roa_pct AS fundamental_roa_pct
          , fl.per AS fundamental_per
          , fl.pbr AS fundamental_pbr
          , fl.psr AS fundamental_psr
          , fl.dividend_yield_pct AS fundamental_dividend_yield_pct
          , fl.operating_margin_pct AS fundamental_operating_margin_pct
          , fl.net_margin_pct AS fundamental_net_margin_pct
          , fl.equity_ratio_pct AS fundamental_equity_ratio_pct
          , fl.revenue_growth_yoy_pct AS fundamental_revenue_growth_yoy_pct
          , fl.operating_profit_growth_yoy_pct AS fundamental_operating_profit_growth_yoy_pct
          , fl.eps_growth_yoy_pct AS fundamental_eps_growth_yoy_pct
          , fl.source_quality AS fundamental_source_quality
        """

    universe_join = ""
    universe_cols = ""
    if _table_exists(conn, "universe_master"):
        universe_join = "LEFT JOIN universe_master u ON f.ticker = u.ticker"
        universe_cols = """
          , u.name AS universe_name
          , u.sector AS universe_sector
          , u.bucket AS universe_bucket
          , u.is_core AS universe_is_core
          , u.is_growth AS universe_is_growth
          , u.is_small_discovery AS universe_is_small_discovery
          , u.is_value_candidate AS universe_is_value_candidate
        """

    rows = conn.execute(
        f"""
        SELECT f.*
          {value_cols}
          {fundamental_cols}
          {universe_cols}
        FROM features_daily f
        {value_join}
        {fundamental_join}
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


def _get(row: dict[str, Any] | None, *keys: str, default: float = 0.0) -> float:
    if not row:
        return default
    for key in keys:
        if key in row and row.get(key) is not None:
            return num(row.get(key), default)
    return default


def _get_text(row: dict[str, Any] | None, *keys: str, default: str = "") -> str:
    if not row:
        return default
    for key in keys:
        if key in row and row.get(key) is not None:
            return text(row.get(key), default)
    return default


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(x) for x in value]
    return [str(value)]


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

    action = str(score_row.get("action") or "")
    allowed = set(entry.get("allowed_actions") or ["Trade"])
    if action not in allowed:
        return False, "action_not_allowed"

    score = num(score_row.get("normalized_score"))
    if score < num(entry.get("min_score"), 0.0):
        return False, "score_below_entry_threshold"

    if int(score_row.get("rank") or 999999) > int(entry.get("max_rank_per_day", 999999)):
        return False, "rank_below_cutoff"

    universe_bucket = str(score_row.get("universe_bucket") or feature_row.get("universe_bucket") or "")
    if "require_bucket" in entry and universe_bucket != str(entry["require_bucket"]):
        return False, "bucket_not_allowed"
    allowed_buckets = set(_list(entry.get("allowed_buckets")))
    if allowed_buckets and universe_bucket not in allowed_buckets:
        return False, "bucket_not_allowed"

    if _get(feature_row, "liquidity_score") < num(entry.get("min_liquidity_score"), 0.0):
        return False, "liquidity_below_threshold"

    if _get(feature_row, "avg_traded_value_20d_jpy") < num(entry.get("min_avg_traded_value_20d_jpy"), 0.0):
        return False, "traded_value_below_threshold"

    close = _get(feature_row, "close")
    min_price = num(common.get("min_price_jpy", entry.get("min_price_jpy", 0.0)), 0.0)
    max_price = num(common.get("max_price_jpy", entry.get("max_price_jpy", 0.0)), 0.0)
    if min_price and close < min_price:
        return False, "price_too_low"
    if max_price and close > max_price:
        return False, "price_too_high"

    if entry.get("require_price_above_ma20") and close <= _get(feature_row, "ma_20"):
        return False, "price_not_above_ma20"
    if entry.get("require_price_above_ma50") and close <= _get(feature_row, "ma_50"):
        return False, "price_not_above_ma50"
    if entry.get("require_price_above_ma120") and close <= _get(feature_row, "ma_120"):
        return False, "price_not_above_ma120"

    if "require_volume_ratio_20d_min" in entry and _get(feature_row, "volume_ratio_20d") < num(entry["require_volume_ratio_20d_min"]):
        return False, "volume_ratio_below_threshold"
    if "require_return_1d_pct_min" in entry and _get(feature_row, "return_1d_pct") < num(entry["require_return_1d_pct_min"]):
        return False, "one_day_return_too_low"
    if "require_range_position_20d_0_1_min" in entry and _get(feature_row, "range_position_20d_0_1") < num(entry["require_range_position_20d_0_1_min"]):
        return False, "twenty_day_range_position_too_low"
    if "require_range_position_252d_0_1_min" in entry and _get(feature_row, "range_position_252d_0_1") < num(entry["require_range_position_252d_0_1_min"]):
        return False, "year_range_position_too_low"
    if "require_range_position_252d_0_1_max" in entry and _get(feature_row, "range_position_252d_0_1") > num(entry["require_range_position_252d_0_1_max"]):
        return False, "year_range_position_too_high"

    if "reject_if_rsi_14_gt" in entry and _get(feature_row, "rsi_14") > num(entry["reject_if_rsi_14_gt"]):
        return False, "rsi_overheated"
    if "require_rsi_14_max" in entry and _get(feature_row, "rsi_14") > num(entry["require_rsi_14_max"]):
        return False, "rsi_not_oversold_enough"
    if "require_bollinger_b_20_max" in entry and _get(feature_row, "bollinger_b_20") > num(entry["require_bollinger_b_20_max"]):
        return False, "bollinger_not_low_enough"
    if "require_return_5d_pct_max" in entry and _get(feature_row, "return_5d_pct") > num(entry["require_return_5d_pct_max"]):
        return False, "recent_return_too_high_for_reversal"
    if "require_reversal_exhaustion_score_min" in entry and _get(feature_row, "reversal_exhaustion_score") < num(entry["require_reversal_exhaustion_score_min"]):
        return False, "reversal_score_too_low"
    if "require_return_60d_pct_min" in entry and _get(feature_row, "return_60d_pct") < num(entry["require_return_60d_pct_min"]):
        return False, "medium_return_too_low"
    if "reject_if_return_60d_pct_lt" in entry and _get(feature_row, "return_60d_pct") < num(entry["reject_if_return_60d_pct_lt"]):
        return False, "medium_return_too_weak"
    if "reject_if_volatility_60d_annualized_pct_gt" in entry and _get(feature_row, "volatility_60d_annualized_pct") > num(entry["reject_if_volatility_60d_annualized_pct_gt"]):
        return False, "volatility_too_high"
    if "reject_if_max_drawdown_60d_pct_lt" in entry and _get(feature_row, "max_drawdown_60d_pct") < num(entry["reject_if_max_drawdown_60d_pct_lt"]):
        return False, "drawdown_too_deep"
    if "reject_if_return_5d_pct_gt" in entry and _get(feature_row, "return_5d_pct") > num(entry["reject_if_return_5d_pct_gt"]):
        return False, "five_day_move_too_extended"
    if "reject_if_return_20d_pct_lt" in entry and _get(feature_row, "return_20d_pct") < num(entry["reject_if_return_20d_pct_lt"]):
        return False, "pullback_too_deep"
    if "reject_if_return_20d_pct_gt" in entry and _get(feature_row, "return_20d_pct") > num(entry["reject_if_return_20d_pct_gt"]):
        return False, "twenty_day_move_too_extended"
    if "require_trend_score_weekly_proxy_min" in entry and _get(feature_row, "trend_score_weekly_proxy") < num(entry["require_trend_score_weekly_proxy_min"]):
        return False, "weekly_trend_too_weak"

    if "require_rsi_14_between" in entry:
        lo, hi = entry["require_rsi_14_between"]
        rsi = _get(feature_row, "rsi_14")
        if rsi < num(lo) or rsi > num(hi):
            return False, "rsi_outside_pullback_band"
    if "require_price_vs_ma50_pct_between" in entry:
        lo, hi = entry["require_price_vs_ma50_pct_between"]
        v = _get(feature_row, "price_vs_ma50_pct")
        if v < num(lo) or v > num(hi):
            return False, "price_vs_ma50_outside_band"

    # Fundamental / value-feature gates used by HIZUMI and SAGURI.
    market_cap = _get(feature_row, "fundamental_market_cap_jpy", "market_cap_jpy", default=0.0)
    if "require_market_cap_jpy_min" in entry and market_cap < num(entry["require_market_cap_jpy_min"]):
        return False, "market_cap_too_small"
    if "require_market_cap_jpy_max" in entry and market_cap > num(entry["require_market_cap_jpy_max"]):
        return False, "market_cap_too_large"

    op_margin = _get(feature_row, "fundamental_operating_margin_pct", "operating_margin_pct", default=0.0)
    if "require_operating_margin_pct_min" in entry and op_margin < num(entry["require_operating_margin_pct_min"]):
        return False, "operating_margin_below_threshold"
    roe = _get(feature_row, "fundamental_roe_pct", "roe_pct", default=0.0)
    if "require_roe_pct_min" in entry and roe < num(entry["require_roe_pct_min"]):
        return False, "roe_below_threshold"

    psr = _get(feature_row, "fundamental_psr", "psr", default=0.0)
    if "reject_if_psr_gt" in entry and psr > 0 and psr > num(entry["reject_if_psr_gt"]):
        return False, "psr_too_high"
    pbr = _get(feature_row, "fundamental_pbr", "pbr", default=0.0)
    if "reject_if_pbr_gt" in entry and pbr > 0 and pbr > num(entry["reject_if_pbr_gt"]):
        return False, "pbr_too_high"
    per = _get(feature_row, "fundamental_per", "per", default=0.0)
    if "reject_if_per_gt" in entry and per > 0 and per > num(entry["reject_if_per_gt"]):
        return False, "per_too_high"

    quality = _get(feature_row, "quality_guard_score", default=0.0)
    if "require_quality_guard_score_min" in entry and quality < num(entry["require_quality_guard_score_min"]):
        return False, "quality_guard_below_threshold"
    mispricing = _get(feature_row, "value_mispricing_score", default=0.0)
    if "require_value_mispricing_score_min" in entry and mispricing < num(entry["require_value_mispricing_score_min"]):
        return False, "value_mispricing_score_below_threshold"
    discount = _get(feature_row, "valuation_discount_score", default=0.0)
    if "require_valuation_discount_score_min" in entry and discount < num(entry["require_valuation_discount_score_min"]):
        return False, "valuation_discount_below_threshold"
    trap = _get(feature_row, "value_trap_penalty", default=0.0)
    if "reject_if_value_trap_penalty_gt" in entry and trap > num(entry["reject_if_value_trap_penalty_gt"]):
        return False, "value_trap_penalty_too_high"

    allowed_value_buckets = set(_list(entry.get("allowed_valuation_buckets")))
    if allowed_value_buckets:
        vb = _get_text(feature_row, "valuation_bucket")
        if vb not in allowed_value_buckets:
            return False, "valuation_bucket_not_allowed"

    return True, "entry_rule_passed"
