#!/usr/bin/env python3
from __future__ import annotations

"""Build GPT-4o powered AI Arena War Room / Arena Log payload.

This script is intentionally focused on content quality rather than trading logic.
It reads already-generated AI Arena JSON artifacts, compresses them into a factual
context pack, asks GPT-4o to write an English live chat between the seven agents,
and writes a static-site friendly payload for `/japan/ai-arena/log/`.

Key design decisions
--------------------
- GPT is mandatory by default.  The page is a generative-AI content product; a
  deterministic template fallback would make the conversation feel fake.
- GPT is not allowed to invent external news, target prices, or investment advice.
  The prompt supplies only simulation facts, and the output schema keeps every
  message attached to an evidence label.
- The browser reveals pre-generated messages at randomized 3-5 minute intervals.
  A static Vercel site cannot create new server-side messages every few minutes,
  so the script generates a conversation queue and the UI performs the live reveal.
- History is pruned to avoid repository bloat.

Required environment variables
------------------------------
OPENAI_API_KEY                        Required unless AI_ARENA_WAR_ROOM_ALLOW_FALLBACK=true
OUT_DIR                               Static site output directory. Default: site
AI_ARENA_WAR_ROOM_MODEL               Default: gpt-4o
AI_ARENA_WAR_ROOM_MESSAGES            Default: 34
AI_ARENA_WAR_ROOM_MIN_DELAY_SECONDS   Default: 180
AI_ARENA_WAR_ROOM_MAX_DELAY_SECONDS   Default: 300
AI_ARENA_WAR_ROOM_HISTORY_DAYS        Default: 14
AI_ARENA_WAR_ROOM_ALLOW_FALLBACK      Default: false. Emergency local-only fallback.
"""

import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()

BASE = OUT_DIR / "data" / "japan" / "ai-arena"
AGENTS_YAML = ROOT / "data" / "agents" / "jp_agents.yml"
JST = timezone(timedelta(hours=9))

