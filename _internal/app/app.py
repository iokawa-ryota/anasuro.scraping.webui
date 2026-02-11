from flask import Flask, request, jsonify, make_response
import pandas as pd
import os
from datetime import datetime
import subprocess
import sys
import json
import importlib.util
from flask import send_file
import threading
import uuid
import re
from collections import deque

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
JOBS = {}
JOBS_LOCK = threading.Lock()

TEST_MODE_AVAILABLE = False
TEST_MODE_MAX_DAYS = 3
TEST_MODE_UI_URL = None
TEST_MODE_MODULE_PATH = os.path.join(INTERNAL_ROOT, "devtools", "test_mode", "backend.py")
TEST_MODE_UI_PATH = os.path.join(INTERNAL_ROOT, "devtools", "test_mode", "ui.js")

if os.path.exists(TEST_MODE_MODULE_PATH):
    try:
        spec = importlib.util.spec_from_file_location("dev_test_mode", TEST_MODE_MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "get_config"):
            cfg = module.get_config()
            TEST_MODE_AVAILABLE = bool(cfg.get("enabled", False))
            TEST_MODE_MAX_DAYS = int(cfg.get("max_days_per_store", 3))
        else:
            TEST_MODE_AVAILABLE = bool(getattr(module, "ENABLE_TEST_MODE", False))
            TEST_MODE_MAX_DAYS = int(getattr(module, "MAX_DAYS_PER_STORE", 3))
        if TEST_MODE_AVAILABLE and os.path.exists(TEST_MODE_UI_PATH):
            TEST_MODE_UI_URL = "/devtools/test_mode/ui.js"
    except Exception as e:
        print(f"[警告] devtools test_mode backend 読み込み失敗: {e}")


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

def save_stores(stores):
    """
    ブラウザ編集結果を store_list.csv に保存する。
    stores: [{"name": "...", "url": "...", "directory": "..."}, ...]
    """
    normalized = []
    for i, s in enumerate(stores, start=1):
        name = str((s.get("name") or "").strip())
        url = str((s.get("url") or "").strip())
        directory = str((s.get("directory") or "").strip())
        if not name:
            name = f"店舗{i}"
        normalized.append({
            "store_name": name,
            "store_url": url,
            "data_directory": directory,
        })

    df = pd.DataFrame(normalized, columns=["store_name", "store_url", "data_directory"])
    df.to_csv(STORE_LIST_PATH, index=False, encoding="utf-8-sig")

def _set_job(job_id, **kwargs):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return
        job.update(kwargs)

def _get_job_field(job_id, key, default=None):
    with JOBS_LOCK:
        job = JOBS.get(job_id) or {}
        return job.get(key, default)

def _run_scrape_job(job_id, cmd):
    marker = re.compile(r"__PROGRESS__\s+store\s+(\d+)/(\d+)")
    marker_store_start = re.compile(r"__PROGRESS__\s+store_start\s+(\d+)/(\d+)(?:\s+(.+))?")
    marker_pct = re.compile(r"__PROGRESS__\s+pct\s+(\d{1,3})(?:\s+(.+))?")
    output_tail = deque(maxlen=200)
    try:
        _set_job(job_id, status="running", progress=0, message="スクレイピング処理を開始しました")
        proc = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        for line in proc.stdout:
            line = line.rstrip("\n")
            output_tail.append(line)
            m = marker.search(line)
            if m:
                current = int(m.group(1))
                total = max(1, int(m.group(2)))
                progress = min(99, int((current / total) * 100))
                _set_job(
                    job_id,
                    progress=progress,
                    message=f"スクレイピング処理を実行中... {progress}%",
                    store_done=min(current, total),
                    store_total=total,
                )
                continue

            m_start = marker_store_start.search(line)
            if m_start:
                current_store = min(max(1, int(m_start.group(1))), max(1, int(m_start.group(2))))
                total = max(1, int(m_start.group(2)))
                store_name = (m_start.group(3) or "").strip()
                start_msg = f"店舗処理中: {current_store}/{total}"
                if store_name:
                    start_msg = f"{start_msg} ({store_name})"
                _set_job(
                    job_id,
                    store_current=current_store,
                    store_total=total,
                    message=start_msg,
                )
                continue

            m_pct = marker_pct.search(line)
            if m_pct:
                progress = min(99, max(0, int(m_pct.group(1))))
                detail = (m_pct.group(2) or "").strip()
                message = f"スクレイピング処理を実行中... {progress}%"
                if detail:
                    message = f"{message} ({detail})"
                _set_job(job_id, progress=progress, message=message)

        return_code = proc.wait()
        joined_output = "\n".join(output_tail)
        if return_code == 0:
            _set_job(
                job_id,
                status="completed",
                progress=100,
                message="スクレイピング処理が完了しました",
                store_done=int(_get_job_field(job_id, "store_total", 0) or 0),
                output=joined_output[-4000:],
                completed_at=datetime.now().isoformat(),
            )
        else:
            _set_job(
                job_id,
                status="failed",
                progress=0,
                message="スクレイピング処理に失敗しました",
                output=joined_output[-4000:],
                completed_at=datetime.now().isoformat(),
            )
    except Exception as e:
        _set_job(
            job_id,
            status="failed",
            progress=0,
            message=f"スクレイピング実行エラー: {str(e)}",
            completed_at=datetime.now().isoformat(),
        )


