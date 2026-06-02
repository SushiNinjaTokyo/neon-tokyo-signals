# Neon Tokyo AI Arena Trade Diagnostics

Generated: `2026-06-02T12:32:56+00:00`
Requested Run ID: `display`
Effective Run ID: `arena_jp_rebuild_2026_v022`
Schema: `neon_tokyo_ai_arena_trade_diagnostics_v2`

> Purpose: high-integrity agent-by-agent win/loss diagnosis and rule-improvement source data.

## Dataset Summary

- Closed trades: **393**
- Raw trade rows: **393**
- Duplicates removed: **0**
- Agents with closed trades: **7**
- Official agents: **7**
- Agent summaries: **7**
- Quality status: **ok**

## Run Resolution

- Requested run_id: `display`
- Effective run_id: `arena_jp_rebuild_2026_v022`
- Display resolved: `True`
- Used run_id filter: `True`
- Fallback used: `False`
- display candidate `arena_jp_rebuild_2026_v022`: trades=393, orders=823, equity=686
- display candidate `arena_jp_rebuild_2026_v022`: trades=393, orders=823, equity=686

## Agent Summary

| Agent | Trades | Win | Avg Ret | Avg Win | Avg Loss | Payoff | PF | PnL | Avg MFE | Avg MAE | Avg Giveback | Top Patterns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KYOU / `daily_striker` | 79 | 48.10% | 1.15% | 5.00% | -2.43% | 2.0621 | 1.7407 | ¥1,103,700 | 5.37% | -3.51% | 4.22% | NORMAL_WIN:31, FAST_FAILED_ENTRY:27, NORMAL_LOSS:7, FAST_WINNER:4 |
| NAGARE / `weekly_sage` | 36 | 38.89% | 4.92% | 24.91% | -7.80% | 3.1923 | 2.4006 | ¥2,689,727 | 15.32% | -7.97% | 10.40% | NORMAL_WIN:11, DEEP_ADVERSE_MOVE:10, STOP_LOSS_HIT:8, WINNER_TURNED_LOSER:3 |
| MAMORU / `risk_sentinel` | 92 | 48.91% | 2.02% | 7.44% | -3.17% | 2.3451 | 2.2325 | ¥1,380,806 | 6.65% | -3.58% | 4.64% | NORMAL_WIN:40, STOP_LOSS_HIT:20, SLOW_BLEED_LOSER:13, NORMAL_LOSS:9 |
| SAGURI / `discovery_scout` | 41 | 39.02% | 0.94% | 10.99% | -5.49% | 2.0025 | 1.2556 | ¥406,959 | 9.20% | -5.95% | 8.26% | NORMAL_WIN:8, STOP_LOSS_HIT:8, NORMAL_LOSS:7, GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN:6 |
| MATSU / `contrarian_monk` | 74 | 47.30% | 2.50% | 10.49% | -4.68% | 2.2426 | 1.8252 | ¥1,835,126 | 8.33% | -5.78% | 5.83% | NORMAL_WIN:29, STOP_LOSS_HIT:22, NORMAL_LOSS:9, GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN:5 |
| KAESHI / `reversal_snapback` | 53 | 50.94% | 0.21% | 5.79% | -5.58% | 1.0375 | 1.0852 | ¥131,691 | 5.65% | -5.07% | 5.44% | NORMAL_WIN:19, STOP_LOSS_HIT:18, FAST_WINNER:6, NORMAL_LOSS:5 |
| HIZUMI / `value_mispricing` | 18 | 61.11% | 1.51% | 3.68% | -1.89% | 1.9496 | 2.9489 | ¥384,982 | 4.39% | -2.94% | 2.88% | NORMAL_WIN:11, FAST_FAILED_ENTRY:4, STOP_LOSS_HIT:2, NORMAL_LOSS:1 |

## KYOU / `daily_striker`

Short-Term Breakout / Momentum

### Key Metrics

