# HIZUMI Sector 33 Relative Value + Weekly Fundamentals Snapshot

## Files

- `scripts/fetch_jpx_listed_issues_jp.py`
- `scripts/build_company_master_jp.py`
- `scripts/stamp_fundamentals_snapshot_jp.py`
- `scripts/build_sector_relative_value_features_jp.py`
- `.github/workflows/ai-arena-jp-weekly-fundamentals-snapshot.yml`

## Recommended order

1. Add files and push.
2. Run `AI Arena JP weekly fundamentals snapshot` manually once.
3. Run `AI Arena JP data coverage review` with `fail_on_critical=true`.
4. Run `AI Arena JP season rebuild` after HIZUMI rule integration.

## What this enables

- `company_master_jp` populated with official JPX 33-sector metadata.
- `sector_33_valuation_medians` for PER/PBR/PSR/quality medians.
- `value_features_sector_relative_jp` and updated `value_features_daily` sector-relative columns.
- `fundamentals_snapshot_jp` weekly snapshots for future 3m/6m mispricing gap analysis.

## Important

This bundle starts the data foundation. HIZUMI scoring must read the new sector-relative columns in the agent score/profile layer to fully use the feature.
