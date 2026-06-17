# Neon Tokyo Signals — Live/Season/War Room Bootstrap Recheck Fix

## Root cause recheck

The latest GitHub Actions log showed that the canonical release existed, but the required DuckDB asset was missing:

```text
Available assets in ai-arena-duckdb-latest:
neon_tokyo_jp_latest_manifest.json
Required canonical asset is missing: neon_tokyo_jp_latest.duckdb.zst
Canonical DuckDB was not restored. Bootstrapping a new DB in live-update.
```

The price fetch then succeeded and populated `prices_daily`:

```text
yfinance success count: 853
skipped count: 6
failed count: 0
inserted rows: 298721
latest_price_date: 2026-06-17
is_stale: False
```

The actual failure occurred next:

```text
fundamentals_latest_jp rows before ensure: 0
Canonical DB is being bootstrapped; fundamentals must be fetched before value features.
universe_master has no equity rows. Run universe + price build first.
```

The first patch fixed only `universe_master`.  A deeper recheck found the next likely failure: on a freshly bootstrapped DuckDB, `features_daily` is also empty when `build_value_features_jp.py` runs.  `build_agent_scores_jp.py` rebuilds `features_daily`, but that happens too late because value features are built before agent scores.

## Fix

This patch makes the data pipeline explicit and deterministic:

```text
Build universe CSV
Sync universe_master to DuckDB
Fetch prices into prices_daily
Build price features into features_daily
Export public price JSON
Ensure fundamentals_latest_jp
Build value_features_daily
Build agent_scores_daily
Rebuild AI Arena season
Build War Room payload
Render static pages
Publish canonical DuckDB asset
Commit outputs
```

## Files changed

```text
.github/workflows/ai-arena-jp-live-update.yml
.github/workflows/ai-arena-jp-season-rebuild.yml
.github/workflows/ai-arena-jp-war-room.yml
.github/workflows/ai-arena-jp-fundamentals.yml
scripts/sync_universe_master_from_csv_jp.py
scripts/build_price_features_jp.py
tests/test_universe_master_sync.py
tests/test_price_features_and_workflow_order.py
tests/test_live_update_workflow_bootstrap.py
```

## Validation run locally

```text
python -m compileall scripts tests
python -m unittest discover -s tests -v

Ran 10 tests
OK
```

YAML parsing was also validated for all workflow files.

## What to run next

Run `AI Arena JP live update` with default inputs:

```text
skip_price_fetch=false
price_refresh_mode=incremental
skip_fundamentals_fetch=true
commit_outputs=true
```

Because the canonical DuckDB asset is currently missing, the workflow should bootstrap a fresh DB, then publish `neon_tokyo_jp_latest.duckdb.zst` back to the `ai-arena-duckdb-latest` release.

