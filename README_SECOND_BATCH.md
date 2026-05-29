# AI Arena JP 第二弾 完全版ファイル

## 上書き対象

- scripts/lib/arena_exporter_jp.py
- scripts/review_data_coverage_jp.py
- scripts/fetch_fundamentals_jp.py
- templates/ai_arena_summary_jp.html.j2
- templates/ai_arena_summary_jp.css

## 目的

第一弾で復旧した売買履歴生成を前提に、以下を強化する。

1. Coverage ReviewでAI Arenaの中核事故をcritical検知する。
2. Summary JSONに年間成績、月次、取引品質、ポートフォリオ、銘柄別寄与度、実行診断を含める。
3. Summary UIを「5秒で状況を理解できる」ダッシュボードに寄せる。
4. fetch_fundamentals_jp.pyが部分取得時にvalue_features_dailyを誤って全削除しないようにする。

## 実行順

第一弾適用済みの状態でこの第二弾を上書きしてください。
その後、GitHub Actionsで以下を実行します。

1. AI Arena JP season rebuild
2. AI Arena JP data coverage review

成功条件の目安:

- data coverage review の criticals=0
- summary/latest.json に portfolio / trade_stats / equity_overview が含まれる
- Summaryページで Open Positions / Allocation / Contribution が表示される
