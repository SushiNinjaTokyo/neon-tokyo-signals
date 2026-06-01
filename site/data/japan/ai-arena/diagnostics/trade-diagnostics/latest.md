# Neon Tokyo AI Arena Trade Diagnostics

Generated: `2026-06-01T16:22:49+00:00`
Run ID: `arena_jp_rebuild_2026_v017`

> Purpose: paste this Markdown into ChatGPT and ask for detailed agent-by-agent win/loss diagnosis and rule-improvement ideas.

## Dataset Summary

- Closed trades: **379**
- Open positions: **16**
- Agents with closed trades: **7**
- Exported compact trade rows in JSON: **379**
- Equity curve rows: **686**

## Agent Summary

| Agent | Trades | Win | Avg Ret | Avg Win | Avg Loss | Payoff | PF | PnL | Avg MFE | Avg MAE | Top Failure Patterns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KYOU / `daily_striker` | 79 | 48.10% | 1.15% | 5.00% | -2.43% | 2.0621 | 1.7407 | ¥1,103,700 | 5.37% | -3.51% | NORMAL_LOSS:30, FAST_FAILED_ENTRY:4, DEEP_ADVERSE_MOVE:3, WINNER_TURNED_LOSER:3 |
| NAGARE / `weekly_sage` | 36 | 38.89% | 4.92% | 24.91% | -7.80% | 3.1923 | 2.4006 | ¥2,689,727 | 15.32% | -7.97% | NORMAL_LOSS:9, DEEP_ADVERSE_MOVE:8, WINNER_TURNED_LOSER:5 |
| MAMORU / `risk_sentinel` | 92 | 48.91% | 2.02% | 7.44% | -3.17% | 2.3451 | 2.2325 | ¥1,380,806 | 6.65% | -3.58% | NORMAL_LOSS:24, STOP_LOSS_HIT:17, WINNER_TURNED_LOSER:5, DEEP_ADVERSE_MOVE:1 |
| SAGURI / `discovery_scout` | 25 | 40.00% | -0.09% | 7.85% | -5.39% | 1.4568 | 0.9277 | ¥-67,782 | 9.11% | -5.57% | DEEP_ADVERSE_MOVE:4, NORMAL_LOSS:4, WINNER_TURNED_LOSER:4, FAST_FAILED_ENTRY:3 |
| MATSU / `contrarian_monk` | 74 | 47.30% | 2.50% | 10.49% | -4.68% | 2.2426 | 1.8252 | ¥1,835,126 | 8.33% | -5.78% | STOP_LOSS_HIT:14, NORMAL_LOSS:9, DEEP_ADVERSE_MOVE:8, WINNER_TURNED_LOSER:6 |
| KAESHI / `reversal_snapback` | 66 | 46.97% | 0.74% | 7.07% | -4.86% | 1.4542 | 1.2506 | ¥460,933 | 6.30% | -5.18% | STOP_LOSS_HIT:20, NORMAL_LOSS:8, DEEP_ADVERSE_MOVE:4, WINNER_TURNED_LOSER:3 |
| HIZUMI / `value_mispricing` | 7 | 28.57% | -3.51% | 0.54% | -5.13% | 0.1056 | 0.0501 | ¥-368,394 | 2.03% | -5.17% | STOP_LOSS_HIT:4, NORMAL_LOSS:1 |

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

- Trades: **36**, Win rate: **38.89%**, Total PnL: **¥2,689,727**
- Avg return: **4.92%**, Avg win: **24.91%**, Avg loss: **-7.80%**
- Payoff ratio: **3.1923**, Profit factor: **2.4006**
- Avg MFE: **15.32%**, Avg MAE: **-7.97%**

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

### Failure Patterns

```json
{
  "NORMAL_LOSS": 9,
  "DEEP_ADVERSE_MOVE": 8,
  "WINNER_TURNED_LOSER": 5
}
```

### Success Patterns

