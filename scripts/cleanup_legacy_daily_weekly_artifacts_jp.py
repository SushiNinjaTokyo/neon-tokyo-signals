#!/usr/bin/env python3
"""
Cleanup legacy Daily / Weekly public artifacts for Neon Tokyo Signals.

Purpose
-------
Neon Tokyo Signals is moving to an AI Arena first architecture.  Daily / Weekly
pages and generated JSON are no longer part of the main product path and should
not remain as large public artifacts in ``site/``.

This script is intentionally scoped and defensive:
- It deletes only known legacy Daily / Weekly paths.
- It never deletes AI Arena, AI_LAB / discussion / memory outputs, prices-jp
  latest JSON, DuckDB, universe data, assets used by AI Arena, or data/agents.
- It supports dry-run by default.
- It can optionally remove rendered legacy pages and legacy Daily / Weekly
  workflow files, but those are opt-in via ``--scope``.

Recommended first execution:
    python scripts/cleanup_legacy_daily_weekly_artifacts_jp.py --dry-run --scope data

Then, after confirming the deletion plan:
    python scripts/cleanup_legacy_daily_weekly_artifacts_jp.py --scope data

Scopes
------
``data``
    Remove only legacy Daily / Weekly public JSON directories.  This is the
    safest and recommended first step.

``data_and_pages``
    Remove legacy public JSON directories and rendered legacy Daily / Weekly
    HTML pages / CSS assets.

``data_pages_and_workflows``
    Remove legacy public JSON directories, rendered legacy pages/assets, and
    obsolete Daily / Weekly / prototype GitHub Actions workflow files.  Python
    source scripts are preserved by design so they can be audited or recovered
    later.  AI_LAB data and scripts are also preserved.

The script writes a report to:
    site/data/japan/ai-arena/legacy-cleanup-report.json

That report is intentionally under the AI Arena diagnostics area and is safe to
commit.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


LEGACY_DATA_PATHS = (
    # Heavy Daily / Backtest outputs.
    "site/data/backtest-daily-jp",
    "site/data/daily-jp",
    "site/data/daily-v2-jp",
    # Daily simulation outputs that are not needed by AI Arena after the
    # DuckDB-based simulation path is established.
    "site/data/japan/daily",
    # Weekly outputs.  Keep this explicit to avoid touching unrelated Japan data.
    "site/data/weekly-jp",
    "site/data/japan/weekly",
)

LEGACY_PAGE_AND_ASSET_PATHS = (
    # Rendered public pages.
    "site/japan/daily",
    "site/japan/weekly",
    "site/japan/weekly-backtest",
    "site/japan/weekly-simulation",
    # CSS / JS dedicated to legacy pages.  AI Arena assets are intentionally not
    # listed here.
    "site/assets/daily_jp.css",
    "site/assets/backtest_daily_jp.css",
    "site/assets/daily_simulation_jp.css",
    "site/assets/weekly_jp.css",
    "site/assets/weekly_backtest_jp.css",
    "site/assets/weekly_simulation_jp.css",
)

LEGACY_WORKFLOW_PATHS = (
    # Daily build / render / simulation workflows.  These are intentionally
    # removed after AI Arena becomes the main product path.
    ".github/workflows/backtest-daily-jp-incremental.yml",
    ".github/workflows/backtest-daily-jp-range.yml",
    ".github/workflows/build-daily-jp.yml",
    ".github/workflows/daily-jp-auto.yml",
    ".github/workflows/daily-jp-simulation.yml",
    ".github/workflows/render-backtest-daily-jp.yml",
    ".github/workflows/render-daily-jp.yml",

    # Weekly build / render workflows.
    ".github/workflows/weekly-jp-analysis.yml",
    ".github/workflows/weekly-jp-screening.yml",

    # Generic / old cleanup workflows that still assume Daily / Backtest
    # public JSON exists.  Keeping them scheduled causes false failures after
    # legacy cleanup.
    ".github/workflows/prune-safe-generated-artifacts.yml",
    ".github/workflows/prune-heavy-price-json.yml",
    ".github/workflows/fetch-prices-jp.yml",
    ".github/workflows/render-only.yml",

    # Superseded AI Arena prototype / trial workflows.  AI_LAB data and scripts
    # are preserved; only obsolete GitHub Actions entry points are removed.
    ".github/workflows/agent-scores-jp-duckdb-trial.yml",
    ".github/workflows/ai-arena-cleanup.yml",
    ".github/workflows/ai-arena-jp.yml",
    ".github/workflows/ai-arena-jp-historical-simulation.yml",
)

# Files/directories that must remain after cleanup.  These are AI Arena or
# shared product outputs, not Daily / Weekly outputs.
REQUIRED_AFTER_CLEANUP = (
    "site/index.html",
    "site/data/prices-jp/latest.json",
    "site/data/japan/ai-arena",
    "site/japan/ai-arena",
    "site/assets/ai_arena_jp.css",
    "site/assets/ai_arena_jp.js",
    "data/agents",
)

# Additional protected path prefixes.  The deletion candidate list is fixed, but
# these guards prevent accidental broadening in future edits.
PROTECTED_PREFIXES = (
    "site/data/japan/ai-arena",
    "site/data/japan/agent-scores",
    "site/data/prices-jp/latest.json",
    "site/data/prices-jp/manifest.json",
    "site/data/japan/universe",
    "site/data/japan/company",
    "site/data/japan/fundamentals",
    "site/japan/ai-arena",
    "site/assets/ai_arena",
    "data/agents",
    "data/cache",
)

REPORT_PATH = "site/data/japan/ai-arena/legacy-cleanup-report.json"


@dataclass(frozen=True)
class DeleteCandidate:
    path: str
    kind: str
    reason: str
    exists: bool
    tracked: bool
    size_bytes: int


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def repo_root() -> Path:
    return Path.cwd().resolve()


def normalize_rel(path: str | Path) -> str:
    return Path(str(path).replace("\\", "/")).as_posix().strip("/")


def path_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def is_tracked(root: Path, rel_path: str) -> bool:
    git_dir = root / ".git"
    if not git_dir.exists():
        return False
    # Use git ls-files through os.popen-free subprocess to avoid shell escaping
    # pitfalls.  Import locally to keep top-level dependencies minimal.
    import subprocess

    result = subprocess.run(
        ["git", "ls-files", "--", rel_path],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"git ls-files failed for {rel_path}: {result.stderr}")
    return bool(result.stdout.strip())


def is_protected(rel_path: str) -> bool:
    rel = normalize_rel(rel_path)
    for protected in PROTECTED_PREFIXES:
        p = normalize_rel(protected)
        if rel == p or rel.startswith(p + "/"):
            return True
    return False


def selected_paths(scope: str) -> list[tuple[str, str, str]]:
    paths: list[tuple[str, str, str]] = []
    for p in LEGACY_DATA_PATHS:
        paths.append((p, "legacy_data", "legacy Daily / Weekly generated public data"))

    if scope in {"data_and_pages", "data_pages_and_workflows"}:
        for p in LEGACY_PAGE_AND_ASSET_PATHS:
            paths.append((p, "legacy_page_or_asset", "legacy Daily / Weekly rendered page or asset"))

    if scope == "data_pages_and_workflows":
        for p in LEGACY_WORKFLOW_PATHS:
            paths.append((p, "legacy_workflow", "legacy Daily / Weekly GitHub Actions workflow"))

    return paths


def collect_candidates(root: Path, scope: str) -> list[DeleteCandidate]:
    candidates: list[DeleteCandidate] = []
    seen: set[str] = set()

    for raw_path, kind, reason in selected_paths(scope):
        rel = normalize_rel(raw_path)
        if rel in seen:
            continue
        seen.add(rel)

        if is_protected(rel):
            raise SystemExit(f"Refusing to delete protected path: {rel}")

        path = root / rel
        exists = path.exists()
        tracked = is_tracked(root, rel)
        if not exists and not tracked:
            candidates.append(
                DeleteCandidate(
                    path=rel,
                    kind=kind,
                    reason=reason,
                    exists=False,
                    tracked=False,
                    size_bytes=0,
                )
            )
            continue

        candidates.append(
            DeleteCandidate(
                path=rel,
                kind=kind,
                reason=reason,
                exists=exists,
                tracked=tracked,
                size_bytes=path_size_bytes(path),
            )
        )

    return candidates


def delete_path(root: Path, rel_path: str) -> None:
    path = root / rel_path
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()
    # If the path is tracked but already absent, git add -A in the workflow will
    # stage the deletion.  No action needed here.


def assert_required_paths(root: Path) -> None:
    missing: list[str] = []
    for rel in REQUIRED_AFTER_CLEANUP:
        path = root / rel
        if not path.exists():
            missing.append(rel)
    if missing:
        raise SystemExit("Required AI Arena/shared paths missing after cleanup:\n" + "\n".join(f"- {p}" for p in missing))


def write_report(root: Path, *, scope: str, dry_run: bool, candidates: Iterable[DeleteCandidate]) -> None:
    candidate_list = list(candidates)
    report_path = root / REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "legacy_daily_weekly_cleanup_report_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": scope,
        "dry_run": dry_run,
        "candidate_count": len(candidate_list),
        "candidate_existing_count": sum(1 for c in candidate_list if c.exists),
        "candidate_tracked_count": sum(1 for c in candidate_list if c.tracked),
        "candidate_size_mb": round(sum(c.size_bytes for c in candidate_list) / 1024 / 1024, 4),
        "deleted": [] if dry_run else [asdict(c) for c in candidate_list if c.exists or c.tracked],
        "candidates": [asdict(c) for c in candidate_list],
        "protected_prefixes": list(PROTECTED_PREFIXES),
        "required_after_cleanup": list(REQUIRED_AFTER_CLEANUP),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_plan(candidates: list[DeleteCandidate], dry_run: bool) -> None:
    total_mb = sum(c.size_bytes for c in candidates) / 1024 / 1024
    action = "WOULD_DELETE" if dry_run else "DELETE"
    print("Legacy Daily / Weekly cleanup")
    print(f"dry_run={str(dry_run).lower()}")
    print(f"candidate_count={len(candidates)}")
    print(f"candidate_size_mb={total_mb:.4f}")
    for c in candidates:
        status = "present" if c.exists else "absent"
        tracked = "tracked" if c.tracked else "untracked"
        print(f"{action}\t{c.size_bytes / 1024 / 1024:.4f} MB\t{status}\t{tracked}\t{c.kind}\t{c.path}\t{c.reason}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup legacy Daily / Weekly generated artifacts.")
    parser.add_argument(
        "--scope",
        choices=("data", "data_and_pages", "data_pages_and_workflows"),
        default=os.getenv("LEGACY_CLEANUP_SCOPE", "data"),
        help="Cleanup scope. Default: data. Use data_and_pages after confirming AI Arena pages are stable.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=parse_bool(os.getenv("LEGACY_CLEANUP_DRY_RUN"), True),
        help="Preview deletion targets without deleting. Default true via LEGACY_CLEANUP_DRY_RUN.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute deletion. This overrides --dry-run and LEGACY_CLEANUP_DRY_RUN.",
    )
    args = parser.parse_args()

    dry_run = False if args.execute else bool(args.dry_run)
    root = repo_root()

    if not (root / "scripts").is_dir() or not (root / "site").is_dir():
        raise SystemExit("Run this script from repository root. Expected scripts/ and site/ directories.")

    assert_required_paths(root)
    candidates = collect_candidates(root, args.scope)
    print_plan(candidates, dry_run)

    if not dry_run:
        for candidate in candidates:
            if candidate.exists or candidate.tracked:
                delete_path(root, candidate.path)
        assert_required_paths(root)

    write_report(root, scope=args.scope, dry_run=dry_run, candidates=candidates)
    print(f"report={REPORT_PATH}")
    print("Cleanup preview complete." if dry_run else "Cleanup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
