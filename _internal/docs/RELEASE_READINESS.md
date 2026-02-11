# Release Readiness

この版は「プログラム本体」と「運用データ」を分離済みです。

- 起動用ファイルはルート直下に配置
- `store_list.csv` はルート直下に配置
- 内部実装は `_internal/` に集約
- 実行時生成物は `_internal/runtime/` に集約
- ユーザー編集対象は基本的に `store_list.csv` のみ

起動前チェック:
- `python _internal/bin/setup_check.py`
