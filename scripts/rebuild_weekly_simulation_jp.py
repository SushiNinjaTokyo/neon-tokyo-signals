#!/usr/bin/env python3
"""
Rebuild Japan Weekly Simulation for Neon Tokyo Signals.

Input:
- site/data/prices-jp/latest.json
- data/weekly_candidates_jp.csv, fallback data/universe_jp.csv
- scripts/build_weekly_jp.py scoring functions

Output:
- site/data/japan/weekly/simulation/latest.json
- site/data/japan/weekly/simulation/YYYY-MM-DD.json
- site/data/japan/weekly/simulation/manifest.json
- compatibility copy: site/data/weekly-jp/simulation/latest.json

Design:
- No API calls. Uses cached JP prices only.
- Weekly decisions are made on weekly evaluation dates.
- Orders execute at the next trading day's open.
- Cash accounting is explicit: cash + market value = portfolio equity.
- Benchmark comparison uses TOPIX ETF with the same cash flow per position.
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

try:
    import build_weekly_jp as weekly
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Failed to import scripts/build_weekly_jp.py. Run Weekly JP screening setup first.") from exc

TZ = ZoneInfo("Asia/Tokyo")

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
OUT_DIR = (ROOT / OUT_DIR).resolve() if not OUT_DIR.is_absolute() else OUT_DIR.resolve()

PRICES_JSON = Path(os.getenv("PRICES_JSON", str(OUT_DIR / "data" / "prices-jp" / "latest.json")))
PRICES_JSON = (ROOT / PRICES_JSON).resolve() if not PRICES_JSON.is_absolute() else PRICES_JSON.resolve()

OUT_SIM_DIR = OUT_DIR / "data" / "japan" / "weekly" / "simulation"
LEGACY_OUT_SIM_DIR = OUT_DIR / "data" / "weekly-jp" / "simulation"

WEEKS = int(os.getenv("WEEKLY_JP_SIM_WEEKS", os.getenv("WEEKS", "32")))
END_DATE_ENV = os.getenv("WEEKLY_JP_SIM_END_DATE", os.getenv("END_DATE", "")).strip()
MIN_WEEKLY_BARS = int(os.getenv("WEEKLY_JP_MIN_WEEKLY_BARS", "40"))
RANK_LIMIT = min(10, max(1, int(os.getenv("WEEKLY_JP_SIM_RANK_LIMIT", "10"))))
INITIAL_CAPITAL = float(os.getenv("WEEKLY_JP_SIM_INITIAL_CAPITAL", "10000000"))
POSITION_PCT = float(os.getenv("WEEKLY_JP_SIM_POSITION_PCT", "0.125"))
MAX_POSITIONS = int(os.getenv("WEEKLY_JP_SIM_MAX_POSITIONS", "8"))
MAX_NEW_POSITIONS_PER_WEEK = int(os.getenv("WEEKLY_JP_SIM_MAX_NEW_POSITIONS_PER_WEEK", "3"))
MIN_ENTRY_SCORE = int(os.getenv("WEEKLY_JP_SIM_MIN_ENTRY_SCORE", "600"))
REINVESTMENT_MIN_SCORE = int(os.getenv("WEEKLY_JP_SIM_REINVESTMENT_MIN_SCORE", "650"))
SCORE_EXIT = int(os.getenv("WEEKLY_JP_SIM_SCORE_EXIT", "560"))
STOP_PCT = float(os.getenv("WEEKLY_JP_SIM_STOP_PCT", "-8"))
TAKE_PROFIT_EXTREME_PCT = float(os.getenv("WEEKLY_JP_SIM_TAKE_PROFIT_EXTREME_PCT", "45"))
TIME_EXIT_WEEKS = int(os.getenv("WEEKLY_JP_SIM_TIME_EXIT_WEEKS", "12"))
BUY_SLIPPAGE_PCT = float(os.getenv("WEEKLY_JP_SIM_BUY_SLIPPAGE_PCT", "0.15"))
SELL_SLIPPAGE_PCT = float(os.getenv("WEEKLY_JP_SIM_SELL_SLIPPAGE_PCT", "0.15"))
ROUND_LOT = int(os.getenv("WEEKLY_JP_SIM_ROUND_LOT", "100"))
ALLOW_WATCH = os.getenv("WEEKLY_JP_SIM_ALLOW_WATCH", "true").lower() in {"1", "true", "yes"}
BENCHMARK_SYMBOL = os.getenv("WEEKLY_JP_SIM_BENCHMARK_SYMBOL", "1306.T")
BENCHMARK_RETURN_ABS_LIMIT_PCT = float(os.getenv("WEEKLY_JP_BENCHMARK_RETURN_ABS_LIMIT_PCT", "35"))
WRITE_LEGACY_COPY = os.getenv("WEEKLY_WRITE_LEGACY_COPY", "true").lower() in {"1", "true", "yes"}


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
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")
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


def pct(cur: Any, base: Any) -> float | None:
    c = to_float(cur)
    b = to_float(base)
    if c is None or b is None or b <= 0:
        return None
    return (c / b - 1.0) * 100.0


def avg(values: list[float]) -> float | None:
    clean = [x for x in values if x is not None and math.isfinite(float(x))]
    if not clean:
        return None
    return sum(clean) / len(clean)


def median(values: list[float]) -> float | None:
    clean = sorted([x for x in values if x is not None and math.isfinite(float(x))])
    if not clean:
        return None
    n = len(clean)
    mid = n // 2
    if n % 2:
        return clean[mid]
    return (clean[mid - 1] + clean[mid]) / 2.0


def load_prices() -> dict[str, Any]:
    prices = read_json(PRICES_JSON)
    if not isinstance(prices.get("items"), list):
        raise ValueError("prices JSON has no items list")
    return prices


def equity_items(prices: dict[str, Any]) -> list[dict[str, Any]]:
    raw = prices.get("equities") or []
    if not raw:
        raw = [x for x in prices.get("items") or [] if not x.get("pulse_label")]
    meta = weekly.load_candidate_meta()
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol") or "")
        if symbol in meta:
            out.append(item)
    return out


def pulse_items(prices: dict[str, Any]) -> list[dict[str, Any]]:
    return [x for x in prices.get("market_pulse") or [] if isinstance(x, dict)]


def get_item_by_symbol(prices: dict[str, Any], symbol: str) -> dict[str, Any] | None:
    for item in (prices.get("items") or []) + (prices.get("market_pulse") or []) + (prices.get("equities") or []):
        if isinstance(item, dict) and str(item.get("symbol") or "") == symbol:
            return item
    return None


def get_benchmark_item(prices: dict[str, Any]) -> dict[str, Any] | None:
    for item in pulse_items(prices):
        if str(item.get("symbol") or "") == BENCHMARK_SYMBOL:
            return item
        if str(item.get("pulse_label") or "").upper() == "TOPIX":
            return item
    return get_item_by_symbol(prices, BENCHMARK_SYMBOL)


def clone_with_bars_until(item: dict[str, Any], eval_date: pd.Timestamp) -> dict[str, Any]:
    bars: list[dict[str, Any]] = []
    for bar in item.get("bars") or []:
        try:
            d = pd.Timestamp(bar.get("date"))
        except Exception:
            continue
        if pd.notna(d) and d <= eval_date:
            bars.append(bar)
    cloned = dict(item)
    cloned["bars"] = bars
    cloned["bars_count"] = len(bars)
    if bars:
        cloned["date_start"] = bars[0].get("date")
        cloned["date_end"] = bars[-1].get("date")
    return cloned


def build_truncated_price_payload(prices: dict[str, Any], eval_date: pd.Timestamp) -> dict[str, Any]:
    return {
        **prices,
        "items": [clone_with_bars_until(x, eval_date) for x in prices.get("items") or []],
        "market_pulse": [clone_with_bars_until(x, eval_date) for x in pulse_items(prices)],
        "equities": [clone_with_bars_until(x, eval_date) for x in equity_items(prices)],
    }


def trading_week_eval_dates(prices: dict[str, Any], end_date: pd.Timestamp | None) -> list[pd.Timestamp]:
    benchmark = get_benchmark_item(prices)
    if benchmark is None:
        items = equity_items(prices)
        if not items:
            return []
        benchmark = items[0]
    df = weekly.bars_to_df(benchmark)
    if df.empty:
        return []
    if end_date is not None:
        df = df[df.index <= end_date]
    if df.empty:
        return []
    daily_dates = pd.Series(df.index, index=df.index)
    grouped = daily_dates.groupby(pd.Grouper(freq="W-FRI")).max().dropna()
    return [pd.Timestamp(x).normalize() for x in grouped.tolist()]


def price_df(item: dict[str, Any]) -> pd.DataFrame:
    return weekly.bars_to_df(item)


def index_for_or_prior(df: pd.DataFrame, date: pd.Timestamp) -> int | None:
    if df.empty:
        return None
    target = pd.Timestamp(date).normalize()
    idxs = [pd.Timestamp(x).normalize() for x in df.index]
    prior = [i for i, d in enumerate(idxs) if d <= target]
    if not prior:
        return None
    return max(prior)


def next_open_after(df: pd.DataFrame, eval_date: pd.Timestamp) -> dict[str, Any] | None:
    idx = index_for_or_prior(df, eval_date)
    if idx is None:
        return None
    ni = idx + 1
    if ni >= len(df):
        return None
    row = df.iloc[ni]
    price = to_float(row.get("Open")) or to_float(row.get("Close"))
    if price is None or price <= 0:
        return None
    return {"date": str(pd.Timestamp(row.name).date()), "price": price}


def close_at_or_prior(df: pd.DataFrame, eval_date: pd.Timestamp) -> dict[str, Any] | None:
    idx = index_for_or_prior(df, eval_date)
    if idx is None:
        return None
    row = df.iloc[idx]
    price = to_float(row.get("Close"))
    if price is None or price <= 0:
        return None
    return {"date": str(pd.Timestamp(row.name).date()), "price": price}


def valid_benchmark_price_move(entry: float | None, current: float | None) -> bool:
    if entry is None or current is None or entry <= 0:
        return False
    ret = (current / entry - 1.0) * 100.0
    return abs(ret) <= BENCHMARK_RETURN_ABS_LIMIT_PCT


def score_snapshot(prices: dict[str, Any], eval_date: pd.Timestamp) -> list[dict[str, Any]]:
    truncated = build_truncated_price_payload(prices, eval_date)
    meta = weekly.load_candidate_meta()
    topix_row, _, _ = weekly.benchmark_weekly(truncated)
    scored: list[dict[str, Any]] = []
    for raw in equity_items(truncated):
        symbol = str(raw.get("symbol") or "")
        if not symbol:
            continue
        try:
            item = weekly.score_item(raw, meta.get(symbol, {}), topix_row)
            if item:
                scored.append(item)
        except Exception:
            continue
    scored.sort(key=lambda x: (int(x.get("score_pts") or 0), str(x.get("symbol") or "")), reverse=True)
    for i, item in enumerate(scored, start=1):
        item["rank"] = i
    return scored[:RANK_LIMIT]


def normalize_signal(value: Any) -> str:
    s = str(value or "").strip()
    if s == "Watch":
        return "Monitor"
    return s or "Unknown"


def is_entry_candidate(item: dict[str, Any], existing_symbols: set[str], cash: float) -> tuple[bool, str]:
    symbol = str(item.get("symbol") or "")
    if not symbol:
        return False, "missing symbol"
    if symbol in existing_symbols:
        return False, "already held"
    signal = normalize_signal(item.get("signal"))
    score = int(item.get("score_pts") or 0)
    quality = str(item.get("quality") or "")
    liq = str(item.get("liquidity_band") or "")
    extension = str(item.get("extension_status") or "")
    flags = set(item.get("flags") or [])
    if signal == "Trade":
        pass
    elif signal == "Monitor" and ALLOW_WATCH:
        pass
    else:
        return False, "not trade or monitor"
    if score < MIN_ENTRY_SCORE:
        return False, f"score below entry floor {MIN_ENTRY_SCORE}"
    if signal == "Monitor" and score < MIN_ENTRY_SCORE:
        return False, "monitor score too low"
    if quality in {"D Extended", "E Avoid"}:
        return False, "quality blocked"
    if liq in {"Very Thin", "Unknown"}:
        return False, "liquidity blocked"
    if extension == "Extreme":
        return False, "extreme extension"
    if "distribution_week" in flags or "weak_close" in flags:
        return False, "distribution / weak close"
    if cash <= 0:
        return False, "no cash"
    return True, "eligible"


def build_lot(symbol: str, item: dict[str, Any], price: float, date: str, equity: float, cash: float, bench_price: float | None) -> dict[str, Any] | None:
    raw_target = max(0.0, equity * POSITION_PCT)
    budget = min(cash, raw_target)
    if budget <= 0 or price <= 0:
        return None
    execution_price = price * (1.0 + BUY_SLIPPAGE_PCT / 100.0)
    lot = max(1, ROUND_LOT)
    shares = math.floor(budget / execution_price / lot) * lot
    if shares <= 0:
        return None
    cost = shares * execution_price
    if cost > cash + 1e-6:
        return None
    bench_units = None
    if bench_price is not None and bench_price > 0:
        bench_units = cost / bench_price
    return {
        "symbol": symbol,
        "name": item.get("name"),
        "theme": item.get("theme"),
        "bucket": item.get("bucket"),
        "entry_signal": normalize_signal(item.get("signal")),
        "entry_quality": item.get("quality"),
        "entry_rank": item.get("rank"),
        "entry_score_pts": item.get("score_pts"),
        "entry_date": date,
        "entry_price": safe_round(execution_price, 4),
        "raw_entry_open": safe_round(price, 4),
        "shares": shares,
        "cost_basis": safe_round(cost, 2),
        "cash_flow": safe_round(-cost, 2),
        "benchmark_entry_price": safe_round(bench_price, 4),
        "benchmark_units": safe_round(bench_units, 8),
        "weeks_held": 0,
        "max_unrealized_pct": 0.0,
        "min_unrealized_pct": 0.0,
        "last_score_pts": item.get("score_pts"),
        "last_signal": normalize_signal(item.get("signal")),
        "last_quality": item.get("quality"),
    }


def should_exit(pos: dict[str, Any], current_item: dict[str, Any] | None, current_price: float | None) -> tuple[bool, str]:
    entry = to_float(pos.get("entry_price"))
    if entry is None or current_price is None or entry <= 0:
        return False, "no current price"
    unreal = (current_price / entry - 1.0) * 100.0
    weeks_held = int(pos.get("weeks_held") or 0)
    if unreal <= STOP_PCT:
        return True, f"close stop {STOP_PCT:.1f}%"
    if unreal >= TAKE_PROFIT_EXTREME_PCT:
        return True, "extreme profit / extension harvest"
    if weeks_held >= TIME_EXIT_WEEKS:
        return True, f"time exit {TIME_EXIT_WEEKS}w"
    if current_item is None:
        return False, "not scored this week"
    score = int(current_item.get("score_pts") or 0)
    signal = normalize_signal(current_item.get("signal"))
    quality = str(current_item.get("quality") or "")
    flags = set(current_item.get("flags") or [])
    if score < SCORE_EXIT:
        return True, f"score exit < {SCORE_EXIT}"
    if quality == "E Avoid" and score < REINVESTMENT_MIN_SCORE:
        return True, "quality exit"
    if "distribution_week" in flags or "weak_close" in flags:
        return True, "distribution / weak close exit"
    if signal == "Avoid" and score < REINVESTMENT_MIN_SCORE:
        return True, "signal exit"
    return False, "hold"




def sanitize_benchmark_curve(curve: list[dict[str, Any]], external_capital: float) -> dict[str, Any]:
    """
    Detect and neutralize broken TOPIX benchmark observations.

    yfinance can occasionally return split/adjustment artifacts for JP ETFs
    such as 1306.T. A -90% benchmark move would make strategy alpha and the
    benchmark equity curve meaningless. Raw strategy accounting is preserved;
    only benchmark-derived values are suspended.
    """
    stats = {
        "benchmark_symbol": BENCHMARK_SYMBOL,
        "abs_return_limit_pct": BENCHMARK_RETURN_ABS_LIMIT_PCT,
        "total_points": len(curve),
        "valid_points": 0,
        "invalid_points": 0,
        "status": "valid",
        "message": "Benchmark data passed sanity checks.",
        "invalid_samples": [],
    }

    if not curve or not external_capital or external_capital <= 0:
        stats["status"] = "missing"
        stats["message"] = "Benchmark comparison unavailable because the equity curve or capital base is missing."
        return stats

    invalid_started = False
    for point in curve:
        ret = to_float(point.get("benchmark_return_pct"))
        eq = to_float(point.get("benchmark_equity"))
        invalid_reason = None

        if ret is None or eq is None or eq <= 0:
            invalid_reason = "missing benchmark mark"
        elif abs(ret) > BENCHMARK_RETURN_ABS_LIMIT_PCT:
            invalid_reason = f"benchmark return {ret:.2f}% exceeds ±{BENCHMARK_RETURN_ABS_LIMIT_PCT:.1f}% guardrail"

        # Once a split/adjustment artifact appears, later points are usually on
        # a different price scale. Do not resume the benchmark line after that.
        if invalid_started and invalid_reason is None:
            invalid_reason = "benchmark scale invalid after prior anomaly"

        if invalid_reason:
            invalid_started = True
            point["benchmark_quality"] = "invalid"
            point["benchmark_quality_reason"] = invalid_reason
            point["benchmark_equity_raw"] = point.get("benchmark_equity")
            point["benchmark_return_pct_raw"] = point.get("benchmark_return_pct")
            point["benchmark_equity"] = None
            point["benchmark_return_pct"] = None
            stats["invalid_points"] += 1
            if len(stats["invalid_samples"]) < 8:
                stats["invalid_samples"].append({
                    "date": point.get("date"),
                    "benchmark_equity_raw": point.get("benchmark_equity_raw"),
                    "benchmark_return_pct_raw": point.get("benchmark_return_pct_raw"),
                    "reason": invalid_reason,
                })
        else:
            point["benchmark_quality"] = "valid"
            point["benchmark_quality_reason"] = None
            stats["valid_points"] += 1

    if stats["invalid_points"]:
        stats["status"] = "invalid"
        stats["message"] = "TOPIX benchmark comparison suspended because cached benchmark prices failed the sanity check. Strategy return and cash accounting remain valid."
    elif stats["valid_points"] == 0:
        stats["status"] = "missing"
        stats["message"] = "No valid TOPIX benchmark marks were available."

    return stats


def max_drawdown(curve: list[dict[str, Any]], key: str = "portfolio_equity") -> float | None:
    peak = None
    worst = 0.0
    for p in curve:
        v = to_float(p.get(key))
        if v is None or v <= 0:
            continue
        if peak is None or v > peak:
            peak = v
        dd = (v / peak - 1.0) * 100.0 if peak else 0.0
        worst = min(worst, dd)
    return safe_round(worst, 4)


def summarize_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    rets = [to_float(t.get("return_pct")) for t in trades]
    rets = [x for x in rets if x is not None]
    alphas = [to_float(t.get("alpha_pct")) for t in trades]
    alphas = [x for x in alphas if x is not None]
    return {
        "count": len(trades),
        "win_rate_pct": safe_round((sum(1 for x in rets if x > 0) / len(rets) * 100.0) if rets else None, 2),
        "avg_return_pct": safe_round(avg(rets), 4),
        "median_return_pct": safe_round(median(rets), 4),
        "avg_alpha_pct": safe_round(avg(alphas), 4),
        "median_alpha_pct": safe_round(median(alphas), 4),
        "best_return_pct": safe_round(max(rets) if rets else None, 4),
        "worst_return_pct": safe_round(min(rets) if rets else None, 4),
    }


def exposure_summary(open_positions: list[dict[str, Any]], key: str, total_mv: float) -> list[dict[str, Any]]:
    groups: dict[str, float] = defaultdict(float)
    for p in open_positions:
        label = str(p.get(key) or "Unknown")
        mv = to_float(p.get("market_value")) or 0.0
        groups[label] += mv
    rows = []
    for label, mv in sorted(groups.items(), key=lambda kv: kv[1], reverse=True):
        rows.append({
            key: label,
            "market_value": safe_round(mv, 2),
            "weight_pct": safe_round((mv / total_mv * 100.0) if total_mv > 0 else None, 2),
        })
    return rows


def build_simulation() -> dict[str, Any]:
    prices = load_prices()
    benchmark_item = get_benchmark_item(prices)
    if benchmark_item is None:
        raise RuntimeError("Benchmark TOPIX item not found in prices JSON")
    benchmark_df = price_df(benchmark_item)
    if benchmark_df.empty:
        raise RuntimeError("Benchmark price bars are empty")
    equity_dfs = {str(item.get("symbol")): price_df(item) for item in equity_items(prices)}
    end_date = pd.Timestamp(END_DATE_ENV) if END_DATE_ENV else None
    eval_dates = trading_week_eval_dates(prices, end_date)
    if WEEKS > 0:
        eval_dates = eval_dates[-WEEKS:]

    cash = INITIAL_CAPITAL
    external_capital = INITIAL_CAPITAL
    open_positions: dict[str, dict[str, Any]] = {}
    closed_trades: list[dict[str, Any]] = []
    skipped_orders: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []
    weekly_decisions: list[dict[str, Any]] = []
    benchmark_external_units = None
    first_benchmark_price = None

    for eval_date in eval_dates:
        scored = score_snapshot(prices, eval_date)
        scored_by_symbol = {str(x.get("symbol")): x for x in scored}
        bench_mark = close_at_or_prior(benchmark_df, eval_date)
        bench_next = next_open_after(benchmark_df, eval_date)
        if bench_next is None or to_float(bench_next.get("price")) is None:
            # No executable following session. Do not mix a non-executable
            # weekly decision into the cash-accounted equity curve.
            continue
        execution_date = pd.Timestamp(bench_next.get("date")).normalize()
        if benchmark_external_units is None:
            first_benchmark_price = to_float(bench_next.get("price"))
            if first_benchmark_price and first_benchmark_price > 0:
                benchmark_external_units = INITIAL_CAPITAL / first_benchmark_price

        # Mark current positions at evaluation close for exit decisions only.
        market_value = 0.0
        for symbol, pos in list(open_positions.items()):
            df = equity_dfs.get(symbol)
            mark = close_at_or_prior(df, eval_date) if df is not None else None
            current_price = to_float(mark.get("price")) if mark else None
            entry_price = to_float(pos.get("entry_price"))
            shares = int(pos.get("shares") or 0)
            if current_price is not None and shares > 0:
                mv = shares * current_price
                pos["current_price"] = safe_round(current_price, 4)
                pos["market_value"] = safe_round(mv, 2)
                pos["unrealized_pct"] = safe_round(pct(current_price, entry_price), 4)
                pos["weeks_held"] = int(pos.get("weeks_held") or 0) + 1
                pos["max_unrealized_pct"] = max(to_float(pos.get("max_unrealized_pct")) or 0.0, to_float(pos.get("unrealized_pct")) or 0.0)
                pos["min_unrealized_pct"] = min(to_float(pos.get("min_unrealized_pct")) or 0.0, to_float(pos.get("unrealized_pct")) or 0.0)
                market_value += mv

        pre_trade_equity = cash + market_value

        # Exits execute next open.
        exit_count = 0
        for symbol, pos in list(open_positions.items()):
            df = equity_dfs.get(symbol)
            mark = close_at_or_prior(df, eval_date) if df is not None else None
            current_price = to_float(mark.get("price")) if mark else None
            current_item = scored_by_symbol.get(symbol)
            should, reason = should_exit(pos, current_item, current_price)
            if not should:
                if current_item:
                    pos["last_score_pts"] = current_item.get("score_pts")
                    pos["last_signal"] = normalize_signal(current_item.get("signal"))
                    pos["last_quality"] = current_item.get("quality")
                continue
            execution = next_open_after(df, eval_date) if df is not None else None
            if execution is None:
                continue
            exit_open = to_float(execution.get("price"))
            if exit_open is None:
                continue
            exit_price = exit_open * (1.0 - SELL_SLIPPAGE_PCT / 100.0)
            shares = int(pos.get("shares") or 0)
            proceeds = shares * exit_price
            cost = to_float(pos.get("cost_basis")) or 0.0
            pnl = proceeds - cost
            ret = (exit_price / (to_float(pos.get("entry_price")) or exit_price) - 1.0) * 100.0
            bench_exit_price = to_float(bench_next.get("price")) if bench_next else None
            bench_units = to_float(pos.get("benchmark_units"))
            bench_entry = to_float(pos.get("benchmark_entry_price"))
            bench_value = None
            bench_return = None
            alpha = None
            if bench_exit_price is not None and bench_units is not None and bench_entry is not None and valid_benchmark_price_move(bench_entry, bench_exit_price):
                bench_value = bench_units * bench_exit_price
                bench_return = (bench_exit_price / bench_entry - 1.0) * 100.0
                alpha = ret - bench_return
            cash += proceeds
            closed = {
                **pos,
                "exit_date": execution.get("date"),
                "exit_price": safe_round(exit_price, 4),
                "raw_exit_open": safe_round(exit_open, 4),
                "exit_reason": reason,
                "proceeds": safe_round(proceeds, 2),
                "pnl_jpy": safe_round(pnl, 2),
                "return_pct": safe_round(ret, 4),
                "benchmark_exit_price": safe_round(bench_exit_price, 4),
                "benchmark_value": safe_round(bench_value, 2),
                "benchmark_return_pct": safe_round(bench_return, 4),
                "alpha_pct": safe_round(alpha, 4),
            }
            closed_trades.append(closed)
            del open_positions[symbol]
            exit_count += 1

        # Recompute equity after exits at prior marks.
        market_value = 0.0
        for symbol, pos in open_positions.items():
            mv = to_float(pos.get("market_value")) or 0.0
            market_value += mv
        equity_after_exits = cash + market_value

        # Entries execute next open.
        new_count = 0
        existing = set(open_positions.keys())
        for item in scored:
            if new_count >= MAX_NEW_POSITIONS_PER_WEEK:
                break
            if len(open_positions) >= MAX_POSITIONS:
                break
            ok, reason = is_entry_candidate(item, existing, cash)
            if not ok:
                if int(item.get("rank") or 999) <= 5:
                    skipped_orders.append({
                        "eval_date": str(eval_date.date()),
                        "symbol": item.get("symbol"),
                        "rank": item.get("rank"),
                        "score_pts": item.get("score_pts"),
                        "signal": normalize_signal(item.get("signal")),
                        "reason": reason,
                    })
                continue
            # If cash is recycled after initial deployment, require a stronger score.
            if external_capital > 0 and cash < INITIAL_CAPITAL * 0.25 and int(item.get("score_pts") or 0) < REINVESTMENT_MIN_SCORE:
                continue
            symbol = str(item.get("symbol") or "")
            df = equity_dfs.get(symbol)
            execution = next_open_after(df, eval_date) if df is not None else None
            if execution is None:
                skipped_orders.append({"eval_date": str(eval_date.date()), "symbol": symbol, "rank": item.get("rank"), "score_pts": item.get("score_pts"), "signal": normalize_signal(item.get("signal")), "reason": "no next open"})
                continue
            entry_open = to_float(execution.get("price"))
            bench_entry = to_float(bench_next.get("price")) if bench_next else None
            if entry_open is None:
                continue
            lot = build_lot(symbol, item, entry_open, str(execution.get("date")), equity_after_exits, cash, bench_entry)
            if lot is None:
                skipped_orders.append({"eval_date": str(eval_date.date()), "symbol": symbol, "rank": item.get("rank"), "score_pts": item.get("score_pts"), "signal": normalize_signal(item.get("signal")), "reason": "insufficient cash for round lot"})
                continue
            cash -= to_float(lot.get("cost_basis")) or 0.0
            open_positions[symbol] = lot
            existing.add(symbol)
            new_count += 1

        # Final mark for the executable snapshot. Orders were decided at
        # eval_date close and executed at execution_date open. Therefore the
        # equity curve must be dated on execution_date, not eval_date. Existing
        # and newly opened positions are marked at execution_date close where
        # available; otherwise new positions fall back to entry cost.
        market_value = 0.0
        for symbol, pos in open_positions.items():
            df = equity_dfs.get(symbol)
            mark = close_at_or_prior(df, execution_date) if df is not None else None
            current_price = to_float(mark.get("price")) if mark else None
            if current_price is None:
                current_price = to_float(pos.get("entry_price"))
            shares = int(pos.get("shares") or 0)
            mv = shares * current_price if current_price is not None else 0.0
            pos["current_price"] = safe_round(current_price, 4)
            pos["market_value"] = safe_round(mv, 2)
            pos["unrealized_pct"] = safe_round(pct(current_price, pos.get("entry_price")), 4)
            market_value += mv
        portfolio_equity = cash + market_value
        benchmark_equity = None
        bench_exec_mark = close_at_or_prior(benchmark_df, execution_date)
        if benchmark_external_units is not None and bench_exec_mark and to_float(bench_exec_mark.get("price")):
            benchmark_equity = benchmark_external_units * to_float(bench_exec_mark.get("price"))
        equity_curve.append({
            "date": str(execution_date.date()),
            "eval_date": str(eval_date.date()),
            "execution_date": str(execution_date.date()),
            "cash": safe_round(cash, 2),
            "market_value": safe_round(market_value, 2),
            "portfolio_equity": safe_round(portfolio_equity, 2),
            "portfolio_return_pct": safe_round((portfolio_equity / external_capital - 1.0) * 100.0 if external_capital else None, 4),
            "benchmark_equity": safe_round(benchmark_equity, 2),
            "benchmark_return_pct": safe_round((benchmark_equity / external_capital - 1.0) * 100.0 if benchmark_equity and external_capital else None, 4),
            "open_positions": len(open_positions),
            "new_entries": new_count,
            "exits": exit_count,
            "top_score": scored[0].get("score_pts") if scored else None,
            "top_symbol": scored[0].get("symbol") if scored else None,
        })
        snapshots.append({
            "eval_date": str(eval_date.date()),
            "execution_date": str(execution_date.date()),
            "score_candidates": len(scored),
            "new_entries": new_count,
            "exits": exit_count,
            "cash": safe_round(cash, 2),
            "market_value": safe_round(market_value, 2),
            "portfolio_equity": safe_round(portfolio_equity, 2),
            "top3": [{"rank": x.get("rank"), "symbol": x.get("symbol"), "score_pts": x.get("score_pts"), "signal": normalize_signal(x.get("signal")), "quality": x.get("quality")} for x in scored[:3]],
        })
        weekly_decisions.append({
            "eval_date": str(eval_date.date()),
            "execution_date": str(execution_date.date()),
            "top10": [{"rank": x.get("rank"), "symbol": x.get("symbol"), "score_pts": x.get("score_pts"), "signal": normalize_signal(x.get("signal")), "quality": x.get("quality"), "liquidity_band": x.get("liquidity_band")} for x in scored],
        })

    benchmark_quality = sanitize_benchmark_curve(equity_curve, external_capital)

    final_equity = to_float(equity_curve[-1].get("portfolio_equity")) if equity_curve else INITIAL_CAPITAL
    final_benchmark = to_float(equity_curve[-1].get("benchmark_equity")) if equity_curve else None
    benchmark_valid = benchmark_quality.get("status") == "valid" and final_benchmark is not None
    total_mv = sum(to_float(p.get("market_value")) or 0.0 for p in open_positions.values())
    open_rows = sorted(open_positions.values(), key=lambda x: to_float(x.get("market_value")) or 0.0, reverse=True)
    for p in open_rows:
        p["weight_pct"] = safe_round(((to_float(p.get("market_value")) or 0.0) / final_equity * 100.0) if final_equity else None, 2)

    closed_summary = summarize_trades(closed_trades)
    exit_reasons = Counter(str(t.get("exit_reason") or "Unknown") for t in closed_trades)
    signal_summary: dict[str, Any] = {}
    for sig in sorted(set(str(t.get("entry_signal") or "Unknown") for t in closed_trades)):
        signal_summary[sig] = summarize_trades([t for t in closed_trades if str(t.get("entry_signal") or "Unknown") == sig])
    quality_summary: dict[str, Any] = {}
    for q in sorted(set(str(t.get("entry_quality") or "Unknown") for t in closed_trades)):
        quality_summary[q] = summarize_trades([t for t in closed_trades if str(t.get("entry_quality") or "Unknown") == q])
    theme_summary: dict[str, Any] = {}
    for theme in sorted(set(str(t.get("theme") or "Unknown") for t in closed_trades)):
        theme_summary[theme] = summarize_trades([t for t in closed_trades if str(t.get("theme") or "Unknown") == theme])
    bucket_summary: dict[str, Any] = {}
    for bucket in sorted(set(str(t.get("bucket") or "Unknown") for t in closed_trades)):
        bucket_summary[bucket] = summarize_trades([t for t in closed_trades if str(t.get("bucket") or "Unknown") == bucket])

    summary = {
        "policy_name": "Weekly JP Simulation v1",
        "eval_date_count": len(eval_dates),
        "eval_date_start": str(eval_dates[0].date()) if eval_dates else None,
        "eval_date_end": str(eval_dates[-1].date()) if eval_dates else None,
        "external_capital": safe_round(external_capital, 2),
        "cash": safe_round(cash, 2),
        "market_value": safe_round(total_mv, 2),
        "portfolio_equity": safe_round(final_equity, 2),
        "benchmark_equity": safe_round(final_benchmark, 2) if benchmark_valid else None,
        "net_return_pct": safe_round((final_equity / external_capital - 1.0) * 100.0 if external_capital else None, 4),
        "benchmark_return_pct": safe_round((final_benchmark / external_capital - 1.0) * 100.0 if benchmark_valid and external_capital else None, 4),
        "alpha_pct": safe_round(((final_equity - final_benchmark) / external_capital * 100.0) if benchmark_valid and final_equity and external_capital else None, 4),
        "benchmark_status": benchmark_quality.get("status"),
        "benchmark_message": benchmark_quality.get("message"),
        "max_drawdown_pct": max_drawdown(equity_curve, "portfolio_equity"),
        "benchmark_max_drawdown_pct": max_drawdown(equity_curve, "benchmark_equity") if benchmark_valid else None,
        "open_positions_count": len(open_rows),
        "closed_trades_count": len(closed_trades),
        "skipped_orders_count": len(skipped_orders),
        "closed_trade_summary": closed_summary,
        "exit_reasons": dict(exit_reasons.most_common()),
    }
    payload = {
        "schema_version": "weekly-jp-simulation-v1",
        "generated_at": iso_now(),
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "source_prices": safe_relative(PRICES_JSON),
        "benchmark": {"symbol": BENCHMARK_SYMBOL, "name": "TOPIX ETF proxy"},
        "benchmark_quality": benchmark_quality,
        "policy": {
            "initial_capital": INITIAL_CAPITAL,
            "position_pct": POSITION_PCT,
            "max_positions": MAX_POSITIONS,
            "max_new_positions_per_week": MAX_NEW_POSITIONS_PER_WEEK,
            "min_entry_score": MIN_ENTRY_SCORE,
            "reinvestment_min_score": REINVESTMENT_MIN_SCORE,
            "score_exit": SCORE_EXIT,
            "stop_pct": STOP_PCT,
            "time_exit_weeks": TIME_EXIT_WEEKS,
            "round_lot": ROUND_LOT,
            "buy_slippage_pct": BUY_SLIPPAGE_PCT,
            "sell_slippage_pct": SELL_SLIPPAGE_PCT,
            "allow_watch_monitor_entries": ALLOW_WATCH,
            "order_execution": "next trading day open after weekly evaluation date",
            "mark_to_market": "execution-date close after next-open orders; new positions fall back to entry cost if same-day close is unavailable",
        },
        "summary": summary,
        "equity_curve": equity_curve,
        "snapshots": snapshots,
        "open_positions": open_rows,
        "closed_trades": sorted(closed_trades, key=lambda x: str(x.get("exit_date") or ""), reverse=True),
        "skipped_orders": skipped_orders[-80:],
        "weekly_decisions": weekly_decisions[-20:],
        "strategy_comparison": [
            {"label": "Weekly Strategy", "equity": safe_round(final_equity, 2), "return_pct": summary.get("net_return_pct"), "max_drawdown_pct": summary.get("max_drawdown_pct")},
            {"label": "TOPIX Same Initial Capital", "equity": safe_round(final_benchmark, 2) if benchmark_valid else None, "return_pct": summary.get("benchmark_return_pct"), "max_drawdown_pct": summary.get("benchmark_max_drawdown_pct"), "status": benchmark_quality.get("status"), "message": benchmark_quality.get("message")},
        ],
        "signal_summary": signal_summary,
        "quality_summary": quality_summary,
        "theme_summary": theme_summary,
        "bucket_summary": bucket_summary,
        "open_theme_exposure": exposure_summary(open_rows, "theme", total_mv),
        "open_bucket_exposure": exposure_summary(open_rows, "bucket", total_mv),
        "liquidity_warnings": [p for p in open_rows if str(p.get("entry_quality") or "") in {"D Extended", "E Avoid"} or (to_float(p.get("unrealized_pct")) or 0.0) <= STOP_PCT * 0.65],
    }
    return payload


def write_outputs(payload: dict[str, Any]) -> None:
    as_of = payload.get("summary", {}).get("eval_date_end") or now_jst().strftime("%Y-%m-%d")
    latest = OUT_SIM_DIR / "latest.json"
    dated = OUT_SIM_DIR / f"{as_of}.json"
    manifest = OUT_SIM_DIR / "manifest.json"
    write_json(latest, payload)
    write_json(dated, payload)
    write_json(manifest, {
        "schema_version": "weekly-jp-simulation-manifest-v1",
        "latest": safe_relative(latest),
        "latest_date": as_of,
        "generated_at": payload.get("generated_at"),
        "files": [{"date": as_of, "path": safe_relative(dated)}],
    })
    if WRITE_LEGACY_COPY:
        legacy_latest = LEGACY_OUT_SIM_DIR / "latest.json"
        legacy_dated = LEGACY_OUT_SIM_DIR / f"{as_of}.json"
        write_json(legacy_latest, payload)
        write_json(legacy_dated, payload)
        write_json(LEGACY_OUT_SIM_DIR / "manifest.json", {
            "schema_version": "weekly-jp-simulation-manifest-v1",
            "latest": safe_relative(legacy_latest),
            "latest_date": as_of,
            "generated_at": payload.get("generated_at"),
            "files": [{"date": as_of, "path": safe_relative(legacy_dated)}],
        })


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"PRICES_JSON={safe_relative(PRICES_JSON)}")
    payload = build_simulation()
    write_outputs(payload)
    s = payload.get("summary", {})
    print("eval_dates=", s.get("eval_date_count"))
    print("net_return_pct=", s.get("net_return_pct"))
    print("alpha_pct=", s.get("alpha_pct"))
    print("open_positions=", s.get("open_positions_count"))
    print("closed_trades=", s.get("closed_trades_count"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
