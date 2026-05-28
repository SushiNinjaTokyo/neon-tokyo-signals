#!/usr/bin/env python3
from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = Path(os.getenv("INDEX_UNIVERSE_CSV", str(ROOT / "data" / "universe" / "jp_index_universe.csv")))
FALLBACK_CSV = Path(os.getenv("FALLBACK_UNIVERSE_CSV", str(ROOT / "data" / "universe_jp.csv")))
OUT_CSV = Path(os.getenv("OUT_UNIVERSE_CSV", str(ROOT / "data" / "universe" / "jp_duckdb_trial_300.csv")))
UNIVERSE_LIMIT = int(os.getenv("UNIVERSE_LIMIT", "300"))
CORE_TARGET = int(os.getenv("UNIVERSE_CORE_TARGET", "220"))
GROWTH_TARGET = int(os.getenv("UNIVERSE_GROWTH_TARGET", "60"))
STARTUP_TARGET = int(os.getenv("UNIVERSE_STARTUP_TARGET", "20"))


def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()


def truthy(v: Any) -> bool:
    return clean(v).lower() in {"1", "true", "yes", "y", "on"}


def normalize_ticker(row: dict[str, Any]) -> str:
    raw = clean(row.get("ticker") or row.get("symbol") or row.get("code"))
    raw = raw.upper()
    if not raw:
        return ""
    if raw.endswith(".T"):
        return raw
    return f"{raw}.T"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalize_index_row(row: dict[str, Any]) -> dict[str, str]:
    ticker = normalize_ticker(row)
    code = ticker[:-2] if ticker.endswith(".T") else ticker
    name = clean(row.get("name") or row.get("銘柄名") or row.get("issue_name") or ticker)
    is_topix500 = truthy(row.get("is_topix500")) or "TOPIX 500" in clean(row.get("sources"))
    is_prime150 = truthy(row.get("is_jpx_prime150"))
    is_growth250 = truthy(row.get("is_growth250"))
    is_startup100 = truthy(row.get("is_jpx_startup100"))
    market = clean(row.get("market") or row.get("市場") or ("Growth" if is_growth250 or is_startup100 else "Prime"))
    sector = clean(row.get("sector") or row.get("業種") or "")
    sources = clean(row.get("sources") or row.get("primary_source") or "")
    if is_growth250 or is_startup100 or "growth" in sources.lower():
        bucket = "Discovery"
        theme = "Japan Growth / Small Discovery"
        priority = "B"
    elif is_prime150:
        bucket = "Core"
        theme = "Japan Quality / Prime 150"
        priority = "A"
    elif is_topix500:
        bucket = "Core"
        theme = "Japan TOPIX 500"
        priority = "A"
    else:
        bucket = clean(row.get("bucket") or "Core")
        theme = clean(row.get("theme") or "Japan Equities")
        priority = clean(row.get("priority") or "B").upper()
    return {
        "symbol": ticker,
        "name": name,
        "theme": theme,
        "bucket": bucket,
        "priority": priority,
        "market": market,
        "sector": sector,
        "asset_type": "equity",
        "is_topix500": str(is_topix500).lower(),
        "is_jpx_prime150": str(is_prime150).lower(),
        "is_growth250": str(is_growth250).lower(),
        "is_jpx_startup100": str(is_startup100).lower(),
        "source_detail": sources,
        "source_url": clean(row.get("source_url")),
    }


def normalize_legacy_row(row: dict[str, Any]) -> dict[str, str]:
    ticker = normalize_ticker(row)
    return {
        "symbol": ticker,
        "name": clean(row.get("name") or ticker),
        "theme": clean(row.get("theme") or "Japan Equities"),
        "bucket": clean(row.get("bucket") or "Core"),
        "priority": clean(row.get("priority") or "B").upper(),
        "market": clean(row.get("market") or "JP"),
        "sector": clean(row.get("sector") or ""),
        "asset_type": clean(row.get("asset_type") or "equity"),
        "is_topix500": "false",
        "is_jpx_prime150": "false",
        "is_growth250": "true" if clean(row.get("bucket")).lower() == "discovery" else "false",
        "is_jpx_startup100": "false",
        "source_detail": "legacy_universe_jp",
        "source_url": "",
    }


def pick(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []

    def add(pool: list[dict[str, str]], limit: int) -> None:
        nonlocal out
        for r in pool:
            if len(out) >= UNIVERSE_LIMIT:
                return
            if sum(1 for x in out if x.get("bucket") == r.get("bucket")) >= limit and limit > 0:
                continue
            s = r["symbol"]
            if not s or s in seen:
                continue
            seen.add(s)
            out.append(r)

    core = [r for r in rows if r.get("bucket") == "Core"]
    growth = [r for r in rows if r.get("bucket") == "Discovery" and r.get("is_jpx_startup100") != "true"]
    startup = [r for r in rows if r.get("is_jpx_startup100") == "true"]
    other = [r for r in rows if r not in core and r not in growth and r not in startup]

    add(core, CORE_TARGET)
    add(growth, CORE_TARGET + GROWTH_TARGET)
    add(startup, CORE_TARGET + GROWTH_TARGET + STARTUP_TARGET)
    add(other, UNIVERSE_LIMIT)

    for r in rows:
        if len(out) >= UNIVERSE_LIMIT:
            break
        s = r["symbol"]
        if s and s not in seen:
            seen.add(s)
            out.append(r)
    return out[:UNIVERSE_LIMIT]


def main() -> int:
    source_rows = read_csv(SOURCE_CSV)
    source_used = SOURCE_CSV
    if source_rows:
        rows = [normalize_index_row(r) for r in source_rows]
    else:
        legacy_rows = read_csv(FALLBACK_CSV)
        if not legacy_rows:
            raise FileNotFoundError(f"No source universe CSV found: {SOURCE_CSV} or {FALLBACK_CSV}")
        source_used = FALLBACK_CSV
        rows = [normalize_legacy_row(r) for r in legacy_rows]
    rows = [r for r in rows if r.get("symbol")]
    selected = pick(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "symbol", "name", "theme", "bucket", "priority", "market", "sector", "asset_type",
        "is_topix500", "is_jpx_prime150", "is_growth250", "is_jpx_startup100", "source_detail", "source_url",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(selected)
    print("Build JP DuckDB trial universe")
    print(f"generated_at={datetime.utcnow().isoformat(timespec='seconds')}Z")
    print(f"source_used={source_used.relative_to(ROOT) if source_used.is_relative_to(ROOT) else source_used}")
    print(f"out_csv={OUT_CSV.relative_to(ROOT) if OUT_CSV.is_relative_to(ROOT) else OUT_CSV}")
    print(f"rows={len(selected)}")
    print(f"core={sum(1 for r in selected if r.get('bucket') == 'Core')}")
    print(f"discovery={sum(1 for r in selected if r.get('bucket') == 'Discovery')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
