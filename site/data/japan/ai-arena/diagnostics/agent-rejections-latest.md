# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-08T14:20:09Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-08

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 5519 | 3308 | 20 | 20 | 20 | 0 | 20 | 20 | 0 | 5499 | ENTRY_RULE_REJECTED (3130) |
| KAESHI / `reversal_snapback` | 259 | 219 | 57 | 57 | 57 | 0 | 57 | 57 | 0 | 202 | ENTRY_RULE_REJECTED (129) |
| KYOU / `daily_striker` | 1380 | 1104 | 88 | 88 | 84 | 4 | 84 | 84 | 0 | 1296 | ENTRY_RULE_REJECTED (999) |
| MAMORU / `risk_sentinel` | 42465 | 30668 | 124 | 101 | 101 | 0 | 98 | 98 | 3 | 42364 | ENTRY_RULE_REJECTED (29883) |
| MATSU / `contrarian_monk` | 1196 | 609 | 78 | 78 | 78 | 0 | 77 | 77 | 1 | 1118 | ENTRY_RULE_REJECTED (442) |
| NAGARE / `weekly_sage` | 14024 | 5758 | 256 | 60 | 43 | 17 | 37 | 37 | 6 | 13981 | MAX_POSITIONS_FULL (5753) |
| SAGURI / `discovery_scout` | 580 | 559 | 49 | 49 | 49 | 0 | 49 | 49 | 0 | 531 | ENTRY_RULE_REJECTED (484) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 3130
- `MAX_NEW_ENTRIES_PER_DAY`: 1879
- `NO_NEXT_TRADING_DATE`: 332
- `MAX_SYMBOL_CLOSED_TRADES`: 80
- `ALREADY_OPEN_POSITION`: 39
- `COOLDOWN_AFTER_LOSS`: 39
- Entry rule details:
  - score_below_entry_threshold: 2824
  - blocked_near_year_end: 169
  - year_range_position_too_high: 97
  - market_regime_panic_entry_disabled: 38
  - liquidity_below_threshold: 1
  - valuation_discount_below_threshold: 1

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 129
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
  - reversal_confirmation_failed:0/1: 2
  - liquidity_below_threshold: 1
  - market_regime_panic_entry_disabled: 1
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 999
- `MAX_NEW_ENTRIES_PER_DAY`: 205
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 17
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- `NO_NEXT_TRADING_DATE`: 2
- Entry rule details:
  - score_below_entry_threshold: 544
  - rsi_overheated: 155
  - rank_below_cutoff: 144
  - year_range_position_too_low: 49
  - volume_ratio_below_threshold: 36
  - five_day_move_too_extended: 35
  - liquidity_below_threshold: 20
  - blocked_near_year_end: 9
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 29883
- `MAX_NEW_ENTRIES_PER_DAY`: 6850
- `MAX_POSITIONS_FULL`: 4559
- `ALREADY_OPEN_POSITION`: 661
- `NO_NEXT_TRADING_DATE`: 388
- `ZERO_SHARES_AFTER_SIZING`: 23
- Entry rule details:
  - score_below_entry_threshold: 15333
  - rank_below_cutoff: 12876
  - blocked_near_year_end: 1572
  - price_not_above_ma50: 47
  - weekly_trend_too_weak: 31
  - rsi_overheated: 19
  - price_not_above_ma120: 5

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 442
- `MAX_NEW_ENTRIES_PER_DAY`: 323
- `MAX_POSITIONS_FULL`: 221
- `ALREADY_OPEN_POSITION`: 89
- `NO_NEXT_TRADING_DATE`: 43
- Entry rule details:
  - score_below_entry_threshold: 280
  - blocked_near_year_end: 53
  - rsi_outside_pullback_band: 42
  - rank_below_cutoff: 29
  - price_vs_ma50_outside_band: 21
  - pullback_too_deep: 8
  - weekly_trend_too_weak: 5
  - volatility_too_high: 4

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 5753
- `ENTRY_RULE_REJECTED`: 5244
- `MAX_NEW_ENTRIES_PER_DAY`: 2415
- `ALREADY_OPEN_POSITION`: 258
- `ZERO_SHARES_AFTER_SIZING`: 196
- `NO_NEXT_TRADING_DATE`: 98
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 17
- Entry rule details:
  - rank_below_cutoff: 3227
  - score_below_entry_threshold: 1174
  - blocked_near_year_end: 840
  - twenty_day_move_too_extended: 3

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 484
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
  - twenty_day_move_too_extended: 6
  - market_regime_panic_entry_disabled: 5
  - five_day_return_too_low: 3
  - pullback_too_deep: 1
  - short_term_euphoria_rejected: 1
