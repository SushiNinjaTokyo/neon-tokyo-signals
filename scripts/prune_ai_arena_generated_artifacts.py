#!/usr/bin/env python3
from __future__ import annotations

"""Prune heavy generated artifacts while preserving public AI Arena outputs.

This script is safe-by-default: it removes only known heavy generated files and
cache artifacts. It does not delete source scripts, templates, universe CSVs, or
agent images.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from lib.db import ROOT, safe_rel

OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
MAX_PRICE_LATEST_MB = float(os.getenv("MAX_PRICE_LATEST_JSON_MB", "5"))
MAX_AI_ARENA_JSON_MB = float(os.getenv("MAX_AI_ARENA_JSON_MB", "20"))


def size_mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024 if path.exists() else 0.0


def remove_file(path: Path, removed: list[dict]) -> None:
    if not path.exists() or not path.is_file():
        return
    removed.append({"path": safe_rel(path), "size_mb": round(size_mb(path), 4)})
    if not DRY_RUN:
        path.unlink()



def compact_prices_latest(path: Path, removed: list[dict], warnings: list[str]) -> None:
    """Rewrite legacy full prices latest.json into summary mode in place.

    This handles the case where an earlier workflow committed a 40-50MB full
    OHLCV payload.  The file is not deleted because downstream code expects the
    path to exist; instead we remove per-symbol historical bars and keep latest
    metrics only.
    """
    if not path.exists() or not path.is_file():
        return
    before = size_mb(path)
    if before <= MAX_PRICE_LATEST_MB:
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append(f"{safe_rel(path)} is too large and could not be parsed for compaction: {exc}")
        return
    items = payload.get("items") or []
    if not isinstance(items, list) or not items:
        warnings.append(f"{safe_rel(path)} is too large but has no compactable items[]")
        return

    compact_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        bars = item.get("bars") or []
        latest_bar = bars[-1] if isinstance(bars, list) and bars else item.get("latest_bar")
        compact_items.append({
            "symbol": item.get("symbol"),
            "name": item.get("name"),
            "theme": item.get("theme"),
            "bucket": item.get("bucket"),
            "priority": item.get("priority"),
            "asset_type": item.get("asset_type"),
            "pulse_label": item.get("pulse_label"),
            "market": item.get("market"),
            "currency": item.get("currency"),
            "source": item.get("source"),
            "source_symbol": item.get("source_symbol"),
            "bars_count": item.get("bars_count"),
            "date_start": item.get("date_start"),
            "date_end": item.get("date_end"),
            "is_partial": item.get("is_partial"),
            "warnings": item.get("warnings") or [],
            "source_errors": item.get("source_errors") or [],
            "metrics": item.get("metrics") or {},
            "latest_bar": latest_bar,
            "bars_omitted": True,
        })
    payload["items"] = compact_items
    payload["equities"] = [x for x in compact_items if x.get("asset_type") == "equity"]
    payload["market_pulse"] = [x for x in compact_items if x.get("asset_type") == "market_pulse"]
    payload["public_json_mode"] = "summary"
    payload["bars_omitted"] = True
    if not DRY_RUN:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after = before if DRY_RUN else size_mb(path)
    removed.append({"path": safe_rel(path), "action": "compact_prices_latest", "before_mb": round(before, 4), "after_mb": round(after, 4)})

def main() -> int:
    removed: list[dict] = []
    warnings: list[str] = []

    # DuckDB and binary cache files must never be committed.
    for pattern in ["data/cache/*.duckdb", "data/cache/*.duckdb.wal", "data/cache/*.duckdb.tmp", "data/cache/*.parquet", "data/cache/*.tmp"]:
        for p in ROOT.glob(pattern):
            remove_file(p, removed)

    # Dated price JSONs are heavy and not required for the static site.
    prices_dir = OUT_DIR / "data" / "prices-jp"
    if prices_dir.exists():
        for p in prices_dir.glob("20??-??-??.json"):
            remove_file(p, removed)

    latest_prices = prices_dir / "latest.json"
    compact_prices_latest(latest_prices, removed, warnings)
    if latest_prices.exists() and size_mb(latest_prices) > MAX_PRICE_LATEST_MB:
        warnings.append(f"{safe_rel(latest_prices)} is {size_mb(latest_prices):.2f} MB; expected <= {MAX_PRICE_LATEST_MB} MB")

    # Keep only latest diagnostics/review for agent scores. Dated snapshots are not public contract.
    agent_dir = OUT_DIR / "data" / "japan" / "agent-scores"
    if agent_dir.exists():
        keep = {"latest.json", "diagnostics.json", "review.md", "review.json"}
        for p in agent_dir.glob("*.json"):
            if p.name not in keep and p.name.startswith("20"):
                remove_file(p, removed)
        for p in agent_dir.glob("review-*.json"):
            remove_file(p, removed)
        for p in agent_dir.glob("review-*.md"):
            remove_file(p, removed)

    # Soft guard on AI Arena public JSON size.
    arena_dir = OUT_DIR / "data" / "japan" / "ai-arena"
    if arena_dir.exists():
        for p in arena_dir.rglob("*.json"):
            if size_mb(p) > MAX_AI_ARENA_JSON_MB:
                warnings.append(f"{safe_rel(p)} is {size_mb(p):.2f} MB; expected <= {MAX_AI_ARENA_JSON_MB} MB")

    report = {
        "schema_version": "ai_arena_prune_report_v1",
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "dry_run": DRY_RUN,
        "removed": removed,
        "warnings": warnings,
    }
    out = OUT_DIR / "data" / "japan" / "ai-arena" / "prune-report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"removed={len(removed)} dry_run={DRY_RUN}")
    for w in warnings:
        print("WARNING:", w)
    return 1 if warnings and os.getenv("FAIL_ON_SIZE_WARNING", "false").lower() == "true" else 0


if __name__ == "__main__":
    raise SystemExit(main())
