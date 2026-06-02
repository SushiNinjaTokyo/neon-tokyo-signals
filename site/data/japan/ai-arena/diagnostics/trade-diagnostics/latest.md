# Neon Tokyo AI Arena Trade Diagnostics

Generated: `2026-06-02T06:25:11+00:00`
Run ID: `display`

> Purpose: agent-by-agent win/loss diagnosis and rule-improvement source data.

## Dataset Summary

- Closed trades: **1500**
- Agents with closed trades: **7**
- Official agents: **7**
- Agent summaries: **7**
- Exported compact trade rows in JSON: **1500**

## Diagnostics Notes

- WARNING: arena_trades has no closed trades for run_id='display'; falling back to all closed trades in the current DuckDB.
- Requested run_id: `display`
- Used run_id filter: `False`
- Fallback used: `True`

## Agent Summary

| Agent | Trades | Win | Avg Ret | Avg Win | Avg Loss | Payoff | PF | PnL | Avg MFE | Avg MAE | Top Failure Patterns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KYOU / `daily_striker` | 386 | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 0.0000 | ¥6,799,597 | 0.00% | 0.00% | NORMAL_WIN:386 |
| NAGARE / `weekly_sage` | 83 | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 0.0000 | ¥27,182,965 | 0.00% | 0.00% | NORMAL_WIN:83 |
| MAMORU / `risk_sentinel` | 459 | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 0.0000 | ¥18,361,997 | 0.00% | 0.00% | NORMAL_WIN:459 |
| SAGURI / `discovery_scout` | 82 | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 0.0000 | ¥-883,942 | 0.00% | 0.00% | NORMAL_WIN:82 |
| MATSU / `contrarian_monk` | 149 | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 0.0000 | ¥19,974,614 | 0.00% | 0.00% | NORMAL_WIN:149 |
| KAESHI / `reversal_snapback` | 177 | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 0.0000 | ¥1,333,539 | 0.00% | 0.00% | NORMAL_WIN:177 |
| HIZUMI / `value_mispricing` | 164 | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 0.0000 | ¥4,958,828 | 0.00% | 0.00% | NORMAL_WIN:164 |

## KYOU / `daily_striker`

Short-Term Breakout / Momentum

### Key Metrics

- Trades: **386**, Win rate: **0.00%**, Total PnL: **¥6,799,597**
- Avg return: **0.00%**, Avg win: **0.00%**, Avg loss: **0.00%**
- Payoff ratio: **0.0000**, Profit factor: **0.0000**
- Avg MFE: **0.00%**, Avg MAE: **0.00%**

### Exit Reasons

```json
{
  "UNKNOWN": 386
}
```

### Failure Patterns

```json
{
  "NORMAL_WIN": 386
}
```

### Success Patterns

