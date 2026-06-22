# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-22T15:24:16Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-19

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 2769 | 2526 | 5 | 5 | 5 | 0 | 5 | 5 | 0 | 2764 | ENTRY_RULE_REJECTED (2391) |
| KAESHI / `reversal_snapback` | 249 | 228 | 47 | 47 | 47 | 0 | 47 | 47 | 0 | 202 | ENTRY_RULE_REJECTED (156) |
| KYOU / `daily_striker` | 1447 | 1167 | 91 | 91 | 87 | 4 | 87 | 87 | 0 | 1360 | ENTRY_RULE_REJECTED (1058) |
| MAMORU / `risk_sentinel` | 46144 | 33555 | 137 | 111 | 111 | 0 | 104 | 104 | 7 | 46033 | ENTRY_RULE_REJECTED (32673) |
| MATSU / `contrarian_monk` | 1680 | 887 | 96 | 94 | 92 | 2 | 91 | 91 | 1 | 1588 | ENTRY_RULE_REJECTED (688) |
| NAGARE / `weekly_sage` | 17697 | 2027 | 94 | 66 | 48 | 18 | 44 | 44 | 4 | 17649 | MAX_POSITIONS_FULL (11899) |
| SAGURI / `discovery_scout` | 574 | 574 | 24 | 24 | 24 | 0 | 24 | 24 | 0 | 550 | ENTRY_RULE_REJECTED (535) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 2391
- `MAX_NEW_ENTRIES_PER_DAY`: 212
- `MAX_SYMBOL_CLOSED_TRADES`: 83
- `NO_NEXT_TRADING_DATE`: 31
- `COOLDOWN_AFTER_LOSS`: 26
- `ALREADY_OPEN_POSITION`: 21
- Entry rule details:
  - score_below_entry_threshold: 2212
  - blocked_near_year_end: 170
  - year_range_position_too_high: 9

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 156
- `ALREADY_OPEN_POSITION`: 25
- `MAX_NEW_ENTRIES_PER_DAY`: 12
- `MAX_POSITIONS_FULL`: 9
- Entry rule details:
  - score_below_entry_threshold: 89
  - year_range_position_extremely_low: 23
  - five_day_falling_knife: 17
  - rsi_extremely_weak: 13
  - rank_below_cutoff: 9
  - blocked_near_year_end: 4
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1058
- `MAX_NEW_ENTRIES_PER_DAY`: 204
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 18
- `NO_NEXT_TRADING_DATE`: 7
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 573
  - rsi_overheated: 159
  - rank_below_cutoff: 146
  - year_range_position_too_low: 53
  - volume_ratio_below_threshold: 40
  - five_day_move_too_extended: 37
  - blocked_near_year_end: 23
  - liquidity_below_threshold: 20
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 32673
- `MAX_NEW_ENTRIES_PER_DAY`: 7631
- `MAX_POSITIONS_FULL`: 4549
- `ALREADY_OPEN_POSITION`: 745
- `NO_NEXT_TRADING_DATE`: 409
- `ZERO_SHARES_AFTER_SIZING`: 26
- Entry rule details:
  - score_below_entry_threshold: 17096
  - rank_below_cutoff: 13841
  - blocked_near_year_end: 1623
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 34
  - rsi_overheated: 23
  - price_not_above_ma120: 9

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 688
- `MAX_POSITIONS_FULL`: 439
- `MAX_NEW_ENTRIES_PER_DAY`: 354
- `ALREADY_OPEN_POSITION`: 103
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 2
- `ZERO_SHARES_AFTER_SIZING`: 2
- Entry rule details:
  - score_below_entry_threshold: 383
  - blocked_near_year_end: 71
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
- `ENTRY_RULE_REJECTED`: 1816
- `NO_NEXT_TRADING_DATE`: 153
- `ALREADY_OPEN_POSITION`: 117
- `ZERO_SHARES_AFTER_SIZING`: 28
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 18
- Entry rule details:
  - blocked_near_year_end: 1022
  - rank_below_cutoff: 562
  - score_below_entry_threshold: 230
  - twenty_day_move_too_extended: 2

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 535
- `ALREADY_OPEN_POSITION`: 15
- Entry rule details:
  - five_day_move_too_extended: 170
  - quality_guard_below_threshold: 149
  - liquidity_below_threshold: 84
  - operating_margin_below_threshold: 51
  - rsi_overheated: 28
  - rank_below_cutoff: 12
  - roe_below_threshold: 11
  - twenty_day_move_too_extended: 9
  - blocked_near_year_end: 7
  - market_cap_too_small: 7
  - pbr_too_high: 5
  - five_day_return_too_low: 2