- Trades: **79**, Win rate: **48.10%**, Total PnL: **¥1,103,700**
- Avg return: **1.15%**, Avg win: **5.00%**, Avg loss: **-2.43%**
- Payoff ratio: **2.0621**, Profit factor: **1.7407**
- Avg MFE: **5.37%**, Avg MAE: **-3.51%**, Avg giveback: **4.22%**

### Exit Reasons

```json
{
  "SCORE_COLLAPSE": 70,
  "HARD_STOP": 4,
  "MAX_HOLDING_DAYS": 4,
  "TAKE_PROFIT": 1
}
```

### Diagnostic Patterns

```json
{
  "NORMAL_WIN": 31,
  "FAST_FAILED_ENTRY": 27,
  "NORMAL_LOSS": 7,
  "FAST_WINNER": 4,
  "STOP_LOSS_HIT": 4,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 3,
  "WINNER_TURNED_LOSER": 2,
  "DEEP_ADVERSE_MOVE": 1
}
```

### Entry Context Risk Flags

```json
{
  "upper_range_chase": 38,
  "volume_climax_or_shock": 22,
  "low_roe_company": 17,
  "value_trap_penalty_high": 10,
  "expensive_pbr": 9,
  "operating_loss_company": 6,
  "expensive_per": 3
}
```

## NAGARE / `weekly_sage`

Medium-Term Trend / Flow

### Key Metrics

- Trades: **36**, Win rate: **38.89%**, Total PnL: **¥2,689,727**
- Avg return: **4.92%**, Avg win: **24.91%**, Avg loss: **-7.80%**
- Payoff ratio: **3.1923**, Profit factor: **2.4006**
- Avg MFE: **15.32%**, Avg MAE: **-7.97%**, Avg giveback: **10.40%**

### Exit Reasons

```json
{
  "EARLY_FAIL": 9,
  "TAKE_PROFIT": 8,
  "HARD_STOP": 8,
  "MAX_HOLDING_DAYS": 5,
  "TREND_BREAK": 5,
  "TRAILING_STOP": 1
}
```

### Diagnostic Patterns

```json
{
  "NORMAL_WIN": 11,
  "DEEP_ADVERSE_MOVE": 10,
  "STOP_LOSS_HIT": 8,
  "WINNER_TURNED_LOSER": 3,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 3,
  "SLOW_BLEED_LOSER": 1
}
```

### Entry Context Risk Flags

```json
{
  "upper_range_chase": 29,
  "low_roe_company": 8,
  "expensive_per": 3,
  "operating_loss_company": 2,
  "value_trap_penalty_high": 2,
  "expensive_pbr": 1
}
```

## MAMORU / `risk_sentinel`

Risk Sentinel / Defensive Quality

### Key Metrics

- Trades: **92**, Win rate: **48.91%**, Total PnL: **¥1,380,806**
- Avg return: **2.02%**, Avg win: **7.44%**, Avg loss: **-3.17%**
- Payoff ratio: **2.3451**, Profit factor: **2.2325**
- Avg MFE: **6.65%**, Avg MAE: **-3.58%**, Avg giveback: **4.64%**

### Exit Reasons

```json
{
  "MAX_HOLDING_DAYS": 25,
  "TREND_BREAK": 23,
  "HARD_STOP": 21,
  "TAKE_PROFIT": 19,
  "TRAILING_STOP": 3,
  "VOLATILITY_SPIKE": 1
}
```

### Diagnostic Patterns

```json
{
  "NORMAL_WIN": 40,
  "STOP_LOSS_HIT": 20,
  "SLOW_BLEED_LOSER": 13,
  "NORMAL_LOSS": 9,
  "FAST_FAILED_ENTRY": 4,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 3,
  "FAST_WINNER": 2,
  "DEEP_ADVERSE_MOVE": 1
}
```

### Entry Context Risk Flags

```json
{
  "low_roe_company": 24,
  "upper_range_chase": 21,
  "operating_loss_company": 2,
  "value_trap_penalty_high": 2,
  "expensive_per": 2,
  "expensive_pbr": 1
}
```

## SAGURI / `discovery_scout`

Discovery / Small-Cap Scout

### Key Metrics

