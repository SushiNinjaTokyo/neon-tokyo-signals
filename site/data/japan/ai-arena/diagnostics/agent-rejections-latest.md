# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-22T16:28:12Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-22

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 2789 | 2557 | 5 | 5 | 5 | 0 | 5 | 5 | 0 | 2784 | ENTRY_RULE_REJECTED (2421) |
| KAESHI / `reversal_snapback` | 251 | 228 | 48 | 48 | 48 | 0 | 48 | 48 | 0 | 203 | ENTRY_RULE_REJECTED (155) |
| KYOU / `daily_striker` | 1462 | 1174 | 92 | 92 | 88 | 4 | 88 | 88 | 0 | 1374 | ENTRY_RULE_REJECTED (1064) |
| MAMORU / `risk_sentinel` | 46556 | 33964 | 138 | 112 | 112 | 0 | 105 | 105 | 7 | 46444 | ENTRY_RULE_REJECTED (33070) |
| MATSU / `contrarian_monk` | 1683 | 887 | 98 | 96 | 94 | 2 | 93 | 93 | 1 | 1589 | ENTRY_RULE_REJECTED (683) |
| NAGARE / `weekly_sage` | 17855 | 1522 | 97 | 69 | 50 | 19 | 44 | 44 | 6 | 17805 | MAX_POSITIONS_FULL (12454) |
| SAGURI / `discovery_scout` | 574 | 574 | 25 | 25 | 25 | 0 | 25 | 25 | 0 | 549 | ENTRY_RULE_REJECTED (534) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 2421
- `MAX_NEW_ENTRIES_PER_DAY`: 212
- `MAX_SYMBOL_CLOSED_TRADES`: 84
- `COOLDOWN_AFTER_LOSS`: 26
- `ALREADY_OPEN_POSITION`: 21
- `NO_NEXT_TRADING_DATE`: 20
- Entry rule details:
  - score_below_entry_threshold: 2226
  - blocked_near_year_end: 186
  - year_range_position_too_high: 9

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 155
- `ALREADY_OPEN_POSITION`: 25
- `MAX_NEW_ENTRIES_PER_DAY`: 12
- `MAX_POSITIONS_FULL`: 9
- `NO_NEXT_TRADING_DATE`: 2
- Entry rule details:
  - score_below_entry_threshold: 91
  - year_range_position_extremely_low: 24
  - five_day_falling_knife: 17
  - rsi_extremely_weak: 13
  - rank_below_cutoff: 9
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1064
- `MAX_NEW_ENTRIES_PER_DAY`: 204
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 18
- `NO_NEXT_TRADING_DATE`: 15
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 583
  - rsi_overheated: 159
  - rank_below_cutoff: 146
  - year_range_position_too_low: 53
  - volume_ratio_below_threshold: 40
  - five_day_move_too_extended: 38
  - liquidity_below_threshold: 20
  - blocked_near_year_end: 18
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 33070
- `MAX_NEW_ENTRIES_PER_DAY`: 7631
- `MAX_POSITIONS_FULL`: 4549
- `ALREADY_OPEN_POSITION`: 756
- `NO_NEXT_TRADING_DATE`: 412
- `ZERO_SHARES_AFTER_SIZING`: 26
- Entry rule details:
  - score_below_entry_threshold: 17340
  - rank_below_cutoff: 13999
  - blocked_near_year_end: 1617
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 35
  - rsi_overheated: 23
  - price_not_above_ma120: 9

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 683
- `MAX_POSITIONS_FULL`: 439
- `MAX_NEW_ENTRIES_PER_DAY`: 354
- `ALREADY_OPEN_POSITION`: 106
- `NO_NEXT_TRADING_DATE`: 3
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 2
- `ZERO_SHARES_AFTER_SIZING`: 2
- Entry rule details:
  - score_below_entry_threshold: 399
  - rank_below_cutoff: 72
  - volatility_too_high: 60
  - price_vs_ma50_outside_band: 53
  - rsi_outside_pullback_band: 42
  - blocked_near_year_end: 35
  - pullback_too_deep: 10
  - liquidity_below_threshold: 6
  - weekly_trend_too_weak: 6

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 12454
- `MAX_NEW_ENTRIES_PER_DAY`: 3721
- `ENTRY_RULE_REJECTED`: 1328
- `NO_NEXT_TRADING_DATE`: 158
- `ALREADY_OPEN_POSITION`: 97
- `ZERO_SHARES_AFTER_SIZING`: 28
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 19
- Entry rule details:
  - rank_below_cutoff: 562
  - blocked_near_year_end: 534
  - score_below_entry_threshold: 230
  - twenty_day_move_too_extended: 2

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 534
- `ALREADY_OPEN_POSITION`: 15
- Entry rule details:
  - five_day_move_too_extended: 170
  - quality_guard_below_threshold: 150
  - liquidity_below_threshold: 85
  - operating_margin_below_threshold: 51
  - rsi_overheated: 28
  - rank_below_cutoff: 12
  - roe_below_threshold: 11
  - twenty_day_move_too_extended: 9
  - market_cap_too_small: 7
  - pbr_too_high: 5
  - blocked_near_year_end: 4
  - five_day_return_too_low: 2
