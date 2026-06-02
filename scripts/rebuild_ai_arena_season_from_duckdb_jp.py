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

import json
import os
import uuid
from collections import Counter
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
from lib.agent_rule_engine_jp import fetch_feature_map, fetch_score_map, passes_entry_rule, entry_position_size_multiplier, market_regime_state
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


def truthy_env(value: str | None, default: bool = False) -> bool:
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def latest_equity_price_date(conn) -> date | None:
    row = conn.execute(
        """
        SELECT MAX(p.date)
        FROM prices_daily p
        LEFT JOIN universe_master u USING (ticker)
        WHERE COALESCE(LOWER(u.asset_type), 'equity') = 'equity'
        """
    ).fetchone()
    return parse_date(row[0]) if row and row[0] is not None else None


def resolve_year(conn) -> int:
    raw = first_env("AI_ARENA_YEAR", "ARENA_YEAR", "YEAR", default=str(datetime.utcnow().year))
    if raw.lower() == "auto":
        d = latest_equity_price_date(conn)
        return int(d.year if d else datetime.utcnow().year)
    return int(raw)


def resolve_runtime_config(conn) -> dict[str, Any]:
    year = resolve_year(conn)
    start_date = first_env("AI_ARENA_START_DATE", "ARENA_START_DATE", "START_DATE", default=f"{year}-01-01")
    end_date = first_env("AI_ARENA_END_DATE", "ARENA_END_DATE", "END_DATE", default="")
    run_mode = first_env("AI_ARENA_RUN_MODE", "ARENA_RUN_MODE", "RUN_MODE", default="rebuild").lower()
    # Workflow previously used append. Internally this engine rebuilds a full deterministic season.
    # Keep the display run stable by treating append as live.
    if run_mode == "append":
        run_mode = "live"
    return {
        "year": year,
        "start_date": start_date,
        "end_date": end_date,
        "run_mode": run_mode,
        "run_id": first_env("AI_ARENA_RUN_ID", "ARENA_RUN_ID", "RUN_ID", default=""),
        "reset_run": truthy_env(first_env("AI_ARENA_RESET_RUN", "ARENA_RESET_RUN", "RESET_RUN", default="true"), True),
        "promote_display_run": truthy_env(first_env("AI_ARENA_PROMOTE_DISPLAY_RUN", "ARENA_PROMOTE_DISPLAY_RUN", "PROMOTE_DISPLAY_RUN", default="true"), True),
        "force_finalize_season": truthy_env(os.getenv("FORCE_FINALIZE_SEASON"), False),
        "rule_note": os.getenv("RULES_VERSION_NOTE", ""),
        "fail_if_no_orders": truthy_env(os.getenv("AI_ARENA_FAIL_IF_NO_ORDERS"), True),
    }

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
    symbol_closed_trade_count: dict[str, int] = field(default_factory=dict)
    symbol_realized_pnl_jpy: dict[str, float] = field(default_factory=dict)
    symbol_last_loss_exit_date: dict[str, date] = field(default_factory=dict)


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


def agent_label(agent: dict[str, Any]) -> str:
    return str(agent.get("name") or agent.get("agent_id") or "UNKNOWN")


def portfolio_rule_for_agent(portfolio_rules: dict[str, Any], agent: dict[str, Any]) -> dict[str, Any]:
    # jp_agent_portfolio_rules.yml is keyed by strategy agent_id such as
    # daily_striker / value_mispricing.  Keep fallbacks so older configs that
    # used display names like KYOU still work.
    candidates = [
        str(agent.get("agent_id") or ""),
        str(agent.get("name") or ""),
        str(agent.get("role") or ""),
    ]
    for key in candidates:
        if key and isinstance(portfolio_rules.get(key), dict):
            return portfolio_rules.get(key) or {}
    return {}


def strategy_rule_for_agent(agent_rules: dict[str, Any], agent: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        str(agent.get("agent_id") or ""),
        str(agent.get("name") or ""),
        str(agent.get("role") or ""),
    ]
    for key in candidates:
        if key and isinstance(agent_rules.get(key), dict):
            return agent_rules.get(key) or {}
    return {}


