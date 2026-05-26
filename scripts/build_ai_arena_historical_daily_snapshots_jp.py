from __future__ import annotations

"""
Build historical Daily JP signal snapshots for AI Arena from Daily Backtest output.

Why this exists
---------------
AI Arena simulation reads dated Daily snapshots under site/data/daily-jp/*.json.
Increasing AI_ARENA_LOOKBACK_DAYS alone only widens the price-calendar window;
it does not create historical signal dates.  This script converts the historical
signal rows already produced by scripts/backtest_daily_jp.py into Daily snapshot
files that AI Arena can consume deterministically.

Inputs
------
AI_ARENA_HISTORICAL_BACKTEST_JSON   default: site/data/backtest-daily-jp/latest.json
AI_ARENA_HISTORICAL_DAILY_DIR       default: site/data/daily-jp
AI_ARENA_HISTORICAL_START_DATE      optional YYYY-MM-DD filter
AI_ARENA_HISTORICAL_END_DATE        optional YYYY-MM-DD filter
AI_ARENA_HISTORICAL_OVERWRITE       true/false, default false
AI_ARENA_HISTORICAL_WRITE_LATEST    true/false, default false
AI_ARENA_HISTORICAL_MAX_ITEMS       optional cap per date, default 0 = no extra cap
OUT_DIR                             default: site

Outputs
-------
site/data/daily-jp/YYYY-MM-DD.json  Backtest-derived Daily snapshots
site/data/daily-jp/manifest.json    Rebuilt manifest including existing snapshots

Important
---------
By default this script does not overwrite existing dated Daily snapshots and does
not replace site/data/daily-jp/latest.json.  That prevents the live Daily page
from being accidentally rewound to an old backtest date.
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = (ROOT / OUT_DIR).resolve()

BACKTEST_JSON = Path(
    os.getenv(
        "AI_ARENA_HISTORICAL_BACKTEST_JSON",
        str(OUT_DIR / "data/backtest-daily-jp/latest.json"),
    )
)
DAILY_DIR = Path(
    os.getenv(
        "AI_ARENA_HISTORICAL_DAILY_DIR",
        str(OUT_DIR / "data/daily-jp"),
    )
)
if not DAILY_DIR.is_absolute():
    DAILY_DIR = (ROOT / DAILY_DIR).resolve()

START_DATE = os.getenv("AI_ARENA_HISTORICAL_START_DATE", "").strip()
END_DATE = os.getenv("AI_ARENA_HISTORICAL_END_DATE", "").strip()
OVERWRITE = os.getenv("AI_ARENA_HISTORICAL_OVERWRITE", "false").strip().lower() == "true"
WRITE_LATEST = os.getenv("AI_ARENA_HISTORICAL_WRITE_LATEST", "false").strip().lower() == "true"
MAX_ITEMS = int(os.getenv("AI_ARENA_HISTORICAL_MAX_ITEMS", "0") or "0")

JST = timezone(timedelta(hours=9))


def now_jst_iso() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    if not path.exists():
        raise SystemExit(f"Missing JSON: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Failed to read JSON {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {safe_rel(path)}")


def safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def valid_date(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()[:10]
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except Exception:
        return None


def in_range(date: str) -> bool:
    if START_DATE and date < START_DATE:
        return False
    if END_DATE and date > END_DATE:
        return False
    return True


def as_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def score_pts(item: dict[str, Any]) -> float:
    val = as_float(item.get("score_pts"), None)
    if val is not None:
        return val
    score = as_float(item.get("score"), 0.0) or 0.0
    return score * 10 if score <= 100 else score


def daily_item_from_backtest(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a backtest row into the field shape used by Daily JP snapshots."""
    date = valid_date(row.get("eval_date")) or ""
    latest_close = as_float(row.get("latest_close"), as_float(row.get("entry_close"), 0.0)) or 0.0
    pts = score_pts(row)
    score_0_100 = pts / 10 if pts > 100 else pts

    out = dict(row)
    out.update(
        {
            "as_of": date,
            "latest_date": date,
            "price": latest_close,
            "latest_close": latest_close,
            "source": row.get("source") or "backtest-daily-jp",
            "source_symbol": row.get("source_symbol") or row.get("symbol"),
            "currency": row.get("currency") or "JPY",
            "market": row.get("market") or "JP",
            "score": round(score_0_100, 4),
            "score_pts": int(round(pts)),
            "liquidity_score_0_1": row.get("liquidity_score_0_1"),
            "daily_snapshot_source": "backtest-daily-jp",
        }
    )
    # Avoid implying that future returns were known by the signal engine.
    # Keep them under a clearly diagnostic namespace for auditability only.
    diagnostics = {}
    for key in ("future_returns_pct", "alpha_vs_topix_pct", "alpha_quality", "worst_pullback_pct"):
        if key in out:
            diagnostics[key] = out.pop(key)
    if diagnostics:
        out["backtest_diagnostics"] = diagnostics
    return out


