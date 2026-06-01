from __future__ import annotations

"""Agent-specific exit rule evaluation for AI Arena JP.

This module intentionally keeps exit rules declarative.  Strategy YAML decides
what each agent cares about; the engine evaluates those rules in a stable,
inspectable priority order.

v018 focus:
- HIZUMI can hold true re-rating candidates longer, but cuts non-confirming
  value traps early.
- SAGURI can hold real theme/discovery runs longer, but exits quickly when
  liquidity and early accumulation disappear.
- Existing agents remain backward-compatible with the previous scalar fields.
"""

from typing import Any


REGIMES = {"BULL", "NEUTRAL", "BEAR", "PANIC"}


def f(row: dict[str, Any] | None, key: str, default: float = 0.0) -> float:
    if not row:
        return default
    try:
        v = row.get(key)
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def b(row: dict[str, Any] | None, key: str, default: bool = False) -> bool:
    if not row or key not in row:
        return default
    v = row.get(key)
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return bool(v)
    return str(v).strip().lower() in {"1", "true", "yes", "on", "y"}


def regime_state(feature_row: dict[str, Any] | None) -> str:
    if not feature_row:
        return "NEUTRAL"
    state = str(feature_row.get("market_regime_state") or "NEUTRAL").upper().strip()
    return state if state in REGIMES else "NEUTRAL"


