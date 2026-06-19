# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-19T08:48:18Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-19

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 4161 | 3693 | 7 | 7 | 7 | 0 | 7 | 7 | 0 | 4154 | ENTRY_RULE_REJECTED (3508) |
| KAESHI / `reversal_snapback` | 247 | 226 | 47 | 47 | 47 | 0 | 47 | 47 | 0 | 200 | ENTRY_RULE_REJECTED (154) |
| KYOU / `daily_striker` | 1442 | 1169 | 91 | 91 | 87 | 4 | 87 | 87 | 0 | 1355 | ENTRY_RULE_REJECTED (1060) |
| MAMORU / `risk_sentinel` | 46132 | 33545 | 137 | 111 | 111 | 0 | 104 | 104 | 7 | 46021 | ENTRY_RULE_REJECTED (32664) |
| MATSU / `contrarian_monk` | 1684 | 888 | 96 | 94 | 92 | 2 | 91 | 91 | 1 | 1592 | ENTRY_RULE_REJECTED (689) |
| NAGARE / `weekly_sage` | 17684 | 2017 | 94 | 66 | 48 | 18 | 44 | 44 | 4 | 17636 | MAX_POSITIONS_FULL (11899) |
| SAGURI / `discovery_scout` | 587 | 568 | 42 | 42 | 42 | 0 | 42 | 42 | 0 | 545 | ENTRY_RULE_REJECTED (504) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 3508
- `MAX_NEW_ENTRIES_PER_DAY`: 441
- `MAX_SYMBOL_CLOSED_TRADES`: 129
- `NO_NEXT_TRADING_DATE`: 27
- `COOLDOWN_AFTER_LOSS`: 26
- `ALREADY_OPEN_POSITION`: 23
- Entry rule details:
  - score_below_entry_threshold: 3293
  - blocked_near_year_end: 202
  - year_range_position_too_high: 13

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 154
- `ALREADY_OPEN_POSITION`: 25
- `MAX_NEW_ENTRIES_PER_DAY`: 12
- `MAX_POSITIONS_FULL`: 9
- Entry rule details:
  - score_below_entry_threshold: 88
  - year_range_position_extremely_low: 22
  - five_day_falling_knife: 16
  - rsi_extremely_weak: 13
  - rank_below_cutoff: 9
  - blocked_near_year_end: 5
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1060
- `MAX_NEW_ENTRIES_PER_DAY`: 204
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 18
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 573
  - rsi_overheated: 159
  - rank_below_cutoff: 146
  - year_range_position_too_low: 52
  - volume_ratio_below_threshold: 40
  - five_day_move_too_extended: 36
  - blocked_near_year_end: 27
  - liquidity_below_threshold: 20
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 32664
- `MAX_NEW_ENTRIES_PER_DAY`: 7631
- `MAX_POSITIONS_FULL`: 4549
- `ALREADY_OPEN_POSITION`: 744
- `NO_NEXT_TRADING_DATE`: 407
- `ZERO_SHARES_AFTER_SIZING`: 26
- Entry rule details:
  - score_below_entry_threshold: 17096
  - rank_below_cutoff: 13841
  - blocked_near_year_end: 1614
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 34
  - rsi_overheated: 23
  - price_not_above_ma120: 9

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 689
- `MAX_POSITIONS_FULL`: 439
- `MAX_NEW_ENTRIES_PER_DAY`: 354
- `ALREADY_OPEN_POSITION`: 103
- `NO_NEXT_TRADING_DATE`: 3
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 2
- `ZERO_SHARES_AFTER_SIZING`: 2
- Entry rule details:
  - score_below_entry_threshold: 383
  - blocked_near_year_end: 72
  - rank_below_cutoff: 62
  - volatility_too_high: 59
  - price_vs_ma50_outside_band: 50
  - rsi_outside_pullback_band: 41
  - pullback_too_deep: 10
  - liquidity_below_threshold: 6
  - weekly_trend_too_weak: 6

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 11899
- `MAX_NEW_ENTRIES_PER_DAY`: 3618
- `ENTRY_RULE_REJECTED`: 1807
- `NO_NEXT_TRADING_DATE`: 150
- `ALREADY_OPEN_POSITION`: 116
- `ZERO_SHARES_AFTER_SIZING`: 28
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 18
- Entry rule details:
  - blocked_near_year_end: 1013
  - rank_below_cutoff: 562
  - score_below_entry_threshold: 230
  - twenty_day_move_too_extended: 2

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 504
- `ALREADY_OPEN_POSITION`: 22
- `MAX_NEW_ENTRIES_PER_DAY`: 19
- Entry rule details:
  - five_day_move_too_extended: 166
  - liquidity_below_threshold: 110
  - quality_guard_below_threshold: 73
  - operating_margin_below_threshold: 69
  - rsi_overheated: 26
  - market_cap_too_small: 18
  - roe_below_threshold: 17
  - twenty_day_move_too_extended: 9
  - blocked_near_year_end: 5
  - pbr_too_high: 5
  - rank_below_cutoff: 4
  - five_day_return_too_low: 2
