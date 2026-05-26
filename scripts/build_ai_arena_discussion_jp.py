from __future__ import annotations

"""
Build Neon Tokyo AI Arena LAB discussion feed.

LAB v3 design
-------------
1. Trading decisions stay in deterministic Python simulation.
2. Python extracts Discussion Events from simulation / ranking / positions.
3. Agent Voice Book is stored in data/ai_arena_agents_jp.yml.
4. Agent Memory is stored in site/data/japan/ai-arena/memory/latest.json.
5. This script calls GPT per thread, not once for the whole day.
6. Threads are merged into a 24-hour feed with 5-10 minute random spacing.
7. Quality guard is intentionally minimal: protect factual integrity without
   making the conversation sterile.

No external news is used in this version.
"""

import json
import os
import random
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()

AGENTS_YAML = Path(os.getenv("AI_ARENA_AGENTS_YAML", str(ROOT / "data/ai_arena_agents_jp.yml")))
SIM_JSON = Path(os.getenv("AI_ARENA_SIM_JSON", str(OUT_DIR / "data/japan/ai-arena/simulation/latest.json")))
POSITIONS_JSON = Path(os.getenv("AI_ARENA_POSITIONS_JSON", str(OUT_DIR / "data/japan/ai-arena/positions/latest.json")))
RANKING_JSON = Path(os.getenv("AI_ARENA_RANKING_JSON", str(OUT_DIR / "data/japan/ai-arena/ranking/latest.json")))
EVENTS_JSON = Path(os.getenv("AI_ARENA_EVENTS_JSON", str(OUT_DIR / "data/japan/ai-arena/events/latest.json")))
MEMORY_JSON = Path(os.getenv("AI_ARENA_MEMORY_JSON", str(OUT_DIR / "data/japan/ai-arena/memory/latest.json")))

DISCUSSION_OUT = OUT_DIR / "data/japan/ai-arena/discussion/latest.json"
LEGACY_OUT = OUT_DIR / "data/japan/ai-arena/latest.json"

JST = timezone(timedelta(hours=9))

MODEL_PRICES_USD_PER_1M = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-5.5": {"input": 5.00, "output": 30.00},
}

BANNED_SUBSTRINGS = [
    "strong buy",
    "target price",
    "guaranteed",
    "must own",
    "easy money",
    "recommend",
    "recommendation",
    "hidden gems",
    "exciting opportunities",
    "monitor closely",
    "proceed with caution",
    "fundamentals improved",
    "earnings beat",
    "guidance",
]


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
        print(f"WARN missing YAML: {path}")
        return fallback
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or fallback
    except Exception as exc:
        print(f"WARN failed YAML {path}: {exc}")
        return fallback


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        rel = path.relative_to(ROOT)
    except Exception:
        rel = path
    print(f"Wrote {rel}")


def to_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def to_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(float(x))
    except Exception:
        return default


def fmt_pct(x: Any) -> str:
    return f"{to_float(x):+.2f}%"


def safe_text(x: Any, limit: int = 300) -> str:
    s = str(x or "").strip()
    s = re.sub(r"\s+", " ", s)
    for banned in BANNED_SUBSTRINGS:
        s = re.sub(re.escape(banned), "", s, flags=re.I)
    return s[:limit].strip()


def ai_enabled() -> bool:
    return os.getenv("OPENAI_ENABLE_AI", "false").lower() == "true" and bool(os.getenv("OPENAI_API_KEY"))


def estimate_tokens(s: str) -> int:
    return max(1, int(len(s) / 4))


