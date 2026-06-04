# Neon Tokyo Data Coverage Review

Generated: 2026-06-04T12:54:08+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 1911.762

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-03T17:44:49.444514 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-03T17:44:49.448082 |
| `build_id` | 26890495078-1 | 2026-06-03T17:44:49.433475 |
| `generated_at` | 2026-06-03T17:44:49+00:00 | 2026-06-03T17:44:49.431424 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-03T17:44:49.446321 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-03T17:44:49.426987 |
| `source_ref` | refs/heads/main | 2026-06-03T17:44:49.442619 |
| `source_run_attempt` | 1 | 2026-06-03T17:44:49.439088 |
| `source_run_id` | 26890495078 | 2026-06-03T17:44:49.437322 |
| `source_sha` | ecfd99966e1b2ef809bb60e5547b5fa6b1aef41a | 2026-06-03T17:44:49.440793 |
| `source_workflow` | AI Arena JP live update | 2026-06-03T17:44:49.435393 |

## Executive Warnings

| Severity | Code | Message |
|---|---|---|
| warning | `STALE_PRICE_SYMBOLS` | Some symbols are stale versus latest price date. |
| warning | `DATED_PRICE_JSON_REMAINING` | Dated prices JSON files remain under site/data/prices-jp. |

## Universe

- DuckDB rows: 860
- DuckDB unique tickers: 860
- Suspicious tickers: 0
- CSV `jp_duckdb_trial_300`: exists=True rows=859 suspicious=0
- CSV `jp_index_universe`: exists=True rows=851 suspicious=0
- CSV `legacy_universe_jp`: exists=True rows=36 suspicious=0

## Prices

- Table exists: True
- Rows: 293709
- Unique symbols: 860
- Date range: 2024-12-27 → 2026-06-03
- Insufficient bars symbols: 0
- Stale symbols: 5

## Features

- Table exists: True
- Rows: 293709
- Unique symbols: 860
- Latest date: 2026-06-03
- Latest date symbols: 701

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.707% | 292849 |
| `return_5d_pct` | 98.536% | 289409 |
| `return_20d_pct` | 94.144% | 276509 |
| `return_60d_pct` | 82.432% | 242109 |
| `volume_ratio_20d` | 98.829% | 290269 |
| `avg_traded_value_20d_jpy` | 98.829% | 290269 |
| `rsi_14` | 95.901% | 281669 |
| `range_position_252d_0_1` | 94.437% | 277369 |
| `liquidity_score` | 98.829% | 290269 |

## Agent Scores

- Table exists: True
- Rows: 388035
- Unique agents: 7
- Latest date: 2026-06-03
- Date count: 100
- Trade candidates: 58311
- Season window: 2026-01-01 → 2026-06-01
- Season date count: 98
- Season trade candidates: 57272

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 59484 | 100 | 1120 | 596 | 0.864 | 0.423 | Ignore:43945, Watch:14419, Trade:1120 |
| KYOU / `daily_striker` | 66643 | 100 | 1366 | 731 | 0.9802 | 0.2925 | Ignore:60598, Watch:4679, Trade:1366 |
| SAGURI / `discovery_scout` | 19024 | 100 | 575 | 255 | 1.0 | 0.3166 | Ignore:16254, Watch:2195, Trade:575 |
| KAESHI / `reversal_snapback` | 66643 | 100 | 257 | 731 | 0.8939 | 0.2724 | Ignore:63790, Watch:2596, Trade:257 |
| MAMORU / `risk_sentinel` | 50114 | 100 | 41282 | 502 | 0.9907 | 0.786 | Trade:41282, Watch:7834, Ignore:998 |
| HIZUMI / `value_mispricing` | 66643 | 100 | 5 | 731 | 0.6901 | 0.3172 | Ignore:61408, Watch:5230, Trade:5 |
| NAGARE / `weekly_sage` | 59484 | 100 | 13706 | 596 | 1.0 | 0.4445 | Ignore:37774, Trade:13706, Watch:8004 |

## Company / Fundamentals

### `company_master_jp`

- Exists: True
- Rows: 4052
- Unique tickers: 4052
- Coverage vs universe: 471.163%

### `fundamentals_latest_jp`

- Exists: True
- Rows: 857
- Unique tickers: 857
- Coverage vs universe: 99.651%

| Field | Coverage | Count |
|---|---:|---:|
| `market_cap_jpy` | 99.883% | 856 |
| `per` | 95.449% | 818 |
| `pbr` | 99.883% | 856 |
| `psr` | 99.067% | 849 |
| `roe_pct` | 92.299% | 791 |
| `roa_pct` | 92.299% | 791 |
| `operating_margin_pct` | 100.0% | 857 |
| `dividend_yield_pct` | 77.363% | 663 |

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
- Rows: 84843
- Unique tickers: 857
- Coverage vs universe: 99.651%
- Latest date: 2026-06-02
- Date count: 99
- Latest date tickers: 857
- Season date count: 98

## Arena Simulation Tables

- Live run: `arena_jp_rebuild_2026_v022`
- Live orders: 823
- Live trades: 393
- Live open positions: 16
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 23 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 16006 | 823 |
| `arena_open_positions` | True | 285 | 16 |
| `arena_trades` | True | 7652 | 393 |
| `arena_equity_curve` | True | 15687 | 686 |
| `arena_yearly_rankings` | True | 161 | 7 |
| `arena_monthly_rankings` | True | 861 | 42 |
| `arena_trade_rankings` | True | 880 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 54
- site/data total MB: 7.992
- prices latest MB: 2.764
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/prices-jp/latest.json` | 2.764 |
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/universe/jp_index_universe.json` | 0.421 |
| `site/data/japan/ai-arena/war-room/history/2026-06-04-close_council.json` | 0.357 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.347 |
| `site/data/japan/ai-arena/war-room/history/2026-06-04-night_strategy_lab.json` | 0.347 |
| `site/data/japan/ai-arena/latest.json` | 0.242 |
| `site/data/japan/ai-arena/positions/latest.json` | 0.217 |
| `site/data/japan/ai-arena/summary/latest.json` | 0.214 |
| `site/data/japan/ai-arena/summary/2026/latest.json` | 0.214 |
| `site/data/japan/ai-arena/live/latest.json` | 0.203 |
| `site/data/japan/ai-arena/simulation/latest.json` | 0.203 |
| `site/data/japan/ai-arena/war-room/history/2026-06-03-close_council.json` | 0.2 |
| `site/data/japan/ai-arena/ranking/latest.json` | 0.196 |
| `site/data/japan/universe/jp_index_universe.csv` | 0.174 |
