#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from lib.db import ROOT, safe_rel

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()

PRICE_DUCKDB_PATH = os.getenv("PRICE_DUCKDB_PATH") or "data/cache/neon_tokyo_jp.duckdb"
AGENT_SCORE_DIR = OUT_DIR / "data" / "japan" / "agent-scores"
REVIEW_JSON = AGENT_SCORE_DIR / "review.json"
REVIEW_MD = AGENT_SCORE_DIR / "review.md"
PRICES_JSON = OUT_DIR / "data" / "prices-jp" / "latest.json"
UNIVERSE_CSV = ROOT / "data" / "universe" / "jp_duckdb_trial_300.csv"
INDEX_UNIVERSE_CSV = ROOT / "data" / "universe" / "jp_index_universe.csv"

YEAR_LIKE_RE = re.compile(r"^(?:19|20)\d{2}\.T$")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def safe_float(v: Any) -> float | None:
    try:
        x = float(v)
        if math.isfinite(x):
            return x
    except Exception:
        return None
    return None


def pct(n: int, d: int) -> float | None:
    return round(n / d * 100.0, 2) if d else None


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_review() -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    scores_payload = read_json(AGENT_SCORE_DIR / "latest.json")
    diag_payload = read_json(AGENT_SCORE_DIR / "diagnostics.json")
    prices_payload = read_json(PRICES_JSON)
    trial_universe = read_csv_rows(UNIVERSE_CSV)
    index_universe = read_csv_rows(INDEX_UNIVERSE_CSV)

    review: dict[str, Any] = {
        "schema_version": "neon_tokyo_agent_score_review_v1",
        "generated_at": generated_at,
        "duckdb_path": safe_rel(Path(PRICE_DUCKDB_PATH)),
        "summary": {},
        "agents": [],
        "overlaps": [],
        "universe_review": {},
        "price_json_review": {},
        "warnings": [],
    }

    con = duckdb.connect(str(PRICE_DUCKDB_PATH), read_only=True)

    counts = {
        "prices_daily_rows": con.execute("SELECT COUNT(*) FROM prices_daily").fetchone()[0],
        "features_daily_rows": con.execute("SELECT COUNT(*) FROM features_daily").fetchone()[0],
        "agent_scores_daily_rows": con.execute("SELECT COUNT(*) FROM agent_scores_daily").fetchone()[0],
        "distinct_price_tickers": con.execute("SELECT COUNT(DISTINCT ticker) FROM prices_daily").fetchone()[0],
        "distinct_agent_tickers": con.execute("SELECT COUNT(DISTINCT ticker) FROM agent_scores_daily").fetchone()[0],
    }
    score_date = con.execute("SELECT max(date) FROM agent_scores_daily").fetchone()[0]
    review["summary"] = {
        **counts,
        "score_date": str(score_date) if score_date else None,
        "agent_count": len(scores_payload.get("agents", [])),
        "price_symbols_success": prices_payload.get("symbols_success"),
        "price_symbols_failed": prices_payload.get("symbols_failed"),
        "public_price_json_mode": prices_payload.get("public_json_mode", prices_payload.get("price_store_mode")),
        "bars_omitted_in_public_json": bool(prices_payload.get("bars_omitted")),
    }

    agent_stats = con.execute(
        """
        SELECT
          agent_id,
          any_value(agent_name) AS agent_name,
          COUNT(*) AS candidates_scored,
          SUM(CASE WHEN action='Trade' THEN 1 ELSE 0 END) AS trade_count,
          SUM(CASE WHEN action='Watch' THEN 1 ELSE 0 END) AS watch_count,
          SUM(CASE WHEN action='Ignore' THEN 1 ELSE 0 END) AS ignore_count,
          MIN(normalized_score) AS min_score,
          AVG(normalized_score) AS avg_score,
          MAX(normalized_score) AS max_score
        FROM agent_scores_daily
        GROUP BY agent_id
        ORDER BY agent_id
        """
    ).df()

    top_rows = con.execute(
        """
        SELECT agent_id, agent_name, ticker, name, rank, normalized_score, action,
               reason_code_1, reason_code_2, reason_code_3, universe_bucket
        FROM agent_scores_daily
        WHERE rank <= 10
        ORDER BY agent_id, rank
        """
    ).df()

    for _, row in agent_stats.iterrows():
        aid = row["agent_id"]
        tops = top_rows[top_rows["agent_id"] == aid]
        top_items = []
        reason_counter: Counter[str] = Counter()
        for _, t in tops.iterrows():
            reasons = [str(t.get(f"reason_code_{i}") or "") for i in range(1, 4)]
            for r in reasons:
                if r:
                    reason_counter[r] += 1
            top_items.append({
                "rank": int(t["rank"]),
                "ticker": t["ticker"],
                "name": t["name"],
                "score": round(float(t["normalized_score"]), 4),
                "action": t["action"],
                "universe_bucket": t.get("universe_bucket") or "",
                "reason_codes": reasons,
            })
        item = {
            "agent_id": aid,
            "agent_name": row["agent_name"],
            "candidates_scored": int(row["candidates_scored"]),
            "trade_count": int(row["trade_count"]),
            "watch_count": int(row["watch_count"]),
            "ignore_count": int(row["ignore_count"]),
            "trade_pct": pct(int(row["trade_count"]), int(row["candidates_scored"])),
            "watch_pct": pct(int(row["watch_count"]), int(row["candidates_scored"])),
            "score_min": round(float(row["min_score"]), 4),
            "score_avg": round(float(row["avg_score"]), 4),
            "score_max": round(float(row["max_score"]), 4),
            "top_reason_codes": reason_counter.most_common(8),
            "top10": top_items,
        }
        if item["candidates_scored"] == 0:
            review["warnings"].append(f"{aid}: no candidates scored")
        if item["trade_count"] == 0:
            review["warnings"].append(f"{aid}: no Trade candidates")
        if item["score_max"] < 0.52:
            review["warnings"].append(f"{aid}: max score below Watch threshold")
        review["agents"].append(item)

    # Top ticker overlap across agents.  Some overlap is fine, but high overlap means personalities are not differentiated enough.
    ticker_agents: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for agent in review["agents"]:
        for item in agent["top10"]:
            ticker_agents[item["ticker"]].append({
                "agent_id": agent["agent_id"],
                "agent_name": agent["agent_name"],
                "rank": item["rank"],
                "score": item["score"],
            })
    overlaps = [
        {"ticker": t, "agent_count": len(v), "agents": sorted(v, key=lambda x: (x["rank"], x["agent_id"]))}
        for t, v in ticker_agents.items()
        if len(v) >= 2
    ]
    review["overlaps"] = sorted(overlaps, key=lambda x: (-x["agent_count"], x["ticker"]))[:30]

    failed = prices_payload.get("failures") or []
    weird_trial = []
    for r in trial_universe:
        ticker = str(r.get("symbol") or r.get("ticker") or "").strip().upper()
        name = str(r.get("name") or "").strip()
        if YEAR_LIKE_RE.match(ticker) or not name or name.upper() in {ticker, ticker.replace(".T", "")}:
            weird_trial.append({"ticker": ticker, "name": name, "bucket": r.get("bucket") or r.get("primary_source") or ""})
    weird_index = []
    for r in index_universe:
        ticker = str(r.get("ticker") or "").strip().upper()
        name = str(r.get("name") or "").strip()
        if YEAR_LIKE_RE.match(ticker) or not name or name.upper() in {ticker, ticker.replace(".T", "")}:
            weird_index.append({"ticker": ticker, "name": name, "source": r.get("sources") or r.get("primary_source") or ""})

    review["universe_review"] = {
        "trial_universe_rows": len(trial_universe),
        "index_universe_rows": len(index_universe),
        "failed_price_symbols": [
            {
                "symbol": f.get("symbol"),
                "name": f.get("name"),
                "reason": f.get("reason"),
                "source_errors": f.get("source_errors") or [],
            }
            for f in failed[:50]
        ],
        "failed_price_symbol_count": len(failed),
        "weird_trial_universe_rows": weird_trial[:50],
        "weird_index_universe_rows": weird_index[:50],
        "weird_trial_universe_count": len(weird_trial),
        "weird_index_universe_count": len(weird_index),
    }
    if weird_trial:
        review["warnings"].append(f"trial universe has {len(weird_trial)} suspicious rows")
    if failed:
        review["warnings"].append(f"price fetch failed for {len(failed)} symbols")

    latest_size = PRICES_JSON.stat().st_size if PRICES_JSON.exists() else 0
    review["price_json_review"] = {
        "latest_json_path": safe_rel(PRICES_JSON),
        "latest_json_size_bytes": latest_size,
        "latest_json_size_mb": round(latest_size / 1024 / 1024, 3),
        "dated_price_json_files": [safe_rel(p) for p in sorted((OUT_DIR / "data" / "prices-jp").glob("20??-??-??.json"))],
    }
    if latest_size > 10 * 1024 * 1024:
        review["warnings"].append("prices-jp/latest.json is still larger than 10MB")
    if review["price_json_review"]["dated_price_json_files"]:
        review["warnings"].append("dated prices-jp JSON files still exist")

    return review


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_markdown(path: Path, review: dict[str, Any]) -> None:
    lines = []
    s = review.get("summary", {})
    lines.append("# Neon Tokyo Agent Score Review")
    lines.append("")
    lines.append(f"Generated: {review.get('generated_at')}")
    lines.append(f"Score date: {s.get('score_date')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Price rows: {s.get('prices_daily_rows')}")
    lines.append(f"- Feature rows: {s.get('features_daily_rows')}")
    lines.append(f"- Agent score rows: {s.get('agent_scores_daily_rows')}")
    lines.append(f"- Price symbols: success={s.get('price_symbols_success')} failed={s.get('price_symbols_failed')}")
    lines.append(f"- Public price JSON mode: {s.get('public_price_json_mode')}")
    lines.append("")
    lines.append("## Agent Stats")
    lines.append("")
    lines.append("| Agent | Candidates | Trade | Watch | Max | Avg |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for a in review.get("agents", []):
        lines.append(f"| {a['agent_name']} | {a['candidates_scored']} | {a['trade_count']} | {a['watch_count']} | {a['score_max']} | {a['score_avg']} |")
    lines.append("")
    if review.get("warnings"):
        lines.append("## Warnings")
        lines.append("")
        for w in review["warnings"]:
            lines.append(f"- {w}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    review = build_review()
    write_json(REVIEW_JSON, review)
    write_markdown(REVIEW_MD, review)
    print(f"Wrote {safe_rel(REVIEW_JSON)}")
    print(f"Wrote {safe_rel(REVIEW_MD)}")
    print(f"warnings={len(review.get('warnings', []))}")
    for w in review.get("warnings", [])[:10]:
        print(f"WARNING {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
