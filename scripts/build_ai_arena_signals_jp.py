#!/usr/bin/env python3
from __future__ import annotations

"""Build Agent "today's picks" for the Arena Signals page.

This script uses DuckDB agent_scores_daily and features_daily. GPT commentary is
optional and cached in agent_pick_notes_daily. Numeric metrics always come from
Python/DuckDB, never from GPT.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from lib.db import ROOT, connect_db, safe_rel
from lib.duckdb_schema import initialize_schema
from lib.arena_exporter_jp import write_json
from lib.company_fundamentals_jp import fetch_company_snapshot, upsert_company_from_universe
from lib.gpt_signal_notes_jp import build_fallback_notes, generate_signal_notes, gpt_enabled

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()
PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
PICKS_PER_AGENT = int(os.getenv("SIGNALS_PICKS_PER_AGENT", "5"))
NOTE_VERSION = os.getenv("SIGNAL_NOTE_VERSION", "v1")


def load_agents() -> list[dict[str, Any]]:
    with (ROOT / "data" / "agents" / "jp_agents.yml").open("r", encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("agents", []) or []


def latest_score_date(conn) -> str | None:
    row = conn.execute("SELECT MAX(date) FROM agent_scores_daily").fetchone()
    return str(row[0]) if row and row[0] else None


def get_or_make_notes(conn, *, score_date: str, agent: dict[str, Any], pick: dict[str, Any], company: dict[str, Any]) -> dict[str, str]:
    cached = conn.execute(
        """
        SELECT company_brief_en, signal_thesis_en, valuation_comment_en, risk_comment_en
        FROM agent_pick_notes_daily
        WHERE date = ? AND agent_id = ? AND ticker = ? AND note_version = ?
        LIMIT 1
        """,
        [score_date, agent["agent_id"], pick["ticker"], NOTE_VERSION],
    ).fetchone()
    if cached:
        return dict(zip(["company_brief_en", "signal_thesis_en", "valuation_comment_en", "risk_comment_en"], cached))
    metrics = pick.get("metrics") or {}
    fundamentals = company.get("fundamentals") or {}
    prompt_payload = {
        "ticker": pick["ticker"],
        "company_name": company.get("name_en") or pick.get("name") or pick["ticker"],
        "agent_name": agent.get("name"),
        "signal_type": pick.get("signal_type"),
        "metrics": {**metrics, **fundamentals},
    }
    notes = generate_signal_notes(prompt_payload) if gpt_enabled() else build_fallback_notes(
        company_name=prompt_payload["company_name"], agent_name=prompt_payload["agent_name"], signal_type=prompt_payload["signal_type"], metrics=prompt_payload["metrics"]
    )
    conn.execute(
        """
        INSERT INTO agent_pick_notes_daily
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [score_date, agent["agent_id"], pick["ticker"], NOTE_VERSION, notes["company_brief_en"], notes["signal_thesis_en"], notes["valuation_comment_en"], notes["risk_comment_en"], "gpt" if gpt_enabled() else "template", datetime.utcnow()],
    )
    return notes


def main() -> int:
    conn = connect_db(PRICE_DUCKDB_PATH)
    initialize_schema(conn)
    upsert_company_from_universe(conn)
    agents = load_agents()
    score_date = latest_score_date(conn)
    if not score_date:
        raise SystemExit("agent_scores_daily is empty. Run build_agent_scores_jp.py first.")
    generated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    out_agents = []
    for agent in agents:
        aid = agent["agent_id"]
        rows = conn.execute(
            """
            SELECT s.*, f.return_5d_pct, f.return_20d_pct, f.return_60d_pct, f.volume_ratio_20d,
                   f.rsi_14, f.avg_traded_value_20d_jpy, f.price_vs_ma20_pct, f.price_vs_ma50_pct,
                   f.trend_score_daily, f.trend_score_weekly_proxy, f.liquidity_score, f.risk_score
            FROM agent_scores_daily s
            LEFT JOIN features_daily f ON s.ticker = f.ticker AND s.date = f.date
            WHERE s.date = ? AND s.agent_id = ? AND s.action IN ('Trade','Watch')
            ORDER BY CASE WHEN s.action = 'Trade' THEN 0 ELSE 1 END, s.rank
            LIMIT ?
            """,
            [score_date, aid, PICKS_PER_AGENT],
        ).df()
        picks = []
        for _, r in rows.iterrows():
            metrics = {
                "return_5d_pct": r.get("return_5d_pct"),
                "return_20d_pct": r.get("return_20d_pct"),
                "return_60d_pct": r.get("return_60d_pct"),
                "volume_ratio_20d": r.get("volume_ratio_20d"),
                "rsi_14": r.get("rsi_14"),
                "avg_traded_value_20d_jpy": r.get("avg_traded_value_20d_jpy"),
                "liquidity_score": r.get("liquidity_score"),
                "risk_score": r.get("risk_score"),
            }
            pick = {
                "ticker": r["ticker"],
                "name": r.get("name") or r["ticker"],
                "action": r["action"],
                "rank": int(r["rank"]),
                "score": round(float(r["normalized_score"]), 4),
                "signal_type": str(r.get("reason_code_1") or "Signal").replace("_", " ").title(),
                "reason": r.get("reason_text") or "",
                "metrics": {k: (None if v != v else v) for k, v in metrics.items()},
            }
            company = fetch_company_snapshot(conn, pick["ticker"])
            notes = get_or_make_notes(conn, score_date=score_date, agent=agent, pick=pick, company=company)
            pick["company"] = company
            pick["notes"] = notes
            picks.append(pick)
        out_agents.append({**agent, "picks": picks})
    payload = {"schema_version": "ai_arena_signals_v1", "generated_at": generated_at, "score_date": score_date, "gpt_notes_enabled": gpt_enabled(), "agents": out_agents}
    out_path = OUT_DIR / "data" / "japan" / "ai-arena" / "signals" / "latest.json"
    write_json(out_path, payload)
    print(f"Wrote {safe_rel(out_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
