#!/usr/bin/env python3
"""
Render /japan/daily/ as a decision-first Daily JP signal board.

Input:
- site/data/daily-jp/latest.json

Output:
- site/japan/daily/index.html
- site/assets/daily_jp.css

Design rules:
- Rank equals model score order. Highest Score must be rank #1 / max score.
- Trade is the only truly actionable label.
- Watch is rendered as Monitor Only, not as a buy signal.
- Top 20 is the main board; Rank 21-50 is a lightweight reference shelf.
- Internal model flags are translated, deduplicated, and grouped by severity.
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
OUT_DIR = (ROOT / OUT_DIR).resolve() if not OUT_DIR.is_absolute() else OUT_DIR.resolve()
DAILY_JSON = Path(os.getenv("DAILY_JSON", str(OUT_DIR / "data" / "daily-jp" / "latest.json")))
DAILY_JSON = (ROOT / DAILY_JSON).resolve() if not DAILY_JSON.is_absolute() else DAILY_JSON.resolve()
TEMPLATE_DIR = ROOT / "templates"
TEMPLATE_HTML = "daily_jp.html.j2"
TEMPLATE_CSS = TEMPLATE_DIR / "daily_jp.css"
OUTPUT_HTML = OUT_DIR / "japan" / "daily" / "index.html"
OUTPUT_CSS = OUT_DIR / "assets" / "daily_jp.css"
TZ = ZoneInfo("Asia/Tokyo")

MAIN_RANK_LIMIT = int(os.getenv("DAILY_MAIN_RANK_LIMIT", "20"))
REFERENCE_LIMIT = int(os.getenv("DAILY_REFERENCE_LIMIT", "50"))
BLOCKED_SCORE_FLOOR = int(os.getenv("DAILY_BLOCKED_SCORE_FLOOR", "500"))
BLOCKED_DISPLAY_LIMIT = int(os.getenv("DAILY_BLOCKED_DISPLAY_LIMIT", "5"))

STRICT_FAVORED_FLAGS = {
    "favored_relative_strength",
    "favored_compression_breakout",
    "favored_volume_compression",
    "abnormal_accumulation_high_confidence",
}
GOOD_SUPPORT_FLAGS = {
    "abnormal_accumulation",
    "post_catalyst_digestion",
    "compression_release",
    "breaks_20d_high",
    "breakout_20d",
    "breakout_50d",
    "above_key_mas",
    "upper_20d_range",
    "major_volume_shock",
    "large_traded_value",
    "liquid_enough",
}
HIGH_RISK_FLAGS = {
    "abnormal_distribution",
    "abnormal_distribution_high_confidence",
    "volume_noise",
    "volume_breakout_risk",
    "trade_block_volume_breakout",
    "weak_close_on_volume",
    "red_close_on_volume",
}
MEDIUM_RISK_FLAGS = {
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
    "partial_data",
}
FLAG_LABELS = {
    "favored_relative_strength": "Favored RS setup",
    "favored_compression_breakout": "Favored compression breakout",
    "favored_volume_compression": "Favored volume + compression",
    "abnormal_accumulation_high_confidence": "High-confidence accumulation",
    "abnormal_accumulation": "Abnormal accumulation",
    "post_catalyst_digestion": "Catalyst digestion",
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
    "discovery_watch_candidate": "Discovery monitor candidate",
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
    "rs_20d_positive": "20D RS positive",
    "rs_60d_leader": "60D RS leader",
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
        raise FileNotFoundError(f"Daily JSON not found: {safe_relative(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: Any) -> float | None:
    try:
        if value is None or (isinstance(value, str) and not value.strip()):
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


def unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            out.append(text)
    return out


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


def css_class_for_return(value: Any) -> str:
    v = as_float(value)
    if v is None:
        return "ret-flat"
    return "ret-up" if v > 0 else "ret-down" if v < 0 else "ret-flat"


def css_class_for_liquidity(value: Any) -> str:
    s = str(value or "Unknown").strip().lower().replace(" ", "-")
    return f"liq-{s}" if s in {"high-liquidity", "tradable", "thin", "event-thin", "very-thin", "unknown"} else "liq-unknown"


def css_class_for_signal_status(item: dict[str, Any]) -> str:
    return str(item.get("signal_status") or "blocked").lower().replace(" ", "-")


def flag_label(flag: str) -> str:
    raw = str(flag or "").strip()
    return FLAG_LABELS.get(raw, raw.replace("_", " ").strip().title())


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


def split_flags(flags: Any) -> dict[str, list[str]]:
    if not isinstance(flags, list):
        flags = []
    strict_good: list[str] = []
    support_good: list[str] = []
    high_risk: list[str] = []
    medium_risk: list[str] = []
    neutral: list[str] = []
    for flag in flags:
        f = str(flag or "").strip()
        if not f:
            continue
        label = flag_label(f)
        if f in STRICT_FAVORED_FLAGS:
            strict_good.append(label)
        elif f in GOOD_SUPPORT_FLAGS:
            support_good.append(label)
        elif f in HIGH_RISK_FLAGS:
            high_risk.append(label)
        elif f in MEDIUM_RISK_FLAGS:
            medium_risk.append(label)
        else:
            neutral.append(label)
    return {
        "strict_good": unique_keep_order(strict_good),
        "support_good": unique_keep_order(support_good),
        "high_risk": unique_keep_order(high_risk),
        "medium_risk": unique_keep_order(medium_risk),
        "neutral": unique_keep_order(neutral),
    }


def signal_status(item: dict[str, Any]) -> str:
    triage = str(item.get("triage") or "Ignore")
    if triage == "Trade":
        return "Trade"
    if triage == "Watch":
        return "Monitor Only"
    if item.get("high_risk_flags"):
        return "Blocked · High Risk"
    if item.get("medium_risk_flags"):
        return "Blocked · Needs Confirmation"
    if item.get("strict_good_flags") or item.get("support_good_flags"):
        return "Blocked · No Trigger"
    return "No Action"


def decision_label(item: dict[str, Any]) -> str:
    triage = str(item.get("triage") or "Ignore")
    classification = str(item.get("classification") or "No Signal")
    if triage == "Trade":
        return "Actionable Trade"
    if triage == "Watch":
        if "Discovery" in classification:
            return "Monitor Only · Discovery"
        if "Exhaustion" in classification:
            return "Monitor Only · Risky Tape"
        return "Monitor Only"
    if item.get("high_risk_flags"):
        return "Blocked by High-Severity Risk"
    if item.get("medium_risk_flags"):
        return "Blocked by Confirmation Rules"
    if item.get("strict_good_flags"):
        return "High Quality, Waiting for Trigger"
    if item.get("support_good_flags"):
        return "Constructive, But Not Actionable"
    return "No Action"


def decision_reason(item: dict[str, Any]) -> str:
    triage = str(item.get("triage") or "Ignore")
    score_pts = int(as_float(item.get("score_pts")) or 0)
    high_risk = item.get("high_risk_flags") or []
    medium_risk = item.get("medium_risk_flags") or []
    strict_good = item.get("strict_good_flags") or []
    support_good = item.get("support_good_flags") or []
    classification = str(item.get("classification") or "No Signal")

    if triage == "Trade":
        return "Full daily Trade threshold cleared with timing, liquidity and confirmation."
    if triage == "Watch":
        if "Discovery" in classification:
            return "Monitor only. Abnormal accumulation or catalyst digestion is present, but this is not a Trade signal."
        return "Monitor only. Wait for next-day price and volume confirmation before treating it as actionable."
    if high_risk:
        return f"Blocked by high-severity risk: {', '.join(high_risk[:2])}."
    if medium_risk:
        return f"Blocked until confirmation improves: {', '.join(medium_risk[:2])}."
    if score_pts >= BLOCKED_SCORE_FLOOR and strict_good:
        return f"Strong setup quality, but no actionable trigger yet: {', '.join(strict_good[:2])}."
    if score_pts >= BLOCKED_SCORE_FLOOR and support_good:
        return f"Constructive tape, but still below Monitor/Trade rules: {', '.join(support_good[:2])}."
    if score_pts >= BLOCKED_SCORE_FLOOR:
        return "Score is respectable, but the setup did not clear the daily decision rules."
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
        normalized["score_num"] = score_pts if score_pts is not None else (score if score is not None else 0)
        normalized["score_display"] = int(round(score_pts)) if score_pts is not None else fmt_score(score)
        normalized["score_width"] = score_width(score_pts if score_pts is not None else score)
        normalized["score_class"] = css_class_for_score(score_pts if score_pts is not None else score)
        for key in ["return_1d_pct", "return_3d_pct", "return_5d_pct", "return_10d_pct", "return_20d_pct"]:
            normalized[f"{key}_class"] = css_class_for_return(item.get(key))

        split = split_flags(item.get("flags") or [])
        normalized["strict_good_flags"] = split["strict_good"]
        normalized["support_good_flags"] = split["support_good"]
        normalized["good_flags"] = unique_keep_order(split["strict_good"] + split["support_good"])
        normalized["high_risk_flags"] = split["high_risk"]
        normalized["medium_risk_flags"] = split["medium_risk"]
        normalized["risk_flags"] = unique_keep_order(split["high_risk"] + split["medium_risk"])
        normalized["neutral_flags"] = split["neutral"]
        normalized["has_good_flags"] = bool(normalized["good_flags"])
        normalized["has_risk_flags"] = bool(normalized["risk_flags"])
        normalized["has_strict_favored"] = bool(normalized["strict_good_flags"])
        normalized["has_high_risk"] = bool(normalized["high_risk_flags"])

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
        normalized["signal_status"] = signal_status(normalized)
        normalized["signal_status_class"] = css_class_for_signal_status(normalized)
        normalized["decision_label"] = decision_label(normalized)
        normalized["decision_reason"] = decision_reason(normalized)
        normalized["signal_risk_label"] = "High" if normalized["high_risk_flags"] else "Medium" if normalized["medium_risk_flags"] else "Low"
        normalized["card_tone"] = "trade" if normalized.get("triage") == "Trade" else "monitor" if normalized.get("triage") == "Watch" else "blocked" if normalized.get("risk_flags") or normalized.get("score_num", 0) >= BLOCKED_SCORE_FLOOR else "neutral"
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
    out = []
    for item in pulse:
        if not isinstance(item, dict):
            continue
        normalized = dict(item)
        for key in ["return_1d_pct", "return_5d_pct", "return_20d_pct"]:
            normalized[f"{key}_class"] = css_class_for_return(item.get(key))
        normalized["short_tape"] = market_tape_label(item.get("return_5d_pct"), item.get("return_20d_pct"), item.get("above_sma20"))
        normalized["broad_trend"] = broad_trend_label(item.get("return_20d_pct"), item.get("return_60d_pct"), item.get("above_sma50"))
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
    monitor = [x for x in main_items if x.get("triage") == "Watch"]
    blocked = [x for x in main_items if x.get("triage") == "Ignore"]
    favored = [x for x in main_items if x.get("has_strict_favored")]
    high_risk = [x for x in main_items if x.get("high_risk_flags")]
    medium_risk = [x for x in main_items if x.get("medium_risk_flags")]
    blocked_high = [x for x in blocked if (as_float(x.get("score_pts")) or 0) >= BLOCKED_SCORE_FLOOR or x.get("has_strict_favored")]

    if trade:
        verdict = "TRADE AVAILABLE"
        verdict_tone = "good"
        verdict_text = "At least one name cleared the full daily Trade threshold."
    elif monitor:
        verdict = "MONITOR ONLY"
        verdict_tone = "monitor"
        verdict_text = f"No full Trade today. {len(monitor)} Monitor candidate{'s' if len(monitor) != 1 else ''}. Wait for next-day price/volume confirmation."
    else:
        verdict = "NO ACTION"
        verdict_tone = "neutral"
        verdict_text = "No Trade or Monitor candidate cleared the daily rules. Preserve capital."
    if high_risk and len(high_risk) >= max(4, len(main_items) // 2):
        verdict_text += " High-severity risk controls are active across the board."

    return {
        "trade_count": len(trade),
        "monitor_count": len(monitor),
        "ignore_count": len(blocked),
        "favored_count": len(favored),
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "risk_count": len(high_risk) + len(medium_risk),
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
    total = max(1, len(main_items))
    triage_counts = count_by(main_items, "triage")
    triage_map = [("Trade", "Trade"), ("Monitor", "Watch"), ("Blocked", "Ignore")]
    triage_bars = []
    for label, raw in triage_map:
        count = triage_counts.get(raw, 0)
        triage_bars.append({"label": label, "raw": raw, "count": count, "width": round(count / total * 100, 1)})
    score_bands = {"800+": 0, "700-799": 0, "600-699": 0, "500-599": 0, "<500": 0}
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
    return {
        "triage_bars": [{"label": k, "count": v, "width": round(v / total * 100, 1)} for k, v in [(b["label"], b["count"]) for b in triage_bars]],
        "score_bars": [{"label": k, "count": v, "width": round(v / total * 100, 1)} for k, v in score_bands.items()],
    }


def render() -> None:
    payload = read_json(DAILY_JSON)
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape(["html", "xml"]))
    env.filters["fmt_pct"] = fmt_pct
    env.filters["fmt_score"] = fmt_score
    env.filters["fmt_int"] = fmt_int
    env.filters["fmt_jpy"] = fmt_jpy
    template = env.get_template(TEMPLATE_HTML)

    all_items = normalize_items(payload)
    main_items = [x for x in all_items if x.get("is_main_rank")][:MAIN_RANK_LIMIT] or all_items[:MAIN_RANK_LIMIT]
    reference_items = [x for x in all_items if x.get("is_reference_rank")][: max(0, REFERENCE_LIMIT - MAIN_RANK_LIMIT)]
    trade_items = [x for x in main_items if x.get("triage") == "Trade"]
    monitor_items = [x for x in main_items if x.get("triage") == "Watch"]
    highest_score_item = max(main_items, key=lambda x: (as_float(x.get("score_pts")) or -1, -int(as_float(x.get("rank")) or 9999)), default=None)
    trade_signal = trade_items[0] if trade_items else None
    monitor_signal = monitor_items[0] if monitor_items else None
    primary_signal = trade_signal or monitor_signal

    blocked_high_score_items = [
        x for x in main_items
        if x.get("triage") == "Ignore" and ((as_float(x.get("score_pts")) or 0) >= BLOCKED_SCORE_FLOOR or x.get("has_strict_favored"))
    ][:BLOCKED_DISPLAY_LIMIT]
    favored_items = [x for x in main_items if x.get("has_strict_favored")][:6]
    high_risk_items = [x for x in main_items if x.get("high_risk_flags")][:8]
    medium_risk_items = [x for x in main_items if x.get("medium_risk_flags") and not x.get("high_risk_flags")][:8]

    setup_quality = build_quality_summary(main_items, reference_items)
    bar_data = build_bar_data(main_items)

    rendered = template.render(
        payload=payload,
        all_items=all_items,
        main_items=main_items,
        reference_items=reference_items,
        trade_items=trade_items,
        monitor_items=monitor_items,
        primary_signal=primary_signal,
        trade_signal=trade_signal,
        monitor_signal=monitor_signal,
        highest_score_item=highest_score_item,
        blocked_high_score_items=blocked_high_score_items,
        favored_items=favored_items,
        high_risk_items=high_risk_items,
        medium_risk_items=medium_risk_items,
        market_pulse=normalize_market_pulse(payload),
        setup_quality=setup_quality,
        bar_data=bar_data,
        summary=payload.get("summary") or {},
        generated_at=payload.get("generated_at"),
        source_prices_generated_at=payload.get("source_prices_generated_at"),
        main_rank_limit=MAIN_RANK_LIMIT,
        reference_limit=REFERENCE_LIMIT,
        blocked_score_floor=BLOCKED_SCORE_FLOOR,
        blocked_display_limit=BLOCKED_DISPLAY_LIMIT,
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
    print(f"main_items={len(main_items)}")
    print(f"trade_items={len(trade_items)}")
    print(f"monitor_items={len(monitor_items)}")
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
