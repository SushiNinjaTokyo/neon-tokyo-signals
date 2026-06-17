# AI Arena JP live-update fundamentals bootstrap fix

## Root cause

The previous bootstrap fix correctly allowed `ai-arena-jp-live-update.yml` to recover when the canonical DuckDB release asset `neon_tokyo_jp_latest.duckdb.zst` was missing.

However, a newly bootstrapped DuckDB contains freshly fetched prices but does not yet contain `fundamentals_latest_jp`. The next step, `scripts/build_value_features_jp.py`, intentionally fails when fundamentals are empty because HIZUMI/value features require real fundamentals instead of silently producing degraded value data.

Observed failure:

```text
fundamentals_latest_jp is empty. Run scripts/fetch_fundamentals_jp.py or restore canonical DuckDB first.
```

## Fix

`.github/workflows/ai-arena-jp-live-update.yml` now has a mandatory integrity step before value-feature generation:

```text
Ensure JP fundamentals
```

That step:

1. checks `fundamentals_latest_jp` row count in DuckDB;
2. forces `scripts/fetch_fundamentals_jp.py` when canonical DuckDB is being bootstrapped;
3. forces fundamentals fetch if the table is missing or empty, even if the manual skip flag was left at its default;
4. still allows normal runs to skip fundamentals when a restored canonical DB already contains valid rows;
5. verifies that fundamentals are non-empty after the fetch.

This is not a bypass. It preserves the invariant that `build_value_features_jp.py` only runs after the value/fundamental source table exists.

## Additional workflow hardening

The live-update workflow now also sets explicit price-fetch envs:

```text
STOOQ_FALLBACK_ENABLED=false
STOOQ_TIMEOUT_SECONDS=3
YFINANCE_TIMEOUT_SECONDS=10
PRICE_FETCH_SLEEP_SECONDS=0.05
```

## Files included

```text
.github/workflows/ai-arena-jp-live-update.yml
tests/test_live_update_workflow_bootstrap.py
README_LIVE_UPDATE_FUNDAMENTALS_BOOTSTRAP_FIX.md
```

## Validation performed

```bash
python -m compileall scripts tests
python -m unittest discover -s tests -v
OUT_DIR=site python scripts/render_all.py
```

Result:

```text
6 tests OK
render_all.py OK
```
