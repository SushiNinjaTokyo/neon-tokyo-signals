# Neon Tokyo Data Coverage Review

Generated: 2026-05-31T13:17:01+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 777.012

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-05-31T13:11:56.124146 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-05-31T13:11:56.128531 |
| `build_id` | 26713473544-1 | 2026-05-31T13:11:56.112955 |
| `generated_at` | 2026-05-31T13:11:55+00:00 | 2026-05-31T13:11:56.110876 |
| `release_tag` | ai-arena-duckdb-latest | 2026-05-31T13:11:56.126701 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-05-31T13:11:56.106449 |
| `source_ref` | refs/heads/main | 2026-05-31T13:11:56.122180 |
| `source_run_attempt` | 1 | 2026-05-31T13:11:56.118515 |
| `source_run_id` | 26713473544 | 2026-05-31T13:11:56.116637 |
| `source_sha` | bd45b60c7e251e86652b8c3c697c820611ffd923 | 2026-05-31T13:11:56.120391 |
| `source_workflow` | AI Arena JP live update | 2026-05-31T13:11:56.114823 |

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
- Rows: 102163
- Unique symbols: 301
- Date range: 2024-12-27 → 2026-05-29
- Insufficient bars symbols: 0
- Stale symbols: 3

## Features

- Table exists: True
- Rows: 102163
- Unique symbols: 301
- Latest date: 2026-05-29
- Latest date symbols: 298

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.705% | 101862 |
| `return_5d_pct` | 98.527% | 100658 |
| `return_20d_pct` | 94.107% | 96143 |
| `return_60d_pct` | 82.322% | 84103 |
| `volume_ratio_20d` | 98.821% | 100959 |
| `avg_traded_value_20d_jpy` | 98.821% | 100959 |
| `rsi_14` | 95.875% | 97949 |
| `range_position_252d_0_1` | 94.402% | 96444 |
| `liquidity_score` | 98.821% | 100959 |

## Agent Scores

- Table exists: True
- Rows: 137364
- Unique agents: 7
- Latest date: 2026-05-29
- Date count: 97
- Trade candidates: 26228
- Season window: 2026-01-01 → 2026-05-29
- Season date count: 97
- Season trade candidates: 26228

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 21326 | 97 | 512 | 220 | 0.864 | 0.4384 | Ignore:15114, Watch:5700, Trade:512 |
| KYOU / `daily_striker` | 23562 | 97 | 464 | 258 | 0.9802 | 0.2983 | Ignore:21360, Watch:1738, Trade:464 |
| SAGURI / `discovery_scout` | 2703 | 97 | 139 | 45 | 0.9296 | 0.3897 | Ignore:2053, Watch:511, Trade:139 |
| KAESHI / `reversal_snapback` | 23562 | 97 | 103 | 258 | 0.7978 | 0.2747 | Ignore:22370, Watch:1089, Trade:103 |
| MAMORU / `risk_sentinel` | 21323 | 97 | 17180 | 220 | 0.9907 | 0.7836 | Trade:17180, Watch:3681, Ignore:462 |
| HIZUMI / `value_mispricing` | 23562 | 97 | 2125 | 258 | 0.8234 | 0.5311 | Watch:12905, Ignore:8532, Trade:2125 |
| NAGARE / `weekly_sage` | 21326 | 97 | 5705 | 220 | 1.0 | 0.4782 | Ignore:12714, Trade:5705, Watch:2907 |

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

- Live run: `arena_jp_live_2026`
- Live orders: 667
- Live trades: 316
- Live open positions: 15
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 16 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 9906 | 667 |
| `arena_open_positions` | True | 177 | 15 |
| `arena_trades` | True | 4733 | 316 |
| `arena_equity_curve` | True | 10864 | 679 |
| `arena_yearly_rankings` | True | 112 | 7 |
| `arena_monthly_rankings` | True | 560 | 35 |
| `arena_trade_rankings` | True | 600 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 334
- site/data total MB: 134.007
- prices latest MB: 0.936
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/backtest-daily-jp/latest.json` | 28.595 |
| `site/data/backtest-daily-jp/2026-05-28.json` | 28.595 |
| `site/data/japan/weekly/backtest/2026-05-26.json` | 1.298 |
| `site/data/weekly-jp/backtest/2026-05-26.json` | 1.298 |
| `site/data/japan/weekly/backtest/2026-05-20.json` | 1.297 |
| `site/data/weekly-jp/backtest/2026-05-20.json` | 1.297 |
| `site/data/prices-jp/latest.json` | 0.936 |
| `site/data/japan/weekly/backtest/latest.json` | 0.423 |
| `site/data/japan/weekly/backtest/2026-05-29.json` | 0.423 |
| `site/data/weekly-jp/backtest/latest.json` | 0.423 |
| `site/data/weekly-jp/backtest/2026-05-29.json` | 0.423 |
| `site/data/japan/universe/jp_index_universe.json` | 0.422 |
| `site/data/daily-jp/latest.json` | 0.293 |
| `site/data/daily-jp/2026-05-28.json` | 0.293 |
| `site/data/daily-jp/2026-05-29.json` | 0.293 |
