# AI Arena Agent Rejection Diagnostics

Generated: 2026-05-29T07:37:09Z
Run: `arena_jp_rebuild_2026_v009`
Season: 2026-01-01 → 2026-05-29

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 2639 | 532 | 242 | 207 | 204 | 3 | 202 | 202 | 2 | 2435 | MAX_NEW_ENTRIES_PER_DAY (1819) |
| KAESHI / `reversal_snapback` | 103 | 92 | 34 | 34 | 34 | 0 | 34 | 34 | 0 | 69 | ENTRY_RULE_REJECTED (30) |
| KYOU / `daily_striker` | 466 | 311 | 115 | 110 | 110 | 0 | 110 | 110 | 0 | 356 | ENTRY_RULE_REJECTED (176) |
| MAMORU / `risk_sentinel` | 17180 | 14020 | 108 | 96 | 96 | 0 | 90 | 90 | 6 | 17084 | ENTRY_RULE_REJECTED (13237) |
| MATSU / `contrarian_monk` | 512 | 332 | 57 | 57 | 57 | 0 | 54 | 54 | 3 | 455 | ENTRY_RULE_REJECTED (209) |
| NAGARE / `weekly_sage` | 5114 | 1963 | 198 | 78 | 48 | 30 | 41 | 41 | 7 | 5066 | MAX_POSITIONS_FULL (2151) |
| SAGURI / `discovery_scout` | 112 | 112 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 112 | ENTRY_RULE_REJECTED (112) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `MAX_NEW_ENTRIES_PER_DAY`: 1819
- `MAX_POSITIONS_FULL`: 275
- `ALREADY_OPEN_POSITION`: 208
- `ENTRY_RULE_REJECTED`: 82
- `ZERO_SHARES_AFTER_SIZING`: 35
- `NO_NEXT_TRADING_DATE`: 13
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 3
- Entry rule details:
  - blocked_near_year_end: 65
  - rank_below_cutoff: 12
  - valuation_discount_below_threshold: 3
  - quality_guard_below_threshold: 2

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 30
- `ALREADY_OPEN_POSITION`: 28
- `MAX_NEW_ENTRIES_PER_DAY`: 11
- Entry rule details:
  - score_below_entry_threshold: 30

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 176
- `MAX_NEW_ENTRIES_PER_DAY`: 142
- `ALREADY_OPEN_POSITION`: 20
- `MAX_POSITIONS_FULL`: 7
- `NO_NEXT_TRADING_DATE`: 6
- `ZERO_SHARES_AFTER_SIZING`: 5
- Entry rule details:
  - rsi_overheated: 82
  - score_below_entry_threshold: 44
  - volume_ratio_below_threshold: 27
  - liquidity_below_threshold: 10
  - five_day_move_too_extended: 9
  - blocked_near_year_end: 2
  - twenty_day_move_too_extended: 1
  - volatility_too_high: 1

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
- `MAX_POSITIONS_FULL`: 2151
- `ENTRY_RULE_REJECTED`: 1480
- `MAX_NEW_ENTRIES_PER_DAY`: 971
- `ALREADY_OPEN_POSITION`: 285
- `ZERO_SHARES_AFTER_SIZING`: 120
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 30
- `NO_NEXT_TRADING_DATE`: 29
- Entry rule details:
  - rank_below_cutoff: 822
  - score_below_entry_threshold: 426
  - blocked_near_year_end: 172
  - volatility_too_high: 45
  - twenty_day_move_too_extended: 15

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 112
- Entry rule details:
  - bucket_not_allowed: 104
  - blocked_near_year_end: 8
