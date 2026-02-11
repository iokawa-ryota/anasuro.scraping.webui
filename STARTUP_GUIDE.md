# ユーザーセットアップガイド

このガイドは、一般ユーザー向けの手順です。  
通常は、フォルダ直下のファイルだけ見ていただければ運用できます。

## 1. フォルダ直下で使うもの

- `setup.bat`  
初回セットアップで使います。
- `start.bat`  
通常の起動で使います。
- `store_list.csv`  
店舗設定の保存先です。通常は直接編集しません。
- `data/`  
取得したHTMLが保存されます。
- `output/`  
整形後のCSVが出力されます。

`_internal/` は内部実装用のフォルダです。通常は操作不要です。

## 2. 初回セットアップ手順

1. `setup.bat` を実行します。  
2. `start.bat` を実行します。  
3. ブラウザ画面で「店舗設定を編集」を開き、店舗を登録または更新します。

## 3. 店舗設定について

日常運用では、店舗設定はWeb画面で行います。  
画面で保存した内容は、自動で `store_list.csv` に反映されます。  
通常は `store_list.csv` を直接編集する必要はありません。

## 4. 補足（復旧・メンテナンス時のみ）

何らかの理由で `store_list.csv` を直接編集する場合は、次のカラムが必要です。

- `store_name`
- `store_url`
- `data_directory`

```csv
store_name,store_url,data_directory
店舗A,https://example.com/store-a,.\data\store_a
店舗B,https://example.com/store-b,.\data\store_b
```

## 5. 停止方法

起動中のコンソールで `Ctrl + C` を押してください。