def call_openai_json(model: str, system: str, payload: dict[str, Any], max_tokens: int) -> dict[str, Any] | None:
    if not ai_enabled():
        return None
    request_text = json.dumps(payload, ensure_ascii=False)
    # A soft daily limit.  This is not perfect accounting, but it prevents
    # accidental runaway calls if prompts grow unexpectedly.
    price = MODEL_PRICES_USD_PER_1M.get(model, MODEL_PRICES_USD_PER_1M["gpt-4o-mini"])
    est_cost = estimate_tokens(system + request_text) / 1_000_000 * price["input"] + max_tokens / 1_000_000 * price["output"]
    daily_limit = to_float(os.getenv("AI_ARENA_DAILY_USD_LIMIT") or os.getenv("OPENAI_DAILY_USD_LIMIT") or 0.75, 0.75)
    if est_cost > daily_limit:
        print(f"WARN single request estimated cost {est_cost:.4f} exceeds daily limit {daily_limit:.4f}; fallback")
        return None

    body = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": request_text},
        ],
        "temperature": 0.72,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            data = json.loads(res.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
        print(f"WARN OpenAI discussion call failed: {exc}")
        return None


def agent_configs(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [a for a in (config.get("agents") or []) if a.get("enabled", True)]


def agent_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a.get("id"): a for a in agent_configs(config) if a.get("id")}


def memory_by_id(memory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a.get("agent_id"): a for a in (memory.get("agents") or []) if a.get("agent_id")}


def ranking_agents(ranking: dict[str, Any]) -> list[dict[str, Any]]:
    return ranking.get("agents") or []


def positions_agents(positions: dict[str, Any]) -> list[dict[str, Any]]:
    return positions.get("agents") or []


def make_voice_cards(config: dict[str, Any], agent_ids: list[str] | None = None) -> list[dict[str, Any]]:
    ids = set(agent_ids or [])
    cards = []
    for a in agent_configs(config):
        if ids and a.get("id") not in ids:
            continue
        voice = a.get("voice") or {}
        cards.append({
            "agent_id": a.get("id"),
            "agent_name": a.get("name"),
            "style_label": a.get("style_label") or a.get("screening_profile"),
            "voice_card": (
                f"{a.get('name')}: {voice.get('personality_short') or a.get('personality')}. "
                f"Role: {voice.get('debate_role')}. Style: {voice.get('sentence_style')}. "
                f"Catchphrase may appear rarely: {voice.get('catchphrase')}."
            ),
            "speak_weight": voice.get("speak_weight", 1.0),
        })
    return cards


def make_memory_cards(memory: dict[str, Any], agent_ids: list[str] | None = None) -> list[dict[str, Any]]:
    ids = set(agent_ids or [])
    cards = []
    for a in memory.get("agents", []):
        if ids and a.get("agent_id") not in ids:
            continue
        cards.append({
            "agent_id": a.get("agent_id"),
            "agent_name": a.get("agent_name"),
            "mood": a.get("mood"),
            "yesterday_summary": a.get("yesterday_summary"),
            "lesson": a.get("lesson"),
            "today_bias": a.get("today_bias"),
            "memory_line": a.get("memory_line"),
        })
    return cards


def agent_identity_maps(config: dict[str, Any]) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    name_by_id: dict[str, str] = {"market_master": "Market Master"}
    avatar_by_id: dict[str, dict[str, Any]] = {"market_master": {"avatar_style": "pixel_master", "avatar_image": None}}
    for a in agent_configs(config):
        aid = a.get("id")
        if not aid:
            continue
        name_by_id[aid] = a.get("name") or aid
        avatar_by_id[aid] = {"avatar_style": a.get("avatar_style"), "avatar_image": a.get("avatar_image")}
    return name_by_id, avatar_by_id


def build_context(sim: dict[str, Any], positions: dict[str, Any], ranking: dict[str, Any], events: dict[str, Any], memory: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    ranks = ranking_agents(ranking)
    leader = ranks[0] if ranks else {}
    laggard = ranks[-1] if ranks else {}
    returns = [to_float(a.get("return_pct")) for a in ranks]
    spread = round((max(returns) - min(returns)), 4) if returns else None

    # theme exposure from open positions
    theme_map: dict[str, list[dict[str, Any]]] = {}
    top_positions: list[dict[str, Any]] = []
    for a in positions_agents(positions):
        for p in a.get("open_positions") or []:
            pp = dict(p)
            pp["agent_name"] = a.get("name")
            top_positions.append(pp)
            if p.get("theme"):
                theme_map.setdefault(p["theme"], []).append(pp)
    theme_exposure = [
        {
            "theme": theme,
            "positions": len(rows),
            "aggregate_unrealized_pct": round(sum(to_float(r.get("unrealized_return_pct")) for r in rows), 4),
        }
        for theme, rows in sorted(theme_map.items(), key=lambda kv: len(kv[1]), reverse=True)
    ]

    return {
        "range": sim.get("range"),
        "season": sim.get("season"),
        "diagnostics": sim.get("diagnostics"),
        "leader": leader,
        "laggard": laggard,
        "leader_laggard_spread_pct": spread,
        "ranking": ranks,
        "positions": positions_agents(positions),
        "top_open_positions": sorted(top_positions, key=lambda p: to_float(p.get("unrealized_return_pct")), reverse=True)[:12],
        "theme_exposure": theme_exposure[:8],
        "events": events.get("events") or [],
        "memory": memory.get("agents") or [],
        "news_rule": "No external news is supplied. Use only supplied simulation/ranking/position facts.",
        "disclaimer": (config.get("arena") or {}).get("disclaimer"),
    }


def select_discussion_events(context: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    lab = config.get("lab") or {}
    max_threads = int(os.getenv("AI_ARENA_MAX_DEBATE_THREADS") or lab.get("max_debate_threads") or 9)

    base_events = list(context.get("events") or [])

    # Add synthetic event types that are useful even when no fresh trade action exists.
    if context.get("leader"):
        base_events.append({
            "event_id": "market_master_opening",
            "event_type": "market_master_opening",
            "priority": 98,
            "topic": "Market Master opening: today’s Arena conflict",
            "agents_involved": ["market_master"],
            "facts": [
                f"Leader is {context['leader'].get('name')} with return {context['leader'].get('return_pct')}%.",
                f"Laggard is {context['laggard'].get('name')} with return {context['laggard'].get('return_pct')}%.",
                f"Leader-laggard spread is {context.get('leader_laggard_spread_pct')} percentage points.",
            ],
        })
        base_events.append({
            "event_id": "risk_budget",
            "event_type": "risk_budget",
            "priority": 84,
            "topic": "Risk budget and drawdown review",
            "agents_involved": ["risk_sentinel"],
            "facts": [
                f"{a.get('name')} return={a.get('return_pct')}%, max_drawdown={a.get('max_drawdown_pct')}%, open_positions={a.get('open_positions')}."
                for a in context.get("ranking", [])[:5]
            ],
        })
        base_events.append({
            "event_id": "forecast_challenge",
            "event_type": "forecast_challenge",
            "priority": 68,
            "topic": "Tomorrow’s condition check",
            "agents_involved": [a.get("agent_id") for a in context.get("ranking", [])[:5]],
            "facts": [
                "Agents should state conditional signals they want to see next. This is not a prediction.",
                "Use current positions, ranking, risk, and style-specific constraints.",
            ],
        })
        base_events.append({
            "event_id": "market_master_closing",
            "event_type": "market_master_closing",
            "priority": 60,
            "topic": "Market Master closing recap",
            "agents_involved": ["market_master"],
            "facts": [
                "Summarize the day’s LAB debate using only supplied Arena facts.",
            ],
        })

    # Daily vs Weekly is a persistent philosophical conflict.
    ids = {a.get("agent_id") for a in context.get("ranking", [])}
    if "daily_striker" in ids and "weekly_sage" in ids:
        base_events.append({
            "event_id": "daily_vs_weekly",
            "event_type": "daily_vs_weekly",
            "priority": 86,
            "topic": "KAKERU vs SATORI: speed versus persistence",
            "agents_involved": ["daily_striker", "weekly_sage", "risk_sentinel", "contrarian_monk"],
            "facts": [
                "KAKERU represents daily momentum timing.",
                "SATORI represents weekly trend persistence.",
                "Debate should compare time horizon, follow-through, and holding period.",
            ],
        })

    # Convert event list to stable unique list.
    seen = set()
    unique = []
    for e in sorted(base_events, key=lambda x: int(x.get("priority") or 0), reverse=True):
        eid = e.get("event_id") or e.get("topic")
        if eid in seen:
            continue
        seen.add(eid)
        unique.append(e)

    return unique[:max_threads]


def target_messages_for_event(event: dict[str, Any], config: dict[str, Any]) -> int:
    lab = config.get("lab") or {}
    important = int(os.getenv("AI_ARENA_IMPORTANT_THREAD_MESSAGES") or lab.get("important_thread_messages") or 16)
    normal = int(os.getenv("AI_ARENA_NORMAL_THREAD_MESSAGES") or lab.get("normal_thread_messages") or 12)
    light = 5
    etype = event.get("event_type")
    if etype in {"trade_event", "shared_position", "daily_vs_weekly", "leaderboard"}:
        return important
    if etype in {"market_master_opening", "market_master_closing"}:
        return light
    return normal


def build_thread_prompt(event: dict[str, Any], context: dict[str, Any], config: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    agent_ids = [a for a in (event.get("agents_involved") or []) if a]
    if "market_master" not in agent_ids and event.get("event_type") in {"market_master_opening", "market_master_closing"}:
        agent_ids.append("market_master")
    # Keep full cast available for debate if event is broad.
    if len(agent_ids) < 3 and event.get("event_type") not in {"market_master_opening", "market_master_closing"}:
        agent_ids.extend([a.get("agent_id") for a in context.get("ranking", [])[:5] if a.get("agent_id")])
    # de-dupe
    seen = set()
    agent_ids = [x for x in agent_ids if not (x in seen or seen.add(x))]

    return {
        "thread_event": event,
        "target_messages": target_messages_for_event(event, config),
        "ranking_snapshot": context.get("ranking", [])[:5],
        "top_open_positions": context.get("top_open_positions", [])[:8],
        "theme_exposure": context.get("theme_exposure", [])[:5],
        "voice_cards": make_voice_cards(config, agent_ids if agent_ids else None),
        "memory_cards": make_memory_cards(memory, agent_ids if agent_ids else None),
        "rules": {
            "not_investment_advice": True,
            "no_external_news": True,
            "no_fundamentals_or_earnings_unless_provided": True,
            "use_catchphrases_sparingly": "At most one catchphrase in this thread.",
            "naturalness": "Short reactions are allowed. Do not turn every line into a research paragraph.",
            "progression": [
                "State the conflict.",
                "Let the involved agent defend or explain the action.",
                "Let at least two agents challenge it from their own framework.",
                "Include one counter-rebuttal.",
                "Include one risk, position-sizing, drawdown, or liquidity comment.",
                "End with a forward-looking condition, not a prediction.",
            ],
        },
    }



def symbol_name_map_from_context(context: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in context.get("top_open_positions", []) or []:
        if p.get("symbol") and p.get("name"):
            out[str(p["symbol"])] = str(p["name"])
    for agent in context.get("positions", []) or []:
        for pos in agent.get("open_positions", []) or []:
            if pos.get("symbol") and pos.get("name"):
                out[str(pos["symbol"])] = str(pos["name"])
    for e in context.get("events", []) or []:
        if e.get("symbol") and e.get("name"):
            out[str(e["symbol"])] = str(e["name"])
    return out


def unique_body_key(body: str) -> str:
    return re.sub(r"[^a-z0-9.%]+", " ", str(body or "").lower()).strip()[:180]

def fallback_thread(event: dict[str, Any], context: dict[str, Any], config: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    """Fact-based fallback with real thread progression.

    The previous fallback could repeat the same generic line across agents.
    This version builds topic-specific exchanges so the LAB remains usable when
    OpenAI is disabled or a thread fails validation.
    """
    name_by_id, avatar_by_id = agent_identity_maps(config)
    ranks = context.get("ranking", [])[:5]
    leader = context.get("leader") or (ranks[0] if ranks else {})
    laggard = context.get("laggard") or (ranks[-1] if ranks else {})
    involved = [x for x in (event.get("agents_involved") or []) if x in name_by_id]
    if not involved:
        involved = [a.get("agent_id") for a in ranks if a.get("agent_id")] or ["market_master"]

    mem = memory_by_id(memory)
    symbol_names = symbol_name_map_from_context(context)
    messages: list[dict[str, Any]] = []
    used_bodies: set[str] = set()

    def add(aid: str, body: str, typ: str = "debate", symbol: str | None = None, theme: str | None = None) -> None:
        body = safe_text(body, 320)
        if not body:
            return
        key = unique_body_key(body)
        if key in used_bodies:
            return
        used_bodies.add(key)
        meta = avatar_by_id.get(aid) or {}
        messages.append({
            "agent_id": aid,
            "agent_name": name_by_id.get(aid, aid),
            "avatar_style": meta.get("avatar_style"),
            "avatar_image": meta.get("avatar_image"),
            "type": typ,
            "body": body,
            "linked_symbol": symbol,
            "linked_name": symbol_names.get(symbol or ""),
            "linked_theme": theme,
        })

    def rank_row(agent_id: str) -> dict[str, Any]:
        return next((r for r in ranks if r.get("agent_id") == agent_id), {})

    def largest_position(agent_id: str | None = None, reverse: bool = True) -> dict[str, Any]:
        rows = []
        for p in context.get("top_open_positions", []) or []:
            if agent_id and p.get("agent_id") != agent_id and p.get("agent_name") != name_by_id.get(agent_id):
                continue
            rows.append(p)
        if not rows:
            return {}
        return sorted(rows, key=lambda x: to_float(x.get("unrealized_return_pct")), reverse=reverse)[0]

    etype = event.get("event_type")
    facts = event.get("facts") or []

    if etype == "market_master_opening":
        add("market_master", f"LAB opens with {leader.get('name')} leading at {fmt_pct(leader.get('return_pct'))} and {laggard.get('name')} under pressure at {fmt_pct(laggard.get('return_pct'))}. The question is where the return is really coming from.", "market_master")
        add("risk_sentinel", f"The spread is {fmt_pct(context.get('leader_laggard_spread_pct'))}. I care less about the headline rank and more about concentration, drawdown, and whether the book can survive another session.", "risk_check")
        if leader.get("agent_id"):
            add(leader["agent_id"], f"Rank #{leader.get('rank')} is earned only if the process keeps paying. A lead without repeatability is just a mark-to-market trophy.", "ranking_reaction")

    elif etype == "leaderboard":
        add("risk_sentinel", f"{leader.get('name')} leads at {fmt_pct(leader.get('return_pct'))}, but the leaderboard is not proof of diversified alpha. Show me the drawdown path and the position that carried it.", "risk_check")
        lp = largest_position(leader.get("agent_id")) or largest_position()
        if lp:
            add(leader.get("agent_id"), f"The book is being carried by {lp.get('symbol')} at {fmt_pct(lp.get('unrealized_return_pct'))} after {lp.get('holding_days', 'n/a')} days. I will defend that only while the structure holds.", "portfolio_review", lp.get("symbol"), lp.get("theme"))
        add(laggard.get("agent_id"), f"Rank #{laggard.get('rank')} at {fmt_pct(laggard.get('return_pct'))} is not an excuse. My process has to prove the next entry is cleaner than the last one.", "ranking_reaction")
        add("contrarian_monk", "A leaderboard can seduce the room. I prefer the moment after the applause, when the second entry becomes cheaper and quieter.", "challenge")

    elif etype == "shared_position":
        sym = event.get("symbol")
        theme = event.get("theme")
        add("market_master", f"Shared battlefield: {sym}. Same ticker, different thesis. That is where this LAB becomes more than a return table.", "shared_position", sym, theme)
        if involved:
            add(involved[0], f"I hold {sym} through my own clock. The same symbol can be trend persistence for one agent and discovery risk for another.", "shared_position", sym, theme)
        if len(involved) > 1:
            add(involved[1], f"Agreed on the symbol, not necessarily on the reason. My edge is the setup that appeared before consensus made it comfortable.", "shared_position", sym, theme)
        add("risk_sentinel", f"Two agents sharing {sym} improves the story but raises correlation risk. Position sizing matters more when everyone can be wrong together.", "risk_check", sym, theme)
        add("contrarian_monk", f"When different frameworks crowd the same {sym}, I wait. Crowded conviction is not edge; it is an entry tax.", "challenge", sym, theme)

    elif etype == "why_no_trade":
        aid = involved[0]
        rr = rank_row(aid)
        add(aid, f"No position is not empty. With rank #{rr.get('rank', 'n/a')} and {fmt_pct(rr.get('return_pct'))} return, unused cash is part of the strategy until the setup pays for risk.", "why_no_trade")
        add("risk_sentinel", "Cash is not a failure when the signal quality does not compensate for drawdown risk. The book does not need to swing at every candle.", "risk_check")
        add("contrarian_monk", "I do not move because the room is bored. I wait for the second entry, when the first wave has stopped forcing the trade.", "why_no_trade")

    elif etype == "trade_event":
        aid = involved[0]
        sym = event.get("symbol")
        action = (event.get("action") or {}).get("action") or event.get("event_type")
        add(aid, f"The {action} in {sym} came from the simulation rule, not impulse. Now the position has to prove follow-through, holding quality, and risk budget.", "trade_event", sym, event.get("theme"))
        add("risk_sentinel", f"{sym} is not validated by entry alone. The next test is survivability: liquidity, drawdown, and whether the mark still makes sense after the first reaction.", "risk_check", sym, event.get("theme"))
        add("weekly_sage", f"If {sym} cannot persist beyond the first signal window, I do not treat it as structure. One trigger is not a trend.", "timeframe", sym, event.get("theme"))
        add("contrarian_monk", f"I will not chase the first print in {sym}. If the thesis is real, the second entry will still be there after the heat fades.", "challenge", sym, event.get("theme"))

    elif etype == "daily_vs_weekly":
        add("daily_striker", "I move when pressure arrives. Waiting for every confirmation means arriving after the edge is priced. Price moved first.", "timeframe")
        add("weekly_sage", "One candle is not a thesis. If the trend cannot persist, speed becomes noise rather than a repeatable book.", "timeframe")
        add("risk_sentinel", "Both clocks can be right and still lose money if sizing ignores volatility. Time horizon is not a substitute for risk budget.", "risk_check")
        add("contrarian_monk", "The first move belongs to the impatient. I wait for the second entry, when the crowd has already revealed itself.", "timeframe")

    elif etype == "theme_heat":
        theme = event.get("theme") or ((context.get("theme_exposure") or [{}])[0].get("theme"))
        add("market_master", f"Theme heat is visible in {theme or 'the current book'}, but heat is not diversification. The LAB needs to separate exposure from edge.", "theme_exposure", None, theme)
        add("discovery_scout", f"A theme becomes interesting before it becomes obvious. My job is to find the signal while it is still off-screen, not after the label is crowded.", "theme_exposure", None, theme)
        add("risk_sentinel", f"Theme concentration can lift the book and still increase fragility. If the theme rolls over, correlation does the damage quickly.", "risk_check", None, theme)
        add("contrarian_monk", "When a theme gets too easy to explain, I become more interested in the exit than the entry.", "challenge", None, theme)

    elif etype == "forecast_challenge":
        add("market_master", "Next session is not a prediction problem. It is a condition check: which agents can define what would invalidate their current stance?", "forecast_challenge")
        add("daily_striker", "I need follow-through. If the tape cannot confirm pressure, speed becomes a liability instead of an edge.", "forecast_challenge")
        add("weekly_sage", "I need structure to remain intact. A pullback is acceptable; a broken trend is not.", "forecast_challenge")
        add("risk_sentinel", "I need the book to survive volatility without pretending that return alone solves drawdown.", "forecast_challenge")
        add("contrarian_monk", "I need the room to get too certain. That is when waiting starts to pay.", "forecast_challenge")

    elif etype == "market_master_closing":
        add("market_master", f"Closing note: {leader.get('name')} still owns the scoreboard, but tomorrow’s LAB will ask whether that lead is process, concentration, or timing luck.", "market_master")
        add("market_master", "No external news was used. The argument stays inside simulated positions, rankings, memory, and risk budget.", "market_master")

    else:
        aid = involved[0]
        fact = facts[0] if facts else event.get("topic", "The Arena has a new point to debate.")
        add(aid, f"{fact} The useful question is not whether it sounds convincing, but whether it improves the book after risk.", "debate")

    # Add memory and style-based counterpoints without repeating the same sentence.
    target = min(max(target_messages_for_event(event, config), len(messages)), 18)
    style_lines = {
        "daily_striker": [
            "No follow-through, no edge. I would rather be early and wrong than late and decorative.",
            "The tape already voted once. Now I need it to vote twice.",
        ],
        "weekly_sage": [
            "The trend pays the patient, but only if patience does not become denial.",
            "I do not need the loudest candle. I need structure that keeps compounding.",
        ],
        "risk_sentinel": [
            "Risk budget is not decoration. If the position cannot survive the next session, the thesis is too expensive.",
            "Survival is alpha when the rest of the room is trading ego.",
        ],
        "discovery_scout": [
            "The edge hides off-screen, but hidden does not mean careless. Discovery still has to clear liquidity.",
            "Not every signal starts in the large caps. Some of the map is still dark.",
        ],
        "contrarian_monk": [
            "Cash is also a position. I am not late; I am refusing the crowded first entry.",
            "I wait for the second entry. The first one usually charges too much emotion.",
        ],
    }
    cast = [aid for aid in involved if aid in name_by_id]
    if not cast:
        cast = [a.get("agent_id") for a in ranks if a.get("agent_id")] or ["market_master"]
    cursor = 0
    while len(messages) < target:
        aid = cast[cursor % len(cast)]
        cursor += 1
        m = mem.get(aid) or {}
        if m and len(messages) % 4 == 0 and (m.get("memory_line") or m.get("lesson")):
            body = m.get("memory_line") or m.get("lesson")
            typ = "memory"
        else:
            lines = style_lines.get(aid) or [f"{name_by_id.get(aid, aid)} keeps the process tied to the current Arena facts."]
            body = lines[(cursor + len(messages)) % len(lines)]
            typ = "ambient"
        add(aid, body, typ)
        # Prevent infinite loops if all candidate lines were duplicates.
        if cursor > 60:
            break

    return {
        "thread_id": event.get("event_id") or f"thread_{event.get('event_type')}",
        "thread_type": event.get("event_type") or "debate",
        "title": event.get("topic") or "Arena thread",
        "priority": event.get("priority", 50),
        "source_event": event,
        "messages": messages[:target],
        "fallback_used": True,
    }

def call_thread_ai(event: dict[str, Any], context: dict[str, Any], config: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    model = os.getenv("OPENAI_MODEL_MINI") or (config.get("arena") or {}).get("default_model") or "gpt-4o-mini"
    prompt = build_thread_prompt(event, context, config, memory)

    system = """
You generate ONE thread for Neon Tokyo AI Arena LAB.

Identity:
- The speakers are professional synthetic portfolio managers.
- The scene is a retro-neon investment arena, but the content must be institutionally sharp.
- Use only provided simulation facts, ranking, positions, events, Agent Voice Cards, and Memory Cards.

Output valid JSON:
{
  "thread": {
    "thread_id": string,
    "thread_type": string,
    "title": string,
    "messages": [
      {
        "agent_id": string,
        "type": string,
        "body": string,
        "linked_symbol": string|null,
        "linked_theme": string|null
      }
    ]
  }
}

Message rules:
- Generate the requested number of messages unless the thread is Market Master only.
- Do not over-constrain the conversation: short reactions, irony, and memory references are allowed.
- At least one concrete fact must appear in the thread: rank, return, drawdown, position, symbol, holding days, cash, theme, or event trigger.
- Every 2-3 messages should add a new angle: risk, time horizon, position sizing, memory, crowding, or next condition.
- Agent voices must differ, but analysis comes before catchphrases.
- At most one catchphrase in the thread.
- Memory should shape tone naturally. Do not force every agent to mention yesterday.
- No external news, macro/geopolitics, earnings, fundamentals, guidance, target prices, or recommendations.
- Do not use buy/sell/recommendation language.
- Keep each body under 260 characters.
"""
    result = call_openai_json(model, system, prompt, int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "7000")))
    if not result or not isinstance(result.get("thread"), dict):
        return fallback_thread(event, context, config, memory)

    thread = result["thread"]
    messages = thread.get("messages")
    if not isinstance(messages, list) or len(messages) < 3:
        return fallback_thread(event, context, config, memory)

    name_by_id, avatar_by_id = agent_identity_maps(config)
    allowed_agents = set(name_by_id.keys())
    allowed_symbols = {p.get("symbol") for p in context.get("top_open_positions", []) if p.get("symbol")}
    if event.get("symbol"):
        allowed_symbols.add(event.get("symbol"))
    allowed_themes = {t.get("theme") for t in context.get("theme_exposure", []) if t.get("theme")}
    if event.get("theme"):
        allowed_themes.add(event.get("theme"))

    clean: list[dict[str, Any]] = []
    for row in messages[:24]:
        if not isinstance(row, dict):
            continue
        aid = row.get("agent_id")
        if aid not in allowed_agents:
            continue
        body = safe_text(row.get("body"), 300)
        if not body:
            continue
        lower = body.lower()
        if any(b in lower for b in BANNED_SUBSTRINGS):
            continue
        linked_symbol = row.get("linked_symbol")
        if linked_symbol not in allowed_symbols:
            linked_symbol = None
        linked_theme = row.get("linked_theme")
        if linked_theme not in allowed_themes:
            linked_theme = None
        meta = avatar_by_id.get(aid) or {}
        clean.append({
            "agent_id": aid,
            "agent_name": name_by_id.get(aid, aid),
            "avatar_style": meta.get("avatar_style"),
            "avatar_image": meta.get("avatar_image"),
            "type": row.get("type") or event.get("event_type") or "debate",
            "body": body,
            "linked_symbol": linked_symbol,
            "linked_name": symbol_name_map_from_context(context).get(linked_symbol or ""),
            "linked_theme": linked_theme,
        })

    # Minimal guard: if the thread lost all substance, use fallback.
    has_fact = any(re.search(r"\d|\.T|rank|Rank|return|drawdown|position|cash|P/L", m.get("body", ""), re.I) for m in clean)
    if len(clean) < 3 or not has_fact:
        return fallback_thread(event, context, config, memory)

    return {
        "thread_id": thread.get("thread_id") or event.get("event_id"),
        "thread_type": thread.get("thread_type") or event.get("event_type"),
        "title": safe_text(thread.get("title") or event.get("topic"), 140),
        "priority": event.get("priority", 50),
        "source_event": event,
        "messages": clean,
        "fallback_used": False,
    }


def fallback_brief(context: dict[str, Any]) -> dict[str, str]:
    leader = context.get("leader") or {}
    laggard = context.get("laggard") or {}
    return {
        "analyst_id": "market_master",
        "title": "AI Arena LAB",
        "body": f"{leader.get('name', 'The leader')} controls the season at {fmt_pct(leader.get('return_pct'))}, while {laggard.get('name', 'the laggard')} is under pressure at {fmt_pct(laggard.get('return_pct'))}. Today’s LAB focuses on ranking spread, open positions, memory, and risk budget.",
        "risk_note": "No external news is supplied. All debate is based on simulated positions and rankings only.",
    }


def maybe_ai_brief(context: dict[str, Any], config: dict[str, Any]) -> dict[str, str]:
    model = os.getenv("OPENAI_MODEL_MINI") or (config.get("arena") or {}).get("default_model") or "gpt-4o-mini"
    system = """
Generate a concise Market Master brief for Neon Tokyo AI Arena LAB.
Use only supplied facts. No external news, fundamentals, earnings, guidance, target prices, or recommendations.
Return JSON: {"title": string, "body": string, "risk_note": string}
"""
    payload = {
        "leader": context.get("leader"),
        "laggard": context.get("laggard"),
        "spread_pct": context.get("leader_laggard_spread_pct"),
        "top_open_positions": context.get("top_open_positions")[:5],
        "theme_exposure": context.get("theme_exposure")[:5],
    }
    res = call_openai_json(model, system, payload, 1200)
    if not res:
        return fallback_brief(context)
    return {
        "analyst_id": "market_master",
        "title": safe_text(res.get("title"), 90) or "AI Arena LAB",
        "body": safe_text(res.get("body"), 520) or fallback_brief(context)["body"],
        "risk_note": safe_text(res.get("risk_note"), 300) or fallback_brief(context)["risk_note"],
    }


def fixed_leader_lines(context: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    leader = context.get("leader") or {}
    aid = leader.get("agent_id")
    if not aid:
        return []
    agents = agent_by_id(config)
    agent = agents.get(aid) or {}
    fixed = agent.get("fixed_lines") or {}
    name_by_id, avatar_by_id = agent_identity_maps(config)
    meta = avatar_by_id.get(aid) or {}
    rows = []
    for typ, key in [("leader_open_line", "market_open_leader"), ("leader_close_line", "market_close_leader")]:
        choices = fixed.get(key) or []
        if not choices:
            continue
        body = choices[0]
        rows.append({
            "agent_id": aid,
            "agent_name": name_by_id.get(aid, aid),
            "avatar_style": meta.get("avatar_style"),
            "avatar_image": meta.get("avatar_image"),
            "type": typ,
            "body": body,
            "linked_symbol": None,
            "linked_theme": None,
            "fixed_line": True,
        })
    return rows


def ambient_lines(context: dict[str, Any], config: dict[str, Any], memory: dict[str, Any], needed: int) -> list[dict[str, Any]]:
    """Generate varied low-intensity LAB chatter for 24h coverage."""
    if needed <= 0:
        return []
    name_by_id, avatar_by_id = agent_identity_maps(config)
    mem = memory_by_id(memory)
    ranks = context.get("ranking", [])[:5]
    positions = context.get("top_open_positions", []) or []
    themes = context.get("theme_exposure", []) or []
    leader = context.get("leader") or (ranks[0] if ranks else {})
    laggard = context.get("laggard") or (ranks[-1] if ranks else {})
    rank_by_id = {r.get("agent_id"): r for r in ranks if r.get("agent_id")}
    pos_cycle = positions or [{}]
    theme_cycle = themes or [{}]

    openers = {
        "daily_striker": [
            "I need the next print to confirm pressure",
            "The daily clock is brutal",
            "Speed only matters when it repeats",
            "The tape already voted once",
            "A fast trigger has to earn the second candle",
            "I do not defend motion without continuation",
        ],
        "weekly_sage": [
            "The book does not need drama",
            "One session can lie",
            "Trend persistence is the real audit",
            "I do not need the loudest candle",
            "Time is part of the edge",
            "The weekly structure has to keep absorbing volatility",
        ],
        "risk_sentinel": [
            "The scoreboard is secondary",
            "Risk budget is not decoration",
            "A good idea can still be bad sizing",
            "The mark has to survive volatility",
            "Return without drawdown context is incomplete",
            "Liquidity decides whether the thesis is tradable",
        ],
        "discovery_scout": [
            "The obvious names are rarely the whole map",
            "Discovery begins before consensus",
            "The edge hides off-screen",
            "Small signals need liquidity discipline",
            "The first clue is rarely comfortable",
            "I am looking where the screen is still dark",
        ],
        "contrarian_monk": [
            "Cash is also a position",
            "I wait for the second entry",
            "The loudest move usually charges emotion",
            "Crowded conviction is not edge",
            "Patience is not inactivity",
            "The room gets interesting after the first applause",
        ],
    }
    tails = [
        "while {leader} holds the crown at {leader_ret}.",
        "because {laggard} shows what failed follow-through costs at {laggard_ret}.",
        "and {sym} is the live tape I keep testing at {pnl}.",
        "with {theme} still shaping the Arena's exposure.",
        "but rank #{rank} / {ret} is only a mark, not a verdict.",
        "so the next condition matters more than the last headline.",
        "and the book has to prove it can survive another rebalance.",
        "without pretending that one position is diversification.",
        "before the next trigger spends more risk budget.",
        "while the LAB separates process from noise.",
    ]

    out: list[dict[str, Any]] = []
    used: set[str] = set()
    agents = [a for a in agent_configs(config) if a.get("id") in openers]
    if not agents:
        return []
    idx = 0
    safety = 0
    while len(out) < needed and safety < needed * 50:
        safety += 1
        a = agents[idx % len(agents)]
        aid = a.get("id")
        rr = rank_by_id.get(aid) or {}
        pos = pos_cycle[(idx + len(out)) % len(pos_cycle)]
        theme = theme_cycle[(idx * 2 + len(out)) % len(theme_cycle)]
        op = openers[aid][(idx // len(agents) + len(out)) % len(openers[aid])]
        tail = tails[(idx + len(out) * 3) % len(tails)]
        body = f"{op}, " + tail.format(
            leader=leader.get("name", "the leader"),
            leader_ret=fmt_pct(leader.get("return_pct")),
            laggard=laggard.get("name", "the laggard"),
            laggard_ret=fmt_pct(laggard.get("return_pct")),
            rank=rr.get("rank", "—"),
            ret=fmt_pct(rr.get("return_pct")),
            sym=pos.get("symbol") or "the next setup",
            pnl=fmt_pct(pos.get("unrealized_return_pct")),
            theme=theme.get("theme") or "today's strongest theme",
        )
        if len(out) % 13 == 0 and (mem.get(aid) or {}).get("memory_line"):
            body = f"{(mem.get(aid) or {}).get('memory_line')} That memory still changes how I read this tape."
        key = unique_body_key(body)
        if key in used:
            idx += 1
            continue
        used.add(key)
        meta = avatar_by_id.get(aid) or {}
        out.append({
            "agent_id": aid,
            "agent_name": name_by_id.get(aid, aid),
            "avatar_style": meta.get("avatar_style"),
            "avatar_image": meta.get("avatar_image"),
            "type": "ambient",
            "body": safe_text(body, 280),
            "linked_symbol": pos.get("symbol") if pos.get("symbol") and len(out) % 4 == 0 else None,
            "linked_name": pos.get("name") if pos.get("symbol") and len(out) % 4 == 0 else None,
            "linked_theme": theme.get("theme") if len(out) % 5 == 0 else None,
        })
        idx += 1
    # If the unique pool is exhausted, extend with numbered LAB pulse lines.
    # These are intentionally short and factual, so fallback mode still fills
    # the 24h schedule without repeating the exact same sentence.
    pulse_templates = {
        "daily_striker": "LAB pulse {n}: I still need follow-through before I trust the next daily trigger.",
        "weekly_sage": "LAB pulse {n}: I am watching whether structure survives the next rebalance.",
        "risk_sentinel": "LAB pulse {n}: The book still has to justify risk before it celebrates return.",
        "discovery_scout": "LAB pulse {n}: The map is not finished; one quiet setup can change the board.",
        "contrarian_monk": "LAB pulse {n}: Waiting remains a position until the crowd offers a better entry.",
    }
    fill_idx = 0
    while len(out) < needed and agents:
        a = agents[fill_idx % len(agents)]
        aid = a.get("id")
        pos = pos_cycle[(fill_idx + len(out)) % len(pos_cycle)]
        meta = avatar_by_id.get(aid) or {}
        body = pulse_templates.get(aid, "LAB pulse {n}: The Arena keeps testing process against noise.").format(n=len(out) + 1)
        out.append({
            "agent_id": aid,
            "agent_name": name_by_id.get(aid, aid),
            "avatar_style": meta.get("avatar_style"),
            "avatar_image": meta.get("avatar_image"),
            "type": "ambient",
            "body": safe_text(body, 260),
            "linked_symbol": pos.get("symbol") if pos.get("symbol") and len(out) % 6 == 0 else None,
            "linked_name": pos.get("name") if pos.get("symbol") and len(out) % 6 == 0 else None,
            "linked_theme": None,
        })
        fill_idx += 1
    return out

def schedule_feed(messages: list[dict[str, Any]], config: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    lab = config.get("lab") or {}
    min_interval = int(os.getenv("AI_ARENA_MIN_INTERVAL_MINUTES") or lab.get("min_interval_minutes") or 5)
    max_interval = int(os.getenv("AI_ARENA_MAX_INTERVAL_MINUTES") or lab.get("max_interval_minutes") or 10)
    target_min = int(os.getenv("AI_ARENA_TARGET_FEED_MIN") or lab.get("target_feed_min") or 160)
    target_max = int(os.getenv("AI_ARENA_TARGET_FEED_MAX") or lab.get("target_feed_max") or 220)
    reset_timeline = str(os.getenv("AI_ARENA_RESET_TIMELINE", "false")).lower() in {"1", "true", "yes", "on"}
    backfill_minutes = int(os.getenv("AI_ARENA_BACKFILL_MINUTES") or lab.get("backfill_minutes") or 180)

    target = max(target_min, min(target_max, len(messages)))
    if len(messages) < target_min and str(os.getenv("AI_ARENA_ALLOW_AMBIENT_LINES", lab.get("allow_ambient_lines", True))).lower() != "false":
        target = len(messages)

    # Reset mode intentionally uses the current run timestamp as part of the
    # seed.  This lets a manual Action rebuild create a fresh 24h broadcast
    # timeline that starts a few hours before "now" and continues forward.
    now = now_jst().replace(second=0, microsecond=0)
    if reset_timeline:
        seed = f"reset|{now.isoformat()}|{context.get('season')}|{len(messages)}"
        start = now - timedelta(minutes=backfill_minutes)
    else:
        seed = f"stable|{context.get('season')}|{(context.get('range') or {}).get('end_date')}|{len(messages)}"
        start = now - timedelta(minutes=30)
    rng = random.Random(seed)

    scheduled = []
    current = start
    idx = 0
    for row in messages:
        if len(scheduled) >= target:
            break
        idx += 1
        if idx == 1:
            current = start
        else:
            current += timedelta(minutes=rng.randint(min_interval, max_interval))
        item = dict(row)
        item["id"] = f"feed_{idx:03d}"
        item["show_at"] = iso_jst(current)
        scheduled.append(item)
    return scheduled

def build_payload(config: dict[str, Any], sim: dict[str, Any], positions: dict[str, Any], ranking: dict[str, Any], events: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    context = build_context(sim, positions, ranking, events, memory, config)
    selected_events = select_discussion_events(context, config)

    threads = []
    ai_thread_count = 0
    fallback_thread_count = 0
    for event in selected_events:
        thread = call_thread_ai(event, context, config, memory)
        if thread.get("fallback_used"):
            fallback_thread_count += 1
        else:
            ai_thread_count += 1
        threads.append(thread)

    messages: list[dict[str, Any]] = []
    # Opening leader line should be near the top but not replace Market Master.
    fixed = fixed_leader_lines(context, config)
    if fixed[:1]:
        messages.extend(fixed[:1])

    for thread in sorted(threads, key=lambda x: int(x.get("priority") or 0), reverse=True):
        messages.extend(thread.get("messages") or [])

    if fixed[1:]:
        messages.extend(fixed[1:])

    lab = config.get("lab") or {}
    target_min = int(os.getenv("AI_ARENA_TARGET_FEED_MIN") or lab.get("target_feed_min") or 160)
    if len(messages) < target_min:
        messages.extend(ambient_lines(context, config, memory, target_min - len(messages)))

    feed = schedule_feed(messages, config, context)
    brief = maybe_ai_brief(context, config)

    return {
        "schema_version": "neon_tokyo_ai_arena_lab_v3",
        "generated_at": iso_jst(now_jst()),
        "market": "Japan",
        "timezone": "Asia/Tokyo",
        "season": sim.get("season"),
        "range": sim.get("range"),
        "ai": {
            "enabled": ai_enabled(),
            "model": os.getenv("OPENAI_MODEL_MINI", "gpt-4o-mini"),
            "status": "ok_lab_v3" if ai_thread_count else "fallback_lab_v3",
            "fallback_used": ai_thread_count == 0,
            "ai_threads": ai_thread_count,
            "fallback_threads": fallback_thread_count,
            "external_news_enabled": False,
            "debate_style": "threaded_lab_memory_feed",
        },
        "daily_brief": brief,
        "market_context": context,
        "discussion_events": selected_events,
        "threads": threads,
        "memory": memory,
        "agents": [
            {
                "agent_id": a.get("agent_id"),
                "name": a.get("name"),
                "class": a.get("class"),
                "selection_profile": a.get("selection_profile"),
                "style_label": a.get("style_label"),
                "ui_tone": a.get("ui_tone"),
                "avatar_style": a.get("avatar_style"),
                "avatar_image": a.get("avatar_image"),
                "summary": a.get("summary"),
                "open_positions": a.get("open_positions", [])[:4],
            }
            for a in positions.get("agents", [])
        ],
        "feed": feed,
        "ranking": ranking.get("agents", [])[:8],
        "disclaimer": (config.get("arena") or {}).get("disclaimer") or "Informational only. Not investment advice.",
    }


def main() -> None:
    config = read_yaml(AGENTS_YAML, {})
    sim = read_json(SIM_JSON, {})
    positions = read_json(POSITIONS_JSON, {})
    ranking = read_json(RANKING_JSON, {})
    events = read_json(EVENTS_JSON, {"events": []})
    memory = read_json(MEMORY_JSON, {"agents": []})

    if not sim or not positions or not ranking:
        raise SystemExit("Missing AI Arena simulation/positions/ranking JSON. Run rebuild_ai_arena_simulation_jp.py first.")

    payload = build_payload(config, sim, positions, ranking, events, memory)
    discussion_payload = {
        "schema_version": "ai_arena_discussion_threads_v3",
        "generated_at": payload["generated_at"],
        "season": payload.get("season"),
        "range": payload.get("range"),
        "ai": payload.get("ai"),
        "daily_brief": payload.get("daily_brief"),
        "discussion_events": payload.get("discussion_events"),
        "threads": payload.get("threads"),
        "feed": payload.get("feed"),
    }

    write_json(DISCUSSION_OUT, discussion_payload)
    write_json(LEGACY_OUT, payload)

    print(
        "AI Arena LAB discussion result:",
        f"status={payload['ai']['status']}",
        f"ai_threads={payload['ai']['ai_threads']}",
        f"fallback_threads={payload['ai']['fallback_threads']}",
        f"feed_lines={len(payload.get('feed') or [])}",
    )


if __name__ == "__main__":
    main()
