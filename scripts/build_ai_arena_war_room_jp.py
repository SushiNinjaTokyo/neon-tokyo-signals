#!/usr/bin/env python3
from __future__ import annotations

"""Build the standalone AI Arena War Room / Arena Log payload.

Design goals
------------
This script converts already-generated AI Arena outputs into a high-signal,
English-only, conversation-first page payload for `/japan/ai-arena/log/`.

It deliberately does not change trading logic.  The trading simulation remains
owned by the season rebuild pipeline.  This script reads public JSON artifacts
such as ranking, positions, log, summary, and discussion; then it produces a
new `war-room/latest.json` file that is safe for a static site.

The output is designed to feel like seven autonomous agents are debating the
market in real time, while staying factual:

- every thread is anchored to an actual Arena fact: ranking, open positions,
  filled orders, or current portfolio state;
- GPT is optional and disabled by default;
- when GPT is enabled, it is used only to polish provided facts, never to fetch
  external news or invent reasons;
- cost controls are implemented through a conservative per-run budget gate;
- historical snapshots are pruned to prevent repository bloat.

Environment variables
---------------------
OUT_DIR                         Static site output directory. Default: site
OPENAI_ENABLE_AI                true/false. Default: false
OPENAI_API_KEY                  Required only when OPENAI_ENABLE_AI=true
AI_ARENA_WAR_ROOM_MODEL         Default: gpt-4o-mini. Use gpt-4o if desired.
AI_ARENA_WAR_ROOM_MAX_THREADS   Default: 16
AI_ARENA_WAR_ROOM_HISTORY_DAYS  Default: 14
AI_ARENA_WAR_ROOM_DAILY_USD_LIMIT Default: 0.65
"""

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - GitHub Actions installs PyYAML via requirements.
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()

BASE = OUT_DIR / "data" / "japan" / "ai-arena"
AGENTS_YAML = ROOT / "data" / "agents" / "jp_agents.yml"
VOICE_YAML = ROOT / "data" / "agents" / "jp_agent_voice_rules.yml"
JST = timezone(timedelta(hours=9))

MAX_THREADS = int(os.getenv("AI_ARENA_WAR_ROOM_MAX_THREADS", "16"))
HISTORY_DAYS = int(os.getenv("AI_ARENA_WAR_ROOM_HISTORY_DAYS", "14"))
MODEL = os.getenv("AI_ARENA_WAR_ROOM_MODEL", "gpt-4o-mini")

# Canonical visual identity.  This is intentionally repeated here because the
# old YAML still contains pre-7-agent semantic colors in a few places.
CANONICAL_COLORS = {
    "daily_striker": "#FF4B5C",       # KYOU red
    "weekly_sage": "#B779FF",         # NAGARE purple
    "risk_sentinel": "#7DF9FF",       # MAMORU cyan
    "discovery_scout": "#5DFFB1",     # SAGURI green
    "contrarian_monk": "#FFD166",     # MATSU yellow
    "reversal_snapback": "#FF4FD8",   # KAESHI pink
    "value_mispricing": "#4F46E5",    # HIZUMI indigo blue
}

CANONICAL_NAMES = {
    "daily_striker": "KYOU",
    "weekly_sage": "NAGARE",
    "risk_sentinel": "MAMORU",
    "discovery_scout": "SAGURI",
    "contrarian_monk": "MATSU",
    "reversal_snapback": "KAESHI",
    "value_mispricing": "HIZUMI",
}

CANONICAL_ROLES = {
    "daily_striker": "Intraday momentum and volume pressure",
    "weekly_sage": "Medium-term trend flow and persistence",
    "risk_sentinel": "Capital preservation and drawdown control",
    "discovery_scout": "Small-cap discovery and early theme detection",
    "contrarian_monk": "Patient pullback and second-entry discipline",
    "reversal_snapback": "Oversold reversal and snapback pressure",
    "value_mispricing": "Value distortion, re-rating, and trap detection",
}

AGENT_STATES = {
    "daily_striker": "SCANNING MOMENTUM",
    "weekly_sage": "READING FLOW",
    "risk_sentinel": "RISK GATE ACTIVE",
    "discovery_scout": "HUNTING EARLY SIGNALS",
    "contrarian_monk": "WAITING FOR PULLBACK",
    "reversal_snapback": "SNAPBACK WATCH",
    "value_mispricing": "TESTING MISPRICING",
}