def build_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    by_triage: dict[str, int] = defaultdict(int)
    by_archetype: dict[str, int] = defaultdict(int)
    by_classification: dict[str, int] = defaultdict(int)
    by_bucket: dict[str, int] = defaultdict(int)
    by_risk: dict[str, int] = defaultdict(int)
    for item in items:
        by_triage[str(item.get("triage") or "Unknown")] += 1
        by_archetype[str(item.get("archetype") or "Unknown")] += 1
        by_classification[str(item.get("classification") or "Unknown")] += 1
        by_bucket[str(item.get("bucket") or "Unknown")] += 1
        by_risk[str(item.get("risk_level") or "Unknown")] += 1

    top = items[0] if items else {}
    return {
        "items_count": len(items),
        "top_symbol": top.get("symbol"),
        "top_name": top.get("name"),
        "top_score": top.get("score"),
        "top_score_pts": top.get("score_pts"),
        "top_classification": top.get("classification"),
        "top_triage": top.get("triage"),
        "top_archetype": top.get("archetype"),
        "trade": by_triage.get("Trade", 0),
        "watch": by_triage.get("Watch", 0),
        "ignore": by_triage.get("Ignore", 0),
        "by_triage": dict(sorted(by_triage.items())),
        "by_archetype": dict(sorted(by_archetype.items())),
        "by_classification": dict(sorted(by_classification.items())),
        "by_bucket": dict(sorted(by_bucket.items())),
        "by_risk": dict(sorted(by_risk.items())),
    }


