from __future__ import annotations

"""Portfolio sizing helpers.

The Arena assumes one-share trading. This is not a claim about every broker's
execution model; it is a simulation choice that allows expensive and cheap
Japanese equities to be compared fairly in a game-style league.
"""

import math
from typing import Any


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        v = float(value)
        if math.isfinite(v):
            return v
    except Exception:
        pass
    return default


def apply_bps(price: float, bps: float, side: str) -> float:
    """Apply slippage bps to a raw execution price."""
    p = as_float(price)
    if p <= 0:
        return 0.0
    sign = 1.0 if side.upper() == "BUY" else -1.0
    return p * (1.0 + sign * as_float(bps) / 10000.0)


def conviction_multiplier(score: float, min_score: float) -> float:
    """Convert score excess into a small position-size tilt.

    This is deliberately conservative. Agent personality should mostly come
    from candidate selection and exits, not extreme sizing.
    """
    s = as_float(score)
    m = as_float(min_score)
    if s <= m:
        return 1.0
    return min(1.30, 1.0 + (s - m) * 1.5)


def compute_buy_shares(
    *,
    equity_jpy: float,
    cash_jpy: float,
    execution_price: float,
    score: float,
    min_score: float,
    target_position_pct: float,
    max_position_pct: float,
    max_total_exposure_pct: float,
    current_market_value_jpy: float,
    commission_bps: float,
    share_lot_size: int,
) -> int:
    """Return integer shares to buy, or zero if the order is not affordable."""
    price = as_float(execution_price)
    if price <= 0 or cash_jpy <= 0:
        return 0
    lot = max(1, int(share_lot_size or 1))
    multiplier = conviction_multiplier(score, min_score)
    desired = equity_jpy * as_float(target_position_pct) * multiplier
    desired = min(desired, equity_jpy * as_float(max_position_pct))
    remaining_exposure = max(0.0, equity_jpy * as_float(max_total_exposure_pct) - current_market_value_jpy)
    desired = min(desired, remaining_exposure, cash_jpy)
    if desired <= 0:
        return 0
    gross_price = price * (1.0 + as_float(commission_bps) / 10000.0)
    shares = math.floor(desired / gross_price / lot) * lot
    if shares < lot:
        return 0
    return int(shares)
