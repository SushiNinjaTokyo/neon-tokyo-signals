#!/usr/bin/env python3
from __future__ import annotations

"""Build the canonical JP AI Arena universe CSV.

The historical filename remains ``jp_duckdb_trial_300.csv`` for compatibility,
but the operational limit is no longer a hard 300-stock trial.  The current
production contract is:

- select up to ``UNIVERSE_LIMIT`` equities, default 1000;
- always prioritize ``data/universe/jp_manual_theme_includes.csv``;
- never let the legacy 300 limit accidentally remove manual theme names;
- write diagnostics so scheduled runs are auditable.

Manual include rows are validated and included first.  Invalid rows are rejected
from the generated universe, but the source CSV is never rewritten by this
script.  That prevents transient data/source issues from silently deleting a
human-curated ticker.
"""

import csv
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = Path(os.getenv("INDEX_UNIVERSE_CSV", str(ROOT / "data" / "universe" / "jp_index_universe.csv")))
FALLBACK_CSV = Path(os.getenv("FALLBACK_UNIVERSE_CSV", str(ROOT / "data" / "universe_jp.csv")))
MANUAL_INCLUDE_CSV = Path(os.getenv("MANUAL_THEME_INCLUDE_CSV", str(ROOT / "data" / "universe" / "jp_manual_theme_includes.csv")))
OUT_CSV = Path(os.getenv("OUT_UNIVERSE_CSV", str(ROOT / "data" / "universe" / "jp_duckdb_trial_300.csv")))
DIAG_JSON = Path(os.getenv("UNIVERSE_DIAGNOSTICS_JSON", str(ROOT / "site" / "data" / "japan" / "universe" / "jp_duckdb_trial_300_diagnostics.json")))

# Production upper bound.  The name UNIVERSE_LIMIT is kept because existing
# workflows already use it.  It now means "maximum final equity universe rows".
UNIVERSE_LIMIT = int(os.getenv("UNIVERSE_LIMIT", "1000") or "1000")
CORE_TARGET = int(os.getenv("UNIVERSE_CORE_TARGET", "520") or "520")
GROWTH_TARGET = int(os.getenv("UNIVERSE_GROWTH_TARGET", "320") or "320")
STARTUP_TARGET = int(os.getenv("UNIVERSE_STARTUP_TARGET", "160") or "160")
STRICT_INDEX_UNIVERSE = os.getenv("STRICT_INDEX_UNIVERSE", "true").strip().lower() in {"1", "true", "yes", "y", "on"}
ALLOW_LEGACY_FALLBACK = os.getenv("ALLOW_LEGACY_FALLBACK", "false").strip().lower() in {"1", "true", "yes", "y", "on"}
FAIL_IF_MANUAL_REJECTED = os.getenv("FAIL_IF_MANUAL_REJECTED", "false").strip().lower() in {"1", "true", "yes", "y", "on"}

FIELDNAMES = [
    "symbol", "name", "theme", "bucket", "priority", "market", "sector", "asset_type",
    "is_topix500", "is_jpx_prime150", "is_growth250", "is_jpx_startup100", "source_detail", "source_url",
]

TICKER_RE = re.compile(r"^(?:\d{4}|\d{3}[A-Z]|\d{2}[A-Z]{2}|[A-Z]\d{3})\.T$")


@dataclass(frozen=True)
class ManualReject:
    row_number: int
    symbol: str
    name: str
    reason: str


def safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()


def truthy(v: Any) -> bool:
    return clean(v).lower() in {"1", "true", "yes", "y", "on"}


def normalize_bool(v: Any) -> str:
    return "true" if truthy(v) else "false"


def normalize_ticker(row_or_value: dict[str, Any] | str | None) -> str:
    if isinstance(row_or_value, dict):
        raw = clean(row_or_value.get("symbol") or row_or_value.get("ticker") or row_or_value.get("code"))
    else:
        raw = clean(row_or_value)
    raw = raw.upper().replace(" ", "")
    if not raw:
        return ""
    if raw.endswith(".JP"):
        raw = raw[:-3] + ".T"
    if raw.endswith(".T"):
        return raw
    return f"{raw}.T"


