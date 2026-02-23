import csv
import importlib.util
import os
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_PATH = ROOT / "_internal" / "app" / "app.py"
STORE_LIST_PATH = ROOT / "store_list.csv"
RUNTIME_DIR = ROOT / "_internal" / "runtime"


def load_app_module():
    spec = importlib.util.spec_from_file_location("slot_app", str(APP_PATH))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wait_for_job(client, job_id, timeout_sec=10):
    start = time.time()
    while time.time() - start < timeout_sec:
        res = client.get(f"/api/jobs/{job_id}")
        if res.status_code != 200:
            return None
        payload = res.get_json()
        if payload.get("status") in ("completed", "failed"):
            return payload
        time.sleep(0.1)
    return None


def write_min_store_csv(path):
    rows = [
        ["store_name", "store_url", "data_directory"],
        ["店舗A", "https://example.com/a", ".\\data\\test"],
        ["店舗B", "https://example.com/b", ".\\data\\test2"],
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main():
    original_store_list = STORE_LIST_PATH.read_bytes()
    results = []
    tmp = Path(tempfile.mkdtemp(prefix="slot-smoke-"))

    try:
        write_min_store_csv(STORE_LIST_PATH)

        os.environ["SCRAPING_SCRIPT_PATH"] = str(ROOT / "_internal" / "runtime" / "fake_scraper_ok.py")
        os.environ["LOG_FILE"] = str(tmp / "scraping_log.json")
        os.environ["COMPLETED_STORES_PATH"] = str(tmp / "completed_stores.json")
        os.environ["TEMP_STORE_LIST_PATH"] = str(tmp / "temp_store_list.csv")
        os.environ["OFFLINE_SCRIPT_PATH"] = str(ROOT / "_internal" / "runtime" / "fake_scraper_ok.py")

        app_mod = load_app_module()
        client = app_mod.app.test_client()

        r = client.get("/api/stores")
        stores = r.get_json() if r.status_code == 200 else []
        results.append(("GET /api/stores", r.status_code == 200 and len(stores) >= 2, f"status={r.status_code}, stores={len(stores)}"))

        r = client.post("/api/stores/save", json={"stores": "bad"})
        results.append(("POST /api/stores/save invalid", r.status_code == 400, f"status={r.status_code}"))

        r = client.post(
            "/api/stores/save",
            json={
                "stores": [
                    {"name": "", "url": "https://example.com/blank", "directory": ".\\data\\test"},
                    {"name": "並び替え対象", "url": "https://example.com/2", "directory": ".\\data\\test2"},
                ]
            },
        )
        saved = STORE_LIST_PATH.read_text(encoding="utf-8-sig")
        results.append(("POST /api/stores/save valid", r.status_code == 200 and "店舗1" in saved, f"status={r.status_code}"))

        r = client.post("/api/stores/reorder", json={"order": [".\\data\\test2", ".\\data\\test"]})
        reordered = STORE_LIST_PATH.read_text(encoding="utf-8-sig")
        first_data_row = reordered.splitlines()[1] if len(reordered.splitlines()) > 1 else ""
        results.append(("POST /api/stores/reorder", r.status_code == 200 and ".\\data\\test2" in first_data_row, f"status={r.status_code}"))

        r = client.post("/api/scrape", json={"stores": ["店舗1"]})
        ok_job = r.get_json().get("job_id") if r.status_code == 202 else None
        ok_job_result = wait_for_job(client, ok_job) if ok_job else None
        results.append(
            (
                "POST /api/scrape success flow",
                r.status_code == 202 and ok_job_result and ok_job_result.get("status") == "completed" and ok_job_result.get("progress") == 100,
                f"start={r.status_code}, end={ok_job_result.get('status') if ok_job_result else 'none'}",
            )
        )

        app_mod.SCRAPING_SCRIPT_PATH = str(ROOT / "_internal" / "runtime" / "fake_scraper_fail.py")
        r = client.post("/api/scrape", json={"stores": ["店舗1"]})
        fail_job = r.get_json().get("job_id") if r.status_code == 202 else None
        fail_job_result = wait_for_job(client, fail_job) if fail_job else None
        fail_message = (fail_job_result or {}).get("message", "")
        results.append(
            (
                "POST /api/scrape failure flow",
                r.status_code == 202 and fail_job_result and fail_job_result.get("status") == "failed" and "中断" in fail_message,
                f"start={r.status_code}, end={fail_job_result.get('status') if fail_job_result else 'none'}",
            )
        )

        r = client.post("/api/scrape", json={"stores": []})
        results.append(("POST /api/scrape no stores", r.status_code == 400, f"status={r.status_code}"))

        r = client.post("/api/scrape", json={"stores": ["存在しない店舗"]})
        results.append(("POST /api/scrape unknown store", r.status_code == 400, f"status={r.status_code}"))

        r = client.get("/api/logs")
        logs = r.get_json() if r.status_code == 200 else []
        results.append(("GET /api/logs", r.status_code == 200 and isinstance(logs, list) and len(logs) >= 1, f"status={r.status_code}, logs={len(logs)}"))

        app_mod.OFFLINE_SCRIPT_PATH = str(ROOT / "_internal" / "runtime" / "fake_scraper_ok.py")
        r = client.post("/api/format-offline")
        payload = r.get_json() if r.status_code == 200 else {}
        results.append(("POST /api/format-offline basic", r.status_code == 200 and "message" in payload, f"status={r.status_code}"))

        app_mod.OFFLINE_SCRIPT_PATH = str(tmp / "does_not_exist.py")
        r = client.post("/api/format-offline")
        results.append(("POST /api/format-offline error", r.status_code == 500, f"status={r.status_code}"))

        old_app_dir = app_mod.APP_DIR
        app_mod.APP_DIR = str(tmp)
        r = client.get("/")
        app_mod.APP_DIR = old_app_dir
        results.append(("GET / index missing", r.status_code == 404, f"status={r.status_code}"))

        passed = sum(1 for _, ok, _ in results if ok)
        total = len(results)
        print(f"RESULT {passed}/{total}")
        for name, ok, detail in results:
            mark = "PASS" if ok else "FAIL"
            print(f"{mark}\t{name}\t{detail}")

        return 0 if passed == total else 1
    finally:
        STORE_LIST_PATH.write_bytes(original_store_list)


if __name__ == "__main__":
    sys.exit(main())
