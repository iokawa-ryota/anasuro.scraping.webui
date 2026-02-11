from flask import Flask, request, jsonify
import pandas as pd
import os
from datetime import datetime
import subprocess
import sys
import json

APP_DIR = os.path.dirname(os.path.abspath(__file__))
INTERNAL_ROOT = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(INTERNAL_ROOT)
RUNTIME_DIR = os.path.join(INTERNAL_ROOT, "runtime")
os.makedirs(RUNTIME_DIR, exist_ok=True)

app = Flask(__name__, static_folder='.')
app.config['JSON_AS_ASCII'] = False

STORE_LIST_PATH = os.path.join(PROJECT_ROOT, "store_list.csv")
TEMP_STORE_LIST_PATH = os.getenv("TEMP_STORE_LIST_PATH", os.path.join(RUNTIME_DIR, "temp_store_list.csv"))
SCRAPING_SCRIPT_PATH = os.getenv("SCRAPING_SCRIPT_PATH", os.path.join(APP_DIR, "anasuro_selective.py"))
OFFLINE_SCRIPT_PATH = os.getenv("OFFLINE_SCRIPT_PATH", os.path.join(APP_DIR, "offline-scraing.py"))
LOG_FILE = os.getenv("LOG_FILE", os.path.join(RUNTIME_DIR, "scraping_log.json"))
COMPLETED_STORES_PATH = os.getenv("COMPLETED_STORES_PATH", os.path.join(RUNTIME_DIR, "completed_stores.json"))


def load_stores():
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

        stores = []
        for i, (_, row) in enumerate(df.iterrows(), start=1):
            stores.append({
                "name": str(row.get("store_name") or row.get("name") or f"店舗{i}"),
                "url": str(row.get("store_url") or row.get("url") or ""),
                "directory": str(row.get("data_directory") or row.get("directory") or ""),
            })
        return stores
    except Exception as e:
        print(f"[エラー] 店舗リスト読み込み失敗: {e}")
        return []


@app.route('/')
def index():
    try:
        with open(os.path.join(APP_DIR, 'index.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return "index.html が見つかりません", 404


@app.route('/api/stores', methods=['GET'])
def get_stores():
    return jsonify(load_stores())


@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    try:
        data = request.get_json(silent=True) or {}
        selected_store_names = data.get("stores", [])

        if not selected_store_names:
            return jsonify({"error": "店舗が選択されていません"}), 400

        all_stores = load_stores()
        selected_stores_df = pd.DataFrame([
            store for store in all_stores if store["name"] in selected_store_names
        ])

        if selected_stores_df.empty:
            return jsonify({"error": "選択された店舗が見つかりません"}), 400

        os.makedirs(os.path.dirname(TEMP_STORE_LIST_PATH), exist_ok=True)
        selected_stores_df.to_csv(TEMP_STORE_LIST_PATH, index=False, encoding='utf-8-sig')

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "selected_stores": selected_store_names,
            "count": len(selected_store_names),
            "temp_file": TEMP_STORE_LIST_PATH,
        }
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        try:
            result = subprocess.run(
                [sys.executable, SCRAPING_SCRIPT_PATH],
                capture_output=True,
                text=True,
                timeout=3600,
                cwd=PROJECT_ROOT,
            )
            output = result.stdout + "\n" + result.stderr
            return jsonify({
                "message": f"{len(selected_store_names)} 個の店舗のスクレイピングを実行しました",
                "selected_count": len(selected_store_names),
                "output": output[-500:] if output else "",
            })
        except subprocess.TimeoutExpired:
            return jsonify({"message": f"{len(selected_store_names)} 個の店舗のスクレイピングを開始しました（タイムアウト）"}), 202
        except Exception as e:
            return jsonify({"error": f"スクレイピング実行エラー: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"処理エラー: {str(e)}"}), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify([])

        logs = []
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except Exception:
                    pass
        return jsonify(logs[-20:])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/format-offline', methods=['POST'])
def format_offline():
    try:
        result = subprocess.run(
            [sys.executable, OFFLINE_SCRIPT_PATH],
            capture_output=True,
            text=True,
            timeout=1800,
            cwd=PROJECT_ROOT,
        )
        output = result.stdout + "\n" + result.stderr

        completed_stores = []
        processed_stores = []
        if os.path.exists(COMPLETED_STORES_PATH):
            try:
                with open(COMPLETED_STORES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    completed_stores = data.get("completed", [])
                    processed_stores = data.get("processed", [])
            except Exception:
                pass

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "format_offline",
            "completed_count": len(completed_stores),
            "processed_count": len(processed_stores),
        }
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return jsonify({
            "message": "Excel 自動整形を実行しました",
            "output": output[-500:] if output else "",
            "completed_stores": completed_stores,
            "processed_stores": processed_stores,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"message": "Excel 自動整形処理を開始しました（処理中）", "completed_stores": []}), 202
    except Exception as e:
        return jsonify({"error": f"整形処理実行エラー: {str(e)}", "completed_stores": []}), 500


@app.route('/api/stores/reorder', methods=['POST'])
def reorder_stores():
    try:
        data = request.get_json(silent=True) or {}
        order = data.get('order', [])
        if not order or not isinstance(order, list):
            return jsonify({"error": "並び順が不正です"}), 400

        df = None
        for enc in ("utf-8", "utf-8-sig", "cp932"):
            try:
                df = pd.read_csv(STORE_LIST_PATH, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            return jsonify({"error": "store_list.csv の読み込みに失敗しました"}), 500

        col = 'data_directory' if 'data_directory' in df.columns else ('directory' if 'directory' in df.columns else None)
        if col is None:
            return jsonify({"error": "CSVに data_directory 列がありません"}), 400

        df['__orig_index__'] = range(len(df))
        dir_to_index = {str(row[col]): idx for idx, (_, row) in enumerate(df.iterrows())}

        ordered_indices = []
        for d in order:
            idx = dir_to_index.get(str(d))
            if idx is not None:
                ordered_indices.append(idx)

        remaining_indices = [idx for idx in df['__orig_index__'].tolist() if idx not in ordered_indices]
        final_indices = ordered_indices + remaining_indices

        df = df.iloc[final_indices].drop(columns=['__orig_index__'])
        df.to_csv(STORE_LIST_PATH, index=False, encoding='utf-8-sig')

        return jsonify({"message": f"並び順を保存しました（{len(ordered_indices)} 件を並べ替え）"})
    except Exception as e:
        return jsonify({"error": f"並び順保存エラー: {str(e)}"}), 500


if __name__ == '__main__':
    host = os.getenv("FLASK_HOST", "localhost")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"

    print("=" * 50)
    print("スロット店舗スクレイピング Web UI")
    print("=" * 50)
    print(f"ブラウザで http://{host}:{port} にアクセスしてください")
    print("=" * 50)

    app.run(debug=debug, host=host, port=port)

