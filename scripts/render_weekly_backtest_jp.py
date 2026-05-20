#!/usr/bin/env python3
"""Render /japan/weekly-backtest/ from Weekly JP Backtest JSON."""

from __future__ import annotations

import json
import math
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

BACKTEST_JSON = Path(os.getenv("WEEKLY_BACKTEST_JSON", str(OUT_DIR / "data" / "japan" / "weekly" / "backtest" / "latest.json")))
BACKTEST_JSON = (ROOT / BACKTEST_JSON).resolve() if not BACKTEST_JSON.is_absolute() else BACKTEST_JSON.resolve()
LEGACY_BACKTEST_JSON = OUT_DIR / "data" / "weekly-jp" / "backtest" / "latest.json"

TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_HTML = "weekly_backtest_jp.html.j2"
TEMPLATE_CSS = TEMPLATE_DIR / "weekly_backtest_jp.css"
OUTPUT_HTML = OUT_DIR / "japan" / "weekly-backtest" / "index.html"
OUTPUT_CSS = OUT_DIR / "assets" / "weekly_backtest_jp.css"


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def now_jst() -> datetime:
    return datetime.now(TZ)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists() and LEGACY_BACKTEST_JSON.exists():
        path = LEGACY_BACKTEST_JSON
    if not path.exists():
        return {
            "schema_version": "weekly-jp-backtest-v1",
            "generated_at": now_jst().isoformat(timespec="seconds"),
            "market": "JP",
            "benchmark": "TOPIX",
            "horizons": ["1w", "2w", "4w", "8w", "12w"],
            "primary_horizon": "4w",
            "summary": {"signal_count": 0, "eval_date_count": 0, "top_bucket_performance": {}},
            "performance_trend": [],
            "outcomes": [],
        }
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
    return f"{v:.{digits}f}"


