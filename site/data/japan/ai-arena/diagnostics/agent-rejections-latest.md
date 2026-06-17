# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-17T15:08:56Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-17

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 4100 | 3630 | 7 | 7 | 7 | 0 | 7 | 7 | 0 | 4093 | ENTRY_RULE_REJECTED (3447) |
| KAESHI / `reversal_snapback` | 245 | 221 | 47 | 47 | 47 | 0 | 46 | 46 | 1 | 198 | ENTRY_RULE_REJECTED (149) |
| KYOU / `daily_striker` | 1428 | 1142 | 90 | 90 | 86 | 4 | 86 | 86 | 0 | 1342 | ENTRY_RULE_REJECTED (1034) |
| MAMORU / `risk_sentinel` | 45309 | 32711 | 135 | 111 | 111 | 0 | 102 | 102 | 9 | 45198 | ENTRY_RULE_REJECTED (31848) |
| MATSU / `contrarian_monk` | 1678 | 883 | 94 | 94 | 92 | 2 | 90 | 90 | 2 | 1586 | ENTRY_RULE_REJECTED (686) |
| NAGARE / `weekly_sage` | 17385 | 1741 | 94 | 66 | 48 | 18 | 43 | 43 | 5 | 17337 | MAX_POSITIONS_FULL (11899) |
| SAGURI / `discovery_scout` | 584 | 564 | 41 | 41 | 41 | 0 | 41 | 41 | 0 | 543 | ENTRY_RULE_REJECTED (504) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 3447
- `MAX_NEW_ENTRIES_PER_DAY`: 441
- `MAX_SYMBOL_CLOSED_TRADES`: 127
- `NO_NEXT_TRADING_DATE`: 29
- `COOLDOWN_AFTER_LOSS`: 26
- `ALREADY_OPEN_POSITION`: 23
- Entry rule details:
  - score_below_entry_threshold: 3253
  - blocked_near_year_end: 181
  - year_range_position_too_high: 13

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 149
- `ALREADY_OPEN_POSITION`: 25
- `MAX_NEW_ENTRIES_PER_DAY`: 12
- `MAX_POSITIONS_FULL`: 9
- `NO_NEXT_TRADING_DATE`: 3
- Entry rule details:
  - score_below_entry_threshold: 86
  - year_range_position_extremely_low: 21
  - five_day_falling_knife: 16
  - rsi_extremely_weak: 13
  - rank_below_cutoff: 9
  - blocked_near_year_end: 3
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1034
- `MAX_NEW_ENTRIES_PER_DAY`: 204
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 18
- `NO_NEXT_TRADING_DATE`: 13
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 552
  - rsi_overheated: 158
  - rank_below_cutoff: 144
  - year_range_position_too_low: 51
  - volume_ratio_below_threshold: 37
  - five_day_move_too_extended: 36
  - blocked_near_year_end: 29
  - liquidity_below_threshold: 20
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 31848
- `MAX_NEW_ENTRIES_PER_DAY`: 7631
- `MAX_POSITIONS_FULL`: 4549
- `ALREADY_OPEN_POSITION`: 728
- `NO_NEXT_TRADING_DATE`: 418
- `ZERO_SHARES_AFTER_SIZING`: 24
- Entry rule details:
  - score_below_entry_threshold: 16648
  - rank_below_cutoff: 13545
  - blocked_near_year_end: 1543
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 34
  - rsi_overheated: 22
  - price_not_above_ma120: 9

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 686
- `MAX_POSITIONS_FULL`: 439
- `MAX_NEW_ENTRIES_PER_DAY`: 354
- `ALREADY_OPEN_POSITION`: 103
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 2
- `NO_NEXT_TRADING_DATE`: 2
- Entry rule details:
  - score_below_entry_threshold: 358
  - blocked_near_year_end: 109
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
- `ENTRY_RULE_REJECTED`: 1540
- `NO_NEXT_TRADING_DATE`: 127
- `ALREADY_OPEN_POSITION`: 107
- `ZERO_SHARES_AFTER_SIZING`: 28
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 18
- Entry rule details:
  - blocked_near_year_end: 746
  - rank_below_cutoff: 562
  - score_below_entry_threshold: 230
  - twenty_day_move_too_extended: 2

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 504
- `ALREADY_OPEN_POSITION`: 19
- `MAX_NEW_ENTRIES_PER_DAY`: 19
- `NO_NEXT_TRADING_DATE`: 1
- Entry rule details:
  - five_day_move_too_extended: 166
  - liquidity_below_threshold: 110
  - quality_guard_below_threshold: 70
  - operating_margin_below_threshold: 69
  - rsi_overheated: 26
  - market_cap_too_small: 18
  - roe_below_threshold: 17
  - twenty_day_move_too_extended: 9
  - blocked_near_year_end: 8
  - pbr_too_high: 5
  - rank_below_cutoff: 4
  - five_day_return_too_low: 2
