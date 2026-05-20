#!/usr/bin/env python3
"""
Rebuild Japan Weekly Backtest for Neon Tokyo Signals.

Input:
- site/data/prices-jp/latest.json
- data/weekly_candidates_jp.csv, fallback data/universe_jp.csv
- scripts/build_weekly_jp.py scoring functions

Output:
- site/data/japan/weekly/backtest/latest.json
- site/data/japan/weekly/backtest/YYYY-MM-DD.json
- site/data/japan/weekly/backtest/manifest.json

Design:
- No API calls. Uses only cached JP prices.
- Replays weekly scoring using bars visible at each evaluation date.
- Candidate universe is capped to Weekly Top 10 by score.
- Reports Top 3 / Top 5 / Top 10 forward performance separately.
- Entry uses next trading day's open after the weekly evaluation date.
- Forward returns use trading-day offsets: 1W=5D, 2W=10D, 4W=20D, 8W=40D, 12W=60D.
"""

from __future__ import annotations

import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

try:
    import build_weekly_jp as weekly
except Exception as exc:  # pragma: no cover - action-time safety
    raise RuntimeError("Failed to import scripts/build_weekly_jp.py. Run Weekly JP screening setup first.") from exc

TZ = ZoneInfo("Asia/Tokyo")

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
OUT_DIR = (ROOT / OUT_DIR).resolve() if not OUT_DIR.is_absolute() else OUT_DIR.resolve()

PRICES_JSON = Path(os.getenv("PRICES_JSON", str(OUT_DIR / "data" / "prices-jp" / "latest.json")))
PRICES_JSON = (ROOT / PRICES_JSON).resolve() if not PRICES_JSON.is_absolute() else PRICES_JSON.resolve()

OUT_BACKTEST_DIR = OUT_DIR / "data" / "japan" / "weekly" / "backtest"
LEGACY_OUT_BACKTEST_DIR = OUT_DIR / "data" / "weekly-jp" / "backtest"

WEEKS = int(os.getenv("WEEKLY_JP_BACKTEST_WEEKS", os.getenv("WEEKS", "32")))
END_DATE_ENV = os.getenv("WEEKLY_JP_BACKTEST_END_DATE", os.getenv("END_DATE", "")).strip()
MIN_WEEKLY_BARS = int(os.getenv("WEEKLY_JP_MIN_WEEKLY_BARS", "40"))
RANK_LIMIT = min(10, max(1, int(os.getenv("WEEKLY_JP_BACKTEST_RANK_LIMIT", "10"))))
BENCHMARK_RETURN_ABS_LIMIT_PCT = float(os.getenv("WEEKLY_JP_BENCHMARK_RETURN_ABS_LIMIT_PCT", "35"))
PRIMARY_HORIZON = os.getenv("WEEKLY_JP_PRIMARY_HORIZON", "4w").lower()
HORIZON_WEEKS = [int(x.strip()) for x in os.getenv("WEEKLY_JP_HORIZONS", "1,2,4,8,12").split(",") if x.strip()]
HORIZONS = [f"{w}w" for w in HORIZON_WEEKS]
TRADING_DAYS_BY_HORIZON = {f"{w}w": w * 5 for w in HORIZON_WEEKS}
TOP_BUCKETS = {
    "Top 3": 3,
    "Top 5": 5,
    "Top 10": 10,
}


def now_jst() -> datetime:
    return datetime.now(TZ)