def ticker_is_valid(symbol: str) -> bool:
    return bool(TICKER_RE.match(symbol))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalize_index_row(row: dict[str, Any]) -> dict[str, str]:
    ticker = normalize_ticker(row)
    name = clean(row.get("name") or row.get("銘柄名") or row.get("issue_name") or ticker)
    sources = clean(row.get("sources") or row.get("primary_source") or row.get("source_detail") or "")
    sources_l = sources.lower()
    is_topix500 = truthy(row.get("is_topix500")) or "topix500" in sources_l or "topix 500" in sources_l
    is_prime150 = truthy(row.get("is_jpx_prime150")) or "prime150" in sources_l or "prime 150" in sources_l
    is_growth250 = truthy(row.get("is_growth250")) or "growth250" in sources_l
    is_startup100 = truthy(row.get("is_jpx_startup100")) or "startup100" in sources_l or "su100" in sources_l
    market = clean(row.get("market") or row.get("市場") or ("Growth" if is_growth250 or is_startup100 else "Prime"))
    sector = clean(row.get("sector") or row.get("業種") or "")

    if is_startup100:
        bucket = "Discovery"
        theme = "Japan Startup / Growth Discovery"
        priority = "A"
    elif is_growth250:
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
        "asset_type": clean(row.get("asset_type") or "equity"),
        "is_topix500": str(is_topix500).lower(),
        "is_jpx_prime150": str(is_prime150).lower(),
        "is_growth250": str(is_growth250).lower(),
        "is_jpx_startup100": str(is_startup100).lower(),
        "source_detail": sources,
        "source_url": clean(row.get("source_url")),
    }


def normalize_legacy_row(row: dict[str, Any]) -> dict[str, str]:
    ticker = normalize_ticker(row)
    bucket = clean(row.get("bucket") or "Core")
    return {
        "symbol": ticker,
        "name": clean(row.get("name") or ticker),
        "theme": clean(row.get("theme") or "Japan Equities"),
        "bucket": bucket,
        "priority": clean(row.get("priority") or "B").upper(),
        "market": clean(row.get("market") or "JP"),
        "sector": clean(row.get("sector") or ""),
        "asset_type": clean(row.get("asset_type") or "equity"),
        "is_topix500": "false",
        "is_jpx_prime150": "false",
        "is_growth250": "true" if bucket.lower() == "discovery" else "false",
        "is_jpx_startup100": "false",
        "source_detail": "legacy_universe_jp",
        "source_url": "",
    }


def normalize_manual_row(row: dict[str, Any], row_number: int) -> tuple[dict[str, str] | None, ManualReject | None]:
    ticker = normalize_ticker(row)
    name = clean(row.get("name") or row.get("銘柄名") or row.get("issue_name") or ticker)
    if not ticker:
        return None, ManualReject(row_number, ticker, name, "empty_symbol")
    if not ticker_is_valid(ticker):
        return None, ManualReject(row_number, ticker, name, "invalid_ticker_format")
    if clean(row.get("asset_type") or "equity").lower() != "equity":
        return None, ManualReject(row_number, ticker, name, "asset_type_not_equity")

    theme = clean(row.get("theme") or "Manual Theme Include")
    bucket = clean(row.get("bucket") or "Discovery")
    priority = clean(row.get("priority") or "A").upper()
    if priority not in {"A", "B", "C"}:
        priority = "A"

    return {
        "symbol": ticker,
        "name": name or ticker,
        "theme": theme,
        "bucket": bucket,
        "priority": priority,
        "market": clean(row.get("market") or "JP"),
        "sector": clean(row.get("sector") or ""),
        "asset_type": "equity",
        "is_topix500": normalize_bool(row.get("is_topix500")),
        "is_jpx_prime150": normalize_bool(row.get("is_jpx_prime150")),
        "is_growth250": normalize_bool(row.get("is_growth250")),
        "is_jpx_startup100": normalize_bool(row.get("is_jpx_startup100")),
        "source_detail": "manual_theme_include" + ((":" + clean(row.get("source_detail"))) if clean(row.get("source_detail")) else ""),
        "source_url": clean(row.get("source_url")),
    }, None


def priority_weight(priority: str) -> int:
    return {"A": 0, "B": 1, "C": 2}.get(clean(priority).upper(), 3)