- Trades: **41**, Win rate: **39.02%**, Total PnL: **¥406,959**
- Avg return: **0.94%**, Avg win: **10.99%**, Avg loss: **-5.49%**
- Payoff ratio: **2.0025**, Profit factor: **1.2556**
- Avg MFE: **9.20%**, Avg MAE: **-5.95%**, Avg giveback: **8.26%**

### Exit Reasons

```json
{
  "SCORE_COLLAPSE": 12,
  "HARD_STOP": 8,
  "LIQUIDITY_DRYUP": 7,
  "TAKE_PROFIT": 4,
  "EARLY_FAIL": 4,
  "MOMENTUM_DECAY": 3,
  "DISCOVERY_PROFIT_PROTECTION_1": 2,
  "MAX_HOLDING_DAYS": 1
}
```

### Diagnostic Patterns

```json
{
  "NORMAL_WIN": 8,
  "STOP_LOSS_HIT": 8,
  "NORMAL_LOSS": 7,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 6,
  "DEEP_ADVERSE_MOVE": 5,
  "FAST_FAILED_ENTRY": 3,
  "FAST_WINNER": 2,
  "WINNER_TURNED_LOSER": 2
}
```

### Entry Context Risk Flags

```json
{
  "volume_climax_or_shock": 11,
  "upper_range_chase": 10,
  "expensive_pbr": 7,
  "expensive_per": 1,
  "short_term_overheat_chase": 1
}
```

## MATSU / `contrarian_monk`

Pullback / Patient Reversal

### Key Metrics

- Trades: **74**, Win rate: **47.30%**, Total PnL: **¥1,835,126**
- Avg return: **2.50%**, Avg win: **10.49%**, Avg loss: **-4.68%**
- Payoff ratio: **2.2426**, Profit factor: **1.8252**
- Avg MFE: **8.33%**, Avg MAE: **-5.78%**, Avg giveback: **5.83%**

### Exit Reasons

```json
{
  "PULLBACK_RESOLVED": 23,
  "HARD_STOP": 22,
  "PULLBACK_FAILED": 15,
  "MAX_HOLDING_DAYS": 9,
  "PROFIT_PROTECTION": 3,
  "TREND_BREAK": 1,
  "TAKE_PROFIT": 1
}
```

### Diagnostic Patterns

```json
{
  "NORMAL_WIN": 29,
  "STOP_LOSS_HIT": 22,
  "NORMAL_LOSS": 9,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 5,
  "WINNER_TURNED_LOSER": 3,
  "FAST_FAILED_ENTRY": 2,
  "DEEP_ADVERSE_MOVE": 2,
  "SLOW_BLEED_LOSER": 1,
  "FAST_WINNER": 1
}
```

### Entry Context Risk Flags

```json
{
  "low_roe_company": 9,
  "value_trap_penalty_high": 7,
  "expensive_pbr": 7,
  "operating_loss_company": 3,
  "expensive_per": 1,
  "volume_climax_or_shock": 1
}
```

## KAESHI / `reversal_snapback`

Oversold Reversal / Snapback

### Key Metrics

- Trades: **53**, Win rate: **50.94%**, Total PnL: **¥131,691**
- Avg return: **0.21%**, Avg win: **5.79%**, Avg loss: **-5.58%**
- Payoff ratio: **1.0375**, Profit factor: **1.0852**
- Avg MFE: **5.65%**, Avg MAE: **-5.07%**, Avg giveback: **5.44%**

### Exit Reasons

```json
{
  "HARD_STOP": 19,
  "SCORE_COLLAPSE": 16,
  "SNAPBACK_COMPLETE": 13,
  "EARLY_FAIL": 5
}
```

### Diagnostic Patterns

```json
{
  "NORMAL_WIN": 19,
  "STOP_LOSS_HIT": 18,
  "FAST_WINNER": 6,
  "NORMAL_LOSS": 5,
  "FAST_FAILED_ENTRY": 3,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 2
}
```

### Entry Context Risk Flags