def state_by_date(backtest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for state in backtest.get("date_states") or []:
        if not isinstance(state, dict):
            continue
        d = valid_date(state.get("eval_date"))
        if d:
            out[d] = state
    return out


def snapshot_for_date(
    date: str,
    items: list[dict[str, Any]],
    backtest: dict[str, Any],
    state: dict[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    state = state or {}
    items = sorted(items, key=lambda x: int(x.get("rank") or 999999))
    if MAX_ITEMS > 0:
        items = items[:MAX_ITEMS]
    normalized = [daily_item_from_backtest(x) for x in items]
    return {
        "schema_version": "daily-jp-v2",
        "generated_at": generated_at,
        "market": "JP",
        "timezone": "Asia/Tokyo",
        "source_prices": backtest.get("source_prices") or "site/data/prices-jp/latest.json",
        "source_prices_generated_at": backtest.get("source_prices_generated_at"),
        "methodology": {
            "name": "Backtest-derived historical Daily JP snapshot for AI Arena",
            "derived_from": "site/data/backtest-daily-jp/latest.json",
            "objective": "Provide historical signal snapshots so AI Arena can simulate a wider date range.",
            "news_included": False,
            "important_controls": [
                "Backtest future-return columns are moved to backtest_diagnostics and are not used as signal features.",
                "Existing live Daily snapshots are not overwritten unless AI_ARENA_HISTORICAL_OVERWRITE=true.",
            ],
        },
        "regime": state.get("regime") or (normalized[0].get("regime") if normalized else None),
        "regime_score": state.get("regime_score"),
        "regime_state": state.get("regime_state") or {},
        "market_pulse": [],
        "items": normalized,
        "all_items": normalized,
        "summary": build_summary(normalized),
        "failed": [],
        "historical_snapshot": {
            "enabled": True,
            "source": safe_rel(BACKTEST_JSON),
            "eval_date": date,
            "mode": backtest.get("mode"),
            "created_for": "ai-arena-simulation",
        },
    }


def rebuild_manifest() -> None:
    histories = []
    for path in sorted(DAILY_DIR.glob("*.json")):
        if path.name in {"latest.json", "manifest.json"}:
            continue
        d = valid_date(path.stem)
        if not d:
            continue
        try:
            snap = read_json(path)
        except SystemExit:
            continue
        summary = snap.get("summary") or {}
        histories.append(
            {
                "date": d,
                "path": safe_rel(path),
                "items_count": summary.get("items_count", len(snap.get("all_items") or snap.get("items") or [])),
                "trade": summary.get("trade", (summary.get("by_triage") or {}).get("Trade", 0)),
                "watch": summary.get("watch", (summary.get("by_triage") or {}).get("Watch", 0)),
                "ignore": summary.get("ignore", (summary.get("by_triage") or {}).get("Ignore", 0)),
                "top_symbol": summary.get("top_symbol"),
                "top_score": summary.get("top_score"),
                "top_score_pts": summary.get("top_score_pts"),
                "top_triage": summary.get("top_triage"),
                "top_archetype": summary.get("top_archetype"),
                "top_classification": summary.get("top_classification"),
                "historical_snapshot": bool((snap.get("historical_snapshot") or {}).get("enabled")),
            }
        )

    latest_date = histories[-1]["date"] if histories else None
    latest_path = DAILY_DIR / "latest.json"
    latest_payload = read_json(latest_path) if latest_path.exists() else {}
    live_latest_date = valid_date(latest_payload.get("date"))
    if not live_latest_date:
        for key in ("items", "all_items"):
            vals = latest_payload.get(key)
            if isinstance(vals, list) and vals:
                live_latest_date = valid_date(vals[0].get("latest_date") or vals[0].get("as_of"))
                if live_latest_date:
                    break

    manifest = {
        "schema_version": "daily-jp-manifest-v2",
        "generated_at": now_jst_iso(),
        "latest": safe_rel(latest_path) if latest_path.exists() else None,
        "latest_date": live_latest_date or latest_date,
        "history_count": len(histories),
        "history_start": histories[0]["date"] if histories else None,
        "history_end": histories[-1]["date"] if histories else None,
        "history": histories,
    }
    write_json(DAILY_DIR / "manifest.json", manifest)


def main() -> None:
    backtest = read_json(BACKTEST_JSON)
    if backtest.get("schema_version") != "backtest-daily-jp-v1":
        raise SystemExit(f"Unexpected backtest schema: {backtest.get('schema_version')}")

    rows_by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in backtest.get("items") or []:
        if not isinstance(row, dict):
            continue
        d = valid_date(row.get("eval_date"))
        if not d or not in_range(d):
            continue
        if not row.get("symbol"):
            continue
        rows_by_date[d].append(row)

    if not rows_by_date:
        raise SystemExit("No backtest rows matched the requested historical snapshot range.")

    states = state_by_date(backtest)
    generated_at = now_jst_iso()
    written = 0
    skipped = 0
    for d in sorted(rows_by_date):
        out_path = DAILY_DIR / f"{d}.json"
        if out_path.exists() and not OVERWRITE:
            skipped += 1
            print(f"Skip existing snapshot: {safe_rel(out_path)}")
            continue
        payload = snapshot_for_date(d, rows_by_date[d], backtest, states.get(d), generated_at)
        write_json(out_path, payload)
        written += 1

    if WRITE_LATEST:
        latest_date = sorted(rows_by_date)[-1]
        latest_payload = snapshot_for_date(latest_date, rows_by_date[latest_date], backtest, states.get(latest_date), generated_at)
        write_json(DAILY_DIR / "latest.json", latest_payload)

    rebuild_manifest()
    print(
        "AI Arena historical Daily snapshots:",
        f"source={safe_rel(BACKTEST_JSON)}",
        f"matched_dates={len(rows_by_date)}",
        f"written={written}",
        f"skipped_existing={skipped}",
        f"start={min(rows_by_date)}",
        f"end={max(rows_by_date)}",
    )


if __name__ == "__main__":
    main()