def source_score(row: dict[str, str]) -> tuple[int, int, str]:
    """Deterministic universe rank for non-manual source rows."""
    # Lower tuple sorts first.
    if row.get("is_jpx_prime150") == "true":
        source_rank = 0
    elif row.get("is_topix500") == "true":
        source_rank = 1
    elif row.get("is_jpx_startup100") == "true":
        source_rank = 2
    elif row.get("is_growth250") == "true":
        source_rank = 3
    else:
        source_rank = 4
    return (source_rank, priority_weight(row.get("priority", "B")), row.get("symbol", ""))


def merge_rows(base: dict[str, str], override: dict[str, str]) -> dict[str, str]:
    """Merge manual metadata over source metadata without losing index flags."""
    out = dict(base)
    for key in FIELDNAMES:
        val = clean(override.get(key))
        if val:
            out[key] = val
    for flag in ["is_topix500", "is_jpx_prime150", "is_growth250", "is_jpx_startup100"]:
        out[flag] = "true" if truthy(base.get(flag)) or truthy(override.get(flag)) else "false"
    details = [clean(base.get("source_detail")), clean(override.get("source_detail"))]
    out["source_detail"] = "|".join([x for x in details if x])
    urls = [clean(base.get("source_url")), clean(override.get("source_url"))]
    out["source_url"] = "|".join(dict.fromkeys([x for x in urls if x]))
    return {k: clean(out.get(k)) for k in FIELDNAMES}


def load_source_rows() -> tuple[list[dict[str, str]], Path]:
    source_rows = read_csv(SOURCE_CSV)
    if source_rows:
        return [normalize_index_row(r) for r in source_rows], SOURCE_CSV
    if STRICT_INDEX_UNIVERSE and not ALLOW_LEGACY_FALLBACK:
        raise FileNotFoundError(
            "Index universe CSV is required but was not found: "
            f"{safe_rel(SOURCE_CSV)}. Run Build JP index universe first, or set ALLOW_LEGACY_FALLBACK=true."
        )
    legacy_rows = read_csv(FALLBACK_CSV)
    if not legacy_rows:
        raise FileNotFoundError(f"No source universe CSV found: {safe_rel(SOURCE_CSV)} or {safe_rel(FALLBACK_CSV)}")
    return [normalize_legacy_row(r) for r in legacy_rows], FALLBACK_CSV


def load_manual_rows(source_by_symbol: dict[str, dict[str, str]]) -> tuple[list[dict[str, str]], list[ManualReject], int]:
    raw_rows = read_csv(MANUAL_INCLUDE_CSV)
    manual: list[dict[str, str]] = []
    rejects: list[ManualReject] = []
    seen: set[str] = set()
    for idx, row in enumerate(raw_rows, start=2):
        normalized, reject = normalize_manual_row(row, idx)
        if reject:
            rejects.append(reject)
            continue
        assert normalized is not None
        symbol = normalized["symbol"]
        if symbol in seen:
            rejects.append(ManualReject(idx, symbol, normalized.get("name", ""), "duplicate_manual_symbol"))
            continue
        seen.add(symbol)
        if symbol in source_by_symbol:
            normalized = merge_rows(source_by_symbol[symbol], normalized)
        manual.append(normalized)
    return manual, rejects, len(raw_rows)


