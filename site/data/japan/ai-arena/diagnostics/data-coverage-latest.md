# Neon Tokyo Data Coverage Review

Generated: 2026-06-03T15:01:40+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 1797.262

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-02T16:27:27.749030 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-02T16:27:27.752719 |
| `build_id` | 26821090601-1 | 2026-06-02T16:27:27.737667 |
| `generated_at` | 2026-06-02T16:27:27+00:00 | 2026-06-02T16:27:27.735377 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-02T16:27:27.750773 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-02T16:27:27.730811 |
| `source_ref` | refs/heads/main | 2026-06-02T16:27:27.747153 |
| `source_run_attempt` | 1 | 2026-06-02T16:27:27.743607 |
| `source_run_id` | 26821090601 | 2026-06-02T16:27:27.741301 |
| `source_sha` | fb47ba986989e5523fc5645200ae3f4ef8c40489 | 2026-06-02T16:27:27.745376 |
| `source_workflow` | AI Arena JP live update | 2026-06-02T16:27:27.739444 |

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
- Rows: 292930
- Unique symbols: 860
- Date range: 2024-12-27 → 2026-06-02
- Insufficient bars symbols: 0
- Stale symbols: 4

## Features

- Table exists: True
- Rows: 292930
- Unique symbols: 860
- Latest date: 2026-06-02
- Latest date symbols: 776

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.706% | 292070 |
| `return_5d_pct` | 98.532% | 288630 |
| `return_20d_pct` | 94.128% | 275730 |
| `return_60d_pct` | 82.385% | 241330 |
| `volume_ratio_20d` | 98.826% | 289490 |
| `avg_traded_value_20d_jpy` | 98.826% | 289490 |
| `rsi_14` | 95.89% | 280890 |
| `range_position_252d_0_1` | 94.422% | 276590 |
| `liquidity_score` | 98.826% | 289490 |

## Agent Scores

- Table exists: True
- Rows: 384364
- Unique agents: 7
- Latest date: 2026-06-02
- Date count: 99
- Trade candidates: 57754
- Season window: 2026-01-01 → 2026-06-01
- Season date count: 98
- Season trade candidates: 57272

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 58906 | 99 | 1115 | 596 | 0.864 | 0.4233 | Ignore:43495, Watch:14296, Trade:1115 |
| KYOU / `daily_striker` | 66019 | 99 | 1347 | 730 | 0.9802 | 0.2925 | Ignore:60046, Watch:4626, Trade:1347 |
| SAGURI / `discovery_scout` | 18881 | 99 | 575 | 254 | 1.0 | 0.3183 | Ignore:16113, Watch:2193, Trade:575 |
| KAESHI / `reversal_snapback` | 66019 | 99 | 257 | 730 | 0.8939 | 0.2746 | Ignore:63166, Watch:2596, Trade:257 |
| MAMORU / `risk_sentinel` | 49614 | 99 | 40873 | 502 | 0.9907 | 0.7863 | Trade:40873, Watch:7758, Ignore:983 |
| HIZUMI / `value_mispricing` | 66019 | 99 | 5 | 730 | 0.6901 | 0.3213 | Ignore:60784, Watch:5230, Trade:5 |
| NAGARE / `weekly_sage` | 58906 | 99 | 13582 | 596 | 1.0 | 0.4449 | Ignore:37373, Trade:13582, Watch:7951 |

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
- Rows: 83129
- Unique tickers: 857
- Coverage vs universe: 99.651%
- Latest date: 2026-05-29
- Date count: 97
- Latest date tickers: 857
- Season date count: 97

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
| `arena_orders` | True | 16000 | 823 |
| `arena_open_positions` | True | 286 | 16 |
| `arena_trades` | True | 7649 | 393 |
| `arena_equity_curve` | True | 15680 | 686 |
| `arena_yearly_rankings` | True | 161 | 7 |
| `arena_monthly_rankings` | True | 861 | 42 |
| `arena_trade_rankings` | True | 880 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 52
- site/data total MB: 7.127
- prices latest MB: 2.764
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/prices-jp/latest.json` | 2.764 |
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/universe/jp_index_universe.json` | 0.421 |
| `site/data/japan/ai-arena/latest.json` | 0.242 |
| `site/data/japan/ai-arena/positions/latest.json` | 0.217 |
| `site/data/japan/ai-arena/summary/latest.json` | 0.214 |
| `site/data/japan/ai-arena/summary/2026/latest.json` | 0.214 |
| `site/data/japan/ai-arena/live/latest.json` | 0.203 |
| `site/data/japan/ai-arena/simulation/latest.json` | 0.203 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.2 |
| `site/data/japan/ai-arena/war-room/history/2026-06-03-close_council.json` | 0.2 |
| `site/data/japan/ai-arena/ranking/latest.json` | 0.196 |
| `site/data/japan/universe/jp_index_universe.csv` | 0.174 |
| `site/data/japan/ai-arena/discussion/latest.json` | 0.127 |
| `site/data/japan/agent-scores/latest.json` | 0.104 |
