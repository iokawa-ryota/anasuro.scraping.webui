# テスト実施結果（2026-02-14）

## 実行方法

- コマンド: `python _internal/test/run_api_smoke_tests.py`
- 対象: API中心のスモークテスト（自動実行可能な範囲）

## 結果サマリ

- 初回実行: 12項目中 11項目合格（不合格 1）
- 修正後再実行: 12項目中 12項目合格（不合格 0）

## 項目別結果

- PASS: `GET /api/stores`（店舗一覧取得）
- PASS: `POST /api/stores/save` 不正入力（400）
- PASS: `POST /api/stores/save` 正常保存（空名の自動補完）
- PASS: `POST /api/stores/reorder` 並び替え保存
- PASS: `POST /api/scrape` 正常系（`job_id`返却 -> `completed/100`）
- PASS: `POST /api/scrape` 異常系（監視タイムアウト想定 -> `failed`）
- PASS: `POST /api/scrape` 店舗未選択（400）
- PASS: `POST /api/scrape` 存在しない店舗（400）
- PASS: `GET /api/logs`（ログ取得）
- PASS: `POST /api/format-offline` 基本実行
- FAIL: `POST /api/format-offline` 失敗時ステータス
- PASS: `GET /`（`index.html`欠損時404）

## 不合格の詳細

- 対象: `POST /api/format-offline` 失敗時ステータス
- 期待: 失敗時にエラー（4xx/5xx）を返す
- 実際: 失敗してもHTTP 200が返るケースがある
- 補足: `subprocess.run` の戻り値 `returncode != 0` をエラーとして扱っていないため

## 修正と再テスト

- 修正箇所: `_internal/app/app.py` `format_offline()`  
- 内容: `result.returncode != 0` の場合に `HTTP 500` を返すよう変更
- 再実行結果: `12/12 PASS`

## 未実施（手動/環境依存）

- `setup.bat` 実行完了の実機確認
- Python未導入PCでの導線確認
- `start.bat` からブラウザ操作のE2E
- 実HTML保存の中身確認（`data/`）
- 実CSV生成物の品質確認（`output/`、列品質、欠損/重複）
- 店舗件数負荷（1/10/50）の実時間計測
- 復旧系（途中停止 -> 再実行）
