# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-22T05:44:50Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-22

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 4355 | 3870 | 7 | 7 | 7 | 0 | 7 | 7 | 0 | 4348 | ENTRY_RULE_REJECTED (3684) |
| KAESHI / `reversal_snapback` | 249 | 226 | 47 | 47 | 47 | 0 | 47 | 47 | 0 | 202 | ENTRY_RULE_REJECTED (154) |
| KYOU / `daily_striker` | 1451 | 1169 | 92 | 92 | 88 | 4 | 88 | 88 | 0 | 1363 | ENTRY_RULE_REJECTED (1059) |
| MAMORU / `risk_sentinel` | 46540 | 33952 | 138 | 112 | 112 | 0 | 105 | 105 | 7 | 46428 | ENTRY_RULE_REJECTED (33059) |
| MATSU / `contrarian_monk` | 1688 | 891 | 98 | 96 | 94 | 2 | 92 | 92 | 2 | 1594 | ENTRY_RULE_REJECTED (685) |
| NAGARE / `weekly_sage` | 17842 | 1509 | 97 | 69 | 50 | 19 | 44 | 44 | 6 | 17792 | MAX_POSITIONS_FULL (12454) |
| SAGURI / `discovery_scout` | 587 | 568 | 43 | 42 | 42 | 0 | 42 | 42 | 0 | 545 | ENTRY_RULE_REJECTED (503) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 3684
- `MAX_NEW_ENTRIES_PER_DAY`: 460
- `MAX_SYMBOL_CLOSED_TRADES`: 130
- `COOLDOWN_AFTER_LOSS`: 26
- `NO_NEXT_TRADING_DATE`: 25
- `ALREADY_OPEN_POSITION`: 23
- Entry rule details:
  - score_below_entry_threshold: 3437
  - blocked_near_year_end: 233
  - year_range_position_too_high: 14

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 154
- `ALREADY_OPEN_POSITION`: 25
- `MAX_NEW_ENTRIES_PER_DAY`: 12
- `MAX_POSITIONS_FULL`: 9
- `NO_NEXT_TRADING_DATE`: 2
- Entry rule details:
  - score_below_entry_threshold: 88
  - year_range_position_extremely_low: 24
  - five_day_falling_knife: 16
  - rsi_extremely_weak: 13
  - rank_below_cutoff: 9
  - blocked_near_year_end: 2
  - pullback_too_deep: 1
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1059
- `MAX_NEW_ENTRIES_PER_DAY`: 204
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 18
- `NO_NEXT_TRADING_DATE`: 9
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 584
  - rsi_overheated: 159
  - rank_below_cutoff: 146
  - year_range_position_too_low: 52
  - volume_ratio_below_threshold: 40
  - five_day_move_too_extended: 37
  - liquidity_below_threshold: 20
  - blocked_near_year_end: 14
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 33059
- `MAX_NEW_ENTRIES_PER_DAY`: 7631
- `MAX_POSITIONS_FULL`: 4549
- `ALREADY_OPEN_POSITION`: 755
- `NO_NEXT_TRADING_DATE`: 408
- `ZERO_SHARES_AFTER_SIZING`: 26
- Entry rule details:
  - score_below_entry_threshold: 17340
  - rank_below_cutoff: 13999
  - blocked_near_year_end: 1606
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 35
  - rsi_overheated: 23
  - price_not_above_ma120: 9

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 685
- `MAX_POSITIONS_FULL`: 439
- `MAX_NEW_ENTRIES_PER_DAY`: 354
- `ALREADY_OPEN_POSITION`: 108
- `NO_NEXT_TRADING_DATE`: 4
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 2
- `ZERO_SHARES_AFTER_SIZING`: 2
- Entry rule details:
  - score_below_entry_threshold: 399
  - rank_below_cutoff: 72
  - volatility_too_high: 60
  - price_vs_ma50_outside_band: 53
  - rsi_outside_pullback_band: 42
  - blocked_near_year_end: 37
  - pullback_too_deep: 10
  - liquidity_below_threshold: 6
  - weekly_trend_too_weak: 6

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 12454
- `MAX_NEW_ENTRIES_PER_DAY`: 3721
- `ENTRY_RULE_REJECTED`: 1316
- `NO_NEXT_TRADING_DATE`: 158
- `ALREADY_OPEN_POSITION`: 96
- `ZERO_SHARES_AFTER_SIZING`: 28
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 19
- Entry rule details:
  - rank_below_cutoff: 562
  - blocked_near_year_end: 522
  - score_below_entry_threshold: 230
  - twenty_day_move_too_extended: 2

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 503
- `ALREADY_OPEN_POSITION`: 22
- `MAX_NEW_ENTRIES_PER_DAY`: 19
- `NO_NEXT_OPEN_PRICE`: 1
- Entry rule details:
  - five_day_move_too_extended: 166
  - liquidity_below_threshold: 111
  - quality_guard_below_threshold: 73
  - operating_margin_below_threshold: 69
  - rsi_overheated: 26
  - market_cap_too_small: 19
  - roe_below_threshold: 17
  - twenty_day_move_too_extended: 9
  - pbr_too_high: 5
  - rank_below_cutoff: 4
  - blocked_near_year_end: 2
  - five_day_return_too_low: 2
