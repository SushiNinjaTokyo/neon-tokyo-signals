#!/usr/bin/env python3
from __future__ import annotations

"""Rebuild an AI Arena calendar-year season from DuckDB.

This is the new Daily/Weekly-independent engine. It reads:

- prices_daily
- features_daily
- agent_scores_daily
- data/agents/*.yml

It writes run-scoped orders, positions, trades, equity curves, rankings, and
public lightweight JSON under site/data/japan/ai-arena/.

Design notes:
- The engine rebuilds a complete run from scratch when RESET_RUN=true.
- It never reads site/data/daily-jp or site/data/weekly-jp.
- It supports rebuild run IDs so rule changes can be applied to historical data
  without overwriting prior results.
"""

import os
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from lib.db import ROOT, connect_db, safe_rel
from lib.duckdb_schema import initialize_schema
from lib.arena_calendar_jp import build_season_dates, next_trading_date, parse_date
from lib.arena_run_manager_jp import (
    RunConfig,
    create_or_replace_run,
    default_live_run_id,
    load_yaml,
    next_rebuild_run_id,
    promote_display_run,
    rules_hash_for_files,
)
from lib.agent_rule_engine_jp import fetch_feature_map, fetch_score_map, passes_entry_rule
from lib.execution_engine_jp import choose_execution_price, fetch_price_row
from lib.portfolio_engine_jp import apply_bps, compute_buy_shares
from lib.risk_engine_jp import should_exit_position
from lib.arena_ranking_engine_jp import rebuild_rankings
from lib.arena_exporter_jp import export_arena_payloads

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()

PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
YEAR = int(os.getenv("ARENA_YEAR", os.getenv("YEAR", str(datetime.utcnow().year))))
START_DATE = os.getenv("START_DATE") or f"{YEAR}-01-01"
END_DATE = os.getenv("END_DATE") or ""
RUN_MODE = os.getenv("RUN_MODE", "rebuild").lower().strip()  # rebuild|live
RUN_ID_ENV = os.getenv("RUN_ID", "").strip()
RESET_RUN = os.getenv("RESET_RUN", "true").lower() == "true"
PROMOTE_DISPLAY_RUN = os.getenv("PROMOTE_DISPLAY_RUN", "true").lower() == "true"
FORCE_FINALIZE_SEASON = os.getenv("FORCE_FINALIZE_SEASON", "false").lower() in {"1", "true", "yes", "on"}
RULE_NOTE = os.getenv("RULES_VERSION_NOTE", "")

AGENTS_YML = ROOT / "data" / "agents" / "jp_agents.yml"
STRATEGY_YML = ROOT / "data" / "agents" / "jp_agent_strategy_rules.yml"
PORTFOLIO_YML = ROOT / "data" / "agents" / "jp_agent_portfolio_rules.yml"


@dataclass
class Position:
    position_id: str
    agent_id: str
    ticker: str
    name: str
    entry_signal_date: date
    entry_date: date
    entry_price: float
    shares: int
    cost_basis_jpy: float
    high_water_return_pct: float = 0.0
    entry_reason_code: str = "ENTRY_RULE_PASS"
    entry_reason_text: str = "Entry rule passed."


@dataclass
class AgentState:
    agent_id: str
    cash_jpy: float
    positions: dict[str, Position] = field(default_factory=dict)
    realized_pnl_jpy: float = 0.0
    previous_equity_jpy: float | None = None


