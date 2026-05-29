# AI Arena DuckDB Cache / Validation Fix

## What this fixes

The previous season rebuild workflow failed at validation with:

```text
Cannot open database "data/cache/neon_tokyo_jp.duckdb" in read-only mode: database does not exist
```

Root cause:

```text
scripts/prune_ai_arena_generated_artifacts.py removed data/cache/*.duckdb before validation.
```

DuckDB is an Actions cache artifact. It must not be committed, but it must also
not be deleted before validation/cache save.

## Changed files

```text
.github/workflows/ai-arena-jp-season-rebuild.yml
scripts/prune_ai_arena_generated_artifacts.py
```

## Key changes

- `PRUNE_DUCKDB_CACHE=false` is the default.
- `Prune generated artifacts` no longer removes `data/cache/neon_tokyo_jp.duckdb` during normal workflows.
- Season rebuild workflow now has:
  - `skip_price_fetch`
  - `skip_fundamentals_fetch`
  - explicit DB existence check before build
  - explicit DB existence check before validation
  - `actions/cache@v4` with `save-always: true`

## Safe next run

Because the last failed workflow likely did not save the DuckDB cache, run once with:

```text
skip_price_fetch: false
skip_fundamentals_fetch: false
fetch_fundamentals: true
force_finalize_season: false
commit_outputs: true
```

After one successful run/cache save, reruns for render/validation only can use:

```text
skip_price_fetch: true
skip_fundamentals_fetch: true
fetch_fundamentals: false
force_finalize_season: false
commit_outputs: true
```
