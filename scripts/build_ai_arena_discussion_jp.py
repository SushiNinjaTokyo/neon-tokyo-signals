from __future__ import annotations

"""
Build Neon Tokyo AI Arena discussion data.

V2.1 purpose
------------
This script converts deterministic Agent simulation facts into a professional
debate feed for the Arena page.

Important architecture rule:
- Trading decisions, positions, P/L, rankings = deterministic Python simulation.
- AI text = interpretation and debate only.
- No external news is used in this version.
- The AI must not invent headlines, earnings, fundamentals, macro events, or
  recommendations.

Why this file is intentionally verbose:
The AI Arena will be tuned frequently. Keep each transformation explicit so
future prompt / validation / context changes can be made safely without touching
the trading simulation engine.
"""

import json
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

MODEL_PRICES_USD_PER_1M = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-5.5": {"input": 5.00, "output": 30.00},
}

# These phrases either create investment-advice risk or tend to produce weak,
# promotional writing. They are removed or cause a line to be rejected.
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
    "fundamentals",
    "earnings",
    "guidance",
    "undeniable",
]

# Used as a quality hint. A professional Arena discussion should contain at
# least some portfolio / risk / factor vocabulary instead of vague market talk.
PRO_TERMS = [
    "alpha",
    "drawdown",
    "equity",
    "position",
    "book",
    "liquidity",
    "risk",
    "factor",
    "ranking",
    "return",
    "p/l",
    "unrealized",
    "exposure",
    "holding",
    "entry",
    "cash",
    "volatility",
    "dispersion",
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
    except ValueError:
        rel = path
    print(f"Wrote {rel}")


def to_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return default
        return float(x)
    except Exception:
        return default


def to_int(x: Any, default: int = 0) -> int:
    try:
        if x is None or x == "":
            return default
        return int(float(x))
    except Exception:
        return default


def fmt_pct(x: Any, digits: int = 2) -> str:
    if x is None:
        return "n/a"
    try:
        return f"{float(x):+.{digits}f}%"
    except Exception:
        return "n/a"


def fmt_jpy(x: Any) -> str:
    try:
        return f"¥{float(x):,.0f}"
    except Exception:
        return "n/a"


def safe_text(s: Any, max_len: int = 280) -> str:
    """Normalize whitespace and remove explicit advice-like phrases."""
    text = re.sub(r"\s+", " ", str(s or "")).strip()
    for bad in ["strong buy", "target price", "guaranteed", "must own", "easy money", "recommendation"]:
        text = re.sub(re.escape(bad), "", text, flags=re.I)
    # Avoid direct imperative investment-advice wording.
    text = re.sub(r"\b(buy|sell)\b", "", text, flags=re.I)
    return text[:max_len].strip()


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4) + 1)


def ai_enabled() -> bool:
    return (
        os.getenv("OPENAI_ENABLE_AI", "true").lower() in {"1", "true", "yes", "on"}
        and bool(os.getenv("OPENAI_API_KEY"))
    )


def call_openai_json(
    model: str,
    system_prompt: str,
    user_payload: dict[str, Any],
    max_output_tokens: int = 6000,
) -> dict[str, Any] | None:
    """Call OpenAI Chat Completions and require JSON object output.

    The site must keep working if OpenAI fails, so every failure returns None
    and the caller uses a fallback debate.
    """
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
        # Slightly lower than the previous version. This improves discipline and
        # reduces generic brainstorming while preserving personality.
        "temperature": float(os.getenv("AI_ARENA_DEBATE_TEMPERATURE", "0.62")),
        "max_tokens": max_output_tokens,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        },
        method="POST",
    )

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=75) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as exc:
            print(f"WARN OpenAI discussion call failed attempt {attempt + 1}: {exc}")
            time.sleep(2)

    return None


def normalize_agent_config(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a.get("id"): a for a in (config.get("agents") or []) if a.get("id")}


