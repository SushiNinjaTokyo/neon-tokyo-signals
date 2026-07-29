# Neon Tokyo Data Coverage Review

Generated: 2026-07-29T12:16:37+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 848.012

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-07-26T22:05:49.910975 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-07-26T22:05:49.914590 |
| `build_id` | 30222242155-1 | 2026-07-26T22:05:49.900007 |
| `generated_at` | 2026-07-26T22:05:49+00:00 | 2026-07-26T22:05:49.897879 |
| `release_tag` | ai-arena-duckdb-latest | 2026-07-26T22:05:49.912748 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-07-26T22:05:49.893109 |
| `source_ref` | refs/heads/main | 2026-07-26T22:05:49.909199 |
| `source_run_attempt` | 1 | 2026-07-26T22:05:49.905607 |
| `source_run_id` | 30222242155 | 2026-07-26T22:05:49.903754 |
| `source_sha` | 2b7dd76e0d2653b10c69065c75388e4754afde5d | 2026-07-26T22:05:49.907457 |
| `source_workflow` | AI Arena JP fundamentals refresh | 2026-07-26T22:05:49.901805 |

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
- CSV `jp_index_universe`: exists=True rows=849 suspicious=0
- CSV `legacy_universe_jp`: exists=True rows=36 suspicious=0

## Prices

- Table exists: True
- Rows: 304696
- Unique symbols: 855
- Date range: 2025-01-06 → 2026-06-25
- Insufficient bars symbols: 0
- Stale symbols: 5

## Features

- Table exists: True
- Rows: 304696
- Unique symbols: 855
- Latest date: 2026-06-25
- Latest date symbols: 850

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.719% | 303841 |
| `return_5d_pct` | 98.597% | 300421 |
| `return_20d_pct` | 94.388% | 287596 |
| `return_60d_pct` | 83.164% | 253396 |
| `volume_ratio_20d` | 98.875% | 301269 |
| `avg_traded_value_20d_jpy` | 98.878% | 301276 |
| `rsi_14` | 96.071% | 292726 |
| `range_position_252d_0_1` | 94.668% | 288451 |
| `liquidity_score` | 98.878% | 301276 |

## Agent Scores

- Table exists: True
- Rows: 509581
- Unique agents: 7
- Latest date: 2026-06-25
- Date count: 116
- Trade candidates: 70053
- Season window: 2026-01-01 → 2026-06-25
- Season date count: 116
- Season trade candidates: 70053

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 99055 | 116 | 1716 | 855 | 0.874 | 0.372 | Ignore:79160, Watch:18179, Trade:1716 |
| KYOU / `daily_striker` | 76945 | 116 | 1476 | 732 | 0.9802 | 0.2883 | Ignore:70333, Watch:5136, Trade:1476 |
| SAGURI / `discovery_scout` | 21793 | 116 | 589 | 254 | 0.9806 | 0.3471 | Ignore:18700, Watch:2504, Trade:589 |
| KAESHI / `reversal_snapback` | 76945 | 116 | 251 | 732 | 0.917 | 0.3186 | Ignore:72841, Watch:3853, Trade:251 |
| MAMORU / `risk_sentinel` | 58843 | 116 | 47771 | 508 | 0.9907 | 0.7798 | Trade:47771, Watch:9526, Ignore:1546 |
| HIZUMI / `value_mispricing` | 76945 | 116 | 1 | 732 | 0.6809 | 0.3704 | Ignore:72317, Watch:4627, Trade:1 |
| NAGARE / `weekly_sage` | 99055 | 116 | 18249 | 855 | 1.0 | 0.363 | Ignore:70447, Trade:18249, Watch:10359 |

## Company / Fundamentals

### `company_master_jp`

- Exists: True
- Rows: 4014
- Unique tickers: 4014
- Coverage vs universe: 467.288%

### `fundamentals_latest_jp`

- Exists: True
- Rows: 859
- Unique tickers: 859
- Coverage vs universe: 100.0%

| Field | Coverage | Count |
|---|---:|---:|
| `market_cap_jpy` | 99.302% | 853 |
| `per` | 95.111% | 817 |
| `pbr` | 99.302% | 853 |
| `psr` | 98.37% | 845 |
| `roe_pct` | 95.111% | 817 |
| `roa_pct` | 94.994% | 816 |
| `operating_margin_pct` | 99.302% | 853 |
| `dividend_yield_pct` | 76.834% | 660 |

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
- Rows: 99644
- Unique tickers: 859
- Coverage vs universe: 100.0%
- Latest date: 2026-06-25
- Date count: 116
- Latest date tickers: 859
- Season date count: 116

## Arena Simulation Tables

- Live run: `arena_jp_live_2026`
- Live orders: 917
- Live trades: 440
- Live open positions: 11
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 1 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 917 | 917 |
| `arena_open_positions` | True | 11 | 11 |
| `arena_trades` | True | 440 | 440 |
| `arena_equity_curve` | True | 812 | 812 |
| `arena_yearly_rankings` | True | 7 | 7 |
| `arena_monthly_rankings` | True | 42 | 42 |
| `arena_trade_rankings` | True | 40 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 76
- site/data total MB: 17.665
- prices latest MB: 0.34
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/ai-arena/war-room/history/2026-06-20-weekly_arena_review.json` | 0.631 |
| `site/data/japan/ai-arena/war-room/history/2026-06-23-close_council.json` | 0.611 |
| `site/data/japan/ai-arena/war-room/history/2026-06-24-close_council.json` | 0.609 |
| `site/data/japan/ai-arena/war-room/history/2026-06-25-close_council.json` | 0.605 |
| `site/data/japan/ai-arena/war-room/history/2026-06-22-close_council.json` | 0.604 |
| `site/data/japan/ai-arena/war-room/history/2026-06-17-close_council.json` | 0.6 |
| `site/data/japan/ai-arena/war-room/history/2026-06-24-night_strategy_lab.json` | 0.595 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.589 |
| `site/data/japan/ai-arena/war-room/history/2026-06-25-night_strategy_lab.json` | 0.589 |
| `site/data/japan/ai-arena/war-room/history/2026-06-23-night_strategy_lab.json` | 0.588 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-close_council.json` | 0.588 |
| `site/data/japan/ai-arena/war-room/history/2026-06-19-close_council.json` | 0.587 |
| `site/data/japan/ai-arena/war-room/history/2026-06-10-close_council.json` | 0.576 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-close_council.json` | 0.571 |
