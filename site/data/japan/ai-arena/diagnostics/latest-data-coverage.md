# Neon Tokyo Data Coverage Review

Generated: 2026-06-18T13:40:35+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 1392.262

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-18T12:57:18.934589 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-18T12:57:18.938090 |
| `build_id` | 27760329815-1 | 2026-06-18T12:57:18.923162 |
| `generated_at` | 2026-06-18T12:57:18+00:00 | 2026-06-18T12:57:18.920408 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-18T12:57:18.936305 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-18T12:57:18.915053 |
| `source_ref` | refs/heads/main | 2026-06-18T12:57:18.932797 |
| `source_run_attempt` | 1 | 2026-06-18T12:57:18.928988 |
| `source_run_id` | 27760329815 | 2026-06-18T12:57:18.927127 |
| `source_sha` | 18fdf735cfc305318143ba67f46bb1aaa8316394 | 2026-06-18T12:57:18.930880 |
| `source_workflow` | AI Arena JP live update | 2026-06-18T12:57:18.925261 |

## Executive Warnings

| Severity | Code | Message |
|---|---|---|
| warning | `STALE_PRICE_SYMBOLS` | Some symbols are stale versus latest price date. |
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
- Rows: 300278
- Unique symbols: 855
- Date range: 2025-01-06 → 2026-06-18
- Insufficient bars symbols: 0
- Stale symbols: 4

## Features

- Table exists: True
- Rows: 300278
- Unique symbols: 855
- Latest date: 2026-06-18
- Latest date symbols: 850

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.715% | 299423 |
| `return_5d_pct` | 98.576% | 296003 |
| `return_20d_pct` | 94.305% | 283178 |
| `return_60d_pct` | 82.916% | 248978 |
| `volume_ratio_20d` | 98.859% | 296851 |
| `avg_traded_value_20d_jpy` | 98.861% | 296858 |
| `rsi_14` | 96.014% | 288308 |
| `range_position_252d_0_1` | 94.59% | 284033 |
| `liquidity_score` | 98.861% | 296858 |

## Agent Scores

- Table exists: True
- Rows: 487503
- Unique agents: 7
- Latest date: 2026-06-18
- Date count: 111
- Trade candidates: 67216
- Season window: 2026-01-01 → 2026-06-18
- Season date count: 111
- Season trade candidates: 67216

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 94637 | 111 | 1681 | 855 | 0.874 | 0.3733 | Ignore:75481, Watch:17475, Trade:1681 |
| KYOU / `daily_striker` | 73674 | 111 | 1442 | 731 | 0.9802 | 0.2895 | Ignore:67244, Watch:4988, Trade:1442 |
| SAGURI / `discovery_scout` | 20911 | 111 | 587 | 254 | 0.9805 | 0.3494 | Ignore:17864, Watch:2460, Trade:587 |
| KAESHI / `reversal_snapback` | 73674 | 111 | 247 | 731 | 0.917 | 0.3192 | Ignore:69685, Watch:3742, Trade:247 |
| MAMORU / `risk_sentinel` | 56296 | 111 | 45725 | 508 | 0.9907 | 0.7805 | Trade:45725, Watch:9086, Ignore:1485 |
| HIZUMI / `value_mispricing` | 73674 | 111 | 0 | 731 | 0.6706 | 0.3674 | Ignore:69540, Watch:4134 |
| NAGARE / `weekly_sage` | 94637 | 111 | 17534 | 855 | 1.0 | 0.3656 | Ignore:67044, Trade:17534, Watch:10059 |

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
| `market_cap_jpy` | 99.418% | 854 |
| `per` | 95.111% | 817 |
| `pbr` | 99.418% | 854 |
| `psr` | 98.603% | 847 |
| `roe_pct` | 92.317% | 793 |
| `roa_pct` | 92.317% | 793 |
| `operating_margin_pct` | 99.534% | 855 |
| `dividend_yield_pct` | 54.016% | 464 |

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
- Rows: 95349
- Unique tickers: 859
- Coverage vs universe: 100.0%
- Latest date: 2026-06-18
- Date count: 111
- Latest date tickers: 859
- Season date count: 111

## Arena Simulation Tables

- Live run: `arena_jp_live_2026`
- Live orders: 876
- Live trades: 419
- Live open positions: 14
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 1 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 876 | 876 |
| `arena_open_positions` | True | 14 | 14 |
| `arena_trades` | True | 419 | 419 |
| `arena_equity_curve` | True | 777 | 777 |
| `arena_yearly_rankings` | True | 7 | 7 |
| `arena_monthly_rankings` | True | 42 | 42 |
| `arena_trade_rankings` | True | 40 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 66
- site/data total MB: 11.652
- prices latest MB: 0.34
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/ai-arena/war-room/history/2026-06-17-close_council.json` | 0.6 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-close_council.json` | 0.592 |
| `site/data/japan/ai-arena/war-room/history/2026-06-10-close_council.json` | 0.576 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-close_council.json` | 0.571 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.569 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-night_strategy_lab.json` | 0.569 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-night_strategy_lab.json` | 0.563 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-close_council.json` | 0.556 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-night_strategy_lab.json` | 0.53 |
| `site/data/japan/ai-arena/war-room/history/2026-06-06-weekly_arena_review.json` | 0.471 |
| `site/data/japan/universe/jp_index_universe.json` | 0.421 |
| `site/data/japan/ai-arena/war-room/history/2026-06-05-close_council.json` | 0.399 |
| `site/data/japan/ai-arena/war-room/history/2026-06-05-night_strategy_lab.json` | 0.378 |
| `site/data/japan/ai-arena/war-room/history/2026-06-04-night_strategy_lab.json` | 0.347 |
