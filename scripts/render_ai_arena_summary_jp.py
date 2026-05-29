#!/usr/bin/env python3
from __future__ import annotations

"""Render AI Arena annual summary pages from generated summary JSON."""

import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from lib.db import ROOT, safe_rel

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()
YEAR = os.getenv("ARENA_YEAR") or os.getenv("YEAR") or ""
TEMPLATE_DIR = ROOT / "templates"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": "missing", "rankings": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def render_one(payload: dict, path: Path) -> None:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape())
    html = env.get_template("ai_arena_summary_jp.html.j2").render(payload=payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def main() -> int:
    current_payload = load_json(OUT_DIR / "data" / "japan" / "ai-arena" / "summary" / "latest.json")
    render_one(current_payload, OUT_DIR / "japan" / "ai-arena" / "summary" / "index.html")
    year = YEAR or str(current_payload.get("year") or "")
    if year:
        year_payload = load_json(OUT_DIR / "data" / "japan" / "ai-arena" / "summary" / year / "latest.json")
        render_one(year_payload, OUT_DIR / "japan" / "ai-arena" / "summary" / year / "index.html")
    css_src = TEMPLATE_DIR / "ai_arena_summary_jp.css"
    css_dst = OUT_DIR / "assets" / "ai_arena_summary_jp.css"
    css_dst.parent.mkdir(parents=True, exist_ok=True)
    css_dst.write_text(css_src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {safe_rel(OUT_DIR / 'japan' / 'ai-arena' / 'summary' / 'index.html')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