def threshold(value: Any, *, feature_row: dict[str, Any] | None, default: float | None = None) -> float | None:
    """Return a numeric rule value, supporting regime-specific mappings.

    YAML may use either:
      hard_stop_loss_pct: -6.0
    or:
      hard_stop_loss_pct:
        BULL: -7.0
        NEUTRAL: -6.2
        BEAR: -5.2
        default: -6.2
    """
    if isinstance(value, dict):
        state = regime_state(feature_row)
        raw = value.get(state)
        if raw is None:
            raw = value.get(state.lower())
        if raw is None:
            raw = value.get("default")
        if raw is None:
            return default
    else:
        raw = value
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def _list_rules(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    return []


def _passes_any(feature_row: dict[str, Any] | None, position: dict[str, Any], ret_pct: float, high_water_return_pct: float, items: list[Any]) -> bool:
    if not items:
        return True
    return any(_condition_ok(feature_row, position, ret_pct, high_water_return_pct, item) for item in items)


def _passes_all(feature_row: dict[str, Any] | None, position: dict[str, Any], ret_pct: float, high_water_return_pct: float, items: list[Any]) -> bool:
    if not items:
        return True
    return all(_condition_ok(feature_row, position, ret_pct, high_water_return_pct, item) for item in items)


def _condition_ok(feature_row: dict[str, Any] | None, position: dict[str, Any], ret_pct: float, high_water_return_pct: float, item: Any) -> bool:
    """Evaluate compact extension conditions.

    Supported condition examples:
      {current_return_pct_gt: 0}
      {current_return_pct_gte: 8}
      {mfe_pct_gte: 12}
      {re_rating_signal_score_gte: 0.60}
      {volume_ratio_20d_gte: 1.1}
      {manual_theme_include: true}
    """
    if not isinstance(item, dict):
        return False
    for key, raw in item.items():
        try:
            want = float(raw) if not isinstance(raw, bool) else raw
        except Exception:
            want = raw
        if key in {"current_return_pct_gt", "ret_pct_gt"} and not (ret_pct > float(want)):
            return False
        if key in {"current_return_pct_gte", "ret_pct_gte"} and not (ret_pct >= float(want)):
            return False
        if key in {"current_return_pct_lt", "ret_pct_lt"} and not (ret_pct < float(want)):
            return False
        if key in {"current_return_pct_lte", "ret_pct_lte"} and not (ret_pct <= float(want)):
            return False
        if key in {"mfe_pct_gte", "high_water_return_pct_gte"} and not (high_water_return_pct >= float(want)):
            return False
        if key == "mfe_pct_lt" and not (high_water_return_pct < float(want)):
            return False
        if key.endswith("_gte"):
            field = key[:-4]
            if field in {"current_return_pct", "ret_pct", "mfe_pct", "high_water_return_pct"}:
                continue
            if not (f(feature_row, field) >= float(want)):
                return False
        elif key.endswith("_gt"):
            field = key[:-3]
            if field in {"current_return_pct", "ret_pct"}:
                continue
            if not (f(feature_row, field) > float(want)):
                return False
        elif key.endswith("_lte"):
            field = key[:-4]
            if not (f(feature_row, field) <= float(want)):
                return False
        elif key.endswith("_lt"):
            field = key[:-3]
            if field in {"current_return_pct", "ret_pct", "mfe_pct"}:
                continue
            if not (f(feature_row, field) < float(want)):
                return False
        elif key == "manual_theme_include":
            if bool(want) and not _is_manual_theme(feature_row):
                return False
        elif key == "market_regime_state":
            if regime_state(feature_row) != str(raw).upper():
                return False
        else:
            # Unknown condition should fail closed to avoid accidentally
            # extending trades due to a misspelled rule.
            return False
    return True


def _is_manual_theme(feature_row: dict[str, Any] | None) -> bool:
    if not feature_row:
        return False
    text = " ".join(
        str(feature_row.get(k) or "").lower()
        for k in ("theme", "bucket", "source_detail", "source_url", "sector")
    )
    keys = ["manual", "space", "robot", "drone", "uav", "aerospace", "satellite", "physical ai"]
    return any(k in text for k in keys)


def _early_fail_exit(exit_rule: dict[str, Any], feature_row: dict[str, Any] | None, holding_days: int, ret_pct: float, high_water_return_pct: float) -> tuple[bool, str, str]:
    # v018 structured form.
    structured = exit_rule.get("early_fail")
    if isinstance(structured, dict) and structured.get("enabled", True):
        after_days = int(structured.get("after_days", 0) or 0)
        if holding_days >= after_days:
            req = structured.get("require_all") or {}
            if not isinstance(req, dict):
                req = {}
            mfe_ceiling = threshold(req.get("mfe_below_pct"), feature_row=feature_row, default=None)
            ret_floor = threshold(req.get("current_return_below_pct"), feature_row=feature_row, default=None)
            rerating_below = threshold(req.get("re_rating_signal_below"), feature_row=feature_row, default=None)
            volume_below = threshold(req.get("volume_ratio_20d_below"), feature_row=feature_row, default=None)
            ok = True
            parts: list[str] = []
            if mfe_ceiling is not None:
                ok = ok and high_water_return_pct < mfe_ceiling
                parts.append(f"MFE {high_water_return_pct:.1f}% < {mfe_ceiling:.1f}%")
            if ret_floor is not None:
                ok = ok and ret_pct <= ret_floor
                parts.append(f"return {ret_pct:.1f}% <= {ret_floor:.1f}%")
            if rerating_below is not None:
                rr = f(feature_row, "re_rating_signal_score", 0.0)
                ok = ok and rr < rerating_below
                parts.append(f"re-rating {rr:.2f} < {rerating_below:.2f}")
            if volume_below is not None:
                vr = f(feature_row, "volume_ratio_20d", 0.0)
                ok = ok and vr < volume_below
                parts.append(f"volume ratio {vr:.2f} < {volume_below:.2f}")
            if ok and parts:
                return True, str(structured.get("code") or "EARLY_FAIL"), "Early failure: " + ", ".join(parts) + "."

    # Backward-compatible scalar form.
    early_days = exit_rule.get("early_fail_after_days")
    if early_days is not None and holding_days >= int(early_days):
        mfe_ceiling = float(exit_rule.get("early_fail_mfe_below_pct", 0.0) or 0.0)
        ret_floor = float(exit_rule.get("early_fail_return_below_pct", -10**9) or -10**9)
        if high_water_return_pct < mfe_ceiling and ret_pct <= ret_floor:
            return True, "EARLY_FAIL", f"Early failure: MFE {high_water_return_pct:.1f}% stayed below {mfe_ceiling:.1f}% and return fell to {ret_pct:.1f}%."
    return False, "", ""


def _profit_protection_exit(exit_rule: dict[str, Any], ret_pct: float, high_water_return_pct: float) -> tuple[bool, str, str]:
    applicable: list[tuple[float, float, str]] = []
    for item in _list_rules(exit_rule.get("mfe_profit_protection") or exit_rule.get("profit_protection")):
        try:
            trigger = float(item.get("mfe_pct"))
            floor = float(item.get("floor_return_pct"))
        except Exception:
            continue
        if high_water_return_pct >= trigger:
            applicable.append((trigger, floor, str(item.get("code") or "PROFIT_PROTECTION")))
    if not applicable:
        return False, "", ""
    trigger, floor, code = sorted(applicable, key=lambda x: x[0], reverse=True)[0]
    if ret_pct <= floor:
        return True, code, f"Profit protection: MFE reached {high_water_return_pct:.1f}% after {trigger:.1f}% trigger, current return fell to {ret_pct:.1f}% below {floor:.1f}% floor."
    return False, "", ""


def _liquidity_exit(exit_rule: dict[str, Any], feature_row: dict[str, Any] | None, holding_days: int, ret_pct: float) -> tuple[bool, str, str]:
    structured = exit_rule.get("liquidity_exit")
    if isinstance(structured, dict) and structured.get("enabled", True):
        after_days = int(structured.get("after_days", 0) or 0)
        if holding_days >= after_days:
            req = structured.get("require_all") or {}
            if not isinstance(req, dict):
                req = {}
            vol_below = threshold(req.get("volume_ratio_20d_below"), feature_row=feature_row, default=None)
            ret_below = threshold(req.get("current_return_pct_below"), feature_row=feature_row, default=None)
            ok = True
            if vol_below is not None:
                ok = ok and f(feature_row, "volume_ratio_20d", 1.0) < vol_below
            if ret_below is not None:
                ok = ok and ret_pct < ret_below
            if ok and (vol_below is not None or ret_below is not None):
                return True, str(structured.get("code") or "LIQUIDITY_DRYUP"), "Discovery liquidity faded while the position had not earned enough cushion."
    return False, "", ""


def _extension_active(exit_rule: dict[str, Any], feature_row: dict[str, Any] | None, position: dict[str, Any], ret_pct: float, high_water_return_pct: float) -> tuple[bool, int | None, str]:
    """Return whether a long-hold extension is active and the extended max days."""
    for key, default_code in [
        ("rerating_continuation", "RERATING_CONTINUES"),
        ("theme_trend_extension", "THEME_TREND_CONTINUES"),
    ]:
        rule = exit_rule.get(key)
        if not isinstance(rule, dict) or not rule.get("enabled", True):
            continue
        max_days_raw = rule.get("extend_max_holding_days_to")
        if max_days_raw is None:
            continue
        require_all = rule.get("require_all") or []
        require_any = rule.get("require_any") or []
        if isinstance(require_all, dict):
            require_all = [{k: v} for k, v in require_all.items()]
        if isinstance(require_any, dict):
            require_any = [{k: v} for k, v in require_any.items()]
        if _passes_all(feature_row, position, ret_pct, high_water_return_pct, require_all) and _passes_any(feature_row, position, ret_pct, high_water_return_pct, require_any):
            try:
                return True, int(max_days_raw), str(rule.get("code") or default_code)
            except Exception:
                continue
    return False, None, ""


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
    ret_pct = (current_price / entry_price - 1.0) * 100.0 if entry_price else 0.0

    hard_stop = threshold(exit_rule.get("hard_stop_loss_pct"), feature_row=feature_row, default=None)
    if hard_stop is not None and ret_pct <= hard_stop:
        return True, "HARD_STOP", f"Hard stop triggered at {ret_pct:.1f}% under {regime_state(feature_row)} regime."

    should, code, text = _early_fail_exit(exit_rule, feature_row, holding_days, ret_pct, high_water_return_pct)
    if should:
        return should, code, text

    # Liquidity/risk exits before ordinary score and structural exits.  This is
    # important for SAGURI, where interest can disappear before score catches up.
    should, code, text = _liquidity_exit(exit_rule, feature_row, holding_days, ret_pct)
    if should:
        return should, code, text

    if "liquidity_score_below" in exit_rule and f(feature_row, "liquidity_score", 1.0) < float(exit_rule["liquidity_score_below"]):
        return True, "LIQUIDITY_DRYUP", "Liquidity score fell below the agent threshold."
    if "avg_traded_value_20d_jpy_below" in exit_rule and f(feature_row, "avg_traded_value_20d_jpy", 10**18) < float(exit_rule["avg_traded_value_20d_jpy_below"]):
        return True, "LIQUIDITY_DRYUP", "Average traded value fell below the agent threshold."
    if "risk_score_below" in exit_rule and f(feature_row, "risk_score", 1.0) < float(exit_rule["risk_score_below"]):
        return True, "CAPITAL_PROTECTION", "Risk score deteriorated below the agent threshold."
    if "volatility_20d_annualized_pct_above" in exit_rule and f(feature_row, "volatility_20d_annualized_pct", 0.0) > float(exit_rule["volatility_20d_annualized_pct_above"]):
        return True, "VOLATILITY_SPIKE", "Volatility spiked beyond the risk budget."

    score = f(score_row, "normalized_score", 1.0)
    if "score_below" in exit_rule and score < float(exit_rule["score_below"]):
        return True, "SCORE_COLLAPSE", "Agent score collapsed below the exit threshold."

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
    if "volume_ratio_20d_below" in exit_rule and f(feature_row, "volume_ratio_20d", 1.0) < float(exit_rule["volume_ratio_20d_below"]):
        return True, "VOLUME_DECAY", "Volume confirmation faded."
    if "rsi_14_above" in exit_rule and f(feature_row, "rsi_14", 0.0) > float(exit_rule["rsi_14_above"]):
        return True, "SNAPBACK_COMPLETE", "RSI normalized after the snapback."
    if "rsi_14_below" in exit_rule and f(feature_row, "rsi_14", 100.0) < float(exit_rule["rsi_14_below"]):
        return True, "PULLBACK_FAILED", "RSI deteriorated below the pullback floor."
    if "bollinger_b_20_above" in exit_rule and f(feature_row, "bollinger_b_20", 0.0) > float(exit_rule["bollinger_b_20_above"]):
        return True, "SNAPBACK_COMPLETE", "Bollinger position normalized after rebound."
    if "range_position_252d_0_1_above" in exit_rule and f(feature_row, "range_position_252d_0_1", 0.0) > float(exit_rule["range_position_252d_0_1_above"]):
        return True, "MISPRICING_RESOLVED", "Price moved high enough in its yearly range to reduce the distortion."
    if "return_20d_pct_above" in exit_rule and f(feature_row, "return_20d_pct", 0.0) > float(exit_rule["return_20d_pct_above"]):
        return True, "MISPRICING_RESOLVED", "Recent re-rating progressed enough to harvest gains."
    if "return_5d_pct_above" in exit_rule and f(feature_row, "return_5d_pct", 0.0) > float(exit_rule["return_5d_pct_above"]):
        return True, "PULLBACK_RESOLVED", "Short-term rebound resolved the pullback."
    if "return_3d_pct_above" in exit_rule and f(feature_row, "return_3d_pct", 0.0) > float(exit_rule["return_3d_pct_above"]):
        return True, "SNAPBACK_COMPLETE", "Three-day rebound reached the snapback target."
    if "return_3d_pct_below" in exit_rule and f(feature_row, "return_3d_pct", 0.0) < float(exit_rule["return_3d_pct_below"]):
        return True, "MOMENTUM_DECAY", "Three-day return deteriorated below the agent threshold."

    take_profit = threshold(exit_rule.get("take_profit_pct"), feature_row=feature_row, default=None)
    if take_profit is not None and ret_pct >= take_profit:
        return True, "TAKE_PROFIT", f"Take-profit target reached at {ret_pct:.1f}%."

    should, code, text = _profit_protection_exit(exit_rule, ret_pct, high_water_return_pct)
    if should:
        return should, code, text

    trailing = threshold(exit_rule.get("trailing_stop_pct"), feature_row=feature_row, default=None)
    if trailing is not None and high_water_return_pct >= trailing and (high_water_return_pct - ret_pct) >= trailing:
        return True, "TRAILING_STOP", "Trailing stop protected prior gains."

    max_days_raw = exit_rule.get("max_holding_days")
    max_days = threshold(max_days_raw, feature_row=feature_row, default=None)
    if max_days is not None:
        extended, extended_max, ext_code = _extension_active(exit_rule, feature_row, position, ret_pct, high_water_return_pct)
        effective_max = float(extended_max if extended and extended_max is not None else max_days)
        if holding_days >= int(effective_max):
            if extended:
                return True, "EXTENDED_MAX_HOLDING_DAYS", f"Extended hold limit reached after {ext_code}."
            return True, "MAX_HOLDING_DAYS", "Maximum holding period reached."

    return False, "", ""
