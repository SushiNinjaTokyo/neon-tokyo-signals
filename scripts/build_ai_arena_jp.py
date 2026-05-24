from __future__ import annotations

"""
Build Neon Tokyo AI Arena data.

Design goals
------------
This script is intentionally independent from the existing Daily / Weekly /
Simulation builders. It consumes already-built JSON files and writes a new Arena
JSON. It does NOT modify price data, daily scores, backtests, or simulations.

Key rules
---------
1. Agent definitions live in data/ai_arena_agents_jp.yml.
2. Stock selection is deterministic Python logic.
3. Generative AI is only used for commentary / short feed lines.
4. If OpenAI is disabled, missing, over budget, or fails, fallback text is used.
5. The output schema is stable and defensive for templates/JS.

Expected inputs
---------------
- site/data/daily-jp/latest.json
- site/data/japan/weekly/latest.json      optional but preferred
- site/data/backtest-daily-jp/latest.json optional for result evaluation
- data/ai_arena_agents_jp.yml
- data/ai_arena_prompt_presets_jp.yml

Output
------
- site/data/japan/ai-arena/latest.json
"""

import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - handled in GitHub Actions by requirements-render.txt
    raise SystemExit("PyYAML is required. Add PyYAML>=6.0,<7 to requirements-render.txt") from exc

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()

DAILY_JSON = Path(os.getenv("DAILY_JSON", str(OUT_DIR / "data/daily-jp/latest.json")))
WEEKLY_JSON = Path(os.getenv("WEEKLY_JSON", str(OUT_DIR / "data/japan/weekly/latest.json")))
BACKTEST_JSON = Path(os.getenv("BACKTEST_JSON", str(OUT_DIR / "data/backtest-daily-jp/latest.json")))
AGENTS_YAML = Path(os.getenv("ARENA_AGENTS_YAML", str(ROOT / "data/ai_arena_agents_jp.yml")))
PRESETS_YAML = Path(os.getenv("ARENA_PROMPTS_YAML", str(ROOT / "data/ai_arena_prompt_presets_jp.yml")))
ARENA_OUT = Path(os.getenv("ARENA_OUT", str(OUT_DIR / "data/japan/ai-arena/latest.json")))

JST = timezone(timedelta(hours=9))
UTC = timezone.utc

# Token pricing is deliberately conservative and config-driven. The numbers are
# only used as a local guard before calling the API; actual billing is handled by
# OpenAI. Keep these in sync with your chosen model when you change models.
MODEL_PRICES_USD_PER_1M = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-5.5": {"input": 5.00, "output": 30.00},
}

BANNED_PHRASES_DEFAULT = [
    "strong buy",
    "target price",
    "guaranteed",
    "must own",
    "easy money",
    "can't lose",
    "cannot lose",
    "recommendation",
    "recommend",
]


def now_jst() -> datetime:
    return datetime.now(JST)


def iso_jst(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return dt.astimezone(JST).isoformat(timespec="seconds")


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        print(f"WARN missing JSON: {path}")
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WARN failed to read JSON {path}: {exc}")
        return fallback


def read_yaml(path: Path, fallback: Any) -> Any:
    if not path.exists():
        print(f"WARN missing YAML: {path}")
        return fallback
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or fallback
    except Exception as exc:
        raise SystemExit(f"Failed to parse YAML {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except Exception:
        return default


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def norm_pct(value: Any, lo: float = -10.0, hi: float = 15.0) -> float:
    """Map a percentage-style metric into 0..1 with clipping."""
    v = as_float(value, 0.0)
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (v - lo) / (hi - lo)))


def norm_positive(value: Any, cap: float) -> float:
    v = max(0.0, as_float(value, 0.0))
    return max(0.0, min(1.0, v / cap)) if cap > 0 else 0.0


def score_pts_norm(item: dict[str, Any]) -> float:
    # Daily score_pts appears to be 0..100 in current data, while backtest uses
    # 0..1000 in older snapshots. This guard supports both.
    pts = as_float(item.get("score_pts"), as_float(item.get("score"), 0.0))
    if pts > 150:
        return max(0.0, min(1.0, pts / 1000.0))
    return max(0.0, min(1.0, pts / 100.0))


def item_symbol(item: dict[str, Any]) -> str:
    return str(item.get("symbol") or "").strip()


def item_flags(item: dict[str, Any]) -> set[str]:
    flags = item.get("flags")
    if isinstance(flags, list):
        return {str(x).lower() for x in flags}
    return set()


def has_flag(item: dict[str, Any], needle: str) -> bool:
    n = needle.lower()
    return any(n in f for f in item_flags(item))


def unique_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for item in items:
        sym = item_symbol(item)
        if not sym or sym in seen:
            continue
        seen.add(sym)
        out.append(item)
    return out


def collect_daily_candidates(daily: dict[str, Any]) -> list[dict[str, Any]]:
    # Prefer all_items for breadth, but keep official items first so top-ranked
    # signals win ties. Defensive against missing all_items.
    raw: list[dict[str, Any]] = []
    for key in ("items", "all_items"):
        value = daily.get(key)
        if isinstance(value, list):
            raw.extend([x for x in value if isinstance(x, dict)])
    return unique_items(raw)


