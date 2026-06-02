# Trade Diagnostics v2 修正内容

## 置き換えるファイル

- `scripts/export_ai_arena_trade_diagnostics_jp.py`

## 追加または置き換え候補

- `.github/workflows/ai-arena-jp-trade-diagnostics.yml`

既存のworkflow名を維持したい場合は、workflow全体を差し替えず、以下だけ合わせてください。

```yaml
TRADE_DIAGNOSTICS_ALLOW_FALLBACK: "false"
TRADE_DIAGNOSTICS_FAIL_ON_DATA_QUALITY: "true"
TRADE_DIAGNOSTICS_STRICT_DISPLAY_RESOLUTION: "true"
```

## 重要な修正点

1. `TRADE_DIAGNOSTICS_RUN_ID=display` を実run_idへ解決します。
2. fallbackはデフォルト禁止です。
3. `trade_id`優先で重複排除します。
4. `realized_return_pct`をentry/exit価格から再計算します。
5. `prices_daily`の高値/安値からMFE/MAEを再計算します。
6. 全Exit理由UNKNOWN、全returnゼロ、全MFE/MAEゼロを品質エラーとして落とします。
7. Entry contextとしてfeatures/fundamentals/value/sector-relative情報を可能な範囲で付与します。
8. Agent別にcontext risk flagsを出します。

## 実行

```bash
python -m py_compile scripts/export_ai_arena_trade_diagnostics_jp.py
python scripts/export_ai_arena_trade_diagnostics_jp.py
```

## 推奨workflow入力

- `run_id`: `display`
- `allow_fallback`: `false`

fallbackをtrueにするのは、過去runをざっくり見るだけの調査用途に限定してください。ルール改善の分析には使わないでください。
