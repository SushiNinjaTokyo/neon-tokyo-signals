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
from .market_regime_jp import regime_for_date


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


def boolish(value: Any) -> bool:
    """Return strict truthiness for YAML-style feature gates.

    This avoids treating strings such as "false" as enabled, and makes
    explicit YAML false values disable their gate reliably.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


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
          vf.fundamental_coverage_score,
          vf.sector_33_code,
          vf.sector_33_name,
          vf.valuation_profile,
          vf.theme_tags_json,
          vf.sector_relative_per_discount,
          vf.sector_relative_pbr_discount,
          vf.sector_relative_psr_discount,
          vf.sector_relative_valuation_score,
          vf.sector_relative_quality_score,
          vf.sector_relative_value_confidence
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

    # Attach broad market regime to every security for that signal date.
    # Entry rules can then adjust thresholds without adding columns to
    # features_daily or requiring a schema migration.
    regime = regime_for_date(conn, d)
    for key, value in regime.items():
        rows[key] = value
    return {str(r["ticker"]): r.to_dict() for _, r in rows.iterrows()}


def fetch_score_map(conn: duckdb.DuckDBPyConnection, d: date) -> dict[tuple[str, str], dict[str, Any]]:
    rows = conn.execute("SELECT * FROM agent_scores_daily WHERE date = ?", [d]).fetchdf()
    if rows.empty:
        return {}
    return {(str(r["agent_id"]), str(r["ticker"])): r.to_dict() for _, r in rows.iterrows()}


def _bucket_allowed(score_row: dict[str, Any], feature_row: dict[str, Any], entry: dict[str, Any]) -> tuple[bool, str]:
    bucket = text(score_row.get("universe_bucket") or feature_row.get("bucket"), "").strip()
    if not bucket:
        bucket = "unknown"
    if "require_bucket" in entry and bucket != text(entry.get("require_bucket")):
        return False, "bucket_not_allowed"
    allowed = entry.get("allowed_buckets")
    if allowed:
        allowed_set = {text(x).strip() for x in allowed}
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
        ("require_sector_relative_valuation_score_min", "sector_relative_valuation_score", "sector_relative_valuation_below_threshold", ">="),
        ("require_sector_relative_quality_score_min", "sector_relative_quality_score", "sector_relative_quality_below_threshold", ">="),
        ("require_sector_relative_value_confidence_min", "sector_relative_value_confidence", "sector_relative_value_confidence_below_threshold", ">="),
        ("reject_if_sector_relative_valuation_score_lt", "sector_relative_valuation_score", "sector_relative_valuation_too_weak", ">="),
        ("reject_if_sector_relative_quality_score_lt", "sector_relative_quality_score", "sector_relative_quality_too_weak", ">="),
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
    if "require_liquidity_score_min" in setup and num(feature_row.get("liquidity_score")) < num(setup["require_liquidity_score_min"]):
        return False, "liquidity_below_threshold"
    if "require_avg_traded_value_20d_jpy_min" in setup and num(feature_row.get("avg_traded_value_20d_jpy")) < num(setup["require_avg_traded_value_20d_jpy_min"]):
        return False, "traded_value_below_threshold"
    if "require_volume_ratio_20d_min" in setup and num(feature_row.get("volume_ratio_20d")) < num(setup["require_volume_ratio_20d_min"]):
        return False, "volume_ratio_below_threshold"
    if "require_range_position_60d_0_1_min" in setup and num(feature_row.get("range_position_60d_0_1")) < num(setup["require_range_position_60d_0_1_min"]):
        return False, "range_position_60d_too_low"
    if "require_range_position_20d_0_1_min" in setup and num(feature_row.get("range_position_20d_0_1")) < num(setup["require_range_position_20d_0_1_min"]):
        return False, "range_position_20d_too_low"
    return True, "discovery_financial_setup_passed"




def _passes_discovery_score_setup(score_row: dict[str, Any], feature_row: dict[str, Any], setup: dict[str, Any]) -> tuple[bool, str]:
    """Alternative bucket bypass for SAGURI-style discovery candidates.

    This allows a stock to pass the bucket gate when the source bucket taxonomy is
    too coarse, while still requiring a credible small-cap/liquidity/momentum
    setup.  It only bypasses bucket validation; the normal entry gates below
    still run afterward.
    """
    if not setup:
        return False, "discovery_score_setup_missing"
    if "min_score" in setup and num(score_row.get("normalized_score")) < num(setup["min_score"]):
        return False, "score_below_discovery_setup_threshold"
    if "require_market_cap_jpy_min" in setup and num(feature_row.get("market_cap_jpy")) < num(setup["require_market_cap_jpy_min"]):
        return False, "market_cap_too_small"
    if "require_market_cap_jpy_max" in setup and num(feature_row.get("market_cap_jpy")) > num(setup["require_market_cap_jpy_max"]):
        return False, "market_cap_too_large"
    if "require_liquidity_score_min" in setup and num(feature_row.get("liquidity_score")) < num(setup["require_liquidity_score_min"]):
        return False, "liquidity_below_threshold"
    if "require_volume_ratio_20d_min" in setup and num(feature_row.get("volume_ratio_20d")) < num(setup["require_volume_ratio_20d_min"]):
        return False, "volume_ratio_below_threshold"
    if "require_range_position_60d_0_1_min" in setup and num(feature_row.get("range_position_60d_0_1")) < num(setup["require_range_position_60d_0_1_min"]):
        return False, "range_position_60d_too_low"
    if "require_range_position_20d_0_1_min" in setup and num(feature_row.get("range_position_20d_0_1")) < num(setup["require_range_position_20d_0_1_min"]):
        return False, "range_position_20d_too_low"
    return True, "discovery_score_setup_passed"



def _passes_value_rerating_confirmation(feature_row: dict[str, Any], entry: dict[str, Any]) -> tuple[bool, str]:
    """Require a concrete re-rating signal for HIZUMI-style value entries.

    Cheap stocks can remain cheap.  This confirmation gate lets a candidate pass
    when at least one price/re-rating signal indicates that the market has begun
    to recognize the mispricing.
    """
    if not boolish(entry.get("require_value_rerating_confirmation")):
        return True, "value_rerating_confirmation_not_required"

    setup = entry.get("rerating_confirmation_any") or {}
    if not setup:
        return False, "value_rerating_confirmation_missing"

    checks: list[tuple[bool, str]] = []
    close = num(feature_row.get("close"))

    if boolish(setup.get("price_above_ma20")):
        checks.append((close > num(feature_row.get("ma_20")), "price_above_ma20"))
    if "return_5d_pct_min" in setup:
        checks.append((num(feature_row.get("return_5d_pct")) >= num(setup.get("return_5d_pct_min")), "return_5d_recovered"))
    if "return_20d_pct_min" in setup:
        checks.append((num(feature_row.get("return_20d_pct")) >= num(setup.get("return_20d_pct_min")), "return_20d_positive"))
    if "return_60d_pct_min" in setup:
        checks.append((num(feature_row.get("return_60d_pct")) >= num(setup.get("return_60d_pct_min")), "return_60d_positive"))
    if "range_position_20d_0_1_min" in setup:
        checks.append((num(feature_row.get("range_position_20d_0_1")) >= num(setup.get("range_position_20d_0_1_min")), "range_position_20d_recovered"))
    if "range_position_60d_0_1_min" in setup:
        checks.append((num(feature_row.get("range_position_60d_0_1")) >= num(setup.get("range_position_60d_0_1_min")), "range_position_60d_recovered"))
    if "re_rating_signal_score_min" in setup:
        checks.append((num(feature_row.get("re_rating_signal_score")) >= num(setup.get("re_rating_signal_score_min")), "rerating_signal_score_ok"))
    if "volume_ratio_20d_min" in setup:
        checks.append((num(feature_row.get("volume_ratio_20d")) >= num(setup.get("volume_ratio_20d_min")), "volume_rerating_confirmation"))

    if any(ok for ok, _ in checks):
        passed = [name for ok, name in checks if ok]
        return True, "value_rerating_confirmation_passed:" + ",".join(passed[:3])
    return False, "value_rerating_confirmation_failed"




def market_regime_state(feature_row: dict[str, Any] | None) -> str:
    if not feature_row:
        return "NEUTRAL"
    state = text(feature_row.get("market_regime_state"), "NEUTRAL").upper().strip()
    return state if state in {"BULL", "NEUTRAL", "BEAR", "PANIC"} else "NEUTRAL"


def effective_entry_rule(entry: dict[str, Any], feature_row: dict[str, Any] | None) -> dict[str, Any]:
    """Return entry rules after applying market-regime overrides.

    YAML can define:

      market_regime_rules:
        BULL: {min_score: 0.66}
        BEAR: {min_score: 0.74, position_size_multiplier: 0.5}
        PANIC: {new_entries_enabled: false}

    The returned dict is a shallow merge; top-level regime keys override base
    entry keys. Nested fields that are not explicitly overridden remain intact.
    """
    merged = dict(entry or {})
    state = market_regime_state(feature_row)
    rules = entry.get("market_regime_rules") or {}
    override = rules.get(state) or rules.get(state.lower()) or {}
    if isinstance(override, dict):
        for k, v in override.items():
            if k == "note":
                continue
            merged[k] = v
    merged["_market_regime_state"] = state
    return merged


def entry_position_size_multiplier(agent_rule: dict[str, Any], feature_row: dict[str, Any] | None) -> float:
    entry = effective_entry_rule((agent_rule.get("entry") or {}), feature_row)
    raw = entry.get("position_size_multiplier", 1.0)
    try:
        v = float(raw)
        if v <= 0:
            return 0.0
        return max(0.0, min(1.0, v))
    except Exception:
        return 1.0



def _eval_feature_condition(feature_row: dict[str, Any], condition_key: str, threshold: Any) -> bool:
    """Evaluate a compact YAML condition such as return_5d_pct_gt: 18.

    Supported suffixes are _gt, _gte, _lt, _lte, and _between.  The feature
    name is the condition key without the suffix.  Missing values never pass a
    soft guard condition; this keeps the guard conservative and prevents sparse
    fundamentals from accidentally excluding otherwise valid candidates.
    """
    suffix_ops = (
        ("_between", "between"),
        ("_gte", ">="),
        ("_lte", "<="),
        ("_gt", ">"),
        ("_lt", "<"),
    )
    for suffix, op in suffix_ops:
        if condition_key.endswith(suffix):
            feature_key = condition_key[: -len(suffix)]
            actual_raw = feature_row.get(feature_key)
            if actual_raw is None:
                return False
            actual = num(actual_raw)
            if op == "between":
                try:
                    lo, hi = threshold
                except Exception:
                    return False
                return num(lo) <= actual <= num(hi)
            target = num(threshold)
            if op == ">":
                return actual > target
            if op == ">=":
                return actual >= target
            if op == "<":
                return actual < target
            if op == "<=":
                return actual <= target
    return False


def _conditions_pass(feature_row: dict[str, Any], conditions: dict[str, Any] | None, *, mode: str) -> bool:
    if not isinstance(conditions, dict) or not conditions:
        return False
    results = [_eval_feature_condition(feature_row, key, value) for key, value in conditions.items()]
    if mode == "all":
        return all(results)
    if mode == "any":
        return any(results)
    return False


def _passes_soft_rejects(feature_row: dict[str, Any], entry: dict[str, Any]) -> tuple[bool, str]:
    """Apply optional soft exclusion blocks for fragile entries.

    These are intentionally data-driven and conservative.  A rule rejects only
    when its `all` block is fully true, optionally combined with `any`.  If
    `unless_any` is present and at least one recovery/confirmation condition is
    true, the candidate is allowed through.  This is used for SAGURI overheat
    avoidance and KAESHI falling-knife avoidance without making either strategy
    inert.
    """
    rules = entry.get("soft_rejects") or []
    if not isinstance(rules, list):
        return True, "soft_rejects_not_configured"

    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            continue
        all_conditions = rule.get("all") or {}
        any_conditions = rule.get("any") or {}
        unless_any = rule.get("unless_any") or {}

        all_ok = _conditions_pass(feature_row, all_conditions, mode="all") if all_conditions else True
        any_ok = _conditions_pass(feature_row, any_conditions, mode="any") if any_conditions else True
        if not (all_ok and any_ok):
            continue
        if unless_any and _conditions_pass(feature_row, unless_any, mode="any"):
            continue

        reason = text(rule.get("reason"), f"soft_reject_{idx}").strip() or f"soft_reject_{idx}"
        return False, reason

    return True, "soft_rejects_passed"

def _passes_reversal_confirmation(feature_row: dict[str, Any], entry: dict[str, Any]) -> tuple[bool, str]:
    """Count snapback confirmation signals for KAESHI-style entries."""
    min_count = int(entry.get("reversal_confirmation_min_count", 0) or 0)
    setup = entry.get("reversal_confirmation_any") or {}
    if min_count <= 0 and not setup:
        return True, "reversal_confirmation_not_required"

    checks: list[tuple[bool, str]] = []
    if "return_1d_pct_min" in setup:
        checks.append((num(feature_row.get("return_1d_pct")) >= num(setup.get("return_1d_pct_min")), "positive_1d_return"))
    if "volume_ratio_20d_min" in setup:
        checks.append((num(feature_row.get("volume_ratio_20d")) >= num(setup.get("volume_ratio_20d_min")), "volume_confirmation"))
    if "range_position_20d_0_1_min" in setup:
        checks.append((num(feature_row.get("range_position_20d_0_1")) >= num(setup.get("range_position_20d_0_1_min")), "range_recovery_20d"))
    if "price_above_ma5" in setup and boolish(setup.get("price_above_ma5")):
        checks.append((num(feature_row.get("close")) > num(feature_row.get("ma_5")), "price_above_ma5"))
    if "volume_reaccumulation_score_min" in setup:
        checks.append((num(feature_row.get("volume_reaccumulation_score")) >= num(setup.get("volume_reaccumulation_score_min")), "reaccumulation"))

    passed = [name for ok, name in checks if ok]
    required = min_count if min_count > 0 else 1
    if len(passed) >= required:
        return True, "reversal_confirmation_passed:" + ",".join(passed[:4])
    return False, f"reversal_confirmation_failed:{len(passed)}/{required}"

def passes_entry_rule(
    *,
    score_row: dict[str, Any],
    feature_row: dict[str, Any] | None,
    agent_rule: dict[str, Any],
    trading_dates: list[date],
    signal_date: date,
) -> tuple[bool, str]:
    """Return whether a scored row is eligible for a new position."""
    base_entry = agent_rule.get("entry", {}) or {}
    common = agent_rule.get("common", {}) or {}
    if not feature_row:
        return False, "missing_feature_row"
    entry = effective_entry_rule(base_entry, feature_row)

    if boolish(entry.get("new_entries_enabled")) is False and "new_entries_enabled" in entry:
        return False, f"market_regime_{market_regime_state(feature_row).lower()}_entry_disabled"

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
        bypass_ok = False
        bypass_reasons: list[str] = []

        # SAGURI/discovery rules can bypass imperfect bucket taxonomy if the
        # stock independently satisfies a financial discovery setup.
        if boolish(entry.get("bucket_optional_if_financial_setup")) or boolish(entry.get("allow_bucket_bypass_for_discovery_setup")):
            setup_ok, setup_reason = _passes_discovery_financial_setup(feature_row, entry.get("discovery_financial_setup") or {})
            bypass_ok = bypass_ok or setup_ok
            if not setup_ok:
                bypass_reasons.append(setup_reason)

        # A second, lighter bypass allows high-quality early discovery setups
        # based on score + volume + market-cap range, while all normal gates
        # still run below.
        if boolish(entry.get("bucket_optional_if_score_setup")) or boolish(entry.get("allow_bucket_bypass_for_discovery_setup")):
            score_setup_ok, score_setup_reason = _passes_discovery_score_setup(score_row, feature_row, entry.get("discovery_score_setup") or {})
            bypass_ok = bypass_ok or score_setup_ok
            if not score_setup_ok:
                bypass_reasons.append(score_setup_reason)

        if not bypass_ok:
            # Prefer the most informative setup failure over the generic bucket
            # failure so diagnostics explain what would have allowed bypass.
            return False, bypass_reasons[0] if bypass_reasons else bucket_reason

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

    if boolish(entry.get("require_price_above_ma20")) and close <= num(feature_row.get("ma_20")):
        return False, "price_not_above_ma20"
    if boolish(entry.get("require_price_above_ma50")) and close <= num(feature_row.get("ma_50")):
        return False, "price_not_above_ma50"
    if boolish(entry.get("require_price_above_ma120")) and close <= num(feature_row.get("ma_120")):
        return False, "price_not_above_ma120"

    if "require_volume_ratio_20d_min" in entry and num(feature_row.get("volume_ratio_20d")) < num(entry["require_volume_ratio_20d_min"]):
        return False, "volume_ratio_below_threshold"
    if "require_return_1d_pct_min" in entry and num(feature_row.get("return_1d_pct")) < num(entry["require_return_1d_pct_min"]):
        return False, "one_day_return_too_low"
    if "require_return_5d_pct_min" in entry and num(feature_row.get("return_5d_pct")) < num(entry["require_return_5d_pct_min"]):
        return False, "five_day_return_too_low"
    if "require_return_20d_pct_min" in entry and num(feature_row.get("return_20d_pct")) < num(entry["require_return_20d_pct_min"]):
        return False, "twenty_day_return_too_low"
    if "require_range_position_20d_0_1_min" in entry and num(feature_row.get("range_position_20d_0_1")) < num(entry["require_range_position_20d_0_1_min"]):
        return False, "range_position_20d_too_low"
    if "require_range_position_60d_0_1_min" in entry and num(feature_row.get("range_position_60d_0_1")) < num(entry["require_range_position_60d_0_1_min"]):
        return False, "range_position_60d_too_low"
    if "require_range_position_252d_0_1_min" in entry and num(feature_row.get("range_position_252d_0_1")) < num(entry["require_range_position_252d_0_1_min"]):
        return False, "year_range_position_too_low"
    if "require_range_position_252d_0_1_max" in entry and num(feature_row.get("range_position_252d_0_1")) > num(entry["require_range_position_252d_0_1_max"]):
        return False, "year_range_position_too_high"
    if "reject_if_range_position_252d_0_1_lt" in entry and num(feature_row.get("range_position_252d_0_1")) < num(entry["reject_if_range_position_252d_0_1_lt"]):
        return False, "year_range_position_extremely_low"

    if "reject_if_rsi_14_gt" in entry and num(feature_row.get("rsi_14")) > num(entry["reject_if_rsi_14_gt"]):
        return False, "rsi_overheated"
    if "reject_if_rsi_14_lt" in entry and num(feature_row.get("rsi_14")) < num(entry["reject_if_rsi_14_lt"]):
        return False, "rsi_extremely_weak"
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
    if "reject_if_return_5d_pct_lt" in entry and num(feature_row.get("return_5d_pct")) < num(entry["reject_if_return_5d_pct_lt"]):
        return False, "five_day_falling_knife"
    if "reject_if_return_20d_pct_gt" in entry and num(feature_row.get("return_20d_pct")) > num(entry["reject_if_return_20d_pct_gt"]):
        return False, "twenty_day_move_too_extended"
    if "reject_if_return_20d_pct_lt" in entry and num(feature_row.get("return_20d_pct")) < num(entry["reject_if_return_20d_pct_lt"]):
        return False, "pullback_too_deep"
    if "reject_if_price_vs_ma50_pct_lt" in entry and num(feature_row.get("price_vs_ma50_pct")) < num(entry["reject_if_price_vs_ma50_pct_lt"]):
        return False, "price_vs_ma50_too_low"

    euphoria = entry.get("reject_if_short_term_euphoria") or {}
    if isinstance(euphoria, dict) and euphoria:
        euphoria_hits = []
        if "return_5d_pct_gt" in euphoria:
            euphoria_hits.append(num(feature_row.get("return_5d_pct")) > num(euphoria.get("return_5d_pct_gt")))
        if "return_20d_pct_gt" in euphoria:
            euphoria_hits.append(num(feature_row.get("return_20d_pct")) > num(euphoria.get("return_20d_pct_gt")))
        if "rsi_14_gt" in euphoria:
            euphoria_hits.append(num(feature_row.get("rsi_14")) > num(euphoria.get("rsi_14_gt")))
        if "volume_ratio_20d_gt" in euphoria:
            euphoria_hits.append(num(feature_row.get("volume_ratio_20d")) > num(euphoria.get("volume_ratio_20d_gt")))
        if euphoria_hits and all(euphoria_hits):
            return False, "short_term_euphoria_rejected"
    if "require_trend_score_weekly_proxy_min" in entry and num(feature_row.get("trend_score_weekly_proxy")) < num(entry["require_trend_score_weekly_proxy_min"]):
        return False, "weekly_trend_too_weak"

    ok, reason = _passes_soft_rejects(feature_row, entry)
    if not ok:
        return False, reason

    ok, reason = _passes_value_rerating_confirmation(feature_row, entry)
    if not ok:
        return False, reason

    ok, reason = _passes_reversal_confirmation(feature_row, entry)
    if not ok:
        return False, reason

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
