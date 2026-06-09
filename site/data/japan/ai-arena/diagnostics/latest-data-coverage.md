# Neon Tokyo Data Coverage Review

Generated: 2026-06-09T12:50:49+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 2794.512

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-09T12:41:58.448047 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-09T12:41:58.452015 |
| `build_id` | 27206221502-1 | 2026-06-09T12:41:58.435748 |
| `generated_at` | 2026-06-09T12:41:58+00:00 | 2026-06-09T12:41:58.433535 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-09T12:41:58.449962 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-09T12:41:58.427428 |
| `source_ref` | refs/heads/main | 2026-06-09T12:41:58.445941 |
| `source_run_attempt` | 1 | 2026-06-09T12:41:58.442000 |
| `source_run_id` | 27206221502 | 2026-06-09T12:41:58.440170 |
| `source_sha` | 7a24a6c7d2d08ee4dda270cac8a078de895d90d8 | 2026-06-09T12:41:58.443852 |
| `source_workflow` | AI Arena JP live update | 2026-06-09T12:41:58.438079 |

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
- Rows: 297265
- Unique symbols: 860
- Date range: 2024-12-27 → 2026-06-09
- Insufficient bars symbols: 0
- Stale symbols: 9

## Features

- Table exists: True
- Rows: 297265
- Unique symbols: 860
- Latest date: 2026-06-09
- Latest date symbols: 850

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.711% | 296405 |
| `return_5d_pct` | 98.553% | 292965 |
| `return_20d_pct` | 94.214% | 280065 |
| `return_60d_pct` | 82.642% | 245665 |
| `volume_ratio_20d` | 98.843% | 293825 |
| `avg_traded_value_20d_jpy` | 98.843% | 293825 |
| `rsi_14` | 95.95% | 285225 |
| `range_position_252d_0_1` | 94.503% | 280925 |
| `liquidity_score` | 98.843% | 293825 |

## Agent Scores

- Table exists: True
- Rows: 403967
- Unique agents: 7
- Latest date: 2026-06-09
- Date count: 104
- Trade candidates: 60435
- Season window: 2026-01-01 → 2026-06-09
- Season date count: 104
- Season trade candidates: 60435

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 61949 | 104 | 1225 | 596 | 0.8886 | 0.4226 | Ignore:45784, Watch:14940, Trade:1225 |
| KYOU / `daily_striker` | 69367 | 104 | 1383 | 732 | 0.9802 | 0.2908 | Ignore:63223, Watch:4761, Trade:1383 |
| SAGURI / `discovery_scout` | 19854 | 104 | 581 | 255 | 1.0 | 0.3147 | Ignore:17020, Watch:2253, Trade:581 |
| KAESHI / `reversal_snapback` | 69367 | 104 | 259 | 732 | 0.8939 | 0.2744 | Ignore:66367, Watch:2741, Trade:259 |
| MAMORU / `risk_sentinel` | 52114 | 104 | 42858 | 502 | 0.9907 | 0.7849 | Trade:42858, Watch:8185, Ignore:1071 |
| HIZUMI / `value_mispricing` | 69367 | 104 | 3 | 732 | 0.6906 | 0.3163 | Ignore:64140, Watch:5224, Trade:3 |
| NAGARE / `weekly_sage` | 61949 | 104 | 14126 | 596 | 1.0 | 0.4416 | Ignore:39566, Trade:14126, Watch:8257 |

## Company / Fundamentals

### `company_master_jp`

- Exists: True
- Rows: 4038
- Unique tickers: 4038
- Coverage vs universe: 469.535%

### `fundamentals_latest_jp`

- Exists: True
- Rows: 857
- Unique tickers: 857
- Coverage vs universe: 99.651%

| Field | Coverage | Count |
|---|---:|---:|
| `market_cap_jpy` | 100.0% | 857 |
| `per` | 95.449% | 818 |
| `pbr` | 99.883% | 856 |
| `psr` | 99.183% | 850 |
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
- Rows: 89128
- Unique tickers: 857
- Coverage vs universe: 99.651%
- Latest date: 2026-06-09
- Date count: 104
- Latest date tickers: 857
- Season date count: 104

## Arena Simulation Tables

- Live run: `arena_jp_live_2026`
- Live orders: 880
- Live trades: 423
- Live open positions: 11
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 23 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 16046 | 880 |
| `arena_open_positions` | True | 285 | 11 |
| `arena_trades` | True | 7671 | 423 |
| `arena_equity_curve` | True | 15715 | 728 |
| `arena_yearly_rankings` | True | 161 | 7 |
| `arena_monthly_rankings` | True | 861 | 42 |
| `arena_trade_rankings` | True | 880 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 61
- site/data total MB: 9.241
- prices latest MB: 0.342
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-close_council.json` | 0.578 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.563 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-night_strategy_lab.json` | 0.563 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-close_council.json` | 0.556 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-night_strategy_lab.json` | 0.53 |
| `site/data/japan/ai-arena/war-room/history/2026-06-06-weekly_arena_review.json` | 0.471 |
| `site/data/japan/universe/jp_index_universe.json` | 0.421 |
| `site/data/japan/ai-arena/war-room/history/2026-06-05-close_council.json` | 0.399 |
| `site/data/japan/ai-arena/war-room/history/2026-06-05-night_strategy_lab.json` | 0.378 |
| `site/data/japan/ai-arena/war-room/history/2026-06-04-night_strategy_lab.json` | 0.347 |
| `site/data/prices-jp/latest.json` | 0.342 |
| `site/data/japan/ai-arena/war-room/history/2026-06-04-close_council.json` | 0.318 |
| `site/data/japan/ai-arena/latest.json` | 0.242 |
| `site/data/japan/ai-arena/summary/latest.json` | 0.214 |