```json
{
  "volume_climax_or_shock": 16,
  "value_trap_penalty_high": 11,
  "low_roe_company": 9,
  "operating_loss_company": 9,
  "falling_knife_oversold": 6,
  "structural_breakdown_zone": 5,
  "expensive_pbr": 5,
  "expensive_per": 2
}
```

## HIZUMI / `value_mispricing`

Value Mispricing / Sector Relative Value

### Key Metrics

- Trades: **18**, Win rate: **61.11%**, Total PnL: **¥384,982**
- Avg return: **1.51%**, Avg win: **3.68%**, Avg loss: **-1.89%**
- Payoff ratio: **1.9496**, Profit factor: **2.9489**
- Avg MFE: **4.39%**, Avg MAE: **-2.94%**, Avg giveback: **2.88%**

### Exit Reasons

```json
{
  "MISPRICING_RESOLVED": 14,
  "HARD_STOP": 2,
  "SCORE_COLLAPSE": 2
}
```

### Diagnostic Patterns

```json
{
  "NORMAL_WIN": 11,
  "FAST_FAILED_ENTRY": 4,
  "STOP_LOSS_HIT": 2,
  "NORMAL_LOSS": 1
}
```

### Entry Context Risk Flags

```json
{
  "volume_climax_or_shock": 2,
  "short_term_overheat_chase": 1
}
```

## Worst Trades

| Agent | Ticker | Name | Entry | Exit | Ret | PnL | Hold | MFE | MAE | Giveback | Exit | Pattern |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| NAGARE | `6471.T` | 日本精工 | 2026-02-26 | 2026-03-06 | -11.06% | ¥-250,124 | 8 | 3.18% | -10.97% | 14.24% | EARLY_FAIL | DEEP_ADVERSE_MOVE |
| NAGARE | `1801.T` | 大成建設 | 2026-02-26 | 2026-03-10 | -9.00% | ¥-201,936 | 12 | 8.73% | -13.59% | 17.73% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `6370.T` | 栗田工業 | 2026-02-26 | 2026-03-10 | -8.61% | ¥-194,266 | 12 | 3.18% | -13.87% | 11.79% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `4061.T` | デンカ | 2026-03-12 | 2026-03-23 | -9.39% | ¥-193,199 | 11 | 0.41% | -11.27% | 9.80% | EARLY_FAIL | DEEP_ADVERSE_MOVE |
| KYOU | `5344.T` | ＭＡＲＵＷＡ | 2026-02-04 | 2026-02-06 | -11.96% | ¥-180,019 | 2 | 0.19% | -13.15% | 12.15% | HARD_STOP | STOP_LOSS_HIT |
| KAESHI | `6098.T` | リクルートホールディングス | 2026-02-10 | 2026-02-13 | -16.89% | ¥-179,183 | 3 | -0.06% | -19.25% | 16.83% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `6113.T` | アマダ | 2026-02-16 | 2026-03-10 | -7.79% | ¥-168,725 | 22 | 7.51% | -12.09% | 15.30% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `5831.T` | しずおかフィナンシャルグループ | 2026-02-16 | 2026-03-05 | -7.78% | ¥-168,618 | 17 | 3.86% | -12.78% | 11.63% | HARD_STOP | STOP_LOSS_HIT |
| SAGURI | `4443.T` | Sansan,Inc. | 2026-01-16 | 2026-01-20 | -11.61% | ¥-161,038 | 4 | 1.47% | -14.61% | 13.08% | HARD_STOP | STOP_LOSS_HIT |
| KAESHI | `3133.T` | kaihan co.,Ltd. | 2026-05-19 | 2026-05-20 | -14.52% | ¥-159,218 | 1 | 9.31% | -16.68% | 23.83% | HARD_STOP | STOP_LOSS_HIT |
| MATSU | `5714.T` | ＤＯＷＡホールディングス | 2026-03-18 | 2026-03-23 | -12.70% | ¥-151,270 | 5 | 1.48% | -15.43% | 14.19% | HARD_STOP | STOP_LOSS_HIT |
| MATSU | `1801.T` | 大成建設 | 2026-03-11 | 2026-03-23 | -9.86% | ¥-133,291 | 12 | 2.79% | -12.63% | 12.65% | PULLBACK_FAILED | DEEP_ADVERSE_MOVE |
| NAGARE | `7685.T` | BuySell Technologies Co.,Ltd. | 2026-03-11 | 2026-03-25 | -9.18% | ¥-131,433 | 14 | 5.89% | -14.48% | 15.07% | HARD_STOP | STOP_LOSS_HIT |
| KYOU | `7419.T` | ノジマ | 2026-04-22 | 2026-04-23 | -8.57% | ¥-131,336 | 1 | 1.59% | -12.01% | 10.16% | HARD_STOP | STOP_LOSS_HIT |
| KYOU | `1803.T` | 清水建設 | 2026-05-13 | 2026-05-14 | -8.14% | ¥-126,923 | 1 | 0.34% | -13.71% | 8.48% | HARD_STOP | STOP_LOSS_HIT |

