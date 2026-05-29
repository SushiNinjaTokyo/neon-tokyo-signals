# Neon Tokyo Data Coverage Review

Generated: 2026-05-29T04:30:40+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 51.262

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-05-29T04:24:22.494280 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-05-29T04:24:22.498637 |
| `build_id` | 26617708460-1 | 2026-05-29T04:24:22.481488 |
| `generated_at` | 2026-05-29T04:24:22+00:00 | 2026-05-29T04:24:22.478951 |
| `release_tag` | ai-arena-duckdb-latest | 2026-05-29T04:24:22.496361 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-05-29T04:24:22.475209 |
| `source_ref` | refs/heads/main | 2026-05-29T04:24:22.492281 |
| `source_run_attempt` | 1 | 2026-05-29T04:24:22.488303 |
| `source_run_id` | 26617708460 | 2026-05-29T04:24:22.486323 |
| `source_sha` | 159d30f39e706fb90bc4c1e8f0b0ebd71e02cede | 2026-05-29T04:24:22.490357 |
| `source_workflow` | AI Arena JP season rebuild | 2026-05-29T04:24:22.484351 |

## Executive Warnings

| Severity | Code | Message |
|---|---|---|
| warning | `STALE_PRICE_SYMBOLS` | Some symbols are stale versus latest price date. |
| warning | `LOW_VALUE_FEATURE_ROW_COVERAGE` | value_features_daily row coverage is low. |
| warning | `EMPTY_ARENA_TABLE` | arena_orders table is empty. |
| warning | `EMPTY_ARENA_TABLE` | arena_open_positions table is empty. |
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
- Rows: 1399
- Unique agents: 7
- Latest date: 2026-05-29

| Agent | Rows | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 219 | 219 | N/A | N/A | Ignore:169, Watch:47, Trade:3 |
| KYOU / `daily_striker` | 240 | 240 | N/A | N/A | Ignore:212, Watch:23, Trade:5 |
| SAGURI / `discovery_scout` | 22 | 22 | N/A | N/A | Ignore:17, Watch:5 |
| KAESHI / `reversal_snapback` | 240 | 240 | N/A | N/A | Ignore:237, Watch:3 |
| MAMORU / `risk_sentinel` | 219 | 219 | N/A | N/A | Trade:195, Watch:20, Ignore:4 |
| HIZUMI / `value_mispricing` | 240 | 240 | N/A | N/A | Watch:116, Ignore:101, Trade:23 |
| NAGARE / `weekly_sage` | 219 | 219 | N/A | N/A | Ignore:164, Trade:31, Watch:24 |

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
- Rows: 0
- Unique tickers: 0
- Coverage vs universe: 0.0%
- Latest date: N/A

## Arena Simulation Tables

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 1 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 0 | 0 |
| `arena_open_positions` | True | 0 | 0 |
| `arena_trades` | True | 0 | 0 |
| `arena_equity_curve` | True | 679 | 679 |
| `arena_yearly_rankings` | True | 7 | N/A |
| `arena_monthly_rankings` | True | 35 | N/A |
| `arena_trade_rankings` | True | 0 | N/A |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 330
- site/data total MB: 133.402
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
