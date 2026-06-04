from __future__ import annotations

"""AI Arena Live Lab v5 engine.

This module is intentionally self-contained enough to make future maintenance
clear.  It reads existing Arena JSON artifacts, builds market/evidence context,
asks GPT-4o for professional evidence-bound dialogue, validates identity and
quality, updates a hypothesis ledger, and writes static-site JSON payloads.
"""

import json
import math
import os
import random
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from .market_context_jp import build_market_context
except Exception:  # pragma: no cover
    from market_context_jp import build_market_context  # type: ignore

JST = timezone(timedelta(hours=9))

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
AGENT_PROFILES = {
    "daily_striker": {"state": "SCANNING MOMENTUM", "role": "Today's Momentum Signal", "style_label": "Daily Momentum / Price Acceleration", "voice": "fast, direct, aggressive, focused on price acceleration and confirmation", "edge": "detects pressure before it becomes consensus", "weakness": "can overpay for speed when noise is high"},
    "weekly_sage": {"state": "READING FLOW", "role": "Weekly Trend Flow", "style_label": "Medium-Term Trend / Flow", "voice": "calm, structural, skeptical of one-day moves, focused on persistence", "edge": "holds winners while trend structure remains intact", "weakness": "accepts uncomfortable drawdown to let flow breathe"},
    "risk_sentinel": {"state": "RISK GATE ACTIVE", "role": "Defensive Risk Quant", "style_label": "Risk / Capital Preservation", "voice": "protective, precise, audits drawdown, sizing, concentration, and opportunity cost", "edge": "keeps the Arena alive when other agents chase heat", "weakness": "may surrender upside by demanding too much safety"},
    "discovery_scout": {"state": "HUNTING EARLY SIGNALS", "role": "Hidden Alpha Discovery", "style_label": "Small Cap / Early Discovery", "voice": "curious, early, energetic, hunts overlooked signals before they are obvious", "edge": "finds clean early repricing before the leaderboard notices", "weakness": "one sharp winner can mask low hit-rate exploration"},
    "contrarian_monk": {"state": "WAITING FOR PULLBACK", "role": "Patient Pullback Hunter", "style_label": "Pullback / Patient Reversal", "voice": "minimalist, patient, dry, refuses bad entries and treats waiting as a weapon", "edge": "avoids paying the first-entry tax when others chase", "weakness": "flat positions can become dead capital"},
    "reversal_snapback": {"state": "SNAPBACK WATCH", "role": "Snapback Reversal Signal", "style_label": "Oversold Reversal / Snapback", "voice": "quick, playful but exact, watches compression, exhaustion, and rebound capture", "edge": "sees rebound asymmetry where others only see damage", "weakness": "winning often is not enough if payoff capture is too small"},
    "value_mispricing": {"state": "TESTING MISPRICING", "role": "Mispricing and Valuation Signal", "style_label": "Value / Mispricing / Re-rating", "voice": "intellectual, exacting, trap-aware, separates price movement from value evidence", "edge": "filters value traps and protects against false bargains", "weakness": "can wait too long while faster agents harvest price action"},
}

SESSION_CONFIG = {
    "open_council": {"title": "Open +30m Council", "phase": "open", "target": 12, "min": 9, "tone": "fast, sharp, tense, early-session, not over-interpreting", "purpose": "Opening reaction, first confirmation, failed setups, and risk gates."},
    "midday_council": {"title": "Midday Council", "phase": "midday", "target": 14, "min": 10, "tone": "cool, analytical, focused on persistence versus fade", "purpose": "Judge whether morning moves persisted or faded and define afternoon watch conditions."},
    "close_council": {"title": "Post-Close Council", "phase": "post_close", "target": 22, "min": 18, "tone": "deep, decisive, flagship daily investment committee", "purpose": "Explain winners, losers, risk, attribution, executions, and tomorrow's tests."},
    "night_strategy_lab": {"title": "Night Strategy Lab", "phase": "closed_market_night", "target": 18, "min": 14, "tone": "intellectual, reflective, slightly human, dry humor allowed", "purpose": "Closed-market reflection, tomorrow hypotheses, strategy clash, and memory updates."},
    "weekly_arena_review": {"title": "Weekly Arena Review", "phase": "weekend_review", "target": 28, "min": 22, "tone": "longer, editorial, analytical, diagnostic", "purpose": "Weekly attribution, agent diagnostics, failure modes, and next-week hypotheses."},
}

SCENE_MODES = ["investment_committee", "risk_intervention", "strategy_clash", "post_trade_autopsy", "alpha_discovery", "value_trial", "snapback_watch", "night_debate", "heated_argument", "dry_humor"]
GENERIC_BANNED = ["raises concerns", "should be monitored", "future sessions will confirm", "it remains to be seen", "market noise", "stay vigilant", "calm before the storm", "potential energy", "only time will tell", "signal or luck"]
ADVICE_BANNED = ["strong buy", "strong sell", "target price", "guaranteed", "easy money", "you should buy", "you should sell", "must buy", "must sell"]


def read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def now_jst() -> datetime:
    return datetime.now(JST)


def fmt_pct(value: Any) -> str:
    try:
        x = float(value)
        if not math.isfinite(x):
            return "n/a"
        return f"{x:+.2f}%"
    except Exception:
        return "n/a"


def fmt_jpy(value: Any) -> str:
    try:
        return f"¥{float(value):,.0f}"
    except Exception:
        return "¥0"


