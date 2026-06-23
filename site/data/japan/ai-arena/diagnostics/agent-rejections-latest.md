# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-23T10:29:49Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-23

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 2804 | 2577 | 5 | 5 | 5 | 0 | 5 | 5 | 0 | 2799 | ENTRY_RULE_REJECTED (2440) |
| KAESHI / `reversal_snapback` | 251 | 230 | 48 | 48 | 48 | 0 | 48 | 48 | 0 | 203 | ENTRY_RULE_REJECTED (157) |
| KYOU / `daily_striker` | 1462 | 1189 | 94 | 94 | 90 | 4 | 89 | 89 | 1 | 1372 | ENTRY_RULE_REJECTED (1076) |
| MAMORU / `risk_sentinel` | 46963 | 34376 | 138 | 112 | 112 | 0 | 107 | 107 | 5 | 46851 | ENTRY_RULE_REJECTED (33475) |
| MATSU / `contrarian_monk` | 1686 | 866 | 101 | 99 | 96 | 3 | 95 | 95 | 1 | 1590 | ENTRY_RULE_REJECTED (660) |
| NAGARE / `weekly_sage` | 17996 | 1680 | 97 | 69 | 50 | 19 | 44 | 44 | 6 | 17946 | MAX_POSITIONS_FULL (12454) |
| SAGURI / `discovery_scout` | 575 | 574 | 25 | 25 | 25 | 0 | 25 | 25 | 0 | 550 | ENTRY_RULE_REJECTED (534) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 2440
- `MAX_NEW_ENTRIES_PER_DAY`: 212
- `MAX_SYMBOL_CLOSED_TRADES`: 85
- `COOLDOWN_AFTER_LOSS`: 26
- `ALREADY_OPEN_POSITION`: 21
- `NO_NEXT_TRADING_DATE`: 15
- Entry rule details:
  - score_below_entry_threshold: 2245
  - blocked_near_year_end: 186
  - year_range_position_too_high: 9

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 157
- `ALREADY_OPEN_POSITION`: 25
- `MAX_NEW_ENTRIES_PER_DAY`: 12
- `MAX_POSITIONS_FULL`: 9
- Entry rule details:
  - score_below_entry_threshold: 91
  - year_range_position_extremely_low: 24
  - five_day_falling_knife: 17
  - rsi_extremely_weak: 13
  - rank_below_cutoff: 9
  - blocked_near_year_end: 2
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1076
- `MAX_NEW_ENTRIES_PER_DAY`: 204
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 19
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 591
  - rsi_overheated: 159
  - rank_below_cutoff: 146
  - year_range_position_too_low: 53
  - volume_ratio_below_threshold: 40
  - five_day_move_too_extended: 39
  - blocked_near_year_end: 21
  - liquidity_below_threshold: 20
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 33475
- `MAX_NEW_ENTRIES_PER_DAY`: 7631
- `MAX_POSITIONS_FULL`: 4549
- `ALREADY_OPEN_POSITION`: 763
- `NO_NEXT_TRADING_DATE`: 407
- `ZERO_SHARES_AFTER_SIZING`: 26
- Entry rule details:
  - score_below_entry_threshold: 17584
  - rank_below_cutoff: 14151
  - blocked_near_year_end: 1625
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 36
  - rsi_overheated: 23
  - price_not_above_ma120: 9

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 660
- `MAX_POSITIONS_FULL`: 442
- `MAX_NEW_ENTRIES_PER_DAY`: 375
- `ALREADY_OPEN_POSITION`: 105
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 3
- `NO_NEXT_TRADING_DATE`: 3
- `ZERO_SHARES_AFTER_SIZING`: 2
- Entry rule details:
  - score_below_entry_threshold: 399
  - rank_below_cutoff: 72
  - volatility_too_high: 61
  - price_vs_ma50_outside_band: 54
  - rsi_outside_pullback_band: 43
  - pullback_too_deep: 10
  - blocked_near_year_end: 9
  - liquidity_below_threshold: 6
  - weekly_trend_too_weak: 6

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 12454
- `MAX_NEW_ENTRIES_PER_DAY`: 3721
- `ENTRY_RULE_REJECTED`: 1480
- `NO_NEXT_TRADING_DATE`: 141
- `ALREADY_OPEN_POSITION`: 103
- `ZERO_SHARES_AFTER_SIZING`: 28
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 19
- Entry rule details:
  - blocked_near_year_end: 686
  - rank_below_cutoff: 562
  - score_below_entry_threshold: 230
  - twenty_day_move_too_extended: 2

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 534
- `ALREADY_OPEN_POSITION`: 15
- `NO_NEXT_TRADING_DATE`: 1
- Entry rule details:
  - five_day_move_too_extended: 171
  - quality_guard_below_threshold: 150
  - liquidity_below_threshold: 85
  - operating_margin_below_threshold: 51
  - rsi_overheated: 28
  - rank_below_cutoff: 12
  - roe_below_threshold: 11
  - twenty_day_move_too_extended: 9
  - market_cap_too_small: 7
  - pbr_too_high: 5
  - blocked_near_year_end: 3
  - five_day_return_too_low: 2
