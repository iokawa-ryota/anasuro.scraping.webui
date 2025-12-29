# スロット店舗スクレイピング Web UI

選択された店舗のみをスクレイピングできる Web インターフェース付きのスクレイピングシステムです。

## 📋 ファイル構成

```
d:\Users\Documents\python\pycord\slot\
├── app.py                      # Flask バックエンド（Web サーバー）
├── index.html                  # フロントエンド（店舗選択画面）
├── anasuro_selective.py        # 選択店舗のスクレイピング処理
├── anasuro test.py             # 元のスクレイピングスクリプト
├── scraping_log.json           # 実行ログ記録ファイル
└── temp_store_list.xlsx        # 一時的な選択店舗リスト（自動生成）
```

## 🚀 セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install flask pandas openpyxl undetected-chromedriver selenium beautifulsoup4 webdriver-manager
```

### 2. 既存の店舗リスト Excel ファイルが必要

`D:/Users/Documents/python/saved_html/store_list.xlsx` に以下のカラムを含む必要があります：

| 必須カラム | 説明 |
|-----------|------|
| store_name | 店舗名 |
| store_url | 店舗の Web URL |
| data_directory | データ保存ディレクトリ |

**サンプル:**
```
store_name,store_url,data_directory
店舗A,https://example.com/storeA,D:/data/storeA
店舗B,https://example.com/storeB,D:/data/storeB
店舗C,https://example.com/storeC,D:/data/storeC
```

## 💻 使用方法

### 方法 1: Web UI を使用（推奨）

```bash
# Flask サーバーを起動
python app.py
```

ブラウザで `http://localhost:5000` にアクセスします。

**Web UI の操作:**

1. **店舗リストの表示**  
   左側にチェックボックス付きの店舗リストが表示されます

2. **店舗の選択**
   - チェックボックスをクリックして店舗を選択
   - 「全選択」ボタン: すべての店舗を選択
   - 「全解除」ボタン: すべての選択を解除

3. **スクレイピング実行**
   - 「スクレイピングを開始」ボタンをクリック
   - 選択された店舗のスクレイピングが開始
   - 処理状況がリアルタイムで表示

### 方法 2: コマンドラインから直接実行

```bash
# 一時的な Excel ファイルから店舗を読み込む
python anasuro_selective.py --use-temp

# 指定した Excel ファイルを使用
python anasuro_selective.py --file path/to/store_list.xlsx

# 特定の店舗を指定
python anasuro_selective.py "店舗A" "店舗B"
```

## 📊 データ フロー

```
┌─────────────────────┐
│   ブラウザ           │
│  (Web UI)           │
│  index.html         │
└──────────┬──────────┘
           │ (チェックボックス選択)
           ▼
┌─────────────────────┐
│   Flask サーバー      │
│   (app.py)          │
│  /api/stores       │ ◄─ 店舗リスト取得
│  /api/scrape       │ ◄─ スクレイピング開始
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  選択店舗 Excel 生成  │
│ (temp_store_list.xlsx)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ スクレイピング処理    │
│ (anasuro_selective.py)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  各店舗のデータ保存   │
│  (data_directory/)  │
└─────────────────────┘
```

## 🔧 動作の流れ

### Web UI での実行フロー

```
1. ユーザーがブラウザで http://localhost:5000 にアクセス
                    ↓
2. index.html が読み込まれる
                    ↓
3. JavaScript が /api/stores に GET リクエスト
                    ↓
4. app.py が store_list.xlsx から店舗リストを取得
                    ↓
5. 店舗リストが JSON で返される
                    ↓
6. フロントエンドがチェックボックス付きリストを表示
                    ↓
7. ユーザーが店舗を選択して「スクレイピングを開始」をクリック
                    ↓
8. JavaScript が選択された店舗リストを JSON で /api/scrape に POST
                    ↓
9. app.py が temp_store_list.csv を生成
                    ↓
10. anasuro_selective.py をサブプロセスで実行開始
                    ↓
11. Python スクリプトが選択店舗のみをスクレイピング
                    ↓
12. 完了メッセージが Web UI に返される
```

## 📝 設定ファイル

### app.py の設定