def new_agent_diag(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_id": str(agent.get("agent_id") or ""),
        "agent_name": agent_label(agent),
        "candidate_rows": 0,
        "evaluated_rows": 0,
        "entry_rule_pass": 0,
        "orders_created": 0,
        "buy_orders_filled": 0,
        "buy_orders_cancelled": 0,
        "sell_orders_created": 0,
        "sell_orders_filled": 0,
        "sell_orders_cancelled": 0,
        "final_open_positions": 0,
        "closed_trades": 0,
        "rejected_total": 0,
        "rejected_reasons": Counter(),
        "entry_rule_reject_reasons": Counter(),
    }


def diag_reject(diag: dict[str, Any], reason: str, entry_rule_reason: str | None = None, count: int = 1) -> None:
    if count <= 0:
        return
    diag["rejected_total"] += int(count)
    diag["rejected_reasons"][reason] += int(count)
    if entry_rule_reason:
        key = str(entry_rule_reason).strip()[:180] or "ENTRY_RULE_REJECTED"
        diag["entry_rule_reject_reasons"][key] += int(count)


def serialize_agent_diagnostics(agent_diagnostics: dict[str, dict[str, Any]], *, run_id: str, year: int, season: Any, generated_at: datetime) -> dict[str, Any]:
    agents_payload = []
    totals = Counter()
    for aid, d in agent_diagnostics.items():
        rejected_reasons = dict(sorted(d["rejected_reasons"].items(), key=lambda kv: (-kv[1], kv[0])))
        entry_reasons = dict(sorted(d["entry_rule_reject_reasons"].items(), key=lambda kv: (-kv[1], kv[0]))[:20])
        row = {
            "agent_id": aid,
            "agent_name": d.get("agent_name") or aid,
            "candidate_rows": int(d.get("candidate_rows", 0)),
            "evaluated_rows": int(d.get("evaluated_rows", 0)),
            "entry_rule_pass": int(d.get("entry_rule_pass", 0)),
            "orders_created": int(d.get("orders_created", 0)),
            "buy_orders_filled": int(d.get("buy_orders_filled", 0)),
            "buy_orders_cancelled": int(d.get("buy_orders_cancelled", 0)),
            "sell_orders_created": int(d.get("sell_orders_created", 0)),
            "sell_orders_filled": int(d.get("sell_orders_filled", 0)),
            "sell_orders_cancelled": int(d.get("sell_orders_cancelled", 0)),
            "closed_trades": int(d.get("closed_trades", 0)),
            "final_open_positions": int(d.get("final_open_positions", 0)),
            "rejected_total": int(d.get("rejected_total", 0)),
            "rejected_reasons": rejected_reasons,
            "entry_rule_reject_reasons_top20": entry_reasons,
        }
        for k, v in row.items():
            if isinstance(v, int):
                totals[k] += v
        agents_payload.append(row)
    agents_payload.sort(key=lambda x: x["agent_name"])
    return {
        "schema_version": "neon_tokyo_ai_arena_agent_rejection_diagnostics_v1",
        "generated_at": generated_at.replace(microsecond=0).isoformat() + "Z",
        "run_id": run_id,
        "year": year,
        "season": {
            "start_date": str(season.season_start),
            "end_date": str(season.last_trading_date or season.season_end),
            "trading_days": len(season.trading_dates),
        },
        "totals": dict(totals),
        "agents": agents_payload,
    }


