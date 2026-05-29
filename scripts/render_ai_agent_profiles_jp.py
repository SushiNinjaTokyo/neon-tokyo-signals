#!/usr/bin/env python3
from __future__ import annotations

"""Render the AI Arena Agent Profiles page.

This page is generated from YAML so the public explanation of each agent stays
close to the actual configuration used by the engine.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from lib.db import ROOT, safe_rel
from lib.arena_exporter_jp import write_json

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()

AGENTS_YML = ROOT / "data" / "agents" / "jp_agents.yml"
STRATEGY_YML = ROOT / "data" / "agents" / "jp_agent_strategy_rules.yml"
PORTFOLIO_YML = ROOT / "data" / "agents" / "jp_agent_portfolio_rules.yml"
TEMPLATE_DIR = ROOT / "templates"


def read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    generated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    agents_data = read_yaml(AGENTS_YML)
    strategy = read_yaml(STRATEGY_YML)
    portfolio = read_yaml(PORTFOLIO_YML)
    agents = []
    for a in agents_data.get("agents", []):
        aid = a["agent_id"]
        agents.append({
            **a,
            "strategy": (strategy.get("agents") or {}).get(aid, {}),
            "portfolio": (portfolio.get("agents") or {}).get(aid, {}),
        })
    payload = {
        "schema_version": "ai_arena_agent_profiles_v1",
        "generated_at": generated_at,
        "agents": agents,
        "strategy_rules_version": strategy.get("rules_version"),
        "portfolio_rules_version": portfolio.get("rules_version"),
    }
    data_path = OUT_DIR / "data" / "japan" / "ai-arena" / "agents" / "latest.json"
    write_json(data_path, payload)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape())
    html = env.get_template("ai_agent_profiles_jp.html.j2").render(payload=payload)
    html_path = OUT_DIR / "japan" / "ai-arena" / "agents" / "index.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")

    css_src = TEMPLATE_DIR / "ai_agent_profiles_jp.css"
    css_dst = OUT_DIR / "assets" / "ai_agent_profiles_jp.css"
    css_dst.parent.mkdir(parents=True, exist_ok=True)
    css_dst.write_text(css_src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {safe_rel(data_path)}")
    print(f"Wrote {safe_rel(html_path)}")
    print(f"Wrote {safe_rel(css_dst)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
