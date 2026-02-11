# 起動ガイド

## ユーザーが設定する部分

- 編集するファイル: `store_list.csv`（作業フォルダ直下）
- 必須カラム:
  - `store_name`: 店舗名
  - `store_url`: 店舗URL
  - `data_directory`: 取得HTMLの保存先フォルダ

例:

```csv
store_name,store_url,data_directory
店舗A,https://example.com/store-a,.\data\store_a
店舗B,https://example.com/store-b,.\data\store_b
```

注意:
- 通常運用では、店舗設定はWeb画面の「店舗設定を編集」から変更できます。
- 必要な場合のみ `store_list.csv` を直接編集してください。
- ユーザーが日常的に見る対象はフォルダ直下のみを想定します。
- `_internal/` 配下は内部用途のため、通常は編集しません。

## Windows

- 初回セットアップ: `setup.bat`
- 通常起動: `start.bat`

## テストモード（開発用）

- 画面に「テストモード（件数制限）」が表示される場合のみ利用できます。
- ON にすると、スクレイピングは各店舗の**最新3日分**のみ取得します。
- 配布時に不要なら `_internal/devtools/test_mode/` フォルダごと削除してください。

## 手動起動

```bash
python _internal/bin/setup_check.py
python _internal/app/app.py
```

## 停止

- コンソール起動: `Ctrl + C`
