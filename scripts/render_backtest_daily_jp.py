#!/usr/bin/env python3
"""
Render JP Daily backtest page.

Input:
- site/data/backtest-daily-jp/latest.json

Templates:
- templates/backtest_daily_jp.html.j2
- templates/backtest_daily_jp.css

Output:
- site/japan/daily/backtest/index.html
- site/assets/backtest_daily_jp.css

Important:
- This renderer does not recalculate backtest performance.
- It only formats values already produced by scripts/backtest_daily_jp.py.
- This avoids display-layer calculation drift.
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

BACKTEST_JSON = Path(
    os.getenv(
        "BACKTEST_JSON",
        str(OUT_DIR / "data" / "backtest-daily-jp" / "latest.json"),
    )
)
if not BACKTEST_JSON.is_absolute():
    BACKTEST_JSON = (ROOT / BACKTEST_JSON).resolve()
else:
    BACKTEST_JSON = BACKTEST_JSON.resolve()

TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_HTML = "backtest_daily_jp.html.j2"
TEMPLATE_CSS = TEMPLATE_DIR / "backtest_daily_jp.css"

OUTPUT_HTML = OUT_DIR / "japan" / "daily" / "backtest" / "index.html"
OUTPUT_CSS = OUT_DIR / "assets" / "backtest_daily_jp.css"

TZ = ZoneInfo("Asia/Tokyo")


GROUP_SECTIONS = [
    {
        "key": "by_triage",
        "title": "Triage Performance",
        "subtitle": "Trade / Watch / Ignore should separate signal quality.",
        "label": "Triage",
        "priority": ["Trade", "Watch", "Ignore", "Unknown"],
    },
    {
        "key": "by_archetype",
        "title": "Archetype Performance",
        "subtitle": "Identifies which signal structures are actually working.",
        "label": "Archetype",
        "priority": [
            "Volume + Compression + Breakout",
            "Volume + Compression",
            "Volume + Breakout",
            "Compression + Breakout",
            "Volume",
            "Compression",
            "Breakout",
            "Relative Strength",
            "Mixed",
            "Unknown",
        ],
    },
    {
        "key": "by_score_band",
        "title": "Score Band Performance",
        "subtitle": "Checks whether higher scores are actually predictive.",
        "label": "Score Band",
        "priority": ["800+", "700-799", "600-699", "500-599", "<500", "Unknown"],
    },
    {
        "key": "by_liquidity_band",
        "title": "Liquidity Band Performance",
        "subtitle": "Japan-specific liquidity control is critical.",
        "label": "Liquidity",
        "priority": ["High Liquidity", "Liquid", "Thin", "Very Thin", "Unknown"],
    },
    {
        "key": "by_regime",
        "title": "Market Regime Performance",
        "subtitle": "Shows whether signals work differently by broad market tape.",
        "label": "Regime",
        "priority": ["Risk-on", "Neutral", "Weakening", "Risk-off", "Unknown"],
    },
]


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def now_jst() -> datetime:
    return datetime.now(TZ)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Backtest JSON not found: {safe_relative(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        v = float(value)
        if not math.isfinite(v):
            return None
        return v
    except Exception:
        return None


def fmt_pct(value: Any, digits: int = 2, signed: bool = True) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    sign = "+" if signed and v > 0 else ""
    return f"{sign}{v:.{digits}f}%"


def fmt_num(value: Any, digits: int = 2) -> str:
    v = as_float(value)
    if v is None:
        return "—"
    return f"{v:.{digits}f}"


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


def value_class(value: Any, neutral_band: float = 0.0) -> str:
    v = as_float(value)
    if v is None:
        return "value-na"
    if v > neutral_band:
        return "value-up"
    if v < -neutral_band:
        return "value-down"
    return "value-flat"


def win_class(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "value-na"
    if v >= 55:
        return "value-up"
    if v < 45:
        return "value-down"
    return "value-flat"


def triage_class(value: Any) -> str:
    t = str(value or "").strip().lower()
    if t == "trade":
        return "triage-trade"
    if t == "watch":
        return "triage-watch"
    if t == "ignore":
        return "triage-ignore"
    return "triage-unknown"


def status_class(value: Any) -> str:
    s = str(value or "").strip().lower()
    if s in {"pass", "ok"}:
        return "status-pass"
    if s == "warning":
        return "status-warning"
    if s == "fail":
        return "status-fail"
    return "status-muted"


def horizon_key(h: Any) -> str:
    return f"{int(h)}d"


def parse_horizon_key(value: Any, fallback: int = 5) -> int:
    if value is None:
        return fallback
    text = str(value).strip().lower().replace("d", "")
    try:
        return int(text)
    except Exception:
        return fallback


def evaluation_design(summary: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if not isinstance(summary, dict):
        return {}
    design = summary.get("evaluation_design") or payload.get("evaluation_design") or {}
    return design if isinstance(design, dict) else {}


def primary_horizon_from_summary(summary: dict[str, Any], horizons: list[int]) -> int:
    design = evaluation_design(summary)
    h = parse_horizon_key(design.get("primary_horizon"), 5)
    if h in horizons:
        return h
    if 5 in horizons:
        return 5
    return max(horizons) if horizons else 5


def core_horizons_from_summary(summary: dict[str, Any], horizons: list[int]) -> list[int]:
    design = evaluation_design(summary)
    raw = design.get("daily_core_horizons") or []
    parsed = [parse_horizon_key(x, -1) for x in raw]
    out = [h for h in parsed if h in horizons]
    if out:
        return out
    return [h for h in [1, 3, 5, 10] if h in horizons]


def reference_horizons_from_summary(summary: dict[str, Any], horizons: list[int]) -> list[int]:
    design = evaluation_design(summary)
    raw = design.get("reference_horizons") or []
    parsed = [parse_horizon_key(x, -1) for x in raw]
    out = [h for h in parsed if h in horizons]
    if out:
        return out
    return [h for h in [20] if h in horizons]


def stat_for(summary_section: dict[str, Any], h: Any) -> dict[str, Any]:
    key = horizon_key(h)
    stat = summary_section.get(key) or {}
    return stat if isinstance(stat, dict) else {}


def make_overall_rows(summary: dict[str, Any], horizons: list[int]) -> list[dict[str, Any]]:
    overall = summary.get("overall") or {}
    rows: list[dict[str, Any]] = []

    for h in horizons:
        key = horizon_key(h)
        stat = overall.get(key) or {}

        rows.append(
            {
                "horizon": key.upper(),
                "count": stat.get("count"),
                "avg_return_pct": stat.get("avg_return_pct"),
                "median_return_pct": stat.get("median_return_pct"),
                "win_rate_pct": stat.get("win_rate_pct"),
                "avg_alpha_pct": stat.get("avg_alpha_pct"),
                "positive_alpha_rate_pct": stat.get("positive_alpha_rate_pct"),
                "avg_worst_pullback_pct": stat.get("avg_worst_pullback_pct"),
                "avg_score_pts": stat.get("avg_score_pts"),
                "avg_return_class": value_class(stat.get("avg_return_pct")),
                "avg_alpha_class": value_class(stat.get("avg_alpha_pct")),
                "win_rate_class": win_class(stat.get("win_rate_pct")),
                "pullback_class": value_class(stat.get("avg_worst_pullback_pct")),
            }
        )

    return rows


def sort_group_keys(grouped: dict[str, Any], priority: list[str]) -> list[str]:
    keys = [str(k) for k in grouped.keys()]

    order = {name: i for i, name in enumerate(priority)}

    def key_fn(k: str) -> tuple[int, str]:
        return (order.get(k, 999), k)

    return sorted(keys, key=key_fn)


def make_group_sections(summary: dict[str, Any], horizons: list[int]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []

    for spec in GROUP_SECTIONS:
        grouped = summary.get(spec["key"]) or {}
        if not isinstance(grouped, dict) or not grouped:
            continue

        rows: list[dict[str, Any]] = []

        for group_name in sort_group_keys(grouped, spec["priority"]):
            group_stats = grouped.get(group_name) or {}
            cells: list[dict[str, Any]] = []

            for h in horizons:
                key = horizon_key(h)
                stat = group_stats.get(key) or {}
                cells.append(
                    {
                        "horizon": key.upper(),
                        "count": stat.get("count"),
                        "avg_return_pct": stat.get("avg_return_pct"),
                        "median_return_pct": stat.get("median_return_pct"),
                        "win_rate_pct": stat.get("win_rate_pct"),
                        "avg_alpha_pct": stat.get("avg_alpha_pct"),
                        "positive_alpha_rate_pct": stat.get("positive_alpha_rate_pct"),
                        "avg_worst_pullback_pct": stat.get("avg_worst_pullback_pct"),
                        "avg_return_class": value_class(stat.get("avg_return_pct")),
                        "avg_alpha_class": value_class(stat.get("avg_alpha_pct")),
                        "win_rate_class": win_class(stat.get("win_rate_pct")),
                    }
                )

            first_count = None
            for cell in cells:
                if cell.get("count") is not None:
                    first_count = cell.get("count")
                    break

            rows.append(
                {
                    "name": group_name,
                    "name_class": triage_class(group_name) if spec["key"] == "by_triage" else "",
                    "count": first_count,
                    "cells": cells,
                }
            )

        sections.append(
            {
                "title": spec["title"],
                "subtitle": spec["subtitle"],
                "label": spec["label"],
                "rows": rows,
            }
        )

    return sections


def get_return(row: dict[str, Any], horizon: int = 20) -> float | None:
    return as_float((row.get("future_returns_pct") or {}).get(horizon_key(horizon)))


def get_alpha(row: dict[str, Any], horizon: int = 20) -> float | None:
    return as_float((row.get("alpha_vs_topix_pct") or {}).get(horizon_key(horizon)))


def get_pullback(row: dict[str, Any], horizon: int = 20) -> float | None:
    return as_float((row.get("worst_pullback_pct") or {}).get(horizon_key(horizon)))


def normalize_signal_rows(items: list[dict[str, Any]], horizons: list[int], primary_horizon: int) -> dict[str, list[dict[str, Any]]]:
    if not items:
        return {
            "recent": [],
            "top_return": [],
            "top_alpha": [],
            "worst": [],
        }

    def enrich(row: dict[str, Any]) -> dict[str, Any]:
        r = dict(row)
        ret = get_return(r, primary_horizon)
        alpha = get_alpha(r, primary_horizon)
        pullback = get_pullback(r, primary_horizon)
        r["primary_horizon"] = horizon_key(primary_horizon).upper()
        r["primary_return"] = ret
        r["primary_alpha"] = alpha
        r["primary_pullback"] = pullback
        r["primary_return_class"] = value_class(ret)
        r["primary_alpha_class"] = value_class(alpha)
        r["primary_pullback_class"] = value_class(pullback)
        r["triage_css"] = triage_class(r.get("triage"))
        return r

    enriched = [enrich(x) for x in items if isinstance(x, dict)]

    recent = sorted(
        enriched,
        key=lambda x: (
            str(x.get("eval_date") or ""),
            -int(x.get("rank") or 9999) * -1,
        ),
        reverse=True,
    )[:80]

    top_return = sorted(
        [x for x in enriched if get_return(x, primary_horizon) is not None],
        key=lambda x: get_return(x, primary_horizon) or -9999,
        reverse=True,
    )[:12]

    top_alpha = sorted(
        [x for x in enriched if get_alpha(x, primary_horizon) is not None],
        key=lambda x: get_alpha(x, primary_horizon) or -9999,
        reverse=True,
    )[:12]

    worst = sorted(
        [x for x in enriched if get_return(x, primary_horizon) is not None],
        key=lambda x: get_return(x, primary_horizon) or 9999,
    )[:12]

    return {
        "recent": recent,
        "top_return": top_return,
        "top_alpha": top_alpha,
        "worst": worst,
    }


def make_insights(summary: dict[str, Any], horizons: list[int], primary_horizon: int, core_horizons: list[int]) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    overall = summary.get("overall") or {}
    by_triage = summary.get("by_triage") or {}
    mh = summary.get("model_health") or {}

    primary_stat = overall.get(horizon_key(primary_horizon)) or {}
    if primary_stat:
        insights.append(
            {
                "label": f"Primary {primary_horizon}D avg",
                "value": fmt_pct(primary_stat.get("avg_return_pct")),
                "detail": f"{fmt_pct(primary_stat.get('avg_alpha_pct'))} alpha / {fmt_pct(primary_stat.get('win_rate_pct'), signed=False)} win",
                "class": value_class(primary_stat.get("avg_return_pct")),
            }
        )

    trade_primary = stat_for(by_triage.get("Trade") or {}, primary_horizon)
    if trade_primary.get("count"):
        insights.append(
            {
                "label": f"Trade {primary_horizon}D avg",
                "value": fmt_pct(trade_primary.get("avg_return_pct")),
                "detail": f"{fmt_pct(trade_primary.get('avg_alpha_pct'))} alpha",
                "class": value_class(trade_primary.get("avg_return_pct")),
            }
        )

    checks = ((summary.get("model_diagnostics") or {}).get("cross_horizon_consistency") or {})
    core_count = checks.get("core_horizon_count") or len(core_horizons)
    trade_beats = checks.get("trade_beats_ignore_core_horizons")
    if core_count:
        insights.append(
            {
                "label": "Core short-term edge",
                "value": f"{trade_beats or 0}/{core_count}",
                "detail": "Trade beats Ignore across Daily core horizons",
                "class": "value-up" if trade_beats and trade_beats >= max(1, core_count // 2) else "value-down",
            }
        )

    if mh:
        insights.append(
            {
                "label": "Model health",
                "value": mh.get("verdict") or "—",
                "detail": f"Judged on {str(mh.get('primary_horizon') or horizon_key(primary_horizon)).upper()}, not 20D",
                "class": status_class(mh.get("verdict")),
            }
        )

    if not insights:
        insights.append(
            {
                "label": "Backtest status",
                "value": "No mature stats",
                "detail": "Run a wider range backtest.",
                "class": "value-na",
            }
        )

    return insights[:4]





# -----------------------------------------------------------------------------
# Diagnostic view models. These are format-only transforms; no performance math.
# -----------------------------------------------------------------------------

def make_model_health_view(summary: dict[str, Any]) -> dict[str, Any]:
    mh = summary.get("model_health") or {}
    checks = mh.get("checks") or {}
    cards = [
        {
            "label": "Verdict",
            "value": mh.get("verdict") or "Insufficient",
            "detail": f"Primary short-term horizon: {str(mh.get('primary_horizon') or '—').upper()}",
            "class": status_class(mh.get("verdict")),
        },
        {
            "label": "Trade vs Ignore Alpha",
            "value": fmt_pct(mh.get("trade_minus_ignore_alpha_pct")),
            "detail": checks.get("trade_vs_ignore_alpha") or "Insufficient",
            "class": status_class(checks.get("trade_vs_ignore_alpha")),
        },
        {
            "label": "Watch vs Ignore Alpha",
            "value": fmt_pct(mh.get("watch_minus_ignore_alpha_pct")),
            "detail": checks.get("watch_vs_ignore_alpha") or "Insufficient",
            "class": status_class(checks.get("watch_vs_ignore_alpha")),
        },
        {
            "label": "Score Monotonicity",
            "value": checks.get("score_monotonicity") or "Insufficient",
            "detail": "Higher score bands should beat lower bands",
            "class": status_class(checks.get("score_monotonicity")),
        },
        {
            "label": "Outlier Concentration",
            "value": checks.get("outlier_concentration") or "Insufficient",
            "detail": f"Top symbol: {fmt_pct((mh.get('outlier_concentration') or {}).get('top_symbol_contribution_pct'), signed=False)} of positive-return pool",
            "class": status_class(checks.get("outlier_concentration")),
        },
        {
            "label": "Avg vs Median Gap",
            "value": fmt_pct((mh.get("median_average_gap") or {}).get("gap_pct")),
            "detail": checks.get("median_average_gap") or "Insufficient",
            "class": status_class(checks.get("median_average_gap")),
        },
    ]
    return {"raw": mh, "cards": cards}


def make_filter_rows(summary: dict[str, Any], horizons: list[int]) -> list[dict[str, Any]]:
    fp = summary.get("filtered_performance") or {}
    order = [
        "rank_lte_10",
        "rank_lte_20",
        "trade_only",
        "watch_only",
        "trade_plus_watch",
        "score_gte_500",
        "score_gte_600",
        "score_gte_700",
        "liquidity_gte_liquid",
        "abnormal_accumulation",
        "abnormal_accumulation_watch",
        "abnormal_distribution",
        "volume_noise",
        "excluding_top_1pct_outliers",
        "winsorized_average",
    ]
    rows: list[dict[str, Any]] = []
    for key in order:
        item = fp.get(key) or {}
        stats = item.get("stats") or {}
        if not item:
            continue
        cells = []
        for h in horizons:
            hk = horizon_key(h)
            stat = stats.get(hk) or {}
            cells.append(
                {
                    "horizon": hk.upper(),
                    "count": stat.get("count"),
                    "avg_return_pct": stat.get("avg_return_pct"),
                    "median_return_pct": stat.get("median_return_pct"),
                    "avg_alpha_pct": stat.get("avg_alpha_pct"),
                    "win_rate_pct": stat.get("win_rate_pct"),
                    "winsorized_avg_return_pct": stat.get("winsorized_avg_return_pct"),
                    "gap_pct": stat.get("median_average_gap_pct"),
                    "avg_class": value_class(stat.get("avg_return_pct")),
                    "alpha_class": value_class(stat.get("avg_alpha_pct")),
                    "win_class": win_class(stat.get("win_rate_pct")),
                }
            )
        rows.append({"key": key, "label": item.get("label") or key, "description": item.get("description") or "", "cells": cells})
    return rows


def make_rank_bucket_rows(summary: dict[str, Any], horizons: list[int]) -> list[dict[str, Any]]:
    rb = summary.get("rank_bucket_performance") or {}
    order = ["rank_1_5", "rank_1_10", "rank_11_20", "rank_21_50"]
    rows: list[dict[str, Any]] = []
    for key in order:
        item = rb.get(key) or {}
        if not item:
            continue
        stats = item.get("stats") or {}
        cells = []
        for h in horizons:
            hk = horizon_key(h)
            stat = stats.get(hk) or {}
            cells.append(
                {
                    "horizon": hk.upper(),
                    "count": stat.get("count"),
                    "avg_return_pct": stat.get("avg_return_pct"),
                    "median_return_pct": stat.get("median_return_pct"),
                    "avg_alpha_pct": stat.get("avg_alpha_pct"),
                    "win_rate_pct": stat.get("win_rate_pct"),
                    "gap_pct": stat.get("median_average_gap_pct"),
                    "avg_class": value_class(stat.get("avg_return_pct")),
                    "alpha_class": value_class(stat.get("avg_alpha_pct")),
                    "win_class": win_class(stat.get("win_rate_pct")),
                }
            )
        first_count = next((c.get("count") for c in cells if c.get("count") is not None), None)
        rows.append({"label": item.get("label") or key, "count": first_count, "cells": cells})
    return rows


def make_outlier_view(summary: dict[str, Any]) -> dict[str, Any]:
    oa = summary.get("outlier_analysis") or {}
    contributors = []
    for row in oa.get("top_return_contributors") or []:
        r = dict(row)
        r["triage_css"] = triage_class(r.get("triage"))
        r["return_class"] = value_class(r.get("return_pct"))
        r["alpha_class"] = value_class(r.get("alpha_pct"))
        contributors.append(r)
    symbols = []
    for row in oa.get("top_symbol_contributors") or []:
        r = dict(row)
        r["return_class"] = value_class(r.get("avg_return_pct"))
        symbols.append(r)
    return {"raw": oa, "contributors": contributors[:12], "symbols": symbols[:12], "status_class": status_class(oa.get("average_return_distortion_warning"))}


def make_repeated_symbol_view(summary: dict[str, Any]) -> dict[str, Any]:
    rs = summary.get("repeated_symbol_analysis") or {}
    rows = []
    for row in rs.get("most_repeated_symbols") or []:
        r = dict(row)
        r["return_class"] = value_class(r.get("avg_return_pct"))
        r["alpha_class"] = value_class(r.get("avg_alpha_pct"))
        rows.append(r)
    return {"raw": rs, "rows": rows[:15]}


def make_diagnostic_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    md = summary.get("model_diagnostics") or {}
    checks = md.get("horizon_checks") or {}
    rows = []
    for hk in sorted(checks.keys(), key=lambda x: int(str(x).replace("d", "")) if str(x).replace("d", "").isdigit() else 999):
        item = checks.get(hk) or {}
        mono = item.get("score_band_avg_alpha_monotonicity") or {}
        med_mono = item.get("score_band_median_alpha_monotonicity") or {}
        rows.append(
            {
                "horizon": hk.upper(),
                "role": str(item.get("role") or "secondary").title(),
                "role_class": "role-primary" if item.get("role") == "primary" else "role-core" if item.get("role") == "core" else "role-reference" if item.get("role") == "reference" else "role-secondary",
                "trade_minus_ignore_alpha_pct": item.get("trade_minus_ignore_alpha_pct"),
                "watch_minus_ignore_alpha_pct": item.get("watch_minus_ignore_alpha_pct"),
                "trade_minus_ignore_median_alpha_pct": item.get("trade_minus_ignore_median_alpha_pct"),
                "score_mono": mono.get("status") or "Insufficient",
                "score_mono_class": status_class(mono.get("status")),
                "score_median_mono": med_mono.get("status") or "Insufficient",
                "score_median_mono_class": status_class(med_mono.get("status")),
                "trade_class": value_class(item.get("trade_minus_ignore_alpha_pct")),
                "watch_class": value_class(item.get("watch_minus_ignore_alpha_pct")),
                "median_class": value_class(item.get("trade_minus_ignore_median_alpha_pct")),
            }
        )
    return rows

def render() -> None:
    payload = read_json(BACKTEST_JSON)

    if payload.get("schema_version") != "backtest-daily-jp-v1":
        raise ValueError(f"Unexpected schema_version: {payload.get('schema_version')}")

    horizons = [int(h) for h in payload.get("horizons") or [1, 3, 5, 10, 20]]
    summary = payload.get("summary") or {}
    items = payload.get("items") or []
    date_states = payload.get("date_states") or []

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    env.filters["fmt_pct"] = fmt_pct
    env.filters["fmt_num"] = fmt_num
    env.filters["fmt_int"] = fmt_int
    env.filters["fmt_jpy"] = fmt_jpy

    template = env.get_template(TEMPLATE_HTML)

    primary_horizon = primary_horizon_from_summary(summary, horizons)
    core_horizons = core_horizons_from_summary(summary, horizons)
    reference_horizons = reference_horizons_from_summary(summary, horizons)

    overall_rows = make_overall_rows(summary, horizons)
    group_sections = make_group_sections(summary, horizons)
    signal_rows = normalize_signal_rows(items, horizons, primary_horizon)
    insights = make_insights(summary, horizons, primary_horizon, core_horizons)

    rendered = template.render(
        payload=payload,
        summary=summary,
        horizons=horizons,
        primary_horizon=primary_horizon,
        core_horizons=core_horizons,
        reference_horizons=reference_horizons,
        evaluation_design=evaluation_design(summary, payload),
        overall_rows=overall_rows,
        group_sections=group_sections,
        insights=insights,
        model_health=make_model_health_view(summary),
        filtered_rows=make_filter_rows(summary, horizons),
        rank_bucket_rows=make_rank_bucket_rows(summary, horizons),
        outlier_view=make_outlier_view(summary),
        repeated_symbol_view=make_repeated_symbol_view(summary),
        diagnostic_rows=make_diagnostic_rows(summary),
        recent_rows=signal_rows["recent"],
        top_return_rows=signal_rows["top_return"],
        top_alpha_rows=signal_rows["top_alpha"],
        worst_rows=signal_rows["worst"],
        date_states=date_states[-30:],
        generated_at=payload.get("generated_at"),
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
