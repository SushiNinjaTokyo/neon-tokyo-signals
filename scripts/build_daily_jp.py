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

Design intent:
- Make the Daily page a 5-second decision board for investors.
- Separate Actionable signals from high-score-but-blocked names.
- Keep Rank 1-20 as the main decision set and Rank 21-50 as reference only.
- Translate internal model flags into investor-readable labels.
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
BLOCKED_SCORE_FLOOR = int(os.getenv("DAILY_BLOCKED_SCORE_FLOOR", "500"))

GOOD_FLAGS = {
    "favored_relative_strength",
    "favored_compression_breakout",
    "favored_volume_compression",
    "abnormal_accumulation",
    "abnormal_accumulation_high_confidence",
    "post_catalyst_digestion",
    "rs_20d_positive",
    "rs_60d_leader",
    "compression_release",
    "compressed_setup",
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
    "score_cap_low_volume_confirmation",
    "score_cap_very_low_liquidity",
    "score_cap_hot_5d",
    "score_cap_hot_20d",
    "extended_penalty",
    "extended_risk",
    "very_low_liquidity",
    "low_liquidity",
    "thin_today_value",
    "no_daily_confirmation",
    "weak_5d_momentum",
}

FLAG_LABELS = {
    "favored_relative_strength": "Favored RS setup",
    "favored_compression_breakout": "Favored compression breakout",
    "favored_volume_compression": "Favored volume + compression",
    "abnormal_accumulation": "Abnormal accumulation",
    "abnormal_accumulation_high_confidence": "High-confidence accumulation",
    "post_catalyst_digestion": "Catalyst digestion",
    "rs_20d_positive": "20D RS positive",
    "rs_60d_leader": "60D RS leader",
    "compression_release": "Compression release",
    "compressed_setup": "Compressed setup",
    "breaks_20d_high": "Breaks 20D high",
    "breakout_20d": "20D breakout",
    "breakout_50d": "50D breakout",
    "above_key_mas": "Above key moving averages",
    "upper_20d_range": "Upper 20D range",
    "major_volume_shock": "Major volume shock",
    "volume_expansion": "Volume expansion",
    "large_traded_value": "Institutional-size turnover",
    "liquid_enough": "Tradable liquidity",
    "discovery_watch_candidate": "Discovery watch candidate",
    "volume_breakout_risk": "Exhaustion risk",
    "trade_block_volume_breakout": "Trade blocked: exhaustion pattern",
    "abnormal_distribution": "Distribution risk",
    "abnormal_distribution_high_confidence": "High-confidence distribution",
    "volume_noise": "Noisy volume",
    "weak_close_on_volume": "Weak close on volume",
    "red_close_on_volume": "Red close on volume",
    "score_cap_no_daily_confirmation": "No daily confirmation",
    "score_cap_weak_volume": "Weak volume cap",
    "score_cap_low_volume_confirmation": "Low-volume confirmation cap",
    "score_cap_very_low_liquidity": "Very low liquidity cap",
    "score_cap_hot_5d": "Hot 5D move cap",
    "score_cap_hot_20d": "Hot 20D move cap",
    "extended_penalty": "Extended move penalty",
    "extended_risk": "Extended risk",
    "very_low_liquidity": "Very low liquidity",
    "low_liquidity": "Low liquidity",
    "thin_today_value": "Thin current turnover",
    "no_daily_confirmation": "No daily confirmation",
    "weak_5d_momentum": "Weak 5D momentum",
    "partial_data": "Partial data",
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
    raw = str(flag or "").strip()
    return FLAG_LABELS.get(raw, raw.replace("_", " ").strip().title())


def short_reason(reason: Any, max_len: int = 150) -> str:
    text = str(reason or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def score_width(value: Any) -> int:
    v = as_float(value)
    if v is None:
        return 0
    if v > 100:
        v = v / 10.0
    return int(max(2, min(100, round(v))))


def component_width(value: Any) -> int:
    v = as_float(value)
    if v is None:
        return 0
    return int(max(2, min(100, round(v * 100))))


def infer_liquidity_band(item: dict[str, Any]) -> str:
    existing = item.get("liquidity_band")
    if existing:
        return str(existing)
    avg = as_float(item.get("avg_traded_value_20d_jpy"))
    today = as_float(item.get("latest_traded_value_jpy"))
    if avg is None:
        return "Unknown"
    if avg >= 1_000_000_000:
        return "High Liquidity"
    if avg >= 300_000_000:
        return "Tradable"
    if avg >= 100_000_000:
        return "Thin"
    if today is not None and today >= 300_000_000 and avg >= 70_000_000:
        return "Event Thin"
    return "Very Thin"


def split_flags(flags: Any) -> tuple[list[str], list[str], list[str]]:
    if not isinstance(flags, list):
        flags = []
    good: list[str] = []
    risk: list[str] = []
    neutral: list[str] = []
    for flag in flags:
        f = str(flag or "").strip()
        if not f:
            continue
        label = flag_label(f)
        if f in GOOD_FLAGS:
            good.append(label)
        elif f in RISK_FLAGS:
            risk.append(label)
        else:
            neutral.append(label)
    return good, risk, neutral


def decision_label(item: dict[str, Any]) -> str:
    triage = str(item.get("triage") or "Ignore")
    classification = str(item.get("classification") or "No Signal")
    if triage == "Trade":
        return "Actionable Trade"
    if triage == "Watch":
        if "Discovery" in classification:
            return "Actionable Watch · Discovery"
        if "Exhaustion" in classification:
            return "Watch Only · Risky Tape"
        return "Actionable Watch"
    if item.get("risk_flags"):
        return "Blocked by Risk Controls"
    if item.get("good_flags"):
        return "High Quality, Waiting for Trigger"
    return "No Action"


def decision_reason(item: dict[str, Any]) -> str:
    triage = str(item.get("triage") or "Ignore")
    score_pts = int(as_float(item.get("score_pts")) or 0)
    risk_flags = item.get("risk_flags") or []
    good_flags = item.get("good_flags") or []
    archetype = str(item.get("archetype") or "Mixed")
    classification = str(item.get("classification") or "No Signal")

    if triage == "Trade":
        return "Meets the model’s trade threshold with enough timing, liquidity and confirmation."
    if triage == "Watch":
        if "Discovery" in classification:
            return "Not a full Trade, but abnormal accumulation or catalyst digestion makes it worth monitoring."
        if risk_flags:
            return f"Watch only because risk controls remain active: {', '.join(risk_flags[:2])}."
        return "Setup is actionable enough to monitor after the Tokyo close, but not a full Trade."

    if risk_flags:
        return f"Blocked despite rank/score because risk controls triggered: {', '.join(risk_flags[:3])}."
    if score_pts >= BLOCKED_SCORE_FLOOR and good_flags:
        return f"Good setup quality is present, but no actionable trigger yet: {', '.join(good_flags[:2])}."
    if score_pts >= BLOCKED_SCORE_FLOOR:
        return "Score is respectable, but the signal did not clear the Watch/Trade confirmation rules."
    if "Relative Strength" in archetype:
        return "Relative strength exists, but the daily trigger is not strong enough yet."
    return "Below the model’s daily decision threshold."


def normalize_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = payload.get("items") or []
    all_items = payload.get("all_items") or []
    items = all_items if isinstance(all_items, list) and all_items else raw_items
    if not isinstance(items, list):
        return []

    out: list[dict[str, Any]] = []
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue

        normalized = dict(item)
        rank = int(as_float(item.get("rank")) or idx)
        normalized["rank"] = rank
        normalized["is_main_rank"] = rank <= MAIN_RANK_LIMIT
        normalized["is_reference_rank"] = MAIN_RANK_LIMIT < rank <= REFERENCE_LIMIT

        liquidity_band = infer_liquidity_band(item)
        normalized["liquidity_band"] = liquidity_band
        normalized["liquidity_class"] = css_class_for_liquidity(liquidity_band)

        score_pts = as_float(item.get("score_pts"))
        score = as_float(item.get("score"))
        normalized["score_display"] = int(round(score_pts)) if score_pts is not None else fmt_score(score)
        normalized["score_width"] = score_width(score_pts if score_pts is not None else score)
        normalized["score_class"] = css_class_for_score(score_pts if score_pts is not None else score)
        normalized["risk_class"] = css_class_for_risk(item.get("risk_level"))
        normalized["return_1d_class"] = css_class_for_return(item.get("return_1d_pct"))
        normalized["return_3d_class"] = css_class_for_return(item.get("return_3d_pct"))
        normalized["return_5d_class"] = css_class_for_return(item.get("return_5d_pct"))
        normalized["return_10d_class"] = css_class_for_return(item.get("return_10d_pct"))
        normalized["return_20d_class"] = css_class_for_return(item.get("return_20d_pct"))

        flags = item.get("flags") or []
        good_flags, risk_flags, neutral_flags = split_flags(flags)
        normalized["good_flags"] = good_flags
        normalized["risk_flags"] = risk_flags
        normalized["neutral_flags"] = neutral_flags
        normalized["has_good_flags"] = bool(good_flags)
        normalized["has_risk_flags"] = bool(risk_flags)

        components = item.get("v2_components") or item.get("components") or {}
        if not isinstance(components, dict):
            components = {}
        normalized["component_widths"] = {
            "volume": component_width(components.get("volume_liquidity_shock") or components.get("volume_shock")),
            "compression": component_width(components.get("compression_release") or components.get("compression")),
            "breakout": component_width(components.get("breakout_setup_quality") or components.get("breakout_quality")),
            "relative_strength": component_width(components.get("relative_strength")),
            "entry": component_width(components.get("entry_timing")),
        }

        normalized["short_reason"] = short_reason(item.get("reason"), 140)
        normalized["decision_label"] = decision_label(normalized)
        normalized["decision_reason"] = decision_reason(normalized)
        normalized["card_tone"] = (
            "action" if normalized.get("triage") in {"Trade", "Watch"}
            else "blocked" if risk_flags or (score_pts or 0) >= BLOCKED_SCORE_FLOOR
            else "neutral"
        )

        out.append(normalized)

    out.sort(key=lambda x: int(as_float(x.get("rank")) or 999999))
    return out


def market_tape_label(ret5: Any, ret20: Any, above_sma20: Any = None) -> str:
    r5 = as_float(ret5)
    r20 = as_float(ret20)
    if r5 is not None and r5 <= -3.0:
        return "Weak tape"
    if r5 is not None and r5 <= -1.0:
        return "Soft tape"
    if r5 is not None and r5 >= 2.0:
        return "Strong tape"
    if r20 is not None and r20 >= 5.0 and above_sma20:
        return "Trend intact"
    return "Mixed tape"


def broad_trend_label(ret20: Any, ret60: Any, above_sma50: Any = None) -> str:
    r20 = as_float(ret20)
    r60 = as_float(ret60)
    if above_sma50 and r20 is not None and r20 >= 3.0:
        return "Risk-On trend"
    if r20 is not None and r20 <= -5.0:
        return "Risk-Off trend"
    if r60 is not None and r60 >= 8.0:
        return "Constructive trend"
    return "Neutral trend"


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
        normalized["short_tape"] = market_tape_label(
            item.get("return_5d_pct"),
            item.get("return_20d_pct"),
            item.get("above_sma20"),
        )
        normalized["broad_trend"] = broad_trend_label(
            item.get("return_20d_pct"),
            item.get("return_60d_pct"),
            item.get("above_sma50"),
        )
        out.append(normalized)
    return out


def count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        label = str(item.get(key) or "Unknown")
        out[label] = out.get(label, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def build_quality_summary(main_items: list[dict[str, Any]], reference_items: list[dict[str, Any]]) -> dict[str, Any]:
    trade = [x for x in main_items if x.get("triage") == "Trade"]
    watch = [x for x in main_items if x.get("triage") == "Watch"]
    ignore = [x for x in main_items if x.get("triage") == "Ignore"]
    favored = [x for x in main_items if x.get("good_flags")]
    risk = [x for x in main_items if x.get("risk_flags")]
    blocked_high = [
        x for x in main_items
        if x.get("triage") == "Ignore" and (as_float(x.get("score_pts")) or 0) >= BLOCKED_SCORE_FLOOR
    ]

    if trade:
        verdict = "TRADE AVAILABLE"
        verdict_tone = "good"
        verdict_text = "At least one name cleared the full daily Trade threshold."
    elif watch:
        verdict = "WATCH ONLY"
        verdict_tone = "watch"
        verdict_text = "No full Trade today. Monitor Watch names and wait for confirmation."
    else:
        verdict = "NO ACTION"
        verdict_tone = "neutral"
        verdict_text = "The model found no actionable daily setup. Preserve capital."

    if risk and len(risk) >= max(4, len(main_items) // 2):
        verdict_text += " Risk controls are active across a large part of the board."

    return {
        "trade_count": len(trade),
        "watch_count": len(watch),
        "ignore_count": len(ignore),
        "favored_count": len(favored),
        "risk_count": len(risk),
        "blocked_high_count": len(blocked_high),
        "reference_count": len(reference_items),
        "verdict": verdict,
        "verdict_tone": verdict_tone,
        "verdict_text": verdict_text,
        "by_triage": count_by(main_items, "triage"),
        "by_liquidity": count_by(main_items, "liquidity_band"),
        "by_archetype": count_by(main_items, "archetype"),
    }


def build_bar_data(main_items: list[dict[str, Any]]) -> dict[str, Any]:
    triage_counts = count_by(main_items, "triage")
    total = max(1, len(main_items))
    triage_bars = []
    for label in ["Trade", "Watch", "Ignore"]:
        count = triage_counts.get(label, 0)
        triage_bars.append({"label": label, "count": count, "width": round(count / total * 100, 1)})

    score_bands = {
        "800+": 0,
        "700-799": 0,
        "600-699": 0,
        "500-599": 0,
        "<500": 0,
    }
    for item in main_items:
        pts = as_float(item.get("score_pts")) or 0
        if pts >= 800:
            score_bands["800+"] += 1
        elif pts >= 700:
            score_bands["700-799"] += 1
        elif pts >= 600:
            score_bands["600-699"] += 1
        elif pts >= 500:
            score_bands["500-599"] += 1
        else:
            score_bands["<500"] += 1

    score_bars = [
        {"label": label, "count": count, "width": round(count / total * 100, 1)}
        for label, count in score_bands.items()
    ]
    return {"triage_bars": triage_bars, "score_bars": score_bars}


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

    all_items = normalize_items(payload)
    main_items = [x for x in all_items if x.get("is_main_rank")][:MAIN_RANK_LIMIT]
    if not main_items:
        main_items = all_items[:MAIN_RANK_LIMIT]
    reference_items = [x for x in all_items if x.get("is_reference_rank")][: max(0, REFERENCE_LIMIT - MAIN_RANK_LIMIT)]

    actionable_items = [x for x in main_items if x.get("triage") in {"Trade", "Watch"}]
    trade_items = [x for x in main_items if x.get("triage") == "Trade"]
    watch_items = [x for x in main_items if x.get("triage") == "Watch"]
    highest_score_item = main_items[0] if main_items else None
    actionable_signal = trade_items[0] if trade_items else (watch_items[0] if watch_items else None)

    blocked_high_score_items = [
        x for x in main_items
        if x.get("triage") == "Ignore"
        and ((as_float(x.get("score_pts")) or 0) >= BLOCKED_SCORE_FLOOR or x.get("good_flags"))
    ][:8]
    favored_items = [x for x in main_items if x.get("good_flags")][:8]
    risk_items = [x for x in main_items if x.get("risk_flags")][:10]
    neutral_main_items = [x for x in main_items if x not in actionable_items and x not in blocked_high_score_items]

    market_pulse = normalize_market_pulse(payload)
    setup_quality = build_quality_summary(main_items, reference_items)
    bar_data = build_bar_data(main_items)

    rendered = template.render(
        payload=payload,
        all_items=all_items,
        main_items=main_items,
        reference_items=reference_items,
        actionable_items=actionable_items,
        trade_items=trade_items,
        watch_items=watch_items,
        blocked_high_score_items=blocked_high_score_items,
        favored_items=favored_items,
        risk_items=risk_items,
        neutral_main_items=neutral_main_items,
        actionable_signal=actionable_signal,
        highest_score_item=highest_score_item,
        market_pulse=market_pulse,
        setup_quality=setup_quality,
        bar_data=bar_data,
        summary=payload.get("summary") or {},
        generated_at=payload.get("generated_at"),
        source_prices_generated_at=payload.get("source_prices_generated_at"),
        main_rank_limit=MAIN_RANK_LIMIT,
        reference_limit=REFERENCE_LIMIT,
        blocked_score_floor=BLOCKED_SCORE_FLOOR,
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
    print(f"main_items={len(main_items)}")
    print(f"actionable_items={len(actionable_items)}")
    print(f"blocked_high_score_items={len(blocked_high_score_items)}")
    print(f"reference_items={len(reference_items)}")


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"DAILY_JSON={safe_relative(DAILY_JSON)}")
    render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
