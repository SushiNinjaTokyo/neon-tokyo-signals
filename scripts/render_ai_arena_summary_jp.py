#!/usr/bin/env python3
from __future__ import annotations

"""Render AI Arena annual summary pages from generated summary JSON.

This renderer is deliberately strict about CSS handling because the Summary
page is a visual dashboard.  If the stylesheet is not copied into site/assets,
the deployed page degrades into plain HTML and the product looks broken.

Inputs:
- site/data/japan/ai-arena/summary/latest.json
- site/data/japan/ai-arena/summary/<YEAR>/latest.json

Outputs:
- site/japan/ai-arena/summary/index.html
- site/japan/ai-arena/summary/<YEAR>/index.html
- site/assets/ai_arena_summary_jp.css
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from lib.db import ROOT, safe_rel

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()

YEAR = os.getenv("ARENA_YEAR") or os.getenv("YEAR") or ""
TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_NAME = "ai_arena_summary_jp.html.j2"
CSS_NAME = "ai_arena_summary_jp.css"


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file, returning a safe empty payload when missing.

    Missing JSON should not produce a traceback during local rendering.  The
    generated page will show an empty state, and the workflow validation step
    can still decide whether missing data should fail the build.
    """
    if not path.exists():
        return {
            "schema_version": "missing",
            "generated_at": None,
            "year": YEAR or "",
            "run_id": "missing",
            "status": "missing",
            "rankings": {
                "annual_performance": [],
                "monthly_equity_performance": [],
                "best_trades": [],
                "worst_trades": [],
            },
            "visuals": {"monthly_heatmap": []},
            "diagnostics": {"totals": {}, "agent_activity": [], "warnings": [f"Missing JSON: {safe_rel(path)}"]},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def copy_css() -> Path:
    """Copy the Summary CSS into site/assets and assert it exists.

    The assertion is intentional.  A missing CSS file is not a cosmetic issue
    here; it makes the deployed Summary page nearly unreadable.
    """
    css_src = TEMPLATE_DIR / CSS_NAME
    css_dst = OUT_DIR / "assets" / CSS_NAME
    if not css_src.exists():
        raise FileNotFoundError(f"Required Summary CSS template was not found: {safe_rel(css_src)}")
    css_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(css_src, css_dst)
    if not css_dst.exists() or css_dst.stat().st_size <= 0:
        raise RuntimeError(f"Summary CSS copy failed or produced an empty file: {safe_rel(css_dst)}")
    return css_dst


def build_env() -> Environment:
    """Build the Jinja environment used for the static page."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_one(payload: dict[str, Any], path: Path) -> None:
    """Render one Summary HTML page."""
    env = build_env()
    html = env.get_template(TEMPLATE_NAME).render(payload=payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    if not path.exists() or path.stat().st_size <= 0:
        raise RuntimeError(f"Summary render failed or produced an empty file: {safe_rel(path)}")


def main() -> int:
    css_path = copy_css()

    summary_dir = OUT_DIR / "data" / "japan" / "ai-arena" / "summary"
    current_payload = load_json(summary_dir / "latest.json")
    render_one(current_payload, OUT_DIR / "japan" / "ai-arena" / "summary" / "index.html")

    year = YEAR or str(current_payload.get("year") or "")
    if year:
        year_payload = load_json(summary_dir / year / "latest.json")
        render_one(year_payload, OUT_DIR / "japan" / "ai-arena" / "summary" / year / "index.html")

    # Final hard checks.  These make CSS/HTML regressions fail inside Actions
    # instead of silently deploying a broken dashboard.
    required = [
        OUT_DIR / "japan" / "ai-arena" / "summary" / "index.html",
        css_path,
    ]
    if year:
        required.append(OUT_DIR / "japan" / "ai-arena" / "summary" / year / "index.html")
    for path in required:
        if not path.exists() or path.stat().st_size <= 0:
            raise RuntimeError(f"Required Summary output is missing or empty: {safe_rel(path)}")

    print(f"Wrote {safe_rel(OUT_DIR / 'japan' / 'ai-arena' / 'summary' / 'index.html')}")
    if year:
        print(f"Wrote {safe_rel(OUT_DIR / 'japan' / 'ai-arena' / 'summary' / year / 'index.html')}")
    print(f"Copied CSS {safe_rel(css_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
