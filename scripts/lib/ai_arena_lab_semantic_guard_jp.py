#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Arena Live Lab Semantic Guard JP.

Purpose:
- Normalize agent metadata.
- Prevent agent color/state/name mismatch.
- Prevent self-replies.
- Prevent weak or forced SOXX / semiconductor narratives.
- Normalize topic_id.
- Filter broken historical sessions from display.
- Improve hypothesis ledger so it becomes testable.
- Add semantic quality diagnostics.

This module is deterministic.
Do not call OpenAI from this module.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Optional, Tuple


AGENT_REGISTRY: Dict[str, Dict[str, str]] = {
    "daily_striker": {
        "name": "KYOU",
        "color": "#FF4B5C",
        "state": "SCANNING MOMENTUM",
        "avatar_image": "/assets/ai-arena/agents/daily_striker.png",
    },
    "weekly_sage": {
        "name": "NAGARE",
        "color": "#B779FF",
        "state": "READING FLOW",
        "avatar_image": "/assets/ai-arena/agents/weekly_sage.png",
    },
    "risk_sentinel": {
        "name": "MAMORU",
        "color": "#7DF9FF",
        "state": "RISK GATE ACTIVE",
        "avatar_image": "/assets/ai-arena/agents/risk_sentinel.png",
    },
    "discovery_scout": {
        "name": "SAGURI",
        "color": "#5DFFB1",
        "state": "HUNTING EARLY SIGNALS",
        "avatar_image": "/assets/ai-arena/agents/discovery_scout.png",
    },
    "contrarian_monk": {
        "name": "MATSU",
        "color": "#FFD166",
        "state": "WAITING FOR PULLBACK",
        "avatar_image": "/assets/ai-arena/agents/contrarian_monk.png",
    },
    "reversal_snapback": {
        "name": "KAESHI",
        "color": "#FF4FD8",
        "state": "SNAPBACK WATCH",
        "avatar_image": "/assets/ai-arena/agents/reversal_snapback.png",
    },
    "value_mispricing": {
        "name": "HIZUMI",
        "color": "#4F46E5",
        "state": "TESTING MISPRICING",
        "avatar_image": "/assets/ai-arena/agents/value_mispricing.png",
    },
}

AGENT_NAME_TO_ID: Dict[str, str] = {v["name"]: k for k, v in AGENT_REGISTRY.items()}

SEMICONDUCTOR_RELEVANT_TICKERS = {
    "3436.T",
    "4063.T",
    "5333.T",
    "5334.T",
    "5344.T",
    "5711.T",
    "5714.T",
    "5802.T",
    "5803.T",
    "6323.T",
    "6506.T",
    "6752.T",
    "6754.T",
    "6963.T",
    "6965.T",
    "6976.T",
    "6981.T",
}

MARKET_INDEX_SYMBOLS = {
    "^N225",
    "^GSPC",
    "^IXIC",
    "^RUT",
    "^TNX",
    "JPY=X",
    "USDJPY=X",
    "SOXX",
    "^SOX",
}

SEMICONDUCTOR_WORDS = {
    "semiconductor",
    "semiconductors",
    "semi",
    "SOXX",
    "SOX",
    "chip",
    "chips",
    "sector beta",
    "sectoral beta",
    "semiconductor beta",
    "semiconductor tailwind",
    "sector tailwind",
    "半導体",
}

GENERIC_BAD_PHRASES = {
    "only time will tell",
    "anything can happen",
    "stay vigilant",
    "watch closely",
    "calm before the storm",
    "hidden surprise",
    "market noise",
    "ready to spring",
    "vigilance maintained",
    "still in the game",
    "potential energy",
    "pathways",
    "momentum is not waiting",
    "continuous scrutiny",
    "strong buy",
    "strong sell",
    "must buy",
    "must sell",
    "you should buy",
    "you should sell",
    "guaranteed",
    "easy money",
}

TOPIC_ID_SAFE_RE = re.compile(r"[^a-z0-9_]+")


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def safe_str(value: Any) -> str:
    return "" if value is None else str(value)


