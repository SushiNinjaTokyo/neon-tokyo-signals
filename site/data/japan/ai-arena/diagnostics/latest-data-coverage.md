# Neon Tokyo Data Coverage Review

Generated: 2026-06-24T12:29:33+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 2364.762

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-24T10:15:44.406832 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-24T10:15:44.410563 |
| `build_id` | 28090714713-1 | 2026-06-24T10:15:44.395522 |
| `generated_at` | 2026-06-24T10:15:44+00:00 | 2026-06-24T10:15:44.393353 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-24T10:15:44.408581 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-24T10:15:44.388751 |
| `source_ref` | refs/heads/main | 2026-06-24T10:15:44.404956 |
| `source_run_attempt` | 1 | 2026-06-24T10:15:44.401221 |
| `source_run_id` | 28090714713 | 2026-06-24T10:15:44.399415 |
| `source_sha` | 3bb0c2d31c9795027eb3beb7efd9aba57a84449a | 2026-06-24T10:15:44.403048 |
| `source_workflow` | AI Arena JP War Room | 2026-06-24T10:15:44.397456 |

## Executive Warnings

| Severity | Code | Message |
|---|---|---|
| warning | `STALE_PRICE_SYMBOLS` | Some symbols are stale versus latest price date. |
| warning | `LOW_FUNDAMENTAL_METRIC_COVERAGE` | dividend_yield_pct coverage is low. |
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
- Rows: 303845
- Unique symbols: 855
- Date range: 2025-01-06 → 2026-06-24
- Insufficient bars symbols: 0
- Stale symbols: 5

## Features

- Table exists: True
- Rows: 303845
- Unique symbols: 855
- Latest date: 2026-06-24
- Latest date symbols: 849

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.719% | 302990 |
| `return_5d_pct` | 98.593% | 299570 |
| `return_20d_pct` | 94.372% | 286745 |
| `return_60d_pct` | 83.116% | 252545 |
| `volume_ratio_20d` | 98.872% | 300418 |
| `avg_traded_value_20d_jpy` | 98.874% | 300425 |
| `rsi_14` | 96.06% | 291875 |
| `range_position_252d_0_1` | 94.654% | 287600 |
| `liquidity_score` | 98.874% | 300425 |

## Agent Scores

- Table exists: True
- Rows: 505289
- Unique agents: 7
- Latest date: 2026-06-24
- Date count: 115
- Trade candidates: 69473
- Season window: 2026-01-01 → 2026-06-24
- Season date count: 115
- Season trade candidates: 69473

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 98204 | 115 | 1710 | 855 | 0.874 | 0.3724 | Ignore:78408, Watch:18086, Trade:1710 |
| KYOU / `daily_striker` | 76305 | 115 | 1462 | 731 | 0.9802 | 0.2885 | Ignore:69745, Watch:5098, Trade:1462 |
| SAGURI / `discovery_scout` | 21630 | 115 | 575 | 254 | 0.99 | 0.3421 | Ignore:18640, Watch:2415, Trade:575 |
| KAESHI / `reversal_snapback` | 76305 | 115 | 251 | 731 | 0.917 | 0.3184 | Ignore:72231, Watch:3823, Trade:251 |
| MAMORU / `risk_sentinel` | 58336 | 115 | 47360 | 508 | 0.9907 | 0.78 | Trade:47360, Watch:9442, Ignore:1534 |
| HIZUMI / `value_mispricing` | 76305 | 115 | 0 | 731 | 0.6705 | 0.2864 | Ignore:73490, Watch:2815 |
| NAGARE / `weekly_sage` | 98204 | 115 | 18115 | 855 | 1.0 | 0.3636 | Ignore:69776, Trade:18115, Watch:10313 |

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
| `market_cap_jpy` | 61.816% | 531 |
| `per` | 58.789% | 505 |
| `pbr` | 61.7% | 530 |
| `psr` | 61.001% | 524 |
| `roe_pct` | 57.392% | 493 |
| `roa_pct` | 57.509% | 494 |
| `operating_margin_pct` | 61.816% | 531 |
| `dividend_yield_pct` | 46.217% | 397 |

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
- Rows: 98785
- Unique tickers: 859
- Coverage vs universe: 100.0%
- Latest date: 2026-06-24
- Date count: 115
- Latest date tickers: 859
- Season date count: 115

## Arena Simulation Tables

- Live run: `arena_jp_live_2026`
- Live orders: 869
- Live trades: 416
- Live open positions: 11
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 1 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 869 | 869 |
| `arena_open_positions` | True | 11 | 11 |
| `arena_trades` | True | 416 | 416 |
| `arena_equity_curve` | True | 805 | 805 |
| `arena_yearly_rankings` | True | 7 | 7 |
| `arena_monthly_rankings` | True | 42 | 42 |
| `arena_trade_rankings` | True | 40 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 73
- site/data total MB: 15.946
- prices latest MB: 0.34
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.136 |
| `site/data/japan/ai-arena/war-room/history/2026-06-20-weekly_arena_review.json` | 0.631 |
| `site/data/japan/ai-arena/war-room/latest.json` | 0.615 |
| `site/data/japan/ai-arena/war-room/history/2026-06-24-close_council.json` | 0.615 |
| `site/data/japan/ai-arena/war-room/history/2026-06-23-close_council.json` | 0.611 |
| `site/data/japan/ai-arena/war-room/history/2026-06-22-close_council.json` | 0.604 |
| `site/data/japan/ai-arena/war-room/history/2026-06-17-close_council.json` | 0.6 |
| `site/data/japan/ai-arena/war-room/history/2026-06-23-night_strategy_lab.json` | 0.588 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-close_council.json` | 0.588 |
| `site/data/japan/ai-arena/war-room/history/2026-06-19-close_council.json` | 0.587 |
| `site/data/japan/ai-arena/war-room/history/2026-06-10-close_council.json` | 0.576 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-close_council.json` | 0.571 |
| `site/data/japan/ai-arena/war-room/history/2026-06-19-night_strategy_lab.json` | 0.571 |
| `site/data/japan/ai-arena/war-room/history/2026-06-18-night_strategy_lab.json` | 0.569 |
| `site/data/japan/ai-arena/war-room/history/2026-06-09-night_strategy_lab.json` | 0.563 |