```json
{}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3070.T | JELLY BEANS GROUP Co.,Ltd. | 2026-01-27 | 2026-01-28 | 0.00% | ¥-223,805 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3070.T | JELLY BEANS GROUP Co.,Ltd. | 2026-01-27 | 2026-01-28 | 0.00% | ¥-223,805 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3070.T | JELLY BEANS GROUP Co.,Ltd. | 2026-01-27 | 2026-01-28 | 0.00% | ¥-223,805 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3070.T | JELLY BEANS GROUP Co.,Ltd. | 2026-01-27 | 2026-01-28 | 0.00% | ¥-223,805 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3070.T | JELLY BEANS GROUP Co.,Ltd. | 2026-01-27 | 2026-01-28 | 0.00% | ¥-223,805 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3070.T | JELLY BEANS GROUP Co.,Ltd. | 2026-01-27 | 2026-01-28 | 0.00% | ¥-223,805 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3070.T | JELLY BEANS GROUP Co.,Ltd. | 2026-01-27 | 2026-01-28 | 0.00% | ¥-222,671 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 202A.T | MAMEZO CO.,LTD. | 2026-01-22 | 2026-01-27 | 0.00% | ¥-200,680 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 202A.T | MAMEZO CO.,LTD. | 2026-01-22 | 2026-01-27 | 0.00% | ¥-200,680 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 202A.T | MAMEZO CO.,LTD. | 2026-01-22 | 2026-01-27 | 0.00% | ¥-200,680 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 202A.T | MAMEZO CO.,LTD. | 2026-01-22 | 2026-01-27 | 0.00% | ¥-200,680 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 202A.T | MAMEZO CO.,LTD. | 2026-01-22 | 2026-01-27 | 0.00% | ¥-200,680 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 202A.T | MAMEZO CO.,LTD. | 2026-01-22 | 2026-01-27 | 0.00% | ¥-200,680 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 202A.T | MAMEZO CO.,LTD. | 2026-01-22 | 2026-01-27 | 0.00% | ¥-200,680 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5344.T | ＭＡＲＵＷＡ | 2026-02-04 | 2026-02-06 | 0.00% | ¥-180,019 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 198A.T | PostPrime Inc. | 2026-01-19 | 2026-01-20 | 0.00% | ¥671,809 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 198A.T | PostPrime Inc. | 2026-01-19 | 2026-01-20 | 0.00% | ¥671,809 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 198A.T | PostPrime Inc. | 2026-01-19 | 2026-01-20 | 0.00% | ¥671,809 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 198A.T | PostPrime Inc. | 2026-01-19 | 2026-01-20 | 0.00% | ¥671,809 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 198A.T | PostPrime Inc. | 2026-01-19 | 2026-01-20 | 0.00% | ¥671,809 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 198A.T | PostPrime Inc. | 2026-01-19 | 2026-01-20 | 0.00% | ¥671,809 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 198A.T | PostPrime Inc. | 2026-01-19 | 2026-01-20 | 0.00% | ¥671,809 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 276A.T | CCReB Advisors Inc. | 2026-02-03 | 2026-02-05 | 0.00% | ¥406,822 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 276A.T | CCReB Advisors Inc. | 2026-02-03 | 2026-02-05 | 0.00% | ¥401,566 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 276A.T | CCReB Advisors Inc. | 2026-02-03 | 2026-02-05 | 0.00% | ¥401,566 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 276A.T | CCReB Advisors Inc. | 2026-02-03 | 2026-02-05 | 0.00% | ¥401,566 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 276A.T | CCReB Advisors Inc. | 2026-02-03 | 2026-02-05 | 0.00% | ¥401,566 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 276A.T | CCReB Advisors Inc. | 2026-02-03 | 2026-02-05 | 0.00% | ¥401,566 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 276A.T | CCReB Advisors Inc. | 2026-02-03 | 2026-02-05 | 0.00% | ¥401,566 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4894.T | Cuorips Inc. | 2026-01-09 | 2026-01-16 | 0.00% | ¥286,503 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3563.T | ＦＯＯＤ ＆ ＬＩＦＥ ＣＯＭＰＡＮＩＥＳ | 2026-01-06 | 2026-01-07 | 0.00% | ¥3,011 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4062.T | イビデン | 2026-01-06 | 2026-01-07 | 0.00% | ¥-44,702 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-22,420 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3563.T | ＦＯＯＤ ＆ ＬＩＦＥ ＣＯＭＰＡＮＩＥＳ | 2026-01-06 | 2026-01-07 | 0.00% | ¥3,011 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4062.T | イビデン | 2026-01-06 | 2026-01-07 | 0.00% | ¥-44,702 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-01-06 | 2026-01-07 | 0.00% | ¥48,997 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-22,420 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5020.T | ＥＮＥＯＳホールディングス | 2026-01-07 | 2026-01-08 | 0.00% | ¥-21,283 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Compact Entry Context For Worst Trades

- `3070.T` 2026-01-27 → 2026-01-28 0.00%: feature: return_5d_pct=42.85714285714286, return_20d_pct=66.66666666666667, volume_ratio_20d=7.809473850918813, rsi_14=80.59701492537313, range_position_252d_0_1=0.20703125 / value: value_trap_penalty=0.25 / sector_relative: sector_33_name=卸売業 / fund: market_cap_jpy=7342772736.0, per=None, pbr=1.4650718, roe_pct=-9.423999499999999, operating_margin_pct=4.027
- `3070.T` 2026-01-27 → 2026-01-28 0.00%: feature: return_5d_pct=42.85714285714286, return_20d_pct=66.66666666666667, volume_ratio_20d=7.809473850918813, rsi_14=80.59701492537313, range_position_252d_0_1=0.20703125 / value: value_trap_penalty=0.25 / sector_relative: sector_33_name=卸売業 / fund: market_cap_jpy=7342772736.0, per=None, pbr=1.4650718, roe_pct=-9.423999499999999, operating_margin_pct=4.027
- `3070.T` 2026-01-27 → 2026-01-28 0.00%: feature: return_5d_pct=42.85714285714286, return_20d_pct=66.66666666666667, volume_ratio_20d=7.809473850918813, rsi_14=80.59701492537313, range_position_252d_0_1=0.20703125 / value: value_trap_penalty=0.25 / sector_relative: sector_33_name=卸売業 / fund: market_cap_jpy=7342772736.0, per=None, pbr=1.4650718, roe_pct=-9.423999499999999, operating_margin_pct=4.027
- `3070.T` 2026-01-27 → 2026-01-28 0.00%: feature: return_5d_pct=42.85714285714286, return_20d_pct=66.66666666666667, volume_ratio_20d=7.809473850918813, rsi_14=80.59701492537313, range_position_252d_0_1=0.20703125 / value: value_trap_penalty=0.25 / sector_relative: sector_33_name=卸売業 / fund: market_cap_jpy=7342772736.0, per=None, pbr=1.4650718, roe_pct=-9.423999499999999, operating_margin_pct=4.027
- `3070.T` 2026-01-27 → 2026-01-28 0.00%: feature: return_5d_pct=42.85714285714286, return_20d_pct=66.66666666666667, volume_ratio_20d=7.809473850918813, rsi_14=80.59701492537313, range_position_252d_0_1=0.20703125 / value: value_trap_penalty=0.25 / sector_relative: sector_33_name=卸売業 / fund: market_cap_jpy=7342772736.0, per=None, pbr=1.4650718, roe_pct=-9.423999499999999, operating_margin_pct=4.027
- `3070.T` 2026-01-27 → 2026-01-28 0.00%: feature: return_5d_pct=42.85714285714286, return_20d_pct=66.66666666666667, volume_ratio_20d=7.809473850918813, rsi_14=80.59701492537313, range_position_252d_0_1=0.20703125 / value: value_trap_penalty=0.25 / sector_relative: sector_33_name=卸売業 / fund: market_cap_jpy=7342772736.0, per=None, pbr=1.4650718, roe_pct=-9.423999499999999, operating_margin_pct=4.027
- `3070.T` 2026-01-27 → 2026-01-28 0.00%: feature: return_5d_pct=42.85714285714286, return_20d_pct=66.66666666666667, volume_ratio_20d=7.809473850918813, rsi_14=80.59701492537313, range_position_252d_0_1=0.20703125 / value: value_trap_penalty=0.25 / sector_relative: sector_33_name=卸売業 / fund: market_cap_jpy=7342772736.0, per=None, pbr=1.4650718, roe_pct=-9.423999499999999, operating_margin_pct=4.027
- `202A.T` 2026-01-22 → 2026-01-27 0.00%: feature: return_5d_pct=11.202185792349727, return_20d_pct=28.391167192429023, volume_ratio_20d=1.503204144460876, rsi_14=61.17381489841986, range_position_252d_0_1=0.7621483375959079 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=56817000448.0, per=36.363636, pbr=17.579493, roe_pct=None, operating_margin_pct=19.718
- `202A.T` 2026-01-22 → 2026-01-27 0.00%: feature: return_5d_pct=11.202185792349727, return_20d_pct=28.391167192429023, volume_ratio_20d=1.503204144460876, rsi_14=61.17381489841986, range_position_252d_0_1=0.7621483375959079 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=56817000448.0, per=36.363636, pbr=17.579493, roe_pct=None, operating_margin_pct=19.718
- `202A.T` 2026-01-22 → 2026-01-27 0.00%: feature: return_5d_pct=11.202185792349727, return_20d_pct=28.391167192429023, volume_ratio_20d=1.503204144460876, rsi_14=61.17381489841986, range_position_252d_0_1=0.7621483375959079 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=56817000448.0, per=36.363636, pbr=17.579493, roe_pct=None, operating_margin_pct=19.718
- `202A.T` 2026-01-22 → 2026-01-27 0.00%: feature: return_5d_pct=11.202185792349727, return_20d_pct=28.391167192429023, volume_ratio_20d=1.503204144460876, rsi_14=61.17381489841986, range_position_252d_0_1=0.7621483375959079 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=56817000448.0, per=36.363636, pbr=17.579493, roe_pct=None, operating_margin_pct=19.718
- `202A.T` 2026-01-22 → 2026-01-27 0.00%: feature: return_5d_pct=11.202185792349727, return_20d_pct=28.391167192429023, volume_ratio_20d=1.503204144460876, rsi_14=61.17381489841986, range_position_252d_0_1=0.7621483375959079 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=56817000448.0, per=36.363636, pbr=17.579493, roe_pct=None, operating_margin_pct=19.718
- `202A.T` 2026-01-22 → 2026-01-27 0.00%: feature: return_5d_pct=11.202185792349727, return_20d_pct=28.391167192429023, volume_ratio_20d=1.503204144460876, rsi_14=61.17381489841986, range_position_252d_0_1=0.7621483375959079 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=56817000448.0, per=36.363636, pbr=17.579493, roe_pct=None, operating_margin_pct=19.718
- `202A.T` 2026-01-22 → 2026-01-27 0.00%: feature: return_5d_pct=11.202185792349727, return_20d_pct=28.391167192429023, volume_ratio_20d=1.503204144460876, rsi_14=61.17381489841986, range_position_252d_0_1=0.7621483375959079 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=56817000448.0, per=36.363636, pbr=17.579493, roe_pct=None, operating_margin_pct=19.718
- `5344.T` 2026-02-04 → 2026-02-06 0.00%: feature: return_5d_pct=5.720776538620398, return_20d_pct=16.26163979105155, volume_ratio_20d=1.992074686009806, rsi_14=62.52354048964218, range_position_252d_0_1=0.9744212400841833 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=ガラス・土石製品 / fund: market_cap_jpy=879833841664.0, per=48.467133, pbr=5.9746156, roe_pct=13.204001000000002, operating_margin_pct=35.202998


## NAGARE / `weekly_sage`

Medium-Term Trend / Flow

### Key Metrics

- Trades: **83**, Win rate: **0.00%**, Total PnL: **¥27,182,965**
- Avg return: **0.00%**, Avg win: **0.00%**, Avg loss: **0.00%**
- Payoff ratio: **0.0000**, Profit factor: **0.0000**
- Avg MFE: **0.00%**, Avg MAE: **0.00%**

### Exit Reasons

```json
{
  "UNKNOWN": 83
}
```

### Failure Patterns

```json
{
  "NORMAL_WIN": 83
}
```

### Success Patterns

```json
{}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4506.T | 住友ファーマ | 2026-01-08 | 2026-01-20 | 0.00% | ¥-51,218 | 12 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-29 | 2026-02-03 | 0.00% | ¥-39,691 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-29 | 2026-02-03 | 0.00% | ¥-39,691 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-29 | 2026-02-03 | 0.00% | ¥-39,691 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-29 | 2026-02-03 | 0.00% | ¥-39,691 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-29 | 2026-02-03 | 0.00% | ¥-39,691 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-29 | 2026-02-03 | 0.00% | ¥-39,691 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-29 | 2026-02-03 | 0.00% | ¥-38,897 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-30 | 0.00% | ¥675,597 | 24 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-30 | 0.00% | ¥675,597 | 24 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-30 | 0.00% | ¥675,597 | 24 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-30 | 0.00% | ¥675,597 | 24 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-30 | 0.00% | ¥675,597 | 24 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-30 | 0.00% | ¥675,597 | 24 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 0.00% | ¥613,064 | 37 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 0.00% | ¥613,064 | 37 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 0.00% | ¥613,064 | 37 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 0.00% | ¥613,064 | 37 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 0.00% | ¥613,064 | 37 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 0.00% | ¥613,064 | 37 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 0.00% | ¥610,393 | 37 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 0.00% | ¥610,393 | 37 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 0.00% | ¥610,393 | 37 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4506.T | 住友ファーマ | 2026-01-08 | 2026-01-20 | 0.00% | ¥-51,218 | 12 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4506.T | 住友ファーマ | 2026-01-08 | 2026-01-20 | 0.00% | ¥-51,218 | 12 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-01-27 | 0.00% | ¥-92 | 21 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-06 | 2026-01-28 | 0.00% | ¥446,891 | 22 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Compact Entry Context For Worst Trades

