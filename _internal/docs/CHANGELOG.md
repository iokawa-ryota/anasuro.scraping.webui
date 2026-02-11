# CHANGELOG

このプロジェクトの主要な変更履歴を管理します。

## 2026-02-12

### 配布向け構成の整理

- ルート直下を最小化し、内部実装を `_internal/` に集約
- ユーザー導線を `setup.bat` / `start.bat` に統一
- `store_list.csv` をルート直下で参照するよう統一

### Web UI

- 店舗一覧の選択UIを実装・改善
- 店舗設定をブラウザから編集して `store_list.csv` に保存可能化
- 並び順保存（CSV反映）機能を追加
- 入力フォームのレイアウト崩れを修正

### スクレイピング/整形

- テストモード（最新3日制限）を `/_internal/devtools/test_mode/` に分離
- Excel自動整形の出力先を `output/` 直下に統一
- 整形実行中メッセージを `csvを生成しています。` に変更
- 出力CSV列名を `Total` から `total` に変更（既存CSV互換あり）

### ドキュメント

- 目標定義を `PRODUCT_GOALS.md` に整理
- 本ファイル（変更履歴の一本化）を追加
- ユーザー向け `STARTUP_GUIDE.md` をルート直下運用に変更
- `RELEASE_READINESS.md` の内容を本ファイルへ統合し、ファイルは廃止

### リリース準備状態（統合内容）

- 起動用ファイルはルート直下に配置
- `store_list.csv` はルート直下に配置
- 内部実装は `_internal/` に集約
- 実行時生成物は `_internal/runtime/` に集約
- ユーザー編集対象は基本 `store_list.csv`
- 起動前チェック: `python _internal/bin/setup_check.py`