## Best Trades

| Agent | Ticker | Name | Entry | Exit | Ret | PnL | Hold | MFE | MAE | Giveback | Exit | Pattern |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| NAGARE | `5711.T` | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 33.34% | ¥610,393 | 37 | 40.51% | -1.87% | 7.17% | TAKE_PROFIT | NORMAL_WIN |
| NAGARE | `5714.T` | ＤＯＷＡホールディングス | 2026-01-07 | 2026-02-25 | 31.93% | ¥582,563 | 49 | 32.62% | -1.47% | 0.69% | TAKE_PROFIT | NORMAL_WIN |
| NAGARE | `7189.T` | 西日本フィナンシャルホールディングス | 2026-01-06 | 2026-02-13 | 31.71% | ¥576,795 | 38 | 33.94% | -0.52% | 2.22% | TAKE_PROFIT | NORMAL_WIN |
| SAGURI | `5243.T` | note inc. | 2026-01-13 | 2026-01-16 | 45.00% | ¥535,976 | 3 | 50.90% | -4.55% | 5.90% | TAKE_PROFIT | FAST_WINNER |
| SAGURI | `4055.T` | T&S Group Inc. | 2026-05-08 | 2026-05-12 | 35.66% | ¥442,277 | 4 | 39.59% | -1.02% | 3.93% | TAKE_PROFIT | FAST_WINNER |
| NAGARE | `1801.T` | 大成建設 | 2026-01-06 | 2026-02-24 | 23.73% | ¥431,353 | 49 | 24.47% | -3.83% | 0.74% | MAX_HOLDING_DAYS | NORMAL_WIN |
| NAGARE | `3436.T` | ＳＵＭＣＯ | 2026-04-16 | 2026-05-08 | 33.80% | ¥421,782 | 22 | 61.95% | -10.38% | 28.15% | TAKE_PROFIT | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| NAGARE | `6981.T` | 村田製作所 | 2026-04-21 | 2026-05-15 | 35.36% | ¥384,223 | 24 | 37.86% | -1.53% | 2.50% | TAKE_PROFIT | NORMAL_WIN |
| NAGARE | `6752.T` | パナソニック ホールディングス | 2026-03-12 | 2026-04-28 | 17.61% | ¥362,126 | 47 | 18.34% | -7.50% | 0.72% | MAX_HOLDING_DAYS | NORMAL_WIN |
| NAGARE | `6963.T` | ローム | 2026-03-25 | 2026-05-12 | 24.83% | ¥334,760 | 48 | 25.23% | -6.92% | 0.40% | MAX_HOLDING_DAYS | NORMAL_WIN |
| NAGARE | `6754.T` | アンリツ | 2026-04-21 | 2026-05-26 | 30.66% | ¥333,818 | 35 | 34.91% | -2.02% | 4.25% | TAKE_PROFIT | NORMAL_WIN |
| KYOU | `2334.T` | eole Inc. | 2026-04-30 | 2026-05-11 | 22.49% | ¥325,425 | 11 | 24.72% | -2.20% | 2.23% | SCORE_COLLAPSE | NORMAL_WIN |
| NAGARE | `6976.T` | 太陽誘電 | 2026-04-16 | 2026-05-20 | 25.97% | ¥323,712 | 34 | 34.98% | -1.01% | 9.01% | TAKE_PROFIT | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| KYOU | `4894.T` | Cuorips Inc. | 2026-01-09 | 2026-01-16 | 22.12% | ¥286,503 | 7 | 22.38% | -2.63% | 0.26% | TAKE_PROFIT | NORMAL_WIN |
| SAGURI | `7685.T` | BuySell Technologies Co.,Ltd. | 2026-02-16 | 2026-02-24 | 29.00% | ¥272,649 | 8 | 30.35% | -1.02% | 1.35% | TAKE_PROFIT | NORMAL_WIN |