VOICE_LINES = {
    "daily_striker": {
        "brief": "I only move when price, volume, and timing compress into one clean strike.",
        "buy": "The tape gave me pressure and confirmation. I take the strike, then I let the stop define the debate.",
        "sell": "Momentum lost the right to occupy capital. I exit and recycle attention to the next live setup.",
        "challenge": "Slow confirmation can become expensive when the market has already moved.",
    },
    "weekly_sage": {
        "brief": "One candle is not a trend. I am watching whether leadership can persist beyond the first impulse.",
        "buy": "This enters the flow only if the structure can survive more than a single burst.",
        "sell": "The flow weakened. I would rather leave than turn a trend thesis into hope.",
        "challenge": "Speed is useful, but durability is what compounds.",
    },
    "risk_sentinel": {
        "brief": "The Arena is only alive if drawdown stays controlled. I audit every signal through exposure and liquidity.",
        "buy": "Entry is permitted only because the risk budget can absorb a defined failure.",
        "sell": "Cutting risk is not pessimism. It is the cost of keeping the simulation alive.",
        "challenge": "A good idea still fails if sizing, liquidity, or stop distance is wrong.",
    },
    "discovery_scout": {
        "brief": "The useful signal often appears before the market gives it a famous label.",
        "buy": "This is exactly where discovery matters: early movement, imperfect consensus, and asymmetric attention.",
        "sell": "When the first discovery edge fades, I leave before curiosity becomes attachment.",
        "challenge": "Large liquid leaders are visible to everyone; the edge may be hiding lower in the stack.",
    },
    "contrarian_monk": {
        "brief": "I do not pay the first-entry tax. I wait until the crowd gives me a cleaner second door.",
        "buy": "The pullback is controlled enough to test. Patience finally converted into action.",
        "sell": "The setup stopped rewarding patience. Waiting is discipline; overstaying is not.",
        "challenge": "The best trade may be the one we refuse until price cools.",
    },
    "reversal_snapback": {
        "brief": "Panic is not enough. I need stretched pressure with room for a violent reversal.",
        "buy": "The selloff stretched far enough to create snapback tension. I take the rebound window, not the narrative.",
        "sell": "The rebound window closed. I do not confuse a bounce with a new regime.",
        "challenge": "Trend followers often arrive after the elastic energy has already been spent.",
    },
    "value_mispricing": {
        "brief": "Mispricing alone is not alpha. I need proof that the discount is not a trap.",
        "buy": "The distortion is actionable only because price behavior supports re-rating rather than value decay.",
        "sell": "The distortion failed to close. I exit before cheap becomes permanently cheap.",
        "challenge": "Momentum can hide overpayment; value can hide deterioration. Evidence must decide.",
    },
}

MODEL_PRICES_USD_PER_1M = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

BANNED_PHRASES = [
    "buy recommendation",
    "sell recommendation",
    "target price",
    "guaranteed",
    "must own",
    "strong buy",
    "strong sell",
    "easy money",
]


def now_jst() -> datetime:
    return datetime.now(JST)


def iso_jst(dt: datetime | None = None) -> str:
    return (dt or now_jst()).astimezone(JST).isoformat(timespec="seconds")


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        print(f"WARN missing JSON: {path}")
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WARN failed to read JSON {path}: {exc}")
        return fallback


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        rel = path.relative_to(ROOT)
    except Exception:
        rel = path
    print(f"Wrote {rel}")


def read_yaml(path: Path) -> dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"WARN failed to read YAML {path}: {exc}")
        return {}


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def fmt_pct(value: Any, digits: int = 2) -> str:
    return f"{to_float(value):+.{digits}f}%"


def fmt_jpy(value: Any) -> str:
    v = to_float(value)
    return f"¥{v:,.0f}"


def clean_text(text: Any, limit: int = 280) -> str:
    s = str(text or "").strip()
    s = re.sub(r"\s+", " ", s)
    # Remove old five-agent names that may exist in legacy discussion JSON.
    s = re.sub(r"\bKAKERU\b", "KYOU", s)
    s = re.sub(r"\bSATORI\b", "NAGARE", s)
    for phrase in BANNED_PHRASES:
        s = re.sub(re.escape(phrase), "", s, flags=re.I)
    return s[:limit].strip(" -—,:;.")


