from __future__ import annotations

"""Optional GPT note generation for Arena Signals.

The engine's buy/sell decisions must remain deterministic Python output.
This module only converts already-supplied metrics into short English copy.
It uses the standard library so no new OpenAI SDK dependency is required.
If OPENAI_API_KEY is missing or ENABLE_GPT_SIGNAL_NOTES is false, callers should
fall back to deterministic template notes.
"""

import json
import os
import urllib.request
from typing import Any


def gpt_enabled() -> bool:
    return os.getenv("ENABLE_GPT_SIGNAL_NOTES", "false").lower() == "true" and bool(os.getenv("OPENAI_API_KEY"))


def build_fallback_notes(*, company_name: str, agent_name: str, signal_type: str, metrics: dict[str, Any]) -> dict[str, str]:
    return {
        "company_brief_en": f"{company_name} is a Japanese listed company monitored by Neon Tokyo Signals.",
        "signal_thesis_en": f"{agent_name} highlights this name for a {signal_type} setup based on the supplied quantitative metrics.",
        "valuation_comment_en": "Valuation data is limited." if not metrics.get("per") and not metrics.get("pbr") else "Valuation metrics are shown in the card and should be compared with sector peers.",
        "risk_comment_en": "Signal quality can deteriorate if liquidity, trend, or risk metrics weaken.",
    }


def generate_signal_notes(payload: dict[str, Any]) -> dict[str, str]:
    """Generate short notes using OpenAI Chat Completions compatible endpoint.

    This function is intentionally isolated and optional. It returns fallback
    notes on any API failure so the daily workflow never fails solely because GPT
    note generation is unavailable.
    """
    fallback = build_fallback_notes(
        company_name=payload.get("company_name") or payload.get("ticker") or "This company",
        agent_name=payload.get("agent_name") or "The agent",
        signal_type=payload.get("signal_type") or "signal",
        metrics=payload.get("metrics") or {},
    )
    if not gpt_enabled():
        return fallback

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_SIGNAL_MODEL", "gpt-4.1-mini")
    system = (
        "You write concise factual English notes for global investors discovering Japanese equities. "
        "Use only supplied data. Do not invent financial numbers. Do not give investment advice. "
        "Return JSON with company_brief_en, signal_thesis_en, valuation_comment_en, risk_comment_en."
    )
    user = json.dumps(payload, ensure_ascii=False)
    req_body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=req_body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        out = json.loads(content)
        return {k: str(out.get(k) or fallback[k]) for k in fallback}
    except Exception:
        return fallback
