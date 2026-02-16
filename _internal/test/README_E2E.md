# UI E2E テスト（Playwright）

このディレクトリ配下で、フロントUIのE2Eテストを実行できます。  
既存の API スモークテストとは別に、画面操作の回帰を確認します。

## 1. 初回セットアップ

```powershell
python -m pip install -r _internal/test/requirements-e2e.txt
python -m playwright install chromium
```

## 2. 実行

```powershell
python _internal/test/run_ui_e2e_playwright.py
```

## 3. テスト対象（現状）

- 店舗設定パネルを開けること
- 削除確認モーダル（キャンセル/確定）の挙動
- 行追加して保存できること

## 補足

- 実行中は Flask サーバーをテスト側で自動起動します（`127.0.0.1:5010`）。
- `store_list.csv` はテスト用内容に一時置き換えますが、終了時に元へ復元します。