## Largest MFE Givebacks

| Agent | Ticker | Name | Entry | Exit | Ret | PnL | Hold | MFE | MAE | Giveback | Exit | Pattern |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| NAGARE | `3436.T` | ＳＵＭＣＯ | 2026-04-16 | 2026-05-08 | 33.80% | ¥421,782 | 22 | 61.95% | -10.38% | 28.15% | TAKE_PROFIT | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| KAESHI | `3133.T` | kaihan co.,Ltd. | 2026-05-19 | 2026-05-20 | -14.52% | ¥-159,218 | 1 | 9.31% | -16.68% | 23.83% | HARD_STOP | STOP_LOSS_HIT |
| KYOU | `4564.T` | OncoTherapy Science,Inc. | 2026-04-17 | 2026-04-20 | -0.20% | ¥-2,795 | 3 | 21.31% | -7.24% | 21.51% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| NAGARE | `6305.T` | 日立建機 | 2026-02-17 | 2026-03-10 | -11.81% | ¥-2,338 | 21 | 9.44% | -17.60% | 21.25% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `1605.T` | ＩＮＰＥＸ | 2026-03-16 | 2026-04-16 | -8.48% | ¥-17,925 | 31 | 12.50% | -10.36% | 20.98% | TREND_BREAK | DEEP_ADVERSE_MOVE |
| SAGURI | `4419.T` | Finatext Holdings Ltd. | 2026-05-11 | 2026-05-15 | -7.58% | ¥-87,143 | 4 | 13.35% | -12.69% | 20.93% | HARD_STOP | STOP_LOSS_HIT |
| SAGURI | `2986.T` | LA Holdings Co.,Ltd. | 2026-02-02 | 2026-02-18 | -0.40% | ¥-4,846 | 16 | 20.14% | -5.67% | 20.55% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| NAGARE | `9104.T` | 商船三井 | 2026-03-11 | 2026-04-21 | 0.62% | ¥8,970 | 41 | 20.95% | -0.79% | 20.33% | TRAILING_STOP | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| NAGARE | `1801.T` | 大成建設 | 2026-02-26 | 2026-03-10 | -9.00% | ¥-201,936 | 12 | 8.73% | -13.59% | 17.73% | HARD_STOP | STOP_LOSS_HIT |
| KAESHI | `6098.T` | リクルートホールディングス | 2026-02-10 | 2026-02-13 | -16.89% | ¥-179,183 | 3 | -0.06% | -19.25% | 16.83% | HARD_STOP | STOP_LOSS_HIT |
| KYOU | `4593.T` | HEALIOS K.K. | 2026-03-02 | 2026-03-04 | -5.04% | ¥-78,489 | 2 | 11.44% | -9.33% | 16.48% | SCORE_COLLAPSE | DEEP_ADVERSE_MOVE |
| SAGURI | `5253.T` | COVER Corporation | 2026-05-18 | 2026-05-27 | 3.53% | ¥41,281 | 9 | 19.93% | -1.93% | 16.40% | MOMENTUM_DECAY | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| NAGARE | `2579.T` | コカ・コーラ ボトラーズジャパンホールディングス | 2026-02-17 | 2026-03-24 | -4.74% | ¥-902 | 35 | 11.58% | -5.48% | 16.32% | TREND_BREAK | WINNER_TURNED_LOSER |
| MATSU | `6525.T` | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-03-04 | 2026-03-16 | -8.08% | ¥-103,137 | 12 | 7.79% | -11.82% | 15.87% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `6113.T` | アマダ | 2026-02-16 | 2026-03-10 | -7.79% | ¥-168,725 | 22 | 7.51% | -12.09% | 15.30% | HARD_STOP | STOP_LOSS_HIT |

