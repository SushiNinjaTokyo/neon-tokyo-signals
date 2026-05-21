#!/usr/bin/env python3
"""
Render /japan/daily/simulation/ from Daily JP Simulation JSON.
"""

from __future__ import annotations

import json
import math
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

SIM_JSON = Path(os.getenv("DAILY_SIM_JSON", str(OUT_DIR / "data" / "japan" / "daily" / "simulation" / "latest.json")))
if not SIM_JSON.is_absolute():
    SIM_JSON = (ROOT / SIM_JSON).resolve()
else:
    SIM_JSON = SIM_JSON.resolve()

TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_HTML = "daily_simulation_jp.html.j2"
TEMPLATE_CSS = TEMPLATE_DIR / "daily_simulation_jp.css"
OUTPUT_HTML = OUT_DIR / "japan" / "daily" / "simulation" / "index.html"
OUTPUT_CSS = OUT_DIR / "assets" / "daily_simulation_jp.css"
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
        raise FileNotFoundError(f"Daily simulation JSON not found: {safe_relative(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        v = float(value)
        if math.isnan(v) or math.isinf(v):
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


def fmt_jpy(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    if abs(v) >= 1_000_000_000:
        return f"¥{v/1_000_000_000:.2f}B"
    if abs(v) >= 1_000_000:
        return f"¥{v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"¥{v/1_000:.0f}K"
    return f"¥{v:,.0f}"


def fmt_num(value: Any, digits: int = 0) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    if digits <= 0:
        return f"{int(round(v)):,}"
    return f"{v:,.{digits}f}"


def value_class(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "neutral"
    if v > 0:
        return "positive"
    if v < 0:
        return "negative"
    return "neutral"


def chart_points(series: list[dict[str, Any]], key: str, width: int = 920, height: int = 280, pad: int = 20) -> dict[str, Any]:
    rows = []
    for row in series:
        v = as_float(row.get(key))
        if v is None:
            continue
        rows.append((row.get("date"), v))
    if not rows:
        return {"points": "", "area_points": "", "min": None, "max": None}
    vals = [v for _, v in rows]
    min_v, max_v = min(vals), max(vals)
    if min_v == max_v:
        min_v -= 1
        max_v += 1
    span = max_v - min_v
    n = len(rows)
    pts = []
    base_y = height - pad
    for i, (_, v) in enumerate(rows):
        x = pad + (width - 2 * pad) * (i / max(n - 1, 1))
        y = height - pad - ((v - min_v) / span) * (height - 2 * pad)
        pts.append(f"{x:.1f},{y:.1f}")
    area = f"{pad:.1f},{base_y:.1f} " + " ".join(pts) + f" {width-pad:.1f},{base_y:.1f}"
    return {
        "points": " ".join(pts),
        "area_points": area,
        "min": round(min_v, 2),
        "max": round(max_v, 2),
        "first_date": rows[0][0],
        "last_date": rows[-1][0],
        "last_value": round(rows[-1][1], 2),
    }


def bar_width(value: Any, max_abs: float | None = None) -> float:
    v = as_float(value) or 0.0
    denom = max_abs if max_abs and max_abs > 0 else max(abs(v), 1.0)
    return max(2.0, min(100.0, abs(v) / denom * 100.0))


def prepare(payload: dict[str, Any]) -> dict[str, Any]:
    equity_curve = payload.get("equity_curve") or []
    strategy_chart = chart_points(equity_curve, "portfolio_equity_jpy")
    benchmark_chart = chart_points(equity_curve, "benchmark_equity_jpy")
    ret_chart = chart_points(equity_curve, "strategy_return_pct")

    policies = payload.get("policy_comparison") or []
    max_policy_ret = max([abs(as_float(p.get("strategy_return_pct")) or 0) for p in policies] + [1])

    for p in policies:
        p["return_class"] = value_class(p.get("strategy_return_pct"))
        p["alpha_class"] = value_class(p.get("alpha_pct"))
        p["bar_width"] = bar_width(p.get("strategy_return_pct"), max_policy_ret)

    closed = payload.get("closed_trades") or []
    for t in closed:
        t["return_class"] = value_class(t.get("return_pct"))
        t["alpha_class"] = value_class(t.get("alpha_pct"))
        t["pnl_class"] = value_class(t.get("pnl_jpy"))

    open_positions = payload.get("open_positions") or []
    for p in open_positions:
        p["return_class"] = value_class(p.get("return_pct"))

    closed_summary = payload.get("closed_trade_summary") or {}
    for r in closed_summary.get("by_signal") or []:
        r["return_class"] = value_class(r.get("avg_return_pct"))

    return {
        "strategy_chart": strategy_chart,
        "benchmark_chart": benchmark_chart,
        "ret_chart": ret_chart,
        "policies": policies,
        "open_positions": open_positions,
        "closed_trades": closed[:40],
        "closed_summary": closed_summary,
    }


def render() -> None:
    payload = read_json(SIM_JSON)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["fmt_pct"] = fmt_pct
    env.filters["fmt_jpy"] = fmt_jpy
    env.filters["fmt_num"] = fmt_num

    template = env.get_template(TEMPLATE_HTML)
    prepared = prepare(payload)
    html = template.render(
        payload=payload,
        summary=payload.get("summary") or {},
        policy=payload.get("policy") or {},
        benchmark_quality=payload.get("benchmark_quality") or {},
        prepared=prepared,
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


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"DAILY_SIM_JSON={safe_relative(SIM_JSON)}")
    render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
