# AI Arena Agent Rejection Diagnostics

Generated: 2026-06-05T12:26:17Z
Run: `arena_jp_live_2026`
Season: 2026-01-01 → 2026-06-05

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 5279 | 3455 | 19 | 19 | 19 | 0 | 19 | 19 | 0 | 5260 | ENTRY_RULE_REJECTED (3279) |
| KAESHI / `reversal_snapback` | 258 | 218 | 57 | 57 | 57 | 0 | 57 | 57 | 0 | 201 | ENTRY_RULE_REJECTED (128) |
| KYOU / `daily_striker` | 1378 | 1102 | 86 | 86 | 82 | 4 | 82 | 82 | 0 | 1296 | ENTRY_RULE_REJECTED (1000) |
| MAMORU / `risk_sentinel` | 42077 | 30267 | 122 | 99 | 99 | 0 | 97 | 97 | 2 | 41978 | ENTRY_RULE_REJECTED (29494) |
| MATSU / `contrarian_monk` | 1153 | 584 | 78 | 78 | 78 | 0 | 77 | 77 | 1 | 1075 | ENTRY_RULE_REJECTED (417) |
| NAGARE / `weekly_sage` | 13926 | 5661 | 256 | 60 | 43 | 17 | 36 | 36 | 7 | 13883 | MAX_POSITIONS_FULL (5753) |
| SAGURI / `discovery_scout` | 580 | 561 | 46 | 46 | 46 | 0 | 46 | 46 | 0 | 534 | ENTRY_RULE_REJECTED (490) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 3279
- `MAX_NEW_ENTRIES_PER_DAY`: 1801
- `MAX_SYMBOL_CLOSED_TRADES`: 78
- `COOLDOWN_AFTER_LOSS`: 40
- `ALREADY_OPEN_POSITION`: 39
- `NO_NEXT_TRADING_DATE`: 23
- Entry rule details:
  - score_below_entry_threshold: 2941
  - blocked_near_year_end: 218
  - year_range_position_too_high: 100
  - market_regime_panic_entry_disabled: 18
  - five_day_return_too_low: 1
  - liquidity_below_threshold: 1

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 128
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
  - rsi_not_oversold_enough: 1

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 1000
- `MAX_NEW_ENTRIES_PER_DAY`: 205
- `MAX_POSITIONS_FULL`: 69
- `ALREADY_OPEN_POSITION`: 16
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 4
- `NO_NEXT_TRADING_DATE`: 2
- Entry rule details:
  - score_below_entry_threshold: 533
  - rsi_overheated: 153
  - rank_below_cutoff: 142
  - year_range_position_too_low: 49
  - volume_ratio_below_threshold: 36
  - five_day_move_too_extended: 33
  - blocked_near_year_end: 27
  - liquidity_below_threshold: 20
  - volatility_too_high: 4
  - range_position_20d_too_low: 2
  - twenty_day_move_too_extended: 1

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 29494
- `MAX_NEW_ENTRIES_PER_DAY`: 6850
- `MAX_POSITIONS_FULL`: 4559
- `ALREADY_OPEN_POSITION`: 651
- `NO_NEXT_TRADING_DATE`: 401
- `ZERO_SHARES_AFTER_SIZING`: 23
- Entry rule details:
  - score_below_entry_threshold: 15078
  - rank_below_cutoff: 12751
  - blocked_near_year_end: 1565
  - price_not_above_ma50: 46
  - weekly_trend_too_weak: 31
  - rsi_overheated: 18
  - price_not_above_ma120: 5

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 417
- `MAX_NEW_ENTRIES_PER_DAY`: 323
- `MAX_POSITIONS_FULL`: 221
- `ALREADY_OPEN_POSITION`: 89
- `NO_NEXT_TRADING_DATE`: 25
- Entry rule details:
  - score_below_entry_threshold: 275
  - rsi_outside_pullback_band: 42
  - blocked_near_year_end: 33
  - rank_below_cutoff: 29
  - price_vs_ma50_outside_band: 21
  - pullback_too_deep: 8
  - weekly_trend_too_weak: 5
  - volatility_too_high: 4

### NAGARE / `weekly_sage`
- `MAX_POSITIONS_FULL`: 5753
- `ENTRY_RULE_REJECTED`: 5153
- `MAX_NEW_ENTRIES_PER_DAY`: 2415
- `ALREADY_OPEN_POSITION`: 252
- `ZERO_SHARES_AFTER_SIZING`: 196
- `NO_NEXT_TRADING_DATE`: 97
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 17
- Entry rule details:
  - rank_below_cutoff: 3227
  - score_below_entry_threshold: 1174
  - blocked_near_year_end: 749
  - twenty_day_move_too_extended: 3

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 490
- `ALREADY_OPEN_POSITION`: 25
- `MAX_NEW_ENTRIES_PER_DAY`: 19
- Entry rule details:
  - five_day_move_too_extended: 153
  - quality_guard_below_threshold: 72
  - operating_margin_below_threshold: 67
  - liquidity_below_threshold: 65
  - score_below_entry_threshold: 33
  - rsi_overheated: 30
  - roe_below_threshold: 20
  - rank_below_cutoff: 14
  - market_cap_too_small: 10
  - pbr_too_high: 10
  - twenty_day_move_too_extended: 6
  - market_regime_panic_entry_disabled: 5
  - five_day_return_too_low: 3
  - pullback_too_deep: 1
  - short_term_euphoria_rejected: 1
