# Neon Tokyo Data Coverage Review

Generated: 2026-05-29T05:26:57+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 163.012

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-05-29T05:17:07.991464 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-05-29T05:17:07.995661 |
| `build_id` | 26619470846-1 | 2026-05-29T05:17:07.979677 |
| `generated_at` | 2026-05-29T05:17:07+00:00 | 2026-05-29T05:17:07.977388 |
| `release_tag` | ai-arena-duckdb-latest | 2026-05-29T05:17:07.993433 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-05-29T05:17:07.972617 |
| `source_ref` | refs/heads/main | 2026-05-29T05:17:07.989479 |
| `source_run_attempt` | 1 | 2026-05-29T05:17:07.985744 |
| `source_run_id` | 26619470846 | 2026-05-29T05:17:07.983652 |
| `source_sha` | 488cc0d0a2e1682cd9b69e486bb2f19711a63820 | 2026-05-29T05:17:07.987555 |
| `source_workflow` | AI Arena JP season rebuild | 2026-05-29T05:17:07.981552 |

## Executive Warnings

| Severity | Code | Message |
|---|---|---|
| warning | `STALE_PRICE_SYMBOLS` | Some symbols are stale versus latest price date. |
| warning | `DATED_PRICE_JSON_REMAINING` | Dated prices JSON files remain under site/data/prices-jp. |

## Universe

- DuckDB rows: 301
- DuckDB unique tickers: 301
- Suspicious tickers: 0
- CSV `jp_duckdb_trial_300`: exists=True rows=300 suspicious=0
- CSV `jp_index_universe`: exists=True rows=852 suspicious=0
- CSV `legacy_universe_jp`: exists=True rows=36 suspicious=0

## Prices

- Table exists: True
- Rows: 102729
- Unique symbols: 301
- Date range: 2024-12-25 → 2026-05-29
- Insufficient bars symbols: 0
- Stale symbols: 3

## Features

- Table exists: True
- Rows: 102729
- Unique symbols: 301
- Latest date: 2026-05-29
- Latest date symbols: 295

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.707% | 102428 |
| `return_5d_pct` | 98.535% | 101224 |
| `return_20d_pct` | 94.14% | 96709 |
| `return_60d_pct` | 82.42% | 84669 |
| `volume_ratio_20d` | 98.828% | 101525 |
| `avg_traded_value_20d_jpy` | 98.828% | 101525 |
| `rsi_14` | 95.898% | 98515 |
| `range_position_252d_0_1` | 94.433% | 97010 |
| `liquidity_score` | 98.828% | 101525 |

## Agent Scores

- Table exists: True
- Rows: 137361
- Unique agents: 7
- Latest date: 2026-05-29
- Date count: 97
- Trade candidates: 28764
- Season window: 2026-01-01 → 2026-05-29
- Season date count: 97
- Season trade candidates: 28764

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 21326 | 97 | 716 | 220 | 0.9005 | 0.4552 | Ignore:14269, Watch:6341, Trade:716 |
| KYOU / `daily_striker` | 23561 | 97 | 621 | 258 | 0.9492 | 0.3417 | Ignore:21262, Watch:1678, Trade:621 |
| SAGURI / `discovery_scout` | 2703 | 97 | 167 | 45 | 0.9937 | 0.3875 | Ignore:2026, Watch:510, Trade:167 |
| KAESHI / `reversal_snapback` | 23561 | 97 | 103 | 258 | 0.7978 | 0.2743 | Ignore:22370, Watch:1088, Trade:103 |
| MAMORU / `risk_sentinel` | 21323 | 97 | 18814 | 220 | 0.9888 | 0.8013 | Trade:18814, Watch:2333, Ignore:176 |
| HIZUMI / `value_mispricing` | 23561 | 97 | 2639 | 258 | 0.8294 | 0.5525 | Watch:13577, Ignore:7345, Trade:2639 |
| NAGARE / `weekly_sage` | 21326 | 97 | 5704 | 220 | 1.0 | 0.4783 | Ignore:12712, Trade:5704, Watch:2910 |

## Company / Fundamentals

### `company_master_jp`

- Exists: True
- Rows: 0
- Unique tickers: 0
- Coverage vs universe: 0.0%

### `fundamentals_latest_jp`

- Exists: True
- Rows: 298
- Unique tickers: 298
- Coverage vs universe: 99.003%

| Field | Coverage | Count |
|---|---:|---:|
| `market_cap_jpy` | 100.0% | 298 |
| `per` | 96.309% | 287 |
| `pbr` | 99.664% | 297 |
| `psr` | 99.329% | 296 |
| `roe_pct` | 91.275% | 272 |
| `roa_pct` | 90.94% | 271 |
| `operating_margin_pct` | 100.0% | 298 |
| `dividend_yield_pct` | 82.215% | 245 |

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
- Rows: 28906
- Unique tickers: 298
- Coverage vs universe: 99.003%
- Latest date: 2026-05-29
- Date count: 97
- Latest date tickers: 298
- Season date count: 97

## Arena Simulation Tables

- Live run: `arena_jp_rebuild_2026_v003`
- Live orders: 601
- Live trades: 291
- Live open positions: 7
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 3 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 1202 | 601 |
| `arena_open_positions` | True | 14 | 7 |
| `arena_trades` | True | 582 | 291 |
| `arena_equity_curve` | True | 2037 | 679 |
| `arena_yearly_rankings` | True | 21 | 7 |
| `arena_monthly_rankings` | True | 105 | 35 |
| `arena_trade_rankings` | True | 80 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 331
- site/data total MB: 133.843
- prices latest MB: 0.935
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/backtest-daily-jp/latest.json` | 28.595 |
| `site/data/backtest-daily-jp/2026-05-28.json` | 28.595 |
| `site/data/japan/weekly/backtest/2026-05-26.json` | 1.298 |
| `site/data/weekly-jp/backtest/2026-05-26.json` | 1.298 |
| `site/data/japan/weekly/backtest/2026-05-20.json` | 1.297 |
| `site/data/weekly-jp/backtest/2026-05-20.json` | 1.297 |
| `site/data/prices-jp/latest.json` | 0.935 |
| `site/data/japan/weekly/backtest/latest.json` | 0.423 |
| `site/data/japan/weekly/backtest/2026-05-29.json` | 0.423 |
| `site/data/weekly-jp/backtest/latest.json` | 0.423 |
| `site/data/weekly-jp/backtest/2026-05-29.json` | 0.423 |
| `site/data/japan/universe/jp_index_universe.json` | 0.422 |
| `site/data/daily-jp/latest.json` | 0.293 |
| `site/data/daily-jp/2026-05-28.json` | 0.293 |
| `site/data/daily-jp/2026-05-29.json` | 0.293 |
