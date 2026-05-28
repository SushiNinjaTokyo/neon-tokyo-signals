#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.getenv("OUT_DIR", str(ROOT / "site")))
if not OUT_DIR.is_absolute():
    OUT_DIR = ROOT / OUT_DIR
OUT_DIR = OUT_DIR.resolve()

PRICE_DIR = OUT_DIR / "data" / "prices-jp"
MAX_LATEST_MB = float(os.getenv("MAX_PRICES_LATEST_MB", "25"))
DELETE_DATED = os.getenv("DELETE_DATED_PRICES_JSON", "true").strip().lower() in {"1", "true", "yes", "on"}
DRY_RUN = os.getenv("DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "on"}


def safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    PRICE_DIR.mkdir(parents=True, exist_ok=True)

    removed: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []

    dated = sorted(PRICE_DIR.glob("20??-??-??.json"))
    if DELETE_DATED:
        for p in dated:
            info = {"path": safe_rel(p), "size_bytes": p.stat().st_size if p.exists() else 0, "reason": "dated_price_snapshot"}
            removed.append(info)
            if not DRY_RUN:
                p.unlink(missing_ok=True)
    else:
        for p in dated:
            kept.append({"path": safe_rel(p), "size_bytes": p.stat().st_size if p.exists() else 0, "reason": "dated_deletion_disabled"})

    latest = PRICE_DIR / "latest.json"
    latest_size = latest.stat().st_size if latest.exists() else 0
    latest_mb = latest_size / 1024 / 1024
    latest_payload = read_json(latest)
    latest_mode = latest_payload.get("public_json_mode") or latest_payload.get("price_store_mode")
    latest_has_bars = False
    for item in latest_payload.get("items", [])[:5]:
        if item.get("bars"):
            latest_has_bars = True
            break

    warnings: list[str] = []
    if latest.exists() and latest_mb > MAX_LATEST_MB:
        warnings.append(f"latest.json is still large: {latest_mb:.2f}MB > {MAX_LATEST_MB:.2f}MB")
    if latest_has_bars:
        warnings.append("latest.json still appears to contain historical bars")

    manifest = read_json(PRICE_DIR / "manifest.json")
    if manifest:
        manifest["pruned_at"] = generated_at
        manifest["dated_snapshots_pruned"] = DELETE_DATED
        manifest["history"] = [] if DELETE_DATED else manifest.get("history", [])
        if not DRY_RUN:
            (PRICE_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "schema_version": "prices_jp_prune_report_v1",
        "generated_at": generated_at,
        "dry_run": DRY_RUN,
        "price_dir": safe_rel(PRICE_DIR),
        "delete_dated": DELETE_DATED,
        "max_latest_mb": MAX_LATEST_MB,
        "latest_json": {
            "path": safe_rel(latest),
            "exists": latest.exists(),
            "size_bytes": latest_size,
            "size_mb": round(latest_mb, 3),
            "mode": latest_mode,
            "has_bars_sample": latest_has_bars,
        },
        "removed": removed,
        "kept": kept,
        "warnings": warnings,
    }
    report_path = PRICE_DIR / "prune-report.json"
    if not DRY_RUN:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
