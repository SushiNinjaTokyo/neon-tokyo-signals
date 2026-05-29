# AI Arena data pipeline fix - implementation notes

## What this diff fixes

1. `site/data/prices-jp/latest.json` is forced to lightweight `summary` mode.
2. Agent score date selection is coverage-based and no longer uses ETF-only `MAX(date)`.
3. Data coverage diagnostics uses internal agent IDs and display names correctly.
4. Season rebuild verifies that Arena rows are persisted to DuckDB tables.
5. yfinance-based JP fundamentals refresh is added and writes `fundamentals_latest_jp` / `value_features_daily`.

## Safe execution order

After placing files and committing:

```bash
git add -A
git commit -m "Fix AI Arena data pipeline coverage and fundamentals"
git push origin main
```

### 1. Run prune once to compact the existing huge latest.json

Workflow:

```text
AI Arena JP prune generated artifacts
```

Inputs:

```text
dry_run: false
commit_outputs: true
```

Expected log:

```text
compact_prices_latest
site/data/prices-jp/latest.json <= 5MB
fatal: pathspec 'data/cache' does not appear
```

### 2. Run season rebuild

Workflow:

```text
AI Arena JP season rebuild
```

Recommended inputs:

```text
year: 2026
start_date: 2026-01-01
end_date: blank
universe_limit: 300
run_mode: rebuild
reset_run: true
promote_display_run: true
enable_gpt_signal_notes: false
fetch_fundamentals: true
force_finalize_season: false
commit_outputs: true
```

Important: keep `force_finalize_season=false` during the year.  Otherwise open positions are forcibly closed.

### 3. Run data coverage review

Workflow:

```text
AI Arena JP data coverage review
```

Inputs:

```text
fail_on_critical: false
commit_outputs: true
min_bars_required: 60
stale_price_days: 5
min_fundamental_coverage_pct: 50
```

Check:

```text
site/data/japan/ai-arena/diagnostics/data-coverage-latest.md
site/data/japan/ai-arena/diagnostics/fundamentals-latest.json
```

## Pass criteria

- `site/data/prices-jp/latest.json` is under 5MB.
- `public_json_mode` is `summary`.
- `bars_omitted` is `true`.
- `arena_equity_curve` has rows for the run_id.
- `arena_orders` is present and has rows, unless no agent qualifies.
- Data coverage review no longer reports missing KYOU/NAGARE/etc. due to internal ID mismatch.
- `fundamentals_latest_jp` has rows.
- `value_features_daily` has rows for the latest covered feature date.