- `4506.T` 2026-01-08 → 2026-01-20 0.00%: feature: return_5d_pct=23.703703703703695, return_20d_pct=16.90343833642165, volume_ratio_20d=3.088129543454777, rsi_14=87.31294729993493, range_position_252d_0_1=0.9527494908350306 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `5713.T` 2026-01-29 → 2026-02-03 0.00%: feature: return_5d_pct=20.47677261613692, return_20d_pct=53.48076623578881, volume_ratio_20d=2.225535274466997, rsi_14=91.70616113744076, range_position_252d_0_1=0.9928329683456102 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=非鉄金属 / fund: market_cap_jpy=2349183270912.0, per=13.360517, pbr=1.1322266, roe_pct=8.695, operating_margin_pct=13.155
- `5713.T` 2026-01-29 → 2026-02-03 0.00%: feature: return_5d_pct=20.47677261613692, return_20d_pct=53.48076623578881, volume_ratio_20d=2.225535274466997, rsi_14=91.70616113744076, range_position_252d_0_1=0.9928329683456102 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=非鉄金属 / fund: market_cap_jpy=2349183270912.0, per=13.360517, pbr=1.1322266, roe_pct=8.695, operating_margin_pct=13.155
- `5713.T` 2026-01-29 → 2026-02-03 0.00%: feature: return_5d_pct=20.47677261613692, return_20d_pct=53.48076623578881, volume_ratio_20d=2.225535274466997, rsi_14=91.70616113744076, range_position_252d_0_1=0.9928329683456102 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=非鉄金属 / fund: market_cap_jpy=2349183270912.0, per=13.360517, pbr=1.1322266, roe_pct=8.695, operating_margin_pct=13.155
- `5713.T` 2026-01-29 → 2026-02-03 0.00%: feature: return_5d_pct=20.47677261613692, return_20d_pct=53.48076623578881, volume_ratio_20d=2.225535274466997, rsi_14=91.70616113744076, range_position_252d_0_1=0.9928329683456102 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=非鉄金属 / fund: market_cap_jpy=2349183270912.0, per=13.360517, pbr=1.1322266, roe_pct=8.695, operating_margin_pct=13.155
- `5713.T` 2026-01-29 → 2026-02-03 0.00%: feature: return_5d_pct=20.47677261613692, return_20d_pct=53.48076623578881, volume_ratio_20d=2.225535274466997, rsi_14=91.70616113744076, range_position_252d_0_1=0.9928329683456102 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=非鉄金属 / fund: market_cap_jpy=2349183270912.0, per=13.360517, pbr=1.1322266, roe_pct=8.695, operating_margin_pct=13.155
- `5713.T` 2026-01-29 → 2026-02-03 0.00%: feature: return_5d_pct=20.47677261613692, return_20d_pct=53.48076623578881, volume_ratio_20d=2.225535274466997, rsi_14=91.70616113744076, range_position_252d_0_1=0.9928329683456102 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=非鉄金属 / fund: market_cap_jpy=2349183270912.0, per=13.360517, pbr=1.1322266, roe_pct=8.695, operating_margin_pct=13.155
- `5713.T` 2026-01-29 → 2026-02-03 0.00%: feature: return_5d_pct=20.47677261613692, return_20d_pct=53.48076623578881, volume_ratio_20d=2.225535274466997, rsi_14=91.70616113744076, range_position_252d_0_1=0.9928329683456102 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=非鉄金属 / fund: market_cap_jpy=2349183270912.0, per=13.360517, pbr=1.1322266, roe_pct=8.695, operating_margin_pct=13.155
- `1801.T` 2026-01-06 → 2026-01-27 0.00%: feature: return_5d_pct=5.065414290506531, return_20d_pct=16.64804469273744, volume_ratio_20d=0.8446872713972202, rsi_14=70.11308562197092, range_position_252d_0_1=0.9969687784177024 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=建設業 / fund: market_cap_jpy=2108523020288.0, per=12.609426, pbr=2.224009, roe_pct=None, operating_margin_pct=9.766
- `1801.T` 2026-01-06 → 2026-01-27 0.00%: feature: return_5d_pct=5.065414290506531, return_20d_pct=16.64804469273744, volume_ratio_20d=0.8446872713972202, rsi_14=70.11308562197092, range_position_252d_0_1=0.9969687784177024 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=建設業 / fund: market_cap_jpy=2108523020288.0, per=12.609426, pbr=2.224009, roe_pct=None, operating_margin_pct=9.766
- `1801.T` 2026-01-06 → 2026-01-27 0.00%: feature: return_5d_pct=5.065414290506531, return_20d_pct=16.64804469273744, volume_ratio_20d=0.8446872713972202, rsi_14=70.11308562197092, range_position_252d_0_1=0.9969687784177024 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=建設業 / fund: market_cap_jpy=2108523020288.0, per=12.609426, pbr=2.224009, roe_pct=None, operating_margin_pct=9.766
- `1801.T` 2026-01-06 → 2026-01-27 0.00%: feature: return_5d_pct=5.065414290506531, return_20d_pct=16.64804469273744, volume_ratio_20d=0.8446872713972202, rsi_14=70.11308562197092, range_position_252d_0_1=0.9969687784177024 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=建設業 / fund: market_cap_jpy=2108523020288.0, per=12.609426, pbr=2.224009, roe_pct=None, operating_margin_pct=9.766
- `1801.T` 2026-01-06 → 2026-01-27 0.00%: feature: return_5d_pct=5.065414290506531, return_20d_pct=16.64804469273744, volume_ratio_20d=0.8446872713972202, rsi_14=70.11308562197092, range_position_252d_0_1=0.9969687784177024 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=建設業 / fund: market_cap_jpy=2108523020288.0, per=12.609426, pbr=2.224009, roe_pct=None, operating_margin_pct=9.766
- `1801.T` 2026-01-06 → 2026-01-27 0.00%: feature: return_5d_pct=5.065414290506531, return_20d_pct=16.64804469273744, volume_ratio_20d=0.8446872713972202, rsi_14=70.11308562197092, range_position_252d_0_1=0.9969687784177024 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=建設業 / fund: market_cap_jpy=2108523020288.0, per=12.609426, pbr=2.224009, roe_pct=None, operating_margin_pct=9.766
- `1801.T` 2026-01-06 → 2026-01-27 0.00%: feature: return_5d_pct=5.065414290506531, return_20d_pct=16.64804469273744, volume_ratio_20d=0.8446872713972202, rsi_14=70.11308562197092, range_position_252d_0_1=0.9969687784177024 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=建設業 / fund: market_cap_jpy=2108523020288.0, per=12.609426, pbr=2.224009, roe_pct=None, operating_margin_pct=9.766


