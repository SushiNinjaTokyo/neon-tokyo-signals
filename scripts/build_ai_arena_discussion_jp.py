from __future__ import annotations

"""
Build Neon Tokyo AI Arena discussion data.

This script turns deterministic simulation facts into an AI-readable Arena page.
It does not decide trades. Trading state comes from
site/data/japan/ai-arena/simulation/latest.json.

The discussion pipeline is intentionally structured:
1. Market Master brief from simulation / ranking / position facts.
2. Agent thesis lines derived from their live positions and recent actions.
3. Debate synthesis into Arena Log.

External news is intentionally out of scope for this version. The prompt tells
OpenAI to use only provided facts.
"""

import json
import math
import os
import re
import time
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
DISCUSSION_OUT = OUT_DIR / "data/japan/ai-arena/discussion/latest.json"
LEGACY_OUT = OUT_DIR / "data/japan/ai-arena/latest.json"

JST = timezone(timedelta(hours=9))
MODEL_PRICES_USD_PER_1M = {"gpt-4o-mini": {"input": 0.15, "output": 0.60}, "gpt-4o": {"input": 2.50, "output": 10.00}, "gpt-5.5": {"input": 5.00, "output": 30.00}}
BANNED = ["strong buy", "target price", "guaranteed", "must own", "easy money", "buy ", "sell ", "recommend"]


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
        return fallback
    return yaml.safe_load(path.read_text(encoding="utf-8")) or fallback


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


def safe_text(s: Any, max_len: int = 260) -> str:
    text = re.sub(r"\s+", " ", str(s or "")).strip()
    for bad in BANNED:
        text = re.sub(re.escape(bad), "", text, flags=re.I)
    return text[:max_len].strip()


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4) + 1)


def ai_enabled() -> bool:
    return os.getenv("OPENAI_ENABLE_AI", "true").lower() in {"1", "true", "yes", "on"} and bool(os.getenv("OPENAI_API_KEY"))


def call_openai_json(model: str, system_prompt: str, user_payload: dict[str, Any], max_output_tokens: int = 3500) -> dict[str, Any] | None:
    if not ai_enabled():
        print("AI disabled or OPENAI_API_KEY missing; using fallback discussion.")
        return None
    payload_text = json.dumps(user_payload, ensure_ascii=False)
    in_tok = estimate_tokens(system_prompt) + estimate_tokens(payload_text)
    price = MODEL_PRICES_USD_PER_1M.get(model, MODEL_PRICES_USD_PER_1M["gpt-4o-mini"])
    est_cost = in_tok / 1_000_000 * price["input"] + max_output_tokens / 1_000_000 * price["output"]
    limit = float(os.getenv("OPENAI_DAILY_USD_LIMIT", "0.50"))
    if est_cost > limit:
        print(f"AI cost guard: estimated ${est_cost:.4f} > daily limit ${limit:.2f}; fallback.")
        return None
    body = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload_text},
        ],
        "temperature": 0.85,
        "max_tokens": max_output_tokens,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
        method="POST",
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as exc:
            print(f"WARN OpenAI discussion call failed attempt {attempt+1}: {exc}")
            time.sleep(2)
    return None