## Deepest Adverse Trades

| Agent | Ticker | Name | Entry | Exit | Ret | PnL | Hold | MFE | MAE | Giveback | Exit | Pattern |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| KAESHI | `6098.T` | リクルートホールディングス | 2026-02-10 | 2026-02-13 | -16.89% | ¥-179,183 | 3 | -0.06% | -19.25% | 16.83% | HARD_STOP | STOP_LOSS_HIT |
| KAESHI | `4013.T` | Kinjiro Co.,Ltd. | 2026-02-12 | 2026-02-13 | -9.62% | ¥-95,294 | 1 | 0.69% | -18.73% | 10.30% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `6305.T` | 日立建機 | 2026-02-17 | 2026-03-10 | -11.81% | ¥-2,338 | 21 | 9.44% | -17.60% | 21.25% | HARD_STOP | STOP_LOSS_HIT |
| SAGURI | `247A.T` | Ai ROBOTICS INC. | 2026-02-17 | 2026-02-18 | -7.97% | ¥-89,830 | 1 | 2.83% | -17.36% | 10.81% | SCORE_COLLAPSE | DEEP_ADVERSE_MOVE |
| KAESHI | `3133.T` | kaihan co.,Ltd. | 2026-05-19 | 2026-05-20 | -14.52% | ¥-159,218 | 1 | 9.31% | -16.68% | 23.83% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `3563.T` | ＦＯＯＤ ＆ ＬＩＦＥ ＣＯＭＰＡＮＩＥＳ | 2026-03-05 | 2026-03-10 | -11.01% | ¥-77,561 | 5 | 3.73% | -16.03% | 14.73% | HARD_STOP | STOP_LOSS_HIT |
| MATSU | `5714.T` | ＤＯＷＡホールディングス | 2026-03-18 | 2026-03-23 | -12.70% | ¥-151,270 | 5 | 1.48% | -15.43% | 14.19% | HARD_STOP | STOP_LOSS_HIT |
| MATSU | `4062.T` | イビデン | 2026-03-05 | 2026-03-10 | -5.16% | ¥-69,769 | 5 | 3.76% | -14.81% | 8.92% | HARD_STOP | STOP_LOSS_HIT |
| SAGURI | `4443.T` | Sansan,Inc. | 2026-01-16 | 2026-01-20 | -11.61% | ¥-161,038 | 4 | 1.47% | -14.61% | 13.08% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `7685.T` | BuySell Technologies Co.,Ltd. | 2026-03-11 | 2026-03-25 | -9.18% | ¥-131,433 | 14 | 5.89% | -14.48% | 15.07% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `6370.T` | 栗田工業 | 2026-02-26 | 2026-03-10 | -8.61% | ¥-194,266 | 12 | 3.18% | -13.87% | 11.79% | HARD_STOP | STOP_LOSS_HIT |
| MATSU | `5101.T` | 横浜ゴム | 2026-03-04 | 2026-03-10 | -7.01% | ¥-91,967 | 6 | 3.88% | -13.86% | 10.88% | HARD_STOP | STOP_LOSS_HIT |
| MAMORU | `3391.T` | ツルハホールディングス | 2026-01-06 | 2026-01-09 | -9.78% | ¥-84,851 | 3 | 4.18% | -13.85% | 13.96% | HARD_STOP | STOP_LOSS_HIT |
| KYOU | `1803.T` | 清水建設 | 2026-05-13 | 2026-05-14 | -8.14% | ¥-126,923 | 1 | 0.34% | -13.71% | 8.48% | HARD_STOP | STOP_LOSS_HIT |
| NAGARE | `1801.T` | 大成建設 | 2026-02-26 | 2026-03-10 | -9.00% | ¥-201,936 | 12 | 8.73% | -13.59% | 17.73% | HARD_STOP | STOP_LOSS_HIT |
