# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-01T04:02:46Z
Run: `arena_jp_rebuild_2026_v016`
Season: 2026-01-01 → 2026-06-01

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 3231 | 1339 | 57 | 49 | 49 | 0 | 49 | 49 | 0 | 3182 | MAX_NEW_ENTRIES_PER_DAY (1359) |
| KAESHI / `reversal_snapback` | 284 | 148 | 64 | 64 | 64 | 0 | 64 | 64 | 0 | 220 | MAX_NEW_ENTRIES_PER_DAY (84) |
| KYOU / `daily_striker` | 1330 | 1056 | 83 | 83 | 79 | 4 | 79 | 79 | 0 | 1251 | ENTRY_RULE_REJECTED (957) |
| MAMORU / `risk_sentinel` | 40093 | 28684 | 119 | 96 | 96 | 0 | 92 | 92 | 4 | 39997 | ENTRY_RULE_REJECTED (27935) |
| MATSU / `contrarian_monk` | 1101 | 557 | 78 | 78 | 78 | 0 | 74 | 74 | 4 | 1023 | ENTRY_RULE_REJECTED (390) |
| NAGARE / `weekly_sage` | 13411 | 5980 | 275 | 58 | 37 | 21 | 33 | 33 | 4 | 13374 | ENTRY_RULE_REJECTED (5435) |
| SAGURI / `discovery_scout` | 613 | 570 | 68 | 67 | 67 | 0 | 67 | 67 | 0 | 546 | ENTRY_RULE_REJECTED (458) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `MAX_NEW_ENTRIES_PER_DAY`: 1359
- `ENTRY_RULE_REJECTED`: 1155
- `MAX_POSITIONS_FULL`: 533
- `ALREADY_OPEN_POSITION`: 127
- `ZERO_SHARES_AFTER_SIZING`: 8
- Entry rule details:
  - rank_below_cutoff: 462
  - year_range_position_too_high: 447
  - blocked_near_year_end: 139
  - pullback_too_deep: 60
  - value_rerating_confirmation_failed: 24
  - medium_return_too_weak: 13
  - quality_guard_below_threshold: 6
  - value_mispricing_below_threshold: 4

### KAESHI / `reversal_snapback`
- `MAX_NEW_ENTRIES_PER_DAY`: 84
- `MAX_POSITIONS_FULL`: 52
- `ENTRY_RULE_REJECTED`: 50
- `ALREADY_OPEN_POSITION`: 34
- Entry rule details:
  - score_below_entry_threshold: 47
  - blocked_near_year_end: 3

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 957
- `MAX_NEW_ENTRIES_PER_DAY`: 205
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 16
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 514
  - rsi_overheated: 144
  - rank_below_cutoff: 140
  - year_range_position_too_low: 44
  - volume_ratio_below_threshold: 33
  - five_day_move_too_extended: 32
  - blocked_near_year_end: 23
  - liquidity_below_threshold: 20
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 27935
- `MAX_NEW_ENTRIES_PER_DAY`: 6850
- `MAX_POSITIONS_FULL`: 4559
- `ALREADY_OPEN_POSITION`: 630
- `ZERO_SHARES_AFTER_SIZING`: 23
- Entry rule details:
  - score_below_entry_threshold: 14001
  - rank_below_cutoff: 12326
  - blocked_near_year_end: 1515
  - price_not_above_ma50: 42
  - weekly_trend_too_weak: 29
  - rsi_overheated: 17
  - price_not_above_ma120: 5

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 390
- `MAX_NEW_ENTRIES_PER_DAY`: 323
- `MAX_POSITIONS_FULL`: 221
- `ALREADY_OPEN_POSITION`: 89
- Entry rule details:
  - score_below_entry_threshold: 264
  - rsi_outside_pullback_band: 41
  - rank_below_cutoff: 29
  - price_vs_ma50_outside_band: 21
  - blocked_near_year_end: 18
  - pullback_too_deep: 8
  - weekly_trend_too_weak: 5
  - volatility_too_high: 4

### NAGARE / `weekly_sage`
- `ENTRY_RULE_REJECTED`: 5435
- `MAX_POSITIONS_FULL`: 5067
- `MAX_NEW_ENTRIES_PER_DAY`: 2364
- `ALREADY_OPEN_POSITION`: 270
- `ZERO_SHARES_AFTER_SIZING`: 217
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 21
- Entry rule details:
  - rank_below_cutoff: 3379
  - score_below_entry_threshold: 1268
  - blocked_near_year_end: 787
  - twenty_day_move_too_extended: 1

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 458
- `ALREADY_OPEN_POSITION`: 44
- `MAX_NEW_ENTRIES_PER_DAY`: 28
- `MAX_POSITIONS_FULL`: 15
- `ZERO_SHARES_AFTER_SIZING`: 1
- Entry rule details:
  - five_day_move_too_extended: 272
  - operating_margin_below_threshold: 53
  - quality_guard_below_threshold: 46
  - blocked_near_year_end: 29
  - roe_below_threshold: 20
  - liquidity_below_threshold: 19
  - market_cap_too_small: 12
  - pbr_too_high: 6
  - rank_below_cutoff: 1