## MAMORU / `risk_sentinel`

Risk Sentinel / Defensive Quality

### Key Metrics

- Trades: **459**, Win rate: **0.00%**, Total PnL: **¥18,361,997**
- Avg return: **0.00%**, Avg win: **0.00%**, Avg loss: **0.00%**
- Payoff ratio: **0.0000**, Profit factor: **0.0000**
- Avg MFE: **0.00%**, Avg MAE: **0.00%**

### Exit Reasons

```json
{
  "UNKNOWN": 459
}
```

### Failure Patterns

```json
{
  "NORMAL_WIN": 459
}
```

### Success Patterns

```json
{}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 8354.T | ふくおかフィナンシャルグループ | 2026-01-23 | 2026-02-06 | 0.00% | ¥162,874 | 14 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8354.T | ふくおかフィナンシャルグループ | 2026-01-23 | 2026-02-06 | 0.00% | ¥162,874 | 14 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8354.T | ふくおかフィナンシャルグループ | 2026-01-23 | 2026-02-06 | 0.00% | ¥162,874 | 14 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8354.T | ふくおかフィナンシャルグループ | 2026-01-23 | 2026-02-06 | 0.00% | ¥162,874 | 14 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8354.T | ふくおかフィナンシャルグループ | 2026-01-23 | 2026-02-06 | 0.00% | ¥162,874 | 14 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8354.T | ふくおかフィナンシャルグループ | 2026-01-23 | 2026-02-06 | 0.00% | ¥162,874 | 14 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8591.T | オリックス | 2026-01-28 | 2026-02-12 | 0.00% | ¥157,503 | 15 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8591.T | オリックス | 2026-01-28 | 2026-02-12 | 0.00% | ¥157,503 | 15 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8591.T | オリックス | 2026-01-28 | 2026-02-12 | 0.00% | ¥157,503 | 15 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8591.T | オリックス | 2026-01-28 | 2026-02-12 | 0.00% | ¥157,503 | 15 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8591.T | オリックス | 2026-01-28 | 2026-02-12 | 0.00% | ¥157,503 | 15 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8591.T | オリックス | 2026-01-28 | 2026-02-12 | 0.00% | ¥157,503 | 15 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3407.T | 旭化成 | 2026-02-04 | 2026-02-09 | 0.00% | ¥137,651 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3407.T | 旭化成 | 2026-02-04 | 2026-02-09 | 0.00% | ¥137,651 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3407.T | 旭化成 | 2026-02-04 | 2026-02-09 | 0.00% | ¥137,651 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | 0.00% | ¥-84,851 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-08 | 2026-01-09 | 0.00% | ¥-104,417 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Compact Entry Context For Worst Trades

- `3391.T` 2026-01-08 → 2026-01-09 0.00%: feature: return_5d_pct=-7.473867595818817, return_20d_pct=-5.565433854907543, volume_ratio_20d=4.063589241663088, rsi_14=33.95669291338582, range_position_252d_0_1=0.7532894736842105 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-08 → 2026-01-09 0.00%: feature: return_5d_pct=-7.473867595818817, return_20d_pct=-5.565433854907543, volume_ratio_20d=4.063589241663088, rsi_14=33.95669291338582, range_position_252d_0_1=0.7532894736842105 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-08 → 2026-01-09 0.00%: feature: return_5d_pct=-7.473867595818817, return_20d_pct=-5.565433854907543, volume_ratio_20d=4.063589241663088, rsi_14=33.95669291338582, range_position_252d_0_1=0.7532894736842105 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-08 → 2026-01-09 0.00%: feature: return_5d_pct=-7.473867595818817, return_20d_pct=-5.565433854907543, volume_ratio_20d=4.063589241663088, rsi_14=33.95669291338582, range_position_252d_0_1=0.7532894736842105 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-08 → 2026-01-09 0.00%: feature: return_5d_pct=-7.473867595818817, return_20d_pct=-5.565433854907543, volume_ratio_20d=4.063589241663088, rsi_14=33.95669291338582, range_position_252d_0_1=0.7532894736842105 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-08 → 2026-01-09 0.00%: feature: return_5d_pct=-7.473867595818817, return_20d_pct=-5.565433854907543, volume_ratio_20d=4.063589241663088, rsi_14=33.95669291338582, range_position_252d_0_1=0.7532894736842105 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-08 → 2026-01-09 0.00%: feature: return_5d_pct=-7.473867595818817, return_20d_pct=-5.565433854907543, volume_ratio_20d=4.063589241663088, rsi_14=33.95669291338582, range_position_252d_0_1=0.7532894736842105 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-06 → 2026-01-09 0.00%: feature: return_5d_pct=2.996515679442502, return_20d_pct=5.590283979282007, volume_ratio_20d=1.1142528572106036, rsi_14=74.51403887688986, range_position_252d_0_1=0.9736649597659107 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-06 → 2026-01-09 0.00%: feature: return_5d_pct=2.996515679442502, return_20d_pct=5.590283979282007, volume_ratio_20d=1.1142528572106036, rsi_14=74.51403887688986, range_position_252d_0_1=0.9736649597659107 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-06 → 2026-01-09 0.00%: feature: return_5d_pct=2.996515679442502, return_20d_pct=5.590283979282007, volume_ratio_20d=1.1142528572106036, rsi_14=74.51403887688986, range_position_252d_0_1=0.9736649597659107 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-06 → 2026-01-09 0.00%: feature: return_5d_pct=2.996515679442502, return_20d_pct=5.590283979282007, volume_ratio_20d=1.1142528572106036, rsi_14=74.51403887688986, range_position_252d_0_1=0.9736649597659107 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-06 → 2026-01-09 0.00%: feature: return_5d_pct=2.996515679442502, return_20d_pct=5.590283979282007, volume_ratio_20d=1.1142528572106036, rsi_14=74.51403887688986, range_position_252d_0_1=0.9736649597659107 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-06 → 2026-01-09 0.00%: feature: return_5d_pct=2.996515679442502, return_20d_pct=5.590283979282007, volume_ratio_20d=1.1142528572106036, rsi_14=74.51403887688986, range_position_252d_0_1=0.9736649597659107 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-06 → 2026-01-09 0.00%: feature: return_5d_pct=2.996515679442502, return_20d_pct=5.590283979282007, volume_ratio_20d=1.1142528572106036, rsi_14=74.51403887688986, range_position_252d_0_1=0.9736649597659107 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636
- `3391.T` 2026-01-06 → 2026-01-09 0.00%: feature: return_5d_pct=2.996515679442502, return_20d_pct=5.590283979282007, volume_ratio_20d=1.1142528572106036, rsi_14=74.51403887688986, range_position_252d_0_1=0.9736649597659107 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=880231383040.0, per=13.493055, pbr=1.0049295, roe_pct=7.546, operating_margin_pct=3.636


## SAGURI / `discovery_scout`

Discovery / Small-Cap Scout

### Key Metrics

- Trades: **82**, Win rate: **0.00%**, Total PnL: **¥-883,942**
- Avg return: **0.00%**, Avg win: **0.00%**, Avg loss: **0.00%**
- Payoff ratio: **0.0000**, Profit factor: **0.0000**
- Avg MFE: **0.00%**, Avg MAE: **0.00%**

### Exit Reasons

```json
{
  "UNKNOWN": 82
}
```

### Failure Patterns

```json
{
  "NORMAL_WIN": 82
}
```

### Success Patterns

```json
{}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 202A.T | MAMEZO CO.,LTD. | 2026-01-22 | 2026-01-27 | 0.00% | ¥-164,621 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-162,876 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-161,038 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-161,038 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-161,038 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | 0.00% | ¥-160,584 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-156,214 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-156,214 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | 0.00% | ¥-134,118 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | 0.00% | ¥-134,118 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | 0.00% | ¥-125,892 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | 0.00% | ¥-125,892 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-16 | 2026-01-26 | 0.00% | ¥-118,267 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-16 | 2026-01-26 | 0.00% | ¥-118,267 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-16 | 2026-01-26 | 0.00% | ¥-117,473 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5243.T | note inc. | 2026-01-13 | 2026-01-16 | 0.00% | ¥535,976 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-13 | 2026-01-16 | 0.00% | ¥535,976 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-13 | 2026-01-16 | 0.00% | ¥535,976 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-14 | 2026-01-16 | 0.00% | ¥336,885 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-14 | 2026-01-16 | 0.00% | ¥312,944 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5243.T | note inc. | 2026-01-14 | 2026-01-16 | 0.00% | ¥312,944 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9270.T | Valuence Holdings Inc. | 2026-01-13 | 2026-01-19 | 0.00% | ¥271,303 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5834.T | SBI Leasing | 2026-01-30 | 2026-02-10 | 0.00% | ¥147,700 | 11 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 2986.T | LA Holdings Co.,Ltd. | 2026-02-02 | 2026-02-13 | 0.00% | ¥81,690 | 11 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3479.T | TKP Corporation | 2026-01-26 | 2026-02-06 | 0.00% | ¥67,727 | 11 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥59,484 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥59,326 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥59,326 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥59,326 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥59,326 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥36,618 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥34,754 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥36,618 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥39,748 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥34,754 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥36,618 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 325A.T | TENTIAL Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-65,955 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-11,027 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥59,326 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥36,618 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥34,754 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥36,618 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥39,748 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥34,754 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 0.00% | ¥36,618 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 325A.T | TENTIAL Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-65,955 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-11,027 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥-10,996 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-14 | 2026-01-15 | 0.00% | ¥59,326 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Compact Entry Context For Worst Trades

