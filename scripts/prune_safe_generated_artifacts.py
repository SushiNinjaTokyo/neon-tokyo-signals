#!/usr/bin/env python3
"""
Prune only low-risk generated artifacts from the static site tree.

This script is intentionally conservative.
It does NOT delete:
- latest.json
- manifest.json
- files referenced by manifest.latest or manifest.history[].path
- daily-jp dated snapshots, because AI Arena historical simulation reads them
- AI Arena simulation / positions / ranking / discussion / memory / events JSON

Default targets:
- old dated JSON files under site/data/backtest-daily-jp
- old dated JSON files under site/data/prices-jp
- Python bytecode caches under scripts/

The dated JSON files kept by the current manifest are preserved, even when they
are large. This avoids dangling manifest references and keeps the cleanup safe.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATE_JSON_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}\.json$")

DEFAULT_PRUNE_DIRS = (
    "site/data/backtest-daily-jp",
    "site/data/prices-jp",
)

REQUIRED_AFTER_PRUNE = (
    "site/index.html",
    "site/data/prices-jp/latest.json",
    "site/data/prices-jp/manifest.json",
    "site/data/backtest-daily-jp/latest.json",
    "site/data/backtest-daily-jp/manifest.json",
    "site/data/daily-jp/latest.json",
    "site/data/daily-jp/manifest.json",
    "site/data/japan/ai-arena/simulation/latest.json",
    "site/data/japan/ai-arena/positions/latest.json",
    "site/data/japan/ai-arena/ranking/latest.json",
)


@dataclass(frozen=True)
class DeleteCandidate:
    path: Path
    reason: str
    size_bytes: int


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {path}: {exc}") from exc


def repo_root() -> Path:
    return Path.cwd().resolve()


def rel_to_root(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def resolve_manifest_path(raw_path: str, root: Path, manifest_dir: Path) -> Path | None:
    if not raw_path:
        return None

    raw = raw_path.replace("\\", "/")
    candidates = []

    p = Path(raw)
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.append(root / p)
        candidates.append(manifest_dir / p)

    for candidate in candidates:
        try:
            return candidate.resolve()
        except OSError:
            continue
    return None


def protected_paths_for_manifest(directory: Path, root: Path) -> set[Path]:
    protected: set[Path] = set()

    for name in ("latest.json", "manifest.json"):
        protected.add((directory / name).resolve())

    manifest_path = directory / "manifest.json"
    manifest = read_json(manifest_path)
    if not manifest:
        return protected

    for key in ("latest", "path"):
        resolved = resolve_manifest_path(str(manifest.get(key) or ""), root, directory)
        if resolved is not None:
            protected.add(resolved)

    latest_date = str(manifest.get("latest_date") or "").strip()
    if latest_date:
        protected.add((directory / f"{latest_date}.json").resolve())

    history = manifest.get("history")
    if isinstance(history, list):
        for item in history:
            if not isinstance(item, dict):
                continue
            resolved = resolve_manifest_path(str(item.get("path") or ""), root, directory)
            if resolved is not None:
                protected.add(resolved)
            date_value = str(item.get("date") or "").strip()
            if date_value:
                protected.add((directory / f"{date_value}.json").resolve())

    return protected


def collect_dated_json_candidates(root: Path, directory: Path) -> list[DeleteCandidate]:
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise SystemExit(f"Expected directory, got file: {directory}")

    protected = protected_paths_for_manifest(directory, root)
    candidates: list[DeleteCandidate] = []

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if not DATE_JSON_RE.match(path.name):
            continue
        if path.resolve() in protected:
            continue
        candidates.append(
            DeleteCandidate(
                path=path,
                reason="dated generated JSON not referenced by manifest/latest",
                size_bytes=path.stat().st_size,
            )
        )

    return candidates


def collect_python_cache_candidates(root: Path) -> list[DeleteCandidate]:
    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return []

    candidates: list[DeleteCandidate] = []

    for cache_dir in sorted(scripts_dir.rglob("__pycache__")):
        if cache_dir.is_dir():
            size = sum(p.stat().st_size for p in cache_dir.rglob("*") if p.is_file())
            candidates.append(
                DeleteCandidate(
                    path=cache_dir,
                    reason="python bytecode cache directory",
                    size_bytes=size,
                )
            )

    for path in sorted(scripts_dir.rglob("*.py[co]")):
        if path.is_file():
            candidates.append(
                DeleteCandidate(
                    path=path,
                    reason="python bytecode cache file",
                    size_bytes=path.stat().st_size,
                )
            )

    # Deduplicate child .pyc files when their __pycache__ directory is already included.
    cache_dirs = {c.path.resolve() for c in candidates if c.path.is_dir()}
    deduped: list[DeleteCandidate] = []
    for candidate in candidates:
        resolved = candidate.path.resolve()
        if candidate.path.is_file() and any(parent in resolved.parents for parent in cache_dirs):
            continue
        deduped.append(candidate)
    return deduped


def assert_required_files_exist(root: Path) -> None:
    missing = [path for path in REQUIRED_AFTER_PRUNE if not (root / path).is_file()]
    if missing:
        raise SystemExit("Required files missing after prune:\n" + "\n".join(f"- {p}" for p in missing))


def delete_candidate(candidate: DeleteCandidate) -> None:
    if candidate.path.is_dir():
        shutil.rmtree(candidate.path)
    elif candidate.path.exists():
        candidate.path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune low-risk generated artifacts.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=parse_bool(os.getenv("PRUNE_DRY_RUN"), False),
        help="Print deletion plan without deleting files. Can also be set by PRUNE_DRY_RUN=true.",
    )
    parser.add_argument(
        "--skip-python-cache",
        action="store_true",
        default=parse_bool(os.getenv("PRUNE_SKIP_PYTHON_CACHE"), False),
        help="Do not delete scripts/__pycache__ or .pyc/.pyo files.",
    )
    args = parser.parse_args()

    root = repo_root()
    if not (root / "scripts").is_dir() or not (root / "site").is_dir():
        raise SystemExit("Run this script from the repository root. Expected scripts/ and site/ directories.")

    assert_required_files_exist(root)

    candidates: list[DeleteCandidate] = []
    for relative_dir in DEFAULT_PRUNE_DIRS:
        candidates.extend(collect_dated_json_candidates(root, root / relative_dir))

    if not args.skip_python_cache:
        candidates.extend(collect_python_cache_candidates(root))

    total_bytes = sum(c.size_bytes for c in candidates)

    print("Prune safe generated artifacts")
    print(f"generated_at_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"dry_run={args.dry_run}")
    print(f"candidate_count={len(candidates)}")
    print(f"candidate_size_mb={total_bytes / 1024 / 1024:.2f}")

    for candidate in candidates:
        print(
            f"{'WOULD_DELETE' if args.dry_run else 'DELETE'}\t"
            f"{candidate.size_bytes / 1024 / 1024:.2f} MB\t"
            f"{rel_to_root(candidate.path, root)}\t"
            f"{candidate.reason}"
        )

    if args.dry_run:
        print("Dry run complete. No files were deleted.")
        return 0

    for candidate in candidates:
        delete_candidate(candidate)

    assert_required_files_exist(root)
    print("Prune complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
