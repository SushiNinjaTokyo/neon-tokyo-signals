from __future__ import annotations

"""Agent-specific exit rule evaluation.

The engine returns the first matching reason in a fixed priority order. This is
important for clean UI: each sale should have one primary reason rather than a
random list of simultaneous conditions.
"""

from typing import Any


def f(row: dict[str, Any] | None, key: str, default: float = 0.0) -> float:
    if not row:
        return default
    try:
        v = float(row.get(key))
        return v
    except Exception:
        return default


def b(row: dict[str, Any] | None, key: str) -> bool:
    return bool(row and row.get(key))


def should_exit_position(
    *,
    agent_id: str,
    rule: dict[str, Any],
    position: dict[str, Any],
    feature_row: dict[str, Any] | None,
    score_row: dict[str, Any] | None,
    current_price: float,
    holding_days: int,
    high_water_return_pct: float,
) -> tuple[bool, str, str]:
    """Evaluate exit conditions and return (should_exit, code, text)."""
    exit_rule = rule.get("exit", {}) or {}
    entry_price = f(position, "entry_price", 0.0)
    if entry_price <= 0 or current_price <= 0:
        return True, "MISSING_PRICE_EXIT", "Price data became invalid."
    ret_pct = (current_price / entry_price - 1.0) * 100.0

    hard_stop = exit_rule.get("hard_stop_loss_pct")
    if hard_stop is not None and ret_pct <= float(hard_stop):
        return True, "HARD_STOP", f"Hard stop triggered at {ret_pct:.1f}%."

    # Emergency liquidity/risk exits before ordinary profit exits.
    if "liquidity_score_below" in exit_rule and f(feature_row, "liquidity_score", 1.0) < float(exit_rule["liquidity_score_below"]):
        return True, "LIQUIDITY_DRYUP", "Liquidity score fell below the agent threshold."
    if "risk_score_below" in exit_rule and f(feature_row, "risk_score", 1.0) < float(exit_rule["risk_score_below"]):
        return True, "CAPITAL_PROTECTION", "Risk score deteriorated below the agent threshold."
    if "volatility_20d_annualized_pct_above" in exit_rule and f(feature_row, "volatility_20d_annualized_pct", 0.0) > float(exit_rule["volatility_20d_annualized_pct_above"]):
        return True, "VOLATILITY_SPIKE", "Volatility spiked beyond the risk budget."

    score = f(score_row, "normalized_score", 1.0)
    if "score_below" in exit_rule and score < float(exit_rule["score_below"]):
        return True, "SCORE_COLLAPSE", "Agent score collapsed below the exit threshold."

    # Agent-specific structural exits.
    if exit_rule.get("price_below_ma10") and current_price < f(feature_row, "ma_10", 0.0):
        return True, "MOMENTUM_DECAY", "Price lost MA10 and short-term momentum faded."
    if exit_rule.get("price_below_ma20") and current_price < f(feature_row, "ma_20", 0.0):
        return True, "MOMENTUM_DECAY", "Price lost MA20."
    if exit_rule.get("price_below_ma50") and current_price < f(feature_row, "ma_50", 0.0):
        return True, "TREND_BREAK", "Price broke below MA50."
    if exit_rule.get("price_below_ma120") and current_price < f(feature_row, "ma_120", 0.0):
        return True, "PULLBACK_FAILED", "Pullback turned into a deeper trend break."
    if "trend_score_weekly_proxy_below" in exit_rule and f(feature_row, "trend_score_weekly_proxy", 1.0) < float(exit_rule["trend_score_weekly_proxy_below"]):
        return True, "TREND_BREAK", "Weekly trend proxy weakened."
    if "rsi_14_above" in exit_rule and f(feature_row, "rsi_14", 0.0) > float(exit_rule["rsi_14_above"]):
        return True, "SNAPBACK_COMPLETE", "RSI normalized after the snapback."
    if "bollinger_b_20_above" in exit_rule and f(feature_row, "bollinger_b_20", 0.0) > float(exit_rule["bollinger_b_20_above"]):
        return True, "SNAPBACK_COMPLETE", "Bollinger position normalized after rebound."
    if "range_position_252d_0_1_above" in exit_rule and f(feature_row, "range_position_252d_0_1", 0.0) > float(exit_rule["range_position_252d_0_1_above"]):
        return True, "MISPRICING_RESOLVED", "Price moved high enough in its yearly range to reduce the distortion."
    if "return_20d_pct_above" in exit_rule and f(feature_row, "return_20d_pct", 0.0) > float(exit_rule["return_20d_pct_above"]):
        return True, "MISPRICING_RESOLVED", "Recent re-rating progressed enough to harvest gains."

    take_profit = exit_rule.get("take_profit_pct")
    if take_profit is not None and ret_pct >= float(take_profit):
        return True, "TAKE_PROFIT", f"Take-profit target reached at {ret_pct:.1f}%."

    trailing = exit_rule.get("trailing_stop_pct")
    if trailing is not None and high_water_return_pct >= float(trailing) and (high_water_return_pct - ret_pct) >= float(trailing):
        return True, "TRAILING_STOP", "Trailing stop protected prior gains."

    max_days = exit_rule.get("max_holding_days")
    if max_days is not None and holding_days >= int(max_days):
        return True, "MAX_HOLDING_DAYS", "Maximum holding period reached."

    return False, "", ""
