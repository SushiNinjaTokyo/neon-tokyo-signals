#!/usr/bin/env python3
"""Render /japan/weekly/ from Weekly JP screening JSON."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Tokyo")

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
OUT_DIR = (ROOT / OUT_DIR).resolve() if not OUT_DIR.is_absolute() else OUT_DIR.resolve()

WEEKLY_JSON = Path(os.getenv("WEEKLY_JSON", str(OUT_DIR / "data" / "japan" / "weekly" / "latest.json")))
WEEKLY_JSON = (ROOT / WEEKLY_JSON).resolve() if not WEEKLY_JSON.is_absolute() else WEEKLY_JSON.resolve()
LEGACY_WEEKLY_JSON = OUT_DIR / "data" / "weekly-jp" / "latest.json"

TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_HTML = "weekly_jp.html.j2"
TEMPLATE_CSS = TEMPLATE_DIR / "weekly_jp.css"
OUTPUT_HTML = OUT_DIR / "japan" / "weekly" / "index.html"
OUTPUT_CSS = OUT_DIR / "assets" / "weekly_jp.css"


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def now_jst() -> datetime:
    return datetime.now(TZ)


def read_json(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if LEGACY_WEEKLY_JSON.exists():
        print(f"WARNING: primary weekly JSON missing, using legacy {safe_relative(LEGACY_WEEKLY_JSON)}")
        return json.loads(LEGACY_WEEKLY_JSON.read_text(encoding="utf-8"))
    print(f"WARNING: Weekly JSON not found: {safe_relative(path)}")
    return {
        "schema_version": "weekly-jp-v1",
        "date": "Unknown",
        "generated_at": now_jst().isoformat(timespec="seconds"),
        "summary": {},
        "benchmarks": {},
        "items": [],
        "all_items": [],
        "methodology": {},
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
    return f"{v:.0f}"


def fmt_jpy(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    if abs(v) >= 1_000_000_000_000:
        return f"¥{v / 1_000_000_000_000:.2f}T"
    if abs(v) >= 1_000_000_000:
        return f"¥{v / 1_000_000_000:.2f}B"
    if abs(v) >= 1_000_000:
        return f"¥{v / 1_000_000:.1f}M"
    return f"¥{v:,.0f}"


def clamp_pct(value: Any, low: float = 0.0, high: float = 100.0) -> float:
    v = as_float(value)
    if v is None:
        return low
    return max(low, min(high, v))


def flag_label(flag: str) -> str:
    mapping = {
        "stage2_trend": "Stage 2 trend",
        "fresh_10w_breakout": "Fresh 10W breakout",
        "near_52w_high": "Near 52W high",
        "volume_accumulation": "Volume accumulation",
        "institutional_liquidity": "Institutional liquidity",
        "high_liquidity": "High liquidity",
        "tradable_liquidity": "Tradable liquidity",
        "thin_liquidity": "Thin liquidity",
        "event_thin_liquidity": "Event-thin liquidity",
        "very_thin_liquidity": "Very thin liquidity",
        "extended": "Extended",
        "very_extended": "Very extended",
        "weak_close": "Weak weekly close",
        "distribution_week": "Distribution week",
        "limit_move_risk": "Limit-move risk",
    }
    return mapping.get(flag, flag.replace("_", " ").title())


def css_for_signal(signal: str | None) -> str:
    s = str(signal or "").lower()
    if s == "trade":
        return "signal-trade"
    if s == "watch":
        return "signal-watch"
    return "signal-avoid"


def css_for_score(score: Any) -> str:
    v = as_float(score) or 0.0
    if v >= 820:
        return "score-elite"
    if v >= 750:
        return "score-strong"
    if v >= 680:
        return "score-watch"
    return "score-muted"


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    x = dict(item)
    metrics = x.get("metrics") if isinstance(x.get("metrics"), dict) else {}
    flags = x.get("flags") if isinstance(x.get("flags"), list) else []
    x["signal_class"] = css_for_signal(x.get("signal"))
    x["score_class"] = css_for_score(x.get("score_pts"))
    x["ret4w"] = metrics.get("return_4w_pct")
    x["ret12w"] = metrics.get("return_12w_pct")
    x["rs12w"] = metrics.get("rs_vs_topix_12w_pct")
    x["avg_value"] = metrics.get("avg_traded_value_10w_jpy")
    x["rvol"] = metrics.get("rvol_10w")
    x["distance_52w"] = metrics.get("distance_from_52w_high_pct")
    x["score_width"] = clamp_pct((as_float(x.get("score_pts")) or 0) / 10.0, 3, 100)
    component_pts = x.get("component_pts") if isinstance(x.get("component_pts"), dict) else {}
    x["component_bars"] = [
        ("Trend", component_pts.get("trend_template_stage2"), 220),
        ("RS", component_pts.get("relative_strength_vs_topix"), 180),
        ("Breakout", component_pts.get("breakout_freshness"), 160),
        ("Base", component_pts.get("base_vcp_quality"), 150),
        ("Volume", component_pts.get("volume_accumulation"), 120),
        ("Liquidity", component_pts.get("liquidity_tradability"), 100),
    ]
    x["good_flags"] = [flag_label(f) for f in flags if f in {"stage2_trend", "fresh_10w_breakout", "near_52w_high", "volume_accumulation", "institutional_liquidity", "high_liquidity"}]
    x["risk_flags"] = [flag_label(f) for f in flags if f in {"extended", "very_extended", "weak_close", "distribution_week", "limit_move_risk", "thin_liquidity", "event_thin_liquidity", "very_thin_liquidity"}]
    return x


def build_visual(summary: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    total = max(len(items), 1)
    trade = int(summary.get("trade") or 0)
    watch = int(summary.get("watch") or 0)
    avoid = int(summary.get("avoid") or 0)
    by_bucket = summary.get("by_bucket") if isinstance(summary.get("by_bucket"), dict) else {}
    bucket_total = max(sum(int(v or 0) for v in by_bucket.values()), 1)
    return {
        "signal_mix": [
            {"label": "Trade", "value": trade, "width": trade / total * 100, "class": "signal-trade"},
            {"label": "Watch", "value": watch, "width": watch / total * 100, "class": "signal-watch"},
            {"label": "Avoid", "value": avoid, "width": avoid / total * 100, "class": "signal-avoid"},
        ],
        "bucket_mix": [
            {"label": k, "value": int(v or 0), "width": int(v or 0) / bucket_total * 100} for k, v in sorted(by_bucket.items())
        ],
        "score_bars": [
            {"label": x.get("symbol"), "score": x.get("score_pts"), "width": x.get("score_width"), "class": x.get("score_class")} for x in items[:8]
        ],
    }


def render() -> None:
    payload = read_json(WEEKLY_JSON)
    items = [normalize_item(x) for x in (payload.get("items") or []) if isinstance(x, dict)]
    trade_items = [x for x in items if x.get("signal") == "Trade"]
    watch_items = [x for x in items if x.get("signal") == "Watch"]
    avoid_items = [x for x in items if x.get("signal") == "Avoid"]
    top3 = items[:3]
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    benchmarks = payload.get("benchmarks") if isinstance(payload.get("benchmarks"), dict) else {}
    visual = build_visual(summary, items)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape(["html", "xml"]))
    env.filters["fmt_pct"] = fmt_pct
    env.filters["fmt_score"] = fmt_score
    env.filters["fmt_jpy"] = fmt_jpy
    template = env.get_template(TEMPLATE_HTML)
    html = template.render(
        weekly=payload,
        items=items,
        trade_items=trade_items,
        watch_items=watch_items,
        avoid_items=avoid_items,
        top3=top3,
        summary=summary,
        benchmarks=benchmarks,
        visual=visual,
        generated_at=payload.get("generated_at"),
        asset_version=now_jst().strftime("%Y%m%d%H%M"),
    )
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    OUTPUT_CSS.parent.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE_CSS.exists():
        raise FileNotFoundError(f"CSS template not found: {safe_relative(TEMPLATE_CSS)}")
    shutil.copyfile(TEMPLATE_CSS, OUTPUT_CSS)
    print(f"Wrote {safe_relative(OUTPUT_HTML)}")
    print(f"Wrote {safe_relative(OUTPUT_CSS)}")
    print("weekly items=", len(items), "trade=", len(trade_items), "watch=", len(watch_items), "avoid=", len(avoid_items))


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"WEEKLY_JSON={safe_relative(WEEKLY_JSON)}")
    render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
