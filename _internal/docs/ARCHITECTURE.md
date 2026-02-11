# 設計書（Architecture）

## 1. 目的

エンドユーザーの操作対象を最小化し、内部実装と運用データを分離する。

## 2. ディレクトリ設計

```text
project-root/
├─ setup.bat
├─ start.bat
├─ store_list.csv
├─ data/
├─ output/
└─ _internal/
   ├─ app/
   ├─ bin/
   ├─ docs/
   ├─ devtools/
   └─ runtime/
```

## 3. 主要コンポーネント

- `_internal/app/app.py`
  - Flask APIとUI配信
  - `store_list.csv` の読込/保存
  - スクレイピング実行と整形実行の入口
- `_internal/app/anasuro_selective.py`
  - 店舗一覧URLからHTMLを `data/` に保存
- `_internal/app/offline-scraing.py`
  - `data/` のHTMLを解析して `output/` にCSV出力
- `_internal/bin/setup_check.py`
  - 起動前の依存確認

## 4. データフロー

1. ユーザーがWeb UIで店舗選択
2. スクレイピングで `data/<store>/YYYY-MM-DD.html` を保存
3. Excel自動整形で `output/<store>-slotdata.csv` を生成/更新

## 5. 運用方針

- ユーザーが直接触るのは原則ルート直下のみ
- `_internal/` は実装詳細として扱い、通常運用での編集対象にしない
- 開発専用機能は `/_internal/devtools/` に隔離し、配布時に除去可能にする

## 6. 未解決/今後

- 長時間処理の安定した進捗通知の再設計（必要時）
- 設定値の完全Web UI化（`store_list.csv` 直編集依存の削減）
