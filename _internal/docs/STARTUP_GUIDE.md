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
- 通常運用でユーザーが直接編集するのは `store_list.csv` のみです。
- ユーザーが日常的に見る対象はフォルダ直下のみを想定します。
- `_internal/` 配下は内部用途のため、通常は編集しません。

## Windows

- 初回セットアップ: `setup.bat`
- 通常起動: `start.bat`

## 手動起動

```bash
python _internal/bin/setup_check.py
python _internal/app/app.py
```

## 停止

- コンソール起動: `Ctrl + C`