def slug_text(value: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return s[:64] or "item"


def infer_session_type(env_value: str | None = None, dt: datetime | None = None) -> str:
    value = (env_value or "auto").strip().lower()
    if value and value != "auto":
        return value if value in SESSION_CONFIG else "close_council"
    dt = dt or now_jst()
    if dt.weekday() >= 5:
        return "weekly_arena_review"
    minutes = dt.hour * 60 + dt.minute
    if 9 * 60 <= minutes <= 10 * 60 + 30:
        return "open_council"
    if 11 * 60 + 30 <= minutes <= 13 * 60:
        return "midday_council"
    if 15 * 60 <= minutes <= 17 * 60:
        return "close_council"
    if 20 * 60 <= minutes <= 22 * 60:
        return "night_strategy_lab"
    return "close_council"


@dataclass
class Settings:
    root: Path
    out_dir: Path
    model: str = "gpt-4o"
    session_type: str = "auto"
    min_delay_seconds: int = 180
    max_delay_seconds: int = 300
    history_days: int = 14
    temperature: float = 0.82
    openai_min_interval_seconds: float = 30.0
    openai_max_retries: int = 8
    openai_429_base_sleep_seconds: float = 75.0
    market_context_enabled: bool = True
    mock_openai: bool = False


class OpenAIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.last_call_ts = 0.0
        self.rate_limit_encountered = False

    def chat_json(self, *, system: str, user: dict[str, Any], temperature: float | None = None) -> dict[str, Any]:
        if self.settings.mock_openai:
            return self._mock(user)
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required. Set the GitHub Actions secret named OPENAI_API_KEY.")
        elapsed = time.time() - self.last_call_ts
        if elapsed < self.settings.openai_min_interval_seconds:
            time.sleep(self.settings.openai_min_interval_seconds - elapsed)
        body = {
            "model": self.settings.model,
            "temperature": temperature if temperature is not None else self.settings.temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(1, self.settings.openai_max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                self.last_call_ts = time.time()
                content = payload.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                return parse_json_object(content)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 429:
                    self.rate_limit_encountered = True
                    retry_after = exc.headers.get("Retry-After")
                    try:
                        wait = max(self.settings.openai_429_base_sleep_seconds, float(retry_after or 0))
                    except Exception:
                        wait = self.settings.openai_429_base_sleep_seconds
                    wait = wait + min(60, attempt * 15)
                    print(f"WARN OpenAI 429 attempt {attempt}/{self.settings.openai_max_retries}; sleeping {wait:.0f}s")
                    time.sleep(wait)
                    continue
                raise
            except Exception as exc:
                last_error = exc
                wait = min(60, attempt * 5)
                print(f"WARN OpenAI attempt {attempt}/{self.settings.openai_max_retries} failed: {exc}; sleeping {wait}s")
                time.sleep(wait)
        raise RuntimeError(f"OpenAI generation failed after retries: {last_error}")

    def _mock(self, user: dict[str, Any]) -> dict[str, Any]:
        if user.get("task") == "generate_council_verdict":
            return {"council_verdict": {"headline": "Mock council verdict", "market_read": "Market context is being tested.", "strongest_signal": "NAGARE remains the benchmark.", "main_risk": "Concentration risk remains the main audit item.", "next_test": "Check whether the same alpha persists next session.", "confidence": "medium"}, "daily_brief": {"headline": "Mock Live Lab Brief", "summary": "Mock generation path validated.", "bullets": ["Mock bullet with evidence", "Mock hypothesis pending"]}}
        if user.get("task") == "generate_thinking_states":
            return {"agent_thinking_states": [{"agent_id": aid, "state": AGENT_PROFILES[aid]["state"].title(), "focus": "Mock focus", "current_question": "What needs confirmation next?", "confidence": 0.6, "stress_level": 0.4} for aid in CANONICAL_NAMES]}
        # topic dialogue
        messages = []
        cast = user.get("speaker_cast", [])
        topic = user.get("topic", {})
        for i, sp in enumerate(cast):
            ev = topic.get("evidence_numbers", ["+1.00%"])
            body = f"{topic.get('headline','This topic')} needs a concrete test. {sp.get('agent_name')} reads {ev[0] if ev else 'the evidence'} as process evidence, not a slogan, and asks what would invalidate it next session."
            messages.append({"agent_id": sp["agent_id"], "message_type": "challenge" if i % 2 else "evidence", "reply_to_agent": cast[i-1]["agent_name"] if i else "", "body": body, "evidence_label": topic.get("headline", "Evidence"), "evidence_numbers": ev[:3], "linked_symbol": (topic.get("linked_symbols") or [""])[0], "linked_name": "", "why_it_matters": topic.get("why_it_matters", "It connects evidence to a next test."), "mood": "analytical"})
        return {"messages": messages}


def parse_json_object(content: str) -> dict[str, Any]:
    try:
        obj = json.loads(content)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    m = re.search(r"\{.*\}", content, flags=re.S)
    if m:
        obj = json.loads(m.group(0))
        if isinstance(obj, dict):
            return obj
    raise ValueError("OpenAI response did not contain a valid JSON object")


def load_arena_context(base: Path) -> dict[str, Any]:
    live = read_json(base / "live/latest.json", {})
    ranking_payload = read_json(base / "ranking/latest.json", {})
    positions_payload = read_json(base / "positions/latest.json", {})
    summary_payload = read_json(base / "summary/latest.json", {})
    data = live.get("data", live) if isinstance(live, dict) and live else {}
    agents = data.get("agents") or ranking_payload.get("agents") or []
    ranking = data.get("ranking") or ranking_payload.get("ranking") or []
    open_positions = data.get("open_positions") or positions_payload.get("open_positions") or []
    recent_trades = data.get("recent_trades") or positions_payload.get("closed_trades", [])[:50]
    portfolio = data.get("portfolio") or positions_payload.get("portfolio") or summary_payload.get("portfolio") or {}
    trade_stats = data.get("trade_stats") or ranking_payload.get("trade_stats") or summary_payload.get("trade_stats") or []
    return {"agents": agents, "ranking": ranking, "open_positions": open_positions, "recent_trades": recent_trades, "portfolio": portfolio, "trade_stats": trade_stats, "raw": data}


def normalize_agents(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    ranking_by_agent = {r.get("agent_id"): r for r in ctx.get("ranking", [])}
    out = []
    seen = set()
    source_agents = ctx.get("agents") or []
    for aid, name in CANONICAL_NAMES.items():
        src = next((a for a in source_agents if a.get("agent_id") == aid), {})
        r = ranking_by_agent.get(aid, {})
        profile = AGENT_PROFILES[aid]
        ret = r.get("total_return_pct", r.get("return_pct", 0.0))
        mdd = r.get("max_drawdown_pct", 0.0)
        win = r.get("win_rate_pct", 0.0)
        image = src.get("image") or f"/assets/ai-arena/agents/{aid}.png"
        out.append({
            "agent_id": aid,
            "name": name,
            "role": src.get("role") or profile["role"],
            "style_label": src.get("style_label") or profile["style_label"],
            "description": src.get("description") or src.get("short_description") or profile["edge"],
            "voice": profile["voice"],
            "edge": profile["edge"],
            "weakness": profile["weakness"],
            "state": profile["state"],
            "image": image,
            "color": CANONICAL_COLORS[aid],
            "rank": r.get("rank", None),
            "return_pct": ret,
            "return_label": fmt_pct(ret),
            "mdd_label": fmt_pct(mdd),
            "win_rate_label": fmt_pct(win),
            "trade_count": int(r.get("trade_count", 0) or 0),
        })
        seen.add(aid)
    return out


def normalize_ranking(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    open_counts: dict[str, int] = {}
    for p in ctx.get("open_positions", []):
        open_counts[p.get("agent_id", "")] = open_counts.get(p.get("agent_id", ""), 0) + 1
    for r in sorted(ctx.get("ranking", []), key=lambda x: x.get("rank", 999)):
        aid = r.get("agent_id")
        if aid not in CANONICAL_NAMES:
            continue
        ret = r.get("total_return_pct", r.get("return_pct", 0.0))
        equity = r.get("end_equity_jpy", r.get("equity_jpy", 0.0))
        out.append({"rank": r.get("rank"), "agent_id": aid, "name": CANONICAL_NAMES[aid], "return_pct": ret, "return_label": fmt_pct(ret), "equity_jpy": equity, "equity_label": fmt_jpy(equity), "max_drawdown_pct": r.get("max_drawdown_pct", 0.0), "mdd_label": fmt_pct(r.get("max_drawdown_pct", 0.0)), "win_rate_pct": r.get("win_rate_pct", 0.0), "win_rate_label": fmt_pct(r.get("win_rate_pct", 0.0)), "trade_count": r.get("trade_count", 0), "open_count": open_counts.get(aid, 0)})
    return out


def normalize_positions(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    total = sum(float(p.get("market_value_jpy") or 0) for p in ctx.get("open_positions", [])) or 0.0
    out = []
    for p in ctx.get("open_positions", []):
        aid = p.get("agent_id")
        item = dict(p)
        item["agent_name"] = CANONICAL_NAMES.get(aid, aid)
        item["pnl_pct"] = p.get("unrealized_return_pct", p.get("pnl_pct", 0.0))
        item["pnl_label"] = fmt_pct(item["pnl_pct"])
        mv = float(p.get("market_value_jpy") or 0)
        item["weight_pct"] = round((mv / total * 100), 3) if total else 0.0
        item.setdefault("bucket", "")
        out.append(item)
    return out


def build_topics(ranking: list[dict[str, Any]], positions: list[dict[str, Any]], portfolio: dict[str, Any], recent_trades: list[dict[str, Any]], memory: dict[str, Any]) -> list[dict[str, Any]]:
    topics: list[dict[str, Any]] = []
    if ranking:
        leader = ranking[0]
        topics.append({"topic_id": f"leaderboard_battle_{leader['agent_id']}", "topic_type": "leaderboard_battle", "priority": 110, "headline": f"{leader['name']} leads at {leader['return_label']}, but risk-adjusted quality is still open for debate", "editorial_angle": "Debate raw return versus drawdown, win rate, and repeatability.", "evidence_numbers": [f"#{leader['rank']} {leader['name']}", f"return {leader['return_label']}", f"MDD {leader['mdd_label']}", f"win rate {leader['win_rate_label']}"], "linked_symbols": [], "required_agents": [leader["agent_id"], "risk_sentinel"], "challenger_agents": ["value_mispricing", "contrarian_monk", "daily_striker"], "why_it_matters": "Readers need to know whether leadership is durable alpha or simply the highest-risk style currently rewarded."})
    if positions:
        best = max(positions, key=lambda x: float(x.get("pnl_pct") or 0))
        if float(best.get("pnl_pct") or 0) > 0:
            aid = best.get("agent_id")
            topics.append({"topic_id": f"best_open_alpha_{slug_text(best.get('ticker','position'))}", "topic_type": "best_open_alpha", "priority": 104, "headline": f"{CANONICAL_NAMES.get(aid, aid)} owns the cleanest open alpha: {best.get('ticker')} {best.get('pnl_label')}", "editorial_angle": "Test whether the open gain reflects repeatable process, regime help, or one-position noise.", "evidence_numbers": [f"{best.get('ticker')} {best.get('name')}", f"open return {best.get('pnl_label')}", f"holding days {best.get('holding_days')}", f"agent {CANONICAL_NAMES.get(aid, aid)}"], "linked_symbols": [best.get("ticker")], "required_agents": [aid, "risk_sentinel", "value_mispricing"], "challenger_agents": ["daily_striker", "weekly_sage"], "why_it_matters": "The strongest live position should be tested for alpha quality rather than celebrated blindly."})
        flat = sorted([p for p in positions if abs(float(p.get("pnl_pct") or 0)) < 0.01], key=lambda x: int(x.get("holding_days") or 0), reverse=True)
        if flat:
            p = flat[0]
            aid = p.get("agent_id")
            topics.append({"topic_id": f"dead_capital_{slug_text(p.get('ticker','position'))}", "topic_type": "dead_capital", "priority": 88, "headline": f"{p.get('ticker')} is flat after {p.get('holding_days')} days: setup compression or dead capital?", "editorial_angle": "Force a debate between patience, opportunity cost, and failed confirmation.", "evidence_numbers": [f"{p.get('ticker')} {p.get('name')}", f"open return {p.get('pnl_label')}", f"holding days {p.get('holding_days')}", f"agent {CANONICAL_NAMES.get(aid, aid)}"], "linked_symbols": [p.get("ticker")], "required_agents": [aid, "risk_sentinel"], "challenger_agents": ["daily_striker", "reversal_snapback", "value_mispricing"], "why_it_matters": "Flat positions consume capital and attention even when price risk looks quiet."})
    best_contrib = (portfolio.get("best_ticker_contribution") or [])[:1]
    if best_contrib:
        b = best_contrib[0]
        topics.append({"topic_id": f"performance_attribution_{slug_text(b.get('ticker',''))}", "topic_type": "performance_attribution", "priority": 100, "headline": f"Attribution check: {b.get('ticker')} has contributed {fmt_jpy(b.get('total_pnl_jpy'))}", "editorial_angle": "Separate repeatable process from a few large historical contributors.", "evidence_numbers": [f"best contributor {b.get('ticker')}", f"total P/L {fmt_jpy(b.get('total_pnl_jpy'))}", f"closed trades {int(float(b.get('closed_trades') or 0))}"], "linked_symbols": [b.get("ticker")], "required_agents": ["value_mispricing", "weekly_sage"], "challenger_agents": ["risk_sentinel", "discovery_scout"], "why_it_matters": "Attribution shows whether current leadership is backed by repeatable engines or a few winners."})
    allocations = portfolio.get("allocation_by_agent") or []
    if allocations:
        top = max(allocations, key=lambda x: float(x.get("weight_pct") or 0))
        aid = top.get("agent_id")
        topics.append({"topic_id": f"concentration_risk_{aid}", "topic_type": "risk_council", "priority": 96, "headline": f"{CANONICAL_NAMES.get(aid, aid)} controls {float(top.get('weight_pct') or 0):.1f}% of open market value", "editorial_angle": "Discuss whether Arena returns are diversified or style-concentrated.", "evidence_numbers": [f"allocation {float(top.get('weight_pct') or 0):.1f}%", f"positions {int(top.get('position_count') or 0)}", f"unrealized P/L {fmt_jpy(top.get('unrealized_pnl_jpy'))}"], "linked_symbols": [], "required_agents": ["risk_sentinel", aid], "challenger_agents": ["value_mispricing", "contrarian_monk"], "why_it_matters": "Style concentration can make the Arena look stronger than its diversification really is."})
    for r in ranking:
        if r.get("agent_id") == "reversal_snapback" and float(r.get("win_rate_pct") or 0) > 49:
            topics.append({"topic_id": "payoff_ratio_kaeshi", "topic_type": "strategy_clash", "priority": 86, "headline": f"KAESHI wins often enough but ranks low: {r['win_rate_label']} win rate, {r['return_label']} return", "editorial_angle": "Discuss payoff capture: a strategy can be directionally right but economically weak.", "evidence_numbers": [f"KAESHI return {r['return_label']}", f"win rate {r['win_rate_label']}", f"MDD {r['mdd_label']}", f"trades {r.get('trade_count')}"] , "linked_symbols": [], "required_agents": ["reversal_snapback", "risk_sentinel"], "challenger_agents": ["contrarian_monk", "value_mispricing"], "why_it_matters": "Win rate alone does not prove economic edge when payoff capture is too small."})
            break
    ledger = memory.get("hypothesis_ledger") or []
    pending = [h for h in ledger if h.get("status") in {"pending", "strengthening", "weakening"}]
    if pending:
        h = pending[0]
        topics.append({"topic_id": f"memory_review_{h.get('hypothesis_id','hyp')}", "topic_type": "memory_review", "priority": 92, "headline": f"Memory review: {h.get('owner_agent_name')} must revisit {h.get('linked_symbol') or 'an open hypothesis'}", "editorial_angle": "Review whether an earlier claim is strengthening, weakening, or still unresolved.", "evidence_numbers": h.get("evidence_at_creation", [])[:4] or [h.get("claim", "prior hypothesis")], "linked_symbols": [h.get("linked_symbol")] if h.get("linked_symbol") else [], "required_agents": [h.get("owner_agent_id", "value_mispricing"), "value_mispricing"], "challenger_agents": ["risk_sentinel", "weekly_sage"], "why_it_matters": "A real lab should remember what it claimed and test whether the claim is improving or failing."})
    seen = set()
    clean = []
    for t in sorted(topics, key=lambda x: x["priority"], reverse=True):
        if t["topic_id"] in seen:
            continue
        t["linked_symbols"] = [s for s in t.get("linked_symbols", []) if s]
        t["required_agents"] = list(dict.fromkeys([a for a in t.get("required_agents", []) if a in CANONICAL_NAMES]))
        t["challenger_agents"] = list(dict.fromkeys([a for a in t.get("challenger_agents", []) if a in CANONICAL_NAMES and a not in t["required_agents"]]))
        clean.append(t)
        seen.add(t["topic_id"])
    return clean[:10]


def scene_profile(session_type: str, seed: int | None = None) -> dict[str, Any]:
    rnd = random.Random(seed or int(time.time()))
    if session_type == "night_strategy_lab":
        modes = ["night_debate", "strategy_clash", "value_trial", "dry_humor"]
        humor = rnd.choice([1, 1, 2])
        intensity = rnd.uniform(0.45, 0.78)
    elif session_type == "weekly_arena_review":
        modes = ["investment_committee", "post_trade_autopsy", "value_trial"]
        humor = rnd.choice([0, 1])
        intensity = rnd.uniform(0.35, 0.65)
    elif session_type == "open_council":
        modes = ["risk_intervention", "strategy_clash", "snapback_watch"]
        humor = 0
        intensity = rnd.uniform(0.65, 0.9)
    else:
        modes = SCENE_MODES[:7]
        humor = rnd.choice([0, 0, 1])
        intensity = rnd.uniform(0.45, 0.82)
    return {"scene_mode": rnd.choice(modes), "scene_intensity": round(intensity, 2), "humor_budget": humor, "conflict_budget": rnd.randint(2, 5), "macro_influence": round(rnd.uniform(0.35, 0.75), 2), "memory_influence": round(rnd.uniform(0.25, 0.65), 2), "closing_agent": rnd.choice(list(CANONICAL_NAMES))}


def cast_speakers(topic: dict[str, Any], scene: dict[str, Any], target: int, rng: random.Random) -> list[dict[str, Any]]:
    pool = []
    for aid in topic.get("required_agents", []) + topic.get("challenger_agents", []):
        if aid in CANONICAL_NAMES and aid not in pool:
            pool.append(aid)
    for aid in ["risk_sentinel", "value_mispricing", "weekly_sage", "daily_striker", "contrarian_monk", "discovery_scout", "reversal_snapback"]:
        if aid not in pool:
            pool.append(aid)
    count = max(2, min(target, rng.randint(max(2, min(3, target)), min(5, max(2, target)))))
    chosen = pool[:max(2, min(len(pool), count))]
    tail = chosen[1:]
    rng.shuffle(tail)
    chosen = [chosen[0]] + tail
    cast = []
    roles = ["owner_or_primary", "risk_auditor", "challenger", "process_auditor", "closer"]
    for i, aid in enumerate(chosen[:count]):
        cast.append({"agent_id": aid, "agent_name": CANONICAL_NAMES[aid], "state": AGENT_PROFILES[aid]["state"], "color": CANONICAL_COLORS[aid], "role_in_scene": roles[i] if i < len(roles) else "participant", "voice": AGENT_PROFILES[aid]["voice"], "edge": AGENT_PROFILES[aid]["edge"], "weakness": AGENT_PROFILES[aid]["weakness"]})
    return cast


def system_prompt() -> str:
    return """You are the dialogue engine for Neon Tokyo Signals AI Arena Live Lab.

You are simultaneously a senior financial editor, market structure analyst, character dialogue writer, and factual consistency auditor.

Write evidence-bound English dialogue for seven simulated Japanese-equity trading agents. This is not generic chatbot commentary and not investment advice.

Hard rules:
- Use only supplied Arena evidence, market_context, memory, and topic data.
- Do not invent news, catalysts, fundamentals, current prices, target prices, analyst ratings, geopolitical events, or recommendations.
- Use only speaker_cast agents. Do not add, remove, rename, or reorder agent identities.
- Never let one agent claim another agent's return, win rate, drawdown, position, or allocation as "my". If discussing another agent's data, name that agent explicitly.
- Agent state, tone, and reasoning must match the speaker profile.
- Every message must interpret evidence, challenge an assumption, compare strategies, define risk, separate alpha from beta, review memory, or create a next-session test.
- Avoid generic phrases: raises concerns, should be monitored, future sessions will confirm, it remains to be seen, market noise, stay vigilant, calm before the storm, potential energy, only time will tell, signal or luck.
- Humor is allowed only when scene allows it, and it must be dry, brief, and reveal investment philosophy. No meme language.
- Return valid JSON only.
"""


def topic_prompt_payload(session: dict[str, Any], topic: dict[str, Any], cast: list[dict[str, Any]], market_context: dict[str, Any], memory: dict[str, Any], message_target: int) -> dict[str, Any]:
    return {"task": "generate_topic_dialogue", "instructions": {"message_target": message_target, "word_range_per_message": "28-70 words", "must_use_exact_speaker_cast": True, "require_at_least_one_next_test": True}, "session": session, "topic": topic, "speaker_cast": cast, "market_context": market_context, "memory_excerpt": {"hypothesis_ledger": (memory.get("hypothesis_ledger") or [])[:5]}, "output_schema": {"messages": [{"agent_id": "one of speaker_cast", "message_type": "evidence|challenge|rebuttal|risk|alpha_beta|hypothesis|watch|dry_humor|closing", "reply_to_agent": "agent name or empty", "body": "dialogue text", "evidence_label": "short label", "evidence_numbers": ["strings from provided evidence"], "linked_symbol": "symbol or empty", "linked_name": "company name or empty", "why_it_matters": "one concise sentence", "mood": "calm|tense|analytical|challenging|witty"}]}}


def validate_message(msg: dict[str, Any], cast_ids: set[str], topic: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    aid = msg.get("agent_id")
    body = str(msg.get("body") or "")
    if aid not in CANONICAL_NAMES:
        issues.append("unknown_agent")
    if cast_ids and aid not in cast_ids:
        issues.append("speaker_not_in_cast")
    if msg.get("agent_name") and msg.get("agent_name") != CANONICAL_NAMES.get(aid):
        issues.append("agent_name_mismatch")
    if len(body.split()) < 18:
        issues.append("too_short")
    low = body.lower()
    if any(p in low for p in GENERIC_BANNED):
        issues.append("generic_phrase")
    if any(p in low for p in ADVICE_BANNED):
        issues.append("investment_advice")
    # Catch the most common ownership failure: my metric while topic evidence belongs to another agent.
    if re.search(r"\bmy\s+[+\-]?\d+(?:\.\d+)?%", low):
        owner_ids = set(topic.get("required_agents", [])[:1])
        if aid not in owner_ids:
            issues.append("wrong_metric_ownership")
    state = msg.get("state")
    if state and aid in AGENT_PROFILES and state != AGENT_PROFILES[aid]["state"]:
        issues.append("state_mismatch")
    return issues


def normalize_generated_messages(raw: list[dict[str, Any]], cast: list[dict[str, Any]], topic: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    cast_by_id = {c["agent_id"]: c for c in cast}
    cast_ids = set(cast_by_id)
    out: list[dict[str, Any]] = []
    issues: list[str] = []
    seen_bodies: set[str] = set()
    for raw_msg in raw:
        if not isinstance(raw_msg, dict):
            continue
        aid = raw_msg.get("agent_id")
        if aid not in cast_by_id:
            # Do not salvage identity-broken messages; repair can regenerate.
            issues.append("dropped_unknown_speaker")
            continue
        body = re.sub(r"\s+", " ", str(raw_msg.get("body") or "")).strip()
        if not body or body.lower() in seen_bodies:
            issues.append("dropped_empty_or_duplicate")
            continue
        seen_bodies.add(body.lower())
        profile = cast_by_id[aid]
        msg = {
            "agent_id": aid,
            "agent_name": CANONICAL_NAMES[aid],
            "avatar_image": f"/assets/ai-arena/agents/{aid}.png",
            "color": CANONICAL_COLORS[aid],
            "state": AGENT_PROFILES[aid]["state"],
            "mood": raw_msg.get("mood") or "analytical",
            "message_type": raw_msg.get("message_type") or "evidence",
            "reply_to_agent": raw_msg.get("reply_to_agent") or "",
            "body": body,
            "evidence_label": raw_msg.get("evidence_label") or topic.get("headline", "Evidence"),
            "evidence_numbers": [str(x) for x in (raw_msg.get("evidence_numbers") or topic.get("evidence_numbers") or []) if x][:4],
            "linked_symbol": raw_msg.get("linked_symbol") or ((topic.get("linked_symbols") or [""])[0] if topic.get("linked_symbols") else ""),
            "linked_name": raw_msg.get("linked_name") or "",
            "why_it_matters": raw_msg.get("why_it_matters") or topic.get("why_it_matters", "This links the debate to a concrete Arena test."),
            "topic_id": topic.get("topic_id"),
            "topic_type": topic.get("topic_type"),
        }
        msg_issues = validate_message(msg, cast_ids, topic)
        if msg_issues:
            issues.extend(msg_issues)
            continue
        out.append(msg)
    return out, issues


def message_targets_for_topics(session_type: str, topics: list[dict[str, Any]], total_target: int) -> list[int]:
    selected = topics[:7 if session_type != "weekly_arena_review" else 9]
    if not selected:
        return []
    min_each = 2 if session_type != "weekly_arena_review" else 3
    targets = [min_each for _ in selected]
    remain = max(0, total_target - sum(targets))
    i = 0
    while remain > 0:
        cap = 5 if session_type != "weekly_arena_review" else 6
        if targets[i] < cap:
            targets[i] += 1
            remain -= 1
        i = (i + 1) % len(targets)
        if all(t >= cap for t in targets):
            break
    return targets


def generate_dialogue(client: OpenAIClient, session: dict[str, Any], topics: list[dict[str, Any]], market_context: dict[str, Any], memory: dict[str, Any], target: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(hash(session["session_id"]) & 0xFFFFFFFF)
    selected = topics[:7 if session["session_type"] != "weekly_arena_review" else 9]
    targets = message_targets_for_topics(session["session_type"], selected, target)
    all_messages: list[dict[str, Any]] = []
    selected_meta: list[dict[str, Any]] = []
    speaker_counts: dict[str, int] = {}
    max_share_soft = max(3, math.ceil(target * 0.30))
    for idx, (topic, n) in enumerate(zip(selected, targets), start=1):
        cast = cast_speakers(topic, session.get("scene_profile", {}), n, rng)
        # Keep required speakers, but rotate optional participants away from agents
        # already near the soft concentration ceiling. This preserves randomness
        # without letting one persona dominate the whole lab.
        required = set(topic.get("required_agents", [])[:2])
        used_ids = {c["agent_id"] for c in cast}
        for c in cast:
            aid = c["agent_id"]
            if aid in required or speaker_counts.get(aid, 0) < max_share_soft:
                continue
            replacements = [x for x in CANONICAL_NAMES if x not in used_ids and speaker_counts.get(x, 0) < max_share_soft]
            if replacements:
                new_aid = min(replacements, key=lambda x: speaker_counts.get(x, 0))
                c.update({"agent_id": new_aid, "agent_name": CANONICAL_NAMES[new_aid], "state": AGENT_PROFILES[new_aid]["state"], "color": CANONICAL_COLORS[new_aid], "voice": AGENT_PROFILES[new_aid]["voice"], "edge": AGENT_PROFILES[new_aid]["edge"], "weakness": AGENT_PROFILES[new_aid]["weakness"]})
                used_ids.add(new_aid)
        selected_meta.append({**topic, "speaker_cast": cast, "message_target": n})
        payload = topic_prompt_payload(session, topic, cast, market_context, memory, n)
        result = client.chat_json(system=system_prompt(), user=payload)
        raw = result.get("messages") if isinstance(result.get("messages"), list) else []
        messages, issues = normalize_generated_messages(raw, cast, topic)
        if len(messages) < max(2, min(n, len(cast))):
            repair_payload = {**payload, "task": "repair_topic_dialogue", "validation_issues": issues, "repair_instruction": "Regenerate only this topic. Fix identity, ownership, generic phrasing, and evidence support. Return exactly the requested number of messages."}
            result = client.chat_json(system=system_prompt(), user=repair_payload, temperature=max(0.45, client.settings.temperature - 0.1))
            raw = result.get("messages") if isinstance(result.get("messages"), list) else []
            messages, issues = normalize_generated_messages(raw, cast, topic)
        print(f"Topic {topic['topic_id']}: target={n} accepted={len(messages)} issues={len(issues)}")
        accepted = messages[:n]
        for m in accepted:
            speaker_counts[m.get("agent_id", "")] = speaker_counts.get(m.get("agent_id", ""), 0) + 1
        all_messages.extend(accepted)
    return all_messages[:target], selected_meta


def make_session_context(session_type: str, config: dict[str, Any], scene: dict[str, Any], target: int) -> dict[str, Any]:
    ts = now_jst().isoformat(timespec="seconds")
    return {"session_id": f"{now_jst().date().isoformat()}-{session_type}", "session_type": session_type, "session_title": config["title"], "market_phase": config["phase"], "generated_at": ts, "purpose": config["purpose"], "tone": config["tone"], "target_messages": target, "scene_profile": scene}


def generate_verdict(client: OpenAIClient, session: dict[str, Any], topics: list[dict[str, Any]], messages: list[dict[str, Any]], market_context: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    payload = {"task": "generate_council_verdict", "session": session, "topics": topics[:6], "message_summaries": [{"agent": m.get("agent_name"), "type": m.get("message_type"), "body": m.get("body")} for m in messages[:10]], "market_context": market_context, "memory": {"hypothesis_ledger": (memory.get("hypothesis_ledger") or [])[:5]}, "output_schema": {"council_verdict": {"headline": "", "market_read": "", "strongest_signal": "", "main_risk": "", "next_test": "", "confidence": "low|medium|high"}, "daily_brief": {"headline": "", "summary": "", "bullets": ["3-5 bullets"]}}}
    try:
        result = client.chat_json(system=system_prompt(), user=payload, temperature=0.65)
    except Exception as exc:
        raise RuntimeError(f"Council verdict generation failed: {exc}")
    return result


def generate_thinking_states(client: OpenAIClient, session: dict[str, Any], agents: list[dict[str, Any]], topics: list[dict[str, Any]], market_context: dict[str, Any]) -> list[dict[str, Any]]:
    payload = {"task": "generate_thinking_states", "session": session, "agents": agents, "topics": topics[:7], "market_context": market_context, "instructions": "Generate one concise thinking state for each agent. Do not change agent_id. Focus on what they are currently trying to resolve.", "output_schema": {"agent_thinking_states": [{"agent_id": "", "state": "", "focus": "", "current_question": "", "confidence": 0.0, "stress_level": 0.0}]}}
    result = client.chat_json(system=system_prompt(), user=payload, temperature=0.7)
    raw = result.get("agent_thinking_states") if isinstance(result.get("agent_thinking_states"), list) else []
    by_id = {a["agent_id"]: a for a in agents}
    out = []
    for item in raw:
        aid = item.get("agent_id")
        if aid not in by_id:
            continue
        out.append({"agent_id": aid, "agent_name": CANONICAL_NAMES[aid], "color": CANONICAL_COLORS[aid], "avatar_image": by_id[aid].get("image"), "state": str(item.get("state") or AGENT_PROFILES[aid]["state"])[:90], "focus": str(item.get("focus") or AGENT_PROFILES[aid]["edge"])[:160], "current_question": str(item.get("current_question") or "What changes next session?")[:180], "confidence": max(0.0, min(1.0, float(item.get("confidence") or 0.5))), "stress_level": max(0.0, min(1.0, float(item.get("stress_level") or 0.5)))})
    # Fill any missing agent deterministically with data-bound states.
    done = {x["agent_id"] for x in out}
    for a in agents:
        aid = a["agent_id"]
        if aid not in done:
            out.append({"agent_id": aid, "agent_name": CANONICAL_NAMES[aid], "color": CANONICAL_COLORS[aid], "avatar_image": a.get("image"), "state": AGENT_PROFILES[aid]["state"].title(), "focus": AGENT_PROFILES[aid]["edge"], "current_question": "Which evidence would confirm or invalidate the current setup?", "confidence": 0.55, "stress_level": 0.45})
    return out


def update_hypothesis_ledger(memory: dict[str, Any], session: dict[str, Any], messages: list[dict[str, Any]], topics: list[dict[str, Any]]) -> dict[str, Any]:
    memory = dict(memory or {})
    ledger = list(memory.get("hypothesis_ledger") or [])
    ts = now_jst().isoformat(timespec="seconds")
    # Age open hypotheses.
    for h in ledger:
        if h.get("status") in {"pending", "strengthening", "weakening"}:
            h["review_count"] = int(h.get("review_count") or 0) + 1
            if int(h.get("review_count") or 0) >= int(h.get("expires_after_sessions") or 4):
                h["status"] = "expired"
                h["latest_result"] = "Expired without enough confirming evidence."
            else:
                h["last_reviewed_at"] = ts
                h.setdefault("latest_result", "Still pending.")
    # Create up to two new hypotheses from hypothesis/watch/alpha-beta messages.
    candidates = [m for m in messages if m.get("message_type") in {"hypothesis", "watch", "alpha_beta", "closing"}]
    if not candidates:
        candidates = messages[-3:]
    existing_claims = {str(h.get("claim", "")).lower() for h in ledger}
    for m in candidates[:2]:
        claim = str(m.get("body") or "")
        if len(claim.split()) > 32:
            claim = " ".join(claim.split()[:32]) + "..."
        if not claim or claim.lower() in existing_claims:
            continue
        aid = m.get("agent_id") if m.get("agent_id") in CANONICAL_NAMES else "value_mispricing"
        symbol = m.get("linked_symbol") or ""
        hid = f"hyp-{now_jst().strftime('%Y%m%d%H%M')}-{aid}-{slug_text(symbol or claim)[:24]}"
        ledger.insert(0, {"hypothesis_id": hid, "created_at": ts, "owner_agent_id": aid, "owner_agent_name": CANONICAL_NAMES[aid], "linked_symbol": symbol, "linked_name": m.get("linked_name") or "", "claim": claim, "evidence_at_creation": m.get("evidence_numbers") or [], "test_condition": m.get("why_it_matters") or "Revisit the evidence in the next council session.", "status": "pending", "expires_after_sessions": 4 if session["session_type"] != "weekly_arena_review" else 2, "review_count": 0, "last_reviewed_at": "", "latest_result": ""})
        existing_claims.add(claim.lower())
    ledger = ledger[:40]
    memory["hypothesis_ledger"] = ledger
    memory["watch_items"] = [{"created_at": h.get("created_at"), "owner": h.get("owner_agent_name"), "agent_id": h.get("owner_agent_id"), "symbol": h.get("linked_symbol"), "hypothesis": h.get("claim"), "check_next": "next_session", "status": h.get("status")} for h in ledger[:8]]
    memory["hypotheses"] = [{"created_at": h.get("created_at"), "owner": h.get("owner_agent_name"), "agent_id": h.get("owner_agent_id"), "claim": h.get("claim"), "evidence": h.get("evidence_at_creation"), "check_next": h.get("test_condition"), "status": h.get("status")} for h in ledger[:8]]
    return memory


def schedule_messages(messages: list[dict[str, Any]], session: dict[str, Any], settings: Settings) -> list[dict[str, Any]]:
    base = now_jst()
    elapsed = 0
    out = []
    rng = random.Random(hash(session["session_id"]) & 0xFFFFFFFF)
    for i, m in enumerate(messages, start=1):
        delay = 0 if i == 1 else rng.randint(settings.min_delay_seconds, settings.max_delay_seconds)
        elapsed += delay
        item = dict(m)
        item.update({"message_id": f"live-msg-{i:03d}", "sequence": i, "delay_seconds": delay, "reveal_after_seconds": elapsed, "scheduled_at": (base + timedelta(seconds=elapsed)).isoformat(timespec="seconds"), "session_id": session["session_id"], "session_type": session["session_type"], "session_title": session["session_title"], "global_sequence": i})
        out.append(item)
    return out


def build_evidence_tape(ranking: list[dict[str, Any]], positions: list[dict[str, Any]], topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for r in ranking:
        aid = r.get("agent_id")
        items.append({"label": f"#{r.get('rank')} {r.get('name')}", "value": f"{r.get('return_label')} / MDD {r.get('mdd_label')}", "agent_id": aid, "color": CANONICAL_COLORS.get(aid, "#7DF9FF")})
    for t in topics[:8]:
        aid = (t.get("required_agents") or ["value_mispricing"])[0]
        items.append({"label": str(t.get("topic_type", "topic")).replace("_", " ").upper(), "value": t.get("headline"), "agent_id": aid, "color": CANONICAL_COLORS.get(aid, "#7DF9FF")})
    for p in sorted(positions, key=lambda x: abs(float(x.get("pnl_pct") or 0)), reverse=True)[:6]:
        aid = p.get("agent_id")
        items.append({"label": f"OPEN {p.get('ticker')}", "value": f"{CANONICAL_NAMES.get(aid, aid)} {p.get('pnl_label')} / {p.get('holding_days')}d", "agent_id": aid, "color": CANONICAL_COLORS.get(aid, "#7DF9FF")})
    return items[:30]


def quality_report(messages: list[dict[str, Any]], target: int) -> dict[str, Any]:
    counts: dict[str, int] = {}
    generic = 0
    identity_errors = 0
    numeric = 0
    for m in messages:
        aid = m.get("agent_id")
        counts[aid] = counts.get(aid, 0) + 1
        body = str(m.get("body") or "").lower()
        if m.get("evidence_numbers") or re.search(r"[+\-]?\d+(\.\d+)?%|¥\d", body):
            numeric += 1
        if any(p in body for p in GENERIC_BANNED):
            generic += 1
        if m.get("agent_name") != CANONICAL_NAMES.get(aid):
            identity_errors += 1
    max_share = max(counts.values()) / len(messages) if messages else 0
    score = 100
    score -= max(0, target - len(messages)) * 4
    score -= generic * 8
    score -= identity_errors * 20
    if max_share > 0.3:
        score -= int((max_share - 0.3) * 100)
    return {"messages_generated": len(messages), "target_messages": target, "messages_with_numbers": numeric, "agent_distribution": counts, "max_agent_share": round(max_share, 3), "generic_phrase_count": generic, "identity_errors": identity_errors, "conversation_score": max(0, min(100, score))}


def build_payload(settings: Settings) -> dict[str, Any]:
    base = settings.out_dir / "data/japan/ai-arena"
    war_dir = base / "war-room"
    memory_path = war_dir / "memory.json"
    ctx = load_arena_context(base)
    agents = normalize_agents(ctx)
    ranking = normalize_ranking(ctx)
    positions = normalize_positions(ctx)
    portfolio = ctx.get("portfolio", {})
    memory = read_json(memory_path, {"watch_items": [], "hypotheses": [], "hypothesis_ledger": []})
    session_type = infer_session_type(settings.session_type)
    config = SESSION_CONFIG[session_type]
    target = int(os.getenv("AI_ARENA_WAR_ROOM_MESSAGES", "") or config["target"])
    scene = scene_profile(session_type)
    session = make_session_context(session_type, config, scene, target)
    market_context = build_market_context(enabled=settings.market_context_enabled)
    topics = build_topics(ranking, positions, portfolio, ctx.get("recent_trades", []), memory)
    if not topics:
        raise RuntimeError("No War Room topics could be created from Arena evidence.")
    client = OpenAIClient(settings)
    messages, selected_topics = generate_dialogue(client, session, topics, market_context, memory, target)
    min_required = int(config["min"])
    if len(messages) < min_required:
        raise RuntimeError(f"GPT dialogue generated only {len(messages)} messages; minimum required is {min_required}.")
    scheduled = schedule_messages(messages, session, settings)
    verdict_result = generate_verdict(client, session, selected_topics, scheduled, market_context, memory)
    thinking_states = generate_thinking_states(client, session, agents, selected_topics, market_context)
    memory = update_hypothesis_ledger(memory, session, scheduled, selected_topics)
    write_json(memory_path, memory)
    council_verdict = verdict_result.get("council_verdict") or {}
    daily_brief = verdict_result.get("daily_brief") or {"headline": council_verdict.get("headline", "AI Arena Live Lab"), "summary": council_verdict.get("market_read", "Generated from Arena evidence."), "bullets": []}
    current_session = {**session, "headline": council_verdict.get("headline", config["title"]), "summary": daily_brief.get("summary", config["purpose"]), "topics": selected_topics, "messages": scheduled, "quality": quality_report(scheduled, target)}
    # Preserve a compact recent session archive.
    prev = read_json(war_dir / "latest.json", {})
    sessions = [current_session]
    for old in prev.get("sessions", []) if isinstance(prev, dict) else []:
        if old.get("session_id") != current_session["session_id"]:
            sessions.append(old)
        if len(sessions) >= 8:
            break
    evidence_tape = build_evidence_tape(ranking, positions, selected_topics)
    pulse = [{"agent_id": s["agent_id"], "agent_name": s["agent_name"], "color": s["color"], "body": s["current_question"], "state": s["state"]} for s in thinking_states]
    next_watch = [{"question": h.get("test_condition") or h.get("claim"), "owner": h.get("owner_agent_name"), "symbol": h.get("linked_symbol", ""), "status": h.get("status"), "check_at": "next_session"} for h in (memory.get("hypothesis_ledger") or [])[:5]]
    payload = {"schema_version": "ai_arena_live_lab_v5_market_context_hypothesis_thinking", "generated_at": now_jst().isoformat(timespec="seconds"), "page": {"title": "AI Arena Live Lab", "subtitle": "Seven trading agents debate Japanese equities through simulation evidence, market context, hypotheses, and GPT-4o reasoning."}, "market_context": market_context, "council_verdict": council_verdict, "daily_brief": daily_brief, "current_session": current_session, "sessions": sessions, "agents": agents, "agent_thinking_states": thinking_states, "hypothesis_ledger": memory.get("hypothesis_ledger", []), "next_council_watch": next_watch, "ranking": ranking, "open_positions": positions, "portfolio": portfolio, "topics": selected_topics, "live_messages": scheduled, "feed": scheduled, "threads": [], "evidence_tape": evidence_tape, "pulse": pulse, "memory": memory, "live_config": {"mode": "browser_reveal_queue", "min_delay_seconds": settings.min_delay_seconds, "max_delay_seconds": settings.max_delay_seconds, "message_count": len(scheduled), "schedule_note": "Static page reveals pre-generated GPT-4o messages at randomized 3-5 minute intervals. GitHub Actions generates sessions at Open +30m, Midday, Close, Night, and Weekly Review."}, "metrics": {"agent_count": len(agents), "message_count": len(scheduled), "session_message_count": len(scheduled), "session_target_messages": target, "session_count": len(sessions), "open_position_count": len(positions), "ranking_count": len(ranking), "topic_count": len(topics), "selected_topic_count": len(selected_topics), "evidence_items": len(evidence_tape), "hypothesis_count": len(memory.get("hypothesis_ledger", []))}, "quality": quality_report(scheduled, target), "ai": {"required": True, "enabled": True, "status": "gpt-4o_generated", "model": settings.model, "temperature": settings.temperature, "rate_limit_encountered": client.rate_limit_encountered, "pipeline": "Evidence -> Market Context -> Hypothesis Ledger -> Scene -> Casting -> GPT Dialogue -> Validator -> Memory"}, "disclaimer": "AI Arena is a quantitative simulation and generative discussion interface. Informational only. Not investment advice."}
    write_json(war_dir / "latest.json", payload)
    write_json(war_dir / "history" / f"{session['session_id']}.json", payload)
    prune_history(war_dir / "history", settings.history_days)
    return payload


def prune_history(path: Path, days: int) -> None:
    if not path.exists():
        return
    cutoff = time.time() - max(1, days) * 86400
    for p in path.glob("*.json"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
        except Exception:
            pass


def settings_from_env(root: Path) -> Settings:
    out = Path(os.getenv("OUT_DIR", str(root / "site")))
    if not out.is_absolute():
        out = (root / out).resolve()
    return Settings(root=root, out_dir=out, model=os.getenv("AI_ARENA_WAR_ROOM_MODEL", "gpt-4o"), session_type=os.getenv("AI_ARENA_WAR_ROOM_SESSION_TYPE", "auto"), min_delay_seconds=int(os.getenv("AI_ARENA_WAR_ROOM_MIN_DELAY_SECONDS", "180")), max_delay_seconds=int(os.getenv("AI_ARENA_WAR_ROOM_MAX_DELAY_SECONDS", "300")), history_days=int(os.getenv("AI_ARENA_WAR_ROOM_HISTORY_DAYS", "14")), temperature=float(os.getenv("AI_ARENA_WAR_ROOM_TEMPERATURE", "0.82")), openai_min_interval_seconds=float(os.getenv("AI_ARENA_WAR_ROOM_OPENAI_MIN_INTERVAL_SECONDS", "30")), openai_max_retries=int(os.getenv("AI_ARENA_WAR_ROOM_OPENAI_MAX_RETRIES", "8")), openai_429_base_sleep_seconds=float(os.getenv("AI_ARENA_WAR_ROOM_OPENAI_429_BASE_SLEEP_SECONDS", "75")), market_context_enabled=os.getenv("AI_ARENA_WAR_ROOM_MARKET_CONTEXT", "true").lower() not in {"0", "false", "no", "off"}, mock_openai=os.getenv("AI_ARENA_WAR_ROOM_MOCK_OPENAI", "false").lower() in {"1", "true", "yes", "on"})
