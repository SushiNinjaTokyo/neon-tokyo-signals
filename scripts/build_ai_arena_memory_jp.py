from __future__ import annotations

"""
Build Neon Tokyo AI Arena Agent Memory.

Purpose
-------
Agent Memory makes the LAB feel continuous: agents remember yesterday's
ranking, open positions, failed trades, cash-only decisions and lessons.

Architecture rule
-----------------
This script does not make trading decisions. It reads deterministic simulation
outputs and writes concise memory cards that the discussion builder can pass to
GPT as context.

Outputs
-------
site/data/japan/ai-arena/memory/latest.json
site/data/japan/ai-arena/memory/history/YYYY-MM-DD.json
"""

import json
import os
import urllib.request
import urllib.error
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
MEMORY_OUT = OUT_DIR / "data/japan/ai-arena/memory/latest.json"
MEMORY_HISTORY_DIR = OUT_DIR / "data/japan/ai-arena/memory/history"

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


def fmt_pct(x: Any) -> str:
    v = to_float(x)
    return f"{v:+.2f}%"


def ai_enabled() -> bool:
    return os.getenv("OPENAI_ENABLE_AI", "false").lower() == "true" and bool(os.getenv("OPENAI_API_KEY"))


def call_openai_json(model: str, system: str, payload: dict[str, Any], max_tokens: int = 4000) -> dict[str, Any] | None:
    """Minimal OpenAI Chat Completions client.

    We keep this local instead of adding an SDK dependency. If the API fails,
    fallback memories are still written.
    """
    if not ai_enabled():
        return None

    body = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": 0.55,
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
        with urllib.request.urlopen(req, timeout=90) as res:
            data = json.loads(res.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
        print(f"WARN OpenAI memory call failed: {exc}")
        return None


def agent_meta(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a.get("id"): a for a in (config.get("agents") or []) if a.get("id")}


def ranking_map(ranking: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a.get("agent_id"): a for a in (ranking.get("agents") or []) if a.get("agent_id")}


def position_map(positions: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a.get("agent_id"): a for a in (positions.get("agents") or []) if a.get("agent_id")}


def latest_agent_state(sim: dict[str, Any], positions: dict[str, Any], ranking: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    ranks = ranking_map(ranking)
    pos_by_agent = position_map(positions)
    meta = agent_meta(config)
    states: list[dict[str, Any]] = []

    for agent_id, cfg in meta.items():
        rank = ranks.get(agent_id, {})
        pos_agent = pos_by_agent.get(agent_id, {})
        open_positions = pos_agent.get("open_positions") or []
        recent_actions = pos_agent.get("recent_actions") or []
        closed = []
        for sim_agent in sim.get("agents", []):
            if sim_agent.get("agent_id") == agent_id:
                closed = sim_agent.get("closed_trades") or []
                break

        worst_open = min(open_positions, key=lambda p: to_float(p.get("unrealized_return_pct")), default=None)
        best_open = max(open_positions, key=lambda p: to_float(p.get("unrealized_return_pct")), default=None)
        last_exit = next((a for a in reversed(recent_actions) if a.get("action") == "exit"), None)
        last_entry = next((a for a in reversed(recent_actions) if a.get("action") == "entry"), None)

        states.append({
            "agent_id": agent_id,
            "agent_name": cfg.get("name") or agent_id,
            "style_label": cfg.get("style_label") or cfg.get("screening_profile"),
            "rank": rank.get("rank"),
            "return_pct": rank.get("return_pct"),
            "max_drawdown_pct": rank.get("max_drawdown_pct"),
            "win_rate_pct": rank.get("win_rate_pct"),
            "open_positions_count": len(open_positions),
            "cash_jpy": (pos_agent.get("summary") or {}).get("cash_jpy"),
            "best_open_position": best_open,
            "worst_open_position": worst_open,
            "recent_entry": last_entry,
            "recent_exit": last_exit,
            "recent_actions": recent_actions[-6:],
            "voice_summary": (cfg.get("voice") or {}).get("personality_short") or cfg.get("personality"),
        })
    return states


def deterministic_memory(states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    memories: list[dict[str, Any]] = []
    for s in states:
        name = s.get("agent_name")
        rank = s.get("rank")
        ret = fmt_pct(s.get("return_pct"))
        open_count = s.get("open_positions_count") or 0
        worst = s.get("worst_open_position") or {}
        best = s.get("best_open_position") or {}

        if rank == 1:
            mood = "confident"
            lesson = "The current process is being paid, but the lead still has to survive concentration and drawdown."
        elif to_float(s.get("return_pct")) < 0:
            mood = "wounded"
            lesson = "The recent process has not converted into return; the next signal needs cleaner confirmation."
        elif open_count == 0:
            mood = "patient"
            lesson = "No position can be a valid allocation when the signal does not clear the strategy threshold."
        else:
            mood = "focused"
            lesson = "The book is alive, but open risk still has to earn its place."

        if worst:
            last_mistake = f"{worst.get('symbol')} is the weakest live mark at {fmt_pct(worst.get('unrealized_return_pct'))}."
        elif s.get("recent_exit"):
            ex = s["recent_exit"]
            last_mistake = f"The last exit was {ex.get('symbol')} via {ex.get('reason') or 'exit rule'}."
        else:
            last_mistake = "No fresh damage stands out; the main question is whether the process is too quiet."

        if best:
            today_bias = f"Defend or reassess {best.get('symbol')} only if the position keeps validating the strategy."
        elif open_count == 0:
            today_bias = "Preserve optionality until a cleaner setup appears."
        else:
            today_bias = "Keep the book focused on positions that still validate the style."

        memories.append({
            "agent_id": s.get("agent_id"),
            "agent_name": name,
            "mood": mood,
            "yesterday_summary": f"{name} sits at rank #{rank} with {ret} and {open_count} open positions.",
            "last_mistake": last_mistake,
            "lesson": lesson,
            "today_bias": today_bias,
            "memory_line": f"{name} remembers rank #{rank}: {lesson}",
        })
    return memories


def maybe_ai_refine(memories: list[dict[str, Any]], states: list[dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], bool, str]:
    model = os.getenv("OPENAI_MODEL_MINI") or (config.get("arena") or {}).get("default_model") or "gpt-4o-mini"
    system = """
You refine AI Arena Agent Memory cards.

Use only the supplied facts. Do not invent news, fundamentals, earnings, guidance, target prices, or recommendations.
Return JSON:
{
  "agents": [
    {
      "agent_id": string,
      "mood": string,
      "yesterday_summary": string,
      "last_mistake": string,
      "lesson": string,
      "today_bias": string,
      "memory_line": string
    }
  ]
}

Rules:
- Keep each field concise.
- Make memories sound like professional portfolio self-reflection, not diary drama.
- Memory should shape tomorrow's tone, not replace analysis.
- Use the Agent's rank, return, live position, cash-only stance, or recent action when relevant.
- No buy/sell/recommendation language.
"""
    response = call_openai_json(model, system, {"seed_memories": memories, "agent_states": states}, 4500)
    if not response or not isinstance(response.get("agents"), list):
        return memories, True, "fallback_memory_no_ai"

    by_id = {m["agent_id"]: m for m in memories}
    refined: list[dict[str, Any]] = []
    for row in response.get("agents", []):
        if not isinstance(row, dict) or row.get("agent_id") not in by_id:
            continue
        base = by_id[row["agent_id"]]
        merged = dict(base)
        for k in ["mood", "yesterday_summary", "last_mistake", "lesson", "today_bias", "memory_line"]:
            v = row.get(k)
            if isinstance(v, str) and v.strip():
                merged[k] = v.strip()[:420]
        refined.append(merged)
    if len(refined) < len(memories):
        return memories, True, "fallback_memory_partial"
    return refined, False, "ok_memory_ai"


def main() -> None:
    config = read_yaml(AGENTS_YAML, {})
    sim = read_json(SIM_JSON, {})
    positions = read_json(POSITIONS_JSON, {})
    ranking = read_json(RANKING_JSON, {})
    if not sim or not positions or not ranking:
        raise SystemExit("Missing simulation/positions/ranking JSON. Run rebuild_ai_arena_simulation_jp.py first.")

    states = latest_agent_state(sim, positions, ranking, config)
    seed = deterministic_memory(states)
    memories, fallback, status = maybe_ai_refine(seed, states, config)

    memory_date = (sim.get("range") or {}).get("end_date") or now_jst().strftime("%Y-%m-%d")
    payload = {
        "schema_version": "ai_arena_agent_memory_v1",
        "generated_at": iso_jst(now_jst()),
        "memory_date": memory_date,
        "ai": {
            "enabled": ai_enabled(),
            "model": os.getenv("OPENAI_MODEL_MINI", "gpt-4o-mini"),
            "status": status,
            "fallback_used": fallback,
        },
        "agents": memories,
    }

    write_json(MEMORY_OUT, payload)
    write_json(MEMORY_HISTORY_DIR / f"{memory_date}.json", payload)
    print(f"AI Arena memory result: status={status} fallback={fallback} agents={len(memories)}")


if __name__ == "__main__":
    main()