def pick_universe(source_rows: list[dict[str, str]], manual_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if UNIVERSE_LIMIT <= 0:
        raise ValueError("UNIVERSE_LIMIT must be greater than zero")
    if len(manual_rows) > UNIVERSE_LIMIT:
        raise ValueError(f"manual include count {len(manual_rows)} exceeds UNIVERSE_LIMIT={UNIVERSE_LIMIT}")

    selected: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(row: dict[str, str]) -> bool:
        symbol = row.get("symbol", "")
        if not symbol or symbol in seen:
            return False
        selected.append({k: clean(row.get(k)) for k in FIELDNAMES})
        seen.add(symbol)
        return True

    for row in sorted(manual_rows, key=lambda r: (priority_weight(r.get("priority", "A")), r.get("symbol", ""))):
        add(row)

    source_valid = [r for r in source_rows if r.get("symbol") and ticker_is_valid(r.get("symbol", ""))]
    by_bucket = {
        "core": sorted([r for r in source_valid if r.get("bucket") == "Core"], key=source_score),
        "growth": sorted([r for r in source_valid if r.get("bucket") == "Discovery" and r.get("is_jpx_startup100") != "true"], key=source_score),
        "startup": sorted([r for r in source_valid if r.get("is_jpx_startup100") == "true"], key=source_score),
    }
    other = sorted([r for r in source_valid if r not in by_bucket["core"] and r not in by_bucket["growth"] and r not in by_bucket["startup"]], key=source_score)

    targets = [
        ("core", CORE_TARGET),
        ("growth", CORE_TARGET + GROWTH_TARGET),
        ("startup", CORE_TARGET + GROWTH_TARGET + STARTUP_TARGET),
    ]
    for key, target_total in targets:
        for row in by_bucket[key]:
            if len(selected) >= UNIVERSE_LIMIT:
                break
            if len(selected) >= target_total:
                break
            add(row)

    for row in other + sorted(source_valid, key=source_score):
        if len(selected) >= UNIVERSE_LIMIT:
            break
        add(row)

    diag = {
        "selected_rows": len(selected),
        "manual_selected_rows": sum(1 for r in selected if "manual_theme_include" in (r.get("source_detail") or "")),
        "source_selected_rows": len(selected) - sum(1 for r in selected if "manual_theme_include" in (r.get("source_detail") or "")),
        "core": sum(1 for r in selected if r.get("bucket") == "Core"),
        "discovery": sum(1 for r in selected if r.get("bucket") == "Discovery"),
        "topix500": sum(1 for r in selected if r.get("is_topix500") == "true"),
        "prime150": sum(1 for r in selected if r.get("is_jpx_prime150") == "true"),
        "growth250": sum(1 for r in selected if r.get("is_growth250") == "true"),
        "startup100": sum(1 for r in selected if r.get("is_jpx_startup100") == "true"),
    }
    return selected, diag


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_diag(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    source_rows, source_used = load_source_rows()
    source_rows = [r for r in source_rows if r.get("symbol") and ticker_is_valid(r.get("symbol", ""))]
    source_by_symbol = {r["symbol"]: r for r in source_rows}
    manual_rows, manual_rejects, manual_raw_count = load_manual_rows(source_by_symbol)

    selected, pick_diag = pick_universe(source_rows, manual_rows)
    write_csv(OUT_CSV, selected)

    manual_symbols = {r["symbol"] for r in manual_rows}
    selected_symbols = {r["symbol"] for r in selected}
    missing_manual = sorted(manual_symbols - selected_symbols)

    diagnostics = {
        "schema_version": "jp_ai_arena_universe_diagnostics_v2",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_used": safe_rel(source_used),
        "manual_include_csv": safe_rel(MANUAL_INCLUDE_CSV),
        "out_csv": safe_rel(OUT_CSV),
        "universe_limit": UNIVERSE_LIMIT,
        "core_target": CORE_TARGET,
        "growth_target": GROWTH_TARGET,
        "startup_target": STARTUP_TARGET,
        "strict_index_universe": STRICT_INDEX_UNIVERSE,
        "source_input_rows": len(source_rows),
        "manual_raw_rows": manual_raw_count,
        "manual_valid_rows": len(manual_rows),
        "manual_rejected_rows": len(manual_rejects),
        "manual_rejects": [asdict(r) for r in manual_rejects],
        "manual_missing_after_selection": missing_manual,
        **pick_diag,
        "selected_symbols_sample": [r["symbol"] for r in selected[:25]],
        "manual_symbols": sorted(manual_symbols),
    }
    write_diag(DIAG_JSON, diagnostics)

    print("Build JP AI Arena universe")
    print(f"generated_at={diagnostics['generated_at']}")
    print(f"source_used={diagnostics['source_used']}")
    print(f"manual_include_csv={diagnostics['manual_include_csv']}")
    print(f"out_csv={diagnostics['out_csv']}")
    print(f"diagnostics_json={safe_rel(DIAG_JSON)}")
    print(f"universe_limit={UNIVERSE_LIMIT}")
    print(f"rows={len(selected)}")
    print(f"manual_valid_rows={len(manual_rows)}")
    print(f"manual_rejected_rows={len(manual_rejects)}")
    print(f"core={pick_diag['core']} discovery={pick_diag['discovery']}")

    if manual_rejects:
        for reject in manual_rejects:
            print(f"manual_reject row={reject.row_number} symbol={reject.symbol} reason={reject.reason}")
        if FAIL_IF_MANUAL_REJECTED:
            raise SystemExit("Manual include CSV contains rejected rows. See diagnostics JSON.")
    if missing_manual:
        raise SystemExit(f"Manual include symbols missing after selection: {missing_manual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
