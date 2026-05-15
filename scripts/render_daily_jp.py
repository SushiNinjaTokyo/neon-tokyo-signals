#!/usr/bin/env python3
"""
Render /japan/daily/ page from site/data/daily-jp/latest.json.

Input:
- site/data/daily-jp/latest.json

Templates:
- templates/daily_jp.html.j2
- templates/daily_jp.css

Output:
- site/japan/daily/index.html
- site/assets/daily_jp.css
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()
else:
    OUT_DIR = OUT_DIR.resolve()

DAILY_JSON = Path(
    os.getenv("DAILY_JSON", str(OUT_DIR / "data" / "daily-jp" / "latest.json"))
)
if not DAILY_JSON.is_absolute():
    DAILY_JSON = (ROOT / DAILY_JSON).resolve()
else:
    DAILY_JSON = DAILY_JSON.resolve()

TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_HTML = "daily_jp.html.j2"
TEMPLATE_CSS = TEMPLATE_DIR / "daily_jp.css"

OUTPUT_HTML = OUT_DIR / "japan" / "daily" / "index.html"
OUTPUT_CSS = OUT_DIR / "assets" / "daily_jp.css"

TZ = ZoneInfo("Asia/Tokyo")


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def now_jst() -> datetime:
    return datetime.now(TZ)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        print(f"WARNING: Daily JSON not found: {safe_relative(path)}")
        return fallback_payload()

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fallback_payload() -> dict[str, Any]:
    generated_at = now_jst().isoformat(timespec="seconds")
    return {
        "schema_version": "daily-jp-v1",
        "generated_at": generated_at,
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "source_prices": None,
        "source_prices_generated_at": None,
        "weights": {},
        "score_notes": {
            "not_included_yet": [
                "news",
                "earnings",
                "timely_disclosure",
                "fundamentals",
            ]
        },
        "market_pulse": [],
        "items": [],
        "summary": {
            "items_count": 0,
            "top_symbol": None,
            "top_name": None,
            "top_score": None,
            "top_classification": None,
            "by_classification": {},
            "by_bucket": {},
            "by_risk": {},
        },
    }


def as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        v = float(value)
        if v != v:
            return None
        return v
    except Exception:
        return None


def fmt_pct(value: Any, digits: int = 1, signed: bool = True) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    sign = "+" if signed and v > 0 else ""
    return f"{sign}{v:.{digits}f}%"


def fmt_score(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    return f"{v:.1f}"


def fmt_int(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    return f"{int(round(v)):,}"


def fmt_jpy(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "—"

    if abs(v) >= 1_000_000_000:
        return f"¥{v / 1_000_000_000:.2f}B"

    if abs(v) >= 1_000_000:
        return f"¥{v / 1_000_000:.1f}M"

    return f"¥{v:,.0f}"


def css_class_for_score(score: Any) -> str:
    v = as_float(score)
    if v is None:
        return "score-none"
    if v >= 80:
        return "score-hot"
    if v >= 65:
        return "score-strong"
    if v >= 50:
        return "score-watch"
    return "score-muted"


def css_class_for_risk(risk: Any) -> str:
    r = str(risk or "").strip().lower()
    if r == "high":
        return "risk-high"
    if r == "medium":
        return "risk-medium"
    if r == "normal":
        return "risk-normal"
    return "risk-unknown"


def css_class_for_return(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "ret-flat"
    if v > 0:
        return "ret-up"
    if v < 0:
        return "ret-down"
    return "ret-flat"


def normalize_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("items") or []
    if not isinstance(items, list):
        return []

    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        normalized = dict(item)
        normalized["score_class"] = css_class_for_score(item.get("score"))
        normalized["risk_class"] = css_class_for_risk(item.get("risk_level"))
        normalized["return_1d_class"] = css_class_for_return(item.get("return_1d_pct"))
        normalized["return_5d_class"] = css_class_for_return(item.get("return_5d_pct"))
        normalized["return_20d_class"] = css_class_for_return(item.get("return_20d_pct"))
        out.append(normalized)

    return out


def normalize_market_pulse(payload: dict[str, Any]) -> list[dict[str, Any]]:
    pulse = payload.get("market_pulse") or []
    if not isinstance(pulse, list):
        return []

    out: list[dict[str, Any]] = []
    for item in pulse:
        if not isinstance(item, dict):
            continue

        normalized = dict(item)
        normalized["return_1d_class"] = css_class_for_return(item.get("return_1d_pct"))
        normalized["return_5d_class"] = css_class_for_return(item.get("return_5d_pct"))
        normalized["return_20d_class"] = css_class_for_return(item.get("return_20d_pct"))
        out.append(normalized)

    return out


def render() -> None:
    payload = read_json(DAILY_JSON)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    env.filters["fmt_pct"] = fmt_pct
    env.filters["fmt_score"] = fmt_score
    env.filters["fmt_int"] = fmt_int
    env.filters["fmt_jpy"] = fmt_jpy

    template = env.get_template(TEMPLATE_HTML)

    items = normalize_items(payload)
    market_pulse = normalize_market_pulse(payload)

    top_items = items[:10]

    rendered = template.render(
        payload=payload,
        items=items,
        top_items=top_items,
        market_pulse=market_pulse,
        summary=payload.get("summary") or {},
        generated_at=payload.get("generated_at"),
        source_prices_generated_at=payload.get("source_prices_generated_at"),
        asset_version=now_jst().strftime("%Y%m%d%H%M"),
    )

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(rendered, encoding="utf-8")

    OUTPUT_CSS.parent.mkdir(parents=True, exist_ok=True)
    if TEMPLATE_CSS.exists():
        shutil.copyfile(TEMPLATE_CSS, OUTPUT_CSS)
    else:
        raise FileNotFoundError(f"CSS template not found: {safe_relative(TEMPLATE_CSS)}")

    print(f"Wrote {safe_relative(OUTPUT_HTML)}")
    print(f"Wrote {safe_relative(OUTPUT_CSS)}")


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"DAILY_JSON={safe_relative(DAILY_JSON)}")
    render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
