# Neon Tokyo Data Coverage Review

Generated: 2026-06-08T14:22:17+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 2133.012

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-07T22:10:46.911126 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-07T22:10:46.915978 |
| `build_id` | 27106202096-1 | 2026-06-07T22:10:46.898214 |
| `generated_at` | 2026-06-07T22:10:46+00:00 | 2026-06-07T22:10:46.895549 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-07T22:10:46.913487 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-07T22:10:46.890186 |
| `source_ref` | refs/heads/main | 2026-06-07T22:10:46.908575 |
| `source_run_attempt` | 1 | 2026-06-07T22:10:46.904444 |
| `source_run_id` | 27106202096 | 2026-06-07T22:10:46.902342 |
| `source_sha` | cbc8227566e25dd290fd0ae13c4f5f2e95b59b42 | 2026-06-07T22:10:46.906553 |
| `source_workflow` | AI Arena JP fundamentals refresh | 2026-06-07T22:10:46.900274 |

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
- Rows: 295564
- Unique symbols: 860
- Date range: 2024-12-27 → 2026-06-05
- Insufficient bars symbols: 0
- Stale symbols: 5

## Features

- Table exists: True
- Rows: 295564
- Unique symbols: 860
- Latest date: 2026-06-05
- Latest date symbols: 851

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.709% | 294704 |
| `return_5d_pct` | 98.545% | 291264 |
| `return_20d_pct` | 94.181% | 278364 |
| `return_60d_pct` | 82.542% | 243964 |
| `volume_ratio_20d` | 98.836% | 292124 |
| `avg_traded_value_20d_jpy` | 98.836% | 292124 |
| `rsi_14` | 95.926% | 283524 |
| `range_position_252d_0_1` | 94.472% | 279224 |
| `liquidity_score` | 98.836% | 292124 |

## Agent Scores

- Table exists: True
- Rows: 396302
- Unique agents: 7
- Latest date: 2026-06-05
- Date count: 102
- Trade candidates: 59377
- Season window: 2026-01-01 → 2026-06-05
- Season date count: 102
- Season trade candidates: 59377

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 60763 | 102 | 1153 | 596 | 0.864 | 0.4224 | Ignore:44957, Watch:14653, Trade:1153 |
| KYOU / `daily_striker` | 68056 | 102 | 1378 | 732 | 0.9802 | 0.2918 | Ignore:61962, Watch:4716, Trade:1378 |
| SAGURI / `discovery_scout` | 19494 | 102 | 580 | 255 | 1.0 | 0.3151 | Ignore:16687, Watch:2227, Trade:580 |
| KAESHI / `reversal_snapback` | 68056 | 102 | 258 | 732 | 0.8939 | 0.2732 | Ignore:65124, Watch:2674, Trade:258 |
| MAMORU / `risk_sentinel` | 51114 | 102 | 42077 | 502 | 0.9907 | 0.7855 | Trade:42077, Watch:8006, Ignore:1031 |
| HIZUMI / `value_mispricing` | 68056 | 102 | 5 | 732 | 0.6901 | 0.3162 | Ignore:62777, Watch:5274, Trade:5 |
| NAGARE / `weekly_sage` | 60763 | 102 | 13926 | 596 | 1.0 | 0.443 | Ignore:38705, Trade:13926, Watch:8132 |

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
- Rows: 87414
- Unique tickers: 857
- Coverage vs universe: 99.651%
- Latest date: 2026-06-05
- Date count: 102
- Latest date tickers: 857
- Season date count: 102

## Arena Simulation Tables

- Live run: `arena_jp_live_2026`
- Live orders: 859
- Live trades: 414
- Live open positions: 10
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 23 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 16025 | 859 |
| `arena_open_positions` | True | 284 | 10 |
| `arena_trades` | True | 7662 | 414 |
| `arena_equity_curve` | True | 15701 | 714 |
| `arena_yearly_rankings` | True | 161 | 7 |
| `arena_monthly_rankings` | True | 861 | 42 |
| `arena_trade_rankings` | True | 880 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 59
- site/data total MB: 10.452
- prices latest MB: 2.764
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/prices-jp/latest.json` | 2.764 |
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.538 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-close_council.json` | 0.538 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-night_strategy_lab.json` | 0.53 |
| `site/data/japan/ai-arena/war-room/history/2026-06-06-weekly_arena_review.json` | 0.471 |
| `site/data/japan/universe/jp_index_universe.json` | 0.421 |
| `site/data/japan/ai-arena/war-room/history/2026-06-05-close_council.json` | 0.399 |
| `site/data/japan/ai-arena/war-room/history/2026-06-05-night_strategy_lab.json` | 0.378 |
| `site/data/japan/ai-arena/war-room/history/2026-06-04-night_strategy_lab.json` | 0.347 |
| `site/data/japan/ai-arena/war-room/history/2026-06-04-close_council.json` | 0.318 |
| `site/data/japan/ai-arena/latest.json` | 0.242 |
| `site/data/japan/ai-arena/summary/latest.json` | 0.211 |
| `site/data/japan/ai-arena/summary/2026/latest.json` | 0.211 |
| `site/data/japan/ai-arena/positions/latest.json` | 0.206 |