def write_agent_diagnostics(out_dir: Path, payload: dict[str, Any]) -> dict[str, Path]:
    diag_dir = out_dir / "data" / "japan" / "ai-arena" / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    json_path = diag_dir / "agent-rejections-latest.json"
    md_path = diag_dir / "agent-rejections-latest.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    lines = [
        "# AI Arena Agent Rejection Diagnostics",
        "",
        f"Generated: {payload.get('generated_at')}",
        f"Run: `{payload.get('run_id')}`",
        f"Season: {payload.get('season', {}).get('start_date')} → {payload.get('season', {}).get('end_date')}",
        "",
        "| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for a in payload.get("agents", []):
        reasons = a.get("rejected_reasons") or {}
        top_reason = "-"
        if reasons:
            k, v = next(iter(reasons.items()))
            top_reason = f"{k} ({v})"
        lines.append(
            "| {agent_name} / `{agent_id}` | {candidate_rows} | {evaluated_rows} | {entry_rule_pass} | {orders_created} | {buy_orders_filled} | {buy_orders_cancelled} | {sell_orders_filled} | {closed_trades} | {final_open_positions} | {rejected_total} | {top_reason} |".format(
                top_reason=top_reason,
                **a,
            )
        )
    lines.extend(["", "## Reject reasons by agent", ""])
    for a in payload.get("agents", []):
        lines.append(f"### {a.get('agent_name')} / `{a.get('agent_id')}`")
        reasons = a.get("rejected_reasons") or {}
        if not reasons:
            lines.append("- None")
        else:
            for k, v in reasons.items():
                lines.append(f"- `{k}`: {v}")
        entry_reasons = a.get("entry_rule_reject_reasons_top20") or {}
        if entry_reasons:
            lines.append("- Entry rule details:")
            for k, v in entry_reasons.items():
                lines.append(f"  - {k}: {v}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"agent_rejection_diagnostics_json": json_path, "agent_rejection_diagnostics_md": md_path}


def _single_value(conn, sql: str, params: list[Any] | None = None) -> Any:
    row = conn.execute(sql, params or []).fetchone()
    return row[0] if row else None


def main() -> int:
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)
    cfg = resolve_runtime_config(conn)
    year = int(cfg["year"])
    start_date = str(cfg["start_date"])
    end_date = str(cfg["end_date"] or "")
    run_mode = str(cfg["run_mode"])
    run_id_env = str(cfg["run_id"] or "")
    reset_run = bool(cfg["reset_run"])
    promote_display = bool(cfg["promote_display_run"])
    force_finalize = bool(cfg["force_finalize_season"])
    rule_note = str(cfg["rule_note"] or "")
    fail_if_no_orders = bool(cfg["fail_if_no_orders"])

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

    season = build_season_dates(conn, year, start_date, end_date or None)
    if not season.trading_dates:
        raise SystemExit(f"No trading dates found in prices_daily for {start_date} - {end_date or year}")

    score_dates = int(_single_value(
        conn,
        """
        SELECT COUNT(DISTINCT date)
        FROM agent_scores_daily
        WHERE date BETWEEN ? AND ?
        """,
        [season.season_start, season.last_trading_date or season.season_end],
    ) or 0)
    candidate_score_rows = int(_single_value(
        conn,
        """
        SELECT COUNT(*)
        FROM agent_scores_daily
        WHERE date BETWEEN ? AND ? AND action IN ('Trade', 'Watch')
        """,
        [season.season_start, season.last_trading_date or season.season_end],
    ) or 0)
    if score_dates < 2:
        raise SystemExit(
            f"agent_scores_daily has only {score_dates} score date(s) in season range "
            f"{season.season_start} - {season.last_trading_date or season.season_end}. "
            "Run scripts/build_agent_scores_jp.py with AGENT_SCORE_MODE=range before season rebuild."
        )
    if candidate_score_rows <= 0:
        raise SystemExit(
            f"agent_scores_daily has no Trade/Watch candidate rows in season range {season.season_start} - "
            f"{season.last_trading_date or season.season_end}. Entry orders cannot be created."
        )

    run_id = run_id_env
    if not run_id:
        run_id = default_live_run_id(year) if run_mode == "live" else next_rebuild_run_id(conn, year)

    rules_hash = rules_hash_for_files([AGENTS_YML, STRATEGY_YML, PORTFOLIO_YML])
    run_cfg = RunConfig(
        run_id=run_id,
        year=year,
        run_type=run_mode,
        start_date=season.season_start,
        end_date=season.last_trading_date or season.season_end,
        initial_capital_jpy=initial_capital,
        share_lot_size=share_lot_size,
        strategy_rules_version=str(strategy_cfg.get("rules_version") or "unknown"),
        portfolio_rules_version=str(portfolio_cfg.get("rules_version") or "unknown"),
        rules_hash=rules_hash,
    )
    create_or_replace_run(conn, run_cfg, reset_run=reset_run, note=rule_note)
    try:
        conn.execute(
            "UPDATE arena_simulation_runs SET force_close_positions_at_year_end = ?, finalized_season = ? WHERE run_id = ?",
            [force_finalize, force_finalize, run_id],
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
    agent_diagnostics = {a["agent_id"]: new_agent_diag(a) for a in agents}
    default_max_new_entries_per_day = int(global_pf.get("default_max_new_entries_per_day", 3) or 3)

    def effective_allowed_actions_for_agent(agent: dict[str, Any]) -> set[str]:
        """Return actions that may become entry candidates for this agent.

        agent_scores_daily uses a global action threshold where only scores >=0.68
        become Trade.  HIZUMI/value_mispricing intentionally uses a lower entry
        score, so its Watch rows must be allowed into the entry-rule engine and
        then validated by the strategy-specific min_score/rank/value gates.
        """
        arule = strategy_rule_for_agent(agent_rules, agent)
        entry = (arule.get("entry") or {}) if isinstance(arule, dict) else {}
        allowed = entry.get("allowed_actions") or ["Trade"]
        return {str(x) for x in allowed if str(x).strip()} or {"Trade"}

    def filter_candidate_scores_for_agent(scores_df: pd.DataFrame, agent: dict[str, Any]) -> pd.DataFrame:
        if scores_df.empty:
            return pd.DataFrame()
        aid = str(agent.get("agent_id") or "")
        allowed_actions = effective_allowed_actions_for_agent(agent)
        adf = scores_df[scores_df["agent_id"].astype(str) == aid]
        if adf.empty:
            return adf
        return adf[adf["action"].astype(str).isin(allowed_actions)]

    def close_position(*, state: AgentState, pos: Position, signal_date: date, exit_date: date, exit_price_raw: float, code: str, text: str) -> None:
        exit_price = apply_bps(exit_price_raw, slippage_bps, "SELL")
        value = exit_price * pos.shares
        pnl = (exit_price - pos.entry_price) * pos.shares
        ret = (exit_price / pos.entry_price - 1.0) * 100.0 if pos.entry_price else 0.0
        state.cash_jpy += value
        state.realized_pnl_jpy += pnl
        state.symbol_closed_trade_count[pos.ticker] = state.symbol_closed_trade_count.get(pos.ticker, 0) + 1
        state.symbol_realized_pnl_jpy[pos.ticker] = state.symbol_realized_pnl_jpy.get(pos.ticker, 0.0) + pnl
        if pnl < 0:
            state.symbol_last_loss_exit_date[pos.ticker] = exit_date
        state.positions.pop(pos.ticker, None)
        agent_diagnostics[state.agent_id]["closed_trades"] += 1
        agent_diagnostics[state.agent_id]["sell_orders_filled"] += 1
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


    def reentry_block_reason(*, state: AgentState, ticker: str, entry_rule: dict[str, Any], signal_date: date) -> str | None:
        cooldown = int(entry_rule.get("cooldown_after_loss_days", 0) or 0)
        last_loss = state.symbol_last_loss_exit_date.get(ticker)
        if cooldown > 0 and last_loss is not None and (signal_date - last_loss).days < cooldown:
            return "COOLDOWN_AFTER_LOSS"

        max_closed = int(entry_rule.get("max_closed_trades_per_symbol_per_season", 0) or 0)
        if max_closed > 0 and state.symbol_closed_trade_count.get(ticker, 0) >= max_closed:
            return "MAX_SYMBOL_CLOSED_TRADES"

        loss_trade_limit = int(entry_rule.get("reject_if_symbol_realized_pnl_negative_after_trades", 0) or 0)
        if (
            loss_trade_limit > 0
            and state.symbol_closed_trade_count.get(ticker, 0) >= loss_trade_limit
            and state.symbol_realized_pnl_jpy.get(ticker, 0.0) < 0
        ):
            return "SYMBOL_REALIZED_PNL_NEGATIVE"

        return None

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
                if order["side"] == "BUY":
                    agent_diagnostics[order["agent_id"]]["buy_orders_cancelled"] += 1
                    diag_reject(agent_diagnostics[order["agent_id"]], "CANCELLED_NO_EXECUTION_PRICE")
                elif order["side"] == "SELL":
                    agent_diagnostics[order["agent_id"]]["sell_orders_cancelled"] += 1
                orders.append(order)
                continue
            if order["side"] == "BUY":
                exec_px = apply_bps(px, slippage_bps, "BUY")
                cost = exec_px * int(order["shares"])
                if cost > state.cash_jpy or order["ticker"] in state.positions:
                    order.update({"order_status": "CANCELLED", "execution_price": exec_px, "order_value_jpy": 0.0, "commission_jpy": 0.0, "slippage_jpy": (exec_px - px) * int(order["shares"])})
                    agent_diagnostics[order["agent_id"]]["buy_orders_cancelled"] += 1
                    diag_reject(agent_diagnostics[order["agent_id"]], "CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION")
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
                agent_diagnostics[order["agent_id"]]["buy_orders_filled"] += 1
                orders.append(order)
            elif order["side"] == "SELL":
                pos = state.positions.get(order["ticker"])
                if not pos:
                    order.update({"order_status": "CANCELLED", "execution_price": px, "order_value_jpy": 0.0, "commission_jpy": 0.0, "slippage_jpy": 0.0})
                    agent_diagnostics[order["agent_id"]]["sell_orders_cancelled"] += 1
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
            rule = strategy_rule_for_agent(agent_rules, agent)
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
                    agent_diagnostics[aid]["sell_orders_created"] += 1
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
                "SELECT * FROM agent_scores_daily WHERE date = ? AND action IN ('Trade', 'Watch') ORDER BY agent_id, rank",
                [d],
            ).df()
            for agent in agents:
                aid = agent["agent_id"]
                state = states[aid]
                arule = strategy_rule_for_agent(agent_rules, agent)
                prule = portfolio_rule_for_agent(portfolio_rules, agent)
                max_positions = int(prule.get("max_positions", 8) or 8)
                max_new = int(prule.get("max_new_entries_per_day", default_max_new_entries_per_day) or default_max_new_entries_per_day)
                diag = agent_diagnostics[aid]
                adf = filter_candidate_scores_for_agent(scores_df, agent)
                candidate_count = int(len(adf))
                diag["candidate_rows"] += candidate_count
                if candidate_count <= 0:
                    continue
                if len(state.positions) >= max_positions:
                    diag_reject(diag, "MAX_POSITIONS_FULL", count=candidate_count)
                    continue
                new_count = 0
                for idx, sr in enumerate(adf.itertuples(index=False)):
                    remaining = candidate_count - idx
                    if new_count >= max_new:
                        diag_reject(diag, "MAX_NEW_ENTRIES_PER_DAY", count=remaining)
                        break
                    if len(state.positions) >= max_positions:
                        diag_reject(diag, "MAX_POSITIONS_FULL", count=remaining)
                        break
                    row = sr._asdict() if hasattr(sr, "_asdict") else dict(sr)
                    diag["evaluated_rows"] += 1
                    ticker = str(row["ticker"])
                    if ticker in state.positions:
                        diag_reject(diag, "ALREADY_OPEN_POSITION")
                        continue
                    if any(o["agent_id"] == aid and o["ticker"] == ticker and o["side"] == "BUY" for o in pending_orders):
                        diag_reject(diag, "PENDING_BUY_EXISTS")
                        continue
                    entry_rule = (arule.get("entry") or {})
                    block_reason = reentry_block_reason(state=state, ticker=ticker, entry_rule=entry_rule, signal_date=d)
                    if block_reason:
                        diag_reject(diag, block_reason)
                        continue
                    feat = feature_for_ticker(feature_map, ticker)
                    ok, reason = passes_entry_rule(score_row=row, feature_row=feat, agent_rule=arule, trading_dates=season.trading_dates, signal_date=d)
                    if not ok:
                        diag_reject(diag, "ENTRY_RULE_REJECTED", entry_rule_reason=reason)
                        continue
                    diag["entry_rule_pass"] += 1
                    next_price = choose_execution_price(fetch_price_row(conn, ticker, next_d), "open")
                    if next_price is None:
                        diag_reject(diag, "NO_NEXT_OPEN_PRICE")
                        continue
                    current_mv = 0.0
                    for p in state.positions.values():
                        pr = fetch_price_row(conn, p.ticker, d)
                        cp = choose_execution_price(pr, "close") or p.entry_price
                        current_mv += cp * p.shares
                    size_multiplier = entry_position_size_multiplier(arule, feat)
                    if size_multiplier <= 0:
                        diag_reject(diag, "REGIME_POSITION_SIZE_ZERO")
                        continue
                    base_target_pct = float(prule.get("target_position_pct", 0.10) or 0.10)
                    base_max_pct = float(prule.get("max_position_pct", 0.15) or 0.15)
                    shares = compute_buy_shares(
                        equity_jpy=state.cash_jpy + current_mv,
                        cash_jpy=state.cash_jpy,
                        execution_price=apply_bps(next_price, slippage_bps, "BUY"),
                        score=float(row.get("normalized_score") or 0.0),
                        min_score=float((arule.get("entry") or {}).get("min_score", 0.0) or 0.0),
                        target_position_pct=base_target_pct * size_multiplier,
                        max_position_pct=base_max_pct * size_multiplier,
                        max_total_exposure_pct=float(prule.get("max_total_exposure_pct", 0.90) or 0.90),
                        current_market_value_jpy=current_mv,
                        commission_bps=commission_bps,
                        share_lot_size=share_lot_size,
                    )
                    if shares <= 0:
                        diag_reject(diag, "ZERO_SHARES_AFTER_SIZING")
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
                        "reason_text": f"{agent_label(agent)} entry: {reason}; regime={market_regime_state(feat)}; size_multiplier={size_multiplier:.2f}",
                        "created_at": now,
                    })
                    diag["orders_created"] += 1
                    new_count += 1
        else:
            # Last trading day has no next-open execution. Count Trade rows as rejected for diagnostics.
            scores_df = conn.execute(
                "SELECT * FROM agent_scores_daily WHERE date = ? AND action IN ('Trade', 'Watch') ORDER BY agent_id, rank",
                [d],
            ).df()
            for agent in agents:
                aid = str(agent.get("agent_id") or "")
                adf = filter_candidate_scores_for_agent(scores_df, agent)
                count = int(len(adf))
                if aid in agent_diagnostics and count > 0:
                    agent_diagnostics[aid]["candidate_rows"] += count
                    diag_reject(agent_diagnostics[aid], "NO_NEXT_TRADING_DATE", count=count)

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
    should_finalize = bool(force_finalize)
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

    for aid, state in states.items():
        agent_diagnostics[aid]["final_open_positions"] = len(state.positions)

    diagnostics_payload = serialize_agent_diagnostics(
        agent_diagnostics,
        run_id=run_id,
        year=year,
        season=season,
        generated_at=now,
    )
    diagnostics_outputs = write_agent_diagnostics(OUT_DIR, diagnostics_payload)

    persisted_counts = {
        "arena_orders": conn.execute("SELECT COUNT(*) FROM arena_orders WHERE run_id = ?", [run_id]).fetchone()[0],
        "arena_trades": conn.execute("SELECT COUNT(*) FROM arena_trades WHERE run_id = ?", [run_id]).fetchone()[0],
        "arena_open_positions": conn.execute("SELECT COUNT(*) FROM arena_open_positions WHERE run_id = ?", [run_id]).fetchone()[0],
        "arena_equity_curve": conn.execute("SELECT COUNT(*) FROM arena_equity_curve WHERE run_id = ?", [run_id]).fetchone()[0],
    }
    if persisted_counts["arena_equity_curve"] <= 0:
        raise RuntimeError(f"Arena run {run_id} did not persist equity curve rows to DuckDB: {persisted_counts}")
    if fail_if_no_orders and persisted_counts["arena_orders"] <= 0:
        raise RuntimeError(
            f"Arena run {run_id} produced zero orders: {persisted_counts}. "
            "This usually means agent_scores_daily was not built in range mode, or entry rules are too strict."
        )
    if fail_if_no_orders and (persisted_counts["arena_open_positions"] + persisted_counts["arena_trades"] <= 0):
        raise RuntimeError(
            f"Arena run {run_id} produced neither open positions nor closed trades: {persisted_counts}."
        )

    ranking_diag = rebuild_rankings(conn, run_id=run_id, year=year, initial_capital_jpy=initial_capital)
    if promote_display:
        promote_display_run(conn, year=year, run_id=run_id, note=rule_note or "Promoted by season rebuild workflow")

    outputs = export_arena_payloads(conn, out_dir=OUT_DIR, run_id=run_id, year=year, agents=load_agents_for_public())
    outputs.update(diagnostics_outputs)
    print(f"runtime_config={cfg}")
    print(f"run_id={run_id}")
    print(f"agent_score_dates={score_dates} trade_score_rows={trade_score_rows}")
    print(f"trading_dates={len(season.trading_dates)}")
    print(f"orders={len(orders)} trades={len(trades)} equity_rows={len(equity_rows)} open_positions={len(open_rows)} finalized={force_finalize}")
    print(f"persisted_counts={persisted_counts}")
    print(f"ranking_diag={ranking_diag}")
    for key, path in outputs.items():
        print(f"Wrote {key}: {safe_rel(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
