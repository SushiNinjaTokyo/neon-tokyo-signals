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
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from lib.agent_profiles_jp import AGENT_PROFILES, build_agent_scores
from lib.db import ROOT, connect_db, safe_rel, scalar
from lib.duckdb_schema import initialize_schema
from lib.feature_engine_jp import rebuild_features
from lib.market_regime_jp import attach_market_regime
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
START_DATE = (
    os.getenv("AGENT_SCORE_START_DATE")
    or os.getenv("VALUE_FEATURE_START_DATE")
    or os.getenv("AI_ARENA_START_DATE")
    or os.getenv("START_DATE")
    or ""
)
END_DATE = (
    os.getenv("AGENT_SCORE_END_DATE")
    or os.getenv("VALUE_FEATURE_END_DATE")
    or os.getenv("AI_ARENA_END_DATE")
    or os.getenv("END_DATE")
    or ""
)
FAIL_IF_RANGE_TOO_SMALL = os.getenv("AGENT_SCORE_FAIL_IF_RANGE_TOO_SMALL", "true").lower() in {"1", "true", "yes", "on"}



def first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def latest_equity_feature_date(conn) -> date | None:
    row = conn.execute(
        """
        WITH counts AS (
          SELECT f.date, COUNT(DISTINCT f.ticker) AS symbols
          FROM features_daily f
          JOIN universe_master u USING (ticker)
          WHERE COALESCE(LOWER(u.asset_type), 'equity') = 'equity'
            AND COALESCE(u.is_excluded, FALSE) = FALSE
          GROUP BY 1
        ), mx AS (SELECT MAX(symbols) AS max_symbols FROM counts)
        SELECT date
        FROM counts, mx
        WHERE symbols >= GREATEST(1, CAST(CEIL(max_symbols * 0.70) AS INTEGER))
        ORDER BY date DESC
        LIMIT 1
        """
    ).fetchone()
    return parse_date(row[0]) if row and row[0] is not None else None


def resolve_score_range(conn) -> tuple[str, str, dict[str, Any]]:
    start = START_DATE
    end = END_DATE
    year_raw = first_env("AGENT_SCORE_YEAR", "VALUE_FEATURE_YEAR", "AI_ARENA_YEAR", "ARENA_YEAR", "YEAR", default=str(datetime.utcnow().year))
    latest_date = latest_equity_feature_date(conn)
    if year_raw.lower() == "auto":
        year = int(latest_date.year if latest_date else datetime.utcnow().year)
    else:
        year = int(year_raw)
    if MODE == "range" and (not start or start.lower() == "auto"):
        start = f"{year}-01-01"
    if MODE == "range" and (not end or end.lower() == "auto") and latest_date:
        end = str(latest_date)
    return start, end, {"year": year, "start_date": start, "end_date": end, "latest_equity_feature_date": str(latest_date) if latest_date else None}

def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")
    tmp.replace(path)


def _table_exists(conn, table: str) -> bool:
    try:
        return conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [table]).fetchone()[0] > 0
    except Exception:
        return False


def load_feature_universe_frame(conn) -> pd.DataFrame:
    """Load all features joined with universe metadata, value features, and market regime.

    Market regime is intentionally attached at score-build time rather than
    stored in features_daily so the schema remains stable and the regime logic
    can be tuned independently from technical feature generation.
    """
    value_join = ""
    value_cols = ""
    if _table_exists(conn, "value_features_daily"):
        value_join = "LEFT JOIN value_features_daily vf ON f.ticker = vf.ticker AND f.date = vf.date"
        value_cols = """,
          vf.valuation_discount_score,
          vf.quality_guard_score,
          vf.earnings_stability_score,
          vf.shareholder_return_score,
          vf.re_rating_signal_score,
          vf.value_trap_penalty,
          vf.value_mispricing_score,
          vf.valuation_bucket,
          vf.value_status,
          vf.sector_33_code,
          vf.sector_33_name,
          vf.valuation_profile,
          vf.theme_tags_json,
          vf.sector_relative_per_discount,
          vf.sector_relative_pbr_discount,
          vf.sector_relative_psr_discount,
          vf.sector_relative_valuation_score,
          vf.sector_relative_quality_score,
          vf.sector_relative_value_confidence
        """
    df = conn.execute(
        f"""
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
          u.exclude_reason,
          u.source_detail,
          u.source_url
          {value_cols}
        FROM features_daily f
        LEFT JOIN universe_master u USING (ticker)
        {value_join}
        """
    ).df()
    return attach_market_regime(df, conn)


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



