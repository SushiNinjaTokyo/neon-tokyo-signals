# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-25T07:03:57Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-25

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 2826 | 2603 | 5 | 5 | 5 | 0 | 5 | 5 | 0 | 2821 | ENTRY_RULE_REJECTED (2464) |
| KAESHI / `reversal_snapback` | 251 | 230 | 48 | 48 | 48 | 0 | 48 | 48 | 0 | 203 | ENTRY_RULE_REJECTED (157) |
| KYOU / `daily_striker` | 1469 | 1189 | 96 | 96 | 92 | 4 | 92 | 92 | 0 | 1377 | ENTRY_RULE_REJECTED (1073) |
| MAMORU / `risk_sentinel` | 47763 | 35180 | 139 | 113 | 113 | 0 | 108 | 108 | 5 | 47650 | ENTRY_RULE_REJECTED (34265) |
| MATSU / `contrarian_monk` | 1745 | 893 | 102 | 100 | 97 | 3 | 96 | 96 | 1 | 1648 | ENTRY_RULE_REJECTED (686) |
| NAGARE / `weekly_sage` | 18253 | 1940 | 97 | 69 | 50 | 19 | 45 | 45 | 5 | 18203 | MAX_POSITIONS_FULL (12454) |
| SAGURI / `discovery_scout` | 575 | 575 | 26 | 26 | 26 | 0 | 26 | 26 | 0 | 549 | ENTRY_RULE_REJECTED (534) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 2464
- `MAX_NEW_ENTRIES_PER_DAY`: 212
- `MAX_SYMBOL_CLOSED_TRADES`: 87
- `COOLDOWN_AFTER_LOSS`: 26
- `ALREADY_OPEN_POSITION`: 21
- `NO_NEXT_TRADING_DATE`: 11
- Entry rule details:
  - score_below_entry_threshold: 2270
  - blocked_near_year_end: 185
  - year_range_position_too_high: 9

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 157
- `ALREADY_OPEN_POSITION`: 25
- `MAX_NEW_ENTRIES_PER_DAY`: 12
- `MAX_POSITIONS_FULL`: 9
- Entry rule details:
  - score_below_entry_threshold: 92
  - year_range_position_extremely_low: 24
  - five_day_falling_knife: 17
  - rsi_extremely_weak: 13
  - rank_below_cutoff: 9
  - pullback_too_deep: 1
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1073
- `MAX_NEW_ENTRIES_PER_DAY`: 204
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 20
- `NO_NEXT_TRADING_DATE`: 7
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 604
  - rsi_overheated: 161
  - rank_below_cutoff: 147
  - year_range_position_too_low: 53
  - five_day_move_too_extended: 41
  - volume_ratio_below_threshold: 40
  - liquidity_below_threshold: 20
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 34265
- `MAX_NEW_ENTRIES_PER_DAY`: 7631
- `MAX_POSITIONS_FULL`: 4549
- `ALREADY_OPEN_POSITION`: 776
- `NO_NEXT_TRADING_DATE`: 403
- `ZERO_SHARES_AFTER_SIZING`: 26
- Entry rule details:
  - score_below_entry_threshold: 18076
  - rank_below_cutoff: 14473
  - blocked_near_year_end: 1597
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 40
  - rsi_overheated: 23
  - price_not_above_ma120: 9

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 686
- `MAX_POSITIONS_FULL`: 442
- `MAX_NEW_ENTRIES_PER_DAY`: 375
- `ALREADY_OPEN_POSITION`: 105
- `NO_NEXT_TRADING_DATE`: 35
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 3
- `ZERO_SHARES_AFTER_SIZING`: 2
- Entry rule details:
  - score_below_entry_threshold: 400
  - rank_below_cutoff: 72
  - volatility_too_high: 61
  - price_vs_ma50_outside_band: 54
  - rsi_outside_pullback_band: 44
  - blocked_near_year_end: 33
  - pullback_too_deep: 10
  - liquidity_below_threshold: 6
  - weekly_trend_too_weak: 6

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 12454
- `MAX_NEW_ENTRIES_PER_DAY`: 3721
- `ENTRY_RULE_REJECTED`: 1728
- `NO_NEXT_TRADING_DATE`: 138
- `ALREADY_OPEN_POSITION`: 115
- `ZERO_SHARES_AFTER_SIZING`: 28
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 19
- Entry rule details:
  - blocked_near_year_end: 934
  - rank_below_cutoff: 562
  - score_below_entry_threshold: 230
  - twenty_day_move_too_extended: 2

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 534
- `ALREADY_OPEN_POSITION`: 15
- Entry rule details:
  - five_day_move_too_extended: 172
  - quality_guard_below_threshold: 151
  - liquidity_below_threshold: 85
  - operating_margin_below_threshold: 51
  - rsi_overheated: 28
  - rank_below_cutoff: 12
  - roe_below_threshold: 11
  - twenty_day_move_too_extended: 9
  - market_cap_too_small: 7
  - pbr_too_high: 5
  - five_day_return_too_low: 2
  - blocked_near_year_end: 1
