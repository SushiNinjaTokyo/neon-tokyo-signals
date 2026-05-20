#!/usr/bin/env python3
"""Render /japan/weekly-simulation/ from Weekly JP simulation JSON."""

from __future__ import annotations

import json
import math
import os
import shutil
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Tokyo")

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
OUT_DIR = (ROOT / OUT_DIR).resolve() if not OUT_DIR.is_absolute() else OUT_DIR.resolve()

SIM_JSON = Path(os.getenv("WEEKLY_JP_SIMULATION_JSON", str(OUT_DIR / "data" / "japan" / "weekly" / "simulation" / "latest.json")))
SIM_JSON = (ROOT / SIM_JSON).resolve() if not SIM_JSON.is_absolute() else SIM_JSON.resolve()

TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_HTML = "weekly_simulation_jp.html.j2"
TEMPLATE_CSS = TEMPLATE_DIR / "weekly_simulation_jp.css"
OUTPUT_HTML = OUT_DIR / "japan" / "weekly-simulation" / "index.html"
OUTPUT_CSS = OUT_DIR / "assets" / "weekly_simulation_jp.css"


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def now_jst() -> datetime:
    return datetime.now(TZ)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Simulation JSON not found: {safe_relative(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        v = float(value)
        if not math.isfinite(v):
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


def fmt_num(value: Any, digits: int = 1) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    return f"{v:,.{digits}f}"


def fmt_int(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    return f"{int(round(v)):,}"


def fmt_jpy(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1_000_000_000:
        return f"{sign}¥{v/1_000_000_000:.2f}B"
    if v >= 1_000_000:
        return f"{sign}¥{v/1_000_000:.1f}M"
    return f"{sign}¥{v:,.0f}"


def return_class(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "flat"
    if v > 0:
        return "up"
    if v < 0:
        return "down"
    return "flat"


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def polyline(points: list[dict[str, Any]], key: str, width: int = 920, height: int = 260, pad: int = 26) -> str:
    vals = [as_float(p.get(key)) for p in points]
    clean = [v for v in vals if v is not None]
    if len(clean) < 2:
        return ""
    lo = min(clean)
    hi = max(clean)
    if abs(hi - lo) < 1e-9:
        lo -= 1
        hi += 1
    coords = []
    n = len(points)
    for i, p in enumerate(points):
        v = as_float(p.get(key))
        if v is None:
            continue
        x = pad + (width - pad * 2) * (i / max(1, n - 1))
        y = height - pad - (height - pad * 2) * ((v - lo) / (hi - lo))
        coords.append(f"{x:.1f},{y:.1f}")
    return " ".join(coords)


def build_chart(payload: dict[str, Any]) -> dict[str, Any]:
    curve = payload.get("equity_curve") or []
    benchmark_quality = payload.get("benchmark_quality") or {}
    benchmark_valid = benchmark_quality.get("status") == "valid"
    return {
        "strategy_line": polyline(curve, "portfolio_equity"),
        "benchmark_line": polyline(curve, "benchmark_equity") if benchmark_valid else "",
        "return_line": polyline(curve, "portfolio_return_pct"),
        "benchmark_return_line": polyline(curve, "benchmark_return_pct") if benchmark_valid else "",
        "benchmark_valid": benchmark_valid,
        "benchmark_status": benchmark_quality.get("status") or "unknown",
        "benchmark_message": benchmark_quality.get("message"),
        "points": curve,
        "last": curve[-1] if curve else {},
        "first": curve[0] if curve else {},
    }


def bars_from_summary(summary_map: dict[str, Any], metric: str = "avg_return_pct", limit: int = 8) -> list[dict[str, Any]]:
    rows = []
    for label, data in (summary_map or {}).items():
        value = as_float((data or {}).get(metric))
        rows.append({"label": label, "value": value, "class": return_class(value)})
    rows.sort(key=lambda x: (x["value"] is not None, x["value"] or -999), reverse=True)
    max_abs = max([abs(x["value"] or 0) for x in rows] + [1])
    for x in rows:
        x["width"] = clamp(abs(x["value"] or 0) / max_abs * 100, 3, 100)
    return rows[:limit]


def render() -> None:
    payload = read_json(SIM_JSON)
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape(["html", "xml"]))
    env.filters["fmt_pct"] = fmt_pct
    env.filters["fmt_num"] = fmt_num
    env.filters["fmt_int"] = fmt_int
    env.filters["fmt_jpy"] = fmt_jpy
    env.filters["return_class"] = return_class
    template = env.get_template(TEMPLATE_HTML)
    summary = payload.get("summary") or {}
    chart = build_chart(payload)
    closed = payload.get("closed_trades") or []
    open_positions = payload.get("open_positions") or []
    rendered = template.render(
        payload=payload,
        summary=summary,
        policy=payload.get("policy") or {},
        chart=chart,
        benchmark_quality=payload.get("benchmark_quality") or {},
        benchmark_valid=(payload.get("benchmark_quality") or {}).get("status") == "valid",
        open_positions=open_positions,
        closed_trades=closed[:12],
        skipped_orders=(payload.get("skipped_orders") or [])[-12:],
        strategy_comparison=payload.get("strategy_comparison") or [],
        signal_bars=bars_from_summary(payload.get("signal_summary") or {}, "avg_return_pct"),
        quality_bars=bars_from_summary(payload.get("quality_summary") or {}, "avg_return_pct"),
        theme_exposure=payload.get("open_theme_exposure") or [],
        bucket_exposure=payload.get("open_bucket_exposure") or [],
        asset_version=now_jst().strftime("%Y%m%d%H%M"),
    )
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(rendered, encoding="utf-8")
    OUTPUT_CSS.parent.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE_CSS.exists():
        raise FileNotFoundError(f"CSS template not found: {safe_relative(TEMPLATE_CSS)}")
    shutil.copyfile(TEMPLATE_CSS, OUTPUT_CSS)
    print(f"Wrote {safe_relative(OUTPUT_HTML)}")
    print(f"Wrote {safe_relative(OUTPUT_CSS)}")


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"SIM_JSON={safe_relative(SIM_JSON)}")
    render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
