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
MAIN_RANK_LIMIT = int(os.getenv("DAILY_MAIN_RANK_LIMIT", "20"))
REFERENCE_LIMIT = int(os.getenv("DAILY_REFERENCE_LIMIT", "50"))

GOOD_FLAGS = {
    "favored_relative_strength",
    "favored_compression_breakout",
    "favored_volume_compression",
    "abnormal_accumulation",
    "abnormal_accumulation_high_confidence",
    "post_catalyst_digestion",
}

RISK_FLAGS = {
    "volume_breakout_risk",
    "trade_block_volume_breakout",
    "abnormal_distribution",
    "abnormal_distribution_high_confidence",
    "volume_noise",
    "weak_close_on_volume",
    "red_close_on_volume",
    "score_cap_no_daily_confirmation",
    "score_cap_weak_volume",
    "score_cap_very_low_liquidity",
    "extended_penalty",
}


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
        "schema_version": "daily-jp-v2",
        "generated_at": generated_at,
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "source_prices": None,
        "source_prices_generated_at": None,
        "methodology": {},
        "regime": "Unknown",
        "market_pulse": [],
        "items": [],
        "all_items": [],
        "summary": {
            "items_count": 0,
            "top_symbol": None,
            "top_name": None,
            "top_score": None,
            "top_score_pts": None,
            "top_classification": None,
            "top_triage": None,
            "top_archetype": None,
            "trade": 0,
            "watch": 0,
            "ignore": 0,
            "by_triage": {},
            "by_archetype": {},
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
    if abs(v) >= 1_000_000_000_000:
        return f"¥{v / 1_000_000_000_000:.2f}T"
    if abs(v) >= 1_000_000_000:
        return f"¥{v / 1_000_000_000:.2f}B"
    if abs(v) >= 1_000_000:
        return f"¥{v / 1_000_000:.1f}M"
    return f"¥{v:,.0f}"


def css_class_for_score(score: Any) -> str:
    v = as_float(score)
    if v is None:
        return "score-none"
    # Prefer score_pts when present; normalize to 0-100 display band.
    if v > 100:
        v = v / 10.0
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


def css_class_for_liquidity(value: Any) -> str:
    s = str(value or "Unknown").strip().lower().replace(" ", "-")
    if s in {"high-liquidity", "tradable", "thin", "event-thin", "very-thin", "unknown"}:
        return f"liq-{s}"
    return "liq-unknown"


def flag_label(flag: str) -> str:
    return str(flag or "").replace("_", " ").strip()


def short_reason(reason: Any, max_len: int = 150) -> str:
    text = str(reason or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def score_width(value: Any) -> int:
    v = as_float(value)
    if v is None:
        return 2
    if v <= 1:
        v *= 100
    return max(2, min(100, int(round(v))))


def normalize_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = payload.get("all_items") or payload.get("items") or []
    if not isinstance(raw_items, list):
        return []

    out: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue

        normalized = dict(item)
        flags = item.get("flags") or []
        if not isinstance(flags, list):
            flags = []
        flags = [str(x) for x in flags]

        score_for_class = item.get("score_pts", item.get("score"))
        normalized["score_class"] = css_class_for_score(score_for_class)
        normalized["risk_class"] = css_class_for_risk(item.get("risk_level"))
        normalized["return_1d_class"] = css_class_for_return(item.get("return_1d_pct"))
        normalized["return_3d_class"] = css_class_for_return(item.get("return_3d_pct"))
        normalized["return_5d_class"] = css_class_for_return(item.get("return_5d_pct"))
        normalized["return_10d_class"] = css_class_for_return(item.get("return_10d_pct"))
        normalized["return_20d_class"] = css_class_for_return(item.get("return_20d_pct"))
        normalized["liquidity_band"] = item.get("liquidity_band") or infer_liquidity_band(item)
        normalized["liquidity_class"] = css_class_for_liquidity(normalized.get("liquidity_band"))
        normalized["is_main_rank"] = (as_float(item.get("rank")) or 9999) <= MAIN_RANK_LIMIT
        normalized["is_reference_rank"] = MAIN_RANK_LIMIT < (as_float(item.get("rank")) or 9999) <= REFERENCE_LIMIT
        normalized["good_flags"] = [f for f in flags if f in GOOD_FLAGS]
        normalized["risk_flags"] = [f for f in flags if f in RISK_FLAGS]
        normalized["neutral_flags"] = [f for f in flags if f not in GOOD_FLAGS and f not in RISK_FLAGS]
        normalized["has_good_setup"] = bool(normalized["good_flags"])
        normalized["has_risk_flag"] = bool(normalized["risk_flags"])
        normalized["good_flag_label"] = flag_label(normalized["good_flags"][0]) if normalized["good_flags"] else ""
        normalized["risk_flag_label"] = flag_label(normalized["risk_flags"][0]) if normalized["risk_flags"] else ""
        normalized["reason_short"] = short_reason(item.get("reason"))

        comps = item.get("v2_components") or item.get("components") or {}
        normalized["component_widths"] = {
            "volume": score_width(comps.get("volume_liquidity_shock", comps.get("volume_shock"))),
            "compression": score_width(comps.get("compression_release", comps.get("compression"))),
            "breakout": score_width(comps.get("breakout_setup_quality", comps.get("breakout_quality"))),
            "rs": score_width(comps.get("relative_strength")),
            "entry": score_width(comps.get("entry_timing")),
        }
        out.append(normalized)

    out.sort(key=lambda x: as_float(x.get("rank")) or 999999)
    return out


def infer_liquidity_band(item: dict[str, Any]) -> str:
    avg_value = as_float(item.get("avg_traded_value_20d_jpy"))
    today_value = as_float(item.get("latest_traded_value_jpy"))
    if avg_value is None:
        return "Unknown"
    if avg_value >= 1_000_000_000:
        return "High Liquidity"
    if avg_value >= 300_000_000:
        return "Tradable"
    if avg_value >= 100_000_000:
        return "Thin"
    if today_value is not None and today_value >= 300_000_000 and avg_value >= 70_000_000:
        return "Event Thin"
    return "Very Thin"


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


def count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "Unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def make_setup_quality(items: list[dict[str, Any]]) -> dict[str, Any]:
    main = [x for x in items if x.get("is_main_rank")]
    trade = [x for x in main if x.get("triage") == "Trade"]
    watch = [x for x in main if x.get("triage") == "Watch"]
    ignore = [x for x in main if x.get("triage") == "Ignore"]
    favored = [x for x in main if x.get("has_good_setup")]
    risk = [x for x in main if x.get("has_risk_flag")]
    volume_breakout = [x for x in main if "volume_breakout_risk" in (x.get("flags") or [])]
    distribution = [x for x in main if "abnormal_distribution" in (x.get("flags") or [])]
    noise = [x for x in main if "volume_noise" in (x.get("flags") or [])]

    return {
        "main_count": len(main),
        "reference_count": len([x for x in items if x.get("is_reference_rank")]),
        "trade_count": len(trade),
        "watch_count": len(watch),
        "ignore_count": len(ignore),
        "favored_count": len(favored),
        "risk_count": len(risk),
        "volume_breakout_risk_count": len(volume_breakout),
        "abnormal_distribution_count": len(distribution),
        "volume_noise_count": len(noise),
        "liquidity_counts": count_by(main, "liquidity_band"),
        "bucket_counts": count_by(main, "bucket"),
        "archetype_counts": count_by(main, "archetype"),
    }


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
    env.filters["flag_label"] = flag_label

    template = env.get_template(TEMPLATE_HTML)

    all_items = normalize_items(payload)
    main_items = all_items[:MAIN_RANK_LIMIT]
    reference_items = all_items[MAIN_RANK_LIMIT:REFERENCE_LIMIT]
    top_items = main_items
    market_pulse = normalize_market_pulse(payload)
    setup_quality = make_setup_quality(all_items)
    risk_items = [x for x in main_items if x.get("has_risk_flag")]
    favored_items = [x for x in main_items if x.get("has_good_setup")]

    rendered = template.render(
        payload=payload,
        items=main_items,
        all_items=all_items,
        main_items=main_items,
        reference_items=reference_items,
        top_items=top_items,
        risk_items=risk_items[:8],
        favored_items=favored_items[:8],
        market_pulse=market_pulse,
        setup_quality=setup_quality,
        summary=payload.get("summary") or {},
        generated_at=payload.get("generated_at"),
        source_prices_generated_at=payload.get("source_prices_generated_at"),
        main_rank_limit=MAIN_RANK_LIMIT,
        reference_limit=REFERENCE_LIMIT,
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
    print(f"main_items={len(main_items)} reference_items={len(reference_items)} all_items={len(all_items)}")
    print(f"risk_items={len(risk_items)} favored_items={len(favored_items)}")


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"DAILY_JSON={safe_relative(DAILY_JSON)}")
    render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
