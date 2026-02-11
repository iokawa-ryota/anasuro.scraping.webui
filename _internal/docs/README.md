# 配布版ドキュメント

## 目的

ユーザー混乱を防ぐため、プログラム本体と運用データを分離しています。

## 実フォルダ構成

```text
anaslot-public-20260212/
├─ setup.bat / start.bat          # ユーザー導線
├─ store_list.csv                 # ユーザー設定
├─ data/                          # HTML保存先
├─ output/                        # 整形CSV出力
└─ _internal/                     # 内部実装
   ├─ app/                        # Python本体 + UI
   ├─ bin/                        # 内部スクリプト/依存定義
   ├─ docs/                       # 内部ドキュメント
   └─ runtime/                    # ログ・一時CSV
```

## 初期設定

1. `pip install -r _internal/bin/requirements.txt`
2. `store_list.csv` を編集
3. `python _internal/bin/setup_check.py`
4. `python _internal/app/app.py`

## 補足

- エンドユーザーが日常的に見る対象はフォルダ直下のみを想定
- 実行時生成物（内部ログなど）は `_internal/runtime/` に出力されます

## 仕様方針

- 最終目標と進行方針: `_internal/docs/PRODUCT_GOALS.md`