def agent_name(agent_id: str) -> str:
    return CANONICAL_NAMES.get(agent_id, agent_id.upper())


def agent_color(agent_id: str) -> str:
    return CANONICAL_COLORS.get(agent_id, "#7DF9FF")


def agent_image(agent_id: str) -> str:
    return f"/assets/ai-arena/agents/{agent_id}.png"


def load_agents() -> list[dict[str, Any]]:
    agents_json = read_json(BASE / "agents" / "latest.json", {})
    raw_agents = agents_json.get("agents") if isinstance(agents_json, dict) else None
    if not raw_agents:
        raw_agents = (read_yaml(AGENTS_YAML).get("agents") or [])

    by_id: dict[str, dict[str, Any]] = {}
    for raw in raw_agents or []:
        aid = str(raw.get("agent_id") or raw.get("id") or "")
        if not aid:
            continue
        by_id[aid] = raw

    agents: list[dict[str, Any]] = []
    for aid in CANONICAL_NAMES:
        raw = by_id.get(aid, {})
        agents.append({
            "agent_id": aid,
            "name": agent_name(aid),
            "role": raw.get("role") or raw.get("style_label") or CANONICAL_ROLES[aid],
            "style_label": raw.get("style_label") or CANONICAL_ROLES[aid],
            "description": raw.get("short_description") or raw.get("description") or CANONICAL_ROLES[aid],
            "image": raw.get("image") or raw.get("avatar_image") or agent_image(aid),
            "color": agent_color(aid),
            "state": AGENT_STATES[aid],
            "voice": VOICE_LINES[aid],
        })
    return agents


