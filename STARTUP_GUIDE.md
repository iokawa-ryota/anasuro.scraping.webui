# ユーザーセットアップガイド

このファイルはエンドユーザー向けです。通常はフォルダ直下のファイルだけ見れば運用できます。

## 1. 使うファイル（フォルダ直下）

- `setup.bat` 初回セットアップ
- `start.bat` 通常起動
- `store_list.csv` 店舗設定
- `data/` 取得したHTML
- `output/` 整形後CSV

`_internal/` は内部実装です。通常は編集不要です。

## 2. 初回セットアップ

1. `setup.bat` を実行
2. 必要に応じて `store_list.csv` を編集
3. `start.bat` で起動

## 3. 店舗設定

必須カラム:

- `store_name`
- `store_url`
- `data_directory`

例:

```csv
store_name,store_url,data_directory
店舗A,https://example.com/store-a,.\data\store_a
店舗B,https://example.com/store-b,.\data\store_b
```

通常運用ではWeb画面の「店舗設定を編集」を優先してください。

## 4. 停止方法

- 起動中のコンソールで `Ctrl + C`
