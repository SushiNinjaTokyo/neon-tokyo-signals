# Neon Tokyo Data Coverage Review

Generated: 2026-06-19T13:49:01+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 2511.012

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-19T13:38:48.080176 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-19T13:38:48.084347 |
| `build_id` | 27828501190-1 | 2026-06-19T13:38:48.068136 |
| `generated_at` | 2026-06-19T13:38:47+00:00 | 2026-06-19T13:38:48.065964 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-19T13:38:48.082087 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-19T13:38:48.061102 |
| `source_ref` | refs/heads/main | 2026-06-19T13:38:48.078345 |
| `source_run_attempt` | 1 | 2026-06-19T13:38:48.074289 |
| `source_run_id` | 27828501190 | 2026-06-19T13:38:48.072387 |
| `source_sha` | 5482dde885426741f0f85c9d9e3c388529019c55 | 2026-06-19T13:38:48.076246 |
| `source_workflow` | AI Arena JP live update | 2026-06-19T13:38:48.070083 |

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
- Rows: 301128
- Unique symbols: 855
- Date range: 2025-01-06 → 2026-06-19
- Insufficient bars symbols: 0
- Stale symbols: 4

## Features

- Table exists: True
- Rows: 301128
- Unique symbols: 855
- Latest date: 2026-06-19
- Latest date symbols: 850

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.716% | 300273 |
| `return_5d_pct` | 98.58% | 296853 |
| `return_20d_pct` | 94.321% | 284028 |
| `return_60d_pct` | 82.964% | 249828 |
| `volume_ratio_20d` | 98.862% | 297701 |
| `avg_traded_value_20d_jpy` | 98.864% | 297708 |
| `rsi_14` | 96.025% | 289158 |
| `range_position_252d_0_1` | 94.605% | 284883 |
| `liquidity_score` | 98.864% | 297708 |

## Agent Scores

- Table exists: True
- Rows: 491806
- Unique agents: 7
- Latest date: 2026-06-19
- Date count: 112
- Trade candidates: 67776
- Season window: 2026-01-01 → 2026-06-19
- Season date count: 112
- Season trade candidates: 67776

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 95487 | 112 | 1684 | 855 | 0.874 | 0.3732 | Ignore:76134, Watch:17669, Trade:1684 |
| KYOU / `daily_striker` | 74317 | 112 | 1442 | 731 | 0.9802 | 0.2891 | Ignore:67871, Watch:5004, Trade:1442 |
| SAGURI / `discovery_scout` | 21078 | 112 | 587 | 254 | 0.9805 | 0.3489 | Ignore:18027, Watch:2464, Trade:587 |
| KAESHI / `reversal_snapback` | 74317 | 112 | 247 | 731 | 0.917 | 0.3189 | Ignore:70312, Watch:3758, Trade:247 |
| MAMORU / `risk_sentinel` | 56803 | 112 | 46132 | 508 | 0.9907 | 0.7803 | Trade:46132, Watch:9174, Ignore:1497 |
| HIZUMI / `value_mispricing` | 74317 | 112 | 0 | 731 | 0.6706 | 0.3674 | Ignore:70156, Watch:4161 |
| NAGARE / `weekly_sage` | 95487 | 112 | 17684 | 855 | 1.0 | 0.3652 | Ignore:67690, Trade:17684, Watch:10113 |

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
- Rows: 96208
- Unique tickers: 859
- Coverage vs universe: 100.0%
- Latest date: 2026-06-19
- Date count: 112
- Latest date tickers: 859
- Season date count: 112

## Arena Simulation Tables

- Live run: `arena_jp_live_2026`
- Live orders: 880
- Live trades: 422
- Live open positions: 12
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 1 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 880 | 880 |
| `arena_open_positions` | True | 12 | 12 |
| `arena_trades` | True | 422 | 422 |
| `arena_equity_curve` | True | 784 | 784 |
| `arena_yearly_rankings` | True | 7 | 7 |
| `arena_monthly_rankings` | True | 42 | 42 |
| `arena_trade_rankings` | True | 40 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 68
- site/data total MB: 12.816
- prices latest MB: 0.34
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/ai-arena/war-room/history/2026-06-17-close_council.json` | 0.6 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-close_council.json` | 0.588 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.587 |
| `site/data/japan/ai-arena/war-room/history/2026-06-19-close_council.json` | 0.587 |
| `site/data/japan/ai-arena/war-room/history/2026-06-10-close_council.json` | 0.576 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-close_council.json` | 0.571 |
| `site/data/japan/ai-arena/war-room/history/2026-06-19-night_strategy_lab.json` | 0.571 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-night_strategy_lab.json` | 0.569 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-night_strategy_lab.json` | 0.563 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-close_council.json` | 0.556 |
| `site/data/japan/ai-arena/war-room/history/2026-06-08-night_strategy_lab.json` | 0.53 |
| `site/data/japan/ai-arena/war-room/history/2026-06-06-weekly_arena_review.json` | 0.471 |
| `site/data/japan/universe/jp_index_universe.json` | 0.421 |
| `site/data/japan/ai-arena/war-room/history/2026-06-05-close_council.json` | 0.399 |