- `202A.T` 2026-01-22 → 2026-01-27 0.00%: feature: return_5d_pct=11.202185792349727, return_20d_pct=28.391167192429023, volume_ratio_20d=1.503204144460876, rsi_14=61.17381489841986, range_position_252d_0_1=0.7621483375959079 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=56817000448.0, per=36.363636, pbr=17.579493, roe_pct=None, operating_margin_pct=19.718
- `4443.T` 2026-01-16 → 2026-01-20 0.00%: feature: return_5d_pct=7.813378302417084, return_20d_pct=13.089622641509436, volume_ratio_20d=2.1983851732031967, rsi_14=65.14657980456026, range_position_252d_0_1=0.3203125 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=220477161472.0, per=108.40598, pbr=11.616269, roe_pct=15.695, operating_margin_pct=21.867001
- `4443.T` 2026-01-16 → 2026-01-20 0.00%: feature: return_5d_pct=7.813378302417084, return_20d_pct=13.089622641509436, volume_ratio_20d=2.1983851732031967, rsi_14=65.14657980456026, range_position_252d_0_1=0.3203125 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=220477161472.0, per=108.40598, pbr=11.616269, roe_pct=15.695, operating_margin_pct=21.867001
- `4443.T` 2026-01-16 → 2026-01-20 0.00%: feature: return_5d_pct=7.813378302417084, return_20d_pct=13.089622641509436, volume_ratio_20d=2.1983851732031967, rsi_14=65.14657980456026, range_position_252d_0_1=0.3203125 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=220477161472.0, per=108.40598, pbr=11.616269, roe_pct=15.695, operating_margin_pct=21.867001
- `4443.T` 2026-01-16 → 2026-01-20 0.00%: feature: return_5d_pct=7.813378302417084, return_20d_pct=13.089622641509436, volume_ratio_20d=2.1983851732031967, rsi_14=65.14657980456026, range_position_252d_0_1=0.3203125 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=220477161472.0, per=108.40598, pbr=11.616269, roe_pct=15.695, operating_margin_pct=21.867001
- `5243.T` 2026-01-26 → 2026-01-27 0.00%: feature: return_5d_pct=0.512070226773953, return_20d_pct=79.96070726915521, volume_ratio_20d=0.919902156053698, rsi_14=70.77747989276139, range_position_252d_0_1=0.8210689388071263 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=37418340352.0, per=71.980675, pbr=6.832572, roe_pct=19.439, operating_margin_pct=19.326
- `4443.T` 2026-01-16 → 2026-01-20 0.00%: feature: return_5d_pct=7.813378302417084, return_20d_pct=13.089622641509436, volume_ratio_20d=2.1983851732031967, rsi_14=65.14657980456026, range_position_252d_0_1=0.3203125 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=220477161472.0, per=108.40598, pbr=11.616269, roe_pct=15.695, operating_margin_pct=21.867001
- `4443.T` 2026-01-16 → 2026-01-20 0.00%: feature: return_5d_pct=7.813378302417084, return_20d_pct=13.089622641509436, volume_ratio_20d=2.1983851732031967, rsi_14=65.14657980456026, range_position_252d_0_1=0.3203125 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=220477161472.0, per=108.40598, pbr=11.616269, roe_pct=15.695, operating_margin_pct=21.867001
- `5243.T` 2026-01-26 → 2026-01-27 0.00%: feature: return_5d_pct=0.512070226773953, return_20d_pct=79.96070726915521, volume_ratio_20d=0.919902156053698, rsi_14=70.77747989276139, range_position_252d_0_1=0.8210689388071263 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=37418340352.0, per=71.980675, pbr=6.832572, roe_pct=19.439, operating_margin_pct=19.326
- `5243.T` 2026-01-26 → 2026-01-27 0.00%: feature: return_5d_pct=0.512070226773953, return_20d_pct=79.96070726915521, volume_ratio_20d=0.919902156053698, rsi_14=70.77747989276139, range_position_252d_0_1=0.8210689388071263 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=37418340352.0, per=71.980675, pbr=6.832572, roe_pct=19.439, operating_margin_pct=19.326
- `5243.T` 2026-01-26 → 2026-01-27 0.00%: feature: return_5d_pct=0.512070226773953, return_20d_pct=79.96070726915521, volume_ratio_20d=0.919902156053698, rsi_14=70.77747989276139, range_position_252d_0_1=0.8210689388071263 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=37418340352.0, per=71.980675, pbr=6.832572, roe_pct=19.439, operating_margin_pct=19.326
- `5243.T` 2026-01-26 → 2026-01-27 0.00%: feature: return_5d_pct=0.512070226773953, return_20d_pct=79.96070726915521, volume_ratio_20d=0.919902156053698, rsi_14=70.77747989276139, range_position_252d_0_1=0.8210689388071263 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=37418340352.0, per=71.980675, pbr=6.832572, roe_pct=19.439, operating_margin_pct=19.326
- `3556.T` 2026-01-16 → 2026-01-26 0.00%: feature: return_5d_pct=16.666666666666675, return_20d_pct=30.196936542669594, volume_ratio_20d=1.9530528814453383, rsi_14=74.09638554216868, range_position_252d_0_1=0.8844765342960289 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=12089499648.0, per=16.703787, pbr=8.011809, roe_pct=69.43, operating_margin_pct=11.677
- `3556.T` 2026-01-16 → 2026-01-26 0.00%: feature: return_5d_pct=16.666666666666675, return_20d_pct=30.196936542669594, volume_ratio_20d=1.9530528814453383, rsi_14=74.09638554216868, range_position_252d_0_1=0.8844765342960289 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=12089499648.0, per=16.703787, pbr=8.011809, roe_pct=69.43, operating_margin_pct=11.677
- `3556.T` 2026-01-16 → 2026-01-26 0.00%: feature: return_5d_pct=16.666666666666675, return_20d_pct=30.196936542669594, volume_ratio_20d=1.9530528814453383, rsi_14=74.09638554216868, range_position_252d_0_1=0.8844765342960289 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=小売業 / fund: market_cap_jpy=12089499648.0, per=16.703787, pbr=8.011809, roe_pct=69.43, operating_margin_pct=11.677