def weekly_by_symbol(weekly: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key in ("items", "all_items"):
        for item in weekly.get(key, []) or []:
            if isinstance(item, dict) and item_symbol(item):
                out.setdefault(item_symbol(item), item)
    return out


def theme_heat(daily_items: list[dict[str, Any]], weekly_items: list[dict[str, Any]]) -> dict[str, float]:
    """Compute a simple 0..1 theme heat score from current Daily + Weekly data."""
    buckets: dict[str, list[float]] = defaultdict(list)

    for item in daily_items:
        theme = str(item.get("theme") or "Other")
        base = score_pts_norm(item)
        ret = norm_pct(item.get("return_5d_pct"), -8, 12)
        vol = norm_positive(item.get("volume_ratio_20d"), 4)
        buckets[theme].append(0.55 * base + 0.25 * ret + 0.20 * vol)

    for item in weekly_items:
        theme = str(item.get("theme") or "Other")
        pts = as_float(item.get("score_pts"), 0.0)
        base = min(1.0, pts / 1000.0) if pts > 100 else min(1.0, pts / 100.0)
        buckets[theme].append(0.85 * base)

    raw = {theme: (sum(vals) / len(vals) + min(0.25, len(vals) * 0.035)) for theme, vals in buckets.items() if vals}
    maxv = max(raw.values(), default=1.0)
    return {theme: max(0.0, min(1.0, val / maxv)) for theme, val in raw.items()}


def liquidity_score(item: dict[str, Any]) -> float:
    direct = item.get("liquidity_score_0_1")
    if direct is not None:
        return max(0.0, min(1.0, as_float(direct, 0.0)))
    traded = as_float(item.get("avg_traded_value_20d_jpy"), 0.0)
    # 0 at 0, roughly 1 at 20bn JPY/day. This is a UI/game score, not a trading rule.
    return min(1.0, math.log10(max(1.0, traded)) / math.log10(20_000_000_000))


def extension_risk(item: dict[str, Any]) -> float:
    ext20 = abs(as_float(item.get("extension_sma20_pct"), 0.0))
    dist_high = abs(as_float(item.get("distance_from_52w_high_pct"), 0.0))
    ret5 = max(0.0, as_float(item.get("return_5d_pct"), 0.0))
    return max(0.0, min(1.0, 0.45 * norm_positive(ext20, 18) + 0.25 * norm_positive(ret5, 18) + 0.30 * (1.0 - norm_positive(dist_high, 35))))


def noise_penalty(item: dict[str, Any]) -> float:
    flags = item_flags(item)
    penalty = 0.0
    if any("abnormal_distribution" in f for f in flags):
        penalty += 0.45
    if any("volume_noise" in f for f in flags):
        penalty += 0.35
    if any("illiquid" in f or "low_liquidity" in f for f in flags):
        penalty += 0.20
    if "Avoid" in str(item.get("signal") or item.get("triage") or ""):
        penalty += 0.20
    return min(0.8, penalty)


def discovery_score(item: dict[str, Any]) -> float:
    text = " ".join(str(item.get(k) or "") for k in ["bucket", "theme", "archetype", "classification", "reason"]).lower()
    flags = " ".join(item_flags(item))
    score = 0.0
    for kw, pts in [
        ("discovery", 0.45),
        ("small", 0.20),
        ("emerging", 0.20),
        ("ai", 0.12),
        ("robot", 0.12),
        ("space", 0.10),
        ("semiconductor", 0.08),
    ]:
        if kw in text or kw in flags:
            score += pts
    # Core mega-caps should not dominate Discovery Scout unless the data says
    # discovery explicitly.
    if str(item.get("bucket") or "").lower() == "core" and "discovery" not in text:
        score -= 0.20
    return max(0.0, min(1.0, score))


def weekly_strength(item: dict[str, Any], weekly_map: dict[str, dict[str, Any]]) -> float:
    w = weekly_map.get(item_symbol(item), {})
    if not w:
        return 0.35 * score_pts_norm(item)
    pts = as_float(w.get("score_pts"), 0.0)
    base = min(1.0, pts / 1000.0) if pts > 100 else min(1.0, pts / 100.0)
    signal = str(w.get("signal") or "").lower()
    quality = str(w.get("quality") or w.get("classification") or "").lower()
    boost = 0.08 if "trade" in signal or "leader" in quality or "constructive" in quality else 0.0
    return max(0.0, min(1.0, base + boost))


@dataclass
class ArenaContext:
    daily: dict[str, Any]
    weekly: dict[str, Any]
    backtest: dict[str, Any]
    daily_items: list[dict[str, Any]]
    weekly_items: list[dict[str, Any]]
    weekly_map: dict[str, dict[str, Any]]
    theme_scores: dict[str, float]


def profile_score(profile: str, item: dict[str, Any], ctx: ArenaContext) -> float:
    """Score one candidate for a selection profile. Returns 0..1-ish."""
    base = score_pts_norm(item)
    ret1 = norm_pct(item.get("return_1d_pct"), -6, 8)
    ret3 = norm_pct(item.get("return_3d_pct"), -8, 12)
    ret5 = norm_pct(item.get("return_5d_pct"), -10, 16)
    ret20 = norm_pct(item.get("return_20d_pct"), -15, 30)
    vol = norm_positive(item.get("volume_ratio_20d"), 4.0)
    liq = liquidity_score(item)
    ext_risk = extension_risk(item)
    low_ext = 1.0 - ext_risk
    theme = str(item.get("theme") or "Other")
    th = ctx.theme_scores.get(theme, 0.0)
    wk = weekly_strength(item, ctx.weekly_map)
    disc = discovery_score(item)
    penalty = noise_penalty(item)

    if profile == "momentum":
        score = 0.30 * base + 0.22 * ret5 + 0.20 * vol + 0.13 * ret20 + 0.10 * liq + 0.05 * th - 0.35 * penalty
    elif profile == "theme":
        score = 0.25 * base + 0.35 * th + 0.20 * wk + 0.10 * vol + 0.10 * ret5 - 0.25 * penalty
    elif profile == "risk_control":
        stability = 0.55 * low_ext + 0.45 * norm_pct(item.get("return_20d_pct"), -8, 18)
        score = 0.30 * liq + 0.25 * base + 0.22 * stability + 0.13 * wk + 0.10 * th - 0.55 * penalty
    elif profile == "discovery":
        score = 0.30 * disc + 0.20 * base + 0.18 * vol + 0.14 * th + 0.10 * ret5 + 0.08 * low_ext - 0.30 * max(0.0, 0.45 - liq) - 0.25 * penalty
    elif profile == "contrarian":
        # Looks for weekly/theme support with less short-term heat.
        short_cool = 1.0 - max(ret1, ret3 * 0.85, ext_risk)
        recovery = max(0.0, min(1.0, 0.55 * wk + 0.25 * th + 0.20 * base))
        score = 0.30 * recovery + 0.22 * short_cool + 0.18 * liq + 0.15 * low_ext + 0.15 * ret20 - 0.35 * penalty
    else:
        score = 0.60 * base + 0.20 * ret5 + 0.20 * liq - 0.30 * penalty
    return max(0.0, min(1.0, score))


def pick_for_agent(agent: dict[str, Any], ctx: ArenaContext, used_symbols: set[str], unique: bool) -> dict[str, Any] | None:
    profile = str(agent.get("selection_profile") or "momentum")
    candidates = []
    for item in ctx.daily_items:
        sym = item_symbol(item)
        if not sym:
            continue
        # Keep Avoid out of most agent picks unless it is the only data available.
        triage_signal = str(item.get("triage") or item.get("signal") or "").lower()
        avoidish = "avoid" in triage_signal or "blocked" in triage_signal
        raw_score = profile_score(profile, item, ctx)
        if avoidish:
            raw_score *= 0.70
        if unique and sym in used_symbols:
            raw_score *= 0.75
        candidates.append((raw_score, item))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    chosen = candidates[0][1]
    if unique:
        for _, item in candidates:
            if item_symbol(item) not in used_symbols:
                chosen = item
                break
    used_symbols.add(item_symbol(chosen))
    return chosen


def build_pick_payload(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not item:
        return None
    keys = [
        "symbol", "name", "theme", "bucket", "priority", "rank", "triage", "classification", "archetype",
        "risk_level", "latest_date", "as_of", "price", "score_pts", "return_1d_pct", "return_3d_pct",
        "return_5d_pct", "return_20d_pct", "volume_ratio_20d", "liquidity_band", "liquidity_score_0_1",
        "extension_sma20_pct", "distance_from_52w_high_pct", "reason",
    ]
    payload = {k: item.get(k) for k in keys if k in item}
    payload["symbol"] = item_symbol(item)
    payload["score_norm_0_1"] = round(score_pts_norm(item), 4)
    payload["liquidity_score_0_1"] = round(liquidity_score(item), 4)
    payload["extension_risk_0_1"] = round(extension_risk(item), 4)
    payload["noise_penalty_0_1"] = round(noise_penalty(item), 4)
    return payload


def build_stats(item: dict[str, Any] | None, ctx: ArenaContext) -> dict[str, int]:
    if not item:
        return {"signal_power": 0, "theme_heat": 0, "risk_guard": 0, "liquidity": 0}
    theme = str(item.get("theme") or "Other")
    return {
        "signal_power": int(round(clamp(score_pts_norm(item) * 100))),
        "theme_heat": int(round(clamp(ctx.theme_scores.get(theme, 0.0) * 100))),
        "risk_guard": int(round(clamp((1.0 - extension_risk(item) - noise_penalty(item) * 0.45) * 100))),
        "liquidity": int(round(clamp(liquidity_score(item) * 100))),
    }


def top_theme_summary(ctx: ArenaContext, limit: int = 6) -> list[dict[str, Any]]:
    counter = Counter(str(x.get("theme") or "Other") for x in ctx.daily_items)
    out = []
    for theme, score in sorted(ctx.theme_scores.items(), key=lambda x: x[1], reverse=True)[:limit]:
        out.append({"theme": theme, "heat_score": round(score * 100, 1), "signal_count": counter.get(theme, 0)})
    return out


def top_symbols_summary(ctx: ArenaContext, limit: int = 10) -> list[dict[str, Any]]:
    """Compact current-symbol context for AI conversation.

    The Arena should feel topical, but we avoid web/news dependencies in V1.
    This summary gives the model enough concrete material to discuss the current
    Japan signal board without inventing external facts.
    """
    rows: list[dict[str, Any]] = []
    for item in ctx.daily_items[: max(limit * 3, limit)]:
        sym = item_symbol(item)
        if not sym:
            continue
        rows.append({
            "symbol": sym,
            "name": item.get("name"),
            "theme": item.get("theme"),
            "score_pts": item.get("score_pts"),
            "return_1d_pct": item.get("return_1d_pct"),
            "return_5d_pct": item.get("return_5d_pct"),
            "return_20d_pct": item.get("return_20d_pct"),
            "volume_ratio_20d": item.get("volume_ratio_20d"),
            "triage": item.get("triage") or item.get("signal"),
            "bucket": item.get("bucket"),
        })
    rows.sort(key=lambda x: as_float(x.get("score_pts"), 0.0), reverse=True)
    return rows[:limit]


def compact_regime_label(regime: Any) -> str:
    """Convert evolving Daily regime payloads into a short human-readable label.

    Daily JSON sometimes stores regime as a nested dict with TOPIX/NIKKEI/Growth
    internals. Passing that raw dict into the LLM caused ugly UI leakage such as
    ``Regime: {'regime': 'Neutral', ...}``. The Arena prompt should only receive
    concise, presentation-safe context.
    """
    if isinstance(regime, str):
        return regime.strip() or "Unknown"
    if isinstance(regime, dict):
        label = regime.get("label") or regime.get("state") or regime.get("regime") or regime.get("market_regime")
        score = regime.get("regime_score") or regime.get("score")
        if label and score is not None:
            return f"{str(label).strip()} ({as_float(score):.2f})"
        if label:
            return str(label).strip()
        # Last-resort summary: count positive index trends instead of dumping raw JSON.
        positives = []
        for key in ("topix", "nikkei", "growth"):
            value = regime.get(key)
            if isinstance(value, dict):
                ret20 = value.get("ret20")
                above20 = value.get("above_sma20")
                label2 = value.get("label") or key.upper()
                if ret20 is not None:
                    positives.append(f"{label2} 20D {as_float(ret20):+.1f}%")
                elif above20 is not None:
                    positives.append(f"{label2} {'above' if above20 else 'below'} SMA20")
        return "; ".join(positives[:3]) if positives else "Mixed regime"
    return "Unknown"


def strip_raw_json_leak(text: Any) -> str:
    """Sanitize AI/fallback prose so raw Python/JSON blobs never hit the UI."""
    s = sanitize_text(text)
    # Raw context leakage usually contains Python dict markers or JSON braces with
    # market internals. If found, replace the sentence with a clean generic line.
    if re.search(r"\{[\'\"]|[\'\"]regime_score[\'\"]|[\'\"]topix[\'\"]|[\'\"]above_sma20[\'\"]", s, flags=re.IGNORECASE):
        return "Tokyo signals are mixed, with leadership concentrated in the strongest current themes."
    return s


def notable_move_lines(ctx: ArenaContext, top_symbols: list[dict[str, Any]], limit: int = 8) -> list[str]:
    """Generate concise, data-grounded topic lines for the AI prompt/fallback."""
    lines: list[str] = []
    for row in top_symbols[:limit]:
        sym = row.get("symbol") or "Unknown"
        name = row.get("name") or sym
        theme = row.get("theme") or "Japan signal"
        ret5 = row.get("return_5d_pct")
        vol = row.get("volume_ratio_20d")
        score = row.get("score_pts")
        pieces = [f"{sym} {name} appears in {theme}"]
        if ret5 is not None:
            pieces.append(f"5D {as_float(ret5):.2f}%")
        if vol is not None:
            pieces.append(f"RVOL {as_float(vol):.2f}x")
        if score is not None:
            pieces.append(f"score {as_float(score):.1f}")
        lines.append("; ".join(pieces))
    return lines


def build_market_context(ctx: ArenaContext, top_themes: list[dict[str, Any]], agents: list[dict[str, Any]], generated: datetime) -> dict[str, Any]:
    """Build the shared context all Agents are reacting to.

    V1 deliberately avoids external news calls. The 'latest topics' are derived
    from the most recent Daily/Weekly signal data and current Agent picks. This
    keeps the Arena grounded and cheap. Later, real news headlines can be added
    here without touching templates or the Agent YAML structure.
    """
    top_symbols = top_symbols_summary(ctx)
    picks = []
    for agent in agents:
        pick = agent.get("pick") or {}
        if pick:
            picks.append({
                "agent_id": agent.get("agent_id"),
                "agent_name": agent.get("name"),
                "symbol": pick.get("symbol"),
                "name": pick.get("name"),
                "theme": pick.get("theme"),
                "score_pts": pick.get("score_pts"),
                "return_5d_pct": pick.get("return_5d_pct"),
                "volume_ratio_20d": pick.get("volume_ratio_20d"),
                "liquidity_score_0_1": pick.get("liquidity_score_0_1"),
                "extension_risk_0_1": pick.get("extension_risk_0_1"),
            })
    regime = compact_regime_label(ctx.daily.get("regime_state") or ctx.daily.get("regime") or "unknown")
    risk_context = [
        "Do not treat a hot candle as a full thesis.",
        "Smaller discovery names require explicit liquidity caution.",
        "If TOPIX alpha quality is invalid, raw return should not be over-interpreted.",
    ]
    if top_themes:
        risk_context.append(f"Theme concentration is highest around {top_themes[0].get('theme')}.")
    return {
        "arena_date": extract_latest_daily_date(ctx.daily, ctx.daily_items, generated),
        "generated_at": iso_jst(generated),
        "daily_generated_at": ctx.daily.get("generated_at"),
        "weekly_generated_at": ctx.weekly.get("generated_at"),
        "market_regime": regime,
        "top_themes": top_themes,
        "top_symbols": top_symbols,
        "agent_picks": picks,
        "notable_moves": notable_move_lines(ctx, top_symbols),
        "news_context": [
            "No external news feed is used in this V1 run; topics are inferred from latest signal data.",
            "Use only provided signal context. Do not invent macro headlines or company news.",
        ],
        "risk_context": risk_context,
    }



def extract_latest_daily_date(daily: dict[str, Any], daily_items: list[dict[str, Any]], generated: datetime) -> str:
    """Return the clearest Arena date from Daily JSON.

    Daily JSON has evolved over time, so this helper checks summary/date level
    fields first, then item-level latest_date/as_of values, and finally falls
    back to the current JST date. Keeping this logic centralized prevents the
    UI and AI prompt from accidentally showing stale or ambiguous dates.
    """
    candidates: list[str] = []
    summary = daily.get("summary") if isinstance(daily.get("summary"), dict) else {}
    for value in [
        summary.get("date"),
        daily.get("date"),
        daily.get("latest_trading_date"),
        daily.get("as_of"),
    ]:
        if value:
            candidates.append(str(value)[:10])
    for item in daily_items:
        for key in ("latest_date", "as_of", "eval_date", "date"):
            value = item.get(key)
            if value:
                candidates.append(str(value)[:10])
    # ISO YYYY-MM-DD sorts lexicographically; ignore non-date-looking values.
    valid = [x for x in candidates if re.match(r"^\d{4}-\d{2}-\d{2}$", x)]
    return max(valid) if valid else generated.date().isoformat()


def days_between(date_text: Any, reference: datetime | None = None) -> int | None:
    """Return age in days for ISO date strings, or None when unavailable."""
    if not date_text:
        return None
    try:
        d = datetime.fromisoformat(str(date_text)[:10]).date()
        ref = (reference or now_jst()).astimezone(JST).date()
        return (ref - d).days
    except Exception:
        return None

def find_latest_mature_results(backtest: dict[str, Any], symbols: set[str], horizon: str = "1d") -> dict[str, dict[str, Any]]:
    """Return latest valid backtest result per symbol for the requested horizon.

    This is intentionally used only for Arena game results. It does not change
    Daily Backtest or Simulation logic.
    """
    items = [x for x in backtest.get("items", []) if isinstance(x, dict)]
    by_symbol: dict[str, dict[str, Any]] = {}
    for item in items:
        sym = item_symbol(item)
        if sym not in symbols:
            continue
        future = item.get("future_returns_pct") or {}
        if horizon not in future or future.get(horizon) is None:
            continue
        alpha_quality = item.get("alpha_quality") or {}
        q = alpha_quality.get(horizon) if isinstance(alpha_quality, dict) else None
        alpha = (item.get("alpha_vs_topix_pct") or {}).get(horizon) if isinstance(item.get("alpha_vs_topix_pct"), dict) else None
        eval_date = str(item.get("eval_date") or "")
        prev = by_symbol.get(sym)
        if prev is None or eval_date > str(prev.get("eval_date") or ""):
            by_symbol[sym] = {
                # In Daily Backtest, eval_date is the signal/evaluation start date.
                # The exact future close date is not stored in current schema, so
                # the UI labels this as Signal Date and explains the horizon.
                "eval_date": eval_date,
                "signal_date": eval_date,
                "date_age_days": days_between(eval_date),
                "symbol": sym,
                "name": item.get("name"),
                "theme": item.get("theme"),
                "rank": item.get("rank"),
                "return_pct": future.get(horizon),
                "alpha_vs_topix_pct": alpha,
                "alpha_quality": q,
            }
    return by_symbol


def build_result_payload(agents: list[dict[str, Any]], backtest: dict[str, Any], horizon: str) -> dict[str, Any]:
    symbols = {a.get("pick", {}).get("symbol") for a in agents if isinstance(a.get("pick"), dict)}
    symbols = {str(s) for s in symbols if s}
    if not symbols or not backtest:
        return {"status": "pending", "evaluation_horizon": horizon, "winner_agent_id": None, "reason": "No backtest results available."}

    results_by_symbol = find_latest_mature_results(backtest, symbols, horizon)
    agent_results = []
    for agent in agents:
        pick = agent.get("pick") or {}
        sym = pick.get("symbol")
        res = results_by_symbol.get(sym)
        status = "mature" if res else "pending"
        agent_result = {
            "agent_id": agent.get("agent_id"),
            "symbol": sym,
            "status": status,
            "evaluation_horizon": horizon,
        }
        if res:
            agent_result.update(res)
        agent["result"] = agent_result
        agent_results.append(agent_result)

    mature = [r for r in agent_results if r.get("status") == "mature"]
    if not mature:
        return {"status": "pending", "evaluation_horizon": horizon, "winner_agent_id": None, "agent_results": agent_results}

    def rank_key(r: dict[str, Any]) -> tuple[float, float]:
        alpha = r.get("alpha_vs_topix_pct")
        ret = r.get("return_pct")
        # If alpha is invalid/null, use raw return as fallback but rank below valid alpha.
        return (as_float(alpha, -999.0), as_float(ret, -999.0))

    winner = max(mature, key=rank_key)
    return {
        "status": "mature",
        "evaluation_horizon": horizon,
        "winner_agent_id": winner.get("agent_id"),
        "winner_symbol": winner.get("symbol"),
        "winner_return_pct": winner.get("return_pct"),
        "winner_alpha_vs_topix_pct": winner.get("alpha_vs_topix_pct"),
        "winner_eval_date": winner.get("eval_date"),
        "winner_signal_date": winner.get("signal_date") or winner.get("eval_date"),
        "winner_date_age_days": winner.get("date_age_days"),
        "result_label": "Latest resolved battle",
        "agent_results": agent_results,
    }


def fallback_daily_brief(ctx: ArenaContext, top_themes: list[dict[str, Any]]) -> dict[str, str]:
    regime = compact_regime_label(ctx.daily.get("regime_state") or ctx.daily.get("regime") or "Unknown regime")
    theme = top_themes[0]["theme"] if top_themes else "No dominant theme"
    return {
        "analyst_id": "grand_market_analyst",
        "title": f"Tokyo signal field: {theme}",
        "body": f"The current Arena is built from the latest Japan signal board. Regime: {regime}. Theme leadership is concentrated around {theme}.",
        "risk_note": "Signal quality matters more than raw heat. This is a signal-selection game, not investment advice.",
    }


def fallback_agent_comment(agent: dict[str, Any], pick: dict[str, Any] | None) -> str:
    name = agent.get("name", "Agent")
    sym = (pick or {}).get("symbol", "the board")
    theme = (pick or {}).get("theme", "Japan signals")
    profile = agent.get("selection_profile", "signal")
    templates = {
        "momentum": f"{name} tracks acceleration in {sym}. Strength, volume, and relative pressure are the setup.",
        "theme": f"{name} frames {sym} through {theme}. Narrative strength is the edge to watch.",
        "risk_control": f"{name} chooses discipline over heat. {sym} must prove it can survive volatility.",
        "discovery": f"{name} scouts {sym} as an under-watched signal. Liquidity risk stays on the screen.",
        "contrarian": f"{name} avoids the hottest candle. {sym} is judged by setup quality and controlled extension.",
    }
    return templates.get(profile, f"{name} enters the Arena with {sym}.")


def fallback_battle_line(agent: dict[str, Any], pick: dict[str, Any] | None) -> str:
    return f"{agent.get('name', 'Agent')} enters the Arena: {(pick or {}).get('symbol', 'No pick')}"


def fallback_feed(agents: list[dict[str, Any]], start: datetime, interval_minutes: int, max_posts: int, market_context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Generate a dense, threaded party-chat feed without AI.

    This function is also used as a quality fallback when the model returns
    repetitive one-liners. The goal is not to create perfect market prose; it is
    to guarantee that the Arena never looks like a status ticker. Every line is
    written as a reply, challenge, agreement, or counterpoint in a short RPG
    party-chat style.
    """
    lines: list[dict[str, Any]] = []
    if not agents:
        return lines

    market_context = market_context or {}
    top_theme = "Japan signals"
    if market_context.get("top_themes"):
        top_theme = str(market_context["top_themes"][0].get("theme") or top_theme)
    top_symbols = market_context.get("top_symbols") or []
    notable = market_context.get("notable_moves") or []
    risk_context = market_context.get("risk_context") or []

    by_profile = {str(a.get("selection_profile")): a for a in agents}

    def pick_agent(profile: str, fallback_index: int) -> dict[str, Any]:
        return by_profile.get(profile) or agents[fallback_index % len(agents)]

    mh = pick_agent("momentum", 0)
    tr = pick_agent("theme", 1)
    rs = pick_agent("risk_control", 2)
    ds = pick_agent("discovery", 3)
    cq = pick_agent("contrarian", 4)

    def sym(agent: dict[str, Any]) -> str:
        return str((agent.get("pick") or {}).get("symbol") or "the board")

    def name(agent: dict[str, Any]) -> str:
        return str((agent.get("pick") or {}).get("name") or sym(agent))

    def theme(agent: dict[str, Any]) -> str:
        return str((agent.get("pick") or {}).get("theme") or top_theme)

    def ret5(agent: dict[str, Any]) -> str:
        value = (agent.get("pick") or {}).get("return_5d_pct")
        return f"{as_float(value):+.1f}% over 5D" if value is not None else "fresh pressure"

    risk_line = str(risk_context[0]) if risk_context else "Breadth is selective, so signal quality matters more than heat."
    board_symbol = str(top_symbols[0].get("symbol") if top_symbols and isinstance(top_symbols[0], dict) else sym(mh))
    board_theme = str(top_symbols[0].get("theme") if top_symbols and isinstance(top_symbols[0], dict) else top_theme)
    notable_line = str(notable[0]) if notable else f"{board_symbol} is one of the clearest current pressure points."

    # Each tuple is (speaker, body, type). The sequence is intentionally ordered
    # so later lines respond to earlier lines. Avoid exact repetition even when
    # max_posts is large by using a long bank before any template reuse.
    scripted: list[tuple[dict[str, Any], str, str]] = [
        (mh, f"I will start with the tape: {sym(mh)} is showing pressure, and {ret5(mh)} keeps it on my screen.", "conversation"),
        (rs, f"Pressure is only step one. I want to know whether {sym(mh)} can hold when liquidity thins.", "warning"),
        (tr, f"Both of you are too ticker-first. The larger question is whether {top_theme} is the story global capital can parse.", "theme"),
        (ds, f"That story may not live only in the obvious names. Japan's edge often hides below the first screen.", "discovery"),
        (cq, f"When the room agrees too quickly, I slow down. Crowded conviction is not the same as edge.", "counterpoint"),
        (mh, f"Crowded or not, strength pays the entry fee. {name(mh)} did not get here by being quiet.", "challenge"),
        (rs, f"And yet a clean signal should survive more than one loud candle. {risk_line}", "warning"),
        (tr, f"The exportable narrative still matters. {theme(tr)} gives foreign investors a reason to keep watching.", "theme"),
        (ds, f"I agree on narrative, but I want the name global screens still miss, not the headline everyone already owns.", "discovery"),
        (cq, f"Exactly. The best setup may be the one improving while attention is trapped somewhere louder.", "counterpoint"),
        (mh, f"Then test the board, not the opinion. {sym(mh)} has acceleration; that is my evidence.", "conversation"),
        (rs, f"My evidence is different: liquidity, drawdown behavior, and whether the move avoids turning into volume noise.", "warning"),
        (tr, f"Today feels like a narrative filter. Price action without a global story may not travel far.", "theme"),
        (ds, f"But a small discovery signal with real volume can travel fast once the story becomes legible.", "discovery"),
        (cq, f"I am watching for the opposite: the signal that improves after the crowd stops cheering.", "counterpoint"),
        (mh, f"{notable_line} That is enough for me to keep pressing the momentum case.", "conversation"),
        (rs, f"Pressing is fine. Chasing is not. I want tomorrow's tape to confirm today's excitement.", "warning"),
        (tr, f"If {top_theme} remains the leadership cluster, the Agent who reads the theme cleanly has the advantage.", "theme"),
        (ds, f"Leadership clusters create shadows. I want to search the shadows for the next signal.", "discovery"),
        (cq, f"Search the shadows, yes. But never pay full price for a story that already became obvious.", "counterpoint"),
        (mh, f"You can wait for quiet. I will follow the pressure while it is still visible.", "challenge"),
        (rs, f"And I will ask whether that pressure is durable enough to deserve trust.", "warning"),
        (tr, f"Durability plus narrative is the combination. Japan needs signals foreign capital can explain in one sentence.", "theme"),
        (ds, f"Then my question is simple: which current signal is still under-owned by that foreign capital?", "discovery"),
        (cq, f"My question is colder: which signal has the least regret priced into it?", "counterpoint"),
    ]

    # If a user asks for more feed lines than the scripted bank, continue with
    # varied response templates rather than repeating the same five sentences.
    continuation = [
        (mh, lambda: f"I am not asking for a perfect story. I am asking whether {sym(mh)} still has force behind the move.", "conversation"),
        (rs, lambda: f"Force without control is just volatility. My vote stays with survivability.", "warning"),
        (tr, lambda: f"The strongest Japan signals today need two engines: price action and a theme that travels overseas.", "theme"),
        (ds, lambda: f"The discovery edge appears before the global label becomes obvious. That is where I want to look.", "discovery"),
        (cq, lambda: f"I prefer the setup that gets stronger while the crowd argues about yesterday's winner.", "counterpoint"),
        (mh, lambda: f"If volume keeps confirming, I do not need consensus. I need momentum to stay honest.", "conversation"),
        (rs, lambda: f"Honest momentum leaves footprints. Noisy momentum leaves traps.", "warning"),
        (tr, lambda: f"This Arena is not only about which ticker jumps. It is about which Japan story becomes investable to outsiders.", "theme"),
        (ds, lambda: f"Outsiders usually arrive late. I am trying to meet the signal before it gets translated.", "discovery"),
        (cq, lambda: f"And I am trying to meet it after the first wave gets tired.", "counterpoint"),
    ]

    scheduled: list[tuple[dict[str, Any], str, str]] = scripted[:]
    j = 0
    while len(scheduled) < max_posts:
        agent, fn, kind = continuation[j % len(continuation)]
        scheduled.append((agent, fn(), kind))
        j += 1

    for i, (agent, body, kind) in enumerate(scheduled[:max_posts]):
        pick = agent.get("pick") or {}
        lines.append({
            "id": f"feed_{i+1:03d}",
            "show_at": iso_jst(start + timedelta(minutes=i * interval_minutes)),
            "agent_id": agent.get("agent_id"),
            "agent_name": agent.get("name"),
            "type": kind,
            "body": sanitize_text(body),
            "linked_symbol": pick.get("symbol"),
            "linked_theme": pick.get("theme"),
        })
    return lines


def normalized_feed_body(text: Any) -> str:
    """Normalize a feed body for repetition checks."""
    s = sanitize_text(text).lower()
    s = re.sub(r"[^a-z0-9.%]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def feed_needs_quality_fallback(feed: list[dict[str, Any]], agents: list[dict[str, Any]]) -> bool:
    """Detect model output that looks like repeated status lines, not dialogue.

    The Arena should feel like a party chat. If the model produces a small set of
    repeated slogans, or if too many bodies are generic and non-reactive, replace
    the feed with the deterministic threaded fallback. This is stricter than a
    normal AI text acceptance check because the UI quality depends on dialogue.
    """
    if len(feed) < max(12, len(agents) * 2):
        return True

    bodies = [normalized_feed_body(x.get("body")) for x in feed if normalized_feed_body(x.get("body"))]
    if not bodies:
        return True
    unique_ratio = len(set(bodies)) / max(1, len(bodies))
    if unique_ratio < 0.72:
        return True

    # Exact repetition in a chat feed is visually obvious and should never ship.
    counts = Counter(bodies)
    if counts and max(counts.values()) >= 3:
        return True

    generic_patterns = [
        r"watch for signs",
        r"focus on .*trends",
        r"monitoring .*movements",
        r"best japan signal today needs both price action",
        r"obvious mega cap answer is not always",
        r"i like the setup that improves while attention is elsewhere",
    ]
    generic_hits = sum(1 for body in bodies if any(re.search(p, body) for p in generic_patterns))
    if generic_hits / max(1, len(bodies)) > 0.25:
        return True

    # A conversational feed should include several rebuttal/continuation markers.
    reactive_words = ("but", "and", "then", "if", "yet", "still", "exactly", "agree", "not enough", "rather", "while")
    reactive_hits = sum(1 for body in bodies[:20] if any(w in body for w in reactive_words))
    if reactive_hits < 6:
        return True

    return False

def approx_tokens(text: str) -> int:
    # Conservative enough for budget gating, not exact billing.
    return max(1, int(len(text) / 3.5))


def estimate_cost_usd(model: str, input_tokens: int, max_output_tokens: int) -> float:
    price = MODEL_PRICES_USD_PER_1M.get(model, MODEL_PRICES_USD_PER_1M["gpt-4o-mini"])
    return input_tokens / 1_000_000 * price["input"] + max_output_tokens / 1_000_000 * price["output"]


def ai_enabled() -> bool:
    return str(os.getenv("OPENAI_ENABLE_AI", "true")).strip().lower() in {"1", "true", "yes", "on"}


def openai_chat_json(model: str, system: str, user: str, max_output_tokens: int = 3500) -> dict[str, Any] | None:
    """Minimal OpenAI Chat Completions client using urllib.

    Avoids adding the openai SDK dependency to the static-render workflow. If the
    endpoint/model changes later, this single function is the replacement point.
    """
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None

    # Local pre-call cost guard. This is not a substitute for OpenAI Project
    # budget alerts; it simply prevents accidental oversized prompts.
    input_tokens = approx_tokens(system + "\n" + user)
    est = estimate_cost_usd(model, input_tokens, max_output_tokens)
    daily_limit = as_float(os.getenv("OPENAI_DAILY_USD_LIMIT"), 0.50)
    if est > daily_limit:
        print(f"WARN AI skipped by local budget guard: estimate=${est:.4f} > daily_limit=${daily_limit:.4f}")
        return None

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=70) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            content = raw["choices"][0]["message"]["content"]
            return json.loads(content)
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
            print(f"WARN OpenAI call failed attempt={attempt+1}: {exc}")
            time.sleep(1.5)
    return None


def sanitize_text(text: Any, banned: list[str] | None = None) -> str:
    """Remove obviously unsafe/advice-like phrasing from generated text."""
    s = str(text or "").strip()
    s = re.sub(r"\s+", " ", s)
    if not s:
        return "Signal line unavailable."
    banned = banned or BANNED_PHRASES_DEFAULT
    # Replace banned phrases rather than failing the full build. This keeps the
    # site rendering even when the model drifts.
    for phrase in banned:
        s = re.sub(re.escape(phrase), "signal", s, flags=re.IGNORECASE)
    return s[:520]


def build_ai_payload(config: dict[str, Any], ctx: ArenaContext, agents: list[dict[str, Any]], top_themes: list[dict[str, Any]], market_context: dict[str, Any]) -> dict[str, Any] | None:
    """Ask the model for a daily brief plus a conversation-style feed.

    V1.1 change: the model is no longer asked for isolated agent blurbs. It is
    given a shared market_context and explicit voice rules so the Arena Log feels
    like Agents reacting to each other around current Japan signal topics.
    """
    if not ai_enabled():
        print("AI disabled by OPENAI_ENABLE_AI")
        return None

    analyst = config.get("global_market_analyst") or {}
    model = os.getenv("OPENAI_MODEL_MINI") or analyst.get("model") or config.get("arena", {}).get("default_model") or "gpt-4o-mini"
    max_posts = int(os.getenv("OPENAI_MAX_AGENT_FEED_POSTS") or config.get("arena", {}).get("max_feed_posts") or 72)
    max_posts = max(5, min(160, max_posts))

    compact_agents = []
    for a in agents:
        pick = a.get("pick") or {}
        compact_agents.append({
            "agent_id": a.get("agent_id"),
            "name": a.get("name"),
            "class": a.get("class"),
            "personality": a.get("personality"),
            "philosophy": a.get("philosophy"),
            "conversation_role": a.get("conversation_role"),
            "speech_style": a.get("speech_style"),
            "selection_profile": a.get("selection_profile"),
            "pick": {
                "symbol": pick.get("symbol"),
                "name": pick.get("name"),
                "theme": pick.get("theme"),
                "score_pts": pick.get("score_pts"),
                "return_1d_pct": pick.get("return_1d_pct"),
                "return_5d_pct": pick.get("return_5d_pct"),
                "return_20d_pct": pick.get("return_20d_pct"),
                "volume_ratio_20d": pick.get("volume_ratio_20d"),
                "liquidity_score_0_1": pick.get("liquidity_score_0_1"),
                "extension_risk_0_1": pick.get("extension_risk_0_1"),
            },
        })

    system = analyst.get("system_prompt") or "You are a concise market commentator. Return strict JSON."
    system += """

Return valid JSON only.
Never use buy/sell/recommendation/target-price/guaranteed language.
Do not invent external news. Use only the provided market_context and signal data.
Never quote or restate raw JSON, Python dictionaries, field names, or nested market data. Convert data into plain market language.
The Arena Log must feel like a real conversation: each line should respond to a prior line, challenge it, agree with it, or extend it.
Do not produce a rotating list of independent slogans. Do not repeat the same sentence template.
Do not write scheduling/meta text such as unlock, locked, scheduled, later, or reveal.
Keep lines short, concrete, and grounded in symbols/themes from the input.
"""
    user = json.dumps({
        "task": "Generate Neon Tokyo AI Arena daily brief, agent comments, battle lines, and a conversation-style scheduled feed.",
        "arena_style": "KAWAII pixel RPG party chat + serious institutional Japan equity signal commentary.",
        "conversation_rules": [
            "Create a flowing party chat, not standalone status updates.",
            "The first 20 feed lines must read like one continuous conversation where each Agent responds to the previous idea.",
            "Use conversational links such as agreement, disagreement, warning, or reframing. Avoid isolated generic observations.",
            "Do not reuse the same sentence pattern or repeat a body with minor wording changes.",
            "Use each Agent's conversation_role and speech_style so all voices feel clearly different.",
            "Mention concrete symbols or themes when useful, but avoid pretending to know news not in the data.",
            "Every few lines, include a challenge, warning, or counterpoint.",
            "Do not repeat the same Agent more than twice in a row.",
            "Avoid generic lines such as 'watch for signs', 'monitor closely', or 'focus on trends' unless tied to a specific symbol/theme.",
            "Never mention scheduling, unlocking, locked messages, or future reveal mechanics.",
            "Each feed body must be <= 30 words.",
        ],
        "requirements": {
            "daily_brief": {"title": "<= 9 words", "body": "<= 70 words", "risk_note": "<= 28 words"},
            "agents": "For each agent_id, provide agent_comment <= 34 words and battle_line <= 14 words.",
            "feed": f"Create {max_posts} feed lines. Use a conversational sequence across Agents. One agent per line.",
            "json_shape": {
                "daily_brief": {"title": "...", "body": "...", "risk_note": "..."},
                "agents": [{"agent_id": "...", "agent_comment": "...", "battle_line": "..."}],
                "feed": [{"agent_id": "...", "type": "conversation|challenge|warning|theme|discovery|counterpoint", "body": "..."}],
            },
        },
        "market_context": market_context,
        "agents": compact_agents,
    }, ensure_ascii=False)

    return openai_chat_json(model=model, system=system, user=user, max_output_tokens=int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS") or 6000))


def merge_ai_text(arena: dict[str, Any], ai_payload: dict[str, Any] | None, config: dict[str, Any], ctx: ArenaContext, market_context: dict[str, Any] | None = None) -> None:
    agents = arena["agents"]
    interval = int(config.get("arena", {}).get("feed_interval_minutes") or 10)
    max_posts = int(os.getenv("OPENAI_MAX_AGENT_FEED_POSTS") or config.get("arena", {}).get("max_feed_posts") or 72)
    max_posts = max(5, min(160, max_posts))
    # Start far enough in the past so the first page view already feels like a
    # live party chat. We intentionally avoid showing "locked/unlock" rows in
    # the UI; instead, the generated feed contains many already-visible lines
    # plus future lines that simply appear later.
    #
    # 15 visible lines is roughly 3x the first prototype density. Keep the number
    # independent from Agent count so adding/removing Agents does not make the
    # opening screen feel empty.
    initial_visible_lines = int(os.getenv("AI_ARENA_INITIAL_VISIBLE_LINES") or config.get("arena", {}).get("initial_visible_lines") or 15)
    initial_visible_lines = max(len(agents), min(30, initial_visible_lines))
    show_start = now_jst().replace(second=0, microsecond=0) - timedelta(minutes=interval * max(0, initial_visible_lines - 1))

    if not ai_payload:
        for agent in agents:
            agent["agent_comment"] = fallback_agent_comment(agent, agent.get("pick"))
            agent["battle_line"] = fallback_battle_line(agent, agent.get("pick"))
        arena["feed"] = fallback_feed(agents, show_start, interval, max_posts, market_context=market_context)
        arena["ai"]["fallback_used"] = True
        arena["ai"]["status"] = "fallback"
        return

    daily_brief = ai_payload.get("daily_brief") if isinstance(ai_payload, dict) else None
    if isinstance(daily_brief, dict):
        arena["daily_brief"] = {
            "analyst_id": "grand_market_analyst",
            "title": strip_raw_json_leak(daily_brief.get("title")),
            "body": strip_raw_json_leak(daily_brief.get("body")),
            "risk_note": strip_raw_json_leak(daily_brief.get("risk_note")),
        }

    ai_agents = ai_payload.get("agents") if isinstance(ai_payload, dict) else []
    by_id = {str(x.get("agent_id")): x for x in ai_agents if isinstance(x, dict) and x.get("agent_id")}
    for agent in agents:
        generated = by_id.get(str(agent.get("agent_id")), {})
        agent["agent_comment"] = strip_raw_json_leak(generated.get("agent_comment") or fallback_agent_comment(agent, agent.get("pick")))
        agent["battle_line"] = strip_raw_json_leak(generated.get("battle_line") or fallback_battle_line(agent, agent.get("pick")))

    raw_feed = ai_payload.get("feed") if isinstance(ai_payload, dict) else []
    feed = []
    if isinstance(raw_feed, list):
        enabled_ids = {a.get("agent_id") for a in agents}
        for item in raw_feed[:max_posts]:
            if not isinstance(item, dict):
                continue
            aid = item.get("agent_id")
            if aid not in enabled_ids:
                continue
            agent = next((a for a in agents if a.get("agent_id") == aid), None)
            pick = (agent or {}).get("pick") or {}
            feed.append({
                "id": f"feed_{len(feed)+1:03d}",
                "show_at": iso_jst(show_start + timedelta(minutes=len(feed) * interval)),
                "agent_id": aid,
                "agent_name": (agent or {}).get("name") or aid,
                "type": sanitize_text(item.get("type") or "conversation"),
                "body": sanitize_text(item.get("body")),
                "linked_symbol": pick.get("symbol"),
                "linked_theme": pick.get("theme"),
            })
    if feed_needs_quality_fallback(feed, agents):
        # The API may succeed but still return a repetitive ticker-like feed.
        # In that case, protect the product experience by switching to the
        # deterministic threaded conversation. This keeps the UI from looking
        # like a copy-pasted alert loop.
        feed = fallback_feed(agents, show_start, interval, max_posts, market_context=market_context)
        arena["ai"]["fallback_used"] = True
        arena["ai"]["status"] = "fallback_quality_guard"
    else:
        arena["ai"]["fallback_used"] = False
        arena["ai"]["status"] = "ok"
    arena["feed"] = feed


def build_arena() -> dict[str, Any]:
    config = read_yaml(AGENTS_YAML, {})
    _presets = read_yaml(PRESETS_YAML, {})  # Loaded now so YAML errors fail early; used for future prompt tuning.
    daily = read_json(DAILY_JSON, {})
    weekly = read_json(WEEKLY_JSON, {})
    backtest = read_json(BACKTEST_JSON, {})

    daily_items = collect_daily_candidates(daily)
    weekly_items = unique_items([x for k in ("items", "all_items") for x in (weekly.get(k, []) or []) if isinstance(x, dict)])
    ctx = ArenaContext(
        daily=daily,
        weekly=weekly,
        backtest=backtest,
        daily_items=daily_items,
        weekly_items=weekly_items,
        weekly_map=weekly_by_symbol(weekly),
        theme_scores=theme_heat(daily_items, weekly_items),
    )

    arena_cfg = config.get("arena") or {}
    enabled_agents_cfg = [a for a in (config.get("agents") or []) if isinstance(a, dict) and a.get("enabled", True)]
    if not enabled_agents_cfg:
        raise SystemExit("No enabled agents in data/ai_arena_agents_jp.yml")

    used: set[str] = set()
    unique = bool(arena_cfg.get("unique_agent_picks", True))
    agents = []
    for agent_cfg in enabled_agents_cfg:
        item = pick_for_agent(agent_cfg, ctx, used, unique)
        pick = build_pick_payload(item)
        agents.append({
            "agent_id": agent_cfg.get("id"),
            "name": agent_cfg.get("name"),
            "class": agent_cfg.get("class"),
            "enabled": True,
            "model": agent_cfg.get("model") or arena_cfg.get("default_model") or "gpt-4o-mini",
            "selection_profile": agent_cfg.get("selection_profile"),
            "avatar_style": agent_cfg.get("avatar_style"),
            "ui_tone": agent_cfg.get("ui_tone"),
            "personality": agent_cfg.get("personality"),
            "philosophy": agent_cfg.get("philosophy"),
            "pick": pick,
            "stats": build_stats(item, ctx),
            "agent_comment": None,
            "battle_line": None,
            "result": {"status": "pending"},
        })

    top_themes = top_theme_summary(ctx)
    analyst = config.get("global_market_analyst") or {}
    generated = now_jst()
    arena_date = extract_latest_daily_date(daily, daily_items, generated)
    market_context = build_market_context(ctx, top_themes, agents, generated)

    arena = {
        "schema_version": "neon_tokyo_ai_arena_v1",
        "generated_at": iso_jst(generated),
        "arena_date": arena_date,
        "market": "Japan",
        "timezone": "Asia/Tokyo",
        "config_version": arena_cfg.get("version") or config.get("arena", {}).get("version") or "v1",
        "source": {
            "daily_json": str(DAILY_JSON.relative_to(ROOT)) if DAILY_JSON.is_relative_to(ROOT) else str(DAILY_JSON),
            "weekly_json": str(WEEKLY_JSON.relative_to(ROOT)) if WEEKLY_JSON.is_relative_to(ROOT) else str(WEEKLY_JSON),
            "backtest_json": str(BACKTEST_JSON.relative_to(ROOT)) if BACKTEST_JSON.is_relative_to(ROOT) else str(BACKTEST_JSON),
            "daily_generated_at": daily.get("generated_at"),
            "weekly_generated_at": weekly.get("generated_at"),
            "backtest_generated_at": backtest.get("generated_at"),
        },
        "ai": {
            "enabled": ai_enabled(),
            "model": os.getenv("OPENAI_MODEL_MINI") or analyst.get("model") or arena_cfg.get("default_model") or "gpt-4o-mini",
            "future_daily_analyst_model": analyst.get("future_model"),
            "status": "not_run",
            "fallback_used": False,
        },
        "daily_brief": fallback_daily_brief(ctx, top_themes),
        "market_context": market_context,
        "top_themes": top_themes,
        "agents": agents,
        "feed": [],
        "user_interaction": {"mode": "localStorage", "backing_enabled": True},
        "arena_result": {"status": "pending", "evaluation_horizon": arena_cfg.get("result_horizon", "1d"), "winner_agent_id": None},
        "disclaimer": arena_cfg.get("disclaimer") or "Informational only. Not investment advice.",
    }

    if daily_items:
        ai_payload = build_ai_payload(config, ctx, agents, top_themes, market_context)
        merge_ai_text(arena, ai_payload, config, ctx, market_context=market_context)
    else:
        merge_ai_text(arena, None, config, ctx, market_context=market_context)
        arena["daily_brief"] = {
            "analyst_id": "grand_market_analyst",
            "title": "Arena awaiting signal data",
            "body": "Daily signal JSON was not available. Rendered a safe empty Arena shell.",
            "risk_note": "Run the Daily JP build before relying on Arena output.",
        }

    horizon = str(arena_cfg.get("result_horizon") or "1d")
    arena["arena_result"] = build_result_payload(arena["agents"], backtest, horizon)
    return arena


def main() -> None:
    arena = build_arena()
    write_json(ARENA_OUT, arena)


if __name__ == "__main__":
    main()