def rows_to_insert(conn, table: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    df = pd.DataFrame(rows)
    conn.register(f"_{table}", df)
    conn.execute(f"INSERT INTO {table} SELECT * FROM _{table}")
    conn.unregister(f"_{table}")


def load_agents_for_public() -> list[dict[str, Any]]:
    data = load_yaml(AGENTS_YML)
    return data.get("agents", []) or []


def feature_for_ticker(feature_map: dict[str, dict[str, Any]], ticker: str) -> dict[str, Any] | None:
    return feature_map.get(ticker)


def score_for_ticker(score_map: dict[tuple[str, str], dict[str, Any]], agent_id: str, ticker: str) -> dict[str, Any] | None:
    return score_map.get((agent_id, ticker))


def main() -> int:
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)

    agents_cfg = load_yaml(AGENTS_YML)
    strategy_cfg = load_yaml(STRATEGY_YML)
    portfolio_cfg = load_yaml(PORTFOLIO_YML)
    agents = agents_cfg.get("agents", []) or []
    if len(agents) != 7:
        raise SystemExit(f"Expected 7 agents in {AGENTS_YML}, got {len(agents)}")

    global_pf = portfolio_cfg.get("global", {}) or {}
    initial_capital = float(global_pf.get("initial_capital_jpy", 10_000_000))
    share_lot_size = int(global_pf.get("share_lot_size", 1) or 1)
    commission_bps = float(global_pf.get("commission_bps", 0) or 0)
    slippage_bps = float(global_pf.get("slippage_bps", 10) or 0)

    season = build_season_dates(conn, YEAR, START_DATE, END_DATE or None)
    if not season.trading_dates:
        raise SystemExit(f"No trading dates found in prices_daily for {START_DATE} - {END_DATE or YEAR}")

    run_id = RUN_ID_ENV
    if not run_id:
        run_id = default_live_run_id(YEAR) if RUN_MODE == "live" else next_rebuild_run_id(conn, YEAR)

    rules_hash = rules_hash_for_files([AGENTS_YML, STRATEGY_YML, PORTFOLIO_YML])
    run_cfg = RunConfig(
        run_id=run_id,
        year=YEAR,
        run_type=RUN_MODE,
        start_date=season.season_start,
        end_date=season.last_trading_date or season.season_end,
        initial_capital_jpy=initial_capital,
        share_lot_size=share_lot_size,
        strategy_rules_version=str(strategy_cfg.get("rules_version") or "unknown"),
        portfolio_rules_version=str(portfolio_cfg.get("rules_version") or "unknown"),
        rules_hash=rules_hash,
    )
    create_or_replace_run(conn, run_cfg, reset_run=RESET_RUN, note=RULE_NOTE)
    try:
        conn.execute(
            "UPDATE arena_simulation_runs SET force_close_positions_at_year_end = ?, finalized_season = ? WHERE run_id = ?",
            [FORCE_FINALIZE_SEASON, FORCE_FINALIZE_SEASON, run_id],
        )
    except Exception:
        # Older DB caches may not have finalized_season until schema migration.
        pass

    states = {a["agent_id"]: AgentState(agent_id=a["agent_id"], cash_jpy=initial_capital) for a in agents}
    agent_rules = strategy_cfg.get("agents", {}) or {}
    portfolio_rules = portfolio_cfg.get("agents", {}) or {}

    orders: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    equity_rows: list[dict[str, Any]] = []
    pending_orders: list[dict[str, Any]] = []
    now = datetime.utcnow()

    def close_position(*, state: AgentState, pos: Position, signal_date: date, exit_date: date, exit_price_raw: float, code: str, text: str) -> None:
        exit_price = apply_bps(exit_price_raw, slippage_bps, "SELL")
        value = exit_price * pos.shares
        pnl = (exit_price - pos.entry_price) * pos.shares
        ret = (exit_price / pos.entry_price - 1.0) * 100.0 if pos.entry_price else 0.0
        state.cash_jpy += value
        state.realized_pnl_jpy += pnl
        state.positions.pop(pos.ticker, None)
        trades.append({
            "run_id": run_id,
            "trade_id": f"TRD-{uuid.uuid4().hex[:16]}",
            "agent_id": state.agent_id,
            "ticker": pos.ticker,
            "name": pos.name,
            "entry_signal_date": pos.entry_signal_date,
            "entry_date": pos.entry_date,
            "entry_price": pos.entry_price,
            "exit_signal_date": signal_date,
            "exit_date": exit_date,
            "exit_price": exit_price,
            "shares": pos.shares,
            "realized_pnl_jpy": pnl,
            "realized_return_pct": ret,
            "holding_days": max(0, (exit_date - pos.entry_date).days),
            "entry_reason_code": pos.entry_reason_code,
            "entry_reason_text": pos.entry_reason_text,
            "exit_reason_code": code,
            "exit_reason_text": text,
            "created_at": now,
        })
        orders.append({
            "run_id": run_id,
            "order_id": f"ORD-{uuid.uuid4().hex[:16]}",
            "agent_id": state.agent_id,
            "ticker": pos.ticker,
            "name": pos.name,
            "signal_date": signal_date,
            "execution_date": exit_date,
            "side": "SELL",
            "order_type": "year_end" if code == "YEAR_END_CLOSE" else "exit",
            "planned_price": exit_price_raw,
            "execution_price": exit_price,
            "shares": pos.shares,
            "order_value_jpy": value,
            "commission_jpy": 0.0,
            "slippage_jpy": (exit_price_raw - exit_price) * pos.shares,
            "order_status": "FILLED",
            "reason_code": code,
            "reason_text": text,
            "created_at": now,
        })

    for d in season.trading_dates:
        feature_map = fetch_feature_map(conn, d)
        score_map = fetch_score_map(conn, d)
        next_d = next_trading_date(season.trading_dates, d)

        # 1) Execute pending next-open orders scheduled by prior signals.
        still_pending = []
        for order in pending_orders:
            if order["execution_date"] != d:
                still_pending.append(order)
                continue
            state = states[order["agent_id"]]
            px = choose_execution_price(fetch_price_row(conn, order["ticker"], d), "open")
            if px is None:
                order.update({"order_status": "CANCELLED", "execution_price": None, "order_value_jpy": 0.0, "commission_jpy": 0.0, "slippage_jpy": 0.0})
                orders.append(order)
                continue
            if order["side"] == "BUY":
                exec_px = apply_bps(px, slippage_bps, "BUY")
                cost = exec_px * int(order["shares"])
                if cost > state.cash_jpy or order["ticker"] in state.positions:
                    order.update({"order_status": "CANCELLED", "execution_price": exec_px, "order_value_jpy": 0.0, "commission_jpy": 0.0, "slippage_jpy": (exec_px - px) * int(order["shares"])})
                    orders.append(order)
                    continue
                state.cash_jpy -= cost
                state.positions[order["ticker"]] = Position(
                    position_id=f"POS-{uuid.uuid4().hex[:16]}",
                    agent_id=state.agent_id,
                    ticker=order["ticker"],
                    name=order["name"],
                    entry_signal_date=order["signal_date"],
                    entry_date=d,
                    entry_price=exec_px,
                    shares=int(order["shares"]),
                    cost_basis_jpy=cost,
                    entry_reason_code=order["reason_code"],
                    entry_reason_text=order["reason_text"],
                )
                order.update({"order_status": "FILLED", "execution_price": exec_px, "order_value_jpy": cost, "commission_jpy": 0.0, "slippage_jpy": (exec_px - px) * int(order["shares"])})
                orders.append(order)
            elif order["side"] == "SELL":
                pos = state.positions.get(order["ticker"])
                if not pos:
                    order.update({"order_status": "CANCELLED", "execution_price": px, "order_value_jpy": 0.0, "commission_jpy": 0.0, "slippage_jpy": 0.0})
                    orders.append(order)
                    continue
                close_position(
                    state=state,
                    pos=pos,
                    signal_date=order["signal_date"],
                    exit_date=d,
                    exit_price_raw=px,
                    code=order["reason_code"],
                    text=order["reason_text"],
                )
        pending_orders = still_pending

        # 2) Mark-to-market and evaluate exits.
        for agent in agents:
            aid = agent["agent_id"]
            state = states[aid]
            rule = agent_rules.get(aid, {}) or {}
            for ticker, pos in list(state.positions.items()):
                price_row = fetch_price_row(conn, ticker, d)
                close_px = choose_execution_price(price_row, "close")
                if close_px is None:
                    continue
                ret = (close_px / pos.entry_price - 1.0) * 100.0 if pos.entry_price else 0.0
                pos.high_water_return_pct = max(pos.high_water_return_pct, ret)
                should_exit, code, text = should_exit_position(
                    agent_id=aid,
                    rule=rule,
                    position=pos.__dict__,
                    feature_row=feature_for_ticker(feature_map, ticker),
                    score_row=score_for_ticker(score_map, aid, ticker),
                    current_price=close_px,
                    holding_days=max(0, (d - pos.entry_date).days),
                    high_water_return_pct=pos.high_water_return_pct,
                )
                if should_exit and next_d:
                    # Signal at current close, execute next session open.
                    pending_orders.append({
                        "run_id": run_id,
                        "order_id": f"ORD-{uuid.uuid4().hex[:16]}",
                        "agent_id": aid,
                        "ticker": ticker,
                        "name": pos.name,
                        "signal_date": d,
                        "execution_date": next_d,
                        "side": "SELL",
                        "order_type": "exit",
                        "planned_price": close_px,
                        "execution_price": None,
                        "shares": pos.shares,
                        "order_value_jpy": None,
                        "commission_jpy": None,
                        "slippage_jpy": None,
                        "order_status": "PENDING",
                        "reason_code": code,
                        "reason_text": text,
                        "created_at": now,
                    })
                    # To avoid duplicate sell orders, keep position but skip new exits until it fills.

        # 3) Create new entry orders from today's scores.
        if next_d:
            scores_df = conn.execute(
                "SELECT * FROM agent_scores_daily WHERE date = ? AND action = 'Trade' ORDER BY agent_id, rank",
                [d],
            ).df()
            for agent in agents:
                aid = agent["agent_id"]
                state = states[aid]
                arule = agent_rules.get(aid, {}) or {}
                prule = portfolio_rules.get(aid, {}) or {}
                max_positions = int(prule.get("max_positions", 8) or 8)
                max_new = int(prule.get("max_new_entries_per_day", 1) or 1)
                if len(state.positions) >= max_positions:
                    continue
                new_count = 0
                adf = scores_df[scores_df["agent_id"] == aid] if not scores_df.empty else pd.DataFrame()
                for _, sr in adf.iterrows():
                    if new_count >= max_new or len(state.positions) >= max_positions:
                        break
                    row = sr.to_dict()
                    ticker = str(row["ticker"])
                    if ticker in state.positions:
                        continue
                    if any(o["agent_id"] == aid and o["ticker"] == ticker and o["side"] == "BUY" for o in pending_orders):
                        continue
                    feat = feature_for_ticker(feature_map, ticker)
                    ok, reason = passes_entry_rule(score_row=row, feature_row=feat, agent_rule=arule, trading_dates=season.trading_dates, signal_date=d)
                    if not ok:
                        continue
                    next_price = choose_execution_price(fetch_price_row(conn, ticker, next_d), "open")
                    if next_price is None:
                        continue
                    current_mv = 0.0
                    for p in state.positions.values():
                        pr = fetch_price_row(conn, p.ticker, d)
                        cp = choose_execution_price(pr, "close") or p.entry_price
                        current_mv += cp * p.shares
                    shares = compute_buy_shares(
                        equity_jpy=state.cash_jpy + current_mv,
                        cash_jpy=state.cash_jpy,
                        execution_price=apply_bps(next_price, slippage_bps, "BUY"),
                        score=float(row.get("normalized_score") or 0.0),
                        min_score=float((arule.get("entry") or {}).get("min_score", 0.0) or 0.0),
                        target_position_pct=float(prule.get("target_position_pct", 0.10) or 0.10),
                        max_position_pct=float(prule.get("max_position_pct", 0.15) or 0.15),
                        max_total_exposure_pct=float(prule.get("max_total_exposure_pct", 0.90) or 0.90),
                        current_market_value_jpy=current_mv,
                        commission_bps=commission_bps,
                        share_lot_size=share_lot_size,
                    )
                    if shares <= 0:
                        continue
                    pending_orders.append({
                        "run_id": run_id,
                        "order_id": f"ORD-{uuid.uuid4().hex[:16]}",
                        "agent_id": aid,
                        "ticker": ticker,
                        "name": row.get("name") or ticker,
                        "signal_date": d,
                        "execution_date": next_d,
                        "side": "BUY",
                        "order_type": "entry",
                        "planned_price": next_price,
                        "execution_price": None,
                        "shares": shares,
                        "order_value_jpy": None,
                        "commission_jpy": None,
                        "slippage_jpy": None,
                        "order_status": "PENDING",
                        "reason_code": "ENTRY_RULE_PASS",
                        "reason_text": f"{agent.get('name', aid)} entry: {reason}",
                        "created_at": now,
                    })
                    new_count += 1

        # 4) Record end-of-day equity.
        for agent in agents:
            aid = agent["agent_id"]
            state = states[aid]
            mv = 0.0
            unrealized = 0.0
            for pos in state.positions.values():
                pr = fetch_price_row(conn, pos.ticker, d)
                cp = choose_execution_price(pr, "close") or pos.entry_price
                mv += cp * pos.shares
                unrealized += (cp - pos.entry_price) * pos.shares
            equity = state.cash_jpy + mv
            daily_ret = 0.0 if state.previous_equity_jpy in (None, 0) else (equity / state.previous_equity_jpy - 1.0) * 100.0
            total_ret = (equity / initial_capital - 1.0) * 100.0
            state.previous_equity_jpy = equity
            equity_rows.append({
                "run_id": run_id,
                "agent_id": aid,
                "date": d,
                "cash_jpy": state.cash_jpy,
                "market_value_jpy": mv,
                "realized_pnl_jpy": state.realized_pnl_jpy,
                "unrealized_pnl_jpy": unrealized,
                "portfolio_equity_jpy": equity,
                "daily_return_pct": daily_ret,
                "total_return_pct": total_ret,
                "open_positions": len(state.positions),
                "created_at": now,
            })

    # 5) Optionally force-close all remaining positions.
    # During an in-progress calendar year, open positions must remain open.
    # Otherwise the public Positions page becomes empty and the simulation no
    # longer represents the live season.  Force-close only when explicitly
    # finalizing the season, typically after year-end.
    last_d = season.last_trading_date
    should_finalize = bool(FORCE_FINALIZE_SEASON)
    if should_finalize and last_d:
        equity_rows = [r for r in equity_rows if r["date"] != last_d]
        for aid, state in states.items():
            for ticker, pos in list(state.positions.items()):
                pr = fetch_price_row(conn, ticker, last_d)
                cp = choose_execution_price(pr, "close") or pos.entry_price
                close_position(
                    state=state,
                    pos=pos,
                    signal_date=last_d,
                    exit_date=last_d,
                    exit_price_raw=cp,
                    code="YEAR_END_CLOSE",
                    text="Closed automatically at season finalization to lock annual ranking.",
                )
        for agent in agents:
            aid = agent["agent_id"]
            state = states[aid]
            equity = state.cash_jpy
            equity_rows.append({
                "run_id": run_id,
                "agent_id": aid,
                "date": last_d,
                "cash_jpy": state.cash_jpy,
                "market_value_jpy": 0.0,
                "realized_pnl_jpy": state.realized_pnl_jpy,
                "unrealized_pnl_jpy": 0.0,
                "portfolio_equity_jpy": equity,
                "daily_return_pct": 0.0 if state.previous_equity_jpy in (None, 0) else (equity / state.previous_equity_jpy - 1.0) * 100.0,
                "total_return_pct": (equity / initial_capital - 1.0) * 100.0,
                "open_positions": 0,
                "created_at": now,
            })

    # 6) Persist the run output.
    rows_to_insert(conn, "arena_orders", orders)
    rows_to_insert(conn, "arena_trades", trades)
    rows_to_insert(conn, "arena_equity_curve", equity_rows)

    open_rows = []
    for aid, state in states.items():
        for pos in state.positions.values():
            pr = fetch_price_row(conn, pos.ticker, season.last_trading_date or season.trading_dates[-1])
            cp = choose_execution_price(pr, "close") or pos.entry_price
            mv = cp * pos.shares
            open_rows.append({
                "run_id": run_id,
                "position_id": pos.position_id,
                "agent_id": aid,
                "ticker": pos.ticker,
                "name": pos.name,
                "entry_signal_date": pos.entry_signal_date,
                "entry_date": pos.entry_date,
                "entry_price": pos.entry_price,
                "shares": pos.shares,
                "cost_basis_jpy": pos.cost_basis_jpy,
                "last_date": season.last_trading_date,
                "last_price": cp,
                "market_value_jpy": mv,
                "unrealized_pnl_jpy": (cp - pos.entry_price) * pos.shares,
                "unrealized_return_pct": (cp / pos.entry_price - 1.0) * 100.0 if pos.entry_price else 0.0,
                "holding_days": max(0, ((season.last_trading_date or pos.entry_date) - pos.entry_date).days),
                "high_water_return_pct": pos.high_water_return_pct,
                "status": "OPEN",
                "updated_at": now,
            })
    rows_to_insert(conn, "arena_open_positions", open_rows)

    persisted_counts = {
        "arena_orders": conn.execute("SELECT COUNT(*) FROM arena_orders WHERE run_id = ?", [run_id]).fetchone()[0],
        "arena_trades": conn.execute("SELECT COUNT(*) FROM arena_trades WHERE run_id = ?", [run_id]).fetchone()[0],
        "arena_open_positions": conn.execute("SELECT COUNT(*) FROM arena_open_positions WHERE run_id = ?", [run_id]).fetchone()[0],
        "arena_equity_curve": conn.execute("SELECT COUNT(*) FROM arena_equity_curve WHERE run_id = ?", [run_id]).fetchone()[0],
    }
    if persisted_counts["arena_equity_curve"] <= 0:
        raise RuntimeError(f"Arena run {run_id} did not persist equity curve rows to DuckDB: {persisted_counts}")

    ranking_diag = rebuild_rankings(conn, run_id=run_id, year=YEAR, initial_capital_jpy=initial_capital)
    if PROMOTE_DISPLAY_RUN:
        promote_display_run(conn, year=YEAR, run_id=run_id, note=RULE_NOTE or "Promoted by season rebuild workflow")

    outputs = export_arena_payloads(conn, out_dir=OUT_DIR, run_id=run_id, year=YEAR, agents=load_agents_for_public())
    print(f"run_id={run_id}")
    print(f"trading_dates={len(season.trading_dates)}")
    print(f"orders={len(orders)} trades={len(trades)} equity_rows={len(equity_rows)} open_positions={len(open_rows)} finalized={FORCE_FINALIZE_SEASON}")
    print(f"persisted_counts={persisted_counts}")
    print(f"ranking_diag={ranking_diag}")
    for key, path in outputs.items():
        print(f"Wrote {key}: {safe_rel(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
