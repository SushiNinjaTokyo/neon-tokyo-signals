# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-02T00:59:22Z
Run: `arena_jp_rebuild_2026_v019`
Season: 2026-01-01 → 2026-06-01

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 7832 | 4703 | 30 | 30 | 30 | 0 | 28 | 28 | 2 | 7802 | ENTRY_RULE_REJECTED (4564) |
| KAESHI / `reversal_snapback` | 257 | 115 | 67 | 67 | 67 | 0 | 66 | 66 | 1 | 190 | MAX_POSITIONS_FULL (72) |
| KYOU / `daily_striker` | 1330 | 1056 | 83 | 83 | 79 | 4 | 79 | 79 | 0 | 1251 | ENTRY_RULE_REJECTED (957) |
| MAMORU / `risk_sentinel` | 40093 | 28684 | 119 | 96 | 96 | 0 | 92 | 92 | 4 | 39997 | ENTRY_RULE_REJECTED (27935) |
| MATSU / `contrarian_monk` | 1101 | 557 | 78 | 78 | 78 | 0 | 74 | 74 | 4 | 1023 | ENTRY_RULE_REJECTED (390) |
| NAGARE / `weekly_sage` | 13411 | 5600 | 253 | 57 | 42 | 15 | 36 | 36 | 6 | 13369 | MAX_POSITIONS_FULL (5466) |
| SAGURI / `discovery_scout` | 575 | 556 | 44 | 42 | 42 | 0 | 41 | 41 | 1 | 533 | ENTRY_RULE_REJECTED (486) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 4564
- `MAX_NEW_ENTRIES_PER_DAY`: 2720
- `MAX_POSITIONS_FULL`: 409
- `ALREADY_OPEN_POSITION`: 109
- Entry rule details:
  - rank_below_cutoff: 3451
  - blocked_near_year_end: 557
  - year_range_position_too_high: 451
  - five_day_return_too_low: 46
  - score_below_entry_threshold: 42
  - liquidity_below_threshold: 6
  - valuation_discount_below_threshold: 5
  - pullback_too_deep: 3
  - quality_guard_below_threshold: 2
  - medium_return_too_weak: 1

### KAESHI / `reversal_snapback`
- `MAX_POSITIONS_FULL`: 72
- `MAX_NEW_ENTRIES_PER_DAY`: 70
- `ALREADY_OPEN_POSITION`: 37
- `ENTRY_RULE_REJECTED`: 11
- Entry rule details:
  - blocked_near_year_end: 4
  - score_below_entry_threshold: 3
  - reversal_confirmation_failed:0/1: 2
  - liquidity_below_threshold: 1
  - rsi_not_oversold_enough: 1

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
- `MAX_POSITIONS_FULL`: 5466
- `ENTRY_RULE_REJECTED`: 5100
- `MAX_NEW_ENTRIES_PER_DAY`: 2345
- `ALREADY_OPEN_POSITION`: 247
- `ZERO_SHARES_AFTER_SIZING`: 196
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 15
- Entry rule details:
  - rank_below_cutoff: 3227
  - score_below_entry_threshold: 1174
  - blocked_near_year_end: 696
  - twenty_day_move_too_extended: 3

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 486
- `ALREADY_OPEN_POSITION`: 26
- `MAX_NEW_ENTRIES_PER_DAY`: 19
- `ZERO_SHARES_AFTER_SIZING`: 2
- Entry rule details:
  - five_day_move_too_extended: 153
  - operating_margin_below_threshold: 69
  - quality_guard_below_threshold: 69
  - liquidity_below_threshold: 63
  - blocked_near_year_end: 37
  - score_below_entry_threshold: 33
  - roe_below_threshold: 23
  - rank_below_cutoff: 14
  - pbr_too_high: 11
  - market_cap_too_small: 10
  - five_day_return_too_low: 3
  - pullback_too_deep: 1
