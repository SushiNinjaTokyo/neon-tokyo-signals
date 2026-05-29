# AI Arena Agent Rejection Diagnostics

Generated: 2026-05-29T08:21:00Z
Run: `arena_jp_rebuild_2026_v012`
Season: 2026-01-01 → 2026-05-29

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 2090 | 494 | 70 | 55 | 55 | 0 | 52 | 52 | 3 | 2035 | MAX_NEW_ENTRIES_PER_DAY (1075) |
| KAESHI / `reversal_snapback` | 103 | 92 | 34 | 34 | 34 | 0 | 34 | 34 | 0 | 69 | ENTRY_RULE_REJECTED (30) |
| KYOU / `daily_striker` | 466 | 410 | 49 | 49 | 49 | 0 | 49 | 49 | 0 | 417 | ENTRY_RULE_REJECTED (348) |
| MAMORU / `risk_sentinel` | 17180 | 14020 | 108 | 96 | 96 | 0 | 90 | 90 | 6 | 17084 | ENTRY_RULE_REJECTED (13237) |
| MATSU / `contrarian_monk` | 512 | 332 | 57 | 57 | 57 | 0 | 54 | 54 | 3 | 455 | ENTRY_RULE_REJECTED (209) |
| NAGARE / `weekly_sage` | 5704 | 1851 | 165 | 62 | 42 | 20 | 36 | 36 | 6 | 5662 | MAX_POSITIONS_FULL (2798) |
| SAGURI / `discovery_scout` | 139 | 138 | 26 | 26 | 26 | 0 | 25 | 25 | 1 | 113 | ENTRY_RULE_REJECTED (94) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `MAX_NEW_ENTRIES_PER_DAY`: 1075
- `MAX_POSITIONS_FULL`: 509
- `ENTRY_RULE_REJECTED`: 336
- `ALREADY_OPEN_POSITION`: 88
- `ZERO_SHARES_AFTER_SIZING`: 15
- `NO_NEXT_TRADING_DATE`: 12
- Entry rule details:
  - year_range_position_too_high: 286
  - blocked_near_year_end: 32
  - rank_below_cutoff: 16
  - quality_guard_below_threshold: 1
  - valuation_discount_below_threshold: 1

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 30
- `ALREADY_OPEN_POSITION`: 28
- `MAX_NEW_ENTRIES_PER_DAY`: 11
- Entry rule details:
  - score_below_entry_threshold: 30

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 348
- `MAX_NEW_ENTRIES_PER_DAY`: 50
- `ALREADY_OPEN_POSITION`: 13
- `NO_NEXT_TRADING_DATE`: 6
- Entry rule details:
  - score_below_entry_threshold: 188
  - rsi_overheated: 77
  - volume_ratio_below_threshold: 31
  - rank_below_cutoff: 18
  - year_range_position_too_low: 14
  - five_day_move_too_extended: 11
  - liquidity_below_threshold: 6
  - blocked_near_year_end: 2
  - range_position_20d_too_low: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 13237
- `MAX_NEW_ENTRIES_PER_DAY`: 2394
- `ALREADY_OPEN_POSITION`: 675
- `MAX_POSITIONS_FULL`: 595
- `NO_NEXT_TRADING_DATE`: 171
- `ZERO_SHARES_AFTER_SIZING`: 12
- Entry rule details:
  - rank_below_cutoff: 6341
  - score_below_entry_threshold: 6155
  - blocked_near_year_end: 620
  - price_not_above_ma50: 73
  - weekly_trend_too_weak: 21
  - rsi_overheated: 17
  - price_not_above_ma120: 10

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 209
- `MAX_POSITIONS_FULL`: 102
- `MAX_NEW_ENTRIES_PER_DAY`: 78
- `ALREADY_OPEN_POSITION`: 66
- Entry rule details:
  - score_below_entry_threshold: 138
  - rank_below_cutoff: 20
  - rsi_outside_pullback_band: 20
  - price_vs_ma50_outside_band: 12
  - blocked_near_year_end: 10
  - pullback_too_deep: 4
  - volatility_too_high: 3
  - weekly_trend_too_weak: 2

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 2798
- `ENTRY_RULE_REJECTED`: 1469
- `MAX_NEW_ENTRIES_PER_DAY`: 1024
- `ALREADY_OPEN_POSITION`: 217
- `ZERO_SHARES_AFTER_SIZING`: 103
- `NO_NEXT_TRADING_DATE`: 31
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 20
- Entry rule details:
  - rank_below_cutoff: 875
  - score_below_entry_threshold: 340
  - blocked_near_year_end: 246
  - twenty_day_move_too_extended: 4
  - volatility_too_high: 4

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 94
- `ALREADY_OPEN_POSITION`: 18
- `MAX_NEW_ENTRIES_PER_DAY`: 1
- Entry rule details:
  - five_day_move_too_extended: 27
  - operating_margin_below_threshold: 24
  - blocked_near_year_end: 9
  - market_cap_too_small: 9
  - roe_below_threshold: 9
  - liquidity_below_threshold: 8
  - quality_guard_below_threshold: 8