def normalize_ranking(payload: dict[str, Any], agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_agent = {a["agent_id"]: a for a in agents}
    rows = payload.get("ranking") or []
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        aid = str(row.get("agent_id") or row.get("agent", {}).get("agent_id") or "")
        if not aid:
            continue
        agent = by_agent.get(aid, {})
        out.append({
            "rank": to_int(row.get("rank"), idx + 1),
            "agent_id": aid,
            "name": agent.get("name") or agent_name(aid),
            "role": agent.get("role") or CANONICAL_ROLES.get(aid, ""),
            "image": agent.get("image") or agent_image(aid),
            "color": agent_color(aid),
            "return_pct": to_float(row.get("total_return_pct")),
            "return_label": fmt_pct(row.get("total_return_pct")),
            "equity_jpy": to_float(row.get("end_equity_jpy")),
            "equity_label": fmt_jpy(row.get("end_equity_jpy")),
            "max_drawdown_pct": to_float(row.get("max_drawdown_pct")),
            "mdd_label": fmt_pct(row.get("max_drawdown_pct")),
            "win_rate_pct": to_float(row.get("win_rate_pct")),
            "win_rate_label": fmt_pct(row.get("win_rate_pct")),
            "trade_count": to_int(row.get("trade_count")),
        })
    return sorted(out, key=lambda x: x["rank"])


def normalize_positions(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    def normalize_one(row: dict[str, Any], is_open: bool) -> dict[str, Any]:
        aid = str(row.get("agent_id") or row.get("agent", {}).get("agent_id") or "")
        ticker = str(row.get("ticker") or row.get("symbol") or "")
        name = str(row.get("name") or row.get("company_name") or ticker)
        pnl = row.get("unrealized_return_pct") if is_open else row.get("return_pct")
        if pnl is None:
            pnl = row.get("unrealized_pnl_pct") if is_open else None
        if pnl is None:
            pnl = row.get("pnl_pct") or row.get("realized_pnl_pct")
        return {
            "agent_id": aid,
            "agent_name": agent_name(aid),
            "ticker": ticker,
            "name": name,
            "side": str(row.get("side") or "LONG"),
            "entry_date": str(row.get("entry_date") or row.get("date") or ""),
            "exit_date": str(row.get("exit_date") or ""),
            "holding_days": to_int(row.get("holding_days")),
            "entry_price": to_float(row.get("entry_price")),
            "last_price": to_float(row.get("last_price") or row.get("exit_price")),
            "pnl_pct": to_float(pnl),
            "pnl_label": fmt_pct(pnl),
            "pnl_jpy": to_float(row.get("unrealized_pnl_jpy") or row.get("realized_pnl_jpy")),
            "reason": str(row.get("exit_reason") or row.get("reason_code") or row.get("reason") or ""),
        }

    open_positions = [normalize_one(x, True) for x in payload.get("open_positions", []) if isinstance(x, dict)]
    closed_trades = [normalize_one(x, False) for x in payload.get("closed_trades", []) if isinstance(x, dict)]
    portfolio = payload.get("portfolio") or {}
    return open_positions, closed_trades, portfolio


def normalize_log_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    events = []
    for idx, row in enumerate(payload.get("events", []) if isinstance(payload, dict) else []):
        if not isinstance(row, dict):
            continue
        aid = str(row.get("agent_id") or "")
        side = str(row.get("side") or row.get("badge") or "").upper()
        badge = "IN" if side == "BUY" or side == "IN" else "OUT" if side == "SELL" or side == "OUT" else str(row.get("badge") or "")
        events.append({
            "event_id": str(row.get("event_id") or f"event-{idx+1:04d}"),
            "show_at": str(row.get("show_at") or iso_jst()),
            "event_type": str(row.get("event_type") or "TRADE_LOG"),
            "agent_id": aid,
            "agent_name": agent_name(aid),
            "ticker": str(row.get("ticker") or row.get("linked_symbol") or ""),
            "name": str(row.get("name") or row.get("linked_name") or row.get("ticker") or ""),
            "badge": badge,
            "side": side,
            "reason_code": str(row.get("reason_code") or row.get("reason") or ""),
            "message": clean_text(row.get("message") or row.get("body") or ""),
        })
    return events


@dataclass
class Context:
    agents: list[dict[str, Any]]
    ranking: list[dict[str, Any]]
    open_positions: list[dict[str, Any]]
    closed_trades: list[dict[str, Any]]
    portfolio: dict[str, Any]
    events: list[dict[str, Any]]
    summary: dict[str, Any]


def evidence_card(title: str, rows: list[tuple[str, Any]]) -> dict[str, Any]:
    return {
        "title": title,
        "rows": [{"label": label, "value": str(value)} for label, value in rows if value not in (None, "")],
    }


def message(agent_id: str, body: str, msg_type: str = "analysis", state: str | None = None, symbol: str = "", name: str = "") -> dict[str, Any]:
    return {
        "message_id": "",  # assigned after thread assembly
        "agent_id": agent_id,
        "agent_name": agent_name(agent_id),
        "avatar_image": agent_image(agent_id),
        "color": agent_color(agent_id),
        "state": state or AGENT_STATES.get(agent_id, "ANALYZING"),
        "type": msg_type,
        "body": clean_text(body, 360),
        "linked_symbol": symbol,
        "linked_name": name,
    }


def assign_ids(thread: dict[str, Any], thread_index: int) -> dict[str, Any]:
    thread["thread_id"] = thread.get("thread_id") or f"war-thread-{thread_index:04d}"
    for i, msg in enumerate(thread.get("messages", []), start=1):
        msg["message_id"] = msg.get("message_id") or f"{thread['thread_id']}-msg-{i:02d}"
    return thread


def build_opening_thread(ctx: Context) -> dict[str, Any]:
    leader = ctx.ranking[0] if ctx.ranking else {}
    second = ctx.ranking[1] if len(ctx.ranking) > 1 else {}
    open_count = len(ctx.open_positions)
    season = ctx.summary.get("year") or ctx.summary.get("run", {}).get("year") or "Live"
    rows = [
        ("Season", season),
        ("Leader", f"{leader.get('name','—')} {leader.get('return_label','')}") if leader else ("Leader", "—"),
        ("Second", f"{second.get('name','—')} {second.get('return_label','')}") if second else ("Second", "—"),
        ("Open positions", open_count),
        ("Mode", "Simulation data only"),
    ]
    msgs = [
        message("weekly_sage", f"{leader.get('name','The leader')} controls the board for now, but I care less about rank than whether the flow persists."),
        message("risk_sentinel", f"The room has {open_count} open positions. The useful question is not who is loudest; it is whose risk survives the next reversal.", "risk"),
        message("value_mispricing", "I will not call a move intelligent until price, valuation pressure, and trap risk agree.", "challenge"),
        message("daily_striker", "If fresh pressure appears today, I do not wait for the story to become comfortable.", "momentum"),
    ]
    return {
        "thread_type": "market_council",
        "priority": 1000,
        "title": "Seven agents are online. The market council is live.",
        "subtitle": "A fast brief built from ranking, positions, and filled Arena events.",
        "trigger": {"event_type": "ROOM_OPEN", "badge": "LIVE", "agent_id": "market"},
        "evidence": evidence_card("Arena state", rows),
        "messages": msgs,
        "show_at": iso_jst(now_jst() - timedelta(minutes=50)),
    }


def build_ranking_thread(ctx: Context) -> dict[str, Any] | None:
    if len(ctx.ranking) < 2:
        return None
    leader, challenger = ctx.ranking[0], ctx.ranking[1]
    spread = leader["return_pct"] - challenger["return_pct"]
    msgs = [
        message(leader["agent_id"], f"Rank one is not a trophy. It is a temporary claim on process discipline. My return stands at {leader['return_label']}.", "leader"),
        message(challenger["agent_id"], f"The gap is {spread:.2f} percentage points. That is close enough for one regime shift to matter.", "challenge"),
        message("risk_sentinel", f"I am watching the drawdown difference: {leader['name']} at {leader['mdd_label']} versus {challenger['name']} at {challenger['mdd_label']}.", "risk"),
        message("contrarian_monk", "Leaderboard pressure is where impatient agents overtrade. The best response may be waiting for a cleaner pitch.", "discipline"),
    ]
    return {
        "thread_type": "ranking_duel",
        "priority": 900,
        "title": f"Leaderboard duel: {leader['name']} leads, {challenger['name']} is within striking distance.",
        "subtitle": "Return is visible. Risk-adjusted discipline is the hidden fight.",
        "trigger": {"event_type": "RANKING", "badge": "DUEL", "agent_id": leader["agent_id"]},
        "evidence": evidence_card("Duel metrics", [
            ("Leader", f"{leader['name']} {leader['return_label']}"),
            ("Challenger", f"{challenger['name']} {challenger['return_label']}"),
            ("Gap", f"{spread:.2f} pts"),
            ("Leader MDD", leader["mdd_label"]),
            ("Challenger MDD", challenger["mdd_label"]),
        ]),
        "messages": msgs,
        "show_at": iso_jst(now_jst() - timedelta(minutes=42)),
    }


def build_trade_thread(event: dict[str, Any], idx: int) -> dict[str, Any]:
    aid = event.get("agent_id") or "daily_striker"
    ticker = event.get("ticker") or ""
    name = event.get("name") or ticker
    badge = event.get("badge") or "EVENT"
    is_in = badge == "IN" or str(event.get("side", "")).upper() == "BUY"
    actor_line = VOICE_LINES.get(aid, VOICE_LINES["daily_striker"])["buy" if is_in else "sell"]
    title_action = "entered" if is_in else "exited"
    counter_id = "risk_sentinel" if aid != "risk_sentinel" else "weekly_sage"
    msgs = [
        message(aid, f"{ticker} {title_action}. {actor_line}", "trade_decision", "EXECUTING" if is_in else "CLOSING", ticker, name),
        message(counter_id, VOICE_LINES[counter_id]["challenge"], "challenge", symbol=ticker, name=name),
    ]
    if is_in:
        msgs.append(message("value_mispricing", "Entry is only interesting if the evidence separates opportunity from a crowded chase.", "evidence", symbol=ticker, name=name))
        msgs.append(message("weekly_sage", "I will watch whether this becomes structure or remains a single-session impulse.", "flow", symbol=ticker, name=name))
    else:
        msgs.append(message("contrarian_monk", "An exit can be wise or premature. The difference appears only after the next clean setup is offered.", "reflection", symbol=ticker, name=name))
        msgs.append(message("reversal_snapback", "When exits cluster, I start watching for elastic pressure. Not prediction; just tension.", "snapback", symbol=ticker, name=name))
    return {
        "thread_type": "trade_event",
        "priority": 820 - idx,
        "title": f"{agent_name(aid)} {title_action} {ticker}",
        "subtitle": event.get("message") or f"Filled Arena event: {badge} {ticker}",
        "trigger": {
            "event_type": "TRADE_EVENT",
            "badge": badge,
            "agent_id": aid,
            "symbol": ticker,
            "company_name": name,
            "reason_code": event.get("reason_code") or "",
        },
        "evidence": evidence_card("Trade evidence", [
            ("Agent", agent_name(aid)),
            ("Ticker", ticker),
            ("Company", name),
            ("Side", badge),
            ("Reason", event.get("reason_code") or "Filled order"),
            ("Source", "arena_orders / log/latest.json"),
        ]),
        "messages": msgs,
        "show_at": event.get("show_at") or iso_jst(now_jst() - timedelta(minutes=idx * 7)),
    }


def build_position_thread(pos: dict[str, Any], idx: int) -> dict[str, Any]:
    aid = pos.get("agent_id") or "daily_striker"
    ticker = pos.get("ticker") or ""
    name = pos.get("name") or ticker
    pnl = pos.get("pnl_pct", 0)
    is_positive = to_float(pnl) >= 0
    support = "weekly_sage" if is_positive else "risk_sentinel"
    tension = "This position is working, but working positions still need exit discipline." if is_positive else "This position is under pressure, so the debate shifts from thesis to damage control."
    msgs = [
        message(aid, f"{ticker} is still open at {pos.get('pnl_label')}. I am judging whether the original edge remains intact.", "position", symbol=ticker, name=name),
        message(support, tension, "analysis", symbol=ticker, name=name),
        message("value_mispricing", "I separate temporary price noise from structural deterioration. The latter is what turns patience into a trap.", "evidence", symbol=ticker, name=name),
    ]
    if not is_positive:
        msgs.append(message("reversal_snapback", "Pressure can become opportunity only when exhaustion appears. Until then, it is simply pressure.", "snapback", symbol=ticker, name=name))
    else:
        msgs.append(message("risk_sentinel", "Unrealized profit is not owned until the exit process protects it.", "risk", symbol=ticker, name=name))
    return {
        "thread_type": "open_position",
        "priority": 760 - idx,
        "title": f"Open position watch: {ticker} at {pos.get('pnl_label')}",
        "subtitle": "The agents debate whether current exposure deserves more time.",
        "trigger": {"event_type": "POSITION", "badge": "OPEN", "agent_id": aid, "symbol": ticker, "company_name": name},
        "evidence": evidence_card("Position evidence", [
            ("Agent", agent_name(aid)),
            ("Ticker", ticker),
            ("Company", name),
            ("Unrealized P/L", pos.get("pnl_label")),
            ("Holding days", pos.get("holding_days")),
            ("Entry date", pos.get("entry_date")),
        ]),
        "messages": msgs,
        "show_at": iso_jst(now_jst() - timedelta(minutes=28 - idx * 4)),
    }


def build_agent_manifest(ctx: Context) -> list[dict[str, Any]]:
    ranking_by_id = {r["agent_id"]: r for r in ctx.ranking}
    open_by_id: dict[str, int] = {}
    for p in ctx.open_positions:
        open_by_id[p["agent_id"]] = open_by_id.get(p["agent_id"], 0) + 1
    manifest = []
    for agent in ctx.agents:
        aid = agent["agent_id"]
        rank = ranking_by_id.get(aid, {})
        state = agent["state"]
        if open_by_id.get(aid, 0) == 0:
            state = "OBSERVING"
        manifest.append({
            **agent,
            "rank": rank.get("rank"),
            "return_pct": rank.get("return_pct", 0),
            "return_label": rank.get("return_label", "+0.00%"),
            "mdd_label": rank.get("mdd_label", "+0.00%"),
            "win_rate_label": rank.get("win_rate_label", "+0.00%"),
            "trade_count": rank.get("trade_count", 0),
            "open_positions": open_by_id.get(aid, 0),
            "state": state,
        })
    return manifest


def build_pulse(ctx: Context) -> list[dict[str, Any]]:
    pulse = []
    for agent in ctx.agents:
        aid = agent["agent_id"]
        pulse.append({
            "agent_id": aid,
            "agent_name": agent_name(aid),
            "color": agent_color(aid),
            "state": AGENT_STATES[aid],
            "body": VOICE_LINES[aid]["brief"],
        })
    return pulse


def ai_enabled() -> bool:
    return os.getenv("OPENAI_ENABLE_AI", "false").lower() == "true" and bool(os.getenv("OPENAI_API_KEY"))


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4))


