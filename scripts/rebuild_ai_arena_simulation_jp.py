from __future__ import annotations

"""
Rebuild Neon Tokyo AI Arena agent simulations.

This is the core engine for the AI Arena product line. It is deliberately
independent from the existing Daily / Weekly simulation pages so that AI Arena
can evolve, or eventually replace those pages, without coupling page behavior.

What this script does
---------------------
1. Reads existing Daily signal snapshots and JP price bars.
2. Reads Agent definitions from data/ai_arena_agents_jp.yml.
3. Runs a deterministic trading simulation for each Agent.
4. Writes Position / Ranking / Simulation JSON under site/data/japan/ai-arena/.

What this script does NOT do
----------------------------
- It does not call OpenAI.
- It does not fetch prices.
- It does not mutate existing Daily / Weekly / Backtest outputs.
- It does not use LLMs for trading decisions.

Execution model
---------------
Signal date close -> next trading day open entry -> close valuation.
Open positions are valued at every trading day close. Stops and take-profits are
close-based in this first AI Arena simulation engine. That means a stop of -5%
can realize worse than -5% if the close gaps below the stop threshold.

Environment variables
---------------------
OUT_DIR                          default: site
AI_ARENA_START_DATE              YYYY-MM-DD, optional
AI_ARENA_END_DATE                YYYY-MM-DD, optional
AI_ARENA_LOOKBACK_DAYS           default from YAML simulation.default_lookback_days
AI_ARENA_AGENTS_YAML             default: data/ai_arena_agents_jp.yml
AI_ARENA_PRICES_JSON             default: site/data/prices-jp/latest.json
AI_ARENA_DAILY_DIR               default: site/data/daily-jp
AI_ARENA_WEEKLY_JSON             default: site/data/japan/weekly/latest.json
"""

import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()

AGENTS_YAML = Path(os.getenv("AI_ARENA_AGENTS_YAML", str(ROOT / "data/ai_arena_agents_jp.yml")))
PRICES_JSON = Path(os.getenv("AI_ARENA_PRICES_JSON", str(OUT_DIR / "data/prices-jp/latest.json")))
DAILY_DIR = Path(os.getenv("AI_ARENA_DAILY_DIR", str(OUT_DIR / "data/daily-jp")))
WEEKLY_JSON = Path(os.getenv("AI_ARENA_WEEKLY_JSON", str(OUT_DIR / "data/japan/weekly/latest.json")))

SIM_OUT = OUT_DIR / "data/japan/ai-arena/simulation/latest.json"
POSITIONS_OUT = OUT_DIR / "data/japan/ai-arena/positions/latest.json"
RANKING_OUT = OUT_DIR / "data/japan/ai-arena/ranking/latest.json"

JST = timezone(timedelta(hours=9))


def now_jst() -> datetime:
    return datetime.now(JST)


def iso_jst(dt: datetime) -> str:
    return dt.astimezone(JST).isoformat(timespec="seconds")


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        print(f"WARN missing JSON: {path}")
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WARN failed JSON {path}: {exc}")
        return fallback