```python
# 設定セクション
STORE_LIST_PATH = "D:/Users/Documents/python/saved_html/store_list.csv"
SCRAPING_SCRIPT_PATH = "anasuro.py"  # または "anasuro_selective.py"
LOG_FILE = "scraping_log.json"
```

必要に応じて以下の部分を変更してください：

```python
# ポート番号を変更
app.run(debug=True, host='localhost', port=8080)

# リモートアクセスを許可する場合
app.run(debug=False, host='0.0.0.0', port=5000)
```

## 🐛 トラブルシューティング

### 店舗リストが表示されない

1. `store_list.xlsx` のパスを確認
2. Excel ファイルのカラム名を確認（store_name, store_url, data_directory）
3. Python コンソールで確認:
   ```python
   import pandas as pd
   df = pd.read_excel("D:/Users/Documents/python/saved_html/store_list.xlsx")
   print(df.columns)
   print(df)
   ```

### スクレイピングが開始されない

1. `anasuro.py` またはスクレイピングスクリプトの存在確認
2. ブラウザの開発者ツール（F12）でコンソールを確認
3. Python の実行権限を確認
4. ログファイル `scraping_log.json` を確認

### Chrome ドライバーエラー

```
undetected-chromedriver で Chrome のバージョン自動検出に失敗した場合
```

**解決策:**
```bash
# Chrome を最新版にアップデート
# または手動で ChromeDriver をインストール
pip install --upgrade undetected-chromedriver
```

### ポート 5000 が既に使用中

```bash
# 別のポート番号で起動
# app.py の最後の行を以下に変更：
app.run(debug=True, host='localhost', port=8080)
```

## 📚 API リファレンス

### GET /api/stores

店舗リストを取得

**レスポンス例:**
```json
[
  {
    "name": "店舗A",
    "url": "https://example.com/storeA",
    "directory": "D:/data/storeA"
  },
  {
    "name": "店舗B",
    "url": "https://example.com/storeB",
    "directory": "D:/data/storeB"
  }
]
```

### POST /api/scrape

スクレイピングを開始

**リクエスト例:**
```json
{
  "stores": ["店舗A", "店舗B"]
}
```

**レスポンス例:**
```json
{
  "message": "2 個の店舗のスクレイピングを実行しました",
  "selected_count": 2,
  "output": "...(出力の最後の500文字)..."
}
```

### GET /api/logs

実行ログを取得（最新20件）

**レスポンス例:**
```json
[
  {
    "timestamp": "2025-01-15T10:30:45.123456",
    "selected_stores": ["店舗A", "店舗B"],
    "count": 2,
    "temp_file": "temp_store_list.csv"
  }
]
```

## 🔐 セキュリティ上の注意

本番環境での使用時は以下の対策を推奨します：

1. **デバッグモードを無効化**
   ```python
   app.run(debug=False, host='localhost', port=5000)
   ```

2. **HTTPS を有効化**（プロキシサーバー経由など）

3. **認証機能の追加**
   ```python
   from flask_httpauth import HTTPBasicAuth
   auth = HTTPBasicAuth()
   ```

4. **CSRF 保護**
   ```python
   from flask_wtf.csrf import CSRFProtect
   csrf = CSRFProtect(app)
   ```

5. **ファイアウォール設定**
   - localhost からのアクセスのみに制限
   - VPN 経由でのアクセスに制限

## 💡 カスタマイズ例

### タイムアウト時間を変更

```python
# app.py の scrape 関数内
result = subprocess.run(
    [sys.executable, SCRAPING_SCRIPT_PATH],
    capture_output=True,
    text=True,
    timeout=7200  # 2 時間に変更
)
```

### スクレイピングスクリプトを変更

```python
# app.py の SCRAPING_SCRIPT_PATH を変更
SCRAPING_SCRIPT_PATH = "anasuro_selective.py"
```

### UI のスタイルを変更

`index.html` の `<style>` セクションを編集してカスタマイズできます。

## 📞 サポート

エラーメッセージが表示される場合：

1. ブラウザコンソール（F12）でエラーメッセージを確認
2. Python コンソールのエラー出力を確認
3. `scraping_log.json` でログを確認

## 📄 ライセンス

元のスクレイピングスクリプトに準じます。

---

**最終更新**: 2025-01-15
