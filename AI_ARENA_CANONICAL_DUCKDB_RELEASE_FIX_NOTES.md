# AI Arena DuckDB Canonical Release State Fix

## Purpose

This change stops treating GitHub Actions cache as the source of truth for AI Arena state.

Old model:

```text
Actions cache = pseudo database source of truth
```

New model:

```text
GitHub Release asset = canonical DuckDB source of truth
Actions cache = not used for DB handoff
```

## New canonical assets

Release tag:

```text
ai-arena-duckdb-latest
```

Assets:

```text
neon_tokyo_jp_latest.duckdb.zst
neon_tokyo_jp_latest_manifest.json
```

## Added helper scripts

```text
scripts/lib/duckdb_build_metadata.py
scripts/stamp_duckdb_build_metadata.py
scripts/show_duckdb_build_metadata.py
```

## Workflows replaced

```text
.github/workflows/ai-arena-jp-season-rebuild.yml
.github/workflows/ai-arena-jp-data-coverage-review.yml
.github/workflows/ai-arena-jp-live-update.yml
```

## What changes

1. No v1/v2/v3 fallback.
2. Season rebuild downloads canonical DB if available.
3. Season rebuild writes DB build metadata.
4. Season rebuild uploads DuckDB explicitly as a GitHub Release asset.
5. Coverage Review downloads that exact canonical DuckDB.
6. Live Update downloads that exact canonical DuckDB, updates it, and republishes it.
7. All relevant workflows print DB build metadata and row counts.

## First execution order

1. Commit these files.
2. Run `AI Arena JP season rebuild`.
3. Confirm Release `ai-arena-duckdb-latest` exists and has:
   - `neon_tokyo_jp_latest.duckdb.zst`
   - `neon_tokyo_jp_latest_manifest.json`
4. Run `AI Arena JP data coverage review`.
5. Confirm logs show `duckdb_build_metadata` and the latest build_id.

## Recommended season rebuild inputs for the first run

```text
skip_price_fetch: false
fetch_fundamentals: true
skip_fundamentals_fetch: false
force_finalize_season: false
commit_outputs: true
```

## Recommended subsequent rerun without re-fetching prices

```text
skip_price_fetch: true
fetch_fundamentals: false
skip_fundamentals_fetch: true
force_finalize_season: false
commit_outputs: true
```

## Important note

Do not reintroduce Actions cache as a fallback for DuckDB state.
Fallbacks to old DBs are exactly what caused the v1/v3 confusion.
