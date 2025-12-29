from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from datetime import datetime
import subprocess
import sys
import json

app = Flask(__name__, static_folder='.')
app.config['JSON_AS_ASCII'] = False

# 設定
STORE_LIST_PATH = "D:/Users/Documents/python/saved_html/store_list.csv"
SCRAPING_SCRIPT_PATH = "anasuro.py"  # スクレイピング処理メインスクリプト
LOG_FILE = "scraping_log.json"

# 店舗リストをメモリにキャッシュ
store_cache = None
last_load_time = None

def load_stores():
    """CSV から店舗リストを読み込む（エンコーディング自動フォールバック）"""
    global store_cache, last_load_time

    try:
        if not os.path.exists(STORE_LIST_PATH):
            return []

        df = None
        for enc in ("utf-8", "utf-8-sig", "cp932"):
            try:
                df = pd.read_csv(STORE_LIST_PATH, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            raise RuntimeError("store_list.csv の読み込みに失敗しました（encoding不一致）")

        store_cache = [
            {
                "name": str(row.get("store_name", f"店舗{i}")),
                "url": str(row.get("store_url", "")),
                "directory": str(row.get("data_directory", ""))
            }
            for i, (_, row) in enumerate(df.iterrows())
        ]
        last_load_time = datetime.now()
        return store_cache
    except Exception as e:
        print(f"[エラー] 店舗リスト読み込み失敗: {e}")
        return []

@app.route('/')
def index():
    """HTML フロントエンドを提供"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "index.html が見つかりません", 404

@app.route('/api/stores', methods=['GET'])
def get_stores():
    """店舗リストを JSON で返す"""
    stores = load_stores()
    return jsonify(stores)

@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    """
    選択された店舗のスクレイピングを開始
    
    リクエスト例:
    {
        "stores": ["店舗A", "店舗B"]
    }
    """
    try:
        data = request.get_json()
        selected_store_names = data.get("stores", [])
        
        if not selected_store_names:
            return jsonify({"error": "店舗が選択されていません"}), 400
        
        # 全店舗リストから選択された店舗に対応する行を抽出
        all_stores = load_stores()
        selected_stores_df = pd.DataFrame([
            store for store in all_stores 
            if store["name"] in selected_store_names
        ])
        
        if selected_stores_df.empty:
            return jsonify({"error": "選択された店舗が見つかりません"}), 400
        
        # 一時的な CSV ファイルを作成（Excel対応のUTF-8 BOM付き）
        temp_store_list = "temp_store_list.csv"
        selected_stores_df.to_csv(temp_store_list, index=False, encoding='utf-8-sig')
        
        # ログに記録
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "selected_stores": selected_store_names,
            "count": len(selected_store_names),
            "temp_file": temp_store_list
        }
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        # バックグラウンドでスクレイピングスクリプトを実行
        # (実運用では Celery などのタスクキューを使用することを推奨)
        try:
            result = subprocess.run(
                [sys.executable, SCRAPING_SCRIPT_PATH],
                capture_output=True,
                text=True,
                timeout=3600  # 最大 1 時間
            )
            
            output = result.stdout + "\n" + result.stderr
            return jsonify({
                "message": f"{len(selected_store_names)} 個の店舗のスクレイピングを実行しました",
                "selected_count": len(selected_store_names),
                "output": output[-500:] if output else ""  # 最後の 500 文字
            })
        except subprocess.TimeoutExpired:
            return jsonify({
                "message": f"{len(selected_store_names)} 個の店舗のスクレイピングを開始しました（タイムアウト）"
            }), 202  # Accepted
        except Exception as e:
            return jsonify({
                "error": f"スクレイピング実行エラー: {str(e)}"
            }), 500
        
    except Exception as e:
        print(f"[エラー] API エラー: {e}")
        return jsonify({"error": f"処理エラー: {str(e)}"}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """実行ログを取得"""
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify([])
        
        logs = []
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except:
                    pass
        
        return jsonify(logs[-20:])  # 最新 20 件を返す
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/format-offline', methods=['POST'])
def format_offline():
    """
    オフラインExcel整形処理を実行
    
    リクエスト例:
    {
        "stores": ["店舗A", "店舗B"]  // 空配列の場合は全店舗対象
    }
    """
    try:
        data = request.get_json()
        selected_store_names = data.get("stores", [])
        
        # 全店舗リストを読み込み
        all_stores = load_stores()
        
        if selected_store_names:
            # 選択店舗のみ
            target_stores = [
                store for store in all_stores 
                if store["name"] in selected_store_names
            ]
        else:
            # 全店舗対象
            target_stores = all_stores
        
        if not target_stores:
            return jsonify({"error": "店舗が見つかりません"}), 400
        
        print(f"[整形] {len(target_stores)} 個の店舗を処理します")
        
        # オフライン整形スクリプトを実行
        try:
            result = subprocess.run(
                [sys.executable, "offline_scraping.py"],
                capture_output=True,
                text=True,
                timeout=1800  # 最大 30 分
            )
            
            output = result.stdout + "\n" + result.stderr
            
            # ログに記録
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "format_offline",
                "selected_stores": selected_store_names if selected_store_names else "all",
                "count": len(target_stores)
            }
            
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            return jsonify({
                "message": f"{len(target_stores)} 個の店舗のExcel整形を実行しました",
                "selected_count": len(target_stores),
                "output": output[-500:] if output else ""
            })
        except subprocess.TimeoutExpired:
            return jsonify({
                "message": f"{len(target_stores)} 個の店舗の整形処理を開始しました（処理中）"
            }), 202
        except Exception as e:
            return jsonify({
                "error": f"整形処理実行エラー: {str(e)}"
            }), 500
        
    except Exception as e:
        print(f"[エラー] API エラー: {e}")
        return jsonify({"error": f"処理エラー: {str(e)}"}), 500

@app.route('/api/stores/reorder', methods=['POST'])
def reorder_stores():
    """店舗CSVの並び順を更新（UTF-8 BOMで保存）"""
    try:
        data = request.get_json()
        order = data.get('order', [])
        if not order or not isinstance(order, list):
            return jsonify({"error": "並び順が不正です"}), 400

        # CSV 読み込み（エンコーディング自動フォールバック）
        df = None
        for enc in ("utf-8", "utf-8-sig", "cp932"):
            try:
                df = pd.read_csv(STORE_LIST_PATH, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            return jsonify({"error": "store_list.csv の読み込みに失敗しました"}), 500

        # data_directory 列の確認
        col = 'data_directory' if 'data_directory' in df.columns else (
            'directory' if 'directory' in df.columns else None
        )
        if col is None:
            return jsonify({"error": "CSVに data_directory 列がありません"}), 400

        # 既存順序を保持するためのインデックス列
        df['__orig_index__'] = range(len(df))

        # 指定順序に基づいて並び替え（存在するもののみ）
        dir_to_index = {str(row[col]): idx for idx, (_, row) in enumerate(df.iterrows())}
        ordered_indices = []
        for d in order:
            idx = dir_to_index.get(str(d))
            if idx is not None:
                ordered_indices.append(idx)

        # 指定がなかった残りは元の順序で後ろに付与
        remaining_indices = [idx for idx in df['__orig_index__'].tolist() if idx not in ordered_indices]
        final_indices = ordered_indices + remaining_indices

        df = df.iloc[final_indices].drop(columns=['__orig_index__'])

        # UTF-8 BOMで保存（Excel向け）
        df.to_csv(STORE_LIST_PATH, index=False, encoding='utf-8-sig')

        # キャッシュ更新
        load_stores()

        return jsonify({"message": f"並び順を保存しました（{len(ordered_indices)} 件を並べ替え）"})
    except Exception as e:
        print(f"[エラー] 並び順保存失敗: {e}")
        return jsonify({"error": f"並び順保存エラー: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("スロット店舗スクレイピング Web UI")
    print("=" * 50)
    print(f"サーバーが起動しました")
    print(f"ブラウザで http://localhost:5000 にアクセスしてください")
    print("=" * 50)
    
    app.run(debug=True, host='localhost', port=5000)