def date_coverage_diagnostics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or "date" not in df.columns:
        return {"date_count": 0}
    work = df.copy()
    work["_date"] = pd.to_datetime(work["date"], errors="coerce").dt.date
    if "asset_type" in work.columns:
        work = work[work["asset_type"].fillna("equity").astype(str).str.lower().eq("equity")]
    if "is_excluded" in work.columns:
        work = work[~work["is_excluded"].fillna(False).astype(bool)]
    denom = int(work["ticker"].nunique()) if "ticker" in work.columns else int(len(work))
    rows = []
    if "ticker" in work.columns:
        g = work.groupby("_date")["ticker"].nunique().sort_index()
    else:
        g = work.groupby("_date").size().sort_index()
    for d, n in g.tail(15).items():
        rows.append({"date": str(d), "symbols": int(n), "coverage_pct": round((n / denom * 100.0), 2) if denom else None})
    eligible_threshold_pct = float(os.getenv("AGENT_SCORE_MIN_DATE_COVERAGE_PCT", "70") or 70)
    eligible = [r for r in rows if (r.get("coverage_pct") or 0) >= eligible_threshold_pct]
    return {
        "date_count": int(len(g)),
        "equity_symbol_denominator": denom,
        "min_date_coverage_pct": eligible_threshold_pct,
        "recent_dates": rows,
        "latest_recent_eligible_date": eligible[-1]["date"] if eligible else None,
    }

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


def _score_date_count(scores: pd.DataFrame) -> int:
    if scores.empty or "date" not in scores.columns:
        return 0
    return int(pd.to_datetime(scores["date"], errors="coerce").dt.date.nunique())


def main() -> int:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)

    price_rows = int(scalar(conn, "SELECT COUNT(*) FROM prices_daily") or 0)
    if price_rows <= 0:
        raise SystemExit("prices_daily is empty. Run fetch_prices_jp.py with DuckDB enabled first.")

    feature_diag = rebuild_features(conn)
    df = load_feature_universe_frame(conn)

    score_start_date, score_end_date, range_runtime = resolve_score_range(conn)

    if MODE == "range":
        scores = score_range(df, score_start_date, score_end_date)
        s = parse_date(score_start_date) if score_start_date else None
        e = parse_date(score_end_date) if score_end_date else None
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

    score_date_count = _score_date_count(scores)
    trade_candidate_rows = int((scores.get("action") == "Trade").sum()) if not scores.empty and "action" in scores.columns else 0
    diagnostics = {
        "schema_version": "neon_tokyo_agent_scores_diagnostics_v1",
        "generated_at": generated_at,
        "duckdb_path": safe_rel(Path(PRICE_DUCKDB_PATH)),
        "mode": MODE,
        "range": range_runtime,
        "price_rows": price_rows,
        "feature_diagnostics": feature_diag,
        "score_date_coverage": date_coverage_diagnostics(df),
        "agent_score_rows": int(len(scores)),
        "agent_score_date_count": score_date_count,
        "trade_candidate_rows": trade_candidate_rows,
    }
    write_agent_score_outputs(scores, generated_at, diagnostics)
    print(f"Wrote {safe_rel(AGENT_SCORE_OUT_DIR / 'latest.json')}")
    print(f"Wrote {safe_rel(AGENT_SCORE_OUT_DIR / 'diagnostics.json')}")
    print(f"price_rows={price_rows}")
    print(f"feature_rows={feature_diag.get('feature_rows')}")
    print(f"agent_score_rows={len(scores)}")
    print(f"agent_score_date_count={score_date_count}")
    print(f"trade_candidate_rows={trade_candidate_rows}")
    if len(scores) == 0:
        print("No agent scores were generated. Check diagnostics.json for feature dates and universe filters.")
        return 2
    if MODE == "range" and FAIL_IF_RANGE_TOO_SMALL and score_date_count < 2:
        print("Range mode generated fewer than 2 score dates. This would create a cash-only Arena season.")
        return 3
    if MODE == "range" and FAIL_IF_RANGE_TOO_SMALL and trade_candidate_rows <= 0:
        print("Range mode generated no Trade candidates. Entry orders cannot be created.")
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