@app.route('/')
def index():
    try:
        with open(os.path.join(APP_DIR, 'index.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        resp = make_response(html)
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    except Exception:
        return "index.html が見つかりません", 404


@app.route('/api/stores', methods=['GET'])
def get_stores():
    return jsonify(load_stores())

@app.route('/api/ui-config', methods=['GET'])
def get_ui_config():
    return jsonify({
        "test_mode_available": TEST_MODE_AVAILABLE,
        "test_mode_max_days": TEST_MODE_MAX_DAYS,
        "test_mode_ui_url": TEST_MODE_UI_URL,
    })

@app.route('/devtools/test_mode/ui.js', methods=['GET'])
def devtools_test_mode_ui():
    if not (TEST_MODE_AVAILABLE and os.path.exists(TEST_MODE_UI_PATH)):
        return jsonify({"error": "Not Found"}), 404
    return send_file(TEST_MODE_UI_PATH, mimetype="application/javascript")

@app.route('/api/stores/save', methods=['POST'])
def save_stores_api():
    try:
        data = request.get_json(silent=True) or {}
        stores = data.get("stores", [])
        if not isinstance(stores, list):
            return jsonify({"error": "stores は配列で指定してください"}), 400

        save_stores(stores)
        return jsonify({"message": f"{len(stores)} 件の店舗設定を保存しました"})
    except Exception as e:
        return jsonify({"error": f"店舗設定の保存に失敗しました: {str(e)}"}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({"error": "job not found"}), 404
        return jsonify(job)


@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    try:
        data = request.get_json(silent=True) or {}
        selected_store_names = data.get("stores", [])
        options = data.get("options", {}) or {}
        requested_test_mode = bool(options.get("test_mode", False))
        max_stores = int(options.get("max_stores", 0) or 0)
        max_days_per_store = int(options.get("max_days_per_store", 0) or 0)

        # devtools test_mode が有効な場合のみ、テストモード制限を適用
        if TEST_MODE_AVAILABLE and requested_test_mode:
            max_days_per_store = TEST_MODE_MAX_DAYS

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

        # -u で標準出力バッファを無効化し、進捗をリアルタイム取得する
        cmd = [sys.executable, "-u", SCRAPING_SCRIPT_PATH]
        if max_stores > 0:
            cmd += ["--max-stores", str(max_stores)]
        if max_days_per_store > 0:
            cmd += ["--max-days-per-store", str(max_days_per_store)]

        job_id = uuid.uuid4().hex
        with JOBS_LOCK:
            JOBS[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "progress": 0,
                "message": "キューに登録しました",
                "selected_count": len(selected_store_names),
                "store_done": 0,
                "store_total": len(selected_store_names),
                "store_current": 0,
                "test_mode_applied": bool(TEST_MODE_AVAILABLE and requested_test_mode),
                "test_mode_max_days": TEST_MODE_MAX_DAYS if (TEST_MODE_AVAILABLE and requested_test_mode) else 0,
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "output": "",
            }

        t = threading.Thread(target=_run_scrape_job, args=(job_id, cmd), daemon=True)
        t.start()
        return jsonify({
            "job_id": job_id,
            "message": f"{len(selected_store_names)} 個の店舗のスクレイピングを開始しました",
            "selected_count": len(selected_store_names),
            "test_mode_applied": bool(TEST_MODE_AVAILABLE and requested_test_mode),
            "test_mode_max_days": TEST_MODE_MAX_DAYS if (TEST_MODE_AVAILABLE and requested_test_mode) else 0,
        }), 202

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
    print(f"store_list.csv: {os.path.abspath(STORE_LIST_PATH)}")
    print(f"ブラウザで http://{host}:{port} にアクセスしてください")
    print("=" * 50)

    app.run(debug=debug, host=host, port=port)

