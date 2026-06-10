# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-10T07:20:35Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-10

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 5244 | 3348 | 20 | 20 | 20 | 0 | 20 | 20 | 0 | 5224 | ENTRY_RULE_REJECTED (3161) |
| KAESHI / `reversal_snapback` | 260 | 220 | 57 | 57 | 57 | 0 | 57 | 57 | 0 | 203 | ENTRY_RULE_REJECTED (130) |
| KYOU / `daily_striker` | 1383 | 1109 | 88 | 88 | 84 | 4 | 84 | 84 | 0 | 1299 | ENTRY_RULE_REJECTED (1004) |
| MAMORU / `risk_sentinel` | 43237 | 31449 | 126 | 103 | 103 | 0 | 98 | 98 | 5 | 43134 | ENTRY_RULE_REJECTED (30647) |
| MATSU / `contrarian_monk` | 1280 | 681 | 78 | 78 | 78 | 0 | 77 | 77 | 1 | 1202 | ENTRY_RULE_REJECTED (514) |
| NAGARE / `weekly_sage` | 14210 | 5064 | 259 | 63 | 44 | 19 | 38 | 38 | 6 | 14166 | MAX_POSITIONS_FULL (6550) |
| SAGURI / `discovery_scout` | 583 | 560 | 49 | 49 | 49 | 0 | 49 | 49 | 0 | 534 | ENTRY_RULE_REJECTED (485) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 3161
- `MAX_NEW_ENTRIES_PER_DAY`: 1879
- `MAX_SYMBOL_CLOSED_TRADES`: 87
- `COOLDOWN_AFTER_LOSS`: 41
- `ALREADY_OPEN_POSITION`: 39
- `NO_NEXT_TRADING_DATE`: 17
- Entry rule details:
  - score_below_entry_threshold: 2901
  - year_range_position_too_high: 97
  - blocked_near_year_end: 92
  - market_regime_panic_entry_disabled: 69
  - liquidity_below_threshold: 1
  - valuation_discount_below_threshold: 1

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 130
- `ALREADY_OPEN_POSITION`: 33
- `MAX_NEW_ENTRIES_PER_DAY`: 29
- `MAX_POSITIONS_FULL`: 10
- `NO_NEXT_TRADING_DATE`: 1
- Entry rule details:
  - rank_below_cutoff: 53
  - year_range_position_extremely_low: 30
  - five_day_falling_knife: 19
  - rsi_extremely_weak: 16
  - score_below_entry_threshold: 6
  - market_regime_panic_entry_disabled: 2
  - reversal_confirmation_failed:0/1: 2
  - liquidity_below_threshold: 1
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1004
- `MAX_NEW_ENTRIES_PER_DAY`: 205
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 17
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- Entry rule details:
  - score_below_entry_threshold: 550
  - rsi_overheated: 156
  - rank_below_cutoff: 144
  - year_range_position_too_low: 49
  - five_day_move_too_extended: 37
  - volume_ratio_below_threshold: 36
  - liquidity_below_threshold: 20
  - blocked_near_year_end: 5
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 30647
- `MAX_NEW_ENTRIES_PER_DAY`: 6850
- `MAX_POSITIONS_FULL`: 4559
- `ALREADY_OPEN_POSITION`: 676
- `NO_NEXT_TRADING_DATE`: 379
- `ZERO_SHARES_AFTER_SIZING`: 23
- Entry rule details:
  - score_below_entry_threshold: 15849
  - rank_below_cutoff: 13139
  - blocked_near_year_end: 1553
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 32
  - rsi_overheated: 22
  - price_not_above_ma120: 5

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 514
- `MAX_NEW_ENTRIES_PER_DAY`: 323
- `MAX_POSITIONS_FULL`: 221
- `ALREADY_OPEN_POSITION`: 89
- `NO_NEXT_TRADING_DATE`: 55
- Entry rule details:
  - score_below_entry_threshold: 285
  - blocked_near_year_end: 117
  - rsi_outside_pullback_band: 42
  - rank_below_cutoff: 29
  - price_vs_ma50_outside_band: 24
  - pullback_too_deep: 8
  - weekly_trend_too_weak: 5
  - volatility_too_high: 4

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 6550
- `ENTRY_RULE_REJECTED`: 4593
- `MAX_NEW_ENTRIES_PER_DAY`: 2512
- `ALREADY_OPEN_POSITION`: 212
- `ZERO_SHARES_AFTER_SIZING`: 196
- `NO_NEXT_TRADING_DATE`: 84
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 19
- Entry rule details:
  - rank_below_cutoff: 3227
  - score_below_entry_threshold: 1174
  - blocked_near_year_end: 188
  - twenty_day_move_too_extended: 4

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 485
- `ALREADY_OPEN_POSITION`: 26
- `MAX_NEW_ENTRIES_PER_DAY`: 21
- `NO_NEXT_TRADING_DATE`: 2
- Entry rule details:
  - five_day_move_too_extended: 152
  - quality_guard_below_threshold: 71
  - operating_margin_below_threshold: 67
  - liquidity_below_threshold: 65
  - score_below_entry_threshold: 33
  - rsi_overheated: 30
  - roe_below_threshold: 19
  - rank_below_cutoff: 14
  - market_cap_too_small: 10
  - pbr_too_high: 7
  - market_regime_panic_entry_disabled: 6
  - twenty_day_move_too_extended: 6
  - five_day_return_too_low: 3
  - pullback_too_deep: 1
  - short_term_euphoria_rejected: 1