def iso_now() -> str:
    return now_jst().isoformat(timespec="seconds")


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON not found: {safe_relative(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def to_float(value: Any) -> float | None:
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


def safe_round(value: Any, digits: int = 4) -> float | None:
    v = to_float(value)
    if v is None:
        return None
    return round(v, digits)


def median(values: list[float]) -> float | None:
    clean = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    if not clean:
        return None
    return statistics.median(clean)


def avg(values: list[float]) -> float | None:
    clean = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    if not clean:
        return None
    return sum(clean) / len(clean)


def percentile(values: list[float], q: float) -> float | None:
    clean = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    if not clean:
        return None
    return float(np.percentile(clean, q))


def classify_score_band(score: Any) -> str:
    s = to_float(score)
    if s is None:
        return "Unknown"
    if s >= 850:
        return "850+"
    if s >= 800:
        return "800-849"
    if s >= 750:
        return "750-799"
    if s >= 700:
        return "700-749"
    if s >= 650:
        return "650-699"
    if s >= 600:
        return "600-649"
    return "<600"


def load_prices() -> dict[str, Any]:
    prices = read_json(PRICES_JSON)
    if not isinstance(prices.get("items"), list):
        raise ValueError("prices JSON has no items list")
    return prices


def equity_items(prices: dict[str, Any]) -> list[dict[str, Any]]:
    raw = prices.get("equities") or []
    if not raw:
        raw = [x for x in prices.get("items") or [] if not x.get("pulse_label")]
    meta = weekly.load_candidate_meta()
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol") or "")
        if symbol in meta:
            out.append(item)
    return out


def pulse_items(prices: dict[str, Any]) -> list[dict[str, Any]]:
    return [x for x in prices.get("market_pulse") or [] if isinstance(x, dict)]


def clone_with_bars_until(item: dict[str, Any], eval_date: pd.Timestamp) -> dict[str, Any]:
    bars = []
    for bar in item.get("bars") or []:
        try:
            d = pd.Timestamp(bar.get("date"))
        except Exception:
            continue
        if pd.notna(d) and d <= eval_date:
            bars.append(bar)
    cloned = dict(item)
    cloned["bars"] = bars
    cloned["bars_count"] = len(bars)
    if bars:
        cloned["date_start"] = bars[0].get("date")
        cloned["date_end"] = bars[-1].get("date")
    return cloned


def build_truncated_price_payload(prices: dict[str, Any], eval_date: pd.Timestamp) -> dict[str, Any]:
    return {
        **prices,
        "items": [clone_with_bars_until(x, eval_date) for x in prices.get("items") or []],
        "market_pulse": [clone_with_bars_until(x, eval_date) for x in pulse_items(prices)],
        "equities": [clone_with_bars_until(x, eval_date) for x in equity_items(prices)],
    }


def get_topix_item(prices: dict[str, Any]) -> dict[str, Any] | None:
    for item in pulse_items(prices):
        label = str(item.get("pulse_label") or "").upper()
        symbol = str(item.get("symbol") or "")
        if label == "TOPIX" or symbol == "1306.T":
            return item
    for item in prices.get("items") or []:
        if str(item.get("symbol") or "") == "1306.T":
            return item
    return None


def trading_week_eval_dates(prices: dict[str, Any], end_date: pd.Timestamp | None) -> list[pd.Timestamp]:
    topix = get_topix_item(prices)
    if topix is None:
        # Fallback to first equity. Better to fail softly than to block render-only flows.
        items = equity_items(prices)
        if not items:
            return []
        topix = items[0]
    df = weekly.bars_to_df(topix)
    if df.empty:
        return []
    if end_date is not None:
        df = df[df.index <= end_date]
    if df.empty:
        return []
    daily_dates = pd.Series(df.index, index=df.index)
    grouped = daily_dates.groupby(pd.Grouper(freq="W-FRI")).max().dropna()
    return [pd.Timestamp(x).normalize() for x in grouped.tolist()]


def date_index(df: pd.DataFrame) -> dict[pd.Timestamp, int]:
    return {pd.Timestamp(idx).normalize(): i for i, idx in enumerate(df.index)}


def future_return_from_daily(
    df: pd.DataFrame,
    eval_date: pd.Timestamp,
    trading_days: int,
) -> dict[str, Any] | None:
    if df.empty:
        return None
    idx_map = date_index(df)
    eval_key = pd.Timestamp(eval_date).normalize()
    if eval_key not in idx_map:
        prior = [d for d in idx_map.keys() if d <= eval_key]
        if not prior:
            return None
        eval_key = max(prior)
    eval_i = idx_map[eval_key]
    entry_i = eval_i + 1
    exit_i = entry_i + trading_days - 1
    if entry_i >= len(df) or exit_i >= len(df):
        return None
    entry_row = df.iloc[entry_i]
    exit_row = df.iloc[exit_i]
    entry_price = to_float(entry_row.get("Open")) or to_float(entry_row.get("Close"))
    exit_price = to_float(exit_row.get("Close"))
    if entry_price is None or exit_price is None or entry_price <= 0:
        return None
    low_slice = df.iloc[entry_i : exit_i + 1]["Low"].dropna()
    worst = None
    if not low_slice.empty:
        worst = (float(low_slice.min()) / entry_price - 1.0) * 100.0
    return {
        "entry_date": str(pd.Timestamp(entry_row.name).date()),
        "exit_date": str(pd.Timestamp(exit_row.name).date()),
        "entry_price": safe_round(entry_price, 4),
        "exit_price": safe_round(exit_price, 4),
        "return_pct": safe_round((exit_price / entry_price - 1.0) * 100.0, 4),
        "worst_drawdown_pct": safe_round(worst, 4),
    }


def valid_benchmark_return(value: Any) -> float | None:
    v = to_float(value)
    if v is None or abs(v) > BENCHMARK_RETURN_ABS_LIMIT_PCT:
        return None
    return v


def summarize_forward(records: list[dict[str, Any]], horizon: str) -> dict[str, Any]:
    vals: list[float] = []
    alphas: list[float] = []
    dds: list[float] = []
    scores: list[float] = []
    for r in records:
        f = (r.get("forward") or {}).get(horizon) or {}
        ret = to_float(f.get("return_pct"))
        alpha = to_float(f.get("alpha_pct"))
        dd = to_float(f.get("worst_drawdown_pct"))
        score = to_float(r.get("score_pts"))
        if ret is not None:
            vals.append(ret)
        if alpha is not None:
            alphas.append(alpha)
        if dd is not None:
            dds.append(dd)
        if score is not None:
            scores.append(score)
    return {
        "count": len(vals),
        "avg_return_pct": safe_round(avg(vals), 4),
        "median_return_pct": safe_round(median(vals), 4),
        "win_rate_pct": safe_round((sum(1 for x in vals if x > 0) / len(vals) * 100.0) if vals else None, 2),
        "avg_alpha_pct": safe_round(avg(alphas), 4),
        "median_alpha_pct": safe_round(median(alphas), 4),
        "positive_alpha_rate_pct": safe_round((sum(1 for x in alphas if x > 0) / len(alphas) * 100.0) if alphas else None, 2),
        "avg_worst_drawdown_pct": safe_round(avg(dds), 4),
        "avg_score_pts": safe_round(avg(scores), 2),
        "p10_return_pct": safe_round(percentile(vals, 10), 4),
        "p90_return_pct": safe_round(percentile(vals, 90), 4),
        "max_return_pct": safe_round(max(vals) if vals else None, 4),
        "min_return_pct": safe_round(min(vals) if vals else None, 4),
        "alpha_valid_count": len(alphas),
    }


def summarize_by(records: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        value = r.get(key)
        if value is None:
            value = "Unknown"
        groups[str(value)].append(r)
    return {name: {h: summarize_forward(rows, h) for h in HORIZONS} for name, rows in sorted(groups.items())}


def top_bucket_performance(records: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label, limit in TOP_BUCKETS.items():
        rows = [r for r in records if int(r.get("rank") or 999) <= limit]
        out[label] = {h: summarize_forward(rows, h) for h in HORIZONS}
    return out


def daily_trend(records: list[dict[str, Any]], horizon: str) -> list[dict[str, Any]]:
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        by_date[str(r.get("eval_date"))].append(r)

    curve = {label: 100.0 for label in TOP_BUCKETS}
    out: list[dict[str, Any]] = []
    for eval_date in sorted(by_date.keys()):
        rows = by_date[eval_date]
        point: dict[str, Any] = {"eval_date": eval_date}
        for label, limit in TOP_BUCKETS.items():
            bucket_rows = [r for r in rows if int(r.get("rank") or 999) <= limit]
            returns = []
            alphas = []
            for r in bucket_rows:
                f = (r.get("forward") or {}).get(horizon) or {}
                ret = to_float(f.get("return_pct"))
                alpha = to_float(f.get("alpha_pct"))
                if ret is not None:
                    returns.append(ret)
                if alpha is not None:
                    alphas.append(alpha)
            avg_ret = avg(returns)
            avg_alpha = avg(alphas)
            if avg_ret is not None:
                curve[label] *= 1.0 + avg_ret / 100.0
            key = label.lower().replace(" ", "_")
            point[f"{key}_avg_return_pct"] = safe_round(avg_ret, 4)
            point[f"{key}_avg_alpha_pct"] = safe_round(avg_alpha, 4)
            point[f"{key}_equity_index"] = safe_round(curve[label], 4)
            point[f"{key}_count"] = len(bucket_rows)
        out.append(point)
    return out


def benchmark_quality(records: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for h in HORIZONS:
        vals = []
        invalid = 0
        valid = 0
        for r in records:
            f = (r.get("forward") or {}).get(h) or {}
            b = to_float(f.get("benchmark_return_pct"))
            if b is None:
                continue
            vals.append(b)
            if f.get("alpha_quality") == "valid":
                valid += 1
            elif f.get("alpha_quality") == "invalid_benchmark":
                invalid += 1
        out[h] = {
            "valid_alpha_count": valid,
            "invalid_alpha_count": invalid,
            "invalid_rate_pct": safe_round((invalid / (valid + invalid) * 100.0) if (valid + invalid) else None, 2),
            "benchmark_return_min_pct": safe_round(min(vals) if vals else None, 4),
            "benchmark_return_max_pct": safe_round(max(vals) if vals else None, 4),
            "abs_limit_pct": BENCHMARK_RETURN_ABS_LIMIT_PCT,
        }
    return out


def build_backtest() -> dict[str, Any]:
    prices = load_prices()
    meta = weekly.load_candidate_meta()
    equities = equity_items(prices)
    full_dfs = {str(x.get("symbol")): weekly.bars_to_df(x) for x in equities}
    topix_full_item = get_topix_item(prices)
    topix_df = weekly.bars_to_df(topix_full_item) if topix_full_item else pd.DataFrame()

    end_date = pd.Timestamp(END_DATE_ENV).normalize() if END_DATE_ENV else None
    eval_dates_all = trading_week_eval_dates(prices, end_date)
    if not eval_dates_all:
        raise RuntimeError("No weekly evaluation dates found from cached prices.")

    max_days = max(TRADING_DAYS_BY_HORIZON.values())
    topix_idx = date_index(topix_df) if not topix_df.empty else {}

    eligible_eval_dates: list[pd.Timestamp] = []
    for d in eval_dates_all:
        if d not in topix_idx:
            prior = [x for x in topix_idx.keys() if x <= d]
            if not prior:
                continue
            d_key = max(prior)
        else:
            d_key = d
        idx = topix_idx.get(d_key)
        if idx is None:
            continue
        if idx + 1 + max_days - 1 < len(topix_df):
            eligible_eval_dates.append(d_key)

    selected_dates = eligible_eval_dates[-WEEKS:]
    records: list[dict[str, Any]] = []
    skipped_dates: list[dict[str, Any]] = []

    for eval_date in selected_dates:
        truncated = build_truncated_price_payload(prices, eval_date)
        topix_row, benchmark_rows, benchmark_state = weekly.benchmark_weekly(truncated)
        scored: list[dict[str, Any]] = []
        for item in equity_items(truncated):
            symbol = str(item.get("symbol") or "")
            candidate_meta = meta.get(symbol, {})
            try:
                row = weekly.score_item(item, candidate_meta, topix_row)
            except Exception as exc:
                continue
            if not row:
                continue
            scored.append(row)

        scored.sort(key=lambda x: (to_float(x.get("score_pts")) or -1, str(x.get("symbol") or "")), reverse=True)
        for i, row in enumerate(scored, start=1):
            row["rank"] = i
        top_rows = scored[:RANK_LIMIT]
        if not top_rows:
            skipped_dates.append({"eval_date": str(eval_date.date()), "reason": "no scored rows"})
            continue

        benchmark_forward: dict[str, Any] = {}
        for h, days in TRADING_DAYS_BY_HORIZON.items():
            b = future_return_from_daily(topix_df, eval_date, days) if not topix_df.empty else None
            b_ret = to_float((b or {}).get("return_pct"))
            b_valid = valid_benchmark_return(b_ret)
            benchmark_forward[h] = {
                **(b or {}),
                "return_pct": safe_round(b_ret, 4),
                "alpha_quality": "valid" if b_valid is not None else "invalid_benchmark",
                "valid_return_pct": safe_round(b_valid, 4),
            }

        for row in top_rows:
            symbol = str(row.get("symbol") or "")
            df = full_dfs.get(symbol, pd.DataFrame())
            forward: dict[str, Any] = {}
            entry_date = None
            for h, days in TRADING_DAYS_BY_HORIZON.items():
                f = future_return_from_daily(df, eval_date, days)
                b = benchmark_forward.get(h) or {}
                ret = to_float((f or {}).get("return_pct"))
                b_valid = to_float(b.get("valid_return_pct"))
                alpha = ret - b_valid if ret is not None and b_valid is not None else None
                if f and entry_date is None:
                    entry_date = f.get("entry_date")
                forward[h] = {
                    **(f or {"status": "pending_or_missing"}),
                    "benchmark_return_pct": safe_round(to_float(b.get("return_pct")), 4),
                    "alpha_pct": safe_round(alpha, 4),
                    "alpha_quality": "valid" if alpha is not None else "invalid_benchmark_or_missing_price",
                }

            rank = int(row.get("rank") or 0)
            top_bucket = "Top 10"
            if rank <= 3:
                top_bucket = "Top 3"
            elif rank <= 5:
                top_bucket = "Top 5"

            records.append({
                "eval_date": str(eval_date.date()),
                "entry_date": entry_date,
                "rank": rank,
                "top_bucket": top_bucket,
                "symbol": row.get("symbol"),
                "name": row.get("name"),
                "theme": row.get("theme"),
                "bucket": row.get("bucket"),
                "priority": row.get("priority"),
                "score_pts": row.get("score_pts"),
                "score_band": classify_score_band(row.get("score_pts")),
                "signal": row.get("signal"),
                "quality": row.get("quality") or row.get("classification"),
                "liquidity_band": row.get("liquidity_band"),
                "entry_quality": row.get("entry_quality"),
                "extension_status": row.get("extension_status"),
                "relative_strength_status": row.get("relative_strength_status"),
                "why_now": row.get("why_now"),
                "main_risk": row.get("main_risk"),
                "flags": row.get("flags") or [],
                "metrics": row.get("metrics") or {},
                "component_pts": row.get("component_pts") or {},
                "forward": forward,
            })

    overall = {h: summarize_forward(records, h) for h in HORIZONS}
    top_perf = top_bucket_performance(records)

    primary = PRIMARY_HORIZON if PRIMARY_HORIZON in HORIZONS else HORIZONS[min(2, len(HORIZONS)-1)]
    trend = daily_trend(records, primary)

    best = sorted(
        [r for r in records if to_float(((r.get("forward") or {}).get(primary) or {}).get("return_pct")) is not None],
        key=lambda r: to_float(((r.get("forward") or {}).get(primary) or {}).get("return_pct")) or -999,
        reverse=True,
    )[:20]
    worst = sorted(
        [r for r in records if to_float(((r.get("forward") or {}).get(primary) or {}).get("return_pct")) is not None],
        key=lambda r: to_float(((r.get("forward") or {}).get(primary) or {}).get("return_pct")) or 999,
    )[:20]

    signal_counts = Counter(str(r.get("signal") or "Unknown") for r in records)
    quality_counts = Counter(str(r.get("quality") or "Unknown") for r in records)

    summary = {
        "eval_date_count": len(selected_dates),
        "eval_date_start": str(selected_dates[0].date()) if selected_dates else None,
        "eval_date_end": str(selected_dates[-1].date()) if selected_dates else None,
        "signal_count": len(records),
        "rank_limit": RANK_LIMIT,
        "weeks_requested": WEEKS,
        "primary_horizon": primary,
        "horizons": HORIZONS,
        "top_bucket_performance": top_perf,
        "overall": overall,
        "signal_counts": dict(signal_counts),
        "quality_counts": dict(quality_counts),
        "benchmark_quality": benchmark_quality(records),
        "best_primary_forward_moves": best,
        "worst_primary_forward_moves": worst,
    }

    payload = {
        "schema_version": "weekly-jp-backtest-v1",
        "generated_at": iso_now(),
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "source_prices": safe_relative(PRICES_JSON),
        "source_prices_generated_at": prices.get("generated_at"),
        "benchmark": "TOPIX",
        "primary_horizon": primary,
        "horizons": HORIZONS,
        "trading_days_by_horizon": TRADING_DAYS_BY_HORIZON,
        "methodology": {
            "name": "Neon Tokyo Weekly JP Backtest v1",
            "api_calls": 0,
            "candidate_policy": "Each weekly evaluation date is scored using only bars visible at that date. Only score-ranked Top 10 are retained.",
            "entry_policy": "Next trading day's open after the weekly evaluation date.",
            "return_policy": "Forward returns use trading-day offsets: 1W=5D, 2W=10D, 4W=20D, 8W=40D, 12W=60D.",
            "alpha_policy": "Alpha equals stock return minus TOPIX ETF return for the same horizon. TOPIX returns above the absolute guard are invalidated.",
            "benchmark_return_abs_limit_pct": BENCHMARK_RETURN_ABS_LIMIT_PCT,
        },
        "config": {
            "weeks": WEEKS,
            "end_date": END_DATE_ENV or None,
            "min_weekly_bars": MIN_WEEKLY_BARS,
            "rank_limit": RANK_LIMIT,
            "top_buckets": TOP_BUCKETS,
        },
        "summary": summary,
        "performance_trend": trend,
        "outcomes": records,
        "by_signal": summarize_by(records, "signal"),
        "by_quality": summarize_by(records, "quality"),
        "by_score_band": summarize_by(records, "score_band"),
        "by_bucket": summarize_by(records, "bucket"),
        "by_liquidity": summarize_by(records, "liquidity_band"),
        "by_extension_status": summarize_by(records, "extension_status"),
        "by_entry_quality": summarize_by(records, "entry_quality"),
        "by_theme": summarize_by(records, "theme"),
        "skipped_dates": skipped_dates,
    }
    return payload


def write_outputs(payload: dict[str, Any]) -> None:
    date_key = now_jst().date().isoformat()
    latest = OUT_BACKTEST_DIR / "latest.json"
    dated = OUT_BACKTEST_DIR / f"{date_key}.json"
    manifest = OUT_BACKTEST_DIR / "manifest.json"
    write_json(latest, payload)
    write_json(dated, payload)
    write_json(manifest, {
        "schema_version": "weekly-jp-backtest-manifest-v1",
        "generated_at": payload.get("generated_at"),
        "latest": safe_relative(latest),
        "items": [
            {"date": date_key, "path": safe_relative(dated), "generated_at": payload.get("generated_at")}
        ],
    })

    # Compatibility copy for older links/tools.
    write_json(LEGACY_OUT_BACKTEST_DIR / "latest.json", payload)
    write_json(LEGACY_OUT_BACKTEST_DIR / "manifest.json", {
        "schema_version": "weekly-jp-backtest-manifest-v1",
        "generated_at": payload.get("generated_at"),
        "latest": safe_relative(LEGACY_OUT_BACKTEST_DIR / "latest.json"),
    })


def main() -> int:
    print(f"ROOT={ROOT}")
    print(f"OUT_DIR={safe_relative(OUT_DIR)}")
    print(f"PRICES_JSON={safe_relative(PRICES_JSON)}")
    print(f"WEEKS={WEEKS} RANK_LIMIT={RANK_LIMIT} HORIZONS={HORIZONS}")
    payload = build_backtest()
    write_outputs(payload)
    print(f"Wrote {safe_relative(OUT_BACKTEST_DIR / 'latest.json')}")
    print(f"eval_dates={payload['summary']['eval_date_count']} signals={payload['summary']['signal_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