def normalize_symbol(value: Any) -> str:
    raw = safe_str(value).strip().upper()
    if not raw:
        return ""
    raw = raw.replace("-", ".")
    if raw == "USDJPY=X":
        return "JPY=X"
    return raw


def normalize_topic_id(value: Any) -> str:
    raw = safe_str(value).strip().lower()
    if not raw:
        return "unknown_topic"
    raw = raw.replace(".t", "_t")
    raw = raw.replace("-", "_")
    raw = TOPIC_ID_SAFE_RE.sub("_", raw)
    raw = re.sub(r"_+", "_", raw).strip("_")
    return raw or "unknown_topic"


def message_text(message: Dict[str, Any]) -> str:
    return safe_str(message.get("body"))


def list_text(values: Any) -> str:
    return " ".join(safe_str(x) for x in as_list(values))


def contains_any(text: str, words: set[str]) -> bool:
    lower = text.lower()
    return any(word.lower() in lower for word in words)


def contains_semiconductor_context(
    text: str,
    evidence_numbers: Optional[List[Any]] = None,
    evidence_label: str = "",
) -> bool:
    haystack = " ".join([safe_str(text), list_text(evidence_numbers or []), safe_str(evidence_label)])
    return contains_any(haystack, SEMICONDUCTOR_WORDS)


def symbol_allows_semiconductor_context(symbol: str) -> bool:
    symbol = normalize_symbol(symbol)
    if not symbol:
        return True
    if symbol in {"SOXX", "^SOX", "^IXIC"}:
        return True
    return symbol in SEMICONDUCTOR_RELEVANT_TICKERS


def remove_semiconductor_sentences(text: str) -> str:
    if not text:
        return text
    parts = re.split(r"(?<=[\.!?。！？])\s+", text.strip())
    kept: List[str] = []
    for part in parts:
        if not part.strip():
            continue
        if contains_any(part, SEMICONDUCTOR_WORDS):
            continue
        kept.append(part.strip())
    result = " ".join(kept).strip()
    if result == text.strip():
        result = re.sub(r"(?i)\b(the\s+)?SOXX ETF'?s? [^\.。!?]*[\.。!?]?", "", result).strip()
        result = re.sub(r"(?i)[^\.。!?]*(semiconductor|sectoral beta|sector beta|chip|chips)[^\.。!?]*[\.。!?]?", "", result).strip()
    return result


