# Neon Tokyo Data Coverage Review

Generated: 2026-05-29T02:52:01+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Executive Warnings

| Severity | Code | Message |
|---|---|---|
| warning | `LOW_FEATURE_LATEST_COVERAGE` | Latest feature-date symbol coverage is low. |
| warning | `LOW_FUNDAMENTAL_METRIC_COVERAGE` | per coverage is low. |
| warning | `LOW_FUNDAMENTAL_METRIC_COVERAGE` | pbr coverage is low. |
| warning | `LOW_FUNDAMENTAL_METRIC_COVERAGE` | roe_pct coverage is low. |
| warning | `LOW_FUNDAMENTAL_METRIC_COVERAGE` | market_cap_jpy coverage is low. |
| warning | `LOW_FUNDAMENTAL_ROW_COVERAGE` | Fundamental row coverage is low. |
| warning | `STALE_PRICE_SYMBOLS` | Some symbols are stale versus latest price date. |

## Universe

- DuckDB rows: 300
- DuckDB unique tickers: 300
- Suspicious tickers: 0
- CSV `jp_duckdb_trial_300`: exists=True rows=300 suspicious=0
- CSV `jp_index_universe`: exists=True rows=852 suspicious=0
- CSV `legacy_universe_jp`: exists=True rows=36 suspicious=0

## Prices

- Table exists: True
- Rows: 101797
- Unique symbols: 300
- Date range: 2024-12-25 → 2026-05-28
- Insufficient bars symbols: 0
- Stale symbols: 3

## Features

- Table exists: True
- Rows: 101797
- Unique symbols: 300
- Latest date: 2026-05-28
- Latest date symbols: 3

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.71% | 101497 |
| `return_5d_pct` | 98.53% | 100297 |
| `return_20d_pct` | 94.11% | 95797 |
| `return_60d_pct` | 82.32% | 83797 |
| `volume_ratio_20d` | 98.82% | 100597 |
| `avg_traded_value_20d_jpy` | 98.82% | 100597 |
| `rsi_14` | 95.87% | 97597 |
| `range_position_252d_0_1` | 94.4% | 96097 |
| `liquidity_score` | 98.82% | 100597 |

## Agent Scores

- Table exists: True
- Rows: 1395
- Unique agents: 7
- Latest date: 2026-05-27

| Agent | Rows | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 219 | 219 | N/A | N/A | Ignore:176, Watch:40, Trade:3 |
| KYOU / `daily_striker` | 239 | 239 | N/A | N/A | Ignore:209, Watch:26, Trade:4 |
| SAGURI / `discovery_scout` | 21 | 21 | N/A | N/A | Ignore:14, Watch:4, Trade:3 |
| KAESHI / `reversal_snapback` | 239 | 239 | N/A | N/A | Ignore:228, Watch:10, Trade:1 |
| MAMORU / `risk_sentinel` | 219 | 219 | N/A | N/A | Trade:184, Watch:32, Ignore:3 |
| HIZUMI / `value_mispricing` | 239 | 239 | N/A | N/A | Watch:114, Ignore:107, Trade:18 |
| NAGARE / `weekly_sage` | 219 | 219 | N/A | N/A | Ignore:167, Trade:33, Watch:19 |

## Company / Fundamentals

### `company_master_jp`

- Exists: False
- Rows: N/A
- Unique tickers: N/A
- Coverage vs universe: N/A%

### `fundamentals_latest_jp`

- Exists: False
- Rows: N/A
- Unique tickers: N/A
- Coverage vs universe: N/A%

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

## Arena Simulation Tables

| Table | Exists | Rows |
|---|---:|---:|
| `arena_simulation_runs` | False | N/A |
| `arena_display_runs` | False | N/A |
| `arena_orders` | False | N/A |
| `arena_open_positions` | False | N/A |
| `arena_trades` | False | N/A |
| `arena_equity_curve` | False | N/A |
| `arena_yearly_rankings` | False | N/A |
| `arena_monthly_rankings` | False | N/A |
| `arena_trade_rankings` | False | N/A |
| `agent_pick_notes_daily` | False | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 330
- site/data total MB: 133.728
- prices latest MB: 0.935
- dated prices JSON count: 0

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