```json
{
  "PATIENT_TREND_WINNER": 9,
  "NORMAL_WIN": 3,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 2
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6305.T | 日立建機 | 2026-02-17 | 2026-03-10 | -11.81% | ¥-2,338 | 21 | 9.44% | -17.60% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6471.T | 日本精工 | 2026-02-26 | 2026-03-06 | -11.06% | ¥-250,124 | 8 | 3.18% | -10.97% | EARLY_FAIL | NORMAL_LOSS |
| 3563.T | ＦＯＯＤ ＆ ＬＩＦＥ ＣＯＭＰＡＮＩＥＳ | 2026-03-05 | 2026-03-10 | -11.01% | ¥-77,561 | 5 | 3.73% | -16.03% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1860.T | 戸田建設 | 2026-03-05 | 2026-03-13 | -10.42% | ¥-74,263 | 8 | 1.39% | -11.70% | EARLY_FAIL | NORMAL_LOSS |
| 4061.T | デンカ | 2026-03-12 | 2026-03-23 | -9.39% | ¥-193,199 | 11 | 0.41% | -11.27% | EARLY_FAIL | NORMAL_LOSS |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-03-11 | 2026-03-25 | -9.18% | ¥-131,433 | 14 | 5.89% | -14.48% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5019.T | 出光興産 | 2026-04-02 | 2026-04-21 | -9.09% | ¥-39,892 | 19 | 5.09% | -11.23% | TREND_BREAK | WINNER_TURNED_LOSER |
| 1801.T | 大成建設 | 2026-02-26 | 2026-03-10 | -9.00% | ¥-201,936 | 12 | 8.73% | -13.59% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6370.T | 栗田工業 | 2026-02-26 | 2026-03-10 | -8.61% | ¥-194,266 | 12 | 3.18% | -13.87% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1605.T | ＩＮＰＥＸ | 2026-03-16 | 2026-04-16 | -8.48% | ¥-17,925 | 31 | 12.50% | -10.36% | TREND_BREAK | WINNER_TURNED_LOSER |
| 6674.T | ジーエス・ユアサ コーポレーション | 2026-04-16 | 2026-04-30 | -8.33% | ¥-103,720 | 14 | 3.31% | -8.25% | EARLY_FAIL | NORMAL_LOSS |
| 6301.T | 小松製作所 | 2026-02-17 | 2026-03-04 | -8.20% | ¥-1,280 | 15 | 0.00% | -11.23% | EARLY_FAIL | NORMAL_LOSS |
| 9513.T | 電源開発 | 2026-04-02 | 2026-04-14 | -7.91% | ¥-34,539 | 12 | 3.36% | -8.32% | EARLY_FAIL | NORMAL_LOSS |
| 6113.T | アマダ | 2026-02-16 | 2026-03-10 | -7.79% | ¥-168,725 | 22 | 7.51% | -12.09% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5831.T | しずおかフィナンシャルグループ | 2026-02-16 | 2026-03-05 | -7.78% | ¥-168,618 | 17 | 3.86% | -12.78% | HARD_STOP | DEEP_ADVERSE_MOVE |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6981.T | 村田製作所 | 2026-04-21 | 2026-05-15 | 35.36% | ¥384,223 | 24 | 37.86% | -1.53% | TAKE_PROFIT | NORMAL_WIN |
| 3436.T | ＳＵＭＣＯ | 2026-04-16 | 2026-05-08 | 33.80% | ¥421,782 | 22 | 61.95% | -10.38% | TAKE_PROFIT | NORMAL_WIN |
| 5711.T | 三菱マテリアル | 2026-01-07 | 2026-02-13 | 33.34% | ¥610,393 | 37 | 40.51% | -1.87% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 5714.T | ＤＯＷＡホールディングス | 2026-01-07 | 2026-02-25 | 31.93% | ¥582,563 | 49 | 32.62% | -1.47% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 7189.T | 西日本フィナンシャルホールディングス | 2026-01-06 | 2026-02-13 | 31.71% | ¥576,795 | 38 | 33.94% | -0.52% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 6471.T | 日本精工 | 2026-01-08 | 2026-02-25 | 30.67% | ¥118,991 | 48 | 32.31% | -0.97% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 6754.T | アンリツ | 2026-04-21 | 2026-05-26 | 30.66% | ¥333,818 | 35 | 34.91% | -2.02% | TAKE_PROFIT | PATIENT_TREND_WINNER |
| 5333.T | 日本碍子 | 2026-01-08 | 2026-02-25 | 27.81% | ¥107,251 | 48 | 29.51% | -1.67% | MAX_HOLDING_DAYS | PATIENT_TREND_WINNER |
| 6976.T | 太陽誘電 | 2026-04-16 | 2026-05-20 | 25.97% | ¥323,712 | 34 | 34.98% | -1.01% | TAKE_PROFIT | NORMAL_WIN |
| 6963.T | ローム | 2026-03-25 | 2026-05-12 | 24.83% | ¥334,760 | 48 | 25.23% | -6.92% | MAX_HOLDING_DAYS | PATIENT_TREND_WINNER |
| 1801.T | 大成建設 | 2026-01-06 | 2026-02-24 | 23.73% | ¥431,353 | 49 | 24.47% | -3.83% | MAX_HOLDING_DAYS | PATIENT_TREND_WINNER |
| 6752.T | パナソニック ホールディングス | 2026-03-12 | 2026-04-28 | 17.61% | ¥362,126 | 47 | 18.34% | -7.50% | MAX_HOLDING_DAYS | PATIENT_TREND_WINNER |
| 6954.T | ファナック | 2026-01-06 | 2026-02-24 | 0.74% | ¥13,390 | 49 | 8.55% | -5.86% | MAX_HOLDING_DAYS | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 9104.T | 商船三井 | 2026-03-11 | 2026-04-21 | 0.62% | ¥8,970 | 41 | 20.95% | -0.79% | TRAILING_STOP | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 8031.T | 三井物産 | 2026-03-11 | 2026-04-20 | -2.19% | ¥-31,397 | 40 | 10.77% | -7.14% | TREND_BREAK | WINNER_TURNED_LOSER |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 3436.T | ＳＵＭＣＯ | 2026-04-16 | 2026-05-08 | 33.80% | ¥421,782 | 22 | 61.95% | -10.38% | TAKE_PROFIT | NORMAL_WIN |
| 6305.T | 日立建機 | 2026-02-17 | 2026-03-10 | -11.81% | ¥-2,338 | 21 | 9.44% | -17.60% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1605.T | ＩＮＰＥＸ | 2026-03-16 | 2026-04-16 | -8.48% | ¥-17,925 | 31 | 12.50% | -10.36% | TREND_BREAK | WINNER_TURNED_LOSER |
| 9104.T | 商船三井 | 2026-03-11 | 2026-04-21 | 0.62% | ¥8,970 | 41 | 20.95% | -0.79% | TRAILING_STOP | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 1801.T | 大成建設 | 2026-02-26 | 2026-03-10 | -9.00% | ¥-201,936 | 12 | 8.73% | -13.59% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 2579.T | コカ・コーラ ボトラーズジャパンホールディングス | 2026-02-17 | 2026-03-24 | -4.74% | ¥-902 | 35 | 11.58% | -5.48% | TREND_BREAK | WINNER_TURNED_LOSER |
| 6113.T | アマダ | 2026-02-16 | 2026-03-10 | -7.79% | ¥-168,725 | 22 | 7.51% | -12.09% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-03-11 | 2026-03-25 | -9.18% | ¥-131,433 | 14 | 5.89% | -14.48% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 8058.T | 三菱商事 | 2026-03-12 | 2026-04-16 | -3.40% | ¥-69,774 | 35 | 11.59% | -4.03% | TREND_BREAK | WINNER_TURNED_LOSER |
| 3563.T | ＦＯＯＤ ＆ ＬＩＦＥ ＣＯＭＰＡＮＩＥＳ | 2026-03-05 | 2026-03-10 | -11.01% | ¥-77,561 | 5 | 3.73% | -16.03% | HARD_STOP | DEEP_ADVERSE_MOVE |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6305.T | 日立建機 | 2026-02-17 | 2026-03-10 | -11.81% | ¥-2,338 | 21 | 9.44% | -17.60% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 3563.T | ＦＯＯＤ ＆ ＬＩＦＥ ＣＯＭＰＡＮＩＥＳ | 2026-03-05 | 2026-03-10 | -11.01% | ¥-77,561 | 5 | 3.73% | -16.03% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-03-11 | 2026-03-25 | -9.18% | ¥-131,433 | 14 | 5.89% | -14.48% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6370.T | 栗田工業 | 2026-02-26 | 2026-03-10 | -8.61% | ¥-194,266 | 12 | 3.18% | -13.87% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1801.T | 大成建設 | 2026-02-26 | 2026-03-10 | -9.00% | ¥-201,936 | 12 | 8.73% | -13.59% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5831.T | しずおかフィナンシャルグループ | 2026-02-16 | 2026-03-05 | -7.78% | ¥-168,618 | 17 | 3.86% | -12.78% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1942.T | 関電工 | 2026-03-05 | 2026-03-10 | -7.12% | ¥-50,620 | 5 | 1.39% | -12.51% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6113.T | アマダ | 2026-02-16 | 2026-03-10 | -7.79% | ¥-168,725 | 22 | 7.51% | -12.09% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1860.T | 戸田建設 | 2026-03-05 | 2026-03-13 | -10.42% | ¥-74,263 | 8 | 1.39% | -11.70% | EARLY_FAIL | NORMAL_LOSS |
| 4061.T | デンカ | 2026-03-12 | 2026-03-23 | -9.39% | ¥-193,199 | 11 | 0.41% | -11.27% | EARLY_FAIL | NORMAL_LOSS |


### Compact Entry Context For Worst Trades

- `6305.T` 2026-02-17 → 2026-03-10 -11.81%: score: rank=4, action=Trade / feature: return_5d_pct=7.55055446836268, return_20d_pct=21.656520937096467, volume_ratio_20d=0.7333831275736258, rsi_14=91.7755991285403, range_position_252d_0_1=0.9633342881695789 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1083039350784.0, per=14.792108, pbr=1.2031553, roe_pct=9.119, operating_margin_pct=9.391
- `6471.T` 2026-02-26 → 2026-03-06 -11.06%: score: rank=1, action=Trade / feature: return_5d_pct=4.461538461538472, return_20d_pct=24.873563218390803, volume_ratio_20d=1.031296417365805, rsi_14=87.7643504531722, range_position_252d_0_1=0.9957467493012516 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=585717252096.0, per=25.69221, pbr=0.87163514, roe_pct=3.5709999999999997, operating_margin_pct=4.281
- `3563.T` 2026-03-05 → 2026-03-10 -11.01%: score: rank=2, action=Trade / feature: return_5d_pct=2.2297925054196366, return_20d_pct=19.21271217045866, volume_ratio_20d=1.3231653373749288, rsi_14=64.84490398818316, range_position_252d_0_1=0.9453457237360214 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1195190386688.0, per=41.87731, pbr=10.423231, roe_pct=29.883, operating_margin_pct=11.113000000000001
- `1860.T` 2026-03-05 → 2026-03-13 -10.42%: score: rank=4, action=Trade / feature: return_5d_pct=1.3937282229965264, return_20d_pct=18.819599109131403, volume_ratio_20d=1.8044194981063186, rsi_14=56.8075117370892, range_position_252d_0_1=0.9656042192157762 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=470111584256.0, per=12.882291, pbr=1.2145845, roe_pct=9.923001, operating_margin_pct=5.298
- `4061.T` 2026-03-12 → 2026-03-23 -9.39%: score: rank=6, action=Trade / feature: return_5d_pct=8.635947512969189, return_20d_pct=21.274058933742126, volume_ratio_20d=0.75237114134489, rsi_14=60.825958702064895, range_position_252d_0_1=0.905284147557328 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=370658770944.0, per=23.599142, pbr=1.1929642, roe_pct=3.4779999999999998, operating_margin_pct=8.5880004
- `7685.T` 2026-03-11 → 2026-03-25 -9.18%: score: rank=4, action=Trade / feature: return_5d_pct=20.46678635547576, return_20d_pct=35.555555555555564, volume_ratio_20d=1.1572475364271877, rsi_14=68.75, range_position_252d_0_1=0.9911445649767545 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=242373541888.0, per=45.26559, pbr=5.0126595, roe_pct=39.259, operating_margin_pct=9.9750005
- `5019.T` 2026-04-02 → 2026-04-21 -9.09%: score: rank=2, action=Trade / feature: return_5d_pct=7.188444743029887, return_20d_pct=8.389945652173903, volume_ratio_20d=1.1477653069277876, rsi_14=66.0164271047228, range_position_252d_0_1=0.996870697208662 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1616417652736.0, per=9.500748, pbr=0.84727466, operating_margin_pct=8.121
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

- Trades: **25**, Win rate: **40.00%**, Total PnL: **¥-67,782**
- Avg return: **-0.09%**, Avg win: **7.85%**, Avg loss: **-5.39%**
- Payoff ratio: **1.4568**, Profit factor: **0.9277**
- Avg MFE: **9.11%**, Avg MAE: **-5.57%**

### Exit Reasons

```json
{
  "SCORE_COLLAPSE": 8,
  "PROFIT_PROTECTION": 5,
  "HARD_STOP": 4,
  "EARLY_FAIL": 4,
  "TAKE_PROFIT": 2,
  "MOMENTUM_DECAY": 1,
  "MAX_HOLDING_DAYS": 1
}
```

### Failure Patterns

```json
{
  "DEEP_ADVERSE_MOVE": 4,
  "NORMAL_LOSS": 4,
  "WINNER_TURNED_LOSER": 4,
  "FAST_FAILED_ENTRY": 3
}
```

### Success Patterns

```json
{
  "NORMAL_WIN": 5,
  "FAST_WINNER": 3,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 2
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | -11.91% | ¥-125,892 | 1 | 1.07% | -16.15% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | -11.61% | ¥-156,214 | 4 | 1.47% | -14.61% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 3692.T | FFRI Security,Inc. | 2026-02-09 | 2026-02-10 | -9.73% | ¥-97,946 | 1 | 0.19% | -12.05% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4419.T | Finatext Holdings Ltd. | 2026-05-11 | 2026-05-15 | -7.58% | ¥-81,489 | 4 | 13.35% | -12.69% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5842.T | Integral Corporation | 2026-01-16 | 2026-01-20 | -7.07% | ¥-94,992 | 4 | 1.28% | -11.10% | EARLY_FAIL | FAST_FAILED_ENTRY |
| 4071.T | Plus Alpha Consulting Co.,LTD. | 2026-05-08 | 2026-05-13 | -5.49% | ¥-59,250 | 5 | 0.94% | -6.60% | EARLY_FAIL | FAST_FAILED_ENTRY |
| 5574.T | ABEJA,Inc. | 2026-02-06 | 2026-02-16 | -4.98% | ¥-55,297 | 10 | 3.78% | -7.37% | SCORE_COLLAPSE | NORMAL_LOSS |
| 7172.T | Commodities | 2026-05-01 | 2026-05-08 | -4.81% | ¥-58,954 | 7 | 0.04% | -5.40% | EARLY_FAIL | FAST_FAILED_ENTRY |
| 299A.T | Kurashiru,Inc. | 2026-05-12 | 2026-05-21 | -3.74% | ¥-44,876 | 9 | 6.72% | -5.95% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 4384.T | RAKSUL INC. | 2026-02-05 | 2026-02-16 | -3.73% | ¥-38,272 | 11 | 1.33% | -5.60% | EARLY_FAIL | NORMAL_LOSS |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-05-18 | 2026-05-19 | -3.38% | ¥-38,190 | 1 | 9.17% | -4.44% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 6544.T | ジャパンエレベーターサービスホールディングス | 2026-05-18 | 2026-05-21 | -3.17% | ¥-41,196 | 3 | 0.83% | -3.98% | SCORE_COLLAPSE | NORMAL_LOSS |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-02-17 | 2026-03-04 | -2.89% | ¥-37,108 | 15 | 14.79% | -4.76% | PROFIT_PROTECTION | WINNER_TURNED_LOSER |
| 2986.T | LA Holdings Co.,Ltd. | 2026-02-02 | 2026-02-18 | -0.40% | ¥-4,528 | 16 | 20.14% | -5.67% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 9279.T | GIFT HOLDINGS INC. | 2026-03-19 | 2026-03-23 | -0.31% | ¥-3,098 | 4 | 1.97% | -2.28% | SCORE_COLLAPSE | NORMAL_LOSS |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5243.T | note inc. | 2026-01-14 | 2026-01-16 | 25.88% | ¥312,944 | 2 | 31.01% | -1.33% | TAKE_PROFIT | FAST_WINNER |
| 7318.T | SERENDIP HOLDINGS Co.,Ltd. | 2026-02-25 | 2026-03-02 | 19.40% | ¥198,538 | 5 | 29.74% | -0.17% | TAKE_PROFIT | FAST_WINNER |
| 7777.T | 3-D Matrix,Ltd. | 2026-02-26 | 2026-03-05 | 9.78% | ¥102,208 | 7 | 18.55% | -2.93% | PROFIT_PROTECTION | FAST_WINNER |
| 3479.T | TKP Corporation | 2026-01-26 | 2026-02-24 | 7.51% | ¥93,964 | 29 | 10.12% | -1.10% | MAX_HOLDING_DAYS | NORMAL_WIN |
| 5253.T | COVER Corporation | 2026-05-18 | 2026-05-27 | 3.53% | ¥37,616 | 9 | 19.93% | -1.93% | PROFIT_PROTECTION | NORMAL_WIN |
| 4449.T | giftee Inc. | 2026-04-28 | 2026-04-30 | 3.20% | ¥32,635 | 2 | 3.30% | -1.84% | SCORE_COLLAPSE | NORMAL_WIN |
| 3905.T | Datasection Inc. | 2026-01-07 | 2026-01-13 | 3.06% | ¥34,754 | 6 | 10.60% | -3.04% | SCORE_COLLAPSE | NORMAL_WIN |
| 7172.T | Commodities | 2026-02-12 | 2026-02-13 | 2.40% | ¥25,271 | 1 | 3.83% | -2.56% | MOMENTUM_DECAY | NORMAL_WIN |
| 6532.T | ベイカレント | 2026-04-17 | 2026-04-24 | 2.25% | ¥13,702 | 7 | 12.85% | -0.25% | PROFIT_PROTECTION | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 7806.T | MTG Co.,Ltd. | 2026-05-13 | 2026-05-18 | 1.46% | ¥17,888 | 5 | 10.65% | -5.55% | PROFIT_PROTECTION | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 9279.T | GIFT HOLDINGS INC. | 2026-03-19 | 2026-03-23 | -0.31% | ¥-3,098 | 4 | 1.97% | -2.28% | SCORE_COLLAPSE | NORMAL_LOSS |
| 2986.T | LA Holdings Co.,Ltd. | 2026-02-02 | 2026-02-18 | -0.40% | ¥-4,528 | 16 | 20.14% | -5.67% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-02-17 | 2026-03-04 | -2.89% | ¥-37,108 | 15 | 14.79% | -4.76% | PROFIT_PROTECTION | WINNER_TURNED_LOSER |
| 6544.T | ジャパンエレベーターサービスホールディングス | 2026-05-18 | 2026-05-21 | -3.17% | ¥-41,196 | 3 | 0.83% | -3.98% | SCORE_COLLAPSE | NORMAL_LOSS |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-05-18 | 2026-05-19 | -3.38% | ¥-38,190 | 1 | 9.17% | -4.44% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4419.T | Finatext Holdings Ltd. | 2026-05-11 | 2026-05-15 | -7.58% | ¥-81,489 | 4 | 13.35% | -12.69% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 2986.T | LA Holdings Co.,Ltd. | 2026-02-02 | 2026-02-18 | -0.40% | ¥-4,528 | 16 | 20.14% | -5.67% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-02-17 | 2026-03-04 | -2.89% | ¥-37,108 | 15 | 14.79% | -4.76% | PROFIT_PROTECTION | WINNER_TURNED_LOSER |
| 5253.T | COVER Corporation | 2026-05-18 | 2026-05-27 | 3.53% | ¥37,616 | 9 | 19.93% | -1.93% | PROFIT_PROTECTION | NORMAL_WIN |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | -11.61% | ¥-156,214 | 4 | 1.47% | -14.61% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | -11.91% | ¥-125,892 | 1 | 1.07% | -16.15% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 7685.T | BuySell Technologies Co.,Ltd. | 2026-05-18 | 2026-05-19 | -3.38% | ¥-38,190 | 1 | 9.17% | -4.44% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 6532.T | ベイカレント | 2026-04-17 | 2026-04-24 | 2.25% | ¥13,702 | 7 | 12.85% | -0.25% | PROFIT_PROTECTION | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 299A.T | Kurashiru,Inc. | 2026-05-12 | 2026-05-21 | -3.74% | ¥-44,876 | 9 | 6.72% | -5.95% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 7318.T | SERENDIP HOLDINGS Co.,Ltd. | 2026-02-25 | 2026-03-02 | 19.40% | ¥198,538 | 5 | 29.74% | -0.17% | TAKE_PROFIT | FAST_WINNER |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5243.T | note inc. | 2026-01-26 | 2026-01-27 | -11.91% | ¥-125,892 | 1 | 1.07% | -16.15% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4443.T | Sansan,Inc. | 2026-01-16 | 2026-01-20 | -11.61% | ¥-156,214 | 4 | 1.47% | -14.61% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4419.T | Finatext Holdings Ltd. | 2026-05-11 | 2026-05-15 | -7.58% | ¥-81,489 | 4 | 13.35% | -12.69% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 3692.T | FFRI Security,Inc. | 2026-02-09 | 2026-02-10 | -9.73% | ¥-97,946 | 1 | 0.19% | -12.05% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5842.T | Integral Corporation | 2026-01-16 | 2026-01-20 | -7.07% | ¥-94,992 | 4 | 1.28% | -11.10% | EARLY_FAIL | FAST_FAILED_ENTRY |
| 5574.T | ABEJA,Inc. | 2026-02-06 | 2026-02-16 | -4.98% | ¥-55,297 | 10 | 3.78% | -7.37% | SCORE_COLLAPSE | NORMAL_LOSS |
| 4071.T | Plus Alpha Consulting Co.,LTD. | 2026-05-08 | 2026-05-13 | -5.49% | ¥-59,250 | 5 | 0.94% | -6.60% | EARLY_FAIL | FAST_FAILED_ENTRY |
| 299A.T | Kurashiru,Inc. | 2026-05-12 | 2026-05-21 | -3.74% | ¥-44,876 | 9 | 6.72% | -5.95% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 2986.T | LA Holdings Co.,Ltd. | 2026-02-02 | 2026-02-18 | -0.40% | ¥-4,528 | 16 | 20.14% | -5.67% | SCORE_COLLAPSE | WINNER_TURNED_LOSER |
| 4384.T | RAKSUL INC. | 2026-02-05 | 2026-02-16 | -3.73% | ¥-38,272 | 11 | 1.33% | -5.60% | EARLY_FAIL | NORMAL_LOSS |


### Compact Entry Context For Worst Trades

- `5243.T` 2026-01-26 → 2026-01-27 -11.91%: score: rank=6, action=Trade / feature: return_5d_pct=17.384433030422763, return_20d_pct=90.93830334190231, volume_ratio_20d=1.4437206857180407, rsi_14=77.67672591980157, range_position_252d_0_1=0.9115797262301147 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=38538764288.0, per=74.13601, pbr=7.0371614, roe_pct=19.439, operating_margin_pct=19.326
- `4443.T` 2026-01-16 → 2026-01-20 -11.61%: score: rank=2, action=Trade / feature: return_5d_pct=11.575381140598529, return_20d_pct=17.479191438763376, volume_ratio_20d=6.196071396537806, rsi_14=73.46938775510205, range_position_252d_0_1=0.376953125 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=226175877120.0, per=110.79404, pbr=11.916517, roe_pct=15.695, operating_margin_pct=21.867001
- `3692.T` 2026-02-09 → 2026-02-10 -9.73%: score: rank=4, action=Trade / feature: return_5d_pct=7.8918918918919, return_20d_pct=20.531400966183575, volume_ratio_20d=1.3248302818350133, rsi_14=50.110864745011085, range_position_252d_0_1=0.6649122807017543 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=46191714304.0, per=42.084023, pbr=12.229753, roe_pct=33.481, operating_margin_pct=31.441997999999998
- `4419.T` 2026-05-11 → 2026-05-15 -7.58%: score: rank=9, action=Trade / feature: return_5d_pct=16.34877384196185, return_20d_pct=26.33136094674555, volume_ratio_20d=1.87451106713911, rsi_14=79.29292929292929, range_position_252d_0_1=0.7140921409214093 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=69232304128.0, per=46.4323, pbr=6.3791428, roe_pct=15.955, operating_margin_pct=28.726998
- `5842.T` 2026-01-16 → 2026-01-20 -7.07%: score: rank=3, action=Trade / feature: return_5d_pct=17.94117647058824, return_20d_pct=23.006134969325153, volume_ratio_20d=4.320946108360175, rsi_14=79.57446808510639, range_position_252d_0_1=0.8234495246717972 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=115273490432.0, per=19.651669, pbr=1.683341, roe_pct=20.898001, operating_margin_pct=85.797995
- `4071.T` 2026-05-08 → 2026-05-13 -5.49%: score: rank=5, action=Trade / feature: return_5d_pct=10.551106924163921, return_20d_pct=11.602472658107455, volume_ratio_20d=2.412945426562066, rsi_14=77.67527675276753, range_position_252d_0_1=0.7497639282341831 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=113946345472.0, per=28.71488, pbr=7.0832276, roe_pct=29.786, operating_margin_pct=41.122
- `5574.T` 2026-02-06 → 2026-02-16 -4.98%: score: rank=6, action=Trade / feature: return_5d_pct=12.862773199570054, return_20d_pct=20.55109070034442, volume_ratio_20d=2.08154803040774, rsi_14=53.95629238884702, range_position_252d_0_1=0.5058430717863105 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=22137724928.0, per=42.92044, pbr=4.523564, roe_pct=11.931, operating_margin_pct=14.396999999999998
- `7172.T` 2026-05-01 → 2026-05-08 -4.81%: score: rank=2, action=Trade / feature: return_5d_pct=11.438739196746317, return_20d_pct=11.212582445459152, volume_ratio_20d=4.4394724078043595, rsi_14=67.48878923766816, range_position_252d_0_1=0.6659340659340659 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=121756221440.0, per=11.5514965, pbr=1.5774169, roe_pct=16.031000000000002, operating_margin_pct=67.407995


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
  "PULLBACK_FAILED": 14,
  "MAX_HOLDING_DAYS": 9,
  "PROFIT_PROTECTION": 4,
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
| 5344.T | ＭＡＲＵＷＡ | 2026-03-23 | 2026-03-31 | -3.60% | ¥-41,537 | 8 | 11.65% | -5.19% | PROFIT_PROTECTION | WINNER_TURNED_LOSER |
| 6506.T | 安川電機 | 2026-02-19 | 2026-03-05 | -7.28% | ¥-101,307 | 14 | 7.00% | -13.29% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5714.T | ＤＯＷＡホールディングス | 2026-03-18 | 2026-03-23 | -12.70% | ¥-151,270 | 5 | 1.48% | -15.43% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 1801.T | 大成建設 | 2026-03-11 | 2026-03-23 | -9.86% | ¥-133,291 | 12 | 2.79% | -12.63% | PULLBACK_FAILED | DEEP_ADVERSE_MOVE |
| 6368.T | オルガノ | 2026-03-09 | 2026-03-24 | -2.35% | ¥-1,032 | 15 | 9.41% | -9.13% | HARD_STOP | WINNER_TURNED_LOSER |
| 4385.T | メルカリ | 2026-02-25 | 2026-03-04 | -0.23% | ¥-2,986 | 7 | 11.26% | -2.41% | PROFIT_PROTECTION | WINNER_TURNED_LOSER |
| 5101.T | 横浜ゴム | 2026-03-04 | 2026-03-10 | -7.01% | ¥-91,967 | 6 | 3.88% | -13.86% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5471.T | 大同特殊鋼 | 2026-03-09 | 2026-03-23 | -1.66% | ¥-827 | 14 | 9.18% | -3.55% | PROFIT_PROTECTION | WINNER_TURNED_LOSER |
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

- Trades: **66**, Win rate: **46.97%**, Total PnL: **¥460,933**
- Avg return: **0.74%**, Avg win: **7.07%**, Avg loss: **-4.86%**
- Payoff ratio: **1.4542**, Profit factor: **1.2506**
- Avg MFE: **6.30%**, Avg MAE: **-5.18%**

### Exit Reasons

```json
{
  "HARD_STOP": 25,
  "SCORE_COLLAPSE": 15,
  "SNAPBACK_COMPLETE": 12,
  "EARLY_FAIL": 8,
  "SNAPBACK_PROFIT_PROTECTION": 4,
  "TAKE_PROFIT": 2
}
```

### Failure Patterns

```json
{
  "STOP_LOSS_HIT": 20,
  "NORMAL_LOSS": 8,
  "DEEP_ADVERSE_MOVE": 4,
  "WINNER_TURNED_LOSER": 3
}
```

### Success Patterns

```json
{
  "NORMAL_WIN": 16,
  "FAST_WINNER": 13,
  "GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN": 2
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6098.T | リクルートホールディングス | 2026-02-12 | 2026-02-16 | -11.57% | ¥-127,501 | 4 | 2.31% | -13.40% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 6701.T | 日本電気 | 2026-02-12 | 2026-02-16 | -10.52% | ¥-117,491 | 4 | 1.09% | -11.20% | HARD_STOP | STOP_LOSS_HIT |
| 4013.T | Kinjiro Co.,Ltd. | 2026-02-13 | 2026-02-16 | -9.73% | ¥-96,755 | 3 | 0.40% | -12.12% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | -9.68% | ¥-105,576 | 3 | 1.50% | -12.08% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 3626.T | ＴＩＳ | 2026-02-12 | 2026-02-16 | -9.13% | ¥-107,475 | 4 | 0.32% | -10.45% | HARD_STOP | STOP_LOSS_HIT |
| 4592.T | SanBio Company Limited | 2026-05-22 | 2026-05-26 | -8.27% | ¥-94,001 | 4 | 0.47% | -11.42% | HARD_STOP | STOP_LOSS_HIT |
| 4180.T | Appier Group,Inc. | 2026-02-18 | 2026-02-20 | -6.79% | ¥-69,739 | 2 | 0.66% | -11.40% | HARD_STOP | STOP_LOSS_HIT |
| 9024.T | 西武ホールディングス | 2026-05-18 | 2026-05-19 | -6.73% | ¥-74,388 | 1 | 0.75% | -10.01% | HARD_STOP | STOP_LOSS_HIT |
| 6039.T | Japan Animal Referral Medical Center Co.,Ltd. | 2026-05-20 | 2026-05-21 | -6.32% | ¥-70,430 | 1 | 0.54% | -10.80% | HARD_STOP | STOP_LOSS_HIT |
| 7157.T | LIFENET INSURANCE COMPANY | 2026-05-08 | 2026-05-12 | -6.03% | ¥-64,511 | 4 | 0.40% | -9.23% | HARD_STOP | STOP_LOSS_HIT |
| 7733.T | オリンパス | 2026-02-18 | 2026-02-24 | -6.00% | ¥-61,384 | 6 | 0.45% | -7.36% | HARD_STOP | STOP_LOSS_HIT |
| 4478.T | freee K.K. | 2026-02-06 | 2026-02-16 | -5.49% | ¥-62,101 | 10 | 5.81% | -8.87% | HARD_STOP | WINNER_TURNED_LOSER |
| 4449.T | giftee Inc. | 2026-02-19 | 2026-02-20 | -5.34% | ¥-55,392 | 1 | -0.00% | -5.43% | HARD_STOP | STOP_LOSS_HIT |
| 4980.T | デクセリアルズ | 2026-02-13 | 2026-02-16 | -5.28% | ¥-52,513 | 3 | 0.57% | -6.14% | HARD_STOP | STOP_LOSS_HIT |
| 9168.T | Rise Consulting Group,Inc. | 2026-01-16 | 2026-01-20 | -4.91% | ¥-50,073 | 4 | 0.06% | -6.11% | HARD_STOP | STOP_LOSS_HIT |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 4180.T | Appier Group,Inc. | 2026-02-24 | 2026-02-27 | 21.39% | ¥212,132 | 3 | 24.47% | -2.32% | SNAPBACK_COMPLETE | FAST_WINNER |
| 5803.T | フジクラ | 2026-05-22 | 2026-05-26 | 21.26% | ¥242,476 | 4 | 21.45% | -2.08% | SCORE_COLLAPSE | FAST_WINNER |
| 4478.T | freee K.K. | 2026-02-25 | 2026-02-27 | 18.71% | ¥184,906 | 2 | 21.96% | -2.17% | SCORE_COLLAPSE | FAST_WINNER |
| 4588.T | Oncolys BioPharma Inc. | 2026-05-22 | 2026-05-25 | 16.18% | ¥187,423 | 3 | 27.93% | -9.48% | SNAPBACK_COMPLETE | FAST_WINNER |
| 4194.T | ビジョナル | 2026-02-25 | 2026-03-02 | 16.15% | ¥164,644 | 5 | 17.21% | -0.80% | SNAPBACK_COMPLETE | FAST_WINNER |
| 4151.T | 協和キリン | 2026-02-04 | 2026-02-12 | 11.85% | ¥119,111 | 8 | 13.30% | -0.60% | SNAPBACK_COMPLETE | FAST_WINNER |
| 9501.T | 東京電力ホールディングス | 2026-01-29 | 2026-02-05 | 10.55% | ¥111,087 | 7 | 10.68% | -1.24% | TAKE_PROFIT | FAST_WINNER |
| 4812.T | 電通総研 | 2026-02-17 | 2026-03-02 | 9.76% | ¥99,358 | 13 | 10.99% | -3.72% | SCORE_COLLAPSE | NORMAL_WIN |
| 5929.T | 三和ホールディングス | 2026-02-02 | 2026-02-10 | 8.73% | ¥94,152 | 8 | 10.63% | -2.18% | SCORE_COLLAPSE | FAST_WINNER |
| 2501.T | サッポロホールディングス | 2026-05-15 | 2026-05-20 | 8.71% | ¥96,866 | 5 | 10.30% | -3.19% | SNAPBACK_COMPLETE | FAST_WINNER |
| 4088.T | エア・ウォーター | 2026-05-07 | 2026-05-13 | 8.35% | ¥94,519 | 6 | 11.16% | -1.87% | SNAPBACK_COMPLETE | FAST_WINNER |
| 7731.T | ニコン | 2026-04-28 | 2026-05-07 | 7.40% | ¥79,128 | 9 | 12.17% | -2.01% | SNAPBACK_COMPLETE | FAST_WINNER |
| 4516.T | 日本新薬 | 2026-05-11 | 2026-05-21 | 7.36% | ¥78,094 | 10 | 9.06% | -2.30% | SCORE_COLLAPSE | FAST_WINNER |
| 4043.T | トクヤマ | 2026-02-04 | 2026-02-10 | 7.21% | ¥75,587 | 6 | 8.35% | -0.38% | SCORE_COLLAPSE | FAST_WINNER |
| 4480.T | MEDLEY,INC. | 2026-02-17 | 2026-02-20 | 5.91% | ¥59,256 | 3 | 12.39% | -1.48% | SNAPBACK_COMPLETE | NORMAL_WIN |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 5255.T | Monstarlab Inc. | 2026-02-24 | 2026-02-26 | 4.03% | ¥39,985 | 2 | 19.37% | -8.57% | SNAPBACK_COMPLETE | NORMAL_WIN |
| 4519.T | 中外製薬 | 2026-04-28 | 2026-05-07 | 2.24% | ¥24,091 | 9 | 17.20% | -0.23% | SNAPBACK_COMPLETE | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |
| 6098.T | リクルートホールディングス | 2026-02-12 | 2026-02-16 | -11.57% | ¥-127,501 | 4 | 2.31% | -13.40% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4588.T | Oncolys BioPharma Inc. | 2026-05-22 | 2026-05-25 | 16.18% | ¥187,423 | 3 | 27.93% | -9.48% | SNAPBACK_COMPLETE | FAST_WINNER |
| 6701.T | 日本電気 | 2026-02-12 | 2026-02-16 | -10.52% | ¥-117,491 | 4 | 1.09% | -11.20% | HARD_STOP | STOP_LOSS_HIT |
| 4478.T | freee K.K. | 2026-02-06 | 2026-02-16 | -5.49% | ¥-62,101 | 10 | 5.81% | -8.87% | HARD_STOP | WINNER_TURNED_LOSER |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | -9.68% | ¥-105,576 | 3 | 1.50% | -12.08% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4013.T | Kinjiro Co.,Ltd. | 2026-02-13 | 2026-02-16 | -9.73% | ¥-96,755 | 3 | 0.40% | -12.12% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 3626.T | ＴＩＳ | 2026-02-12 | 2026-02-16 | -9.13% | ¥-107,475 | 4 | 0.32% | -10.45% | HARD_STOP | STOP_LOSS_HIT |
| 4443.T | Sansan,Inc. | 2026-02-06 | 2026-02-13 | 0.39% | ¥4,368 | 7 | 9.61% | -8.21% | SNAPBACK_PROFIT_PROTECTION | GAVE_BACK_LARGE_MFE_BUT_CLOSED_GREEN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6098.T | リクルートホールディングス | 2026-02-12 | 2026-02-16 | -11.57% | ¥-127,501 | 4 | 2.31% | -13.40% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4013.T | Kinjiro Co.,Ltd. | 2026-02-13 | 2026-02-16 | -9.73% | ¥-96,755 | 3 | 0.40% | -12.12% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 4307.T | 野村総合研究所 | 2026-02-02 | 2026-02-05 | -9.68% | ¥-105,576 | 3 | 1.50% | -12.08% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 247A.T | Ai ROBOTICS INC. | 2026-05-18 | 2026-05-19 | -4.52% | ¥-52,007 | 1 | 0.33% | -12.01% | HARD_STOP | DEEP_ADVERSE_MOVE |
| 5838.T | 楽天銀行 | 2026-03-02 | 2026-03-05 | -4.78% | ¥-50,452 | 3 | 3.58% | -11.48% | HARD_STOP | STOP_LOSS_HIT |
| 4592.T | SanBio Company Limited | 2026-05-22 | 2026-05-26 | -8.27% | ¥-94,001 | 4 | 0.47% | -11.42% | HARD_STOP | STOP_LOSS_HIT |
| 4180.T | Appier Group,Inc. | 2026-02-18 | 2026-02-20 | -6.79% | ¥-69,739 | 2 | 0.66% | -11.40% | HARD_STOP | STOP_LOSS_HIT |
| 6701.T | 日本電気 | 2026-02-12 | 2026-02-16 | -10.52% | ¥-117,491 | 4 | 1.09% | -11.20% | HARD_STOP | STOP_LOSS_HIT |
| 6039.T | Japan Animal Referral Medical Center Co.,Ltd. | 2026-05-20 | 2026-05-21 | -6.32% | ¥-70,430 | 1 | 0.54% | -10.80% | HARD_STOP | STOP_LOSS_HIT |
| 3626.T | ＴＩＳ | 2026-02-12 | 2026-02-16 | -9.13% | ¥-107,475 | 4 | 0.32% | -10.45% | HARD_STOP | STOP_LOSS_HIT |


### Compact Entry Context For Worst Trades

- `6098.T` 2026-02-12 → 2026-02-16 -11.57%: score: rank=3, action=Trade / feature: return_5d_pct=-11.792905081495686, return_20d_pct=-19.773272291257904, volume_ratio_20d=1.818524865961227, rsi_14=29.989015012815813, range_position_252d_0_1=0.2594059405940594 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=15552312508416.0, per=32.135155, pbr=9.854402, roe_pct=30.830999999999996, operating_margin_pct=14.045
- `6701.T` 2026-02-12 → 2026-02-16 -10.52%: score: rank=2, action=Trade / feature: return_5d_pct=-9.676816738277605, return_20d_pct=-17.18054128126071, volume_ratio_20d=1.8749082183771328, rsi_14=32.18475073313783, range_position_252d_0_1=0.6204970678581402 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=5794909650944.0, per=21.477104, pbr=2.6338751, roe_pct=12.556999999999999, operating_margin_pct=15.059000000000001
- `4013.T` 2026-02-13 → 2026-02-16 -9.73%: score: rank=2, action=Trade / feature: return_5d_pct=-17.497456765005083, return_20d_pct=-37.22910216718266, volume_ratio_20d=6.045451031923939, rsi_14=19.81845688350984, range_position_252d_0_1=0.35049683830171635 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=11168519168.0, per=11.007572, pbr=1.0873401, roe_pct=10.009, operating_margin_pct=24.493000000000002
- `4307.T` 2026-02-02 → 2026-02-05 -9.68%: score: rank=1, action=Trade / feature: return_5d_pct=-20.725126475548063, return_20d_pct=-21.532298447671504, volume_ratio_20d=5.545538564332412, rsi_14=9.214830970556164, range_position_252d_0_1=0.056854410201912856 / value: value_trap_penalty=0.2 / fund: market_cap_jpy=3077084807168.0, per=201.23967, pbr=7.091607, roe_pct=3.604, operating_margin_pct=-28.653000000000002
- `3626.T` 2026-02-12 → 2026-02-16 -9.13%: score: rank=1, action=Trade / feature: return_5d_pct=-19.35338005878363, return_20d_pct=-30.89887640449438, volume_ratio_20d=1.5358477481989443, rsi_14=11.967921036397286, range_position_252d_0_1=0.0903674280039722 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=754402197504.0, per=17.3947, pbr=2.4153821, roe_pct=14.008000000000001, operating_margin_pct=13.372
- `4592.T` 2026-05-22 → 2026-05-26 -8.27%: score: rank=3, action=Trade / feature: return_5d_pct=-16.547553600879606, return_20d_pct=-27.403156384505024, volume_ratio_20d=0.7882147467537398, rsi_14=33.0532212885154, range_position_252d_0_1=0.050326546292739145 / value: value_trap_penalty=0.35 / fund: market_cap_jpy=99970965504.0, per=-31.389364, pbr=7.3472896, roe_pct=-50.003, operating_margin_pct=0.0
- `4180.T` 2026-02-18 → 2026-02-20 -6.79%: score: rank=2, action=Trade / feature: return_5d_pct=-17.54932502596054, return_20d_pct=-28.532853285328528, volume_ratio_20d=2.3644846140091356, rsi_14=19.560439560439562, range_position_252d_0_1=0.012785388127853882 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=94620147712.0, per=37.094837, pbr=2.5063334, roe_pct=7.371999999999999, operating_margin_pct=1.52900005
- `9024.T` 2026-05-18 → 2026-05-19 -6.73%: score: rank=4, action=Trade / feature: return_5d_pct=-15.116857284932872, return_20d_pct=-16.548521143974583, volume_ratio_20d=3.587528492467678, rsi_14=33.73056994818653, range_position_252d_0_1=0.11998567335243553 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=699497316352.0, per=18.244497, pbr=1.2294874, roe_pct=6.855, operating_margin_pct=0.5


## HIZUMI / `value_mispricing`

### Key Metrics

- Trades: **7**, Win rate: **28.57%**, Total PnL: **¥-368,394**
- Avg return: **-3.51%**, Avg win: **0.54%**, Avg loss: **-5.13%**
- Payoff ratio: **0.1056**, Profit factor: **0.0501**
- Avg MFE: **2.03%**, Avg MAE: **-5.17%**

### Exit Reasons

```json
{
  "HARD_STOP": 4,
  "MISPRICING_RESOLVED": 2,
  "EARLY_FAIL": 1
}
```

### Failure Patterns

```json
{
  "STOP_LOSS_HIT": 4,
  "NORMAL_LOSS": 1
}
```

### Success Patterns

```json
{
  "NORMAL_WIN": 2
}
```

### Worst Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6326.T | クボタ | 2026-05-11 | 2026-05-21 | -6.17% | ¥-101,927 | 10 | 3.45% | -7.78% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-05-18 | 2026-05-26 | -5.44% | ¥-92,750 | 8 | 0.09% | -7.28% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-04-09 | 2026-04-27 | -5.34% | ¥-42,476 | 18 | 4.10% | -6.96% | HARD_STOP | STOP_LOSS_HIT |
| 7172.T | Commodities | 2026-05-01 | 2026-05-08 | -4.81% | ¥-80,535 | 7 | 0.04% | -5.40% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-04-30 | 2026-05-08 | -3.87% | ¥-70,123 | 8 | 0.43% | -5.76% | EARLY_FAIL | NORMAL_LOSS |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.11% | ¥2,056 | 1 | 3.12% | -0.47% | MISPRICING_RESOLVED | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-02-09 | 2026-02-12 | 0.97% | ¥17,361 | 3 | 2.97% | -2.55% | MISPRICING_RESOLVED | NORMAL_WIN |


### Best Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 8473.T | ＳＢＩホールディングス | 2026-02-09 | 2026-02-12 | 0.97% | ¥17,361 | 3 | 2.97% | -2.55% | MISPRICING_RESOLVED | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.11% | ¥2,056 | 1 | 3.12% | -0.47% | MISPRICING_RESOLVED | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-04-30 | 2026-05-08 | -3.87% | ¥-70,123 | 8 | 0.43% | -5.76% | EARLY_FAIL | NORMAL_LOSS |
| 7172.T | Commodities | 2026-05-01 | 2026-05-08 | -4.81% | ¥-80,535 | 7 | 0.04% | -5.40% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-04-09 | 2026-04-27 | -5.34% | ¥-42,476 | 18 | 4.10% | -6.96% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-05-18 | 2026-05-26 | -5.44% | ¥-92,750 | 8 | 0.09% | -7.28% | HARD_STOP | STOP_LOSS_HIT |
| 6326.T | クボタ | 2026-05-11 | 2026-05-21 | -6.17% | ¥-101,927 | 10 | 3.45% | -7.78% | HARD_STOP | STOP_LOSS_HIT |


### Largest MFE Givebacks

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6326.T | クボタ | 2026-05-11 | 2026-05-21 | -6.17% | ¥-101,927 | 10 | 3.45% | -7.78% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-04-09 | 2026-04-27 | -5.34% | ¥-42,476 | 18 | 4.10% | -6.96% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-05-18 | 2026-05-26 | -5.44% | ¥-92,750 | 8 | 0.09% | -7.28% | HARD_STOP | STOP_LOSS_HIT |
| 7172.T | Commodities | 2026-05-01 | 2026-05-08 | -4.81% | ¥-80,535 | 7 | 0.04% | -5.40% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-04-30 | 2026-05-08 | -3.87% | ¥-70,123 | 8 | 0.43% | -5.76% | EARLY_FAIL | NORMAL_LOSS |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.11% | ¥2,056 | 1 | 3.12% | -0.47% | MISPRICING_RESOLVED | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-02-09 | 2026-02-12 | 0.97% | ¥17,361 | 3 | 2.97% | -2.55% | MISPRICING_RESOLVED | NORMAL_WIN |


### Deepest Adverse Trades

| Ticker | Name | Entry | Exit | Return | PnL | Hold | MFE | MAE | Exit | Pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6326.T | クボタ | 2026-05-11 | 2026-05-21 | -6.17% | ¥-101,927 | 10 | 3.45% | -7.78% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-05-18 | 2026-05-26 | -5.44% | ¥-92,750 | 8 | 0.09% | -7.28% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-04-09 | 2026-04-27 | -5.34% | ¥-42,476 | 18 | 4.10% | -6.96% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-04-30 | 2026-05-08 | -3.87% | ¥-70,123 | 8 | 0.43% | -5.76% | EARLY_FAIL | NORMAL_LOSS |
| 7172.T | Commodities | 2026-05-01 | 2026-05-08 | -4.81% | ¥-80,535 | 7 | 0.04% | -5.40% | HARD_STOP | STOP_LOSS_HIT |
| 8473.T | ＳＢＩホールディングス | 2026-02-09 | 2026-02-12 | 0.97% | ¥17,361 | 3 | 2.97% | -2.55% | MISPRICING_RESOLVED | NORMAL_WIN |
| 8473.T | ＳＢＩホールディングス | 2026-01-06 | 2026-01-07 | 0.11% | ¥2,056 | 1 | 3.12% | -0.47% | MISPRICING_RESOLVED | NORMAL_WIN |


### Compact Entry Context For Worst Trades

- `6326.T` 2026-05-11 → 2026-05-21 -6.17%: score: rank=7, action=Trade / feature: return_5d_pct=12.944009632751353, return_20d_pct=12.133891213389125, volume_ratio_20d=3.1022275267475954, rsi_14=53.79229871645275, range_position_252d_0_1=0.7392303273980471 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=3181151780864.0, per=17.115408, pbr=1.1835096, roe_pct=8.871, operating_margin_pct=12.104
- `8473.T` 2026-05-18 → 2026-05-26 -5.44%: score: rank=4, action=Trade / feature: return_5d_pct=2.243483998680307, return_20d_pct=2.5479814692256797, volume_ratio_20d=0.8596020388015825, rsi_14=51.22410546139359, range_position_252d_0_1=0.6262183235867447 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1881560842240.0, per=4.6614037, pbr=1.0482572, roe_pct=20.613999999999997, operating_margin_pct=28.927000000000003
- `8473.T` 2026-04-09 → 2026-04-27 -5.34%: score: rank=1, action=Trade / feature: return_5d_pct=5.094905094905089, return_20d_pct=4.746100232326578, volume_ratio_20d=1.229206606111055, rsi_14=48.45132743362832, range_position_252d_0_1=0.6944922547332186 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1881560842240.0, per=4.6614037, pbr=1.0482572, roe_pct=20.613999999999997, operating_margin_pct=28.927000000000003
- `7172.T` 2026-05-01 → 2026-05-08 -4.81%: score: rank=7, action=Trade / feature: return_5d_pct=11.438739196746317, return_20d_pct=11.212582445459152, volume_ratio_20d=4.4394724078043595, rsi_14=67.48878923766816, range_position_252d_0_1=0.6659340659340659 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=121756221440.0, per=11.5514965, pbr=1.5774169, roe_pct=16.031000000000002, operating_margin_pct=67.407995
- `8473.T` 2026-04-30 → 2026-05-08 -3.87%: score: rank=1, action=Trade / feature: return_5d_pct=0.712896953985731, return_20d_pct=9.090909090909083, volume_ratio_20d=1.3940624366076626, rsi_14=46.83377308707124, range_position_252d_0_1=0.6443818906873094 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1881560842240.0, per=4.6614037, pbr=1.0482572, roe_pct=20.613999999999997, operating_margin_pct=28.927000000000003
- `8473.T` 2026-01-06 → 2026-01-07 0.11%: score: rank=1, action=Trade / feature: return_5d_pct=2.4578027835356897, return_20d_pct=7.253564786112832, volume_ratio_20d=1.2361704156025308, rsi_14=56.095143706640236, range_position_252d_0_1=0.8267241379310345 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1881560842240.0, per=4.6614037, pbr=1.0482572, roe_pct=20.613999999999997, operating_margin_pct=28.927000000000003
- `8473.T` 2026-02-09 → 2026-02-12 0.97%: score: rank=7, action=Trade / feature: return_5d_pct=0.22962112514350874, return_20d_pct=1.1880614314691451, volume_ratio_20d=1.5178486273280283, rsi_14=38.36032388663968, range_position_252d_0_1=0.8390705679862306 / value: value_trap_penalty=0.0 / fund: market_cap_jpy=1881560842240.0, per=4.6614037, pbr=1.0482572, roe_pct=20.613999999999997, operating_margin_pct=28.927000000000003


## Prompt Suggestion

```text
このTrade Diagnosticsをもとに、各Agentの勝因・敗因を定量的に分析してください。特に、勝率と損益の非対称性、MFE/MAE、exit reason、entry context、fundamental/value contextを見て、Agent別に改善すべき売買ルールを優先順位付きで提案してください。
```
