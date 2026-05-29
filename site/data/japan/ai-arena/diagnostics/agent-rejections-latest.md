# AI Arena Agent Rejection Diagnostics

Generated: 2026-05-29T07:05:53Z
Run: `arena_jp_rebuild_2026_v008`
Season: 2026-01-01 → 2026-05-29

| Agent | Candidates | Evaluated | Entry Pass | Orders | Buy Fills | Buy Cancels | Sells | Trades | Open | Rejected | Top Reject Reason |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| HIZUMI / `value_mispricing` | 2639 | 2626 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2639 | ENTRY_RULE_REJECTED (2626) |
| KAESHI / `reversal_snapback` | 103 | 92 | 34 | 34 | 34 | 0 | 34 | 34 | 0 | 69 | ENTRY_RULE_REJECTED (30) |
| KYOU / `daily_striker` | 621 | 462 | 85 | 85 | 84 | 1 | 84 | 84 | 0 | 537 | ENTRY_RULE_REJECTED (299) |
| MAMORU / `risk_sentinel` | 18814 | 17473 | 96 | 96 | 96 | 0 | 94 | 94 | 2 | 18718 | ENTRY_RULE_REJECTED (16884) |
| MATSU / `contrarian_monk` | 716 | 678 | 44 | 43 | 43 | 0 | 41 | 41 | 2 | 673 | ENTRY_RULE_REJECTED (567) |
| NAGARE / `weekly_sage` | 5704 | 2674 | 153 | 67 | 50 | 17 | 47 | 47 | 3 | 5654 | ENTRY_RULE_REJECTED (2234) |
| SAGURI / `discovery_scout` | 167 | 167 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 167 | ENTRY_RULE_REJECTED (167) |

## Reject reasons by agent

### HIZUMI / `value_mispricing`
- `ENTRY_RULE_REJECTED`: 2626
- `NO_NEXT_TRADING_DATE`: 13
- Entry rule details:
  - score_below_entry_threshold: 2532
  - blocked_near_year_end: 94

### KAESHI / `reversal_snapback`
- `ENTRY_RULE_REJECTED`: 30
- `ALREADY_OPEN_POSITION`: 28
- `MAX_NEW_ENTRIES_PER_DAY`: 11
- Entry rule details:
  - score_below_entry_threshold: 30

### KYOU / `daily_striker`
- `ENTRY_RULE_REJECTED`: 299
- `MAX_NEW_ENTRIES_PER_DAY`: 102
- `ALREADY_OPEN_POSITION`: 78
- `MAX_POSITIONS_FULL`: 52
- `NO_NEXT_TRADING_DATE`: 5
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 1
- Entry rule details:
  - score_below_entry_threshold: 234
  - rsi_overheated: 46
  - blocked_near_year_end: 6
  - liquidity_below_threshold: 6
  - rank_below_cutoff: 5
  - volume_ratio_below_threshold: 2

### MAMORU / `risk_sentinel`
- `ENTRY_RULE_REJECTED`: 16884
- `MAX_NEW_ENTRIES_PER_DAY`: 1146
- `ALREADY_OPEN_POSITION`: 493
- `NO_NEXT_TRADING_DATE`: 195
- Entry rule details:
  - score_below_entry_threshold: 11896
  - rank_below_cutoff: 4264
  - blocked_near_year_end: 723
  - price_not_above_ma120: 1

### MATSU / `contrarian_monk`
- `ENTRY_RULE_REJECTED`: 567
- `ALREADY_OPEN_POSITION`: 67
- `MAX_NEW_ENTRIES_PER_DAY`: 33
- `NO_NEXT_TRADING_DATE`: 3
- `MAX_POSITIONS_FULL`: 2
- `ZERO_SHARES_AFTER_SIZING`: 1
- Entry rule details:
  - score_below_entry_threshold: 454
  - price_vs_ma50_outside_band: 46
  - rank_below_cutoff: 39
  - blocked_near_year_end: 22
  - rsi_outside_pullback_band: 6

### NAGARE / `weekly_sage`
- `ENTRY_RULE_REJECTED`: 2234
- `MAX_POSITIONS_FULL`: 2031
- `MAX_NEW_ENTRIES_PER_DAY`: 968
- `ALREADY_OPEN_POSITION`: 287
- `ZERO_SHARES_AFTER_SIZING`: 86
- `NO_NEXT_TRADING_DATE`: 31
- `CANCELLED_NO_CASH_OR_DUPLICATE_AT_EXECUTION`: 17
- Entry rule details:
  - rank_below_cutoff: 1084
  - score_below_entry_threshold: 919
  - blocked_near_year_end: 227
  - volatility_too_high: 4

### SAGURI / `discovery_scout`
- `ENTRY_RULE_REJECTED`: 167
- Entry rule details:
  - score_below_entry_threshold: 98
  - bucket_not_allowed: 60
  - blocked_near_year_end: 9