def top_open_positions(positions_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for agent in positions_payload.get("agents", []) or []:
        for p in agent.get("open_positions", []) or []:
            rows.append({**p, "agent_id": agent.get("agent_id"), "agent_name": agent.get("name")})
    rows.sort(key=lambda x: abs(float(x.get("unrealized_return_pct") or 0)), reverse=True)
    return rows[:12]


def agent_theses(positions_payload: dict[str, Any], ranking_payload: dict[str, Any]) -> list[dict[str, Any]]:
    ranking_by_agent = {a.get("agent_id"): a for a in ranking_payload.get("agents", []) or []}
    theses = []
    for agent in positions_payload.get("agents", []) or []:
        aid = agent.get("agent_id")
        summary = agent.get("summary") or {}
        rank = ranking_by_agent.get(aid, {}).get("rank")
        open_pos = agent.get("open_positions", []) or []
        if open_pos:
            lead = sorted(open_pos, key=lambda p: abs(float(p.get("unrealized_return_pct") or 0)), reverse=True)[0]
            thesis = f"{agent.get('name')} is focused on {lead.get('symbol')} {lead.get('name')} in {lead.get('theme')}; current P/L {lead.get('unrealized_return_pct')}%, holding {lead.get('holding_days')} days."
        else:
            thesis = f"{agent.get('name')} holds cash and is waiting for its screening profile to produce a cleaner entry."
        theses.append({
            "agent_id": aid,
            "agent_name": agent.get("name"),
            "class": agent.get("class"),
            "rank": rank,
            "return_pct": summary.get("return_pct"),
            "open_positions": len(open_pos),
            "thesis": thesis,
            "personality": agent.get("personality"),
            "philosophy": agent.get("philosophy"),
        })
    return theses


def fallback_debate(theses: list[dict[str, Any]], ranking: dict[str, Any], positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Non-random fallback with actual position/ranking facts. This is used only
    # when AI is off/fails. It remains more alive than fixed slogan loops.
    base = now_jst().replace(second=0, microsecond=0)
    lines = []
    ordered = sorted(theses, key=lambda x: x.get("rank") or 99)
    for i, t in enumerate(ordered[:5]):
        body = t["thesis"]
        if i == 0:
            body += " The board has to respect the leader until the equity curve says otherwise."
        elif "Risk" in str(t.get("agent_name")):
            body += " I still care more about survivability than headline heat."
        elif "Discovery" in str(t.get("agent_name")):
            body += " The interesting part is where global screens are still blind."
        elif "Contrarian" in str(t.get("agent_name")) or "Monk" in str(t.get("agent_name")):
            body += " Crowded conviction is not the same thing as edge."
        else:
            body += " The theme has to be readable for foreign capital, not just locally noisy."
        lines.append({
            "id": f"feed_{i+1:03d}",
            "show_at": iso_jst(base + timedelta(minutes=i * 10)),
            "agent_id": t["agent_id"],
            "agent_name": t["agent_name"],
            "type": "debate",
            "body": safe_text(body, 320),
            "linked_symbol": positions[i % len(positions)].get("symbol") if positions else None,
            "linked_theme": positions[i % len(positions)].get("theme") if positions else None,
        })
    # Extend first-screen density without copy-paste loops.
    for j, p in enumerate(positions[:10], start=len(lines)+1):
        speaker = ordered[j % len(ordered)] if ordered else {}
        body = f"On {p.get('symbol')}, the live position says {p.get('unrealized_return_pct')}% unrealized P/L. That is the fact; the debate is whether the setup still deserves risk."
        lines.append({"id": f"feed_{j:03d}", "show_at": iso_jst(base + timedelta(minutes=(j-1)*10)), "agent_id": speaker.get("agent_id"), "agent_name": speaker.get("agent_name"), "type": "position_check", "body": safe_text(body, 320), "linked_symbol": p.get("symbol"), "linked_theme": p.get("theme")})
    return lines[:30]


def build_context(sim: dict[str, Any], positions: dict[str, Any], ranking: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    champion = ranking.get("champion") or {}
    top_positions = top_open_positions(positions)
    theses = agent_theses(positions, ranking)
    return {
        "range": sim.get("range"),
        "season": sim.get("season"),
        "champion": champion,
        "ranking": ranking.get("agents", [])[:5],
        "top_open_positions": top_positions,
        "agent_theses": theses,
        "external_news_enabled": False,
        "news_rule": "No external news is supplied. Do not invent headlines or macro events.",
        "disclaimer": (config.get("arena") or {}).get("disclaimer"),
    }


def build_ai_discussion(context: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], bool, str]:
    master = config.get("market_master") or {}
    model = os.getenv("OPENAI_MODEL_MINI") or master.get("model") or (config.get("arena") or {}).get("default_model") or "gpt-4o-mini"
    system = """
You generate Neon Tokyo AI Arena discussion JSON.
Use ONLY the provided simulation facts. Do not invent news, fundamentals, earnings, guidance, macro events, target prices, or trade recommendations.
Output valid JSON with exactly these keys:
{
  "daily_brief": {"title": string, "body": string, "risk_note": string},
  "feed": [
    {"agent_id": string, "type": "debate"|"challenge"|"risk_check"|"position_check"|"ranking_reaction", "body": string, "linked_symbol": string|null, "linked_theme": string|null}
  ]
}
Rules for feed:
- 18 to 30 lines.
- It must read like a natural debate about actual current positions and ranking.
- Every line must react to a previous claim or a concrete position/ranking fact.
- No generic slogans such as hidden gems, monitor closely, exciting opportunities, proceed with caution.
- Mention only symbols/themes present in the input.
- Keep each body under 220 characters.
- No buy/sell/recommend/target/guarantee language.
"""
    result = call_openai_json(model, system, context, int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "6000")))
    if not result:
        return {}, True, "fallback_no_ai"
    feed = result.get("feed")
    brief = result.get("daily_brief")
    if not isinstance(feed, list) or len(feed) < 8 or not isinstance(brief, dict):
        return {}, True, "fallback_bad_schema"
    allowed_symbols = {p.get("symbol") for p in context.get("top_open_positions", []) if p.get("symbol")}
    allowed_agents = {t.get("agent_id") for t in context.get("agent_theses", []) if t.get("agent_id")}
    sanitized = []
    base = now_jst().replace(second=0, microsecond=0)
    for i, row in enumerate(feed[:30], 1):
        if not isinstance(row, dict):
            continue
        body = safe_text(row.get("body"), 260)
        if not body or any(x in body.lower() for x in ["fundamental", "earnings", "guidance", "target price", "hidden gems", "exciting opportunities", "monitor closely", "proceed with caution"]):
            continue
        aid = row.get("agent_id") if row.get("agent_id") in allowed_agents else (context.get("agent_theses") or [{}])[(i-1) % max(1, len(context.get("agent_theses") or [{}]))].get("agent_id")
        agent_name = next((t.get("agent_name") for t in context.get("agent_theses", []) if t.get("agent_id") == aid), aid)
        sym = row.get("linked_symbol") if row.get("linked_symbol") in allowed_symbols else None
        theme = row.get("linked_theme")
        sanitized.append({"id": f"feed_{len(sanitized)+1:03d}", "show_at": iso_jst(base + timedelta(minutes=(len(sanitized))*10)), "agent_id": aid, "agent_name": agent_name, "type": row.get("type") or "debate", "body": body, "linked_symbol": sym, "linked_theme": theme})
    if len(sanitized) < 8:
        return {}, True, "fallback_quality_guard"
    result["feed"] = sanitized
    result["daily_brief"] = {"analyst_id": "market_master", "title": safe_text(brief.get("title"), 80), "body": safe_text(brief.get("body"), 420), "risk_note": safe_text(brief.get("risk_note"), 260)}
    return result, False, "ok"