def read_yaml(path: Path, fallback: Any) -> Any:
    if not path.exists():
        raise SystemExit(f"Missing AI Arena config: {path}")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or fallback
    except Exception as exc:
        raise SystemExit(f"Failed to parse YAML {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        rel = path.relative_to(ROOT)
    except Exception:
        rel = path
    print(f"Wrote {rel}")


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def norm_pct(value: Any, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.5
    return clamp((as_float(value) - lo) / (hi - lo))


def norm_positive(value: Any, cap: float) -> float:
    return clamp(max(0.0, as_float(value)) / cap) if cap > 0 else 0.0


def parse_date(s: Any) -> str | None:
    if not s:
        return None
    text = str(s)[:10]
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return text
    except Exception:
        return None


def pct(a: float, b: float) -> float:
    return ((a / b) - 1.0) * 100.0 if b else 0.0


def score_norm(item: dict[str, Any]) -> float:
    pts = as_float(item.get("score_pts"), as_float(item.get("score"), 0.0))
    return clamp(pts / 1000.0 if pts > 150 else pts / 100.0)


def liquidity_score(item: dict[str, Any]) -> float:
    if item.get("liquidity_score_0_1") is not None:
        return clamp(as_float(item.get("liquidity_score_0_1")))
    band = str(item.get("liquidity_band") or "").lower()
    if "high" in band:
        return 1.0
    if "tradable" in band:
        return 0.75
    if "thin" in band or "low" in band:
        return 0.25
    # fallback: traded value is unavailable in Daily, so use RVOL lightly.
    return 0.55


def extension_risk(item: dict[str, Any]) -> float:
    if item.get("extension_risk_0_1") is not None:
        return clamp(as_float(item.get("extension_risk_0_1")))
    ext = abs(as_float(item.get("extension_sma20_pct"), 0.0))
    return clamp(ext / 30.0)


def extension_control(item: dict[str, Any]) -> float:
    return 1.0 - extension_risk(item)


def item_symbol(item: dict[str, Any]) -> str:
    return str(item.get("symbol") or "").strip()


def daily_date(snapshot: dict[str, Any]) -> str | None:
    # Prefer actual item latest_date/as_of; generated_at can be after market close
    # but the signal belongs to the price date.
    for key in ("items", "all_items"):
        vals = snapshot.get(key)
        if isinstance(vals, list) and vals:
            for it in vals:
                if isinstance(it, dict):
                    d = parse_date(it.get("latest_date") or it.get("as_of"))
                    if d:
                        return d
    return parse_date(snapshot.get("date") or snapshot.get("generated_at"))


def collect_daily_snapshots() -> list[tuple[str, dict[str, Any]]]:
    """Collect Daily signal snapshots.

    Important operational note:
    ---------------------------
    The current repo sometimes has only ``site/data/daily-jp/latest.json``
    and a small number of historical dated snapshots.  The first V2 engine
    intentionally skipped latest.json to avoid duplicated dates. That was too
    strict: if only one dated signal snapshot exists, entries are scheduled for
    the next trading day but never executed because the default simulation end
    date was the same signal date.

    This function now reads dated files *and* latest.json.  Duplicates are
    deduplicated by actual signal date and latest.json wins only when it is the
    freshest copy for that same date.
    """
    out: list[tuple[str, dict[str, Any], str]] = []
    if not DAILY_DIR.exists():
        return []

    for path in sorted(DAILY_DIR.glob("*.json")):
        if path.name == "manifest.json":
            continue
        data = read_json(path, {})
        if not isinstance(data, dict):
            continue
        d = daily_date(data) or (parse_date(path.stem) if path.name != "latest.json" else None)
        if d:
            out.append((d, data, path.name))

    by_date: dict[str, tuple[dict[str, Any], str]] = {}
    for d, data, source_name in out:
        # Dated files usually win; latest.json may be the only available source
        # or may contain a fresher rebuilt copy for the same signal date.
        if d not in by_date or source_name == "latest.json":
            by_date[d] = (data, source_name)
    return sorted((d, data) for d, (data, _source) in by_date.items())


def snapshot_items(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    raw: list[dict[str, Any]] = []
    for key in ("items", "all_items"):
        vals = snapshot.get(key)
        if isinstance(vals, list):
            raw.extend([x for x in vals if isinstance(x, dict) and item_symbol(x)])
    seen = set()
    out = []
    for it in raw:
        sym = item_symbol(it)
        if sym and sym not in seen:
            seen.add(sym)
            out.append(dict(it))
    return out


def load_prices() -> dict[str, dict[str, Any]]:
    data = read_json(PRICES_JSON, {})
    out: dict[str, dict[str, Any]] = {}
    for item in data.get("equities") or data.get("items") or []:
        if not isinstance(item, dict) or not item_symbol(item):
            continue
        bars = [b for b in item.get("bars", []) if isinstance(b, dict) and parse_date(b.get("date"))]
        bars = sorted(bars, key=lambda b: b["date"])
        if not bars:
            continue
        out[item_symbol(item)] = {**item, "bars": bars, "bars_by_date": {b["date"]: b for b in bars}}
    return out


def weekly_features() -> dict[str, dict[str, Any]]:
    data = read_json(WEEKLY_JSON, {})
    out: dict[str, dict[str, Any]] = {}
    for key in ("items", "all_items"):
        for item in data.get(key) or []:
            if isinstance(item, dict) and item_symbol(item):
                out.setdefault(item_symbol(item), item)
    return out


def trading_calendar(prices: dict[str, dict[str, Any]]) -> list[str]:
    dates = set()
    for item in prices.values():
        for b in item.get("bars", []):
            dates.add(b["date"])
    return sorted(dates)


def next_trading_date(calendar: list[str], date: str) -> str | None:
    for d in calendar:
        if d > date:
            return d
    return None


def bar_on_or_before(item: dict[str, Any], date: str) -> dict[str, Any] | None:
    bars = item.get("bars", [])
    last = None
    for b in bars:
        if b["date"] <= date:
            last = b
        else:
            break
    return last


def theme_heat_from_snapshot(items: list[dict[str, Any]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for it in items:
        theme = str(it.get("theme") or "Other")
        val = 0.45 * score_norm(it) + 0.25 * norm_pct(it.get("return_5d_pct"), -8, 12) + 0.2 * norm_positive(it.get("volume_ratio_20d"), 3.5) + 0.1 * liquidity_score(it)
        grouped[theme].append(val)
    return {k: clamp(sum(v) / len(v)) for k, v in grouped.items() if v}


def feature_value(name: str, item: dict[str, Any], weekly: dict[str, Any] | None, theme_heat: dict[str, float]) -> float:
    theme = str(item.get("theme") or "Other")
    if name == "score_norm":
        return score_norm(item)
    if name == "weekly_score_norm":
        if weekly:
            pts = as_float(weekly.get("score_pts"), as_float(weekly.get("score"), 0.0))
            return clamp(pts / 1000.0 if pts > 150 else pts / 100.0)
        return 0.0
    if name == "return_1d_norm":
        return norm_pct(item.get("return_1d_pct"), -8, 8)
    if name == "return_3d_norm":
        return norm_pct(item.get("return_3d_pct"), -10, 12)
    if name == "return_5d_norm":
        return norm_pct(item.get("return_5d_pct"), -12, 18)
    if name == "return_20d_norm":
        return norm_pct(item.get("return_20d_pct"), -20, 45)
    if name == "volume_ratio_norm":
        return norm_positive(item.get("volume_ratio_20d"), 3.0)
    if name == "liquidity_score":
        return liquidity_score(item)
    if name == "extension_control":
        return extension_control(item)
    if name == "theme_heat":
        return theme_heat.get(theme, 0.0)
    if name == "discovery_bonus":
        return 1.0 if str(item.get("bucket") or "").lower() == "discovery" else 0.0
    if name == "short_term_pullback":
        # Highest score when the short-term tape is soft but not collapsing.
        r5 = as_float(item.get("return_5d_pct"), 0.0)
        if r5 < -18:
            return 0.0
        if r5 <= 0:
            return clamp((18 + r5) / 18.0)
        return clamp(1.0 - r5 / 12.0)
    return 0.0


def profile_score(item: dict[str, Any], profile: dict[str, Any], weekly: dict[str, Any] | None, heat: dict[str, float]) -> float:
    universe = profile.get("universe") or {}
    buckets = set(universe.get("buckets") or [])
    if buckets and str(item.get("bucket") or "") not in buckets:
        return -999.0
    allow_triage = set(universe.get("allow_triage") or [])
    triage = str(item.get("triage") or "")
    if allow_triage and triage and triage not in allow_triage:
        return -999.0
    min_liq = as_float(universe.get("min_liquidity_score"), 0.0)
    if liquidity_score(item) < min_liq:
        return -999.0

    total = 0.0
    for key, weight in (profile.get("weights") or {}).items():
        total += as_float(weight) * feature_value(key, item, weekly, heat)

    penalties = profile.get("penalties") or {}
    if triage.lower() == "ignore":
        total += as_float(penalties.get("ignore_triage"), 0.0)
    if extension_risk(item) > 0.72:
        total += as_float(penalties.get("high_extension"), 0.0)
    if as_float(item.get("return_1d_pct"), 0.0) < -3:
        total += as_float(penalties.get("weak_1d"), 0.0)
    if as_float(item.get("return_5d_pct"), 0.0) < 0:
        total += as_float(penalties.get("negative_5d"), 0.0)
    if as_float(item.get("return_5d_pct"), 0.0) < -12:
        total += as_float(penalties.get("deep_5d_drop"), 0.0)
    if liquidity_score(item) < 0.45:
        total += as_float(penalties.get("weak_liquidity"), as_float(penalties.get("illiquid"), 0.0))
    if as_float(item.get("return_20d_pct"), 0.0) < -15:
        total += as_float(penalties.get("collapse_20d"), 0.0)
    return total


@dataclass
class Position:
    symbol: str
    name: str
    theme: str
    entry_date: str
    entry_price: float
    shares: int
    agent_score: float
    entry_reason: str
    max_holding_days: int
    stop_loss_pct: float
    take_profit_pct: float
    current_price: float = 0.0
    current_date: str = ""

    def market_value(self) -> float:
        return self.shares * (self.current_price or self.entry_price)

    def unrealized_pct(self) -> float:
        return pct(self.current_price or self.entry_price, self.entry_price)

    def holding_days(self, calendar: list[str], current_date: str) -> int:
        try:
            return max(0, calendar.index(current_date) - calendar.index(self.entry_date) + 1)
        except ValueError:
            return 0


@dataclass
class AgentState:
    agent: dict[str, Any]
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    closed_trades: list[dict[str, Any]] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    daily_actions: list[dict[str, Any]] = field(default_factory=list)


def run_simulation(config: dict[str, Any], prices: dict[str, dict[str, Any]], daily_snaps: list[tuple[str, dict[str, Any]]], weekly_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    arena_cfg = config.get("arena") or {}
    sim_cfg = config.get("simulation") or {}
    profiles = config.get("screening_profiles") or {}
    agents = [a for a in config.get("agents", []) if a.get("enabled", True)]
    if not agents:
        raise SystemExit("No enabled AI Arena agents in YAML")

    calendar = trading_calendar(prices)
    if not calendar:
        raise SystemExit("No trading calendar from prices JSON")

    # Default simulation end date must be the latest available price date, not
    # the latest signal date.  Entries are generated after the signal close and
    # executed on the next trading day; using the signal date as end_date causes
    # valid orders to be scheduled but never executed.
    end_date = os.getenv("AI_ARENA_END_DATE") or calendar[-1]
    lookback = int(os.getenv("AI_ARENA_LOOKBACK_DAYS") or sim_cfg.get("default_lookback_days") or 90)
    start_date = os.getenv("AI_ARENA_START_DATE")
    if not start_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_dt - timedelta(days=lookback)).strftime("%Y-%m-%d")

    daily_by_date = {d: snap for d, snap in daily_snaps if start_date <= d <= end_date}
    sim_dates = [d for d in calendar if start_date <= d <= end_date]

    print(
        "AI Arena simulation input:",
        f"daily_snapshots={len(daily_by_date)}",
        f"price_days={len(sim_dates)}",
        f"start_date={start_date}",
        f"end_date={end_date}",
    )

    initial_capital = as_float(arena_cfg.get("initial_capital_jpy"), 1_000_000)
    lot_size = int(arena_cfg.get("lot_size") or 100)
    max_orders_per_day = int(sim_cfg.get("max_orders_per_agent_per_day") or 2)
    allow_reentry = bool(sim_cfg.get("allow_reentry_same_symbol", False))

    states = {a["id"]: AgentState(agent=a, cash=initial_capital) for a in agents}
    pending_orders: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scheduled_orders_count = 0
    executed_entries_count = 0
    closed_exits_count = 0

    for current_date in sim_dates:
        # 1) Execute pending entries at today's open.
        for order in pending_orders.pop(current_date, []):
            state = states[order["agent_id"]]
            sym = order["symbol"]
            if sym in state.positions:
                continue
            pitem = prices.get(sym)
            if not pitem:
                continue
            bar = pitem.get("bars_by_date", {}).get(current_date)
            if not bar:
                continue
            entry_price = as_float(bar.get("open"), as_float(bar.get("close"), 0.0))
            if entry_price <= 0:
                continue
            policy = state.agent.get("trading_policy") or {}
            one_lot_cost = entry_price * lot_size
            allocation = state.cash * as_float(policy.get("position_size_pct"), 0.15)
            shares = int(allocation // one_lot_cost) * lot_size

            # Japan equities generally trade in 100-share lots.  With a game
            # account size that is intentionally modest, high-priced liquid
            # leaders such as DISCO can otherwise never be traded.  When the
            # policy allows it, buy the minimum lot if cash can afford it even
            # if the position-size budget is smaller than one lot.  This keeps
            # the Arena active while preserving 100-share execution.
            if shares <= 0 and bool(policy.get("allow_minimum_lot_entry", True)) and state.cash >= one_lot_cost:
                shares = lot_size

            if shares <= 0:
                state.daily_actions.append({
                    "date": current_date,
                    "action": "skip_entry",
                    "symbol": sym,
                    "price": round(entry_price, 4),
                    "reason": "insufficient_cash_for_minimum_lot",
                })
                continue
            cost = shares * entry_price
            if cost > state.cash:
                state.daily_actions.append({
                    "date": current_date,
                    "action": "skip_entry",
                    "symbol": sym,
                    "price": round(entry_price, 4),
                    "reason": "insufficient_cash",
                })
                continue
            state.cash -= cost
            state.positions[sym] = Position(
                symbol=sym,
                name=order.get("name") or sym,
                theme=order.get("theme") or "Other",
                entry_date=current_date,
                entry_price=entry_price,
                shares=shares,
                agent_score=as_float(order.get("agent_score"), 0.0),
                entry_reason=order.get("entry_reason") or "Agent screening entry",
                max_holding_days=int(policy.get("max_holding_days") or 5),
                stop_loss_pct=as_float(policy.get("stop_loss_pct"), -5.0),
                take_profit_pct=as_float(policy.get("take_profit_pct"), 10.0),
            )
            state.daily_actions.append({"date": current_date, "action": "entry", "symbol": sym, "price": round(entry_price, 4), "shares": shares, "reason": order.get("entry_reason")})
            executed_entries_count += 1

        # 2) Mark positions and close exits at today's close.
        for state in states.values():
            exits: list[tuple[str, str]] = []
            for sym, pos in state.positions.items():
                pitem = prices.get(sym)
                bar = pitem.get("bars_by_date", {}).get(current_date) if pitem else None
                if not bar:
                    bar = bar_on_or_before(pitem, current_date) if pitem else None
                if not bar:
                    continue
                close = as_float(bar.get("close"), pos.entry_price)
                pos.current_price = close
                pos.current_date = current_date
                ret = pos.unrealized_pct()
                held = pos.holding_days(calendar, current_date)
                if ret <= pos.stop_loss_pct:
                    exits.append((sym, "stop_loss"))
                elif ret >= pos.take_profit_pct:
                    exits.append((sym, "take_profit"))
                elif held >= pos.max_holding_days:
                    exits.append((sym, "max_holding"))
            for sym, reason in exits:
                pos = state.positions.pop(sym)
                exit_price = pos.current_price or pos.entry_price
                proceeds = pos.shares * exit_price
                state.cash += proceeds
                trade = {
                    "agent_id": state.agent["id"],
                    "symbol": pos.symbol,
                    "name": pos.name,
                    "theme": pos.theme,
                    "entry_date": pos.entry_date,
                    "exit_date": current_date,
                    "entry_price": round(pos.entry_price, 4),
                    "exit_price": round(exit_price, 4),
                    "shares": pos.shares,
                    "return_pct": round(pos.unrealized_pct(), 4),
                    "pnl_jpy": round((exit_price - pos.entry_price) * pos.shares, 0),
                    "holding_days": pos.holding_days(calendar, current_date),
                    "exit_reason": reason,
                    "entry_reason": pos.entry_reason,
                }
                state.closed_trades.append(trade)
                state.daily_actions.append({"date": current_date, "action": "exit", "symbol": sym, "price": round(exit_price, 4), "shares": pos.shares, "reason": reason})
                closed_exits_count += 1

        # 3) Record end-of-day equity.
        for state in states.values():
            market_value = sum(p.market_value() for p in state.positions.values())
            equity = state.cash + market_value
            state.equity_curve.append({
                "date": current_date,
                "cash_jpy": round(state.cash, 0),
                "market_value_jpy": round(market_value, 0),
                "portfolio_equity_jpy": round(equity, 0),
                "return_pct": round(pct(equity, initial_capital), 4),
                "open_positions": len(state.positions),
            })

        # 4) After close, read today's signal and schedule next-day entries.
        snap = daily_by_date.get(current_date)
        if not snap:
            continue
        items = snapshot_items(snap)
        heat = theme_heat_from_snapshot(items)
        next_date = next_trading_date(calendar, current_date)
        if not next_date:
            continue
        for state in states.values():
            agent = state.agent
            policy = agent.get("trading_policy") or {}
            if len(state.positions) >= int(policy.get("max_positions") or 5):
                continue
            profile_name = agent.get("screening_profile")
            profile = profiles.get(profile_name) or {}
            scored = []
            for it in items:
                sym = item_symbol(it)
                if not sym or sym not in prices:
                    continue
                if not allow_reentry and sym in state.positions:
                    continue
                wk = weekly_map.get(sym)
                s = profile_score(it, profile, wk, heat)
                if s < as_float(policy.get("min_agent_score"), 0.5):
                    continue
                scored.append((s, it))
            scored.sort(key=lambda x: x[0], reverse=True)
            slots = max(0, int(policy.get("max_positions") or 5) - len(state.positions))
            for s, it in scored[: min(slots, max_orders_per_day)]:
                pending_orders[next_date].append({
                    "agent_id": agent["id"],
                    "symbol": item_symbol(it),
                    "name": it.get("name") or item_symbol(it),
                    "theme": it.get("theme") or "Other",
                    "agent_score": round(s, 4),
                    "entry_reason": f"{agent.get('name')} {profile_name} score {s:.2f}; {it.get('reason') or it.get('archetype') or 'screen match'}",
                })
                scheduled_orders_count += 1

    # Final snapshot structures.
    agents_out = []
    ranking_agents = []
    latest_date = sim_dates[-1] if sim_dates else end_date
    season = latest_date[:7]

    for state in states.values():
        last_equity = state.equity_curve[-1]["portfolio_equity_jpy"] if state.equity_curve else initial_capital
        returns = [x["return_pct"] for x in state.equity_curve]
        peak = -1e18
        max_dd = 0.0
        for row in state.equity_curve:
            eq = row["portfolio_equity_jpy"]
            peak = max(peak, eq)
            dd = pct(eq, peak) if peak > 0 else 0.0
            max_dd = min(max_dd, dd)
        wins = [t for t in state.closed_trades if t["return_pct"] > 0]
        losses = [t for t in state.closed_trades if t["return_pct"] <= 0]
        open_positions = []
        for p in state.positions.values():
            open_positions.append({
                "agent_id": state.agent["id"],
                "symbol": p.symbol,
                "name": p.name,
                "theme": p.theme,
                "entry_date": p.entry_date,
                "entry_price": round(p.entry_price, 4),
                "current_date": p.current_date or latest_date,
                "current_price": round(p.current_price or p.entry_price, 4),
                "shares": p.shares,
                "market_value_jpy": round(p.market_value(), 0),
                "unrealized_return_pct": round(p.unrealized_pct(), 4),
                "unrealized_pnl_jpy": round(((p.current_price or p.entry_price) - p.entry_price) * p.shares, 0),
                "holding_days": p.holding_days(calendar, p.current_date or latest_date),
                "agent_score": round(p.agent_score, 4),
                "entry_reason": p.entry_reason,
            })
        summary = {
            "agent_id": state.agent["id"],
            "name": state.agent.get("name"),
            "class": state.agent.get("class"),
            "screening_profile": state.agent.get("screening_profile"),
            "initial_capital_jpy": round(initial_capital, 0),
            "cash_jpy": round(state.cash, 0),
            "market_value_jpy": round(sum(p.market_value() for p in state.positions.values()), 0),
            "portfolio_equity_jpy": round(last_equity, 0),
            "return_pct": round(pct(last_equity, initial_capital), 4),
            "max_drawdown_pct": round(max_dd, 4),
            "closed_trades": len(state.closed_trades),
            "win_rate_pct": round(len(wins) / len(state.closed_trades) * 100, 2) if state.closed_trades else None,
            "open_positions": len(open_positions),
            # UI identity fields are copied from YAML so Ranking can use
            # real PNG avatars when present and fall back to CSS sprites.
            "ui_tone": state.agent.get("ui_tone"),
            "avatar_style": state.agent.get("avatar_style"),
            "avatar_image": state.agent.get("avatar_image"),
        }
        agents_out.append({
            "agent_id": state.agent["id"],
            "name": state.agent.get("name"),
            "class": state.agent.get("class"),
            "ui_tone": state.agent.get("ui_tone"),
            "avatar_style": state.agent.get("avatar_style"),
            "avatar_image": state.agent.get("avatar_image"),
            "personality": state.agent.get("personality"),
            "philosophy": state.agent.get("philosophy"),
            "summary": summary,
            "open_positions": open_positions,
            "closed_trades": state.closed_trades[-50:],
            "equity_curve": state.equity_curve,
            "recent_actions": state.daily_actions[-30:],
        })
        ranking_agents.append(summary)

    ranking_agents.sort(key=lambda a: a["return_pct"], reverse=True)
    for i, row in enumerate(ranking_agents, 1):
        row["rank"] = i

    print(
        "AI Arena simulation result:",
        f"scheduled_orders={scheduled_orders_count}",
        f"executed_entries={executed_entries_count}",
        f"closed_exits={closed_exits_count}",
        f"open_positions={sum(len(s.positions) for s in states.values())}",
    )

    payload = {
        "schema_version": "neon_tokyo_ai_arena_simulation_v1",
        "generated_at": iso_jst(now_jst()),
        "market": "Japan",
        "timezone": "Asia/Tokyo",
        "range": {"start_date": start_date, "end_date": end_date, "trading_days": len(sim_dates)},
        "diagnostics": {
            "daily_snapshots_used": len(daily_by_date),
            "scheduled_orders": scheduled_orders_count,
            "executed_entries": executed_entries_count,
            "closed_exits": closed_exits_count,
            "pending_orders_after_end": sum(len(v) for v in pending_orders.values()),
            "initial_capital_jpy": round(initial_capital, 0),
            "lot_size": lot_size,
        },
        "season": season,
        "config": {"agents_yaml": str(AGENTS_YAML.relative_to(ROOT)), "prices_json": str(PRICES_JSON.relative_to(ROOT)) if PRICES_JSON.is_relative_to(ROOT) else str(PRICES_JSON), "daily_dir": str(DAILY_DIR.relative_to(ROOT)) if DAILY_DIR.is_relative_to(ROOT) else str(DAILY_DIR)},
        "methodology": {
            "entry": "next trading day open after signal date",
            "valuation": "close-based daily valuation",
            "position_sizing": "agent-specific percentage of available cash, rounded down to 100-share lots",
            "exits": "close-based stop loss, take profit, or max holding days",
            "important_note": "This is a simulation game, not an executed portfolio and not investment advice.",
        },
        "agents": agents_out,
        "ranking": {"season": season, "agents": ranking_agents},
    }

    # Split outputs for pages. Keep full simulation as canonical source.
    positions_payload = {
        "schema_version": "neon_tokyo_ai_arena_positions_v1",
        "generated_at": payload["generated_at"],
        "range": payload["range"],
        "season": season,
        "agents": [
            {k: a.get(k) for k in ("agent_id", "name", "class", "ui_tone", "avatar_style", "avatar_image", "personality", "philosophy", "summary", "open_positions", "recent_actions")}
            for a in agents_out
        ],
    }
    ranking_payload = {
        "schema_version": "neon_tokyo_ai_arena_ranking_v1",
        "generated_at": payload["generated_at"],
        "range": payload["range"],
        "season": season,
        "agents": ranking_agents,
        "champion": ranking_agents[0] if ranking_agents else None,
        "season_archive_note": "Monthly JSON archives can be added after live behavior is validated.",
    }
    return {"simulation": payload, "positions": positions_payload, "ranking": ranking_payload}


def main() -> None:
    config = read_yaml(AGENTS_YAML, {})
    prices = load_prices()
    weekly = weekly_features()
    snaps = collect_daily_snapshots()
    if not snaps:
        raise SystemExit("No daily snapshots found under site/data/daily-jp. Run Daily JP first.")
    outputs = run_simulation(config, prices, snaps, weekly)
    write_json(SIM_OUT, outputs["simulation"])
    write_json(POSITIONS_OUT, outputs["positions"])
    write_json(RANKING_OUT, outputs["ranking"])


if __name__ == "__main__":
    main()