def maybe_polish_with_openai(payload: dict[str, Any]) -> dict[str, Any]:
    """Optionally polish thread titles/messages without changing facts.

    The deterministic payload is already production-ready.  This function is a
    bounded enhancement: one compact JSON request, conservative token estimate,
    and strict fallback to the original payload on any error.
    """
    if not ai_enabled():
        payload.setdefault("ai", {})["enabled"] = False
        payload["ai"]["status"] = "disabled"
        return payload

    model_prices = MODEL_PRICES_USD_PER_1M.get(MODEL, MODEL_PRICES_USD_PER_1M["gpt-4o-mini"])
    daily_limit = to_float(os.getenv("AI_ARENA_WAR_ROOM_DAILY_USD_LIMIT", "0.65"), 0.65)
    compact = {
        "brief": payload.get("daily_brief"),
        "threads": [
            {
                "thread_id": t.get("thread_id"),
                "thread_type": t.get("thread_type"),
                "title": t.get("title"),
                "trigger": t.get("trigger"),
                "messages": [
                    {"agent_id": m.get("agent_id"), "body": m.get("body"), "type": m.get("type")}
                    for m in t.get("messages", [])[:4]
                ],
            }
            for t in payload.get("threads", [])[:8]
        ],
    }
    system = (
        "You polish an English-only fictional AI trading simulation discussion. "
        "Use only provided facts. Do not add news, earnings, targets, recommendations, or claims. "
        "Return JSON with keys daily_brief and threads. Keep every thread_id and agent_id unchanged. "
        "Make the dialogue sharper, more specific, and professional."
    )
    request_text = json.dumps(compact, ensure_ascii=False)
    max_tokens = 1800
    est_cost = estimate_tokens(system + request_text) / 1_000_000 * model_prices["input"] + max_tokens / 1_000_000 * model_prices["output"]
    if est_cost > daily_limit:
        payload.setdefault("ai", {})["enabled"] = False
        payload["ai"]["status"] = f"skipped_cost_gate_est_${est_cost:.4f}"
        return payload

    body = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": request_text},
        ],
        "temperature": 0.58,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            data = json.loads(res.read().decode("utf-8"))
        polished = json.loads(data["choices"][0]["message"]["content"])
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        payload.setdefault("ai", {})["enabled"] = False
        payload["ai"]["status"] = f"fallback_openai_error: {exc}"
        return payload

    by_thread = {t.get("thread_id"): t for t in payload.get("threads", [])}
    for pt in polished.get("threads", []) if isinstance(polished, dict) else []:
        target = by_thread.get(pt.get("thread_id"))
        if not target:
            continue
        if clean_text(pt.get("title")):
            target["title"] = clean_text(pt.get("title"), 140)
        pmsgs = pt.get("messages") or []
        for idx, pm in enumerate(pmsgs):
            if idx >= len(target.get("messages", [])):
                continue
            if pm.get("agent_id") != target["messages"][idx].get("agent_id"):
                continue
            body_text = clean_text(pm.get("body"), 360)
            if body_text:
                target["messages"][idx]["body"] = body_text
    if isinstance(polished, dict) and polished.get("daily_brief"):
        payload["daily_brief"]["headline"] = clean_text(polished["daily_brief"], 180)
    payload.setdefault("ai", {})["enabled"] = True
    payload["ai"]["status"] = "polished"
    payload["ai"]["model"] = MODEL
    payload["ai"]["estimated_cost_usd"] = round(est_cost, 5)
    return payload


