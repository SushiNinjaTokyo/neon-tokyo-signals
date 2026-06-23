# Neon Tokyo Data Coverage Review

Generated: 2026-06-23T12:46:48+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 1439.762

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-23T12:40:27.505195 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-23T12:40:27.509362 |
| `build_id` | 28026124270-1 | 2026-06-23T12:40:27.492855 |
| `generated_at` | 2026-06-23T12:40:27+00:00 | 2026-06-23T12:40:27.490645 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-23T12:40:27.507288 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-23T12:40:27.485746 |
| `source_ref` | refs/heads/main | 2026-06-23T12:40:27.502373 |
| `source_run_attempt` | 1 | 2026-06-23T12:40:27.498553 |
| `source_run_id` | 28026124270 | 2026-06-23T12:40:27.496732 |
| `source_sha` | 0f859d21102ee0d2488977a68f2722f48d928b99 | 2026-06-23T12:40:27.500529 |
| `source_workflow` | AI Arena JP live update | 2026-06-23T12:40:27.494929 |

## Executive Warnings

| Severity | Code | Message |
|---|---|---|
| warning | `STALE_PRICE_SYMBOLS` | Some symbols are stale versus latest price date. |
| warning | `LOW_FUNDAMENTAL_METRIC_COVERAGE` | dividend_yield_pct coverage is low. |
| warning | `DATED_PRICE_JSON_REMAINING` | Dated prices JSON files remain under site/data/prices-jp. |

## Universe

- DuckDB rows: 859
- DuckDB unique tickers: 859
- Suspicious tickers: 0
- CSV `jp_duckdb_trial_300`: exists=True rows=859 suspicious=0
- CSV `jp_index_universe`: exists=True rows=851 suspicious=0
- CSV `legacy_universe_jp`: exists=True rows=36 suspicious=0

## Prices

- Table exists: True
- Rows: 302996
- Unique symbols: 855
- Date range: 2025-01-06 → 2026-06-23
- Insufficient bars symbols: 0
- Stale symbols: 5

## Features

- Table exists: True
- Rows: 302996
- Unique symbols: 855
- Latest date: 2026-06-23
- Latest date symbols: 850

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.718% | 302141 |
| `return_5d_pct` | 98.589% | 298721 |
| `return_20d_pct` | 94.356% | 285896 |
| `return_60d_pct` | 83.069% | 251696 |
| `volume_ratio_20d` | 98.869% | 299569 |
| `avg_traded_value_20d_jpy` | 98.871% | 299576 |
| `rsi_14` | 96.049% | 291026 |
| `range_position_252d_0_1` | 94.639% | 286751 |
| `liquidity_score` | 98.871% | 299576 |

## Agent Scores

- Table exists: True
- Rows: 501021
- Unique agents: 7
- Latest date: 2026-06-23
- Date count: 114
- Trade candidates: 68933
- Season window: 2026-01-01 → 2026-06-23
- Season date count: 114
- Season trade candidates: 68933

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 97355 | 114 | 1686 | 855 | 0.874 | 0.3723 | Ignore:77751, Watch:17918, Trade:1686 |
| KYOU / `daily_striker` | 75670 | 114 | 1462 | 731 | 0.9802 | 0.289 | Ignore:69123, Watch:5085, Trade:1462 |
| SAGURI / `discovery_scout` | 21472 | 114 | 575 | 254 | 0.99 | 0.3426 | Ignore:18488, Watch:2409, Trade:575 |
| KAESHI / `reversal_snapback` | 75670 | 114 | 251 | 731 | 0.917 | 0.3186 | Ignore:71618, Watch:3801, Trade:251 |
| MAMORU / `risk_sentinel` | 57829 | 114 | 46963 | 508 | 0.9907 | 0.7802 | Trade:46963, Watch:9348, Ignore:1518 |
| HIZUMI / `value_mispricing` | 75670 | 114 | 0 | 731 | 0.6705 | 0.2866 | Ignore:72866, Watch:2804 |
| NAGARE / `weekly_sage` | 97355 | 114 | 17996 | 855 | 1.0 | 0.3642 | Ignore:69113, Trade:17996, Watch:10246 |

## Company / Fundamentals

### `company_master_jp`

- Exists: True
- Rows: 0
- Unique tickers: 0
- Coverage vs universe: 0.0%

### `fundamentals_latest_jp`

- Exists: True
- Rows: 859
- Unique tickers: 859
- Coverage vs universe: 100.0%

| Field | Coverage | Count |
|---|---:|---:|
| `market_cap_jpy` | 61.816% | 531 |
| `per` | 58.789% | 505 |
| `pbr` | 61.7% | 530 |
| `psr` | 61.001% | 524 |
| `roe_pct` | 57.392% | 493 |
| `roa_pct` | 57.509% | 494 |
| `operating_margin_pct` | 61.816% | 531 |
| `dividend_yield_pct` | 46.217% | 397 |

### `fundamentals_latest`

- Exists: True
- Rows: 0
- Unique tickers: 0
- Coverage vs universe: 0.0%

| Field | Coverage | Count |
|---|---:|---:|
| `market_cap_jpy` | N/A% | 0 |
| `per` | N/A% | 0 |
| `pbr` | N/A% | 0 |
| `psr` | N/A% | 0 |
| `roe_pct` | N/A% | 0 |
| `roa_pct` | N/A% | 0 |
| `operating_margin_pct` | N/A% | 0 |
| `dividend_yield_pct` | N/A% | 0 |

### `value_features_daily`

- Exists: True
- Rows: 97926
- Unique tickers: 859
- Coverage vs universe: 100.0%
- Latest date: 2026-06-23
- Date count: 114
- Latest date tickers: 859
- Season date count: 114

## Arena Simulation Tables

- Live run: `arena_jp_live_2026`
- Live orders: 865
- Live trades: 413
- Live open positions: 13
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 1 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 865 | 865 |
| `arena_open_positions` | True | 13 | 13 |
| `arena_trades` | True | 413 | 413 |
| `arena_equity_curve` | True | 798 | 798 |
| `arena_yearly_rankings` | True | 7 | 7 |
| `arena_monthly_rankings` | True | 42 | 42 |
| `arena_trade_rankings` | True | 40 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 72
- site/data total MB: 15.312
- prices latest MB: 0.34
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/ai-arena/war-room/history/2026-06-20-weekly_arena_review.json` | 0.631 |
| `site/data/japan/ai-arena/war-room/history/2026-06-23-close_council.json` | 0.609 |
| `site/data/japan/ai-arena/war-room/history/2026-06-22-close_council.json` | 0.604 |
| `site/data/japan/ai-arena/war-room/history/2026-06-17-close_council.json` | 0.6 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.588 |
| `site/data/japan/ai-arena/war-room/history/2026-06-23-night_strategy_lab.json` | 0.588 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-close_council.json` | 0.588 |
| `site/data/japan/ai-arena/war-room/history/2026-06-19-close_council.json` | 0.587 |
| `site/data/japan/ai-arena/war-room/history/2026-06-10-close_council.json` | 0.576 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-close_council.json` | 0.571 |
| `site/data/japan/ai-arena/war-room/history/2026-06-19-night_strategy_lab.json` | 0.571 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-night_strategy_lab.json` | 0.569 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-night_strategy_lab.json` | 0.563 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-close_council.json` | 0.556 |
