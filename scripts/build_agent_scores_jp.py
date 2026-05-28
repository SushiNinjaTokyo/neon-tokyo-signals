#!/usr/bin/env python3
from __future__ import annotations

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

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()
AGENT_SCORE_OUT_DIR = OUT_DIR / "data" / "japan" / "agent-scores"
PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
AS_OF_DATE = os.getenv("AGENT_SCORE_AS_OF_DATE") or ""
TOP_N_PER_AGENT = int(os.getenv("AGENT_SCORE_TOP_N", "30"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def main() -> int:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)

    price_rows = int(scalar(conn, "SELECT COUNT(*) FROM prices_daily") or 0)
    if price_rows <= 0:
        raise SystemExit("prices_daily is empty. Run fetch_prices_jp.py with DuckDB enabled first.")

    feature_diag = rebuild_features(conn)

    df = conn.execute(
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
    scores = build_agent_scores(df, as_of_date=AS_OF_DATE or None)
    conn.execute("DELETE FROM agent_scores_daily")
    if not scores.empty:
        conn.register("_agent_scores_daily", scores)
        conn.execute("INSERT INTO agent_scores_daily SELECT * FROM _agent_scores_daily")
        conn.unregister("_agent_scores_daily")

    latest_date = None
    if not scores.empty:
        latest_date = str(pd.to_datetime(scores["date"]).max().date())

    agents_out = []
    for profile in AGENT_PROFILES:
        adf = scores[scores["agent_id"] == profile.id].copy() if not scores.empty else pd.DataFrame()
        adf = adf.sort_values("rank").head(TOP_N_PER_AGENT)
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
        agents_out.append({
            "agent_id": profile.id,
            "name": profile.name,
            "style_label": profile.style_label,
            "universe_rule": profile.universe_rule,
            "candidates_scored": int(len(scores[scores["agent_id"] == profile.id])) if not scores.empty else 0,
            "items": items,
        })

    diagnostics = {
        "schema_version": "neon_tokyo_agent_scores_diagnostics_v1",
        "generated_at": generated_at,
        "duckdb_path": safe_rel(Path(PRICE_DUCKDB_PATH)),
        "price_rows": price_rows,
        "feature_diagnostics": feature_diag,
        "agent_score_rows": int(len(scores)),
        "latest_date": latest_date,
        "agents": [
            {
                "agent_id": a["agent_id"],
                "name": a["name"],
                "candidates_scored": a["candidates_scored"],
                "top_items": len(a["items"]),
            }
            for a in agents_out
        ],
    }
    payload = {
        "schema_version": "neon_tokyo_agent_scores_v1",
        "generated_at": generated_at,
        "market": "Japan",
        "timezone": "Asia/Tokyo",
        "latest_date": latest_date,
        "top_n_per_agent": TOP_N_PER_AGENT,
        "agents": agents_out,
        "diagnostics_path": "site/data/japan/agent-scores/diagnostics.json",
    }

    latest_path = AGENT_SCORE_OUT_DIR / "latest.json"
    diag_path = AGENT_SCORE_OUT_DIR / "diagnostics.json"
    write_json(latest_path, payload)
    write_json(diag_path, diagnostics)
    print(f"Wrote {safe_rel(latest_path)}")
    print(f"Wrote {safe_rel(diag_path)}")
    print(f"price_rows={price_rows}")
    print(f"feature_rows={feature_diag.get('feature_rows')}")
    print(f"agent_score_rows={len(scores)}")
    if len(scores) == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