def prune_history(history_dir: Path, keep_days: int) -> None:
    if keep_days <= 0 or not history_dir.exists():
        return
    cutoff = now_jst().date() - timedelta(days=keep_days)
    for path in history_dir.glob("*.json"):
        try:
            day = datetime.strptime(path.stem, "%Y-%m-%d").date()
        except ValueError:
            continue
        if day < cutoff:
            path.unlink(missing_ok=True)
            print(f"Pruned old war-room snapshot: {path}")


def build_payload() -> dict[str, Any]:
    agents = load_agents()
    ranking_payload = read_json(BASE / "ranking" / "latest.json", {})
    positions_payload = read_json(BASE / "positions" / "latest.json", {})
    summary_payload = read_json(BASE / "summary" / "latest.json", {})
    log_payload = read_json(BASE / "log" / "latest.json", {})

    ranking = normalize_ranking(ranking_payload, agents)
    open_positions, closed_trades, portfolio = normalize_positions(positions_payload)
    events = normalize_log_events(log_payload)
    ctx = Context(agents, ranking, open_positions, closed_trades, portfolio, events, summary_payload)

    threads: list[dict[str, Any]] = [build_opening_thread(ctx)]
    ranking_thread = build_ranking_thread(ctx)
    if ranking_thread:
        threads.append(ranking_thread)

    # Filled order events create the most immediate "live debate" sensation.
    for idx, event in enumerate(events[-8:][::-1], start=1):
        threads.append(build_trade_thread(event, idx))

    # Open positions provide investor-useful monitoring value beyond chat drama.
    watched_positions = sorted(open_positions, key=lambda p: abs(to_float(p.get("pnl_pct"))), reverse=True)[:5]
    for idx, pos in enumerate(watched_positions, start=1):
        threads.append(build_position_thread(pos, idx))

    threads = sorted(threads, key=lambda t: to_int(t.get("priority")), reverse=True)[:MAX_THREADS]
    threads = [assign_ids(t, i) for i, t in enumerate(threads, start=1)]

    # A flat feed is kept for compatibility and for mobile/SEO-friendly summaries.
    feed: list[dict[str, Any]] = []
    for thread in threads:
        for msg in thread.get("messages", []):
            feed.append({
                "id": msg["message_id"],
                "thread_id": thread["thread_id"],
                "thread_type": thread["thread_type"],
                "show_at": thread.get("show_at"),
                **msg,
            })

    leader = ranking[0] if ranking else {}
    open_count = len(open_positions)
    payload = {
        "schema_version": "ai_arena_war_room_v1",
        "generated_at": iso_jst(),
        "run_id": ranking_payload.get("run_id") or positions_payload.get("run_id") or summary_payload.get("run_id") or log_payload.get("run_id") or "",
        "year": ranking_payload.get("year") or summary_payload.get("year") or "",
        "page": {
            "title": "AI Arena War Room",
            "subtitle": "Seven trading agents debate Japan equities using live simulation evidence.",
            "path": "/japan/ai-arena/log/",
        },
        "daily_brief": {
            "headline": f"{leader.get('name', 'Seven agents')} leads the room while {open_count} open positions keep the debate live.",
            "summary": "This page transforms the latest AI Arena ranking, positions, and filled orders into a fast, evidence-linked agent discussion. It is a simulation interface, not investment advice.",
            "bullets": [
                f"Current leader: {leader.get('name', '—')} {leader.get('return_label', '')}".strip(),
                f"Open positions under debate: {open_count}",
                f"Recent filled Arena events analyzed: {len(events)}",
            ],
        },
        "agents": build_agent_manifest(ctx),
        "ranking": ranking,
        "open_positions": open_positions[:24],
        "threads": threads,
        "feed": feed[:160],
        "pulse": build_pulse(ctx),
        "metrics": {
            "agent_count": len(agents),
            "thread_count": len(threads),
            "message_count": len(feed),
            "open_position_count": open_count,
            "recent_event_count": len(events),
            "leader": leader.get("name", "—"),
            "leader_return": leader.get("return_label", ""),
        },
        "ai": {
            "enabled": False,
            "status": "deterministic",
            "model": MODEL,
            "cost_policy": "Optional GPT polishing is capped by AI_ARENA_WAR_ROOM_DAILY_USD_LIMIT. Default deterministic generation costs $0.",
        },
        "disclaimer": "AI Arena is a quantitative simulation and discussion interface. Informational only. Not investment advice.",
    }
    return maybe_polish_with_openai(payload)


def main() -> int:
    payload = build_payload()
    latest = BASE / "war-room" / "latest.json"
    write_json(latest, payload)

    # Keep a small rolling history for debugging and future animations, but do
    # not allow daily snapshots to grow forever in git.
    history_dir = BASE / "war-room" / "history"
    snapshot = history_dir / f"{now_jst().date().isoformat()}.json"
    write_json(snapshot, payload)
    prune_history(history_dir, HISTORY_DAYS)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
