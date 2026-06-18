# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-18T11:11:19Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-18

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 4134 | 3659 | 7 | 7 | 7 | 0 | 7 | 7 | 0 | 4127 | ENTRY_RULE_REJECTED (3475) |
| KAESHI / `reversal_snapback` | 247 | 224 | 47 | 47 | 47 | 0 | 47 | 47 | 0 | 200 | ENTRY_RULE_REJECTED (152) |
| KYOU / `daily_striker` | 1442 | 1155 | 91 | 91 | 87 | 4 | 87 | 87 | 0 | 1355 | ENTRY_RULE_REJECTED (1046) |
| MAMORU / `risk_sentinel` | 45725 | 33131 | 136 | 111 | 111 | 0 | 104 | 104 | 7 | 45614 | ENTRY_RULE_REJECTED (32258) |
| MATSU / `contrarian_monk` | 1681 | 885 | 94 | 94 | 92 | 2 | 90 | 90 | 2 | 1589 | ENTRY_RULE_REJECTED (688) |
| NAGARE / `weekly_sage` | 17534 | 1869 | 94 | 66 | 48 | 18 | 43 | 43 | 5 | 17486 | MAX_POSITIONS_FULL (11899) |
| SAGURI / `discovery_scout` | 587 | 565 | 41 | 41 | 41 | 0 | 41 | 41 | 0 | 546 | ENTRY_RULE_REJECTED (505) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 3475
- `MAX_NEW_ENTRIES_PER_DAY`: 441
- `MAX_SYMBOL_CLOSED_TRADES`: 128
- `NO_NEXT_TRADING_DATE`: 34
- `COOLDOWN_AFTER_LOSS`: 26
- `ALREADY_OPEN_POSITION`: 23
- Entry rule details:
  - score_below_entry_threshold: 3272
  - blocked_near_year_end: 190
  - year_range_position_too_high: 13

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 152
- `ALREADY_OPEN_POSITION`: 25
- `MAX_NEW_ENTRIES_PER_DAY`: 12
- `MAX_POSITIONS_FULL`: 9
- `NO_NEXT_TRADING_DATE`: 2
- Entry rule details:
  - score_below_entry_threshold: 87
  - year_range_position_extremely_low: 22
  - five_day_falling_knife: 16
  - rsi_extremely_weak: 13
  - rank_below_cutoff: 9
  - blocked_near_year_end: 4
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1046
- `MAX_NEW_ENTRIES_PER_DAY`: 204
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 18
- `NO_NEXT_TRADING_DATE`: 14
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 572
  - rsi_overheated: 158
  - rank_below_cutoff: 146
  - year_range_position_too_low: 52
  - volume_ratio_below_threshold: 40
  - five_day_move_too_extended: 36
  - liquidity_below_threshold: 20
  - blocked_near_year_end: 15
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 32258
- `MAX_NEW_ENTRIES_PER_DAY`: 7631
- `MAX_POSITIONS_FULL`: 4549
- `ALREADY_OPEN_POSITION`: 737
- `NO_NEXT_TRADING_DATE`: 414
- `ZERO_SHARES_AFTER_SIZING`: 25
- Entry rule details:
  - score_below_entry_threshold: 16870
  - rank_below_cutoff: 13690
  - blocked_near_year_end: 1586
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 34
  - rsi_overheated: 22
  - price_not_above_ma120: 9

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 688
- `MAX_POSITIONS_FULL`: 439
- `MAX_NEW_ENTRIES_PER_DAY`: 354
- `ALREADY_OPEN_POSITION`: 103
- `NO_NEXT_TRADING_DATE`: 3
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 2
- Entry rule details:
  - score_below_entry_threshold: 358
  - blocked_near_year_end: 111
  - volatility_too_high: 57
  - rank_below_cutoff: 52
  - price_vs_ma50_outside_band: 48
  - rsi_outside_pullback_band: 40
  - pullback_too_deep: 10
  - liquidity_below_threshold: 6
  - weekly_trend_too_weak: 6

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 11899
- `MAX_NEW_ENTRIES_PER_DAY`: 3618
- `ENTRY_RULE_REJECTED`: 1664
- `NO_NEXT_TRADING_DATE`: 148
- `ALREADY_OPEN_POSITION`: 111
- `ZERO_SHARES_AFTER_SIZING`: 28
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 18
- Entry rule details:
  - blocked_near_year_end: 870
  - rank_below_cutoff: 562
  - score_below_entry_threshold: 230
  - twenty_day_move_too_extended: 2

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 505
- `ALREADY_OPEN_POSITION`: 19
- `MAX_NEW_ENTRIES_PER_DAY`: 19
- `NO_NEXT_TRADING_DATE`: 3
- Entry rule details:
  - five_day_move_too_extended: 166
  - liquidity_below_threshold: 110
  - quality_guard_below_threshold: 72
  - operating_margin_below_threshold: 69
  - rsi_overheated: 26
  - market_cap_too_small: 18
  - roe_below_threshold: 17
  - twenty_day_move_too_extended: 9
  - blocked_near_year_end: 7
  - pbr_too_high: 5
  - rank_below_cutoff: 4
  - five_day_return_too_low: 2