## MATSU / `contrarian_monk`

Pullback / Patient Reversal

### Key Metrics

- Trades: **149**, Win rate: **0.00%**, Total PnL: **¥19,974,614**
- Avg return: **0.00%**, Avg win: **0.00%**, Avg loss: **0.00%**
- Payoff ratio: **0.0000**, Profit factor: **0.0000**
- Avg MFE: **0.00%**, Avg MAE: **0.00%**

### Exit Reasons

```json
{
  "UNKNOWN": 149
}
```

### Failure Patterns

```json
{
  "NORMAL_WIN": 149
}
```

### Success Patterns

```json
{}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5706.T | 三井金属 | 2026-02-02 | 2026-02-12 | 0.00% | ¥275,319 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5706.T | 三井金属 | 2026-02-02 | 2026-02-12 | 0.00% | ¥275,319 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5706.T | 三井金属 | 2026-02-02 | 2026-02-12 | 0.00% | ¥275,319 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5706.T | 三井金属 | 2026-02-02 | 2026-02-12 | 0.00% | ¥275,319 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5706.T | 三井金属 | 2026-02-02 | 2026-02-12 | 0.00% | ¥275,319 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5706.T | 三井金属 | 2026-02-02 | 2026-02-12 | 0.00% | ¥275,319 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5706.T | 三井金属 | 2026-02-02 | 2026-02-12 | 0.00% | ¥275,319 | 10 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1893.T | 五洋建設 | 2026-01-23 | 2026-02-10 | 0.00% | ¥252,397 | 18 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1893.T | 五洋建設 | 2026-01-23 | 2026-02-10 | 0.00% | ¥252,397 | 18 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1893.T | 五洋建設 | 2026-01-23 | 2026-02-10 | 0.00% | ¥252,397 | 18 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1893.T | 五洋建設 | 2026-01-23 | 2026-02-10 | 0.00% | ¥252,397 | 18 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1893.T | 五洋建設 | 2026-01-23 | 2026-02-10 | 0.00% | ¥252,397 | 18 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1893.T | 五洋建設 | 2026-01-23 | 2026-02-10 | 0.00% | ¥252,397 | 18 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1893.T | 五洋建設 | 2026-01-23 | 2026-02-10 | 0.00% | ¥252,397 | 18 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5802.T | 住友電気工業 | 2026-01-27 | 2026-02-04 | 0.00% | ¥247,873 | 8 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-96,814 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | 0.00% | ¥-89,476 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Compact Entry Context For Worst Trades

- `4506.T` 2026-01-20 → 2026-01-21 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-21 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-21 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-21 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-21 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-21 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-21 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-23 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-23 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-23 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-23 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-23 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-23 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-23 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859
- `4506.T` 2026-01-20 → 2026-01-23 0.00%: feature: return_5d_pct=-20.173420633516194, return_20d_pct=-0.5511463844797171, volume_ratio_20d=1.3594353168716935, rsi_14=46.74022066198595, range_position_252d_0_1=0.715071283095723 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=667731361792.0, per=5.5351033, pbr=2.0219872, roe_pct=46.266996999999996, operating_margin_pct=-52.859


## KAESHI / `reversal_snapback`

Oversold Reversal / Snapback

### Key Metrics

- Trades: **177**, Win rate: **0.00%**, Total PnL: **¥1,333,539**
- Avg return: **0.00%**, Avg win: **0.00%**, Avg loss: **0.00%**
- Payoff ratio: **0.0000**, Profit factor: **0.0000**
- Avg MFE: **0.00%**, Avg MAE: **0.00%**

### Exit Reasons

```json
{
  "UNKNOWN": 177
}
```

### Failure Patterns

```json
{
  "NORMAL_WIN": 177
}
```

### Success Patterns

```json
{}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-105,576 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-105,576 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-105,576 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-105,576 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-100,527 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | 0.00% | ¥-99,609 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4151.T | 協和キリン | 2026-02-04 | 2026-02-12 | 0.00% | ¥120,211 | 8 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4151.T | 協和キリン | 2026-02-04 | 2026-02-12 | 0.00% | ¥119,111 | 8 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4151.T | 協和キリン | 2026-02-04 | 2026-02-12 | 0.00% | ¥119,111 | 8 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4151.T | 協和キリン | 2026-02-04 | 2026-02-12 | 0.00% | ¥119,111 | 8 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4151.T | 協和キリン | 2026-02-04 | 2026-02-12 | 0.00% | ¥119,111 | 8 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9501.T | 東京電力ホールディングス | 2026-01-29 | 2026-02-05 | 0.00% | ¥111,087 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9501.T | 東京電力ホールディングス | 2026-01-29 | 2026-02-05 | 0.00% | ¥111,087 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9501.T | 東京電力ホールディングス | 2026-01-29 | 2026-02-05 | 0.00% | ¥111,087 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9501.T | 東京電力ホールディングス | 2026-01-29 | 2026-02-05 | 0.00% | ¥111,087 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5929.T | 三和ホールディングス | 2026-02-02 | 2026-02-09 | 0.00% | ¥107,347 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5929.T | 三和ホールディングス | 2026-02-02 | 2026-02-09 | 0.00% | ¥106,244 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5929.T | 三和ホールディングス | 2026-02-02 | 2026-02-09 | 0.00% | ¥106,244 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5929.T | 三和ホールディングス | 2026-02-02 | 2026-02-09 | 0.00% | ¥106,244 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5929.T | 三和ホールディングス | 2026-02-02 | 2026-02-09 | 0.00% | ¥106,244 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5929.T | 三和ホールディングス | 2026-02-02 | 2026-02-09 | 0.00% | ¥106,244 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 9168.T | Rise Consulting Group,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-50,073 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9168.T | Rise Consulting Group,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-50,073 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9168.T | Rise Consulting Group,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-50,073 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9168.T | Rise Consulting Group,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-50,073 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3697.T | ＳＨＩＦＴ | 2026-01-19 | 2026-01-23 | 0.00% | ¥-11,651 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3697.T | ＳＨＩＦＴ | 2026-01-19 | 2026-01-23 | 0.00% | ¥-11,651 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3697.T | ＳＨＩＦＴ | 2026-01-19 | 2026-01-23 | 0.00% | ¥-11,651 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3697.T | ＳＨＩＦＴ | 2026-01-19 | 2026-01-23 | 0.00% | ¥-11,651 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 7373.T | Aidma Holdings,Inc. | 2026-01-19 | 2026-01-23 | 0.00% | ¥-31,171 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 7373.T | Aidma Holdings,Inc. | 2026-01-19 | 2026-01-23 | 0.00% | ¥-31,171 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 9168.T | Rise Consulting Group,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-50,073 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9168.T | Rise Consulting Group,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-50,073 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9168.T | Rise Consulting Group,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-50,073 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 9168.T | Rise Consulting Group,Inc. | 2026-01-16 | 2026-01-20 | 0.00% | ¥-50,073 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3391.T | ツルハホールディングス | 2026-01-15 | 2026-01-22 | 0.00% | ¥11,914 | 7 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3697.T | ＳＨＩＦＴ | 2026-01-19 | 2026-01-23 | 0.00% | ¥-11,651 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3697.T | ＳＨＩＦＴ | 2026-01-19 | 2026-01-23 | 0.00% | ¥-11,651 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3697.T | ＳＨＩＦＴ | 2026-01-19 | 2026-01-23 | 0.00% | ¥-11,651 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3697.T | ＳＨＩＦＴ | 2026-01-19 | 2026-01-23 | 0.00% | ¥-11,651 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 7373.T | Aidma Holdings,Inc. | 2026-01-19 | 2026-01-23 | 0.00% | ¥-31,171 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 7373.T | Aidma Holdings,Inc. | 2026-01-19 | 2026-01-23 | 0.00% | ¥-31,171 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Compact Entry Context For Worst Trades

- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4307.T` 2026-02-02 → 2026-02-05 0.00%: feature: return_5d_pct=-20.47986289631534, return_20d_pct=-22.936389304102313, volume_ratio_20d=2.390068346155116, rsi_14=8.435013262599469, range_position_252d_0_1=0.017130620985010708 / value: value_trap_penalty=0.2 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=2916251598848.0, per=190.57808, pbr=6.7209425, roe_pct=3.604, operating_margin_pct=-28.653000000000002


## HIZUMI / `value_mispricing`

Value Mispricing / Sector Relative Value

### Key Metrics

- Trades: **164**, Win rate: **0.00%**, Total PnL: **¥4,958,828**
- Avg return: **0.00%**, Avg win: **0.00%**, Avg loss: **0.00%**
- Payoff ratio: **0.0000**, Profit factor: **0.0000**
- Avg MFE: **0.00%**, Avg MAE: **0.00%**

### Exit Reasons

```json
{
  "UNKNOWN": 164
}
```

### Failure Patterns

```json
{
  "NORMAL_WIN": 164
}
```

### Success Patterns

```json
{}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5713.T | 住友金属鉱山 | 2026-01-30 | 2026-02-02 | 0.00% | ¥-181,421 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3659.T | ネクソン | 2026-01-30 | 2026-02-03 | 0.00% | ¥-168,215 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-02-05 | 2026-02-06 | 0.00% | ¥-142,395 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3659.T | ネクソン | 2026-01-30 | 2026-02-02 | 0.00% | ¥-133,673 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5842.T | Integral Corporation | 2026-01-16 | 2026-01-20 | 0.00% | ¥-132,593 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5842.T | Integral Corporation | 2026-01-16 | 2026-01-20 | 0.00% | ¥-131,180 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8604.T | 野村ホールディングス | 2026-01-29 | 2026-02-03 | 0.00% | ¥-80,520 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8604.T | 野村ホールディングス | 2026-01-29 | 2026-02-03 | 0.00% | ¥-79,564 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4503.T | アステラス製薬 | 2026-01-27 | 2026-01-28 | 0.00% | ¥-78,895 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3659.T | ネクソン | 2026-01-28 | 2026-01-29 | 0.00% | ¥-76,284 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5105.T | ＴＯＹＯ ＴＩＲＥ | 2026-01-23 | 2026-01-26 | 0.00% | ¥-51,103 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-02-05 | 2026-02-06 | 0.00% | ¥-47,355 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5105.T | ＴＯＹＯ ＴＩＲＥ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-46,243 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-20 | 2026-01-21 | 0.00% | ¥-45,339 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1928.T | 積水ハウス | 2026-01-23 | 2026-01-26 | 0.00% | ¥-43,139 | 3 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4503.T | アステラス製薬 | 2026-01-28 | 2026-02-06 | 0.00% | ¥266,357 | 9 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4503.T | アステラス製薬 | 2026-01-28 | 2026-02-06 | 0.00% | ¥263,639 | 9 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5838.T | 楽天銀行 | 2026-02-06 | 2026-02-12 | 0.00% | ¥260,866 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5838.T | 楽天銀行 | 2026-02-06 | 2026-02-12 | 0.00% | ¥258,844 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5838.T | 楽天銀行 | 2026-02-06 | 2026-02-12 | 0.00% | ¥258,844 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 6269.T | 三井海洋開発 | 2026-01-09 | 2026-01-15 | 0.00% | ¥164,971 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-15 | 0.00% | ¥156,783 | 9 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-15 | 0.00% | ¥156,783 | 9 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1925.T | 大和ハウス工業 | 2026-01-07 | 2026-02-09 | 0.00% | ¥144,671 | 33 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-08 | 2026-01-14 | 0.00% | ¥126,861 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-08 | 2026-01-14 | 0.00% | ¥126,651 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-08 | 2026-01-14 | 0.00% | ¥126,440 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-08 | 2026-01-14 | 0.00% | ¥126,440 | 6 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1925.T | 大和ハウス工業 | 2026-01-06 | 2026-02-09 | 0.00% | ¥125,985 | 34 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1925.T | 大和ハウス工業 | 2026-01-06 | 2026-02-09 | 0.00% | ¥125,985 | 34 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1605.T | ＩＮＰＥＸ | 2026-01-06 | 2026-01-07 | 0.00% | ¥-657 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-06 | 2026-01-07 | 0.00% | ¥-766 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3288.T | オープンハウスグループ | 2026-01-06 | 2026-01-07 | 0.00% | ¥12,764 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4503.T | アステラス製薬 | 2026-01-06 | 2026-01-07 | 0.00% | ¥9,402 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.00% | ¥2,056 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.00% | ¥2,056 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.00% | ¥2,056 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3659.T | ネクソン | 2026-01-07 | 2026-01-08 | 0.00% | ¥-3,125 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-07 | 2026-01-08 | 0.00% | ¥-8,327 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4578.T | 大塚ホールディングス | 2026-01-07 | 2026-01-09 | 0.00% | ¥45,102 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3288.T | オープンハウスグループ | 2026-01-08 | 2026-01-09 | 0.00% | ¥-1,632 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4503.T | アステラス製薬 | 2026-01-08 | 2026-01-09 | 0.00% | ¥12,835 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-08 | 2026-01-13 | 0.00% | ¥87,625 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-08 | 2026-01-13 | 0.00% | ¥75,232 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3659.T | ネクソン | 2026-01-09 | 2026-01-13 | 0.00% | ¥21,230 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1605.T | ＩＮＰＥＸ | 2026-01-06 | 2026-01-07 | 0.00% | ¥-657 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-06 | 2026-01-07 | 0.00% | ¥-766 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3288.T | オープンハウスグループ | 2026-01-06 | 2026-01-07 | 0.00% | ¥12,764 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4503.T | アステラス製薬 | 2026-01-06 | 2026-01-07 | 0.00% | ¥9,402 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.00% | ¥2,056 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.00% | ¥2,056 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.00% | ¥2,056 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3659.T | ネクソン | 2026-01-07 | 2026-01-08 | 0.00% | ¥-3,125 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-01-07 | 2026-01-08 | 0.00% | ¥-8,327 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4578.T | 大塚ホールディングス | 2026-01-07 | 2026-01-09 | 0.00% | ¥45,102 | 2 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3288.T | オープンハウスグループ | 2026-01-08 | 2026-01-09 | 0.00% | ¥-1,632 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 4503.T | アステラス製薬 | 2026-01-08 | 2026-01-09 | 0.00% | ¥12,835 | 1 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-08 | 2026-01-13 | 0.00% | ¥87,625 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-01-08 | 2026-01-13 | 0.00% | ¥75,232 | 5 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |
| 3659.T | ネクソン | 2026-01-09 | 2026-01-13 | 0.00% | ¥21,230 | 4 | 0.00% | 0.00% | UNKNOWN | NORMAL_WIN |