MODEL = os.getenv("AI_ARENA_WAR_ROOM_MODEL", "gpt-4o")
MESSAGE_COUNT = int(os.getenv("AI_ARENA_WAR_ROOM_MESSAGES", "34"))
MIN_DELAY_SECONDS = int(os.getenv("AI_ARENA_WAR_ROOM_MIN_DELAY_SECONDS", "180"))
MAX_DELAY_SECONDS = int(os.getenv("AI_ARENA_WAR_ROOM_MAX_DELAY_SECONDS", "300"))
HISTORY_DAYS = int(os.getenv("AI_ARENA_WAR_ROOM_HISTORY_DAYS", "14"))
ALLOW_FALLBACK = os.getenv("AI_ARENA_WAR_ROOM_ALLOW_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}

CANONICAL_NAMES = {
    "daily_striker": "KYOU",
    "weekly_sage": "NAGARE",
    "risk_sentinel": "MAMORU",
    "discovery_scout": "SAGURI",
    "contrarian_monk": "MATSU",
    "reversal_snapback": "KAESHI",
    "value_mispricing": "HIZUMI",
}

CANONICAL_COLORS = {
    "daily_striker": "#FF4B5C",
    "weekly_sage": "#B779FF",
    "risk_sentinel": "#7DF9FF",
    "discovery_scout": "#5DFFB1",
    "contrarian_monk": "#FFD166",
    "reversal_snapback": "#FF4FD8",
    "value_mispricing": "#4F46E5",
}

AGENT_PERSONAS = {
    "daily_striker": {
        "name": "KYOU",
        "role": "momentum striker",
        "voice": "fast, sharp, aggressive, focused on price pressure and volume confirmation",
        "state": "SCANNING MOMENTUM",
    },
    "weekly_sage": {
        "name": "NAGARE",
        "role": "medium-term trend sage",
        "voice": "calm, structural, skeptical of one-day moves, obsessed with persistence",
        "state": "READING FLOW",
    },
    "risk_sentinel": {
        "name": "MAMORU",
        "role": "risk sentinel",
        "voice": "disciplined, protective, audits drawdown, liquidity, sizing, and failure modes",
        "state": "RISK GATE ACTIVE",
    },
    "discovery_scout": {
        "name": "SAGURI",
        "role": "small-cap discovery scout",
        "voice": "curious, early, hunts overlooked signals before they become obvious",
        "state": "HUNTING EARLY SIGNALS",
    },
    "contrarian_monk": {
        "name": "MATSU",
        "role": "patient pullback monk",
        "voice": "minimalist, patient, refuses bad entries, values waiting as a weapon",
        "state": "WAITING FOR PULLBACK",
    },
    "reversal_snapback": {
        "name": "KAESHI",
        "role": "oversold snapback hunter",
        "voice": "energetic, playful but precise, looks for stretched pressure and violent rebounds",
        "state": "SNAPBACK WATCH",
    },
    "value_mispricing": {
        "name": "HIZUMI",
        "role": "value distortion mathematician",
        "voice": "intellectual, exacting, searches for mispricing but rejects value traps",
        "state": "TESTING MISPRICING",
    },
}

BANNED_PATTERNS = [
    r"\bstrong buy\b",
    r"\bstrong sell\b",
    r"\btarget price\b",
    r"\bguaranteed\b",
    r"\beasy money\b",
    r"\byou should buy\b",
    r"\byou should sell\b",
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


def read_yaml(path: Path) -> dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"WARN failed to read YAML {path}: {exc}")
        return {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        rel = path.relative_to(ROOT)
    except Exception:
        rel = path
    print(f"Wrote {rel}")


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def fmt_pct(value: Any, digits: int = 2) -> str:
    return f"{to_float(value):+.{digits}f}%"


def fmt_jpy(value: Any) -> str:
    return f"¥{to_float(value):,.0f}"


def clean_text(text: Any, limit: int = 420) -> str:
    s = str(text or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\bKAKERU\b", "KYOU", s)
    s = re.sub(r"\bSATORI\b", "NAGARE", s)
    for pattern in BANNED_PATTERNS:
        s = re.sub(pattern, "", s, flags=re.I)
    return s[:limit].strip(" -—,:;.")


def agent_name(agent_id: str) -> str:
    return CANONICAL_NAMES.get(agent_id, agent_id.upper())


def agent_image(agent_id: str) -> str:
    return f"/assets/ai-arena/agents/{agent_id}.png"


def load_agents() -> list[dict[str, Any]]:
    raw_yaml = read_yaml(AGENTS_YAML).get("agents") or []
    raw_by_id = {str(a.get("agent_id") or a.get("id") or ""): a for a in raw_yaml if isinstance(a, dict)}
    agents: list[dict[str, Any]] = []
    for aid, persona in AGENT_PERSONAS.items():
        raw = raw_by_id.get(aid, {})
        agents.append({
            "agent_id": aid,
            "name": persona["name"],
            "role": raw.get("role") or raw.get("style_label") or persona["role"],
            "style_label": raw.get("style_label") or persona["role"],
            "description": raw.get("short_description") or raw.get("description") or persona["voice"],
            "voice": persona["voice"],
            "state": persona["state"],
            "image": raw.get("image") or raw.get("avatar_image") or agent_image(aid),
            "color": CANONICAL_COLORS[aid],
        })
    return agents


def normalize_ranking(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("ranking") or []
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        aid = str(row.get("agent_id") or row.get("agent", {}).get("agent_id") or "")
        if aid not in CANONICAL_NAMES:
            continue
        out.append({
            "rank": to_int(row.get("rank"), idx + 1),
            "agent_id": aid,
            "name": agent_name(aid),
            "return_pct": to_float(row.get("total_return_pct")),
            "return_label": fmt_pct(row.get("total_return_pct")),
            "equity_jpy": to_float(row.get("end_equity_jpy")),
            "equity_label": fmt_jpy(row.get("end_equity_jpy")),
            "max_drawdown_pct": to_float(row.get("max_drawdown_pct")),
            "mdd_label": fmt_pct(row.get("max_drawdown_pct")),
            "win_rate_pct": to_float(row.get("win_rate_pct")),
            "win_rate_label": fmt_pct(row.get("win_rate_pct")),
            "trade_count": to_int(row.get("trade_count") or row.get("closed_trades")),
            "open_count": to_int(row.get("open_count") or row.get("open_positions")),
        })
    return sorted(out, key=lambda x: x["rank"])


def normalize_positions(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    def one(row: dict[str, Any], is_open: bool) -> dict[str, Any]:
        aid = str(row.get("agent_id") or row.get("agent", {}).get("agent_id") or "")
        ticker = str(row.get("ticker") or row.get("symbol") or "")
        name = str(row.get("name") or row.get("company_name") or ticker)
        pnl = row.get("unrealized_return_pct") if is_open else row.get("return_pct")
        if pnl is None:
            pnl = row.get("unrealized_pnl_pct") if is_open else row.get("realized_pnl_pct")
        if pnl is None:
            pnl = row.get("pnl_pct")
        return {
            "agent_id": aid,
            "agent_name": agent_name(aid),
            "ticker": ticker,
            "name": name,
            "entry_date": str(row.get("entry_date") or row.get("date") or ""),
            "exit_date": str(row.get("exit_date") or ""),
            "holding_days": to_int(row.get("holding_days")),
            "entry_price": to_float(row.get("entry_price")),
            "last_price": to_float(row.get("last_price") or row.get("exit_price")),
            "pnl_pct": to_float(pnl),
            "pnl_label": fmt_pct(pnl),
            "reason": str(row.get("exit_reason") or row.get("reason_code") or row.get("reason") or ""),
        }
    open_positions = [one(x, True) for x in payload.get("open_positions", []) if isinstance(x, dict)]
    closed_trades = [one(x, False) for x in payload.get("closed_trades", []) if isinstance(x, dict)]
    return open_positions, closed_trades, payload.get("portfolio") or {}


def normalize_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("events") if isinstance(payload, dict) else []
    events: list[dict[str, Any]] = []
    for idx, row in enumerate(raw or []):
        if not isinstance(row, dict):
            continue
        aid = str(row.get("agent_id") or "")
        if aid not in CANONICAL_NAMES:
            continue
        side = str(row.get("side") or row.get("badge") or "").upper()
        badge = "IN" if side in {"BUY", "IN"} else "OUT" if side in {"SELL", "OUT"} else str(row.get("badge") or "")
        events.append({
            "event_id": str(row.get("event_id") or f"event-{idx+1:04d}"),
            "show_at": str(row.get("show_at") or iso_jst()),
            "agent_id": aid,
            "agent_name": agent_name(aid),
            "ticker": str(row.get("ticker") or row.get("linked_symbol") or ""),
            "name": str(row.get("name") or row.get("linked_name") or row.get("ticker") or ""),
            "badge": badge,
            "side": side,
            "reason_code": str(row.get("reason_code") or row.get("reason") or ""),
            "message": clean_text(row.get("message") or row.get("body") or ""),
        })
    return events[:80]


def build_fact_pack(agents: list[dict[str, Any]], ranking: list[dict[str, Any]], open_positions: list[dict[str, Any]], closed_trades: list[dict[str, Any]], events: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    leader = ranking[0] if ranking else {}
    second = ranking[1] if len(ranking) > 1 else {}
    top_open = sorted(open_positions, key=lambda x: abs(x.get("pnl_pct", 0)), reverse=True)[:18]
    recent_closed = closed_trades[:12]
    recent_events = events[:24]
    return {
        "generated_at_jst": iso_jst(),
        "season": summary.get("year") or summary.get("season") or summary.get("run", {}).get("year") or "current",
        "agents": [{"agent_id": a["agent_id"], "name": a["name"], "role": a["role"], "voice": a["voice"]} for a in agents],
        "leaderboard": ranking[:7],
        "leader": leader,
        "second_place": second,
        "open_positions": top_open,
        "recent_closed_trades": recent_closed,
        "recent_trade_events": recent_events,
        "counts": {
            "agents": len(agents),
            "open_positions": len(open_positions),
            "recent_events": len(events),
            "closed_trades_available": len(closed_trades),
        },
    }


def compact_json(data: Any, max_chars: int = 16000) -> str:
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= max_chars:
        return text
    # Prefer truncating long event arrays instead of clipping JSON mid-object.
    if isinstance(data, dict):
        clone = dict(data)
        clone["recent_trade_events"] = clone.get("recent_trade_events", [])[:12]
        clone["open_positions"] = clone.get("open_positions", [])[:12]
        clone["recent_closed_trades"] = clone.get("recent_closed_trades", [])[:8]
        return json.dumps(clone, ensure_ascii=False, separators=(",", ":"))[:max_chars]
    return text[:max_chars]


def openai_chat(messages: list[dict[str, str]], *, max_tokens: int = 4200, temperature: float = 0.92) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for AI Arena War Room. Set GitHub Secrets.OPENAI_API_KEY or set AI_ARENA_WAR_ROOM_ALLOW_FALLBACK=true only for emergency local testing.")
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=80) as res:
                body = json.loads(res.read().decode("utf-8"))
            return str(body["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:900]
            last_err = RuntimeError(f"OpenAI HTTP {exc.code}: {detail}")
        except Exception as exc:  # pragma: no cover - network dependent
            last_err = exc
        time.sleep(2 + attempt * 3)
    raise RuntimeError(f"OpenAI request failed after retries: {last_err}")


def build_prompt(facts: dict[str, Any]) -> list[dict[str, str]]:
    system = """
You are the showrunner and market-intelligence editor for Neon Tokyo Signals AI Arena JP.
Write a world-class English live chat between seven fictional quantitative trading agents.
The output must feel like real-time thinking: short reactions, interruptions, disagreement, self-correction, and useful market interpretation.

Hard rules:
- Use ONLY the supplied simulation facts. Do not invent external news, earnings, macro events, analyst views, or real-world reasons.
- Do not give investment advice. Never say users should buy or sell.
- Keep every message anchored to Arena data: rank, return, drawdown, open positions, recent entries/exits, risk, persistence, pullback, snapback, or value distortion.
- Use all seven agents across the stream. Make their personalities distinct.
- Avoid templated lines. Avoid repeating the same sentence structure.
- This is a live chat, not a report and not threaded. Messages should read like they arrive one by one.
- Make it genuinely useful: explain what the Arena is learning from behavior, not just what happened.
- English only.

Return strict JSON only with this shape:
{
  "headline": "...",
  "brief": "...",
  "bullets": ["...", "...", "...", "..."],
  "messages": [
    {
      "agent_id": "daily_striker|weekly_sage|risk_sentinel|discovery_scout|contrarian_monk|reversal_snapback|value_mispricing",
      "state": "short uppercase status",
      "mood": "calm|alert|challenging|excited|skeptical|protective|analytical",
      "body": "1-3 natural sentences, no markdown",
      "evidence_label": "short factual anchor from supplied data",
      "linked_symbol": "optional ticker from supplied data only",
      "linked_name": "optional company name from supplied data only"
    }
  ],
  "pulse": ["short ambient thought", "..."]
}
""".strip()
    user = f"""
Create {MESSAGE_COUNT} live-chat messages for today's AI Arena War Room.
The conversation should feel like agents are thinking in real time over the next few hours.
Use direct disagreement and follow-up, but keep it concise.

FACT PACK JSON:
{compact_json(facts)}
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_ai_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if not match:
            raise
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("OpenAI response was not a JSON object")
    return data


def emergency_fallback(facts: dict[str, Any]) -> dict[str, Any]:
    # This exists only so a developer can render locally without a key.  The
    # workflow is configured to require GPT-4o, matching the production design.
    leader = facts.get("leader") or {}
    open_count = facts.get("counts", {}).get("open_positions", 0)
    base = [
        ("weekly_sage", "READING FLOW", f"The board is led by {leader.get('name', 'the current leader')}, but I need to see whether that advantage persists beyond one window."),
        ("risk_sentinel", "RISK CHECK", f"There are {open_count} open positions. My first question is not return; it is whether the room can survive a bad rotation."),
        ("daily_striker", "MOMENTUM WATCH", "If volume confirms pressure, waiting for a perfect story is just another form of hesitation."),
        ("value_mispricing", "TRAP TEST", "A discount is not intelligence until behavior proves it is not deterioration."),
    ]
    messages = []
    for i in range(MESSAGE_COUNT):
        aid, state, body = base[i % len(base)]
        messages.append({"agent_id": aid, "state": state, "mood": "analytical", "body": body, "evidence_label": "local fallback", "linked_symbol": "", "linked_name": ""})
    return {"headline": "AI Arena War Room is live", "brief": "Local fallback content. Production requires GPT-4o.", "bullets": ["GPT fallback mode", "Simulation data only"], "messages": messages, "pulse": []}


def schedule_messages(raw_messages: list[dict[str, Any]], agents_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(now_jst().strftime("%Y%m%d%H"))
    elapsed = 0
    out: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_messages[:MESSAGE_COUNT], start=1):
        aid = str(item.get("agent_id") or "").strip()
        if aid not in CANONICAL_NAMES:
            aid = list(CANONICAL_NAMES)[idx % len(CANONICAL_NAMES)]
        delay = 0 if idx == 1 else rng.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
        elapsed += delay
        reveal_at = now_jst() + timedelta(seconds=elapsed)
        body = clean_text(item.get("body"), 520)
        if not body:
            body = f"I am checking the Arena evidence before reacting. The useful signal must survive more than noise."
        out.append({
            "message_id": f"live-msg-{idx:03d}",
            "sequence": idx,
            "agent_id": aid,
            "agent_name": agent_name(aid),
            "avatar_image": agents_by_id.get(aid, {}).get("image") or agent_image(aid),
            "color": CANONICAL_COLORS[aid],
            "state": clean_text(item.get("state") or AGENT_PERSONAS[aid]["state"], 42).upper(),
            "mood": clean_text(item.get("mood") or "analytical", 32).lower(),
            "body": body,
            "evidence_label": clean_text(item.get("evidence_label") or "Arena simulation evidence", 96),
            "linked_symbol": clean_text(item.get("linked_symbol") or "", 24),
            "linked_name": clean_text(item.get("linked_name") or "", 64),
            "delay_seconds": delay,
            "reveal_after_seconds": elapsed,
            "scheduled_at": reveal_at.isoformat(timespec="seconds"),
        })
    return out


def enrich_agents(agents: list[dict[str, Any]], ranking: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rank_by_id = {r["agent_id"]: r for r in ranking}
    out = []
    for agent in agents:
        r = rank_by_id.get(agent["agent_id"], {})
        x = dict(agent)
        x.update({
            "rank": r.get("rank", "—"),
            "return_pct": r.get("return_pct", 0),
            "return_label": r.get("return_label", "—"),
            "mdd_label": r.get("mdd_label", "—"),
            "win_rate_label": r.get("win_rate_label", "—"),
            "trade_count": r.get("trade_count", 0),
        })
        out.append(x)
    return out


def build_evidence_tape(ranking: list[dict[str, Any]], open_positions: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tape: list[dict[str, Any]] = []
    for r in ranking[:7]:
        tape.append({"label": f"#{r['rank']} {r['name']}", "value": f"{r['return_label']} / MDD {r['mdd_label']}", "agent_id": r["agent_id"], "color": CANONICAL_COLORS.get(r["agent_id"], "#7DF9FF")})
    for p in open_positions[:10]:
        tape.append({"label": f"OPEN {p['ticker']}", "value": f"{p['agent_name']} {p['pnl_label']}", "agent_id": p["agent_id"], "color": CANONICAL_COLORS.get(p["agent_id"], "#7DF9FF")})
    for e in events[:8]:
        tape.append({"label": f"{e['badge']} {e['ticker']}", "value": f"{e['agent_name']} / {e['reason_code'] or 'event'}", "agent_id": e["agent_id"], "color": CANONICAL_COLORS.get(e["agent_id"], "#7DF9FF")})
    return tape[:24]


def prune_history(history_dir: Path) -> None:
    if HISTORY_DAYS <= 0 or not history_dir.exists():
        return
    cutoff = now_jst().date() - timedelta(days=HISTORY_DAYS)
    for path in history_dir.glob("*.json"):
        try:
            d = datetime.strptime(path.stem, "%Y-%m-%d").date()
        except Exception:
            continue
        if d < cutoff:
            path.unlink(missing_ok=True)
            print(f"Pruned old War Room snapshot: {path}")


def main() -> int:
    agents = load_agents()
    agents_by_id = {a["agent_id"]: a for a in agents}
    ranking_payload = read_json(BASE / "ranking" / "latest.json", {})
    positions_payload = read_json(BASE / "positions" / "latest.json", {})
    summary_payload = read_json(BASE / "summary" / "latest.json", {})
    log_payload = read_json(BASE / "log" / "latest.json", {})

    ranking = normalize_ranking(ranking_payload if isinstance(ranking_payload, dict) else {})
    open_positions, closed_trades, portfolio = normalize_positions(positions_payload if isinstance(positions_payload, dict) else {})
    events = normalize_events(log_payload if isinstance(log_payload, dict) else {})
    fact_pack = build_fact_pack(agents, ranking, open_positions, closed_trades, events, summary_payload if isinstance(summary_payload, dict) else {})

    try:
        ai_raw = openai_chat(build_prompt(fact_pack))
        ai_data = parse_ai_json(ai_raw)
        ai_status = "gpt-4o_generated"
    except Exception as exc:
        if not ALLOW_FALLBACK:
            raise
        print(f"WARN using emergency fallback because GPT failed: {exc}")
        ai_data = emergency_fallback(fact_pack)
        ai_status = "emergency_fallback"

    live_messages = schedule_messages(ai_data.get("messages") or [], agents_by_id)
    enriched_agents = enrich_agents(agents, ranking)
    evidence_tape = build_evidence_tape(ranking, open_positions, events)
    pulse = []
    for i, p in enumerate(ai_data.get("pulse") or []):
        aid = list(CANONICAL_NAMES)[i % len(CANONICAL_NAMES)]
        pulse.append({"agent_id": aid, "agent_name": agent_name(aid), "color": CANONICAL_COLORS[aid], "body": clean_text(p, 120), "state": AGENT_PERSONAS[aid]["state"]})
    if not pulse:
        pulse = [{"agent_id": a["agent_id"], "agent_name": a["name"], "color": a["color"], "body": a["description"][:110], "state": a["state"]} for a in enriched_agents]

    payload = {
        "schema_version": "ai_arena_live_chat_v2_gpt4o_required",
        "generated_at": iso_jst(),
        "page": {
            "title": "AI Arena Live Council",
            "subtitle": "Seven trading agents think out loud over live simulation evidence from Japanese equities.",
        },
        "daily_brief": {
            "headline": clean_text(ai_data.get("headline") or "The Live Council is online.", 120),
            "summary": clean_text(ai_data.get("brief") or "GPT-4o generated this Arena discussion from ranking, positions, and trade evidence.", 520),
            "bullets": [clean_text(x, 120) for x in (ai_data.get("bullets") or [])[:6]],
        },
        "agents": enriched_agents,
        "ranking": ranking,
        "open_positions": open_positions[:30],
        "portfolio": portfolio,
        "live_messages": live_messages,
        "feed": live_messages,  # compatibility alias
        "threads": [],  # intentionally empty: the new design is a single live chat stream
        "evidence_tape": evidence_tape,
        "pulse": pulse,
        "live_config": {
            "mode": "browser_reveal_queue",
            "min_delay_seconds": MIN_DELAY_SECONDS,
            "max_delay_seconds": MAX_DELAY_SECONDS,
            "message_count": len(live_messages),
            "schedule_note": "The static page reveals pre-generated GPT-4o messages at random 3-5 minute intervals in the browser.",
        },
        "metrics": {
            "agent_count": len(enriched_agents),
            "message_count": len(live_messages),
            "open_position_count": len(open_positions),
            "ranking_count": len(ranking),
            "evidence_items": len(evidence_tape),
        },
        "ai": {
            "required": True,
            "enabled": True,
            "status": ai_status,
            "model": MODEL,
            "temperature": 0.92,
        },
        "disclaimer": "AI Arena is a quantitative simulation and generative discussion interface. Informational only. Not investment advice.",
    }

    latest_path = BASE / "war-room" / "latest.json"
    history_path = BASE / "war-room" / "history" / f"{now_jst().date().isoformat()}.json"
    write_json(latest_path, payload)
    write_json(history_path, payload)
    prune_history(history_path.parent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
