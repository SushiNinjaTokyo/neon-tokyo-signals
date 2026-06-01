# Neon Tokyo Data Coverage Review

Generated: 2026-06-01T16:18:45+00:00
DuckDB: `data/cache/neon_tokyo_jp.duckdb`
DuckDB exists: **True**

## Canonical DuckDB Metadata

- Metadata table exists: True
- DB size MB: 1026.512

| Key | Value | Updated At |
|---|---|---|
| `artifact_kind` | github-release-asset | 2026-06-01T05:27:26.868834 |
| `asset_name` | neon_tokyo_jp_latest.duckdb.zst | 2026-06-01T05:27:26.872840 |
| `build_id` | 26736770839-1 | 2026-06-01T05:27:26.854783 |
| `generated_at` | 2026-06-01T05:27:26+00:00 | 2026-06-01T05:27:26.852542 |
| `release_tag` | ai-arena-duckdb-latest | 2026-06-01T05:27:26.870870 |
| `schema_version` | neon_tokyo_duckdb_state_v1 | 2026-06-01T05:27:26.847878 |
| `source_ref` | refs/heads/main | 2026-06-01T05:27:26.866850 |
| `source_run_attempt` | 1 | 2026-06-01T05:27:26.862636 |
| `source_run_id` | 26736770839 | 2026-06-01T05:27:26.858665 |
| `source_sha` | b7c439392bca6781de1c1e4edb4d4ffc0a1e58b3 | 2026-06-01T05:27:26.864894 |
| `source_workflow` | AI Arena JP season rebuild | 2026-06-01T05:27:26.856772 |

## Executive Warnings

| Severity | Code | Message |
|---|---|---|
| warning | `STALE_PRICE_SYMBOLS` | Some symbols are stale versus latest price date. |
| warning | `DATED_PRICE_JSON_REMAINING` | Dated prices JSON files remain under site/data/prices-jp. |

## Universe

- DuckDB rows: 860
- DuckDB unique tickers: 860
- Suspicious tickers: 0
- CSV `jp_duckdb_trial_300`: exists=True rows=860 suspicious=0
- CSV `jp_index_universe`: exists=True rows=852 suspicious=0
- CSV `legacy_universe_jp`: exists=True rows=36 suspicious=0

## Prices

- Table exists: True
- Rows: 291853
- Unique symbols: 860
- Date range: 2024-12-27 → 2026-06-01
- Insufficient bars symbols: 0
- Stale symbols: 4

## Features

- Table exists: True
- Rows: 291853
- Unique symbols: 860
- Latest date: 2026-06-01
- Latest date symbols: 554

| Feature | Coverage | Count |
|---|---:|---:|
| `return_1d_pct` | 99.705% | 290993 |
| `return_5d_pct` | 98.527% | 287553 |
| `return_20d_pct` | 94.107% | 274653 |
| `return_60d_pct` | 82.32% | 240253 |
| `volume_ratio_20d` | 98.821% | 288413 |
| `avg_traded_value_20d_jpy` | 98.821% | 288413 |
| `rsi_14` | 95.875% | 279813 |
| `range_position_252d_0_1` | 94.401% | 275513 |
| `liquidity_score` | 98.821% | 288413 |

## Agent Scores

- Table exists: True
- Rows: 377118
- Unique agents: 7
- Latest date: 2026-05-29
- Date count: 97
- Trade candidates: 64489
- Season window: 2026-01-01 → 2026-06-01
- Season date count: 97
- Season trade candidates: 64489

| Agent | Rows | Dates | Trade candidates | Tickers | Max Score | Avg Score | Actions |
|---|---:|---:|---:|---:|---:|---:|---|
| MATSU / `contrarian_monk` | 57797 | 97 | 1101 | 596 | 0.864 | 0.424 | Ignore:42601, Watch:14095, Trade:1101 |
| KYOU / `daily_striker` | 64771 | 97 | 1330 | 730 | 0.9802 | 0.2931 | Ignore:58869, Watch:4572, Trade:1330 |
| SAGURI / `discovery_scout` | 18598 | 97 | 575 | 254 | 1.0 | 0.3219 | Ignore:15831, Watch:2192, Trade:575 |
| KAESHI / `reversal_snapback` | 64771 | 97 | 257 | 730 | 0.8939 | 0.279 | Ignore:61918, Watch:2596, Trade:257 |
| MAMORU / `risk_sentinel` | 48613 | 97 | 40093 | 502 | 0.9907 | 0.787 | Trade:40093, Watch:7573, Ignore:947 |
| HIZUMI / `value_mispricing` | 64771 | 97 | 7722 | 730 | 0.945 | 0.4663 | Ignore:33963, Watch:23086, Trade:7722 |
| NAGARE / `weekly_sage` | 57797 | 97 | 13411 | 596 | 1.0 | 0.4462 | Ignore:36557, Trade:13411, Watch:7829 |

## Company / Fundamentals

### `company_master_jp`

- Exists: True
- Rows: 0
- Unique tickers: 0
- Coverage vs universe: 0.0%

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

- Live run: `arena_jp_rebuild_2026_v017`
- Live orders: 795
- Live trades: 379
- Live open positions: 16
- Live yearly ranking rows: 7

| Table | Exists | Rows | Rows for live run |
|---|---:|---:|---:|
| `arena_simulation_runs` | True | 18 | N/A |
| `arena_display_runs` | True | 1 | N/A |
| `arena_orders` | True | 11656 | 795 |
| `arena_open_positions` | True | 205 | 16 |
| `arena_trades` | True | 5570 | 379 |
| `arena_equity_curve` | True | 12236 | 686 |
| `arena_yearly_rankings` | True | 126 | 7 |
| `arena_monthly_rankings` | True | 644 | 42 |
| `arena_trade_rankings` | True | 680 | 40 |
| `agent_pick_notes_daily` | True | 0 | N/A |

## Site Outputs

- Missing outputs: 0

## Repo Artifact Size

- site/data files: 45
- site/data total MB: 7.098
- prices latest MB: 2.764
- dated prices JSON count: 1

| Largest file | MB |
|---|---:|
| `site/data/prices-jp/latest.json` | 2.764 |
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.json` | 1.55 |
| `site/data/japan/universe/jp_index_universe.json` | 0.422 |
| `site/data/japan/ai-arena/latest.json` | 0.242 |
| `site/data/japan/ai-arena/positions/latest.json` | 0.216 |
| `site/data/japan/ai-arena/summary/latest.json` | 0.214 |
| `site/data/japan/ai-arena/summary/2026/latest.json` | 0.214 |
| `site/data/japan/ai-arena/live/latest.json` | 0.203 |
| `site/data/japan/ai-arena/simulation/latest.json` | 0.203 |
| `site/data/japan/ai-arena/ranking/latest.json` | 0.196 |
| `site/data/japan/universe/jp_index_universe.csv` | 0.174 |
| `site/data/japan/ai-arena/discussion/latest.json` | 0.127 |
| `site/data/japan/agent-scores/latest.json` | 0.104 |
| `site/data/japan/ai-arena/hero/latest.json` | 0.092 |
| `site/data/japan/ai-arena/diagnostics/trade-diagnostics/latest.md` | 0.075 |