def truncate_text(value: str, max_len: int = 240) -> str:
    text = safe_str(value).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def force_agent_metadata(message: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    msg = dict(message)
    issues: List[str] = []
    agent_id = safe_str(msg.get("agent_id")).strip()
    reg = AGENT_REGISTRY.get(agent_id)
    if not reg:
        issues.append(f"unknown agent_id: {agent_id}")
        return msg, issues
    if msg.get("agent_name") != reg["name"]:
        issues.append(f"fixed agent_name for {agent_id}: {msg.get('agent_name')} -> {reg['name']}")
    if msg.get("color") != reg["color"]:
        issues.append(f"fixed color for {agent_id}: {msg.get('color')} -> {reg['color']}")
    if msg.get("state") != reg["state"]:
        issues.append(f"fixed state for {agent_id}: {msg.get('state')} -> {reg['state']}")
    if msg.get("avatar_image") != reg["avatar_image"]:
        issues.append(f"fixed avatar_image for {agent_id}")
    msg["agent_name"] = reg["name"]
    msg["color"] = reg["color"]
    msg["state"] = reg["state"]
    msg["avatar_image"] = reg["avatar_image"]
    return msg, issues


def normalize_agents(agents: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    out: List[Dict[str, Any]] = []
    issues: List[str] = []
    for agent in agents or []:
        row = dict(agent)
        agent_id = safe_str(row.get("agent_id")).strip()
        reg = AGENT_REGISTRY.get(agent_id)
        if not reg:
            issues.append(f"unknown agent in agents list: {agent_id}")
            out.append(row)
            continue
        if row.get("name") != reg["name"]:
            issues.append(f"fixed agents.name for {agent_id}")
        if row.get("color") != reg["color"]:
            issues.append(f"fixed agents.color for {agent_id}")
        if row.get("state") != reg["state"]:
            issues.append(f"fixed agents.state for {agent_id}")
        if row.get("image") != reg["avatar_image"]:
            issues.append(f"fixed agents.image for {agent_id}")
        row["name"] = reg["name"]
        row["color"] = reg["color"]
        row["state"] = reg["state"]
        row["image"] = reg["avatar_image"]
        out.append(row)
    return out, issues


def sanitize_message(message: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    msg, issues = force_agent_metadata(message)
    agent_id = safe_str(msg.get("agent_id")).strip()
    reg = AGENT_REGISTRY.get(agent_id)
    body = message_text(msg).strip()
    if not body:
        return None, issues + [f"dropped empty body for {agent_id}"]

    reply_to = safe_str(msg.get("reply_to_agent")).strip()
    if reply_to and reg:
        own_refs = {agent_id, reg["name"], reg["name"].upper(), reg["name"].lower()}
        if reply_to in own_refs:
            msg["reply_to_agent"] = ""
            issues.append(f"removed self reply for {agent_id}")

    if msg.get("topic_id"):
        old_topic_id = safe_str(msg.get("topic_id"))
        new_topic_id = normalize_topic_id(old_topic_id)
        if old_topic_id != new_topic_id:
            issues.append(f"normalized message topic_id: {old_topic_id} -> {new_topic_id}")
        msg["topic_id"] = new_topic_id

    linked_symbol = normalize_symbol(msg.get("linked_symbol"))
    msg["linked_symbol"] = linked_symbol
    evidence_numbers = as_list(msg.get("evidence_numbers"))
    evidence_label = safe_str(msg.get("evidence_label"))

    if contains_semiconductor_context(body, evidence_numbers, evidence_label):
        if not symbol_allows_semiconductor_context(linked_symbol):
            cleaned_body = remove_semiconductor_sentences(body)
            if not cleaned_body or len(cleaned_body) < 40:
                return None, issues + [f"dropped forced semiconductor message for non-related symbol {linked_symbol or '(blank)'}"]
            msg["body"] = cleaned_body
            issues.append(f"removed forced semiconductor context for non-related symbol {linked_symbol or '(blank)'}")

    bad_hits = [phrase for phrase in GENERIC_BAD_PHRASES if phrase.lower() in safe_str(msg.get("body")).lower()]
    if bad_hits:
        issues.append(f"generic/banned phrase found: {bad_hits}")

    cleaned_evidence = []
    for item in evidence_numbers:
        s = safe_str(item).strip()
        if not s:
            continue
        if s in {"next_session", "market_context", "semiconductor_proxy", "nikkei_225", "usd_jpy"}:
            if s not in safe_str(msg.get("body")):
                continue
        cleaned_evidence.append(item)
    msg["evidence_numbers"] = cleaned_evidence
    return msg, issues


def sanitize_topics(topics: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    out: List[Dict[str, Any]] = []
    issues: List[str] = []
    for topic in topics or []:
        t = dict(topic)
        old_id = safe_str(t.get("topic_id"))
        new_id = normalize_topic_id(old_id)
        if old_id != new_id:
            issues.append(f"normalized topic_id: {old_id} -> {new_id}")
        t["topic_id"] = new_id

        linked_symbols = [normalize_symbol(x) for x in as_list(t.get("linked_symbols")) if normalize_symbol(x)]
        t["linked_symbols"] = list(dict.fromkeys(linked_symbols))

        for key in ("required_agents", "challenger_agents"):
            seen = set()
            cleaned = []
            for agent_id in as_list(t.get(key)):
                agent_id = safe_str(agent_id).strip()
                if agent_id in AGENT_REGISTRY and agent_id not in seen:
                    cleaned.append(agent_id)
                    seen.add(agent_id)
                elif agent_id and agent_id not in AGENT_REGISTRY:
                    issues.append(f"removed unknown {key} agent: {agent_id}")
            t[key] = cleaned

        cast = []
        for c in as_list(t.get("speaker_cast")):
            if not isinstance(c, dict):
                continue
            agent_id = safe_str(c.get("agent_id")).strip()
            reg = AGENT_REGISTRY.get(agent_id)
            if not reg:
                issues.append(f"removed unknown speaker_cast agent: {agent_id}")
                continue
            cc = dict(c)
            cc["agent_name"] = reg["name"]
            cc["color"] = reg["color"]
            cc["state"] = reg["state"]
            cast.append(cc)
        t["speaker_cast"] = cast
        out.append(t)
    return out, issues


def sanitize_allocation_by_agent(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    out: List[Dict[str, Any]] = []
    issues: List[str] = []
    for item in items or []:
        row = dict(item)
        agent_id = safe_str(row.get("agent_id")).strip()
        reg = AGENT_REGISTRY.get(agent_id)
        if not reg:
            issues.append(f"allocation_by_agent unknown agent_id: {agent_id}")
            out.append(row)
            continue
        if row.get("agent_name") != reg["name"]:
            issues.append(f"fixed allocation agent_name for {agent_id}")
        if row.get("color") != reg["color"]:
            issues.append(f"fixed allocation color for {agent_id}: {row.get('color')} -> {reg['color']}")
        row["agent_name"] = reg["name"]
        row["color"] = reg["color"]
        out.append(row)
    return out, issues


def sanitize_open_positions(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    out: List[Dict[str, Any]] = []
    issues: List[str] = []
    for item in items or []:
        row = dict(item)
        agent_id = safe_str(row.get("agent_id")).strip()
        reg = AGENT_REGISTRY.get(agent_id)
        if reg and row.get("agent_name") != reg["name"]:
            issues.append(f"fixed open position agent_name for {agent_id}")
            row["agent_name"] = reg["name"]
        if row.get("ticker"):
            row["ticker"] = normalize_symbol(row.get("ticker"))
        out.append(row)
    return out, issues


def session_quality_issues(session: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    messages = as_list(session.get("messages"))
    if not messages:
        return ["empty session messages"]
    counts: Dict[str, int] = {}
    for msg in messages:
        if not isinstance(msg, dict):
            issues.append("non-dict message")
            continue
        agent_id = safe_str(msg.get("agent_id")).strip()
        counts[agent_id] = counts.get(agent_id, 0) + 1
        reg = AGENT_REGISTRY.get(agent_id)
        if not reg:
            issues.append(f"unknown agent_id: {agent_id}")
            continue
        if msg.get("agent_name") != reg["name"]:
            issues.append(f"agent_name mismatch: {agent_id}")
        if msg.get("color") != reg["color"]:
            issues.append(f"color mismatch: {agent_id}")
        if msg.get("state") != reg["state"]:
            issues.append(f"state mismatch: {agent_id}")
        reply_to = safe_str(msg.get("reply_to_agent")).strip()
        if reply_to in {agent_id, reg["name"]}:
            issues.append(f"self reply: {agent_id}")
        linked_symbol = normalize_symbol(msg.get("linked_symbol"))
        if contains_semiconductor_context(message_text(msg), as_list(msg.get("evidence_numbers")), safe_str(msg.get("evidence_label"))):
            if not symbol_allows_semiconductor_context(linked_symbol):
                issues.append(f"forced semiconductor context on non-related symbol: {linked_symbol or '(blank)'}")
        body = message_text(msg)
        bad_hits = [phrase for phrase in GENERIC_BAD_PHRASES if phrase.lower() in body.lower()]
        if bad_hits:
            issues.append(f"generic/banned phrase: {bad_hits}")
    total = len(messages)
    if total:
        top3_share = sum(sorted(counts.values(), reverse=True)[:3]) / total
        if top3_share > 0.82:
            issues.append(f"top3 agent concentration too high: {top3_share:.3f}")
    zero_agents = [a for a in AGENT_REGISTRY if counts.get(a, 0) == 0]
    if total >= 14 and len(zero_agents) >= 3:
        issues.append(f"too many zero-speaker agents: {zero_agents}")
    return issues


def sanitize_session(session: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    s = copy.deepcopy(session)
    issues: List[str] = []
    topics, topic_issues = sanitize_topics(as_list(s.get("topics")))
    s["topics"] = topics
    issues.extend(topic_issues)
    sanitized_messages: List[Dict[str, Any]] = []
    for msg in as_list(s.get("messages")):
        if not isinstance(msg, dict):
            issues.append("removed non-dict message")
            continue
        cleaned, msg_issues = sanitize_message(msg)
        issues.extend(msg_issues)
        if cleaned is not None:
            sanitized_messages.append(cleaned)
    for idx, msg in enumerate(sanitized_messages, start=1):
        msg["sequence"] = idx
        if "global_sequence" in msg:
            msg["global_sequence"] = idx
        if not msg.get("message_id"):
            msg["message_id"] = f"live-msg-{idx:03d}"
    s["messages"] = sanitized_messages
    s.setdefault("quality", {})
    semantic_issues = session_quality_issues(s)
    s["quality"]["semantic_validation_issues"] = semantic_issues
    s["quality"]["semantic_validation_issue_count"] = len(semantic_issues)
    return s, issues


def should_drop_historical_session(session: Dict[str, Any]) -> bool:
    issues = as_list(session.get("quality", {}).get("semantic_validation_issues"))
    hard_markers = (
        "forced semiconductor context",
        "state mismatch",
        "color mismatch",
        "self reply",
        "unknown agent_id",
        "empty session messages",
    )
    return any(any(marker in safe_str(issue) for marker in hard_markers) for issue in issues)


def sanitize_sessions(sessions: List[Dict[str, Any]], keep_limit: int = 6) -> Tuple[List[Dict[str, Any]], List[str]]:
    cleaned_sessions: List[Dict[str, Any]] = []
    issues: List[str] = []
    for raw_session in sessions or []:
        if not isinstance(raw_session, dict):
            issues.append("dropped non-dict session")
            continue
        session, session_issues = sanitize_session(raw_session)
        session_id = safe_str(session.get("session_id"))
        issues.extend([f"{session_id}: {x}" for x in session_issues])
        if should_drop_historical_session(session):
            issues.append(
                f"dropped low-quality historical session: {session_id} / "
                f"{session.get('quality', {}).get('semantic_validation_issues', [])[:5]}"
            )
            continue
        cleaned_sessions.append(session)
    return cleaned_sessions[:keep_limit], issues


def improve_hypothesis_ledger(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    out: List[Dict[str, Any]] = []
    issues: List[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        symbol = normalize_symbol(row.get("linked_symbol"))
        claim = safe_str(row.get("claim"))
        if symbol:
            row["linked_symbol"] = symbol
        metric_to_watch: List[str] = []
        if "SOXX" in claim or symbol in {"SOXX", "^SOX"}:
            metric_to_watch.extend([
                "SOXX change_pct",
                "weekly_sage open P/L change",
                "weekly_sage return_pct change",
            ])
        if symbol and symbol not in MARKET_INDEX_SYMBOLS:
            metric_to_watch.append(f"{symbol} unrealized_return_pct change")
            metric_to_watch.append(f"{symbol} holding_days")
        if "NAGARE" in claim or row.get("owner_agent_id") == "weekly_sage":
            metric_to_watch.extend([
                "weekly_sage return_pct change",
                "weekly_sage max_drawdown_pct change",
                "weekly_sage open_position_pnl change",
            ])
        if "drawdown" in claim.lower():
            metric_to_watch.append("max_drawdown_pct change")
        if "concentration" in claim.lower() or "allocation" in claim.lower():
            metric_to_watch.append("allocation_by_agent weight_pct change")
        if not metric_to_watch:
            metric_to_watch = ["linked position P/L change", "owner agent return_pct change"]
        row["metric_to_watch"] = list(dict.fromkeys(metric_to_watch))
        test_condition = safe_str(row.get("test_condition")).strip()
        abstract_starts = (
            "distinguishing",
            "identifying",
            "testing under",
            "clarifies",
            "confirms",
            "understanding",
            "evaluating",
        )
        if len(test_condition) < 40 or test_condition.lower().startswith(abstract_starts):
            row["test_condition"] = (
                "Next session: compare metric_to_watch against the current evidence. "
                "Mark 'strengthened' only when the metric moves in the claim's direction; "
                "mark 'weakened' when the opposite occurs; otherwise keep 'pending'."
            )
            issues.append(f"rewrote abstract test_condition for {row.get('hypothesis_id')}")
        if row.get("claim"):
            row["claim"] = truncate_text(row["claim"], 260)
        out.append(row)
    return out, issues


def improve_memory_watch_items(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    out: List[Dict[str, Any]] = []
    issues: List[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        if row.get("symbol"):
            row["symbol"] = normalize_symbol(row.get("symbol"))
        if row.get("hypothesis"):
            row["hypothesis"] = truncate_text(row["hypothesis"], 260)
        if not row.get("check_next"):
            row["check_next"] = "next_session"
            issues.append("filled missing watch_item.check_next")
        if not row.get("status"):
            row["status"] = "pending"
            issues.append("filled missing watch_item.status")
        out.append(row)
    return out, issues


def sanitize_agent_thinking_states(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    out: List[Dict[str, Any]] = []
    issues: List[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        agent_id = safe_str(row.get("agent_id")).strip()
        reg = AGENT_REGISTRY.get(agent_id)
        if not reg:
            issues.append(f"removed unknown thinking_state agent: {agent_id}")
            continue
        row["agent_name"] = reg["name"]
        row["color"] = reg["color"]
        row["avatar_image"] = reg["avatar_image"]
        row["state"] = reg["state"]
        for k in ("confidence", "stress_level"):
            try:
                row[k] = max(0.0, min(1.0, float(row.get(k, 0.5))))
            except Exception:
                row[k] = 0.5
                issues.append(f"fixed thinking_state {k} for {agent_id}")
        out.append(row)
    existing = {safe_str(x.get("agent_id")) for x in out}
    for agent_id, reg in AGENT_REGISTRY.items():
        if agent_id in existing:
            continue
        out.append({
            "agent_id": agent_id,
            "agent_name": reg["name"],
            "color": reg["color"],
            "avatar_image": reg["avatar_image"],
            "state": reg["state"],
            "focus": "Waiting for the next valid evidence update.",
            "current_question": "What changed in the latest Arena evidence?",
            "confidence": 0.5,
            "stress_level": 0.5,
        })
        issues.append(f"added missing thinking_state for {agent_id}")
    return out, issues


def calculate_semantic_score(payload: Dict[str, Any]) -> int:
    quality = payload.get("quality") or {}
    issues = as_list(quality.get("semantic_guard_issues"))
    current = payload.get("current_session") or {}
    messages = as_list(current.get("messages"))
    score = 100
    hard_penalties = (
        "forced semiconductor",
        "unknown agent_id",
        "self reply",
        "state mismatch",
        "color mismatch",
        "empty session",
    )
    for issue in issues:
        issue_text = safe_str(issue)
        if any(marker in issue_text for marker in hard_penalties):
            score -= 12
        else:
            score -= 2
    counts: Dict[str, int] = {}
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        aid = safe_str(msg.get("agent_id"))
        counts[aid] = counts.get(aid, 0) + 1
    if messages:
        top3_share = sum(sorted(counts.values(), reverse=True)[:3]) / len(messages)
        if top3_share > 0.82:
            score -= 10
    zero_agents = [a for a in AGENT_REGISTRY if counts.get(a, 0) == 0]
    if len(messages) >= 14 and len(zero_agents) >= 3:
        score -= 8
    return max(0, min(100, score))


def sanitize_lab_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point.

    Usage:
        from scripts.lib.ai_arena_lab_semantic_guard_jp import sanitize_lab_payload
        payload = sanitize_lab_payload(payload)
    """
    data = copy.deepcopy(payload)
    semantic_issues: List[str] = []

    agents, issues = normalize_agents(as_list(data.get("agents")))
    if agents:
        data["agents"] = agents
    semantic_issues.extend([f"agents: {x}" for x in issues])

    topics, issues = sanitize_topics(as_list(data.get("topics")))
    data["topics"] = topics
    semantic_issues.extend([f"topics: {x}" for x in issues])

    current_session = data.get("current_session")
    if isinstance(current_session, dict):
        current_session, issues = sanitize_session(current_session)
        data["current_session"] = current_session
        semantic_issues.extend([f"current_session: {x}" for x in issues])
        current_messages = as_list(current_session.get("messages"))
        data["live_messages"] = current_messages
        data["feed"] = current_messages

    sessions, issues = sanitize_sessions(as_list(data.get("sessions")), keep_limit=6)
    data["sessions"] = sessions
    semantic_issues.extend([f"sessions: {x}" for x in issues])

    portfolio = data.get("portfolio")
    if isinstance(portfolio, dict):
        allocation, issues = sanitize_allocation_by_agent(as_list(portfolio.get("allocation_by_agent")))
        portfolio["allocation_by_agent"] = allocation
        semantic_issues.extend([f"portfolio: {x}" for x in issues])
        top_positions, issues = sanitize_open_positions(as_list(portfolio.get("top_positions")))
        portfolio["top_positions"] = top_positions
        semantic_issues.extend([f"portfolio: {x}" for x in issues])
        data["portfolio"] = portfolio

    open_positions, issues = sanitize_open_positions(as_list(data.get("open_positions")))
    data["open_positions"] = open_positions
    semantic_issues.extend([f"open_positions: {x}" for x in issues])

    ledger, issues = improve_hypothesis_ledger(as_list(data.get("hypothesis_ledger")))
    data["hypothesis_ledger"] = ledger
    semantic_issues.extend([f"hypothesis_ledger: {x}" for x in issues])

    memory = data.get("memory")
    if isinstance(memory, dict):
        watch_items, issues = improve_memory_watch_items(as_list(memory.get("watch_items")))
        memory["watch_items"] = watch_items
        semantic_issues.extend([f"memory.watch_items: {x}" for x in issues])
        mem_ledger, issues = improve_hypothesis_ledger(as_list(memory.get("hypothesis_ledger")))
        memory["hypothesis_ledger"] = mem_ledger
        semantic_issues.extend([f"memory.hypothesis_ledger: {x}" for x in issues])
        data["memory"] = memory

    thinking_states, issues = sanitize_agent_thinking_states(as_list(data.get("agent_thinking_states")))
    data["agent_thinking_states"] = thinking_states
    semantic_issues.extend([f"agent_thinking_states: {x}" for x in issues])

    data["pulse"] = [
        {
            "agent_id": x["agent_id"],
            "agent_name": x["agent_name"],
            "color": x["color"],
            "body": x.get("current_question") or x.get("focus") or "",
            "state": x["state"],
        }
        for x in thinking_states
    ]

    current_messages = as_list((data.get("current_session") or {}).get("messages"))
    data.setdefault("metrics", {})
    data["metrics"]["message_count"] = len(current_messages)
    data["metrics"]["session_message_count"] = len(current_messages)
    data["metrics"]["session_count"] = len(as_list(data.get("sessions")))
    data["metrics"]["hypothesis_count"] = len(as_list(data.get("hypothesis_ledger")))

    data.setdefault("quality", {})
    data["quality"]["semantic_guard_issues"] = semantic_issues
    data["quality"]["semantic_guard_issue_count"] = len(semantic_issues)
    data["quality"]["semantic_score"] = calculate_semantic_score(data)

    data.setdefault("ai", {})
    data["ai"]["semantic_guard_enabled"] = True
    return data
