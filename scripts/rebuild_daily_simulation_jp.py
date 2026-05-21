#!/usr/bin/env python3
"""
Rebuild Daily JP Simulation for Neon Tokyo Signals.

Input:
- site/data/prices-jp/latest.json
- scripts/build_daily_jp.py scoring engine

Output:
- site/data/japan/daily/simulation/latest.json
- site/data/japan/daily/simulation/YYYY-MM-DD.json
- site/data/japan/daily/simulation/manifest.json
- site/data/daily-jp/simulation/latest.json      (compat)
- site/data/daily-jp/simulation/YYYY-MM-DD.json  (compat)
- site/data/daily-jp/simulation/manifest.json    (compat)

Design:
- Evaluate Daily score at eval_date close using only bars visible at eval_date.
- Execute exits and entries at the next trading day's open.
- Mark positions at execution_date close.
- Equity curve date == execution_date.
- JP round lot support.
- TOPIX benchmark sanity guard.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()
else:
    OUT_DIR = OUT_DIR.resolve()

PRICES_JSON = Path(os.getenv("PRICES_JSON", str(OUT_DIR / "data" / "prices-jp" / "latest.json")))
if not PRICES_JSON.is_absolute():
    PRICES_JSON = (ROOT / PRICES_JSON).resolve()
else:
    PRICES_JSON = PRICES_JSON.resolve()

PRIMARY_OUT_DIR = OUT_DIR / "data" / "japan" / "daily" / "simulation"
COMPAT_OUT_DIR = OUT_DIR / "data" / "daily-jp" / "simulation"

TZ = ZoneInfo("Asia/Tokyo")

INITIAL_CAPITAL = float(os.getenv("DAILY_JP_SIM_INITIAL_CAPITAL", "10000000"))
POSITION_SIZE_PCT = float(os.getenv("DAILY_JP_SIM_POSITION_SIZE_PCT", "0.125"))
MAX_POSITIONS = int(os.getenv("DAILY_JP_SIM_MAX_POSITIONS", "8"))
MAX_NEW_POSITIONS_PER_DAY = int(os.getenv("DAILY_JP_SIM_MAX_NEW_POSITIONS_PER_DAY", "3"))
ROUND_LOT = int(os.getenv("DAILY_JP_SIM_ROUND_LOT", "100"))
BUY_SLIPPAGE_PCT = float(os.getenv("DAILY_JP_SIM_BUY_SLIPPAGE_PCT", "0.0015"))
SELL_SLIPPAGE_PCT = float(os.getenv("DAILY_JP_SIM_SELL_SLIPPAGE_PCT", "0.0015"))

SIM_DAYS = int(os.getenv("DAILY_JP_SIM_DAYS", "220"))
MIN_HISTORY_BARS = int(os.getenv("DAILY_JP_SIM_MIN_HISTORY_BARS", "80"))
RANK_LIMIT = min(10, max(1, int(os.getenv("DAILY_JP_SIM_RANK_LIMIT", "10"))))
ENTRY_RANK_LIMIT = min(RANK_LIMIT, max(1, int(os.getenv("DAILY_JP_SIM_ENTRY_RANK_LIMIT", "10"))))
ENTRY_SCORE_FLOOR = int(os.getenv("DAILY_JP_SIM_ENTRY_SCORE_FLOOR", "500"))
REINVESTMENT_SCORE_FLOOR = int(os.getenv("DAILY_JP_SIM_REINVESTMENT_SCORE_FLOOR", "600"))
ALLOW_MONITOR = os.getenv("DAILY_JP_SIM_ALLOW_MONITOR", "true").strip().lower() == "true"
TRADE_ONLY = os.getenv("DAILY_JP_SIM_TRADE_ONLY", "false").strip().lower() == "true"

STOP_LOSS_PCT = float(os.getenv("DAILY_JP_SIM_STOP_LOSS_PCT", "0.05"))
SCORE_EXIT_FLOOR = int(os.getenv("DAILY_JP_SIM_SCORE_EXIT_FLOOR", "420"))
TIME_EXIT_DAYS = int(os.getenv("DAILY_JP_SIM_TIME_EXIT_DAYS", "5"))
PROFIT_TAKE_PCT = float(os.getenv("DAILY_JP_SIM_PROFIT_TAKE_PCT", "0.18"))
BENCHMARK_SYMBOL = os.getenv("DAILY_JP_SIM_BENCHMARK_SYMBOL", "1306.T")
BENCHMARK_ABS_LIMIT_PCT = float(os.getenv("DAILY_JP_SIM_BENCHMARK_RETURN_ABS_LIMIT_PCT", "35"))

POLICY_PRESETS = [
    {"id": "default", "label": "Default", "rank_limit": 10, "score_floor": 500, "allow_monitor": True, "stop": 0.05, "time_exit": 5},
    {"id": "top3", "label": "Top 3", "rank_limit": 3, "score_floor": 500, "allow_monitor": True, "stop": 0.05, "time_exit": 5},
    {"id": "top5", "label": "Top 5", "rank_limit": 5, "score_floor": 500, "allow_monitor": True, "stop": 0.05, "time_exit": 5},
    {"id": "trade_only", "label": "Trade only", "rank_limit": 10, "score_floor": 500, "allow_monitor": False, "stop": 0.05, "time_exit": 5},
    {"id": "score600", "label": "Score ≥600", "rank_limit": 10, "score_floor": 600, "allow_monitor": True, "stop": 0.05, "time_exit": 5},
    {"id": "stop8", "label": "Stop -8%", "rank_limit": 10, "score_floor": 500, "allow_monitor": True, "stop": 0.08, "time_exit": 5},
]

RISK_FLAGS = {
    "abnormal_distribution",
    "volume_noise",
    "volume_breakout_risk",
    "trade_block_volume_breakout",
    "weak_close_on_volume",
    "red_close_on_volume",
    "score_cap_very_low_liquidity",
    "score_cap_weak_volume",
}


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
        raise FileNotFoundError(f"Missing JSON: {safe_relative(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


def safe_round(value: Any, digits: int = 4) -> float | None:
    v = to_float(value)
    if v is None:
        return None
    return round(v, digits)


def load_build_daily_module():
    path = ROOT / "scripts" / "build_daily_jp.py"
    spec = importlib.util.spec_from_file_location("build_daily_jp_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scripts/build_daily_jp.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    required = ["score_equity_item", "sort_ranked_items", "market_regime_from_pulse", "bars_to_df"]
    for name in required:
        if not hasattr(mod, name):
            raise AttributeError(f"build_daily_jp.py missing required function: {name}")
    return mod


def bars_to_df_from_item(item: dict[str, Any]) -> pd.DataFrame:
    bars = item.get("bars") or []
    rows = []
    for b in bars:
        if not isinstance(b, dict):
            continue
        date = b.get("date")
        if not date:
            continue
        rows.append({
            "Date": pd.to_datetime(date),
            "Open": to_float(b.get("open")),
            "High": to_float(b.get("high")),
            "Low": to_float(b.get("low")),
            "Close": to_float(b.get("close")),
            "Volume": to_float(b.get("volume")) or 0,
        })
    if not rows:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    df = pd.DataFrame(rows).dropna(subset=["Date", "Open", "High", "Low", "Close"])
    if df.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    df = df.set_index("Date").sort_index()
    return df[~df.index.duplicated(keep="last")]


def df_to_bars(df: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for idx, row in df.iterrows():
        out.append({
            "date": idx.strftime("%Y-%m-%d"),
            "open": safe_round(row.get("Open"), 6),
            "high": safe_round(row.get("High"), 6),
            "low": safe_round(row.get("Low"), 6),
            "close": safe_round(row.get("Close"), 6),
            "volume": int(row.get("Volume") or 0),
        })
    return out


def clone_item_with_bars(item: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
    cloned = {k: v for k, v in item.items() if k != "bars"}
    cloned["bars"] = df_to_bars(df)
    cloned["bars_count"] = len(cloned["bars"])
    if cloned["bars"]:
        cloned["date_start"] = cloned["bars"][0]["date"]
        cloned["date_end"] = cloned["bars"][-1]["date"]
        cloned["is_partial"] = False
    return cloned


def open_on_or_after(df: pd.DataFrame, date: pd.Timestamp) -> tuple[pd.Timestamp, float] | tuple[None, None]:
    sub = df[df.index >= date]
    if sub.empty:
        return None, None
    idx = sub.index[0]
    return idx, to_float(sub.iloc[0].get("Open"))


def close_on_or_before(df: pd.DataFrame, date: pd.Timestamp) -> tuple[pd.Timestamp, float] | tuple[None, None]:
    sub = df[df.index <= date]
    if sub.empty:
        return None, None
    idx = sub.index[-1]
    return idx, to_float(sub.iloc[-1].get("Close"))


def next_trading_date(df: pd.DataFrame, eval_date: pd.Timestamp) -> pd.Timestamp | None:
    sub = df[df.index > eval_date]
    if sub.empty:
        return None
    return sub.index[0]


def pct_return(entry: float | None, exit_: float | None) -> float | None:
    if entry is None or exit_ is None or entry <= 0:
        return None
    return (exit_ / entry - 1.0) * 100.0


@dataclass
class Position:
    symbol: str
    name: str
    theme: str
    bucket: str
    signal: str
    quality: str
    entry_eval_date: str
    entry_date: str
    entry_price: float
    shares: int
    cost: float
    score_entry: int
    rank_entry: int
    benchmark_entry_price: float | None
    benchmark_units: float | None
    holding_days: int = 0

    def market_value(self, price: float | None) -> float:
        if price is None:
            return self.cost
        return self.shares * price

    def return_pct(self, price: float | None) -> float | None:
        if price is None:
            return None
        return pct_return(self.entry_price, price)


def score_snapshot(
    build_mod: Any,
    equities: list[dict[str, Any]],
    benchmark_item: dict[str, Any] | None,
    eval_date: pd.Timestamp,
) -> list[dict[str, Any]]:
    pulse_items = []
    topix_last = None

    if benchmark_item is not None:
        bdf = bars_to_df_from_item(benchmark_item)
        bdf = bdf[bdf.index <= eval_date]
        if len(bdf) >= 20:
            tmp = clone_item_with_bars(benchmark_item, bdf)
            try:
                bdf2 = build_mod.add_indicators(build_mod.bars_to_df(tmp))
                if not bdf2.empty:
                    topix_last = bdf2.iloc[-1]
            except Exception:
                topix_last = None

    # Use a neutral regime for historical replay unless benchmark data is available and sane.
    regime = "Neutral"
    regime_score = 0.5

    scored = []
    for item in equities:
        df = bars_to_df_from_item(item)
        hist = df[df.index <= eval_date]
        if len(hist) < MIN_HISTORY_BARS:
            continue
        cloned = clone_item_with_bars(item, hist)
        try:
            s = build_mod.score_equity_item(cloned, topix_last, regime, regime_score)
        except Exception:
            s = None
        if s:
            scored.append(s)

    ranked = build_mod.sort_ranked_items(scored)
    return ranked[:RANK_LIMIT]


def translate_signal(triage: str | None) -> str:
    if triage == "Trade":
        return "Trade"
    if triage == "Watch":
        return "Monitor"
    return "Blocked"


def is_entry_candidate(item: dict[str, Any], policy: dict[str, Any]) -> bool:
    rank = int(item.get("rank") or 9999)
    score = int(item.get("score_pts") or 0)
    signal = item.get("triage")
    flags = set(item.get("flags") or [])
    liquidity = str(item.get("liquidity_band") or "")
    risk = str(item.get("risk_level") or "")
    if rank > int(policy["rank_limit"]):
        return False
    if score < int(policy["score_floor"]):
        return False
    if signal == "Trade":
        pass
    elif signal == "Watch" and bool(policy.get("allow_monitor")):
        pass
    else:
        return False
    if flags & RISK_FLAGS:
        return False
    if liquidity in {"Very Thin", "Unknown"}:
        return False
    if "High" in risk:
        return False
    return True


def exit_reason(pos: Position, signal_item: dict[str, Any] | None, close_price: float | None, policy: dict[str, Any]) -> str | None:
    ret = pos.return_pct(close_price)
    flags = set((signal_item or {}).get("flags") or [])
    score = int((signal_item or {}).get("score_pts") or 0)
    triage = (signal_item or {}).get("triage")
    if ret is not None and ret <= -float(policy["stop"]) * 100.0:
        return f"close stop -{float(policy['stop']) * 100:.1f}%"
    if flags & {"abnormal_distribution", "volume_noise", "weak_close_on_volume", "red_close_on_volume"}:
        return "distribution / weak close exit"
    if score and score < SCORE_EXIT_FLOOR:
        return f"score exit < {SCORE_EXIT_FLOOR}"
    if triage == "Ignore" and pos.holding_days >= 1:
        return "signal decay exit"
    if ret is not None and ret >= PROFIT_TAKE_PCT * 100.0:
        return "profit / extension harvest"
    if pos.holding_days >= int(policy["time_exit"]):
        return f"time exit {int(policy['time_exit'])}D"
    return None


def aggregate_closed_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {
            "count": 0,
            "win_rate_pct": None,
            "avg_return_pct": None,
            "avg_alpha_pct": None,
            "valid_alpha_count": 0,
            "exit_reasons": [],
            "by_signal": [],
        }
    returns = [to_float(t.get("return_pct")) for t in trades if to_float(t.get("return_pct")) is not None]
    alphas = [to_float(t.get("alpha_pct")) for t in trades if to_float(t.get("alpha_pct")) is not None]
    wins = [r for r in returns if r > 0]
    reasons: dict[str, int] = {}
    by_signal: dict[str, list[float]] = {}
    for t in trades:
        reasons[t.get("exit_reason") or "other"] = reasons.get(t.get("exit_reason") or "other", 0) + 1
        r = to_float(t.get("return_pct"))
        sig = t.get("signal") or "Unknown"
        if r is not None:
            by_signal.setdefault(sig, []).append(r)
    return {
        "count": len(trades),
        "win_rate_pct": round(len(wins) / len(returns) * 100.0, 2) if returns else None,
        "avg_return_pct": round(float(np.mean(returns)), 4) if returns else None,
        "avg_alpha_pct": round(float(np.mean(alphas)), 4) if alphas else None,
        "valid_alpha_count": len(alphas),
        "exit_reasons": [{"reason": k, "count": v} for k, v in sorted(reasons.items(), key=lambda kv: kv[1], reverse=True)],
        "by_signal": [
            {
                "signal": k,
                "count": len(v),
                "avg_return_pct": round(float(np.mean(v)), 4),
                "win_rate_pct": round(sum(1 for x in v if x > 0) / len(v) * 100.0, 2),
            }
            for k, v in sorted(by_signal.items())
        ],
    }


def max_drawdown_pct(values: list[float]) -> float | None:
    if not values:
        return None
    peak = values[0]
    max_dd = 0.0
    for v in values:
        peak = max(peak, v)
        if peak > 0:
            dd = (v / peak - 1.0) * 100.0
            max_dd = min(max_dd, dd)
    return round(max_dd, 4)


def run_simulation(
    equities: list[dict[str, Any]],
    benchmark_item: dict[str, Any] | None,
    policy: dict[str, Any],
    eval_dates: list[pd.Timestamp],
    snapshots_by_date: dict[str, list[dict[str, Any]]],
    dfs: dict[str, pd.DataFrame],
    bdf: pd.DataFrame,
) -> dict[str, Any]:

    cash = INITIAL_CAPITAL
    positions: dict[str, Position] = {}
    closed_trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []
    benchmark_initial_open: float | None = None
    benchmark_units: float | None = None
    benchmark_invalid = False
    benchmark_invalid_samples: list[dict[str, Any]] = []

    latest_snapshot: list[dict[str, Any]] = []

    for eval_date in eval_dates:
        execution_date = None
        if not bdf.empty:
            execution_date = next_trading_date(bdf, eval_date)
        if execution_date is None:
            # fallback to earliest next date across equities
            next_dates = []
            for df in dfs.values():
                nd = next_trading_date(df, eval_date)
                if nd is not None:
                    next_dates.append(nd)
            if next_dates:
                execution_date = min(next_dates)
        if execution_date is None:
            continue

        snapshot = snapshots_by_date.get(eval_date.strftime("%Y-%m-%d"), [])
        if snapshot:
            latest_snapshot = snapshot
        snap_by_symbol = {x.get("symbol"): x for x in snapshot}

        bench_open = None
        bench_close = None
        if not bdf.empty:
            _, bench_open = open_on_or_after(bdf, execution_date)
            _, bench_close = close_on_or_before(bdf, execution_date)

        if benchmark_initial_open is None and bench_open and bench_open > 0:
            benchmark_initial_open = bench_open
            benchmark_units = INITIAL_CAPITAL / benchmark_initial_open

        # Exits at execution open.
        for symbol, pos in list(positions.items()):
            df = dfs.get(symbol)
            if df is None or df.empty:
                continue
            _, exec_open = open_on_or_after(df, execution_date)
            _, eval_close = close_on_or_before(df, eval_date)
            if exec_open is None:
                continue
            sig = snap_by_symbol.get(symbol)
            reason = exit_reason(pos, sig, eval_close, policy)
            pos.holding_days += 1
            if reason:
                sell_price = exec_open * (1.0 - SELL_SLIPPAGE_PCT)
                proceeds = pos.shares * sell_price
                cash += proceeds
                ret_pct = pct_return(pos.entry_price, sell_price)
                bench_ret = pct_return(pos.benchmark_entry_price, bench_open) if pos.benchmark_entry_price and bench_open else None
                alpha = (ret_pct - bench_ret) if ret_pct is not None and bench_ret is not None and not benchmark_invalid else None
                pnl = proceeds - pos.cost
                closed_trades.append({
                    "symbol": symbol,
                    "name": pos.name,
                    "theme": pos.theme,
                    "bucket": pos.bucket,
                    "signal": pos.signal,
                    "quality": pos.quality,
                    "rank_entry": pos.rank_entry,
                    "score_entry": pos.score_entry,
                    "entry_eval_date": pos.entry_eval_date,
                    "entry_date": pos.entry_date,
                    "exit_eval_date": eval_date.strftime("%Y-%m-%d"),
                    "exit_date": execution_date.strftime("%Y-%m-%d"),
                    "entry_price": round(pos.entry_price, 4),
                    "exit_price": round(sell_price, 4),
                    "shares": pos.shares,
                    "return_pct": safe_round(ret_pct, 4),
                    "benchmark_return_pct": safe_round(bench_ret, 4),
                    "alpha_pct": safe_round(alpha, 4),
                    "exit_reason": reason,
                    "pnl_jpy": round(pnl, 2),
                })
                del positions[symbol]

        # Entries at execution open.
        equity_before_entries = cash + sum(
            pos.market_value(close_on_or_before(dfs.get(sym, pd.DataFrame()), execution_date)[1])
            for sym, pos in positions.items()
        )
        entry_budget_base = max(0.0, equity_before_entries * POSITION_SIZE_PCT)
        new_count = 0
        for item in snapshot:
            if new_count >= MAX_NEW_POSITIONS_PER_DAY:
                break
            if len(positions) >= MAX_POSITIONS:
                break
            symbol = item.get("symbol")
            if not symbol or symbol in positions:
                continue
            effective_policy = dict(policy)
            if len(closed_trades) > 0:
                effective_policy["score_floor"] = max(int(policy["score_floor"]), REINVESTMENT_SCORE_FLOOR)
            if not is_entry_candidate(item, effective_policy):
                continue
            df = dfs.get(symbol)
            if df is None or df.empty:
                continue
            _, exec_open = open_on_or_after(df, execution_date)
            if exec_open is None or exec_open <= 0:
                continue
            buy_price = exec_open * (1.0 + BUY_SLIPPAGE_PCT)
            budget = min(entry_budget_base, cash)
            shares = int((budget // (buy_price * ROUND_LOT)) * ROUND_LOT)
            if shares < ROUND_LOT:
                continue
            cost = shares * buy_price
            if cost > cash:
                continue
            cash -= cost
            positions[symbol] = Position(
                symbol=symbol,
                name=item.get("name") or symbol,
                theme=item.get("theme") or "Unknown",
                bucket=item.get("bucket") or "Unknown",
                signal=translate_signal(item.get("triage")),
                quality=item.get("classification") or item.get("archetype") or "Unknown",
                entry_eval_date=eval_date.strftime("%Y-%m-%d"),
                entry_date=execution_date.strftime("%Y-%m-%d"),
                entry_price=buy_price,
                shares=shares,
                cost=cost,
                score_entry=int(item.get("score_pts") or 0),
                rank_entry=int(item.get("rank") or 9999),
                benchmark_entry_price=bench_open,
                benchmark_units=(cost / bench_open) if bench_open and bench_open > 0 else None,
            )
            new_count += 1

        # Mark-to-market at execution close.
        market_value = 0.0
        open_positions = []
        for symbol, pos in positions.items():
            df = dfs.get(symbol)
            close_price = close_on_or_before(df, execution_date)[1] if df is not None else None
            mv = pos.market_value(close_price)
            market_value += mv
            ret = pos.return_pct(close_price)
            open_positions.append({
                "symbol": symbol,
                "name": pos.name,
                "theme": pos.theme,
                "bucket": pos.bucket,
                "signal": pos.signal,
                "quality": pos.quality,
                "entry_date": pos.entry_date,
                "entry_eval_date": pos.entry_eval_date,
                "entry_price": round(pos.entry_price, 4),
                "last_price": safe_round(close_price, 4),
                "shares": pos.shares,
                "market_value_jpy": round(mv, 2),
                "weight_pct": None,
                "return_pct": safe_round(ret, 4),
                "score_entry": pos.score_entry,
                "rank_entry": pos.rank_entry,
                "stop_distance_pct": safe_round((ret or 0) + STOP_LOSS_PCT * 100.0, 4) if ret is not None else None,
            })

        equity = cash + market_value
        for op in open_positions:
            if equity > 0:
                op["weight_pct"] = round(op["market_value_jpy"] / equity * 100.0, 4)

        benchmark_equity = None
        benchmark_return = None
        if benchmark_units is not None and bench_close and benchmark_initial_open:
            raw_bench_ret = pct_return(benchmark_initial_open, bench_close)
            if raw_bench_ret is not None and abs(raw_bench_ret) > BENCHMARK_ABS_LIMIT_PCT:
                benchmark_invalid = True
                if len(benchmark_invalid_samples) < 10:
                    benchmark_invalid_samples.append({
                        "date": execution_date.strftime("%Y-%m-%d"),
                        "benchmark_return_pct": safe_round(raw_bench_ret, 4),
                    })
            if not benchmark_invalid:
                benchmark_equity = benchmark_units * bench_close
                benchmark_return = (benchmark_equity / INITIAL_CAPITAL - 1.0) * 100.0

        strategy_return = (equity / INITIAL_CAPITAL - 1.0) * 100.0
        alpha = (strategy_return - benchmark_return) if benchmark_return is not None and not benchmark_invalid else None

        equity_curve.append({
            "date": execution_date.strftime("%Y-%m-%d"),
            "eval_date": eval_date.strftime("%Y-%m-%d"),
            "execution_date": execution_date.strftime("%Y-%m-%d"),
            "cash_jpy": round(cash, 2),
            "market_value_jpy": round(market_value, 2),
            "portfolio_equity_jpy": round(equity, 2),
            "strategy_return_pct": round(strategy_return, 4),
            "benchmark_equity_jpy": round(benchmark_equity, 2) if benchmark_equity is not None else None,
            "benchmark_return_pct": safe_round(benchmark_return, 4),
            "alpha_pct": safe_round(alpha, 4),
            "open_positions_count": len(positions),
            "closed_trades_count": len(closed_trades),
        })

    final_equity = equity_curve[-1]["portfolio_equity_jpy"] if equity_curve else INITIAL_CAPITAL
    final_return = (final_equity / INITIAL_CAPITAL - 1.0) * 100.0
    final_benchmark_return = equity_curve[-1].get("benchmark_return_pct") if equity_curve else None
    final_alpha = (final_return - final_benchmark_return) if final_benchmark_return is not None else None

    equity_values = [float(x["portfolio_equity_jpy"]) for x in equity_curve]
    closed_summary = aggregate_closed_trades(closed_trades)

    open_positions_final = []
    if equity_curve:
        # Reconstruct final open positions from current dict.
        final_date = pd.to_datetime(equity_curve[-1]["date"])
        final_equity = float(equity_curve[-1]["portfolio_equity_jpy"])
        for symbol, pos in positions.items():
            df = dfs.get(symbol)
            close_price = close_on_or_before(df, final_date)[1] if df is not None else None
            mv = pos.market_value(close_price)
            open_positions_final.append({
                "symbol": symbol,
                "name": pos.name,
                "theme": pos.theme,
                "bucket": pos.bucket,
                "signal": pos.signal,
                "quality": pos.quality,
                "entry_date": pos.entry_date,
                "entry_eval_date": pos.entry_eval_date,
                "entry_price": round(pos.entry_price, 4),
                "last_price": safe_round(close_price, 4),
                "shares": pos.shares,
                "market_value_jpy": round(mv, 2),
                "weight_pct": round(mv / final_equity * 100.0, 4) if final_equity else None,
                "return_pct": safe_round(pos.return_pct(close_price), 4),
                "score_entry": pos.score_entry,
                "rank_entry": pos.rank_entry,
            })

    theme_exposure: dict[str, float] = {}
    bucket_exposure: dict[str, float] = {}
    for p in open_positions_final:
        theme_exposure[p["theme"]] = theme_exposure.get(p["theme"], 0.0) + float(p["market_value_jpy"] or 0)
        bucket_exposure[p["bucket"]] = bucket_exposure.get(p["bucket"], 0.0) + float(p["market_value_jpy"] or 0)

    def exposure_rows(src: dict[str, float]) -> list[dict[str, Any]]:
        total = sum(src.values())
        return [
            {"name": k, "market_value_jpy": round(v, 2), "weight_pct": round(v / total * 100.0, 2) if total else None}
            for k, v in sorted(src.items(), key=lambda kv: kv[1], reverse=True)
        ]

    benchmark_quality = {
        "benchmark_symbol": BENCHMARK_SYMBOL,
        "abs_return_limit_pct": BENCHMARK_ABS_LIMIT_PCT,
        "status": "invalid" if benchmark_invalid else "valid",
        "message": (
            "TOPIX benchmark comparison suspended because cached benchmark prices failed the sanity check. "
            "Strategy return and cash accounting remain valid."
            if benchmark_invalid
            else "Benchmark comparison passed sanity checks."
        ),
        "invalid_samples": benchmark_invalid_samples,
    }

    return {
        "policy_id": policy["id"],
        "policy_label": policy["label"],
        "summary": {
            "initial_capital_jpy": INITIAL_CAPITAL,
            "portfolio_equity_jpy": round(final_equity, 2),
            "cash_jpy": round(cash, 2),
            "market_value_jpy": round(sum(float(p.get("market_value_jpy") or 0) for p in open_positions_final), 2),
            "strategy_return_pct": round(final_return, 4),
            "benchmark_return_pct": safe_round(final_benchmark_return, 4) if not benchmark_invalid else None,
            "alpha_pct": safe_round(final_alpha, 4) if final_alpha is not None and not benchmark_invalid else None,
            "max_drawdown_pct": max_drawdown_pct(equity_values),
            "open_positions_count": len(open_positions_final),
            "closed_trades_count": len(closed_trades),
            "eval_points": len(equity_curve),
            "date_start": equity_curve[0]["date"] if equity_curve else None,
            "date_end": equity_curve[-1]["date"] if equity_curve else None,
        },
        "policy": {
            "position_size_pct": POSITION_SIZE_PCT,
            "max_positions": MAX_POSITIONS,
            "max_new_positions_per_day": MAX_NEW_POSITIONS_PER_DAY,
            "round_lot": ROUND_LOT,
            "buy_slippage_pct": BUY_SLIPPAGE_PCT,
            "sell_slippage_pct": SELL_SLIPPAGE_PCT,
            "entry_rank_limit": policy["rank_limit"],
            "entry_score_floor": policy["score_floor"],
            "allow_monitor": policy["allow_monitor"],
            "stop_loss_pct": policy["stop"],
            "score_exit_floor": SCORE_EXIT_FLOOR,
            "time_exit_days": policy["time_exit"],
        },
        "benchmark_quality": benchmark_quality,
        "equity_curve": equity_curve,
        "open_positions": open_positions_final,
        "closed_trades": closed_trades[-80:],
        "closed_trade_summary": closed_summary,
        "theme_exposure": exposure_rows(theme_exposure),
        "bucket_exposure": exposure_rows(bucket_exposure),
        "latest_snapshot": latest_snapshot[:10],
    }


def select_eval_dates(equities: list[dict[str, Any]], benchmark_item: dict[str, Any] | None) -> list[pd.Timestamp]:
    if benchmark_item:
        base_df = bars_to_df_from_item(benchmark_item)
    else:
        base_df = bars_to_df_from_item(equities[0]) if equities else pd.DataFrame()
    if base_df.empty:
        return []
    dates = list(base_df.index)
    # Need next open, so remove the latest date.
    dates = dates[:-1]
    # Require enough history and preserve recent days.
    dates = dates[MIN_HISTORY_BARS:]
    if SIM_DAYS > 0:
        dates = dates[-SIM_DAYS:]
    return dates


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"PRICES_JSON={safe_relative(PRICES_JSON)}")

    build_mod = load_build_daily_module()
    prices = read_json(PRICES_JSON)
    equities = prices.get("equities") or []
    if not equities:
        raise RuntimeError("No equities in price JSON")

    benchmark_item = None
    for item in (prices.get("market_pulse") or []) + equities:
        if item.get("symbol") == BENCHMARK_SYMBOL or item.get("source_symbol") == BENCHMARK_SYMBOL:
            benchmark_item = item
            break

    eval_dates = select_eval_dates(equities, benchmark_item)
    if not eval_dates:
        raise RuntimeError("No evaluation dates available for Daily JP simulation")

    dfs = {item["symbol"]: bars_to_df_from_item(item) for item in equities}
    bdf = bars_to_df_from_item(benchmark_item) if benchmark_item else pd.DataFrame()

    snapshots_by_date: dict[str, list[dict[str, Any]]] = {}
    print(f"Precomputing Daily score snapshots for {len(eval_dates)} evaluation days...")
    for i, d in enumerate(eval_dates, 1):
        key = d.strftime("%Y-%m-%d")
        snapshots_by_date[key] = score_snapshot(build_mod, equities, benchmark_item, d)
        if i % 25 == 0 or i == len(eval_dates):
            print(f"  snapshots {i}/{len(eval_dates)}")

    default_policy = dict(POLICY_PRESETS[0])
    default_policy.update({
        "rank_limit": ENTRY_RANK_LIMIT,
        "score_floor": ENTRY_SCORE_FLOOR,
        "allow_monitor": ALLOW_MONITOR and not TRADE_ONLY,
        "stop": STOP_LOSS_PCT,
        "time_exit": TIME_EXIT_DAYS,
    })

    default_result = run_simulation(equities, benchmark_item, default_policy, eval_dates, snapshots_by_date, dfs, bdf)

    comparisons = []
    for p in POLICY_PRESETS:
        result = run_simulation(equities, benchmark_item, p, eval_dates, snapshots_by_date, dfs, bdf)
        comparisons.append({
            "policy_id": p["id"],
            "label": p["label"],
            "strategy_return_pct": result["summary"].get("strategy_return_pct"),
            "alpha_pct": result["summary"].get("alpha_pct"),
            "max_drawdown_pct": result["summary"].get("max_drawdown_pct"),
            "closed_trades_count": result["summary"].get("closed_trades_count"),
            "win_rate_pct": result["closed_trade_summary"].get("win_rate_pct"),
            "portfolio_equity_jpy": result["summary"].get("portfolio_equity_jpy"),
        })

    generated_at = iso_now()
    asof = default_result["summary"].get("date_end")
    payload = {
        "schema_version": "daily-jp-simulation-v1",
        "generated_at": generated_at,
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "source_prices": safe_relative(PRICES_JSON),
        "source_prices_generated_at": prices.get("generated_at"),
        "date": asof,
        "range": {
            "eval_date_start": eval_dates[0].strftime("%Y-%m-%d"),
            "eval_date_end": eval_dates[-1].strftime("%Y-%m-%d"),
            "execution_date_start": default_result["summary"].get("date_start"),
            "execution_date_end": default_result["summary"].get("date_end"),
            "eval_days": len(eval_dates),
        },
        "summary": default_result["summary"],
        "policy": default_result["policy"],
        "benchmark_quality": default_result["benchmark_quality"],
        "equity_curve": default_result["equity_curve"],
        "open_positions": default_result["open_positions"],
        "closed_trades": default_result["closed_trades"],
        "closed_trade_summary": default_result["closed_trade_summary"],
        "theme_exposure": default_result["theme_exposure"],
        "bucket_exposure": default_result["bucket_exposure"],
        "policy_comparison": comparisons,
        "latest_snapshot": default_result["latest_snapshot"],
        "methodology": {
            "entry": "Signal date close, next trading day open execution.",
            "mark_to_market": "Execution date close. New entries are never marked on pre-entry dates.",
            "benchmark": f"{BENCHMARK_SYMBOL} initialized at the same first execution open.",
            "controls": "JP round lots, slippage, cash accounting, benchmark sanity guard, no API calls during replay.",
        },
    }

    date_key = asof or now_jst().strftime("%Y-%m-%d")
    for out_dir in [PRIMARY_OUT_DIR, COMPAT_OUT_DIR]:
        write_json(out_dir / f"{date_key}.json", payload)
        write_json(out_dir / "latest.json", payload)
        write_json(out_dir / "manifest.json", {
            "schema_version": "daily-jp-simulation-manifest-v1",
            "generated_at": generated_at,
            "latest": "latest.json",
            "items": [{"date": date_key, "path": f"{date_key}.json"}],
        })

    print(f"Wrote {safe_relative(PRIMARY_OUT_DIR / 'latest.json')}")
    print(f"eval_days={len(eval_dates)} return={payload['summary'].get('strategy_return_pct')} closed={payload['summary'].get('closed_trades_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