def ranking_agents(ranking_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = ranking_payload.get("agents", []) or []
    return sorted(rows, key=lambda x: to_int(x.get("rank"), 999))


def ranking_by_agent(ranking_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a.get("agent_id"): a for a in ranking_agents(ranking_payload) if a.get("agent_id")}


def position_agents(positions_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return positions_payload.get("agents", []) or []


def top_open_positions(positions_payload: dict[str, Any], limit: int = 14) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for agent in position_agents(positions_payload):
        for p in agent.get("open_positions", []) or []:
            rows.append({**p, "agent_id": agent.get("agent_id"), "agent_name": agent.get("name")})
    # Prioritize positions that are driving the ranking narrative.
    rows.sort(key=lambda x: abs(to_float(x.get("unrealized_return_pct"))), reverse=True)
    return rows[:limit]


def symbol_mentions(text: str) -> set[str]:
    return set(re.findall(r"\b\d{3,4}[A-Z]?\.T\b", text or ""))


def theme_exposure(positions_payload: dict[str, Any]) -> list[dict[str, Any]]:
    agg: dict[str, dict[str, Any]] = {}
    for p in top_open_positions(positions_payload, 100):
        theme = p.get("theme") or "Unclassified"
        row = agg.setdefault(theme, {"theme": theme, "positions": 0, "gross_unrealized_pct": 0.0, "agents": set()})
        row["positions"] += 1
        row["gross_unrealized_pct"] += to_float(p.get("unrealized_return_pct"))
        row["agents"].add(p.get("agent_name") or p.get("agent_id"))
    out = []
    for row in agg.values():
        out.append({
            "theme": row["theme"],
            "positions": row["positions"],
            "gross_unrealized_pct": round(row["gross_unrealized_pct"], 2),
            "agents": sorted(row["agents"]),
        })
    out.sort(key=lambda r: (r["positions"], abs(r["gross_unrealized_pct"])), reverse=True)
    return out[:8]


def overlapping_symbols(positions_payload: dict[str, Any]) -> list[dict[str, Any]]:
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    for p in top_open_positions(positions_payload, 100):
        sym = p.get("symbol")
        if not sym:
            continue
        by_symbol.setdefault(sym, []).append(p)
    rows = []
    for sym, ps in by_symbol.items():
        if len(ps) >= 2:
            rows.append({
                "symbol": sym,
                "name": ps[0].get("name"),
                "theme": ps[0].get("theme"),
                "agents": [p.get("agent_name") for p in ps],
                "unrealized_returns": [p.get("unrealized_return_pct") for p in ps],
            })
    rows.sort(key=lambda r: len(r["agents"]), reverse=True)
    return rows


def agent_theses(
    positions_payload: dict[str, Any],
    ranking_payload: dict[str, Any],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build compact, fact-heavy briefs for each Agent.

    This is the most important input to the debate model. If the model receives
    vague inputs, it will produce vague chat. Each thesis therefore includes:
    rank, return, equity, open positions, largest position, realized context, and
    the Agent's explicit philosophy from YAML.
    """
    rank_map = ranking_by_agent(ranking_payload)
    cfg_by_id = normalize_agent_config(config)
    theses: list[dict[str, Any]] = []

    for agent in position_agents(positions_payload):
        aid = agent.get("agent_id")
        cfg = cfg_by_id.get(aid, {})
        summary = agent.get("summary") or {}
        rank_row = rank_map.get(aid, {})
        open_pos = agent.get("open_positions", []) or []

        leader = None
        if open_pos:
            leader = sorted(
                open_pos,
                key=lambda p: abs(to_float(p.get("unrealized_return_pct"))),
                reverse=True,
            )[0]

        if leader:
            core_thesis = (
                f"{agent.get('name')} is ranked #{rank_row.get('rank', 'n/a')} with "
                f"{fmt_pct(rank_row.get('return_pct'))} season return and {fmt_jpy(rank_row.get('equity_jpy'))} equity. "
                f"Its live book is led by {leader.get('symbol')} {leader.get('name')} "
                f"({leader.get('theme')}); unrealized {fmt_pct(leader.get('unrealized_return_pct'))}, "
                f"holding {leader.get('holding_days', 'n/a')} days."
            )
        else:
            core_thesis = (
                f"{agent.get('name')} is ranked #{rank_row.get('rank', 'n/a')} with "
                f"{fmt_pct(rank_row.get('return_pct'))} season return and {fmt_jpy(rank_row.get('equity_jpy'))} equity. "
                f"It currently holds no open position, so its edge is cash discipline and selectivity."
            )

        theses.append({
            "agent_id": aid,
            "agent_name": agent.get("name"),
            "class": agent.get("class") or cfg.get("class"),
            "selection_profile": agent.get("selection_profile") or cfg.get("selection_profile"),
            "rank": rank_row.get("rank"),
            "return_pct": rank_row.get("return_pct"),
            "equity_jpy": rank_row.get("equity_jpy"),
            "win_rate_pct": rank_row.get("win_rate_pct"),
            "max_drawdown_pct": rank_row.get("max_drawdown_pct"),
            "open_positions": len(open_pos),
            "largest_position": leader,
            "core_thesis": core_thesis,
            "personality": cfg.get("personality") or agent.get("personality"),
            "philosophy": cfg.get("philosophy") or agent.get("philosophy"),
            "conversation_role": cfg.get("conversation_role"),
            "speech_style": cfg.get("speech_style"),
            "policy_hint": (cfg.get("trading_policy") or {}),
        })

    return theses


def build_debate_agenda(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Create an agenda so the AI debate has structure.

    The model still writes the actual lines, but the agenda forces the debate to
    cover real portfolio tensions rather than generic market talk.
    """
    ranking = context.get("ranking", [])
    positions = context.get("top_open_positions", [])
    overlaps = context.get("overlapping_symbols", [])
    themes = context.get("theme_exposure", [])

    agenda: list[dict[str, Any]] = []

    if ranking:
        leader = ranking[0]
        laggard = ranking[-1]
        agenda.append({
            "topic": "leader_challenge",
            "instruction": (
                f"Open by challenging why #{leader.get('rank')} {leader.get('name')} leads with "
                f"{fmt_pct(leader.get('return_pct'))}, and why #{laggard.get('rank')} {laggard.get('name')} trails with "
                f"{fmt_pct(laggard.get('return_pct'))}."
            ),
        })

    if positions:
        best = sorted(positions, key=lambda p: to_float(p.get("unrealized_return_pct")), reverse=True)[0]
        worst = sorted(positions, key=lambda p: to_float(p.get("unrealized_return_pct")))[0]
        agenda.append({
            "topic": "position_quality",
            "instruction": (
                f"Discuss whether the strongest live position {best.get('symbol')} "
                f"({fmt_pct(best.get('unrealized_return_pct'))}) is genuine edge or just marked-to-market heat. "
                f"Contrast it with weaker live position {worst.get('symbol')} ({fmt_pct(worst.get('unrealized_return_pct'))})."
            ),
        })

    if overlaps:
        o = overlaps[0]
        agenda.append({
            "topic": "shared_ticker_tension",
            "instruction": (
                f"Discuss why multiple agents hold {o.get('symbol')} {o.get('name')} from different philosophies: "
                f"{', '.join([str(a) for a in o.get('agents', [])])}."
            ),
        })

    if themes:
        t = themes[0]
        agenda.append({
            "topic": "theme_exposure",
            "instruction": (
                f"Discuss theme concentration in {t.get('theme')} across {t.get('positions')} open positions, "
                f"with aggregate unrealized P/L {fmt_pct(t.get('gross_unrealized_pct'))}."
            ),
        })

    agenda.append({
        "topic": "risk_budget",
        "instruction": (
            "At least one agent must argue that alpha ranking is not enough; position sizing, drawdown, "
            "liquidity and holding period decide whether the strategy is scalable."
        ),
    })

    return agenda


def build_context(sim: dict[str, Any], positions: dict[str, Any], ranking: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    rank_rows = ranking_agents(ranking)
    pos_rows = top_open_positions(positions)
    theses = agent_theses(positions, ranking, config)

    # Ranking dispersion helps the debate talk about whether the game is close
    # or if one agent is dominating.
    returns = [to_float(r.get("return_pct")) for r in rank_rows]
    dispersion = {
        "leader_return_pct": max(returns) if returns else None,
        "laggard_return_pct": min(returns) if returns else None,
        "spread_pct": round((max(returns) - min(returns)), 2) if returns else None,
    }

    context = {
        "range": sim.get("range"),
        "season": sim.get("season"),
        "diagnostics": sim.get("diagnostics"),
        "champion": ranking.get("champion") or (rank_rows[0] if rank_rows else {}),
        "ranking": rank_rows[:8],
        "ranking_dispersion": dispersion,
        "top_open_positions": pos_rows,
        "theme_exposure": theme_exposure(positions),
        "overlapping_symbols": overlapping_symbols(positions),
        "agent_theses": theses,
        "debate_agenda": [],
        "external_news_enabled": False,
        "news_rule": "No external news is supplied. Do not invent headlines, macro events, company news, earnings, guidance, or fundamentals.",
        "disclaimer": (config.get("arena") or {}).get("disclaimer"),
    }
    context["debate_agenda"] = build_debate_agenda(context)
    return context


def line_is_too_generic(body: str) -> bool:
    b = body.lower()
    if any(x in b for x in BANNED_SUBSTRINGS):
        return True
    # Reject lines that sound like canned motivational chatter.
    weak_patterns = [
        "let's keep",
        "stay sharp",
        "the market is unpredictable",
        "discipline is key",
        "we need to be cautious",
        "watch for signs",
        "could yield",
        "might surprise",
        "broader narrative landscape",
    ]
    return any(p in b for p in weak_patterns)


def professional_density_score(lines: list[dict[str, Any]]) -> float:
    if not lines:
        return 0.0
    count = 0
    for row in lines:
        body = str(row.get("body") or "").lower()
        if any(term in body for term in PRO_TERMS):
            count += 1
        if re.search(r"[+-]?\d+(\.\d+)?%", body):
            count += 1
    return count / max(1, len(lines))


def build_ai_discussion(context: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], bool, str]:
    master = config.get("market_master") or config.get("global_market_analyst") or {}
    model = (
        os.getenv("OPENAI_MODEL_MINI")
        or master.get("model")
        or (config.get("arena") or {}).get("default_model")
        or "gpt-4o-mini"
    )

    system = """
You generate Neon Tokyo AI Arena discussion JSON.

Core identity:
- The speakers are professional synthetic portfolio managers, not chatbots.
- They debate real simulated Agent portfolios, ranking, open positions, alpha, drawdown, liquidity, holding period, and risk budget.
- Their comments should feel like an institutional portfolio review in a retro game arena.

Use ONLY the provided simulation facts.
Do NOT invent:
- external news
- macro events
- geopolitics
- company fundamentals
- earnings
- guidance
- target prices
- recommendations

Output valid JSON with exactly these keys:
{
  "daily_brief": {
    "title": string,
    "body": string,
    "risk_note": string
  },
  "feed": [
    {
      "agent_id": string,
      "type": "debate"|"challenge"|"risk_check"|"position_check"|"ranking_reaction"|"theme_exposure"|"portfolio_review",
      "body": string,
      "linked_symbol": string|null,
      "linked_theme": string|null
    }
  ]
}

Daily brief rules:
- 2 to 3 sentences total.
- Mention the season leader, return spread, and one live position or theme concentration.
- No raw JSON, no field names.

Feed rules:
- 24 to 32 lines.
- Each line must react to a previous line OR a concrete fact from ranking/positions.
- At least 70% of lines must contain a concrete number, symbol, rank, return, equity, drawdown, holding-days, or position fact.
- Use professional concepts: alpha, drawdown, liquidity, position sizing, risk budget, factor exposure, holding period, entry quality, concentration, scalability.
- Mention only symbols and themes present in the input.
- Do not talk about fundamentals unless the input explicitly provides fundamentals. It does not.
- Do not use generic phrases like "hidden gems", "exciting opportunities", "monitor closely", "proceed with caution", "discipline is key".
- Keep each body under 230 characters.
- No buy/sell/recommend/target/guarantee language.
- The debate should have tension: leader gets challenged, laggard defends process, risk agent critiques drawdown, theme agent reframes exposure, discovery agent argues under-watched edge, contrarian agent questions crowding.
"""

    result = call_openai_json(model, system, context, int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "7000")))
    if not result:
        return {}, True, "fallback_no_ai"

    feed = result.get("feed")
    brief = result.get("daily_brief")
    if not isinstance(feed, list) or len(feed) < 12 or not isinstance(brief, dict):
        return {}, True, "fallback_bad_schema"

    allowed_symbols = {p.get("symbol") for p in context.get("top_open_positions", []) if p.get("symbol")}
    allowed_symbols.update({(t.get("largest_position") or {}).get("symbol") for t in context.get("agent_theses", []) if (t.get("largest_position") or {}).get("symbol")})
    allowed_themes = {p.get("theme") for p in context.get("top_open_positions", []) if p.get("theme")}
    allowed_agents = {t.get("agent_id") for t in context.get("agent_theses", []) if t.get("agent_id")}
    agent_name_by_id = {t.get("agent_id"): t.get("agent_name") for t in context.get("agent_theses", [])}

    sanitized: list[dict[str, Any]] = []
    base = now_jst().replace(second=0, microsecond=0)

    for row in feed[:36]:
        if not isinstance(row, dict):
            continue
        raw_body = str(row.get("body") or "")
        body = safe_text(raw_body, 260)
        if not body or line_is_too_generic(body):
            continue

        mentions = symbol_mentions(body)
        if any(sym not in allowed_symbols for sym in mentions):
            continue

        aid = row.get("agent_id")
        if aid not in allowed_agents:
            # Keep conversation going rather than failing hard, but map unknown
            # speakers to the next real agent.
            if not context.get("agent_theses"):
                continue
            aid = context["agent_theses"][len(sanitized) % len(context["agent_theses"])]["agent_id"]

        linked_symbol = row.get("linked_symbol")
        if linked_symbol not in allowed_symbols:
            linked_symbol = next(iter(mentions), None)
        if linked_symbol not in allowed_symbols:
            linked_symbol = None

        linked_theme = row.get("linked_theme")
        if linked_theme not in allowed_themes:
            linked_theme = None

        sanitized.append({
            "id": f"feed_{len(sanitized) + 1:03d}",
            "show_at": iso_jst(base + timedelta(minutes=len(sanitized) * 10)),
            "agent_id": aid,
            "agent_name": agent_name_by_id.get(aid, aid),
            "type": row.get("type") or "debate",
            "body": body,
            "linked_symbol": linked_symbol,
            "linked_theme": linked_theme,
        })

    # Quality gate. We want professional, fact-linked discussion. If mini gives
    # generic lines, fallback is better than showing low-quality AI chatter.
    if len(sanitized) < 12:
        return {}, True, "fallback_quality_guard_short"
    if professional_density_score(sanitized) < 0.72:
        return {}, True, "fallback_quality_guard_low_density"

    result["feed"] = sanitized[:32]
    result["daily_brief"] = {
        "analyst_id": "market_master",
        "title": safe_text(brief.get("title"), 90) or "Arena portfolio review",
        "body": safe_text(brief.get("body"), 460),
        "risk_note": safe_text(brief.get("risk_note"), 280),
    }
    return result, False, "ok_pro_debate"


def fallback_debate(theses: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    """Last-resort debate if AI is unavailable.

    This is not the preferred mode, but it must be professional and factual.
    """
    base = now_jst().replace(second=0, microsecond=0)
    ordered = sorted(theses, key=lambda x: to_int(x.get("rank"), 999))
    positions = context.get("top_open_positions", [])
    ranking = context.get("ranking", [])
    lines: list[dict[str, Any]] = []

    def add(agent: dict[str, Any], body: str, typ: str = "debate", symbol: str | None = None, theme: str | None = None) -> None:
        lines.append({
            "id": f"feed_{len(lines) + 1:03d}",
            "show_at": iso_jst(base + timedelta(minutes=len(lines) * 10)),
            "agent_id": agent.get("agent_id"),
            "agent_name": agent.get("agent_name"),
            "type": typ,
            "body": safe_text(body, 260),
            "linked_symbol": symbol,
            "linked_theme": theme,
        })

    if not ordered:
        return []

    leader = ordered[0]
    laggard = ordered[-1]
    add(leader, f"My book leads at rank #{leader.get('rank')} with {fmt_pct(leader.get('return_pct'))}. The question is whether the equity curve is repeatable or just one position carrying the month.", "ranking_reaction")
    add(laggard, f"I am last at rank #{laggard.get('rank')}, but I would rather defend process than chase another agent's factor exposure. Return is not edge without drawdown control.", "challenge")

    if positions:
        best = sorted(positions, key=lambda p: to_float(p.get("unrealized_return_pct")), reverse=True)[0]
        worst = sorted(positions, key=lambda p: to_float(p.get("unrealized_return_pct")))[0]
        # Rotate through agents with specific roles.
        for i, agent in enumerate(ordered):
            p = positions[i % len(positions)]
            add(agent, f"{p.get('symbol')} is {fmt_pct(p.get('unrealized_return_pct'))} unrealized after {p.get('holding_days', 'n/a')} days. I care less about the label and more about whether that P/L survives the next rebalance.", "position_check", p.get("symbol"), p.get("theme"))
        add(leader, f"The strongest live mark is {best.get('symbol')} at {fmt_pct(best.get('unrealized_return_pct'))}. That helps the leaderboard, but it also concentrates the narrative risk.", "portfolio_review", best.get("symbol"), best.get("theme"))
        add(laggard, f"The weakest live mark is {worst.get('symbol')} at {fmt_pct(worst.get('unrealized_return_pct'))}. A bad mark is useful only if it exposes a rule that needs tightening.", "risk_check", worst.get("symbol"), worst.get("theme"))

    for t in context.get("theme_exposure", [])[:4]:
        agent = ordered[len(lines) % len(ordered)]
        add(agent, f"{t.get('theme')} now carries {t.get('positions')} open positions and {fmt_pct(t.get('gross_unrealized_pct'))} aggregate unrealized P/L. That is theme exposure, not diversification.", "theme_exposure", None, t.get("theme"))

    # Fill to first-screen density with differentiated process remarks.
    while len(lines) < 24:
        agent = ordered[len(lines) % len(ordered)]
        add(agent, f"{agent.get('agent_name')} stays with its process: rank #{agent.get('rank')}, {fmt_pct(agent.get('return_pct'))} return, {agent.get('open_positions')} open positions. The Arena should reward process, not noise.", "debate")

    return lines[:32]


def fallback_brief(context: dict[str, Any]) -> dict[str, str]:
    ranking = context.get("ranking", [])
    leader = ranking[0] if ranking else {}
    spread = ((context.get("ranking_dispersion") or {}).get("spread_pct"))
    top_pos = (context.get("top_open_positions") or [{}])[0]
    title = "Arena portfolio review"
    body = (
        f"{leader.get('name', 'The leading agent')} leads the season at {fmt_pct(leader.get('return_pct'))}; "
        f"leader-laggard spread is {fmt_pct(spread)}. "
        f"The largest live position impact is {top_pos.get('symbol', 'n/a')} at {fmt_pct(top_pos.get('unrealized_return_pct'))} unrealized."
    )
    risk = "External news is disabled; this discussion is based only on simulated positions, ranking, and risk metrics."
    return {"analyst_id": "market_master", "title": title, "body": body, "risk_note": risk}


def build_payload(
    config: dict[str, Any],
    sim: dict[str, Any],
    positions: dict[str, Any],
    ranking: dict[str, Any],
    context: dict[str, Any],
    ai_payload: dict[str, Any],
    fallback: bool,
    status: str,
) -> dict[str, Any]:
    if fallback:
        feed = fallback_debate(context["agent_theses"], context)
        daily_brief = fallback_brief(context)
    else:
        feed = ai_payload["feed"]
        daily_brief = ai_payload["daily_brief"]

    return {
        "schema_version": "neon_tokyo_ai_arena_discussion_v2_1",
        "generated_at": iso_jst(now_jst()),
        "market": "Japan",
        "timezone": "Asia/Tokyo",
        "season": sim.get("season"),
        "range": sim.get("range"),
        "ai": {
            "enabled": ai_enabled(),
            "model": os.getenv("OPENAI_MODEL_MINI", "gpt-4o-mini"),
            "status": status,
            "fallback_used": fallback,
            "external_news_enabled": False,
            "debate_style": "professional_portfolio_review",
        },
        "daily_brief": daily_brief,
        "market_context": context,
        "agents": [
            {
                "agent_id": a.get("agent_id"),
                "name": a.get("name"),
                "class": a.get("class"),
                "selection_profile": a.get("selection_profile"),
                "ui_tone": a.get("ui_tone"),
                "avatar_style": a.get("avatar_style"),
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

    if not sim or not positions or not ranking:
        raise SystemExit(
            "Missing AI Arena simulation/positions/ranking JSON. "
            "Run rebuild_ai_arena_simulation_jp.py first."
        )

    context = build_context(sim, positions, ranking, config)
    ai_payload, fallback, status = build_ai_discussion(context, config)
    payload = build_payload(config, sim, positions, ranking, context, ai_payload, fallback, status)

    write_json(DISCUSSION_OUT, payload)
    # Keep legacy latest.json for the existing renderer / external links.
    write_json(LEGACY_OUT, payload)

    print(
        "AI Arena discussion result: "
        f"status={payload['ai']['status']} "
        f"fallback={payload['ai']['fallback_used']} "
        f"feed_lines={len(payload.get('feed') or [])}"
    )


if __name__ == "__main__":
    main()