def main() -> None:
    config = read_yaml(AGENTS_YAML, {})
    sim = read_json(SIM_JSON, {})
    positions = read_json(POSITIONS_JSON, {})
    ranking = read_json(RANKING_JSON, {})
    if not sim or not positions or not ranking:
        raise SystemExit("Missing AI Arena simulation/positions/ranking JSON. Run rebuild_ai_arena_simulation_jp.py first.")
    context = build_context(sim, positions, ranking, config)
    ai_payload, fallback, status = build_ai_discussion(context, config)
    theses = context["agent_theses"]
    pos = context["top_open_positions"]
    if fallback:
        feed = fallback_debate(theses, ranking, pos)
        daily_brief = {"analyst_id": "market_master", "title": "Arena simulation online", "body": "Agent portfolios are now driven by distinct screening rules. The Arena debate is based on live simulated positions, not external news.", "risk_note": "External news is disabled in this build; discussion uses simulation facts only."}
    else:
        feed = ai_payload["feed"]
        daily_brief = ai_payload["daily_brief"]

    payload = {
        "schema_version": "neon_tokyo_ai_arena_discussion_v2",
        "generated_at": iso_jst(now_jst()),
        "market": "Japan",
        "timezone": "Asia/Tokyo",
        "season": sim.get("season"),
        "range": sim.get("range"),
        "ai": {"enabled": ai_enabled(), "model": os.getenv("OPENAI_MODEL_MINI", "gpt-4o-mini"), "status": status, "fallback_used": fallback, "external_news_enabled": False},
        "daily_brief": daily_brief,
        "market_context": context,
        "agents": [
            {"agent_id": a.get("agent_id"), "name": a.get("name"), "class": a.get("class"), "ui_tone": a.get("ui_tone"), "avatar_style": a.get("avatar_style"), "summary": a.get("summary"), "open_positions": a.get("open_positions", [])[:3]}
            for a in positions.get("agents", [])
        ],
        "feed": feed,
        "ranking": ranking.get("agents", [])[:5],
        "disclaimer": (config.get("arena") or {}).get("disclaimer") or "Informational only. Not investment advice.",
    }
    write_json(DISCUSSION_OUT, payload)
    # Keep legacy latest.json for existing renderer / external links during migration.
    write_json(LEGACY_OUT, payload)


if __name__ == "__main__":
    main()
