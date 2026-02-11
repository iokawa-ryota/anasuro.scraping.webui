# anaslot-public-20260212

役割ごとに分離した構成です。

- `setup.bat` / `start.bat`: 起動用（ルート直下）
- `store_list.csv`: 店舗設定（ルート直下）
- `_internal/`: 内部スクリプト・プログラム本体・内部ログ
- `output/`: 整形済み出力
- `data/`: 取得HTMLの保存先

## ユーザー導線方針

- エンドユーザーが日常的に見る対象は、フォルダ直下のファイルだけを想定します。
- 内部管理ファイルは `_internal/` 配下に配置します。

## 最短起動

1. 初回のみ `setup.bat` を実行
2. 2回目以降は `start.bat` で起動

Windows（手動）:
- `start.bat`

手動:
- `python _internal/bin/setup_check.py`
- `python _internal/app/app.py`

詳細は `_internal/docs/README.md` を参照。

## 将来目標

- `_internal/docs/PRODUCT_GOALS.md` に最終目標と受け入れ条件を定義しています。
