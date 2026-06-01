# Neon Tokyo AI Arena Trade Diagnostics

Generated: `2026-06-01T04:39:57+00:00`
Run ID: `arena_jp_rebuild_2026_v016`

> Purpose: paste this Markdown into ChatGPT and ask for detailed agent-by-agent win/loss diagnosis and rule-improvement ideas.

## Dataset Summary

- Closed trades: **458**
- Open positions: **12**
- Agents with closed trades: **7**
- Exported compact trade rows in JSON: **458**
- Equity curve rows: **686**

## Agent Summary

| Agent | Trades | Win | Avg Ret | Avg Win | Avg Loss | Payoff | PF | PnL | Avg MFE | Avg MAE | Top Failure Patterns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KYOU / `daily_striker` | 79 | 48.10% | 1.15% | 5.00% | -2.43% | 2.0621 | 1.7407 | ¥1,103,700 | 5.37% | -3.51% | NORMAL_LOSS:30, FAST_FAILED_ENTRY:4, DEEP_ADVERSE_MOVE:3, WINNER_TURNED_LOSER:3 |
| NAGARE / `weekly_sage` | 33 | 45.45% | 5.75% | 22.69% | -8.37% | 2.7123 | 2.3166 | ¥2,613,371 | 16.69% | -8.06% | DEEP_ADVERSE_MOVE:10, WINNER_TURNED_LOSER:6, STOP_LOSS_HIT:2 |
| MAMORU / `risk_sentinel` | 92 | 48.91% | 2.02% | 7.44% | -3.17% | 2.3451 | 2.2325 | ¥1,380,806 | 6.65% | -3.58% | NORMAL_LOSS:24, STOP_LOSS_HIT:17, WINNER_TURNED_LOSER:5, DEEP_ADVERSE_MOVE:1 |
| SAGURI / `discovery_scout` | 67 | 44.78% | 0.62% | 7.71% | -5.13% | 1.5033 | 1.1188 | ¥287,883 | 8.20% | -5.60% | NORMAL_LOSS:12, DEEP_ADVERSE_MOVE:8, FAST_FAILED_ENTRY:7, STOP_LOSS_HIT:5 |
| MATSU / `contrarian_monk` | 74 | 47.30% | 2.50% | 10.49% | -4.68% | 2.2426 | 1.8252 | ¥1,835,126 | 8.33% | -5.78% | STOP_LOSS_HIT:14, NORMAL_LOSS:9, DEEP_ADVERSE_MOVE:8, WINNER_TURNED_LOSER:6 |
| KAESHI / `reversal_snapback` | 64 | 54.69% | 0.45% | 4.96% | -4.99% | 0.9935 | 1.1902 | ¥287,117 | 5.99% | -5.47% | STOP_LOSS_HIT:9, DEEP_ADVERSE_MOVE:6, NORMAL_LOSS:6, WINNER_TURNED_LOSER:6 |
| HIZUMI / `value_mispricing` | 49 | 59.18% | -0.61% | 3.33% | -6.31% | 0.5272 | 0.7231 | ¥-598,948 | 3.89% | -4.09% | STOP_LOSS_HIT:10, NORMAL_LOSS:6, DEEP_ADVERSE_MOVE:2, SLOW_BLEED_LOSER:1 |

## KYOU / `daily_striker`

### Key Metrics

- Trades: **79**, Win rate: **48.10%**, Total PnL: **¥1,103,700**
- Avg return: **1.15%**, Avg win: **5.00%**, Avg loss: **-2.43%**
- Payoff ratio: **2.0621**, Profit factor: **1.7407**
- Avg MFE: **5.37%**, Avg MAE: **-3.51%**

### Exit Reasons

```json
{
  "SCORE_COLLAPSE": 70,
  "HARD_STOP": 4,
  "MAX_HOLDING_DAYS": 4,
  "TAKE_PROFIT": 1
}
```

### Failure Patterns

```json
{
  "NORMAL_LOSS": 30,
  "FAST_FAILED_ENTRY": 4,
  "DEEP_ADVERSE_MOVE": 3,
  "WINNER_TURNED_LOSER": 3,
  "STOP_LOSS_HIT": 1
}
```

### Success Patterns

