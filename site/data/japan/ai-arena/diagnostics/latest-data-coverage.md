# Neon Tokyo Data Coverage Review

Generated: 2026-06-22T15:32:42+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 277.512

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-22T15:30:05.390497 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-22T15:30:05.394845 |
| `build_id` | 27963017838-1 | 2026-06-22T15:30:05.370571 |
| `generated_at` | 2026-06-22T15:30:05+00:00 | 2026-06-22T15:30:05.368144 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-22T15:30:05.392626 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-22T15:30:05.364448 |
| `source_ref` | refs/heads/main | 2026-06-22T15:30:05.387720 |
| `source_run_attempt` | 1 | 2026-06-22T15:30:05.377668 |
| `source_run_id` | 27963017838 | 2026-06-22T15:30:05.375354 |
| `source_sha` | df42fdf5dba70fca23ed6424e054bd7d955d4295 | 2026-06-22T15:30:05.379720 |
| `source_workflow` | AI Arena JP live update | 2026-06-22T15:30:05.372900 |

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
- Rows: 301296
- Unique symbols: 855
- Date range: 2025-01-06 → 2026-06-19
- Insufficient bars symbols: 0
- Stale symbols: 4

## Features

- Table exists: True
- Rows: 301296
- Unique symbols: 855
- Latest date: 2026-06-19
- Latest date symbols: 850

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.716% | 300441 |
| `return_5d_pct` | 98.581% | 297021 |
| `return_20d_pct` | 94.325% | 284196 |
| `return_60d_pct` | 82.974% | 249996 |
| `volume_ratio_20d` | 98.863% | 297869 |
| `avg_traded_value_20d_jpy` | 98.865% | 297876 |
| `rsi_14` | 96.027% | 289326 |
| `range_position_252d_0_1` | 94.608% | 285051 |
| `liquidity_score` | 98.865% | 297876 |

## Agent Scores

- Table exists: True
- Rows: 492438
- Unique agents: 7
- Latest date: 2026-06-19
- Date count: 112
- Trade candidates: 67791
- Season window: 2026-01-01 → 2026-06-19
- Season date count: 112
- Season trade candidates: 67791

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 95655 | 112 | 1680 | 855 | 0.874 | 0.3727 | Ignore:76356, Watch:17619, Trade:1680 |
| KYOU / `daily_striker` | 74388 | 112 | 1447 | 731 | 0.9802 | 0.2893 | Ignore:67925, Watch:5016, Trade:1447 |
| SAGURI / `discovery_scout` | 21149 | 112 | 574 | 254 | 0.99 | 0.3434 | Ignore:18182, Watch:2393, Trade:574 |
| KAESHI / `reversal_snapback` | 74388 | 112 | 249 | 731 | 0.917 | 0.3191 | Ignore:70365, Watch:3774, Trade:249 |
| MAMORU / `risk_sentinel` | 56815 | 112 | 46144 | 508 | 0.9907 | 0.7804 | Trade:46144, Watch:9173, Ignore:1498 |
| HIZUMI / `value_mispricing` | 74388 | 112 | 0 | 731 | 0.6705 | 0.2867 | Ignore:71619, Watch:2769 |
| NAGARE / `weekly_sage` | 95655 | 112 | 17697 | 855 | 1.0 | 0.3649 | Ignore:67833, Trade:17697, Watch:10125 |

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
- Rows: 96208
- Unique tickers: 859
- Coverage vs universe: 100.0%
- Latest date: 2026-06-19
- Date count: 112
- Latest date tickers: 859
- Season date count: 112

## Arena Simulation Tables

- Live run: `arena_jp_live_2026`
- Live orders: 840
- Live trades: 402
- Live open positions: 12
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 1 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 840 | 840 |
| `arena_open_positions` | True | 12 | 12 |
| `arena_trades` | True | 402 | 402 |
| `arena_equity_curve` | True | 784 | 784 |
| `arena_yearly_rankings` | True | 7 | 7 |
| `arena_monthly_rankings` | True | 42 | 42 |
| `arena_trade_rankings` | True | 40 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 71
- site/data total MB: 14.675
- prices latest MB: 0.34
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/ai-arena/war-room/history/2026-06-20-weekly_arena_review.json` | 0.631 |
| `site/data/japan/ai-arena/war-room/history/2026-06-22-close_council.json` | 0.604 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.6 |
| `site/data/japan/ai-arena/war-room/history/2026-06-23-close_council.json` | 0.6 |
| `site/data/japan/ai-arena/war-room/history/2026-06-17-close_council.json` | 0.6 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-close_council.json` | 0.588 |
| `site/data/japan/ai-arena/war-room/history/2026-06-19-close_council.json` | 0.587 |
| `site/data/japan/ai-arena/war-room/history/2026-06-10-close_council.json` | 0.576 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-close_council.json` | 0.571 |
| `site/data/japan/ai-arena/war-room/history/2026-06-19-night_strategy_lab.json` | 0.571 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-night_strategy_lab.json` | 0.569 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-night_strategy_lab.json` | 0.563 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-close_council.json` | 0.556 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-night_strategy_lab.json` | 0.53 |
