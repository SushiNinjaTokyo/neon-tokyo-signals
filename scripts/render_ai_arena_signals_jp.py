#!/usr/bin/env python3
from __future__ import annotations

"""Render Arena Signals page from signals/latest.json."""

import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from lib.db import ROOT, safe_rel

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()
TEMPLATE_DIR = ROOT / "templates"


def main() -> int:
    data_path = OUT_DIR / "data" / "japan" / "ai-arena" / "signals" / "latest.json"
    payload = json.loads(data_path.read_text(encoding="utf-8")) if data_path.exists() else {"agents": []}
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape())
    html = env.get_template("ai_arena_signals_jp.html.j2").render(payload=payload)
    html_path = OUT_DIR / "japan" / "ai-arena" / "signals" / "index.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    css_src = TEMPLATE_DIR / "ai_arena_signals_jp.css"
    css_dst = OUT_DIR / "assets" / "ai_arena_signals_jp.css"
    css_dst.parent.mkdir(parents=True, exist_ok=True)
    css_dst.write_text(css_src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {safe_rel(html_path)}")
    print(f"Wrote {safe_rel(css_dst)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