### Compact Entry Context For Worst Trades

- `5713.T` 2026-01-30 → 2026-02-02 0.00%: feature: return_5d_pct=10.273327049952874, return_20d_pct=40.2247191011236, volume_ratio_20d=3.6103269800317297, rsi_14=79.2725327627708, range_position_252d_0_1=0.8769694306697634 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=非鉄金属 / fund: market_cap_jpy=2349183270912.0, per=13.360517, pbr=1.1322266, roe_pct=8.695, operating_margin_pct=13.155
- `3659.T` 2026-01-30 → 2026-02-03 0.00%: feature: return_5d_pct=-16.693055869712737, return_20d_pct=-3.6872384937238545, volume_ratio_20d=3.2804629756585943, rsi_14=34.99142367066895, range_position_252d_0_1=0.7119846596356664 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=1795799515136.0, per=19.87303, pbr=1.6922827, roe_pct=11.564, operating_margin_pct=38.206002
- `5713.T` 2026-02-05 → 2026-02-06 0.00%: feature: return_5d_pct=-10.451547437848808, return_20d_pct=23.013660440479498, volume_ratio_20d=1.358015608611495, rsi_14=59.53370684981022, range_position_252d_0_1=0.8098047831272362 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=非鉄金属 / fund: market_cap_jpy=2349183270912.0, per=13.360517, pbr=1.1322266, roe_pct=8.695, operating_margin_pct=13.155
- `3659.T` 2026-01-30 → 2026-02-02 0.00%: feature: return_5d_pct=-16.693055869712737, return_20d_pct=-3.6872384937238545, volume_ratio_20d=3.2804629756585943, rsi_14=34.99142367066895, range_position_252d_0_1=0.7119846596356664 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=1795799515136.0, per=19.87303, pbr=1.6922827, roe_pct=11.564, operating_margin_pct=38.206002
- `5842.T` 2026-01-16 → 2026-01-20 0.00%: feature: return_5d_pct=6.8245125348189495, return_20d_pct=19.470404984423674, volume_ratio_20d=3.849613381726369, rsi_14=69.1449814126394, range_position_252d_0_1=0.7442281575373472 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=証券、商品先物取引業 / fund: market_cap_jpy=111527534592.0, per=18.98991, pbr=1.6286386, roe_pct=20.898001, operating_margin_pct=85.797995
- `5842.T` 2026-01-16 → 2026-01-20 0.00%: feature: return_5d_pct=6.8245125348189495, return_20d_pct=19.470404984423674, volume_ratio_20d=3.849613381726369, rsi_14=69.1449814126394, range_position_252d_0_1=0.7442281575373472 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=証券、商品先物取引業 / fund: market_cap_jpy=111527534592.0, per=18.98991, pbr=1.6286386, roe_pct=20.898001, operating_margin_pct=85.797995
- `8604.T` 2026-01-29 → 2026-02-03 0.00%: feature: return_5d_pct=0.6720905553590395, return_20d_pct=8.460365853658548, volume_ratio_20d=1.0106059554310831, rsi_14=56.19834710743802, range_position_252d_0_1=0.8999400838825644 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=証券、商品先物取引業 / fund: market_cap_jpy=3800831623168.0, per=10.934084, pbr=1.0176169, roe_pct=10.07, operating_margin_pct=18.655
- `8604.T` 2026-01-29 → 2026-02-03 0.00%: feature: return_5d_pct=0.6720905553590395, return_20d_pct=8.460365853658548, volume_ratio_20d=1.0106059554310831, rsi_14=56.19834710743802, range_position_252d_0_1=0.8999400838825644 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=証券、商品先物取引業 / fund: market_cap_jpy=3800831623168.0, per=10.934084, pbr=1.0176169, roe_pct=10.07, operating_margin_pct=18.655
- `4503.T` 2026-01-27 → 2026-01-28 0.00%: feature: return_5d_pct=-1.6983240223463647, return_20d_pct=5.0883898709985775, volume_ratio_20d=1.06978986270554, rsi_14=58.80239520958083, range_position_252d_0_1=0.8754578754578755 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=医薬品 / fund: market_cap_jpy=3882163634176.0, per=13.361697, pbr=2.12251, roe_pct=17.438000000000002, operating_margin_pct=16.509001
- `3659.T` 2026-01-28 → 2026-01-29 0.00%: feature: return_5d_pct=0.14114326040930436, return_20d_pct=12.470277410832242, volume_ratio_20d=1.0663071610716488, rsi_14=69.01172529313233, range_position_252d_0_1=0.9321188878235858 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=情報・通信業 / fund: market_cap_jpy=1795799515136.0, per=19.87303, pbr=1.6922827, roe_pct=11.564, operating_margin_pct=38.206002
- `5105.T` 2026-01-23 → 2026-01-26 0.00%: feature: return_5d_pct=-1.9625137816979055, return_20d_pct=-0.5813953488372103, volume_ratio_20d=0.9294839383827148, rsi_14=57.96269727403156, range_position_252d_0_1=0.9496201519392243 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=ゴム製品 / fund: market_cap_jpy=557464420352.0, per=8.761951, pbr=1.0463513, roe_pct=13.172, operating_margin_pct=15.739
- `1605.T` 2026-02-05 → 2026-02-06 0.00%: feature: return_5d_pct=3.6109493302271423, return_20d_pct=17.81456953642384, volume_ratio_20d=0.9985008447773336, rsi_14=78.76386687797148, range_position_252d_0_1=0.961674230963187 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=鉱業 / fund: market_cap_jpy=4154828521472.0, per=10.811382, pbr=0.84966874, roe_pct=8.282, operating_margin_pct=48.582
- `5105.T` 2026-01-20 → 2026-01-21 0.00%: feature: return_5d_pct=-0.9957003847024248, return_20d_pct=-1.0180995475113086, volume_ratio_20d=1.094241098897444, rsi_14=45.845272206303726, range_position_252d_0_1=0.9212315073970412 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=ゴム製品 / fund: market_cap_jpy=557464420352.0, per=8.761951, pbr=1.0463513, roe_pct=13.172, operating_margin_pct=15.739
- `1605.T` 2026-01-20 → 2026-01-21 0.00%: feature: return_5d_pct=0.34799114204364656, return_20d_pct=2.157809983896941, volume_ratio_20d=0.6247421072781159, rsi_14=50.95108695652174, range_position_252d_0_1=0.8863636363636364 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=鉱業 / fund: market_cap_jpy=4154828521472.0, per=10.811382, pbr=0.84966874, roe_pct=8.282, operating_margin_pct=48.582
- `1928.T` 2026-01-23 → 2026-01-26 0.00%: feature: return_5d_pct=-1.9742253907321095, return_20d_pct=4.471069549970785, volume_ratio_20d=1.3360804433169404, rsi_14=59.50617283950618, range_position_252d_0_1=0.8404522613065326 / value: value_trap_penalty=0.0 / sector_relative: sector_33_name=建設業 / fund: market_cap_jpy=2098344624128.0, per=9.04569, pbr=0.98071206, roe_pct=11.247, operating_margin_pct=10.34


## Prompt Suggestion

```text
このTrade Diagnosticsをもとに、各Agentの勝因・敗因を定量的に分析してください。特に、勝率と損益の非対称性、MFE/MAE、exit reason、entry context、fundamental/value/sector-relative value contextを見て、Agent別に改善すべき売買ルールを優先順位付きで提案してください。
```