def fmt_int(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    return f"{int(round(v)):,}"


def return_class(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "ret-flat"
    if v > 0:
        return "ret-up"
    if v < 0:
        return "ret-down"
    return "ret-flat"


def clamp(v: float, low: float, high: float) -> float:
    return max(low, min(high, v))


def metric(summary: dict[str, Any], key: str, horizon: str, field: str) -> Any:
    try:
        return summary["top_bucket_performance"][key][horizon][field]
    except Exception:
        return None


def top_bucket_cards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    summary = payload.get("summary") or {}
    primary = payload.get("primary_horizon") or summary.get("primary_horizon") or "4w"
    cards = []
    for label, subtitle in [("Top 3", "highest conviction"), ("Top 5", "focused board"), ("Top 10", "full weekly board")]:
        p = ((summary.get("top_bucket_performance") or {}).get(label) or {}).get(primary) or {}
        cards.append({
            "label": label,
            "subtitle": subtitle,
            "count": p.get("count"),
            "avg_return_pct": p.get("avg_return_pct"),
            "median_return_pct": p.get("median_return_pct"),
            "avg_alpha_pct": p.get("avg_alpha_pct"),
            "win_rate_pct": p.get("win_rate_pct"),
            "drawdown_pct": p.get("avg_worst_drawdown_pct"),
            "return_class": return_class(p.get("avg_return_pct")),
            "alpha_class": return_class(p.get("avg_alpha_pct")),
        })
    return cards


def signal_cards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    primary = payload.get("primary_horizon") or "4w"
    by_signal = payload.get("by_signal") or {}
    cards = []
    for signal in ["Trade", "Watch", "Avoid"]:
        row = (by_signal.get(signal) or {}).get(primary) or {}
        cards.append({
            "label": signal if signal != "Watch" else "Monitor",
            "count": row.get("count"),
            "avg_return_pct": row.get("avg_return_pct"),
            "avg_alpha_pct": row.get("avg_alpha_pct"),
            "win_rate_pct": row.get("win_rate_pct"),
            "return_class": return_class(row.get("avg_return_pct")),
        })
    return cards


def build_bar_width(value: Any, max_abs: float = 8.0) -> float:
    v = as_float(value) or 0.0
    return clamp(abs(v) / max_abs * 100.0, 3.0, 100.0)


def bar_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    primary = payload.get("primary_horizon") or "4w"
    rows = []
    for card in top_bucket_cards(payload):
        rows.append({
            "label": card["label"],
            "value": card.get("avg_alpha_pct"),
            "width": build_bar_width(card.get("avg_alpha_pct"), 5.0),
            "class": return_class(card.get("avg_alpha_pct")),
        })
    return rows



def horizon_coverage_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    summary = payload.get("summary") or {}
    windows = summary.get("horizon_windows") or {}
    horizons = payload.get("horizons") or ["1w", "2w", "4w", "8w", "12w"]
    rows: list[dict[str, Any]] = []
    for h in horizons:
        w = windows.get(h) or {}
        valid = as_float(w.get("valid_signal_count")) or 0
        expected = as_float(w.get("expected_signal_count")) or 0
        coverage = as_float(w.get("coverage_pct"))
        rows.append({
            "horizon": str(h).upper(),
            "start": w.get("eval_date_start"),
            "end": w.get("eval_date_end"),
            "eval_date_count": w.get("eval_date_count") or 0,
            "valid_signal_count": int(valid),
            "pending_or_missing_signal_count": w.get("pending_or_missing_signal_count") or 0,
            "expected_signal_count": int(expected),
            "coverage_pct": coverage,
            "coverage_width": clamp(float(coverage or 0), 4.0, 100.0),
        })
    return rows

def path_from_points(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def build_trend_chart(payload: dict[str, Any]) -> dict[str, Any]:
    trend = payload.get("performance_trend") or []
    labels = ["Top 3", "Top 5", "Top 10"]
    keys = {
        "Top 3": "top_3_equity_index",
        "Top 5": "top_5_equity_index",
        "Top 10": "top_10_equity_index",
    }
    width = 920
    height = 300
    pad_x = 42
    pad_y = 34
    values = []
    for row in trend:
        for key in keys.values():
            v = as_float(row.get(key))
            if v is not None:
                values.append(v)
    if not trend or not values:
        return {"available": False, "series": [], "min": None, "max": None, "start": None, "end": None}

    min_v = min(values)
    max_v = max(values)
    if abs(max_v - min_v) < 1e-9:
        min_v -= 1.0
        max_v += 1.0
    span_x = width - 2 * pad_x
    span_y = height - 2 * pad_y
    n = max(1, len(trend) - 1)

    series = []
    for label in labels:
        pts = []
        key = keys[label]
        for i, row in enumerate(trend):
            v = as_float(row.get(key))
            if v is None:
                continue
            x = pad_x + span_x * i / n
            y = pad_y + span_y * (1 - (v - min_v) / (max_v - min_v))
            pts.append((x, y))
        latest = as_float(trend[-1].get(key))
        series.append({"label": label, "points": path_from_points(pts), "latest": latest})

    return {
        "available": True,
        "width": width,
        "height": height,
        "series": series,
        "min": min_v,
        "max": max_v,
        "start": trend[0].get("eval_date"),
        "end": trend[-1].get("eval_date"),
    }


def compact_outcomes(payload: dict[str, Any], limit: int = 30) -> list[dict[str, Any]]:
    primary = payload.get("primary_horizon") or "4w"
    out = []
    for r in (payload.get("outcomes") or [])[-limit:]:
        f = (r.get("forward") or {}).get(primary) or {}
        row = dict(r)
        row["primary_return_pct"] = f.get("return_pct")
        row["primary_alpha_pct"] = f.get("alpha_pct")
        row["primary_drawdown_pct"] = f.get("worst_drawdown_pct")
        row["return_class"] = return_class(row["primary_return_pct"])
        row["alpha_class"] = return_class(row["primary_alpha_pct"])
        out.append(row)
    return out


def top_movers(payload: dict[str, Any], key: str, limit: int = 8, reverse: bool = True) -> list[dict[str, Any]]:
    primary = payload.get("primary_horizon") or "4w"
    rows = []
    for r in payload.get("outcomes") or []:
        f = (r.get("forward") or {}).get(primary) or {}
        v = as_float(f.get(key))
        if v is None:
            continue
        row = dict(r)
        row["metric_value"] = v
        row["metric_class"] = return_class(v)
        rows.append(row)
    return sorted(rows, key=lambda x: x["metric_value"], reverse=reverse)[:limit]


def render() -> None:
    payload = read_json(BACKTEST_JSON)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["fmt_pct"] = fmt_pct
    env.filters["fmt_num"] = fmt_num
    env.filters["fmt_int"] = fmt_int

    template = env.get_template(TEMPLATE_HTML)
    rendered = template.render(
        payload=payload,
        summary=payload.get("summary") or {},
        generated_at=payload.get("generated_at"),
        source_prices_generated_at=payload.get("source_prices_generated_at"),
        primary_horizon=payload.get("primary_horizon") or "4w",
        top_bucket_cards=top_bucket_cards(payload),
        signal_cards=signal_cards(payload),
        bar_rows=bar_rows(payload),
        coverage_rows=horizon_coverage_rows(payload),
        trend_chart=build_trend_chart(payload),
        recent_outcomes=compact_outcomes(payload, 40),
        best_movers=top_movers(payload, "return_pct", 8, True),
        worst_movers=top_movers(payload, "return_pct", 8, False),
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
    print(f"BACKTEST_JSON={safe_relative(BACKTEST_JSON)}")
    render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
