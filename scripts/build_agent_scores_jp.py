#!/usr/bin/env python3
from __future__ import annotations

"""Build AI agent scores from DuckDB features.

This script supports two modes:

- AGENT_SCORE_MODE=latest: build the latest available score date, same as the
  prior implementation.
- AGENT_SCORE_MODE=range: rebuild scores for every trading date in a date range.

Range mode is required for the AI Arena calendar-year season engine. The key
anti-leakage principle is simple: each score row is created from features whose
`date` is the same signal date. The feature engine itself uses rolling windows
on historical prices, so future prices are not needed for a given signal date.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from lib.agent_profiles_jp import AGENT_PROFILES, build_agent_scores
from lib.db import ROOT, connect_db, safe_rel, scalar
from lib.duckdb_schema import initialize_schema
from lib.feature_engine_jp import rebuild_features
from lib.arena_calendar_jp import parse_date

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()
AGENT_SCORE_OUT_DIR = OUT_DIR / "data" / "japan" / "agent-scores"
PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
AS_OF_DATE = os.getenv("AGENT_SCORE_AS_OF_DATE") or ""
TOP_N_PER_AGENT = int(os.getenv("AGENT_SCORE_TOP_N", "30"))
MODE = os.getenv("AGENT_SCORE_MODE", "latest").lower().strip()
START_DATE = os.getenv("AGENT_SCORE_START_DATE") or os.getenv("START_DATE") or ""
END_DATE = os.getenv("AGENT_SCORE_END_DATE") or os.getenv("END_DATE") or ""


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")
    tmp.replace(path)


def load_feature_universe_frame(conn) -> pd.DataFrame:
    """Load all features joined with universe metadata."""
    return conn.execute(
        """
        SELECT
          f.*,
          u.name,
          u.market,
          u.sector,
          u.theme,
          u.bucket,
          u.priority,
          u.asset_type,
          u.is_topix500,
          u.is_jpx_prime150,
          u.is_growth250,
          u.is_jpx_startup100,
          u.is_core,
          u.is_growth,
          u.is_small_discovery,
          u.is_value_candidate,
          u.is_excluded,
          u.exclude_reason
        FROM features_daily f
        LEFT JOIN universe_master u USING (ticker)
        """
    ).df()


def score_range(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """Score each date independently by reusing build_agent_scores with cutoff."""
    if df.empty:
        return pd.DataFrame()
    work = df.copy()
    work["_date"] = pd.to_datetime(work["date"], errors="coerce")
    s = parse_date(start_date) if start_date else None
    e = parse_date(end_date) if end_date else None
    dates = sorted(d.date() for d in work["_date"].dropna().unique())
    if s:
        dates = [d for d in dates if d >= s]
    if e:
        dates = [d for d in dates if d <= e]

    frames = []
    # build_agent_scores picks the latest eligible date <= as_of_date from the
    # provided frame. Passing the full historical frame plus as_of_date keeps the
    # behavior aligned with latest mode and avoids future-date selection.
    for d in dates:
        scored = build_agent_scores(df, as_of_date=str(d))
        if not scored.empty:
            # Defensive guard: only keep rows for the intended signal date.
            scored = scored[pd.to_datetime(scored["date"], errors="coerce").dt.date == d]
            if not scored.empty:
                frames.append(scored)
    if not frames:
        return build_agent_scores(pd.DataFrame())
    return pd.concat(frames, ignore_index=True)


def write_agent_score_outputs(scores: pd.DataFrame, generated_at: str, diagnostics: dict[str, Any]) -> None:
    latest_date = None
    if not scores.empty:
        latest_date = str(pd.to_datetime(scores["date"]).max().date())

    required_score_columns = {"agent_id", "rank"}
    agents_out = []
    for profile in AGENT_PROFILES:
        if not scores.empty and required_score_columns.issubset(scores.columns):
            latest_scores = scores[pd.to_datetime(scores["date"], errors="coerce").dt.date == pd.to_datetime(latest_date).date()] if latest_date else scores
            adf = latest_scores[latest_scores["agent_id"] == profile.id].copy()
            adf = adf.sort_values("rank").head(TOP_N_PER_AGENT)
        else:
            adf = pd.DataFrame()
        items = []
        for _, r in adf.iterrows():
            items.append({
                "rank": int(r["rank"]),
                "ticker": r["ticker"],
                "name": r.get("name") or r["ticker"],
                "score": round(float(r["normalized_score"]), 4),
                "score_pts": round(float(r["normalized_score"]) * 100, 1),
                "action": r["action"],
                "signal_strength": r["signal_strength"],
                "universe_bucket": r.get("universe_bucket") or "",
                "reason_codes": [r.get("reason_code_1"), r.get("reason_code_2"), r.get("reason_code_3")],
                "reason": r.get("reason_text") or "",
            })
        count = int(len(scores[scores["agent_id"] == profile.id])) if not scores.empty and "agent_id" in scores.columns else 0
        agents_out.append({
            "agent_id": profile.id,
            "name": profile.name,
            "style_label": profile.style_label,
            "universe_rule": profile.universe_rule,
            "candidates_scored": count,
            "items": items,
        })

    payload = {
        "schema_version": "neon_tokyo_agent_scores_v1",
        "generated_at": generated_at,
        "market": "Japan",
        "timezone": "Asia/Tokyo",
        "mode": MODE,
        "latest_date": latest_date,
        "top_n_per_agent": TOP_N_PER_AGENT,
        "agents": agents_out,
        "diagnostics_path": "site/data/japan/agent-scores/diagnostics.json",
    }
    diagnostics["latest_date"] = latest_date
    diagnostics["agents"] = [{"agent_id": a["agent_id"], "name": a["name"], "candidates_scored": a["candidates_scored"], "top_items": len(a["items"])} for a in agents_out]
    diagnostics["score_columns"] = list(scores.columns) if not scores.empty else []
    write_json(AGENT_SCORE_OUT_DIR / "latest.json", payload)
    write_json(AGENT_SCORE_OUT_DIR / "diagnostics.json", diagnostics)


def main() -> int:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)

    price_rows = int(scalar(conn, "SELECT COUNT(*) FROM prices_daily") or 0)
    if price_rows <= 0:
        raise SystemExit("prices_daily is empty. Run fetch_prices_jp.py with DuckDB enabled first.")

    feature_diag = rebuild_features(conn)
    df = load_feature_universe_frame(conn)

    if MODE == "range":
        scores = score_range(df, START_DATE, END_DATE)
        s = parse_date(START_DATE) if START_DATE else None
        e = parse_date(END_DATE) if END_DATE else None
        if s and e:
            conn.execute("DELETE FROM agent_scores_daily WHERE date BETWEEN ? AND ?", [s, e])
        elif s:
            conn.execute("DELETE FROM agent_scores_daily WHERE date >= ?", [s])
        elif e:
            conn.execute("DELETE FROM agent_scores_daily WHERE date <= ?", [e])
        else:
            conn.execute("DELETE FROM agent_scores_daily")
    else:
        scores = build_agent_scores(df, as_of_date=AS_OF_DATE or None)
        # Latest mode intentionally replaces the score table, matching the prior
        # implementation used by the trial Action.
        conn.execute("DELETE FROM agent_scores_daily")

    if not scores.empty:
        conn.register("_agent_scores_daily", scores)
        conn.execute("INSERT INTO agent_scores_daily SELECT * FROM _agent_scores_daily")
        conn.unregister("_agent_scores_daily")

    diagnostics = {
        "schema_version": "neon_tokyo_agent_scores_diagnostics_v1",
        "generated_at": generated_at,
        "duckdb_path": safe_rel(Path(PRICE_DUCKDB_PATH)),
        "mode": MODE,
        "range": {"start_date": START_DATE, "end_date": END_DATE},
        "price_rows": price_rows,
        "feature_diagnostics": feature_diag,
        "agent_score_rows": int(len(scores)),
    }
    write_agent_score_outputs(scores, generated_at, diagnostics)
    print(f"Wrote {safe_rel(AGENT_SCORE_OUT_DIR / 'latest.json')}")
    print(f"Wrote {safe_rel(AGENT_SCORE_OUT_DIR / 'diagnostics.json')}")
    print(f"price_rows={price_rows}")
    print(f"feature_rows={feature_diag.get('feature_rows')}")
    print(f"agent_score_rows={len(scores)}")
    if len(scores) == 0:
        print("No agent scores were generated. Check diagnostics.json for feature dates and universe filters.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