```json
{
  "NORMAL_WIN": 31,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 4,
  "FAST_WINNER": 3
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5344.T | ＭＡＲＵＷＡ | 2026-02-04 | 2026-02-06 | -11.96% | ¥-180,019 | 2 | 0.19% | -13.15% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7419.T | ノジマ | 2026-04-22 | 2026-04-23 | -8.57% | ¥-131,336 | 1 | 1.59% | -12.01% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1803.T | 清水建設 | 2026-05-13 | 2026-05-14 | -8.14% | ¥-126,923 | 1 | 0.34% | -13.71% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6814.T | 古野電気 | 2026-04-15 | 2026-04-16 | -7.08% | ¥-93,293 | 1 | -0.10% | -8.99% | HARD_STOP | STOP_LOSS_HIT |
| 4684.T | オービック | 2026-04-23 | 2026-04-24 | -6.20% | ¥-92,057 | 1 | 0.28% | -6.35% | SCORE_COLLAPSE | FAST_FAILED_ENTRY |
| 4593.T | HEALIOS K.K. | 2026-03-02 | 2026-03-04 | -5.04% | ¥-78,489 | 2 | 11.44% | -9.33% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 4516.T | 日本新薬 | 2026-03-12 | 2026-03-13 | -4.78% | ¥-65,647 | 1 | -0.10% | -4.95% | SCORE_COLLAPSE | FAST_FAILED_ENTRY |
| 9983.T | ファーストリテイリング | 2026-01-13 | 2026-01-16 | -4.50% | ¥-68,285 | 3 | 0.84% | -5.16% | SCORE_COLLAPSE | FAST_FAILED_ENTRY |
| 7282.T | 豊田合成 | 2026-04-30 | 2026-05-07 | -4.17% | ¥-67,783 | 7 | 0.51% | -6.29% | SCORE_COLLAPSE | FAST_FAILED_ENTRY |
| 5233.T | 太平洋セメント | 2026-05-14 | 2026-05-15 | -3.89% | ¥-62,264 | 1 | 1.23% | -6.28% | SCORE_COLLAPSE | NORMAL_LOSS |
| 6951.T | 日本電子 | 2026-04-22 | 2026-04-23 | -3.65% | ¥-54,688 | 1 | 1.57% | -5.12% | SCORE_COLLAPSE | NORMAL_LOSS |
| 6324.T | ハーモニック・ドライブ・システムズ | 2026-04-28 | 2026-04-30 | -2.96% | ¥-43,677 | 2 | 8.70% | -3.68% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 7733.T | オリンパス | 2026-05-14 | 2026-05-18 | -2.69% | ¥-45,814 | 4 | 1.69% | -5.48% | SCORE_COLLAPSE | NORMAL_LOSS |
| 4324.T | 電通グループ | 2026-04-14 | 2026-04-15 | -2.22% | ¥-36,457 | 1 | -0.10% | -3.43% | SCORE_COLLAPSE | NORMAL_LOSS |
| 2871.T | ニチレイ | 2026-01-21 | 2026-01-22 | -2.21% | ¥-34,869 | 1 | -0.05% | -3.19% | SCORE_COLLAPSE | NORMAL_LOSS |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 2334.T | eole Inc. | 2026-04-30 | 2026-05-11 | 22.49% | ¥325,425 | 11 | 24.72% | -2.20% | SCORE_COLLAPSE | NORMAL_WIN |
| 4894.T | Cuorips Inc. | 2026-01-09 | 2026-01-16 | 22.12% | ¥286,503 | 7 | 22.38% | -2.63% | TAKE_PROFIT | FAST_WINNER |
| 6268.T | ナブテスコ | 2026-04-28 | 2026-05-11 | 14.25% | ¥199,717 | 13 | 15.01% | -2.88% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 5333.T | 日本碍子 | 2026-05-01 | 2026-05-12 | 12.84% | ¥199,208 | 11 | 15.11% | -1.43% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 6361.T | 荏原製作所 | 2026-01-08 | 2026-01-20 | 11.46% | ¥154,019 | 12 | 14.48% | -2.38% | SCORE_COLLAPSE | NORMAL_WIN |
| 7282.T | 豊田合成 | 2026-02-04 | 2026-02-13 | 11.02% | ¥161,629 | 9 | 13.41% | -0.75% | SCORE_COLLAPSE | FAST_WINNER |
| 6586.T | マキタ | 2026-02-02 | 2026-02-13 | 10.33% | ¥161,731 | 11 | 12.34% | -1.93% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 6471.T | 日本精工 | 2026-02-05 | 2026-02-17 | 9.09% | ¥133,459 | 12 | 9.20% | -1.97% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 1803.T | 清水建設 | 2026-02-06 | 2026-02-13 | 6.19% | ¥38,884 | 7 | 11.69% | -0.26% | SCORE_COLLAPSE | FAST_WINNER |
| 8304.T | あおぞら銀行 | 2026-02-06 | 2026-02-13 | 5.94% | ¥37,221 | 7 | 8.30% | -1.32% | SCORE_COLLAPSE | NORMAL_WIN |
| 5834.T | SBI Leasing | 2026-02-02 | 2026-02-03 | 5.93% | ¥80,409 | 1 | 7.27% | -0.10% | SCORE_COLLAPSE | NORMAL_WIN |
| 6841.T | 横河電機 | 2026-02-25 | 2026-03-03 | 5.82% | ¥80,804 | 6 | 7.86% | -0.56% | SCORE_COLLAPSE | NORMAL_WIN |
| 3994.T | マネーフォワード | 2026-04-16 | 2026-04-20 | 5.79% | ¥95,102 | 4 | 9.71% | -1.16% | SCORE_COLLAPSE | NORMAL_WIN |
| 4203.T | 住友ベークライト | 2026-05-12 | 2026-05-15 | 5.73% | ¥98,927 | 3 | 9.18% | -0.81% | SCORE_COLLAPSE | NORMAL_WIN |
| 6526.T | ソシオネクスト | 2026-05-22 | 2026-05-27 | 5.52% | ¥74,776 | 5 | 7.53% | -3.51% | SCORE_COLLAPSE | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4564.T | OncoTherapy Science,Inc. | 2026-04-17 | 2026-04-20 | -0.20% | ¥-2,795 | 3 | 21.31% | -7.24% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 4593.T | HEALIOS K.K. | 2026-03-02 | 2026-03-04 | -5.04% | ¥-78,489 | 2 | 11.44% | -9.33% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 319A.T | Next Generation Technology Group Inc. | 2026-05-19 | 2026-05-21 | 0.68% | ¥9,382 | 2 | 15.11% | -7.79% | SCORE_COLLAPSE | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 5344.T | ＭＡＲＵＷＡ | 2026-02-04 | 2026-02-06 | -11.96% | ¥-180,019 | 2 | 0.19% | -13.15% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6324.T | ハーモニック・ドライブ・システムズ | 2026-04-28 | 2026-04-30 | -2.96% | ¥-43,677 | 2 | 8.70% | -3.68% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 6232.T | ACSL Ltd. | 2026-03-11 | 2026-03-13 | 1.88% | ¥25,940 | 2 | 12.19% | -1.14% | SCORE_COLLAPSE | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 7419.T | ノジマ | 2026-04-22 | 2026-04-23 | -8.57% | ¥-131,336 | 1 | 1.59% | -12.01% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4005.T | 住友化学 | 2026-02-04 | 2026-02-06 | 0.41% | ¥6,745 | 2 | 9.42% | -1.12% | SCORE_COLLAPSE | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 1803.T | 清水建設 | 2026-05-13 | 2026-05-14 | -8.14% | ¥-126,923 | 1 | 0.34% | -13.71% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5838.T | 楽天銀行 | 2026-02-12 | 2026-02-16 | 0.89% | ¥12,373 | 4 | 8.23% | -0.10% | SCORE_COLLAPSE | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1803.T | 清水建設 | 2026-05-13 | 2026-05-14 | -8.14% | ¥-126,923 | 1 | 0.34% | -13.71% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5344.T | ＭＡＲＵＷＡ | 2026-02-04 | 2026-02-06 | -11.96% | ¥-180,019 | 2 | 0.19% | -13.15% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7419.T | ノジマ | 2026-04-22 | 2026-04-23 | -8.57% | ¥-131,336 | 1 | 1.59% | -12.01% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4593.T | HEALIOS K.K. | 2026-03-02 | 2026-03-04 | -5.04% | ¥-78,489 | 2 | 11.44% | -9.33% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 6814.T | 古野電気 | 2026-04-15 | 2026-04-16 | -7.08% | ¥-93,293 | 1 | -0.10% | -8.99% | HARD_STOP | STOP_LOSS_HIT |
| 319A.T | Next Generation Technology Group Inc. | 2026-05-19 | 2026-05-21 | 0.68% | ¥9,382 | 2 | 15.11% | -7.79% | SCORE_COLLAPSE | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 6806.T | ヒロセ電機 | 2026-02-05 | 2026-02-10 | -0.58% | ¥-9,612 | 5 | 1.67% | -7.30% | SCORE_COLLAPSE | NORMAL_LOSS |
| 4564.T | OncoTherapy Science,Inc. | 2026-04-17 | 2026-04-20 | -0.20% | ¥-2,795 | 3 | 21.31% | -7.24% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 4684.T | オービック | 2026-04-23 | 2026-04-24 | -6.20% | ¥-92,057 | 1 | 0.28% | -6.35% | SCORE_COLLAPSE | FAST_FAILED_ENTRY |
| 7282.T | 豊田合成 | 2026-04-30 | 2026-05-07 | -4.17% | ¥-67,783 | 7 | 0.51% | -6.29% | SCORE_COLLAPSE | FAST_FAILED_ENTRY |


### Compact Entry Context For Worst Trades

- `5344.T` 2026-02-04 → 2026-02-06 -11.96%: score: rank=2, action=Trade / feature: return_5d_pct=5.068186444127831, return_20d_pct=14.787636201912392, volume_ratio_20d=3.3563511455788095, rsi_14=64.9367088607595, range_position_252d_0_1=0.988663967611336 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=917593915392.0, per=50.45084, pbr=6.2310295, roe_pct=13.204001000000002, operating_margin_pct=35.202998
- `7419.T` 2026-04-22 → 2026-04-23 -8.57%: score: rank=1, action=Trade / feature: return_5d_pct=15.732368896925863, return_20d_pct=18.518518518518512, volume_ratio_20d=9.13923586250969, rsi_14=75.97402597402598, range_position_252d_0_1=0.8227349365635868 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=425198747648.0, per=11.646683, pbr=1.7179112, roe_pct=17.407, operating_margin_pct=6.364
- `1803.T` 2026-05-13 → 2026-05-14 -8.14%: score: rank=1, action=Trade / feature: return_5d_pct=14.055299539170507, return_20d_pct=14.54545454545455, volume_ratio_20d=3.8606016588646725, rsi_14=70.77826725403818, range_position_252d_0_1=0.9309099119440054 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1749622456320.0, per=13.802711, pbr=1.7890282, roe_pct=13.411999999999999, operating_margin_pct=7.022
- `6814.T` 2026-04-15 → 2026-04-16 -7.08%: score: rank=3, action=Trade / feature: return_5d_pct=15.522388059701498, return_20d_pct=13.823529411764701, volume_ratio_20d=1.7698911543768205, rsi_14=62.72040302267003, range_position_252d_0_1=0.7225264695144213 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=190917296128.0, per=11.400529, pbr=2.1369026, roe_pct=20.662001, operating_margin_pct=9.422
- `4684.T` 2026-04-23 → 2026-04-24 -6.20%: score: rank=3, action=Trade / feature: return_5d_pct=10.944309927360774, return_20d_pct=18.581780538302283, volume_ratio_20d=2.9337932356041008, rsi_14=75.287797390637, range_position_252d_0_1=0.45045965270684374 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1811508887552.0, per=24.409725, pbr=3.5161414, roe_pct=15.831999999999999, operating_margin_pct=67.586
- `4593.T` 2026-03-02 → 2026-03-04 -5.04%: score: rank=3, action=Trade / feature: return_5d_pct=14.88250652741514, return_20d_pct=21.88365650969528, volume_ratio_20d=2.92743850836723, rsi_14=64.53201970443351, range_position_252d_0_1=0.4448462929475588 / value: value_trap_penalty=0.55 / fund: market_cap_jpy=42795601920.0, per=-11.142355, pbr=5.2836857, roe_pct=-65.403, operating_margin_pct=-141.25
- `4516.T` 2026-03-12 → 2026-03-13 -4.78%: score: rank=2, action=Trade / feature: return_5d_pct=16.028955532574972, return_20d_pct=9.784735812133082, volume_ratio_20d=2.228500899668387, rsi_14=73.08518253400143, range_position_252d_0_1=0.7419988770353734 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=279444258816.0, per=9.399229, pbr=0.9578595, roe_pct=11.027000000000001, operating_margin_pct=7.251
- `9983.T` 2026-01-13 → 2026-01-16 -4.50%: score: rank=1, action=Trade / feature: return_5d_pct=10.203723217421846, return_20d_pct=12.717801329261725, volume_ratio_20d=3.6762576339482465, rsi_14=70.71330589849109, range_position_252d_0_1=1.0 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=24789582348288.0, per=51.920258, pbr=9.416889, roe_pct=20.616, operating_margin_pct=17.723


## NAGARE / `weekly_sage`

### Key Metrics

- Trades: **33**, Win rate: **45.45%**, Total PnL: **¥2,613,371**
- Avg return: **5.75%**, Avg win: **22.69%**, Avg loss: **-8.37%**
- Payoff ratio: **2.7123**, Profit factor: **2.3166**
- Avg MFE: **16.69%**, Avg MAE: **-8.06%**

### Exit Reasons

```json
{
  "HARD_STOP": 13,
  "TAKE_PROFIT": 8,
  "MAX_HOLDING_DAYS": 5,
  "TREND_BREAK": 5,
  "TRAILING_STOP": 2
}
```

### Failure Patterns

```json
{
  "DEEP_ADVERSE_MOVE": 10,
  "WINNER_TURNED_LOSER": 6,
  "STOP_LOSS_HIT": 2
}
```

### Success Patterns

```json
{
  "PATIENT_TREND_WINNER": 9,
  "NORMAL_WIN": 4,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 2
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6963.T | ローム | 2026-04-21 | 2026-04-28 | -12.07% | ¥-240,595 | 7 | 0.11% | -16.95% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6471.T | 日本精工 | 2026-02-26 | 2026-03-10 | -11.82% | ¥-267,431 | 12 | 3.18% | -17.75% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6305.T | 日立建機 | 2026-02-17 | 2026-03-10 | -11.81% | ¥-2,338 | 21 | 9.44% | -17.60% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 9513.T | 電源開発 | 2026-04-01 | 2026-04-21 | -10.35% | ¥-870 | 20 | 7.37% | -10.97% | HARD_STOP | WINNER_TURNED_LOSER |
| 6963.T | ローム | 2026-03-09 | 2026-03-24 | -10.14% | ¥-55,443 | 15 | 0.64% | -13.91% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 8766.T | 東京海上ホールディングス | 2026-03-26 | 2026-04-15 | -9.24% | ¥-102,456 | 20 | 2.88% | -10.82% | HARD_STOP | STOP_LOSS_HIT |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-03-11 | 2026-03-25 | -9.18% | ¥-190,562 | 14 | 5.89% | -14.48% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1801.T | 大成建設 | 2026-02-26 | 2026-03-10 | -9.00% | ¥-201,936 | 12 | 8.73% | -13.59% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6370.T | 栗田工業 | 2026-02-26 | 2026-03-10 | -8.61% | ¥-194,266 | 12 | 3.18% | -13.87% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6113.T | アマダ | 2026-02-16 | 2026-03-10 | -7.79% | ¥-168,725 | 22 | 7.51% | -12.09% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5831.T | しずおかフィナンシャルグループ | 2026-02-16 | 2026-03-05 | -7.78% | ¥-168,618 | 17 | 3.86% | -12.78% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6301.T | 小松製作所 | 2026-02-17 | 2026-03-05 | -7.71% | ¥-1,204 | 16 | 0.00% | -11.23% | HARD_STOP | STOP_LOSS_HIT |
| 8031.T | 三井物産 | 2026-03-25 | 2026-04-20 | -7.16% | ¥-143,540 | 26 | 5.15% | -8.92% | TREND_BREAK | WINNER_TURNED_LOSER |
| 5019.T | 出光興産 | 2026-04-01 | 2026-04-21 | -6.89% | ¥-642 | 20 | 7.63% | -9.09% | TREND_BREAK | WINNER_TURNED_LOSER |
| 8830.T | 住友不動産 | 2026-03-09 | 2026-03-24 | -6.03% | ¥-32,862 | 15 | 5.95% | -9.64% | TREND_BREAK | WINNER_TURNED_LOSER |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6762.T | ＴＤＫ | 2026-04-23 | 2026-05-26 | 34.57% | ¥952 | 33 | 38.59% | -4.79% | TAKE_PROFIT | NORMAL_WIN |
| 3436.T | ＳＵＭＣＯ | 2026-04-16 | 2026-05-08 | 33.80% | ¥674,235 | 22 | 61.95% | -10.38% | TAKE_PROFIT | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 33.34% | ¥610,393 | 37 | 40.51% | -1.87% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 5714.T | ＤＯＷＡホールディングス | 2026-01-07 | 2026-02-25 | 31.93% | ¥582,563 | 49 | 32.62% | -1.47% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 7189.T | 西日本フィナンシャルホールディングス | 2026-01-06 | 2026-02-13 | 31.71% | ¥576,795 | 38 | 33.94% | -0.52% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 6471.T | 日本精工 | 2026-01-08 | 2026-02-25 | 30.67% | ¥118,991 | 48 | 32.31% | -0.97% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 6754.T | アンリツ | 2026-04-21 | 2026-05-26 | 30.66% | ¥609,246 | 35 | 34.91% | -2.02% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 5333.T | 日本碍子 | 2026-01-08 | 2026-02-25 | 27.81% | ¥107,251 | 48 | 29.51% | -1.67% | MAX_HOLDING_DAYS | PATIENT_TREND_WINNER |
| 6976.T | 太陽誘電 | 2026-04-16 | 2026-05-20 | 25.97% | ¥516,723 | 34 | 34.98% | -1.01% | TAKE_PROFIT | NORMAL_WIN |
| 1801.T | 大成建設 | 2026-01-06 | 2026-02-24 | 23.73% | ¥431,353 | 49 | 24.47% | -3.83% | MAX_HOLDING_DAYS | PATIENT_TREND_WINNER |
| 6752.T | パナソニック ホールディングス | 2026-03-12 | 2026-04-28 | 17.61% | ¥238,167 | 47 | 18.34% | -7.50% | MAX_HOLDING_DAYS | PATIENT_TREND_WINNER |
| 6674.T | ジーエス・ユアサ コーポレーション | 2026-04-01 | 2026-05-19 | 12.35% | ¥694 | 48 | 23.66% | -1.61% | MAX_HOLDING_DAYS | PATIENT_TREND_WINNER |
| 8031.T | 三井物産 | 2026-03-06 | 2026-03-24 | 4.84% | ¥104,569 | 18 | 14.87% | -5.11% | TRAILING_STOP | NORMAL_WIN |
| 6954.T | ファナック | 2026-01-06 | 2026-02-24 | 0.74% | ¥13,390 | 49 | 8.55% | -5.86% | MAX_HOLDING_DAYS | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 9104.T | 商船三井 | 2026-03-11 | 2026-04-21 | 0.62% | ¥13,020 | 41 | 20.95% | -0.79% | TRAILING_STOP | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3436.T | ＳＵＭＣＯ | 2026-04-16 | 2026-05-08 | 33.80% | ¥674,235 | 22 | 61.95% | -10.38% | TAKE_PROFIT | NORMAL_WIN |
| 6305.T | 日立建機 | 2026-02-17 | 2026-03-10 | -11.81% | ¥-2,338 | 21 | 9.44% | -17.60% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 9104.T | 商船三井 | 2026-03-11 | 2026-04-21 | 0.62% | ¥13,020 | 41 | 20.95% | -0.79% | TRAILING_STOP | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 1801.T | 大成建設 | 2026-02-26 | 2026-03-10 | -9.00% | ¥-201,936 | 12 | 8.73% | -13.59% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 9513.T | 電源開発 | 2026-04-01 | 2026-04-21 | -10.35% | ¥-870 | 20 | 7.37% | -10.97% | HARD_STOP | WINNER_TURNED_LOSER |
| 2579.T | コカ・コーラ ボトラーズジャパンホールディングス | 2026-02-17 | 2026-03-24 | -4.74% | ¥-902 | 35 | 11.58% | -5.48% | TREND_BREAK | WINNER_TURNED_LOSER |
| 6113.T | アマダ | 2026-02-16 | 2026-03-10 | -7.79% | ¥-168,725 | 22 | 7.51% | -12.09% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-03-11 | 2026-03-25 | -9.18% | ¥-190,562 | 14 | 5.89% | -14.48% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6471.T | 日本精工 | 2026-02-26 | 2026-03-10 | -11.82% | ¥-267,431 | 12 | 3.18% | -17.75% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 8058.T | 三菱商事 | 2026-03-11 | 2026-04-16 | -4.36% | ¥-90,386 | 36 | 10.48% | -4.99% | TREND_BREAK | WINNER_TURNED_LOSER |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6471.T | 日本精工 | 2026-02-26 | 2026-03-10 | -11.82% | ¥-267,431 | 12 | 3.18% | -17.75% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6305.T | 日立建機 | 2026-02-17 | 2026-03-10 | -11.81% | ¥-2,338 | 21 | 9.44% | -17.60% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6963.T | ローム | 2026-04-21 | 2026-04-28 | -12.07% | ¥-240,595 | 7 | 0.11% | -16.95% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-03-11 | 2026-03-25 | -9.18% | ¥-190,562 | 14 | 5.89% | -14.48% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6963.T | ローム | 2026-03-09 | 2026-03-24 | -10.14% | ¥-55,443 | 15 | 0.64% | -13.91% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6370.T | 栗田工業 | 2026-02-26 | 2026-03-10 | -8.61% | ¥-194,266 | 12 | 3.18% | -13.87% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1801.T | 大成建設 | 2026-02-26 | 2026-03-10 | -9.00% | ¥-201,936 | 12 | 8.73% | -13.59% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5831.T | しずおかフィナンシャルグループ | 2026-02-16 | 2026-03-05 | -7.78% | ¥-168,618 | 17 | 3.86% | -12.78% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1605.T | ＩＮＰＥＸ | 2026-03-25 | 2026-04-13 | -5.93% | ¥-122,192 | 19 | 7.17% | -12.30% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6113.T | アマダ | 2026-02-16 | 2026-03-10 | -7.79% | ¥-168,725 | 22 | 7.51% | -12.09% | HARD_STOP | DEEP_ADVERSE_MOVE |


### Compact Entry Context For Worst Trades

- `6963.T` 2026-04-21 → 2026-04-28 -12.07%: score: rank=2, action=Trade / feature: return_5d_pct=5.480210351508452, return_20d_pct=22.856221792391995, volume_ratio_20d=0.637186004784689, rsi_14=84.77064220183486, range_position_252d_0_1=0.9719957461892946 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=2022823821312.0, per=60.306133, pbr=2.668311, operating_margin_pct=1.042
- `6471.T` 2026-02-26 → 2026-03-10 -11.82%: score: rank=1, action=Trade / feature: return_5d_pct=4.461538461538472, return_20d_pct=24.873563218390803, volume_ratio_20d=1.031296417365805, rsi_14=87.7643504531722, range_position_252d_0_1=0.9957467493012516 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=585717252096.0, per=25.69221, pbr=0.87163514, roe_pct=3.5709999999999997, operating_margin_pct=4.281
- `6305.T` 2026-02-17 → 2026-03-10 -11.81%: score: rank=4, action=Trade / feature: return_5d_pct=7.55055446836268, return_20d_pct=21.656520937096467, volume_ratio_20d=0.7333831275736258, rsi_14=91.7755991285403, range_position_252d_0_1=0.9633342881695789 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1083039350784.0, per=14.792108, pbr=1.2031553, roe_pct=9.119, operating_margin_pct=9.391
- `9513.T` 2026-04-01 → 2026-04-21 -10.35%: score: rank=1, action=Trade / feature: return_5d_pct=12.289344049779615, return_20d_pct=16.927645788336942, volume_ratio_20d=1.6806683631377743, rsi_14=72.82511210762331, range_position_252d_0_1=0.9465807045820861 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=690128486400.0, per=12.050526, pbr=0.49287915, roe_pct=4.926, operating_margin_pct=4.006
- `6963.T` 2026-03-09 → 2026-03-24 -10.14%: score: rank=3, action=Trade / feature: return_5d_pct=12.760778859527111, return_20d_pct=18.57404021937843, volume_ratio_20d=0.5713590726984693, rsi_14=80.42588042588042, range_position_252d_0_1=1.0 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=2022823821312.0, per=60.306133, pbr=2.668311, operating_margin_pct=1.042
- `8766.T` 2026-03-26 → 2026-04-15 -9.24%: score: rank=1, action=Trade / feature: return_5d_pct=32.18371467025571, return_20d_pct=23.927444794952677, volume_ratio_20d=4.93868490903414, rsi_14=80.16447368421052, range_position_252d_0_1=1.0 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=13628409380864.0, per=13.748425, pbr=2.456466, roe_pct=18.701, operating_margin_pct=37.647998
- `7685.T` 2026-03-11 → 2026-03-25 -9.18%: score: rank=4, action=Trade / feature: return_5d_pct=20.46678635547576, return_20d_pct=35.555555555555564, volume_ratio_20d=1.1572475364271877, rsi_14=68.75, range_position_252d_0_1=0.9911445649767545 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=242373541888.0, per=45.26559, pbr=5.0126595, roe_pct=39.259, operating_margin_pct=9.9750005
- `1801.T` 2026-02-26 → 2026-03-10 -9.00%: score: rank=3, action=Trade / feature: return_5d_pct=9.985569985569986, return_20d_pct=23.57328145265889, volume_ratio_20d=0.7559730816132966, rsi_14=72.45989304812834, range_position_252d_0_1=0.9877113279213525 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=2206328422400.0, per=13.198053, pbr=2.3271716, operating_margin_pct=9.766


## MAMORU / `risk_sentinel`

### Key Metrics

- Trades: **92**, Win rate: **48.91%**, Total PnL: **¥1,380,806**
- Avg return: **2.02%**, Avg win: **7.44%**, Avg loss: **-3.17%**
- Payoff ratio: **2.3451**, Profit factor: **2.2325**
- Avg MFE: **6.65%**, Avg MAE: **-3.58%**

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

### Failure Patterns

```json
{
  "NORMAL_LOSS": 24,
  "STOP_LOSS_HIT": 17,
  "WINNER_TURNED_LOSER": 5,
  "DEEP_ADVERSE_MOVE": 1
}
```

### Success Patterns

```json
{
  "NORMAL_WIN": 34,
  "FAST_WINNER": 9,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 2
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | -9.78% | ¥-84,851 | 3 | 4.18% | -13.85% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6383.T | ダイフク | 2026-03-03 | 2026-03-04 | -8.22% | ¥-43,950 | 1 | 0.15% | -11.34% | HARD_STOP | STOP_LOSS_HIT |
| 5406.T | 神戸製鋼所 | 2026-02-19 | 2026-03-04 | -8.21% | ¥-36,152 | 13 | 1.22% | -10.52% | TREND_BREAK | NORMAL_LOSS |
| 4183.T | 三井化学 | 2026-02-27 | 2026-03-05 | -6.05% | ¥-26,837 | 6 | 2.46% | -10.54% | HARD_STOP | STOP_LOSS_HIT |
| 9531.T | 東京瓦斯 | 2026-03-03 | 2026-03-24 | -5.96% | ¥-31,691 | 21 | 4.93% | -8.19% | HARD_STOP | STOP_LOSS_HIT |
| 9042.T | 阪急阪神ホールディングス | 2026-04-16 | 2026-04-23 | -5.95% | ¥-55,434 | 7 | 1.57% | -7.02% | HARD_STOP | STOP_LOSS_HIT |
| 9502.T | 中部電力 | 2026-04-21 | 2026-04-23 | -5.85% | ¥-52,292 | 2 | 0.30% | -7.99% | HARD_STOP | STOP_LOSS_HIT |
| 2503.T | キリンホールディングス | 2026-03-17 | 2026-03-23 | -5.66% | ¥-47,939 | 6 | 0.55% | -8.79% | HARD_STOP | STOP_LOSS_HIT |
| 9433.T | ＫＤＤＩ | 2026-05-20 | 2026-05-26 | -5.56% | ¥-52,034 | 6 | 1.21% | -5.84% | HARD_STOP | STOP_LOSS_HIT |
| 4183.T | 三井化学 | 2026-02-13 | 2026-02-26 | -5.16% | ¥-49,715 | 13 | 0.15% | -6.07% | HARD_STOP | STOP_LOSS_HIT |
| 7181.T | かんぽ生命保険 | 2026-02-09 | 2026-02-17 | -5.01% | ¥-27,857 | 8 | 2.03% | -6.74% | HARD_STOP | STOP_LOSS_HIT |
| 3003.T | ヒューリック | 2026-03-04 | 2026-03-16 | -4.93% | ¥-47,158 | 12 | 2.57% | -5.32% | HARD_STOP | STOP_LOSS_HIT |
| 4188.T | 三菱ケミカルグループ | 2026-02-16 | 2026-03-05 | -4.85% | ¥-7,477 | 17 | 4.92% | -9.51% | HARD_STOP | STOP_LOSS_HIT |
| 5411.T | ＪＦＥホールディングス | 2026-02-09 | 2026-02-26 | -4.30% | ¥-23,930 | 17 | 3.09% | -7.33% | HARD_STOP | STOP_LOSS_HIT |
| 5831.T | しずおかフィナンシャルグループ | 2026-01-13 | 2026-01-22 | -4.28% | ¥-20,953 | 9 | 1.38% | -6.18% | HARD_STOP | STOP_LOSS_HIT |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 8354.T | ふくおかフィナンシャルグループ | 2026-01-23 | 2026-02-06 | 18.55% | ¥162,874 | 14 | 23.52% | -2.08% | TAKE_PROFIT | NORMAL_WIN |
| 8591.T | オリックス | 2026-01-28 | 2026-02-12 | 18.00% | ¥157,503 | 15 | 22.66% | -1.12% | TAKE_PROFIT | NORMAL_WIN |
| 6724.T | セイコーエプソン | 2026-05-01 | 2026-05-08 | 16.73% | ¥147,340 | 7 | 17.81% | -1.38% | VOLATILITY_SPIKE | FAST_WINNER |
| 3407.T | 旭化成 | 2026-02-04 | 2026-02-09 | 15.28% | ¥137,651 | 5 | 15.73% | -0.96% | TAKE_PROFIT | FAST_WINNER |
| 9104.T | 商船三井 | 2026-03-17 | 2026-03-19 | 14.92% | ¥126,612 | 2 | 19.96% | -1.07% | TAKE_PROFIT | FAST_WINNER |
| 6178.T | 日本郵政 | 2026-01-26 | 2026-02-10 | 14.55% | ¥6,566 | 15 | 16.66% | -2.59% | TAKE_PROFIT | NORMAL_WIN |
| 4503.T | アステラス製薬 | 2026-01-28 | 2026-02-06 | 14.36% | ¥127,441 | 9 | 18.71% | -1.05% | TAKE_PROFIT | FAST_WINNER |
| 1802.T | 大林組 | 2026-01-27 | 2026-02-09 | 13.78% | ¥120,636 | 13 | 22.61% | -4.03% | TAKE_PROFIT | NORMAL_WIN |
| 2768.T | 双日 | 2026-01-06 | 2026-01-14 | 13.01% | ¥113,333 | 8 | 16.56% | -0.22% | TAKE_PROFIT | FAST_WINNER |
| 6971.T | 京セラ | 2026-05-11 | 2026-05-27 | 12.99% | ¥115,754 | 16 | 13.10% | -0.72% | TAKE_PROFIT | NORMAL_WIN |
| 8031.T | 三井物産 | 2026-01-29 | 2026-02-12 | 12.08% | ¥10,241 | 14 | 16.74% | -0.96% | TAKE_PROFIT | NORMAL_WIN |
| 9107.T | 川崎汽船 | 2026-03-10 | 2026-03-19 | 11.50% | ¥65,833 | 9 | 14.92% | -1.51% | TAKE_PROFIT | FAST_WINNER |
| 9147.T | ＮＩＰＰＯＮ ＥＸＰＲＥＳＳホールディングス | 2026-04-28 | 2026-05-11 | 11.24% | ¥103,373 | 13 | 16.04% | -1.06% | TAKE_PROFIT | NORMAL_WIN |
| 2267.T | ヤクルト本社 | 2026-04-27 | 2026-05-07 | 10.95% | ¥98,190 | 10 | 12.36% | -1.83% | TAKE_PROFIT | FAST_WINNER |
| 9513.T | 電源開発 | 2026-03-25 | 2026-04-03 | 10.91% | ¥101,696 | 9 | 13.33% | -3.09% | TAKE_PROFIT | FAST_WINNER |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | -9.78% | ¥-84,851 | 3 | 4.18% | -13.85% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1721.T | コムシスホールディングス | 2026-05-01 | 2026-05-13 | -3.39% | ¥-29,783 | 12 | 9.55% | -8.27% | HARD_STOP | WINNER_TURNED_LOSER |
| 9531.T | 東京瓦斯 | 2026-03-03 | 2026-03-24 | -5.96% | ¥-31,691 | 21 | 4.93% | -8.19% | HARD_STOP | STOP_LOSS_HIT |
| 5019.T | 出光興産 | 2026-02-26 | 2026-03-05 | 0.62% | ¥5,943 | 7 | 10.95% | -3.16% | TRAILING_STOP | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 4188.T | 三菱ケミカルグループ | 2026-02-16 | 2026-03-05 | -4.85% | ¥-7,477 | 17 | 4.92% | -9.51% | HARD_STOP | STOP_LOSS_HIT |
| 7912.T | 大日本印刷 | 2026-03-09 | 2026-03-23 | -3.78% | ¥-35,553 | 14 | 5.84% | -6.36% | TREND_BREAK | WINNER_TURNED_LOSER |
| 5406.T | 神戸製鋼所 | 2026-02-19 | 2026-03-04 | -8.21% | ¥-36,152 | 13 | 1.22% | -10.52% | TREND_BREAK | NORMAL_LOSS |
| 9042.T | 阪急阪神ホールディングス | 2026-05-14 | 2026-05-26 | 0.15% | ¥1,379 | 12 | 9.36% | -2.58% | TRAILING_STOP | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 1802.T | 大林組 | 2026-01-27 | 2026-02-09 | 13.78% | ¥120,636 | 13 | 22.61% | -4.03% | TAKE_PROFIT | NORMAL_WIN |
| 4183.T | 三井化学 | 2026-02-27 | 2026-03-05 | -6.05% | ¥-26,837 | 6 | 2.46% | -10.54% | HARD_STOP | STOP_LOSS_HIT |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3391.T | ツルハホールディングス | 2026-01-06 | 2026-01-09 | -9.78% | ¥-84,851 | 3 | 4.18% | -13.85% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6383.T | ダイフク | 2026-03-03 | 2026-03-04 | -8.22% | ¥-43,950 | 1 | 0.15% | -11.34% | HARD_STOP | STOP_LOSS_HIT |
| 4183.T | 三井化学 | 2026-02-27 | 2026-03-05 | -6.05% | ¥-26,837 | 6 | 2.46% | -10.54% | HARD_STOP | STOP_LOSS_HIT |
| 5406.T | 神戸製鋼所 | 2026-02-19 | 2026-03-04 | -8.21% | ¥-36,152 | 13 | 1.22% | -10.52% | TREND_BREAK | NORMAL_LOSS |
| 4188.T | 三菱ケミカルグループ | 2026-02-16 | 2026-03-05 | -4.85% | ¥-7,477 | 17 | 4.92% | -9.51% | HARD_STOP | STOP_LOSS_HIT |
| 2503.T | キリンホールディングス | 2026-03-17 | 2026-03-23 | -5.66% | ¥-47,939 | 6 | 0.55% | -8.79% | HARD_STOP | STOP_LOSS_HIT |
| 5076.T | インフロニア・ホールディングス | 2026-02-26 | 2026-03-05 | -2.66% | ¥-25,651 | 7 | 3.45% | -8.78% | HARD_STOP | STOP_LOSS_HIT |
| 1721.T | コムシスホールディングス | 2026-05-01 | 2026-05-13 | -3.39% | ¥-29,783 | 12 | 9.55% | -8.27% | HARD_STOP | WINNER_TURNED_LOSER |
| 9531.T | 東京瓦斯 | 2026-03-03 | 2026-03-24 | -5.96% | ¥-31,691 | 21 | 4.93% | -8.19% | HARD_STOP | STOP_LOSS_HIT |
| 9502.T | 中部電力 | 2026-04-21 | 2026-04-23 | -5.85% | ¥-52,292 | 2 | 0.30% | -7.99% | HARD_STOP | STOP_LOSS_HIT |


### Compact Entry Context For Worst Trades

- `3391.T` 2026-01-06 → 2026-01-09 -9.78%: score: rank=3, action=Trade / feature: return_5d_pct=0.7005253940455258, return_20d_pct=4.166666666666674, volume_ratio_20d=1.0158954921040588, rsi_14=57.1875, range_position_252d_0_1=0.962278675904542 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=868679221248.0, per=13.304885, pbr=0.99174076, roe_pct=7.546, operating_margin_pct=3.636
- `6383.T` 2026-03-03 → 2026-03-04 -8.22%: score: rank=4, action=Trade / feature: return_5d_pct=-0.9169960474308292, return_20d_pct=16.1200667037243, volume_ratio_20d=0.9488290812996651, rsi_14=66.91394658753708, range_position_252d_0_1=0.9260249554367201 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=2659645390848.0, per=35.716755, pbr=5.802992, operating_margin_pct=15.223
- `5406.T` 2026-02-19 → 2026-03-04 -8.21%: score: rank=1, action=Trade / feature: return_5d_pct=-0.8743169398907069, return_20d_pct=-0.17609509134932644, volume_ratio_20d=0.5840567480177463, rsi_14=54.97925311203319, range_position_252d_0_1=0.879957127545552 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=770737963008.0, per=8.195963, pbr=0.611056, roe_pct=7.621, operating_margin_pct=4.971
- `4183.T` 2026-02-27 → 2026-03-05 -6.05%: score: rank=3, action=Trade / feature: return_5d_pct=-1.275781416117372, return_20d_pct=3.131941359395829, volume_ratio_20d=1.0877509288017249, rsi_14=44.09523809523809, range_position_252d_0_1=0.864905823771379 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=767109300224.0, per=23.160881, pbr=0.90329856, roe_pct=4.788, operating_margin_pct=3.531
- `9531.T` 2026-03-03 → 2026-03-24 -5.96%: score: rank=5, action=Trade / feature: return_5d_pct=1.5049504950495063, return_20d_pct=14.436672123827954, volume_ratio_20d=1.045675908439635, rsi_14=67.22433460076046, range_position_252d_0_1=0.9257078777684329 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=2036190281728.0, per=9.329504, pbr=1.184508, roe_pct=12.762, operating_margin_pct=6.959999999999999
- `9042.T` 2026-04-16 → 2026-04-23 -5.95%: score: rank=3, action=Trade / feature: return_5d_pct=-0.29136316337148305, return_20d_pct=14.289122137404586, volume_ratio_20d=0.8045203303318319, rsi_14=73.81703470031546, range_position_252d_0_1=0.9069965870307167 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1089115717632.0, per=13.905801, pbr=0.9867622, roe_pct=7.153, operating_margin_pct=3.9739999999999998
- `9502.T` 2026-04-21 → 2026-04-23 -5.85%: score: rank=8, action=Trade / feature: return_5d_pct=-0.10779734099892746, return_20d_pct=10.427010923535263, volume_ratio_20d=1.4799116968346917, rsi_14=68.36734693877551, range_position_252d_0_1=0.8752260397830018 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=2132475904000.0, per=9.361011, pbr=0.6795099, roe_pct=7.7360004, operating_margin_pct=6.2750004
- `2503.T` 2026-03-17 → 2026-03-23 -5.66%: score: rank=8, action=Trade / feature: return_5d_pct=0.07664303506418335, return_20d_pct=0.7717538105344479, volume_ratio_20d=0.6723104805527333, rsi_14=46.09297725024728, range_position_252d_0_1=0.8329065300896287 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=2129601495040.0, per=14.527287, pbr=1.6203139, roe_pct=12.194, operating_margin_pct=8.402999999999999


## SAGURI / `discovery_scout`

### Key Metrics

- Trades: **67**, Win rate: **44.78%**, Total PnL: **¥287,883**
- Avg return: **0.62%**, Avg win: **7.71%**, Avg loss: **-5.13%**
- Payoff ratio: **1.5033**, Profit factor: **1.1188**
- Avg MFE: **8.20%**, Avg MAE: **-5.60%**

### Exit Reasons

```json
{
  "SCORE_COLLAPSE": 21,
  "MAX_HOLDING_DAYS": 13,
  "HARD_STOP": 13,
  "MOMENTUM_DECAY": 8,
  "LIQUIDITY_DRYUP": 5,
  "TAKE_PROFIT": 5,
  "TRAILING_STOP": 2
}
```

### Failure Patterns

```json
{
  "NORMAL_LOSS": 12,
  "DEEP_ADVERSE_MOVE": 8,
  "FAST_FAILED_ENTRY": 7,
  "STOP_LOSS_HIT": 5,
  "WINNER_TURNED_LOSER": 5
}
```

### Success Patterns

```json
{
  "NORMAL_WIN": 18,
  "FAST_WINNER": 8,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 4
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | -11.91% | ¥-160,584 | 1 | 1.07% | -16.15% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | -11.61% | ¥-162,876 | 4 | 1.47% | -14.61% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-02-25 | 2026-03-04 | -11.03% | ¥-149,409 | 7 | 1.87% | -12.75% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7047.T | PORT INC. | 2026-02-18 | 2026-02-25 | -8.35% | ¥-114,349 | 7 | 2.37% | -9.57% | HARD_STOP | STOP_LOSS_HIT |
| 4419.T | Finatext Holdings Ltd. | 2026-05-11 | 2026-05-15 | -7.58% | ¥-104,006 | 4 | 13.35% | -12.69% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 3556.T | RenetJapanGroup,Inc. | 2026-01-16 | 2026-01-23 | -7.54% | ¥-105,739 | 7 | 1.18% | -9.36% | HARD_STOP | STOP_LOSS_HIT |
| 4431.T | Smaregi,Inc. | 2026-01-20 | 2026-01-21 | -7.34% | ¥-101,602 | 1 | -0.10% | -9.22% | SCORE_COLLAPSE | FAST_FAILED_ENTRY |
| 5532.T | REALGATE INC. | 2026-04-21 | 2026-04-22 | -6.36% | ¥-69,422 | 1 | 0.48% | -16.17% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 9553.T | MicroAd,Inc. | 2026-02-20 | 2026-02-25 | -6.26% | ¥-86,983 | 5 | 2.58% | -8.50% | HARD_STOP | STOP_LOSS_HIT |
| 299A.T | Kurashiru,Inc. | 2026-05-01 | 2026-05-08 | -6.21% | ¥-84,798 | 7 | 1.62% | -12.13% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 9279.T | GIFT HOLDINGS INC. | 2026-02-26 | 2026-03-04 | -5.92% | ¥-80,646 | 6 | 0.85% | -7.49% | SCORE_COLLAPSE | FAST_FAILED_ENTRY |
| 332A.T | MEEQ Inc. | 2026-04-20 | 2026-04-27 | -5.77% | ¥-13,170 | 7 | 5.23% | -10.25% | HARD_STOP | WINNER_TURNED_LOSER |
| 7806.T | MTG Co.,Ltd. | 2026-03-02 | 2026-03-04 | -5.58% | ¥-78,692 | 2 | 1.12% | -7.92% | HARD_STOP | STOP_LOSS_HIT |
| 4071.T | Plus Alpha Consulting Co.,LTD. | 2026-05-08 | 2026-05-13 | -5.49% | ¥-13,825 | 5 | 0.94% | -6.60% | SCORE_COLLAPSE | FAST_FAILED_ENTRY |
| 4413.T | baudroie,inc. | 2026-04-16 | 2026-04-27 | -5.44% | ¥-75,789 | 11 | 4.97% | -7.20% | SCORE_COLLAPSE | NORMAL_LOSS |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4055.T | T&S Group Inc. | 2026-05-08 | 2026-05-12 | 35.66% | ¥89,707 | 4 | 39.59% | -1.02% | TAKE_PROFIT | FAST_WINNER |
| 5243.T | note inc. | 2026-01-14 | 2026-01-16 | 25.88% | ¥336,885 | 2 | 31.01% | -1.33% | TAKE_PROFIT | FAST_WINNER |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-02-16 | 2026-02-19 | 21.06% | ¥283,356 | 3 | 22.20% | -1.02% | TAKE_PROFIT | FAST_WINNER |
| 9270.T | Valuence Holdings Inc. | 2026-01-13 | 2026-01-19 | 20.95% | ¥271,303 | 6 | 22.87% | -0.60% | TAKE_PROFIT | FAST_WINNER |
| 7318.T | SERENDIP HOLDINGS Co.,Ltd. | 2026-02-25 | 2026-03-02 | 19.40% | ¥263,231 | 5 | 29.74% | -0.17% | TAKE_PROFIT | FAST_WINNER |
| 5834.T | SBI Leasing | 2026-01-30 | 2026-02-10 | 11.22% | ¥147,700 | 11 | 13.40% | -1.21% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 7777.T | 3-D Matrix,Ltd. | 2026-02-26 | 2026-03-05 | 9.78% | ¥133,516 | 7 | 18.55% | -2.93% | MOMENTUM_DECAY | FAST_WINNER |
| 9270.T | Valuence Holdings Inc. | 2026-04-03 | 2026-04-06 | 9.64% | ¥131,843 | 3 | 10.89% | -0.10% | LIQUIDITY_DRYUP | FAST_WINNER |
| 6039.T | Japan Animal Referral Medical Center Co.,Ltd. | 2026-02-17 | 2026-02-25 | 7.40% | ¥102,097 | 8 | 11.84% | -2.34% | SCORE_COLLAPSE | FAST_WINNER |
| 3482.T | Loadstar Capital K.K. | 2026-02-17 | 2026-03-02 | 6.74% | ¥92,911 | 13 | 10.18% | -1.69% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 2986.T | LA Holdings Co.,Ltd. | 2026-02-02 | 2026-02-13 | 6.17% | ¥81,690 | 11 | 20.14% | -3.24% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 2980.T | SRE Holdings Corporation | 2026-04-09 | 2026-04-21 | 6.02% | ¥83,386 | 12 | 8.53% | -7.46% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 7806.T | MTG Co.,Ltd. | 2026-03-06 | 2026-03-17 | 5.59% | ¥76,738 | 11 | 10.47% | -3.00% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-04-16 | 2026-04-17 | 5.28% | ¥73,450 | 1 | 9.30% | -1.17% | LIQUIDITY_DRYUP | NORMAL_WIN |
| 3479.T | TKP Corporation | 2026-01-26 | 2026-02-06 | 5.02% | ¥67,727 | 11 | 9.89% | -1.10% | MAX_HOLDING_DAYS | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 7777.T | 3-D Matrix,Ltd. | 2026-03-06 | 2026-03-13 | -3.68% | ¥-50,659 | 7 | 20.03% | -14.18% | TRAILING_STOP | DEEP_ADVERSE_MOVE |
| 4419.T | Finatext Holdings Ltd. | 2026-05-11 | 2026-05-15 | -7.58% | ¥-104,006 | 4 | 13.35% | -12.69% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5253.T | COVER Corporation | 2026-05-18 | 2026-05-27 | 3.53% | ¥47,532 | 9 | 19.93% | -1.93% | MOMENTUM_DECAY | NORMAL_WIN |
| 153A.T | Caulis Inc. | 2026-04-17 | 2026-04-28 | 2.81% | ¥39,079 | 11 | 18.87% | -5.80% | MOMENTUM_DECAY | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 7806.T | MTG Co.,Ltd. | 2026-05-13 | 2026-05-19 | -3.38% | ¥-46,159 | 6 | 10.65% | -6.00% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 2986.T | LA Holdings Co.,Ltd. | 2026-02-02 | 2026-02-13 | 6.17% | ¥81,690 | 11 | 20.14% | -3.24% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 4417.T | Global Security Experts Inc. | 2026-05-07 | 2026-05-15 | -0.60% | ¥-8,111 | 8 | 13.17% | -2.07% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 7318.T | SERENDIP HOLDINGS Co.,Ltd. | 2026-02-13 | 2026-02-20 | 0.21% | ¥2,853 | 7 | 13.37% | -1.17% | MOMENTUM_DECAY | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | -11.61% | ¥-162,876 | 4 | 1.47% | -14.61% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | -11.91% | ¥-160,584 | 1 | 1.07% | -16.15% | HARD_STOP | DEEP_ADVERSE_MOVE |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5532.T | REALGATE INC. | 2026-04-21 | 2026-04-22 | -6.36% | ¥-69,422 | 1 | 0.48% | -16.17% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | -11.91% | ¥-160,584 | 1 | 1.07% | -16.15% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | -11.61% | ¥-162,876 | 4 | 1.47% | -14.61% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7777.T | 3-D Matrix,Ltd. | 2026-03-06 | 2026-03-13 | -3.68% | ¥-50,659 | 7 | 20.03% | -14.18% | TRAILING_STOP | DEEP_ADVERSE_MOVE |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-02-25 | 2026-03-04 | -11.03% | ¥-149,409 | 7 | 1.87% | -12.75% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4419.T | Finatext Holdings Ltd. | 2026-05-11 | 2026-05-15 | -7.58% | ¥-104,006 | 4 | 13.35% | -12.69% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-03-10 | 2026-03-24 | -4.33% | ¥-59,664 | 14 | 8.33% | -12.51% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 299A.T | Kurashiru,Inc. | 2026-05-01 | 2026-05-08 | -6.21% | ¥-84,798 | 7 | 1.62% | -12.13% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 153A.T | Caulis Inc. | 2026-05-01 | 2026-05-12 | 3.64% | ¥49,761 | 11 | 7.96% | -12.07% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 332A.T | MEEQ Inc. | 2026-04-20 | 2026-04-27 | -5.77% | ¥-13,170 | 7 | 5.23% | -10.25% | HARD_STOP | WINNER_TURNED_LOSER |


### Compact Entry Context For Worst Trades

- `5243.T` 2026-01-26 → 2026-01-27 -11.91%: score: rank=6, action=Trade / feature: return_5d_pct=17.384433030422763, return_20d_pct=90.93830334190231, volume_ratio_20d=1.4437206857180407, rsi_14=77.67672591980157, range_position_252d_0_1=0.9115797262301147 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=38538764288.0, per=74.13601, pbr=7.0371614, roe_pct=19.439, operating_margin_pct=19.326
- `4443.T` 2026-01-16 → 2026-01-20 -11.61%: score: rank=3, action=Trade / feature: return_5d_pct=11.575381140598529, return_20d_pct=17.479191438763376, volume_ratio_20d=6.196071396537806, rsi_14=73.46938775510205, range_position_252d_0_1=0.376953125 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=226175877120.0, per=110.79404, pbr=11.916517, roe_pct=15.695, operating_margin_pct=21.867001
- `7685.T` 2026-02-25 → 2026-03-04 -11.03%: score: rank=3, action=Trade / feature: return_5d_pct=10.07194244604317, return_20d_pct=22.768304914744242, volume_ratio_20d=2.1359339119024185, rsi_14=84.51086956521739, range_position_252d_0_1=0.9328053755699544 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=242373541888.0, per=45.26559, pbr=5.0126595, roe_pct=39.259, operating_margin_pct=9.9750005
- `7047.T` 2026-02-18 → 2026-02-25 -8.35%: score: rank=2, action=Trade / feature: return_5d_pct=16.852367688022273, return_20d_pct=12.366071428571423, volume_ratio_20d=6.741645451322871, rsi_14=72.38605898123325, range_position_252d_0_1=0.9641666666666666 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=28334635008.0, per=10.629921, pbr=2.680739, roe_pct=8.584999999999999, operating_margin_pct=9.6870005
- `4419.T` 2026-05-11 → 2026-05-15 -7.58%: score: rank=7, action=Trade / feature: return_5d_pct=16.34877384196185, return_20d_pct=26.33136094674555, volume_ratio_20d=1.87451106713911, rsi_14=79.29292929292929, range_position_252d_0_1=0.7140921409214093 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=69232304128.0, per=46.4323, pbr=6.3791428, roe_pct=15.955, operating_margin_pct=28.726998
- `3556.T` 2026-01-16 → 2026-01-23 -7.54%: score: rank=5, action=Trade / feature: return_5d_pct=13.179723502304142, return_20d_pct=39.54545454545455, volume_ratio_20d=4.29489639293937, rsi_14=81.00208768267223, range_position_252d_0_1=0.9187725631768953 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=12602387456.0, per=17.412432, pbr=8.351704, roe_pct=69.43, operating_margin_pct=11.677
- `4431.T` 2026-01-20 → 2026-01-21 -7.34%: score: rank=9, action=Trade / feature: return_5d_pct=3.8772213247172838, return_20d_pct=3.70967741935484, volume_ratio_20d=4.074817371758851, rsi_14=57.2992700729927, range_position_252d_0_1=0.6617766911165445 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=47574470656.0, per=27.450544, pbr=5.337275, roe_pct=23.876, operating_margin_pct=27.095999999999997
- `5532.T` 2026-04-21 → 2026-04-22 -6.36%: score: rank=6, action=Trade / feature: return_5d_pct=9.768637532133685, return_20d_pct=56.2385656787413, volume_ratio_20d=1.9268292682926829, rsi_14=87.77335984095427, range_position_252d_0_1=0.9634034766697164 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=23002251264.0, per=34.86842, pbr=5.6436296, roe_pct=18.462999, operating_margin_pct=7.375


## MATSU / `contrarian_monk`

### Key Metrics

- Trades: **74**, Win rate: **47.30%**, Total PnL: **¥1,835,126**
- Avg return: **2.50%**, Avg win: **10.49%**, Avg loss: **-4.68%**
- Payoff ratio: **2.2426**, Profit factor: **1.8252**
- Avg MFE: **8.33%**, Avg MAE: **-5.78%**

### Exit Reasons

```json
{
  "PULLBACK_RESOLVED": 23,
  "HARD_STOP": 22,
  "PULLBACK_FAILED": 15,
  "MAX_HOLDING_DAYS": 9,
  "TRAILING_STOP": 3,
  "TREND_BREAK": 1,
  "TAKE_PROFIT": 1
}
```

### Failure Patterns

```json
{
  "STOP_LOSS_HIT": 14,
  "NORMAL_LOSS": 9,
  "DEEP_ADVERSE_MOVE": 8,
  "WINNER_TURNED_LOSER": 6,
  "FAST_FAILED_ENTRY": 2
}
```

### Success Patterns

```json
{
  "NORMAL_WIN": 19,
  "FAST_WINNER": 16
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5714.T | ＤＯＷＡホールディングス | 2026-03-18 | 2026-03-23 | -12.70% | ¥-151,270 | 5 | 1.48% | -15.43% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1801.T | 大成建設 | 2026-03-11 | 2026-03-23 | -9.86% | ¥-133,291 | 12 | 2.79% | -12.63% | PULLBACK_FAILED | DEEP_ADVERSE_MOVE |
| 6323.T | ローツェ | 2026-03-03 | 2026-03-04 | -8.22% | ¥-115,367 | 1 | 0.91% | -12.75% | PULLBACK_FAILED | DEEP_ADVERSE_MOVE |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-03-04 | 2026-03-16 | -8.08% | ¥-103,137 | 12 | 7.79% | -11.82% | HARD_STOP | WINNER_TURNED_LOSER |
| 5016.T | ＪＸ金属 | 2026-05-15 | 2026-05-18 | -7.95% | ¥-105,747 | 3 | 2.78% | -10.43% | HARD_STOP | STOP_LOSS_HIT |
| 5110.T | 住友ゴム工業 | 2026-03-03 | 2026-03-05 | -7.67% | ¥-101,340 | 2 | 0.25% | -12.48% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1605.T | ＩＮＰＥＸ | 2026-04-13 | 2026-04-16 | -7.51% | ¥-101,491 | 3 | 0.68% | -9.42% | HARD_STOP | STOP_LOSS_HIT |
| 4506.T | 住友ファーマ | 2026-01-20 | 2026-01-23 | -7.32% | ¥-89,476 | 3 | 0.19% | -9.97% | HARD_STOP | STOP_LOSS_HIT |
| 6506.T | 安川電機 | 2026-02-19 | 2026-03-05 | -7.28% | ¥-101,307 | 14 | 7.00% | -13.29% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5101.T | 横浜ゴム | 2026-03-04 | 2026-03-10 | -7.01% | ¥-91,967 | 6 | 3.88% | -13.86% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 8058.T | 三菱商事 | 2026-04-13 | 2026-04-16 | -6.62% | ¥-80,315 | 3 | 1.26% | -7.24% | HARD_STOP | STOP_LOSS_HIT |
| 1803.T | 清水建設 | 2026-03-11 | 2026-03-17 | -6.56% | ¥-88,085 | 6 | 0.80% | -7.21% | HARD_STOP | STOP_LOSS_HIT |
| 5713.T | 住友金属鉱山 | 2026-04-23 | 2026-04-28 | -6.02% | ¥-72,036 | 5 | 0.05% | -9.75% | HARD_STOP | STOP_LOSS_HIT |
| 6920.T | レーザーテック | 2026-05-15 | 2026-05-18 | -5.99% | ¥-86,450 | 3 | -0.10% | -7.76% | HARD_STOP | STOP_LOSS_HIT |
| 7003.T | 三井Ｅ＆Ｓ | 2026-03-06 | 2026-03-10 | -5.78% | ¥-76,285 | 4 | 0.97% | -13.16% | HARD_STOP | DEEP_ADVERSE_MOVE |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5802.T | 住友電気工業 | 2026-01-27 | 2026-02-04 | 21.33% | ¥247,873 | 8 | 26.18% | -0.67% | PULLBACK_RESOLVED | FAST_WINNER |
| 285A.T | キオクシアホールディングス | 2026-03-27 | 2026-04-07 | 20.48% | ¥91,020 | 11 | 21.12% | -4.03% | PULLBACK_RESOLVED | NORMAL_WIN |
| 5344.T | ＭＡＲＵＷＡ | 2026-05-12 | 2026-05-14 | 20.20% | ¥264,911 | 2 | 30.59% | -1.40% | TAKE_PROFIT | FAST_WINNER |
| 1803.T | 清水建設 | 2026-01-27 | 2026-02-06 | 18.43% | ¥210,197 | 10 | 26.32% | -1.52% | PULLBACK_RESOLVED | FAST_WINNER |
| 5803.T | フジクラ | 2026-04-01 | 2026-04-10 | 18.21% | ¥198,317 | 9 | 29.02% | -3.12% | PULLBACK_RESOLVED | FAST_WINNER |
| 5706.T | 三井金属 | 2026-02-02 | 2026-02-10 | 17.35% | ¥100,674 | 8 | 18.92% | -2.47% | PULLBACK_RESOLVED | FAST_WINNER |
| 1893.T | 五洋建設 | 2026-01-29 | 2026-02-09 | 17.10% | ¥194,842 | 11 | 18.26% | -2.12% | PULLBACK_RESOLVED | NORMAL_WIN |
| 6963.T | ローム | 2026-04-28 | 2026-05-11 | 16.99% | ¥197,695 | 13 | 21.08% | -0.10% | PULLBACK_RESOLVED | NORMAL_WIN |
| 4385.T | メルカリ | 2026-02-06 | 2026-02-13 | 16.19% | ¥198,907 | 7 | 18.75% | -1.29% | PULLBACK_RESOLVED | FAST_WINNER |
| 7806.T | MTG Co.,Ltd. | 2026-05-22 | 2026-05-29 | 16.04% | ¥219,603 | 7 | 18.82% | -3.85% | PULLBACK_RESOLVED | FAST_WINNER |
| 5802.T | 住友電気工業 | 2026-05-21 | 2026-05-27 | 15.20% | ¥194,308 | 6 | 19.14% | -4.53% | PULLBACK_RESOLVED | FAST_WINNER |
| 1802.T | 大林組 | 2026-02-02 | 2026-02-09 | 13.05% | ¥76,649 | 7 | 21.82% | -1.52% | PULLBACK_RESOLVED | FAST_WINNER |
| 5344.T | ＭＡＲＵＷＡ | 2026-05-21 | 2026-05-26 | 12.01% | ¥152,114 | 5 | 13.10% | -1.96% | PULLBACK_RESOLVED | FAST_WINNER |
| 5802.T | 住友電気工業 | 2026-04-16 | 2026-04-23 | 11.75% | ¥154,298 | 7 | 12.27% | -0.34% | PULLBACK_RESOLVED | FAST_WINNER |
| 4061.T | デンカ | 2026-04-21 | 2026-04-27 | 11.61% | ¥137,773 | 6 | 13.79% | -0.84% | PULLBACK_RESOLVED | FAST_WINNER |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-03-04 | 2026-03-16 | -8.08% | ¥-103,137 | 12 | 7.79% | -11.82% | HARD_STOP | WINNER_TURNED_LOSER |
| 5344.T | ＭＡＲＵＷＡ | 2026-03-23 | 2026-03-31 | -3.60% | ¥-41,537 | 8 | 11.65% | -5.19% | TRAILING_STOP | WINNER_TURNED_LOSER |
| 6506.T | 安川電機 | 2026-02-19 | 2026-03-05 | -7.28% | ¥-101,307 | 14 | 7.00% | -13.29% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5714.T | ＤＯＷＡホールディングス | 2026-03-18 | 2026-03-23 | -12.70% | ¥-151,270 | 5 | 1.48% | -15.43% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1801.T | 大成建設 | 2026-03-11 | 2026-03-23 | -9.86% | ¥-133,291 | 12 | 2.79% | -12.63% | PULLBACK_FAILED | DEEP_ADVERSE_MOVE |
| 6368.T | オルガノ | 2026-03-09 | 2026-03-24 | -2.35% | ¥-1,032 | 15 | 9.41% | -9.13% | HARD_STOP | WINNER_TURNED_LOSER |
| 4385.T | メルカリ | 2026-02-25 | 2026-03-04 | -0.23% | ¥-2,986 | 7 | 11.26% | -2.41% | TRAILING_STOP | WINNER_TURNED_LOSER |
| 5101.T | 横浜ゴム | 2026-03-04 | 2026-03-10 | -7.01% | ¥-91,967 | 6 | 3.88% | -13.86% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5471.T | 大同特殊鋼 | 2026-03-09 | 2026-03-23 | -1.66% | ¥-827 | 14 | 9.18% | -3.55% | PULLBACK_FAILED | WINNER_TURNED_LOSER |
| 5803.T | フジクラ | 2026-04-01 | 2026-04-10 | 18.21% | ¥198,317 | 9 | 29.02% | -3.12% | PULLBACK_RESOLVED | FAST_WINNER |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5714.T | ＤＯＷＡホールディングス | 2026-03-18 | 2026-03-23 | -12.70% | ¥-151,270 | 5 | 1.48% | -15.43% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4062.T | イビデン | 2026-03-05 | 2026-03-10 | -5.16% | ¥-69,769 | 5 | 3.76% | -14.81% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5101.T | 横浜ゴム | 2026-03-04 | 2026-03-10 | -7.01% | ¥-91,967 | 6 | 3.88% | -13.86% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6506.T | 安川電機 | 2026-02-19 | 2026-03-05 | -7.28% | ¥-101,307 | 14 | 7.00% | -13.29% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7003.T | 三井Ｅ＆Ｓ | 2026-03-06 | 2026-03-10 | -5.78% | ¥-76,285 | 4 | 0.97% | -13.16% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6323.T | ローツェ | 2026-03-03 | 2026-03-04 | -8.22% | ¥-115,367 | 1 | 0.91% | -12.75% | PULLBACK_FAILED | DEEP_ADVERSE_MOVE |
| 1801.T | 大成建設 | 2026-03-11 | 2026-03-23 | -9.86% | ¥-133,291 | 12 | 2.79% | -12.63% | PULLBACK_FAILED | DEEP_ADVERSE_MOVE |
| 5110.T | 住友ゴム工業 | 2026-03-03 | 2026-03-05 | -7.67% | ¥-101,340 | 2 | 0.25% | -12.48% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6525.T | ＫＯＫＵＳＡＩ ＥＬＥＣＴＲＩＣ | 2026-03-04 | 2026-03-16 | -8.08% | ¥-103,137 | 12 | 7.79% | -11.82% | HARD_STOP | WINNER_TURNED_LOSER |
| 8035.T | 東京エレクトロン | 2026-03-05 | 2026-03-10 | -4.26% | ¥-59,837 | 5 | 1.78% | -11.60% | HARD_STOP | STOP_LOSS_HIT |


### Compact Entry Context For Worst Trades

- `5714.T` 2026-03-18 → 2026-03-23 -12.70%: score: rank=1, action=Trade / feature: return_5d_pct=-4.395822973644947, return_20d_pct=1.3922582006117512, volume_ratio_20d=0.4597549556203263, rsi_14=42.36495844875346, range_position_252d_0_1=0.716625 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=610114797568.0, per=9.827835, pbr=1.3392563, roe_pct=14.482999999999999, operating_margin_pct=8.708
- `1801.T` 2026-03-11 → 2026-03-23 -9.86%: score: rank=2, action=Trade / feature: return_5d_pct=-12.556618017111221, return_20d_pct=-2.1953278919223163, volume_ratio_20d=0.7559751183592597, rsi_14=50.35816618911175, range_position_252d_0_1=0.7779942231477127 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=2206328422400.0, per=13.198053, pbr=2.3271716, operating_margin_pct=9.766
- `6323.T` 2026-03-03 → 2026-03-04 -8.22%: score: rank=1, action=Trade / feature: return_5d_pct=-8.5161662817552, return_20d_pct=-8.410404624277456, volume_ratio_20d=1.2897949708231768, rsi_14=44.80519480519481, range_position_252d_0_1=0.7836914757364452 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=669099687936.0, per=35.284435, pbr=5.137869, roe_pct=13.017999999999999, operating_margin_pct=22.115000000000002
- `6525.T` 2026-03-04 → 2026-03-16 -8.08%: score: rank=6, action=Trade / feature: return_5d_pct=-2.808724305664523, return_20d_pct=-3.2187500000000036, volume_ratio_20d=0.6602304145866795, rsi_14=44.13043478260869, range_position_252d_0_1=0.8302007884844596 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1819397193728.0, per=60.41424, pbr=8.294063, roe_pct=14.49, operating_margin_pct=15.021999999999998
- `5016.T` 2026-05-15 → 2026-05-18 -7.95%: score: rank=3, action=Trade / feature: return_5d_pct=-15.712661106899162, return_20d_pct=-2.8402883985143124, volume_ratio_20d=0.9871628110690178, rsi_14=43.43039772727273, range_position_252d_0_1=0.7287210010411141 / value: value_trap_penalty=0.2 / fund: market_cap_jpy=3550766956544.0, per=34.00142, pbr=5.349444, operating_margin_pct=-23.812
- `5110.T` 2026-03-03 → 2026-03-05 -7.67%: score: rank=2, action=Trade / feature: return_5d_pct=-5.193370165745859, return_20d_pct=3.937007874015741, volume_ratio_20d=1.8931140667257984, rsi_14=45.00000000000001, range_position_252d_0_1=0.8516683184671292 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=530139774976.0, per=10.523844, pbr=0.73050123, roe_pct=8.461001, operating_margin_pct=4.986
- `1605.T` 2026-04-13 → 2026-04-16 -7.51%: score: rank=1, action=Trade / feature: return_5d_pct=-11.29411764705882, return_20d_pct=-3.5357059781344513, volume_ratio_20d=0.5634858692435619, rsi_14=39.756097560975604, range_position_252d_0_1=0.7554479418886199 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=3946796548096.0, per=10.275652, pbr=0.8071259, roe_pct=8.282, operating_margin_pct=48.582
- `4506.T` 2026-01-20 → 2026-01-23 -7.32%: score: rank=1, action=Trade / feature: return_5d_pct=-17.924041931603362, return_20d_pct=5.407194879717503, volume_ratio_20d=2.012274854419339, rsi_14=52.126892573900506, range_position_252d_0_1=0.7690427698574338 / value: value_trap_penalty=0.2 / fund: market_cap_jpy=702721622016.0, per=5.824936, pbr=2.1279428, roe_pct=46.266996999999996, operating_margin_pct=-52.859


## KAESHI / `reversal_snapback`

### Key Metrics

- Trades: **64**, Win rate: **54.69%**, Total PnL: **¥287,117**
- Avg return: **0.45%**, Avg win: **4.96%**, Avg loss: **-4.99%**
- Payoff ratio: **0.9935**, Profit factor: **1.1902**
- Avg MFE: **5.99%**, Avg MAE: **-5.47%**

### Exit Reasons

```json
{
  "SCORE_COLLAPSE": 20,
  "HARD_STOP": 19,
  "MAX_HOLDING_DAYS": 18,
  "SNAPBACK_COMPLETE": 5,
  "TAKE_PROFIT": 1,
  "TRAILING_STOP": 1
}
```

### Failure Patterns

```json
{
  "STOP_LOSS_HIT": 9,
  "DEEP_ADVERSE_MOVE": 6,
  "NORMAL_LOSS": 6,
  "WINNER_TURNED_LOSER": 6,
  "FAST_FAILED_ENTRY": 2
}
```

### Success Patterns

```json
{
  "NORMAL_WIN": 25,
  "FAST_WINNER": 8,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 2
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | -9.68% | ¥-100,527 | 3 | 1.50% | -12.08% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4194.T | ビジョナル | 2026-02-20 | 2026-02-25 | -8.61% | ¥-90,973 | 5 | -0.10% | -10.88% | HARD_STOP | STOP_LOSS_HIT |
| 4592.T | SanBio Company Limited | 2026-05-19 | 2026-05-20 | -8.39% | ¥-87,045 | 1 | 2.56% | -19.91% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4592.T | SanBio Company Limited | 2026-05-22 | 2026-05-26 | -8.27% | ¥-87,500 | 4 | 0.47% | -11.42% | HARD_STOP | STOP_LOSS_HIT |
| 6532.T | ベイカレント | 2026-02-16 | 2026-02-25 | -8.19% | ¥-84,210 | 9 | 6.73% | -12.83% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5110.T | 住友ゴム工業 | 2026-03-05 | 2026-03-10 | -7.56% | ¥-78,642 | 5 | 0.35% | -12.29% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7733.T | オリンパス | 2026-02-18 | 2026-02-25 | -7.55% | ¥-77,325 | 7 | 0.45% | -7.78% | HARD_STOP | STOP_LOSS_HIT |
| 5838.T | 楽天銀行 | 2026-05-26 | 2026-05-28 | -6.94% | ¥-72,569 | 2 | -0.10% | -8.66% | HARD_STOP | STOP_LOSS_HIT |
| 4180.T | Appier Group,Inc. | 2026-02-18 | 2026-02-20 | -6.79% | ¥-69,365 | 2 | 0.66% | -11.40% | HARD_STOP | STOP_LOSS_HIT |
| 7777.T | 3-D Matrix,Ltd. | 2026-03-25 | 2026-03-31 | -6.35% | ¥-64,303 | 6 | 5.60% | -6.94% | MAX_HOLDING_DAYS | WINNER_TURNED_LOSER |
| 6323.T | ローツェ | 2026-03-05 | 2026-03-10 | -6.17% | ¥-65,540 | 5 | 2.34% | -13.64% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7003.T | 三井Ｅ＆Ｓ | 2026-05-19 | 2026-05-21 | -5.38% | ¥-57,047 | 2 | 5.18% | -7.26% | HARD_STOP | WINNER_TURNED_LOSER |
| 3626.T | ＴＩＳ | 2026-02-06 | 2026-02-13 | -5.33% | ¥-56,336 | 7 | 0.57% | -11.55% | MAX_HOLDING_DAYS | FAST_FAILED_ENTRY |
| 6580.T | Writeup Co.,Ltd. | 2026-03-30 | 2026-04-01 | -5.28% | ¥-55,059 | 2 | 6.59% | -11.96% | HARD_STOP | WINNER_TURNED_LOSER |
| 9348.T | ispace,inc. | 2026-04-01 | 2026-04-06 | -4.91% | ¥-49,599 | 5 | 10.90% | -5.26% | HARD_STOP | WINNER_TURNED_LOSER |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4180.T | Appier Group,Inc. | 2026-02-24 | 2026-02-27 | 21.39% | ¥217,190 | 3 | 24.47% | -2.32% | SCORE_COLLAPSE | FAST_WINNER |
| 6920.T | レーザーテック | 2026-05-20 | 2026-05-26 | 17.44% | ¥176,994 | 6 | 20.29% | -4.46% | SCORE_COLLAPSE | FAST_WINNER |
| 4588.T | Oncolys BioPharma Inc. | 2026-05-22 | 2026-05-25 | 16.18% | ¥168,221 | 3 | 27.93% | -9.48% | SCORE_COLLAPSE | FAST_WINNER |
| 5255.T | Monstarlab Inc. | 2026-02-26 | 2026-02-27 | 11.16% | ¥122,739 | 1 | 12.90% | -1.72% | SNAPBACK_COMPLETE | FAST_WINNER |
| 5929.T | 三和ホールディングス | 2026-02-02 | 2026-02-09 | 10.49% | ¥107,346 | 7 | 10.63% | -2.18% | SCORE_COLLAPSE | FAST_WINNER |
| 2501.T | サッポロホールディングス | 2026-05-15 | 2026-05-20 | 8.71% | ¥91,043 | 5 | 10.30% | -3.19% | SCORE_COLLAPSE | FAST_WINNER |
| 4088.T | エア・ウォーター | 2026-05-08 | 2026-05-13 | 6.94% | ¥70,108 | 5 | 9.71% | -1.20% | SNAPBACK_COMPLETE | FAST_WINNER |
| 9501.T | 東京電力ホールディングス | 2026-01-29 | 2026-02-04 | 6.72% | ¥70,127 | 6 | 9.59% | -1.24% | MAX_HOLDING_DAYS | FAST_WINNER |
| 3905.T | Datasection Inc. | 2026-03-06 | 2026-03-11 | 5.32% | ¥55,036 | 5 | 9.43% | -6.52% | SCORE_COLLAPSE | NORMAL_WIN |
| 4483.T | JMDC Inc. | 2026-05-13 | 2026-05-14 | 5.31% | ¥55,267 | 1 | 13.48% | -0.14% | TAKE_PROFIT | NORMAL_WIN |
| 5243.T | note inc. | 2026-02-16 | 2026-02-19 | 5.15% | ¥53,177 | 3 | 9.28% | -4.21% | SCORE_COLLAPSE | NORMAL_WIN |
| 5713.T | 住友金属鉱山 | 2026-03-24 | 2026-03-26 | 5.12% | ¥52,198 | 2 | 6.39% | -2.87% | SCORE_COLLAPSE | NORMAL_WIN |
| 5838.T | 楽天銀行 | 2026-03-05 | 2026-03-10 | 5.06% | ¥53,627 | 5 | 6.76% | -4.67% | SNAPBACK_COMPLETE | NORMAL_WIN |
| 4516.T | 日本新薬 | 2026-05-12 | 2026-05-19 | 4.83% | ¥49,361 | 7 | 7.27% | -0.57% | SCORE_COLLAPSE | NORMAL_WIN |
| 6701.T | 日本電気 | 2026-02-06 | 2026-02-12 | 4.81% | ¥50,579 | 6 | 13.66% | -0.98% | SNAPBACK_COMPLETE | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 9348.T | ispace,inc. | 2026-04-01 | 2026-04-06 | -4.91% | ¥-49,599 | 5 | 10.90% | -5.26% | HARD_STOP | WINNER_TURNED_LOSER |
| 6532.T | ベイカレント | 2026-02-16 | 2026-02-25 | -8.19% | ¥-84,210 | 9 | 6.73% | -12.83% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7777.T | 3-D Matrix,Ltd. | 2026-03-25 | 2026-03-31 | -6.35% | ¥-64,303 | 6 | 5.60% | -6.94% | MAX_HOLDING_DAYS | WINNER_TURNED_LOSER |
| 6580.T | Writeup Co.,Ltd. | 2026-03-30 | 2026-04-01 | -5.28% | ¥-55,059 | 2 | 6.59% | -11.96% | HARD_STOP | WINNER_TURNED_LOSER |
| 4588.T | Oncolys BioPharma Inc. | 2026-05-22 | 2026-05-25 | 16.18% | ¥168,221 | 3 | 27.93% | -9.48% | SCORE_COLLAPSE | FAST_WINNER |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | -9.68% | ¥-100,527 | 3 | 1.50% | -12.08% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4592.T | SanBio Company Limited | 2026-05-19 | 2026-05-20 | -8.39% | ¥-87,045 | 1 | 2.56% | -19.91% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7003.T | 三井Ｅ＆Ｓ | 2026-05-19 | 2026-05-21 | -5.38% | ¥-57,047 | 2 | 5.18% | -7.26% | HARD_STOP | WINNER_TURNED_LOSER |
| 141A.T | TRIAL Holdings,Inc. | 2026-05-19 | 2026-05-25 | 1.56% | ¥16,487 | 6 | 10.81% | -2.61% | TRAILING_STOP | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 6701.T | 日本電気 | 2026-02-06 | 2026-02-12 | 4.81% | ¥50,579 | 6 | 13.66% | -0.98% | SNAPBACK_COMPLETE | NORMAL_WIN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4592.T | SanBio Company Limited | 2026-05-19 | 2026-05-20 | -8.39% | ¥-87,045 | 1 | 2.56% | -19.91% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6323.T | ローツェ | 2026-03-05 | 2026-03-10 | -6.17% | ¥-65,540 | 5 | 2.34% | -13.64% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6532.T | ベイカレント | 2026-02-16 | 2026-02-25 | -8.19% | ¥-84,210 | 9 | 6.73% | -12.83% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5110.T | 住友ゴム工業 | 2026-03-05 | 2026-03-10 | -7.56% | ¥-78,642 | 5 | 0.35% | -12.29% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | -9.68% | ¥-100,527 | 3 | 1.50% | -12.08% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 247A.T | Ai ROBOTICS INC. | 2026-05-18 | 2026-05-19 | -4.52% | ¥-47,993 | 1 | 0.33% | -12.01% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6580.T | Writeup Co.,Ltd. | 2026-03-30 | 2026-04-01 | -5.28% | ¥-55,059 | 2 | 6.59% | -11.96% | HARD_STOP | WINNER_TURNED_LOSER |
| 3626.T | ＴＩＳ | 2026-02-06 | 2026-02-13 | -5.33% | ¥-56,336 | 7 | 0.57% | -11.55% | MAX_HOLDING_DAYS | FAST_FAILED_ENTRY |
| 4592.T | SanBio Company Limited | 2026-05-22 | 2026-05-26 | -8.27% | ¥-87,500 | 4 | 0.47% | -11.42% | HARD_STOP | STOP_LOSS_HIT |
| 4180.T | Appier Group,Inc. | 2026-02-18 | 2026-02-20 | -6.79% | ¥-69,365 | 2 | 0.66% | -11.40% | HARD_STOP | STOP_LOSS_HIT |


### Compact Entry Context For Worst Trades

- `4307.T` 2026-02-02 → 2026-02-05 -9.68%: score: rank=1, action=Trade / feature: return_5d_pct=-20.725126475548063, return_20d_pct=-21.532298447671504, volume_ratio_20d=5.545538564332412, rsi_14=9.214830970556164, range_position_252d_0_1=0.056854410201912856 / value: value_trap_penalty=0.2 / fund: market_cap_jpy=3077084807168.0, per=201.23967, pbr=7.091607, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `4194.T` 2026-02-20 → 2026-02-25 -8.61%: score: rank=1, action=Trade / feature: return_5d_pct=-16.296918095694924, return_20d_pct=-24.303220908795144, volume_ratio_20d=2.8768618387262457, rsi_14=24.290220820189276, range_position_252d_0_1=0.05419399378667587 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=332936380416.0, per=19.207834, pbr=4.3245783, roe_pct=26.342, operating_margin_pct=24.484
- `4592.T` 2026-05-19 → 2026-05-20 -8.39%: score: rank=4, action=Trade / feature: return_5d_pct=-24.966740576496672, return_20d_pct=-13.364055299539167, volume_ratio_20d=1.0145138659940043, rsi_14=29.85190958690569, range_position_252d_0_1=0.07895791583166333 / value: value_trap_penalty=0.35 / fund: market_cap_jpy=99970965504.0, per=-31.389364, pbr=7.3472896, roe_pct=-50.003, operating_margin_pct=0.0
- `4592.T` 2026-05-22 → 2026-05-26 -8.27%: score: rank=1, action=Trade / feature: return_5d_pct=-16.547553600879606, return_20d_pct=-27.403156384505024, volume_ratio_20d=0.7882147467537398, rsi_14=33.0532212885154, range_position_252d_0_1=0.050326546292739145 / value: value_trap_penalty=0.35 / fund: market_cap_jpy=99970965504.0, per=-31.389364, pbr=7.3472896, roe_pct=-50.003, operating_margin_pct=0.0
- `6532.T` 2026-02-16 → 2026-02-25 -8.19%: score: rank=2, action=Trade / feature: return_5d_pct=-15.428571428571425, return_20d_pct=-40.41371650701097, volume_ratio_20d=2.081779980605538, rsi_14=19.63001027749229, range_position_252d_0_1=0.014220939818631493 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=925943988224.0, per=24.628033, pbr=7.967812, roe_pct=35.793, operating_margin_pct=37.120998
- `5110.T` 2026-03-05 → 2026-03-10 -7.56%: score: rank=3, action=Trade / feature: return_5d_pct=-19.12902645312219, return_20d_pct=-9.083552498482705, volume_ratio_20d=1.1584043001003788, rsi_14=26.738934056007224, range_position_252d_0_1=0.6356128179715891 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=530139774976.0, per=10.523844, pbr=0.73050123, roe_pct=8.461001, operating_margin_pct=4.986
- `7733.T` 2026-02-18 → 2026-02-25 -7.55%: score: rank=2, action=Trade / feature: return_5d_pct=-19.396440546814553, return_20d_pct=-21.620265864058187, volume_ratio_20d=2.21158522773657, rsi_14=27.69701606732977, range_position_252d_0_1=0.13153549807374793 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1996849283072.0, per=29.612997, pbr=2.459053, roe_pct=8.719000000000001, operating_margin_pct=16.857
- `5838.T` 2026-05-26 → 2026-05-28 -6.94%: score: rank=1, action=Trade / feature: return_5d_pct=-22.799575821845174, return_20d_pct=-20.7588244440989, volume_ratio_20d=1.7431335151556568, rsi_14=33.497133497133504, range_position_252d_0_1=0.06985456148082855 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=763478409216.0, per=10.459001, pbr=2.0518374, roe_pct=20.291999999999998, operating_margin_pct=55.230000000000004


## HIZUMI / `value_mispricing`

### Key Metrics

- Trades: **49**, Win rate: **59.18%**, Total PnL: **¥-598,948**
- Avg return: **-0.61%**, Avg win: **3.33%**, Avg loss: **-6.31%**
- Payoff ratio: **0.5272**, Profit factor: **0.7231**
- Avg MFE: **3.89%**, Avg MAE: **-4.09%**

### Exit Reasons

```json
{
  "MISPRICING_RESOLVED": 34,
  "HARD_STOP": 12,
  "MAX_HOLDING_DAYS": 2,
  "TRAILING_STOP": 1
}
```

### Failure Patterns

```json
{
  "STOP_LOSS_HIT": 10,
  "NORMAL_LOSS": 6,
  "DEEP_ADVERSE_MOVE": 2,
  "SLOW_BLEED_LOSER": 1,
  "WINNER_TURNED_LOSER": 1
}
```

### Success Patterns

```json
{
  "NORMAL_WIN": 26,
  "FAST_WINNER": 3
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5838.T | 楽天銀行 | 2026-02-25 | 2026-02-27 | -20.41% | ¥-399,489 | 2 | 0.44% | -25.11% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 9022.T | 東海旅客鉄道 | 2026-04-20 | 2026-05-01 | -11.71% | ¥-213,538 | 11 | 2.33% | -14.84% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4503.T | アステラス製薬 | 2026-04-27 | 2026-05-01 | -9.48% | ¥-175,124 | 4 | 0.48% | -10.67% | HARD_STOP | STOP_LOSS_HIT |
| 1605.T | ＩＮＰＥＸ | 2026-05-14 | 2026-05-26 | -9.31% | ¥-165,450 | 12 | 1.12% | -9.82% | HARD_STOP | STOP_LOSS_HIT |
| 3288.T | オープンハウスグループ | 2026-03-05 | 2026-03-13 | -8.64% | ¥-161,058 | 8 | 1.00% | -8.55% | HARD_STOP | STOP_LOSS_HIT |
| 5929.T | 三和ホールディングス | 2026-05-11 | 2026-05-19 | -8.56% | ¥-140,400 | 8 | 2.94% | -8.80% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-02-19 | 2026-02-25 | -7.88% | ¥-155,641 | 6 | 1.29% | -8.57% | HARD_STOP | STOP_LOSS_HIT |
| 1925.T | 大和ハウス工業 | 2026-03-03 | 2026-03-24 | -7.70% | ¥-144,440 | 21 | 0.19% | -8.37% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-05-07 | 2026-05-27 | -7.42% | ¥-132,430 | 20 | 0.25% | -7.79% | HARD_STOP | STOP_LOSS_HIT |
| 3635.T | コーエーテクモホールディングス | 2026-03-18 | 2026-03-26 | -7.25% | ¥-134,086 | 8 | 0.20% | -9.00% | HARD_STOP | STOP_LOSS_HIT |
| 3288.T | オープンハウスグループ | 2026-04-06 | 2026-04-17 | -6.42% | ¥-120,948 | 11 | 2.57% | -8.15% | HARD_STOP | STOP_LOSS_HIT |
| 1605.T | ＩＮＰＥＸ | 2026-04-10 | 2026-04-17 | -6.07% | ¥-775 | 7 | 3.22% | -8.07% | HARD_STOP | STOP_LOSS_HIT |
| 1928.T | 積水ハウス | 2026-03-26 | 2026-05-01 | -3.90% | ¥-73,106 | 36 | 4.51% | -4.82% | MAX_HOLDING_DAYS | SLOW_BLEED_LOSER |
| 8725.T | ＭＳ＆ＡＤインシュアランスグループホールディングス | 2026-04-08 | 2026-04-09 | -2.36% | ¥-1,606 | 1 | -0.08% | -3.72% | MISPRICING_RESOLVED | NORMAL_LOSS |
| 5830.T | いよぎんホールディングス | 2026-02-27 | 2026-03-02 | -2.06% | ¥-39,081 | 3 | 3.40% | -3.12% | MISPRICING_RESOLVED | NORMAL_LOSS |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4503.T | アステラス製薬 | 2026-03-23 | 2026-03-25 | 8.17% | ¥151,569 | 2 | 8.53% | -1.12% | MISPRICING_RESOLVED | FAST_WINNER |
| 1925.T | 大和ハウス工業 | 2026-01-07 | 2026-02-09 | 7.91% | ¥144,671 | 33 | 8.25% | -2.17% | MISPRICING_RESOLVED | NORMAL_WIN |
| 4578.T | 大塚ホールディングス | 2026-03-06 | 2026-03-12 | 7.64% | ¥140,661 | 6 | 11.26% | -3.54% | MISPRICING_RESOLVED | FAST_WINNER |
| 1605.T | ＩＮＰＥＸ | 2026-01-08 | 2026-01-14 | 6.96% | ¥126,861 | 6 | 8.16% | -0.10% | MISPRICING_RESOLVED | FAST_WINNER |
| 8725.T | ＭＳ＆ＡＤインシュアランスグループホールディングス | 2026-04-22 | 2026-05-13 | 6.51% | ¥525 | 21 | 9.47% | -3.65% | MISPRICING_RESOLVED | NORMAL_WIN |
| 4503.T | アステラス製薬 | 2026-01-29 | 2026-02-04 | 5.76% | ¥5,210 | 6 | 7.43% | -1.10% | MISPRICING_RESOLVED | NORMAL_WIN |
| 5334.T | 日本特殊陶業 | 2026-03-31 | 2026-04-02 | 5.68% | ¥104,998 | 2 | 6.99% | -0.54% | MISPRICING_RESOLVED | NORMAL_WIN |
| 3003.T | ヒューリック | 2026-01-26 | 2026-02-02 | 5.47% | ¥95,223 | 7 | 6.31% | -3.19% | MISPRICING_RESOLVED | NORMAL_WIN |
| 8630.T | ＳＯＭＰＯホールディングス | 2026-01-28 | 2026-02-04 | 5.27% | ¥99,031 | 7 | 8.03% | -1.00% | MISPRICING_RESOLVED | NORMAL_WIN |
| 4578.T | 大塚ホールディングス | 2026-01-20 | 2026-01-26 | 5.14% | ¥96,122 | 6 | 7.69% | -1.21% | MISPRICING_RESOLVED | NORMAL_WIN |
| 1605.T | ＩＮＰＥＸ | 2026-02-16 | 2026-02-20 | 4.78% | ¥93,857 | 4 | 5.39% | -1.37% | MISPRICING_RESOLVED | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-09 | 2026-01-13 | 4.00% | ¥73,008 | 4 | 5.36% | -0.24% | MISPRICING_RESOLVED | NORMAL_WIN |
| 4503.T | アステラス製薬 | 2026-03-04 | 2026-03-12 | 3.79% | ¥71,043 | 8 | 6.96% | -1.17% | MISPRICING_RESOLVED | NORMAL_WIN |
| 8604.T | 野村ホールディングス | 2026-02-05 | 2026-02-10 | 3.77% | ¥72,787 | 5 | 4.95% | -3.46% | MISPRICING_RESOLVED | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-27 | 2026-02-05 | 3.62% | ¥68,127 | 9 | 4.27% | -4.27% | MISPRICING_RESOLVED | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5838.T | 楽天銀行 | 2026-02-25 | 2026-02-27 | -20.41% | ¥-399,489 | 2 | 0.44% | -25.11% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 9022.T | 東海旅客鉄道 | 2026-04-20 | 2026-05-01 | -11.71% | ¥-213,538 | 11 | 2.33% | -14.84% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5929.T | 三和ホールディングス | 2026-05-11 | 2026-05-19 | -8.56% | ¥-140,400 | 8 | 2.94% | -8.80% | HARD_STOP | STOP_LOSS_HIT |
| 1605.T | ＩＮＰＥＸ | 2026-05-14 | 2026-05-26 | -9.31% | ¥-165,450 | 12 | 1.12% | -9.82% | HARD_STOP | STOP_LOSS_HIT |
| 4503.T | アステラス製薬 | 2026-04-27 | 2026-05-01 | -9.48% | ¥-175,124 | 4 | 0.48% | -10.67% | HARD_STOP | STOP_LOSS_HIT |
| 3288.T | オープンハウスグループ | 2026-03-05 | 2026-03-13 | -8.64% | ¥-161,058 | 8 | 1.00% | -8.55% | HARD_STOP | STOP_LOSS_HIT |
| 1605.T | ＩＮＰＥＸ | 2026-04-10 | 2026-04-17 | -6.07% | ¥-775 | 7 | 3.22% | -8.07% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-02-19 | 2026-02-25 | -7.88% | ¥-155,641 | 6 | 1.29% | -8.57% | HARD_STOP | STOP_LOSS_HIT |
| 5105.T | ＴＯＹＯ ＴＩＲＥ | 2026-04-07 | 2026-05-13 | -1.92% | ¥-36,209 | 36 | 7.10% | -3.10% | MAX_HOLDING_DAYS | WINNER_TURNED_LOSER |
| 3288.T | オープンハウスグループ | 2026-04-06 | 2026-04-17 | -6.42% | ¥-120,948 | 11 | 2.57% | -8.15% | HARD_STOP | STOP_LOSS_HIT |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5838.T | 楽天銀行 | 2026-02-25 | 2026-02-27 | -20.41% | ¥-399,489 | 2 | 0.44% | -25.11% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 9022.T | 東海旅客鉄道 | 2026-04-20 | 2026-05-01 | -11.71% | ¥-213,538 | 11 | 2.33% | -14.84% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4503.T | アステラス製薬 | 2026-04-27 | 2026-05-01 | -9.48% | ¥-175,124 | 4 | 0.48% | -10.67% | HARD_STOP | STOP_LOSS_HIT |
| 1605.T | ＩＮＰＥＸ | 2026-05-14 | 2026-05-26 | -9.31% | ¥-165,450 | 12 | 1.12% | -9.82% | HARD_STOP | STOP_LOSS_HIT |
| 3635.T | コーエーテクモホールディングス | 2026-03-18 | 2026-03-26 | -7.25% | ¥-134,086 | 8 | 0.20% | -9.00% | HARD_STOP | STOP_LOSS_HIT |
| 5929.T | 三和ホールディングス | 2026-05-11 | 2026-05-19 | -8.56% | ¥-140,400 | 8 | 2.94% | -8.80% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-02-19 | 2026-02-25 | -7.88% | ¥-155,641 | 6 | 1.29% | -8.57% | HARD_STOP | STOP_LOSS_HIT |
| 3288.T | オープンハウスグループ | 2026-03-05 | 2026-03-13 | -8.64% | ¥-161,058 | 8 | 1.00% | -8.55% | HARD_STOP | STOP_LOSS_HIT |
| 1925.T | 大和ハウス工業 | 2026-03-03 | 2026-03-24 | -7.70% | ¥-144,440 | 21 | 0.19% | -8.37% | HARD_STOP | STOP_LOSS_HIT |
| 3288.T | オープンハウスグループ | 2026-04-06 | 2026-04-17 | -6.42% | ¥-120,948 | 11 | 2.57% | -8.15% | HARD_STOP | STOP_LOSS_HIT |


### Compact Entry Context For Worst Trades

- `5838.T` 2026-02-25 → 2026-02-27 -20.41%: score: rank=10, action=Trade / feature: return_5d_pct=-4.004130335016065, return_20d_pct=17.29987382587972, volume_ratio_20d=0.9996242014280345, rsi_14=65.53282588011419, range_position_252d_0_1=0.812881623005712 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=763478409216.0, per=10.459001, pbr=2.0518374, roe_pct=20.291999999999998, operating_margin_pct=55.230000000000004
- `9022.T` 2026-04-20 → 2026-05-01 -11.71%: score: rank=4, action=Trade / feature: return_5d_pct=-0.023832221163011535, return_20d_pct=-0.8977084809827507, volume_ratio_20d=0.7560055112921584, rsi_14=57.42444152431012, range_position_252d_0_1=0.68994140625 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=3246912700416.0, per=5.953757, pbr=0.64059347, roe_pct=11.4700004, operating_margin_pct=27.111
- `4503.T` 2026-04-27 → 2026-05-01 -9.48%: score: rank=2, action=Trade / feature: return_5d_pct=-3.3483454082631647, return_20d_pct=-5.422494730791339, volume_ratio_20d=0.8146249131466086, rsi_14=32.046332046332054, range_position_252d_0_1=0.8225231646471846 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=3831106109440.0, per=13.174593, pbr=2.0945952, roe_pct=17.438000000000002, operating_margin_pct=16.509001
- `1605.T` 2026-05-14 → 2026-05-26 -9.31%: score: rank=2, action=Trade / feature: return_5d_pct=-4.565322972316654, return_20d_pct=-7.092198581560282, volume_ratio_20d=0.7672160632757515, rsi_14=47.94929157345265, range_position_252d_0_1=0.6756329113924051 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=3946796548096.0, per=10.275652, pbr=0.8071259, roe_pct=8.282, operating_margin_pct=48.582
- `3288.T` 2026-03-05 → 2026-03-13 -8.64%: score: rank=3, action=Trade / feature: return_5d_pct=-5.736981465136804, return_20d_pct=19.824974755974424, volume_ratio_20d=1.1942500067047497, rsi_14=63.926380368098165, range_position_252d_0_1=0.8314094775212637 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=928879017984.0, per=8.51539, pbr=1.597236, roe_pct=20.129, operating_margin_pct=12.274000000000001
- `5929.T` 2026-05-11 → 2026-05-19 -8.56%: score: rank=18, action=Trade / feature: return_5d_pct=1.3070077864293594, return_20d_pct=2.8805422197119457, volume_ratio_20d=1.1909259571597235, rsi_14=45.02712477396022, range_position_252d_0_1=0.112668743509865 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=766288527360.0, per=12.9748745, pbr=2.2053187, roe_pct=17.823, operating_margin_pct=15.279001000000001
- `8473.T` 2026-02-19 → 2026-02-25 -7.88%: score: rank=4, action=Trade / feature: return_5d_pct=-5.104022191400837, return_20d_pct=-4.62782269305827, volume_ratio_20d=0.602421535653823, rsi_14=46.49021864211737, range_position_252d_0_1=0.8085197934595525 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1881560842240.0, per=4.6614037, pbr=1.0482572, roe_pct=20.613999999999997, operating_margin_pct=28.927000000000003
- `1925.T` 2026-03-03 → 2026-03-24 -7.70%: score: rank=7, action=Trade / feature: return_5d_pct=1.1604714415231143, return_20d_pct=7.578094870806007, volume_ratio_20d=0.8204646324959074, rsi_14=52.95480880648899, range_position_252d_0_1=0.8130686517783292 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=2621696114688.0, per=7.472857, pbr=0.90505034, roe_pct=12.528, operating_margin_pct=16.343


## Prompt Suggestion

```text
このTrade Diagnosticsをもとに、各Agentの勝因・敗因を定量的に分析してください。特に、勝率と損益の非対称性、MFE/MAE、exit reason、entry context、fundamental/value contextを見て、Agent別に改善すべき売買ルールを優先順位付きで提案してください。
```
