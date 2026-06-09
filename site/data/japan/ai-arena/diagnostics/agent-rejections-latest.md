# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-09T04:59:00Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-09

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 5532 | 3327 | 20 | 20 | 20 | 0 | 20 | 20 | 0 | 5512 | ENTRY_RULE_REJECTED (3144) |
| KAESHI / `reversal_snapback` | 259 | 220 | 57 | 57 | 57 | 0 | 57 | 57 | 0 | 202 | ENTRY_RULE_REJECTED (130) |
| KYOU / `daily_striker` | 1383 | 1106 | 88 | 88 | 84 | 4 | 84 | 84 | 0 | 1299 | ENTRY_RULE_REJECTED (1001) |
| MAMORU / `risk_sentinel` | 42858 | 31056 | 125 | 102 | 102 | 0 | 98 | 98 | 4 | 42756 | ENTRY_RULE_REJECTED (30263) |
| MATSU / `contrarian_monk` | 1225 | 652 | 78 | 78 | 78 | 0 | 77 | 77 | 1 | 1147 | ENTRY_RULE_REJECTED (485) |
| NAGARE / `weekly_sage` | 14126 | 4962 | 259 | 63 | 44 | 19 | 38 | 38 | 6 | 14082 | MAX_POSITIONS_FULL (6550) |
| SAGURI / `discovery_scout` | 581 | 560 | 49 | 49 | 49 | 0 | 49 | 49 | 0 | 532 | ENTRY_RULE_REJECTED (485) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 3144
- `MAX_NEW_ENTRIES_PER_DAY`: 1879
- `NO_NEXT_TRADING_DATE`: 326
- `MAX_SYMBOL_CLOSED_TRADES`: 84
- `COOLDOWN_AFTER_LOSS`: 40
- `ALREADY_OPEN_POSITION`: 39
- Entry rule details:
  - score_below_entry_threshold: 2861
  - blocked_near_year_end: 132
  - year_range_position_too_high: 97
  - market_regime_panic_entry_disabled: 52
  - liquidity_below_threshold: 1
  - valuation_discount_below_threshold: 1

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 130
- `ALREADY_OPEN_POSITION`: 33
- `MAX_NEW_ENTRIES_PER_DAY`: 29
- `MAX_POSITIONS_FULL`: 10
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
- `ENTRY_RULE_REJECTED`: 1001
- `MAX_NEW_ENTRIES_PER_DAY`: 205
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 17
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- `NO_NEXT_TRADING_DATE`: 3
- Entry rule details:
  - score_below_entry_threshold: 548
  - rsi_overheated: 156
  - rank_below_cutoff: 144
  - year_range_position_too_low: 49
  - five_day_move_too_extended: 37
  - volume_ratio_below_threshold: 36
  - liquidity_below_threshold: 20
  - blocked_near_year_end: 4
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 30263
- `MAX_NEW_ENTRIES_PER_DAY`: 6850
- `MAX_POSITIONS_FULL`: 4559
- `ALREADY_OPEN_POSITION`: 668
- `NO_NEXT_TRADING_DATE`: 393
- `ZERO_SHARES_AFTER_SIZING`: 23
- Entry rule details:
  - score_below_entry_threshold: 15589
  - rank_below_cutoff: 13000
  - blocked_near_year_end: 1570
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 32
  - rsi_overheated: 20
  - price_not_above_ma120: 5

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 485
- `MAX_NEW_ENTRIES_PER_DAY`: 323
- `MAX_POSITIONS_FULL`: 221
- `ALREADY_OPEN_POSITION`: 89
- `NO_NEXT_TRADING_DATE`: 29
- Entry rule details:
  - score_below_entry_threshold: 280
  - blocked_near_year_end: 95
  - rsi_outside_pullback_band: 42
  - rank_below_cutoff: 29
  - price_vs_ma50_outside_band: 22
  - pullback_too_deep: 8
  - weekly_trend_too_weak: 5
  - volatility_too_high: 4

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 6550
- `ENTRY_RULE_REJECTED`: 4497
- `MAX_NEW_ENTRIES_PER_DAY`: 2512
- `ALREADY_OPEN_POSITION`: 206
- `ZERO_SHARES_AFTER_SIZING`: 196
- `NO_NEXT_TRADING_DATE`: 102
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 19
- Entry rule details:
  - rank_below_cutoff: 3227
  - score_below_entry_threshold: 1174
  - blocked_near_year_end: 92
  - twenty_day_move_too_extended: 4

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 485
- `ALREADY_OPEN_POSITION`: 26
- `MAX_NEW_ENTRIES_PER_DAY`: 21
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
