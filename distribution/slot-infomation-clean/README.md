# slot-infomation

店舗データをまとめて、CSVファイルとして保存するためのツールです。  
一般ユーザー向けに、運用で必要な情報をこのREADMEにまとめています。

## このツールの動作

1. 指定した店舗のデータをアナスロから取得し、HTMLファイルとして保存します
   （保存先: `data/`）
2. 保存したHTMLファイルを読み込み、CSVファイルに変換します
   （保存先: `output/`）

## 前提条件

- Windowsパソコンを使用している
- Python がインストール済み（`setup.bat` 実行時に利用）

## フォルダ直下で使うもの

- `setup.bat`: 初回セットアップで使います
- `start.bat`: 通常の起動で使います
- `store_list.csv`: 店舗設定の保存先です（通常は直接編集しません）
- `data/`: 取得したHTMLの保存先です
- `output/`: 作成したCSVの保存先です

`_internal/` は内部実装用フォルダです。通常は操作不要です。

## 初回セットアップ

1. このフォルダを開く
2. `setup.bat` をダブルクリック
3. 画面に「Setup complete」が出たら、`start.bat` をダブルクリック
4. ブラウザ画面で「店舗設定を編集」を開き、店舗を登録または更新

## 起動方法

1. `start.bat` をダブルクリック
2. 自動でブラウザが開かない場合は、ブラウザで `http://localhost:5000` を開く
3. 画面上で必要な操作を行う

## 店舗設定について

- 日常運用では、店舗設定はWeb画面で行います
- 画面で保存した内容は `store_list.csv` に自動反映されます
- 通常は `store_list.csv` を直接編集する必要はありません

## 補足（復旧・メンテナンス時のみ）

`store_list.csv` を直接編集する場合は、次のカラムが必要です。

- `store_name`
- `store_url`
- `data_directory`

```csv
store_name,store_url,data_directory
店舗A,https://example.com/store-a,.\data\store_a
店舗B,https://example.com/store-b,.\data\store_b
```

## 終了方法

- 黒い画面（コンソール）を選んだ状態で `Ctrl + C` を押します

## 困ったとき

- `setup.bat` でエラーが出る場合は、Pythonが入っていない可能性があります
